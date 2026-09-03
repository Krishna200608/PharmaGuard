"""
Unit tests for two-stage term canonicalization layer (pharmaguard/utils/canonicalize.py).

Tests exact matching, curated alias resolution, high-confidence fuzzy matching (auto-resolve),
middle-band fuzzy matching (human review flagged), and low-confidence rejection (unmapped).

Grounded in DECISIONS.md / CANONICALIZATION.md.
Owner: Krishna Sikheriya (IIT2023139)
"""

import pytest
from pharmaguard.utils.canonicalize import (
    canonicalize_term,
    CANONICAL_DRUGS,
    CANONICAL_EVENTS,
)


class TestExactMatches:
    """Stage 1A: Exact canonical vocabulary matches."""

    @pytest.mark.parametrize("drug", [
        "montelukast",
        "ciprofloxacin",
        "valproic_acid",
        "metformin",
        "amlodipine",
        "lisinopril",
        "citalopram",
    ])
    def test_canonical_drugs_exact(self, drug):
        res = canonicalize_term(drug, "drug")
        assert res["canonical"] == drug
        assert res["confidence"] == 1.0
        assert res["match_type"] == "exact"
        assert res["needs_human_review"] is False
        assert res["original_input"] == drug

    @pytest.mark.parametrize("event", [
        "suicidal_ideation",
        "myocardial_infarction",
        "hepatotoxicity",
        "acute_kidney_injury",
        "gastrointestinal_haemorrhage",
        "hypoglycaemia",
        "pancreatic_cancer",
    ])
    def test_canonical_events_exact(self, event):
        res = canonicalize_term(event, "event")
        assert res["canonical"] == event
        assert res["confidence"] == 1.0
        assert res["match_type"] == "exact"
        assert res["needs_human_review"] is False
        assert res["original_input"] == event

    def test_case_and_delimiter_insensitivity(self):
        """Upper case, spaces, and hyphens should resolve as exact canonical matches."""
        res1 = canonicalize_term("VALPROIC ACID", "drug")
        assert res1["canonical"] == "valproic_acid"
        assert res1["match_type"] == "exact"
        assert res1["confidence"] == 1.0

        res2 = canonicalize_term("  acute kidney injury  ", "event")
        assert res2["canonical"] == "acute_kidney_injury"
        assert res2["match_type"] == "exact"
        assert res2["confidence"] == 1.0

        res3 = canonicalize_term("Gastrointestinal-Haemorrhage", "event")
        assert res3["canonical"] == "gastrointestinal_haemorrhage"
        assert res3["match_type"] == "exact"
        assert res3["confidence"] == 1.0


class TestAliasMatches:
    """Stage 1B: Curated alias resolution (brand names, clinical synonyms, UK/US spelling)."""

    @pytest.mark.parametrize("raw,expected_drug", [
        ("singulair", "montelukast"),
        ("lipitor", "atorvastatin"),
        ("glucophage", "metformin"),
        ("prozac", "fluoxetine"),
        ("zoloft", "sertraline"),
        ("celexa", "citalopram"),
        ("norvasc", "amlodipine"),
        ("salbutamol", "albuterol"),
        ("ventolin", "albuterol"),
        ("depakote", "valproic_acid"),
        ("hctz", "hydrochlorothiazide"),
        ("humira", "adalimumab"),
        ("keytruda", "pembrolizumab"),
        ("accutane", "isotretinoin"),
    ])
    def test_drug_aliases(self, raw, expected_drug):
        res = canonicalize_term(raw, "drug")
        assert res["canonical"] == expected_drug
        assert res["match_type"] == "alias"
        assert res["confidence"] == 0.98
        assert res["needs_human_review"] is False

    @pytest.mark.parametrize("raw,expected_event", [
        # Lay terms
        ("heart attack", "myocardial_infarction"),
        ("liver failure", "hepatotoxicity"),
        ("kidney failure", "acute_kidney_injury"),
        ("renal failure", "acute_kidney_injury"),
        ("gi bleed", "gastrointestinal_haemorrhage"),
        ("low blood sugar", "hypoglycaemia"),
        ("ruptured tendon", "tendon_rupture"),
        ("birth defects", "teratogenicity"),
        # US English spelling variations
        ("hypoglycemia", "hypoglycaemia"),
        ("gastrointestinal hemorrhage", "gastrointestinal_haemorrhage"),
        # Abbreviations
        ("mi", "myocardial_infarction"),
        ("aki", "acute_kidney_injury"),
        ("dili", "hepatotoxicity"),
    ])
    def test_event_aliases(self, raw, expected_event):
        res = canonicalize_term(raw, "event")
        assert res["canonical"] == expected_event
        assert res["match_type"] == "alias"
        assert res["confidence"] == 0.98
        assert res["needs_human_review"] is False


class TestFuzzyHighConfidence:
    """Stage 2: High-confidence fuzzy matches (>= 0.85) auto-resolved without review."""

    def test_event_typo_hepatoxicity(self):
        """Classic 1-char deletion 'hepatoxicity' -> 'hepatotoxicity' (ratio ~0.923)."""
        res = canonicalize_term("hepatoxicity", "event")
        assert res["canonical"] == "hepatotoxicity"
        assert res["match_type"] == "fuzzy"
        assert res["confidence"] >= 0.85
        assert res["needs_human_review"] is False

    def test_drug_typo_montelucast(self):
        """1-char phonetic substitution 'montelucast' -> 'montelukast' (ratio ~0.909)."""
        res = canonicalize_term("montelucast", "drug")
        assert res["canonical"] == "montelukast"
        assert res["match_type"] == "fuzzy"
        assert res["confidence"] >= 0.85
        assert res["needs_human_review"] is False

    def test_drug_typo_ciprofloxacine(self):
        """Trailing 'e' typo 'ciprofloxacine' -> 'ciprofloxacin' (ratio ~0.963)."""
        res = canonicalize_term("ciprofloxacine", "drug")
        assert res["canonical"] == "ciprofloxacin"
        assert res["match_type"] == "fuzzy"
        assert res["confidence"] >= 0.85
        assert res["needs_human_review"] is False

    def test_drug_typo_citalopramm(self):
        """Double letter typo 'citalopramm' -> 'citalopram' (ratio ~0.952)."""
        res = canonicalize_term("citalopramm", "drug")
        assert res["canonical"] == "citalopram"
        assert res["match_type"] == "fuzzy"
        assert res["confidence"] >= 0.85
        assert res["needs_human_review"] is False


class TestFuzzyMiddleBand:
    """Stage 2: Middle-band fuzzy matches (0.65 <= S < 0.85) flagged for human review."""

    def test_truncated_phrase_kidney_injury(self):
        """'kidney injury' vs 'acute_kidney_injury' has ratio ~0.8125 -> flagged."""
        res = canonicalize_term("kidney injury", "event")
        assert res["canonical"] == "acute_kidney_injury"
        assert res["match_type"] == "fuzzy"
        assert 0.65 <= res["confidence"] < 0.85
        assert res["needs_human_review"] is True


class TestUnmappedAndEdgeCases:
    """Stage 2: Below 0.65 similarity floor rejected as unmapped; invalid input checks."""

    def test_unrelated_drug_aspirin(self):
        """'aspirin' is not in PharmaGuard's 50-drug vocabulary -> unmapped."""
        res = canonicalize_term("aspirin", "drug")
        assert res["canonical"] is None
        assert res["match_type"] == "unmapped"
        assert res["confidence"] < 0.65
        assert res["needs_human_review"] is False

    def test_unrelated_event_headache(self):
        """'headache' is not in PharmaGuard's 15-event vocabulary -> unmapped."""
        res = canonicalize_term("headache", "event")
        assert res["canonical"] is None
        assert res["match_type"] == "unmapped"
        assert res["confidence"] < 0.65
        assert res["needs_human_review"] is False

    def test_empty_or_whitespace_input(self):
        res = canonicalize_term("   ", "drug")
        assert res["canonical"] is None
        assert res["match_type"] == "unmapped"
        assert res["confidence"] == 0.0
        assert res["needs_human_review"] is False

    def test_invalid_term_type(self):
        with pytest.raises(ValueError, match="Invalid term_type"):
            canonicalize_term("aspirin", "disease")  # type: ignore
