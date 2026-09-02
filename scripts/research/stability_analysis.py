"""
Leave-One-Out (LOO) Stability Analysis for PharmaGuard.

Evaluates metric stability under systematic single-pair ablation across the
frozen 15 benchmark pairs without pipeline re-execution.
Reuses metric computation logic directly from scripts/evaluator.py.

Owner: Krishna Sikheriya (IIT2023139)
"""

import json
import logging
import math
from pathlib import Path
import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pharmaguard.agent.output_schema import TriageReport
from scripts.evaluator import calc_metrics, compute_confusion_matrix, load_ground_truth

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_stability_analysis(outputs_dir: Path = None, gt_path: Path = None) -> dict:
    if outputs_dir is None:
        outputs_dir = REPO_ROOT / "outputs" / "core"
    if gt_path is None:
        gt_path = REPO_ROOT / "pharmaguard" / "data" / "ground_truth.json"

    ground_truth = load_ground_truth(gt_path)
    if not ground_truth:
        raise ValueError(f"No ground truth records loaded from {gt_path}")

    # Load the 15 production reports
    report_files = sorted(list(outputs_dir.glob("eval-run-*_report.json")))
    if not report_files:
        raise FileNotFoundError(f"No evaluation reports found in {outputs_dir}")

    records = []
    for r_file in report_files:
        with open(r_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            report = TriageReport(**data)

        key = f"{report.drug}::{report.event}"
        if key not in ground_truth:
            continue

        gt_entry = ground_truth[key]
        expected = gt_entry["expected_escalation"]
        actual = (
            report.triage.escalation.value
            if hasattr(report.triage.escalation, "value")
            else str(report.triage.escalation)
        )
        category = gt_entry.get("category", "unknown")

        records.append({
            "key": key,
            "drug": report.drug,
            "event": report.event,
            "category": category,
            "expected": expected,
            "actual": actual,
            "is_gt_positive": expected == "ESCALATE",
        })

    if len(records) < 2:
        raise ValueError(f"Insufficient records ({len(records)}) for LOO analysis.")

    # 1. Full-set baseline metrics
    strict_cm, lenient_cm = compute_confusion_matrix(records)
    base_sp, base_sr, base_ss, base_sf1 = calc_metrics(strict_cm)
    base_lp, base_lr, base_ls, base_lf1 = calc_metrics(lenient_cm)

    baseline_metrics = {
        "n_pairs": len(records),
        "strict": {
            "TP": strict_cm["TP"], "FP": strict_cm["FP"],
            "TN": strict_cm["TN"], "FN": strict_cm["FN"],
            "precision": round(base_sp, 4),
            "recall": round(base_sr, 4),
            "specificity": round(base_ss, 4),
            "f1": round(base_sf1, 4),
        },
        "lenient": {
            "TP": lenient_cm["TP"], "FP": lenient_cm["FP"],
            "TN": lenient_cm["TN"], "FN": lenient_cm["FN"],
            "precision": round(base_lp, 4),
            "recall": round(base_lr, 4),
            "specificity": round(base_ls, 4),
            "f1": round(base_lf1, 4),
        },
    }

    # 2. Leave-one-out iterations
    loo_results = []
    strict_p_list = []
    strict_r_list = []
    strict_s_list = []
    strict_f1_list = []

    lenient_p_list = []
    lenient_r_list = []
    lenient_s_list = []
    lenient_f1_list = []

    for i in range(len(records)):
        dropped_record = records[i]
        subset = records[:i] + records[i + 1:]

        s_cm, l_cm = compute_confusion_matrix(subset)
        sp, sr, ss, sf1 = calc_metrics(s_cm)
        lp, lr, ls, lf1 = calc_metrics(l_cm)

        strict_p_list.append(sp)
        strict_r_list.append(sr)
        strict_s_list.append(ss)
        strict_f1_list.append(sf1)

        lenient_p_list.append(lp)
        lenient_r_list.append(lr)
        lenient_s_list.append(ls)
        lenient_f1_list.append(lf1)

        delta_sf1 = sf1 - base_sf1
        delta_lf1 = lf1 - base_lf1

        loo_results.append({
            "dropped_pair": dropped_record["key"],
            "category": dropped_record["category"],
            "expected": dropped_record["expected"],
            "actual": dropped_record["actual"],
            "strict": {
                "precision": round(sp, 4),
                "recall": round(sr, 4),
                "specificity": round(ss, 4),
                "f1": round(sf1, 4),
                "delta_f1": round(delta_sf1, 4),
            },
            "lenient": {
                "precision": round(lp, 4),
                "recall": round(lr, 4),
                "specificity": round(ls, 4),
                "f1": round(lf1, 4),
                "delta_f1": round(delta_lf1, 4),
            },
        })

    # Summary statistics (mean ± sample SD)
    def mean_sd(vals: list[float]) -> dict:
        n = len(vals)
        mean_val = sum(vals) / n
        var = sum((x - mean_val) ** 2 for x in vals) / (n - 1) if n > 1 else 0.0
        sd_val = math.sqrt(var)
        return {
            "mean": round(mean_val, 4),
            "sd": round(sd_val, 4),
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
        }

    summary = {
        "strict": {
            "precision": mean_sd(strict_p_list),
            "recall": mean_sd(strict_r_list),
            "specificity": mean_sd(strict_s_list),
            "f1": mean_sd(strict_f1_list),
        },
        "lenient": {
            "precision": mean_sd(lenient_p_list),
            "recall": mean_sd(lenient_r_list),
            "specificity": mean_sd(lenient_s_list),
            "f1": mean_sd(lenient_f1_list),
        },
    }

    # Identify brittle pairs (causing largest absolute metric swing)
    max_strict_swing = max(abs(r["strict"]["delta_f1"]) for r in loo_results)
    max_lenient_swing = max(abs(r["lenient"]["delta_f1"]) for r in loo_results)

    brittle_strict = [
        r["dropped_pair"]
        for r in loo_results
        if abs(abs(r["strict"]["delta_f1"]) - max_strict_swing) < 1e-6
    ]
    brittle_lenient = [
        r["dropped_pair"]
        for r in loo_results
        if abs(abs(r["lenient"]["delta_f1"]) - max_lenient_swing) < 1e-6
    ]

    analysis_output = {
        "baseline_metrics": baseline_metrics,
        "summary": summary,
        "brittle_pairs": {
            "max_strict_f1_swing": round(max_strict_swing, 4),
            "strict_brittle_pairs": brittle_strict,
            "max_lenient_f1_swing": round(max_lenient_swing, 4),
            "lenient_brittle_pairs": brittle_lenient,
        },
        "loo_iterations": loo_results,
    }

    # Save to outputs/research/stability/loo_analysis.json
    out_dir = REPO_ROOT / "outputs" / "research" / "stability"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "loo_analysis.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(analysis_output, f, indent=2)
    logger.info(f"Saved LOO stability analysis to {out_file}")

    # Print markdown table
    print("\n" + "=" * 80)
    print("PHARMAGUARD LEAVE-ONE-OUT (LOO) STABILITY ANALYSIS (n=15)")
    print("=" * 80)
    print(
        f"Baseline Full Set (15 pairs): Strict F1 = {base_sf1:.3f} | Lenient F1 = {base_lf1:.3f}\n"
    )

    print(
        "| Dropped Pair | Category | Strict F1 | Δ Strict F1 | Lenient F1 | Δ Lenient F1 |"
    )
    print(
        "|:---|:---|:---:|:---:|:---:|:---:|"
    )
    for r in loo_results:
        s_f1_str = f"{r['strict']['f1']:.3f}"
        s_d_str = f"{r['strict']['delta_f1']:+.3f}"
        l_f1_str = f"{r['lenient']['f1']:.3f}"
        l_d_str = f"{r['lenient']['delta_f1']:+.3f}"
        print(
            f"| `{r['dropped_pair']}` | {r['category']} | {s_f1_str} | {s_d_str} | {l_f1_str} | {l_d_str} |"
        )

    print("\n### Summary Statistics Across 15 LOO Iterations (Mean ± SD)")
    print(
        f"- **Strict Metrics**:  Precision = {summary['strict']['precision']['mean']:.3f} ± {summary['strict']['precision']['sd']:.3f} | "
        f"Recall = {summary['strict']['recall']['mean']:.3f} ± {summary['strict']['recall']['sd']:.3f} | "
        f"Specificity = {summary['strict']['specificity']['mean']:.3f} ± {summary['strict']['specificity']['sd']:.3f} | "
        f"F1 = {summary['strict']['f1']['mean']:.3f} ± {summary['strict']['f1']['sd']:.3f}"
    )
    print(
        f"- **Lenient Metrics**: Precision = {summary['lenient']['precision']['mean']:.3f} ± {summary['lenient']['precision']['sd']:.3f} | "
        f"Recall = {summary['lenient']['recall']['mean']:.3f} ± {summary['lenient']['recall']['sd']:.3f} | "
        f"Specificity = {summary['lenient']['specificity']['mean']:.3f} ± {summary['lenient']['specificity']['sd']:.3f} | "
        f"F1 = {summary['lenient']['f1']['mean']:.3f} ± {summary['lenient']['f1']['sd']:.3f}"
    )

    print("\n### Sensitivity / Brittle Pair Analysis")
    print(
        f"- **Strict F1 Max Swing**: {max_strict_swing:+.3f} caused by dropping: {', '.join(f'`{p}`' for p in brittle_strict)}"
    )
    print(
        f"- **Lenient F1 Max Swing**: {max_lenient_swing:+.3f} caused by dropping: {', '.join(f'`{p}`' for p in brittle_lenient)}"
    )
    print("=" * 80 + "\n")

    return analysis_output


if __name__ == "__main__":
    run_stability_analysis()