Last updated: 2026-08-29 | Sprint: Completed Capstone Benchmark | Updated by: Antigravity

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
│   ├── confounding.py        # ConfoundingTool + ConfoundingAssessment schema
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
    ├── confounding_assessment.txt  # Confounding assessment evaluator prompt
    └── prompts_version.txt         # Current version string (currently v1.1)

configs/
└── config.yaml               # All runtime settings (mode, model, weights, cache, APIs)

scripts/
├── run_eval.py               # Run all 15 ground truth pairs → outputs/
├── run_pilot.py              # Run 3-pair pilot set → outputs/
├── evaluator.py              # Score TriageReport JSONs against ground_truth.json
├── baseline.py               # Single-shot Gemini baseline (no tool use)
├── stability_analysis.py     # 15-fold Leave-One-Out (LOO) stability analysis
├── run_critic_probe.py       # Adversarial mechanistic leakage critic probe
├── run_confounding_probe.py  # Confounding self-probe harness
├── generate_paper_figures.py # Publication-ready figure generator
├── dashboard.py              # Multi-view Streamlit dashboard entrypoint
├── dashboard_modules/        # Modular dashboard views, components, and styles
├── check_albuterol.py        # One-off FAERS probe for albuterol+suicidal_ideation
└── verify_reports.py         # Quick sanity-check on output JSON structure

tests/                        # pytest unit tests (51 tests, all passing)
docs/
└── context/
    ├── ARCHITECTURE.md       # Technical architecture & schema reference
    ├── CONTRIBUTION.md       # Grounded project contribution claims
    ├── CONVENTIONS.md        # Coding and data-curation conventions
    ├── DECISIONS.md          # Complete 29-section design decision record
    ├── GROUND_TRUTH_CANDIDATES.md  # Ground truth sourcing + regulatory citations
    ├── NOTES.md              # Design constraints, escalation thresholds
    ├── PROGRESS.md           # Continuous sprint log and audit history
    ├── PROJECT_OVERVIEW.md   # High-level project summary and scope boundaries
    └── UNDERSTAND.md         # Comprehensive project guide and results walk-through

outputs/
├── eval-run-*_report.json    # Frozen production TriageReport JSONs (15 pairs)
├── baseline/                 # Single-shot LLM baseline reports
├── ablation/                 # Force-agent derivation ablation reports
├── react_agent/              # ReAct LangGraph agent reports
├── stability/                # Leave-One-Out cross-validation outputs (loo_analysis.json)
├── critic_probe/             # Adversarial critic audit results
├── confounding_probe/        # Confounding self-probe and Metformin reports
└── paper_figures/            # High-resolution publication figures

assets/
└── Screenshots/              # 1080p dashboard captures (Light and Dark themes)

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
- **Performance**: Strict P=1.000, R=0.857, F1=0.923; Lenient P=0.875, R=1.000, F1=0.933 (`PROGRESS.md`, `DECISIONS.md §16`)

### ReAct Agent (`pharmaguard/agent/react_agent.py`) — `mode: react`
- **Class**: `PharmaGuardAgent`
- **Execution order**: LLM-driven via LangGraph ReAct loop; tool calls decided
  dynamically based on conversation state
- Uses `langchain_core.tools` decorated tool wrappers; same underlying
  `FaersLegacySource`, `ChemblTool`, `PubMedTool` as the fixed pipeline
- Computes final reported escalation strictly via the shared deterministic formula
- **Empirical Divergence**: The agent's unconstrained freeform synthesis diverged from
  deterministic escalation on 4 of 15 pairs (26.7%), demonstrating why postmarketing
  safety requires deterministic evidence gating (`DECISIONS.md §24`)

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
     - Optional ConfoundingTool.assess() (if confounding.enabled: true):
       → computes discount_factor (0.0 to 1.0) and adjusted_prr_score = round(prr_score * discount_factor, 4)
     - All paths route through _finalize() → guaranteed cache write
         │
         ▼
  2. ChemblTool.get_plausibility(drug, event)
     - Static lookup in chembl_lookup.json (ChEMBL ID + MoA text)
     - plausibility_ratings.json lookup (human-curated, production default)
     - On cache miss or force_agent mode: LLM call → PlausibilityLevel + explanation text
     - Optional LeakageCritique maker-checker audit (if plausibility.leakage_critic.enabled: true)
     - Returns PlausibilityResult with level, score, source, rationale, leak flags
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
     - confidence = 0.40 × adjusted_prr_score + 0.40 × grade_score + 0.20 × plausibility_score
     - derive_escalation(confidence, signal_strength) — see below
         │
         ▼
  5. TriageReport (Pydantic) → written to outputs/eval-run-*_report.json
     - Computes source_agreement property (CONCORDANT vs. DISCORDANT)
```

---

## Confidence Formula and Escalation Gate

```python
# weights defined in both output_schema.py and configs/config.yaml (must stay in sync)
confidence = 0.40 * prr_score + 0.40 * grade_score + 0.20 * plausibility_score
```

Sub-score ranges:
- `prr_score`: 0.0 (NO_SIGNAL) / 0.33 (WEAK) / 0.66 (MODERATE) / 1.0 (STRONG)
  (When confounding assessment is active: `adjusted_prr_score = round(prr_score * discount_factor, 4)`)
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
> evidence. Thresholds 0.70 and 0.35 are uncalibrated priors — see `docs/context/NOTES.md` and `DECISIONS.md §18`.

---

## Pydantic Schemas & Core Data Models

PharmaGuard uses Pydantic v2 data models to enforce strictly typed schemas across tool outputs, orchestrator results, and serialization artifacts.

### 1. `TriageReport` (`pharmaguard/agent/output_schema.py`)
The primary document schema serialized to `outputs/eval-run-*_report.json`:

| Field | Type | Description |
|---|---|---|
| `schema_version` | `str = "1.1"` | Schema version identifier |
| `run_id` | `str` | Unique UUID4 run identifier |
| `timestamp` | `datetime` | UTC timestamp of report generation |
| `prompts_version` | `str` | Version tag of active prompts (e.g. `"v1.1"`) |
| `drug` | `str` | Evaluated active pharmaceutical ingredient |
| `event` | `str` | Adverse event MedDRA Preferred Term |
| `signal_stats` | `SignalStatsOutput` | Statistical disproportionality evidence |
| `mechanism` | `MechanismOutput` | Molecular mechanism & plausibility evidence |
| `literature` | `LiteratureOutput` | Biomedical literature grading evidence |
| `triage` | `TriageOutput` | Final confidence score and escalation decision |
| `source_agreement` | `Literal["CONCORDANT", "DISCORDANT"]` | **Computed property** (`@computed_field`) evaluating cross-source evidence concordance |

#### Cross-Source Agreement (`source_agreement`):
Evaluates agreement across the three normalized sub-scores ($S_{\text{FAERS}} = \text{prr\_score}$, $S_{\text{Lit}} = \text{grade\_score}$, $S_{\text{Mech}} = \text{plausibility\_score}$) via `compute_source_agreement()`:
$$\text{DISCORDANT} \iff \max(S_{\text{FAERS}}, S_{\text{Lit}}, S_{\text{Mech}}) \ge 0.66 \land \min(S_{\text{FAERS}}, S_{\text{Lit}}, S_{\text{Mech}}) \le 0.33$$
Otherwise classified as `"CONCORDANT"`. Isolates the 3 benchmark edge cases (`montelukast`, `metformin`, `atorvastatin::dementia`) exhibiting cross-modality divergence (`DECISIONS.md §26`).

### 2. `SignalStatsOutput` (`pharmaguard/agent/output_schema.py`)
Encapsulates openFDA FAERS disproportionality metrics and confounding adjustments:

| Field | Type | Description |
|---|---|---|
| `prr` | `Optional[float]` | Proportional Reporting Ratio ($A/(A+B) / C/(C+D)$) |
| `ror` | `Optional[float]` | Reporting Odds Ratio ($(A/B) / (C/D)$) |
| `prr_lower_ci` | `Optional[float]` | 95% lower confidence interval for PRR |
| `ror_lower_ci` | `Optional[float]` | 95% lower confidence interval for ROR |
| `report_count` | `int` | Total FAERS spontaneous co-occurrence count |
| `source_endpoint` | `str` | Source API identifier (`"openfda_legacy"`) |
| `data_pulled_at` | `datetime` | Data retrieval timestamp |
| `null_reason` | `Optional[str]` | Sentinel reason if data unavailable |
| `prr_score` | `float` | Base or adjusted statistical sub-score ($0.0, 0.33, 0.66, 1.0$) |
| `prr_score_label` | `SignalStrength` | Discrete tier: `STRONG`, `MODERATE`, `WEAK`, `NO_SIGNAL` |
| `ci_downgraded` | `bool` | True if lower CI gate forced a one-tier downgrade |
| `discount_factor` | `Optional[float] = None` | **Confounding discount multiplier** ($0.0 \le \text{factor} \le 1.0$), populated when confounding tool is enabled |
| `is_confounded` | `Optional[bool] = None` | True if signal is driven by polypharmacy or indication bias |
| `confounding_drugs` | `Optional[list[str]] = None`| Concomitant drugs contributing to disproportionality |
| `confounding_explanation`| `Optional[str] = None`| Clinical rationale for the confounding assessment |

### 3. `MechanismOutput` & `LeakageCritique` (`pharmaguard/agent/output_schema.py`)
Encapsulates ChEMBL target pharmacology, plausibility derivation, and critic audit results:

| Field | Type | Description |
|---|---|---|
| `chembl_id` | `Optional[str]` | ChEMBL compound identifier |
| `moa` | `Optional[str]` | Mechanism of action description |
| `biological_plausibility`| `PlausibilityLevel` | Discrete level: `HIGH`, `MODERATE`, `LOW`, `UNKNOWN` |
| `plausibility_score` | `float` | Sub-score mapping: `HIGH=1.0`, `MODERATE=0.5`, `LOW/UNKNOWN=0.0` |
| `plausibility_source` | `PlausibilitySource` | `"human_curated"`, `"agent_derived"`, or `"unknown"` |
| `plausibility_rationale`| `str` | Free-text biological rationale |
| `curated_reference` | `Optional[PlausibilityLevel]`| Human-curated benchmark reference label (in ablation mode) |
| `plausibility_agreement`| `Optional[bool]` | Concordance between agent-derived and curated labels |
| `leak_detected` | `Optional[bool] = None` | True if adversarial critic detected regulatory/parametric leakage |
| `leak_phrases` | `Optional[list[str]] = None`| Verbatim leak substrings isolated by the critic |

#### Adversarial Mechanistic Critic (`LeakageCritique`):
Pydantic model produced by the blinded maker-checker critic agent (`pharmaguard/tools/chembl_tool.py's _critique_plausibility_leakage() method (LeakageCritique model in pharmaguard/agent/output_schema.py)`, MARCH pattern) to audit rationales for non-mechanistic knowledge leakage (`DECISIONS.md §27`):

| Field | Type | Description |
|---|---|---|
| `leaked` | `bool` | True if non-mechanistic knowledge or clinical/regulatory leakage is detected |
| `leak_phrases` | `list[str]` | Verbatim substrings from the rationale indicating leakage |
| `mechanistic_only_score`| `Literal["HIGH", "MODERATE", "LOW"]` | Plausibility level considering solely molecular/biochemical mechanisms |
| `rationale_critique` | `Optional[str] = ""` | Brief evaluation summary from the critic |

### 4. `ConfoundingAssessment` (`pharmaguard/tools/confounding.py`)
Structured output generated by `ConfoundingTool.assess()` when evaluating spontaneous reporting for polypharmacy artifacts (`DECISIONS.md §28`):

| Field | Type | Description |
|---|---|---|
| `is_confounded` | `bool` | True if the FAERS signal is significantly driven by co-medications or indication confounding |
| `confounding_drugs` | `list[str]` | Concomitant medications or drug classes that independently contribute to the adverse event |
| `discount_factor` | `float` | Multiplier ($0.0 \le \text{discount\_factor} \le 1.0$) representing the fraction genuinely attributable to the candidate drug |
| `confounding_explanation`| `str` | Clinical and pharmacological rationale explaining the confounding assessment |

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
- **Uncertainty Quantification**: Wilson score intervals and non-parametric bootstrap resampling (B=1000, seed=42)

**CLI flags:**
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
be visually compared directly.** See `DECISIONS.md §12` for the standard footnote
to attach to any comparison table.

**Final verified benchmark results (15-pair set, gemini-3.1-flash-lite):**

| System | Strict P | Strict R | Strict F1 | Lenient P | Lenient R | Lenient F1 | Over-Caution Rate |
|---|---|---|---|---|---|---|---|
| PharmaGuard (Fixed Pipeline) | 1.000 | 0.857 | 0.923 | 0.875 | 1.000 | 0.933 | 12.5% (1/8) |
| Baseline (Single-Shot LLM) | 0.875 | 1.000 | 0.933 | 0.700 | 1.000 | 0.824 | 25.0% (2/8) |

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

`CACHE_SCHEMA_VERSION` is currently **`v7`** (defined in `cache.py`).

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
| `streamlit>=1.35.0` | Interactive evaluation dashboard |

Active model: **`gemini-3.1-flash-lite`** (configured in `config.yaml`).
See `DECISIONS.md section 10` for rationale.