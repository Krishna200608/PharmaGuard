# PharmaGuard -- Design Notes and Deferred Decisions

This file records implementation decisions that are intentional but uncalibrated,
or that were made during scaffolding rather than formal spec review. Read before
modifying thresholds, scoring rules, or evaluation logic.

---

## 1. Escalation Thresholds (output_schema.py)

**Decision:** `confidence >= 0.70` triggers ESCALATE; `confidence >= 0.35` triggers MONITOR.

**Status: UNCALIBRATED PRIORS -- not derived from data.**

These values were chosen during scaffolding as reasonable starting points. They have
not been validated against any ground-truth distribution. Once evaluation runs on
the full 15-20 pair ground-truth set exist, revisit these thresholds using ROC
analysis on the confidence score distribution and adjust to optimize for the
precision/recall tradeoff agreed with the supervisor.

Do not treat the current thresholds as meaningful for the paper's claims.

---

## 2. MONITOR Verdict -- Scoring Rule Against Binary Ground Truth

**Context:** `derive_escalation()` produces three outcomes: ESCALATE, MONITOR,
DO_NOT_ESCALATE. The ground-truth labels in `data/ground_truth.json` are binary:
`expected_escalation` is either "ESCALATE" or "DO_NOT_ESCALATE". This creates an
ambiguity when the agent returns MONITOR.

**Scoring rule (applies to evaluator.py -- Teammate 2 must implement this exactly):**

Two metrics are computed in parallel. Do not collapse into one.

### Strict metric (primary -- use for paper claims)

    ESCALATE          -> predicted positive
    MONITOR           -> predicted negative
    DO_NOT_ESCALATE   -> predicted negative

Rationale: answers "does the agent correctly identify signals requiring escalation?"
MONITOR means the agent was not confident enough to escalate -- a miss on a true
positive. This is the conservative, defensible choice for the primary metric.

### Lenient metric (secondary -- report alongside strict)

    ESCALATE          -> predicted positive
    MONITOR           -> predicted positive
    DO_NOT_ESCALATE   -> predicted negative

Rationale: answers "does the agent at least flag the pair for attention?" Captures
whether the agent's uncertainty is calibrated (it says MONITOR on genuine signals
rather than confidently DO_NOT_ESCALATE).

### Over-caution rate (additional -- report separately)

For negative-control pairs (ground truth = DO_NOT_ESCALATE): report the fraction
that return MONITOR. This is the agent's false-alarm rate on known negatives --
a separate failure mode from low recall on positives.

### Summary table for evaluator.py

| Agent output    | GT = ESCALATE (positive)    | GT = DO_NOT_ESCALATE (negative)  |
|-----------------|-----------------------------|----------------------------------|
| ESCALATE        | TP (both metrics)           | FP (both metrics)                |
| MONITOR         | FN (strict) / TP (lenient)  | Over-caution (report separately) |
| DO_NOT_ESCALATE | FN (both metrics)           | TN (both metrics)                |

**Primary evaluation metric for the paper: strict F1.**
Secondary metrics: lenient recall, over-caution rate.

---

## 3. Plausibility Ratings (data/plausibility_ratings.json)

HIGH/MODERATE/LOW ratings are human-assigned (Naitik Jain) using the rubric in
`pharmaguard/prompts/evidence_grading_rubric.txt`. Not independently validated.
The ablation (force_agent vs. human-curated on identical pairs) will report
agreement rate -- that agreement rate is itself an evaluation result.

---

## 4. PubMed Evidence Grade Keyword Lists (pharmaguard/tools/pubmed_tool.py)

Grade A and Grade B keyword lists in `_grade_evidence()` are heuristic. They will
over-count Grade B for common clinical language and may under-count Grade A for
papers reporting significance without standard phrases.

Planned improvement (post mid-sem demo): recency weighting (year > 2015 preferred)
and study-type detection (RCT > cohort > case report). Not in scope for Sprint 1.
