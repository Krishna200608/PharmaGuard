# PharmaGuard — Weekly Progress Update
### Response to feedback: architectural novelty, multi-disease consideration, refined problem statement

**Submitted to:** Dr. Nikhilanand Arya  
**Group 07:** Krishna Sikheriya (IIT2023139), Lokesh Bawariya, Naitik Jain  
**Date:** September 2026

---

## 1. Feedback & Guidance from Previous Meeting (Recap)

In our last meeting, three key aspects were highlighted:

1. **Architectural Novelty:** Moving beyond a basic multi-agent pipeline ("an AI checks drug safety") to incorporate genuine, domain-grounded architectural novelty.
2. **Multi-Disease Modeling:** Explicitly accounting for indication and disease context, rather than treating every drug and adverse event pair under uniform baseline assumptions.
3. **Literature Grounding & Problem Scope:** Reviewing IEEE Transactions / journal literature to identify genuine methodological gaps, and sharpening the problem statement to be narrower and more defensible.

This document summarizes our progress, methodology, and experimental findings in response to all three points.

---

## 2. What We Found in the Research

We searched IEEE Xplore journals and other academic sources to see what's already been done in this space, so we could find a genuine gap rather than reinventing something that already exists.

**What we found:**

- "AI agents that check drug safety" is now a **crowded area** — several very recent papers (2024–2026) build similar baseline pipelines. This aligns with your feedback that a generic agentic safety pitch alone lacks sufficient novelty.
- However, we found a real, well-documented gap: almost no drug-safety systems account for **which disease a drug is being used to treat** when judging whether a side-effect report is a real warning sign. A 2022–2023 review of 101 similar studies found that **only 10 of them** even attempted this.
- We also found that a full solution to this gap already exists in recent research (a 2025–2026 paper using "causal knowledge graphs") — but it needs large private hospital datasets (like UK Biobank) that we, as students, don't have access to.

**This gave us a clear, honest opportunity:** build a lighter-weight version of the same idea, using only free, public data — something a real hospital or small pharma team could actually use without needing expensive hospital records.

---

## 3. What "Multi-Disease Consideration" Means Here (Plain Explanation)

**The core problem, in simple terms:**

Imagine a drug that's given to millions of people with heart disease. If some of those people later have a heart attack, is that because the *drug* caused it — or because they already had heart disease and were always at risk of a heart attack anyway?

Our original system couldn't tell the difference. It just looked at raw statistics — how often a side effect was reported for a drug — and used a fixed cutoff to decide "is this worth flagging or not?" That approach doesn't know *why* the drug was prescribed, so it can't tell "real side effect" apart from "the disease was going to cause this anyway."

**What we built this week:**

1. **A "Disease Context" checker.** For any drug, the system now looks up which part of the body / which disease area it treats (using a free, official World Health Organization drug classification list — no paid data needed).

2. **An "Indication Concordance" flag.** For every drug–side-effect pair the system checks, it now asks: *"Does this side-effect naturally overlap with the disease this drug treats?"* For example:
   - A blood-pressure drug flagged for a heart attack — plausible overlap, since heart patients are already at higher heart-attack risk.
   - An antidepressant flagged for a broken bone — no natural overlap, so more likely a genuine drug effect.

   The system now reasons across **7 different disease categories** (heart/blood, mental health, stomach/gut, diabetes, cancer/blood disorders, kidney, and breathing conditions), each backed by real published medical research — we checked every citation twice, by hand, against the actual papers, and fixed several that turned out to be wrong on the first pass.

3. **This flag is shown on every report**, so a human reviewer can see it and use their judgement — it doesn't currently change the automated decision by itself (see the honest test below for why).

4. **A results dashboard update**, so this disease-context breakdown is now visible visually, not just buried in a spreadsheet.

---

## 4. The Honest Experiment: Should This Flag Change the Actual Decision?

This naturally raises a logical follow-up question: *why stop at just flagging it — why not let it actively modulate the automated triage decision?*

We tried this properly, the right way:

- We designed a fixed, modest adjustment (reduce confidence by 15% when the flag fires) — **decided in advance, based on general research literature, before looking at any results.** This avoids the trap of tuning a number to make our own test cases look good, which would be scientifically dishonest.
- We tested it on **40 completely new drug–side-effect pairs the system had never seen before** — genuinely fresh data, not anything used to design the system.
- **Honest result:** the flag only fired on 4 of those 40 pairs, and in all 4 cases, the final decision didn't change. This is a real result, but with only 4 examples, it's too small a sample to say for certain whether this kind of adjustment helps or not.

**Why we're presenting this instead of hiding it:** A confident claim on too little evidence would be worse than an honest "not enough data yet." This is exactly the kind of finding real pharmacovigilance researchers report — negative or inconclusive results are still valuable science.

**Decision for now:** the automated escalation decisions remain conservative and unaffected by default, while the flag serves as transparent, high-visibility provenance for human reviewers. Whether to pursue active score discounting further depends on your guidance and whether additional validation cohorts are recommended.

---

## 5. Revised, More Specific Problem Statement

**Before (too broad):**
> "An AI agent that triages pharmacovigilance signals for drug safety."

**Now (specific, and honestly describes what's actually built):**
> A lightweight, freely-reproducible AI system for drug-safety signal triage that combines real-time adverse-event statistics, drug-mechanism data, and medical literature — and additionally reasons about **which disease each drug treats**, using only free public data (not restricted hospital records), to flag cases where a reported side-effect might just be a symptom of the underlying disease rather than a genuine drug reaction.

This is narrower, points at a real literature gap (only 10 of 101 similar studies do this), and is honest about what's proven versus what's still an open question.

---

## 6. Summary & Key Discussion Points

| Feedback / Guidance | Action Taken This Week |
|---|---|
| **Novelty & Architectural Depth** | Identified the specific literature gap (disease-context reasoning without requiring restricted hospital records) and implemented a lightweight, reproducible ontology-based mechanism. |
| **Multi-Disease Consideration** | Implemented a 7-category clinical indication-overlap layer across major organ systems, integrated live on every report and visualized on the dashboard. |
| **IEEE Literature & Scoping** | Completed targeted literature review and reformulated the problem statement around confounding-by-indication. |
| **Validation Experiment** | Pre-registered and evaluated a 15% discount factor ($\delta = 0.85$) against 40 unseen held-out OMOP pairs. Result: low-power null result (4/40 triggered, 0 category flips, 0 regressions). |

### Key Discussion Points for Your Guidance:
1. **Triage Architecture:** Do you agree with maintaining indication concordance as an explicit, high-visibility informational flag on reports and the dashboard (preserving conservative automated triage), while keeping the quantitative discount factor config-gated as an experimental feature?
2. **Evaluation Scope:** Would you recommend expanding our validation batch to a larger corpus to observe boundary-adjacent pairs, or is the current 40-pair held-out validation with honest null reporting sufficient for the conference paper?
3. **Paper Drafting:** Does this multi-disease architectural novelty provide a solid foundation to begin drafting the conference manuscript (methodology and related work sections), or would you like us to explore additional refinements first?
