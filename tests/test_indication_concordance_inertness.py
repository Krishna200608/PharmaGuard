"""
Unit tests for IndicationConcordance scoring inertness (DECISIONS.md §35.7).

CRITICAL INVARIANT:
  IndicationConcordance is strictly informational. It MUST NEVER influence:
  - FAERS PRR score or SignalStrength label
  - PubMed Grade score
  - ChEMBL Biological Plausibility score
  - Composite confidence score
  - EscalationDecision (ESCALATE / MONITOR / DO_NOT_ESCALATE)

If any test in this file fails, DO NOT patch scoring logic — stop immediately
and report the isolation breach.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
import pytest

from pharmaguard.agent.output_schema import (
    IndicationConcordance,
    TriageReport,
    compute_confidence,
    derive_escalation,
    EscalationDecision,
    SignalStrength,
    EvidenceGrade,
    PlausibilityLevel,
)
from pharmaguard.tools.indication_concordance import (
    IndicationConcordanceTool,
    CONFOUNDING_RULES,
    check_indication_concordance,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = REPO_ROOT / "outputs" / "core"
OMOP_DIR = REPO_ROOT / "outputs" / "research" / "omop_pilot"


class TestScoringInertnessSignatures:
    """Verify that scoring functions have zero parameters related to indication concordance."""

    def test_compute_confidence_signature_isolation(self):
        sig = inspect.signature(compute_confidence)
        params = list(sig.parameters.keys())
        assert params == ["prr_score", "grade", "plausibility"], (
            f"compute_confidence signature leaked parameters: {params}"
        )

    def test_derive_escalation_signature_isolation(self):
        sig = inspect.signature(derive_escalation)
        params = list(sig.parameters.keys())
        assert params == ["confidence", "signal_strength"], (
            f"derive_escalation signature leaked parameters: {params}"
        )


class TestFrozenReportsScoringInertness:
    """Assert mathematical identity of confidence and escalation across all 47 frozen reports."""

    @pytest.fixture
    def all_frozen_reports(self) -> list[TriageReport]:
        reports = []
        for directory in (CORE_DIR, OMOP_DIR):
            for path in sorted(directory.glob("eval-run-*_report.json")):
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                reports.append(TriageReport.model_validate(data))
        assert len(reports) == 47, f"Expected 47 frozen reports, found {len(reports)}"
        return reports

    def test_confidence_and_escalation_independent_of_indication_flag(self, all_frozen_reports):
        """
        For every frozen report, re-evaluating scoring with:
          1. indication_concordance = None
          2. indication_concordance = True (forced flag)
          3. indication_concordance = False (forced clear)
        MUST yield mathematically identical confidence and identical escalation decisions.
        """
        tool = IndicationConcordanceTool()

        for rpt in all_frozen_reports:
            # 1. Baseline values from frozen report
            frozen_conf = rpt.triage.confidence
            frozen_esc = rpt.triage.escalation

            # Re-evaluate independently
            calc_conf = compute_confidence(
                rpt.signal_stats.prr_score,
                rpt.literature.evidence_grade,
                rpt.mechanism.biological_plausibility,
            )
            calc_esc = derive_escalation(calc_conf, rpt.signal_stats.prr_score_label)

            assert calc_conf == frozen_conf, (
                f"Confidence mismatch for {rpt.drug}::{rpt.event}: {calc_conf} != {frozen_conf}"
            )
            assert calc_esc == frozen_esc, (
                f"Escalation mismatch for {rpt.drug}::{rpt.event}: {calc_esc} != {frozen_esc}"
            )

            # 2. Test with live computed concordance
            live_ic = tool.check(rpt.drug, rpt.event)
            rpt_with_live = rpt.model_copy(update={"indication_concordance": live_ic})

            # Re-run scoring
            conf_live = compute_confidence(
                rpt_with_live.signal_stats.prr_score,
                rpt_with_live.literature.evidence_grade,
                rpt_with_live.mechanism.biological_plausibility,
            )
            esc_live = derive_escalation(conf_live, rpt_with_live.signal_stats.prr_score_label)

            assert conf_live == frozen_conf, f"Live IC altered confidence for {rpt.drug}::{rpt.event}"
            assert esc_live == frozen_esc, f"Live IC altered escalation for {rpt.drug}::{rpt.event}"

            # 3. Test with synthetic forced TRUE concordance
            forced_true_ic = IndicationConcordance(
                concordant=True,
                overlap_category="Synthetic Test Category",
                rationale="Synthetic test rationale",
                rule_source="Test Citation (2026)",
            )
            rpt_forced_true = rpt.model_copy(update={"indication_concordance": forced_true_ic})

            conf_true = compute_confidence(
                rpt_forced_true.signal_stats.prr_score,
                rpt_forced_true.literature.evidence_grade,
                rpt_forced_true.mechanism.biological_plausibility,
            )
            esc_true = derive_escalation(conf_true, rpt_forced_true.signal_stats.prr_score_label)

            assert conf_true == frozen_conf, f"Forced True IC altered confidence for {rpt.drug}::{rpt.event}"
            assert esc_true == frozen_esc, f"Forced True IC altered escalation for {rpt.drug}::{rpt.event}"

            # 4. Test with synthetic forced FALSE concordance
            forced_false_ic = IndicationConcordance(
                concordant=False,
                overlap_category=None,
                rationale="",
                rule_source="",
            )
            rpt_forced_false = rpt.model_copy(update={"indication_concordance": forced_false_ic})

            conf_false = compute_confidence(
                rpt_forced_false.signal_stats.prr_score,
                rpt_forced_false.literature.evidence_grade,
                rpt_forced_false.mechanism.biological_plausibility,
            )
            esc_false = derive_escalation(conf_false, rpt_forced_false.signal_stats.prr_score_label)

            assert conf_false == frozen_conf, f"Forced False IC altered confidence for {rpt.drug}::{rpt.event}"
            assert esc_false == frozen_esc, f"Forced False IC altered escalation for {rpt.drug}::{rpt.event}"


class TestRuleTableClinicalCoverage:
    """Verify all 7 rules trigger as documented in DECISIONS.md §35.3."""

    def test_all_seven_rules_present(self):
        rule_ids = [r.rule_id for r in CONFOUNDING_RULES]
        expected_ids = [f"IND-CONF-0{i}" for i in range(1, 8)]
        assert rule_ids == expected_ids

    def test_rule_table_reproduces_35_4_descriptive_results(self):
        """Assert exact reproduction of the 7 flagged pairs from DECISIONS.md §35.4."""
        tool = IndicationConcordanceTool()

        with open(REPO_ROOT / "pharmaguard" / "data" / "ground_truth.json", "r", encoding="utf-8") as fh:
            core_pairs = json.load(fh)["pairs"]

        with open(REPO_ROOT / "pharmaguard" / "data" / "ground_truth_omop_pilot.json", "r", encoding="utf-8") as fh:
            omop_pairs = json.load(fh)["pairs"]

        core_flagged = [
            (p["drug_canonical"], p["event_meddra_pt"])
            for p in core_pairs
            if tool.check(p["drug_canonical"], p["event_meddra_pt"]).concordant
        ]
        assert core_flagged == [("metformin", "hypoglycaemia")], (
            f"Core benchmark flagging mismatch: {core_flagged}"
        )

        omop_flagged = [
            (p["drug_canonical"], p["event_meddra_pt"])
            for p in omop_pairs
            if tool.check(p["drug_canonical"], p["event_meddra_pt"]).concordant
        ]
        expected_omop = [
            ("hydrochlorothiazide", "acute_kidney_injury"),
            ("lisinopril", "acute_kidney_injury"),
            ("amlodipine", "myocardial_infarction"),
            ("dipyridamole", "myocardial_infarction"),
            ("nifedipine", "myocardial_infarction"),
            ("ketoprofen", "gastrointestinal_haemorrhage"),
        ]
        assert sorted(omop_flagged) == sorted(expected_omop), (
            f"OMOP benchmark flagging mismatch: {omop_flagged}"
        )

    def test_known_negative_cases_remain_clear(self):
        """Verify that §31 false negatives without indication overlap are NOT flagged (DECISIONS.md §35.5)."""
        tool = IndicationConcordanceTool()

        # Atorvastatin :: dementia — statin indicated for dyslipidemia (C10), dementia is neurodegenerative
        res = tool.check("atorvastatin", "dementia")
        assert not res.concordant

        # SSRIs :: gastrointestinal_haemorrhage — SSRIs are psychotropics (N06AB), bleeding is anti-hemostatic toxicity
        for ssri in ("citalopram", "fluoxetine", "sertraline"):
            res = tool.check(ssri, "gastrointestinal_haemorrhage")
            assert not res.concordant, f"{ssri} :: GI haemorrhage should NOT be flagged"

        # Captopril :: hepatotoxicity — idiosyncratic metabolic toxicity, zero indication overlap
        res = tool.check("captopril", "hepatotoxicity")
        assert not res.concordant


class TestOfflineIndicationConcordanceReproducibility:
    """Confirm IndicationConcordanceTool introduces zero live network calls beyond static cache."""

    def test_offline_concordance_all_47_benchmark_pairs(self):
        """Mock urllib.request.urlopen to forbid any network access; assert all 47 pairs evaluate successfully."""
        from unittest.mock import patch

        tool = IndicationConcordanceTool()

        with open(REPO_ROOT / "pharmaguard" / "data" / "ground_truth.json", "r", encoding="utf-8") as fh:
            core_pairs = json.load(fh)["pairs"]

        with open(REPO_ROOT / "pharmaguard" / "data" / "ground_truth_omop_pilot.json", "r", encoding="utf-8") as fh:
            omop_pairs = json.load(fh)["pairs"]

        all_pairs = core_pairs + omop_pairs
        assert len(all_pairs) == 47

        with patch("urllib.request.urlopen", side_effect=RuntimeError("Offline: Network call forbidden")):
            flagged_count = 0
            for p in all_pairs:
                res = tool.check(p["drug_canonical"], p["event_meddra_pt"])
                assert isinstance(res, IndicationConcordance)
                if res.concordant:
                    flagged_count += 1

            assert flagged_count == 7, f"Expected exactly 7 flagged pairs offline, got {flagged_count}"

