# PharmaGuard: A Tool-Grounded LLM Agent for Pharmacovigilance Signal Triage

**Capstone Project Proposal**
Krishna Sikheriya (IIT2023139) — B.Tech IT, 7th Semester
Supervisor: Dr. Nikhilanand Arya
Date: 18 August 2026

---

## 1. Problem Statement

Spontaneous adverse event reporting systems such as the FDA Adverse Event Reporting System (FAERS) receive a very large and continuously growing volume of drug safety reports each year. Clinical safety teams face a persistent triage bottleneck: distinguishing genuine, emergent safety signals from background statistical noise, uncorroborated single reports, and effects confounded by polypharmacy (patients on multiple drugs simultaneously). This triage step is currently manual, does not scale well, and delays the point at which a real signal reaches formal review.

Large language models are increasingly proposed as assistants for this kind of triage, but ungrounded LLMs — models answering purely from pretrained knowledge, without querying real data — carry a documented, empirically measured risk in clinical contexts. A recent multi-model study (Omar et al., *Communications Medicine*, 2025) found that leading LLMs elaborated on a single fabricated clinical detail in up to 83% of test cases, with mitigation prompting only partially reducing the error rate. For a task like drug-safety triage, where a model might confidently recall that a historical safety *concern* existed without checking whether it was later investigated and formally *dismissed*, this failure mode is directly disqualifying for unsupervised use.

## 2. Motivation

The core question this project investigates: **can an LLM-based agent be constrained to reason only from verifiable, real-time evidence — rather than parametric memory — for a safety-critical triage task, and does this grounding produce measurably better and more defensible decisions than an ungrounded model answering the same question?**

This is not a purely theoretical question. Agentic AI in pharmacovigilance is an active area of conceptual interest — a recent narrative review (Venugopal, *J. Med. AI*, Jan 2026) surveys the space of signal-detection and reporting agents connecting to FAERS, EudraVigilance, and the medical literature — but, per a literature search conducted for this proposal, no concrete, evaluated system combining real-time statistical disproportionality analysis, drug mechanism-based plausibility reasoning, and literature evidence grading into a single triage decision currently exists in the published record for this specific domain. The closest methodological analog, PSEBench (2026), demonstrates the general pattern — agentic, evidence-grounded, escalation-tiered safety triage evaluated against curated real-world ground truth — for hospital incident reporting, at a scale of over 5,000 cases, but not for drug pharmacovigilance specifically.

## 3. Objectives

1. Design and implement an LLM agent that triages a given drug–adverse-event pair into one of three tiers — **ESCALATE**, **MONITOR**, or **DO_NOT_ESCALATE** — grounded in three independent, real, publicly accessible evidence sources.
2. Combine these evidence sources through a deterministic, auditable scoring formula rather than an opaque model judgment, so that every triage decision is traceable to specific inputs.
3. Curate a small, source-verified ground-truth evaluation set of real confirmed and dismissed drug-safety signals, drawn from FDA/EMA regulatory actions and peer-reviewed literature.
4. Evaluate the system rigorously against this ground truth, including comparison against an ungrounded single-shot LLM baseline, to test whether grounding produces a measurable difference in triage quality.
5. Characterize, honestly, where the system's reasoning may still be influenced by the underlying LLM's memorized knowledge rather than genuine evidence-based inference, and report this as a documented property of the system rather than an unexamined assumption.

## 4. Proposed Methodology

### 4.1 Evidence sources

- **FAERS (FDA Adverse Event Reporting System):** queried for real-world disproportionality statistics — the Proportional Reporting Ratio (PRR) and Reporting Odds Ratio (ROR), with confidence intervals — for a given drug–event pair.
- **ChEMBL:** a public drug mechanism-of-action database, used to assess whether a drug's known pharmacology makes a proposed adverse effect biologically plausible.
- **PubMed:** the medical literature database, searched for supporting evidence, with retrieved abstracts graded for the strength of statistical support they provide.

### 4.2 Agent architecture

The system is designed around a tool-use agent architecture in the spirit of the ReAct pattern (Yao et al., 2023) — interleaving reasoning steps with calls to external, verifiable tools rather than answering from memory alone. Two orchestration modes are planned: a fixed, deterministic sequence of tool calls for reliability, and a more flexible agent-directed mode for comparison, following architectural precedents in the multi-agent medical-AI literature (Kim et al.'s MDAgents, 2024; Mishra et al.'s TeamMedAgents, 2025) while intentionally keeping the design simpler — a fixed division of labor across tool roles rather than dynamic agent negotiation, to keep the system auditable within a single-semester scope.

### 4.3 Scoring and decision logic

The three evidence signals are combined into a single confidence score via a fixed, published weighting formula, not a free-form LLM judgment. A hard safety gate is applied: if the real-world statistical evidence shows no disproportionate signal at all, the system will not escalate regardless of what the other two signals suggest — grounding the final decision in empirical data as the primary evidence, with mechanism and literature treated as corroborating context.

### 4.4 Evaluation plan

- A curated ground-truth set of confirmed and dismissed drug-safety signals, each individually sourced to a real FDA/EMA action or a peer-reviewed disproportionality study — not synthetically generated.
- Both strict (exact match to ESCALATE only) and lenient (ESCALATE or MONITOR both count) scoring, since a triage system that appropriately expresses uncertainty is not the same as one that has failed.
- A single-shot LLM baseline (identical prompt, no tool access) run on the same evaluation set, to directly test whether grounding produces a measurable difference — following the comparative methodology used in DruGagent (multi-agent LLM reasoning for drug-target interaction prediction, with ablation studies isolating each component's contribution).
- An ablation study comparing curated, human-verified plausibility judgments against judgments the agent derives entirely on its own, specifically to test whether the agent's reasoning is genuinely independent evidence or is influenced by memorized regulatory knowledge.

## 5. Expected Outcomes

- A working, evaluated prototype demonstrating measurable benefit from evidence-grounding over an ungrounded LLM baseline on a realistic drug-safety triage task.
- A rigorously sourced evaluation methodology (ground truth curation, dual strict/lenient scoring, baseline comparison, ablation study) that is itself a transferable contribution to how agentic clinical-AI systems can be evaluated, independent of this specific application.
- An honest characterization of the system's current limitations — including where LLM-derived reasoning may not be fully separable from memorized knowledge — documented as findings, not hidden as gaps.

## 6. Constraints and Scope

This project is scoped to fit a single-semester capstone timeline, using free-tier compute and public data sources only. The evaluation set size is necessarily small given the manual, source-verified curation this project's evaluation standard requires; the project explicitly does not claim clinical-grade validation, and independent human-expert review of the system's judgments is identified as important future work beyond the current scope.

## 7. Tentative Timeline

| Phase | Focus |
|---|---|
| Weeks 1–4 | Tool integration (FAERS, ChEMBL, PubMed), agent architecture, core scoring logic |
| Weeks 5–8 | Ground-truth curation, initial evaluation pipeline, mid-semester checkpoint |
| Weeks 9–12 | Full evaluation, baseline comparison, ablation study, refinement |
| Weeks 13–16 | Final evaluation, documentation, end-of-semester presentation |

## 8. References

1. Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *ICLR 2023*.
2. PSEBench: A Controllable and Verifiable Benchmark for Evaluating LLMs in Patient Safety Event Triage. arXiv:2606.05463 (2026).
3. Omar, M., et al. (2025). Multi-model assurance analysis showing large language models are highly vulnerable to adversarial hallucination attacks during clinical decision support. *Communications Medicine*, 5(1), 330.
4. Venugopal, R. (2026). Large language models-powered agentic AI design and implementation in pharmacovigilance — a narrative review. *Journal of Medical Artificial Intelligence*.
5. DruGagent: Multi-Agent Large Language Model-Based Reasoning for Drug-Target Interaction Prediction.
6. Kim, Y., et al. (2024). MDAgents: An Adaptive Collaboration of LLMs for Medical Decision-Making.
7. Mishra, S., Arvan, M., & Zalake, M. (2025). TeamMedAgents: Structured Teamwork Protocols for Medical LLM Agents.
