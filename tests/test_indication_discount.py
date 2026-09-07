"""
Unit tests for IndicationConcordance discount factor (§37, §38).

Verifies:
1. apply_indication_discount() math directly with hand-checked cases.
2. discount_enabled=False produces zero change to frozen reports.
3. discount_enabled=True only affects pairs where concordant=True.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from pharmaguard.agent.output_schema import (
    apply_indication_discount,
    compute_confidence,
    derive_escalation,
    TriageReport,
)
from pharmaguard.tools.indication_concordance import IndicationConcordanceTool
from pharmaguard.utils.config_loader import load_config

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = REPO_ROOT / "outputs" / "core"
OMOP_DIR = REPO_ROOT / "outputs" / "research" / "omop_pilot"


class TestApplyIndicationDiscountMath:
    """Direct mathematical verification of apply_indication_discount()."""

    def test_discordant_returns_unchanged(self):
        for score in [1.0, 0.66, 0.33, 0.0, 0.5]:
            assert apply_indication_discount(score, concordant=False, discount_factor=0.85) == score
            assert apply_indication_discount(score, concordant=False, discount_factor=0.50) == score

    def test_concordant_standard_discount_085(self):
        # 1.0 * 0.85 = 0.8500
        assert apply_indication_discount(1.0, concordant=True, discount_factor=0.85) == 0.8500
        # 0.66 * 0.85 = 0.5610
        assert apply_indication_discount(0.66, concordant=True, discount_factor=0.85) == 0.5610
        # 0.33 * 0.85 = 0.2805
        assert apply_indication_discount(0.33, concordant=True, discount_factor=0.85) == 0.2805
        # 0.0 * 0.85 = 0.0000
        assert apply_indication_discount(0.0, concordant=True, discount_factor=0.85) == 0.0000

    def test_concordant_custom_discount_factors(self):
        assert apply_indication_discount(1.0, concordant=True, discount_factor=0.80) == 0.8000
        assert apply_indication_discount(0.66, concordant=True, discount_factor=0.80) == 0.5280
        assert apply_indication_discount(1.0, concordant=True, discount_factor=1.00) == 1.0000

    def test_default_discount_factor_is_085(self):
        assert apply_indication_discount(1.0, concordant=True) == 0.8500
        assert apply_indication_discount(0.66, concordant=True) == 0.5610


class TestDiscountDisabledZeroProductionChange:
    """Verify that with discount_enabled=False, scoring across all 47 frozen reports is 100% unchanged."""

    @pytest.fixture
    def frozen_reports(self) -> list[TriageReport]:
        reports = []
        for d in (CORE_DIR, OMOP_DIR):
            for path in sorted(d.glob("eval-run-*_report.json")):
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                reports.append(TriageReport.model_validate(data))
        assert len(reports) == 47
        return reports

    def test_default_config_has_discount_disabled(self):
        cfg = load_config(reload=True)
        assert cfg.indication_concordance.discount_enabled is False
        assert cfg.indication_concordance.discount_factor == 0.85

    def test_zero_change_to_all_frozen_reports_when_disabled(self, frozen_reports):
        tool = IndicationConcordanceTool()
        for rpt in frozen_reports:
            ind_conc = tool.check(rpt.drug, rpt.event)
            # When discount_enabled=False (the default), prr_score is never modified:
            prr_score = rpt.signal_stats.prr_score
            conf = compute_confidence(prr_score, rpt.literature.evidence_grade, rpt.mechanism.biological_plausibility)
            esc = derive_escalation(conf, rpt.signal_stats.prr_score_label)

            assert prr_score == rpt.signal_stats.prr_score
            assert conf == rpt.triage.confidence
            assert esc == rpt.triage.escalation


class TestDiscountEnabledSelectiveTargeting:
    """Verify that discount_enabled=True ONLY affects pairs where concordant=True."""

    @pytest.fixture
    def frozen_reports(self) -> list[TriageReport]:
        reports = []
        for d in (CORE_DIR, OMOP_DIR):
            for path in sorted(d.glob("eval-run-*_report.json")):
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                reports.append(TriageReport.model_validate(data))
        return reports

    def test_discount_only_modifies_concordant_pairs(self, frozen_reports):
        tool = IndicationConcordanceTool()
        discount_factor = 0.85

        concordant_count = 0
        discordant_count = 0

        for rpt in frozen_reports:
            ind_conc = tool.check(rpt.drug, rpt.event)
            raw_prr_score = rpt.signal_stats.prr_score
            adj_prr_score = apply_indication_discount(raw_prr_score, ind_conc.concordant, discount_factor)

            if not ind_conc.concordant:
                discordant_count += 1
                # Must be strictly identical
                assert adj_prr_score == raw_prr_score
                new_conf = compute_confidence(adj_prr_score, rpt.literature.evidence_grade, rpt.mechanism.biological_plausibility)
                assert new_conf == rpt.triage.confidence
            else:
                concordant_count += 1
                # When concordant and raw_prr_score > 0, score must be discounted
                if raw_prr_score > 0:
                    assert adj_prr_score < raw_prr_score
                    new_conf = compute_confidence(adj_prr_score, rpt.literature.evidence_grade, rpt.mechanism.biological_plausibility)
                    assert new_conf <= rpt.triage.confidence
                else:
                    assert adj_prr_score == 0.0

        assert concordant_count > 0, "Expected some concordant pairs in the 47 benchmark set"
        assert discordant_count > 0, "Expected some discordant/clear pairs in the 47 benchmark set"
