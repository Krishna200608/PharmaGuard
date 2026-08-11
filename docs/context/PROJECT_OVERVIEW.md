> **SESSION BOOTSTRAP**: At the beginning of every session, immediately read all 5 files in the `docs/context/` folder (`PROJECT_OVERVIEW.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `PROGRESS.md`, `CONVENTIONS.md`). Do not begin execution until you have read and internalized the current ground truth.

Last updated: 2026-08-10 | Sprint: Sprint 2 (COMPLETED) | Updated by: Antigravity

# PROJECT OVERVIEW

## Problem Statement & Goals
PharmaGuard is a ReAct-based pharmacovigilance triage agent designed to evaluate drug-adverse event pairs. It acts as an automated triage layer to filter potential safety signals using three data streams:
- Statistical disproportionality from OpenFDA/FAERS.
- Mechanism-of-action lookup from ChEMBL.
- Evidence grading from PubMed literature.

The project is a 7th-semester academic capstone owned and developed entirely by a single student (Krishna).

## Target Scope
- **Evaluation Set**: Mid-semester demo targets 8-10 verified drug-event pairs. End-semester targets 15-20 verified pairs with baseline comparisons.
- **Output**: Structured JSON TriageReport output to decouple agent internals from the evaluation module.

## Explicit Out of Scope Boundaries
- **Dynamic ChEMBL ID Resolution**: Out of scope. IDs are mapped statically to ensure absolute reliability.
- **Scaling/Productionization**: The evaluation is strictly bounded to the 15-20 target pairs.
- **Complex Evidence Grading Improvements**: Post mid-sem demo features (e.g., recency weighting, study-type detection) are out of scope for Sprint 1.

## Hard Constraints
- **Infrastructure**: Strictly constrained to Gemini Flash API free tier. No paid compute. No GPUs or Google Colab dependencies.
- **Data**: Public APIs only (OpenFDA legacy API, ChEMBL REST, PubMed E-utilities). No PHI-gated data.
- **Rate Limits**: Extremely tight. Caching via diskcache and exponential backoffs are mandatory requirements, not optional optimizations.
