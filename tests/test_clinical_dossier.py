"""
Unit Tests for Clinical Report Generator
========================================
Validates that generate_clinical_dossier_markdown produces standardized,
regulatory-compliant Pharmacovigilance Safety Briefing dossiers from both
TriageReport instances and serialized dictionaries without crashing or schema errors.
"""
from datetime import datetime, timezone
import pytest
from scripts.dashboard_modules.reports import generate_clinical_dossier_markdown
from pharmaguard.agent.output_schema import (
    TriageReport,
    TriageOutput,
    SignalStatsOutput,
    MechanismOutput,
    LiteratureOutput,
    IndicationConcordance,
    EscalationDecision,
    SignalStrength,
    EvidenceGrade,
    PlausibilityLevel,
    PlausibilitySource,
)


@pytest.fixture
def sample_escalate_report() -> TriageReport:
    """Fixture providing a confirmed positive ESCALATE report."""
    return TriageReport(
        drug="ciprofloxacin",
        event="tendon rupture",
        run_id="run-cipro-test-01",
        prompts_version="v1.0",
        signal_stats=SignalStatsOutput(
            report_count=2340,
            prr=8.45,
            prr_lower_ci=6.20,
            prr_score=1.0,
            prr_score_label=SignalStrength.STRONG,
            ror=9.12,
            ror_lower_ci=6.80,
            ci_downgraded=False,
            source_endpoint="openfda_faers",
            data_pulled_at=datetime.now(timezone.utc),
        ),
        mechanism=MechanismOutput(
            chembl_id="CHEMBL8",
            moa="DNA gyrase and topoisomerase IV inhibitor",
            biological_plausibility=PlausibilityLevel.MODERATE,
            plausibility_score=0.50,
            plausibility_source=PlausibilitySource.HUMAN_CURATED,
            plausibility_rationale="Inhibition of tenocyte metabolism and chelation of intracellular magnesium.",
        ),
        literature=LiteratureOutput(
            pubmed_query="ciprofloxacin tendon rupture",
            abstracts_retrieved=15,
            evidence_grade=EvidenceGrade.A,
            grade_score=1.0,
            supporting_pmids=["12345678", "87654321"],
            evidence_summary="Extensive epidemiological cohort and case-control studies establish strong hazard ratio for Achilles tendon rupture.",
        ),
        indication_concordance=IndicationConcordance(
            concordant=False,
            overlap_category="None",
            rationale="Infection indication does not overlap with musculoskeletal rupture.",
            rule_source="None",
        ),
        triage=TriageOutput(
            signal_strength=SignalStrength.STRONG,
            evidence_grade=EvidenceGrade.A,
            escalation=EscalationDecision.ESCALATE,
            confidence=0.8000,
            prompts_version="v1.0",
            agent_reasoning_trace=[
                "FAERS disproportionality is STRONG (PRR=8.45, Lower CI=6.20)",
                "ChEMBL target confirms MODERATE plausibility",
                "PubMed epidemiological literature confirms Grade A evidence",
                "Composite confidence 0.8000 exceeds 0.70 threshold -> ESCALATE",
            ],
        ),
    )


@pytest.fixture
def sample_monitor_report() -> TriageReport:
    """Fixture providing a MONITOR report."""
    return TriageReport(
        drug="montelukast",
        event="suicidal ideation",
        run_id="run-mont-test-02",
        prompts_version="v1.0",
        signal_stats=SignalStatsOutput(
            report_count=3540,
            prr=4.12,
            prr_lower_ci=3.10,
            prr_score=0.66,
            prr_score_label=SignalStrength.MODERATE,
            ror=4.30,
            ror_lower_ci=3.20,
            ci_downgraded=False,
            source_endpoint="openfda_faers",
            data_pulled_at=datetime.now(timezone.utc),
        ),
        mechanism=MechanismOutput(
            chembl_id="CHEMBL1486",
            moa="CysLT1 receptor antagonist",
            biological_plausibility=PlausibilityLevel.LOW,
            plausibility_score=0.0,
            plausibility_source=PlausibilitySource.HUMAN_CURATED,
            plausibility_rationale="No established central nervous system target pathway.",
        ),
        literature=LiteratureOutput(
            pubmed_query="montelukast suicidal ideation",
            abstracts_retrieved=10,
            evidence_grade=EvidenceGrade.A,
            grade_score=1.0,
            supporting_pmids=["22334455"],
            evidence_summary="Observational and FDA review data describe neuropsychiatric events.",
        ),
        indication_concordance=IndicationConcordance(
            concordant=False,
            overlap_category="None",
            rationale="Respiratory indication does not overlap with neuropsychiatric symptoms.",
            rule_source="None",
        ),
        triage=TriageOutput(
            signal_strength=SignalStrength.MODERATE,
            evidence_grade=EvidenceGrade.A,
            escalation=EscalationDecision.MONITOR,
            confidence=0.6640,
            prompts_version="v1.0",
            agent_reasoning_trace=[
                "FAERS signal is MODERATE",
                "ChEMBL plausibility is LOW (0.0)",
                "PubMed literature is Grade A (1.0)",
                "Composite confidence 0.6640 lies in MONITOR band [0.35, 0.70)",
            ],
        ),
    )


def test_generate_dossier_escalate(sample_escalate_report):
    """Verify markdown dossier for high-priority escalation."""
    md = generate_clinical_dossier_markdown(sample_escalate_report)
    assert "# 🛡️ PharmaGuard — Clinical Safety Briefing & Triage Dossier" in md
    assert "Ciprofloxacin" in md
    assert "Tendon Rupture" in md
    assert "ESCALATE" in md
    assert "🚨 HIGH-PRIORITY REGULATORY ESCALATION" in md
    assert "0.8000" in md
    assert "SHA256:" in md
    assert "PMID 12345678" in md
    assert "0.40 * (A)" not in md
    assert "1.00" in md  # Grade A numeric sub-score


def test_generate_dossier_monitor(sample_monitor_report):
    """Verify markdown dossier for active watchlist surveillance."""
    md = generate_clinical_dossier_markdown(sample_monitor_report)
    assert "Montelukast" in md
    assert "Suicidal Ideation" in md
    assert "MONITOR" in md
    assert "👁️ ACTIVE PHARMACOVIGILANCE WATCHLIST SURVEILLANCE" in md
    assert "0.6640" in md
    assert "DISCORDANT" in md


def test_generate_dossier_from_dict(sample_escalate_report):
    """Verify that generate_clinical_dossier_markdown transparently accepts raw dictionaries."""
    raw_dict = sample_escalate_report.model_dump(mode="json")
    assert isinstance(raw_dict, dict)
    md = generate_clinical_dossier_markdown(raw_dict)
    assert "Ciprofloxacin" in md
    assert "ESCALATE" in md
    assert "SHA256:" in md
