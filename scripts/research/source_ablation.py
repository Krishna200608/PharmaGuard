"""
Multi-Source Ablation, Threshold Sensitivity, and Counterfactual Decomposition (Experiment 2).

Implements:
1. Six ablation conditions with rigorous separation of FAERS gate-bypass vs gate-applied.
2. Threshold sensitivity grid sweep (+/-0.05, +/-0.10 around 0.70 / 0.35).
3. Counterfactual decision margins per pair.
4. Paired bootstrap comparison (B=1000, seed=42) against baseline.

Output artifacts:
- outputs/research/source_ablation/ablation_results.json
- outputs/research/source_ablation/threshold_sensitivity.json
- outputs/research/source_ablation/counterfactual_margins.json

Owner: Krishna Sikheriya (IIT2023139)
"""

import argparse
import json
import logging
import math
import os
import random
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np

from pharmaguard.utils.config_loader import load_config
from pharmaguard.utils.prompt_loader import PromptLoader
from pharmaguard.tools.cache import CACHE_SCHEMA_VERSION
from pharmaguard.agent.output_schema import (
    PRR_SCORE_WEIGHTS,
    compute_confidence,
    derive_escalation,
    SignalStrength,
    EscalationDecision,
    TriageReport,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("source_ablation")

OUTPUT_DIR = REPO_ROOT / "outputs" / "research" / "source_ablation"
GROUND_TRUTH_FILE = REPO_ROOT / "pharmaguard" / "data" / "ground_truth.json"
PRODUCTION_REPORTS_DIR = REPO_ROOT / "outputs"
BASELINE_REPORTS_DIR = REPO_ROOT / "outputs" / "baseline"


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


def load_ground_truth(gt_path: Path = GROUND_TRUTH_FILE) -> dict:
    with open(gt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {f"{p['drug_canonical']}::{p['event_meddra_pt']}": p for p in data.get("pairs", [])}


def load_reports(reports_dir: Path) -> dict[str, TriageReport]:
    reports = {}
    for rf in sorted(reports_dir.glob("eval-run-*_report.json")):
        with open(rf, "r", encoding="utf-8") as f:
            d = json.load(f)
        report = TriageReport(**d)
        pair_key = f"{report.drug}::{report.event}"
        reports[pair_key] = report
    return reports


def calc_f1_metrics(actual_list: list[str], expected_list: list[str]) -> dict:
    """Calculate strict and lenient precision, recall, specificity, F1."""
    s_tp = s_fp = s_tn = s_fn = 0
    l_tp = l_fp = l_tn = l_fn = 0
    for act, exp in zip(actual_list, expected_list):
        gt_pos = exp == "ESCALATE"
        act_s_pos = act == "ESCALATE"
        act_l_pos = act in ("ESCALATE", "MONITOR")

        if gt_pos:
            if act_s_pos: s_tp += 1
            else: s_fn += 1
            if act_l_pos: l_tp += 1
            else: l_fn += 1
        else:
            if act_s_pos: s_fp += 1
            else: s_tn += 1
            if act_l_pos: l_fp += 1
            else: l_tn += 1

    def metrics(tp, fp, tn, fn):
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        return {
            "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "precision": round(prec, 4), "recall": round(rec, 4),
            "specificity": round(spec, 4), "f1": round(f1, 4),
        }

    return {
        "strict": metrics(s_tp, s_fp, s_tn, s_fn),
        "lenient": metrics(l_tp, l_fp, l_tn, l_fn),
    }
# ----------------------------------------------------------------------
# 1. Multi-Source Ablation Conditions
# ----------------------------------------------------------------------

def run_multi_source_ablation(prod_reports: dict[str, TriageReport], ground_truth: dict) -> dict:
    pair_ablation_results = {}
    gate_artifact_counts = {"faers_removed": 0, "pubmed_only": 0, "chembl_only": 0}
    decision_flip_counts = {
        "faers_removed_gate_bypassed": 0,
        "faers_removed_gate_applied": 0,
        "pubmed_removed": 0,
        "chembl_removed": 0,
        "faers_only": 0,
        "pubmed_only_gate_bypassed": 0,
        "pubmed_only_gate_applied": 0,
        "chembl_only_gate_bypassed": 0,
        "chembl_only_gate_applied": 0,
    }

    condition_preds: dict[str, list[str]] = {k: [] for k in decision_flip_counts.keys()}
    expected_list: list[str] = []

    for pair_key in sorted(prod_reports.keys()):
        rep = prod_reports[pair_key]
        gt = ground_truth[pair_key]
        exp_esc = gt["expected_escalation"]
        expected_list.append(exp_esc)

        prr_sc = rep.signal_stats.prr_score
        ss_label_str = rep.signal_stats.prr_score_label.value if hasattr(rep.signal_stats.prr_score_label, "value") else rep.signal_stats.prr_score_label
        ss_label = SignalStrength(ss_label_str)
        grade_sc = rep.literature.grade_score
        grade_str = rep.literature.evidence_grade.value if hasattr(rep.literature.evidence_grade, "value") else rep.literature.evidence_grade
        plaus_sc = rep.mechanism.plausibility_score
        plaus_str = rep.mechanism.biological_plausibility.value if hasattr(rep.mechanism.biological_plausibility, "value") else rep.mechanism.biological_plausibility
        real_conf = rep.triage.confidence
        real_esc = rep.triage.escalation.value if hasattr(rep.triage.escalation, "value") else rep.triage.escalation

        had_real_signal = (ss_label != SignalStrength.NO_SIGNAL)

        # Condition 1: FAERS-removed (gate-bypassed)
        c_faers_rm = round(0.40 * grade_sc + 0.20 * plaus_sc, 4)
        if c_faers_rm >= 0.70:
            esc_faers_rm_bypassed = "ESCALATE"
        elif c_faers_rm >= 0.35:
            esc_faers_rm_bypassed = "MONITOR"
        else:
            esc_faers_rm_bypassed = "DO_NOT_ESCALATE"

        # Condition 2: FAERS-removed (gate-applied)
        esc_faers_rm_applied = derive_escalation(c_faers_rm, SignalStrength.NO_SIGNAL).value
        is_faers_gate_artifact = had_real_signal
        if is_faers_gate_artifact:
            gate_artifact_counts["faers_removed"] += 1

        # Condition 3: PubMed-removed
        c_pubmed_rm = round(0.40 * prr_sc + 0.20 * plaus_sc, 4)
        esc_pubmed_rm = derive_escalation(c_pubmed_rm, ss_label).value

        # Condition 4: ChEMBL-removed
        c_chembl_rm = round(0.40 * prr_sc + 0.40 * grade_sc, 4)
        esc_chembl_rm = derive_escalation(c_chembl_rm, ss_label).value

        # Condition 5: FAERS-only
        c_faers_only = round(0.40 * prr_sc, 4)
        esc_faers_only = derive_escalation(c_faers_only, ss_label).value

        # Condition 6: PubMed-only
        c_pubmed_only = round(0.40 * grade_sc, 4)
        esc_pubmed_only_bypassed = (
            "ESCALATE" if c_pubmed_only >= 0.70 else ("MONITOR" if c_pubmed_only >= 0.35 else "DO_NOT_ESCALATE")
        )
        esc_pubmed_only_applied = derive_escalation(c_pubmed_only, SignalStrength.NO_SIGNAL).value
        if had_real_signal:
            gate_artifact_counts["pubmed_only"] += 1

        # Condition 7: ChEMBL-only
        c_chembl_only = round(0.20 * plaus_sc, 4)
        esc_chembl_only_bypassed = (
            "ESCALATE" if c_chembl_only >= 0.70 else ("MONITOR" if c_chembl_only >= 0.35 else "DO_NOT_ESCALATE")
        )
        esc_chembl_only_applied = derive_escalation(c_chembl_only, SignalStrength.NO_SIGNAL).value
        if had_real_signal:
            gate_artifact_counts["chembl_only"] += 1

        cond_map = {
            "faers_removed_gate_bypassed": esc_faers_rm_bypassed,
            "faers_removed_gate_applied": esc_faers_rm_applied,
            "pubmed_removed": esc_pubmed_rm,
            "chembl_removed": esc_chembl_rm,
            "faers_only": esc_faers_only,
            "pubmed_only_gate_bypassed": esc_pubmed_only_bypassed,
            "pubmed_only_gate_applied": esc_pubmed_only_applied,
            "chembl_only_gate_bypassed": esc_chembl_only_bypassed,
            "chembl_only_gate_applied": esc_chembl_only_applied,
        }

        for c_name, c_esc in cond_map.items():
            condition_preds[c_name].append(c_esc)
            if c_esc != real_esc:
                decision_flip_counts[c_name] += 1

        pair_ablation_results[pair_key] = {
            "original": {
                "prr_score": prr_sc,
                "signal_strength": ss_label_str,
                "grade_score": grade_sc,
                "evidence_grade": grade_str,
                "plausibility_score": plaus_sc,
                "biological_plausibility": plaus_str,
                "confidence": real_conf,
                "escalation": real_esc,
            },
            "faers_removed_gate_bypassed": {
                "confidence": c_faers_rm,
                "escalation": esc_faers_rm_bypassed,
                "matches_real": esc_faers_rm_bypassed == real_esc,
            },
            "faers_removed_gate_applied": {
                "confidence": c_faers_rm,
                "escalation": esc_faers_rm_applied,
                "matches_real": esc_faers_rm_applied == real_esc,
                "is_gate_artifact": is_faers_gate_artifact,
            },
            "pubmed_removed": {
                "confidence": c_pubmed_rm,
                "escalation": esc_pubmed_rm,
                "matches_real": esc_pubmed_rm == real_esc,
            },
            "chembl_removed": {
                "confidence": c_chembl_rm,
                "escalation": esc_chembl_rm,
                "matches_real": esc_chembl_rm == real_esc,
            },
            "faers_only": {
                "confidence": c_faers_only,
                "escalation": esc_faers_only,
                "matches_real": esc_faers_only == real_esc,
            },
            "pubmed_only": {
                "confidence": c_pubmed_only,
                "gate_bypassed_escalation": esc_pubmed_only_bypassed,
                "gate_applied_escalation": esc_pubmed_only_applied,
                "matches_real_bypassed": esc_pubmed_only_bypassed == real_esc,
                "matches_real_applied": esc_pubmed_only_applied == real_esc,
            },
            "chembl_only": {
                "confidence": c_chembl_only,
                "gate_bypassed_escalation": esc_chembl_only_bypassed,
                "gate_applied_escalation": esc_chembl_only_applied,
                "matches_real_bypassed": esc_chembl_only_bypassed == real_esc,
                "matches_real_applied": esc_chembl_only_applied == real_esc,
            },
        }

    condition_metrics = {}
    for c_name, preds in condition_preds.items():
        condition_metrics[c_name] = calc_f1_metrics(preds, expected_list)

    return {
        "per_pair_ablation": pair_ablation_results,
        "decision_flip_counts": decision_flip_counts,
        "gate_artifact_counts": gate_artifact_counts,
        "condition_performance": condition_metrics,
    }
# ----------------------------------------------------------------------
# 2. Threshold Sensitivity Grid Sweep
# ----------------------------------------------------------------------

def run_threshold_sensitivity_sweep(prod_reports: dict[str, TriageReport], ground_truth: dict) -> dict:
    esc_thresholds = [0.60, 0.65, 0.70, 0.75, 0.80]
    mon_thresholds = [0.25, 0.30, 0.35, 0.40, 0.45]

    pair_keys = sorted(prod_reports.keys())
    expected_list = [ground_truth[pk]["expected_escalation"] for pk in pair_keys]
    real_decisions = [
        prod_reports[pk].triage.escalation.value
        if hasattr(prod_reports[pk].triage.escalation, "value")
        else prod_reports[pk].triage.escalation
        for pk in pair_keys
    ]

    grid_results = []

    for t_esc in esc_thresholds:
        for t_mon in mon_thresholds:
            if t_mon >= t_esc:
                continue

            sweep_preds = []
            flips = 0

            for i, pk in enumerate(pair_keys):
                rep = prod_reports[pk]
                c = rep.triage.confidence
                ss_str = rep.signal_stats.prr_score_label.value if hasattr(rep.signal_stats.prr_score_label, "value") else rep.signal_stats.prr_score_label
                ss = SignalStrength(ss_str)

                if ss == SignalStrength.NO_SIGNAL:
                    pred = "DO_NOT_ESCALATE"
                elif c >= t_esc and ss in (SignalStrength.STRONG, SignalStrength.MODERATE):
                    pred = "ESCALATE"
                elif c >= t_mon:
                    pred = "MONITOR"
                else:
                    pred = "DO_NOT_ESCALATE"

                sweep_preds.append(pred)
                if pred != real_decisions[i]:
                    flips += 1

            metrics = calc_f1_metrics(sweep_preds, expected_list)

            grid_results.append({
                "threshold_escalate": t_esc,
                "threshold_monitor": t_mon,
                "is_production_baseline": (t_esc == 0.70 and t_mon == 0.35),
                "num_decision_flips": flips,
                "strict_f1": metrics["strict"]["f1"],
                "strict_precision": metrics["strict"]["precision"],
                "strict_recall": metrics["strict"]["recall"],
                "lenient_f1": metrics["lenient"]["f1"],
                "lenient_precision": metrics["lenient"]["precision"],
                "lenient_recall": metrics["lenient"]["recall"],
            })

    return {
        "base_thresholds": {"escalate": 0.70, "monitor": 0.35},
        "grid_points": grid_results,
    }


# ----------------------------------------------------------------------
# 3. Counterfactual Decomposition
# ----------------------------------------------------------------------

def run_counterfactual_decomposition(prod_reports: dict[str, TriageReport]) -> dict:
    counterfactuals = {}

    for pair_key, rep in sorted(prod_reports.items()):
        prr_sc = rep.signal_stats.prr_score
        ss_label_str = rep.signal_stats.prr_score_label.value if hasattr(rep.signal_stats.prr_score_label, "value") else rep.signal_stats.prr_score_label
        ss_label = SignalStrength(ss_label_str)
        grade_sc = rep.literature.grade_score
        plaus_sc = rep.mechanism.plausibility_score
        c = rep.triage.confidence
        act = rep.triage.escalation.value if hasattr(rep.triage.escalation, "value") else rep.triage.escalation

        candidate_flips = []

        if act == "MONITOR":
            target_dec = "ESCALATE"
            if ss_label in (SignalStrength.STRONG, SignalStrength.MODERATE):
                for p_val in [0.5, 1.0]:
                    if p_val > plaus_sc:
                        new_c = round(c + 0.20 * (p_val - plaus_sc), 4)
                        if new_c >= 0.70:
                            candidate_flips.append({
                                "source": "plausibility_score",
                                "from": plaus_sc,
                                "to": p_val,
                                "delta_subscore": round(p_val - plaus_sc, 2),
                                "resulting_confidence": new_c,
                                "target_decision": target_dec,
                            })

                for g_val in [0.5, 1.0]:
                    if g_val > grade_sc:
                        new_c = round(c + 0.40 * (g_val - grade_sc), 4)
                        if new_c >= 0.70:
                            candidate_flips.append({
                                "source": "grade_score",
                                "from": grade_sc,
                                "to": g_val,
                                "delta_subscore": round(g_val - grade_sc, 2),
                                "resulting_confidence": new_c,
                                "target_decision": target_dec,
                            })

                for prr_val in [0.66, 1.0]:
                    if prr_val > prr_sc:
                        new_c = round(c + 0.40 * (prr_val - prr_sc), 4)
                        if new_c >= 0.70:
                            candidate_flips.append({
                                "source": "prr_score",
                                "from": prr_sc,
                                "to": prr_val,
                                "delta_subscore": round(prr_val - prr_sc, 2),
                                "resulting_confidence": new_c,
                                "target_decision": target_dec,
                            })

        elif act == "DO_NOT_ESCALATE":
            if ss_label == SignalStrength.NO_SIGNAL:
                for new_ss, new_prr in [(SignalStrength.WEAK, 0.33), (SignalStrength.MODERATE, 0.66), (SignalStrength.STRONG, 1.0)]:
                    new_c = round(0.40 * new_prr + 0.40 * grade_sc + 0.20 * plaus_sc, 4)
                    new_esc = derive_escalation(new_c, new_ss).value
                    if new_esc in ("MONITOR", "ESCALATE"):
                        candidate_flips.append({
                            "source": "prr_score_and_signal_strength",
                            "from": f"{prr_sc} (NO_SIGNAL)",
                            "to": f"{new_prr} ({new_ss.value})",
                            "delta_subscore": round(new_prr - prr_sc, 2),
                            "resulting_confidence": new_c,
                            "target_decision": new_esc,
                            "gate_unblocked": True,
                        })
            else:
                for p_val in [0.5, 1.0]:
                    if p_val > plaus_sc:
                        new_c = round(c + 0.20 * (p_val - plaus_sc), 4)
                        if new_c >= 0.35:
                            candidate_flips.append({
                                "source": "plausibility_score",
                                "from": plaus_sc,
                                "to": p_val,
                                "delta_subscore": round(p_val - plaus_sc, 2),
                                "resulting_confidence": new_c,
                                "target_decision": "MONITOR",
                            })
                for g_val in [0.5, 1.0]:
                    if g_val > grade_sc:
                        new_c = round(c + 0.40 * (g_val - grade_sc), 4)
                        if new_c >= 0.35:
                            candidate_flips.append({
                                "source": "grade_score",
                                "from": grade_sc,
                                "to": g_val,
                                "delta_subscore": round(g_val - grade_sc, 2),
                                "resulting_confidence": new_c,
                                "target_decision": "MONITOR",
                            })

        elif act == "ESCALATE":
            for p_val in [0.5, 0.0]:
                if p_val < plaus_sc:
                    new_c = round(c - 0.20 * (plaus_sc - p_val), 4)
                    if new_c < 0.70:
                        candidate_flips.append({
                            "source": "plausibility_score (downward)",
                            "from": plaus_sc,
                            "to": p_val,
                            "delta_subscore": round(p_val - plaus_sc, 2),
                            "resulting_confidence": new_c,
                            "target_decision": "MONITOR",
                        })
            for g_val in [0.5, 0.0]:
                if g_val < grade_sc:
                    new_c = round(c - 0.40 * (grade_sc - g_val), 4)
                    if new_c < 0.70:
                        candidate_flips.append({
                            "source": "grade_score (downward)",
                            "from": grade_sc,
                            "to": g_val,
                            "delta_subscore": round(g_val - grade_sc, 2),
                            "resulting_confidence": new_c,
                            "target_decision": "MONITOR",
                        })

        smallest_flip = None
        if candidate_flips:
            smallest_flip = min(candidate_flips, key=lambda f: abs(f["delta_subscore"]))

        counterfactuals[pair_key] = {
            "current_escalation": act,
            "current_confidence": c,
            "current_signal_strength": ss_label_str,
            "is_blocked_by_no_signal_gate": (ss_label == SignalStrength.NO_SIGNAL and act == "DO_NOT_ESCALATE"),
            "smallest_perturbation_to_flip": smallest_flip,
            "all_single_subscore_flips": candidate_flips,
        }

    return counterfactuals
# ----------------------------------------------------------------------
# 4. Paired Bootstrap Comparison (PharmaGuard vs Baseline)
# ----------------------------------------------------------------------

def run_paired_bootstrap_comparison(
    prod_reports: dict[str, TriageReport],
    base_reports: dict[str, TriageReport],
    ground_truth: dict,
    n_resamples: int = 1000,
    seed: int = 42,
) -> dict:
    pair_keys = sorted(prod_reports.keys())
    paired_data = []

    for pk in pair_keys:
        gt_pos = ground_truth[pk]["expected_escalation"] == "ESCALATE"
        pg_act = prod_reports[pk].triage.escalation.value if hasattr(prod_reports[pk].triage.escalation, "value") else prod_reports[pk].triage.escalation
        base_act = base_reports[pk].triage.escalation.value if hasattr(base_reports[pk].triage.escalation, "value") else base_reports[pk].triage.escalation

        paired_data.append({
            "pair": pk,
            "gt_pos": gt_pos,
            "pg_strict": pg_act == "ESCALATE",
            "pg_lenient": pg_act in ("ESCALATE", "MONITOR"),
            "base_strict": base_act == "ESCALATE",
            "base_lenient": base_act in ("ESCALATE", "MONITOR"),
        })

    random.seed(seed)
    np.random.seed(seed)

    diff_strict_f1 = []
    diff_lenient_f1 = []
    pg_strict_f1_list = []
    base_strict_f1_list = []
    pg_lenient_f1_list = []
    base_lenient_f1_list = []

    n = len(paired_data)

    for _ in range(n_resamples):
        sample = [paired_data[random.randint(0, n - 1)] for _ in range(n)]

        def f1_from_sample(pred_key):
            tp = sum(1 for r in sample if r["gt_pos"] and r[pred_key])
            fp = sum(1 for r in sample if not r["gt_pos"] and r[pred_key])
            fn = sum(1 for r in sample if r["gt_pos"] and not r[pred_key])
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            return (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        pg_s = f1_from_sample("pg_strict")
        base_s = f1_from_sample("base_strict")
        pg_l = f1_from_sample("pg_lenient")
        base_l = f1_from_sample("base_lenient")

        pg_strict_f1_list.append(pg_s)
        base_strict_f1_list.append(base_s)
        pg_lenient_f1_list.append(pg_l)
        base_lenient_f1_list.append(base_l)

        diff_strict_f1.append(pg_s - base_s)
        diff_lenient_f1.append(pg_l - base_l)

    def ci(vals):
        return [round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)]

    strict_diff_ci = ci(diff_strict_f1)
    lenient_diff_ci = ci(diff_lenient_f1)

    strict_crosses_zero = (strict_diff_ci[0] <= 0.0 <= strict_diff_ci[1])
    lenient_crosses_zero = (lenient_diff_ci[0] <= 0.0 <= lenient_diff_ci[1])

    return {
        "n_resamples": n_resamples,
        "seed": seed,
        "strict": {
            "mean_pg_f1": round(float(np.mean(pg_strict_f1_list)), 4),
            "mean_base_f1": round(float(np.mean(base_strict_f1_list)), 4),
            "mean_diff_f1": round(float(np.mean(diff_strict_f1)), 4),
            "diff_f1_95_ci": strict_diff_ci,
            "crosses_zero": strict_crosses_zero,
            "interpretation": (
                "Inconclusive difference at n=15 (95% CI crosses zero); cannot claim parity or superiority."
                if strict_crosses_zero
                else "Statistically distinguishable positive difference under bootstrap resampling."
            ),
        },
        "lenient": {
            "mean_pg_f1": round(float(np.mean(pg_lenient_f1_list)), 4),
            "mean_base_f1": round(float(np.mean(base_lenient_f1_list)), 4),
            "mean_diff_f1": round(float(np.mean(diff_lenient_f1)), 4),
            "diff_f1_95_ci": lenient_diff_ci,
            "crosses_zero": lenient_crosses_zero,
            "interpretation": (
                "Inconclusive difference at n=15 (95% CI crosses zero); cannot claim parity or superiority."
                if lenient_crosses_zero
                else "Statistically distinguishable positive difference under bootstrap resampling."
            ),
        },
    }


# ----------------------------------------------------------------------
# Main Orchestration & CLI
# ----------------------------------------------------------------------

def run_experiment_2():
    experiment_id = str(uuid.uuid4())
    git_hash = get_git_commit_hash()
    config = load_config()
    prompt_loader = PromptLoader()

    logger.info("Loading ground truth and reports for Experiment 2...")
    ground_truth = load_ground_truth()
    prod_reports = load_reports(PRODUCTION_REPORTS_DIR)
    base_reports = load_reports(BASELINE_REPORTS_DIR)

    if len(prod_reports) != 15:
        raise ValueError(f"Expected 15 production reports, found {len(prod_reports)}")
    if len(base_reports) != 15:
        raise ValueError(f"Expected 15 baseline reports, found {len(base_reports)}")

    metadata = {
        "experiment_id": experiment_id,
        "git_commit_hash": git_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_name": config.agent.llm_model,
        "prompts_version": prompt_loader.version,
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "config_snapshot": {
            "agent_mode": config.agent.mode,
            "plausibility_source": config.plausibility.source,
            "leakage_critic_enabled": getattr(getattr(config, "plausibility", None), "leakage_critic", None) and config.plausibility.leakage_critic.enabled,
            "confounding_enabled": getattr(config, "confounding", None) and config.confounding.enabled,
        },
    }

    ablation_out = run_multi_source_ablation(prod_reports, ground_truth)
    ablation_payload = {**metadata, **ablation_out}

    threshold_out = run_threshold_sensitivity_sweep(prod_reports, ground_truth)
    threshold_payload = {**metadata, **threshold_out}

    cf_out = run_counterfactual_decomposition(prod_reports)
    cf_payload = {**metadata, "counterfactual_margins": cf_out}

    boot_out = run_paired_bootstrap_comparison(prod_reports, base_reports, ground_truth)
    ablation_payload["paired_bootstrap_vs_baseline"] = boot_out

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "ablation_results.json", "w", encoding="utf-8") as f:
        json.dump(ablation_payload, f, indent=2)
    with open(OUTPUT_DIR / "threshold_sensitivity.json", "w", encoding="utf-8") as f:
        json.dump(threshold_payload, f, indent=2)
    with open(OUTPUT_DIR / "counterfactual_margins.json", "w", encoding="utf-8") as f:
        json.dump(cf_payload, f, indent=2)

    logger.info("Saved all Experiment 2 artifacts to %s", OUTPUT_DIR)
    return ablation_payload, threshold_payload, cf_payload


def print_experiment_2_report(ablation_data: dict, threshold_data: dict, cf_data: dict):
    print("\n" + "=" * 95)
    print("PHARMAGUARD EXPERIMENT 2: MULTI-SOURCE ABLATION & SENSITIVITY REPORT")
    print("=" * 95)
    print(f"Experiment ID:   {ablation_data['experiment_id']}")
    print(f"Git Commit Hash: {ablation_data['git_commit_hash']}")
    print("-" * 95)

    print("\n--- 1. MULTI-SOURCE ABLATION SUMMARY ---")
    print(f"{'Ablation Condition':<35} | {'Decision Flips':<15} | {'Strict F1':<12} | {'Lenient F1':<12}")
    print("-" * 80)
    perf = ablation_data["condition_performance"]
    flips = ablation_data["decision_flip_counts"]
    for c_name in [
        "faers_removed_gate_bypassed",
        "faers_removed_gate_applied",
        "pubmed_removed",
        "chembl_removed",
        "faers_only",
        "pubmed_only_gate_bypassed",
        "pubmed_only_gate_applied",
        "chembl_only_gate_bypassed",
        "chembl_only_gate_applied",
    ]:
        p = perf[c_name]
        print(f"{c_name:<35} | {flips[c_name]:<2}/15 pairs     | {p['strict']['f1']:<12.4f} | {p['lenient']['f1']:<12.4f}")

    print("\nGate Conflation Analysis:")
    print(f"  FAERS-removed (gate-applied): {ablation_data['gate_artifact_counts']['faers_removed']}/15 pairs triggered Gate 1 purely as an artifact of zeroing (originally non-NO_SIGNAL pairs).")

    print("\n--- 2. THRESHOLD SENSITIVITY GRID SWEEP (around 0.70 / 0.35) ---")
    print(f"{'Escalation Threshold':<22} | {'Monitor Threshold':<20} | {'Flips vs 0.70/0.35':<20} | {'Strict F1':<12} | {'Lenient F1':<12}")
    print("-" * 95)
    for pt in threshold_data["grid_points"]:
        flag = " (BASE)" if pt["is_production_baseline"] else ""
        print(f"{pt['threshold_escalate']:<22.2f} | {pt['threshold_monitor']:<20.2f} | {pt['num_decision_flips']:<2}/15{flag:<15} | {pt['strict_f1']:<12.4f} | {pt['lenient_f1']:<12.4f}")

    print("\n--- 3. COUNTERFACTUAL DECISION MARGINS (Smallest Perturbation to Flip Decision) ---")
    print(f"{'Drug :: Event':<35} | {'Decision':<15} | {'Conf':<6} | {'Smallest Flip Perturbation'}")
    print("-" * 95)
    for pk, cf in cf_data["counterfactual_margins"].items():
        s_flip = cf["smallest_perturbation_to_flip"]
        if s_flip:
            flip_desc = f"{s_flip['source']} ({s_flip['from']} -> {s_flip['to']}, delta={s_flip['delta_subscore']:+.2f}) -> {s_flip['target_decision']} (c={s_flip['resulting_confidence']:.4f})"
        elif cf["is_blocked_by_no_signal_gate"]:
            flip_desc = "BLOCKED by Gate 1 (NO_SIGNAL override; non-FAERS sub-score increases have 0 effect)"
        else:
            flip_desc = "Already at highest escalation tier (ESCALATE)"
        print(f"{pk:<35} | {cf['current_escalation']:<15} | {cf['current_confidence']:<6.4f} | {flip_desc}")

    print("\n--- 4. PAIRED BOOTSTRAP COMPARISON (PharmaGuard vs Baseline, B=1000, Seed=42) ---")
    boot = ablation_data["paired_bootstrap_vs_baseline"]
    s_b = boot["strict"]
    l_b = boot["lenient"]
    print(f"Strict F1 Difference:  PharmaGuard Mean={s_b['mean_pg_f1']:.4f}, Baseline Mean={s_b['mean_base_f1']:.4f}, Delta={s_b['mean_diff_f1']:+.4f} | 95% CI: {s_b['diff_f1_95_ci']}")
    print(f"  -> Interpretation: {s_b['interpretation']}")
    print(f"Lenient F1 Difference: PharmaGuard Mean={l_b['mean_pg_f1']:.4f}, Baseline Mean={l_b['mean_base_f1']:.4f}, Delta={l_b['mean_diff_f1']:+.4f} | 95% CI: {l_b['diff_f1_95_ci']}")
    print(f"  -> Interpretation: {l_b['interpretation']}")
    print("=" * 95 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Experiment 2: Multi-Source Ablation & Threshold Sensitivity")
    args = parser.parse_args()

    ablation_payload, threshold_payload, cf_payload = run_experiment_2()
    print_experiment_2_report(ablation_payload, threshold_payload, cf_payload)


if __name__ == "__main__":
    main()