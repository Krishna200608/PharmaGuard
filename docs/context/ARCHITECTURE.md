Last updated: 2026-08-12 | Sprint: Sprint 3 (COMPLETED) | Updated by: Antigravity

# ARCHITECTURE

## Overview

PharmaGuard is a pharmacovigilance triage agent that assesses drug-adverse event
pairs and issues one of three decisions: **ESCALATE / MONITOR / DO_NOT_ESCALATE**.
It integrates three real-world data sources (FAERS disproportionality data, ChEMBL
mechanism-of-action metadata, PubMed literature grading) into a deterministic
confidence formula and escalation rule set. All external calls are cache-backed.

---

## Repo Structure

```
pharmaguard/                  # Python package (core source)
│
├── agent/
│   ├── fixed_pipeline.py     # Fixed-order orchestrator (production default)
│   ├── react_agent.py        # LangGraph ReAct orchestrator (LLM-driven order)
│   ├── output_schema.py      # Pydantic output schema + confidence formula
│   └── transcript_logger.py  # Per-run JSON transcript writer → run_logs/
│
├── tools/
│   ├── signal_source.py      # Abstract SignalDataSource + FaersLegacySource
│   ├── chembl_tool.py        # ChEMBL static lookup + plausibility derivation
│   ├── pubmed_tool.py        # NCBI E-utilities + LLM evidence grading
│   └── cache.py              # Disk-backed ToolCache (diskcache)
│
├── utils/
│   ├── config_loader.py      # Parses configs/config.yaml → AppConfig
│   ├── prompt_loader.py      # Loads versioned prompt files from pharmaguard/prompts/
│   └── text.py               # normalize_term(): snake_case → natural language
│
├── data/
│   ├── chembl_lookup.json    # Pre-resolved ChEMBL IDs + MoA text (15 drugs)
│   ├── plausibility_ratings.json  # Human-curated plausibility labels (lookup default)
│   ├── ground_truth.json     # 15-pair evaluation set with categories + citations
│   └── pilot_set.json        # 3-pair quick-check set for development runs
│
└── prompts/
    ├── baseline_single_shot.txt    # Single-shot prompt for baseline.py
    ├── evidence_grading_rubric.txt # Grade A/B/C rubric for PubMed LLM grading
    ├── react_system.txt            # ReAct agent system prompt
    ├── react_tool_call_format.txt  # Tool-call format instructions for ReAct
    ├── synthesis_prompt.txt        # Synthesis step prompt
    └── prompts_version.txt         # Current version string (currently v1.0)

configs/
└── config.yaml               # All runtime settings (mode, model, weights, cache, APIs)

scripts/
├── run_eval.py               # Run all 15 ground truth pairs → outputs/
├── run_pilot.py              # Run 3-pair pilot set → outputs/
├── evaluator.py              # Score TriageReport JSONs against ground_truth.json
├── baseline.py               # Single-shot Gemini baseline (no tool use)
├── check_albuterol.py        # One-off FAERS probe for albuterol+suicidal_ideation
└── verify_reports.py         # Quick sanity-check on output JSON structure

tests/                        # pytest unit tests (51 tests, all passing)
docs/
├── NOTES.md                  # Design constraints, escalation thresholds
└── context/
    ├── ARCHITECTURE.md       # This file
    ├── CONVENTIONS.md        # Coding and data-curation conventions
    ├── DECISIONS.md          # Design decision log with rationale
    ├── PROGRESS.md           # Sprint progress and bug log
    ├── PROJECT_OVERVIEW.md   # High-level project description
    └── GROUND_TRUTH_CANDIDATES.md  # Ground truth sourcing + FAERS evidence

outputs/
├── eval-run-*_report.json    # TriageReport JSONs from the main pipeline
└── baseline/
    └── eval-run-*_report.json  # TriageReport JSONs from baseline.py

run_logs/                     # Per-run JSON transcripts (TranscriptLogger)
```

---

## Dual Agent Modes

Both modes are **production-verified**: each has been run against the full 15-pair
ground truth set and produced scored TriageReport outputs.

Mode is selected via `config.yaml → agent.mode` (`"fixed_pipeline"` | `"react"`).
The entry point `scripts/run_eval.py` respects this setting at runtime.

### Fixed Pipeline (`pharmaguard/agent/fixed_pipeline.py`) — current default
- **Class**: `FixedPipelineAgent`
- **Execution order**: deterministic — FAERS → ChEMBL → PubMed → synthesize
- Injects `chembl_llm_fn` into `ChemblTool` for agent-derived plausibility
- Injects `pubmed_llm_fn` into `PubMedTool` for LLM evidence grading
- Structured LLM outputs via `GradeOutput` and `PlausibilityLLMOutput` Pydantic
  models (prevents adversarial label contamination from explanation text)
- **Evidence**: 15/15 pairs, P=1.000 R=1.000 F1=1.000 (strict)

### ReAct Agent (`pharmaguard/agent/react_agent.py`) — `mode: react`
- **Class**: `PharmaGuardAgent`
- **Execution order**: LLM-driven via LangGraph ReAct loop; tool calls decided
  dynamically based on conversation state
- Uses `langchain_core.tools` decorated tool wrappers; same underlying
  `FaersLegacySource`, `ChemblTool`, `PubMedTool` as the fixed pipeline
- Identical `chembl_llm_fn` injection pattern for plausibility consistency
- **Evidence**: verified on pilot set; full 15-pair run available

---

## Data Flow (Fixed Pipeline, typical run)

```
Input: (drug: str, event: str)
         │
         ▼
  1. FaersLegacySource.get_signal_stats(drug, event)
     - normalize_term(event): snake_case → spaces before any API call
     - OpenFDA /drug/event.json: co-occurrence counts + PRR + ROR + lower CIs
     - compute_prr_score() → (prr_score: float, signal_strength: SignalStrength, ci_downgraded: bool)
     - All paths route through _finalize() → guaranteed cache write
         │
         ▼
  2. ChemblTool.get_plausibility(drug, event)
     - Static lookup in chembl_lookup.json (ChEMBL ID + MoA text)
     - plausibility_ratings.json lookup (human-curated, production default)
     - On cache miss or force_agent mode: LLM call → PlausibilityLevel + explanation text
     - Returns PlausibilityResult with level, score, source, rationale
         │
         ▼
  3. PubMedTool.fetch_and_grade(drug, event)
     - normalize_term(event) before query construction
     - NCBI E-utilities: fetches up to max_pubmed_abstracts abstracts
     - LLM grades evidence via evidence_grading_rubric.txt → GradeOutput(grade, explanation)
     - Returns: evidence_grade, grade_score, supporting_pmids, evidence_summary
         │
         ▼
  4. Confidence + Escalation (output_schema.py — fully deterministic)
     - confidence = 0.40 × prr_score + 0.40 × grade_score + 0.20 × plausibility_score
     - derive_escalation(confidence, signal_strength) — see below
         │
         ▼
  5. TriageReport (Pydantic) → written to outputs/eval-run-*_report.json
```

---

## Confidence Formula and Escalation Gate

```python
# weights defined in both output_schema.py and configs/config.yaml (must stay in sync)
confidence = 0.40 * prr_score + 0.40 * grade_score + 0.20 * plausibility_score
```

Sub-score ranges:
- `prr_score`: 0.0 (NO_SIGNAL) / 0.33 (WEAK) / 0.66 (MODERATE) / 1.0 (STRONG)
- `grade_score`: A=1.0, B=0.5, C=0.0
- `plausibility_score`: HIGH=1.0, MODERATE=0.5, LOW=0.0, UNKNOWN=0.0

**Maximum achievable confidence with NO_SIGNAL FAERS data = 0.60**
(grade-A * 0.40 + HIGH plausibility * 0.20 = 0.60)

### Escalation rules (`derive_escalation` — evaluated top to bottom, first match wins)

| Priority | Condition | Decision |
|---|---|---|
| 1 | `signal_strength == NO_SIGNAL` | **DO_NOT_ESCALATE** (hard gate — fires before confidence check; confidence is *ignored*) |
| 2 | `confidence >= 0.70` AND `signal_strength in {STRONG, MODERATE}` | **ESCALATE** |
| 3 | `confidence >= 0.35` | **MONITOR** |
| 4 | Otherwise | **DO_NOT_ESCALATE** |

> The NO_SIGNAL gate is intentional: a zero-report pair can theoretically reach
> confidence=0.60 from grade-A literature + HIGH plausibility alone. Without the
> hard gate, such pairs would receive MONITOR despite no FAERS disproportionality
> evidence. Thresholds 0.70 and 0.35 are uncalibrated priors — see `docs/NOTES.md`.

---

## Evaluation Harness (`scripts/evaluator.py`)

Reads `eval-run-*_report.json` files from an outputs directory and scores them
against `pharmaguard/data/ground_truth.json`.

**Metrics computed:**
- **Strict metrics**: ESCALATE-only counts as TP
- **Lenient metrics**: ESCALATE or MONITOR counts as TP
- Both: Precision, Recall, Specificity, F1
- **Category breakdown**: per `confirmed_positive` / `genuine_negative_control` / `zero_report_edge_case`
- **Over-Caution Rate**: MONITOR on known-negative pairs

**CLI flags (additive — default behaviour unchanged):**
```
--outputs-dir PATH   Directory of report JSONs. Default: outputs/
--title TEXT         Label in report header. Default: "PharmaGuard"
```

---

## Baseline (`scripts/baseline.py`)

Single-shot Gemini comparison: one LLM call per pair, no tool use, no database
access. Produces TriageReport JSON to `outputs/baseline/` with null sentinel values
for `signal_stats`, `mechanism`, and `literature` sub-objects so `evaluator.py`
can score it without modification.

Cache key: `baseline::{drug}::{event}::{prompts_version}::{CACHE_SCHEMA_VERSION}`

**Warning - Confidence comparability:**
PharmaGuard's `confidence` is the deterministic formula above. Baseline's
`confidence` is raw LLM self-report with no data grounding. **Escalation decisions
are directly comparable; confidence numbers are not on the same scale and must not
be visually compared directly.** See `DECISIONS.md section 12` for the standard footnote
to attach to any comparison table.

**Sprint 3 results (15-pair set, gemini-3.1-flash-lite, same model both systems):**

| System | Strict P | Strict R | Strict F1 | Lenient P | Lenient R | Lenient F1 |
|---|---|---|---|---|---|---|
| PharmaGuard (Fixed Pipeline) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Baseline (Single-Shot LLM) | 0.875 | 1.000 | 0.933 | 0.700 | 1.000 | 0.824 |

---

## Caching and Rate-Limit Strategy

All external calls (FAERS, PubMed, ChEMBL LLM derivation, baseline LLM) are
fronted by `ToolCache` (`pharmaguard/tools/cache.py`, backed by `diskcache`).

Key naming conventions (all include `CACHE_SCHEMA_VERSION` for schema-version invalidation):
```
FAERS:        faers::{drug_lower}::{event_lower}::{CACHE_SCHEMA_VERSION}
PubMed fetch: pubmed::{sha256(query)[:16]}
PubMed grade: pubmed_grade::{sha256(query)[:16]}::{prompts_version}::{CACHE_SCHEMA_VERSION}
Plausibility: plausibility::{drug_lower}::{event_lower}::{prompts_version}::{CACHE_SCHEMA_VERSION}
Baseline:     baseline::{drug_lower}::{event_lower}::{prompts_version}::{CACHE_SCHEMA_VERSION}
```

`CACHE_SCHEMA_VERSION` is currently **`v6`** (defined in `cache.py`).

---

## Tech Stack (verified from `requirements.txt`)

| Package | Role |
|---|---|
| `langchain>=0.2.0` | LLM orchestration |
| `langgraph>=0.1.0` | ReAct graph execution |
| `langchain-google-genai>=1.0.0` | Gemini API client |
| `pydantic>=2.0.0` | Schema validation + structured LLM outputs |
| `diskcache>=5.6.0` | Persistent disk-backed cache |
| `requests>=2.31.0` | HTTP queries (FAERS, NCBI) |
| `pytest>=8.0.0` | Test runner |
| `pandas>=2.0.0`, `matplotlib>=3.8.0` | Evaluation analysis |

Active model: **`gemini-3.1-flash-lite`** (configured in `config.yaml`).
See `DECISIONS.md section 10` for the rationale and mid-semester verification recommendation.
