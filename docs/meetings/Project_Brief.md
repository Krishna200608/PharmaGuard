# PharmaGuard: Project Brief & Progress Report

**Course:** B.Tech Major Project (7th Semester) — Department of Information Technology  
**Institution:** Indian Institute of Information Technology, Allahabad (IIIT Allahabad)  
**Project Group:** Group 07  
**Project Title:** PharmaGuard: A Tool-Grounded Agentic AI Architecture for Pharmacovigilance Signal Triage  
**Students:**  
* Krishna Sikheriya (Roll No: **IIT2023139**)  
* Lokesh  
* Naitik  
**Project Supervisor:** Dr. Nikhilanand Arya, Assistant Professor, Department of Information Technology  
**Date:** September 2026  
**Repository & Codebase:** [https://github.com/Krishna200608/PharmaGuard](https://github.com/Krishna200608/PharmaGuard) (84/84 Automated Tests Passing)  

---

## 1. Executive Summary & Problem Statement

### 1.1 The Real-World Challenge
When a new medicine is approved and prescribed to millions of patients, postmarketing surveillance (**Pharmacovigilance**) continuously monitors for unexpected side effects. Databases like the **FDA Adverse Event Reporting System (FAERS)** receive over 2 million safety reports each year. 

Safety teams face a severe **triage bottleneck**: they must rapidly distinguish between:
1. **Real, dangerous safety signals** that need immediate regulatory warnings or label updates (e.g., severe liver damage or cardiac arrest).
2. **Benign statistical noise or co-medication artifacts** (e.g., a diabetic patient on metformin who experiences low blood sugar primarily because they also take insulin).

Currently, this triage step is largely manual, labor-intensive, and prone to delays.

### 1.2 Why Standard AI (ChatGPT / Raw LLMs) Cannot Be Used Directly
Large Language Models (LLMs) are often proposed to automate clinical triage, but ungrounded LLMs suffer from severe, well-documented flaws:
* **Hallucination & Fabricated Associations:** Recent clinical studies ([Omar et al., *Communications Medicine*, 2025](https://doi.org/10.1038/s43856-025-00787-8)) found that leading LLMs hallucinate clinical relationships in up to 83% of edge-case scenarios.
* **Temporal Confusion:** An LLM might recall from its training data that a historical safety concern was raised in 2013, but fail to realize that health authorities formally investigated and cleared it in 2014.
* **Uncalibrated Confidence:** A raw LLM cannot provide a mathematically verifiable confidence score—it only provides a self-reported text estimate.

### 1.3 The PharmaGuard Solution
PharmaGuard is a **tool-grounded, multi-source agentic AI architecture**. Instead of letting the AI answer from memory, PharmaGuard strictly forces the model to fetch and verify real-time data from **three independent biomedical databases** before combining the findings using a **deterministic mathematical formula** to produce an auditable decision: **ESCALATE**, **MONITOR**, or **DO_NOT_ESCALATE**.

---

## 2. System Architecture & Methodology

```
                       [ Input: Candidate Drug + Adverse Event ]
                                           │
                                           ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │                    3 INDEPENDENT EVIDENCE GATHERING ENGINES               │
   ├───────────────────────────┬───────────────────────────┬───────────────────┤
   │     1. openFDA FAERS      │    2. ChEMBL Database     │ 3. PubMed Tool    │
   │  Spontaneous Reports DB   │   Molecular Pharmacology  │ Medical Literature│
   │  Calculates PRR, ROR, CIs │ Biological Plausibility   │ Evidence Grading  │
   │      (Score: 0.0 to 1.0)  │    (Score: 0.0 to 1.0)    │(Score: 0.0 to 1.0)│
   └───────────────────────────┴───────────────────────────┴───────────────────┘
                                           │
                                           ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │                 DETERMINISTIC CONFIDENCE SCORE FORMULATION                │
   │                                                                           │
   │   Confidence = 0.40 · S_FAERS + 0.40 · S_PubMed + 0.20 · S_ChEMBL         │
   │   (Completely transparent and auditable — zero LLM guesswork)             │
   └───────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │                       HIERARCHICAL ESCALATION GATING                      │
   ├───────────────────────────────────────────────────────────────────────────┤
   │  Gate 1 (Hard Stop) : If FAERS == NO_SIGNAL  ──► DO_NOT_ESCALATE          │
   │  Gate 2 (Escalate)  : If Confidence >= 0.70  ──► ESCALATE                 │
   │  Gate 3 (Monitor)   : If Confidence >= 0.35  ──► MONITOR                  │
   │  Gate 4 (Default)   : Otherwise              ──► DO_NOT_ESCALATE          │
   └───────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
            [ Structured JSON Report + Interactive Streamlit UI ]
```

### 2.1 The Three Evidence Streams
1. **Real-World Epidemiological Statistics (openFDA FAERS):**
   Queries the live FDA database to construct $2 \times 2$ contingency tables and compute the **Proportional Reporting Ratio (PRR)** and **Reporting Odds Ratio (ROR)** with exact log-normal 95% confidence intervals ([Evans et al., 2001](https://doi.org/10.1002/pds.677); [van Puijenbroek et al., 2002](https://doi.org/10.1002/pds.688)).
2. **Molecular Pharmacology (ChEMBL Target Database):**
   Checks whether the drug’s biological mechanism of action (MoA) makes it biologically plausible that it could cause the symptom ([Gaulton et al., *Nucleic Acids Res*, 2019](https://doi.org/10.1093/nar/gky1075)). Ratings: `HIGH` (1.0), `MODERATE` (0.5), `LOW` (0.0), `UNKNOWN` (0.0).
3. **Biomedical Literature Grading (NCBI PubMed E-Utilities):**
   Searches published medical literature via NCBI E-utilities and grades evidence under a strict rubric: `Grade A` (1.0) for statistically significant clinical findings, `Grade B` (0.5) for case reports/series, and `Grade C` (0.0) for unconfirmed or negative literature.

### 2.2 The Deterministic Safety Gate
If a drug–event pair has **no statistical signal in FAERS** ($S_{\text{FAERS}} = \text{NO\_SIGNAL}$), **Gate 1 unconditionally outputs `DO_NOT_ESCALATE`**. This prevents the system from generating false alarms based purely on theoretical literature discussions.

---

## 3. Work Completed So Far

1. **Core Pipeline Implementation:** Full end-to-end Python pipeline with dual orchestration modes:
   * **Fixed Pipeline Agent (`pharmaguard/agent/fixed_pipeline.py`):** Deterministic sequence (FAERS $\to$ ChEMBL $\to$ PubMed $\to$ Combine).
   * **ReAct LangGraph Agent (`pharmaguard/agent/react_agent.py`):** LLM-directed dynamic tool-use graph ([Yao et al., *ICLR*, 2023](https://arxiv.org/abs/2210.03629)).
2. **Disk-Backed Tool Cache (`pharmaguard/tools/cache.py`):** Schema-versioned persistent cache (`diskcache`, `v7`), enabling $100\%$ zero-cost, offline, reproducible evaluation.
3. **Epistemic Auditing & Confounding Modules:**
   * **Adversarial Mechanistic Leakage Critic (`pharmaguard/tools/chembl_tool.py`):** A secondary blind critic (inspired by the MARCH framework, [ACL 2026](https://arxiv.org/)) that detects if the primary agent leaked pre-trained regulatory memory.
   * **Confounding-Aware Discounting Tool (`pharmaguard/tools/confounding.py`):** Automatically discounts confounded signals caused by multi-drug regimens (e.g. polypharmacy in diabetic populations).
4. **Curated Benchmark Datasets:**
   * **Core Benchmark (15 pairs):** 7 Confirmed Positives (FDA Boxed Warnings), 5 Genuine Negative Controls, 3 Zero-Report Edge Cases with full regulatory citations.
   * **Secondary OMOP Pilot Benchmark (32 pairs):** Derived from the international OHDSI OMOP reference set ([Ryan et al., *Drug Safety*, 2013](https://doi.org/10.1007/s40264-013-0097-8)) across 4 clinical endpoints.
5. **Interactive Streamlit Evaluation Dashboard (`scripts/dashboard.py`):**
   * Complete 6-view web interface with dynamic Light/Dark theme switching, high-resolution metric cards, dense comparison tables, and Plotly confidence waterfall charts.
6. **Automated Verification Suite:**
   * 84/84 unit and integration tests passing (`pytest`).
   * Automated 1080p screenshot suite via Playwright (`scripts/dev/capture_screenshots.py`).

---

## 4. Experimental Results & Benchmarks

```
========================================================================================
                          SUMMARY OF EXPERIMENTAL RESULTS
========================================================================================
Core Benchmark (15 pairs):     Strict F1: 0.923 (Precision=1.000, Recall=0.857)
                               Lenient F1: 0.933 (Precision=0.875, Recall=1.000)
                               Specificity: 1.000 (8/8 negative controls cleared)
                               Spurious False Alarms: FP = 0

Single-Shot LLM Baseline:      Strict F1: 0.933 | Lenient F1: 0.824 | False Alarms: FP = 1

15-Fold LOO Stability:         Strict F1 = 0.923 ± 0.023 | Lenient F1 = 0.933 ± 0.019

ReAct Divergence Finding:      26.7% divergence (4/15 pairs) between unconstrained LLM
                               generative chat and deterministic safety gating

Leakage Critic Sensitivity:    100% Detection (4/4 leakage cases detected and redacted)

Metformin Confounding Fix:     Discounted confidence 0.400 -> 0.080 (DO_NOT_ESCALATE)

OMOP Pilot (32 pairs):         Specificity: 1.000 (16/16 negative controls cleared)
                               Lenient F1: 0.720 (9/16 true positives captured)
========================================================================================
```

### 4.1 Primary Benchmark Comparison (15 Core Pairs)

| Metric | PharmaGuard (Tool-Grounded) | Wilson 95% CI | Single-Shot LLM Baseline (No Tools) | Real-World Meaning |
|---|:---:|:---:|:---:|---|
| **Strict Precision** | **1.000** | [0.610, 1.000] | 0.875 | When PharmaGuard escalates, it is always a genuine safety signal. |
| **Strict Recall** | **0.857** (6/7) | [0.487, 0.974] | 1.000 | 6 of 7 positives escalated; 1 modulated to MONITOR. |
| **Strict Specificity** | **1.000** (8/8) | [0.676, 1.000] | 0.875 | **Zero false alarms** on known negative controls. |
| **Lenient Recall** | **1.000** (7/7) | [0.646, 1.000] | 1.000 | **100% signal capture** — no true safety hazard is missed. |
| **Lenient Specificity**| **0.875** (7/8) | [0.529, 0.978] | 0.625 | 7 of 8 negative controls safely cleared without human review. |
| **Over-Caution Rate** | **12.5%** (1/8) | [0.022, 0.471] | **25.0%** (2/8) | PharmaGuard produces half the clinician alert fatigue of raw LLMs. |

---

### 4.2 Four Illustrative Case Studies

1. **Liraglutide + Pancreatic Cancer (The Grounding Victory):**
   * *Background:* In 2013, historical safety concerns were raised, but joint FDA/EMA reviews in 2014 concluded no causal link ([Egan et al., *NEJM*, 2014](https://doi.org/10.1056/NEJMp1401876)).
   * *Baseline (Raw LLM):* Hallucinated an `ESCALATE` decision from outdated training memory.
   * *PharmaGuard:* Queried FAERS, saw 0 co-occurrences, fired Gate 1, and output **`DO_NOT_ESCALATE`**.
2. **Montelukast + Suicidal Ideation (Honest Uncertainty under Mechanistic Ambiguity):**
   * *Background:* FDA Boxed Warning issued in 2020 ([FDA DSC, 2020](https://www.fda.gov/drugs/drug-safety-and-availability/fda-requires-boxed-warning-about-serious-mental-health-side-effects-asthma-and-allergy-drug)), but the biological mechanism in the central nervous system remains unconfirmed.
   * *PharmaGuard:* Curated plausibility is honestly `LOW` (0.0). Output was modulated to **`MONITOR`** (confidence 0.664), correctly expressing caution without over-escalating unconfirmed biology.
3. **Metformin + Hypoglycaemia (Resolving Polypharmacy Confounding):**
   * *Background:* Appears in 9,300+ FAERS reports ($\text{PRR}=10.73$) because diabetic patients take insulin/sulfonylureas together with metformin.
   * *PharmaGuard:* The Confounding Tool identified concomitant diabetes medications and applied a $0.20$ discount factor, dropping confidence from $0.4000 \to 0.0800$ (**`DO_NOT_ESCALATE`**), eliminating the false positive.
4. **Citalopram + Gastrointestinal Haemorrhage (The OMOP Pilot Finding):**
   * *Background:* SSRIs inhibit platelet serotonin reuptake, increasing bleeding risk (plausibility `HIGH`).
   * *PharmaGuard:* Because millions of patients take SSRIs, massive denominator prescription volume diluted the FAERS PRR point estimate to $1.904$ (below the static $2.0$ cutoff). This tripped Gate 1, uncovering a clear boundary condition of static thresholding.

---

## 5. Why is PharmaGuard Novel & Publishable?

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE 5 PILLARS OF NOVELTY                                   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. First Multi-Source Evidence-Grounded Agent for Pharmacovigilance Triage             │
│ 2. Empirical Discovery of "Parametric Regulatory Leakage" in Medical LLMs              │
│ 3. Novel Blinded Maker-Checker Adversarial Critic (MARCH Audit Pattern)                │
│ 4. Empirical Quantification of Generative vs. Deterministic Divergence (26.7%)         │
│ 5. Methodological Benchmark with Non-Overfitted, Honest Boundary Disclosures            │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **First Multi-Source PV Agent Architecture:** While prior works examine single-tool RAG or theoretical multi-agent setups ([Venugopal, *J Med AI*, 2026](https://doi.org/10.21037/jmai-24-118); [PSEBench, 2026](https://arxiv.org/abs/2606.05463)), PharmaGuard is the first concrete, evaluated system combining live FAERS disproportionality, ChEMBL target pharmacology, and PubMed literature grading into a deterministic safety-gated framework.
2. **Discovery of "Parametric Regulatory Leakage":** We experimentally proved that when medical LLMs claim to deduce biochemical plausibility, they often cheat by recalling FDA Boxed Warnings from pre-training memory.
3. **Blinded Adversarial Auditing Framework:** We designed an independent maker-checker critic that inspects rationales without knowing drug/event names, achieving 100% detection of regulatory contamination—a transferable auditing framework for healthcare AI.
4. **Empirical Justification for Deterministic Rules:** Proved that unconstrained ReAct agents diverge from safety rules in $26.7\%$ of cases, demonstrating why clinical AI requires deterministic mathematical gating.
5. **Target Publication Venues:**
   * **Conferences:** **IEEE BIBM 2026** (IEEE Intl. Conf. on Bioinformatics and Biomedicine), **ACM CHIL** (Conference on Health, Inference, and Learning), **AMIA Annual Symposium**.
   * **Journals:** **JAMIA Open** (Oxford Academic), **Journal of Biomedical Informatics (JBI)**, **Drug Safety** (Springer/ISoP).

---

## 6. Challenges Encountered & How We Addressed Them

| Challenge | Real-World Impact | How PharmaGuard Solved It |
|---|---|---|
| **1. LLM Regulatory Memory Leakage** | Models recall FDA warnings instead of evaluating true biochemistry. | Built the blinded Adversarial Leakage Critic (MARCH pattern) to detect and redact non-mechanistic text. |
| **2. Polypharmacy Confounding** | Drug combinations artificially inflate FAERS reporting ratios ($\text{PRR} > 10.0$). | Implemented the Confounding Assessment Tool to discount co-prescribed medication artifacts. |
| **3. Chronic Medication Denominator Dilution** | High prescription volume dilutes PRR point estimates below $2.0$ for chronic drugs (e.g., SSRIs). | Documented this finding honestly on the OMOP benchmark without post-hoc threshold cheating; planned dynamic CI-based gating. |

---

## 7. Next Phase Roadmap & Timeline

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            NEXT PHASE ROADMAP & MILESTONES                              │
├──────────────────────┬──────────────────────────────────────────────────────────────────┤
│ Phase 4.1 (Week 1–2) │ Dynamic Statistical Gating (Lower 95% CI Bound / Bayesian EBGM)  │
│ Phase 4.2 (Week 3–4) │ MedDRA Ontology Canonicalization Layer (LLT -> PT Normalization) │
│ Phase 4.3 (Week 5–6) │ External Clinical Pharmacologist Expert Validation Protocol      │
│ Phase 4.4 (Week 7–8) │ Conference Manuscript Drafting & Final Capstone Defense Deck     │
└──────────────────────┴──────────────────────────────────────────────────────────────────┘
```

1. **Dynamic Disproportionality Gating:** Upgrade the static $\text{PRR} \ge 2.0$ cutoff to evaluate the 95% lower confidence interval ($\text{PRR}_{\text{lower\_ci}} > 1.0$) or Empirical Bayes Geometric Mean (EBGM, [Dumouchel, 1999](https://doi.org/10.1080/00031305.1999.10474456)) to rescue chronic diluted signals.
2. **MedDRA Term Canonicalization Layer:** Automatically map lay symptoms and British spellings (e.g. *hypoglycaemia*) to official MedDRA Preferred Terms (PTs) via biomedical ontology resolution.
3. **Clinical Pharmacologist Review Protocol:** Prepare a blinded validation protocol for external clinical pharmacologists to formally review our biological plausibility scores.
4. **Conference Manuscript Drafting:** Complete full academic paper drafting targeting **IEEE BIBM 2026** or **ACM CHIL**.

---

## 8. Specific Guidance & Discussion Points for Meeting

We would appreciate Dr. Arya's guidance on the following four points during our in-person discussion:

1. **Statistical Gating Formulation:** Advice on transitioning from static $\text{PRR} \ge 2.0$ cutoffs to confidence interval lower bounds ($\text{PRR}_{\text{lower\_ci}} > 1.0$) or Bayesian shrinkage for high-volume chronic drugs.
2. **Dual-Metric Evaluation Framing:** Validation of our Strict vs. Lenient evaluation framework for our final capstone defense.
3. **Conference Target Selection:** Recommendations on the most suitable submission venue (IEEE BIBM, ACM CHIL, or AMIA).
4. **Defense Presentation Structure:** Guidance on structuring our final 15-minute slide deck and live dashboard demonstration.

---

## 9. Comprehensive References & Research Paper Links

### Foundational Agentic AI & Medical LLM Architectures
1. **ReAct Pattern:** Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *International Conference on Learning Representations (ICLR 2023)*. [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)
2. **Clinical LLM Hallucination Assurance:** Omar, M., et al. (2025). Multi-model assurance analysis showing large language models are highly vulnerable to adversarial hallucination attacks during clinical decision support. *Communications Medicine*, 5(1), 330. [DOI: 10.1038/s43856-025-00787-8](https://doi.org/10.1038/s43856-025-00787-8)
3. **Agentic AI in Pharmacovigilance:** Venugopal, R. (2026). Large language models-powered agentic AI design and implementation in pharmacovigilance — a narrative review. *Journal of Medical Artificial Intelligence*. [DOI: 10.21037/jmai-24-118](https://doi.org/10.21037/jmai-24-118)
4. **Patient Safety Incident Triage Benchmark (PSEBench):** PSEBench: A Controllable and Verifiable Benchmark for Evaluating LLMs in Patient Safety Event Triage. *arXiv:2606.05463* (2026). [arXiv:2606.05463](https://arxiv.org/abs/2606.05463)
5. **Medical Multi-Agent Teamwork Protocols:**
   * Kim, Y., et al. (2024). MDAgents: An Adaptive Collaboration of LLMs for Medical Decision-Making. *NeurIPS 2024*. [arXiv:2404.15155](https://arxiv.org/abs/2404.15155)
   * Mishra, S., Arvan, M., & Zalake, M. (2025). TeamMedAgents: Structured Teamwork Protocols for Medical LLM Agents. *arXiv:2501.04250*. [arXiv:2501.04250](https://arxiv.org/abs/2501.04250)

### Pharmacovigilance Disproportionality Algorithms & Reference Datasets
6. **Proportional Reporting Ratio (PRR):** Evans, S. J., Waller, P. C., & Davis, S. (2001). Use of proportional reporting ratios (PRRs) for signal generation from spontaneous adverse drug reaction reports. *Pharmacoepidemiology and Drug Safety*, 10(6), 483–486. [DOI: 10.1002/pds.677](https://doi.org/10.1002/pds.677)
7. **Disproportionality Algorithm Comparisons (PRR, ROR, BCPNN):** van Puijenbroek, E. P., Bate, A., Leufkens, H. G., Lindquist, M., Orre, R., & Egberts, A. C. (2002). A comparison of different statistical methods for disproportionality analysis within a spontaneous reporting database. *Pharmacoepidemiology and Drug Safety*, 11(1), 3–10. [DOI: 10.1002/pds.688](https://doi.org/10.1002/pds.688)
8. **Bayesian Data Mining & Multi-Item Gamma Poisson Shrinker (MGPS / EBGM):** DuMouchel, W. (1999). Bayesian Data Mining in Large Frequency Tables, with an Application to the FDA Spontaneous Reporting System. *The American Statistician*, 53(3), 177–190. [DOI: 10.1080/00031305.1999.10474456](https://doi.org/10.1080/00031305.1999.10474456)
9. **OMOP Reference Dataset Benchmark:** Ryan, P. B., Schuemie, M. J., Welebob, E., Duke, J., Valentine, S., & Hartzema, A. G. (2013). Defining a Reference Set to Support Evaluation of Methods for Disproportionality Analysis in Spontaneous Reporting Systems. *Drug Safety*, 36(1), 33–47. [DOI: 10.1007/s40264-013-0097-8](https://doi.org/10.1007/s40264-013-0097-8) / [OHDSI MethodEvaluation Repository](https://github.com/OHDSI/MethodEvaluation)
10. **OMOP Reference Set Critical Appraisal:** Hoffman, K. B., Dimbil, M., Erdman, C. B., Tatonetti, N. P., & Overhage, J. M. (2016). The OMOP Reference Set: An Honest Appraisal. *Drug Safety*, 39(8), 719–725. [DOI: 10.1007/s40264-016-0428-1](https://doi.org/10.1007/s40264-016-0428-1)

### Public Biomedical Databases & Regulatory Actions
11. **openFDA Drug Adverse Event API:** U.S. Food and Drug Administration. [openFDA Drug Event Endpoint Documentation](https://open.fda.gov/apis/drug/event/)
12. **ChEMBL Bioactivity & Target Pharmacology Database:** Gaulton, A., et al. (2019). The ChEMBL database in 2019. *Nucleic Acids Research*, 47(D1), D930–D940. [DOI: 10.1093/nar/gky1075](https://doi.org/10.1093/nar/gky1075) / [ChEMBL Portal](https://www.ebi.ac.uk/chembl/)
13. **NCBI PubMed E-Utilities API:** Sayers, E. (2010). A General Introduction to the E-utilities. *NCBI Bookshelf*. [NCBI E-utilities Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
14. **Montelukast FDA Boxed Warning (March 2020):** U.S. FDA Drug Safety Communication. [FDA Requires Boxed Warning About Serious Mental Health Side Effects for Asthma and Allergy Drug Montelukast](https://www.fda.gov/drugs/drug-safety-and-availability/fda-requires-boxed-warning-about-serious-mental-health-side-effects-asthma-and-allergy-drug)
15. **Liraglutide FDA/EMA Joint Assessment (2014):** Egan, A. G., et al. (2014). Pancreatic Safety of Incretin-Based Drugs — FDA and EMA Assessment. *New England Journal of Medicine*, 370(9), 794–797. [DOI: 10.1056/NEJMp1401876](https://doi.org/10.1056/NEJMp1401876)

---
*End of Project Brief — Group 07, IIIT Allahabad (September 2026)*
