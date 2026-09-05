"""
Unit tests for DiseaseContextTool and WHO ATC therapeutic-context resolution.

Tests:
  - ATC Level 1 (A-V) and Level 2 ontology parsing
  - Valid and malformed ChEMBL API response handling (mocked)
  - Network failure resiliency (guaranteed non-throwing contract)
  - Known ChEMBL gap fallbacks (atorvastatin, simethicone)
  - Multi-ATC code preservation and representative selection
  - Deterministic utilization classification (CHRONIC, ACUTE, MIXED, UNKNOWN)
  - Cache hit and miss behavior
  - Determinism and idempotence

Owner: Krishna Sikheriya (IIT2023139)
"""

import json
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

from pharmaguard.tools.disease_context import (
    DiseaseContextTool,
    DiseaseContext,
    derive_utilization_class,
    ATC_LEVEL_1_MAP,
    ATC_LEVEL_2_MAP,
    ATC_FALLBACK_MAP,
    MULTI_ATC_SELECTION_POLICY,
)


class TestAtcOntologyParsing:
    """Verify deterministic ontology mapping for Level 1 and Level 2."""

    def test_all_level_1_anatomical_groups(self):
        """Ensure all 14 standard WHO ATC Level 1 groups are present and correctly mapped."""
        assert len(ATC_LEVEL_1_MAP) == 14
        expected = {
            "A": "Alimentary tract and metabolism",
            "B": "Blood and blood forming organs",
            "C": "Cardiovascular system",
            "D": "Dermatologicals",
            "G": "Genito-urinary system and sex hormones",
            "H": "Systemic hormonal preparations, excl. sex hormones and insulins",
            "J": "Antiinfectives for systemic use",
            "L": "Antineoplastic and immunomodulating agents",
            "M": "Musculo-skeletal system",
            "N": "Nervous system",
            "P": "Antiparasitic products, insecticides and repellents",
            "R": "Respiratory system",
            "S": "Sensory organs",
            "V": "Various",
        }
        assert ATC_LEVEL_1_MAP == expected

    @pytest.mark.parametrize("prefix,expected_name", [
        ("C08", "Calcium channel blockers"),
        ("C09", "Agents acting on the renin-angiotensin system"),
        ("C10", "Lipid modifying agents"),
        ("A10", "Drugs used in diabetes"),
        ("J01", "Antibacterials for systemic use"),
        ("N06", "Psychoanaleptics"),
        ("M01", "Anti-inflammatory and antirheumatic products"),
    ])
    def test_level_2_subgroups(self, prefix, expected_name):
        assert prefix in ATC_LEVEL_2_MAP
        assert ATC_LEVEL_2_MAP[prefix] == expected_name


class TestUtilizationClassification:
    """Verify deterministic clinical duration annotation."""

    @pytest.mark.parametrize("atc,expected_class", [
        ("C08CA01", "CHRONIC"),  # amlodipine
        ("C09AA01", "CHRONIC"),  # captopril
        ("C10AA05", "CHRONIC"),  # atorvastatin
        ("A10BA02", "CHRONIC"),  # metformin
        ("N06AB04", "CHRONIC"),  # citalopram
        ("R03DC03", "CHRONIC"),  # montelukast
        ("L01FF02", "CHRONIC"),  # pembrolizumab
        ("M04AA01", "CHRONIC"),  # allopurinol
        ("B01AC07", "CHRONIC"),  # dipyridamole
    ])
    def test_chronic_utilization(self, atc, expected_class):
        u_class, rationale = derive_utilization_class(atc)
        assert u_class == expected_class
        assert len(rationale) > 10

    @pytest.mark.parametrize("atc,expected_class", [
        ("J01MA02", "ACUTE"),    # ciprofloxacin
        ("J01CA04", "ACUTE"),    # amoxicillin
        ("J05AB01", "ACUTE"),    # acyclovir
        ("C01EB10", "ACUTE"),    # adenosine (IV bolus)
        ("D10BA01", "ACUTE"),    # oral isotretinoin (finite course)
    ])
    def test_acute_utilization(self, atc, expected_class):
        u_class, rationale = derive_utilization_class(atc)
        assert u_class == expected_class
        assert len(rationale) > 10

    @pytest.mark.parametrize("atc,expected_class", [
        ("M01AE02", "MIXED"),    # naproxen
        ("M01AB01", "MIXED"),    # indomethacin
        ("R03AC02", "MIXED"),    # albuterol
        ("J04AC01", "MIXED"),    # isoniazid
        ("A03AX13", "MIXED"),    # simethicone
        ("A06AD11", "MIXED"),    # lactulose
        ("N05CD07", "MIXED"),    # temazepam
    ])
    def test_mixed_utilization(self, atc, expected_class):
        u_class, rationale = derive_utilization_class(atc)
        assert u_class == expected_class
        assert len(rationale) > 10

    def test_unknown_or_short_atc(self):
        u1, r1 = derive_utilization_class(None)
        assert u1 == "UNKNOWN"
        u2, r2 = derive_utilization_class("XX")
        assert u2 == "UNKNOWN"
        u3, r3 = derive_utilization_class("Z99ZZ99")
        assert u3 == "UNKNOWN"


class TestFallbacksAndUnresolved:
    """Verify handling of known fallbacks and unresolved drugs."""


    def test_schema_conformance_section_2_1(self):
        """Verify DiseaseContext conforms to §34 Section 2.1 schema fields."""
        tool = DiseaseContextTool()
        ctx = tool.resolve("atorvastatin")
        # Direct §34 Section 2.1 fields
        assert hasattr(ctx, "atc_codes")
        assert hasattr(ctx, "primary_atc")
        assert hasattr(ctx, "therapeutic_area")
        assert hasattr(ctx, "pharmacological_subgroup")
        assert hasattr(ctx, "utilization_class")
        assert hasattr(ctx, "utilization_rationale")
        assert hasattr(ctx, "atc_source")

        assert ctx.primary_atc == "C10AA05"
        assert ctx.atc_codes == ["C10AA05"]
        assert ctx.therapeutic_area == "Cardiovascular system"
        assert ctx.utilization_class == "CHRONIC"
        assert ctx.atc_source == "hardcoded_fallback"

    def test_atorvastatin_fallback(self):
        tool = DiseaseContextTool()
        ctx = tool.resolve("atorvastatin")
        assert ctx.is_resolved is True
        assert ctx.atc_source == "hardcoded_fallback"
        assert ctx.selected_atc == "C10AA05"
        assert ctx.therapeutic_area_code == "C"
        assert ctx.therapeutic_area == "Cardiovascular system"
        assert ctx.pharmacological_subgroup_code == "C10"
        assert ctx.utilization_class == "CHRONIC"
        assert "ChEMBL v34" in ctx.selection_rationale

    def test_simethicone_fallback(self):
        tool = DiseaseContextTool()
        ctx = tool.resolve("simethicone")
        assert ctx.is_resolved is True
        assert ctx.atc_source == "hardcoded_fallback"
        assert ctx.selected_atc == "A03AX13"
        assert ctx.therapeutic_area_code == "A"
        assert ctx.therapeutic_area == "Alimentary tract and metabolism"
        assert ctx.utilization_class == "MIXED"

    def test_unknown_drug_returns_structured_unresolved(self):
        tool = DiseaseContextTool()
        ctx = tool.resolve("non_existent_fake_drug_xyz")
        assert ctx.is_resolved is False
        assert ctx.atc_source == "unresolved"
        assert ctx.selected_atc is None
        assert ctx.therapeutic_area_code is None
        assert ctx.therapeutic_area is None
        assert ctx.all_atc_codes == []
        assert ctx.drug_canonical == "non_existent_fake_drug_xyz"


class TestMultiAtcPreservationAndSelection:
    """Verify multi-ATC preservation, secondary codes, and representative selection."""

    def test_ciprofloxacin_systemic_priority(self):
        tool = DiseaseContextTool()
        # Mocking API response with all 4 ChEMBL ATC codes
        mock_response = json.dumps({
            "atc_classifications": ["J01MA02", "S03AA07", "S01AE03", "S02AA15"]
        }).encode("utf-8")

        with patch("urllib.request.urlopen") as mock_url:
            mock_url.return_value.__enter__.return_value.read.return_value = mock_response
            ctx = tool.resolve("ciprofloxacin")

        assert ctx.is_resolved is True
        assert ctx.selected_atc == "J01MA02"
        assert ctx.therapeutic_area_code == "J"
        assert len(ctx.all_atc_codes) == 4
        assert "S03AA07" in ctx.secondary_atc_codes
        assert "S01AE03" in ctx.secondary_atc_codes
        assert "S02AA15" in ctx.secondary_atc_codes
        assert "J01MA02" not in ctx.secondary_atc_codes
        assert ctx.selection_method == "systemic_route_priority"

    def test_allopurinol_monotherapy_priority(self):
        tool = DiseaseContextTool()
        mock_response = json.dumps({
            "atc_classifications": ["M04AA01", "M04AA51"]
        }).encode("utf-8")

        with patch("urllib.request.urlopen") as mock_url:
            mock_url.return_value.__enter__.return_value.read.return_value = mock_response
            ctx = tool.resolve("allopurinol")

        assert ctx.is_resolved is True
        assert ctx.selected_atc == "M04AA01"
        assert ctx.secondary_atc_codes == ["M04AA51"]
        assert ctx.selection_method == "monotherapy_priority"

    def test_unmapped_multi_atc_homogeneous_level1(self):
        """If an unmapped multi-ATC drug has all codes under same Level 1, select first and preserve."""
        tool = DiseaseContextTool()
        codes = ["C08CA01", "C08CA02"]
        ctx = tool._build_context("dummy_cardio", codes, atc_source="chembl_api")
        assert ctx.selected_atc == "C08CA01"
        assert ctx.secondary_atc_codes == ["C08CA02"]
        assert ctx.therapeutic_area_code == "C"
        assert ctx.selection_method == "homogeneous_level1_first"

    def test_unmapped_multi_atc_heterogeneous_level1(self):
        """If an unmapped multi-ATC drug spans multiple Level 1s, preserve all and flag deterministically."""
        tool = DiseaseContextTool()
        codes = ["J01CA04", "D06AA01"]
        ctx = tool._build_context("dummy_multi", codes, atc_source="chembl_api")
        # With deterministic sorting, D06AA01 sorts before J01CA04
        assert ctx.selected_atc == "D06AA01"
        assert ctx.secondary_atc_codes == ["J01CA04"]
        assert ctx.selection_method == "heterogeneous_multi_level1_first"
        assert "D, J" in ctx.selection_rationale

    def test_input_permutation_invariance(self):
        """Verify that list permutation of ATC codes produces identical results."""
        tool = DiseaseContextTool()
        # Unmapped drug permutation
        ctx_fwd = tool._build_context("unmapped_drug", ["J01CA04", "D06AA01"], atc_source="chembl_api")
        ctx_rev = tool._build_context("unmapped_drug", ["D06AA01", "J01CA04"], atc_source="chembl_api")
        assert ctx_fwd.selected_atc == ctx_rev.selected_atc
        assert ctx_fwd.secondary_atc_codes == ctx_rev.secondary_atc_codes

        # Mapped drug permutation of secondary codes
        ctx_m1 = tool._build_context("ciprofloxacin", ["J01MA02", "S01AE03", "S02AA15"], atc_source="chembl_api")
        ctx_m2 = tool._build_context("ciprofloxacin", ["S02AA15", "J01MA02", "S01AE03"], atc_source="chembl_api")
        assert ctx_m1.selected_atc == ctx_m2.selected_atc == "J01MA02"
        assert ctx_m1.secondary_atc_codes == ctx_m2.secondary_atc_codes

    def test_duplicate_atc_deduplication(self):
        """Ensure duplicate ATC codes in raw API response are cleanly deduplicated."""
        tool = DiseaseContextTool()
        codes = ["J01MA02", "J01MA02", "S01AE03", "S01AE03"]
        ctx = tool._build_context("ciprofloxacin", codes, atc_source="chembl_api")
        assert ctx.all_atc_codes == ["J01MA02", "S01AE03"]
        assert ctx.secondary_atc_codes == ["S01AE03"]


class TestApiErrorsAndResiliency:
    """Verify guaranteed non-throwing behavior under network or parsing errors."""

    def test_http_404_error_handled(self):
        tool = DiseaseContextTool()
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 404, "Not Found", None, None)):
            ctx = tool.resolve("metformin")
        assert ctx.is_resolved is False
        assert ctx.atc_source == "unresolved"
        assert "404" in ctx.selection_rationale

    def test_timeout_error_handled(self):
        tool = DiseaseContextTool()
        with patch("urllib.request.urlopen", side_effect=TimeoutError("Request timed out")):
            ctx = tool.resolve("metformin")
        assert ctx.is_resolved is False
        assert ctx.atc_source == "unresolved"
        assert "timed out" in ctx.selection_rationale.lower()

    def test_malformed_json_handled(self):
        tool = DiseaseContextTool()
        with patch("urllib.request.urlopen") as mock_url:
            mock_url.return_value.__enter__.return_value.read.return_value = b"{malformed json"
            ctx = tool.resolve("metformin")
        assert ctx.is_resolved is False
        assert ctx.atc_source == "unresolved"

    def test_empty_atc_list_handled(self):
        tool = DiseaseContextTool()
        with patch("urllib.request.urlopen") as mock_url:
            mock_url.return_value.__enter__.return_value.read.return_value = json.dumps({"atc_classifications": []}).encode("utf-8")
            ctx = tool.resolve("metformin")
        assert ctx.is_resolved is False
        assert ctx.atc_source == "unresolved"


class TestCacheIntegration:
    """Verify ToolCache interaction."""

    def test_cache_hit_bypasses_network(self):
        mock_cache = MagicMock()
        cached_dict = {
            "drug_canonical": "testdrug",
            "all_atc_codes": ["C08CA01"],
            "selected_atc": "C08CA01",
            "secondary_atc_codes": [],
            "therapeutic_area_code": "C",
            "therapeutic_area": "Cardiovascular system",
            "pharmacological_subgroup_code": "C08",
            "pharmacological_subgroup": "Calcium channel blockers",
            "utilization_class": "CHRONIC",
            "utilization_rationale": "Test rationale",
            "selection_method": "single_code",
            "selection_rationale": "Test",
            "atc_source": "chembl_api",
            "is_resolved": True,
        }
        mock_cache.atc_key.return_value = "atc::testdrug::v7"
        mock_cache.get.return_value = cached_dict

        tool = DiseaseContextTool(cache=mock_cache)
        with patch("urllib.request.urlopen") as mock_http:
            ctx = tool.resolve("testdrug")
            mock_http.assert_not_called()

        assert ctx.is_resolved is True
        assert ctx.selected_atc == "C08CA01"

    def test_cache_miss_writes_to_cache(self):
        mock_cache = MagicMock()
        mock_cache.atc_key.return_value = "atc::atorvastatin::v7"
        mock_cache.get.return_value = None  # Cache miss

        tool = DiseaseContextTool(cache=mock_cache)
        ctx = tool.resolve("atorvastatin")

        assert ctx.is_resolved is True
        mock_cache.set.assert_called_once()
        args, kwargs = mock_cache.set.call_args
        assert args[0] == "atc::atorvastatin::v7"
        assert args[1]["selected_atc"] == "C10AA05"
