"""
Evaluator for PharmaGuard Triage Reports.
Calculates Strict and Lenient metrics against ground_truth.json.

Confidence intervals: bootstrap resampling (1000 iterations, 95% CI).
Rationale for bootstrap over Wilson score: Wilson applies cleanly to a single
proportion (e.g. bare recall = TP/(TP+FN)), but precision, F1, and specificity
are computed from *jointly dependent* TP/FP/TN/FN counts across the same n=15
sample. Bootstrap treats the 15 (prediction, ground-truth) pairs as the empirical
distribution, resamples with replacement, and propagates uncertainty through all
metric formulas simultaneously -- capturing the joint covariance that Wilson would
ignore. At n=15 this is the standard choice; the resampling distribution is
reported as the 2.5th--97.5th percentile interval.
"""
import argparse
import json
import logging
import random
from pathlib import Path
from pydantic import ValidationError
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from pharmaguard.agent.output_schema import TriageReport

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def load_ground_truth(gt_path: Path) -> dict:
    if not gt_path.exists():
        logger.error(f"Ground truth file not found: {gt_path}")
        return {}
    with open(gt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Return as dict keyed by canonical drug/event pair
    return {f"{pair['drug_canonical']}::{pair['event_meddra_pt']}": pair for pair in data.get("pairs", [])}

BOOTSTRAP_N = 1000
BOOTSTRAP_SEED = 42
CI_ALPHA = 0.05  # 95% confidence interval


def bootstrap_ci(
    observations: list[tuple[bool, bool]],  # list of (is_gt_positive, is_predicted_positive)
    n_iter: int = BOOTSTRAP_N,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, tuple[float, float]]:
    """
    Bootstrap 95% CI for precision, recall, specificity, and F1.

    Each observation is a (is_gt_positive, is_predicted_positive) pair.
    Resamples with replacement n_iter times; returns the 2.5th-97.5th
    percentile interval for each metric.

    NOTE: at n=15 the bootstrap distribution is granular (precision can only
    take values k/15 for small k), so CIs are coarse by nature of the sample
    size, not a limitation of the method. This is the honest result to report.
    """
    rng = random.Random(seed)
    n = len(observations)
    precisions, recalls, specificities, f1s = [], [], [], []

    for _ in range(n_iter):
        sample = [observations[rng.randint(0, n - 1)] for _ in range(n)]
        tp = sum(1 for gt, pred in sample if gt and pred)
        fp = sum(1 for gt, pred in sample if not gt and pred)
        tn = sum(1 for gt, pred in sample if not gt and not pred)
        fn = sum(1 for gt, pred in sample if gt and not pred)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        precisions.append(prec)
        recalls.append(rec)
        specificities.append(spec)
        f1s.append(f1)

    def percentile(data: list[float], pct: float) -> float:
        data_sorted = sorted(data)
        idx = (pct / 100) * (len(data_sorted) - 1)
        lo, hi = int(idx), min(int(idx) + 1, len(data_sorted) - 1)
        return data_sorted[lo] + (idx - lo) * (data_sorted[hi] - data_sorted[lo])

    lo_pct = CI_ALPHA / 2 * 100
    hi_pct = (1 - CI_ALPHA / 2) * 100
    return {
        "precision":    (percentile(precisions,    lo_pct), percentile(precisions,    hi_pct)),
        "recall":       (percentile(recalls,        lo_pct), percentile(recalls,        hi_pct)),
        "specificity":  (percentile(specificities,  lo_pct), percentile(specificities,  hi_pct)),
        "f1":           (percentile(f1s,            lo_pct), percentile(f1s,            hi_pct)),
    }


def run_evaluation(outputs_dir: Path = None, title: str = "PharmaGuard"):
    project_root = Path(__file__).resolve().parents[1]
    gt_path = project_root / "pharmaguard" / "data" / "ground_truth.json"
    if outputs_dir is None:
        outputs_dir = project_root / "outputs"
    
    ground_truth = load_ground_truth(gt_path)
    if not ground_truth:
        return

    # Track metrics
    strict_metrics = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    lenient_metrics = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    over_caution_count = 0
    negative_control_count = 0

    # Per-pair (is_gt_positive, is_predicted_positive) observations for bootstrap
    strict_obs: list[tuple[bool, bool]] = []
    lenient_obs: list[tuple[bool, bool]] = []

    evaluated_pairs = set()
    category_metrics = {}
    disagreements = []

    if not outputs_dir.exists():
        logger.error(f"Outputs directory not found: {outputs_dir}")
        return

    for report_file in outputs_dir.glob("eval-run-*_report.json"):
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                report = TriageReport(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Failed to parse report {report_file}: {e}")
            continue
            
        key = f"{report.drug}::{report.event}"
        
        if key not in ground_truth:
            continue
            
        gt_entry = ground_truth[key]
        expected = gt_entry["expected_escalation"]
        actual = report.triage.escalation.value if hasattr(report.triage.escalation, 'value') else report.triage.escalation
        category = gt_entry.get("category", "unknown")
        
        evaluated_pairs.add(key)
        
        is_gt_positive = expected == "ESCALATE"
        is_gt_negative = expected == "DO_NOT_ESCALATE"
        
        is_strict_positive = actual == "ESCALATE"
        is_lenient_positive = actual in ("ESCALATE", "MONITOR")
        
        if expected != actual:
            disagreements.append({"pair": key, "category": category, "expected": expected, "actual": actual})
            
        if category not in category_metrics:
            category_metrics[category] = {"strict": {"TP":0, "FP":0, "TN":0, "FN":0}, "lenient": {"TP":0, "FP":0, "TN":0, "FN":0}, "count": 0}
            
        category_metrics[category]["count"] += 1
        
        # Strict logic update
        if is_gt_positive:
            if is_strict_positive:
                strict_metrics["TP"] += 1
                category_metrics[category]["strict"]["TP"] += 1
            else:
                strict_metrics["FN"] += 1
                category_metrics[category]["strict"]["FN"] += 1
        else:
            if is_strict_positive:
                strict_metrics["FP"] += 1
                category_metrics[category]["strict"]["FP"] += 1
            else:
                strict_metrics["TN"] += 1
                category_metrics[category]["strict"]["TN"] += 1
        strict_obs.append((is_gt_positive, is_strict_positive))

        # Lenient logic update
        if is_gt_positive:
            if is_lenient_positive:
                lenient_metrics["TP"] += 1
                category_metrics[category]["lenient"]["TP"] += 1
            else:
                lenient_metrics["FN"] += 1
                category_metrics[category]["lenient"]["FN"] += 1
        else:
            if is_lenient_positive:
                lenient_metrics["FP"] += 1
                category_metrics[category]["lenient"]["FP"] += 1
            else:
                lenient_metrics["TN"] += 1
                category_metrics[category]["lenient"]["TN"] += 1
        lenient_obs.append((is_gt_positive, is_lenient_positive))
                
        # Over-caution tracking
        if is_gt_negative:
            negative_control_count += 1
            if actual == "MONITOR":
                over_caution_count += 1

    missing = set(ground_truth.keys()) - evaluated_pairs
    if missing:
        logger.warning(f"Missing reports for {len(missing)} pairs: {missing}")

    print("=" * 60)
    print(f"{title} Evaluation Report")
    print(f"Pairs evaluated: {len(evaluated_pairs)} / {len(ground_truth)}")
    print("=" * 60)
    
    def calc_metrics(m):
        tp, fp, tn, fn = m["TP"], m["FP"], m["TN"], m["FN"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        return precision, recall, specificity, f1
        
    p, r, s, f1 = calc_metrics(strict_metrics)
    print(f"\n--- STRICT METRICS (Primary) ---")
    print(f"TP: {strict_metrics['TP']}, FP: {strict_metrics['FP']}, TN: {strict_metrics['TN']}, FN: {strict_metrics['FN']}")
    print(f"Precision  : {p:.3f}")
    print(f"Recall     : {r:.3f}")
    print(f"Specificity: {s:.3f}")
    print(f"F1-Score   : {f1:.3f}")

    p_l, r_l, s_l, f1_l = calc_metrics(lenient_metrics)
    print(f"\n--- LENIENT METRICS (Secondary) ---")
    print(f"TP: {lenient_metrics['TP']}, FP: {lenient_metrics['FP']}, TN: {lenient_metrics['TN']}, FN: {lenient_metrics['FN']}")
    print(f"Precision  : {p_l:.3f}")
    print(f"Recall     : {r_l:.3f}")
    print(f"Specificity: {s_l:.3f}")
    print(f"F1-Score   : {f1_l:.3f}")
    
    print(f"\n--- CATEGORY BREAKDOWN ---")
    for cat, data in category_metrics.items():
        print(f"\nCategory: {cat} (Count: {data['count']})")
        cp, cr, cs, cf1 = calc_metrics(data['strict'])
        print(f"  Strict -> TP: {data['strict']['TP']}, FP: {data['strict']['FP']}, TN: {data['strict']['TN']}, FN: {data['strict']['FN']} | P: {cp:.2f}, R: {cr:.2f}, S: {cs:.2f}")
        lp, lr, ls, lf1 = calc_metrics(data['lenient'])
        print(f"  Lenient-> TP: {data['lenient']['TP']}, FP: {data['lenient']['FP']}, TN: {data['lenient']['TN']}, FN: {data['lenient']['FN']} | P: {lp:.2f}, R: {lr:.2f}, S: {ls:.2f}")

    print(f"\n--- BOOTSTRAP 95% CONFIDENCE INTERVALS (n={len(evaluated_pairs)}, {BOOTSTRAP_N} iterations) ---")
    print(f"Method: percentile bootstrap, seed={BOOTSTRAP_SEED}.")
    print(f"Note: at n=15 the CI grid is coarse (metrics take k/15 values); CIs reflect genuine")
    print(f"      small-sample uncertainty, not a method limitation.")
    s_ci = bootstrap_ci(strict_obs)
    l_ci = bootstrap_ci(lenient_obs)
    print(f"\n  Strict  Precision  : {p:.3f}  95% CI [{s_ci['precision'][0]:.3f}, {s_ci['precision'][1]:.3f}]")
    print(f"  Strict  Recall     : {r:.3f}  95% CI [{s_ci['recall'][0]:.3f}, {s_ci['recall'][1]:.3f}]")
    print(f"  Strict  Specificity: {s:.3f}  95% CI [{s_ci['specificity'][0]:.3f}, {s_ci['specificity'][1]:.3f}]")
    print(f"  Strict  F1-Score   : {f1:.3f}  95% CI [{s_ci['f1'][0]:.3f}, {s_ci['f1'][1]:.3f}]")
    print(f"  Lenient Precision  : {p_l:.3f}  95% CI [{l_ci['precision'][0]:.3f}, {l_ci['precision'][1]:.3f}]")
    print(f"  Lenient Recall     : {r_l:.3f}  95% CI [{l_ci['recall'][0]:.3f}, {l_ci['recall'][1]:.3f}]")
    print(f"  Lenient Specificity: {s_l:.3f}  95% CI [{l_ci['specificity'][0]:.3f}, {l_ci['specificity'][1]:.3f}]")
    print(f"  Lenient F1-Score   : {f1_l:.3f}  95% CI [{l_ci['f1'][0]:.3f}, {l_ci['f1'][1]:.3f}]")

    print(f"\n--- FAILURE MODES ---")
    oc_rate = over_caution_count / negative_control_count if negative_control_count > 0 else 0.0
    print(f"Over-Caution Rate (MONITOR on known negatives): {oc_rate:.1%} ({over_caution_count}/{negative_control_count})")
    
    print(f"\n--- DISAGREEMENTS (Expected != Actual) ---")
    if not disagreements:
        print("None! Perfect agreement.")
    else:
        for d in disagreements:
            print(f"- {d['pair']} ({d['category']}): Expected {d['expected']}, Got {d['actual']}")
            
    print("=" * 60)
    
    # Save a minimal summary report
    with open(outputs_dir / "evaluation_summary.txt", "w", encoding="utf-8") as f:
        f.write("Evaluation Summary complete.\n")
    logger.info(f"Saved summary to {outputs_dir / 'evaluation_summary.txt'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate PharmaGuard triage reports.")
    parser.add_argument(
        "--outputs-dir",
        type=Path,
        default=None,
        help="Directory containing eval-run-*_report.json files. Defaults to outputs/.",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="PharmaGuard",
        help="Label shown in the report header (e.g. 'PharmaGuard' or 'Baseline').",
    )
    args = parser.parse_args()
    run_evaluation(outputs_dir=args.outputs_dir, title=args.title)
