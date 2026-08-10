"""
Evaluator for PharmaGuard Triage Reports.
Calculates Strict and Lenient metrics against ground_truth.json.
"""
import json
import logging
from pathlib import Path
from pydantic import ValidationError
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

def run_evaluation():
    project_root = Path(__file__).resolve().parent
    gt_path = project_root / "pharmaguard" / "data" / "ground_truth.json"
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

    if not outputs_dir.exists():
        logger.error(f"Outputs directory not found: {outputs_dir}")
        return

    for report_file in outputs_dir.glob("*_report.json"):
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                report = TriageReport(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Failed to parse report {report_file}: {e}")
            continue
            
        key = f"{report.drug}::{report.event}"
        
        if key not in ground_truth:
            # Pair not in ground truth, skip or just log
            continue
            
        gt_entry = ground_truth[key]
        expected = gt_entry["expected_escalation"]
        actual = report.triage.escalation
        
        evaluated_pairs.add(key)
        
        is_gt_positive = expected == "ESCALATE"
        is_gt_negative = expected == "DO_NOT_ESCALATE"
        
        # Strict logic:
        # ESCALATE -> predicted positive
        # MONITOR -> predicted negative
        # DO_NOT_ESCALATE -> predicted negative
        is_strict_positive = actual == "ESCALATE"
        
        if is_gt_positive:
            if is_strict_positive:
                strict_metrics["TP"] += 1
            else:
                strict_metrics["FN"] += 1
        else:
            if is_strict_positive:
                strict_metrics["FP"] += 1
            else:
                strict_metrics["TN"] += 1
                
        # Lenient logic:
        # ESCALATE -> predicted positive
        # MONITOR -> predicted positive
        # DO_NOT_ESCALATE -> predicted negative
        is_lenient_positive = actual in ("ESCALATE", "MONITOR")
        
        if is_gt_positive:
            if is_lenient_positive:
                lenient_metrics["TP"] += 1
            else:
                lenient_metrics["FN"] += 1
        else:
            if is_lenient_positive:
                lenient_metrics["FP"] += 1
            else:
                lenient_metrics["TN"] += 1
                
        # Over-caution tracking
        if is_gt_negative:
            negative_control_count += 1
            if actual == "MONITOR":
                over_caution_count += 1

    # Check for missing reports
    missing = set(ground_truth.keys()) - evaluated_pairs
    if missing:
        logger.warning(f"Missing reports for {len(missing)} pairs: {missing}")

    print("=" * 60)
    print(f"PharmaGuard Evaluation Report")
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
    
    print(f"\n--- FAILURE MODES ---")
    oc_rate = over_caution_count / negative_control_count if negative_control_count > 0 else 0.0
    print(f"Over-Caution Rate (MONITOR on known negatives): {oc_rate:.1%} ({over_caution_count}/{negative_control_count})")
    print("=" * 60)
    
    report_text = (
        f"PharmaGuard Evaluation Report\n"
        f"Pairs evaluated: {len(evaluated_pairs)} / {len(ground_truth)}\n\n"
        f"Strict Metrics:\nTP: {strict_metrics['TP']}, FP: {strict_metrics['FP']}, TN: {strict_metrics['TN']}, FN: {strict_metrics['FN']}\n"
        f"Precision={p:.3f}, Recall={r:.3f}, Specificity={s:.3f}, F1={f1:.3f}\n\n"
        f"Lenient Metrics:\nTP: {lenient_metrics['TP']}, FP: {lenient_metrics['FP']}, TN: {lenient_metrics['TN']}, FN: {lenient_metrics['FN']}\n"
        f"Precision={p_l:.3f}, Recall={r_l:.3f}, Specificity={s_l:.3f}, F1={f1_l:.3f}\n\n"
        f"Over-Caution Rate: {oc_rate:.1%} ({over_caution_count}/{negative_control_count})\n"
    )
    with open(outputs_dir / "evaluation_summary.txt", "w", encoding="utf-8") as f:
        f.write(report_text)
    
    logger.info(f"Saved summary to {outputs_dir / 'evaluation_summary.txt'}")

if __name__ == "__main__":
    run_evaluation()
