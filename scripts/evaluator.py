"""
Evaluator for PharmaGuard Triage Reports.
Calculates Strict and Lenient metrics against ground_truth.json.
"""
import argparse
import json
import logging
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

def calc_metrics(m: dict) -> tuple[float, float, float, float]:
    """Calculate (precision, recall, specificity, f1) from a confusion matrix dict."""
    tp, fp, tn, fn = m["TP"], m["FP"], m["TN"], m["FN"]
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, specificity, f1

def compute_confusion_matrix(evaluated_records: list[dict]) -> tuple[dict, dict]:
    """
    Compute strict and lenient confusion matrices from evaluated records.
    Each record must have:
      is_gt_positive: bool
      actual: str ("ESCALATE" | "MONITOR" | "DO_NOT_ESCALATE")
    Returns (strict_metrics, lenient_metrics).
    """
    strict_metrics = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    lenient_metrics = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    for r in evaluated_records:
        is_gt_pos = r["is_gt_positive"]
        act = r["actual"]
        is_s_pos = act == "ESCALATE"
        is_l_pos = act in ("ESCALATE", "MONITOR")
        
        if is_gt_pos:
            if is_s_pos:
                strict_metrics["TP"] += 1
            else:
                strict_metrics["FN"] += 1
            if is_l_pos:
                lenient_metrics["TP"] += 1
            else:
                lenient_metrics["FN"] += 1
        else:
            if is_s_pos:
                strict_metrics["FP"] += 1
            else:
                strict_metrics["TN"] += 1
            if is_l_pos:
                lenient_metrics["FP"] += 1
            else:
                lenient_metrics["TN"] += 1
    return strict_metrics, lenient_metrics

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

    # --- 95% Confidence Intervals ---
    # Method 1: Non-parametric bootstrap resampling (B=1000, seed=42)
    # Why Bootstrap: Resampling paired ground-truth/prediction observations preserves the joint
    # covariance between TP, FP, TN, and FN. Percentile intervals provide robust empirical
    # uncertainty bounds without assuming asymptotic normality on small sample sizes (n=15),
    # and provide a natural, unified formulation for non-linear composite metrics like F1-Score.
    #
    # Method 2: Wilson score interval (exact binomial proportion)
    # Why Wilson: Recommended exact analytical interval for small-n proportions (Brown et al., 2001)
    # where standard Wald/normal intervals fail near boundary conditions (0.0 / 1.0).
    import random
    import math
    import numpy as np

    def compute_wilson_ci(k, n, z=1.95996):
        if n == 0:
            return (0.0, 0.0)
        p_val = k / n
        denom = 1 + (z**2) / n
        center = (p_val + (z**2) / (2 * n)) / denom
        margin = (z * math.sqrt((p_val * (1 - p_val) / n) + (z**2) / (4 * n**2))) / denom
        return (max(0.0, center - margin), min(1.0, center + margin))

    # Reconstruct paired record list for bootstrap resampling
    pair_records = []
    for report_file in outputs_dir.glob("eval-run-*_report.json"):
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                rep = TriageReport(**d)
        except Exception:
            continue
        k = f"{rep.drug}::{rep.event}"
        if k in ground_truth:
            gt_e = ground_truth[k]
            act = rep.triage.escalation.value if hasattr(rep.triage.escalation, 'value') else rep.triage.escalation
            pair_records.append({
                "gt_pos": gt_e["expected_escalation"] == "ESCALATE",
                "pred_strict": act == "ESCALATE",
                "pred_lenient": act in ("ESCALATE", "MONITOR"),
            })

    random.seed(42)
    np.random.seed(42)
    n_resamples = 1000
    boot_strict = {"p": [], "r": [], "s": [], "f1": []}
    boot_lenient = {"p": [], "r": [], "s": [], "f1": []}
    n_rec = len(pair_records)

    if n_rec > 0:
        for _ in range(n_resamples):
            sample = [pair_records[random.randint(0, n_rec - 1)] for _ in range(n_rec)]
            for mode_dict, pred_k in [(boot_strict, "pred_strict"), (boot_lenient, "pred_lenient")]:
                tp = sum(1 for r in sample if r["gt_pos"] and r[pred_k])
                fp = sum(1 for r in sample if not r["gt_pos"] and r[pred_k])
                tn = sum(1 for r in sample if not r["gt_pos"] and not r[pred_k])
                fn = sum(1 for r in sample if r["gt_pos"] and not r[pred_k])
                prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
                f1_val = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
                mode_dict["p"].append(prec)
                mode_dict["r"].append(rec)
                mode_dict["s"].append(spec)
                mode_dict["f1"].append(f1_val)

    def get_ci_bounds(vals):
        if not vals:
            return (0.0, 0.0)
        return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))

    w_strict_p = compute_wilson_ci(strict_metrics["TP"], strict_metrics["TP"] + strict_metrics["FP"])
    w_strict_r = compute_wilson_ci(strict_metrics["TP"], strict_metrics["TP"] + strict_metrics["FN"])
    w_strict_s = compute_wilson_ci(strict_metrics["TN"], strict_metrics["TN"] + strict_metrics["FP"])

    w_lenient_p = compute_wilson_ci(lenient_metrics["TP"], lenient_metrics["TP"] + lenient_metrics["FP"])
    w_lenient_r = compute_wilson_ci(lenient_metrics["TP"], lenient_metrics["TP"] + lenient_metrics["FN"])
    w_lenient_s = compute_wilson_ci(lenient_metrics["TN"], lenient_metrics["TN"] + lenient_metrics["FP"])

    b_strict_p = get_ci_bounds(boot_strict["p"])
    b_strict_r = get_ci_bounds(boot_strict["r"])
    b_strict_s = get_ci_bounds(boot_strict["s"])
    b_strict_f1 = get_ci_bounds(boot_strict["f1"])

    b_lenient_p = get_ci_bounds(boot_lenient["p"])
    b_lenient_r = get_ci_bounds(boot_lenient["r"])
    b_lenient_s = get_ci_bounds(boot_lenient["s"])
    b_lenient_f1 = get_ci_bounds(boot_lenient["f1"])

    print(f"\n--- 95% CONFIDENCE INTERVALS (Bootstrap B=1000, Seed=42 / Wilson Score) ---")
    print(f"Strict:")
    print(f"  Precision  : {p:.3f}  [Bootstrap 95% CI: {b_strict_p[0]:.3f} - {b_strict_p[1]:.3f}]  [Wilson Score: {w_strict_p[0]:.3f} - {w_strict_p[1]:.3f}]")
    print(f"  Recall     : {r:.3f}  [Bootstrap 95% CI: {b_strict_r[0]:.3f} - {b_strict_r[1]:.3f}]  [Wilson Score: {w_strict_r[0]:.3f} - {w_strict_r[1]:.3f}]")
    print(f"  Specificity: {s:.3f}  [Bootstrap 95% CI: {b_strict_s[0]:.3f} - {b_strict_s[1]:.3f}]  [Wilson Score: {w_strict_s[0]:.3f} - {w_strict_s[1]:.3f}]")
    print(f"  F1-Score   : {f1:.3f}  [Bootstrap 95% CI: {b_strict_f1[0]:.3f} - {b_strict_f1[1]:.3f}]")
    print(f"Lenient:")
    print(f"  Precision  : {p_l:.3f}  [Bootstrap 95% CI: {b_lenient_p[0]:.3f} - {b_lenient_p[1]:.3f}]  [Wilson Score: {w_lenient_p[0]:.3f} - {w_lenient_p[1]:.3f}]")
    print(f"  Recall     : {r_l:.3f}  [Bootstrap 95% CI: {b_lenient_r[0]:.3f} - {b_lenient_r[1]:.3f}]  [Wilson Score: {w_lenient_r[0]:.3f} - {w_lenient_r[1]:.3f}]")
    print(f"  Specificity: {s_l:.3f}  [Bootstrap 95% CI: {b_lenient_s[0]:.3f} - {b_lenient_s[1]:.3f}]  [Wilson Score: {w_lenient_s[0]:.3f} - {w_lenient_s[1]:.3f}]")
    print(f"  F1-Score   : {f1_l:.3f}  [Bootstrap 95% CI: {b_lenient_f1[0]:.3f} - {b_lenient_f1[1]:.3f}]")
    
    print(f"\n--- CATEGORY BREAKDOWN ---")
    for cat, data in category_metrics.items():
        print(f"\nCategory: {cat} (Count: {data['count']})")
        cp, cr, cs, cf1 = calc_metrics(data['strict'])
        print(f"  Strict -> TP: {data['strict']['TP']}, FP: {data['strict']['FP']}, TN: {data['strict']['TN']}, FN: {data['strict']['FN']} | P: {cp:.2f}, R: {cr:.2f}, S: {cs:.2f}")
        lp, lr, ls, lf1 = calc_metrics(data['lenient'])
        print(f"  Lenient-> TP: {data['lenient']['TP']}, FP: {data['lenient']['FP']}, TN: {data['lenient']['TN']}, FN: {data['lenient']['FN']} | P: {lp:.2f}, R: {lr:.2f}, S: {ls:.2f}")

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
