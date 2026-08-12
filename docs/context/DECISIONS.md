Last updated: 2026-08-10 | Sprint: Sprint 2 (COMPLETED) | Updated by: Antigravity

# DECISIONS

## 1. ChEMBL ID Resolution is Static
**Decision:** ChEMBL IDs are pre-resolved in a static local JSON lookup table.
**Why:** Reliability tradeoff; fuzzy dynamic matching via ChEMBL API is error-prone, and a static map ensures guaranteed agent stability on the limited target evaluation set.

## 1.1 MoA Curation Methodology (Anti-Circularity Rule)
**Decision:** Mechanism of Action (MoA) text must be authored or reviewed strictly for general pharmacology WITHOUT looking at which adverse event it will be evaluated against. General pharmacology is written first, and only paired with `ground_truth.json` afterward.
**Why:** Prevents data leakage/circularity. If an adverse-event-specific mechanism (e.g., "causes mitochondrial dysfunction" for hepatotoxicity) is planted directly into the MoA field, the LLM isn't independently reasoning from general pharmacology—it's just being handed the answer.
**Known Limitation:** Even with clean, blinded MoA input, it is impossible to fully distinguish whether the LLM's plausibility verdict reflects genuine step-by-step pharmacological inference or training-data memorization of a famous, heavily-published drug-safety case (e.g., clozapine/agranulocytosis). Both are legitimate but distinct capabilities. The `rationale` field in `PlausibilityResult` now captures the LLM's free-text justification to help reviewers make this assessment, but it cannot be treated as definitive proof of either.

## 2. Plausibility Default is Human-Curated
**Decision:** Plausibility levels default to human-curated labels in data/plausibility_ratings.json. (As of Sprint 3, all further curation, evaluation, and documentation work is solely Krishna's responsibility).
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

## 6. Caching Layer & Rate Limiting
- **Decision:** All external tool calls (FAERS, PubMed, ChEMBL) must pass through `ToolCache` (disk-backed using `diskcache`).
- **Rationale:** The system is heavily constrained by public API rate limits (e.g. NCBI's 3 req/s without key, 10 req/s with key) and free-tier LLM rate limits. Caching makes development iteration viable.
- **Decision:** Cache keys for LLM grading and plausibility derivation must include both `prompts_version` and an internal `CACHE_SCHEMA_VERSION`.
- **Rationale:** Changing the rubric (text) invalidates via `prompts_version`. Changing the parsing logic/schema (code) invalidates via `CACHE_SCHEMA_VERSION`. This guarantees stale outputs are never inadvertently served after code refactors.

## 7. PubMed Grading via LLM, Not Keywords
**Decision:** The PubMed tool routes evidence grading through an LLM evaluation instead of string substring matching (e.g. searching for " or ").
**Why:** String matching was highly adversarial and triggered false positives (e.g. general English words). LLM evaluation ensures semantic checking based on the rubric, cached efficiently against the prompt's version.

## 8. ReAct Fallback Pipeline
**Decision:** A fallback fixed-order pipeline must be implemented alongside ReAct.
**Why:** If the LangGraph ReAct model becomes unreliable or flaky during mid-semester testing, a deterministic sequence guarantees a working demo.

## 9. LangGraph ReAct Agent Guardrails
**Decision:** The ReAct loop enforces a strict recursion_limit (e.g. 15 iterations) and defaults to safe placeholder values (UNKNOWN/C/None) if the agent terminates early without properly fetching data from all tools.
**Why:** Prevents runaway agent iterations draining the LLM API quota, fulfilling the robustness requirement while preserving the fallback gracefully.

## 9. ReAct Architecture Tool Nodes
**Decision:** LangGraph nodes directly execute the three underlying data fetchers (FAERS, ChEMBL, PubMed), pushing the raw return objects onto the graph state before assembling the final TriageReport deterministically outside the LLM.
**Why:** Ensures compute_prr_score, compute_confidence, and derive_escalation remain untampered by the agent's generative layer.

## 10. LLM Model Selection & Configuration
**Decision:** The default Gemini model is configured to "gemini-3.1-flash-lite" via config.yaml, reading from Google's v1beta endpoints.
**Why:** Gemini 1.0 and 1.5 models were retired, leading to 404 NOT_FOUND errors. A dynamic reading of available models showed 3.1-flash-lite as a stable fallback. It's explicitly decoupled to config.yaml to handle Google's aggressive deprecation cadence (e.g. 2.0 Flash retired June 2026, 2.5 Flash cut off before Oct 2026). A mid-semester verification is recommended.

## 11. Sprint 3 Evaluator Hand-off & Query Normalization
**Decision:** All external API query construction (e.g. FAERS, PubMed) must pass through a shared `normalize_term` utility to convert internal snake_case keys into natural language strings (e.g., `tendon_rupture` to `tendon rupture`).
**Why:** Directly passing internal schema keys to external APIs (like FAERS' `patient.reaction` field) corrupted the signal strength, yielding zero results for heavily documented side effects because the endpoints expect spaces. After implementing normalization, the pipeline achieved 100% Specificity and 100% Lenient Recall on the 15-pair ground truth. (Strict Recall remains 0%, as all true positives correctly triggered `MONITOR` rather than `ESCALATE`).

## 12. Confidence Score Comparability Caveat (Baseline vs. Pipeline)
**Decision:** When presenting comparison tables between PharmaGuard and the single-shot baseline, any column labelled "confidence" must carry a note distinguishing the two scales.
**Why:** PharmaGuard's `confidence` is a deterministic formula output:
```
confidence = 0.40 × PRR_score + 0.40 × grade_score + 0.20 × plausibility_score
```
It is bounded by what the FAERS/PubMed/ChEMBL data can support and is fully reproducible.
The baseline's `confidence` is raw LLM self-report — a single-call subjective probability estimate with no grounding in external data. The escalation **decisions** (ESCALATE / MONITOR / DO_NOT_ESCALATE) are directly comparable across both systems. The confidence **numbers** are not on the same scale and must not be presented as if they are.

**Standard footnote to attach to any comparison table:**
> ⚠️ "Confidence" values are not directly comparable: PharmaGuard uses a deterministic weighted formula over FAERS PRR score, PubMed evidence grade, and ChEMBL plausibility score; the baseline uses raw LLM self-reported confidence with no grounding in external data. Escalation decisions are comparable; confidence numbers are not.

## 13. Preserved Example — liraglutide + pancreatic_cancer (Grounded vs. Ungrounded Reasoning)
**Purpose:** Citable illustration of the difference between PharmaGuard's tool-grounded triage and the baseline's ungrounded prior. Preserved here so it survives cache-clears and re-runs.

**Pair:** `liraglutide` + `pancreatic_cancer` | Ground truth: `genuine_negative_control` | Expected: `DO_NOT_ESCALATE`

### Baseline (Single-Shot LLM) — WRONG: ESCALATE, confidence=0.85
> *"Liraglutide is a GLP-1 receptor agonist, and there has been significant historical concern and ongoing regulatory scrutiny regarding the potential association between GLP-1 receptor agonists and an increased risk of pancreatitis and pancreatic neoplasms. Given the seriousness of pancreatic cancer, this signal warrants immediate escalation for formal safety review."*

The model correctly recalls that a concern exists, but it halts at the concern itself. It neither consults the regulatory resolution nor distinguishes "this concern was investigated" from "this concern was confirmed."

### PharmaGuard (Fixed Pipeline) — CORRECT: DO_NOT_ESCALATE, confidence=0.20
- **FAERS signal:** NO_SIGNAL (PRR score = 0.0) — FAERS disproportionality data did not support a statistically significant signal.
- **PubMed evidence grade:** B — retrieved abstracts contained association language but no statistical evidence (p-values, CIs excluding 1.0, hazard ratios) meeting Grade A criteria.
- **Plausibility:** LOW (agent-derived from GLP-1 receptor agonist MoA).
- **Outcome:** The hard NO_SIGNAL gate in `derive_escalation()` forces DO_NOT_ESCALATE regardless of literature grade or plausibility score.

**Why this matters for the writeup:**
The FDA and EMA both conducted formal safety reviews of GLP-1 agonists and pancreatic cancer (2014 FDA/EMA joint review; see `source_url` in `ground_truth.json`) and concluded the evidence was insufficient to establish causality. The baseline escalates on the unresolved historical concern; PharmaGuard correctly resolves it through signal grounding. This is the clearest single example in the 15-pair set of what tool-grounded triage adds over raw LLM recall.

