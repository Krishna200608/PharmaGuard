"""
tests/test_error_taxonomy.py - Unit tests for PharmaGuard Error Taxonomy.

Validates:
- All 7 defined taxonomy categories are non-empty and backed by real artifacts.
- montelukast::suicidal_ideation classifies as MECHANISTIC_UNCERTAINTY and CROSS_SOURCE_DISCORDANCE.
- metformin::hypoglycaemia classifies as CONFOUNDED_SIGNAL and CROSS_SOURCE_DISCORDANCE.
- The 3 zero-report edge cases classify strictly as ZERO_REPORT_EDGE_CASE only.
- Critic probe leakage cases count matches the 4 flagged cases.
- ReAct agent architecture divergence matches the 4 divergent pairs.
- Gate artifacts match the 8 FAERS-zeroing affected pairs.
- All classifications have non-empty, valid evidence citations.
"""

import json
from pathlib import Path
import pytest

from scripts.research.error_taxonomy import (
    TAXONOMY_CATEGORIES,
    build_error_taxonomy,
    save_taxonomy_results,
)


@pytest.fixture(scope="module")
def taxonomy_data():
    """Build taxonomy data once for all test cases."""
    return build_error_taxonomy()


def test_taxonomy_categories_defined_and_non_empty(taxonomy_data):
    """Verify all 7 categories exist in the summary counts and have at least 1 supporting pair."""
    summary_b = taxonomy_data["summary_counts"]["benchmark_pairs"]
    summary_t = taxonomy_data["summary_counts"]["all_evaluated_cases"]

    assert len(TAXONOMY_CATEGORIES) == 7
    for cat in TAXONOMY_CATEGORIES:
        assert cat in summary_b
        assert cat in summary_t
        # Benchmark count >= 1 for all categories
        assert summary_b[cat] >= 1, f"Category {cat} has 0 benchmark pairs!"
        # Total cases >= 1
        assert summary_t[cat] >= 1, f"Category {cat} has 0 total cases!"


def test_montelukast_classification(taxonomy_data):
    """montelukast::suicidal_ideation must contain MECHANISTIC_UNCERTAINTY and CROSS_SOURCE_DISCORDANCE."""
    pair_key = "montelukast::suicidal_ideation"
    assert pair_key in taxonomy_data["benchmark_pairs"]
    item = taxonomy_data["benchmark_pairs"][pair_key]
    cats = item["categories"]

    assert "MECHANISTIC_UNCERTAINTY" in cats
    assert "CROSS_SOURCE_DISCORDANCE" in cats
    assert "LLM_MEMORIZATION_LEAKAGE" in cats
    assert "GATE_ARTIFACT" in cats
    assert "AGENT_ARCHITECTURE_DIVERGENCE" in cats

    # Check evidence citations
    assert "outputs/eval-run-" in item["evidence"]["MECHANISTIC_UNCERTAINTY"]
    assert "Strict False Negative" in item["evidence"]["MECHANISTIC_UNCERTAINTY"]
    assert "scripts/dev/backfill_agreement.py" in item["evidence"]["CROSS_SOURCE_DISCORDANCE"]


def test_metformin_classification(taxonomy_data):
    """metformin::hypoglycaemia must contain CONFOUNDED_SIGNAL and CROSS_SOURCE_DISCORDANCE."""
    pair_key = "metformin::hypoglycaemia"
    assert pair_key in taxonomy_data["benchmark_pairs"]
    item = taxonomy_data["benchmark_pairs"][pair_key]
    cats = item["categories"]

    assert "CONFOUNDED_SIGNAL" in cats
    assert "CROSS_SOURCE_DISCORDANCE" in cats
    assert "GATE_ARTIFACT" in cats

    # Check evidence citations
    assert "outputs/research/stability" in item["evidence"]["CONFOUNDED_SIGNAL"]
    assert "discount_factor" in item["evidence"]["CONFOUNDED_SIGNAL"]
    assert "DISCORDANT" in item["evidence"]["CROSS_SOURCE_DISCORDANCE"]


def test_zero_report_edge_cases_exclusive(taxonomy_data):
    """The 3 zero-report pairs must classify as ZERO_REPORT_EDGE_CASE only (no failure modes)."""
    zero_pairs = [
        "atorvastatin::common_cold",
        "imatinib::tooth_eruption",
        "adalimumab::frostbite",
    ]
    for pk in zero_pairs:
        assert pk in taxonomy_data["benchmark_pairs"]
        item = taxonomy_data["benchmark_pairs"][pk]
        assert item["categories"] == ["ZERO_REPORT_EDGE_CASE"], (
            f"Zero report pair {pk} has unexpected categories: {item['categories']}"
        )
        assert "pharmaguard/data/ground_truth.json" in item["evidence"]["ZERO_REPORT_EDGE_CASE"]


def test_leakage_critic_cases(taxonomy_data):
    """Verify LLM_MEMORIZATION_LEAKAGE has exactly 4 cases across all evaluated cases."""
    summary_t = taxonomy_data["summary_counts"]["all_evaluated_cases"]
    assert summary_t["LLM_MEMORIZATION_LEAKAGE"] == 4

    # 1 benchmark + 3 supplementary
    assert "montelukast::suicidal_ideation" in taxonomy_data["benchmark_pairs"]
    assert "LLM_MEMORIZATION_LEAKAGE" in taxonomy_data["benchmark_pairs"]["montelukast::suicidal_ideation"]["categories"]

    probe_cases = taxonomy_data["supplementary_probe_cases"]
    for pk in ["topiramate::hypohidrosis", "tamsulosin::intraoperative_floppy_iris_syndrome", "terbinafine::ageusia"]:
        assert pk in probe_cases
        assert "LLM_MEMORIZATION_LEAKAGE" in probe_cases[pk]["categories"]


def test_agent_architecture_divergence_cases(taxonomy_data):
    """Verify AGENT_ARCHITECTURE_DIVERGENCE contains the 4 documented divergent pairs."""
    divergent_pairs = [
        "montelukast::suicidal_ideation",
        "liraglutide::pancreatic_cancer",
        "atorvastatin::dementia",
        "albuterol::suicidal_ideation",
    ]
    summary_b = taxonomy_data["summary_counts"]["benchmark_pairs"]
    assert summary_b["AGENT_ARCHITECTURE_DIVERGENCE"] == 4

    for pk in divergent_pairs:
        assert "AGENT_ARCHITECTURE_DIVERGENCE" in taxonomy_data["benchmark_pairs"][pk]["categories"]
        assert "outputs/react_agent_agreement_report.json" in taxonomy_data["benchmark_pairs"][pk]["evidence"]["AGENT_ARCHITECTURE_DIVERGENCE"]


def test_gate_artifact_cases(taxonomy_data):
    """Verify GATE_ARTIFACT has exactly 8 benchmark pairs from FAERS ablation zeroing."""
    summary_b = taxonomy_data["summary_counts"]["benchmark_pairs"]
    assert summary_b["GATE_ARTIFACT"] == 8

    expected_gate_pairs = [
        "ciprofloxacin::tendon_rupture",
        "clozapine::agranulocytosis",
        "isotretinoin::teratogenicity",
        "metformin::hypoglycaemia",
        "montelukast::suicidal_ideation",
        "pembrolizumab::pneumonitis",
        "rosiglitazone::myocardial_infarction",
        "valproic_acid::hepatotoxicity",
    ]
    for pk in expected_gate_pairs:
        assert "GATE_ARTIFACT" in taxonomy_data["benchmark_pairs"][pk]["categories"]


def test_amoxicillin_clean_performance(taxonomy_data):
    """amoxicillin::tendon_rupture is a clean negative control with no anomalous categories."""
    item = taxonomy_data["benchmark_pairs"]["amoxicillin::tendon_rupture"]
    assert item["categories"] == []
    assert item["evidence"] == {}


def test_evidence_citations_integrity(taxonomy_data):
    """Every category assigned to any pair must have an evidence citation string."""
    for pk, item in taxonomy_data["benchmark_pairs"].items():
        for cat in item["categories"]:
            assert cat in item["evidence"]
            assert len(item["evidence"][cat]) > 10

    for pk, item in taxonomy_data["supplementary_probe_cases"].items():
        for cat in item["categories"]:
            assert cat in item["evidence"]
            assert len(item["evidence"][cat]) > 10


def test_saved_json_artifact_matches(tmp_path, taxonomy_data):
    """Verify saving and reloading taxonomy JSON preserves all fields."""
    test_file = tmp_path / "taxonomy_test.json"
    save_taxonomy_results(taxonomy_data, test_file)
    assert test_file.exists()

    with open(test_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["metadata"]["total_benchmark_pairs"] == 15
    assert loaded["summary_counts"] == taxonomy_data["summary_counts"]