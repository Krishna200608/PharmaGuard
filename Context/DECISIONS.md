Last updated: 2026-08-10 | Sprint: Sprint 1 (Transitioning to Sprint 2) | Updated by: Antigravity

# DECISIONS

## 1. ChEMBL ID Resolution is Static
**Decision:** ChEMBL IDs are pre-resolved in a static local JSON lookup table.
**Why:** Reliability tradeoff; fuzzy dynamic matching via ChEMBL API is error-prone, and a static map ensures guaranteed agent stability on the limited target evaluation set.

## 2. Plausibility Default is Human-Curated
**Decision:** Plausibility levels default to human-curated labels in data/plausibility_ratings.json.
**Why:** Agent-derived plausibility is kept as a fallback/ablation mode via config.yaml (plausibility.source = force_agent). This guarantees verifiable reference baselines without burning unnecessary agent logic for the main pipeline.

## 3. FAERS Caching Finalization
**Decision:** All FAERS API returns (0 count, insufficient data, normal) route through a single _finalize() helper function.
**Why:** Prevents short-circuited branching logic from silently bypassing diskcache writes, which was causing severe API quota drains.

## 4. Hard NO_SIGNAL Gate Overrides Confidence
**Decision:** In derive_escalation(), a NO_SIGNAL from FAERS strictly forces DO_NOT_ESCALATE regardless of how high the confidence score is.
**Why:** FAERS is the primary source; literature and plausibility are corroborating. A hypothesis (even with high plausibility and literature grade A) is not a true pharmacovigilance signal if the empirical report count is zero.

## 5. Escalation Thresholds are Uncalibrated Priors
**Decision:** confidence >= 0.70 (ESCALATE) and confidence >= 0.35 (MONITOR).
**Why:** Set arbitrarily during scaffolding to allow the pipeline to function. Explicitly noted to be recalibrated once the ground-truth set is evaluated.

## 6. PubMed Grading via LLM, Not Keywords
**Decision:** The PubMed tool routes evidence grading through an LLM evaluation instead of string substring matching (e.g. searching for " or ").
**Why:** String matching was highly adversarial and triggered false positives (e.g. general English words). LLM evaluation ensures semantic checking based on the rubric, cached efficiently against the prompt's version.

## 7. ReAct Fallback Pipeline
**Decision:** A fallback fixed-order pipeline must be implemented alongside ReAct.
**Why:** If the LangGraph ReAct model becomes unreliable or flaky during mid-semester testing, a deterministic sequence guarantees a working demo.
