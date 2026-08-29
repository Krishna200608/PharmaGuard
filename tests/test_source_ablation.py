"""
Unit tests for Multi-Source Ablation & Threshold Sensitivity (Experiment 2).
Includes documented hand-verified spot-checks for STRONG, MODERATE, and NO_SIGNAL pairs.
"""

import math
import pytest
from pharmaguard.agent.output_schema import (
    SignalStrength,
    EscalationDecision,
    compute_confidence,
    derive_escalation,
    TriageReport,
    SignalStatsOutput,
    MechanismOutput,
    LiteratureOutput,
    TriageOutput,
    PlausibilityLevel,
    EvidenceGrade,
    PlausibilitySource,
)
from scripts.research.source_ablation import (
    run_multi_source_ablation,
    run_threshold_sensitivity_sweep,
    run_counterfactual_decomposition,
    run_paired_bootstrap_comparison,
    calc_f1_metrics,
)
from datetime import datetime, timezone


def make_dummy_report(drug, event, prr_score, ss_label, grade, grade_score, plaus_level, plaus_score, conf, esc):
    now = datetime.now(timezone.utc)
    s_out = SignalStatsOutput(
        prr=5.0 if ss_label == "STRONG" else (3.5 if ss_label == "MODERATE" else 0.0),
        ror=None, prr_lower_ci=2.5 if ss_label == "STRONG" else 1.8, ror_lower_ci=None,
        report_count=1000 if ss_label != "NO_SIGNAL" else 0,
        source_endpoint="dummy", data_pulled_at=now, null_reason=None,
        prr_score=prr_score, prr_score_label=SignalStrength(ss_label), ci_downgraded=False,
    )
    m_out = MechanismOutput(
        chembl_id="CHEMBL1", moa="Test MoA",
        biological_plausibility=PlausibilityLevel(plaus_level),
        plausibility_score=plaus_score,
        plausibility_source=PlausibilitySource.HUMAN_CURATED,
        plausibility_rationale="Test rationale",
    )
    l_out = LiteratureOutput(
        pubmed_query="test query", abstracts_retrieved=5,
        evidence_grade=EvidenceGrade(grade), grade_score=grade_score,
        supporting_pmids=["123"], evidence_summary="Test summary",
    )
    t_out = TriageOutput(
        signal_strength=SignalStrength(ss_label),
        evidence_grade=EvidenceGrade(grade),
        escalation=EscalationDecision(esc),
        confidence=conf,
        prompts_version="v1.0",
        agent_reasoning_trace=["Test trace"],
    )
    return TriageReport(
        run_id=f"test-{drug}", prompts_version="v1.0",
        drug=drug, event=event, signal_stats=s_out, mechanism=m_out, literature=l_out, triage=t_out,
    )


def test_hand_verified_strong_signal_pair():
    """
    Spot-check 1: STRONG signal pair (ciprofloxacin::tendon_rupture).
    Hand-calculated expected values:
      PRR=1.0, Grade=0.5, Plaus=0.5 -> Conf = 0.40(1) + 0.40(0.5) + 0.20(0.5) = 0.70 -> ESCALATE.
    """
    rep = make_dummy_report(
        "ciprofloxacin", "tendon_rupture",
        prr_score=1.0, ss_label="STRONG",
        grade="B", grade_score=0.5,
        plaus_level="MODERATE", plaus_score=0.5,
        conf=0.70, esc="ESCALATE"
    )
    gt = {"ciprofloxacin::tendon_rupture": {"expected_escalation": "ESCALATE"}}
    res = run_multi_source_ablation({"ciprofloxacin::tendon_rupture": rep}, gt)
    p_res = res["per_pair_ablation"]["ciprofloxacin::tendon_rupture"]

    # FAERS-removed gate-bypassed: 0.40*0.5 + 0.20*0.5 = 0.30 -> DO_NOT_ESCALATE (flipped)
    assert math.isclose(p_res["faers_removed_gate_bypassed"]["confidence"], 0.30, abs_tol=1e-4)
    assert p_res["faers_removed_gate_bypassed"]["escalation"] == "DO_NOT_ESCALATE"
    assert p_res["faers_removed_gate_bypassed"]["matches_real"] is False

    # FAERS-removed gate-applied: NO_SIGNAL override -> DO_NOT_ESCALATE, is_gate_artifact = True
    assert p_res["faers_removed_gate_applied"]["escalation"] == "DO_NOT_ESCALATE"
    assert p_res["faers_removed_gate_applied"]["is_gate_artifact"] is True

    # PubMed-removed: 0.40*1.0 + 0.20*0.5 = 0.50 -> MONITOR (flipped from ESCALATE)
    assert math.isclose(p_res["pubmed_removed"]["confidence"], 0.50, abs_tol=1e-4)
    assert p_res["pubmed_removed"]["escalation"] == "MONITOR"
    assert p_res["pubmed_removed"]["matches_real"] is False

    # ChEMBL-removed: 0.40*1.0 + 0.40*0.5 = 0.60 -> MONITOR (flipped from ESCALATE)
    assert math.isclose(p_res["chembl_removed"]["confidence"], 0.60, abs_tol=1e-4)
    assert p_res["chembl_removed"]["escalation"] == "MONITOR"
    assert p_res["chembl_removed"]["matches_real"] is False


def test_hand_verified_moderate_signal_pair():
    """
    Spot-check 2: MODERATE signal pair (montelukast::suicidal_ideation).
    Hand-calculated expected values:
      PRR=0.66, Grade=1.0, Plaus=0.0 -> Conf = 0.40(0.66) + 0.40(1) + 0 = 0.664 -> MONITOR.
    """
    rep = make_dummy_report(
        "montelukast", "suicidal_ideation",
        prr_score=0.66, ss_label="MODERATE",
        grade="A", grade_score=1.0,
        plaus_level="LOW", plaus_score=0.0,
        conf=0.664, esc="MONITOR"
    )
    gt = {"montelukast::suicidal_ideation": {"expected_escalation": "ESCALATE"}}
    res = run_multi_source_ablation({"montelukast::suicidal_ideation": rep}, gt)
    p_res = res["per_pair_ablation"]["montelukast::suicidal_ideation"]

    # FAERS-removed gate-bypassed: 0.40*1.0 = 0.40 >= 0.35 -> MONITOR (matches real decision)
    assert math.isclose(p_res["faers_removed_gate_bypassed"]["confidence"], 0.40, abs_tol=1e-4)
    assert p_res["faers_removed_gate_bypassed"]["escalation"] == "MONITOR"
    assert p_res["faers_removed_gate_bypassed"]["matches_real"] is True

    # FAERS-removed gate-applied: Gate 1 forced -> DO_NOT_ESCALATE (flipped)
    assert p_res["faers_removed_gate_applied"]["escalation"] == "DO_NOT_ESCALATE"
    assert p_res["faers_removed_gate_applied"]["is_gate_artifact"] is True

    # PubMed-removed: 0.40*0.66 = 0.264 < 0.35 -> DO_NOT_ESCALATE (flipped)
    assert math.isclose(p_res["pubmed_removed"]["confidence"], 0.264, abs_tol=1e-4)
    assert p_res["pubmed_removed"]["escalation"] == "DO_NOT_ESCALATE"
    assert p_res["pubmed_removed"]["matches_real"] is False

    # ChEMBL-removed: plaus was 0.0 -> Conf unchanged (0.664) -> MONITOR (matches real)
    assert math.isclose(p_res["chembl_removed"]["confidence"], 0.664, abs_tol=1e-4)
    assert p_res["chembl_removed"]["escalation"] == "MONITOR"
    assert p_res["chembl_removed"]["matches_real"] is True


def test_hand_verified_no_signal_pair():
    """
    Spot-check 3: NO_SIGNAL pair (atorvastatin::dementia).
    Hand-calculated expected values:
      PRR=0.0, Grade=1.0, Plaus=0.5 -> Conf = 0.50. Gate 1 fires -> DO_NOT_ESCALATE.
    """
    rep = make_dummy_report(
        "atorvastatin", "dementia",
        prr_score=0.0, ss_label="NO_SIGNAL",
        grade="A", grade_score=1.0,
        plaus_level="MODERATE", plaus_score=0.5,
        conf=0.50, esc="DO_NOT_ESCALATE"
    )
    gt = {"atorvastatin::dementia": {"expected_escalation": "DO_NOT_ESCALATE"}}
    res = run_multi_source_ablation({"atorvastatin::dementia": rep}, gt)
    p_res = res["per_pair_ablation"]["atorvastatin::dementia"]

    # FAERS-removed gate-bypassed: Conf = 0.50 >= 0.35 -> MONITOR (flipped from real DO_NOT_ESCALATE)
    assert p_res["faers_removed_gate_bypassed"]["escalation"] == "MONITOR"
    assert p_res["faers_removed_gate_bypassed"]["matches_real"] is False

    # FAERS-removed gate-applied: Gate 1 fires -> DO_NOT_ESCALATE. NOT an artifact (real signal was NO_SIGNAL)
    assert p_res["faers_removed_gate_applied"]["escalation"] == "DO_NOT_ESCALATE"
    assert p_res["faers_removed_gate_applied"]["is_gate_artifact"] is False
    assert p_res["faers_removed_gate_applied"]["matches_real"] is True


def test_threshold_sensitivity_sweep_baseline():
    rep = make_dummy_report(
        "testdrug", "testevent",
        prr_score=1.0, ss_label="STRONG",
        grade="B", grade_score=0.5,
        plaus_level="MODERATE", plaus_score=0.5,
        conf=0.70, esc="ESCALATE"
    )
    gt = {"testdrug::testevent": {"expected_escalation": "ESCALATE"}}
    res = run_threshold_sensitivity_sweep({"testdrug::testevent": rep}, gt)
    
    base_point = next(p for p in res["grid_points"] if p["is_production_baseline"])
    assert base_point["threshold_escalate"] == 0.70
    assert base_point["threshold_monitor"] == 0.35
    assert base_point["num_decision_flips"] == 0