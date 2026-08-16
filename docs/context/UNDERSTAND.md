# Understanding PharmaGuard

*A project overview for anyone joining this project with no prior context. This is a summary — the full decision-by-decision record with rationale lives in `docs/context/DECISIONS.md` (21 numbered sections), and this document points there wherever more depth is warranted. Where something in the project's own record is genuinely unclear, unverified, or still open, this document says so directly rather than smoothing it over.*

---

## 1. What this project actually does

PharmaGuard looks at a **drug** and a **possible side effect** — for example, "does semaglutide cause pancreatitis?" — and returns one of three decisions:

- **ESCALATE** — this looks like a real safety signal worth formal review
- **MONITOR** — worth watching; not confident enough yet to escalate, but not safe to dismiss either
- **DO_NOT_ESCALATE** — no real evidence of a problem

The core design choice: PharmaGuard is required to pull real evidence from three public data sources before answering, rather than letting an AI model just answer from what it already "knows" (its training data). That distinction — grounded reasoning versus memorized recall — is the actual thesis of the project, and it is demonstrated concretely later in this document, not just asserted.

**Why this matters:** when a new drug safety concern surfaces, someone has to triage it — decide whether it's worth a formal investigation. This is a real, ongoing bottleneck in pharmacovigilance work. PharmaGuard is a semester capstone prototype exploring whether an AI system, forced to check real evidence rather than reason from memory alone, can do a credible first pass at that triage.

**Stated plainly, because it shapes how to read everything below:** this is a research prototype evaluated on 15 hand-curated drug-event pairs, not a validated clinical tool. Every performance claim in this document is scoped to that 15-pair set.

---

## 2. How it works

### The three data sources

**FAERS** (FDA Adverse Event Reporting System) — the FDA's public database of real, spontaneously reported drug side effects. PharmaGuard queries it for a specific drug+event pair and computes a **PRR (Proportional Reporting Ratio)**: roughly, "how much more often is this event reported for this drug compared to how often it's reported for all other drugs combined?" A PRR near 1.0 means no unusual pattern; well above 2.0 starts looking like a real statistical signal. This is the system's closest thing to hard evidence.

**ChEMBL** — a public database of drug mechanisms. PharmaGuard uses it to ask: "biologically, does this drug's known mechanism make it plausible it could cause this event?" This is rated **HIGH / MODERATE / LOW / UNKNOWN** and is called *plausibility*. By default, plausibility comes from a small human-curated lookup table (someone read the mechanism and made a judgment call in advance); if a pair isn't in that table, the system falls back to asking the LLM to derive plausibility itself from the raw mechanism text.

**PubMed** — the medical literature database. PharmaGuard searches it, retrieves abstracts, and has the LLM grade the strength of what it finds: **Grade A** (statistically significant findings), **Grade B** (weaker or case-report-level support), or **Grade C** (nothing supportive found).

### Combining three signals into one number

```
confidence = 0.40 × (FAERS signal strength) + 0.40 × (literature grade) + 0.20 × (plausibility)
```

This is a fixed, deterministic formula — not an LLM guess. Each input maps to a fixed sub-score (e.g. FAERS: NO_SIGNAL=0.0, WEAK=0.33, MODERATE=0.66, STRONG=1.0; literature grade: A=1.0, B=0.5, C=0.0; plausibility: HIGH=1.0, MODERATE=0.5, LOW/UNKNOWN=0.0).

### Turning confidence into a decision

The escalation rule is evaluated top to bottom, first match wins:

1. **If FAERS shows no real signal at all (NO_SIGNAL), the answer is always DO_NOT_ESCALATE** — regardless of confidence. This is a deliberate hard safety gate: without it, a pair with zero real-world reports could still theoretically reach a moderate confidence score purely from strong literature and plausibility, which would be the wrong behavior for a triage tool grounded in real-world evidence.
2. If confidence ≥ 0.70 and the FAERS signal is at least MODERATE → **ESCALATE**
3. If confidence ≥ 0.35 → **MONITOR**
4. Otherwise → **DO_NOT_ESCALATE**

Note: the 0.70 / 0.35 thresholds are documented as **uncalibrated priors**, not empirically tuned values — there isn't enough data (15 pairs) to calibrate them properly. This is stated explicitly in `DECISIONS.md §18`, not left implicit.

### Two ways the pipeline can run

- **Fixed pipeline** (production default): a deterministic sequence — FAERS → ChEMBL → PubMed → combine. No LLM discretion over order.
- **ReAct agent**: an LLM-driven loop (via LangGraph) that decides tool call order dynamically.

Both are described in `ARCHITECTURE.md` as production-verified, though that file's specific metric numbers are dated Aug 12 and predate several later fixes — treat `DECISIONS.md` and `docs/context/PROGRESS.md` as the more current source for exact numbers.

---

## 3. The real results — including the imperfect parts, on purpose

**Final verified numbers on the 15-pair evaluation set** (reproduced from a clean clone, empty cache — see `PROGRESS.md`):

| | Strict (ESCALATE only counts as correct) | Lenient (ESCALATE or MONITOR counts as correct) |
|---|---|---|
| Precision | 1.000 | 0.875 |
| Recall | 0.857 (6/7) | 1.000 (7/7) |
| Specificity | 1.000 | 0.875 |
| F1 | 0.923 | 0.933 |
| Over-caution rate | — | 12.5% (1 of 8 negative pairs got MONITOR) |

**Why two metrics, and why 6/7 is reported as the honest headline result rather than a clean 15/15:**

This project deliberately reports a result with two documented "misses," and that's worth understanding rather than skimming past.

**Case 1 — `montelukast` + `suicidal_ideation` (a real, confirmed FDA boxed-warning case).** The system gives **MONITOR**, not the expected ESCALATE. Why: FAERS shows a real, moderate statistical signal and the literature grade is strong (A), but the drug's actual biological mechanism for causing neuropsychiatric effects is genuinely not well understood in pharmacology — the curated plausibility rating is honestly LOW. That drags composite confidence to 0.664, just under the 0.70 ESCALATE threshold. **This is not a bug.** It's the system correctly reflecting that a real, regulator-confirmed safety signal can exist without a confirmed biological mechanism — and MONITOR (not ESCALATE, but very much not DO_NOT_ESCALATE either) is arguably the epistemically honest answer here, not a failure.

**Case 2 — `metformin` + `hypoglycaemia` (a negative control).** The system gives **MONITOR**, not the expected DO_NOT_ESCALATE. Why: raw FAERS data shows a strong statistical signal (~9,300 reports) — but this is confounded, because metformin is frequently co-prescribed with insulin or other drugs that do cause hypoglycemia. The system correctly reasons through this: the LLM derives LOW plausibility (metformin's own mechanism doesn't cause hypoglycemia as monotherapy) and the literature grade comes back C (no real supporting evidence). That correctly *reduces* confidence from what raw statistics alone would suggest — but the FAERS signal is strong enough on its own that confidence still clears the 0.35 MONITOR threshold, so it doesn't drop all the way to DO_NOT_ESCALATE.

**Why this matters for how you read the metrics:** in both cases, the raw FAERS statistic alone would have been misleading, and the system's literature/plausibility reasoning correctly pulled the answer in the right direction — just not all the way. That's exactly why both a *strict* and *lenient* metric are reported side by side: strict recall (0.857) shows genuine caution on ambiguous cases; lenient recall (1.000) confirms the system never actually dropped a real signal or fully missed a confounded one. Reporting only one number would hide half the story either way.

**A note on how this 6/7 number came to be the reported result, since it's relevant to trusting the rest of this document:** an earlier version of this evaluation briefly reported a clean 15/15 after a plausibility-rubric revision — but that revision was found, on review, to have been reasoned about with foreknowledge of exactly which pair needed to change to reach 15/15. It was reverted, and the honest 6/7 result was restored and is what's reported everywhere in the current record. The full account, including the specific reasoning that revealed the bias, is preserved (not deleted) in `DECISIONS.md §15`, on the reasoning that an honest account of catching and correcting this is more credible than a suspiciously clean number. Worth reading directly if you want the full context.

### Comparison against a simpler baseline

PharmaGuard was compared against a single-shot LLM baseline (one prompt, no tool access, no real data) on the same 15 pairs:

| | PharmaGuard | Baseline |
|---|---|---|
| Strict P/R/F1 | 1.000 / 0.857 / 0.923 | 0.875 / 1.000 / 0.933 |
| Lenient P/R/F1 | 0.875 / 1.000 / 0.933 | 0.700 / 1.000 / 0.824 |
| Over-caution rate | 12.5% | 25.0% |

The clearest illustrative example: for `liraglutide` + `pancreatic_cancer` (a signal that was investigated and formally dismissed by the FDA and EMA jointly in 2014), the baseline confidently escalated anyway — its own stated reasoning cited "historical concern and ongoing regulatory scrutiny" without checking whether that concern was ever resolved. PharmaGuard correctly returned DO_NOT_ESCALATE, grounded in real FAERS data showing no actual signal. **Important caveat:** PharmaGuard's "confidence" number is the deterministic formula above; the baseline's "confidence" is the LLM directly self-reporting a number with no data behind it. The two confidence *scores* are not on the same scale and should never be compared directly — only the final escalation *decisions* are comparable. (See `DECISIONS.md §12`.)

### The ablation study — and a result that needs its warning label read, not skipped

PharmaGuard was also run in a mode (`force_agent`) that always derives plausibility from scratch via the LLM, bypassing the human-curated lookup table, specifically to compare LLM-derived vs. human-curated plausibility on the same pairs. Across 7 pairs where both a curated rating and an agent-derived rating exist, they agreed on 3 and disagreed on 4.

**In that same `force_agent` run, strict recall comes out to a perfect 1.000 — and this number needs to be read with its warning attached, not on its own.** It's perfect specifically because the LLM's plausibility judgment for `montelukast` got upgraded from LOW (the blinded, mechanism-only curated rating) to MODERATE, because the LLM's own reasoning cited the FDA's boxed warning directly — i.e., it leaked prior regulatory knowledge into what was supposed to be a pure mechanism-based judgment. That happened to push this one case over the ESCALATE threshold. **This is documented explicitly (`DECISIONS.md §16, §19`) as evidence of a real limitation — the LLM substituting memorized regulatory knowledge for genuine mechanistic reasoning — not as evidence that this mode performs better.** It should never be cited as a reason to prefer this configuration over the production default.

### A supplementary finding, outside the formal 15-pair set: can the system's reasoning be told apart from memorization?

A separate small probe (3 additional, deliberately obscure drug-event pairs, not part of the formal evaluation) tested whether the LLM's plausibility reasoning reflects genuine mechanistic inference or just recall of well-known cases. The honest finding: **it's not fully possible to tell the two apart using any real, literature-grounded pair.** The reason is structural, not a flaw in the test — a drug-event pair needs a real, citable mechanism to be a scientifically defensible test case in the first place, and that same citability is what makes it something the LLM could plausibly have encountered in its training data. All three probe rationales opened by stating the association was "well-documented" before giving a mechanistic explanation — meaning even carefully chosen "obscure" cases can't cleanly separate reasoning from recall. This is documented as an honest, stated limitation, not glossed over. Full detail in `DECISIONS.md §17, §20`.

---

## 4. What's still genuinely open

- **Human expert validation** of the plausibility ratings — deferred, not yet done. Planned as Future Scope.
- **Escalation threshold calibration** (0.70 / 0.35) — explicitly documented as uncalibrated priors; real calibration isn't feasible at n=15 and is out of scope for this project's timeline (`DECISIONS.md §18`).
- **The epidemiological-leakage question** — should the plausibility-derivation prompt be tightened to exclude regulatory/trial knowledge and force pure mechanistic reasoning, or is current behavior acceptable as long as it's documented? This has been observed and documented (`§19`) but not yet decided either way.
- **A formal Bradford Hill-style plausibility rubric** — drafted (`pharmaguard/prompts/plausibility_rubric.txt`) but explicitly *not* applied, and deferred indefinitely, because a session attempting to apply it was found to be biased by foreknowledge of which case needed to change (see the 15/15 note above). If this is revisited, it needs a process that guarantees the person defining the rubric doesn't know which specific case is failing — genuinely difficult to guarantee within one continuous work session.
- **MedDRA term coding** — a real, confirmed class of bug: internal event names (e.g. `hypoglycemia`) don't always match the exact term FAERS indexes under (`hypoglycaemia`, British spelling; or a MedDRA Lowest Level Term instead of the Preferred Term FAERS actually uses). Found and fixed for 2 of the 15 pairs during an audit; a general-purpose ontology normalization layer to catch this class of issue automatically is planned but not built (Sprint 4).
- **Ground truth set size** — deliberately fixed at 15 pairs for feasibility reasons; not planned to expand within this project's scope.

---

## 5. Where to look for more depth

| Question | Look here |
|---|---|
| Why was a specific technical decision made? | `docs/context/DECISIONS.md` — 21 numbered sections, each with a decision and its stated reasoning |
| What's the current sprint status / bug history? | `docs/context/PROGRESS.md` |
| How is the code actually structured? | `docs/context/ARCHITECTURE.md` (note: some specific metric numbers there are dated Aug 12 and may lag later fixes — cross-check against `PROGRESS.md` for current numbers) |
| Where did the 15 ground-truth pairs come from, with sourcing? | `docs/context/GROUND_TRUTH_CANDIDATES.md` |
| What does an actual real output look like? | `outputs/eval-run-*_report.json` (production), `outputs/baseline/` (baseline comparison), `outputs/ablation/` (ablation study) |
| Coding/data-curation conventions | `docs/context/CONVENTIONS.md` |

If anything in this document doesn't match what you find in those files, trust the files — this document is a summary, written to be readable, and could itself go stale the way `ARCHITECTURE.md` partially has. When in doubt, `DECISIONS.md` is the most authoritative single source, since it's where every fix and finding in this project's history was recorded at the time it happened.
