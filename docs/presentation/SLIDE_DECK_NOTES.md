# PharmaGuard: Mid-Semester Capstone Defense Slide Deck (v1.0)

**Project:** PharmaGuard — Intelligent Pharmacovigilance Signal Triage Orchestrator Grounded in Multi-Source Clinical Evidence  
**Team:** Krishna Sikheriya (IIT2023139, Leader) · Lokesh Bawariya (IIT2023138) · Naitik Jain (IIB2023036)  
**Supervisor:** [Dr. Nikhilanand Arya](https://scholar.google.com/citations?user=hBf6EmgAAAAJ&hl=en) · Assistant Professor, Department of IT, IIIT Allahabad  
**Slide Deck Artifact:** [`docs/presentation/PharmaGuard_Midsem_Defense.pptx`](PharmaGuard_Midsem_Defense.pptx) (16:9 Widescreen, 13 Slides)

---

## Slide 1: Title & Project Identity

### Visual Content
- **Header Badge:** PharmaGuard Emblem Logo (`assets/Logos/Logo_3.png`)
- **Title:** PharmaGuard: Intelligent Pharmacovigilance Signal Triage Orchestrator Grounded in Multi-Source Clinical Evidence
- **Subtitle:** A Tool-Grounded, Tri-Source Evidence Fusion Agent for Postmarketing Adverse Drug Event Triage
- **Metadata Card:**
  - Team: Krishna Sikheriya (IIT2023139, Leader) · Lokesh Bawariya (IIT2023138) · Naitik Jain (IIB2023036)
  - Supervisor: Dr. Nikhilanand Arya · Assistant Professor, Department of IT
  - Institution: Indian Institute of Information Technology, Allahabad

### Spoken Speaker Script (Time: 0:00 – 0:45)
> "Good morning, Dr. Arya and evaluation committee. I am Krishna Sikheriya, presenting on behalf of our capstone team with Lokesh Bawariya and Naitik Jain. Today we present PharmaGuard: an intelligent pharmacovigilance signal triage orchestrator designed to resolve an acute bottleneck in postmarketing drug safety.
> Our core focus is replacing ungrounded, hallucinated LLM responses with deterministic, multi-source biomedical evidence fusion."

---

## Slide 2: The Clinical Problem & The LLM Triage Trap

### Visual Content (2-Column Card Layout)
- **Left Card: The Postmarketing Triage Crisis**
  - Millions of spontaneous adverse event reports are submitted annually to global postmarketing surveillance databases (e.g. US FDA FAERS).
  - Distinguishing true emergent safety signals from background noise, uncorroborated reports, and heavy polypharmacy confounding is a critical bottleneck.
  - High Cost of Error: False alarms induce severe clinician alert fatigue; missed signals risk patient harm.
- **Right Card: 3 Fatal Failure Modes of Ungrounded LLMs**
  - **1. Hallucinated Clinical Confidence:** LLMs produce uncalibrated self-scores (e.g. 0.85+) without empirical statistical grounding.
  - **2. Historical Regulatory Confusion:** LLMs recall past controversies (e.g. *liraglutide + pancreatic cancer*), confusing investigated hypotheses with confirmed causal links.
  - **3. Parametric Epistemic Leakage:** LLMs memorize famous FDA Boxed Warnings from training weights, overriding mechanistic pathway analysis.

### Spoken Speaker Script (Time: 0:45 – 1:45)
> "Every year, millions of spontaneous adverse drug event reports flood safety surveillance databases. When safety teams attempt to apply foundation models to triage these reports, LLMs fail in three distinct ways: they hallucinate confidence scores without statistical data, they confuse historical investigations with confirmed reactions, and they leak memorized regulatory labels rather than reasoning from first principles. PharmaGuard is architected specifically to overcome these three traps."

---

## Slide 3: Related Work & Literature Positioning

### Visual Content (2-Column Card Layout)
- **Left Card: Foundational & Empirical Precedents**
  - **ReAct Architecture (Yao et al., ICLR 2023):** Foundational framework interleaving thought-action-observation tool loops.
    - *What it shows:* Establishes the agentic tool-execution loop on which PharmaGuard's orchestrator is built.
    - *Gap addressed:* Generic reasoning loop; lacks multi-source evidence weighting, continuous confidence calibration, and deterministic safety gates.
  - **PSEBench (arXiv:2606.05463, 2026):** Closest empirical analog (5,074 cases) evaluating LLMs on escalation-tiered patient safety event triage.
    - *What it shows:* Validates agentic, evidence-grounded triage benchmarking in healthcare.
    - *Gap addressed:* Evaluates acute hospital incident reporting rather than postmarketing drug pharmacovigilance; prior to PharmaGuard, no public drug-safety multi-source triage benchmark existed.
  - **Omar et al. (*Communications Medicine*, 2025):** Multi-model assurance analysis showing LLMs hallucinated on planted false details in up to 83% of clinical cases.
    - *What it shows:* Uncalibrated generative LLMs are highly vulnerable to adversarial and ungrounded clinical errors.
    - *Gap addressed:* Empirically justifies PharmaGuard's elimination of ungrounded LLM scoring in favor of deterministic formulas.
- **Right Card: Domain Landscape & Multi-Agent Contrast**
  - **Venugopal (*J. Med. AI*, Jan 2026):** Narrative review mapping agentic AI across signal detection, intake, and triage.
    - *What it shows:* Conceptually outlines the potential of autonomous agents in drug safety.
    - *Gap addressed:* Purely theoretical survey; PharmaGuard is a concrete, reproducible, open-source realization.
  - **DruGagent (2025/2026):** Multi-agent ReAct + literature grounding + per-tool ablation studies.
    - *What it shows:* Demonstrates the power of component-level ablation in biomedical LLM systems.
    - *Gap addressed:* Targets pre-clinical drug discovery rather than postmarketing adverse-event signal surveillance.
  - **MDAgents (Kim 2024) / TeamMedAgents (Mishra 2025):** Adaptive multi-agent medical teamwork protocols.
    - *What it shows:* Complex conversational medical collaboration frameworks.
    - *Gap addressed:* Dynamic routing introduces non-determinism and high latency; PharmaGuard employs audited single-agent tools with deterministic formula scoring for regulatory auditability.

### Spoken Speaker Script (Time: 1:45 – 3:00)
> "To position PharmaGuard in the academic literature, we examine two foundational base papers and five related clinical agent works:
> First, ReAct by Yao et al. (ICLR 2023) established the tool-calling architecture our agent builds upon. However, ReAct is domain-agnostic and lacks the mathematical weighting and hard safety gates needed in clinical triage.
> Second, PSEBench (2026) is our closest empirical analog, benchmarking LLMs on hospital safety event triage across 5,000 cases. But it focuses on hospital incidents; no drug-safety-specific multi-source benchmark existed prior to PharmaGuard.
> Third, Omar et al. in *Communications Medicine* (2025) proved that leading LLMs elaborate on false details in up to 83% of clinical decision cases without tool verification—providing the empirical justification for our deterministic scoring.
> Fourth, Venugopal (2026) theorized agentic AI in pharmacovigilance; PharmaGuard represents an open-source, evaluated instantiation.
> Finally, in contrast to complex multi-agent frameworks like MDAgents and TeamMedAgents, PharmaGuard employs a streamlined single-agent pipeline with deterministic scoring to guarantee auditability in regulatory environments."

---

## Slide 4: PharmaGuard System Architecture

### Visual Content (3-Stream Cards + Formula Base)
- **Stream 1: openFDA FAERS Engine (Weight: 0.40)**
  - 2×2 Contingency Table (PRR, ROR), Woolf 95% Log-CI.
  - Down-weights signals where lower 95% CI < 1.0 to prevent small-sample false alarms.
- **Stream 2: ChEMBL Target Plausibility (Weight: 0.20)**
  - Target Mechanism of Action (MoA) evaluation.
  - Curated expert lookup (v1.0) with categorical scoring: HIGH (0.90), MOD (0.50), LOW (0.00).
- **Stream 3: PubMed Literature Grading (Weight: 0.40)**
  - NCBI E-utilities API + Abstract Fetch.
  - Structured LLM grading against a versioned clinical rubric (v1.0), replacing earlier brittle keyword-matching heuristics:
    - **Grade A:** Statistically significant association (OR/RR/HR with 95% CIs).
    - **Grade B:** Case reports / clinical observations.
    - **Grade C:** Negative / uncorroborated literature.
- **Deterministic Confidence Formula:**
  $$\text{Confidence} = 0.40 \cdot S_{\text{FAERS}} + 0.40 \cdot S_{\text{PubMed}} + 0.20 \cdot S_{\text{Plausibility}}$$
- **Safety Gates & Decision Boundaries:**
  - **Hard Safety Gate:** If `FAERS == NO_SIGNAL` $\implies$ Immediately force `DO_NOT_ESCALATE`.
  - **Boundaries:** `Confidence >= 0.70 & FAERS >= MODERATE` $\implies$ `ESCALATE` | `Confidence >= 0.35` $\implies$ `MONITOR` | Otherwise $\implies$ `DO_NOT_ESCALATE`.

### Spoken Speaker Script (Time: 3:00 – 4:15)
> "Here is PharmaGuard's core architecture. We fuse three orthogonal streams: openFDA FAERS disproportionality statistics, ChEMBL target biological mechanisms, and PubMed peer-reviewed literature graded against a versioned clinical rubric.
> Crucially, our confidence score is computed by a deterministic formula, not generated arbitrarily by an LLM prompt. If FAERS indicates NO_SIGNAL, our Hard Safety Gate immediately forces DO_NOT_ESCALATE—guaranteeing that hypotheses without real-world patient reports cannot trigger false alarms."

---

## Slide 5: Ground Truth Dataset & Evaluation Methodology

### Visual Content
- **15-Pair Benchmarking Protocol across 3 Cohorts:**
  - **7 Confirmed Positives:** Established pharmacovigilance safety signals (e.g. *rofecoxib::myocardial_infarction*, *rosiglitazone::heart_failure*, *montelukast::suicidal_ideation*).
  - **5 Genuine Negative Controls:** No causal link (e.g. *metformin::hypoglycaemia* [monotherapy negative], *liraglutide::pancreatic_cancer* [investigated negative]).
  - **3 Zero-Report Controls:** Zero FAERS co-occurrences (e.g. *albuterol::suicidal_ideation*) to test hard safety gate short-circuiting.
- **Statistical Rigor:**
  - **Exact Wilson Score 95% Binomial CIs:** Accurately quantifies small-sample uncertainty without 0/N collapse.
  - **Non-parametric Bootstrap Resampling ($B=1000, \text{seed}=42$):** Ensures end-to-end reproducibility.
  - **Dual-Metric Reporting:** Strict binary escalation alongside surveillance-aware safety recall.

### Spoken Speaker Script (Time: 4:15 – 5:15)
> "To validate our system rigorously, we curated a 15-pair benchmark across 3 clinical cohorts: 7 confirmed positives, 5 negative controls, and 3 zero-report controls.
> Rather than relying on simple point estimates, every metric is computed with exact Wilson Score 95% confidence intervals and non-parametric bootstrap resampling."

---

## Slide 6: Headline Benchmark: Why 6/7 Beats 15/15

### Visual Content (Comparative Metric Table)
| Metric | PharmaGuard (Tool-Grounded) | Single-Shot LLM Baseline (No Tools) | Significance & Clinical Meaning |
| :--- | :---: | :---: | :--- |
| **Strict Precision** | **1.000** [0.610 – 1.000] | 0.875 [0.529 – 0.978] | **FP = 0** on negative controls under PharmaGuard |
| **Strict Recall** | **0.857** (6 of 7) [0.487 – 0.974] | 1.000 (7 of 7) [0.646 – 1.000] | Strict FN = Montelukast (held at MONITOR due to unconfirmed CNS mechanism) |
| **Strict Specificity** | **1.000** [0.676 – 1.000] | 0.875 [0.529 – 0.978] | Baseline falsely escalated *liraglutide* on historical controversy |
| **Lenient Recall** | **1.000** (7 of 7) [0.646 – 1.000] | 1.000 (7 of 7) [0.646 – 1.000] | **Zero safety-critical signals missed** across both systems |
| **Over-Caution Rate (OCR)** | **12.5%** (1 of 8) | **25.0%** (2 of 8) | **50% reduction in unnecessary negative control alerts** |

- **Key Finding Card:** In clinical AI, an ungrounded model claiming '15/15 recall' is over-escalating indiscriminately. PharmaGuard's 6/7 Strict Recall reflects genuine epistemic calibration.

### Spoken Speaker Script (Time: 5:15 – 6:30)
> "Here is our headline finding: PharmaGuard achieves 1.000 Strict Precision with zero false positive escalations, and cuts the Over-Caution Rate in half from 25% down to 12.5%.
> Why does 6/7 beat 15/15? Because the baseline's 'perfect' recall is an illusion caused by over-escalating clean negative controls like Liraglutide. PharmaGuard exhibits true clinical calibration."

---

## Slide 7: Dual-Metric Philosophy: Strict vs. Lenient Evaluation

### Visual Content
- **Strict Evaluation (Only ESCALATE = True Positive):**
  - Measures high-confidence, definitive regulatory triage.
  - Requires BOTH strong epidemiological disproportionality AND biological plausibility.
  - Precision: **1.000** | Specificity: **1.000**.
- **Lenient Evaluation (ESCALATE + MONITOR = True Positive):**
  - Measures patient safety surveillance coverage.
  - Confirms that NO potential clinical harm escapes human review.
  - Lenient Recall: **1.000 (7/7)** | Lenient F1: **0.933** (+10.9% gain over baseline).

### Spoken Speaker Script (Time: 6:30 – 7:30)
> "Reporting a single metric in clinical AI is dangerous. Strict evaluation tests whether the system demands both epidemiological and biological evidence before triggering high-cost regulatory alerts. Lenient evaluation verifies safety: did any potential harm escape surveillance? Our Lenient Recall is 1.000 (7 of 7)."

---

## Slide 8: Disagreement Case Study 1: Montelukast & Suicidal Ideation

### Visual Content
- **Evidence Profile:**
  - Ground Truth: Confirmed Positive (FDA Boxed Warning 2020).
  - openFDA FAERS: MODERATE signal (PRR = 3.37, 1,259 reports).
  - PubMed: Grade A (multiple observational studies with statistically significant odds ratios and 95% CIs).
  - ChEMBL MoA: Plausibility = LOW (CysLT1 leukotriene receptors are predominantly peripheral; no direct CNS pathway confirmed).
- **Confidence Decomposition:**
  $$\text{Confidence} = 0.40(0.70) + 0.40(0.85) + 0.20(0.22) = 0.664 < 0.70 \implies \mathbf{MONITOR}$$
- **Clinical Defense:** Real-world signal flagged for active clinician monitoring while honestly reporting mechanistic uncertainty.

### Spoken Speaker Script (Time: 7:30 – 8:45)
> "Let us examine our first disagreement case: Montelukast and Suicidal Ideation. The FDA issued a Boxed Warning in 2020. However, ChEMBL target data reveals leukotriene CysLT1 receptors are predominantly peripheral, with no established CNS penetration mechanism. Because biological plausibility is LOW, composite confidence lands at 0.664—just below the 0.70 threshold. PharmaGuard routes this to MONITOR: ensuring active surveillance while honestly reporting mechanistic uncertainty."

---

## Slide 9: Disagreement Case Study 2: Metformin & Hypoglycaemia

### Visual Content
- **Evidence Profile:**
  - Ground Truth: Negative Control (Monotherapy negative).
  - openFDA FAERS: STRONG signal (PRR = 10.73, 9,344 reports) driven by ubiquitous co-prescription with insulin/sulfonylureas.
  - ChEMBL MoA: Plausibility = LOW (Metformin reduces hepatic gluconeogenesis; does NOT stimulate insulin secretion).
  - PubMed: Grade C (confounded observational mentions).
- **Confidence Decomposition:**
  $$\text{Confidence} = 0.40(1.00) + 0.40(0.00) + 0.20(0.00) = 0.400 \ge 0.35 \implies \mathbf{MONITOR}$$
- **Clinical Defense:** De-weights the confounded signal from ESCALATE down to MONITOR, but refuses to silently drop a pair with 9,340 real patient reports.

### Spoken Speaker Script (Time: 8:45 – 9:45)
> "Our second disagreement is Metformin and Hypoglycaemia. Biologically, Metformin monotherapy does not cause hypoglycaemia. But in FAERS, over 9,340 reports exist due to polypharmacy with insulin. PharmaGuard's 0.40 FAERS weight establishes a 0.400 confidence floor, routing this to MONITOR. This is safety-first triage: discounting the confounded signal without silently ignoring 9,000 real-world patient reports."

---

## Slide 10: Baseline Comparison: The Liraglutide Proof

### Visual Content (Side-by-Side Reasoning Trace)
- **Single-Shot LLM Baseline (No Tools):**
  - **Decision:** `ESCALATE` (Confidence 0.850 — Uncalibrated).
  - **Failure:** Recalls the 2013 FDA/EMA joint investigation into GLP-1 agonists and pancreatic cancer, failing to realize the 2014 regulatory conclusion formally found no causal link. Confuses 'investigated' with 'confirmed'.
- **PharmaGuard (Tool-Grounded):**
  - **Decision:** `DO_NOT_ESCALATE` (Confidence 0.300).
  - **Trace:** Queries openFDA FAERS $\to$ 0 co-occurrences $\to$ `SignalStrength = NO_SIGNAL` fires the **Hard Safety Gate** $\to$ Immediately forces `DO_NOT_ESCALATE`.

### Spoken Speaker Script (Time: 9:45 – 10:45)
> "Slide 10 provides our most compelling concrete proof: Liraglutide and Pancreatic Cancer. The baseline LLM hallucinates an ESCALATE decision with 0.85 confidence because it recalls historical 2013 regulatory headlines. PharmaGuard checks live FAERS records, finds 0 co-occurrences, and fires the Hard Safety Gate—returning DO_NOT_ESCALATE. Tool grounding eliminates phantom regulatory alarms."

---

## Slide 11: Epistemic Discipline & The Ablation Study Warning

### Visual Content
- **The `force_agent` Ablation Finding:**
  - Forcing the LLM to derive plausibility without lookup tables achieved an apparent '1.000 Strict Recall' (7 of 7).
  - **Transcript Audit:** The LLM explicitly cited the FDA Boxed Warning inside its biological reasoning chain!
  - Rather than performing de novo biochemical pathway analysis, the LLM leaked regulatory memory from its pre-training weights.
- **Architectural Defense:**
  - Production locked to `lookup_first` mode (`DECISIONS.md §17 & §19`).
  - LLMs in safety-critical systems must act as structured knowledge synthesizers and evidence graders, never unverified biological oracles.

### Spoken Speaker Script (Time: 10:45 – 11:45)
> "Slide 11 highlights our epistemic honesty. In our Phase 3 ablation study, forcing the LLM to derive biological plausibility dynamically produced 1.000 Strict Recall. But transcript inspection revealed regulatory memory leakage: the LLM cited FDA Boxed Warnings instead of biochemical pathways. We rejected this artificial perfection and locked lookup_first mode to enforce genuine pharmacological grounding."

---

## Slide 12: Modular Evaluation Dashboard & Verified Artifacts

### Visual Content (4-View Suite & Engineering Invariants)
- **4-View Clinical Presentation Suite:**
  - **Overview View:** Hero metrics (0.857 Strict Recall, 12.5% OCR, FP=0), Wilson 95% CIs, brand identity.
  - **Per-Pair Table:** Dense 15-pair matrix with inline report counts, category filters, and interactive Plotly confidence bar charts.
  - **Disagreement Spotlight:** Dedicated dual-column deep dive into Montelukast and Metformin evidence decompositions.
  - **Baseline Comparison:** Side-by-side metric tables and Liraglutide concrete reasoning comparison.
- **Engineering Invariants:**
  - Zero Live Network Calls (reads pre-committed JSON runs in `outputs/`).
  - Modular package structure (`scripts/dashboard_modules/`).
  - 51 passing pytest unit & regression tests.

### Spoken Speaker Script (Time: 11:45 – 12:30)
> "Our evaluation dashboard provides a full clinical review interface with 4 dedicated views. Crucially, it is engineered for zero live network dependencies at runtime, reading pre-committed JSON evaluation runs with interactive Plotly confidence decomposition bar charts."

---

## Slide 13: Capstone Summary, Next Steps & Defense Conclusion

### Visual Content
- **Mid-Semester Accomplishments:**
  - 1. Deterministic tri-source evidence fusion pipeline.
  - 2. Dual-metric benchmark framework with exact Wilson/Bootstrap CIs.
  - 3. 50% reduction in clinician over-caution burden without dropping safety signals.
  - 4. Complete evaluation suite (51 unit tests, modular dashboard).
- **Future Roadmap (Semester 8):**
  - Automated MedDRA SOC/HLT hierarchical roll-up.
  - Multi-jurisdiction ingestion (EudraVigilance, PMDA).
  - Prospective EHR clinical surveillance adapter.
- **Concluding Statement:** Thank you. Questions & Discussion.

### Spoken Speaker Script (Time: 12:30 – 13:15)
> "In summary, PharmaGuard proves that grounding LLMs in deterministic biomedical tools eliminates hallucinations, enforces safety gates, and cuts alert fatigue by 50%.
> In the final semester, we will expand MedDRA hierarchical mapping and integrate international safety streams.
> Thank you, Dr. Arya and members of the committee. We are now open to your questions."
