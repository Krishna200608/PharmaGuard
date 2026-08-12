"""
Baseline Script — single-shot Gemini comparison for PharmaGuard evaluation.

One LLM call per drug-event pair. No tool use. No FAERS, ChEMBL, or PubMed access.
The LLM receives only the drug name and adverse event, and must produce an
escalation decision (ESCALATE / MONITOR / DO_NOT_ESCALATE) with a confidence score.

Output: TriageReport JSON files written to outputs/baseline/, using the exact same
schema as the main pipeline so evaluator.py can score them with zero modification.

Cache: disk-backed via cache.py, key prefix "baseline::{drug}::{event}::{prompts_version}".

Usage:
    python scripts/baseline.py
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

sys.path.append(str(Path(__file__).resolve().parents[1]))

from pharmaguard.agent.output_schema import (
    EscalationDecision,
    EvidenceGrade,
    LiteratureOutput,
    MechanismOutput,
    PlausibilityLevel,
    PlausibilitySource,
    SignalStrength,
    SignalStatsOutput,
    TriageOutput,
    TriageReport,
)
from pharmaguard.tools.cache import ToolCache, CACHE_SCHEMA_VERSION
from pharmaguard.utils.config_loader import load_config
from pharmaguard.utils.prompt_loader import PromptLoader

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured output schema for the LLM — mirrors the pattern in fixed_pipeline
# ---------------------------------------------------------------------------

class BaselineOutput(BaseModel):
    """Structured output for the single-shot baseline LLM call."""
    escalation: Literal["ESCALATE", "MONITOR", "DO_NOT_ESCALATE"] = Field(
        description="Triage recommendation: ESCALATE, MONITOR, or DO_NOT_ESCALATE."
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the recommendation, between 0.0 and 1.0."
    )
    rationale: str = Field(
        description="Brief pharmacological justification for the decision (1-3 sentences)."
    )


# ---------------------------------------------------------------------------
# Cache key for baseline calls
# ---------------------------------------------------------------------------

def baseline_cache_key(drug: str, event: str, prompts_version: str) -> str:
    """
    Distinct prefix so baseline results never collide with pipeline cache entries.
    Includes CACHE_SCHEMA_VERSION so bumping it invalidates baseline too.
    """
    return (
        f"baseline::{drug.lower().strip()}"
        f"::{event.lower().strip()}"
        f"::{prompts_version}"
        f"::{CACHE_SCHEMA_VERSION}"
    )


# ---------------------------------------------------------------------------
# Sentinel sub-objects: fill required TriageReport fields with explicit nulls
# so evaluator.py can load the JSON without modification.
# The baseline makes no tool calls, so all three data sources are absent.
# ---------------------------------------------------------------------------

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

def _null_signal_stats() -> SignalStatsOutput:
    return SignalStatsOutput(
        prr=None,
        ror=None,
        prr_lower_ci=None,
        ror_lower_ci=None,
        report_count=0,
        source_endpoint="baseline_no_tool_call",
        data_pulled_at=_EPOCH,
        null_reason="Baseline: no FAERS query made.",
        prr_score=0.0,
        prr_score_label=SignalStrength.NO_SIGNAL,
        ci_downgraded=False,
    )


def _null_mechanism() -> MechanismOutput:
    return MechanismOutput(
        chembl_id=None,
        moa=None,
        biological_plausibility=PlausibilityLevel.UNKNOWN,
        plausibility_score=0.0,
        plausibility_source=PlausibilitySource.UNKNOWN,
        plausibility_rationale="Baseline: no ChEMBL query made.",
    )


def _null_literature() -> LiteratureOutput:
    return LiteratureOutput(
        pubmed_query="",
        abstracts_retrieved=0,
        evidence_grade=EvidenceGrade.C,
        grade_score=0.0,
        supporting_pmids=[],
        evidence_summary="Baseline: no PubMed query made.",
    )


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_baseline():
    load_dotenv()

    project_root = Path(__file__).resolve().parents[1]
    gt_path = project_root / "pharmaguard" / "data" / "ground_truth.json"
    output_dir = project_root / "outputs" / "baseline"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not gt_path.exists():
        logger.error("Ground truth file not found at %s", gt_path)
        return

    with open(gt_path, "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    pairs = gt_data.get("pairs", [])
    if not pairs:
        logger.error("No pairs found in ground_truth.json.")
        return

    config = load_config()
    cache = ToolCache() if config.cache.enabled else None
    prompt_loader = PromptLoader()
    prompts_version = prompt_loader.version
    prompt_template = prompt_loader.get("baseline_single_shot")

    # Lazy-import langchain to keep startup fast
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage

    llm = ChatGoogleGenerativeAI(model=config.agent.llm_model, temperature=0.0)
    structured_llm = llm.with_structured_output(BaselineOutput)

    logger.info(
        "Running baseline on %d pairs | model=%s | prompts_version=%s | cache=%s",
        len(pairs), config.agent.llm_model, prompts_version,
        "enabled" if cache else "disabled",
    )

    for i, pair in enumerate(pairs):
        drug = pair["drug_canonical"]
        event = pair["event_meddra_pt"]
        run_id = f"eval-run-{i}-{drug.replace(' ', '')}-{event.replace(' ', '')}"

        logger.info(
            "Pair %d/%d: %s + %s  (run_id: %s)",
            i + 1, len(pairs), drug, event, run_id
        )

        # Cache check — skip LLM call if we already have a result
        cached_result = None
        cache_key = None
        if cache:
            cache_key = baseline_cache_key(drug, event, prompts_version)
            cached_result = cache.get(cache_key)

        if cached_result:
            logger.info("  Cache HIT — skipping LLM call")
            escalation_str = cached_result["escalation"]
            confidence = cached_result["confidence"]
            rationale = cached_result["rationale"]
        else:
            prompt = prompt_template.format(drug=drug, event=event)
            try:
                result: BaselineOutput = structured_llm.invoke([HumanMessage(content=prompt)])
            except Exception as exc:
                logger.error("  LLM call failed for %s + %s: %s", drug, event, exc)
                continue

            escalation_str = result.escalation
            confidence = result.confidence
            rationale = result.rationale
            logger.info(
                "  Decision: %s  (confidence=%.2f)", escalation_str, confidence
            )

            if cache and cache_key:
                cache.set(cache_key, {
                    "escalation": escalation_str,
                    "confidence": confidence,
                    "rationale": rationale,
                })

        # Map escalation string to enum
        escalation = EscalationDecision(escalation_str)

        # Assemble a TriageReport with null sub-objects for unused tool outputs.
        # signal_strength and evidence_grade are synthetic sentinels — they are
        # not used by evaluator.py (it reads only .triage.escalation). They
        # are set to plausible values so the report is internally consistent.
        report = TriageReport(
            run_id=run_id,
            prompts_version=prompts_version,
            drug=drug,
            event=event,
            signal_stats=_null_signal_stats(),
            mechanism=_null_mechanism(),
            literature=_null_literature(),
            triage=TriageOutput(
                signal_strength=SignalStrength.NO_SIGNAL,  # sentinel; no FAERS data
                evidence_grade=EvidenceGrade.C,            # sentinel; no PubMed data
                escalation=escalation,
                confidence=confidence,
                prompts_version=prompts_version,
                agent_reasoning_trace=[
                    f"Baseline single-shot call. No tool use.",
                    f"LLM decision: {escalation_str} (confidence={confidence:.2f})",
                    f"Rationale: {rationale}",
                ],
            ),
        )

        out_path = output_dir / f"{run_id}_report.json"
        with open(out_path, "w", encoding="utf-8") as rf:
            rf.write(report.model_dump_json(indent=2))

    logger.info("Baseline complete. Reports written to %s", output_dir)


if __name__ == "__main__":
    run_baseline()
