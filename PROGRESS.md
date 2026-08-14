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
- Key example: baseline escalated liraglutide::pancreatic_cancer (FDA/EMA-cleared) at confidence 0.85;
  PharmaGuard correctly gave DO_NOT_ESCALATE via FAERS NO_SIGNAL gate.
- Confidence scores not directly comparable (see DECISIONS.md S12).

#### Ablation Study
- force_agent vs. lookup_first on 7 comparable pairs: 3 agreements, 4 disagreements.
- Key finding: LLM overrides mechanistic reasoning with training-data recall of famous drug safety cases.

#### Plausibility Curation
- 6 pairs curated blindly (without looking at agent outputs) to support a valid ablation comparison.
- Total curated entries: 9 (including 3 early illustrative pairs).
- Plausibility rubric draft created (pharmaguard/prompts/plausibility_rubric.txt). NOT applied to ratings;
  see DECISIONS.md S15 for why the rubric-based re-curation was attempted and then reverted.

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
| **TP / FP / TN / FN** | 6 / 0 / 8 / 1 | 7 / 0 / 8 / 0 |
| **Precision** | 1.000 [1.000 - 1.000 / 0.610 - 1.000] | 1.000 [1.000 - 1.000 / 0.646 - 1.000] |
| **Recall** | 0.857 [0.571 - 1.000 / 0.487 - 0.974] | 1.000 [1.000 - 1.000 / 0.646 - 1.000] |
| **Specificity** | 1.000 [1.000 - 1.000 / 0.676 - 1.000] | 1.000 [1.000 - 1.000 / 0.676 - 1.000] |
| **F1-Score** | 0.923 [0.727 - 1.000 / N/A] | 1.000 [1.000 - 1.000 / N/A] |
| **Over-Caution Rate** | 0.0% (0/8) | -- |

*Note on uncertainty & boundary artifact:* Non-parametric bootstrap resampling (B=1000, seed=42) and exact Wilson score intervals are both reported. At n=15, the bootstrap interval showing 1.000-1.000 for precision and specificity is a known percentile-bootstrap artifact at 0/N boundary proportions (it resamples from zero-false-positive empirical outcomes, so it structurally cannot express uncertainty) -- this is NOT evidence of proven perfect precision. The exact Wilson score interval ([0.610, 1.000] for strict precision; [0.676, 1.000] for specificity) is the far more informative and honest measure of small-sample statistical uncertainty here.

### Single Disagreement
  montelukast::suicidal_ideation -- Expected ESCALATE, Got MONITOR.
  Root cause: curated plausibility=LOW (no confirmed CNS mechanism for CysLT1 antagonism) dampens
  composite confidence below the ESCALATE threshold despite MODERATE FAERS signal and Grade A PubMed
  evidence. This is mechanistically correct behaviour -- the signal was not missed (MONITOR !=
  DO_NOT_ESCALATE). See DECISIONS.md S14 for the dual-metric design property this validates.

### Reproducibility Note
A rubric-based re-curation was attempted and then reverted (see DECISIONS.md S15). The 6/7 strict /
7/7 lenient result above is the honest, defensible Sprint 3 final result. The 15/15 result briefly
produced by commit e906fd3 was contingent on a biased rubric revision and is not the final result.

---

## Planned: Sprint 4

- Expand ground truth set beyond 15 pairs
- Human-expert validation outreach for plausibility ratings
- Rubric formalisation (Bradford Hill) -- see DECISIONS.md S15 for the correct process
- Calibrate escalation thresholds (see DECISIONS.md S5 -- currently uncalibrated priors)
- Multi-dataset generalization testing (e.g., EudraVigilance or JADER comparisons)

