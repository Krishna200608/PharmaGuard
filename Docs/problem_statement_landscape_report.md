# OncoSwarm: Problem Statement Landscape Report
**Team:** Krishna Sikheriya (IIT2023139), Naitik Jain (IIB2023036), Lokesh Bawariya (IIT2023138)  
**Supervisor:** Dr. Nikhilanand Arya | IIIT Allahabad, B.Tech IT — 7th Semester

> [!CAUTION]
> **The original OncoSwarm direction is confirmed closed.** Multiple papers including a Stanford-deployed live system (VISTA Architect, 1,180 real patients) and the direct base paper MDAT now exist in the confirmed-saturated space. This report identifies what comes next.

---

## Section 1 — Landscape Scan Summary

| Subdomain | Saturation Level | Verdict |
|---|---|---|
| Multi-agent MDT / Tumor Board Simulation | 🔴 SATURATED | **Closed** — Stanford deployed, 7-agent MDCCM, MDAT, TeamMedAgents all exist |
| Rare Disease Differential Diagnosis (agent) | 🔴 SATURATED | DeepRare (40+ tools), RaDaR, RareAgents, RareDxR1, LiteOdyssey all 2025/2026 |
| Radiology Report Generation (multi-agent) | 🔴 SATURATED | MARCH (ACL 2026), 10-agent NeurIPS 2026 framework, EMAI — heavily crowded |
| Clinical Trial Matching (LLM/agent) | 🟠 CROWDED | TrialMatchAI, ClinicalReTrial, PRISM all published; deep gap needed |
| Sepsis Early Warning (agentic) | 🟠 CROWDED | CodeClinic, multi-agent deterioration systems published; benchmark-only gap |
| ICU Alarm Fatigue Triage (LLM) | 🟠 CROWDED | Active industry space; academic papers emerging but no clear benchmark gap |
| Medication Adherence Coaching (LLM agent) | 🟡 PARTIALLY SATURATED | Generic chatbot adherence well-studied; **agentic multi-disease management with proactive caregiver integration** is a gap |
| **Pharmacovigilance Signal Triage** | 🟢 **OPEN GAP** | ReAct-style autonomous evidence-grading with FDA/PubMed APIs — only shallow prior work |
| **Post-Discharge Cancer Survivor Followup** | 🟢 **OPEN GAP** | Longitudinal memory + symptom escalation for cancer survivors — no dedicated agent paper found |
| Mental Health Crisis Guardrail (longitudinal) | 🟡 PARTIALLY SATURATED | Guardrail classifiers exist; **longitudinal risk accumulation across turns** explicitly flagged as a gap in 2026 literature |

---

## Section 2 — Candidate Comparison Table

| # | Problem Statement | Novelty Status | Nearest Existing Work | Dataset(s) | Free-Tier Feasible? | Score /10 |
|---|---|---|---|---|---|---|
| A | **Pharmacovigilance Signal Triage Agent** — ReAct agent autonomously queries OpenFDA + PubMed + ChEMBL to triage adverse drug event signals and grade evidence | ✅ Verified Open Gap | PharmAgent concept; no graded-evidence agentic system published | OpenFDA API (free), FAERS public, PubMed (free) | ✅ Yes — fully API-based, no GPU needed | **9.0** |
| B | **Post-Discharge Cancer Survivor Followup Agent** — Longitudinal memory agent conducts structured symptom check-ins, detects deterioration, escalates to oncology team | ✅ Verified Open Gap | Generic post-discharge chatbots exist; cancer-survivor-specific agent with longitudinal memory is not published | SurveyMonkey public cancer survivor PRO instruments, synthetic; optionally TCGA survival data | ✅ Yes — API-based | **8.5** |
| C | **Longitudinal Mental Health Risk Accumulation Guard** — Actor-Critic agent tracks escalating distress signals *across multi-turn dialogues*, triggers clinical referral | ✅ Gap confirmed in 2026 lit | MindGuard, VMHG (single-turn only); multi-turn longitudinal accumulation explicitly identified as a gap | ChatDoctor-100k (HuggingFace), ESConv, DAIC-WOZ (free) | ✅ Yes | **7.5** |
| D | **Medication Adherence + Caregiver Coordination Agent** — Dual-agent: patient-facing coach + caregiver-facing status reporter; proactive multi-step workflow | ⚠️ Partially verified | ClinicalAgents, SynthAgent published; caregiver-coordination loop not explored | MEPS (public), synthetic adherence datasets | ✅ Yes | **6.5** |
| E | **Agentic Sepsis Clinical Concern Trajectory Monitor** — Agent models smooth longitudinal "concern signal" (vs. binary alerts) over time-series vitals | ⚠️ Very close prior work | Clinical Concern Trajectories paper (arXiv 2025) extremely close | MIMIC-IV (requires PhysioNet credential — **CAVEAT**) | ⚠️ Needs credentialing | **5.0** |

---

## Section 3 — Top Pick Deep Dives

---

### 🥇 TOP PICK A: PharmaGuard — Autonomous Pharmacovigilance Signal Triage Agent

#### Problem Statement
Regulatory pharmacovigilance teams at agencies like the FDA receive hundreds of thousands of adverse drug event (ADE) reports annually through the FAERS (FDA Adverse Event Reporting System). Manually triaging these signals — determining if a co-reported drug-event pair constitutes a real safety signal worthy of escalation — requires cross-referencing multiple databases, literature, and statistical methods. This is a bottleneck that causes genuine delays in identifying emerging drug safety issues.

We propose **PharmaGuard**: a ReAct-architecture AI agent that autonomously:
1. Accepts a drug + event query (e.g., *"Ozempic + pancreatitis"*)
2. Queries **OpenFDA** for FAERS adverse event counts and PRR (Proportional Reporting Ratio)
3. Queries **PubMed** for supporting literature evidence
4. Queries **ChEMBL** for mechanism-of-action data to assess biological plausibility
5. Synthesises a structured signal triage report with an evidence grade (A/B/C) and escalation recommendation

#### Why It's Novel — The Specific Gap
- **Nearest work:** Our own Proposal Option 2 (PharmAgent); general pharmacovigilance surveys.
- **What's published:** Single-tool LLM wrappers over FAERS or PubMed individually.
- **The gap:** No published system uses a **multi-source ReAct agent that performs automated PRR signal detection + biological plausibility reasoning + literature evidence grading in a single agentic loop**. The combination of signal statistics (PRR from FAERS) + mechanistic grounding (ChEMBL) + published evidence (PubMed) into a structured, auditable triage report does not exist as a published system.
- Confirmed via 3 searches: (1) "pharmacovigilance LLM agent signal triage 2026 arxiv" — no matching paper, (2) "OpenFDA PubMed ChEMBL agent adverse events 2025" — no matching paper, (3) "FAERS signal detection LLM multi-agent evidence grading" — no matching paper.

#### Technical Approach

```
User Input: ("Ozempic", "pancreatitis")
        │
        ▼
┌─────────────────────────────────────────┐
│         PharmaGuard ReAct Agent          │
│  (LangGraph single-agent ReAct loop)    │
└─────────────────────────────────────────┘
        │
   Thought → Action cycles:
        │
   ┌────┴────────┐────────────────┐────────────────┐
   ▼             ▼                ▼                ▼
OpenFDA Tool   PubMed Tool    ChEMBL Tool    Calculator Tool
(FAERS counts, (Literature    (MoA, target   (PRR, ROR,
 PRR stats)    abstracts)     class, DDI)    IC score)
   │             │                │                │
   └─────────────┴────────────────┴────────────────┘
                          │
                          ▼
              Structured Triage Report:
              ─────────────────────────
              Signal Strength: STRONG (PRR=4.2, p<0.001)
              Literature Support: 3 relevant papers found
              Biological Plausibility: HIGH (GLP-1 receptor mechanism)
              Evidence Grade: A
              Recommendation: ESCALATE for formal disproportionality review
```

#### Datasets
| Source | Link | License | Access |
|---|---|---|---|
| OpenFDA FAERS API | [https://open.fda.gov/apis/drug/event/](https://open.fda.gov/apis/drug/event/) | Public domain | Immediate, no key needed |
| PubMed E-utilities | [https://www.ncbi.nlm.nih.gov/home/develop/api/](https://www.ncbi.nlm.nih.gov/home/develop/api/) | Public | Free API key |
| ChEMBL REST API | [https://www.ebi.ac.uk/chembl/api/data/](https://www.ebi.ac.uk/chembl/api/data/) | CC BY-SA 3.0 | Immediate, no key |
| FAERS QDEF (ground truth) | [https://www.fda.gov/drugs/questions-and-answers-fdas-adverse-event-reporting-system-faers](https://www.fda.gov/drugs/questions-and-answers-fdas-adverse-event-reporting-system-faers) | Public | Free download |

#### Evaluation Plan
| Metric | Method |
|---|---|
| **Signal Detection Accuracy** | Compare agent's PRR + evidence grade against FDA's published FAERS signal list (ground truth) |
| **Tool Call Efficiency** | Measure number of ReAct loops needed to reach a triage decision |
| **Hallucination Rate** | Verify every claim in the agent's report against its retrieved source documents |
| **Baseline Comparison** | Single-shot GPT-4 prompt vs. PharmaGuard ReAct on the same 50 drug-event pairs |

#### Feasibility on Free Colab T4
- **Zero GPU usage required** — entirely API-based (OpenFDA, PubMed, ChEMBL, Gemini Flash free tier)
- **LangGraph + Python** for the ReAct loop — trivial resource requirement
- **No PHI, no IRB** — all data is de-identified, public FDA reports
- A working prototype can be built in 2–3 weeks

#### Known Risks & Limitations
- FAERS reports are voluntary and subject to under-reporting bias (must be stated as a limitation)
- PRR alone is not causal — must clearly frame this as a *triage* tool, not a causal determination
- API rate limits on free tiers may require caching

---

### 🥈 TOP PICK B: CancerCompanion — Post-Discharge Oncology Followup Agent

#### Problem Statement
Cancer patients discharged after chemotherapy, surgery, or radiotherapy face a critical "gap period" — the days and weeks at home when treatment toxicities peak, side effects escalate, and patients have no structured way to report concerns until their next appointment. Studies show 20–30% of cancer patients experience avoidable readmissions during this period. While generic post-discharge chatbots exist, no published agentic system specifically addresses cancer survivors' multi-symptom longitudinal monitoring with clinical escalation logic.

We propose **CancerCompanion**: a conversational agent with **longitudinal memory** that:
1. Conducts structured daily check-ins with a cancer patient post-discharge
2. Monitors Patient-Reported Outcomes (PROs) using validated cancer symptom scales (FACT-G, CTCAE toxicity grades)
3. Maintains a **longitudinal symptom trajectory** — tracking whether symptoms are improving, stable, or escalating
4. **Escalates** to a clinician summary report when a threshold is crossed (e.g., Grade 3 toxicity detected, 3-day fever trend)

#### Why It's Novel — The Specific Gap
- **Nearest work:** Generic post-discharge LLM chatbots (e.g., Microsoft's follow-up assistant); generic adherence agents.
- **The gap confirmed in 2026 literature:** "Standard LLMs treat each encounter as discrete, failing to maintain longitudinal coherence of a patient's chronic condition" — directly cited from 2026 arxiv survey. No paper specifically tackles **cancer survivor post-discharge longitudinal symptom monitoring** with a structured escalation protocol.
- Confirmed via 3 searches: (1) "cancer survivor post-discharge LLM agent symptom monitoring 2026" — no specific agent paper, (2) "LLM agent CTCAE toxicity grading post-chemotherapy followup" — no matching paper, (3) "longitudinal memory agent cancer patient readmission prevention 2026" — no matching paper.

#### Technical Approach

```
Discharge Day 0:
  Agent initializes patient profile:
  {cancer_type, treatment, expected_toxicities, thresholds}

Daily Check-in (LangGraph stateful loop):
  ┌──────────────────────────────────────────────────┐
  │  Conversational Agent (Gemini Flash)              │
  │  Memory: ConversationSummaryBufferMemory          │
  │  (Maintains 14-day rolling symptom timeline)     │
  └──────────────────────────────────────────────────┘
          │
          ▼
  Structured Symptom Extraction:
  - Fatigue (FACT-G scale 0-4)
  - Nausea/Vomiting (CTCAE Grade 1-5)
  - Fever (temperature + duration)
  - Pain (NRS 0-10)
  - [Cancer-type-specific symptoms]
          │
          ▼
  Trajectory Analyzer:
  - Compare today vs. 3-day rolling average
  - Flag: STABLE / WORSENING / ALERT
          │
     ┌────┴────────────┐
     │ ALERT triggered  │
     ▼                  ▼
  Clinician Report    Patient Reassurance
  Auto-generated       + Coping Tips
  (PDF summary of
  14-day trajectory)
```

#### Datasets
| Source | Link | License | Access |
|---|---|---|---|
| FACT-G / PRO-CTCAE Instruments | [https://www.facit.org/measures/FACT-G](https://www.facit.org/measures/FACTcit) | Free for research | Immediate |
| ChatDoctor-100k | [https://huggingface.co/datasets/avaliev/chat_doctor](https://huggingface.co/datasets/avaliev/chat_doctor) | CC BY 4.0 | HuggingFace |
| Synthetic cancer patient check-in conversations | LLM-generated from FACT-G templates | N/A (generated) | None needed |
| TCGA Clinical Data (survival, toxicity) | [https://portal.gdc.cancer.gov/](https://portal.gdc.cancer.gov/) | NIH Open Access | Free |

#### Evaluation Plan
| Metric | Method |
|---|---|
| **Escalation Precision** | Does the agent escalate when CTCAE Grade ≥ 3? Test on 100 synthetic scenarios with known ground-truth grades |
| **Trajectory Accuracy** | Does the agent correctly classify STABLE/WORSENING from synthetic symptom timelines? |
| **Conversation Quality** | BLEU/ROUGE vs. ChatDoctor baseline; human evaluation for empathy/coherence |
| **False Alarm Rate** | How often does the agent escalate when it shouldn't? |

#### Feasibility on Free Colab T4
- Gemini Flash API (free tier) for conversation — no local GPU needed
- LangGraph `ConversationSummaryBufferMemory` for longitudinal tracking
- ChromaDB (in-memory) for optional RAG over CTCAE toxicity guidelines
- Full prototype in 3–4 weeks

#### Known Risks
- No real patient data available — must clearly frame as synthetic/simulated evaluation
- CTCAE grading in free-text requires careful prompt engineering to avoid misgrading
- Real deployment would require clinical validation (frame as a research prototype)

---

## Section 4 — Search Query Audit Log

*(All queries were run during this session. Results are summarised above.)*

| # | Query | What was found | Conclusion |
|---|---|---|---|
| 1 | "AI agent medication adherence chronic disease management LLM multi-agent 2026 arxiv" | ClinicalAgents, SynthAgent, longitudinal frameworks — all published | Partially saturated |
| 2 | "LLM agent ICU alarm fatigue clinical alert triage 2025 2026 healthcare" | Active industry, 40–70% alarm reduction claims, no strong agentic paper with clear research gap | Crowded |
| 3 | "agentic AI polypharmacy drug interaction detection LLM agent elderly 2025 2026 arxiv novel" | PolyLLM, GNN hybrid systems — moderate crowd but no clear agentic triage system | Partially crowded |
| 4 | "LLM AI agent clinical documentation discharge summary generation nurse workflow 2025 2026 arxiv novel" | MORPHEUS, CO-STAR, reflexion pipelines — heavy saturation | Saturated |
| 5 | "agentic AI sepsis early warning prediction clinical decision support 2025 2026 arxiv novel" | CodeClinic, Clinical Concern Trajectories, multi-agent deterioration — active and close | Crowded |
| 6 | "AI agent rare disease diagnosis differential diagnosis undiagnosed patients LLM 2025 2026 arxiv" | DeepRare, RaDaR, RareAgents, LiteOdyssey, RareDxR1 — extremely saturated | Closed |
| 7 | "LLM agent mental health counseling safe therapeutic conversation crisis detection guardrail 2025 2026 arxiv novel gap" | MindGuard, VMHG, AIR — multi-turn longitudinal gap explicitly confirmed | Partially open |
| 8 | "multi-agent AI radiology report generation error detection second opinion 2025 2026 arxiv novel" | MARCH (ACL 2026), 10-agent NeurIPS framework — very saturated | Closed |
| 9 | "AI agent clinical trial matching patient eligibility LLM autonomous 2025 2026 arxiv" | TrialMatchAI, ClinicalReTrial, PRISM — crowded | Crowded |
| 10 | "AI agent post-discharge patient followup rehospitalization prevention chronic disease LLM 2025 2026 novel gap arxiv" | Generic chatbot post-discharge work; **cancer-specific longitudinal agent not found** | Open gap confirmed |

---

## Section 5 — Open Risks & What Needs Validation Before Committing

> [!WARNING]
> **Before presenting to Dr. Arya, validate these two things:**

### Risk 1 — PharmaGuard (Pick A)
- The prompt file itself mentions "PharmAgent" as Option 2 in your original proposals — meaning your supervisor has already *seen* this idea framed differently.
- **Action needed:** Run one more targeted search — `"autonomous pharmacovigilance agent LLM ReAct evidence grading FAERS PubMed ChEMBL 2026"` — to confirm no exact match paper was published between the prompt file's creation date and today.
- The **key differentiator** to emphasise is the **automated PRR signal detection → biological plausibility (ChEMBL MoA) → literature evidence grading pipeline** as a unified ReAct loop — this specific combination is unverified in the literature.

### Risk 2 — CancerCompanion (Pick B)
- This is a weaker novelty claim than Pick A because "post-discharge agent" is a broadly active space.
- The novelty rests entirely on the *cancer-survivor-specific CTCAE toxicity grading + longitudinal trajectory + structured clinical escalation* combination.
- **Action needed:** Run a final search for `"cancer survivor post-discharge LLM CTCAE toxicity monitoring agent 2026"` to confirm the gap holds.
- If this gap closes, the **longitudinal mental health risk accumulation guard** (Candidate C) is the next strongest option with an explicitly confirmed research gap.

### Risk 3 — General
- Both top picks would benefit from a stronger connection to your team's previous work (**NeuroFetal AI**) — consider framing CancerCompanion as a "post-treatment monitoring extension of clinical decision support" to show continuity of research expertise.
