---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #f8fafc
color: #334155
style: |
  section {
    font-family: 'Arial', sans-serif;
    padding: 40px 60px;
    font-size: 19px;
  }
  h1 {
    color: #0f172a;
    font-size: 34px;
    margin-bottom: 8px;
  }
  h2 {
    color: #1e293b;
    font-size: 26px;
    margin-top: 0;
  }
  h3 {
    color: #2563eb;
    font-size: 19px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
  }
  strong {
    color: #0f172a;
  }
  footer {
    font-size: 12px;
    color: #94a3b8;
  }
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  .grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
  }
  .card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
  .hero-num {
    font-size: 40px;
    font-weight: 800;
    color: #2563eb;
    line-height: 1;
    margin-top: 4px;
    margin-bottom: 6px;
  }
  .hero-green {
    color: #166534;
  }
  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
    background: #dbeafe;
    color: #1e40af;
    margin-bottom: 8px;
  }
  table {
    font-size: 14px;
    width: 100%;
    border-collapse: collapse;
  }
  th {
    background: #1e293b;
    color: #ffffff;
    padding: 8px;
  }
  td {
    padding: 7px;
    border-bottom: 1px solid #e2e8f0;
  }
---

<!-- _class: lead invert -->
<!-- _backgroundColor: #0f172a -->
<!-- _color: #f8fafc -->

<span class="badge" style="background:#1e3a8a; color:#bfdbfe;">B.TECH 7TH-SEMESTER CAPSTONE DEFENSE (2026–27)</span>

# 🛡️ PharmaGuard
### Intelligent Pharmacovigilance Signal Triage Orchestrator Grounded in Multi-Source Clinical Evidence

**Group 07:** Krishna Sikheriya (IIT2023139, Lead) · Lokesh Bawariya (IIT2023138) · Naitik Jain (IIB2023036)  
**Supervisor:** Dr. Nikhilanand Arya, Assistant Professor, Dept. of Information Technology  
**Institution:** Indian Institute of Information Technology, Allahabad

---

### 1. BACKGROUND & MOTIVATION
# The Pharmacovigilance Triage Bottleneck

<div class="grid-2">
<div class="card">

#### 🚨 The Postmarketing Reality
* **RCTs are fundamentally underpowered** to detect rare, delayed, or idiosyncratic adverse drug reactions in small cohorts.
* **Massive spontaneous data:** US FDA FAERS receives millions of reports annually, yet data is noisy and confounded by disease.
* **Severe human burden:** Adverse drug events are a leading cause of preventable patient hospitalizations worldwide.

</div>
<div class="card">

#### ⚡ The Cognitive Triage Crisis
* **Manual review cannot scale:** Clinicians face thousands of potential candidate pairs weekly.
* **Pervasive Alert Fatigue:** Ungrounded AI tools trigger massive false alarms; clinicians override 49%–96% of alerts.
* **Asymmetric Risk:** False alarms waste review resources; missed signals permit patient harm to compound.

</div>
</div>

---

### 2. SYSTEM MISSION
# What PharmaGuard Is & What Distinguishes It

<div class="grid-3">
<div class="card">

#### Tri-Source Fusion
* **openFDA FAERS:** Real-time $2 \times 2$ disproportionality (PRR, ROR, Woolf 95% CIs) [Weight: 0.40].
* **ChEMBL MoA:** Receptor-level molecular biological plausibility [Weight: 0.20].
* **PubMed NCBI:** Literature retrieval & epidemiological grading [Weight: 0.40].

</div>
<div class="card">

#### Public APIs Only
* **Zero EHR Lock-In:** Unlike recent causal graphs, PharmaGuard requires zero private hospital EHR data.
* **100% Reproducible:** Operates strictly on open-access public APIs.
* **Deterministic Gating:** Gate 1 empirical floor (`NO_SIGNAL` $\implies$ `DO_NOT_ESCALATE`).

</div>
<div class="card">

#### Safe AI Architecture
* **Eliminates Hallucinations:** Replaces uncalibrated self-confidence with closed-form mathematics.
* **Resolves Regulatory Confusion:** Distinguishes past safety reviews from confirmed harms.
* **Adversarial Leakage Critic:** Detects parametric memory leakage.

</div>
</div>

---

### 3. CLINICAL BASELINE
# Current Regulatory Standards & Disproportionality

<div class="grid-2">
<div class="card">

#### $2 \times 2$ Contingency Analysis
* **Proportional Reporting Ratio (PRR, Evans 2001):**
  $$\text{PRR} = \frac{a / (a + b)}{c / (c + d)}$$
* **Reporting Odds Ratio (ROR, van Puijenbroek 2002):**
  $$\text{ROR} = \frac{a \cdot d}{b \cdot c}$$
* **Screening Gate:** $\text{PRR} \ge 2.0$, $n \ge 3$, Woolf $95\% \text{ CI}_{\text{lower}} > 1.0$.

</div>
<div class="card">

#### Classical Limitations
* **Correlational & Blind to Biology:** Cannot check receptor binding mechanisms.
* **Vulnerable to Indication Confounding:** Pre-existing illness symptoms misattributed to drug.
* **Polypharmacy Confounding:** Co-prescribed companion drugs trigger false alarms (e.g. Metformin).
* **Denominator Dilution:** Chronic medications fail static $\text{PRR} \ge 2.0$ cutoffs.

</div>
</div>

---

### 4. PROBLEM & OBJECTIVES
# Problem Statement & 4 Core Engineering Objectives

> *"A lightweight, publicly-reproducible multi-agent framework for adverse event triage fusing FAERS disproportionality, ChEMBL pharmacology, and PubMed literature grading through deterministic safety-gated escalation logic, incorporating disease-context reasoning via public WHO ATC classifications without restricted EHR data."*

1. **Deterministic Evidence Fusion:** Closed-form mathematical confidence formula ($0.40/0.20/0.40$).
2. **Hard Safety Gating:** `FAERS NO_SIGNAL` strictly forces `DO_NOT_ESCALATE`.
3. **Public Disease-Context Reasoning:** Characterize indication confounding via WHO ATC ontologies.
4. **Multi-Scale Empirical Validation:** 165 pairs across 3 standardized cohorts with Wilson 95% CIs.

---

### 5. LITERATURE EVOLUTION
# Three Generations of Pharmacovigilance

<div class="grid-3">
<div class="card">

#### Gen 1 (1998–2009)
* **Statistical Disproportionality**
* Bate 1998, Evans 2001, van Puijenbroek 2002.
* $2 \times 2$ contingency tables, Empirical Bayes shrinkage.
* *Boundary:* Fast & public, but blind to pharmacology and heavily confounded.

</div>
<div class="card">

#### Gen 2 (2012–2023)
* **Unimodal ML on EHRs**
* Harpaz 2012, Vilar 2014, Coste 2023.
* Supervised classification on hospital notes.
* *Boundary:* Locked behind restricted EHRs; black-box opacity.

</div>
<div class="card">

#### Gen 3 (2023–2026)
* **Multi-Agent & Foundation Models**
* Yao 2023, Omar 2025, Toonsi 2026.
* Generative agents & causal knowledge graphs.
* *Boundary:* Hallucinated confidence or massive UK Biobank requirement.

</div>
</div>

<div class="card" style="margin-top:14px; background:#eff6ff; border-color:#2563eb;">
<strong>PharmaGuard's Positioning:</strong> Tool-grounded, disease-context-aware agent delivering causal-grade auditability using only open public APIs with deterministic mathematical safety guarantees.
</div>

---

### 6. RESEARCH GAPS
# Identified Gaps in Contemporary Literature

<div class="grid-3">
<div class="card">

#### Gap 1: Indication Confounding Neglected
* **Coste et al. 2023 Systematic Review:** Only **10 of 101 studies (9.9%)** addressed confounding by indication or reported stratified performance.
* *Impact:* Disease natural history misattributed as adverse drug effect.
* *Fix:* Pre-registered 7-rule `IndicationConcordance` cascade.

</div>
<div class="card">

#### Gap 2: Static Cutoffs Fail on Chronic Drugs
* **OMOP Pilot Empirical Finding (§31):** Static $\text{PRR} \ge 2.0$ thresholds systematically suppress signals on high-volume chronic blockbusters (Amlodipine, SSRIs).
* *Impact:* Denominator dilution suppresses true signals into 1.1–1.9 range.
* *Fix:* CI-based signal detection floor (Evans 2001).

</div>
<div class="card">

#### Gap 3: Causal PV Locked in EHRs
* **Data Access Barrier:** State-of-the-art causal graphs (Toonsi 2026) depend entirely on private patient EHRs.
* *Impact:* Prevents global auditability and clinical deployment.
* *Fix:* 100% public WHO ATC ontology resolution via ChEMBL.

</div>
</div>

---

### 7. BENCHMARK COHORTS
# Multi-Tiered Benchmark Cohorts ($N = 165$ Total Pairs)

<div class="grid-3">
<div class="card">

#### Core Benchmark (15 Pairs)
* **Golden Ground Truth**
* 7 Confirmed Positives (Boxed Warnings & RCTs).
* 5 Genuine Negative Controls (Formally dismissed signals).
* 3 Zero-Report Controls (Safety gate verification).

</div>
<div class="card">

#### Top Prescribed (50 Pairs)
* **Real-World Outpatient Safety**
* 25 High-Mortality Boxed Warnings (Statins, ACEi, Opioids).
* 25 Balanced Negative Controls.
* 100% evaluated offline via local Ollama (`qwen2.5:7b`).

</div>
<div class="card">

#### OMOP Reference (100 Pairs)
* **OHDSI Organ Toxicity Standard**
* 50 Positives + 50 Negatives (Ryan et al. 2013).
* 4 Severe Phenotypes: AMI, AKI, Liver Injury, GI Bleed.
* Validated chronic therapy denominator dilution.

</div>
</div>

<div class="card" style="margin-top:14px; background:#f0fdf4; border-color:#166534;">
<strong>Open-Science Standard:</strong> 100% public domain / open access (FDA public records, ChEMBL CC BY-SA 3.0, OHDSI Apache 2.0). Zero MedDRA MSSO licensing dependencies.
</div>

---

### 8. ARCHITECTURE & FUSION
# Tri-Source Evidence Fusion & Closed-Form Gating

$$\text{Confidence} = 0.40 \cdot S_{\text{FAERS}} + 0.40 \cdot S_{\text{PubMed}} + 0.20 \cdot S_{\text{ChEMBL}}$$

<div class="grid-3">
<div class="card">

#### Stream 1: FAERS (0.40)
* $2 \times 2$ PRR / ROR computation.
* Discrete Tiers: `STRONG` (1.00), `MODERATE` (0.66), `WEAK` (0.33), `NO_SIGNAL` (0.00).
* Woolf CI fallthrough gate.

</div>
<div class="card">

#### Stream 2: ChEMBL (0.20)
* Molecular mechanism of action.
* Biological Plausibility: `HIGH` (0.90), `MODERATE` (0.50), `LOW` (0.00).
* Blinded MoA curation (§1.1).

</div>
<div class="card">

#### Stream 3: PubMed (0.40)
* Automated abstract retrieval.
* Rubric v1.0: `Grade A` (1.00: RCT/OR/HR), `Grade B` (0.50: Case reports), `Grade C` (0.00).
* Semantic LLM grading.

</div>
</div>

<div class="card" style="margin-top:12px;">
<strong>Deterministic Decision Gating:</strong><br>
• <strong>Gate 1 (Hard Stop):</strong> <code>FAERS == NO_SIGNAL</code> $\implies$ Immediately force <strong><code>DO_NOT_ESCALATE</code></strong>.<br>
• <strong>ESCALATE:</strong> <code>Confidence ≥ 0.70 AND FAERS ≥ MODERATE</code> | <strong>MONITOR:</strong> <code>Confidence ≥ 0.35</code> | <strong>DO_NOT_ESCALATE:</strong> Otherwise.
</div>

---

### 9. DEEP-DIVE #1
# Disease-Context Reasoning via WHO ATC Ontologies

<div class="grid-2">
<div class="card">

#### WHO ATC Taxonomy Resolution
* **The Biological Problem:** Chronic illness medications naturally co-occur with complications of that disease (indication confounding).
* **Hierarchical Resolution:**
  * **Level 1:** Main Anatomical Group (e.g. `C` — Cardiovascular, `N` — Nervous).
  * **Level 2:** Pharmacological Subgroup (e.g. `C08` — Calcium Channel Blockers, `N06A` — Antidepressants).
  * **Level 4/5:** Generic chemical substance.
* **Coverage:** 95.7% automated corpus coverage with verified fallbacks.

</div>
<div class="card">

#### Utilization Duration Derivation
* **CHRONIC (≥ 3 Months Continuous):** Antihypertensives, Statins, Antidiabetics. Tens of millions exposed; vulnerable to denominator dilution.
* **ACUTE (< 4 Weeks Temporary):** Antibacterials, Antivirals. High event concentration yields robust disproportionality.
* **MIXED:** NSAIDs, Bronchodilators (acute relief vs. maintenance).
* **Robustness:** Exponential backoff (`retries=3`) and live name resolution ensure 96.3% holdout stability.

</div>
</div>

---

### 10. DEEP-DIVE #2
# IndicationConcordance Heuristics & Citation Auditing

<div class="grid-2">
<div class="card">

#### 7 Pre-Registered Clinical Rules (§35)
* **IND-CONF-01:** ATC C, B01 $\times$ Myocardial Infarction, Stroke
* **IND-CONF-02:** ATC N $\times$ Suicidal Ideation, Depression, Seizures
* **IND-CONF-03:** ATC A02, M01 $\times$ GI Bleed, Peptic Ulcer
* **IND-CONF-04:** ATC A10 $\times$ Hypoglycaemia, DKA
* **IND-CONF-05:** ATC L $\times$ Neutropenia, Thrombocytopenia
* **IND-CONF-06:** ATC C03, C09 $\times$ Acute Kidney Injury
* **IND-CONF-07:** ATC R03 $\times$ Bronchospasm, Asthma Crisis

</div>
<div class="card">

#### Two-Round Citation Audit Discipline
* **The Clinical AI Integrity Hazard:** LLMs routinely invent or drift clinical literature citations.
* **Round 1 (PubMed/NIH Audit):** Audited all 21 supporting citations; identified and corrected 13 erroneous journals, volumes, or years.
* **Round 2 (Domain-Specific Trials):** Replaced general editorial commentary with verified clinical trials (Lapi 2013 on AKI; Hernández-Díaz 2000 on NSAID GI bleeding).
* **Result:** 100% of rules verified against peer-reviewed literature.

</div>
</div>

---

### 11. DEEP-DIVE #3
# Scoring-Isolation Design: The Core Architectural Novelty

<div class="grid-2">
<div class="card">

#### The Isolation Wall Design
* **Strictly Informational Surveillance:** `IndicationConcordance` operates as an audit annotation in production.
* **Scoring Contribution = 0.000:** Causes zero decision boundary shifts in frozen baseline reports.
* **High-Visibility Clinical Provenance:** Flagged prominently on review cards and clinical dossiers to alert human reviewers to channeling bias.
* **Regression Invariance:** Automated tests confirm byte-identical pipeline output stability.

</div>
<div class="card">

#### Why Scoring-Inert? Anti-Overfitting
* **No Universal Confounder Constant Exists:** Pharmacoepidemiology consensus (Walker 1996, Psaty 1999) proves bias factors vary wildly (1.2 to 20-fold). A fixed scalar discount without EHR data is unscientific guesswork.
* **The Atorvastatin Regression Trap (§32):** Automated chronic gate conditioning caused an immediate false-positive regression on Atorvastatin + Dementia.
* **Holdout Validation (§37):** A 0.85× discount attenuated continuous confidence downward in 4 concordant pairs, but shifted 0 discrete triage categories (null result).

</div>
</div>

---

### 12. EXPERIMENTAL FINDING #1
# OMOP 100-Pair Evaluation & The Chronic PRR Dilution Paradox

<div class="grid-3">
<div class="card" style="background:#f0fdf4; border-color:#166534;">

### STRICT SPECIFICITY
<div class="hero-num hero-green">100.0%</div>
50 / 50 Negative Controls Cleared (FP = 0)

</div>
<div class="card">

### LENIENT PRECISION
<div class="hero-num">93.3%</div>
14 / 15 Triaged Signals True Toxicities

</div>
<div class="card">

### OVER-CAUTION RATE
<div class="hero-num" style="color:#0f172a;">2.0%</div>
Only 1 / 50 Negatives in MONITOR

</div>
</div>

<div class="card" style="margin-top:14px;">

#### The Chronic PRR Denominator Dilution Paradox (DECISIONS.md §31)
* **The Finding:** While negative controls were completely cleared (100% specificity), Strict Recall on OMOP positives was 0.060 (3/50) and Lenient Recall was 0.280 (14/50).
* **The Root Cause:** Chronic blockbuster therapies (Amlodipine, SSRIs, Nifedipine) accumulate millions of background reports across decades.
* **Mathematical Compression:** The massive denominator compresses PRR into the 1.1–1.9 range—below the static $\text{PRR} \ge 2.0$ gate—despite thousands of absolute reports ($n \le 4,610$), significant lower 95% CIs ($> 1.0$), and established biological plausibility.
* **Epidemiological Contribution:** Empirically proves static magnitude gates fail on chronic high-utilization drugs.

</div>

---

### 13. EXPERIMENTAL FINDING #2
# Top Prescribed Blockbusters (50 Pairs & Boxed Warnings)

<div class="grid-3">
<div class="card" style="background:#f0fdf4; border-color:#166534;">

### LENIENT F1-SCORE
<div class="hero-num hero-green">0.9388</div>
Wilson 95% CI: [0.850 – 0.978]

</div>
<div class="card">

### BOXED WARNING RECALL
<div class="hero-num">92.0%</div>
23 / 25 FDA Boxed Warnings Caught

</div>
<div class="card">

### STRICT PRECISION
<div class="hero-num" style="color:#0f172a;">1.0000</div>
10 / 10 Strict Escalations Confirmed

</div>
</div>

<div class="card" style="margin-top:14px;">

#### Real-World Outpatient Triage Efficacy
* **Cohort Balance:** 25 high-mortality Boxed Warnings vs. 25 balanced negative controls across 7 major therapeutic classes (Statins, ACEi/ARBs, Antibiotics, Antidepressants, Opioids, Anticonvulsants).
* **Critical Toxicities Flagged:** Metformin lactic acidosis, Lisinopril angioedema, Clozapine agranulocytosis, Amiodarone pulmonary fibrosis, Ciprofloxacin tendon rupture, Bupropion seizures.
* **Clinician Alert Discipline:** 24 of 25 negative controls completely cleared; only 1 diabetic medication entered MONITOR due to diabetic polypharmacy confounding.
* **Offline Execution:** 100% evaluated offline via local Ollama (`qwen2.5:7b`) with persistent disk caching.

</div>

---

### 14. RESULTS SYNTHESIS
# Master Multi-Cohort Benchmark Matrix ($N = 165$)

| Evaluation Suite & Model | Strict Prec | Strict Rec | Strict Spec | Strict $F_1$ | Len Prec | Len Rec | Len Spec | Len $F_1$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PharmaGuard (Core, $n=15$)** | **1.0000** | **0.8571** | **1.0000** | **0.9231** | **0.8750** | **1.0000** | **0.8750** | **0.9333** |
| *Single-Shot Baseline (Core)* | 0.8750 | 1.0000 | 0.8750 | 0.9333 | 0.7000 | 1.0000 | 0.6250 | 0.8235 |
| **PharmaGuard (Blockbusters, $n=50$)** | **1.0000** | **0.4000** | **1.0000** | **0.5714** | **0.9583** | **0.9200** | **0.9600** | **0.9388** |
| **PharmaGuard (OMOP, $n=100$)** | **1.0000** | **0.0600** | **1.0000** | **0.1132** | **0.9333** | **0.2800** | **0.9800** | **0.4308** |

<div class="card" style="margin-top:14px;">
<strong>Core Benchmark Takeaways:</strong><br>
• <strong>Zero False Alarms:</strong> 1.0000 Strict Precision across all 165 pairs; never escalates a negative control.<br>
• <strong>92.0% Boxed Warning Capture:</strong> Flags critical outpatient risks with 0.9388 Lenient $F_1$.<br>
• <strong>Halving Alert Fatigue:</strong> Over-caution cut to 4.0% on blockbusters and 2.0% on OMOP vs. 25.0% on baseline.
</div>

---

### 15. SCIENTIFIC CONTRIBUTIONS
# Key Scientific Contributions & Architectural Novelties

<div class="grid-2">
<div class="card">

#### 1. Scoring-Inert Architecture
* Decouples clinical disease context from numerical confidence scoring.
* Alerts reviewers to channeling bias while preserving mathematical determinism and avoiding benchmark overfitting.

#### 2. Public-API Disease Reasoning
* Proves standardized WHO ATC codes via ChEMBL provide disease-context reasoning without private hospital EHR data.
* Democratizes reproducible signal triage globally.

</div>
<div class="card">

#### 3. Two-Round Citation Auditing
* Independently verified all 21 supporting citations against PubMed, correcting 13 historical errors.
* Ensures 100% of heuristics are backed by real clinical trials.

#### 4. Engineering Rigor & Reproducibility
* 242 automated pytest unit tests; persistent SHA-256 caching.
* Dual-metric philosophy accurately characterizes clinical uncertainty.

</div>
</div>

---

### 16. LIMITATIONS & ROADMAP
# Methodological Limitations & Semester 8 Roadmap

<div class="grid-2">
<div class="card">

#### Methodological Limitations
* **Single-Curator Golden Set:** Core set curated by primary investigator; multi-center consensus panels needed.
* **Heuristic Linear Priors:** Weights (0.40/0.40/0.20) are expert priors rather than learned parameters.
* **Low Statistical Power on Holdout (§37):** Only 4 of 40 held-out pairs triggered concordance; expanding to $N \ge 100$ concordant pairs is required.
* **Primary Indication Simplification:** Off-label uses and multi-indication drugs uncaptured.

</div>
<div class="card">

#### Semester 8 Roadmap
* **Multi-Jurisdiction Ingestion:** Ingest EMA EudraVigilance, PMDA JADER, and WHO VigiBase.
* **MedDRA Hierarchical Roll-Up:** Map Preferred Terms (PT) to High-Level Group Terms (HLGT) and SOCs.
* **Exposure-Adjusted Bayesian Gating:** Condition gates on prescription volume to rescue chronic therapies.
* **Conference Paper Submission:** Full 9-section manuscript drafted for IEEE BIBM / ACM CHIL / JAMIA.

</div>
</div>

---

### 17. ENGINEERING RIGOR
# Production Tech Stack & Clinical Dashboard

<div class="grid-2">
<div class="card">

#### Runtime & Engineering Rigor
* **Python 3.13 Environment:** Pandas, NumPy, Pydantic v2 data models.
* **Dual Inference Engines:** Local Ollama (`qwen2.5:7b`, 100% offline & unmetered) + Cloud Google Gemini.
* **Deterministic Caching:** SHA-256 diskcache guarantees zero live network calls during evaluation runs.
* **Continuous Integration:** GitHub Actions CI with bytecode compilation, ruff linting, and 242 unit tests.

</div>
<div class="card">

#### Interactive Streamlit Dashboard
* **Global Benchmark Switcher:** Instant top-bar toggling between Core [15], Blockbusters [50], and OMOP [100].
* **Live Signal Triage:** Typeahead selectbox with 151 presets and arbitrary drug-event screening.
* **Clinical Dossier Export:** One-click download of regulatory Clinical Safety Briefings (.md & .json).
* **Methodology Probes View:** Adversarial Critic audit table & Confounding before/after waterfalls.

</div>
</div>

---

### 18. VERIFIED REFERENCES
# Independently Audited & Verified Academic Literature

<div class="grid-2">
<div class="card">

#### Disproportionality & Standards
* **Evans et al. (2001):** PRR signal generation. *Pharmacoepidemiol Drug Saf*, 10(6), 483–486.
* **van Puijenbroek et al. (2002):** ROR in spontaneous systems. *Br J Clin Pharmacol*, 54(4), 414–421.
* **Bate & Evans (2009):** Quantitative signal detection. *Pharmacoepidemiol Drug Saf*, 18(6), 427–436.
* **Ryan et al. (2013):** OMOP ground truth set. *Drug Safety*, 36(Suppl 1), S33–S47.
* **Coste et al. (2023):** Systematic review of 101 PV studies. *Pharmacoepidemiol Drug Saf*, 32(1), 28–43.

</div>
<div class="card">

#### Epidemiology, LLMs & Causal Graphs
* **Omar et al. (2025):** LLM hallucination vulnerabilities. *Communications Medicine*, 5(1), 330.
* **Toonsi et al. (2026):** Causal knowledge graphs. *Bioinformatics*, 42(1), btaf661.
* **Walker (1996):** Confounding by indication. *Epidemiology*, 7(4), 335–336.
* **Psaty et al. (1999):** Channeling bias in cardiovascular trials. *J Am Geriatr Soc*, 47(6), 749–754.
* **Schneeweiss & Avorn (2005):** Health utilization databases. *J Clin Epidemiol*, 58(4), 323–337.

</div>
</div>

---

<!-- _class: lead invert -->
<!-- _backgroundColor: #0f172a -->
<!-- _color: #f8fafc -->

<span class="badge" style="background:#166534; color:#dcfce7;">DEFENSE CONCLUSION</span>

# Summary of Capstone Achievements

* **Evidence-Grounded Triage:** Replaced LLM hallucinations with deterministic tri-source fusion and hard safety gates.
* **Flawless Specificity:** 100% Strict Precision across all 165 pairs, halving clinician alert fatigue.
* **Public Disease-Context Reasoning:** Resolved WHO ATC indication concordance without restricted hospital EHR data.
* **Engineering Rigor:** 242 passing pytest unit tests, live Streamlit dashboard, and complete conference paper draft.

**Repository:** `github.com/Krishna200608/PharmaGuard`  
*Thank you! Floor is open for questions and committee feedback.*
