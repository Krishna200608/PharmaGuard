## PharmaGuard Research Repository — Continuation Context

### Repository

- **Location:** `d:\Research Project\PharmaGuard`
- **GitHub:** `https://github.com/Krishna200608/PharmaGuard.git` (branch: `main`)
- **Stack:** Python 3.13, `.venv`, `pytest` (79 tests, all passing), `gemini-3.1-flash-lite` for LLM calls
- **Python Venv:** `d:\Research Project\PharmaGuard\.venv\Scripts\python.exe`
- **Cache Schema Version:** `v7` (source of truth: `pharmaguard/tools/cache.py`)
- **Prompts Version:** `v1.1` (current production)
- **Test runner:** `python -m pytest` from the repo root

---

### Architecture Summary

PharmaGuard is a pharmacovigilance triage pipeline that evaluates drug-event pairs across three evidence sources:

1. **FAERS signal stats** (`prr_score`) — Proportional Reporting Ratio disproportionality
2. **PubMed literature** (`grade_score`) — Graded A/B/C evidence
3. **ChEMBL mechanistic plausibility** (`plausibility_score`) — LLM-derived

**Escalation formula** (deterministic, not LLM-free-text):

- Gate 1 `NO_SIGNAL`: if FAERS reports = 0 → `DO_NOT_ESCALATE`
- Gate 2 confounding discount applied to `prr_score`
- Composite confidence = weighted sum of the 3 scores
- If confidence ≥ 0.70 → `ESCALATE`; if ≥ 0.35 → `MONITOR`; else → `DO_NOT_ESCALATE`

**Key source files:**

- `pharmaguard/agent/output_schema.py` — `TriageReport`, `compute_source_agreement()`, `LeakageCritique`
- `pharmaguard/tools/chembl_tool.py` — `_critique_plausibility_leakage()` (leakage critic)
- `pharmaguard/tools/cache.py` — `CACHE_SCHEMA_VERSION = "v7"`, `ToolCache`
- `pharmaguard/data/ground_truth.json` — 15 benchmark pairs (7 confirmed\_positive, 5 genuine\_negative\_control, 3 zero\_report\_edge\_case)
- `pharmaguard/evaluator.py` — benchmark evaluation runner

---

### Benchmark: 15 Ground Truth Pairs

| **#DrugEventCategoryExpected** |                |                        |                            |                   |
| ------------------------------ | -------------- | ---------------------- | -------------------------- | ----------------- |
| 0                              | montelukast    | suicidal\_ideation     | confirmed\_positive        | ESCALATE          |
| 1                              | ciprofloxacin  | tendon\_rupture        | confirmed\_positive        | ESCALATE          |
| 2                              | isotretinoin   | teratogenicity         | confirmed\_positive        | ESCALATE          |
| 3                              | clozapine      | agranulocytosis        | confirmed\_positive        | ESCALATE          |
| 4                              | valproic\_acid | hepatotoxicity         | confirmed\_positive        | ESCALATE          |
| 5                              | rosiglitazone  | myocardial\_infarction | confirmed\_positive        | ESCALATE          |
| 6                              | pembrolizumab  | pneumonitis            | confirmed\_positive        | ESCALATE          |
| 7                              | liraglutide    | pancreatic\_cancer     | genuine\_negative\_control | DO\_NOT\_ESCALATE |
| 8                              | metformin      | hypoglycaemia          | genuine\_negative\_control | DO\_NOT\_ESCALATE |
| 9                              | atorvastatin   | dementia               | genuine\_negative\_control | DO\_NOT\_ESCALATE |
| 10                             | albuterol      | suicidal\_ideation     | genuine\_negative\_control | DO\_NOT\_ESCALATE |
| 11                             | amoxicillin    | tendon\_rupture        | genuine\_negative\_control | DO\_NOT\_ESCALATE |
| 12                             | atorvastatin   | common\_cold           | zero\_report\_edge\_case   | DO\_NOT\_ESCALATE |
| 13                             | imatinib       | tooth\_eruption        | zero\_report\_edge\_case   | DO\_NOT\_ESCALATE |
| 14                             | adalimumab     | frostbite              | zero\_report\_edge\_case   | DO\_NOT\_ESCALATE |

**Production baseline results** (`outputs/eval-run-*_report.json`, `prompts_version: v1.0`, timestamp: August 14 2026):

- Strict: Precision 1.00, Recall 0.857 (1 FN: `montelukast` outputs `MONITOR`, confidence 0.664 < 0.70)
- Lenient: Precision 0.875, Recall 1.00 (1 FP: `metformin` outputs `MONITOR` due to confounded FAERS signal)

---

### Completed Research Work

#### Experiment 1 — Repeated-Run Stability (R0)

- **Script:** `scripts/research/stability_repeated_runs.py`
- **Artifact:** `outputs/research/stability/repeated_run_variance.json`
- **Finding:** 0/15 unstable pairs (temperature=0.0, n=10 repeats), but ran with `confounding_enabled: false`

#### Experiment 1b — Confounding Stability Follow-Up (R0)

- **Script:** same stability script, confounding-eligible pairs only (8 pairs with prr\_score > 0)
- **Artifact:** `outputs/research/stability/repeated_run_variance_confounding.json`
- **Finding:** 100% discount\_factor stability across 10 runs (Wilson 95% CI: [0.7225, 1.0000] — does NOT rule out \~25% instability rate)
- **Important caveat in DECISIONS.md §28:** The metformin discount\_factor (0.10 vs 0.20 discrepancy originally found) cannot be attributed to a specific cause at n=10

#### Experiment 2 — Multi-Source Ablation, Threshold Sensitivity, Counterfactual Decomposition (R0)

- **Script:** `scripts/research/source_ablation.py`
- **Artifacts:**
  - `outputs/research/source_ablation/ablation_results.json`
  - `outputs/research/source_ablation/threshold_sensitivity.json`
  - `outputs/research/source_ablation/counterfactual_margins.json`
- **Key findings:**
  - Removing FAERS alone: 8 gate artifacts (NO\_SIGNAL triggered artificially)
  - Removing Lit or ChEMBL alone: fewer flips
  - Threshold 0.75/0.80 flips: `ciprofloxacin` and `rosiglitazone` (both confidence=0.70) → MONITOR

#### DECISIONS.md §30 — Threats to Validity (R0)

- 8-point synthesis with empirical citations
- Commits: `b9a3d88` (added), `22e5f04` (corrected rosiglitazone vs valproic\_acid in §30.5)

#### R1 Error Taxonomy

- **Script:** `scripts/research/error_taxonomy.py`
- **Artifact:** `outputs/research/error_taxonomy/taxonomy_results.json`
- **Tests:** `tests/test_error_taxonomy.py` (10/10 passing)
- **7 categories:** MECHANISTIC\_UNCERTAINTY, CONFOUNDED\_SIGNAL, CROSS\_SOURCE\_DISCORDANCE, LLM\_MEMORIZATION\_LEAKAGE, GATE\_ARTIFACT, AGENT\_ARCHITECTURE\_DIVERGENCE, ZERO\_REPORT\_EDGE\_CASE

**Multi-category co-occurrences** (4 pairs):

| **PairCategories**                    |                                                                                                                                   |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| montelukast::suicidal\_ideation       | MECHANISTIC\_UNCERTAINTY, CROSS\_SOURCE\_DISCORDANCE, LLM\_MEMORIZATION\_LEAKAGE, GATE\_ARTIFACT, AGENT\_ARCHITECTURE\_DIVERGENCE |
| metformin::hypoglycaemia              | CONFOUNDED\_SIGNAL, CROSS\_SOURCE\_DISCORDANCE, GATE\_ARTIFACT                                                                    |
| atorvastatin::dementia                | CROSS\_SOURCE\_DISCORDANCE, AGENT\_ARCHITECTURE\_DIVERGENCE                                                                       |
| rosiglitazone::myocardial\_infarction | CONFOUNDED\_SIGNAL, GATE\_ARTIFACT                                                                                                |

#### R1 Reproducibility Manifest

- **Script:** `scripts/research/build_reproducibility_manifest.py`
- **Artifacts:** `outputs/research/reproducibility_manifest.json` + `.md`
- **Tests:** `tests/test_reproducibility_manifest.py` (5/5 passing)
- **Coverage:** 75/75 JSON files under `outputs/` indexed, 1:1 verified
- Completeness: 5 COMPLETE (research experiments), 66 PARTIAL (frozen eval reports), 4 MINIMAL (legacy probes)
- **Commit:** `e3804cd` (pushed to GitHub)

---

### OMOP Reference Set Feasibility — Status: GO-SCOPED (with corrections)

**Official file:** `OHDSI/MethodEvaluation/data/omopReferenceSet.rda` (6,872 bytes XZ-compressed)

- **pyreadr** (`pip install pyreadr`) successfully parses it with **zero R dependency** → `pandas.DataFrame(399, 10)`
- **10 columns:** `exposureId`, `exposureName`, `outcomeId`, `outcomeName`, `groundTruth`, `indicationId`, `indicationName`, `comparatorId`, `comparatorName`, `comparatorType`
- **182 unique exposures, 4 outcome endpoints:**
  - `OMOP Acute Liver Failure 1` (n=118: 81 pos, 37 neg)
  - `OMOP Acute Renal Failure 1` (n=88: 24 pos, 64 neg)
  - `OMOP Acute myocardial Infarction 1` (n=102: 36 pos, 66 neg)
  - `HOI Upper GI #3` (n=91: 24 pos, 67 neg)

**VERIFIED collision list (corrected from prior investigation):**

| **PG DrugPG EventOMOP ExposureOMOP OutcomeOMOP groundTruthVerdict**                        |                        |                  |                                           |              |                                     |
| ------------------------------------------------------------------------------------------ | ---------------------- | ---------------- | ----------------------------------------- | ------------ | ----------------------------------- |
| valproic\_acid                                                                             | hepatotoxicity         | Valproate        | Acute Liver Failure                       | 1 (Positive) | ✅ Real collision                    |
| rosiglitazone                                                                              | myocardial\_infarction | rosiglitazone    | HOI Upper GI #3                           | 0 (Negative) | ❌ NOT a collision — wrong outcome   |
| ciprofloxacin                                                                              | tendon\_rupture        | Ciprofloxacin    | Acute Liver Failure                       | 1 (Positive) | ✅ Partial overlap (different event) |
| clozapine                                                                                  | agranulocytosis        | Clozapine        | Acute Liver Failure + Acute Renal Failure | 1 + 0        | ✅ Partial overlap (different event) |
| imatinib                                                                                   | tooth\_eruption        | imatinib         | Acute Liver Failure                       | 1 (Positive) | ✅ Partial overlap (different event) |
| metformin                                                                                  | hypoglycaemia          | NOT in exposures | —                                         | —            | ❌ Was only an active comparator     |
| amoxicillin                                                                                | tendon\_rupture        | NOT in exposures | —                                         | —            | ❌ Was only an active comparator     |
| montelukast, isotretinoin, pembrolizumab, liraglutide, atorvastatin, albuterol, adalimumab | any                    | NOT in OMOP      | —                                         | —            | ❌ Absent from OMOP dataset          |

**True collision count: 1 exact, 3 partial drug-only overlaps. The prior claim of 2 exact + 5 partial was wrong.**

---

### DECISIONS.md — Key Section Index

- §18: Escalation thresholds (0.70 / 0.35) — uncalibrated, documented priors
- §21: Confounding discount mechanism
- §24: ReAct vs deterministic pipeline divergence (4/15 pairs, 73.3% agreement)
- §26: Cross-source agreement metric (3/15 DISCORDANT: montelukast, metformin, atorvastatin::dementia)
- §27: Adversarial leakage critic (4 probe cases, all flagged leaked=True)
- §28: Confounding stability investigation (metformin discount\_factor discrepancy)
- §30: Threats to Validity — 8-point synthesis (corrected §30.5: rosiglitazone not valproic\_acid)

---

### Key Pending / Next Steps (not yet implemented)

1. **OMOP GO-SCOPED integration:** Acquire the 399 pairs via pyreadr, curate a 24–32 pair high-confidence subset (6–8 per outcome), store in `pharmaguard/data/ground_truth_omop_pilot.json` as a **parallel secondary benchmark** (do NOT merge into existing 15-pair `ground_truth.json`). Proxy MedDRA PT mappings: AMI → `myocardial_infarction`, Upper GI → `gastrointestinal_haemorrhage`, Liver → `hepatotoxicity`, Renal → `acute_kidney_injury`.
2. **Paper writing gate:** Per standing instruction in DECISIONS.md §25, paper writing requires an **explicit, separate go-ahead from Krishna**. Not yet granted.

---

### Full Test Suite State

```
79 tests total, 79 passed (53s)
```

tests/test\_agent\_parsers.py         (2)

tests/test\_cache.py                 (7)

tests/test\_chembl\_tool.py           (5)

tests/test\_confounding.py           (7)

tests/test\_error\_taxonomy.py        (10)

tests/test\_output\_schema.py         (25)

tests/test\_pubmed\_tool.py           (3)

tests/test\_signal\_source.py         (9)

tests/test\_source\_ablation.py       (4)

tests/test\_stability\_repeated\_runs.py (7)

tests/test\_reproducibility\_manifest.py (5)  ← newest

---

### Git Log (recent)

```
e3804cd feat(research): implement R1 error taxonomy and consolidated reproducibility manifest
```

22e5f04 docs(context): fix flipped pair name from valproic\_acid to rosiglitazone in §30.5

b9a3d88 docs(context): synthesize consolidated Threats to Validity section in DECISIONS.md

674adb2 feat(research): add repeated-run stability artifact for confounding-eligible pairs

64ecb1e feat(research): support confounding-enabled repeated-run stability analysis

caa7f05 feat(research): implement Experiment 2 multi-source ablation, threshold sensitivity, counterfactual margins