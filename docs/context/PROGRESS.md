Last updated: 2026-08-11 | Sprint: Sprint 3 (COMPLETED)

# PROGRESS

## Completed (Verified by passing tests)
- **Sprint 3: Evaluation & Validation (COMPLETED)**
  **Goal:** Run the full 15-pair ground truth set through the Fixed Pipeline Orchestrator and generate category-level breakdown metrics.
  **Status:** **COMPLETED**
  ### Checkpoints
  - [x] Finalized 15-pair Ground Truth Dataset (`ground_truth.json`) with strict categories (`confirmed_positive`, `genuine_negative_control`, `zero_report_edge_case`) and validated citation sources.
  - [x] Extracted empirical FAERS evidence (PRR and report counts) for negative controls (e.g., `albuterol` + `suicidal_ideation`) and stored in `GROUND_TRUTH_CANDIDATES.md`.
  - [x] Repository Reorganization: Cleaned up the repo into `docs/`, `scripts/`, `configs/`, `tests/`, and `outputs/` while maintaining `pharmaguard/` structure.
  - [x] Upgraded Evaluator Harness (`evaluator.py`) to map categories, flag specific disagreements (Expected vs Actual), and calculate strict and lenient metrics.
  - [x] Fixed Enum access bugs in `fixed_pipeline.py` and `react_agent.py` when hydrating fallback strings.
  - [x] **Verified via Live Run**: Successfully ran all 15 pairs across the APIs and evaluated them.
  - [x] **Verified UTF-8 Encoding**: All 15 generated reports are correctly written in UTF-8.
  - [x] **Verified Grade Consistency**: Sampled multiple reports across different categories to ensure the LLM-derived grade matched the tail summary justification.

- **Sprint 2: Core Triage Orchestration (COMPLETED)**
  - Defined `TriageReport` and `TriageOutput` Pydantic schemas.
  - Wired `FaersLegacySource`, `ChemblTool`, and `PubMedTool`.
  - Built `PharmaGuardAgent` (ReAct loop) and `FixedPipelineAgent` fallback.
  - Verified caching with strict `CACHE_SCHEMA_VERSION`.

## In Progress
- (No active orchestration tasks, pending next steps)

## Next Steps
- Finalize documentation, commit and push changes.
- Review evaluation metrics to strategize prompt engineering and tuning for the agent (e.g. why are there false negatives on confirmed positives?).

## Known Blockers / Risks
- **Over-caution vs False Negatives**: Current iteration yields high specificity (1.000) but low recall (0.000 Strict, 0.429 Lenient). The agent defaults heavily to DO_NOT_ESCALATE on confirmed positive pairs. This will require iteration on the system prompts and scoring weights.
