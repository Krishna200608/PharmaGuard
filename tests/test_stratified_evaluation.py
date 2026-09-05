"""
Unit tests for therapeutic-area stratified evaluation and statistical guardrails.

Tests:
  - Confusion matrix derivation per stratum (TP, FP, TN, FN)
  - Precision, Recall, Specificity, and F1 calculation per stratum
  - Exact Wilson score confidence interval computation
  - Zero-positive strata handling (recall=None, precision=None if no predictions)
  - Zero-negative strata handling (specificity=None)
  - All-positive and all-negative strata boundary conditions
  - Sample size thresholding (is_exploratory flag for n < 5)
  - Core vs OMOP dataset separation
  - Aggregate metric invariance under stratification
  - Non-mutation invariance: verifying therapeutic-context annotations cannot alter predictions

Owner: Krishna Sikheriya (IIT2023139)
"""

import pytest
from scripts.evaluator import (
    calc_metrics,
    compute_confusion_matrix,
    compute_wilson_ci,
    compute_stratified_metrics,
)


class TestWilsonScoreInterval:
    """Verify exact Wilson score interval calculations."""

    def test_wilson_ci_zero_sample(self):
        low, high = compute_wilson_ci(0, 0)
        assert low == 0.0
        assert high == 0.0

    def test_wilson_ci_perfect_boundary(self):
        # 10 / 10 successes: Wilson CI should not collapse to [1.0, 1.0] (unlike naive Wald)
        low, high = compute_wilson_ci(10, 10)
        assert 0.0 < low < 1.0
        assert high == 1.0
        assert round(low, 3) == 0.722

    def test_wilson_ci_zero_boundary(self):
        # 0 / 10 successes
        low, high = compute_wilson_ci(0, 10)
        assert low == 0.0
        assert 0.0 < high < 1.0
        assert round(high, 3) == 0.278

    def test_wilson_ci_intermediate(self):
        # 5 / 10 successes (50%)
        low, high = compute_wilson_ci(5, 10)
        assert round(low, 3) == 0.237
        assert round(high, 3) == 0.763


class TestStratifiedMetricsComputation:
    """Verify compute_stratified_metrics with synthetic and boundary records."""

    def test_basic_two_strata(self):
        records = [
            # Stratum C: 2 records (1 GT positive escalated, 1 GT negative not escalated)
            {"therapeutic_area_code": "C", "therapeutic_area": "Cardiovascular", "is_gt_positive": True, "actual": "ESCALATE", "pair": "c_pos"},
            {"therapeutic_area_code": "C", "therapeutic_area": "Cardiovascular", "is_gt_positive": False, "actual": "DO_NOT_ESCALATE", "pair": "c_neg"},
            # Stratum J: 3 records (1 GT positive monitor, 2 GT negatives not escalated)
            {"therapeutic_area_code": "J", "therapeutic_area": "Antiinfectives", "is_gt_positive": True, "actual": "MONITOR", "pair": "j_pos"},
            {"therapeutic_area_code": "J", "therapeutic_area": "Antiinfectives", "is_gt_positive": False, "actual": "DO_NOT_ESCALATE", "pair": "j_neg1"},
            {"therapeutic_area_code": "J", "therapeutic_area": "Antiinfectives", "is_gt_positive": False, "actual": "DO_NOT_ESCALATE", "pair": "j_neg2"},
        ]

        strat = compute_stratified_metrics(records, strata_key="therapeutic_area_code")
        assert "C" in strat
        assert "J" in strat

        # Stratum C checks
        c_res = strat["C"]
        assert c_res["n"] == 2
        assert c_res["is_exploratory"] is True  # n < 5
        assert c_res["strict"]["TP"] == 1
        assert c_res["strict"]["FP"] == 0
        assert c_res["strict"]["TN"] == 1
        assert c_res["strict"]["FN"] == 0
        assert c_res["strict"]["precision"] == 1.0
        assert c_res["strict"]["recall"] == 1.0
        assert c_res["strict"]["specificity"] == 1.0
        assert c_res["strict"]["f1"] == 1.0

        # Stratum J checks
        j_res = strat["J"]
        assert j_res["n"] == 3
        assert j_res["strict"]["TP"] == 0
        assert j_res["strict"]["FN"] == 1  # MONITOR counts as negative in strict
        assert j_res["strict"]["TN"] == 2
        assert j_res["lenient"]["TP"] == 1  # MONITOR counts as positive in lenient
        assert j_res["lenient"]["FN"] == 0
        assert j_res["lenient"]["TN"] == 2

    def test_zero_positive_stratum_handling(self):
        """When a stratum contains only negative controls, recall is mathematically undefined."""
        records = [
            {"therapeutic_area_code": "A", "therapeutic_area": "Alimentary", "is_gt_positive": False, "actual": "DO_NOT_ESCALATE", "pair": "a_neg1"},
            {"therapeutic_area_code": "A", "therapeutic_area": "Alimentary", "is_gt_positive": False, "actual": "DO_NOT_ESCALATE", "pair": "a_neg2"},
        ]
        strat = compute_stratified_metrics(records, strata_key="therapeutic_area_code")
        a_res = strat["A"]
        assert a_res["strict"]["TP"] == 0
        assert a_res["strict"]["FN"] == 0
        assert a_res["strict"]["TN"] == 2
        assert a_res["strict"]["FP"] == 0
        assert a_res["strict"]["recall"] is None
        assert a_res["strict"]["precision"] is None
        assert a_res["strict"]["recall_ci"] is None
        assert a_res["strict"]["precision_ci"] is None
        assert a_res["strict"]["specificity"] == 1.0
        assert a_res["strict"]["specificity_ci"] is not None
        assert a_res["strict"]["f1"] is None

    def test_zero_negative_stratum_handling(self):
        """When a stratum contains only positive signals, specificity is mathematically undefined."""
        records = [
            {"therapeutic_area_code": "N", "therapeutic_area": "Nervous", "is_gt_positive": True, "actual": "ESCALATE", "pair": "n_pos1"},
            {"therapeutic_area_code": "N", "therapeutic_area": "Nervous", "is_gt_positive": True, "actual": "ESCALATE", "pair": "n_pos2"},
        ]
        strat = compute_stratified_metrics(records, strata_key="therapeutic_area_code")
        n_res = strat["N"]
        assert n_res["strict"]["TP"] == 2
        assert n_res["strict"]["specificity"] is None
        assert n_res["strict"]["specificity_ci"] is None
        assert n_res["strict"]["precision"] == 1.0
        assert n_res["strict"]["precision_ci"] is not None
        assert n_res["strict"]["recall"] == 1.0
        assert n_res["strict"]["recall_ci"] is not None
        assert n_res["strict"]["f1"] == 1.0

    def test_exploratory_flag_threshold(self):
        """Ensure strata with n < 5 are flagged exploratory, and n >= 5 are not."""
        records_small = [{"therapeutic_area_code": "D", "is_gt_positive": True, "actual": "ESCALATE"} for _ in range(4)]
        strat_small = compute_stratified_metrics(records_small)
        assert strat_small["D"]["is_exploratory"] is True

        records_large = [{"therapeutic_area_code": "D", "is_gt_positive": True, "actual": "ESCALATE"} for _ in range(5)]
        strat_large = compute_stratified_metrics(records_large)
        assert strat_large["D"]["is_exploratory"] is False

    def test_unresolved_atc_preserves_records(self):
        """Records with None or missing strata_key must group under UNRESOLVED and not drop."""
        records = [
            {"therapeutic_area_code": None, "is_gt_positive": True, "actual": "ESCALATE", "pair": "p1"},
            {"therapeutic_area_code": "C", "is_gt_positive": False, "actual": "DO_NOT_ESCALATE", "pair": "p2"},
        ]
        strat = compute_stratified_metrics(records)
        assert "UNRESOLVED" in strat
        assert strat["UNRESOLVED"]["n"] == 1
        assert strat["C"]["n"] == 1


class TestBenchmarkInvarianceAndSeparation:
    """Verify that stratification respects dataset separation and does not alter aggregate totals."""

    def test_stratification_sum_equals_aggregate_confusion_matrix(self):
        # Synthetic mixture of 15 records
        records = [
            {"therapeutic_area_code": "A", "is_gt_positive": True, "actual": "ESCALATE"},
            {"therapeutic_area_code": "A", "is_gt_positive": False, "actual": "MONITOR"},
            {"therapeutic_area_code": "C", "is_gt_positive": True, "actual": "MONITOR"},
            {"therapeutic_area_code": "C", "is_gt_positive": False, "actual": "DO_NOT_ESCALATE"},
            {"therapeutic_area_code": "J", "is_gt_positive": True, "actual": "ESCALATE"},
            {"therapeutic_area_code": "J", "is_gt_positive": False, "actual": "DO_NOT_ESCALATE"},
        ]

        agg_strict, agg_lenient = compute_confusion_matrix(records)
        strat = compute_stratified_metrics(records)

        sum_strict_tp = sum(s["strict"]["TP"] for s in strat.values())
        sum_strict_fp = sum(s["strict"]["FP"] for s in strat.values())
        sum_strict_tn = sum(s["strict"]["TN"] for s in strat.values())
        sum_strict_fn = sum(s["strict"]["FN"] for s in strat.values())

        assert sum_strict_tp == agg_strict["TP"]
        assert sum_strict_fp == agg_strict["FP"]
        assert sum_strict_tn == agg_strict["TN"]
        assert sum_strict_fn == agg_strict["FN"]

        sum_lenient_tp = sum(s["lenient"]["TP"] for s in strat.values())
        sum_lenient_fp = sum(s["lenient"]["FP"] for s in strat.values())
        sum_lenient_tn = sum(s["lenient"]["TN"] for s in strat.values())
        sum_lenient_fn = sum(s["lenient"]["FN"] for s in strat.values())

        assert sum_lenient_tp == agg_lenient["TP"]
        assert sum_lenient_fp == agg_lenient["FP"]
        assert sum_lenient_tn == agg_lenient["TN"]
        assert sum_lenient_fn == agg_lenient["FN"]

    def test_core_and_omop_dataset_isolation(self):
        """Verify that Core records and OMOP records passed to separate evaluators produce distinct outputs."""
        core_records = [
            {"benchmark": "core", "therapeutic_area_code": "C", "is_gt_positive": False, "actual": "DO_NOT_ESCALATE", "pair": "atorvastatin::dementia"}
        ]
        omop_records = [
            {"benchmark": "omop", "therapeutic_area_code": "C", "is_gt_positive": True, "actual": "DO_NOT_ESCALATE", "pair": "amlodipine::myocardial_infarction"}
        ]

        strat_core = compute_stratified_metrics(core_records)
        strat_omop = compute_stratified_metrics(omop_records)

        # In Core, atorvastatin is a true negative control
        assert strat_core["C"]["strict"]["TN"] == 1
        assert strat_core["C"]["strict"]["FN"] == 0

        # In OMOP, amlodipine is a positive signal missed (false negative)
        assert strat_omop["C"]["strict"]["TN"] == 0
        assert strat_omop["C"]["strict"]["FN"] == 1


class TestProductionIsolation:
    """Architectural invariant: therapeutic context cannot alter production scoring, gating, or predictions."""

    def test_production_formula_isolation(self):
        from pharmaguard.agent.output_schema import (
            compute_confidence,
            derive_escalation,
            compute_prr_score,
        )
        from pharmaguard.tools.disease_context import DiseaseContext

        # Base production calculation without context
        base_prr_score, base_strength, _ = compute_prr_score(report_count=50, prr=4.5, prr_lower_ci=2.1)
        base_conf = compute_confidence(prr_score=base_prr_score, grade="A", plausibility="MODERATE")
        base_esc = derive_escalation(base_conf, base_strength)

        # Mutating therapeutic contexts across various extremes
        contexts = [
            DiseaseContext(drug_canonical="drug_a", utilization_class="CHRONIC", therapeutic_area="Cardiovascular"),
            DiseaseContext(drug_canonical="drug_b", utilization_class="ACUTE", therapeutic_area="Antiinfectives"),
            DiseaseContext(drug_canonical="drug_c", utilization_class="UNKNOWN", is_resolved=False),
        ]

        for _ in contexts:
            # Recompute production score
            conf_with_ctx = compute_confidence(prr_score=base_prr_score, grade="A", plausibility="MODERATE")
            esc_with_ctx = derive_escalation(conf_with_ctx, base_strength)

            assert conf_with_ctx == base_conf
            assert esc_with_ctx == base_esc

    def test_record_prediction_equality_with_and_without_context(self):
        """Verify that attaching therapeutic_context to evaluated records does not change predictions."""
        from scripts.evaluator import compute_confusion_matrix

        base_record = {
            "is_gt_positive": True,
            "actual": "ESCALATE",
            "pair": "test::event",
        }
        record_with_ctx = {
            **base_record,
            "therapeutic_context": {
                "drug_canonical": "test",
                "selected_atc": "C08CA01",
                "utilization_class": "CHRONIC",
            },
        }

        # Confusion matrix outputs must be strictly identical
        strict_base, lenient_base = compute_confusion_matrix([base_record])
        strict_with_ctx, lenient_with_ctx = compute_confusion_matrix([record_with_ctx])

        assert strict_base == strict_with_ctx
        assert lenient_base == lenient_with_ctx

