# PharmaGuard -- Progress and Sprint Log

**Project:** PharmaGuard -- Pharmacovigilance Signal Triage Orchestrator
**Owner:** Krishna Sikheriya (IIT2023139) | IIIT Allahabad | B.Tech IT | 7th Semester Capstone (2026-27)
**Supervisor:** Dr. Nikhilanand Arya

---

## Sprint 3 -- COMPLETED (2026-08-14)

### Objective
Build, evaluate, and verify the full PharmaGuard triage pipeline against a 15-pair ground truth dataset.

### Completed Work

#### Evaluation Infrastructure
- scripts/run_eval.py: Runs the full 15-pair ground truth set against fixed_pipeline or react mode.
- scripts/evaluator.py: Computes strict/lenient precision, recall, specificity, F1 per-category. Includes Bootstrap (B=1000, seed=42) and Wilson score 95% confidence intervals. Accepts --outputs-dir and --title flags.
- scripts/baseline.py: Single-shot Gemini baseline (no tools). Same output schema as main pipeline.

#### Bug Fixes (Sprint 3)
Four real bugs found and fixed:
1. FAERS zero-count bug -- drug_canonical/event_meddra_pt passed as snake_case to FAERS. Fixed via normalize_term().
2. Plausibility fallback not firing -- llm_inference_fn not passed to ChemblTool in live pipeline. Fixed.
3. ChEMBL mechs[0] selection -- only first mechanism used; wrong for promiscuous drugs. Fixed.
4. MoA anti-circularity -- valproic_acid MoA had event-specific hepatotoxicity mechanism added. Corrected.

#### Baseline Comparison
- Single-shot LLM baseline vs. PharmaGuard on all 15 pairs.
- Baseline metrics: Strict P/R/Sp/F1 = 0.875 / 1.000 / 0.875 / 0.933 (FP=1 on liraglutide::pancreatic_cancer);
  Lenient P/R/Sp/F1 = 0.700 / 1.000 / 0.625 / 0.824 (FP=3 on liraglutide, metformin, atorvastatin/dementia).
- True 25.0% (2/8) over-caution rate on negative controls vs. PharmaGuard's 12.5% (1/8).
- Key distinction: on metformin::hypoglycaemia, both systems output the same conservative MONITOR decision
  (baseline via ungrounded clinical caution; PharmaGuard via strong FAERS polypharmacy signal modulated by
  Grade C PubMed and LOW plausibility). On liraglutide, baseline escalates on ungrounded prior while PharmaGuard
  correctly yields DO_NOT_ESCALATE via FAERS NO_SIGNAL gate.
- Confidence scores not directly comparable (see DECISIONS.md §12).

#### Ablation Study
- force_agent vs. lookup_first on 7 comparable pairs: 3 agreements, 4 disagreements across curated overlap.
- force_agent metrics (15 pairs): Strict P/R/Sp/F1 = 1.000 / 1.000 / 1.000 / 1.000; Lenient P/R/Sp/F1 = 0.875 / 1.000 / 0.875 / 0.933.
- **WARNING:** force_agent mode's 1.000 strict recall is NOT evidence this mode is better. It results specifically from montelukast's plausibility being upgraded via leaked regulatory knowledge (see DECISIONS.md §19) rather than genuine mechanistic reasoning -- the exact failure mode documented and reverted in DECISIONS.md §15. This number must never be cited as a reason to prefer force_agent over the production lookup_first configuration.
- Key finding: LLM overrides mechanistic reasoning with training-data recall of famous drug safety cases (citing boxed warnings and observational trials in 4/4 disagreements).

#### Plausibility Curation
- 6 pairs curated blindly (without looking at agent outputs) to support a valid ablation comparison.
- Total curated entries: 9 (including 3 early illustrative pairs).
- Plausibility rubric draft created (pharmaguard/prompts/plausibility_rubric.txt). NOT applied to ratings;
  see DECISIONS.md §15 for why the rubric-based re-curation was attempted and then reverted.

---

## Sprint 3 Reproducibility Verification -- COMPLETE

**Date verified:** 2026-08-14

### Steps to Reproduce from a Clean Clone

  git clone https://github.com/Krishna200608/PharmaGuard.git
  cd PharmaGuard
  cp .env.example .env          # Add GOOGLE_API_KEY and NCBI_API_KEY
  python -m venv .venv
  .venv\Scripts\Activate.ps1   # Windows; use source .venv/bin/activate on Linux
  pip install -r requirements.txt
  python scripts/run_eval.py
  python scripts/evaluator.py --outputs-dir outputs --title "PharmaGuard Final"

Prerequisites: GOOGLE_API_KEY and NCBI_API_KEY in .env.
Config.yaml defaults: plausibility.source=lookup_first, output_dir=outputs.

### Final Metrics (plausibility ratings v1.0, cache schema v7, fresh cache, 15 pairs)

| Metric | Strict (Point [95% CI Bootstrap / Wilson]) | Lenient (Point [95% CI Bootstrap / Wilson]) |
|---|---|---|
| **TP / FP / TN / FN** | 6 / 0 / 8 / 1 | 7 / 1 / 7 / 0 |
| **Precision** | 1.000 [1.000 - 1.000 / 0.610 - 1.000] | 0.875 [0.624 - 1.000 / 0.529 - 0.978] |
| **Recall** | 0.857 [0.571 - 1.000 / 0.487 - 0.974] | 1.000 [1.000 - 1.000 / 0.646 - 1.000] |
| **Specificity** | 1.000 [1.000 - 1.000 / 0.676 - 1.000] | 0.875 [0.600 - 1.000 / 0.529 - 0.978] |
| **F1-Score** | 0.923 [0.727 - 1.000 / N/A] | 0.933 [0.769 - 1.000 / N/A] |
| **Over-Caution Rate** | 12.5% (1/8) | -- |

*Note on uncertainty & boundary artifact:* Non-parametric bootstrap resampling (B=1000, seed=42) and exact Wilson score intervals are both reported. At n=15, the bootstrap interval showing 1.000-1.000 for strict precision and specificity is a known percentile-bootstrap artifact at 0/N boundary proportions (it resamples from zero-false-positive empirical outcomes, so it structurally cannot express uncertainty) -- this is NOT evidence of proven perfect precision. The exact Wilson score interval ([0.610, 1.000] for strict precision; [0.676, 1.000] for strict specificity) is the far more informative and honest measure of small-sample statistical uncertainty here.

### Documented Disagreements (Strict/Lenient Dual Validation)
1. **montelukast::suicidal_ideation** (confirmed_positive) -- Expected ESCALATE, Got MONITOR.
   - *Mechanistic confidence gating:* Curated plausibility=LOW (no confirmed CNS mechanism for peripheral CysLT1 antagonism) dampens composite confidence (0.664) below 0.70 despite MODERATE FAERS signal and Grade A PubMed evidence. Strict metrics capture the caution (FN=1); lenient metrics confirm the signal was never dropped (TP=7).
2. **metformin::hypoglycaemia** (genuine_negative_control) -- Expected DO_NOT_ESCALATE, Got MONITOR.
   - *Confounded signal handling:* FAERS contains ~9,340 spontaneous reports (PRR=10.73, STRONG) due to polypharmacy with insulin/secretagogues. The agent correctly derives plausibility=LOW (0.0) and PubMed grades the evidence as Grade C (0.0), successfully de-escalating the signal from ESCALATE down to MONITOR (confidence 0.400). Strict metrics correctly show zero false alarms (FP=0), while lenient metrics record the over-monitoring (FP=1, precision 0.875).

### Reproducibility Note
A rubric-based re-curation was attempted and then reverted (see DECISIONS.md §15). The 6/7 strict /
7/7 lenient result above is the honest, defensible Sprint 3 final result. The 15/15 result briefly
produced by commit e906fd3 was contingent on a biased rubric revision and is not the final result.

---

## Planned: Sprint 4

- Medical ontology normalization layer (MedDRA LLT-to-PT canonicalization and UK/US spelling mapping)
- Anti-leakage prompt guardrails for agent-derived plausibility (see DECISIONS.md §19)
- Independent human-expert panel for biological plausibility adjudication (see DECISIONS.md §20)
- Multi-signal pharmacovigilance integration (EudraVigilance / JADER / WHO VigiBase APIs)
- Paper writing, documentation synthesis, and report generation

---

## Post-Sprint 3 Audit (2026-08-24)

- **ReAct Freeform Recommendation vs. Deterministic Escalation:** External audit flagged that `outputs/react_agent/*.json` escalation fields match `fixed_pipeline` by construction (shared deterministic scoring formula). Added `scripts/verify_react_agreement.py` to independently extract and normalize the agent's raw freeform synthesized recommendations (`triage.agent_reasoning_trace[0]`).
- **Audit Findings:** Found 11/15 (73.3%) agreement; the 4 divergence cases (`montelukast`, `liraglutide`, `atorvastatin::dementia`, `albuterol`) highlight where unconstrained generative reasoning departs from deterministic safety gating. Documented in `DECISIONS.md §24` and reflected in `CONTRIBUTION.md`.

---

## Full Technical & Novelty Audit — Cleared for Paper Writing Prerequisite (2026-08-24)

- **Technical Completeness Audit:** External full-repo review confirmed no stubs/TODOs/incomplete code across pharmaguard/ and scripts/; independently re-derived the PRR/ROR/CI formula by hand against raw FAERS counts and matched test_faers_legacy_calculates_prr_ror exactly; confirmed react_agent.py's reported escalation is genuinely computed via the same deterministic formula as fixed_pipeline.py (consistent with §24); spot-verified a ground_truth.json FDA source citation against the live FDA site; confirmed requirements.txt fully covers actual third-party imports.
- **Novelty/Publishability Audit:** Literature search identified Harvard's ToolUniverse (arXiv:2509.23426) as a relevant prior system; DECISIONS.md §23 updated accordingly (see below) to narrow the novelty claim to PharmaGuard's dedicated benchmarking/evaluation/disclosure methodology, which remains undupplicated as of this audit.
- **Status:** Codebase and novelty positioning are verified sound. This clears the technical-verification prerequisite for paper writing. Per DECISIONS.md §25 ("Paper-Writing Gate Standing Instruction"), paper writing itself remains gated on a separate explicit go-ahead from Krishna and has NOT been started.

---

## 5-Phase Novelty Enhancement Build (2026-08-27)

- **Phase 1 — Cross-Source Evidence Agreement Metric:** Implemented deterministic concordance heuristic (`compute_source_agreement` in `pharmaguard/agent/output_schema.py`) and backfill script (`scripts/dev/backfill_agreement.py`). Metric classifies pairs as `CONCORDANT` or `DISCORDANT` ($\max \ge 0.66 \land \min \le 0.33$), isolating the exact 3/15 edge cases (`montelukast`, `metformin`, `atorvastatin::dementia`). Documented in `DECISIONS.md §26`.
- **Phase 2 — Adversarial Mechanistic Leakage Critic:** Implemented blind maker-checker critic agent (`pharmaguard/tools/chembl_tool.py's _critique_plausibility_leakage() method (LeakageCritique model in pharmaguard/agent/output_schema.py)`, MARCH framework pattern) and probe harness (`scripts/run_critic_probe.py`). Evaluated across 4 documented leak cases (`outputs/critic_probe/leakage_critique_results.json`): achieved 4/4 (100%) detection sensitivity, counterfactually downgrading montelukast plausibility from MODERATE (0.50) to LOW (0.00). Documented in `DECISIONS.md §27`.
- **Phase 3 — Confounding-Aware Signal Discounting & Self-Probe:** Implemented `ConfoundingTool` (`pharmaguard/tools/confounding.py`) and probe harness (`scripts/run_confounding_probe.py`). Evaluated 4-pair self-probe (`outputs/confounding_probe/confounding_self_probe.json`) and pipeline verification on `metformin::hypoglycaemia` (`outputs/confounding_probe/metformin_confounding_report.json`), applying a 0.20 discount factor that dropped confidence from 0.4000 to 0.0800 (`DO_NOT_ESCALATE`), eliminating the sole lenient false positive while documenting clinical guideline recall circularity. Documented in `DECISIONS.md §28`.
- **Phase 4 — Leave-One-Out (LOO) Stability Analysis:** Implemented `scripts/stability_analysis.py` evaluating 15 single-pair folds without pipeline re-execution, reusing `scripts/evaluator.py` functions. Verified mean Strict $F_1 = 0.9226 \pm 0.0225$ (range: 0.9091–1.000) and Lenient $F_1 = 0.9330 \pm 0.0192$ (range: 0.9231–1.000), identifying brittle pairs (`montelukast` swing 0.0769, `metformin` swing 0.0667). Output saved to `outputs/stability/loo_analysis.json`. Documented in `DECISIONS.md §29`.
- **Phase 5 — Publication Figure Generator:** Implemented `scripts/generate_paper_figures.py` to produce publication-ready vector and high-resolution figures for evidence waterfall decompositions, LOO stability distributions, and baseline comparisons.

---

## Evaluation Dashboard Integration & UI Refinement (2026-08-27)

- **Stability & Agreement Integration:** Added 4-card Leave-One-Out stability metric block to Overview tab and `AGREEMENT` badge column (`CONCORDANT` / `DISCORDANT`) with evidence inspector to Per-Pair Table tab.
- **Methodology Probes Tab:** Added dedicated 5th dashboard view (`scripts/dashboard_modules/views/probes.py`) rendering the Adversarial Critic probe audit table, Confounding Self-Probe rationale cards, and side-by-side Metformin before/after waterfall charts.
- **Google Material Icons & Screenshots:** Standardized all UI icons to official Google Material Icons (Material 3 SVG paths and Material Symbols Outlined font), eliminating raw unicode emojis. Added automated Playwright capture script (`scripts/dev/capture_screenshots.py`) and regenerated 10 high-resolution 1080p verification screenshots in `assets/Screenshots/Light/` and `assets/Screenshots/Dark/`.
- **Bugfix (Zero-Row Filter Rendering):** Resolved Markdown indented code-block escaping bug in `scripts/dashboard_modules/views/per_pair.py` by unindenting HTML structure and adding an explicit, styled empty state row when filters match zero pairs.

---

## OMOP Secondary Benchmark Expansion (2026-09-02)

- **OMOP Pilot Evaluation (Stage 2 Complete):** Executed full 32-pair OMOP reference set evaluation (`scripts/research/run_omop_pilot_eval.py`, outputs in `outputs/research/omop_pilot/`). Achieved 100% negative control specificity ($16/16$ true negatives) alongside Strict $F_1 = 0.118$ and Lenient $F_1 = 0.720$; identified that the static $\text{PRR} < 2.0$ magnitude gate attenuates sensitivity on high-utilization chronic medications despite statistically significant 95% CIs and high biological plausibility. Fully documented as a non-retroactively tuned external-validity finding in `DECISIONS.md §31`.
- **Alternative CI-Based Signal Detection Gate (2026-09-03):** Implemented config-gated `compute_prr_score_ci_based()` (`signal_detection.ci_based_gate.enabled: false`, Evans et al. 2001) alongside production gate; 97/97 tests pass; dual-validated: rescues 2 of 6 OMOP chronic false negatives (`dipyridamole`, `nifedipine` -> `MONITOR`, Lenient F1 0.720 -> 0.815), while introducing 1 lenient false positive on `atorvastatin::dementia` on core 15-pair set (documented in `DECISIONS.md §32`).
- **Two-Stage Term Canonicalization Layer (2026-09-03):** Implemented standalone opt-in `canonicalize_term()` in `pharmaguard/utils/canonicalize.py` per `CANONICALIZATION.md`; 51 unit tests in `tests/test_canonicalize.py` (148/148 suite passing); verified 100% exact match across all 47 ground truth pairs (documented in `DECISIONS.md §33`).
- **CI-Based Gate Production Decision (2026-09-03):** Finalized decision to retain static PRR<2.0 gate as production default (`ci_based_gate.enabled: false`); CI-based gate established as validated opt-in alternative, rejected for production adoption due to benchmark asymmetry (Core F1 0.933->0.875 vs OMOP 0.720->0.815), small sample sizes, and §15 anti-overfitting discipline (documented in `DECISIONS.md §32.7`).
- **ATC Therapeutic-Context Stratification (§34 Proposal C, 2026-09-04):** Implemented read-only `DiseaseContextTool` (WHO ATC via ChEMBL API + fallbacks) and stratified evaluation breakdown in `scripts/evaluator.py`; preserved 100% aggregate metric invariance across Core and OMOP benchmarks while exposing differential performance by therapeutic area.




