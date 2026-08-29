> **SESSION BOOTSTRAP**: At the beginning of every session, immediately read all files in the `docs/context/` folder. Do not begin execution until you have read and internalized the current ground truth.

Last updated: 2026-08-29 | Sprint: Completed Capstone Benchmark (Sprint 3 Verified & Novelty Probes Complete) | Updated by: Antigravity

# PROJECT OVERVIEW

## Problem Statement & Goals
PharmaGuard is an evidence-grounded pharmacovigilance triage system designed to evaluate drug–adverse event pairs and issue safety recommendations (**ESCALATE / MONITOR / DO_NOT_ESCALATE**). It operates as an automated triage layer to filter safety signals using three real-world biomedical data streams:
- Statistical disproportionality (PRR, ROR, 95% CIs) from OpenFDA / FAERS.
- Mechanism of action and biological plausibility lookup from ChEMBL.
- Evidence grading (Grades A/B/C) from PubMed medical literature.

The project is a 7th-semester B.Tech academic capstone owned and developed by Krishna Sikheriya (IIT2023139) under supervisor Dr. Nikhilanand Arya at IIIT Allahabad.

## Target Scope
- **Evaluation Benchmark**: Strictly fixed at **15 hand-curated drug–event pairs** (`pharmaguard/data/ground_truth.json`), spanning 7 confirmed positives, 5 genuine negative controls, and 3 zero-report edge cases. This 15-pair set is the settled, frozen production benchmark evaluated with dual-metric (strict/lenient) statistical evaluation, Wilson score and BCa bootstrap 95% confidence intervals, and 15-fold Leave-One-Out (LOO) stability analysis.
- **Output Artifacts**: Structured, typed JSON `TriageReport` outputs decoupling data-fetching and agent orchestration from evaluation and dashboard modules.
- **Interactive Dashboard**: Production Streamlit application (`scripts/dashboard.py`) providing 5 dedicated views (Overview with LOO stability cards, Per-Pair Table with cross-source agreement badges, Disagreement Spotlight, Baseline Comparison, and Methodology Probes with Google Material Icons).

## Explicit Out of Scope Boundaries
- **Dynamic ChEMBL ID Resolution**: Out of scope. IDs and mechanisms are mapped via a pre-resolved static table (`data/chembl_lookup.json`) for absolute determinism.
- **Dataset Scaling**: The benchmark is intentionally bounded to the 15 vetted pairs to guarantee comprehensive regulatory sourcing and reproducibility within the capstone scope. Expanding to large-scale OMOP/EU-ADR sets is deferred to future work.
- **Human Expert Pharmacological Panel**: Formal review of biological plausibility by external clinical pharmacologists is deferred as future research scope.
- **Escalation Threshold Optimization**: Thresholds (0.70 / 0.35) and concordance heuristic bounds (0.66 / 0.33) are documented operational priors; empirical ROC/Youden's J calibration requires a larger sample size than n=15 and is out of scope.

## Hard Constraints
- **Infrastructure**: Constrained to Gemini Flash API free tier. No paid cloud compute. No GPU or external notebook dependencies.
- **Data Integrity**: Public APIs only (openFDA FAERS legacy endpoint, ChEMBL REST, NCBI PubMed E-utilities). Frozen production benchmark reports under `outputs/` are never overwritten.
- **Rate Limits & Caching**: Disk-backed caching via `diskcache` (`ToolCache`) with schema and prompt versioning keys (`CACHE_SCHEMA_VERSION`, `prompts_version`) to guarantee reproducibility and prevent API quota exhaustion.