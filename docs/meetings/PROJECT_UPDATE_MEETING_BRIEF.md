# PharmaGuard: B.Tech Capstone Project Update & Meeting Briefing

**Course:** 7th Semester B.Tech Major Project (IT) — IIIT Allahabad  
**Project Group:** Group 07  
**Project Title:** PharmaGuard: A Tool-Grounded Agentic AI Architecture for Pharmacovigilance Signal Triage  
**Team Members:** Krishna Sikheriya (IIT2023139) [Lead], Lokesh, Naitik  
**Project Supervisor:** Dr. Nikhilanand Arya, Assistant Professor, Department of Information Technology  
**Date of Meeting:** Thursday, September 3, 2026 (1:00 PM) — Cabin CC-III, Room 5414  
**Codebase & Live Artifacts:** [GitHub Repository (Krishna200608/PharmaGuard)](https://github.com/Krishna200608/PharmaGuard) · 84/84 Tests Passing  

---

## 📌 Document Purpose (For Team Members)

> **Team Study Guide:**  
> This briefing document is prepared for **Krishna, Lokesh, and Naitik** to review before our progress update meeting with Dr. Nikhilanand Arya. It summarizes what we built, why our approach is scientifically novel, the exact experimental results obtained, the mathematical concepts behind our architecture, the challenges we solved, and the exact questions Sir is likely to ask.
>
> *Tip for PDF conversion:* This document is formatted with clean markdown tables, callout blocks, and section hierarchies for easy printing or direct PDF export.

---

## 🧠 Part 1: Quick Primer & Core Terminology

Before the meeting, ensure you are comfortable with these core concepts:

| Term | What It Means (Simple English) | Why It Matters for PharmaGuard |
|---|---|---|
| **Pharmacovigilance (PV)** | Postmarketing drug safety monitoring — tracking side effects after a drug is approved and sold to the public. | Millions of safety reports arrive each year; human safety teams face a massive triage bottleneck. |
| **FAERS** | FDA Adverse Event Reporting System — the public database of spontaneous real-world safety reports. | Our system queries live openFDA data to see how often a drug and symptom co-occur in the real world. |
| **PRR (Proportional Reporting Ratio)** | Statistical ratio comparing how often an event is reported for *Drug X* vs. *all other drugs combined*. | A $\text{PRR} > 2.0$ with $\ge 3$ reports indicates a disproportionate statistical signal above background. |
| **ChEMBL** | EMBL-EBI open database of drug targets and biological mechanisms of action (MoA). | Tells us *how* the drug works at a molecular level so we can evaluate biological plausibility. |
| **Biological Plausibility** | Whether a drug's known biochemical target makes it biologically sensible that it could cause the adverse event. | Graded as `HIGH` (1.0), `MODERATE` (0.5), `LOW` (0.0), or `UNKNOWN` (0.0). |
| **PubMed Evidence Grading** | Real-time literature search via NCBI E-utilities, graded by an LLM using a strict rubric. | `Grade A` (1.0) = Statistically significant ($p < 0.05$ / CIs); `Grade B` (0.5) = Case reports; `Grade C` (0.0) = No support. |
| **Parametric Memory** | What an LLM "remembers" from its pre-training data without checking live external sources. | Raw LLMs hallucinate or confuse historical safety *concerns* with *proven* safety actions. |
| **Deterministic Gating** | Using fixed mathematical formulas and explicit logic rules rather than free-form LLM text to make final triage decisions. | Ensures 100% auditability, predictability, and safety compliance in clinical decision-making. |
| **Strict vs. Lenient Evaluation** | • **Strict:** Only `ESCALATE` counts as a True Positive (requires high confidence + strong statistical data).<br>• **Lenient:** Both `ESCALATE` and `MONITOR` count as True Positives (signal was captured and not dismissed). | Captures the clinical reality that expressing appropriate caution under uncertainty is safe behavior. |

---

## ⚙️ Part 2: How PharmaGuard Works (Step-by-Step Architecture)

```
                       [ Input: Drug Name + Adverse Event ]
                                        │
                                        ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │                       MULTI-SOURCE EVIDENCE ENGINE                     │
   ├────────────────────────┬───────────────────────┬───────────────────────┤
   │      1. FAERS API      │    2. ChEMBL Database │    3. PubMed Search   │
   │  openFDA co-occurrence │  Mechanism of Action  │ NCBI E-utilities tool │
   │   PRR & ROR statistics │ Biological Plausibility│ Grade A/B/C Evidence  │
   │   $S_{\text{FAERS}}$   │   $S_{\text{Mech}}$   │  $S_{\text{PubMed}}$  │
   └────────────────────────┴───────────────────────┴───────────────────────┘
                                        │
                                        ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │                 DETERMINISTIC CONFIDENCE SCORE FORMULA                 │
   │                                                                        │
   │   Confidence = 0.40 · S_FAERS + 0.40 · S_PubMed + 0.20 · S_Mech        │
   │   (Range: 0.000 to 1.000 — 100% traceable, no LLM guesswork)           │
   └────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │                       HIERARCHICAL ESCALATION GATING                   │
   ├────────────────────────────────────────────────────────────────────────┤
   │  Gate 1: If S_FAERS == NO_SIGNAL  ──► DO_NOT_ESCALATE (Hard Stop)      │
   │  Gate 2: If Confidence >= 0.70 & Signal is Strong/Mod ──► ESCALATE     │
   │  Gate 3: If Confidence >= 0.35   ──► MONITOR                           │
   │  Gate 4: Otherwise               ──► DO_NOT_ESCALATE                   │
   └────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                   [ Output: TriageReport JSON + Streamlit UI ]
```

### Why Gate 1 is the Most Important Safety Rule in the System:
If an adverse event has **zero reports in FAERS**, a standard LLM might still want to escalate it if it finds theoretical debates in research papers. **Gate 1 prevents this:** if there is no real-world statistical signal, the system unconditionally forces `DO_NOT_ESCALATE` (§4). This eliminates spurious false alarms on negative controls.

---

## 💡 Part 3: Why is PharmaGuard Novel? (Publishability & Research Contributions)

If Dr. Arya asks: *"What is genuinely novel here? Is this work publishable in a reputable venue?"*, use these concrete research points:

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

### 1. The Core Research Gap in Published Literature
Existing pharmacovigilance research falls into two disconnected silos:
* **Traditional Disproportionality Algorithms (PRR, ROR, MGPS, BCPNN):** Rely purely on statistical co-occurrence. They lack any understanding of pharmacology, cannot interpret biomedical literature, and suffer from massive false-positive rates due to polypharmacy and co-prescription artifacts.
* **Ungrounded Clinical LLMs (ChatGPT, Med-PaLM, Gemini):** Treat safety triage as free-form medical chat. As proved in recent clinical literature (Omar et al., *Communications Medicine*, 2025), raw LLMs hallucinate medical associations in up to 83% of edge cases and suffer from **temporal confusion** (confusing historical investigations with final regulatory outcomes).
* **Our Contribution:** PharmaGuard is the **first concrete, evaluated system in the peer-reviewed record** that bridges this gap—uniting live statistical disproportionality, target molecular pharmacology, and structured evidence grading under a deterministic, auditable safety-gating protocol (§23).

---

### 2. Five Specific Scientific Contributions (Paper-Ready):

#### Contribution A: Empirical Discovery of "Parametric Regulatory Leakage"
* In standard medical AI benchmarks, authors claim LLMs can "deduce drug mechanisms."
* We ran an ablation study (`force_agent` mode) and **experimentally proved this is an illusion**: when asked to deduce biochemistry, the LLM achieved an artificial 1.000 strict recall because it recalled the FDA's 2020 Boxed Warning from pre-training memory and injected it into its biological rationale (`DECISIONS.md §16, §19`).
* *Why it's publishable:* We provide the first empirical characterization showing that foundation models leak historical regulatory memory during clinical reasoning tasks.

#### Contribution B: Blinded Maker-Checker Adversarial Critic (MARCH Pattern)
* To solve parametric leakage, we introduced an independent adversarial critic agent inspired by information-asymmetry verification patterns (such as MARCH, ACL 2026).
* The critic audits plausibility rationales **completely blinded to drug names, event terms, and primary scores**, achieving **100% detection sensitivity (4/4)** in isolating non-mechanistic regulatory text (`DECISIONS.md §27`).
* *Why it's publishable:* This provides a transferable, domain-agnostic auditing framework for verifying that clinical AI reasoning is genuinely grounded in data rather than memorized artifacts.

#### Contribution C: Empirical Divergence Finding: Generative ReAct vs. Deterministic Safety (26.7%)
* We compared an unconstrained, generative LangGraph ReAct agent against our deterministic pipeline across all benchmark pairs.
* **Finding:** The unconstrained agent **diverged from deterministic safety rules on 4 of 15 pairs (26.7%)**, over-escalating nominal negative controls swayed by associative literature mentions (`DECISIONS.md §24`).
* *Why it's publishable:* Provides concrete empirical proof that postmarketing safety triage cannot rely on unconstrained generative LLM judgments and mandates deterministic multi-source gating.

#### Contribution D: Confounding-Aware Signal Discounting
* Addressed the classic spontaneous reporting failure mode where drug combinations (e.g., Metformin + Insulin) artificially inflate PRR to $>10.0$.
* Our opt-in confounding tool identifies concomitant medication regimens and applies a grounded discount multiplier ($0.20$), resolving the sole lenient false positive without mutating formula weights (`DECISIONS.md §28`).

#### Contribution E: Honest External Validity Characterization (The OMOP Benchmark)
* Instead of reporting synthetic "flawless" numbers, we evaluated on a secondary 32-pair OMOP benchmark (Ryan et al. 2013) and characterized a genuine epidemiological boundary: static $\text{PRR} \ge 2.0$ thresholds break down on high-utilization chronic therapies (e.g., amlodipine, SSRIs) due to denominator dilution (§31).
* *Why it's publishable:* High-impact journals (like JAMIA or Drug Safety) value honest, reproducible boundary characterizations over cherry-picked synthetic evaluations.

---

### 3. Target Publication Venues & Strategy

| Venue Type | Target Venues | Why PharmaGuard Fits |
|---|---|---|
| **Top AI & Health Conferences** | • **IEEE BIBM 2026** (IEEE Intl. Conf. on Bioinformatics and Biomedicine)<br>• **ACM CHIL** (Conference on Health, Inference, and Learning)<br>• **AMIA Annual Symposium** (American Medical Informatics Association) | Strong focus on agentic AI, biomedical tool use, clinical NLP, and multi-source safety triage. |
| **High-Impact Journals** | • **JAMIA Open** (Oxford Academic)<br>• **Journal of Biomedical Informatics (JBI)** (Elsevier)<br>• **Drug Safety** (Springer / Official Journal of ISoP) | Pharmacovigilance domain fit; values methodological rigor, empirical error analysis, and honest disclosures. |

---

## 📋 Part 4: The 5 Meeting Discussion Points (Dr. Arya's Agenda)

Dr. Arya asked for an update covering five specific areas. Here is our complete response for each:

---

### 1. Work Completed So Far

1. **Pre-Pivot Context & Problem Formulation:** Intentional pivot from an earlier oncology tumor-board simulation (OncoSwarm) in August 2026 after landscape analysis revealed Stanford's deployed system had saturated that niche. Formulated PharmaGuard to address the unaddressed problem of verifiable postmarketing signal triage.
2. **End-to-End Tool-Grounded Pipeline:** Integrated live REST APIs for **openFDA (FAERS)**, **ChEMBL**, and **NCBI PubMed**, with a persistent disk-backed caching layer (`diskcache`, `v7`) guaranteeing $100\%$ zero-cost, offline reproducibility (§3, §6).
3. **Deterministic Mathematical Decision Engine:** Implemented strict Pydantic v2 schemas and dual execution modes: **Fixed Pipeline Agent** (production) and **ReAct LangGraph Agent** (experimental) (§8, §9).
4. **Epistemic Honesty & Methodological Audits:** Built the **Adversarial Mechanistic Leakage Critic** (MARCH pattern, 100% detection) (§27), the **Confounding-Aware Discounting Tool** (§28), the **Cross-Source Agreement Metric** (§26), and **15-Fold Leave-One-Out Cross-Validation** (§29).
5. **Benchmark Datasets Curated & Verified:**
   - **Core Benchmark (15 pairs):** 7 Confirmed Positives, 5 Genuine Negative Controls, 3 Zero-Report Edge Cases with full regulatory citations (§2, §21, §22).
   - **OMOP Pilot Benchmark (32 pairs):** Derived from the international OHDSI OMOP reference set (Ryan et al. 2013) across 4 clinical endpoints (§31).
6. **Interactive Dashboard & Automated Testing:** Complete **6-tab Streamlit dashboard** (`scripts/dashboard.py`), automated Playwright 1080p screenshot suite, and **84/84 unit tests passing**.

---

### 2. Results & Outcomes Obtained

```
========================================================================================
                          KEY HEADLINE EXPERIMENTAL RESULTS
========================================================================================
Core Benchmark (15 pairs):     Strict F1 = 0.923 | Lenient F1 = 0.933
                               Strict Specificity = 1.000 (8/8 negative controls cleared)
                               Lenient Recall = 1.000 (7/7 true signals captured)
                               Spurious False Alarms = 0

Single-Shot LLM Baseline:      Strict F1 = 0.933 | Lenient F1 = 0.824 | False Alarms = 1

15-Fold LOO Stability:         Strict F1 = 0.9226 ± 0.0225 | Lenient F1 = 0.9330 ± 0.0192

Multi-Source Ablation:         Strict F1 = 0.000 across all single-source conditions,
                               confirming genuine multi-source fusion dependency

ReAct Divergence Rate:         26.7% (4/15 pairs diverged from deterministic safety rules)

Epistemic Leakage Critic:      100% Detection Sensitivity (4/4 leakage cases detected)

Confounding Resolution:        Metformin confidence discounted 0.400 -> 0.080 (Cleared FP)

OMOP Pilot (32 pairs):         Specificity = 1.000 (16/16 negative controls cleared)
                               Lenient F1 = 0.720 (9/16 true positives captured)
========================================================================================
```

#### Detailed Core Benchmark Comparison (15 Pairs)

| Evaluation Metric | PharmaGuard (Tool-Grounded) | Wilson 95% Confidence Interval | Single-Shot LLM Baseline (No Tools) | Clinical Significance |
|---|:---:|:---:|:---:|---|
| **Strict Precision** | **1.000** | [0.610, 1.000] | 0.875 | When PharmaGuard escalates, it is always a true signal. |
| **Strict Recall** | **0.857** (6/7) | [0.487, 0.974] | 1.000 | 6 of 7 positives escalated; 1 modulated to MONITOR. |
| **Strict Specificity** | **1.000** (8/8) | [0.676, 1.000] | 0.875 | **Zero false alarms** on known negative controls. |
| **Strict F1-Score** | **0.923** | [0.727, 1.000]* | 0.933 | Harmonic mean under strict gating. |
| **Lenient Recall** | **1.000** (7/7) | [0.646, 1.000] | 1.000 | **100% signal capture** — no true safety hazard is missed. |
| **Lenient Specificity**| **0.875** (7/8) | [0.529, 0.978] | 0.625 | Clears 7 of 8 negative controls without human review. |
| **Lenient F1-Score** | **0.933** | [0.769, 1.000]* | 0.824 | Harmonic mean under lenient scoring. |
| **Over-Caution Rate** | **12.5%** (1/8) | [0.022, 0.471] | **25.0%** (2/8) | PharmaGuard has half the over-caution rate of raw LLMs. |

---

### 3. Challenges & Issues Faced (And How We Solved Them)

The following six genuine technical and methodological challenges were encountered, investigated, and systematically resolved, demonstrating engineering maturity and scientific discipline:

#### Challenge A: Rubric Revision with Foreknowledge Incident & Anti-Overfitting Policy (§15, §18)
* **The Problem:** In Sprint 3, an attempted Bradford Hill plausibility rubric revision upgraded montelukast and albuterol from LOW to MODERATE, temporarily inflating strict recall to 1.000 (7/7).
* **The Resolution:** We recognized that the justification was authored with explicit foreknowledge of which pair was failing. The revision was immediately revoked, ratings were reverted to v1.0, and a permanent non-retroactive tuning policy was established: no post-hoc rubric mutations or threshold adjustments are permitted on evaluated datasets (§15, §18, §20, §31).

#### Challenge B: MARCH Citation Precision & Architectural Framing (§27)
* **The Problem:** Early design notes informally cited multi-agent review patterns.
* **The Resolution:** During the comprehensive novelty audit, this was formally standardized and grounded in the MARCH framework (ACL 2026), precisely framing our adversarial critic as a blinded information-asymmetry verification agent.

#### Challenge C: FAERS-Ablation Gate Conflation & Resolution (§30 item 4)
* **The Problem:** During multi-source ablation, setting FAERS to 0.0 artificially fired Gate 1 (NO_SIGNAL) on 8/15 pairs as a mathematical side effect of numerical zeroing, masking linear weight contributions.
* **The Resolution:** Diagnosed the conflation and created an explicit gate-bypassed analytical view to cleanly isolate linear formula weight contributions from gate dominance.

#### Challenge D: OMOP Negative-Control Collision Investigation (§31)
* **The Problem:** Questions arose regarding whether OMOP negative controls contained true literature associations.
* **The Resolution:** Conducted primary-source verification against the original Ryan et al. (2013) definition tables and FDA drug labels, successfully refuting collision concerns and validating that all 16 negative controls are clean.

#### Challenge E: ChEMBL Lookup Table Coverage Gap (§31)
* **The Problem:** Scaling to 32 OMOP drugs risked zero-score fallbacks due to missing MoA entries in `chembl_lookup.json`.
* **The Resolution:** Queried the official ChEMBL REST API to curate verified mechanisms for all 32 drugs, expanding the curated lookup from 18 to 50 drugs prior to executing the evaluation run.

#### Challenge F: Ground-Truth Curation in Complex Clinical Domains (§21, §30 item 6)
* **The Problem:** Clinical safety lacks absolute mathematical ground truth; MedDRA coding shifts occur (e.g. `TERATOGENICITY` vs `EXPOSURE DURING PREGNANCY`, or British spelling `HYPOGLYCAEMIA` returning 9,300 reports vs 0 for US spelling).
* **The Resolution:** Documented all curation decisions with primary FDA/EMA citations in `GROUND_TRUTH_CANDIDATES.md` and `CONVENTIONS.md`, and resolved MedDRA spelling variants.

---

### 4. Work Planned for the Next Phase

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          NEXT PHASE ROADMAP & TIMELINE                          │
├──────────────────────┬──────────────────────────────────────────────────────────┤
│ Phase 4.1 (Week 1–2) │ Dynamic Statistical Gating (Lower CI Bound / Bayes EBGM) │
│ Phase 4.2 (Week 3–4) │ MedDRA Ontology Canonicalization Layer (LLT -> PT)      │
│ Phase 4.3 (Week 5–6) │ Clinical Pharmacologist Expert Validation Protocol      │
│ Phase 4.4 (Week 7–8) │ Conference Paper Drafting & Final Capstone Defense Deck │
└──────────────────────┴──────────────────────────────────────────────────────────┘
```

1. **Academic Paper Manuscript Drafting:** Currently gated on supervisor review and explicit sign-off per DECISIONS.md §25 standing instructions. We are awaiting Dr. Arya's approval to proceed with formal drafting targeting **IEEE BIBM 2026** or **ACM CHIL**.
2. **Dynamic Disproportionality Gating:** Upgrade the static $\text{PRR} < 2.0$ threshold to a dynamic statistical test (e.g. $\text{PRR}_{\text{lower\_ci}} > 1.0$ or Empirical Bayes Geometric Mean [EBGM]) to rescue chronic diluted signals without adding false positives (§31).
3. **MedDRA Ontology Normalization Layer:** Implement an automatic term-resolution layer that maps colloquial symptoms and British spellings (e.g., *hypoglycaemia* $\to$ *hypoglycemia*) to official MedDRA Preferred Terms (§21, §30).
4. **External Clinical Validation Protocol:** Design a formal blinded review protocol where certified clinical pharmacologists evaluate our biological plausibility scores (§20, §30).

---

### 5. Support & Guidance Required from Dr. Arya

We will ask Sir for his input on these specific points:

1. **Publication Venue & Manuscript Scope:** Does Sir recommend targeting a computer science / biomedical informatics conference (e.g., IEEE BIBM 2026, ACM CHIL) or a medical informatics journal (e.g., JAMIA Open, Journal of Biomedical Informatics)?
2. **Threshold Gating Strategy:** What is his recommendation on replacing static cutoffs ($\text{PRR} \ge 2.0$) with statistical lower bounds ($\text{PRR}_{\text{lower\_ci}} > 1.0$) or Bayesian shrinkage for high-volume chronic drugs?
3. **Secondary Benchmark Cohort Size:** Is the current 32-pair OMOP secondary pilot sufficient to substantiate our external validity claims for an undergraduate capstone, or would Sir recommend scaling to a 64-pair cohort?
4. **Defense Presentation Structure:** Guidance on structuring our final 15-minute 16:9 widescreen presentation deck and live dashboard demonstration.

---

## 📖 Part 5: Four Key Case Studies to Memorize

If Sir asks for specific examples of how the system works, cite these four cases:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. LIRAGLUTIDE + PANCREATIC CANCER (The Grounding Victory)                             │
│    • Story: Historical safety concern raised in 2013, but FDA/EMA cleared it in 2014.   │
│    • Ungrounded Baseline: Hallucinated an ESCALATE from old pre-training memory.        │
│    • PharmaGuard: Checked FAERS, found 0 reports, enforced Gate 1 -> DO_NOT_ESCALATE.   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. MONTELUKAST + SUICIDAL IDEATION (The Honest Uncertainty Case)                       │
│    • Story: FDA Boxed Warning exists, but biological mechanism in the brain is unproven.│
│    • Curated Plausibility: Rated LOW (0.0) because mechanism is not pharmacologically   │
│      confirmed in airways receptors.                                                    │
│    • Output: Confidence = 0.664 -> MONITOR. (Lenient True Positive, honest caution).    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. METFORMIN + HYPOGLYCAEMIA (The Confounding Artifact Case)                           │
│    • Story: 9,300+ FAERS reports caused by co-prescribed insulin in diabetics.          │
│    • Raw Formula: Gave MONITOR due to high raw PRR (10.73).                             │
│    • Confounding Tool: Detected polypharmacy, applied 0.20 discount -> DO_NOT_ESCALATE. │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. CITALOPRAM + GI HAEMORRHAGE (The OMOP Chronic Dilution Case)                        │
│    • Story: SSRI antidepressant inhibits platelet serotonin, increasing bleeding risk. │
│    • Plausibility: HIGH (1.0). But high prescription volume diluted FAERS PRR to 1.904. │
│    • Output: Tripped PRR < 2.0 gate -> DO_NOT_ESCALATE. Proves static threshold limit.  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Part 6: Anticipated Viva / Meeting Questions & Ideal Answers

### Q1: "Why not just ask ChatGPT or Gemini directly to triage drug safety signals?"
> **Ideal Answer:**  
> *"Ungrounded LLMs suffer from three critical failure modes in pharmacovigilance: (1) they hallucinate clinical facts when prompted, (2) they suffer from temporal confusion—recalling past safety investigations that were later dismissed, and (3) their confidence scores are uncalibrated self-reports. PharmaGuard forces the LLM to act as a grounded tool-using agent that retrieves real statistical data from openFDA, mechanisms from ChEMBL, and literature from PubMed, combining them with a deterministic formula rather than opaque generative text."*

### Q2: "What is genuinely novel about this project compared to existing papers?"
> **Ideal Answer:**  
> *"PharmaGuard is novel across three key dimensions: (1) It is the first architecture to unite live epidemiological disproportionality, molecular target mechanisms, and literature grading under a deterministic safety gate. (2) We experimentally proved 'regulatory leakage' in medical LLMs—showing models recall FDA warnings rather than deducing biochemistry—and built a blinded maker-checker adversarial critic (MARCH pattern) to detect it. (3) We proved that unconstrained ReAct agents diverge from safety rules in 26.7% of cases, providing empirical justification for deterministic multi-source gating."*

### Q3: "Why did you choose the weights 0.40 FAERS, 0.40 PubMed, 0.20 ChEMBL?"
> **Ideal Answer:**  
> *"These weights represent a clinically motivated prior: real-world spontaneous reporting (FAERS) and published peer-reviewed medical literature (PubMed) are treated as co-equal primary evidence (0.40 each), while molecular mechanism plausibility (ChEMBL) is treated as corroborating context (0.20). We explicitly disclose in our documentation (DECISIONS.md §18) that these are fixed priors rather than empirically overfitted values, because calibrating weights on a small dataset risks severe overfitting."*

### Q4: "What does the 26.7% ReAct divergence finding prove?"
> **Ideal Answer:**  
> *"When we allowed an unconstrained LangGraph ReAct agent to decide final escalation dynamically from conversational state, it diverged from deterministic safety rules on 4 of 15 pairs (26.7%). For example, it escalated nominal negative controls because it was swayed by conversational literature mentions. This provides empirical proof that safety-critical triage requires deterministic gating rather than free-form LLM judgment."*

### Q5: "Why did your Strict Recall drop on the OMOP 32-pair pilot?"
> **Ideal Answer:**  
> *"On the 16 OMOP confirmed positives, 6 pairs were widely used chronic medications (such as amlodipine and SSRIs). Because millions of patients take these drugs, their adverse event reporting is diluted by massive denominator volume, bringing their PRR point estimate to between 1.16 and 1.90. Our static PRR < 2.0 gate zeroed these signals despite their lower 95% confidence intervals clearing 1.0 and high biological plausibility. Rather than secretly modifying our thresholds post-hoc, we documented this finding as an honest external validity boundary of static thresholding."*

### Q6: "Is your system expensive to run or reliant on paid API keys?"
> **Ideal Answer:**  
> *"No, sir. All external data sources (openFDA, ChEMBL, PubMed E-utilities) are public, free APIs. We use Google's free-tier `gemini-3.1-flash-lite` model for reasoning. Furthermore, our disk-backed cache allows the entire 6-tab Streamlit dashboard and test suite to run with zero network calls and zero cost during evaluation and live presentation."*

---

## 🛠️ Part 7: Quick Checklist for Tomorrow's Meeting

- [ ] **Laptop Battery & Charger:** Fully charged.
- [ ] **Local Dashboard Ready:** Launch with `.venv\Scripts\streamlit.exe run scripts/dashboard.py` (verified running on port 8501 / 8544).
- [ ] **Tabs Walkthrough Order:** Overview $\to$ Per-Pair Table $\to$ Disagreement Spotlight $\to$ Baseline Comparison $\to$ Methodology Probes $\to$ OMOP Pilot.
- [ ] **Test Suite Confirmation:** 84/84 tests passing (`pytest`).
- [ ] **Printed / PDF Copy of this Briefing:** Exported from this markdown file.

---
*End of Briefing Document — Group 07, IIIT Allahabad (September 2026)*
