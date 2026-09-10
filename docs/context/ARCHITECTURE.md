Last updated: 2026-09-10 | Sprint: Sprint 4 Phase 3 (Multi-Benchmark & Indication Concordance) | Updated by: Antigravity

# ARCHITECTURE

## Overview

PharmaGuard is an automated pharmacovigilance triage orchestrator that evaluates drug–adverse event
pairs and issues one of three auditable decisions: **ESCALATE / MONITOR / DO_NOT_ESCALATE**.
It integrates three primary empirical data sources (FAERS postmarketing disproportionality statistics,
ChEMBL target mechanism-of-action metadata, and PubMed literature grading) into a deterministic
confidence formula and escalation rule set. This core tri-source engine is augmented by a clinical
disease-context layer (`DiseaseContextTool`, resolving WHO ATC classifications) and an informational
confounding-by-indication evaluator (`IndicationConcordanceTool`). All external network queries are
fronted by a deterministic, persistent disk cache.

---

## Repo Structure

```
pharmaguard/                  # Python package (core source)
│
├── agent/
│   ├── fixed_pipeline.py     # Fixed-order orchestrator (production default)
│   ├── react_agent.py        # LangGraph ReAct orchestrator (dynamic tool call loop)
│   ├── output_schema.py      # Pydantic output schemas, confidence formulas & escalation gating
│   └── transcript_logger.py  # Per-run JSON transcript logger → run_logs/
│
├── tools/
│   ├── signal_source.py      # Abstract SignalDataSource + FaersLegacySource
│   ├── chembl_tool.py        # ChEMBL static lookup + plausibility derivation + critic audit
│   ├── pubmed_tool.py        # NCBI E-utilities + LLM evidence grading
│   ├── confounding.py        # ConfoundingTool + ConfoundingAssessment schema
│   ├── disease_context.py    # DiseaseContextTool (WHO ATC Level 1-4 ontology resolution)
│   ├── indication_concordance.py # IndicationConcordanceTool (7 clinical rules IND-CONF-01..07)
│   └── cache.py              # Persistent disk-backed ToolCache (diskcache, SHA-256 keying)
│
├── utils/
│   ├── canonicalize.py       # Entity normalization & synonym resolution
│   ├── config_loader.py      # Parses configs/config.yaml → AppConfig
│   ├── prompt_loader.py      # Loads versioned prompt files from pharmaguard/prompts/
│   └── text.py               # normalize_term(): snake_case → natural language
│
├── data/
│   ├── chembl_lookup.json    # Pre-resolved ChEMBL IDs + MoA text (50 drugs, CC BY-SA 3.0)
│   ├── atc_lookup.json       # WHO ATC classification registry (Levels 1–4, CC BY-SA 3.0)
│   ├── plausibility_ratings.json # Human-curated plausibility labels (lookup default)
│   ├── ground_truth.json     # 15-pair core evaluation set with categories & citations
│   ├── ground_truth_omop_pilot.json # 32-pair OMOP pilot reference set (Apache 2.0)
│   ├── ground_truth_omop_validation_holdout.json # 40-pair held-out validation set (Apache 2.0)
│   ├── archive/
│   │   └── pilot_set.json    # 3-pair quick-check set (superseded by ground_truth.json)
│   └── external/
│       ├── omopReferenceSet.rda # OHDSI MethodEvaluation reference dataset (Apache 2.0)
│       └── README.md         # Reference provenance notes
│
└── prompts/
    ├── baseline_single_shot.txt    # Single-shot prompt for baseline.py
    ├── confounding_assessment.txt  # Polypharmacy confounding evaluator prompt
    ├── evidence_grading_rubric.txt # Grade A/B/C rubric for PubMed LLM grading
    ├── leakage_critic.txt          # Adversarial maker-checker critic prompt
    ├── plausibility_rubric.txt     # Plausibility level grading guidelines
    ├── prompts_version.txt         # Active prompt version string (currently v1.1)
    ├── react_system.txt            # ReAct agent system prompt
    ├── react_tool_call_format.txt  # Tool-call format instructions for ReAct
    └── synthesis_prompt.txt        # Synthesis step prompt

configs/
└── config.yaml               # Central pipeline settings (modes, weights, thresholds, APIs, caches)

scripts/
├── dashboard.py              # 6-view Streamlit evaluation dashboard entrypoint
├── evaluator.py              # Score TriageReport JSONs against ground_truth.json
├── baseline.py               # Single-shot Gemini baseline (zero tool use)
├── run_eval.py               # Run 15 ground truth pairs → outputs/core/
├── dashboard_modules/        # Modular dashboard package (components, styles, views)
│   └── views/                # Individual dashboard view tabs (baseline, omop_pilot, probes, etc.)
├── dev/                      # Developer and diagnostic utilities
│   ├── backfill_agreement.py # Cross-source agreement backfill audit
│   ├── build_project_update_docx.py # Project update Word document generator
│   ├── capture_screenshots.py# 1080p automated screenshot utility
│   ├── check_ablation.py     # Diagnostic script for ablation agreement
│   ├── check_albuterol.py    # Diagnostic probe for albuterol
│   ├── fetch_chembl.py       # Utility to query ChEMBL API for chembl_lookup.json
│   ├── run_pilot.py          # Interactive pilot demonstration utility
│   ├── verify_react_agreement.py # Read-only audit for ReAct vs deterministic gating
│   └── verify_reports.py     # Output schema & UTF-8 integrity diagnostic
└── research/                 # Formal research experiments and publication artifacts
    ├── temporal_faers/       # Temporal FAERS partition ingestion and snapshot engine
    ├── temporal_pubmed/      # Temporal PubMed evidence retrieval and filtering
    ├── build_reproducibility_manifest.py # Automated provenance manifest builder
    ├── error_taxonomy.py     # Programmatic error & edge-case taxonomy generator
    ├── export_paper_figures.py # Publication-ready figure generator
    ├── run_confounding_evaluation.py # Metformin confounding discounting evaluation
    ├── run_confounding_probe.py # Confounding self-probe harness
    ├── run_critic_probe.py   # Adversarial mechanistic leakage critic probe
    ├── run_omop_pilot_eval.py# 32-pair OMOP secondary pilot evaluation runner
    ├── run_probe.py          # Memorization-vs-reasoning probe on obscure pairs
    ├── source_ablation.py    # Multi-source ablation & threshold sensitivity
    ├── stability_analysis.py # 15-fold Leave-One-Out (LOO) stability analysis
    └── stability_repeated_runs.py # Repeated-run sub-score variance experiment

tests/                        # pytest unit tests (229 tests across 16 active test modules / 18 test files, all passing)

docs/
├── context/
│   ├── UNDERSTAND.md         # Comprehensive project guide and results walk-through
│   ├── DECISIONS.md          # Complete 38-section chronological record of design decisions
│   ├── PROGRESS.md           # Continuous sprint log, verified metrics & reproduction steps
│   ├── ARCHITECTURE.md       # Technical architecture & schema reference
│   ├── CANONICALIZATION.md   # Event & drug term canonicalization protocols
│   ├── CONTRIBUTION.md       # Grounded project contribution claims (9 verified findings)
│   ├── CONVENTIONS.md        # Coding standards & git workflow
│   ├── GROUND_TRUTH_CANDIDATES.md # Ground truth sourcing & regulatory citations
│   ├── NOTES.md              # Design constraints & escalation thresholds
│   └── PROJECT_OVERVIEW.md   # High-level project summary and scope boundaries
├── meetings/                 # Weekly stakeholder progress updates and briefing memos
│   ├── Weekly/
│   │   ├── 1_PharmaGuard — Weekly Progress Update.md
│   │   └── PharmaGuard - Weekly Progress Update.pdf
│   ├── PharmaGuard_Project_Update_Group07.docx
│   ├── Project_Brief.md
│   └── PROJECT_UPDATE_MEETING_BRIEF.md
├── presentation/             # Capstone defense slides and presentation notes
│   ├── PharmaGuard_Midsem_Defense.pptx
│   └── SLIDE_DECK_NOTES.md
└── proposals/                # Formal capstone proposals & institutional briefs
    ├── 7th_Semester_Project_Proposals.pdf
    ├── Context_Prompt.md
    ├── pharmaguard_build_brief.md
    ├── PharmaGuard_Capstone_Proposal.pdf
    ├── PharmaGuard_Proposal_2026-08-18.md
    └── archive/pre-pivot-oncoswarm/ # Archived pre-pivot tumor-board proposal files

outputs/
├── core/                     # Frozen production TriageReport JSONs (15 pairs) + summary
│   ├── eval-run-*_report.json
│   ├── evaluation_summary.json
│   └── evaluation_summary.txt
├── experiments/              # Isolated experimental condition outputs
│   ├── ablation/             # Force-agent derivation ablation reports
│   ├── baseline/             # Single-shot LLM baseline reports & summary
│   ├── ci_gate_core/         # CI-based gate dual-benchmark validation reports (Core 15 pairs, §32)
│   ├── confounding_probe/    # Confounding self-probe & Metformin discount reports
│   ├── critic_probe/         # Adversarial leakage critic audit results
│   ├── holdout_baseline/     # 40-pair held-out OMOP baseline evaluation reports
│   ├── holdout_discounted/   # 40-pair held-out OMOP reports with delta=0.85 discount
│   ├── indication_concordance_core/ # §35 production wiring dual-benchmark validation reports (Core 15 pairs)
│   ├── probe/                # Obscure-pair epistemic memorization probe reports
│   └── react_agent/          # ReAct LangGraph agent reports & agreement_report.json
└── research/                 # Formal research artifacts and secondary benchmarks
    ├── ci_gate_omop/         # CI-based gate dual-benchmark validation reports (OMOP 32 pairs, §32)
    ├── error_taxonomy/       # Programmatic error & edge-case taxonomy results
    ├── indication_concordance_omop/ # §35 production wiring dual-benchmark validation reports (OMOP 32 pairs)
    ├── omop_pilot/           # 32-pair OMOP pilot benchmark outputs
    ├── paper_figures/        # High-resolution publication figures & vector assets
    ├── source_ablation/      # Multi-source ablation & sensitivity matrices
    ├── stability/            # 15-fold LOO analysis & repeated-run variance datasets
    ├── reproducibility_manifest.json # Consolidated provenance index (.json)
    └── reproducibility_manifest.md   # Consolidated provenance report (.md)

assets/
├── Logos/                    # Vector and raster brand identity assets
└── Screenshots/              # 1080p dashboard captures across Light and Dark themes

run_logs/                     # Per-run JSON execution traces (TranscriptLogger)
```

---

## Dual Agent Modes

Both modes are **production-verified**: each has been run against benchmark datasets and produces valid `TriageReport` JSONs adhering to the shared schema.

Mode is selected via `config.yaml → agent.mode` (`"fixed_pipeline"` | `"react"`). The entry point `scripts/run_eval.py` respects this setting at runtime.

### Fixed Pipeline (`pharmaguard/agent/fixed_pipeline.py`) — current default
- **Class**: `FixedPipelineAgent`
- **Execution order**: Deterministic sequence — FAERS → ChEMBL → PubMed → Disease Context & Concordance → Synthesize
- Injects `chembl_llm_fn` into `ChemblTool` for agent-derived plausibility on lookup misses
- Injects `pubmed_llm_fn` into `PubMedTool` for LLM evidence grading against versioned rubrics
- Structured LLM outputs via `GradeOutput` and `PlausibilityLLMOutput` Pydantic models (prevents adversarial label contamination from narrative explanation text)
- **Performance**: Strict P=1.000, R=0.857, Sp=1.000, F1=0.923; Lenient P=0.875, R=1.000, Sp=0.875, F1=0.933 (`PROGRESS.md`, `DECISIONS.md §16`)

### ReAct Agent (`pharmaguard/agent/react_agent.py`) — `mode: react`
- **Class**: `PharmaGuardAgent`
- **Execution order**: LLM-driven via LangGraph ReAct loop; tool invocations decided dynamically based on conversation state
- Uses `langchain_core.tools` decorated wrappers; shares identical underlying `FaersLegacySource`, `ChemblTool`, and `PubMedTool` instances
- Computes final reported escalation strictly via the shared deterministic formula
- **Empirical Divergence**: The agent's unconstrained freeform synthesis diverged from deterministic escalation on 4 of 15 pairs (26.7%), demonstrating why postmarketing safety triage requires strict deterministic evidence gating (`DECISIONS.md §24`)

---

## Data Flow (Fixed Pipeline)

```
Input: (drug: str, event: str)
         │
         ├──► 1. FaersLegacySource.get_signal_stats(drug, event)
         │      - normalize_term(event): snake_case → spaces before any API call
         │      - OpenFDA /drug/event.json: co-occurrence counts + PRR + ROR + Woolf 95% lower CIs
         │      - compute_prr_score() → (prr_score: float, signal_strength: SignalStrength, ci_downgraded: bool)
         │      - Optional ConfoundingTool.assess() (if confounding.enabled: true):
         │        → computes polypharmacy discount_factor (0.0 to 1.0)
         │      - All paths route through _finalize() → guaranteed cache write
         │
         ├──► 2. ChemblTool.get_plausibility(drug, event)
         │      - Static lookup in chembl_lookup.json (ChEMBL ID + MoA text)
         │      - plausibility_ratings.json lookup (human-curated, production default)
         │      - On cache miss or force_agent mode: LLM call → PlausibilityLevel + explanation text
         │      - Optional LeakageCritique maker-checker audit (if plausibility.leakage_critic.enabled: true)
         │      - Returns PlausibilityResult with level, score, source, rationale, leak flags
         │
         ├──► 3. PubMedTool.fetch_and_grade(drug, event)
         │      - normalize_term(event) before query construction
         │      - NCBI E-utilities: fetches up to max_pubmed_abstracts abstracts
         │      - LLM grades evidence via evidence_grading_rubric.txt → GradeOutput(grade, explanation)
         │      - Returns: evidence_grade, grade_score, supporting_pmids, evidence_summary
         │
         ├──► 4. DiseaseContextTool & IndicationConcordanceTool (Clinical Context Layer)
         │      - DiseaseContextTool.get_context(drug): queries ChEMBL API & atc_lookup.json for WHO ATC codes (Levels 1–4) & approved indications
         │      - IndicationConcordanceTool.evaluate(drug, event, disease_context): evaluates candidate event against indications across 7 heuristic rules (IND-CONF-01 to IND-CONF-07)
         │      - Produces IndicationConcordance object with is_concordant, rule_code, matched_indication, discount_factor (default 1.0 in production)
         │      - STRICT PRODUCTION INVARIANT: Operates as an informational diagnostic flag; scoring-inert by design (does NOT alter confidence or escalate/monitor decisions)
         │
         ▼
  5. Confidence + Escalation (output_schema.py — fully deterministic)
     - adjusted_prr_score = round(prr_score * confounding_discount * concordance_discount, 4)
     - confidence = 0.40 × adjusted_prr_score + 0.40 × grade_score + 0.20 × plausibility_score
     - derive_escalation(confidence, signal_strength) — evaluated top-to-bottom
         │
         ▼
  6. TriageReport (Pydantic) → written to outputs/core/eval-run-*_report.json
     - Computes source_agreement property (CONCORDANT vs. DISCORDANT)
     - Serializes complete evidence sub-objects, confounding assessments, and indication concordance metadata
```

---

## Confidence Formula and Escalation Gate

$$\text{Confidence} = 0.40 \cdot S_{\text{FAERS}} + 0.40 \cdot S_{\text{PubMed}} + 0.20 \cdot S_{\text{Plausibility}}$$

Where:
- $S_{\text{FAERS}} = \text{adjusted\_prr\_score} = \text{round}(\text{prr\_score} \times \text{confounding\_discount\_factor} \times \text{concordance\_discount\_factor}, 4)$
- In production triage, $\text{concordance\_discount\_factor} = 1.0$ (strictly scoring-inert, `DECISIONS.md §35`).

Sub-score ranges:
- `prr_score`: 0.0 (NO_SIGNAL) / 0.33 (WEAK) / 0.66 (MODERATE) / 1.0 (STRONG)
- `grade_score`: A=1.0, B=0.5, C=0.0
- `plausibility_score`: HIGH=1.0, MODERATE=0.5, LOW=0.0, UNKNOWN=0.0

**Maximum achievable confidence with NO_SIGNAL FAERS data = 0.60**
(grade-A * 0.40 + HIGH plausibility * 0.20 = 0.60)

### Escalation rules (`derive_escalation` — evaluated top to bottom, first match wins)

| Priority | Condition | Decision | Rationale |
|---|---|---|---|
| 1 | `signal_strength == NO_SIGNAL` | **DO_NOT_ESCALATE** | Hard Safety Gate: fires unconditionally before confidence check; confidence is *ignored*. Zero postmarketing reports cannot trigger escalation based on theoretical literature alone (`DECISIONS.md §5`). |
| 2 | `confidence >= 0.70` AND `signal_strength in {STRONG, MODERATE}` | **ESCALATE** | Statistically significant postmarketing disproportionality corroborated by high biological plausibility or Grade A literature. |
| 3 | `confidence >= 0.35` | **MONITOR** | Genuine epidemiological signal with unconfirmed mechanism, or confounded signal requiring clinical surveillance. |
| 4 | Otherwise | **DO_NOT_ESCALATE** | Sub-threshold association with insufficient epidemiological and mechanistic corroboration. |

---

## Pydantic Schemas & Core Data Models

PharmaGuard uses Pydantic v2 data models to enforce strictly typed schemas across tool outputs, orchestrator results, and serialization artifacts.

### 1. `TriageReport` (`pharmaguard/agent/output_schema.py`)
The primary document schema serialized to `outputs/core/eval-run-*_report.json`:

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
| `indication_concordance` | `Optional[IndicationConcordance]` | Informational confounding-by-indication assessment (`DECISIONS.md §35`) |
| `source_agreement` | `Literal["CONCORDANT", "DISCORDANT"]` | **Computed property** (`@computed_field`) evaluating cross-source evidence concordance |

#### Cross-Source Agreement (`source_agreement`):
Evaluates agreement across the three normalized sub-scores ($S_{\text{FAERS}} = \text{prr\_score}$, $S_{\text{Lit}} = \text{grade\_score}$, $S_{\text{Mech}} = \text{plausibility\_score}$) via `compute_source_agreement()`:
$$\text{DISCORDANT} \iff \max(S_{\text{FAERS}}, S_{\text{Lit}}, S_{\text{Mech}}) \ge 0.66 \land \min(S_{\text{FAERS}}, S_{\text{Lit}}, S_{\text{Mech}}) \le 0.33$$
Otherwise classified as `"CONCORDANT"`. Isolates benchmark edge cases (`montelukast`, `metformin`, `atorvastatin::dementia`) exhibiting cross-modality divergence (`DECISIONS.md §26`).

### 2. `SignalStatsOutput` (`pharmaguard/agent/output_schema.py`)
Encapsulates openFDA FAERS disproportionality metrics and confounding adjustments:

| Field | Type | Description |
|---|---|---|
| `prr` | `Optional[float]` | Proportional Reporting Ratio ($A/(A+B) / C/(C+D)$) |
| `ror` | `Optional[float]` | Reporting Odds Ratio ($(A/B) / (C/D)$) |
| `prr_lower_ci` | `Optional[float]` | Woolf 95% lower confidence interval bound for PRR |
| `ror_lower_ci` | `Optional[float]` | Woolf 95% lower confidence interval bound for ROR |
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
Pydantic model produced by the blinded maker-checker critic agent (`pharmaguard/tools/chembl_tool.py`, MARCH pattern) to audit rationales for non-mechanistic knowledge leakage (`DECISIONS.md §27`):

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

### 5. `DiseaseContext` (`pharmaguard/tools/disease_context.py`)
Encapsulates WHO ATC ontological mapping and drug utilization context resolved via the ChEMBL API and local registry (`atc_lookup.json`):

| Field | Type | Description |
|---|---|---|
| `drug` | `str` | Active pharmaceutical ingredient name |
| `all_atc_codes` | `list[str]` | Complete list of all resolved WHO ATC codes for the molecule |
| `selected_atc` / `primary_atc` | `Optional[str]` | Primary representative ATC code (e.g., `"C10AA05"` for atorvastatin) |
| `secondary_atc_codes` | `list[str]` | Alternative ATC codes preserving alternate formulations or routes |
| `therapeutic_area_code` | `Optional[str]` | ATC Level 1 single-letter anatomical code (e.g., `"C"` for Cardiovascular) |
| `therapeutic_area` | `Optional[str]` | ATC Level 1 title (e.g., `"Cardiovascular system"`) |
| `pharmacological_subgroup_code` | `Optional[str]` | ATC Level 2 therapeutic subgroup code (e.g., `"C10"`) |
| `pharmacological_subgroup` | `Optional[str]` | ATC Level 2 title (e.g., `"Lipid modifying agents"`) |
| `utilization_class` | `Literal["CHRONIC", "ACUTE", "MIXED", "UNKNOWN"]` | Typical drug administration duration classification |
| `utilization_rationale` | `str` | Pharmacological rationale justifying the utilization duration tier |
| `selection_method` | `str` | Methodology utilized to choose the representative ATC code |
| `selection_rationale` | `str` | Clinical rationale for representative code selection |
| `atc_source` | `Literal["chembl_api", "hardcoded_fallback", "unresolved"]` | Provenance source for the classification data |
| `is_resolved` | `bool` | True if ATC classification was successfully mapped |

### 6. `IndicationConcordance` (`pharmaguard/agent/output_schema.py`, `pharmaguard/tools/indication_concordance.py`)
Encapsulates clinical confounding-by-indication evaluation governed by the 7 pre-registered heuristic rules (`IND-CONF-01` to `IND-CONF-07` in `DECISIONS.md §35`):

| Field | Type | Description |
|---|---|---|
| `concordant` | `bool` | True if candidate adverse event category overlaps with drug therapeutic indication class |
| `overlap_category` | `Optional[str]` | Standardized clinical overlap domain (e.g., `"Cardiovascular & Cerebrovascular Ischemia"`) |
| `rationale` | `str` | Pharmacoepidemiological rationale explaining channeling bias or indication confounding |
| `rule_source` | `str` | Peer-reviewed epidemiological literature citation justifying the rule |

#### The Canonical 7-Rule Clinical Heuristics Cascade:
1. **`IND-CONF-01` (Cardiovascular & Cerebrovascular Ischemia):** ATC `C` / `B01` paired with ischemic endpoints (*myocardial_infarction*, *stroke*, *cardiac_arrest*). Cites Psaty et al. (1999), Salas et al. (1999).
2. **`IND-CONF-02` (Neuropsychiatric & Neurodegenerative Events):** ATC `N` paired with affective or cognitive endpoints (*suicidal_ideation*, *depression*, *dementia*, *seizure*). Cites Schneeweiss & Avorn (2005), Gibbons et al. (2007).
3. **`IND-CONF-03` (Upper Gastrointestinal Ulceration & Hemorrhage):** ATC `A02` / `M01` paired with ulceration or GI bleeding (*gastrointestinal_haemorrhage*, *peptic_ulcer*). Cites García Rodríguez & Jick (1994), Petri & Urquhart (1991).
4. **`IND-CONF-04` (Glycemic Dysregulation & Metabolic Crises):** ATC `A10` paired with glycemic endpoints (*hypoglycaemia*, *diabetic_ketoacidosis*). Cites Cryer (2002), Bate & Evans (2009).
5. **`IND-CONF-05` (Hematologic Cytopenias & Neoplastic Complications):** ATC `L` paired with cytopenias and thromboembolism (*neutropenia*, *thrombocytopenia*, *pulmonary_embolism*). Cites Lyman et al. (2006), Groenwold et al. (2011).
6. **`IND-CONF-06` (Renal Dysfunction & Hemodynamic Azotemia):** ATC `C03` / `C09` paired with acute kidney injury (*acute_kidney_injury*, *hyperkalaemia*). Cites Schoolwerth et al. (2001), Lapi et al. (2013).
7. **`IND-CONF-07` (Airway Hyperresponsiveness & Bronchospastic Crises):** ATC `R03` paired with obstructive exacerbations (*bronchospasm*, *respiratory_failure*). Cites Suissa (2003), Ernst et al. (1993).

---

## Multi-Benchmark Evaluation & Baseline Performance

PharmaGuard is evaluated across two formal benchmark suites: the **Core 15-Pair Ground Truth Benchmark** (7 Confirmed Positives, 5 Genuine Negative Controls, 3 Zero-Report Controls) and the external **OMOP Pilot Benchmark** (32 pairs from the OHDSI MethodEvaluation reference set across 4 acute clinical outcomes: Acute Myocardial Infarction, Acute Pancreatitis, Upper GI Bleeding, and Acute Liver Injury).

### Multi-Benchmark Performance Table

| Evaluation Suite & Model | Strict Precision | Strict Recall | Strict Specificity | Strict F1 | Lenient Precision | Lenient Recall | Lenient Specificity | Lenient F1 | Over-Caution Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PharmaGuard (Core 15-Pair)** | **1.000** [0.610 – 1.000] | **0.857** (6/7) [0.487 – 0.974] | **1.000** [0.676 – 1.000] | **0.923** [0.727 – 1.000] | **0.875** [0.529 – 0.978] | **1.000** (7/7) [0.646 – 1.000] | **0.875** [0.529 – 0.978] | **0.933** [0.769 – 1.000] | **12.5%** (1 of 8) |
| **Single-Shot Baseline (Core 15-Pair)** | 0.875 [0.529 – 0.978] | 1.000 (7/7) [0.646 – 1.000] | 0.875 [0.529 – 0.978] | 0.933 [0.769 – 1.000] | 0.700 [0.397 – 0.892] | 1.000 (7/7) [0.646 – 1.000] | 0.625 [0.306 – 0.863] | 0.824 [0.615 – 0.941] | 25.0% (2 of 8) |
| **PharmaGuard (OMOP Pilot 32-Pair)** | **1.000** (1/1) [0.207 – 1.000] | **0.063** (1/16) [0.011 – 0.270] | **1.000** (16/16) [0.806 – 1.000] | **0.118** [0.024 – 0.426] | **0.846** (11/13) [0.578 – 0.957] | **0.688** (11/16) [0.444 – 0.858] | **0.813** (13/16) [0.570 – 0.934] | **0.720** [0.540 – 0.850] | **18.8%** (3 of 16) |

*Confidence Intervals:* Both Wilson binomial score intervals and non-parametric Bootstrap ($B=1000, \text{seed}=42$) intervals are calculated. On the OMOP Pilot, PharmaGuard achieved **100% Strict Specificity (16/16 negative controls suppressed)** and **68.8% Lenient Recall (11/16 positive controls safely monitored)**.

### Exploratory 40-Pair Held-Out OMOP Validation Batch
To investigate whether indication-concordance discounting ($\delta = 0.85$) could safely attenuate confounded disproportionality signals on previously unseen pairs, an exploratory 40-pair held-out batch (20 positive, 20 negative controls) was curated from `omopReferenceSet.rda`. In this test, concordance criteria triggered on only 4 of the 40 pairs (10.0%)—insufficient sample power to generalize conclusions across broad clinical phenotypes. While the discount mathematically lowered PRR sub-scores without breaching any hard safety gates, it caused zero decision boundary crossings ($\Delta = 0$, Strict F1=0.1818, Lenient F1=0.5000). The experiment is documented as an exploratory negative result in [`docs/context/DECISIONS.md §38`](DECISIONS.md#38-independent-verification-and-factual-correction-of-the-40-pair-held-out-omop-validation-batch).

---

## Caching and Rate-Limit Strategy

All external network operations (openFDA, ChEMBL API, PubMed NCBI E-utilities, Gemini LLM calls) are fronted by `ToolCache` (`pharmaguard/tools/cache.py`, backed by `diskcache`).

Deterministic SHA-256 key naming conventions:
```
FAERS:                  faers::{drug_lower}::{event_lower}::{CACHE_SCHEMA_VERSION}
PubMed fetch:           pubmed::{sha256(query)[:16]}
PubMed grade:           pubmed_grade::{sha256(query)[:16]}::{prompts_version}::{CACHE_SCHEMA_VERSION}
Plausibility:           plausibility::{drug_lower}::{event_lower}::{prompts_version}::{CACHE_SCHEMA_VERSION}
Baseline:               baseline::{drug_lower}::{event_lower}::{prompts_version}::{CACHE_SCHEMA_VERSION}
Disease context / ATC:  atc::{drug_lower}::{CACHE_SCHEMA_VERSION}
Indication Concordance: concordance::{drug_lower}::{event_lower}::{CACHE_SCHEMA_VERSION}
```

`CACHE_SCHEMA_VERSION` is currently **`v7`** (defined in `pharmaguard/tools/cache.py`).

---

## Test Suite Status

PharmaGuard maintains rigorous test coverage via pytest. The test suite comprises **229 tests across 16 active test modules (18 test files)** in `tests/`, all passing:

| Test File | Focus Area | Tests |
|---|---|:---:|
| `test_agent_parsers.py` | Agent tool call parsing & validation | 2 |
| `test_cache.py` | DiskCache persistent storage, schema keys & invalidation | 7 |
| `test_canonicalize.py` | Drug & reaction name normalization and canonicalization | 51 |
| `test_chembl_tool.py` | ChEMBL lookup, target parsing & plausibility derivation | 5 |
| `test_confounding.py` | ConfoundingTool, discount factors & polypharmacy parsing | 7 |
| `test_disease_context.py` | DiseaseContextTool, WHO ATC codes & therapeutic stratification | 52 |
| `test_error_taxonomy.py` | Programmatic triage error taxonomy & failure categorization | 10 |
| `test_indication_concordance_inertness.py` | 7-rule IND-CONF cascade & scoring-inert production invariants | 7 |
| `test_indication_discount.py` | Indication-concordance discount factor math & gating logic | 7 |
| `test_output_schema.py` | Pydantic model validation, PRR score, Woolf CI & safety gates | 38 |
| `test_pubmed_tool.py` | NCBI E-utilities retrieval & LLM Grade A/B/C rubric parser | 3 |
| `test_reproducibility_manifest.py` | Automated reproducibility manifest & provenance hashes | 5 |
| `test_signal_source.py` | Signal data source abstraction, mock fixtures & legacy FAERS | 9 |
| `test_source_ablation.py` | Tri-source evidence ablation & threshold sensitivity sweeps | 4 |
| `test_stability_repeated_runs.py` | Repeated-run variance, Wilson intervals & rank correlation | 7 |
| `test_stratified_evaluation.py` | Stratified metrics computation, benchmark isolation & Wilson CIs | 15 |
| **Total** | **Full Pytest Unit & Regression Suite** | **229 Passed** |

---

## Tech Stack (verified from `requirements.txt`)

| Package | Role |
|---|---|
| `langchain>=0.2.0` | LLM orchestration and prompt template management |
| `langgraph>=0.1.0` | ReAct state graph execution |
| `langchain-google-genai>=1.0.0` | Gemini API client |
| `pydantic>=2.0.0` | Schema validation + structured LLM output enforcement |
| `diskcache>=5.6.0` | Persistent disk-backed cache with atomic writes |
| `requests>=2.31.0` | HTTP client (openFDA REST, ChEMBL API, NCBI E-utilities) |
| `pytest>=8.0.0` | Unit and integration test runner |
| `pandas>=2.0.0`, `matplotlib>=3.8.0` | Evaluation analysis & figure generation |
| `streamlit>=1.35.0` | Multi-view clinical evaluation dashboard |
| `plotly>=5.22.0` | High-density interactive confidence waterfall charts |

Active foundation model: **`gemini-3.1-flash-lite`** (configured in `configs/config.yaml`).
See `docs/context/DECISIONS.md §10` for rationale.