"""
Unit tests for output_schema.py — PRR score formula, confidence formula, escalation rules.

All tests are deterministic — no API calls, no LLM, no agent loop.
These are the most important tests in the project: if the confidence formula
is wrong, every evaluation result is wrong.

Owner: Krishna Sikheriya (IIT2023139)
"""

import pytest
from pharmaguard.agent.output_schema import (
    SignalStrength,
    compute_prr_score,
    compute_confidence,
    derive_escalation,
    EscalationDecision,
)


# ================================================================
# PRR score table — all branches including CI-downgrade fallthrough
# ================================================================

class TestPrrScore:

    def test_zero_report_count(self):
        score, label, downgraded = compute_prr_score(0, None, None)
        assert score == 0.0
        assert label == SignalStrength.NO_SIGNAL
        assert downgraded is False

    def test_strong_signal_ci_passes(self):
        score, label, downgraded = compute_prr_score(100, 5.5, 2.1)
        assert score == 1.0
        assert label == SignalStrength.STRONG
        assert downgraded is False

    def test_strong_magnitude_ci_fails_downgrade_to_moderate(self):
        """The exact undefined case from the review — prr=5.5, ci=1.6."""
        score, label, downgraded = compute_prr_score(100, 5.5, 1.6)
        assert score == 0.66
        assert label == SignalStrength.MODERATE
        assert downgraded is True

    def test_moderate_signal_ci_passes(self):
        score, label, downgraded = compute_prr_score(50, 4.0, 1.6)
        assert score == 0.66
        assert label == SignalStrength.MODERATE
        assert downgraded is False

    def test_moderate_magnitude_ci_fails_downgrade_to_weak(self):
        score, label, downgraded = compute_prr_score(50, 4.0, 1.3)
        assert score == 0.33
        assert label == SignalStrength.WEAK
        assert downgraded is True

    def test_weak_signal_ci_passes(self):
        score, label, downgraded = compute_prr_score(30, 2.5, 1.1)
        assert score == 0.33
        assert label == SignalStrength.WEAK
        assert downgraded is False

    def test_weak_magnitude_ci_fails_downgrade_to_no_signal(self):
        score, label, downgraded = compute_prr_score(30, 2.5, 0.9)
        assert score == 0.0
        assert label == SignalStrength.NO_SIGNAL
        assert downgraded is True

    def test_below_minimum_prr(self):
        score, label, downgraded = compute_prr_score(200, 1.5, 1.2)
        assert score == 0.0
        assert label == SignalStrength.WEAK or label == SignalStrength.NO_SIGNAL
        # prr < 2.0 → always NO_SIGNAL regardless of CI
        assert label == SignalStrength.NO_SIGNAL
        assert downgraded is False

    def test_exact_boundary_prr_5_ci_2(self):
        """Boundary condition: prr exactly 5.0, ci exactly 2.0 — should be STRONG."""
        score, label, downgraded = compute_prr_score(100, 5.0, 2.0)
        assert score == 1.0
        assert label == SignalStrength.STRONG

    def test_exact_boundary_prr_3_ci_1_5(self):
        """Boundary condition: prr exactly 3.0, ci exactly 1.5 — should be MODERATE."""
        score, label, downgraded = compute_prr_score(50, 3.0, 1.5)
        assert score == 0.66
        assert label == SignalStrength.MODERATE


# ================================================================
# Confidence formula
# ================================================================

class TestComputeConfidence:

    def test_all_max_scores(self):
        """PRR_score=1.0, grade=A, plausibility=HIGH → 0.40+0.40+0.20 = 1.0"""
        conf = compute_confidence(1.0, "A", "HIGH")
        assert conf == pytest.approx(1.0, abs=1e-4)

    def test_all_zero_scores(self):
        conf = compute_confidence(0.0, "C", "LOW")
        assert conf == pytest.approx(0.0, abs=1e-4)

    def test_example_ozempic_pancreatitis(self):
        """PRR_score=0.66, grade=A, plausibility=HIGH → 0.264+0.40+0.20 = 0.864"""
        conf = compute_confidence(0.66, "A", "HIGH")
        assert conf == pytest.approx(0.864, abs=1e-3)

    def test_unknown_plausibility_treated_as_zero(self):
        conf_unknown = compute_confidence(0.66, "B", "UNKNOWN")
        conf_low = compute_confidence(0.66, "B", "LOW")
        assert conf_unknown == conf_low

    def test_grade_b_moderate_plausibility(self):
        """0.40×0.66 + 0.40×0.5 + 0.20×0.5 = 0.264+0.20+0.10 = 0.564"""
        conf = compute_confidence(0.66, "B", "MODERATE")
        assert conf == pytest.approx(0.564, abs=1e-3)


# ================================================================
# Escalation rules
# ================================================================

class TestDeriveEscalation:

    def test_high_confidence_strong_signal_escalates(self):
        decision = derive_escalation(0.864, SignalStrength.STRONG)
        assert decision == EscalationDecision.ESCALATE

    def test_high_confidence_moderate_signal_escalates(self):
        decision = derive_escalation(0.75, SignalStrength.MODERATE)
        assert decision == EscalationDecision.ESCALATE

    def test_high_confidence_weak_signal_does_not_escalate_to_escalate(self):
        """Confidence ≥ 0.70 but WEAK signal → MONITOR, not ESCALATE."""
        decision = derive_escalation(0.72, SignalStrength.WEAK)
        assert decision == EscalationDecision.MONITOR

    def test_mid_confidence_monitors(self):
        decision = derive_escalation(0.50, SignalStrength.MODERATE)
        assert decision == EscalationDecision.MONITOR

    def test_low_confidence_no_escalation(self):
        decision = derive_escalation(0.20, SignalStrength.NO_SIGNAL)
        assert decision == EscalationDecision.DO_NOT_ESCALATE

    def test_boundary_confidence_0_35_monitors(self):
        decision = derive_escalation(0.35, SignalStrength.WEAK)
        assert decision == EscalationDecision.MONITOR

    def test_boundary_confidence_just_below_monitor(self):
        decision = derive_escalation(0.34, SignalStrength.WEAK)
        assert decision == EscalationDecision.DO_NOT_ESCALATE
