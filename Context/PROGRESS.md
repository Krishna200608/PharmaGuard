Last updated: 2026-08-10 | Sprint: Sprint 2 (COMPLETED)

# PROGRESS

## Completed (Verified by passing tests)
- **Sprint 2: Core Triage Orchestration (COMPLETED)**
  **Goal:** Wire the three tools together using a LangGraph ReAct agent and establish the fallback fixed pipeline.
  **Status:** **COMPLETED** (Verified via unit tests + live-run end-to-end against real APIs)
  ### Checkpoints
  - [x] Define `TriageReport` and `TriageOutput` Pydantic schemas (Agent Contract).
  - [x] Wire `FaersLegacySource`, `ChemblTool`, and `PubMedTool` as Langchain tools.
  - [x] Build `PharmaGuardAgent` using LangGraph (ReAct loop, 15-step recursion limit).
  - [x] Build `FixedPipelineAgent` fallback (deterministic sequence).
  - [x] Set up YAML-based config (`config.yaml`) to decouple hardcoded values (like LLM models).
  - [x] **Verified via Live Run**: Successfully ran the 3 pilot pairs through both ReAct and Fixed Pipeline modes.
  - [x] **Verified LLM Extraction**: Migrated to Pydantic `with_structured_output` for grading and plausibility parsing, verified via adversarial unit tests AND live API re-runs confirming correctly extracted output JSON schemas.
  - [x] **Verified Caching**: Cache keys strictly versioned against prompt changes AND logic changes (`CACHE_SCHEMA_VERSION`).
- **Tool Scaffolding**: FaersLegacySource, ChemblTool, and PubMedTool are fully implemented and passing unit tests. 48/48 tests are currently green.
- **PubMed Semantic Grading**: Refactored to leverage an LLM inference hook with strict cache versioning based on the rubric, completely eliminating the flawed keyword-matching logic. Adversarial testing verifies non-statistical tokens like " or " are graded correctly.
- **FAERS Caching & OpenFDA API Key**: Caching finalized via a single _finalize() step so all paths return from the cache safely. OpenFDA API key securely wired to OPENFDA_API_KEY from .env.
- **Output Schemas**: TriageReport and sub-models strictly defined in Pydantic. Deterministic confidence scoring and hard NO_SIGNAL gating verified in tests.
- **Cache Infrastructure**: Persistent diskcache implementation running smoothly with specialized keys (aers_key, pubmed_key, pubmed_grade_key, plausibility_key).
- **Sprint 2: ReAct Orchestrator**: Developed LangGraph-based agent loop, logging raw transcripts via `TranscriptLogger`.
- **Sprint 2: Config Loader**: `config_loader.py` securely parses `config.yaml` for dynamic agent routing.

## In Progress
- (No active orchestration tasks, pending Sprint 3 evaluation handoff)

## Next Steps
- (Teammate 1) Finalize Pilot Dataset (ground_truth.json). **NOT YET IMPLEMENTED**.
- (Teammate 2) Implement Evaluation Harness (evaluator.py) to parse TriageReport JSON outputs using strict/lenient rules laid out in NOTES.md. **NOT YET IMPLEMENTED**.


## Known Blockers / Risks
- **Rate Limit Bottlenecks**: OpenFDA legacy migration may cause instability. Any changes to the legacy API could immediately break FaersLegacySource.
- **Prompt Iteration Requirements**: Prompts (eact_tool_call_format.txt, synthesis_prompt.txt) exist as stubs but have not been formally evaluated in the live LangGraph loop.
- **Evaluator Logic Gap**: evaluator.py relies on teammate integration and remains unscaffolded.
