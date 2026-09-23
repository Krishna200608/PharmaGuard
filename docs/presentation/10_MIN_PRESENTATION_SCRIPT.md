# PharmaGuard — 10-Minute Defense Presentation & Live Demo Script
### Minute-by-Minute Rehearsal Guide, Transition Cues, and Live Dashboard Demo Sequence

**Target Event:** B.Tech 7th-Semester Capstone Project Defense (2026–27) · IIIT Allahabad  
**Team (Group 07):** Krishna Sikheriya (IIT2023139, Presenter) · Lokesh Bawariya (Teammate) · Naitik Jain (Teammate)  
**Supervisor:** Dr. Nikhilanand Arya, Assistant Professor, Department of Information Technology  
**Presentation Target:** Strictly **10 Minutes (600 Seconds)** + 5 Minutes Committee Q&A  

---

## ⏱️ Master Pacing & Timing Breakdown

```
[0:00 - 1:30]  Phase 1: Problem & The Pharmacovigilance Bottleneck (Slides 1–3)
[1:30 - 3:30]  Phase 2: Tri-Source Architecture & Safety Gating (Slides 4–7)
[3:30 - 5:00]  Phase 3: Deep Dives: Indication Concordance & Scoring-Inert Wall (Slides 8–12)
[5:00 - 7:00]  Phase 4: Multi-Scale Benchmark Results ($N=165$) & PRR Dilution (Slides 13–15)
[7:00 - 8:30]  Phase 5: LIVE DASHBOARD DEMONSTRATION (http://localhost:8501/)
[8:30 - 10:00] Phase 6: Engineering Rigor, Future Scope & Transition to Q&A (Slides 16–20)
```

---

## Phase 1: Problem & Motivation (0:00 – 1:30)

### Slide 1: Title & Project Identity (0:00 – 0:30)
- **Visual Cue:** Slide 1 displays title, Group 07 members, and Dr. Arya's supervision.
- **Presenter (Krishna):**
  > *"Good morning Dr. Arya and respected members of the evaluation committee. I am Krishna Sikheriya, presenting on behalf of Group 07 alongside my teammates Lokesh Bawariya and Naitik Jain. Today we defend **PharmaGuard**: an intelligent, tool-grounded pharmacovigilance signal triage orchestrator for postmarketing adverse drug event surveillance."*

### Slide 2: The Pharmacovigilance Bottleneck (0:30 – 1:00)
- **Visual Cue:** Slide 2 contrasts small clinical trials with spontaneous reporting databases.
- **Presenter (Krishna):**
  > *"Clinical trials involve small, homogeneous cohorts. Once a drug is marketed to millions, unexpected toxicities inevitably emerge. Spontaneous reporting systems like the US FDA FAERS receive millions of reports annually. However, clinical safety teams face an acute triage bottleneck: separating real emergent toxicities from statistical noise, polypharmacy confounding, and disease natural history is an overwhelmingly manual, non-scalable burden. False alarms cause severe clinician alert fatigue, while missed signals allow preventable patient harm to compound."*

### Slide 3: Introduction: What PharmaGuard Is (1:00 – 1:30)
- **Visual Cue:** Slide 3 highlights the 3 tiers (`ESCALATE`, `MONITOR`, `DO_NOT_ESCALATE`) and public-API claim.
- **Presenter (Krishna):**
  > *"PharmaGuard is an autonomous biomedical agent that triages drug–adverse event pairs into three auditable tiers: ESCALATE, MONITOR, or DO_NOT_ESCALATE. Crucially, unlike recent causal AI methods that depend on restricted hospital electronic health records, PharmaGuard operates **strictly on public, open-access biomedical APIs**—FAERS, ChEMBL, and PubMed. By replacing generative LLM decision-making with deterministic mathematical formulas and empirical safety gates, we eliminate the hallucinated confidence and historical regulatory confusion documented in ungrounded models."*

---

## Phase 2: Tri-Source Architecture & Safety Gating (1:30 – 3:30)

### Slides 4–6: Current Standard & Literature Evolution (1:30 – 2:30)
- **Visual Cue:** Slide 4 (classical PRR $2 \times 2$ table) and Slide 6 (3 generations of PV literature).
- **Presenter (Krishna):**
  > *"Historically, regulatory agencies relied on Generation 1 disproportionality metrics like the Proportional Reporting Ratio (PRR) from Evans et al. (2001). While fast, statistical ratios are blind to biological mechanisms and vulnerable to confounding. Generation 2 introduced machine learning on hospital records, but locked models behind private health databases. Generation 3 brings LLMs, but as Omar et al. (2025) proved, foundation models self-score confidence above 0.85 without verifiable statistics. PharmaGuard fills this gap: a lightweight, disease-context-aware agent delivering regulatory auditability using open APIs."*

### Slide 7 & 9: Tri-Source Evidence Fusion Architecture (2:30 – 3:30)
- **Visual Cue:** Slide 9 architecture diagram showing FAERS (0.40), PubMed (0.40), ChEMBL (0.20), and Gate 1.
- **Presenter (Krishna):**
  > *"Slide 9 shows our tri-source fusion pipeline. We combine three orthogonal evidence streams: openFDA FAERS disproportionality with Woolf 95% log-confidence intervals, ChEMBL receptor-level Mechanism of Action, and PubMed literature graded against an epidemiological clinical rubric. 
  > Our composite confidence is computed via a closed-form formula: 0.40 FAERS, 0.40 PubMed, and 0.20 ChEMBL.
  > Most importantly, Gate 1 enforces a hard empirical stop: if FAERS shows NO_SIGNAL, the system immediately forces DO_NOT_ESCALATE. Literature speculation alone can never trigger an ungrounded alert."*

---

## Phase 3: Indication Concordance & The Scoring-Inert Wall (3:30 – 5:00)

### Slides 10–12: Disease Context & The Anti-Overfitting Isolation Wall (3:30 – 5:00)
- **Visual Cue:** Slide 10 (WHO ATC ontology), Slide 11 (7 clinical rules), Slide 12 (Scoring-Inert Wall).
- **Presenter (Krishna):**
  > *"A fundamental challenge in pharmacovigilance is confounding by indication: a drug given for heart disease frequently co-occurs with heart attacks because of the patient's underlying illness. In response to Dr. Arya's guidance, we built a disease-context engine resolving WHO ATC hierarchies via ChEMBL across 7 clinical rules—audited through two rounds of independent citation verification against PubMed.
  > However, our core architectural innovation in Slide 12 is the **Scoring-Inert Isolation Wall**. Pharmacoepidemiological consensus (Walker 1996, Psaty 1999) establishes that confounding by indication has no universal scalar discount constant. When we tested active score discounting, it caused false-positive regressions on Atorvastatin and Dementia. By keeping Indication Concordance strictly as an informational provenance flag, we provide complete transparency to clinicians without overfitting the scoring engine."*

---

## Phase 4: Multi-Scale Benchmark Results ($N=165$) (5:00 – 7:00)

### Slide 13–15: Master Evaluation Matrix & PRR Denominator Dilution (5:00 – 7:00)
- **Visual Cue:** Slide 15 master cross-benchmark table covering all 165 evaluated pairs.
- **Presenter (Krishna):**
  > *"We validated PharmaGuard across three multi-scale benchmarks totaling 165 pairs:
  > 1. On our 15-pair Core Showcase, PharmaGuard achieved a 0.923 Strict F1 and halved clinician over-caution from 25% down to 12.5% compared to the single-shot baseline.
  > 2. On 50 Top Prescribed Blockbusters, PharmaGuard captured 92.0% of confirmed high-mortality FDA Boxed Warnings with a 0.9388 Lenient F1 and 96.0% specificity.
  > 3. On the 100-pair OMOP reference standard, PharmaGuard achieved **100% Strict Specificity**—all 50 negative controls were completely cleared with zero false alarms.
  > Crucially, on OMOP, we discovered **PRR Denominator Dilution**: for chronic blockbuster drugs like Amlodipine and SSRIs, tens of millions of prescriptions dilute the raw PRR into the 1.1 to 1.9 range, causing single-source statistical tools to drop them. PharmaGuard's tri-source fusion safely routed these chronic toxicities into MONITOR, proving why our dual-metric framework is essential."*

---

## Phase 5: LIVE DASHBOARD DEMO (7:00 – 8:30)

### 🖥️ Switch Display to Browser: `http://localhost:8501/`

#### Step 1: Show Global Benchmark Cohort Switcher (15 Seconds)
- **Action:** Point cursor to top-bar segmented control.
- **Voiceover:**
  > *"Here is our live evaluation dashboard running on localhost:8501. Reviewers can toggle the top-bar switcher between Core Showcase [15], Top Prescribed [50], and OMOP Expanded [100]. Switching re-renders the KPI cards, confusion matrices, and Leave-One-Out stability distributions dynamically."*

#### Step 2: Navigate to 'Live Signal Triage' (15 Seconds)
- **Action:** Click the **`Live Signal Triage`** tab.
- **Voiceover:**
  > *"In our Live Signal Triage playground, safety officers can search 151 benchmark presets or enter arbitrary drug–event pairs."*

#### Step 3: Run Live Demonstration on `Metformin` + `Hypoglycaemia` (30 Seconds)
- **Action:** Select preset: `Metformin — Hypoglycaemia (Negative Control)` $\to$ Click **`Run Triage`** (Primary button).
- **Voiceover:**
  > *"Let's test Metformin and Hypoglycaemia. Notice that FAERS contains 9,344 spontaneous reports with a PRR of 10.73—a classical polypharmacy trap caused by co-prescribed insulin. 
  > Watch how PharmaGuard handles this: the pipeline queries ChEMBL and finds zero molecular plausibility for insulin stimulation, while PubMed literature confirms polypharmacy confounding. 
  > The composite confidence is de-escalated to 0.4000, safely routing the signal to MONITOR and preventing a false alarm."*

#### Step 4: Showcase the Single-Click Clinical Dossier Export (30 Seconds)
- **Action:** Click **`Download Clinical Dossier (.md)`** right below the Verdict Card $\to$ Open the downloaded file or switch to the **`Clinical Dossier Preview`** tab below.
- **Voiceover:**
  > *"Furthermore, safety officers can click 'Download Clinical Dossier' to immediately export a complete, regulatory-ready Pharmacovigilance Safety Briefing containing the 2x2 contingency table, Woolf 95% confidence intervals, ChEMBL receptor audit trail, and cryptographic SHA-256 verification signature."*

---

## Phase 6: Engineering Rigor, Future Scope & Q&A (8:30 – 10:00)

### Slide 18–20: Engineering Stack, Publications & Conclusion (8:30 – 10:00)
- **Visual Cue:** Slide 18 (Local Ollama, 242 tests), Slide 17 (Roadmap), Slide 20 (Conclusion).
- **Presenter (Krishna):**
  > *"To support unmetered, zero-cost scaling, PharmaGuard now runs fully offline on local Ollama using qwen2.5:7b alongside cloud Gemini. Our codebase contains 242 automated pytest unit tests passing with 100% green status, guaranteed by deterministic SHA-256 caching.
  > Our complete 9-section conference paper manuscript is drafted and ready for review. In Semester 8, we plan to expand data ingestion to European and Japanese databases and incorporate automated MedDRA hierarchical roll-up.
  > In conclusion, PharmaGuard proves that grounding AI in deterministic biomedical tools eliminates hallucinations, enforces safety stops, and cuts clinician alert fatigue in half. 
  > Thank you Dr. Arya and committee members. We are now open for your questions."*

---

## 🎯 Presenter Contingency Checklist

| Scenario | Presenter Action |
|---|---|
| **Ollama Daemon is Stopped** | Switch dropdown provider to *Gemini 3.1 Flash (Cloud API)* or demonstrate from pre-computed cache. |
| **Timer reaches 8:00 before demo** | Skip slide 16/17, jump straight to the 1-minute live demo on Metformin, then close on Slide 20. |
| **Committee interrupts during demo** | Leave the live triage result on screen; use the 4 pillar cards and the Dossier Preview tab to directly answer their question. |
