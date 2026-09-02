# Understanding PharmaGuard

*A project overview for anyone joining this project with no prior context. This is a summary — the full decision-by-decision record with rationale lives in `docs/context/DECISIONS.md` (31 numbered sections), and this document points there wherever more depth is warranted. Where something in the project's own record is genuinely unclear, unverified, or still open, this document says so directly rather than smoothing it over.*

---

## 1. What this project actually does

PharmaGuard looks at a **drug** and a **possible side effect** — for example, "does semaglutide cause pancreatitis?" — and returns one of three decisions:

- **ESCALATE** — this looks like a real safety signal worth formal review
- **MONITOR** — worth watching; not confident enough yet to escalate, but not safe to dismiss either
- **DO_NOT_ESCALATE** — no real evidence of a problem

The core design choice: PharmaGuard is required to pull real evidence from three public data sources before answering, rather than letting an AI model just answer from what it already "knows" (its training data). That distinction — grounded reasoning versus memorized recall — is the actual thesis of the project, and it is demonstrated concretely through empirical comparisons and adversarial probes.

**Why this matters:** when a new drug safety concern surfaces, someone has to triage it — decide whether it's worth a formal investigation. This is a real, ongoing bottleneck in pharmacovigilance work. PharmaGuard is a capstone research prototype exploring whether an AI system, forced to check real evidence rather than reason from memory alone, can do a credible, transparent first pass at that triage.

**Stated plainly, because it shapes how to read everything below:** this is a research prototype evaluated on a frozen benchmark of 15 hand-curated drug-event pairs, supplemented by targeted epistemic self-probes. It is not a validated clinical tool. Every primary performance claim in this document is scoped to that 15-pair set.

---

## 2. How it works

### The three data sources

**FAERS** (FDA Adverse Event Reporting System) — the FDA's public database of real, spontaneously reported drug side effects. PharmaGuard queries it for a specific drug+event pair and computes a **PRR (Proportional Reporting Ratio)**: roughly, "how much more often is this event reported for this drug compared to how often it's reported for all other drugs combined?" A PRR near 1.0 means no unusual pattern; well above 2.0 starts looking like a real statistical signal. This is the system's empirical grounding.

**ChEMBL** — a public database of drug mechanisms. PharmaGuard uses it to ask: "biologically, does this drug's known mechanism make it plausible it could cause this event?" This is rated **HIGH / MODERATE / LOW / UNKNOWN** and is called *plausibility*. By default, plausibility comes from a small human-curated lookup table (someone read the mechanism and made a judgment call in advance); if a pair isn't in that table, the system falls back to asking the LLM to derive plausibility from the raw mechanism text.

**PubMed** — the medical literature database. PharmaGuard searches it, retrieves abstracts, and has the LLM grade the strength of what it finds: **Grade A** (statistically significant findings), **Grade B** (weaker or case-report-level support), or **Grade C** (nothing supportive found).

### Combining three signals into one number

```
confidence = 0.40 × (FAERS signal strength) + 0.40 × (literature grade) + 0.20 × (plausibility)
```

This is a fixed, deterministic formula — not an LLM guess. Each input maps to a fixed sub-score:
- FAERS: `NO_SIGNAL = 0.0`, `WEAK = 0.33`, `MODERATE = 0.66`, `STRONG = 1.0`
- Literature grade: `A = 1.0`, `B = 0.5`, `C = 0.0`
- Plausibility: `HIGH = 1.0`, `MODERATE = 0.5`, `LOW / UNKNOWN = 0.0`

### Turning confidence into a decision

The escalation rule is evaluated top to bottom, first match wins:

1. **If FAERS shows no real signal at all (NO_SIGNAL), the answer is always DO_NOT_ESCALATE** — regardless of confidence. This is a deliberate hard safety gate: without it, a pair with zero real-world reports could still theoretically reach a moderate confidence score purely from strong literature debates and plausibility, which would be the wrong behavior for a triage tool grounded in real-world evidence.
2. If confidence ≥ 0.70 and the FAERS signal is at least MODERATE → **ESCALATE**
3. If confidence ≥ 0.35 → **MONITOR**
4. Otherwise → **DO_NOT_ESCALATE**

Note: the 0.70 / 0.35 thresholds are documented as **uncalibrated priors**, not empirically tuned values — there isn't enough data (15 pairs) to calibrate them via ROC search. This is stated explicitly in `DECISIONS.md §18`.

### Cross-source evidence agreement heuristic (DECISIONS.md §26)

To monitor internal consistency across modalities, PharmaGuard computes a deterministic concordance heuristic (`source_agreement`):
$$\text{DISCORDANT} \iff \max(S_{\text{FAERS}}, S_{\text{Lit}}, S_{\text{Mech}}) \ge 0.66 \land \min(S_{\text{FAERS}}, S_{\text{Lit}}, S_{\text{Mech}}) \le 0.33$$
Otherwise, the evidence profile is `CONCORDANT`.

Across the 15 benchmark pairs, exactly **3 pairs (20.0%)** are classified as `DISCORDANT`:
1. `montelukast::suicidal_ideation` (Grade A literature & moderate FAERS vs. unconfirmed CNS mechanism)
2. `metformin::hypoglycaemia` (Strong confounded FAERS reporting vs. grade C literature & zero mechanistic plausibility)
3. `atorvastatin::dementia` (Substantial associative literature debate vs. zero FAERS disproportionality)

This heuristic deterministically flags cases where high confidence in one modality conflicts with absence in another, alerting safety reviewers to underlying epistemic tension.

### Two ways the pipeline can run — and an empirical divergence finding (DECISIONS.md §24)

- **Fixed pipeline** (production default): a deterministic sequence — FAERS → ChEMBL → PubMed → combine. No LLM discretion over tool execution order or score combination.
- **ReAct agent**: an LLM-driven loop (via LangGraph) that decides tool call order dynamically.

**Crucial empirical finding (§24):** When the ReAct agent's unconstrained generative recommendation was compared against the deterministic pipeline across the 15 pairs, they **diverged on 4 out of 15 pairs (26.7%)**:
- For nominal negatives (`atorvastatin::dementia`, `albuterol::suicidal_ideation`), the unconstrained agent recommended `ESCALATE` or `MONITOR` swayed by associative literature mentions, whereas the deterministic pipeline strictly enforced the FAERS disproportionality gate to output `DO_NOT_ESCALATE`.
- For `liraglutide::pancreatic_cancer`, the unconstrained agent recommended `MONITOR` based on theoretical receptor debates, whereas the fixed pipeline correctly enforced the hard `NO_SIGNAL` zero-report safety gate.

This divergence directly demonstrates why postmarketing safety triage cannot rely on unconstrained generative LLM recommendations alone without deterministic multi-source gating.

---

## 3. The real results — including the imperfect parts, on purpose

### Primary benchmark metrics (with statistical confidence intervals)

Evaluated on the frozen 15-pair evaluation set (reproduced from a clean clone, empty cache — see `PROGRESS.md`):

| Metric | Strict (ESCALATE only counts as correct) | 95% Confidence Interval | Lenient (ESCALATE or MONITOR counts as correct) | 95% Confidence Interval |
|---|---|---|---|---|
| **Precision** | **1.000** | [0.610, 1.000] (Wilson) | **0.875** | [0.529, 0.978] (Wilson) |
| **Recall** | **0.857** (6/7) | [0.487, 0.974] (Wilson) / [0.571, 1.000] (Bootstrap) | **1.000** (7/7) | [0.646, 1.000] (Wilson) / [1.000, 1.000] (Bootstrap) |
| **Specificity** | **1.000** | [0.676, 1.000] (Wilson) | **0.875** | [0.529, 0.978] (Wilson) |
| **F1 Score** | **0.923** | [0.727, 1.000] (BCa Bootstrap) | **0.933** | [0.769, 1.000] (BCa Bootstrap) |
| **Over-caution rate** | — | — | **12.5%** | 1 of 8 negative controls $\to$ MONITOR |
| **Spurious false alarms** | **0** | Strict Wilson: [0.610, 1.000] | — | — |

### Leave-One-Out (LOO) stability analysis (DECISIONS.md §29)

To verify that these results do not hinge on a single fragile pair, a 15-fold Leave-One-Out cross-validation was performed:
- **Strict F1:** $0.923 \pm 0.023$ (range: $0.889$ to $1.000$). The most brittle pair is `montelukast::suicidal_ideation` (excluding this single strict false negative swings F1 by $+0.077$ to $1.000$).
- **Lenient F1:** $0.933 \pm 0.019$ (range: $0.923$ to $1.000$). The most brittle pair is `metformin::hypoglycaemia` (excluding this single lenient false positive swings F1 by $+0.067$ to $1.000$).

The narrow standard deviations ($\pm 0.023$ and $\pm 0.019$) confirm that system performance is stable across single-pair perturbations.

---

### The two documented edge cases — and how they were investigated

This project reports an honest headline result with two documented "misses":

#### Case 1 — `montelukast` + `suicidal_ideation` (confirmed positive)
- **Baseline Result:** The system outputs **MONITOR** (confidence 0.664), just below the 0.70 ESCALATE threshold.
- **Root Cause:** FAERS shows a moderate signal (PRR 3.37, 1,259 reports) and literature is Grade A, but the biological mechanism for neuropsychiatric events remains unconfirmed in pharmacology. The curated plausibility rating is honestly LOW ($0.00$).
- **The Ablation Danger (§19):** When run in `force_agent` mode (allowing the LLM to derive plausibility dynamically), recall rose to a clean 1.000. However, inspection revealed this was caused by **parametric regulatory leakage**: the LLM recalled the FDA's 2020 Boxed Warning and upgraded plausibility to MODERATE, substituting memorized regulatory action for genuine biochemical reasoning.
- **The Solution — Adversarial Leakage Critic (§27):** PharmaGuard implemented an independent, blind adversarial critic (inspired by the MARCH framework, ACL 2026) that reviews the primary agent's rationale without access to the drug or event names. Across 4 leakage probe cases, the critic demonstrated **100% detection sensitivity (4/4)**. When applied to Montelukast, the critic isolated the leaked boxed warning phrases and counterfactually downgraded the mechanistic score from MODERATE back to **LOW**, confirming that without regulatory leakage, Montelukast's signal is naturally restrained by mechanistic uncertainty.

#### Case 2 — `metformin` + `hypoglycaemia` (negative control)
- **Baseline Result:** The system outputs **MONITOR** (confidence 0.400), above the 0.35 threshold, creating a lenient false positive.
- **Root Cause:** In spontaneous reporting, metformin co-occurs with hypoglycemia in ~9,300 reports ($PRR = 10.73$) due to polypharmacy: it is routinely co-prescribed with insulin or sulfonylureas in diabetic populations. Because the formula assigns 0.40 weight to FAERS, a strong PRR score guarantees a 0.40 floor regardless of literature (Grade C) or plausibility (LOW).
- **The Solution — Confounding-Aware Discounting (§28):** PharmaGuard added an opt-in confounding evaluator (`pharmaguard/tools/confounding.py`). When evaluated on `metformin::hypoglycaemia`, it identified concomitant insulin and sulfonylureas and computed a **0.20 discount factor**. Multiplying the FAERS sub-score by 0.20 dropped composite confidence from **0.4000 to 0.0800**, correctly routing the signal to **DO_NOT_ESCALATE** and clearing the sole lenient false positive without altering formula weights.
- **Mandatory Epistemic Self-Probe (§28):** An audit across 4 real pairs revealed that the confounding tool itself exhibits clear markers of pre-trained clinical recall (e.g. citing standard ADA diabetes multi-drug regimens). It serves as an effective expert heuristic discounting layer, but inherits the same epistemic circularity as LLM plausibility derivation (§17).

---

### Comparison against a simpler baseline

PharmaGuard was compared against a single-shot LLM baseline (one prompt, no tool access, no real data) on the same 15 pairs:

| Metric | PharmaGuard (Tool-Grounded) | Single-Shot LLM Baseline (No Tools) |
|---|---|---|
| Strict P / R / F1 | 1.000 / 0.857 / 0.923 | 0.875 / 1.000 / 0.933 |
| Lenient P / R / F1 | 0.875 / 1.000 / 0.933 | 0.700 / 1.000 / 0.824 |
| Over-caution rate | 12.5% | 25.0% |

**Key Illustration:** For `liraglutide` + `pancreatic_cancer` (investigated and cleared jointly by the FDA and EMA in 2014), the baseline confidently escalated anyway, citing "historical concern and ongoing regulatory scrutiny" from memory. PharmaGuard correctly returned DO_NOT_ESCALATE based on empirical FAERS data showing zero disproportionality.

**Important caveat:** PharmaGuard's confidence score is derived from a deterministic formula; the baseline's confidence is an uncalibrated number self-reported by the model. Only final escalation decisions are directly comparable (`DECISIONS.md §12`).

---

## 4. What's still genuinely open

1. **Human expert validation** — Biological plausibility ratings remain based on human-curated pharmacology summaries and LLM derivation; formal review by an external panel of clinical pharmacologists is planned as future work.
2. **Escalation threshold calibration** — The 0.70 / 0.35 thresholds are fixed priors. Empirical threshold optimization (e.g., via Youden's J or ROC optimization) requires scaling the ground truth set well beyond 15 pairs (`DECISIONS.md §18`).
3. **MedDRA term normalization** — Spontaneous reporting databases use specific MedDRA Preferred Terms (PT) or British spellings (e.g., `hypoglycaemia`). A general-purpose ontology resolution layer to map lay or American terms automatically remains planned for future production versions.
4. **Benchmark set size** — Deliberately fixed at 15 heavily vetted pairs for capstone scope; expansion to 50–100 pairs from OMOP/EU-ADR benchmarks is the natural next phase.
5. **EHR patient-level de-convolution** — While our confounding discount heuristic effectively addresses polypharmacy artifacts, true de-biasing requires patient-level electronic health records to mathematically deconvolve co-prescription odds ratios.

---

## 5. Interactive Dashboard & Verification Artifacts

PharmaGuard includes a production Streamlit evaluation dashboard (`scripts/dashboard.py`):
- **Tab 1: Evaluation Overview** — Headline recall, precision, confusion matrix, and 4-card Leave-One-Out stability metrics.
- **Tab 2: Per-Pair Table** — Dense aligned table with category/escalation filters, `AGREEMENT` badges (`DISCORDANT` vs `CONCORDANT`), and drill-down evidence breakdowns.
- **Tab 3: Disagreement Spotlight** — Deep-dive evidence and waterfall decomposition charts for Montelukast and Metformin.
- **Tab 4: Baseline Comparison** — Tool-grounded vs. ungrounded baseline metrics and Liraglutide case analysis.
- **Tab 5: Methodology Audits & Epistemic Probes** — Visual reporting for the Adversarial Leakage Critic (§27), Polypharmacy Confounding Self-Probe (§28), and side-by-side Metformin waterfall comparisons, styled with Google Material Icons.
- **High-Resolution Verification Captures:** High-resolution 1080p captures for all views in both Light and Dark modes are maintained under `assets/Screenshots/Light/` and `assets/Screenshots/Dark/`.

---

## 6. Where to look for more depth

| Question | Look here |
|---|---|
| Technical decisions and rationale (all 31 sections) | `docs/context/DECISIONS.md` |
| Sprint status and bug history | `docs/context/PROGRESS.md` |
| Software architecture & graph flow | `docs/context/ARCHITECTURE.md` |
| 15 ground-truth pairs with regulatory sourcing | `docs/context/GROUND_TRUTH_CANDIDATES.md` |
| Frozen production evaluation reports | `outputs/core/*.json` |
| Baseline & ablation reports | `outputs/experiments/baseline/`, `outputs/experiments/ablation/` |
| Stability & Leave-One-Out outputs | `outputs/research/stability/loo_analysis.json` |
| Adversarial critic probe outputs | `outputs/experiments/critic_probe/leakage_critique_results.json` |
| Confounding self-probe outputs | `outputs/experiments/confounding_probe/` |
| Interactive dashboard code | `scripts/dashboard.py` and `scripts/dashboard_modules/` |
| Verification screenshot captures | `assets/Screenshots/Light/`, `assets/Screenshots/Dark/` |