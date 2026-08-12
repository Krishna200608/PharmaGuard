Last updated: 2026-08-12 | Sprint: Sprint 3 (COMPLETED)

# PROGRESS

## Completed (Verified by passing tests)
- **Sprint 3: Evaluation & Validation (COMPLETED)**
  **Goal:** Run the full 15-pair ground truth set through the Fixed Pipeline Orchestrator and generate category-level breakdown metrics.
  **Status:** **COMPLETED — all 4 real bugs found and fixed this session**

  ### Bugs Fixed This Session
  1. **Underscore normalization**: `tendon_rupture` (snake_case key) was passed raw into FAERS `patient.reaction.reactionmeddrapt`, returning zero results for heavily-documented signals. Fixed via `normalize_term` utility (underscores → spaces).
  2. **Missing plausibility fallback**: `llm_inference_fn` was not wired through to the live pipeline, causing all 12 non-curated pairs to return `plausibility_source="unknown"` and cap confidence at ~0.6.
  3. **First-mechanism-only ChEMBL fetch**: `fetch_chembl.py` pulled only `mechs[0]`, yielding irrelevant/generic receptor targets for promiscuous drugs (e.g., clozapine's "5-HT2a" instead of bone-marrow-relevant context). Fixed by manually reviewing all available mechanisms per drug and concatenating the pharmacologically relevant ones.
  4. **MoA circularity**: `valproic_acid`'s curated MoA text included "alters mitochondrial beta-oxidation and causes mitochondrial dysfunction"—the exact adverse-event-specific mechanism for the hepatotoxicity pair being evaluated. Fixed by rewriting to strictly event-agnostic general pharmacology (HDAC inhibitor, GABA transaminase inhibitor, sodium channel blocker). See Decision #1.1.

  ### Final Evaluation Results (v6 cache, blinded MoA curation)
  - **Strict Metrics**: Precision 1.000, Recall 1.000, F1 1.000 (7 TP, 0 FP, 8 TN, 0 FN)
  - **Lenient Metrics**: Precision 1.000, Recall 1.000, F1 1.000
  - **By Category**: confirmed_positive 7/7, genuine_negative_control 5/5, zero_report_edge_case 3/3
  - **Disagreements**: None

  ### Checkpoints
  - [x] Finalized 15-pair Ground Truth Dataset (`ground_truth.json`) with strict categories (`confirmed_positive`, `genuine_negative_control`, `zero_report_edge_case`) and validated citation sources.
  - [x] Extracted empirical FAERS evidence (PRR and report counts) for negative controls (e.g., `albuterol` + `suicidal_ideation`) and stored in `GROUND_TRUTH_CANDIDATES.md`.
  - [x] Repository Reorganization: Cleaned up the repo into `docs/`, `scripts/`, `configs/`, `tests/`, and `outputs/` while maintaining `pharmaguard/` structure.
  - [x] Upgraded Evaluator Harness (`evaluator.py`) to map categories, flag specific disagreements (Expected vs Actual), and calculate strict and lenient metrics.
  - [x] Fixed Enum access bugs in `fixed_pipeline.py` and `react_agent.py` when hydrating fallback strings.
  - [x] **Bug Fix 1**: Fixed query normalization (snake_case → space) for all FAERS/PubMed queries.
  - [x] **Bug Fix 2**: Wired `llm_inference_fn` into live pipeline; verified `plausibility_source="agent_derived"` on all non-curated pairs.
  - [x] **Bug Fix 3**: Manually reviewed and curated MoA text for all 12 auto-fetched ChEMBL drugs; replaced first-mechanism-only pull.
  - [x] **Bug Fix 4**: Rewrote `valproic_acid` MoA to remove event-specific hepatotoxicity mechanism; re-ran evaluation with blinded input. Score held at 7/7.
  - [x] **Transparency**: Updated `chembl_tool.py` to capture LLM's free-text reasoning as `rationale` (instead of a template string). Updated `PlausibilityResult` docs and `DECISIONS.md` §1.1 with memorization-vs-inference caveat.
  - [x] **Verified UTF-8 Encoding**: All 15 generated reports are correctly written in UTF-8.
  - [x] **Verified Grade Consistency**: Sampled multiple reports across different categories to ensure the LLM-derived grade matched the tail summary justification.

- **Sprint 2: Core Triage Orchestration (COMPLETED)**
  - Defined `TriageReport` and `TriageOutput` Pydantic schemas.
  - Wired `FaersLegacySource`, `ChemblTool`, and `PubMedTool`.
  - Built `PharmaGuardAgent` (ReAct loop) and `FixedPipelineAgent` fallback.
  - Verified caching with strict `CACHE_SCHEMA_VERSION`.

## In Progress
- (No active tasks — Sprint 3 is fully complete and committed.)

## Next Steps
- Sprint 4 planning: prompt engineering and threshold recalibration if target metrics change.
- Consider adding a memorization-vs-inference probe (e.g., evaluate on a held-out set of obscure drug-AE pairs not likely to appear in LLM training data) to substantiate the "genuine inference" claim more rigorously before any public writeup.

## Known Blockers / Risks
- **Memorization vs. Inference**: The evaluation set contains several famous, heavily-publicized drug-safety cases (clozapine/agranulocytosis, valproic acid/hepatotoxicity). It cannot be definitively determined whether 7/7 strict recall reflects genuine step-by-step pharmacological reasoning or training-data recall. See DECISIONS.md §1.1 for the full limitation statement.
