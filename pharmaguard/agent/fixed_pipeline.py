"""
Fixed Pipeline Orchestrator - Sprint 2 Fallback Implementation.
Runs a strict, deterministic sequence: Faers -> Chembl -> PubMed.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from pathlib import Path

from pharmaguard.utils.config_loader import load_config
from pharmaguard.utils.prompt_loader import PromptLoader
from pharmaguard.agent.transcript_logger import TranscriptLogger
from pharmaguard.tools.cache import ToolCache
from pharmaguard.tools.signal_source import FaersLegacySource
from pharmaguard.tools.chembl_tool import ChemblTool
from pharmaguard.tools.pubmed_tool import PubMedTool
from pharmaguard.agent.output_schema import (
    TriageReport, TriageOutput, SignalStatsOutput, MechanismOutput, LiteratureOutput,
    compute_prr_score, compute_confidence, derive_escalation, SignalStrength, EvidenceGrade, PlausibilityLevel, EscalationDecision, PlausibilitySource,
    LeakageCritique
)
from pydantic import BaseModel, Field
from typing import Literal

logger = logging.getLogger(__name__)

class GradeOutput(BaseModel):
    grade: Literal["A", "B", "C"] = Field(description="The evidence grade based on the rubric. Must be A, B, or C.")
    explanation: str = Field(description="Explanation for why this grade was assigned.")

class PlausibilityLLMOutput(BaseModel):
    plausibility: Literal["HIGH", "MODERATE", "LOW"] = Field(description="The plausibility level. Must be HIGH, MODERATE, or LOW.")
    explanation: str = Field(description="Explanation for why this plausibility was assigned.")

def extract_text(content) -> str:
    if isinstance(content, str): return content
    if isinstance(content, list): return " ".join([part.get("text", "") for part in content if isinstance(part, dict) and "text" in part])
    return str(content)

class FixedPipelineAgent:
    def __init__(self, run_id: str, cache_dir: str = ".cache/pharmaguard"):
        self.run_id = run_id
        self.config = load_config()
        self.cache = ToolCache(cache_dir=Path(cache_dir)) if self.config.cache.enabled else None
        self.prompt_loader = PromptLoader()
        self.tlog = TranscriptLogger(run_id=run_id)
        
        # In fixed pipeline we can either use the exact same LLM fn or mock it 
        # based on config. We assume we still want to use LLM for PubMed grading.
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import SystemMessage, HumanMessage
        import json
        
        self.llm = ChatGoogleGenerativeAI(model=self.config.agent.llm_model, temperature=0.0)
        
        def pubmed_llm_fn(abstracts: list[str], pmids: list[str], rubric: str):
            sys_msg = SystemMessage(content=rubric)
            user_msg = HumanMessage(content=f"Abstracts:\n{json.dumps(abstracts)}\nPMIDs:\n{json.dumps(pmids)}")
            structured_llm = self.llm.with_structured_output(GradeOutput)
            result = structured_llm.invoke([sys_msg, user_msg])
            text_content = f"Final Grade: {result.grade}\nExplanation: {result.explanation}"
            return result.grade, pmids, text_content
            
        def chembl_llm_fn(moa: str, event: str):
            prompt = f"Given MoA: {moa}, how plausible is {event}? Explain first, then assign HIGH, MODERATE, or LOW."
            structured_llm = self.llm.with_structured_output(PlausibilityLLMOutput)
            result = structured_llm.invoke([HumanMessage(content=prompt)])

            if result.plausibility == "HIGH": level = PlausibilityLevel.HIGH
            elif result.plausibility == "MODERATE": level = PlausibilityLevel.MODERATE
            else: level = PlausibilityLevel.LOW
            return level, result.explanation

        self.faers = FaersLegacySource(cache=self.cache)

        critic_cfg = getattr(self.config.plausibility, "leakage_critic", None)
        critic_enabled = getattr(critic_cfg, "enabled", False) if critic_cfg else False
        critic_action = getattr(critic_cfg, "action", "flag") if critic_cfg else "flag"

        def critic_llm_fn(rationale: str):
            critic_prompt = self.prompt_loader.get("leakage_critic").replace("{rationale}", rationale)
            structured_llm = self.llm.with_structured_output(LeakageCritique)
            return structured_llm.invoke([HumanMessage(content=critic_prompt)])

        self.chembl = ChemblTool(
            cache=self.cache,
            prompts_version=self.prompt_loader.version,
            force_agent_derivation=(self.config.plausibility.source == "force_agent"),
            llm_inference_fn=chembl_llm_fn,
            leakage_critic_enabled=critic_enabled,
            leakage_critic_action=critic_action,
            critic_llm_fn=critic_llm_fn if critic_enabled else None,
        )
        self.pubmed = PubMedTool(
            cache=self.cache,
            prompt_loader=self.prompt_loader,
            llm_inference_fn=pubmed_llm_fn
        )

    def _build_error_fallback_report(self, drug: str, event: str, stage: str, error_msg: str) -> TriageReport:
        """
        Construct a graceful fallback TriageReport reusing the standard null_reason
        contract when an unexpected orchestrator exception occurs during evaluation.
        """
        now = datetime.now(timezone.utc)
        s_out = SignalStatsOutput(
            prr=None,
            ror=None,
            prr_lower_ci=None,
            ror_lower_ci=None,
            report_count=0,
            source_endpoint="pipeline_error_fallback",
            data_pulled_at=now,
            null_reason=f"Pipeline error at stage '{stage}': {error_msg}",
            prr_score=0.0,
            prr_score_label=SignalStrength.NO_SIGNAL,
            ci_downgraded=False,
        )
        m_out = MechanismOutput(
            chembl_id=None,
            moa=None,
            biological_plausibility=PlausibilityLevel.UNKNOWN,
            plausibility_score=0.0,
            plausibility_source=PlausibilitySource.UNKNOWN,
            plausibility_rationale=f"Pipeline error at stage '{stage}': {error_msg}",
        )
        l_out = LiteratureOutput(
            pubmed_query="",
            abstracts_retrieved=0,
            evidence_grade=EvidenceGrade.C,
            grade_score=0.0,
            supporting_pmids=[],
            evidence_summary=f"Pipeline error at stage '{stage}': {error_msg}",
        )
        t_out = TriageOutput(
            signal_strength=SignalStrength.NO_SIGNAL,
            evidence_grade=EvidenceGrade.C,
            escalation=EscalationDecision.DO_NOT_ESCALATE,
            confidence=0.0,
            prompts_version=self.prompt_loader.version,
            agent_reasoning_trace=[f"ERROR: FixedPipelineAgent failed at stage '{stage}' for {drug}::{event}: {error_msg}"],
        )
        return TriageReport(
            run_id=self.run_id,
            prompts_version=self.prompt_loader.version,
            drug=drug,
            event=event,
            signal_stats=s_out,
            mechanism=m_out,
            literature=l_out,
            triage=t_out,
        )

    def run(self, drug: str, event: str) -> TriageReport:
        stage = "initialization"
        try:
            stage = "faers"
            self.tlog.log_thought("Starting Fixed Pipeline. Step 1: FAERS")
            
            # 1. FAERS
            self.tlog.log_action("faers_signal_tool", {"drug": drug, "event": event})
            stats = self.faers.get_signal_stats(drug, event)
            ss_dict = stats.__dict__.copy()
            if hasattr(ss_dict.get("data_pulled_at"), "isoformat"):
                ss_dict["data_pulled_at"] = ss_dict["data_pulled_at"].isoformat()
            self.tlog.log_observation("faers_signal_tool", ss_dict, cache_hit=False)

            # 2. ChEMBL
            stage = "chembl"
            self.tlog.log_thought("Step 2: ChEMBL")
            self.tlog.log_action("chembl_mechanism_tool", {"drug": drug, "event": event})
            plaus = self.chembl.get_plausibility(drug, event)
            entry = self.chembl.get_drug_entry(drug)
            m_dict = {
                "chembl_id": getattr(plaus, "chembl_id", None),
                "moa": getattr(plaus, "moa", None),
                "level": getattr(plaus.level, "value", plaus.level),
                "score": plaus.score,
                "source": plaus.plausibility_source,
                "rationale": plaus.rationale,
                "leak_detected": getattr(plaus, "leak_detected", None),
                "leak_phrases": getattr(plaus, "leak_phrases", None),
            }
            if plaus.curated_reference:
                m_dict["curated_reference"] = getattr(plaus.curated_reference, "value", plaus.curated_reference)
                m_dict["agreement"] = plaus.agreement
            self.tlog.log_observation("chembl_mechanism_tool", m_dict, cache_hit=False)

            # 3. PubMed
            stage = "pubmed"
            self.tlog.log_thought("Step 3: PubMed")
            self.tlog.log_action("pubmed_evidence_tool", {"drug": drug, "event": event})
            res = self.pubmed.search_and_grade(drug, event)
            l_dict = {
                "query": res.query,
                "abstracts_retrieved": res.abstracts_retrieved,
                "grade": res.evidence_grade,
                "supporting_pmids": res.supporting_pmids,
                "summary": res.evidence_summary
            }
            self.tlog.log_observation("pubmed_evidence_tool", l_dict, cache_hit=False)

            stage = "synthesis"
            self.tlog.log_thought("Synthesizing Final Report")
            
            # Build final report
            rc = ss_dict.get("report_count", 0)
            prr = ss_dict.get("prr")
            prr_lci = ss_dict.get("prr_lower_ci")
            prr_score, ss_label, ci_downgraded = compute_prr_score(rc, prr, prr_lci)

            # Confounding assessment & discounting (if enabled)
            discount_factor = 1.0
            confounding_res = None
            confounding_cfg = getattr(self.config, "confounding", None)
            if confounding_cfg and confounding_cfg.enabled and prr_score > 0:
                from pharmaguard.tools.confounding import ConfoundingTool
                c_tool = ConfoundingTool(llm=self.llm, prompt_loader=self.prompt_loader)
                confounding_res = c_tool.assess(drug, event, m_dict.get("moa") or "", rc, prr)
                discount_factor = confounding_res.discount_factor
                logger.info(
                    "Confounding assessment for %s::%s -> is_confounded=%s, discount=%.2f",
                    drug, event, confounding_res.is_confounded, discount_factor
                )

            adjusted_prr_score = round(prr_score * discount_factor, 4)

            s_out = SignalStatsOutput(
                prr=prr,
                ror=ss_dict.get("ror"),
                prr_lower_ci=prr_lci,
                ror_lower_ci=ss_dict.get("ror_lower_ci"),
                report_count=rc,
                source_endpoint=ss_dict.get("source_endpoint", "unknown"),
                data_pulled_at=datetime.fromisoformat(ss_dict["data_pulled_at"]) if "data_pulled_at" in ss_dict else datetime.now(timezone.utc),
                null_reason=ss_dict.get("null_reason"),
                prr_score=adjusted_prr_score,
                prr_score_label=ss_label,
                ci_downgraded=ci_downgraded,
                discount_factor=discount_factor if (confounding_cfg and confounding_cfg.enabled) else None,
                is_confounded=confounding_res.is_confounded if confounding_res else None,
                confounding_drugs=confounding_res.confounding_drugs if confounding_res else None,
                confounding_explanation=confounding_res.confounding_explanation if confounding_res else None,
            )
            
            plaus_level = m_dict.get("level", PlausibilityLevel.UNKNOWN)
            m_out = MechanismOutput(
                chembl_id=m_dict.get("chembl_id"),
                moa=m_dict.get("moa"),
                biological_plausibility=PlausibilityLevel(plaus_level) if plaus_level else PlausibilityLevel.UNKNOWN,
                plausibility_score=m_dict.get("score", 0.0),
                plausibility_source=PlausibilitySource(m_dict.get("source", "unknown")),
                plausibility_rationale=m_dict.get("rationale", ""),
                curated_reference=PlausibilityLevel(m_dict["curated_reference"]) if m_dict.get("curated_reference") else None,
                plausibility_agreement=m_dict.get("agreement"),
                leak_detected=m_dict.get("leak_detected"),
                leak_phrases=m_dict.get("leak_phrases"),
            )
            
            eg_str = l_dict.get("grade", "C")
            l_out = LiteratureOutput(
                pubmed_query=l_dict.get("query", ""),
                abstracts_retrieved=l_dict.get("abstracts_retrieved", 0),
                evidence_grade=EvidenceGrade(eg_str) if eg_str else EvidenceGrade.C,
                grade_score=1.0 if eg_str == "A" else (0.5 if eg_str == "B" else 0.0),
                supporting_pmids=l_dict.get("supporting_pmids", []),
                evidence_summary=l_dict.get("summary", "")
            )
            
            conf = compute_confidence(adjusted_prr_score, eg_str, plaus_level)
            esc = derive_escalation(conf, ss_label)
            
            reasoning = ["Determined using fixed deterministic pipeline: FAERS -> ChEMBL -> PubMed"]
            
            t_out = TriageOutput(
                signal_strength=ss_label,
                evidence_grade=EvidenceGrade(eg_str),
                escalation=esc,
                confidence=conf,
                prompts_version=self.prompt_loader.version,
                agent_reasoning_trace=reasoning
            )
            
            report = TriageReport(
                run_id=self.run_id,
                prompts_version=self.prompt_loader.version,
                drug=drug,
                event=event,
                signal_stats=s_out,
                mechanism=m_out,
                literature=l_out,
                triage=t_out
            )
            
            self.tlog.log_final_answer("\n".join(reasoning))
            self.tlog.finalize()
            
            return report
        except Exception as exc:
            logger.error(
                "Unexpected failure in FixedPipelineAgent at stage '%s' for pair %s::%s: %s",
                stage, drug, event, exc, exc_info=True
            )
            try:
                self.tlog.log_thought(f"ERROR: FixedPipelineAgent failed at stage '{stage}' for {drug}::{event}: {exc}")
                self.tlog.log_final_answer(f"Failed at stage '{stage}': {exc}")
                self.tlog.finalize()
            except Exception as log_exc:
                logger.warning("Failed to finalize transcript logger for %s::%s: %s", drug, event, log_exc)
            
            return self._build_error_fallback_report(drug, event, stage, str(exc))