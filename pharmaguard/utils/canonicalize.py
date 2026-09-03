"""
Two-Stage Term Canonicalization Layer.

Maps raw clinical, colloquial, or typographical drug and adverse event strings
into PharmaGuard's controlled canonical vocabulary.

Architecture (DECISIONS.md / CANONICALIZATION.md):
  Step 0: Input Pre-processing (lowercase, whitespace collapse, punctuation removal)
  Stage 1: Deterministic Matcher (Exact canonical match + Curated alias table)
  Stage 2: Bounded Fuzzy Fallback (difflib.SequenceMatcher across canonical vocabulary)

Licensing Disclosure:
  This module does NOT query, embed, or claim compliance with the proprietary
  MedDRA (MSSO) dictionary. It operates on an internal controlled vocabulary of
  MedDRA Preferred Terms (PTs) curated from public regulatory communications
  and published reference sets (Ryan et al. 2013).

Owner: Krishna Sikheriya (IIT2023139)
"""

import difflib
import re
from typing import Any, Literal


# =====================================================================
# Controlled Canonical Vocabularies
# =====================================================================

CANONICAL_EVENTS: list[str] = [
    "acute_kidney_injury",
    "agranulocytosis",
    "common_cold",
    "dementia",
    "frostbite",
    "gastrointestinal_haemorrhage",
    "hepatotoxicity",
    "hypoglycaemia",
    "myocardial_infarction",
    "pancreatic_cancer",
    "pneumonitis",
    "suicidal_ideation",
    "tendon_rupture",
    "teratogenicity",
    "tooth_eruption",
]

CANONICAL_DRUGS: list[str] = [
    "acarbose",
    "acyclovir",
    "adalimumab",
    "adenosine",
    "albuterol",
    "allopurinol",
    "amlodipine",
    "amoxicillin",
    "atorvastatin",
    "captopril",
    "carbamazepine",
    "ciprofloxacin",
    "citalopram",
    "clindamycin",
    "clozapine",
    "dicyclomine",
    "dipyridamole",
    "fluoxetine",
    "griseofulvin",
    "hydrochlorothiazide",
    "imatinib",
    "indomethacin",
    "isoniazid",
    "isotretinoin",
    "itraconazole",
    "ketoprofen",
    "lactulose",
    "liraglutide",
    "lisinopril",
    "loratadine",
    "metformin",
    "methenamine",
    "miconazole",
    "montelukast",
    "naproxen",
    "nifedipine",
    "nitrofurantoin",
    "pembrolizumab",
    "pioglitazone",
    "rosiglitazone",
    "semaglutide",
    "sertraline",
    "simethicone",
    "sucralfate",
    "sulfisoxazole",
    "tamsulosin",
    "temazepam",
    "terbinafine",
    "topiramate",
    "valproic_acid",
]


# =====================================================================
# Curated Alias Tables (Clinical Synonyms, Lay Terms, Brand Names, INN)
# =====================================================================

EVENT_ALIASES: dict[str, str] = {
    # acute_kidney_injury
    "kidney failure": "acute_kidney_injury",
    "renal failure": "acute_kidney_injury",
    "acute renal failure": "acute_kidney_injury",
    "renal injury": "acute_kidney_injury",
    "acute kidney failure": "acute_kidney_injury",
    "aki": "acute_kidney_injury",
    "acute renal impairment": "acute_kidney_injury",
    # agranulocytosis
    "neutropenia": "agranulocytosis",
    "severe neutropenia": "agranulocytosis",
    "low white blood cells": "agranulocytosis",
    "granulocytopenia": "agranulocytosis",
    # common_cold
    "cold": "common_cold",
    "nasopharyngitis": "common_cold",
    "rhinovirus": "common_cold",
    "upper respiratory infection": "common_cold",
    "acute nasopharyngitis": "common_cold",
    # dementia
    "cognitive decline": "dementia",
    "memory loss": "dementia",
    "alzheimers": "dementia",
    "alzheimer's": "dementia",
    "dementia alzheimer's type": "dementia",
    # frostbite
    "frost bite": "frostbite",
    "cold induced necrosis": "frostbite",
    # gastrointestinal_haemorrhage (including US English spelling)
    "gi bleed": "gastrointestinal_haemorrhage",
    "gi bleeding": "gastrointestinal_haemorrhage",
    "gastrointestinal hemorrhage": "gastrointestinal_haemorrhage",
    "gi hemorrhage": "gastrointestinal_haemorrhage",
    "stomach bleed": "gastrointestinal_haemorrhage",
    "intestinal bleeding": "gastrointestinal_haemorrhage",
    "upper gi bleed": "gastrointestinal_haemorrhage",
    "rectal bleeding": "gastrointestinal_haemorrhage",
    "melena": "gastrointestinal_haemorrhage",
    # hepatotoxicity
    "liver failure": "hepatotoxicity",
    "liver damage": "hepatotoxicity",
    "liver injury": "hepatotoxicity",
    "acute liver injury": "hepatotoxicity",
    "hepatic injury": "hepatotoxicity",
    "drug induced liver injury": "hepatotoxicity",
    "dili": "hepatotoxicity",
    "hepatic failure": "hepatotoxicity",
    "toxic hepatitis": "hepatotoxicity",
    # hypoglycaemia (including US English spelling)
    "hypoglycemia": "hypoglycaemia",
    "low blood sugar": "hypoglycaemia",
    "low blood glucose": "hypoglycaemia",
    "insulin shock": "hypoglycaemia",
    # myocardial_infarction
    "heart attack": "myocardial_infarction",
    "mi": "myocardial_infarction",
    "acute myocardial infarction": "myocardial_infarction",
    "cardiac infarction": "myocardial_infarction",
    # pancreatic_cancer
    "pancreatic carcinoma": "pancreatic_cancer",
    "pancreatic neoplasm": "pancreatic_cancer",
    "cancer of pancreas": "pancreatic_cancer",
    "pancreatic tumor": "pancreatic_cancer",
    "malignant neoplasm of pancreas": "pancreatic_cancer",
    # pneumonitis
    "lung inflammation": "pneumonitis",
    "interstitial pneumonitis": "pneumonitis",
    "drug induced pneumonitis": "pneumonitis",
    # suicidal_ideation
    "suicidal thoughts": "suicidal_ideation",
    "suicidality": "suicidal_ideation",
    "suicide attempt": "suicidal_ideation",
    "suicidal behavior": "suicidal_ideation",
    "suicidal ideations": "suicidal_ideation",
    # tendon_rupture
    "ruptured tendon": "tendon_rupture",
    "achilles tendon rupture": "tendon_rupture",
    "achilles tear": "tendon_rupture",
    "tendon tear": "tendon_rupture",
    "tendon injury": "tendon_rupture",
    # teratogenicity
    "birth defects": "teratogenicity",
    "congenital malformation": "teratogenicity",
    "congenital anomalies": "teratogenicity",
    "fetal toxicity": "teratogenicity",
    "embryotoxicity": "teratogenicity",
    # tooth_eruption
    "teeth eruption": "tooth_eruption",
    "delayed tooth eruption": "tooth_eruption",
    "eruption of tooth": "tooth_eruption",
}

DRUG_ALIASES: dict[str, str] = {
    # Brand names, INN variants, and abbreviations
    "albuterol": "albuterol",
    "salbutamol": "albuterol",
    "ventolin": "albuterol",
    "proair": "albuterol",
    "valproate": "valproic_acid",
    "sodium valproate": "valproic_acid",
    "depakote": "valproic_acid",
    "depakene": "valproic_acid",
    "hctz": "hydrochlorothiazide",
    "microzide": "hydrochlorothiazide",
    "prozac": "fluoxetine",
    "zoloft": "sertraline",
    "celexa": "citalopram",
    "norvasc": "amlodipine",
    "procardia": "nifedipine",
    "adalat": "nifedipine",
    "capoten": "captopril",
    "zestril": "lisinopril",
    "prinivil": "lisinopril",
    "lipitor": "atorvastatin",
    "singulair": "montelukast",
    "cipro": "ciprofloxacin",
    "glucophage": "metformin",
    "avandia": "rosiglitazone",
    "actos": "pioglitazone",
    "clozaril": "clozapine",
    "tegretol": "carbamazepine",
    "inh": "isoniazid",
    "accutane": "isotretinoin",
    "roaccutane": "isotretinoin",
    "keytruda": "pembrolizumab",
    "humira": "adalimumab",
    "gleevec": "imatinib",
    "ozempic": "semaglutide",
    "wegovy": "semaglutide",
    "victoza": "liraglutide",
    "saxenda": "liraglutide",
}


# =====================================================================
# Internal Preprocessing & Matching Logic
# =====================================================================

def _preprocess_input(text: str) -> str:
    """Normalize whitespace, lowercases, and converts delimiters to spaces."""
    if not text:
        return ""
    cleaned = text.strip().lower()
    # Replace hyphens, underscores, slashes, and periods with space
    cleaned = re.sub(r"[-_/.]", " ", cleaned)
    # Collapse multiple whitespace characters
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def canonicalize_term(
    raw_input: str,
    term_type: Literal["drug", "event"],
) -> dict[str, Any]:
    """
    Canonicalize a raw drug or adverse event string into PharmaGuard's controlled vocabulary.

    Parameters:
        raw_input: Raw colloquial, brand name, or clinical text string.
        term_type: Domain selector ("drug" or "event").

    Returns:
        Dictionary adhering to:
        {
            "canonical": str | None,          # Normalized canonical string or None if unmapped
            "confidence": float,              # Similarity / match score (0.0 to 1.0)
            "match_type": str,                # "exact" | "alias" | "fuzzy" | "unmapped"
            "needs_human_review": bool,       # True if match is in the 0.65-0.84 uncertainty band
            "original_input": str             # Preserved raw input for auditability
        }
    """
    if not isinstance(raw_input, str) or not raw_input.strip():
        return {
            "canonical": None,
            "confidence": 0.0,
            "match_type": "unmapped",
            "needs_human_review": False,
            "original_input": raw_input,
        }

    norm_input = _preprocess_input(raw_input)
    if not norm_input:
        return {
            "canonical": None,
            "confidence": 0.0,
            "match_type": "unmapped",
            "needs_human_review": False,
            "original_input": raw_input,
        }

    if term_type == "event":
        canonical_vocab = CANONICAL_EVENTS
        alias_map = EVENT_ALIASES
    elif term_type == "drug":
        canonical_vocab = CANONICAL_DRUGS
        alias_map = DRUG_ALIASES
    else:
        raise ValueError(f"Invalid term_type: {term_type}. Expected 'drug' or 'event'.")

    # -----------------------------------------------------------------
    # Stage 1A: Exact Canonical Match
    # -----------------------------------------------------------------
    for candidate in canonical_vocab:
        candidate_norm = _preprocess_input(candidate)
        if norm_input == candidate_norm or norm_input == candidate:
            return {
                "canonical": candidate,
                "confidence": 1.0,
                "match_type": "exact",
                "needs_human_review": False,
                "original_input": raw_input,
            }

    # -----------------------------------------------------------------
    # Stage 1B: Curated Alias Table Lookup
    # -----------------------------------------------------------------
    # Check normalized input against aliases
    if norm_input in alias_map:
        return {
            "canonical": alias_map[norm_input],
            "confidence": 0.98,
            "match_type": "alias",
            "needs_human_review": False,
            "original_input": raw_input,
        }

    # Also check with apostrophes or punctuation stripped
    no_punct = re.sub(r"[^\w\s]", "", norm_input)
    if no_punct in alias_map:
        return {
            "canonical": alias_map[no_punct],
            "confidence": 0.98,
            "match_type": "alias",
            "needs_human_review": False,
            "original_input": raw_input,
        }

    # -----------------------------------------------------------------
    # Stage 2: Bounded Fuzzy Fallback (difflib.SequenceMatcher)
    # -----------------------------------------------------------------
    best_candidate: str | None = None
    best_ratio: float = 0.0

    for candidate in canonical_vocab:
        candidate_norm = _preprocess_input(candidate)
        # Compare against both space-separated and underscore-separated versions
        r1 = difflib.SequenceMatcher(None, norm_input, candidate_norm).ratio()
        r2 = difflib.SequenceMatcher(None, norm_input, candidate).ratio()
        ratio = max(r1, r2)
        if ratio > best_ratio:
            best_ratio = ratio
            best_candidate = candidate

    rounded_score = round(best_ratio, 4)

    # Tri-band threshold decision
    if best_ratio >= 0.85:
        # High-confidence: minor typo, auto-resolved without review
        return {
            "canonical": best_candidate,
            "confidence": rounded_score,
            "match_type": "fuzzy",
            "needs_human_review": False,
            "original_input": raw_input,
        }
    elif best_ratio >= 0.65:
        # Middle band: substantial distance, flagged for human review
        return {
            "canonical": best_candidate,
            "confidence": rounded_score,
            "match_type": "fuzzy",
            "needs_human_review": True,
            "original_input": raw_input,
        }
    else:
        # Low confidence: below rejection floor
        return {
            "canonical": None,
            "confidence": rounded_score,
            "match_type": "unmapped",
            "needs_human_review": False,
            "original_input": raw_input,
        }
