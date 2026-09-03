# Term Canonicalization Layer — Design & Specification

**Document Version:** 1.0  
**Status:** Approved for Implementation (Phase 1 Complete)  
**Author:** PharmaGuard Research Team  
**Module Target:** `pharmaguard/utils/canonicalize.py`  
**Test Suite Target:** `tests/test_canonicalize.py`  

---

## 1. Regulatory & Terminology Licensing Disclosure

> ### ⚠️ Critical Licensing & Terminology Boundary Notice
> 
> **Actual MedDRA (Medical Dictionary for Regulatory Activities) is a proprietary, subscription-licensed medical terminology maintained by the Maintenance and Support Services Organization (MSSO).**
> Due to strict commercial copyright and distribution licensing, MedDRA is excluded from the public United States National Library of Medicine (NLM) Unified Medical Language System (UMLS) distribution and requires an active institutional or enterprise MSSO subscription.
>
> **Project Compliance Audit:**
> A comprehensive repository and environment audit confirms that the PharmaGuard project does **NOT** possess an active MedDRA MSSO license, subscription credentials, or proprietary MedDRA data distributions. 
>
> **Design Boundary:**
> Under no circumstances does this module claim or imply compliance with the official proprietary MedDRA dictionary. This utility is strictly an **internal controlled-vocabulary normalizer** designed to map colloquial clinical synonyms, UK/US spelling variants, and typographical errors into the specific string representations established within PharmaGuard's curated ground-truth datasets (`ground_truth.json` and `ground_truth_omop_pilot.json`). While these internal string targets are inspired by public MedDRA Preferred Term (PT) naming conventions as cited in open-access literature, this module functions entirely through transparent, open-source heuristics without utilizing proprietary MSSO files.

---

## 2. Background & Motivation

In spontaneous reporting surveillance (e.g., openFDA FAERS), slight orthographic and semantic variations can silently disrupt automated signal detection:
1. **Punctuation & Delimiter Inconsistencies:** Clinical data often mixes snake_case (`myocardial_infarction`), natural spacing (`myocardial infarction`), or hyphens (`drug-induced liver injury`). `pharmaguard/utils/text.py`'s `normalize_term()` only performs basic underscore-to-space replacement.
2. **Spelling Conventions:** FAERS indexes adverse reactions under British English MedDRA PTs (e.g., `hypoglycaemia`, `gastrointestinal_haemorrhage`), whereas US clinical records routinely submit American spellings (`hypoglycemia`, `gastrointestinal_hemorrhage`). As documented in `DECISIONS.md §21`, querying FAERS with `hypoglycemia` returned 0 reports, whereas `hypoglycaemia` returned 9,344 reports.
3. **Colloquial & Lay Synonyms:** Frontline reporters and EHR notes routinely use lay terms ("heart attack", "liver failure", "kidney damage", "GI bleed") that fail exact string matching against surveillance targets.
4. **Typographical & OCR Errors:** Common misspellings (e.g., "hepatoxicity", "ciprofloxacine", "montelucast") should be safely resolved or flagged for human review rather than silently dropping out of triage.

Following proven biomedical NLP intake patterns (such as PVLens and CTG-DB), PharmaGuard implements a **two-stage hybrid normalizer** combining deterministic exact/alias matching with bounded fuzzy sequence similarity.

---

## 3. Controlled Canonical Vocabularies

The canonical target vocabularies are derived from PharmaGuard's verified ground truth datasets and ChEMBL lookup tables:

### 3.1 Canonical Event Vocabulary ($N = 15$ MedDRA PT Targets)
Extracted directly from the union of `pharmaguard/data/ground_truth.json` (13 events) and `pharmaguard/data/ground_truth_omop_pilot.json` (4 events):
1. `acute_kidney_injury`
2. `agranulocytosis`
3. `common_cold`
4. `dementia`
5. `frostbite`
6. `gastrointestinal_haemorrhage`
7. `hepatotoxicity`
8. `hypoglycaemia`
9. `myocardial_infarction`
10. `pancreatic_cancer`
11. `pneumonitis`
12. `suicidal_ideation`
13. `tendon_rupture`
14. `teratogenicity`
15. `tooth_eruption`

### 3.2 Canonical Drug Vocabulary ($N = 50$ Target Active Ingredients)
Extracted from `pharmaguard/data/ground_truth.json` (14 drugs), `ground_truth_omop_pilot.json` (32 drugs), and the 4 probe drugs in `pharmaguard/data/chembl_lookup.json`:
* `acarbose`, `acyclovir`, `adalimumab`, `adenosine`, `albuterol`, `allopurinol`, `amlodipine`, `amoxicillin`, `atorvastatin`, `captopril`, `carbamazepine`, `ciprofloxacin`, `citalopram`, `clindamycin`, `clozapine`, `dicyclomine`, `dipyridamole`, `fluoxetine`, `griseofulvin`, `hydrochlorothiazide`, `imatinib`, `indomethacin`, `isoniazid`, `isotretinoin`, `itraconazole`, `ketoprofen`, `lactulose`, `liraglutide`, `lisinopril`, `loratadine`, `metformin`, `methenamine`, `miconazole`, `montelukast`, `naproxen`, `nifedipine`, `nitrofurantoin`, `pembrolizumab`, `pioglitazone`, `rosiglitazone`, `semaglutide`, `sertraline`, `simethicone`, `sucralfate`, `sulfisoxazole`, `tamsulosin`, `temazepam`, `terbinafine`, `topiramate`, `valproic_acid`.

---

## 4. Two-Stage Matching Architecture

```
                       [ Raw Input String + Term Type ]
                                       │
                                       ▼
                       [ Step 0: Input Pre-processing ]
                       - Strip whitespace, lowercase
                       - Replace hyphens/underscores with spaces
                       - Remove extraneous punctuation
                                       │
                                       ▼
                     [ Stage 1: Deterministic Exact / Alias ]
                                       │
                ┌──────────────────────┴──────────────────────┐
                │ Match Found?                                │
               YES                                            NO
                │                                             │
                ▼                                             ▼
       [ Confidence: 1.00 ]                      [ Stage 2: Fuzzy Fallback ]
       [ Match Type: exact/alias ]               (difflib.SequenceMatcher against
       [ Review: False ]                          canonical vocabulary)
                                                              │
                                                              ▼
                                                   [ Best Match Score: S ]
                                                              │
                    ┌─────────────────────────┬───────────────┴───────────────┐
                    │ S >= 0.85               │ 0.65 <= S < 0.85              │ S < 0.65
                    ▼                         ▼                               ▼
           [ High Confidence ]       [ Middle Band Flag ]            [ Low Confidence ]
           - Canonical Match         - Candidate Match               - Unmapped (None)
           - Confidence: S           - Confidence: S                 - Confidence: S
           - Match Type: fuzzy       - Match Type: fuzzy             - Match Type: unmapped
           - Review: False           - Review: TRUE (Flagged)        - Review: False
```

### Step 0: Input Normalization
Before evaluating any dictionary or sequence comparison, the raw string undergoes deterministic sanitization:
* Trim leading and trailing whitespace.
* Convert all characters to lowercase.
* Replace hyphens, underscores, slashes, and periods with single spaces.
* Collapse multiple consecutive whitespace characters into a single space.

### Stage 1: Deterministic Matcher (Exact & Curated Aliases)
1. **Exact Canonical Match:** Check if the normalized string exactly matches any canonical term (evaluated with both spaces and underscores). If matched:
   $$\text{canonical} = \text{target}, \quad \text{confidence} = 1.00, \quad \text{match\_type} = \text{"exact"}, \quad \text{needs\_human\_review} = \text{False}$$
2. **Curated Alias Table Lookup:** If not an exact match, check against a dedicated dictionary of high-confidence clinical synonyms, international non-proprietary names (INN), brand names, and UK/US orthographic variants:
   $$\text{canonical} = \text{alias\_map}[\text{input}], \quad \text{confidence} = 0.98, \quad \text{match\_type} = \text{"alias"}, \quad \text{needs\_human\_review} = \text{False}$$

#### Curated Event Alias Table:
* **`acute_kidney_injury`:** `"kidney failure"`, `"renal failure"`, `"acute renal failure"`, `"renal injury"`, `"acute kidney failure"`, `"aki"`, `"acute renal impairment"`
* **`agranulocytosis`:** `"neutropenia"`, `"severe neutropenia"`, `"low white blood cells"`, `"granulocytopenia"`
* **`common_cold`:** `"cold"`, `"nasopharyngitis"`, `"rhinovirus"`, `"upper respiratory infection"`, `"acute nasopharyngitis"`
* **`dementia`:** `"cognitive decline"`, `"memory loss"`, `"alzheimers"`, `"alzheimer's"`, `"dementia alzheimer's type"`
* **`frostbite`:** `"frost bite"`, `"cold-induced necrosis"`
* **`gastrointestinal_haemorrhage`:** `"gi bleed"`, `"gi bleeding"`, `"gastrointestinal hemorrhage"`, `"gi hemorrhage"`, `"stomach bleed"`, `"intestinal bleeding"`, `"upper gi bleed"`, `"rectal bleeding"`, `"melena"`
* **`hepatotoxicity`:** `"liver failure"`, `"liver damage"`, `"liver injury"`, `"acute liver injury"`, `"hepatic injury"`, `"drug induced liver injury"`, `"dili"`, `"hepatic failure"`, `"toxic hepatitis"`
* **`hypoglycaemia`:** `"hypoglycemia"`, `"low blood sugar"`, `"low blood glucose"`, `"insulin shock"`
* **`myocardial_infarction`:** `"heart attack"`, `"mi"`, `"acute myocardial infarction"`, `"cardiac infarction"`
* **`pancreatic_cancer`:** `"pancreatic carcinoma"`, `"pancreatic neoplasm"`, `"cancer of pancreas"`, `"pancreatic tumor"`, `"malignant neoplasm of pancreas"`
* **`pneumonitis`:** `"lung inflammation"`, `"interstitial pneumonitis"`, `"drug induced pneumonitis"`
* **`suicidal_ideation`:** `"suicidal thoughts"`, `"suicidality"`, `"suicide attempt"`, `"suicidal behavior"`, `"suicidal ideations"`
* **`tendon_rupture`:** `"ruptured tendon"`, `"achilles tendon rupture"`, `"achilles tear"`, `"tendon tear"`, `"tendon injury"`
* **`teratogenicity`:** `"birth defects"`, `"congenital malformation"`, `"congenital anomalies"`, `"fetal toxicity"`, `"embryotoxicity"`
* **`tooth_eruption`:** `"teeth eruption"`, `"delayed tooth eruption"`, `"eruption of tooth"`

#### Curated Drug Alias Table (Brand Names, INN, & Abbreviations):
* **`albuterol`:** `"salbutamol"`, `"ventolin"`, `"proair"`
* **`valproic_acid`:** `"valproate"`, `"sodium valproate"`, `"depakote"`, `"depakene"`
* **`hydrochlorothiazide`:** `"hctz"`, `"microzide"`
* **`fluoxetine`:** `"prozac"`
* **`sertraline`:** `"zoloft"`
* **`citalopram`:** `"celexa"`
* **`amlodipine`:** `"norvasc"`
* **`nifedipine`:** `"procardia"`, `"adalat"`
* **`captopril`:** `"capoten"`
* **`lisinopril`:** `"zestril"`, `"prinivil"`
* **`atorvastatin`:** `"lipitor"`
* **`montelukast`:** `"singulair"`
* **`ciprofloxacin`:** `"cipro"`
* **`metformin`:** `"glucophage"`
* **`rosiglitazone`:** `"avandia"`
* **`pioglitazone`:** `"actos"`
* **`clozapine`:** `"clozaril"`
* **`carbamazepine`:** `"tegretol"`
* **`isoniazid`:** `"inh"`
* **`isotretinoin`:** `"accutane"`, `"roaccutane"`
* **`pembrolizumab`:** `"keytruda"`
* **`adalimumab`:** `"humira"`
* **`imatinib`:** `"gleevec"`
* **`semaglutide`:** `"ozempic"`, `"wegovy"`
* **`liraglutide`:** `"victoza"`, `"saxenda"`

### Stage 2: Fuzzy String Fallback (`difflib.SequenceMatcher`)
If Stage 1 fails to find an exact or alias match, the input is passed to Stage 2:
1. **Algorithm:** Uses Python's built-in `difflib.SequenceMatcher(None, normalized_input, candidate).ratio()` against all canonical targets in the specified vocabulary. (Zero third-party dependencies required).
2. **Best Match Selection:** Computes similarity ratios across all candidates and identifies the candidate with maximum score $S_{\text{max}}$.
3. **Tri-Band Decision Logic:**
   * **High-Confidence Band ($S_{\text{max}} \ge 0.85$):**  
     Represents minor typographical errors (e.g., 1-character or 2-character slips). Auto-resolved without human interruption.  
     $$\text{confidence} = S_{\text{max}}, \quad \text{match\_type} = \text{"fuzzy"}, \quad \text{needs\_human\_review} = \text{False}$$
   * **Middle Band / Human Review Required ($0.65 \le S_{\text{max}} < 0.85$):**  
     Represents substantial orthographic distance where silent acceptance is unsafe in pharmacovigilance. The system returns the best candidate but flags it explicitly for human sign-off.  
     $$\text{confidence} = S_{\text{max}}, \quad \text{match\_type} = \text{"fuzzy"}, \quad \text{needs\_human\_review} = \text{True}$$
   * **Low-Confidence Band / Unmapped ($S_{\text{max}} < 0.65$):**  
     The string does not match any known target in the controlled vocabulary. It is rejected.  
     $$\text{canonical} = \text{None}, \quad \text{confidence} = S_{\text{max}}, \quad \text{match\_type} = \text{"unmapped"}, \quad \text{needs\_human\_review} = \text{False}$$

---

## 5. Threshold Justification & Empirical Calibration

| Threshold Tier | Score Range | Empirical Behavior | Pharmacovigilance Rationale |
|---|:---:|---|---|
| **Exact Match** | $1.00$ | Identity match on canonical term | Full certainty; zero risk of deviation. |
| **Alias Match** | $0.98$ | Curated synonym / brand name table | Verified clinical synonymy; slight decrement from identity for provenance tracking. |
| **Fuzzy (Auto-Resolve)** | $[0.85, 1.00)$ | Captures 1–2 character typos on 10–15 character words (e.g. `hepatoxicity` = 0.923, `montelucast` = 0.909, `ciprofloxacine` = 0.963) | High character overlap ensures typographical correction without altering drug identity. |
| **Fuzzy (Needs Review)**| $[0.65, 0.85)$ | Truncated strings, stemming variations, or look-alike candidates | **Safety Guard:** Look-alike/sound-alike errors are a major clinical safety risk. Flagging ensures safety teams inspect ambiguous suggestions. |
| **Unmapped (Rejection)** | $< 0.65$ | Dissimilar strings (e.g., `aspirin` vs `atorvastatin` = 0.421, random text) | Prevents arbitrary hallucinated mappings onto the vocabulary. |

---

## 6. Functional Interface & Contract

The function will be implemented in `pharmaguard/utils/canonicalize.py` as an opt-in standalone utility:

```python
def canonicalize_term(
    raw_input: str,
    term_type: Literal["drug", "event"],
) -> dict[str, Any]:
    """
    Canonicalize a raw drug or adverse event string into PharmaGuard's controlled vocabulary.

    Parameters:
        raw_input: Raw colloquial or clinical text string.
        term_type: Domain selector ("drug" or "event").

    Returns:
        Dictionary adhering to:
        {
            "canonical": str | None,          # Normalized canonical string or None if unmapped
            "confidence": float,              # Similarity score (0.0 to 1.0)
            "match_type": str,                # "exact" | "alias" | "fuzzy" | "unmapped"
            "needs_human_review": bool,       # True if match is in the 0.65–0.84 uncertainty band
            "original_input": str             # Preserved raw input for auditing
        }
    """
```

### Opt-In Architectural Invariant:
* This module is an **additive utility**.
* It is **NOT** wired into the existing `FixedPipelineAgent` or `PharmaGuardAgent` execution paths.
* It does **NOT** alter the frozen 15-pair primary benchmark or the 32-pair OMOP secondary benchmark datasets.
* It serves as an intake utility for future interactive tools, CLI wrappers, and expanded surveillance pipelines.

---
*End of Design Document — Awaiting Supervisor / User Review before Phase 2 Implementation.*
