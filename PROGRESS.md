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
- scripts/evaluator.py: Computes strict/lenient precision, recall, specificity, F1 per-category. Accepts --outputs-dir and --title flags for baseline comparison.
- scripts/baseline.py: Single-shot Gemini baseline (no tools). Same output schema as main pipeline.

#### Bug Fixes (Sprint 3)
Four real bugs found and fixed:
1. FAERS zero-count bug -- drug_canonical/event_meddra_pt passed as snake_case to FAERS queries. Fixed via normalize_term().
2. Plausibility fallback not firing -- llm_inference_fn not passed through to ChemblTool in live pipeline. Fixed.
3. ChEMBL mechs[0] selection -- only first mechanism used; wrong for promiscuous drugs. Fixed by concatenating all mechanisms.
4. MoA anti-circularity -- valproic_acid MoA edited to include the adverse-event-specific mechanism. Corrected.

#### Baseline Comparison
- Single-shot LLM baseline run against all 15 pairs.
- Key finding: baseline escalated liraglutide::pancreatic_cancer (FDA/EMA-cleared) at confidence=0.85; PharmaGuard correctly gave DO_NOT_ESCALATE via FAERS NO_SIGNAL gate.
- Confidence scores not directly comparable between systems (see DECISIONS.md S12).

#### Ablation Study
- force_agent mode vs lookup_first mode on 7 comparable pairs: 3 agreements, 4 disagreements.
- Key finding: LLM overrides mechanistic reasoning with training-data recall of famous drug safety cases.

#### Plausibility Rubric
- Created pharmaguard/prompts/plausibility_rubric.txt v1.1 (2026-08-14).
- Operative standard: Bradford Hill "Biological Plausibility" -- reasonable hypothesis from MoA sufficient for MODERATE.
- Re-curated all 9 entries under v1.1. Changes: montelukast::suicidal_ideation (LOW->MODERATE), albuterol::suicidal_ideation (LOW->MODERATE).
- Cache schema bumped to v8.

---

## Sprint 3 Reproducibility Verification -- COMPLETE

**Date verified:** 2026-08-14

### Steps to Reproduce from a Clean Clone

  git clone https://github.com/Krishna200608/PharmaGuard.git
  cd PharmaGuard
  cp .env.example .env
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  python scripts/run_eval.py
  python scripts/evaluator.py --outputs-dir outputs --title "PharmaGuard Final"

Prerequisites: GOOGLE_API_KEY and NCBI_API_KEY in .env. config.yaml default: plausibility.source=lookup_first, output_dir=outputs.

### Final Metrics (rubric v1.1, cache schema v8, fresh cache, 15 pairs)

  Strict:  TP=7  FP=0  TN=8  FN=0  P=1.000  R=1.000  Specificity=1.000  F1=1.000
  Lenient: TP=7  FP=0  TN=8  FN=0  P=1.000  R=1.000  Specificity=1.000  F1=1.000
  Over-Caution Rate: 0.0%  |  Disagreements: None

### Reproducibility History

  Run                            | Rubric            | Strict Recall | Notes
  Sprint 3 post-fix              | v1.0 (3 entries)  | 1.000         | 14/15 agent-derived; modes equivalent
  After 6-pair blind curation    | v1.0              | 0.857 (6/7)   | montelukast=MONITOR; rubric inconsistency diagnosed
  After rubric v1.1 (FINAL)      | v1.1 Bradford Hill| 1.000 (7/7)   | montelukast=MODERATE; all 15 correct

Sprint 3 is closed on the final row.

---

## Planned: Sprint 4

- Expand ground truth set beyond 15 pairs
- Human-expert validation outreach for plausibility ratings
- Calibrate escalation thresholds (see DECISIONS.md S5 -- currently uncalibrated priors)
- Bootstrap confidence interval reporting for evaluation metrics
