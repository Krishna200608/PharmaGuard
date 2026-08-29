"""
Repeated-Run Stability Analysis for PharmaGuard (Revised Experiment 1).

Evaluates LLM-derived sub-score variance, categorical escalation decision mode agreement,
and cross-run rank stability across repeated invocations at temperature=0.0.

Primary experimental unit: (pair, repeated-call) nested within n=15 benchmark pairs.
Output: outputs/research/stability/repeated_run_variance.json

Owner: Krishna Sikheriya (IIT2023139)
"""

import argparse
import json
import logging
import math
import os
import subprocess
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

from pydantic import BaseModel, Field
from typing import Literal

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from pharmaguard.utils.config_loader import load_config
from pharmaguard.utils.prompt_loader import PromptLoader
from pharmaguard.tools.cache import ToolCache, CACHE_SCHEMA_VERSION
from pharmaguard.tools.signal_source import FaersLegacySource
from pharmaguard.tools.chembl_tool import ChemblTool
from pharmaguard.tools.pubmed_tool import PubMedTool
from pharmaguard.agent.output_schema import (
    compute_prr_score,
    compute_confidence,
    derive_escalation,
    PlausibilityLevel,
    EvidenceGrade,
    SignalStrength,
    EscalationDecision,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("stability_repeated_runs")

# Default scratch cache directory — NEVER points to production cache
SCRATCH_CACHE_DIR = REPO_ROOT / ".cache" / "pharmaguard_research_scratch"
DEFAULT_OUTPUT_FILE = REPO_ROOT / "outputs" / "research" / "stability" / "repeated_run_variance.json"
SCRATCH_CONFOUNDING_CACHE_DIR = REPO_ROOT / ".cache" / "pharmaguard_research_confounding_scratch"
DEFAULT_CONFOUNDING_OUTPUT_FILE = REPO_ROOT / "outputs" / "research" / "stability" / "repeated_run_variance_confounding.json"
GROUND_TRUTH_FILE = REPO_ROOT / "pharmaguard" / "data" / "ground_truth.json"


class GradeOutput(BaseModel):
    grade: Literal["A", "B", "C"] = Field(description="The evidence grade based on the rubric. Must be A, B, or C.")
    explanation: str = Field(description="Explanation for why this grade was assigned.")


# ----------------------------------------------------------------------
# Statistical Analysis Functions
# ----------------------------------------------------------------------

def rankdata(a: list[float]) -> list[float]:
    """
    Compute fractional ranks (1-indexed, average ties) identically to scipy.stats.rankdata.
    """
    n = len(a)
    if n == 0:
        return []
    sorted_indices = sorted(range(n), key=lambda i: a[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and a[sorted_indices[j + 1]] == a[sorted_indices[i]]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[sorted_indices[k]] = avg_rank
        i = j + 1
    return ranks


def calc_spearman_rank_correlation(v1: list[float], v2: list[float]) -> float:
    """
    Compute Spearman rank correlation between two continuous vectors.
    """
    if len(v1) != len(v2) or len(v1) < 2:
        return 0.0
    r1 = rankdata(v1)
    r2 = rankdata(v2)
    n = len(r1)
    m1 = sum(r1) / n
    m2 = sum(r2) / n
    num = sum((r1[i] - m1) * (r2[i] - m2) for i in range(n))
    den1 = sum((r1[i] - m1) ** 2 for i in range(n))
    den2 = sum((r2[i] - m2) ** 2 for i in range(n))
    denom = math.sqrt(den1 * den2)
    if denom == 0.0:
        return 1.0 if r1 == r2 else 0.0
    return round(num / denom, 6)


def calc_wilson_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """
    Wilson score interval for binomial proportion.
    Returns (lower_bound, upper_bound) rounded to 4 decimal places.
    """
    if n <= 0:
        return (0.0, 0.0)
    z = 1.959963984540054  # 95% two-sided
    p = k / n
    denom = 1.0 + (z ** 2) / n
    center = (p + (z ** 2) / (2 * n)) / denom
    margin = (z / denom) * math.sqrt((p * (1 - p) / n) + ((z ** 2) / (4 * (n ** 2))))
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return (round(lower, 4), round(upper, 4))


def calc_summary_stats(values: list[float]) -> dict:
    """
    Compute continuous score summary statistics: mean, sample SD, min, max, CV.
    """
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "cv": None}
    mean_val = sum(values) / n
    if n > 1:
        variance = sum((x - mean_val) ** 2 for x in values) / (n - 1)
        std_val = math.sqrt(max(0.0, variance))
    else:
        std_val = 0.0
    
    cv_val = round(std_val / mean_val, 6) if mean_val > 1e-9 else (0.0 if std_val == 0.0 else None)
    return {
        "n": n,
        "mean": round(mean_val, 4),
        "std": round(std_val, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "cv": cv_val,
    }


def calc_mode_and_agreement(categories: list[str]) -> dict:
    """
    Compute categorical mode and percent agreement with mode.
    """
    n = len(categories)
    if n == 0:
        return {
            "mode": "UNKNOWN",
            "mode_count": 0,
            "percent_agreement": 0.0,
            "wilson_ci": [0.0, 0.0],
            "is_100_percent_stable": False,
        }
    counts = Counter(categories)
    mode_cat, mode_cnt = counts.most_common(1)[0]
    agreement_pct = round((mode_cnt / n) * 100.0, 2)
    ci = calc_wilson_interval(mode_cnt, n)
    return {
        "mode": mode_cat,
        "mode_count": mode_cnt,
        "percent_agreement": agreement_pct,
        "wilson_ci": list(ci),
        "is_100_percent_stable": mode_cnt == n,
    }


def get_git_commit_hash() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception as exc:
        logger.warning("Failed to retrieve git commit hash: %s", exc)
        return "unknown"


# ----------------------------------------------------------------------
# Main Experiment Execution
# ----------------------------------------------------------------------

def run_repeated_stability_experiment(
    repeats: int = 10,
    pairs_limit: Optional[int] = None,
    inter_call_delay: float = 4.2,
    scratch_dir: Optional[Path] = None,
    output_file: Optional[Path] = None,
    gt_file: Path = GROUND_TRUTH_FILE,
    enable_confounding: bool = False,
    only_confounding_eligible: bool = False,
) -> dict:
    """
    Execute Experiment 1: Repeated-Run Stability (supports confounding-enabled scoped runs).
    """
    t_start = datetime.now(timezone.utc)
    experiment_id = str(uuid.uuid4())
    git_hash = get_git_commit_hash()
    
    # Load config and ground truth
    config = load_config()
    prompt_loader = PromptLoader()

    if enable_confounding:
        if not hasattr(config, "confounding") or config.confounding is None:
            from pydantic import BaseModel
            class ConfoundingConfig(BaseModel):
                enabled: bool = True
            config.confounding = ConfoundingConfig(enabled=True)
        else:
            config.confounding.enabled = True

        if scratch_dir is None:
            scratch_dir = SCRATCH_CONFOUNDING_CACHE_DIR
        if output_file is None:
            output_file = DEFAULT_CONFOUNDING_OUTPUT_FILE
    else:
        if scratch_dir is None:
            scratch_dir = SCRATCH_CACHE_DIR
        if output_file is None:
            output_file = DEFAULT_OUTPUT_FILE
    
    with open(gt_file, "r", encoding="utf-8") as f:
        gt_data = json.load(f)
    all_pairs = gt_data.get("pairs", [])

    logger.info("Initializing separate scratch cache at %s", scratch_dir)
    scratch_cache = ToolCache(cache_dir=scratch_dir)

    # Instantiate tools pointing exclusively to scratch_cache
    llm = ChatGoogleGenerativeAI(model=config.agent.llm_model, temperature=0.0)

    def pubmed_llm_fn(abstracts: list[str], pmids: list[str], rubric: str):
        if not abstracts:
            return "C", [], "No abstracts retrieved from PubMed for this query."
        sys_msg = SystemMessage(content=rubric)
        user_msg = HumanMessage(content=f"Abstracts:\n{json.dumps(abstracts)}\nPMIDs:\n{json.dumps(pmids)}")
        structured_llm = llm.with_structured_output(GradeOutput)
        max_retries = 5
        backoff = 3.0
        for attempt in range(1, max_retries + 1):
            try:
                result = structured_llm.invoke([sys_msg, user_msg])
                text_content = f"Final Grade: {result.grade}\nExplanation: {result.explanation}"
                return result.grade, pmids, text_content
            except Exception as exc:
                if attempt == max_retries:
                    logger.error("LLM call failed after %d attempts: %s", max_retries, exc)
                    raise
                logger.warning(
                    "LLM call encountered transient network error on attempt %d/%d: %s. Retrying in %.1fs...",
                    attempt, max_retries, exc, backoff
                )
                time.sleep(backoff)
                backoff *= 2.0

    faers = FaersLegacySource(cache=scratch_cache)
    chembl = ChemblTool(
        cache=scratch_cache,
        prompts_version=prompt_loader.version,
        force_agent_derivation=(config.plausibility.source == "force_agent"),
    )
    pubmed_tool = PubMedTool(
        cache=scratch_cache,
        prompt_loader=prompt_loader,
        llm_inference_fn=pubmed_llm_fn,
    )

    confounding_tool = None
    if getattr(config, "confounding", None) and config.confounding.enabled:
        from pharmaguard.tools.confounding import ConfoundingTool
        confounding_tool = ConfoundingTool(llm=llm, prompt_loader=prompt_loader)

    # Seed raw FAERS and PubMed abstracts (and rep_grade for exact parity) from previous scratch cache
    if SCRATCH_CACHE_DIR.exists() and scratch_dir != SCRATCH_CACHE_DIR:
        orig_cache = ToolCache(cache_dir=SCRATCH_CACHE_DIR)
        for k in orig_cache._cache.iterkeys():
            if any(s in str(k) for s in ("research_abstracts_raw", "faers", "openfda", "rep_grade")):
                if k not in scratch_cache._cache:
                    scratch_cache.set(k, orig_cache.get(k))
        orig_cache.close()

    if only_confounding_eligible:
        eligible_keys = set()
        for rf in sorted((REPO_ROOT / "outputs").glob("eval-run-*_report.json")):
            with open(rf, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("signal_stats", {}).get("prr_score", 0.0) > 0:
                eligible_keys.add(f"{d['drug']}::{d['event']}")
        filtered = [p for p in all_pairs if f"{p['drug_canonical']}::{p['event_meddra_pt']}" in eligible_keys]
        logger.info("Filtered to %d confounding-eligible pairs (prr_score > 0): %s", len(filtered), [f"{p['drug_canonical']}::{p['event_meddra_pt']}" for p in filtered])
        all_pairs = filtered

    if pairs_limit is not None:
        all_pairs = all_pairs[:pairs_limit]

    logger.info(
        "Starting Repeated Stability Experiment [ID: %s] on %d pairs x %d repeats",
        experiment_id, len(all_pairs), repeats
    )

    per_pair_raw_results: dict[str, list[dict]] = {}
    pair_keys = []

    # Outer loop: Evaluate each pair across all repeats
    for p_idx, pair_entry in enumerate(all_pairs, 1):
        drug = pair_entry["drug_canonical"]
        event = pair_entry["event_meddra_pt"]
        pair_key = f"{drug}::{event}"
        pair_keys.append(pair_key)
        logger.info("[%d/%d] Processing pair %s", p_idx, len(all_pairs), pair_key)

        # 1. FAERS disproportionality (deterministic, scratch-cached)
        stats = faers.get_signal_stats(drug, event)
        rc = stats.report_count
        prr = stats.prr
        prr_lci = stats.prr_lower_ci
        prr_score, ss_label, ci_downgraded = compute_prr_score(rc, prr, prr_lci)

        # 2. ChEMBL biological plausibility (production lookup_first, scratch-cached)
        plaus = chembl.get_plausibility(drug, event)
        plaus_level_str = getattr(plaus.level, "value", str(plaus.level))
        plaus_score = plaus.score

        # 3. PubMed abstract retrieval (scratch-cached raw abstracts to prevent NCBI rate-limits)
        query = pubmed_tool._build_query(drug, event)
        abstracts_cache_key = f"research_abstracts_raw::{query}"
        cached_abstracts = scratch_cache.get(abstracts_cache_key)
        if cached_abstracts:
            pmids = cached_abstracts["pmids"]
            abstracts = cached_abstracts["abstracts"]
        else:
            pmids = pubmed_tool._esearch(query)
            abstracts = pubmed_tool._efetch_abstracts(pmids[:config.apis.max_pubmed_abstracts])
            scratch_cache.set(abstracts_cache_key, {"pmids": pmids, "abstracts": abstracts})

        rubric = prompt_loader.get("evidence_grading_rubric")

        pair_runs = []
        for rep in range(repeats):
            rep_cache_key = f"rep_grade::{drug}::{event}::run_{rep}::{prompt_loader.version}::{CACHE_SCHEMA_VERSION}"
            cached_rep = scratch_cache.get(rep_cache_key)

            if cached_rep:
                grade = cached_rep["grade"]
                call_ts = cached_rep["timestamp"]
            else:
                grade, supporting_pmids, summary = pubmed_llm_fn(
                    abstracts, pmids[:config.apis.max_pubmed_abstracts], rubric
                )
                call_ts = datetime.now(timezone.utc).isoformat()
                scratch_cache.set(
                    rep_cache_key,
                    {"grade": grade, "supporting": supporting_pmids, "summary": summary, "timestamp": call_ts},
                )
                if inter_call_delay > 0:
                    time.sleep(inter_call_delay)

            grade_score = 1.0 if grade == "A" else (0.5 if grade == "B" else 0.0)

            # 4. Confounding discounting (if active in config)
            discount_factor = 1.0
            if confounding_tool and prr_score > 0:
                conf_key = f"rep_confound::{drug}::{event}::run_{rep}::{prompt_loader.version}::{CACHE_SCHEMA_VERSION}"
                cached_conf = scratch_cache.get(conf_key)
                if cached_conf:
                    discount_factor = cached_conf["discount_factor"]
                else:
                    max_retries = 5
                    backoff = 2.0
                    conf_res = None
                    for attempt in range(1, max_retries + 1):
                        conf_res = confounding_tool.assess(drug, event, getattr(plaus, "moa", "") or "", rc, prr)
                        if (
                            conf_res.confounding_explanation
                            and conf_res.confounding_explanation.startswith("Assessment failed with error:")
                            and attempt < max_retries
                        ):
                            logger.warning(
                                "Transient error in confounding assessment for %s::%s (attempt %d/%d). Retrying in %.1fs...",
                                drug, event, attempt, max_retries, backoff
                            )
                            time.sleep(backoff)
                            backoff *= 2.0
                            continue
                        break
                    discount_factor = conf_res.discount_factor
                    scratch_cache.set(conf_key, {"discount_factor": discount_factor})
                    if inter_call_delay > 0:
                        time.sleep(inter_call_delay)

            adjusted_prr_score = round(prr_score * discount_factor, 4)

            # 5. Deterministic Confidence & Escalation gating
            conf = compute_confidence(adjusted_prr_score, grade, plaus_level_str)
            esc = derive_escalation(conf, ss_label)
            esc_str = getattr(esc, "value", str(esc))

            run_record = {
                "run_index": rep,
                "timestamp": call_ts,
                "prr_score": adjusted_prr_score,
                "plausibility_score": plaus_score,
                "grade": grade,
                "grade_score": grade_score,
                "discount_factor": discount_factor if (confounding_tool is not None) else None,
                "confidence": conf,
                "escalation": esc_str,
            }
            pair_runs.append(run_record)

        per_pair_raw_results[pair_key] = pair_runs

    t_end = datetime.now(timezone.utc)
    wall_clock_seconds = (t_end - t_start).total_seconds()
    wall_clock_hours = round(wall_clock_seconds / 3600.0, 4)
    duration_warning = (
        "Run duration exceeded 24 hours — potential LLM serving backend version shift confound."
        if wall_clock_hours > 24.0
        else None
    )

    # ------------------------------------------------------------------
    # Metrics Calculation
    # ------------------------------------------------------------------

    per_pair_summary_statistics: dict[str, dict] = {}
    unstable_pairs: list[str] = []

    for pair_key, runs in per_pair_raw_results.items():
        plaus_scores = [r["plausibility_score"] for r in runs]
        grade_scores = [r["grade_score"] for r in runs]
        confidences = [r["confidence"] for r in runs]
        escalations = [r["escalation"] for r in runs]

        plaus_stats = calc_summary_stats(plaus_scores)
        grade_stats = calc_summary_stats(grade_scores)
        conf_stats = calc_summary_stats(confidences)
        esc_stats = calc_mode_and_agreement(escalations)

        if not esc_stats["is_100_percent_stable"]:
            unstable_pairs.append(pair_key)

        pair_summary = {
            "plausibility_score": plaus_stats,
            "grade_score": grade_stats,
            "confidence": conf_stats,
            "escalation": esc_stats,
        }

        if runs[0]["discount_factor"] is not None:
            disc_factors = [r["discount_factor"] for r in runs]
            pair_summary["discount_factor"] = calc_summary_stats(disc_factors)

        per_pair_summary_statistics[pair_key] = pair_summary

    # Range of CVs across the 15 pairs
    conf_cvs = [s["confidence"]["cv"] for s in per_pair_summary_statistics.values() if s["confidence"]["cv"] is not None]
    grade_cvs = [s["grade_score"]["cv"] for s in per_pair_summary_statistics.values() if s["grade_score"]["cv"] is not None]
    plaus_cvs = [s["plausibility_score"]["cv"] for s in per_pair_summary_statistics.values() if s["plausibility_score"]["cv"] is not None]

    disc_cvs = [
        s["discount_factor"]["cv"]
        for s in per_pair_summary_statistics.values()
        if "discount_factor" in s and s["discount_factor"]["cv"] is not None
    ]

    cross_pair_summary = {
        "confidence_cv_range": [min(conf_cvs), max(conf_cvs)] if conf_cvs else [0.0, 0.0],
        "grade_score_cv_range": [min(grade_cvs), max(grade_cvs)] if grade_cvs else [0.0, 0.0],
        "plausibility_score_cv_range": [min(plaus_cvs), max(plaus_cvs)] if plaus_cvs else [0.0, 0.0],
        "discount_factor_cv_range": [min(disc_cvs), max(disc_cvs)] if disc_cvs else None,
        "total_pairs_evaluated": len(pair_keys),
        "total_unstable_pairs": len(unstable_pairs),
    }

    # Cross-run rank stability across all C(repeats, 2) run-pairs
    pairwise_correlations = []
    rhos = []
    for i in range(repeats):
        conf_i = [per_pair_raw_results[pk][i]["confidence"] for pk in pair_keys]
        for j in range(i + 1, repeats):
            conf_j = [per_pair_raw_results[pk][j]["confidence"] for pk in pair_keys]
            rho = calc_spearman_rank_correlation(conf_i, conf_j)
            pairwise_correlations.append({"run_i": i, "run_j": j, "spearman_rho": rho})
            rhos.append(rho)

    mean_spearman_rho = round(sum(rhos) / len(rhos), 4) if rhos else 1.0

    output_payload = {
        "experiment_id": experiment_id,
        "git_commit_hash": git_hash,
        "timestamp_start": t_start.isoformat(),
        "timestamp_end": t_end.isoformat(),
        "wall_clock_duration_hours": wall_clock_hours,
        "duration_warning": duration_warning,
        "model_name": config.agent.llm_model,
        "prompts_version": prompt_loader.version,
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "config_snapshot": {
            "agent_mode": config.agent.mode,
            "plausibility_source": config.plausibility.source,
            "leakage_critic_enabled": getattr(getattr(config, "plausibility", None), "leakage_critic", None) and config.plausibility.leakage_critic.enabled,
            "confounding_enabled": getattr(config, "confounding", None) and config.confounding.enabled,
        },
        "per_pair_raw_results": per_pair_raw_results,
        "per_pair_summary_statistics": per_pair_summary_statistics,
        "cross_pair_summary": cross_pair_summary,
        "cross_run_rank_stability": {
            "mean_spearman_rho": mean_spearman_rho,
            "num_run_pairs_compared": len(pairwise_correlations),
            "pairwise_correlations": pairwise_correlations,
        },
        "unstable_pairs": unstable_pairs,
    }

    # Save output artifact
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    logger.info("Saved repeated-run stability artifact to %s", output_file)
    scratch_cache.close()
    return output_payload


def print_summary_report(results: dict):
    print("\n" + "=" * 90)
    print("PHARMAGUARD EXPERIMENT 1: REPEATED-RUN STABILITY SUMMARY (TEMPERATURE=0.0)")
    print("=" * 90)
    print(f"Experiment ID:       {results['experiment_id']}")
    print(f"Git Commit Hash:     {results['git_commit_hash']}")
    print(f"Model / Version:     {results['model_name']} | Prompts: {results['prompts_version']} | Schema: {results['cache_schema_version']}")
    print(f"Duration:            {results['wall_clock_duration_hours']:.4f} hours")
    if results["duration_warning"]:
        print(f"WARNING:             {results['duration_warning']}")
    print(f"Rank Stability:      Mean Spearman Rho = {results['cross_run_rank_stability']['mean_spearman_rho']:.4f} (across {results['cross_run_rank_stability']['num_run_pairs_compared']} run-pairs)")
    print("-" * 90)

    has_confounding = any("discount_factor" in s for s in results["per_pair_summary_statistics"].values())
    if has_confounding:
        print(f"{'Drug :: Event':<35} | {'Grade Mean±SD':<13} | {'Disc Mean±SD (CV)':<18} | {'Conf Mean±SD':<15} | {'Mode Decision':<15} | {'Mode %':<8}")
        print("-" * 110)
        for pk, stats in results["per_pair_summary_statistics"].items():
            g_s = stats["grade_score"]
            c_s = stats["confidence"]
            e_s = stats["escalation"]
            g_str = f"{g_s['mean']:.2f}±{g_s['std']:.2f}"
            c_str = f"{c_s['mean']:.4f}±{c_s['std']:.4f}"
            m_str = f"{e_s['mode']} ({e_s['mode_count']}/{stats['confidence']['n']})"
            pct_str = f"{e_s['percent_agreement']:.1f}%"
            d_s = stats.get("discount_factor")
            d_cv_str = f"{d_s['cv']:.3f}" if (d_s and d_s['cv'] is not None) else "0.000"
            d_str = f"{d_s['mean']:.2f}±{d_s['std']:.2f} ({d_cv_str})" if d_s else "N/A"
            flag = " [UNSTABLE]" if not e_s["is_100_percent_stable"] else ""
            print(f"{pk:<35} | {g_str:<13} | {d_str:<18} | {c_str:<15} | {m_str:<15} | {pct_str:<8}{flag}")
    else:
        for pk, stats in results["per_pair_summary_statistics"].items():
            g_s = stats["grade_score"]
            c_s = stats["confidence"]
            e_s = stats["escalation"]
            g_str = f"{g_s['mean']:.2f}±{g_s['std']:.2f}"
            c_str = f"{c_s['mean']:.4f}±{c_s['std']:.4f}"
            m_str = f"{e_s['mode']} ({e_s['mode_count']}/{stats['confidence']['n']})"
            pct_str = f"{e_s['percent_agreement']:.1f}%"
            flag = " [UNSTABLE]" if not e_s["is_100_percent_stable"] else ""
            print(f"{pk:<35} | {g_str:<15} | {c_str:<15} | {m_str:<15} | {pct_str:<8}{flag}")

    print("-" * 90)
    unstable = results["unstable_pairs"]
    if unstable:
        print(f"Unstable Pairs (<100% agreement): {', '.join(unstable)}")
    else:
        print("Unstable Pairs (<100% agreement): NONE (100% categorical agreement across all pairs)")
    print(f"Confidence CV Range:      {results['cross_pair_summary']['confidence_cv_range']}")
    print(f"Grade Score CV Range:     {results['cross_pair_summary']['grade_score_cv_range']}")
    if results["cross_pair_summary"].get("discount_factor_cv_range"):
        print(f"Discount Factor CV Range: {results['cross_pair_summary']['discount_factor_cv_range']}")
    print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Experiment 1: Repeated-Run Stability Analysis")
    parser.add_argument("--smoke-test", action="store_true", help="Run 3 pairs x 3 repeats for rapid smoke testing")
    parser.add_argument("--repeats", type=int, default=10, help="Number of repetitions per pair (default: 10)")
    parser.add_argument("--pairs-limit", type=int, default=None, help="Limit number of pairs evaluated")
    parser.add_argument("--delay", type=float, default=4.2, help="Inter-call delay in seconds for API pacing (default: 4.2)")
    parser.add_argument("--output", type=Path, default=None, help="Path for JSON artifact")
    parser.add_argument("--scratch-dir", type=Path, default=None, help="Path for scratch cache directory")
    parser.add_argument("--enable-confounding", action="store_true", help="Enable ConfoundingTool assessment and discounting")
    parser.add_argument("--only-confounding-eligible", action="store_true", help="Scope experiment to pairs where prr_score > 0")
    args = parser.parse_args()

    if args.smoke_test:
        logger.info("Executing SMOKE TEST mode: 3 pairs x 3 repeats")
        results = run_repeated_stability_experiment(
            repeats=3,
            pairs_limit=3,
            inter_call_delay=args.delay,
            scratch_dir=args.scratch_dir,
            output_file=args.output,
            enable_confounding=args.enable_confounding,
            only_confounding_eligible=args.only_confounding_eligible,
        )
    else:
        results = run_repeated_stability_experiment(
            repeats=args.repeats,
            pairs_limit=args.pairs_limit,
            inter_call_delay=args.delay,
            scratch_dir=args.scratch_dir,
            output_file=args.output,
            enable_confounding=args.enable_confounding,
            only_confounding_eligible=args.only_confounding_eligible,
        )

    print_summary_report(results)


if __name__ == "__main__":
    main()