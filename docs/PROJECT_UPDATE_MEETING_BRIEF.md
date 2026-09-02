# Group 07: 7th Semester B.Tech Project Progress Briefing

**Project Title:** PharmaGuard: A Tool-Grounded Agentic AI Architecture for Pharmacovigilance Signal Triage  
**Course:** 7th Semester B.Tech Project (IT) — IIIT Allahabad  
**Project Group:** Group 07  
**Team Members:** Krishna Sikheriya (IIT2023139), Lokesh, Naitik  
**Project Supervisor:** Dr. Nikhilanand Arya, Assistant Professor, Department of Information Technology  
**Date:** September 2026  
**Repository State:** Main Branch (`main`), 84/84 Unit & Integration Tests Passing  

---

## Executive Summary

PharmaGuard investigates a critical open question in clinical artificial intelligence: **can large language models (LLMs) be constrained to reason strictly from verifiable, multi-source external evidence rather than memorized parametric knowledge during postmarketing drug-safety triage?**

Spontaneous reporting databases such as the FDA Adverse Event Reporting System (FAERS) receive millions of safety reports annually, creating a severe triage bottleneck for pharmacovigilance teams. While standard LLMs are prone to hallucinations, temporal confusion (recalling a historical concern without checking if it was formally investigated and dismissed), and ungrounded confidence, PharmaGuard enforces deterministic evidence fusion across three independent biomedical data streams:
1. **Empirical Disproportionality:** Real-time FAERS reporting statistics (PRR, ROR, 95% confidence intervals).
2. **Molecular Pharmacology:** ChEMBL target mechanisms and biological plausibility deduction.
3. **Biomedical Literature:** Live PubMed retrieval and structured Grade A/B/C evidence assessment.

The evidence streams are synthesized through a published, fully deterministic linear confidence formula ($0.40 \cdot S_{\text{FAERS}} + 0.40 \cdot S_{\text{PubMed}} + 0.20 \cdot S_{\text{Mech}}$) and an auditable escalation gating protocol (**ESCALATE / MONITOR / DO_NOT_ESCALATE**).

To date, the project has completed full software architecture implementation, extensive benchmark evaluations on a frozen 15-pair curated ground-truth set, Leave-One-Out stability verification, adversarial epistemic leakage audits, confounding discount heuristics, a 32-pair secondary OMOP reference set pilot, and an interactive 6-view Streamlit evaluation dashboard.

---

## 1. Work Completed So Far

### 1.1 Multi-Source Evidence Grounding Pipeline
- **openFDA FAERS Disproportionality Engine (`pharmaguard/tools/signal_source.py`):** Automatically queries the openFDA endpoint to construct $2 \times 2$ contingency tables, computing Proportional Reporting Ratios (PRR), Reporting Odds Ratios (ROR), report counts, and exact log-normal 95% confidence intervals with automatic low-count and CI-downgrade gating.
- **ChEMBL Pharmacology & Plausibility Engine (`pharmaguard/tools/chembl_tool.py`):** Integrates curated ChEMBL mechanism-of-action metadata for 50 benchmark drugs with an agentic plausibility reasoning fallback. Structured Pydantic outputs isolate reasoning traces from discrete ratings (`HIGH=1.0`, `MODERATE=0.5`, `LOW=0.0`, `UNKNOWN=0.0`).
- **PubMed Literature Retrieval & Grading Engine (`pharmaguard/tools/pubmed_tool.py`):** Performs structured NCBI E-utilities queries, extracts abstracts, and applies a strict clinical evidence grading rubric (`Grade A=1.0` for statistically significant associations, `Grade B=0.5` for case reports/series, `Grade C=0.0` for negative or unconfirmed literature).
- **Persistent Disk-Backed Tool Cache (`pharmaguard/tools/cache.py`):** Backed by `diskcache` with schema versioning (`v7`), ensuring $100\%$ zero-network replayability during testing and offline demonstration.

### 1.2 Deterministic Decision Logic & Dual Agent Modes
- **Deterministic Confidence Formulation (`pharmaguard/agent/output_schema.py`):**
  $$\text{Confidence} = 0.40 \times S_{\text{FAERS}} + 0.40 \times S_{\text{PubMed}} + 0.20 \times S_{\text{Mech}}$$
- **Hierarchical Escalation Gating (`derive_escalation()`):**
  - **Gate 1 (Hard Empirical Floor):** If FAERS $S_{\text{FAERS}} == \text{NO\_SIGNAL}$, unconditionally output **`DO_NOT_ESCALATE`** (prevents speculative escalations on zero-report pairs).
  - **Gate 2 (High-Confidence Escalation):** If $\text{Confidence} \ge 0.70$ and $S_{\text{FAERS}} \in \{\text{STRONG}, \text{MODERATE}\}$, output **`ESCALATE`**.
  - **Gate 3 (Modulated Monitoring):** If $\text{Confidence} \ge 0.35$, output **`MONITOR`** (captures emergent signals with mechanistic uncertainty).
  - **Gate 4 (Default):** Otherwise, output **`DO_NOT_ESCALATE`**.
- **Dual Orchestration Engines:**
  - *Fixed Pipeline Agent (`fixed_pipeline.py`):* Deterministic sequence (FAERS $\to$ ChEMBL $\to$ PubMed $\to$ Synthesize) — primary production mode.
  - *ReAct LangGraph Agent (`react_agent.py`):* Dynamic LLM-directed tool-use graph for comparative architectural audits.

### 1.3 Methodology Audits & Epistemic Probes
- **Adversarial Mechanistic Leakage Critic (`chembl_tool.py`):** Implemented an independent, blinded maker-checker critic agent (inspired by the MARCH framework, ACL 2026) that audits plausibility rationales for parametric regulatory leakage without access to drug or event names.
- **Polypharmacy Confounding Evaluator (`confounding.py`):** Implemented an opt-in clinical discounting tool to identify concomitant medication artifacts (e.g., insulin co-prescription in metformin reporting) and apply multiplicative discounting factors ($0.0 \le \text{factor} \le 1.0$).
- **Cross-Source Evidence Concordance Property (`source_agreement`):** Programmatic classification identifying $\text{DISCORDANT}$ vs $\text{CONCORDANT}$ evidence profiles across modalities.

### 1.4 Benchmark Datasets & Secondary Pilots
- **Frozen 15-Pair Core Benchmark (`pharmaguard/data/ground_truth.json`):** 7 Confirmed Positives (FDA Boxed Warnings), 5 Genuine Negative Controls, and 3 Zero-Report Edge Cases, fully documented with regulatory and epidemiological citations.
- **Secondary 32-Pair OMOP Pilot Benchmark (`pharmaguard/data/ground_truth_omop_pilot.json`):** Derived from the OHDSI OMOP reference set (Ryan et al., *Drug Safety* 2013) across 4 clinical endpoints (acute liver injury, acute kidney injury, acute myocardial infarction, upper gastrointestinal bleeding).

### 1.5 Interactive Dashboard & Reproducibility Infrastructure
- **Streamlit Production Dashboard (`scripts/dashboard.py`):** Full 6-view evaluation dashboard with dynamic Light/Dark theme switching, high-resolution metric cards, dense aligned tables, Plotly confidence decomposition charts, and dedicated tabs for Overview, Per-Pair Table, Disagreement Spotlight, Baseline Comparison, Methodology Probes, and OMOP Pilot.
- **Automated Verification & Manifest:** Automated 1080p Playwright screenshot suite (`scripts/dev/capture_screenshots.py`) and programmatic reproducibility manifest (`outputs/research/reproducibility_manifest.json`) covering 107 output artifacts.
- **Comprehensive Test Suite:** 84 passing unit and integration tests (`tests/`) verifying parsers, cache integrity, schema constraints, ablation matrices, and statistical stability.

---

## 2. Results and Outcomes Obtained

```
========================================================================================
                          SUMMARY OF EXPERIMENTAL RESULTS
========================================================================================
Core Benchmark (15 pairs):     Strict F1: 0.923 (P=1.000, R=0.857, S=1.000)
                               Lenient F1: 0.933 (P=0.875, R=1.000, S=0.875)
                               Over-Caution Rate: 12.5% (1/8 negatives -> MONITOR)
                               Spurious False Alarms: FP = 0

Single-Shot LLM Baseline:      Strict F1: 0.933 | Lenient F1: 0.824 | OCR: 25.0% (2/8)

LOO Stability (15 folds):      Strict F1 = 0.923 ± 0.023 | Lenient F1 = 0.933 ± 0.019

ReAct Divergence Rate:         26.7% (4/15 pairs diverged from deterministic gating)

Epistemic Critic Detection:    100% Sensitivity (4/4 leakage cases detected and isolated)

Metformin Confounding Fix:     Confidence discounted 0.4000 -> 0.0800 (DO_NOT_ESCALATE)

OMOP Pilot (32 pairs):         Specificity: 1.000 (16/16 negative controls cleared)
                               Lenient F1: 0.720 (9/16 positives captured)
========================================================================================
```

### 2.1 Primary Benchmark Performance (15 Core Pairs)

| Evaluation Metric | PharmaGuard (Tool-Grounded) | Wilson 95% CI | Bootstrap 95% CI ($B=1000$) | Single-Shot Baseline (Ungrounded LLM) |
| :--- | :---: | :---: | :---: | :---: |
| **Strict Precision** | **1.000** | [0.610, 1.000] | [1.000, 1.000] | 0.875 |
| **Strict Recall** | **0.857** (6/7) | [0.487, 0.974] | [0.571, 1.000] | 1.000 |
| **Strict Specificity** | **1.000** (8/8) | [0.676, 1.000] | [1.000, 1.000] | 0.875 |
| **Strict $F_1$-Score** | **0.923** | — | [0.727, 1.000] | **0.933** |
| **Lenient Precision** | **0.875** | [0.529, 0.978] | [0.778, 1.000] | 0.700 |
| **Lenient Recall** | **1.000** (7/7) | [0.646, 1.000] | [1.000, 1.000] | 1.000 |
| **Lenient Specificity** | **0.875** (7/8) | [0.529, 0.978] | [0.750, 1.000] | 0.625 |
| **Lenient $F_1$-Score** | **0.933** | — | [0.769, 1.000] | **0.824** |
| **Over-Caution Rate (OCR)** | **12.5%** (1/8) | [0.022, 0.471] | — | **25.0%** (2/8) |
| **Spurious False Alarms (FP)**| **0** | — | — | 1 |

*Key Benchmark Insight:* Under lenient scoring, PharmaGuard achieves **$100\%$ Recall ($7/7$)** while maintaining an Over-Caution Rate half that of the ungrounded baseline ($12.5\%$ vs $25.0\%$). In strict mode, PharmaGuard produced **0 spurious false alarms on negative controls**, whereas the baseline hallucinated an escalation for `liraglutide::pancreatic_cancer` based on historical regulatory debate rather than the FDA/EMA 2014 resolution.

### 2.2 Leave-One-Out (LOO) Cross-Validation Stability
- **Strict $F_1$:** Mean $= 0.923 \pm 0.023$ (Range: $0.889$ to $1.000$).
- **Lenient $F_1$:** Mean $= 0.933 \pm 0.019$ (Range: $0.923$ to $1.000$).
- The narrow standard deviations confirm that overall system performance does not hinge on any single fragile drug–event pair.

### 2.3 ReAct Generative Divergence Finding (DECISIONS.md §24)
When the ReAct agent's unconstrained free-form recommendation was compared against the deterministic pipeline across all 15 pairs, the two modes **diverged on 4 of 15 pairs (26.7%)**:
- For nominal negatives (`atorvastatin::dementia`, `albuterol::suicidal_ideation`), the unconstrained agent recommended `ESCALATE` or `MONITOR` swayed by associative literature discussions.
- For `liraglutide::pancreatic_cancer`, the unconstrained agent recommended `MONITOR` based on theoretical receptor biology, whereas the deterministic pipeline enforced the hard `NO_SIGNAL` gate to output `DO_NOT_ESCALATE`.
- *Outcome:* Proves empirically that postmarketing safety triage cannot rely on unconstrained generative LLM judgments without deterministic evidence gating.

### 2.4 Epistemic Auditing & Confounding Solutions
1. **Adversarial Critic (DECISIONS.md §27):** Tested across 4 leakage probe cases, achieving **$100\%$ detection sensitivity (4/4)** in isolating non-mechanistic regulatory text (e.g. boxed warning mentions in Montelukast).
2. **Confounding Discounting (DECISIONS.md §28):** On `metformin::hypoglycaemia` (heavily confounded by co-prescribed insulin/sulfonylureas, FAERS $\text{PRR}=10.73$), the tool computed a $0.20$ discount factor, dropping confidence from **$0.4000$ to $0.0800$** and correctly routing the pair to **`DO_NOT_ESCALATE`**.

### 2.5 Secondary OMOP Pilot Benchmark Results (32 Pairs)

| Clinical Endpoint | Positives | Negatives | Strict Recall | Lenient Recall | Specificity | Outcome Summary |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Hepatotoxicity** | 4 | 4 | 1/4 (25.0%) | 3/4 (75.0%) | 4/4 (100%) | Isoniazid escalated; Carbamazepine & Allopurinol monitored; Captopril missed (conf 0.332) |
| **Acute Kidney Injury** | 4 | 4 | 0/4 (0.0%) | 4/4 (100%) | 4/4 (100%) | All 4 positives (Lisinopril, Naproxen, Acyclovir, HCTZ) captured as MONITOR |
| **Myocardial Infarction** | 4 | 4 | 0/4 (0.0%) | 1/4 (25.0%) | 4/4 (100%) | Indomethacin monitored; Amlodipine, Dipyridamole, Nifedipine zeroed by PRR < 2.0 |
| **GI Haemorrhage** | 4 | 4 | 0/4 (0.0%) | 1/4 (25.0%) | 4/4 (100%) | Ketoprofen monitored; SSRIs (Citalopram, Fluoxetine, Sertraline) zeroed by PRR < 2.0 |
| **Total / Aggregate** | **16** | **16** | **1/16 (6.2%)** | **9/16 (56.2%)** | **16/16 (100%)**| **Strict F1: 0.118 \| Lenient F1: 0.720 \| Specificity: 1.000** |

---

## 3. Challenges and Methodological Issues Faced

### 3.1 Challenge 1: Parametric Regulatory & Clinical Leakage in Foundation Models
- **Issue:** Pre-trained LLMs have memorized FDA Boxed Warnings, label changes, and major clinical trials. When asked to evaluate *biological plausibility* from raw drug mechanisms, LLMs frequently substitute memorized regulatory history for biochemical deduction (e.g., upgrading Montelukast plausibility to MODERATE by citing the 2020 FDA warning).
- **Resolution:** Established a dual plausibility evaluation protocol (human-curated benchmark vs. agent-derived) and developed the independent Adversarial Leakage Critic (MARCH pattern) to detect and redact parametric contamination.

### 3.2 Challenge 2: Polypharmacy Confounding in Spontaneous FAERS Data
- **Issue:** Spontaneous databases report co-occurrences without baseline prescription context. High-volume therapies (such as Metformin in diabetes) exhibit massive disproportionality ($PRR > 10.0$) with hypoglycemia solely because patients take concomitant insulin or sulfonylureas.
- **Resolution:** Introduced the confounding assessment module (`confounding.py`) which detects polypharmacy multi-drug regimens and applies grounded discount multipliers to FAERS sub-scores.

### 3.3 Challenge 3: Denominator Dilution in High-Volume Chronic Medications (The OMOP Finding)
- **Issue:** In the OMOP 32-pair pilot, 6 confirmed positive controls were missed under the strict `PRR < 2.0 -> NO_SIGNAL` hard gate. For chronic, high-utilization drugs (amlodipine, nifedipine, citalopram, fluoxetine, sertraline), enormous total report volumes dilute PRR point estimates to $1.16$–$1.90$, despite 95% lower confidence intervals strictly clearing $1.0$ ($CI_{lower} \ge 1.066$) and high biological plausibility.
- **Methodological Discipline:** In accordance with non-retroactive evaluation rules (`DECISIONS.md §15, §31`), we **refused to mutate thresholds post-hoc**, documenting this limitation as a formal external-validity boundary of static thresholding.

### 3.4 Challenge 4: Heuristic Escalation Threshold Calibration
- **Issue:** Escalation cutoffs ($0.70$ for ESCALATE, $0.35$ for MONITOR) represent fixed heuristic priors. Calibrating optimal thresholds via ROC or Youden's J index requires hundreds of ground-truth pairs, which exceeds manual single-curator validation capacity.
- **Resolution:** Disclosed thresholds as uncalibrated priors in all documentation (`DECISIONS.md §18`) and conducted a 25-point sensitivity sweep to characterize boundary margins.

---

## 4. Work Planned for the Next Phase

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NEXT PHASE ROADMAP & MILESTONES                       │
├──────────────────────┬──────────────────────────────────────────────────────────┤
│ Phase 4.1 (Week 1–2) │ Dynamic Statistical Thresholding (Bayesian / CI Bounds) │
│ Phase 4.2 (Week 3–4) │ MedDRA Ontology Canonicalization Layer (LLT -> PT)      │
│ Phase 4.3 (Week 5–6) │ Clinical Pharmacologist Expert Validation Protocol      │
│ Phase 4.4 (Week 7–8) │ Conference Paper Drafting & Final Capstone Defense Deck │
└──────────────────────┴──────────────────────────────────────────────────────────┘
```

1. **Dynamic Disproportionality Gating:** Investigate replacing the rigid static $PRR < 2.0$ cutoff with statistical significance lower-bound gating ($PRR_{lower\_ci} > 1.0$) or Bayesian Empirical Bayes shrinkage (EBGM) to resolve high-utilization chronic dilution without sacrificing negative control specificity.
2. **Automated MedDRA PT Normalization Layer:** Develop a robust ontology translation module mapping colloquial adverse event terms, British spellings (e.g. *hypoglycaemia*), and Lowest Level Terms (LLTs) to standardized MedDRA Preferred Terms before querying openFDA.
3. **External Clinical Validation Protocol:** Prepare a blinded study protocol for independent review of biological plausibility ratings by clinical pharmacologists to replace single-curator annotations.
4. **Conference Manuscript Preparation:** Complete drafting of the academic research paper targeting health informatics and clinical AI venues (e.g., IEEE BIBM 2026, ACM CHIL, or JAMIA).

---

## 5. Support and Guidance Required from Supervisor

We would appreciate Dr. Arya's feedback and guidance on the following four points during the upcoming in-person meeting:

1. **Threshold Gating Strategy:** Feedback on our proposed transition from static PRR magnitude thresholds ($\ge 2.0$) to lower confidence interval bounds ($PRR_{lower\_ci} > 1.0$) or Bayesian shrinkage (EBGM) for chronic medication signal detection.
2. **Dual-Metric Reporting Framework:** Validation of our Strict vs. Lenient evaluation standard and Leave-One-Out stability methodology for capstone defense and conference publication standards.
3. **Target Publication Venue:** Recommendations on the most suitable submission venue (e.g., IEEE BIBM, ACM Conference on Health, Inference, and Learning [CHIL], or JAMIA Open).
4. **Capstone Defense Pacing:** Guidance on structuring the final 16:9 defense slide deck and live dashboard demonstration.

---

## Summary of Reference Documents & Artifacts

| Document / Artifact | Repository Path | Description |
|---|---|---|
| **Design Decisions Record** | [`docs/context/DECISIONS.md`](file:///d:/Research%20Project/PharmaGuard/docs/context/DECISIONS.md) | Complete 31-section architectural and methodological log |
| **System Architecture** | [`docs/context/ARCHITECTURE.md`](file:///d:/Research%20Project/PharmaGuard/docs/context/ARCHITECTURE.md) | Component data flow, Pydantic schemas, and tech stack |
| **Project Overview** | [`docs/context/UNDERSTAND.md`](file:///d:/Research%20Project/PharmaGuard/docs/context/UNDERSTAND.md) | Complete narrative overview and results walk-through |
| **Core Ground Truth (15 Pairs)** | [`pharmaguard/data/ground_truth.json`](file:///d:/Research%20Project/PharmaGuard/pharmaguard/data/ground_truth.json) | 15 curated pairs with regulatory provenance |
| **OMOP Pilot Ground Truth (32 Pairs)**| [`pharmaguard/data/ground_truth_omop_pilot.json`](file:///d:/Research%20Project/PharmaGuard/pharmaguard/data/ground_truth_omop_pilot.json) | 32 OMOP reference set pilot pairs across 4 endpoints |
| **Evaluation Dashboard** | [`scripts/dashboard.py`](file:///d:/Research%20Project/PharmaGuard/scripts/dashboard.py) | Streamlit interactive evaluation UI (6 views) |
| **Light Verification Screenshots** | [`assets/Screenshots/Light/`](file:///d:/Research%20Project/PharmaGuard/assets/Screenshots/Light/) | 1080p full-panel captures for all 6 views |
| **Dark Verification Screenshots** | [`assets/Screenshots/Dark/`](file:///d:/Research%20Project/PharmaGuard/assets/Screenshots/Dark/) | 1080p full-panel captures for all 6 views |
