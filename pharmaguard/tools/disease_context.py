"""
Disease Context Tool ΓÇö WHO ATC classification resolution and therapeutic-context annotation.

Provides:
  - Deterministic ATC classification lookup via ChEMBL API molecule endpoint
  - Documented fallback mappings for confirmed ChEMBL ATC gaps (atorvastatin, simethicone)
  - Explicit, auditable multi-ATC code preservation and representative selection
  - Deterministic ATC Level 1 (anatomical) and Level 2 (pharmacological) ontology mapping
  - Evaluation-only utilization classification (CHRONIC / ACUTE / MIXED / UNKNOWN) with clinical rationales

SCIENTIFIC BOUNDARY:
  ATC provides a standardized proxy for the drug's therapeutic and pharmacological class.
  It does NOT establish the individual patient's actual indication, why the patient received
  the drug, patient-level treatment duration, or patient-level confounding adjustment.
  This tool is strictly an evaluation-time annotation utility. It has zero effect on
  production scoring, confidence fusion weights, or escalation gating.

Owner: Krishna Sikheriya (IIT2023139)
"""

import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from pharmaguard.tools.cache import ToolCache

logger = logging.getLogger(__name__)

# --- Paths ---
_DATA_DIR = Path(__file__).resolve().parents[2] / "pharmaguard" / "data"
_DEFAULT_CHEMBL_LOOKUP = _DATA_DIR / "chembl_lookup.json"
_DEFAULT_ATC_LOOKUP = _DATA_DIR / "atc_lookup.json"

# --- WHO ATC Level 1: Anatomical Main Group (14 Standard Groups) ---
ATC_LEVEL_1_MAP: dict[str, str] = {
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

# --- WHO ATC Level 2: Therapeutic / Pharmacological Subgroups (Verified for Benchmark Corpus) ---
ATC_LEVEL_2_MAP: dict[str, str] = {
    "A01": "Stomatological preparations",
    "A02": "Drugs for acid related disorders",
    "A03": "Drugs for functional gastrointestinal disorders",
    "A06": "Drugs for constipation",
    "A07": "Antidiarrheals, intestinal anti-inflammatory/antiinfective agents",
    "A10": "Drugs used in diabetes",
    "B01": "Antithrombotic agents",
    "C01": "Cardiac therapy",
    "C03": "Diuretics",
    "C08": "Calcium channel blockers",
    "C09": "Agents acting on the renin-angiotensin system",
    "C10": "Lipid modifying agents",
    "D01": "Antifungals for dermatological use",
    "D06": "Antibiotics and chemotherapeutics for dermatological use",
    "D10": "Anti-acne preparations",
    "G01": "Gynecological antiinfectives and antiseptics",
    "G02": "Other gynecologicals",
    "J01": "Antibacterials for systemic use",
    "J02": "Antimycotics for systemic use",
    "J04": "Antimycobacterials",
    "J05": "Antivirals for systemic use",
    "L01": "Antineoplastic agents",
    "L04": "Immunosuppressants",
    "M01": "Anti-inflammatory and antirheumatic products",
    "M02": "Topical products for joint and muscular pain",
    "M04": "Antigout preparations",
    "N03": "Antiepileptics",
    "N05": "Psycholeptics",
    "N06": "Psychoanaleptics",
    "R03": "Drugs for obstructive airway diseases",
    "R06": "Antihistamines for systemic use",
    "S01": "Ophthalmologicals",
    "S02": "Otologicals",
    "S03": "Ophthalmological and otological preparations",
}

# --- Documented Fallback Mappings for Known ChEMBL API Data Gaps ---
# Provenance: WHO Collaborating Centre for Drug Statistics Methodology (WHOCC, Oslo) ATC Index.
# Verified against DECISIONS.md ┬º34.1.2.
ATC_FALLBACK_MAP: dict[str, dict[str, Any]] = {
    "atorvastatin": {
        "atc_codes": ["C10AA05"],
        "provenance": "WHO ATC Index 2026 (C10AA05: HMG CoA reductase inhibitors). Confirmed ChEMBL v34 data omission.",
    },
    "simethicone": {
        "atc_codes": ["A03AX13"],
        "provenance": "WHO ATC Index 2026 (A03AX13: Other drugs for functional bowel disorders). Confirmed ChEMBL v34 data omission.",
    },
}

# --- Curated Multi-ATC Representative Selection Policy ---
# For drugs with multiple WHO ATC codes, pharmacovigilance evaluation prioritizes:
# 1. Systemic exposure over topical/sensory/local routes (since target adverse events reflect systemic exposure).
# 2. Plain monotherapy formulations over combination codes (e.g. 50+ suffix).
# 3. Primary labeled indication over secondary indications.
MULTI_ATC_SELECTION_POLICY: dict[str, dict[str, str]] = {
    "acyclovir": {
        "selected_atc": "J05AB01",
        "method": "systemic_route_priority",
        "rationale": "Prioritized systemic antiviral (J05AB01) over ophthalmic (S01AD03) and topical dermatological (D06BB) formulations.",
    },
    "albuterol": {
        "selected_atc": "R03AC02",
        "method": "primary_formulation_priority",
        "rationale": "Prioritized inhaled beta-2 agonist (R03AC02, primary clinical delivery) over oral systemic form (R03CC02).",
    },
    "allopurinol": {
        "selected_atc": "M04AA01",
        "method": "monotherapy_priority",
        "rationale": "Prioritized plain allopurinol monotherapy (M04AA01) over fixed-dose combination code (M04AA51).",
    },
    "ciprofloxacin": {
        "selected_atc": "J01MA02",
        "method": "systemic_route_priority",
        "rationale": "Prioritized systemic fluoroquinolone antibacterial (J01MA02) over ophthalmic/otological drops (S01/S02/S03).",
    },
    "clindamycin": {
        "selected_atc": "J01FF01",
        "method": "systemic_route_priority",
        "rationale": "Prioritized systemic lincosamide antibacterial (J01FF01) over topical anti-acne (D10AF01) and vaginal (G01AA10).",
    },
    "griseofulvin": {
        "selected_atc": "D01BA01",
        "method": "systemic_route_priority",
        "rationale": "Prioritized systemic antifungal for dermatological infections (D01BA01) over topical antibiotics (D01AA08).",
    },
    "hydrochlorothiazide": {
        "selected_atc": "C03AA03",
        "method": "monotherapy_priority",
        "rationale": "Prioritized plain low-ceiling thiazide diuretic (C03AA03) over other diuretic code (C03AX01).",
    },
    "indomethacin": {
        "selected_atc": "M01AB01",
        "method": "systemic_indication_priority",
        "rationale": "Prioritized systemic anti-inflammatory NSAID (M01AB01) over topical (M02AA23), combination (M01AB51), ophthalmic (S01BC01), and ductus arteriosus (C01EB03).",
    },
    "isoniazid": {
        "selected_atc": "J04AC01",
        "method": "monotherapy_priority",
        "rationale": "Prioritized plain antimycobacterial monotherapy (J04AC01) over combination code (J04AC51).",
    },
    "isotretinoin": {
        "selected_atc": "D10BA01",
        "method": "systemic_route_priority",
        "rationale": "Prioritized oral systemic retinoid (D10BA01) over topical retinoid preparations (D10AD).",
    },
    "ketoprofen": {
        "selected_atc": "M01AE03",
        "method": "systemic_route_priority",
        "rationale": "Prioritized systemic oral NSAID (M01AE03) over topical gel (M02AA10) and combination code (M01AE53).",
    },
    "lactulose": {
        "selected_atc": "A06AD11",
        "method": "monotherapy_priority",
        "rationale": "Prioritized plain osmotic laxative (A06AD11) over combination code (A06AD61).",
    },
    "miconazole": {
        "selected_atc": "D01AC02",
        "method": "primary_indication_priority",
        "rationale": "Prioritized topical dermatological antifungal (D01AC02, primary WHO classification) over gynecological (G01AF04), stomatological (A01AB09), and systemic (J02AB01).",
    },
    "montelukast": {
        "selected_atc": "R03DC03",
        "method": "monotherapy_priority",
        "rationale": "Prioritized plain leukotriene receptor antagonist monotherapy (R03DC03) over combination code (R03DC53).",
    },
    "naproxen": {
        "selected_atc": "M01AE02",
        "method": "systemic_indication_priority",
        "rationale": "Prioritized systemic anti-inflammatory NSAID (M01AE02) over topical formulation (M02AA12) and vaginal preparation (G02CC02).",
    },
    "nifedipine": {
        "selected_atc": "C08CA05",
        "method": "monotherapy_priority",
        "rationale": "Prioritized plain dihydropyridine calcium channel blocker (C08CA05) over combination code (C08CA55).",
    },
    "nitrofurantoin": {
        "selected_atc": "J01XE01",
        "method": "monotherapy_priority",
        "rationale": "Prioritized plain nitrofuran antibacterial monotherapy (J01XE01) over combination code (J01XE51).",
    },
    "sulfisoxazole": {
        "selected_atc": "J01EB05",
        "method": "systemic_route_priority",
        "rationale": "Prioritized systemic short-acting sulfonamide (J01EB05) over ophthalmic drops (S01AB02).",
    },
}


# --- Pydantic Data Model ---

class DiseaseContext(BaseModel):
    """
    Structured therapeutic-context representation for an active drug substance.

    Provides WHO ATC classification, therapeutic area, and evaluation-only utilization class.
    Preserves all secondary ATC codes to prevent information loss for multi-indication drugs.
    """
    drug_canonical: str
    atc_codes: list[str] = Field(
        default_factory=list,
        description="All resolved WHO ATC codes associated with the drug entity."
    )
    all_atc_codes: list[str] = Field(
        default_factory=list,
        description="All resolved WHO ATC codes associated with the drug entity (alias)."
    )
    primary_atc: Optional[str] = Field(
        default=None,
        description="Primary representative ATC code used for primary stratification."
    )
    selected_atc: Optional[str] = Field(
        default=None,
        description="Selected representative ATC code used for primary stratification (alias)."
    )

    @model_validator(mode="before")
    @classmethod
    def sync_atc_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "atc_codes" in data and "all_atc_codes" not in data:
                data["all_atc_codes"] = data["atc_codes"]
            elif "all_atc_codes" in data and "atc_codes" not in data:
                data["atc_codes"] = data["all_atc_codes"]
            if "primary_atc" in data and "selected_atc" not in data:
                data["selected_atc"] = data["primary_atc"]
            elif "selected_atc" in data and "primary_atc" not in data:
                data["primary_atc"] = data["selected_atc"]
        return data
    secondary_atc_codes: list[str] = Field(
        default_factory=list,
        description="Secondary/alternative ATC codes, preserving alternate routes or indications."
    )
    therapeutic_area_code: Optional[str] = Field(
        default=None,
        description="ATC Level 1 single-letter code (e.g., 'C', 'J', 'N')."
    )
    therapeutic_area: Optional[str] = Field(
        default=None,
        description="ATC Level 1 anatomical/therapeutic area title (e.g., 'Cardiovascular system')."
    )
    pharmacological_subgroup_code: Optional[str] = Field(
        default=None,
        description="ATC Level 2 code (e.g., 'C08', 'J01', 'N06')."
    )
    pharmacological_subgroup: Optional[str] = Field(
        default=None,
        description="ATC Level 2 pharmacological/therapeutic subgroup title (e.g., 'Calcium channel blockers')."
    )
    utilization_class: Literal["CHRONIC", "ACUTE", "MIXED", "UNKNOWN"] = Field(
        default="UNKNOWN",
        description="Evaluation-only annotation representing typical drug utilization duration."
    )
    utilization_rationale: str = Field(
        default="",
        description="Pharmacological rationale justifying the utilization classification."
    )
    selection_method: str = Field(
        default="",
        description="Methodology by which the representative ATC code was selected."
    )
    selection_rationale: str = Field(
        default="",
        description="Clinical rationale for selecting the representative ATC code."
    )
    atc_source: Literal["chembl_api", "hardcoded_fallback", "unresolved"] = Field(
        default="unresolved",
        description="Data provenance for the ATC classification."
    )
    is_resolved: bool = Field(
        default=False,
        description="True if at least one ATC code was successfully resolved."
    )


# --- Utilization Classification Logic ---

def derive_utilization_class(
    selected_atc: Optional[str],
) -> tuple[Literal["CHRONIC", "ACUTE", "MIXED", "UNKNOWN"], str]:
    """
    Derive evaluation-only utilization class from the representative ATC code.

    Grounded strictly in clinical pharmacology guidelines.
    Returns: (utilization_class, utilization_rationale)
    """
    if not selected_atc or len(selected_atc) < 3:
        return "UNKNOWN", "Insufficient ATC structure to derive utilization classification."

    code = selected_atc.upper()
    prefix2 = code[:3]  # Level 2 (e.g. C08, J01)
    prefix3 = code[:4]  # Level 3 (e.g. C01E, R03A, R03D)
    prefix4 = code[:5]  # Level 4 (e.g. D10BA, R03AC, C01EB)

    # 1. Specific High-Granularity Overrides
    if code.startswith("C01EB10"):
        return "ACUTE", "Adenosine is administered as an acute, rapid IV bolus for paroxysmal supraventricular tachycardia conversion or diagnostic imaging."
    if code.startswith("D10BA"):
        return "ACUTE", "Oral isotretinoin is administered as a defined, finite course (typically 16-24 weeks) for severe acne."
    if code.startswith("R03DC"):
        return "CHRONIC", "Leukotriene receptor antagonists are prescribed as daily continuous controller therapy for chronic asthma."
    if code.startswith("R03AC"):
        return "MIXED", "Short-acting beta-2 agonists are used primarily as PRN acute rescue bronchodilators, but usage frequency varies with asthma control."

    # 2. Level 2 / Group Categorizations
    # Cardiovascular & Metabolic Maintenance (Chronic)
    if prefix2 in ("C08", "C09", "C10", "C03"):
        return "CHRONIC", "Prescribed as continuous, daily maintenance therapy for chronic cardiovascular conditions (hypertension, dyslipidemia, heart failure)."
    if prefix2 == "A10":
        return "CHRONIC", "Prescribed for long-term or lifelong glycemic management in diabetes mellitus."
    if prefix2 == "B01":
        return "CHRONIC", "Prescribed for long-term continuous antiplatelet or anticoagulant thromboprophylaxis."
    if prefix2 == "M04":
        return "CHRONIC", "Prescribed as daily long-term urate-lowering therapy for gout prevention."

    # Central Nervous System Maintenance (Chronic)
    if prefix2 in ("N03", "N05") and not prefix3.startswith("N05C"):
        return "CHRONIC", "Prescribed as long-term continuous maintenance therapy for epilepsy, schizophrenia, or bipolar disorder."
    if prefix3 == "N06A":
        return "CHRONIC", "Antidepressants are prescribed for continuous maintenance therapy (typically >=6-12 months) for depressive/anxiety disorders."

    # Oncology & Immunomodulation (Chronic)
    if prefix2 in ("L01", "L04"):
        return "CHRONIC", "Prescribed for ongoing cyclical or continuous maintenance immunotherapy, targeted oncology, or immunosuppression."

    # Acute Antiinfectives (Acute)
    if prefix2 in ("J01", "J05"):
        return "ACUTE", "Prescribed as finite therapeutic courses (typically 3-14 days) for acute bacterial or viral infections."
    if prefix2 == "J02":
        return "ACUTE", "Prescribed as finite therapeutic regimens (typically 2-12 weeks) for acute or subacute systemic fungal infections."

    # Mixed / Context-Dependent Durations
    if prefix2 == "M01":
        return "MIXED", "Bimodal utilization: short-term PRN use for acute pain/fever versus long-term daily use for inflammatory arthritis."
    if prefix2 == "J04":
        return "MIXED", "Intermediate subacute duration: 6-9 months regimen for tuberculosis prophylaxis or therapy."
    if prefix3 == "N05C":
        return "MIXED", "Guidelines recommend short-term acute use (<=2-4 weeks) for insomnia, though clinical practice frequently involves chronic extension."
    if prefix2 in ("A03", "A06", "A07"):
        return "MIXED", "Used both acutely for episodic gastrointestinal symptoms/constipation and chronically for motility or encephalopathy management."
    if prefix2 in ("D01", "D06"):
        return "MIXED", "Used for episodic or subacute courses (weeks to months) for localized fungal or dermatological infections."
    if prefix2 == "R06":
        return "MIXED", "Used both as-needed for acute allergic episodes and daily for seasonal/perennial allergic rhinitis."

    return "UNKNOWN", f"No standardized pharmacological utilization duration rule established for ATC prefix {prefix2}."


# --- Tool Implementation ---

class DiseaseContextTool:
    """
    Lightweight, read-only tool for resolving drug ATC therapeutic classification.

    Resolution Pipeline:
      1. Check disk cache (ToolCache.atc_key)
      2. Check curated fallback map for known ChEMBL data omissions (atorvastatin, simethicone)
      3. Query ChEMBL REST API molecule endpoint via chembl_lookup.json ID
      4. Deterministically select representative ATC code and preserve all secondary codes
      5. Map ATC Level 1 and Level 2 ontology categories
      6. Annotate evaluation-only utilization class (CHRONIC/ACUTE/MIXED/UNKNOWN)
      7. Cache and return DiseaseContext
    """

    def __init__(
        self,
        cache: Optional[ToolCache] = None,
        chembl_lookup_path: Optional[Path] = None,
        atc_lookup_path: Optional[Path] = _DEFAULT_ATC_LOOKUP,
        http_timeout: float = 10.0,
    ):
        self._cache = cache
        self._http_timeout = http_timeout
        self._chembl_lookup_path = chembl_lookup_path or _DEFAULT_CHEMBL_LOOKUP
        self._atc_lookup_path = atc_lookup_path
        self._chembl_lookup: dict[str, Any] = {}
        self._atc_lookup: dict[str, Any] = {}
        self._load_lookups()

    def _load_lookups(self) -> None:
        """Load static ChEMBL and ATC lookup tables."""
        if self._atc_lookup_path and self._atc_lookup_path.exists():
            try:
                with open(self._atc_lookup_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._atc_lookup = data.get("drugs", {})
            except Exception as e:
                logger.warning("Failed to load ATC lookup from %s: %s", self._atc_lookup_path, e)
        elif self._atc_lookup_path:
            logger.warning("ATC lookup path %s does not exist", self._atc_lookup_path)

        if self._chembl_lookup_path.exists():
            try:
                with open(self._chembl_lookup_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._chembl_lookup = data.get("drugs", {})
            except Exception as e:
                logger.warning("Failed to load ChEMBL lookup from %s: %s", self._chembl_lookup_path, e)
        else:
            logger.warning("ChEMBL lookup path %s does not exist", self._chembl_lookup_path)

    def resolve(self, drug_canonical: str) -> DiseaseContext:
        """
        Resolve DiseaseContext for a canonical drug name.

        Guaranteed non-throwing contract: always returns a structured DiseaseContext.
        On failure or missing data, returns DiseaseContext with is_resolved=False.
        """
        drug_norm = drug_canonical.lower().strip()

        # 1. Cache Check
        if self._cache:
            cache_key = self._cache.atc_key(drug_norm)
            cached_data = self._cache.get(cache_key)
            if cached_data and isinstance(cached_data, dict):
                try:
                    return DiseaseContext(**cached_data)
                except Exception as e:
                    logger.debug("Failed to deserialize cached DiseaseContext for %s: %s", drug_norm, e)

        # 2. Static ATC Lookup Check (Committed Cache for Offline Reproducibility)
        if drug_norm in self._atc_lookup:
            entry = self._atc_lookup[drug_norm]
            atc_codes = entry.get("atc_codes", [])
            atc_source = entry.get("atc_source", "chembl_api")
            if not atc_codes:
                return DiseaseContext(
                    drug_canonical=drug_canonical,
                    atc_source="unresolved",
                    is_resolved=False,
                    selection_rationale=entry.get("selection_rationale", "No ATC codes found in static lookup."),
                )
            ctx = self._build_context(
                drug_canonical=drug_canonical,
                atc_codes=atc_codes,
                atc_source=atc_source,
                selection_method=entry.get("selection_method"),
                selection_rationale=entry.get("selection_rationale"),
            )
            self._write_cache(drug_norm, ctx)
            return ctx

        # 3. Check Documented Fallback
        if drug_norm in ATC_FALLBACK_MAP:
            fb = ATC_FALLBACK_MAP[drug_norm]
            ctx = self._build_context(
                drug_canonical=drug_canonical,
                atc_codes=fb["atc_codes"],
                atc_source="hardcoded_fallback",
                selection_method="fallback_mapping",
                selection_rationale=fb.get("provenance", "Documented ChEMBL API omission fallback."),
            )
            self._write_cache(drug_norm, ctx)
            return ctx

        # 4. Resolve via ChEMBL API
        drug_entry = self._chembl_lookup.get(drug_norm)
        chembl_id = drug_entry.get("chembl_id") if isinstance(drug_entry, dict) else None

        if not chembl_id:
            logger.info("Drug '%s' has no ChEMBL ID in lookup — cannot query ChEMBL ATC.", drug_canonical)
            return DiseaseContext(
                drug_canonical=drug_canonical,
                atc_source="unresolved",
                is_resolved=False,
                selection_rationale="No ChEMBL ID found in local reference lookup.",
            )

        try:
            url = f"https://www.ebi.ac.uk/chembl/api/data/molecule/{chembl_id}.json"
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": "PharmaGuard-Research/1.0"}
            )
            with urllib.request.urlopen(req, timeout=self._http_timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            atc_codes = data.get("atc_classifications", [])
            if not atc_codes:
                logger.info("ChEMBL returned empty ATC classifications for %s (%s)", drug_canonical, chembl_id)
                return DiseaseContext(
                    drug_canonical=drug_canonical,
                    atc_source="unresolved",
                    is_resolved=False,
                    selection_rationale=f"ChEMBL molecule {chembl_id} contains no atc_classifications.",
                )

            ctx = self._build_context(
                drug_canonical=drug_canonical,
                atc_codes=atc_codes,
                atc_source="chembl_api",
            )
            self._write_cache(drug_norm, ctx)
            return ctx

        except Exception as e:
            logger.warning("ChEMBL API query failed for %s (%s): %s", drug_canonical, chembl_id, e)
            return DiseaseContext(
                drug_canonical=drug_canonical,
                atc_source="unresolved",
                is_resolved=False,
                selection_rationale=f"ChEMBL API retrieval error: {e}",
            )

    def _build_context(
        self,
        drug_canonical: str,
        atc_codes: list[str],
        atc_source: Literal["chembl_api", "hardcoded_fallback", "unresolved"],
        selection_method: Optional[str] = None,
        selection_rationale: Optional[str] = None,
    ) -> DiseaseContext:
        """Construct structured DiseaseContext from raw ATC code list."""
        # Deduplicate while enforcing deterministic sorted ordering to prevent
        # API return-order fluctuations from introducing nondeterminism in selection or secondary codes.
        cleaned_codes = sorted(list(dict.fromkeys(c.strip().upper() for c in atc_codes if c and c.strip())))
        if not cleaned_codes:
            return DiseaseContext(
                drug_canonical=drug_canonical,
                atc_source=atc_source,
                is_resolved=False,
                selection_rationale="No valid ATC codes extracted.",
            )

        drug_norm = drug_canonical.lower().strip()

        # Selection logic
        if len(cleaned_codes) == 1:
            selected_atc = cleaned_codes[0]
            secondary_codes: list[str] = []
            method = selection_method or "single_code"
            rationale = selection_rationale or "Single unambiguous ATC classification returned by source."
        elif drug_norm in MULTI_ATC_SELECTION_POLICY:
            policy = MULTI_ATC_SELECTION_POLICY[drug_norm]
            target_code = policy["selected_atc"]
            if target_code in cleaned_codes:
                selected_atc = target_code
                secondary_codes = [c for c in cleaned_codes if c != selected_atc]
            else:
                # If target code not found in returned list, select first available
                selected_atc = cleaned_codes[0]
                secondary_codes = cleaned_codes[1:]
            method = policy.get("method", "curated_policy")
            rationale = policy.get("rationale", "Selected via curated multi-ATC policy.")
        else:
            # Fallback for unmapped multi-ATC: check if all share same Level 1
            l1_set = set(c[0] for c in cleaned_codes)
            if len(l1_set) == 1:
                selected_atc = cleaned_codes[0]
                secondary_codes = cleaned_codes[1:]
                method = "homogeneous_level1_first"
                rationale = f"All {len(cleaned_codes)} codes belong to same therapeutic area ({selected_atc[0]}); primary code selected."
            else:
                # Disagreement across Level 1
                selected_atc = cleaned_codes[0]
                secondary_codes = cleaned_codes[1:]
                method = "heterogeneous_multi_level1_first"
                rationale = f"Codes span multiple Level 1 areas ({', '.join(sorted(l1_set))}); primary code selected, secondary codes preserved."

        # Ontology mapping
        l1_code = selected_atc[0] if len(selected_atc) >= 1 else None
        l1_name = ATC_LEVEL_1_MAP.get(l1_code, f"Unresolved Area ({l1_code})") if l1_code else None

        l2_code = selected_atc[:3] if len(selected_atc) >= 3 else None
        l2_name = ATC_LEVEL_2_MAP.get(l2_code, f"Unresolved Subgroup ({l2_code})") if l2_code else None

        # Utilization class derivation
        u_class, u_rationale = derive_utilization_class(selected_atc)

        return DiseaseContext(
            drug_canonical=drug_canonical,
            atc_codes=cleaned_codes,
            all_atc_codes=cleaned_codes,
            primary_atc=selected_atc,
            selected_atc=selected_atc,
            secondary_atc_codes=secondary_codes,
            therapeutic_area_code=l1_code,
            therapeutic_area=l1_name,
            pharmacological_subgroup_code=l2_code,
            pharmacological_subgroup=l2_name,
            utilization_class=u_class,
            utilization_rationale=u_rationale,
            selection_method=method,
            selection_rationale=rationale,
            atc_source=atc_source,
            is_resolved=True,
        )

    def _write_cache(self, drug_norm: str, ctx: DiseaseContext) -> None:
        """Write resolved DiseaseContext to cache if cache is available."""
        if self._cache and ctx.is_resolved:
            try:
                cache_key = self._cache.atc_key(drug_norm)
                self._cache.set(cache_key, ctx.model_dump())
            except Exception as e:
                logger.debug("Failed to write DiseaseContext to cache for %s: %s", drug_norm, e)
