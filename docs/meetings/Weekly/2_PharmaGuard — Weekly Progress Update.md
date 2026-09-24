# PharmaGuard — Weekly Progress Update #2
### Multi-Scale Benchmark Expansion (165 Pairs), Local LLM Integration, and Interactive Evaluation Dashboard

**Submitted to:** Dr. Nikhilanand Arya  
**Group 07:** Krishna Sikheriya (IIT2023139), Lokesh Bawariya, Naitik Jain  
**Date:** September 2026  

---

## 1. Feedback & Guidance from Previous Meeting (Recap)

In our previous meeting and update, we established the following key directions:

1. **Scoring-Inert Clinical Context:** Following our 40-pair test of the indication concordance layer (which yielded a low-power null result of 4/40 triggers without metric movement), we agreed to maintain the disease-context layer as an **explicit, scoring-inert provenance flag** on reports rather than applying ungrounded numerical scalar penalties.
2. **Scale & Rigorous Benchmarking:** You advised moving beyond small-sample toy evaluation (15 pairs) to test whether PharmaGuard's triage gates and tri-source fusion hold up under large-scale, real-world postmarketing surveillance conditions.

This document summarizes our major progress across these key directives.

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
- **Why this matters for PharmaGuard:** A purely statistical tool will drop these real signals. However, PharmaGuard's **tri-source fusion** uses ChEMBL receptor pharmacology and PubMed literature grading to prevent them from being discarded, routing them safely to `MONITOR` rather than `DO_NOT_ESCALATE`. This provides strong empirical justification for our dual-metric (Strict vs. Lenient) evaluation framework.

---

## 3. Zero-Cost, Unmetered Local LLM Integration (Ollama `qwen2.5:7b`)

Executing 165 multi-source pipeline runs against commercial cloud APIs (like Google Gemini Flash) introduced severe rate-limiting bottlenecks (e.g., 15 RPM free-tier ceilings) and recurring API costs.

**What we built:**
- We integrated the **Ollama local inference daemon (`qwen2.5:7b`)** directly into PharmaGuard's LLM factory layer.
- Local LLM inference runs 100% on-device via `http://localhost:11434`, with unmetered throughput, zero API fees, and complete offline privacy.
- We evaluated the entire 50-pair Blockbuster benchmark and 100-pair OMOP benchmark completely locally through Ollama, achieving identical deterministic schema extraction without dropping a single call.
- The system retains seamless dual-backend support: users can switch between local Ollama and Cloud Gemini Flash via a single configuration toggle.

---

## 4. Evaluation Dashboard Multi-Cohort Integration & Live Signal Triage

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
   - Verified that all **245 / 245 unit tests** pass with 100% green status via pytest.

---

## 5. Capstone Presentation Deck Synchronization

We fully synchronized the mid/end-semester capstone presentation materials with the 165-pair benchmark scale:

- **Slide Outline (`docs/presentation/End_Semester_Slide_Content.md`):** Updated the 20-slide presentation deck to reflect the multi-cohort evaluation, PRR denominator dilution findings, local Ollama integration, and live dashboard demo flow.
- **PowerPoint & Marp Decks:** Generated automated 16:9 widescreen presentation deck (`docs/presentation/PharmaGuard_Defense_Deck.pptx`) and Marp markdown slides (`docs/presentation/PharmaGuard_Defense_Deck_Marp.md`).
- **Delivery Notes (`docs/presentation/SLIDE_DECK_NOTES.md`):** Updated presenter cue cards, timing checkpoints (15-minute budget), and anticipated defense/viva defense questions (e.g., explaining why OMOP strict recall is lower due to chronic utilization, and defending why the indication concordance layer is scoring-inert).

---

## 6. Summary of Completed Milestones

| Target Area | Status | Deliverables / Evidence |
|---|---|---|
| **Benchmark Scaling** | **COMPLETE** | 165 total drug–event pairs evaluated across 3 stratified cohorts (15 Core, 50 Blockbusters, 100 OMOP). |
| **Local LLM Backend** | **COMPLETE** | Zero-cost Ollama `qwen2.5:7b` integration; fully tested and reproducible offline. |
| **Interactive Dashboard** | **COMPLETE & LIVE** | Multi-cohort switcher, 151 live triage presets, and methodology probes running on `localhost:8501`. |
| **Defense Slide Deck** | **COMPLETE** | 20-slide end-semester presentation deck (.pptx & Marp) and speaker notes synchronized with 165-pair data. |
| **Code Quality & Tests** | **COMPLETE** | 245/245 pytest unit tests passing cleanly; clean git tree on `origin/main`. |
| **Academic Manuscript** | **FUTURE WORK** | Conference paper drafting scheduled for post-midsem targeting IEEE BIBM / ACM CHIL / JAMIA. |

---

## 7. Future Work & Discussion Points for Your Guidance

### Planned Future Works (Post-Midsem Focus)
1. **Academic Conference Paper Drafting:** Following mid-semester evaluations, we plan to draft the formal conference paper for submission to **IEEE BIBM (International Conference on Bioinformatics and Biomedicine)**, **ACM CHIL (Conference on Health, Inference, and Learning)**, or **JAMIA**. We will seek your guidance on target venue selection.
2. **Multi-Jurisdiction Ingestion:** Expanding beyond US FDA FAERS to incorporate European EudraVigilance, Japanese JADER, and WHO VigiBase.
3. **Exposure-Adjusted Bayesian Gating:** Conditioning signal thresholds on prescription volume to address the chronic therapy PRR dilution phenomenon.

### Discussion Points for This Meeting
1. **Capstone Defense Preparation:**
   - For our upcoming capstone presentation, would you like us to conduct a 10-minute dry-run presentation and live dashboard demonstration during our next meeting?
2. **Benchmark Scale & Clinical Focus:**
   - Are there specific additional drug–event pairs or therapeutic classes you would recommend prioritizing for further analysis?
