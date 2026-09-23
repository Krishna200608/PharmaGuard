# PharmaGuard — Weekly Progress Update #2
### Multi-Scale Benchmark Expansion (165 Pairs), Local LLM Integration, Conference Paper Manuscript, and Interactive Dashboard

**Submitted to:** Dr. Nikhilanand Arya  
**Group 07:** Krishna Sikheriya (IIT2023139), Lokesh Bawariya, Naitik Jain  
**Date:** September 2026  

---

## 1. Feedback & Guidance from Previous Meeting (Recap)

In our previous meeting and update, we established the following key directions:

1. **Scoring-Inert Clinical Context:** Following our 40-pair test of the indication concordance layer (which yielded a low-power null result of 4/40 triggers without metric movement), we agreed to maintain the disease-context layer as an **explicit, scoring-inert provenance flag** on reports rather than applying ungrounded numerical scalar penalties.
2. **Scale & Rigorous Benchmarking:** You advised moving beyond small-sample toy evaluation (15 pairs) to test whether PharmaGuard's triage gates and tri-source fusion hold up under large-scale, real-world postmarketing surveillance conditions.
3. **Conference Paper Drafting:** We received the go-ahead to transition our literature review, methodology, and empirical findings into a formal academic manuscript targeting IEEE / ACM / JAMIA health informatics venues.

This document summarizes our major progress across all three directives.

---

## 2. Multi-Scale Benchmark Expansion (165 Total Pairs Evaluated)

To rigorously stress-test the system, we expanded evaluation from our original 15-pair prototype to **three stratified benchmark cohorts totaling 165 curated drug–event pairs** (with 151 distinct searchable presets):

| Benchmark Cohort | Cohort Size ($N$) | Cohort Composition & Focus | Key Findings & Metrics |
|---|---|---|---|
| **1. Core Showcase Cohort** | **15 Pairs** | 7 confirmed positive toxicities + 8 negative controls. Frozen Sprint 3 baseline. | **Strict $F_1 = 0.9231$**, **Lenient $F_1 = 0.9333$**. Halves clinician over-caution rate from 25.0% down to 12.5% vs. ungrounded LLM. |
| **2. Top Prescribed Blockbusters** | **50 Pairs** | 25 high-recognition, high-mortality FDA Boxed Warnings vs. 25 negative controls across Statins, ACEi/ARBs, Antibiotics, Antidepressants, Opioids, and Anticonvulsants. | **Lenient $F_1 = 0.9388$**, **Recall = 92.0%** (23/25 Boxed Warnings caught), **Specificity = 96.0%** (24/25 cleared), **Strict Precision = 1.0000** (10/10). |
| **3. OMOP Expanded Reference Standard** | **100 Pairs** | 50 positive vs. 50 negative controls from the OHDSI OMOP gold standard across 4 acute organ failure phenotypes: Acute Liver Injury, Acute Renal Failure, Myocardial Infarction, Upper GI Bleeding. | **Strict Specificity = 1.0000** (50/50 negative controls cleared; zero false alarms), **Lenient Specificity = 0.9800** (49/50), **Lenient Precision = 0.9333** (14/15). |

### Key Scientific Discovery: "PRR Denominator Dilution"
While evaluating the 100-pair OMOP reference standard, we made an important empirical observation that directly explains a major challenge in modern pharmacovigilance:
- **The Observation:** On chronic, high-utilization medications (such as long-term statins or PPIs), raw disproportionality metrics like PRR often drop below the classical Evans threshold of $2.0$, despite significant clinical literature and confirmed biological mechanisms.
- **Why this happens:** When tens of millions of patients take a drug continuously, the sheer volume of incidental background reports inflates the denominator of the 2x2 contingency table, artificially depressing the PRR statistic.
- **Why this matters for PharmaGuard:** A purely statistical tool will drop these real signals. However, PharmaGuard's **tri-source fusion** uses ChEMBL receptor pharmacology and PubMed literature grading to prevent them from being discarded, routing them safely to `MONITOR` rather than `DO_NOT_ESCALATE`. This provides strong empirical justification for our dual-metric (Strict vs. Lenient) evaluation framework in the paper.

---

## 3. Zero-Cost, Unmetered Local LLM Integration (Ollama `qwen2.5:7b`)

Executing 165 multi-source pipeline runs against commercial cloud APIs (like Google Gemini Flash) introduced severe rate-limiting bottlenecks (e.g., 15 RPM free-tier ceilings) and recurring API costs.

**What we built:**
- We integrated the **Ollama local inference daemon (`qwen2.5:7b`)** directly into PharmaGuard's LLM factory layer.
- Local LLM inference runs 100% on-device via `http://localhost:11434`, with unmetered throughput, zero API fees, and complete offline privacy.
- We evaluated the entire 50-pair Blockbuster benchmark and 100-pair OMOP benchmark completely locally through Ollama, achieving identical deterministic schema extraction without dropping a single call.
- The system retains seamless dual-backend support: users can switch between local Ollama and Cloud Gemini Flash via a single configuration toggle.

---

## 4. Complete Academic Conference Paper Manuscript (Drafted)

We have completed the full first-draft manuscript of our conference paper, targeted for submission to **IEEE BIBM (International Conference on Bioinformatics and Biomedicine)**, **ACM CHIL (Conference on Health, Inference, and Learning)**, or **JAMIA**:

- **Location:** `docs/paper/PharmaGuard_Conference_Paper.md` (336 lines, ~8,500 words).
- **Structure (9 Formal Sections):**
  1. **Title & Abstract:** Formulates the postmarketing signal triage problem, triage bottleneck, and summary of 165-pair empirical results.
  2. **Introduction:** Contrasts spontaneous reporting realities against pre-approval RCT limitations; details the failure modes of ungrounded LLMs (hallucinated confidence, historical regulatory confusion, parametric leakage).
  3. **Related Work:** Thoroughly positions PharmaGuard against Evans PRR/ROR statistical baselines, modern agentic architectures (ReAct, PSEBench, DruGagent), and EHR-dependent causal AI (Toonsi et al.), highlighting our public-API accessibility advantage.
  4. **System Architecture & Methodology:** Mathematical definitions of the closed-form confidence fusion formula, Gate 1 empirical safety stop, ChEMBL MoA retrieval, PubMed clinical rubric v1.0, and the scoring-inert ATC indication isolation wall.
  5. **Experimental Setup:** Master table of all three benchmark cohorts ($N=165$), ground-truth curation standards, and the dual-metric evaluation framework (Strict vs. Lenient).
  6. **Results:** Comprehensive tables reporting TP, FP, TN, FN, Precision, Recall, Specificity, and $F_1$ with exact **Wilson 95% Confidence Intervals** across all three cohorts.
  7. **Clinical Case Studies:** In-depth case walkthroughs on *Montelukast* (suicidal ideation), *Metformin* (lactic acidosis vs. hypoglycaemia polypharmacy), *Lisinopril* (cough), and *Albuterol* (paradoxical bronchospasm).
  8. **Discussion & Limitations:** Analysis of PRR denominator dilution, the MARCH adversarial critic anti-leakage audit, and current boundary conditions.
  9. **Conclusion & Reproducibility:** Availability statement for code, datasets, Docker deployment, and Streamlit evaluation dashboard.

---

## 5. Evaluation Dashboard Multi-Cohort Integration & Live Signal Triage

We significantly upgraded the Streamlit evaluation dashboard (`scripts/dashboard.py` / `dashboard/app.py` running at `http://localhost:8501`):

1. **Global Multi-Cohort Switcher:**
   - Added a top-bar segmented control switcher allowing reviewers to dynamically toggle the dashboard across:
     - `Core Showcase [15]`
     - `Top Prescribed [50]`
     - `OMOP Expanded [100]`
   - Switching the cohort instantly re-renders the Overview KPI cards, Confusion Matrices, Metric Breakdown tables, and Per-Pair evidence drill-downs.

2. **Searchable Live Signal Triage Playground:**
   - Implemented a dedicated Live Triage tab loaded with **151 searchable benchmark presets** alongside support for arbitrary custom drug–event entry.
   - Executes live, real-time multi-source data extraction across openFDA FAERS, ChEMBL MoA targets, PubMed abstracts, and local Ollama inference with live step-by-step progress tracking.

3. **Methodology Probes & Auditing:**
   - Displays the Adversarial Critic probe audit table (MARCH framework pattern) showing 4/4 detection of parametric training-data leakage.
   - Visualizes side-by-side evidence waterfalls for polypharmacy confounding de-biasing.

4. **Engineering Fixes & UI Polish:**
   - Replaced raw emojis with official Google Material Symbols across all tabs and badges.
   - Fixed a `NoneType` caching exception in `ChemblTool` and `PubMedTool` when disk caching is toggled off.
   - Added automatic module hot-reloading (`importlib.reload`) in `live_triage.py` to prevent persistent Streamlit memory from retaining stale bytecode.
   - Verified that all **242 / 242 unit tests** pass with 100% green status via pytest.

---

## 6. Capstone Presentation Deck Synchronization

We fully synchronized the mid/end-semester capstone presentation materials with the 165-pair benchmark scale:

- **Slide Outline (`docs/presentation/End_Semester_Slide_Content.md`):** Updated the 18-slide presentation deck to reflect the multi-cohort evaluation, PRR denominator dilution findings, local Ollama integration, and live dashboard demo flow.
- **Delivery Notes (`docs/presentation/SLIDE_DECK_NOTES.md`):** Updated presenter cue cards, timing checkpoints (15-minute budget), and anticipated defense/viva defense questions (e.g., explaining why OMOP strict recall is lower due to chronic utilization, and defending why the indication concordance layer is scoring-inert).

---

## 7. Summary of Completed Milestones

| Target Area | Status | Deliverables / Evidence |
|---|---|---|
| **Benchmark Scaling** | **COMPLETE** | 165 total drug–event pairs evaluated across 3 stratified cohorts (15 Core, 50 Blockbusters, 100 OMOP). |
| **Local LLM Backend** | **COMPLETE** | Zero-cost Ollama `qwen2.5:7b` integration; fully tested and reproducible offline. |
| **Academic Manuscript** | **COMPLETE (DRAFT)** | 9-section conference paper manuscript at `docs/paper/PharmaGuard_Conference_Paper.md`. |
| **Interactive Dashboard** | **COMPLETE & LIVE** | Multi-cohort switcher, 151 live triage presets, and methodology probes running on `localhost:8501`. |
| **Defense Slide Deck** | **COMPLETE** | 18-slide end-semester presentation deck and speaker notes synchronized with 165-pair data. |
| **Code Quality & Tests** | **COMPLETE** | 242/242 pytest unit tests passing cleanly; clean git tree on `origin/main`. |

---

## 8. Discussion Points & Next Steps for Your Guidance

We would appreciate your feedback and advice on the following points:

1. **Target Publication Venue:**
   - The manuscript is currently budgeted for a 6–8 page double-column conference format (ideal for **IEEE BIBM 2026** or **ACM CHIL 2026**) or can be extended into a full journal paper for **JAMIA (Journal of the American Medical Informatics Association)**. What venue would you prefer us to format the submission for first?
2. **Manuscript Review:**
   - Would you like to review the markdown manuscript directly (`docs/paper/PharmaGuard_Conference_Paper.md`), or should we compile it into the formal IEEE/ACM LaTeX template with embedded vector PDF figures for your review?
3. **Capstone Defense Preparation:**
   - For our upcoming capstone presentation, would you like us to conduct a 10-minute dry-run presentation and live dashboard demonstration during our next meeting?
