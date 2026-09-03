# PharmaGuard: Project Brief & Progress Report

**Course:** B.Tech Major Project (7th Semester) — Department of Information Technology  
**Institution:** Indian Institute of Information Technology, Allahabad (IIIT Allahabad)  
**Project Group:** Group 07  
**Project Title:** PharmaGuard: A Tool-Grounded Agentic AI Architecture for Pharmacovigilance Signal Triage  
**Students:**  
* Krishna Sikheriya (Roll No: **IIT2023139**) [Lead]  
* Lokesh  
* Naitik  
**Project Supervisor:** Dr. Nikhilanand Arya, Assistant Professor, Department of Information Technology  
**Date:** September 2026  
**Repository & Codebase:** [https://github.com/Krishna200608/PharmaGuard](https://github.com/Krishna200608/PharmaGuard) (84/84 Automated Tests Passing)  

---

## 1. Executive Summary & Problem Statement

### 1.1 The Real-World Challenge
When a medicine is approved and prescribed to millions of patients, postmarketing surveillance (**Pharmacovigilance**) continuously monitors for unexpected or rare adverse reactions. Spontaneous reporting systems such as the **FDA Adverse Event Reporting System (FAERS)** receive over 2 million safety reports each year. 

Safety teams face a severe **triage bottleneck**: they must rapidly distinguish between:
1. **Real, dangerous safety signals** requiring immediate regulatory warnings or label updates (e.g., drug-induced liver failure or cardiac arrhythmias).
2. **Benign statistical noise or co-medication artifacts** (e.g., a diabetic patient on metformin experiencing hypoglycemia primarily because they also take insulin).

Currently, this triage step is largely manual, labor-intensive, and prone to significant delays.

### 1.2 Why Standard AI (ChatGPT / Raw LLMs) Cannot Be Used Directly
Large Language Models (LLMs) are often proposed to automate clinical triage, but ungrounded foundation models suffer from three disqualifying failure modes:
* **Hallucination & Fabricated Associations:** Recent clinical evaluation studies ([Omar et al., *Communications Medicine*, 2025](https://doi.org/10.1038/s43856-025-00787-8)) found that leading LLMs elaborate on planted false clinical details in up to 83% of edge-case scenarios without external data grounding.
* **Temporal Confusion:** An LLM may recall from its pre-training data that a historical safety concern was raised in 2013, failing to recognize that health authorities formally investigated and cleared it in 2014.
* **Uncalibrated Confidence:** A raw LLM cannot provide a mathematically verifiable confidence score—it merely generates subjective, self-reported text probability.

### 1.3 The PharmaGuard Solution
PharmaGuard is a **tool-grounded, multi-source agentic AI architecture**. Instead of permitting the AI to answer from parametric memory, PharmaGuard strictly constrains the model to fetch and verify real-time data from **three independent biomedical databases** before combining the findings using a **deterministic mathematical formula** to produce an auditable decision: **ESCALATE**, **MONITOR**, or **DO_NOT_ESCALATE**.

### 1.4 Project Origin & Research Pivot History
The project executed an intentional and documented research pivot in August 2026 from an earlier multi-agent oncology tumor-board simulation concept ("OncoSwarm"). Landscape research revealed that the oncology tumor-board niche had already been saturated by a published, deployed Stanford system. Consequently, the team pivoted to the unaddressed, high-impact problem of verifiable, tool-grounded pharmacovigilance signal triage.

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
If a drug–event pair has **no statistical signal in FAERS** ($S_{\text{FAERS}} = \text{NO\_SIGNAL}$), **Gate 1 unconditionally outputs `DO_NOT_ESCALATE`** (§4). This prevents the system from generating false alarms based purely on speculative literature discussions or theoretical biochemistry.

---

## 3. Work Completed So Far

1. **Core Pipeline Implementation:** Full end-to-end Python pipeline with dual orchestration modes:
   * **Fixed Pipeline Agent (`pharmaguard/agent/fixed_pipeline.py`):** Deterministic sequence (FAERS $\to$ ChEMBL $\to$ PubMed $\to$ Combine) (§8).
   * **ReAct LangGraph Agent (`pharmaguard/agent/react_agent.py`):** LLM-directed dynamic tool-use graph with recursion guardrails and state isolation ([Yao et al., *ICLR*, 2023](https://arxiv.org/abs/2210.03629)) (§9, §9.1).
2. **Disk-Backed Tool Cache (`pharmaguard/tools/cache.py`):** Schema-versioned persistent cache (`diskcache`, `v7`), enabling $100\%$ zero-cost, offline, reproducible evaluation (§3, §6).
3. **Epistemic Auditing & Novelty Modules:**
   * **Adversarial Mechanistic Leakage Critic (`pharmaguard/tools/chembl_tool.py`):** A secondary blind critic (inspired by the MARCH framework, ACL 2026) that evaluates rationales with zero exposure to drug/event names, achieving 100% detection of leaked regulatory memory (§27).
   * **Confounding-Aware Discounting Tool (`pharmaguard/tools/confounding.py`):** Automatically detects polypharmacy artifacts (e.g. co-prescribed diabetes medications) and applies grounded discount multipliers (§28).
   * **Cross-Source Evidence Agreement Metric:** Deterministic concordance heuristic classifying pairs as `CONCORDANT` or `DISCORDANT` ($\max \ge 0.66 \land \min \le 0.33$) (§26).
   * **Leave-One-Out (LOO) Stability Analysis:** 15-fold cross-validation verifying benchmark stability without pipeline re-execution (§29).
4. **Curated Benchmark Datasets:**
   * **Core Benchmark (15 pairs):** 7 Confirmed Positives (FDA Boxed Warnings), 5 Genuine Negative Controls, 3 Zero-Report Edge Cases with full regulatory citations (§2, §21, §22).
   * **Secondary OMOP Pilot Benchmark (32 pairs):** Derived from the international OHDSI OMOP reference set ([Ryan et al., *Drug Safety*, 2013](https://doi.org/10.1007/s40264-013-0097-8)) across 4 clinical endpoints (§31).
5. **Interactive Streamlit Evaluation Dashboard (`scripts/dashboard.py`):** Complete 6-view web interface with dynamic Light/Dark theme switching, metric cards, dense tables, and Plotly confidence waterfall charts.
6. **Automated Verification Suite:** 84/84 unit and integration tests passing (`pytest`) and automated 1080p Playwright screenshot suite (`scripts/dev/capture_screenshots.py`).

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

15-Fold LOO Stability:         Strict F1 = 0.9226 ± 0.0225 | Lenient F1 = 0.9330 ± 0.0192

Multi-Source Ablation:         Strict F1 = 0.000 across all single-source conditions,
                               confirming genuine multi-source fusion dependency

ReAct Divergence Finding:      26.7% divergence (4/15 pairs) between unconstrained LLM
                               generative chat and deterministic safety gating

Leakage Critic Sensitivity:    100% Detection (4/4 leakage cases detected and isolated)

Metformin Confounding Fix:     Discounted confidence 0.400 -> 0.080 (DO_NOT_ESCALATE)

OMOP Pilot (32 pairs):         Specificity: 1.000 (16/16 negative controls cleared)
                               Lenient F1: 0.720 (9/16 true positives captured)
========================================================================================
```

### 4.1 Primary Benchmark Comparison (15 Core Pairs)

| Metric | PharmaGuard (Tool-Grounded) | Wilson 95% CI | Single-Shot LLM Baseline (No Tools) | Clinical Significance |
|---|:---:|:---:|:---:|---|
| **Strict Precision** | **1.000** | [0.610, 1.000] | 0.875 | When PharmaGuard escalates, it is always a genuine safety signal. |
| **Strict Recall** | **0.857** (6/7) | [0.487, 0.974] | 1.000 | 6 of 7 positives escalated; 1 modulated to MONITOR. |
| **Strict Specificity** | **1.000** (8/8) | [0.676, 1.000] | 0.875 | **Zero false alarms** on known negative controls. |
| **Strict F1-Score** | **0.923** | [0.727, 1.000]* | 0.933 | Harmonic mean under strict gating. |
| **Lenient Recall** | **1.000** (7/7) | [0.646, 1.000] | 1.000 | **100% signal capture** — no true safety hazard is missed. |
| **Lenient Specificity**| **0.875** (7/8) | [0.529, 0.978] | 0.625 | 7 of 8 negative controls safely cleared without human review. |
| **Lenient F1-Score** | **0.933** | [0.769, 1.000]* | 0.824 | Harmonic mean under lenient scoring. |
| **Over-Caution Rate** | **12.5%** (1/8) | [0.022, 0.471] | **25.0%** (2/8) | PharmaGuard produces half the clinician alert fatigue of raw LLMs. |

*\*Note: Bootstrap 95% CI reported for F1 scores ($B=1000$, seed=42). See DECISIONS.md §16 for full confusion matrices.*

### 4.2 Multi-Source Fusion Dependency Finding
Ablation experiments across 9 conditions (`faers_removed`, `pubmed_removed`, `chembl_removed`, `faers_only`, `pubmed_only`, `chembl_only`) demonstrated that **Strict F1 drops to 0.000 across every ablated condition** (§30 item 4). This proves that no individual source alone can reproduce triage performance, confirming genuine multi-source fusion dependency.

### 4.3 Four Illustrative Case Studies
1. **Liraglutide + Pancreatic Cancer (The Grounding Victory):** Joint FDA/EMA reviews in 2014 concluded no causal link ([Egan et al., *NEJM*, 2014](https://doi.org/10.1056/NEJMp1401876)). The ungrounded baseline escalated on outdated memory; PharmaGuard checked FAERS, saw 0 co-occurrences, fired Gate 1, and output **`DO_NOT_ESCALATE`** (§13).
2. **Montelukast + Suicidal Ideation (Honest Uncertainty under Mechanistic Ambiguity):** FDA Boxed Warning exists ([FDA DSC, 2020](https://www.fda.gov/drugs/drug-safety-and-availability/fda-requires-boxed-warning-about-serious-mental-health-side-effects-asthma-and-allergy-drug)), but the central nervous system mechanism is biologically unconfirmed. Plausibility is honestly `LOW` (0.0). Output was modulated to **`MONITOR`** (confidence 0.664), correctly expressing caution (§14, §16).
3. **Metformin + Hypoglycaemia (Resolving Polypharmacy Confounding):** Appears in 9,300+ FAERS reports ($\text{PRR}=10.73$) because diabetic patients take insulin alongside metformin. The Confounding Tool identified concomitant medications and applied a $0.20$ discount factor, dropping confidence from $0.4000 \to 0.0800$ (**`DO_NOT_ESCALATE`**), eliminating the sole lenient false positive (§28).
4. **Citalopram + Gastrointestinal Haemorrhage (The OMOP Pilot Finding):** SSRI antidepressant with `HIGH` biological plausibility. High prescription volume diluted the FAERS PRR point estimate to $1.904$ (below 2.0), tripping Gate 1 and exposing the boundary of static thresholding (§31).

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

1. **First Multi-Source PV Agent Architecture:** While prior works examine single-tool RAG or theoretical multi-agent setups ([Venugopal, *J Med AI*, 2026](https://doi.org/10.21037/jmai-24-118); [PSEBench, 2026](https://arxiv.org/abs/2606.05463)), PharmaGuard is the first concrete, evaluated system combining live FAERS disproportionality, ChEMBL target pharmacology, and PubMed literature grading into a deterministic safety-gated framework (§23).
2. **Discovery of "Parametric Regulatory Leakage":** We experimentally proved that when medical LLMs claim to deduce biochemical plausibility, they frequently cheat by recalling FDA Boxed Warnings from pre-training memory (§16, §17, §19).
3. **Blinded Adversarial Auditing Framework:** We designed an independent maker-checker critic (MARCH pattern) that inspects rationales without drug/event names, achieving 100% detection of regulatory contamination (§27).
4. **Empirical Justification for Deterministic Rules:** Proved that unconstrained ReAct agents diverge from safety rules in $26.7\%$ of cases ($4/15$), demonstrating why clinical AI requires deterministic mathematical gating (§24).
5. **Target Publication Venues:**
   * **Conferences:** **IEEE BIBM 2026** (IEEE Intl. Conf. on Bioinformatics and Biomedicine), **ACM CHIL** (Conference on Health, Inference, and Learning), **AMIA Annual Symposium**.
   * **Journals:** **JAMIA Open** (Oxford Academic), **Journal of Biomedical Informatics (JBI)**, **Drug Safety** (Springer/ISoP).

---

## 6. Challenges Encountered & Methodological Resolutions

The following six genuine technical and methodological challenges were encountered, investigated, and systematically resolved, demonstrating engineering maturity and scientific discipline:

| Challenge | Nature of the Issue | Methodological Resolution | Key Citation |
|---|---|---|:---:|
| **1. Rubric Revision with Foreknowledge** | Attempted to upgrade Montelukast/Albuterol to MODERATE, inflating recall to 1.000. | Caught as biased foreknowledge; reverted to v1.0 ratings and instituted strict anti-overfitting policy prohibiting post-hoc threshold/rubric mutations. | [`§15`](file:///d:/Research%20Project/PharmaGuard/docs/context/DECISIONS.md#L101), [`§18`](file:///d:/Research%20Project/PharmaGuard/docs/context/DECISIONS.md#L196) |
| **2. MARCH Citation Precision** | Early notes cited multi-agent review patterns informally. | Audited and standardized to the formal MARCH framework (ACL 2026) blinded information-asymmetry verification pattern. | [`§27`](file:///d:/Research%20Project/PharmaGuard/docs/context/DECISIONS.md#L353) |
| **3. FAERS-Ablation Gate Conflation** | Zeroing FAERS artificially fired Gate 1 (NO_SIGNAL) on 8/15 pairs as a mathematical artifact. | Diagnosed mathematical conflation and created an explicit gate-bypassed analytical view to isolate true linear formula weight contributions. | [`§30 (4)`](file:///d:/Research%20Project/PharmaGuard/docs/context/DECISIONS.md#L486) |
| **4. OMOP Negative-Control Collisions** | Questions arose regarding whether OMOP negative controls contained true literature associations. | Verified directly against primary Ryan et al. (2013) definition tables and FDA labels, confirming all 16 negative controls are clean. | [`§31`](file:///d:/Research%20Project/PharmaGuard/docs/context/DECISIONS.md#L508) |
| **5. ChEMBL Lookup Table Coverage Gap** | Scaling to 32 OMOP drugs risked zero-score fallbacks due to missing MoA entries. | Queried official ChEMBL REST API to curate verified mechanisms for all 32 drugs, expanding lookup from 18 to 50 drugs prior to evaluation. | [`§31`](file:///d:/Research%20Project/PharmaGuard/docs/context/DECISIONS.md#L508) |
| **6. Clinical Ground-Truth Curation** | Clinical safety lacks absolute mathematical ground truth; MedDRA coding shifts occur. | Documented all boundaries with primary FDA/EMA citations in `GROUND_TRUTH_CANDIDATES.md` and resolved MedDRA spelling variants (e.g. `HYPOGLYCAEMIA`). | [`§21`](file:///d:/Research%20Project/PharmaGuard/docs/context/DECISIONS.md#L212), [`§30 (6)`](file:///d:/Research%20Project/PharmaGuard/docs/context/DECISIONS.md#L492) |

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

1. **Academic Paper Manuscript Drafting:** Currently gated on supervisor review and explicit sign-off per DECISIONS.md §25 standing instructions. We are awaiting Dr. Arya's approval to proceed with formal drafting targeting **IEEE BIBM 2026** or **ACM CHIL**.
2. **Dynamic Disproportionality Gating:** Upgrade the static $\text{PRR} \ge 2.0$ cutoff to evaluate the 95% lower confidence interval ($\text{PRR}_{\text{lower\_ci}} > 1.0$) or Empirical Bayes Geometric Mean (EBGM, [Dumouchel, 1999](https://doi.org/10.1080/00031305.1999.10474456)) to rescue chronic diluted signals without introducing false positives (§31).
3. **MedDRA Term Canonicalization Layer:** Automatically map colloquial symptoms and British spellings (e.g. *hypoglycaemia*) to official MedDRA Preferred Terms (PTs) via biomedical ontology resolution (§21, §30).
4. **Clinical Pharmacologist Review Protocol:** Prepare a blinded validation protocol for external clinical pharmacologists to formally review our biological plausibility ratings (§20, §30).

---

## 8. Specific Guidance & Discussion Points for Meeting

We respectfully request Dr. Arya's guidance on the following four specific open research considerations:

1. **Publication Venue & Manuscript Scope:** Does Sir recommend targeting a computer science / biomedical informatics conference (e.g., IEEE BIBM 2026, ACM CHIL) or a medical informatics journal (e.g., JAMIA Open, Journal of Biomedical Informatics)?
2. **Threshold Formulation for Chronic Signals:** In light of the OMOP pilot finding (§31), does Sir advise introducing dynamic confidence interval gating ($\text{PRR}_{\text{lower\_ci}} > 1.0$) for the final manuscript, or presenting the static threshold limitation as a standalone methodological contribution?
3. **Secondary Benchmark Cohort Size:** Is the current 32-pair OMOP secondary pilot sufficient to substantiate our external validity claims for an undergraduate capstone, or would Sir recommend scaling to a 64-pair cohort?
4. **Defense Presentation Structure:** Guidance on structuring our final 15-minute 16:9 widescreen presentation deck and live dashboard demonstration.

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
