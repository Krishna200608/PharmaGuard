"""
scripts/research/error_taxonomy.py - PharmaGuard Error & Edge-Case Taxonomy.

Synthesizes and classifies observed system behaviors, boundary cases, and failure modes
into a formal, evidence-backed taxonomy derived programmatically from existing repo artifacts:
  1. MECHANISTIC_UNCERTAINTY: Strict FN/FP driven by genuine biological plausibility uncertainty.
  2. CONFOUNDED_SIGNAL: FAERS disproportionality driven by clinical polypharmacy.
  3. CROSS_SOURCE_DISCORDANCE: Pairs with wide spread across evidence modalities.
  4. LLM_MEMORIZATION_LEAKAGE: Pairs/cases where critic flagged regulatory/epidemiological leakage.
  5. GATE_ARTIFACT: Pairs where zeroing FAERS triggered NO_SIGNAL safety gate as an artifact.
  6. AGENT_ARCHITECTURE_DIVERGENCE: Pairs where ReAct freeform synthesis diverged from deterministic gating.
  7. ZERO_REPORT_EDGE_CASE: Curated synthetic/extreme pairs with 0 FAERS reports (structural).

Owner: Krishna Sikheriya (IIT2023139)
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pharmaguard.agent.output_schema import compute_source_agreement

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("error_taxonomy")

DEFAULT_OUTPUT_FILE = REPO_ROOT / "outputs" / "research" / "error_taxonomy" / "taxonomy_results.json"

TAXONOMY_CATEGORIES = [
    "MECHANISTIC_UNCERTAINTY",
    "CONFOUNDED_SIGNAL",
    "CROSS_SOURCE_DISCORDANCE",
    "LLM_MEMORIZATION_LEAKAGE",
    "GATE_ARTIFACT",
    "AGENT_ARCHITECTURE_DIVERGENCE",
    "ZERO_REPORT_EDGE_CASE",
]


def load_source_artifacts(repo_root: Path) -> Dict[str, Any]:
    """
    Dynamically load all empirical artifacts required for taxonomy classification.
    """
    # 1. Ground Truth
    gt_file = repo_root / "pharmaguard" / "data" / "ground_truth.json"
    if not gt_file.exists():
        raise FileNotFoundError(f"Missing ground truth file: {gt_file}")
    with open(gt_file, "r", encoding="utf-8") as f:
        gt_data = json.load(f)
    gt_map = {f"{p['drug_canonical']}::{p['event_meddra_pt']}": p for p in gt_data["pairs"]}

    # 2. Production Evaluation Reports
    outputs_dir = repo_root / "outputs"
    core_dir = outputs_dir / "core"
    report_dir = core_dir if core_dir.exists() else outputs_dir
    prod_reports = {}
    for rf in sorted(report_dir.glob("eval-run-*_report.json")):
        with open(rf, "r", encoding="utf-8") as f:
            d = json.load(f)
        pk = f"{d['drug']}::{d['event']}"
        prod_reports[pk] = d

    # 3. Leakage Critic Probe Results
    critic_file = outputs_dir / "experiments" / "critic_probe" / "leakage_critique_results.json"
    if not critic_file.exists():
        critic_file = outputs_dir / "critic_probe" / "leakage_critique_results.json"
    critic_cases = {}
    if critic_file.exists():
        with open(critic_file, "r", encoding="utf-8") as f:
            c_data = json.load(f)
        for c in c_data.get("probe_cases", []):
            pk = f"{c['drug']}::{c['event']}"
            eval_dict = c.get("critic_evaluation", {})
            if eval_dict.get("leaked"):
                critic_cases[pk] = {
                    "drug": c["drug"],
                    "event": c["event"],
                    "reference": c.get("reference_section"),
                    "phrases": eval_dict.get("leak_phrases", []),
                    "downgraded_score": eval_dict.get("mechanistic_only_score", "LOW"),
                }

    # 4. Confounding Stability & Self-Probe Results
    conf_stability_file = outputs_dir / "research" / "stability" / "repeated_run_variance_confounding.json"
    conf_stability = {}
    if conf_stability_file.exists():
        with open(conf_stability_file, "r", encoding="utf-8") as f:
            cs_data = json.load(f)
        for pk, s in cs_data.get("per_pair_summary_statistics", {}).items():
            conf_stability[pk] = s.get("discount_factor", {})

    conf_probe_file = outputs_dir / "experiments" / "confounding_probe" / "confounding_self_probe.json"
    if not conf_probe_file.exists():
        conf_probe_file = outputs_dir / "confounding_probe" / "confounding_self_probe.json"
    conf_probes = {}
    if conf_probe_file.exists():
        with open(conf_probe_file, "r", encoding="utf-8") as f:
            cp_data = json.load(f)
        for p in cp_data.get("probe_cases", []):
            pk = f"{p['drug']}::{p['event']}"
            ass = p.get("assessment", {})
            conf_probes[pk] = {
                "drug": p["drug"],
                "event": p["event"],
                "is_confounded": ass.get("is_confounded"),
                "discount_factor": ass.get("discount_factor"),
                "drugs": ass.get("confounding_drugs", []),
            }

    # 5. Source Ablation Gate Artifacts
    ablation_file = outputs_dir / "research" / "source_ablation" / "ablation_results.json"
    gate_artifact_pairs = set()
    if ablation_file.exists():
        with open(ablation_file, "r", encoding="utf-8") as f:
            abl_data = json.load(f)
        for pk, c_dict in abl_data.get("per_pair_ablation", {}).items():
            if c_dict.get("faers_removed_gate_applied", {}).get("is_gate_artifact"):
                gate_artifact_pairs.add(pk)

    # 6. ReAct Agent Divergence Audit
    react_report_file = outputs_dir / "experiments" / "react_agent" / "agreement_report.json"
    if not react_report_file.exists():
        react_report_file = outputs_dir / "react_agent_agreement_report.json"
    react_divergent_pairs = {}
    if react_report_file.exists():
        with open(react_report_file, "r", encoding="utf-8") as f:
            rd_data = json.load(f)
        for p in rd_data.get("pairs", []):
            if p.get("agreement") == "MISMATCH":
                react_divergent_pairs[p["drug_event"]] = p

    return {
        "ground_truth": gt_map,
        "production_reports": prod_reports,
        "critic_cases": critic_cases,
        "conf_stability": conf_stability,
        "conf_probes": conf_probes,
        "gate_artifact_pairs": gate_artifact_pairs,
        "react_divergent_pairs": react_divergent_pairs,
    }


def classify_pair(
    pk: str,
    p_gt: Optional[Dict[str, Any]],
    sources: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Classify a single drug-event pair across the taxonomy with concrete evidence citations.
    """
    categories: List[str] = []
    evidence_dict: Dict[str, str] = {}

    prod_reports = sources["production_reports"]
    critic_cases = sources["critic_cases"]
    conf_stability = sources["conf_stability"]
    conf_probes = sources["conf_probes"]
    gate_artifact_pairs = sources["gate_artifact_pairs"]
    react_divergent_pairs = sources["react_divergent_pairs"]

    # 1. ZERO_REPORT_EDGE_CASE
    if p_gt and p_gt.get("category") == "zero_report_edge_case":
        categories.append("ZERO_REPORT_EDGE_CASE")
        evidence_dict["ZERO_REPORT_EDGE_CASE"] = (
            "pharmaguard/data/ground_truth.json: Curated zero-report edge case testing FAERS NO_SIGNAL short-circuit."
        )

    # 2. MECHANISTIC_UNCERTAINTY
    if p_gt and pk in prod_reports:
        rep = prod_reports[pk]
        exp = p_gt["expected_escalation"]
        act = rep["triage"]["escalation"]
        plaus = rep["mechanism"]["plausibility_score"]
        conf = rep["triage"]["confidence"]
        # Strict False Negative driven by low biological plausibility despite other evidence
        if exp == "ESCALATE" and act != "ESCALATE" and plaus <= 0.5:
            categories.append("MECHANISTIC_UNCERTAINTY")
            evidence_dict["MECHANISTIC_UNCERTAINTY"] = (
                f"outputs/core/eval-run-*_report.json: Strict False Negative (expected ESCALATE, actual {act}; "
                f"confidence={conf:.4f} < 0.70 driven by low biological plausibility={plaus})."
            )

    # 3. CONFOUNDED_SIGNAL
    if pk in conf_stability:
        disc = conf_stability[pk].get("mean", 1.0)
        if disc <= 0.50:
            categories.append("CONFOUNDED_SIGNAL")
            evidence_dict["CONFOUNDED_SIGNAL"] = (
                f"outputs/research/stability/repeated_run_variance_confounding.json: Severe polypharmacy confounding "
                f"discount (mean discount_factor={disc:.2f} <= 0.50; DECISIONS.md §21, §28)."
            )
    elif pk in conf_probes and conf_probes[pk].get("is_confounded"):
        disc = conf_probes[pk].get("discount_factor", 1.0)
        drugs = conf_probes[pk].get("drugs", [])
        drugs_str = f" ({', '.join(drugs[:2])})" if drugs else ""
        categories.append("CONFOUNDED_SIGNAL")
        evidence_dict["CONFOUNDED_SIGNAL"] = (
            f"outputs/experiments/confounding_probe/confounding_self_probe.json: Confounding self-probe identified polypharmacy "
            f"co-medication{drugs_str} (discount_factor={disc:.2f}; DECISIONS.md §28)."
        )

    # 4. CROSS_SOURCE_DISCORDANCE
    if pk in prod_reports:
        rep = prod_reports[pk]
        prr_s = rep["signal_stats"]["prr_score"]
        gr_s = rep["literature"]["grade_score"]
        pl_s = rep["mechanism"]["plausibility_score"]
        agr = compute_source_agreement(prr_s, gr_s, pl_s)
        if agr == "DISCORDANT":
            categories.append("CROSS_SOURCE_DISCORDANCE")
            scores = [prr_s, gr_s, pl_s]
            evidence_dict["CROSS_SOURCE_DISCORDANCE"] = (
                f"scripts/dev/backfill_agreement.py / DECISIONS.md §26: Classified DISCORDANT "
                f"(max={max(scores):.2f}, min={min(scores):.2f}, spread >= 0.66 across modalities)."
            )

    # 5. LLM_MEMORIZATION_LEAKAGE
    if pk in critic_cases:
        c_eval = critic_cases[pk]
        phrases = c_eval.get("phrases", [])
        score = c_eval.get("downgraded_score", "LOW")
        categories.append("LLM_MEMORIZATION_LEAKAGE")
        phrase_preview = f"'{phrases[0]}'" if phrases else "regulatory citations"
        evidence_dict["LLM_MEMORIZATION_LEAKAGE"] = (
            f"outputs/experiments/critic_probe/leakage_critique_results.json / DECISIONS.md §27: Adversarial critic flagged "
            f"regulatory/epidemiological leakage ({phrase_preview}); score downgraded to {score}."
        )

    # 6. GATE_ARTIFACT
    if pk in gate_artifact_pairs:
        categories.append("GATE_ARTIFACT")
        evidence_dict["GATE_ARTIFACT"] = (
            "outputs/research/source_ablation/ablation_results.json: Zeroing FAERS in multi-source ablation "
            "triggered Gate 1 (NO_SIGNAL) as an artificial zeroing artifact rather than a true biological absence."
        )

    # 7. AGENT_ARCHITECTURE_DIVERGENCE
    if pk in react_divergent_pairs:
        r_info = react_divergent_pairs[pk]
        categories.append("AGENT_ARCHITECTURE_DIVERGENCE")
        evidence_dict["AGENT_ARCHITECTURE_DIVERGENCE"] = (
            f"outputs/experiments/react_agent/agreement_report.json / DECISIONS.md §24: ReAct agent stated recommendation "
            f"'{r_info['agent_stated_raw']}' diverged from deterministic pipeline reported escalation "
            f"'{r_info['reported_escalation']}'."
        )

    return {
        "categories": categories,
        "evidence": evidence_dict,
    }


def build_error_taxonomy(repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Build complete error taxonomy across both the 15 benchmark pairs and supplementary diagnostic probe cases.
    """
    if repo_root is None:
        repo_root = REPO_ROOT

    sources = load_source_artifacts(repo_root)
    gt_map = sources["ground_truth"]

    benchmark_classifications: Dict[str, Any] = {}
    for pk, p_gt in gt_map.items():
        res = classify_pair(pk, p_gt, sources)
        benchmark_classifications[pk] = {
            "is_benchmark_pair": True,
            "ground_truth_category": p_gt.get("category"),
            "expected_escalation": p_gt.get("expected_escalation"),
            "categories": res["categories"],
            "evidence": res["evidence"],
        }

    # Supplementary Diagnostic Probes (Leakage & Confounding Cases outside benchmark)
    supplementary_classifications: Dict[str, Any] = {}
    extra_pairs: Set[str] = set()
    extra_pairs.update(sources["critic_cases"].keys())
    extra_pairs.update(sources["conf_probes"].keys())
    extra_pairs = extra_pairs - set(gt_map.keys())

    for pk in sorted(extra_pairs):
        res = classify_pair(pk, None, sources)
        supplementary_classifications[pk] = {
            "is_benchmark_pair": False,
            "ground_truth_category": "diagnostic_probe_case",
            "expected_escalation": None,
            "categories": res["categories"],
            "evidence": res["evidence"],
        }

    # Compute category counts
    benchmark_counts = {cat: 0 for cat in TAXONOMY_CATEGORIES}
    total_counts = {cat: 0 for cat in TAXONOMY_CATEGORIES}

    for item in benchmark_classifications.values():
        for cat in item["categories"]:
            benchmark_counts[cat] += 1
            total_counts[cat] += 1

    for item in supplementary_classifications.values():
        for cat in item["categories"]:
            total_counts[cat] += 1

    # Co-occurrence analysis
    multi_category_pairs = {
        pk: item["categories"]
        for pk, item in benchmark_classifications.items()
        if len(item["categories"]) > 1
    }

    payload = {
        "metadata": {
            "taxonomy_version": "1.0",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_benchmark_pairs": len(benchmark_classifications),
            "total_diagnostic_probe_cases": len(supplementary_classifications),
            "defined_categories": TAXONOMY_CATEGORIES,
        },
        "summary_counts": {
            "benchmark_pairs": benchmark_counts,
            "all_evaluated_cases": total_counts,
        },
        "multi_category_co_occurrences": multi_category_pairs,
        "benchmark_pairs": benchmark_classifications,
        "supplementary_probe_cases": supplementary_classifications,
    }

    return payload


def save_taxonomy_results(results: Dict[str, Any], output_file: Optional[Path] = None) -> Path:
    """Save taxonomy results payload to JSON file."""
    if output_file is None:
        output_file = DEFAULT_OUTPUT_FILE

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info("Saved taxonomy artifact to %s", output_file)
    return output_file


def print_taxonomy_summary(results: Dict[str, Any]):
    """Print an exhaustive, formatted summary of the taxonomy results."""
    print("\n" + "=" * 110)
    print("PHARMAGUARD EMPIRICAL ERROR & EDGE-CASE TAXONOMY (R1 SYNTHESIS)")
    print("=" * 110)
    print(f"Total Benchmark Pairs:          {results['metadata']['total_benchmark_pairs']}")
    print(f"Total Supplementary Cases:      {results['metadata']['total_diagnostic_probe_cases']}")
    print("-" * 110)
    print(f"{'Category':<32} | {'Benchmark Count':<16} | {'Total Cases':<12} | {'Description'}")
    print("-" * 110)
    
    descriptions = {
        "MECHANISTIC_UNCERTAINTY": "Strict FN/FP driven by genuine biological plausibility uncertainty",
        "CONFOUNDED_SIGNAL": "FAERS disproportionality heavily inflated by polypharmacy (discount <= 0.50)",
        "CROSS_SOURCE_DISCORDANCE": "Disproportionate spread across modalities (max >= 0.66 & min <= 0.33)",
        "LLM_MEMORIZATION_LEAKAGE": "Adversarial critic detected postmarket/regulatory language leakage",
        "GATE_ARTIFACT": "Zeroing FAERS triggered Gate 1 (NO_SIGNAL) as an artificial zeroing artifact",
        "AGENT_ARCHITECTURE_DIVERGENCE": "Unconstrained ReAct synthesis diverged from deterministic reported escalation",
        "ZERO_REPORT_EDGE_CASE": "Curated structural zero-report controls testing safety gate short-circuit",
    }

    for cat in TAXONOMY_CATEGORIES:
        b_cnt = results["summary_counts"]["benchmark_pairs"].get(cat, 0)
        t_cnt = results["summary_counts"]["all_evaluated_cases"].get(cat, 0)
        print(f"{cat:<32} | {b_cnt:<16} | {t_cnt:<12} | {descriptions.get(cat, '')}")

    print("-" * 110)
    print("\n" + "=" * 110)
    print("PER-PAIR BENCHMARK CLASSIFICATION & MULTI-CATEGORY CO-OCCURRENCE")
    print("=" * 110)
    for pk, item in results["benchmark_pairs"].items():
        cats = item["categories"]
        cats_str = ", ".join(cats) if cats else "NONE (Routine concordant performance)"
        print(f"\n>> {pk}")
        print(f"   Categories [{len(cats)}]: {cats_str}")
        for c in cats:
            print(f"     - [{c}]: {item['evidence'].get(c)}")

    if results.get("supplementary_probe_cases"):
        print("\n" + "=" * 110)
        print("SUPPLEMENTARY DIAGNOSTIC PROBE CASES (EXTERNAL EVALUATIONS)")
        print("=" * 110)
        for pk, item in results["supplementary_probe_cases"].items():
            cats = item["categories"]
            cats_str = ", ".join(cats)
            print(f"\n>> {pk} (Probe)")
            print(f"   Categories [{len(cats)}]: {cats_str}")
            for c in cats:
                print(f"     - [{c}]: {item['evidence'].get(c)}")
    print("\n" + "=" * 110 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Build PharmaGuard Error & Edge-Case Taxonomy")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE, help="Path for JSON artifact")
    args = parser.parse_args()

    results = build_error_taxonomy()
    save_taxonomy_results(results, args.output)
    print_taxonomy_summary(results)


if __name__ == "__main__":
    main()