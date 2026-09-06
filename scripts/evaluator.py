"""
Evaluator for PharmaGuard Triage Reports.
Calculates Strict and Lenient metrics against ground_truth.json.
Includes therapeutic-area stratification based on WHO ATC classification (Phase 2).
"""
import argparse
import json
import logging
import math
import random
from pathlib import Path
from typing import Any, Optional
from pydantic import ValidationError
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np

from pharmaguard.agent.output_schema import TriageReport
from pharmaguard.tools.cache import ToolCache
from pharmaguard.tools.disease_context import (
    DiseaseContextTool,
    ATC_LEVEL_1_MAP,
)

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


def compute_wilson_ci(k: int, n: int, z: float = 1.95996) -> tuple[float, float]:
    """
    Calculate analytical Wilson score confidence interval for a binomial proportion k / n
    (Wilson, 1927; Brown, Cai & DasGupta, 2001).
    """
    if n == 0:
        return (0.0, 0.0)
    p_val = k / n
    denom = 1 + (z**2) / n
    center = (p_val + (z**2) / (2 * n)) / denom
    margin = (z * math.sqrt((p_val * (1 - p_val) / n) + (z**2) / (4 * n**2))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def compute_stratified_metrics(
    evaluated_records: list[dict],
    strata_key: str = "therapeutic_area_code",
) -> dict[str, Any]:
    """
    Compute stratified evaluation metrics (Strict and Lenient) grouped by strata_key.

    Parameters:
      evaluated_records: List of evaluated pair records. Each record dict must contain:
        - "is_gt_positive": bool
        - "actual": str ("ESCALATE" | "MONITOR" | "DO_NOT_ESCALATE")
        - strata_key (e.g. "therapeutic_area_code")
        - optionally "therapeutic_area", "pair", "drug"
      strata_key: The record attribute used for stratification grouping (default: "therapeutic_area_code").

    Returns:
      Dict mapping stratum code -> stratum metrics dictionary:
        - code: str
        - name: str
        - n: int
        - is_exploratory: bool (True if n < 5)
        - strict: dict with TP, FP, TN, FN, precision, recall, specificity, f1, Wilson CIs
        - lenient: dict with TP, FP, TN, FN, precision, recall, specificity, f1, Wilson CIs
        - records: list of pair identifiers
    """
    strata_groups: dict[str, list[dict]] = {}
    strata_names: dict[str, str] = {}

    for r in evaluated_records:
        s_val = r.get(strata_key) or "UNRESOLVED"
        if s_val not in strata_groups:
            strata_groups[s_val] = []
        strata_groups[s_val].append(r)
        if s_val not in strata_names:
            strata_names[s_val] = r.get("therapeutic_area") or ATC_LEVEL_1_MAP.get(s_val, f"Stratum {s_val}")

    results: dict[str, Any] = {}
    for s_code in sorted(strata_groups.keys()):
        group_recs = strata_groups[s_code]
        n_stratum = len(group_recs)
        is_exploratory = n_stratum < 5

        s_conf, l_conf = compute_confusion_matrix(group_recs)

        def _eval_tier(conf: dict) -> dict[str, Any]:
            tp, fp, tn, fn = conf["TP"], conf["FP"], conf["TN"], conf["FN"]
            pos_denom = tp + fp
            rec_denom = tp + fn
            spec_denom = tn + fp

            prec = tp / pos_denom if pos_denom > 0 else None
            rec = tp / rec_denom if rec_denom > 0 else None
            spec = tn / spec_denom if spec_denom > 0 else None

            if prec is not None and rec is not None and (prec + rec) > 0:
                f1_val = 2 * (prec * rec) / (prec + rec)
            else:
                f1_val = 0.0 if (prec is not None or rec is not None) else None

            prec_ci = compute_wilson_ci(tp, pos_denom) if pos_denom > 0 else None
            rec_ci = compute_wilson_ci(tp, rec_denom) if rec_denom > 0 else None
            spec_ci = compute_wilson_ci(tn, spec_denom) if spec_denom > 0 else None

            return {
                "TP": tp,
                "FP": fp,
                "TN": tn,
                "FN": fn,
                "precision": round(prec, 3) if prec is not None else None,
                "recall": round(rec, 3) if rec is not None else None,
                "specificity": round(spec, 3) if spec is not None else None,
                "f1": round(f1_val, 3) if f1_val is not None else None,
                "precision_ci": (round(prec_ci[0], 3), round(prec_ci[1], 3)) if prec_ci is not None else None,
                "recall_ci": (round(rec_ci[0], 3), round(rec_ci[1], 3)) if rec_ci is not None else None,
                "specificity_ci": (round(spec_ci[0], 3), round(spec_ci[1], 3)) if spec_ci is not None else None,
            }

        results[s_code] = {
            "code": s_code,
            "name": strata_names.get(s_code, s_code),
            "n": n_stratum,
            "is_exploratory": is_exploratory,
            "strict": _eval_tier(s_conf),
            "lenient": _eval_tier(l_conf),
            "records": [r.get("pair") for r in group_recs if r.get("pair")],
        }

    return results


def build_evaluated_records(
    reports: list[dict | Any],
    ground_truth: dict[str, Any],
    disease_tool: Optional[DiseaseContextTool] = None,
) -> tuple[list[dict], dict[str, Any]]:
    """
    Build structured evaluated records from a list of report dicts or TriageReport objects,
    annotating each record with WHO ATC Level 1 therapeutic area via DiseaseContextTool.

    Parameters:
      reports: List of report dictionaries or TriageReport instances.
      ground_truth: Ground truth mapping keyed by "drug::event".
      disease_tool: Optional DiseaseContextTool instance (defaults to cached local tool).

    Returns:
      (evaluated_records, drug_contexts)
    """
    if disease_tool is None:
        try:
            cache = ToolCache()
            disease_tool = DiseaseContextTool(cache=cache)
        except Exception as e:
            logger.warning(f"Could not initialize cached ToolCache for DiseaseContextTool: {e}")
            disease_tool = DiseaseContextTool()

    evaluated_records: list[dict] = []
    drug_contexts: dict[str, Any] = {}

    for item in reports:
        if isinstance(item, dict):
            drug = item.get("drug", "")
            event = item.get("event", "")
            triage_dict = item.get("triage", {})
            actual = triage_dict.get("escalation", "")
        else:
            drug = getattr(item, "drug", "")
            event = getattr(item, "event", "")
            triage_obj = getattr(item, "triage", None)
            if triage_obj:
                esc = getattr(triage_obj, "escalation", "")
                actual = esc.value if hasattr(esc, "value") else str(esc)
            else:
                actual = ""

        key = f"{drug}::{event}"
        if key not in ground_truth:
            continue

        gt_entry = ground_truth[key]
        expected = gt_entry.get("expected_escalation", "")
        category = gt_entry.get("category", "unknown")

        is_gt_positive = expected == "ESCALATE"
        is_gt_negative = expected == "DO_NOT_ESCALATE"

        if drug not in drug_contexts:
            drug_contexts[drug] = disease_tool.resolve(drug)
        ctx = drug_contexts[drug]

        evaluated_records.append({
            "pair": key,
            "drug": drug,
            "event": event,
            "expected": expected,
            "actual": actual,
            "category": category,
            "is_gt_positive": is_gt_positive,
            "is_gt_negative": is_gt_negative,
            "therapeutic_area_code": ctx.therapeutic_area_code or "UNRESOLVED",
            "therapeutic_area": ctx.therapeutic_area or "Unresolved Area",
            "utilization_class": ctx.utilization_class,
            "therapeutic_context": ctx.model_dump(),
        })

    return evaluated_records, drug_contexts


def compute_atc_coverage(
    evaluated_records: list[dict],
    drug_contexts: dict[str, Any],
) -> dict[str, Any]:
    """Compute ATC resolution coverage and multi-ATC metrics."""
    unique_drugs = sorted(set(r["drug"] for r in evaluated_records))
    total_drugs = len(unique_drugs)
    resolved_chembl = sum(1 for d in unique_drugs if drug_contexts.get(d) and drug_contexts[d].atc_source == "chembl_api")
    resolved_fallback = sum(1 for d in unique_drugs if drug_contexts.get(d) and drug_contexts[d].atc_source == "hardcoded_fallback")
    unresolved = sum(1 for d in unique_drugs if not drug_contexts.get(d) or not drug_contexts[d].is_resolved)
    pct_resolved = ((resolved_chembl + resolved_fallback) / total_drugs * 100.0) if total_drugs > 0 else 0.0
    multi_atc_count = sum(1 for d in unique_drugs if drug_contexts.get(d) and len(drug_contexts[d].all_atc_codes) > 1)
    multi_l1_count = sum(1 for d in unique_drugs if drug_contexts.get(d) and len(set(c[0] for c in drug_contexts[d].all_atc_codes)) > 1)

    return {
        "total_unique_drugs": total_drugs,
        "chembl_resolved": resolved_chembl,
        "fallback_resolved": resolved_fallback,
        "unresolved": unresolved,
        "resolution_percentage": round(pct_resolved, 1),
        "multi_atc_count": multi_atc_count,
        "multi_level1_count": multi_l1_count,
    }


def evaluate_therapeutic_strata(
    reports: list[dict | Any],
    ground_truth: dict[str, Any],
    disease_tool: Optional[DiseaseContextTool] = None,
) -> dict[str, Any]:
    """
    End-to-end convenience function to evaluate therapeutic-area strata from reports and ground truth.
    Returns dict:
      {
        "strata": dict[str, Any],       # Stratum code -> Stratum metrics
        "coverage": dict[str, Any],     # ATC coverage and resolution stats
        "records": list[dict],          # Annotated evaluated records
      }
    """
    records, drug_contexts = build_evaluated_records(reports, ground_truth, disease_tool=disease_tool)
    strata = compute_stratified_metrics(records, strata_key="therapeutic_area_code")
    coverage = compute_atc_coverage(records, drug_contexts)
    return {
        "strata": strata,
        "coverage": coverage,
        "records": records,
    }


def run_evaluation(
    outputs_dir: Path = None,
    title: str = "PharmaGuard",
    gt_path: Path = None,
    disease_tool: Optional[DiseaseContextTool] = None,
) -> Optional[dict[str, Any]]:
    project_root = Path(__file__).resolve().parents[1]
    if gt_path is None:
        gt_path = project_root / "pharmaguard" / "data" / "ground_truth.json"
    if outputs_dir is None:
        outputs_dir = project_root / "outputs" / "core"
        if not outputs_dir.exists():
            outputs_dir = project_root / "outputs"
    
    ground_truth = load_ground_truth(gt_path)
    if not ground_truth:
        return None

    # Disease context tool setup (cached)
    if disease_tool is None:
        try:
            cache = ToolCache()
            disease_tool = DiseaseContextTool(cache=cache)
        except Exception as e:
            logger.warning(f"Could not initialize cached ToolCache for DiseaseContextTool: {e}")
            disease_tool = DiseaseContextTool()

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
        return None

    raw_reports = []
    for report_file in sorted(outputs_dir.glob("eval-run-*_report.json")):
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                report = TriageReport(**data)
                raw_reports.append(report)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Failed to parse report {report_file}: {e}")
            continue

    evaluated_records, drug_contexts = build_evaluated_records(
        raw_reports, ground_truth, disease_tool=disease_tool
    )

    for r in evaluated_records:
        key = r["pair"]
        expected = r["expected"]
        actual = r["actual"]
        category = r["category"]
        is_gt_positive = r["is_gt_positive"]
        is_gt_negative = r["is_gt_negative"]

        evaluated_pairs.add(key)
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

    lines = []
    def emit(s: str = "") -> None:
        print(s)
        lines.append(s)

    emit("=" * 60)
    emit(f"{title} Evaluation Report")
    emit(f"Pairs evaluated: {len(evaluated_pairs)} / {len(ground_truth)}")
    emit("=" * 60)
    
    p, r, s, f1 = calc_metrics(strict_metrics)
    emit("\n--- STRICT METRICS (Primary) ---")
    emit(f"TP: {strict_metrics['TP']}, FP: {strict_metrics['FP']}, TN: {strict_metrics['TN']}, FN: {strict_metrics['FN']}")
    emit(f"Precision  : {p:.3f}")
    emit(f"Recall     : {r:.3f}")
    emit(f"Specificity: {s:.3f}")
    emit(f"F1-Score   : {f1:.3f}")

    p_l, r_l, s_l, f1_l = calc_metrics(lenient_metrics)
    emit("\n--- LENIENT METRICS (Secondary) ---")
    emit(f"TP: {lenient_metrics['TP']}, FP: {lenient_metrics['FP']}, TN: {lenient_metrics['TN']}, FN: {lenient_metrics['FN']}")
    emit(f"Precision  : {p_l:.3f}")
    emit(f"Recall     : {r_l:.3f}")
    emit(f"Specificity: {s_l:.3f}")
    emit(f"F1-Score   : {f1_l:.3f}")

    # --- 95% Confidence Intervals ---
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

    emit("\n--- 95% CONFIDENCE INTERVALS (Bootstrap B=1000, Seed=42 / Wilson Score) ---")
    emit("Strict:")
    emit(f"  Precision  : {p:.3f}  [Bootstrap 95% CI: {b_strict_p[0]:.3f} - {b_strict_p[1]:.3f}]  [Wilson Score: {w_strict_p[0]:.3f} - {w_strict_p[1]:.3f}]")
    emit(f"  Recall     : {r:.3f}  [Bootstrap 95% CI: {b_strict_r[0]:.3f} - {b_strict_r[1]:.3f}]  [Wilson Score: {w_strict_r[0]:.3f} - {w_strict_r[1]:.3f}]")
    emit(f"  Specificity: {s:.3f}  [Bootstrap 95% CI: {b_strict_s[0]:.3f} - {b_strict_s[1]:.3f}]  [Wilson Score: {w_strict_s[0]:.3f} - {w_strict_s[1]:.3f}]")
    emit(f"  F1-Score   : {f1:.3f}  [Bootstrap 95% CI: {b_strict_f1[0]:.3f} - {b_strict_f1[1]:.3f}]")
    emit("Lenient:")
    emit(f"  Precision  : {p_l:.3f}  [Bootstrap 95% CI: {b_lenient_p[0]:.3f} - {b_lenient_p[1]:.3f}]  [Wilson Score: {w_lenient_p[0]:.3f} - {w_lenient_p[1]:.3f}]")
    emit(f"  Recall     : {r_l:.3f}  [Bootstrap 95% CI: {b_lenient_r[0]:.3f} - {b_lenient_r[1]:.3f}]  [Wilson Score: {w_lenient_r[0]:.3f} - {w_lenient_r[1]:.3f}]")
    emit(f"  Specificity: {s_l:.3f}  [Bootstrap 95% CI: {b_lenient_s[0]:.3f} - {b_lenient_s[1]:.3f}]  [Wilson Score: {w_lenient_s[0]:.3f} - {w_lenient_s[1]:.3f}]")
    emit(f"  F1-Score   : {f1_l:.3f}  [Bootstrap 95% CI: {b_lenient_f1[0]:.3f} - {b_lenient_f1[1]:.3f}]")
    
    emit("\n--- CATEGORY BREAKDOWN ---")
    for cat, data in category_metrics.items():
        emit(f"\nCategory: {cat} (Count: {data['count']})")
        cp, cr, cs, cf1 = calc_metrics(data['strict'])
        emit(f"  Strict -> TP: {data['strict']['TP']}, FP: {data['strict']['FP']}, TN: {data['strict']['TN']}, FN: {data['strict']['FN']} | P: {cp:.2f}, R: {cr:.2f}, S: {cs:.2f}")
        lp, lr, ls, lf1 = calc_metrics(data['lenient'])
        emit(f"  Lenient-> TP: {data['lenient']['TP']}, FP: {data['lenient']['FP']}, TN: {data['lenient']['TN']}, FN: {data['lenient']['FN']} | P: {lp:.2f}, R: {lr:.2f}, S: {ls:.2f}")

    emit("\n--- FAILURE MODES ---")
    oc_rate = over_caution_count / negative_control_count if negative_control_count > 0 else 0.0
    emit(f"Over-Caution Rate (MONITOR on known negatives): {oc_rate:.1%} ({over_caution_count}/{negative_control_count})")
    
    emit("\n--- DISAGREEMENTS (Expected != Actual) ---")
    if not disagreements:
        emit("None! Perfect agreement.")
    else:
        for d in disagreements:
            emit(f"- {d['pair']} ({d['category']}): Expected {d['expected']}, Got {d['actual']}")

    # =========================================================================
    # PHASE 2: THERAPEUTIC AREA STRATIFICATION (ATC LEVEL 1)
    # =========================================================================
    stratified_metrics = compute_stratified_metrics(evaluated_records, strata_key="therapeutic_area_code")

    emit("\n" + "=" * 60)
    emit("--- THERAPEUTIC AREA STRATIFICATION -- ATC LEVEL 1 ---")
    emit("=" * 60)

    emit(
        f"{'Code':<4} | {'Therapeutic Area':<36} | {'n':>2} | {'Status':<12} | "
        f"{'Strict F1':<9} | {'Strict (P/R/Sp)':<19} | "
        f"{'Lenient F1':<10} | {'Lenient (P/R/Sp)'}"
    )
    emit("-" * 120)

    for code, s_data in sorted(stratified_metrics.items()):
        name_short = (s_data["name"][:34] + "..") if len(s_data["name"]) > 36 else s_data["name"]
        status_tag = "[Exploratory]" if s_data["is_exploratory"] else "[Reportable]"

        st = s_data["strict"]
        lt = s_data["lenient"]

        st_f1_str = f"{st['f1']:.3f}" if st["f1"] is not None else "N/A"
        lt_f1_str = f"{lt['f1']:.3f}" if lt["f1"] is not None else "N/A"

        def _fmt_trip(d):
            p_str = f"{d['precision']:.2f}" if d['precision'] is not None else "N/A"
            r_str = f"{d['recall']:.2f}" if d['recall'] is not None else "N/A"
            s_str = f"{d['specificity']:.2f}" if d['specificity'] is not None else "N/A"
            return f"{p_str}/{r_str}/{s_str}"

        emit(
            f"{code:<4} | {name_short:<36} | {s_data['n']:>2} | {status_tag:<12} | "
            f"{st_f1_str:<9} | {_fmt_trip(st):<19} | "
            f"{lt_f1_str:<10} | {_fmt_trip(lt)}"
        )

    emit("\n--- DETAILED STRATUM BREAKDOWN (Wilson 95% Confidence Intervals) ---")
    for code, s_data in sorted(stratified_metrics.items()):
        st = s_data["strict"]
        lt = s_data["lenient"]
        expl_note = " [EXPLORATORY: n < 5 - interpret with caution]" if s_data["is_exploratory"] else ""
        emit(f"\nStratum {code}: {s_data['name']} (n={s_data['n']}){expl_note}")
        
        def _fmt_ci(ci):
            if ci is None or None in ci:
                return "N/A"
            return f"[{ci[0]:.3f} - {ci[1]:.3f}]"

        p_s = f"{st['precision']:.3f}" if st['precision'] is not None else "N/A"
        r_s = f"{st['recall']:.3f}" if st['recall'] is not None else "N/A"
        s_s = f"{st['specificity']:.3f}" if st['specificity'] is not None else "N/A"
        f1_s = f"{st['f1']:.3f}" if st['f1'] is not None else "N/A"

        emit(
            f"  Strict -> TP: {st['TP']}, FP: {st['FP']}, TN: {st['TN']}, FN: {st['FN']} | "
            f"Precision: {p_s} (Wilson: {_fmt_ci(st['precision_ci'])}), "
            f"Recall: {r_s} (Wilson: {_fmt_ci(st['recall_ci'])}), "
            f"Specificity: {s_s} (Wilson: {_fmt_ci(st['specificity_ci'])}), "
            f"F1: {f1_s}"
        )

        p_l = f"{lt['precision']:.3f}" if lt['precision'] is not None else "N/A"
        r_l = f"{lt['recall']:.3f}" if lt['recall'] is not None else "N/A"
        s_l = f"{lt['specificity']:.3f}" if lt['specificity'] is not None else "N/A"
        f1_l = f"{lt['f1']:.3f}" if lt['f1'] is not None else "N/A"

        emit(
            f"  Lenient-> TP: {lt['TP']}, FP: {lt['FP']}, TN: {lt['TN']}, FN: {lt['FN']} | "
            f"Precision: {p_l} (Wilson: {_fmt_ci(lt['precision_ci'])}), "
            f"Recall: {r_l} (Wilson: {_fmt_ci(lt['recall_ci'])}), "
            f"Specificity: {s_l} (Wilson: {_fmt_ci(lt['specificity_ci'])}), "
            f"F1: {f1_l}"
        )

    # =========================================================================
    # ATC ANNOTATION COVERAGE & PROVENANCE
    # =========================================================================
    coverage_summary = compute_atc_coverage(evaluated_records, drug_contexts)
    unique_drugs = sorted(set(r["drug"] for r in evaluated_records))

    emit("\n" + "=" * 60)
    emit("--- ATC ANNOTATION COVERAGE & MULTI-ATC PROVENANCE ---")
    emit("=" * 60)
    emit(f"Total unique benchmark drugs        : {coverage_summary['total_unique_drugs']}")
    emit(f"Resolved via ChEMBL API             : {coverage_summary['chembl_resolved']}")
    emit(f"Resolved via fallback (known gaps)  : {coverage_summary['fallback_resolved']} ({', '.join(d for d in unique_drugs if drug_contexts.get(d) and drug_contexts[d].atc_source == 'hardcoded_fallback') or 'None'})")
    emit(f"Unresolved                          : {coverage_summary['unresolved']}")
    emit(f"Total resolution coverage           : {coverage_summary['resolution_percentage']:.1f}%")
    emit(f"Drugs with multiple ATC codes       : {coverage_summary['multi_atc_count']}")
    emit(f"Drugs spanning multiple Level 1s    : {coverage_summary['multi_level1_count']}")
    emit("\nSCIENTIFIC METHODOLOGY NOTE:")
    emit("  ATC classification provides drug-class / therapeutic context. It does NOT identify")
    emit("  patient-level indication, why the patient was prescribed the drug, or actual duration.")
    emit("  Strata with n < 5 are marked [EXPLORATORY] to prevent spurious ranking of small samples.")
    emit("=" * 60)

    # Save human-readable summary text report
    summary_txt_path = outputs_dir / "evaluation_summary.txt"
    with open(summary_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    logger.info(f"Saved evaluation text summary to {summary_txt_path}")

    # Save structured JSON summary report
    summary_json_path = outputs_dir / "evaluation_summary.json"
    json_payload = {
        "title": title,
        "pairs_evaluated": len(evaluated_pairs),
        "pairs_total": len(ground_truth),
        "strict_metrics": {
            **strict_metrics,
            "precision": p,
            "recall": r,
            "specificity": s,
            "f1": f1,
            "wilson_ci": {
                "precision": w_strict_p,
                "recall": w_strict_r,
                "specificity": w_strict_s,
            },
            "bootstrap_ci": {
                "precision": b_strict_p,
                "recall": b_strict_r,
                "specificity": b_strict_s,
                "f1": b_strict_f1,
            }
        },
        "lenient_metrics": {
            **lenient_metrics,
            "precision": p_l,
            "recall": r_l,
            "specificity": s_l,
            "f1": f1_l,
            "wilson_ci": {
                "precision": w_lenient_p,
                "recall": w_lenient_r,
                "specificity": w_lenient_s,
            },
            "bootstrap_ci": {
                "precision": b_lenient_p,
                "recall": b_lenient_r,
                "specificity": b_lenient_s,
                "f1": b_lenient_f1,
            }
        },
        "over_caution_rate": oc_rate,
        "category_metrics": category_metrics,
        "therapeutic_area_metrics": stratified_metrics,
        "atc_coverage": coverage_summary,
        "disagreements": disagreements,
        "records": evaluated_records,
    }
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2)
    logger.info(f"Saved evaluation JSON summary to {summary_json_path}")

    return json_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate PharmaGuard triage reports.")
    parser.add_argument(
        "--outputs-dir",
        type=Path,
        default=None,
        help="Directory containing eval-run-*_report.json files. Defaults to outputs/core/.",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="PharmaGuard",
        help="Label shown in the report header (e.g. 'PharmaGuard' or 'Baseline').",
    )
    parser.add_argument(
        "--gt-path",
        "--ground-truth",
        dest="gt_path",
        type=Path,
        default=None,
        help="Path to ground truth JSON file. Defaults to pharmaguard/data/ground_truth.json.",
    )
    args = parser.parse_args()
    run_evaluation(outputs_dir=args.outputs_dir, title=args.title, gt_path=args.gt_path)
