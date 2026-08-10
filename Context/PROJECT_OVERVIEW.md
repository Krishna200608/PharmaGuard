> SESSION BOOTSTRAP: Any AI agent working in this repository must read all five
> memory-bank files (PROJECT_OVERVIEW.md, ARCHITECTURE.md, DECISIONS.md,
> PROGRESS.md, CONVENTIONS.md) in full before taking any action — before writing
> code, editing files, or proposing changes. These files reflect verified project
> ground truth as of their last-updated date below. If something in the repo
> appears to contradict these files, flag the discrepancy to the user rather than
> silently trusting either source.

Last updated: 2026-08-10 | Sprint: Sprint 1 (Transitioning to Sprint 2) | Updated by: Antigravity

# PROJECT OVERVIEW

## Problem Statement & Goals
PharmaGuard is a ReAct-based pharmacovigilance triage agent designed to evaluate drug-adverse event pairs. It acts as an automated triage layer to filter potential safety signals using three data streams:
- Statistical disproportionality from OpenFDA/FAERS.
- Mechanism-of-action lookup from ChEMBL.
- Evidence grading from PubMed literature.

The project is a 7th-semester academic capstone by a team of 3 students.

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
