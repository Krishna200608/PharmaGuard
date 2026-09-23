# PharmaGuard — Anticipated Viva & Capstone Defense Q&A Guide
### Step-by-Step Mathematical Defenses, Epidemiological Proofs, and Architectural Rationales

**Project:** PharmaGuard — Intelligent Pharmacovigilance Signal Triage Orchestrator  
**Team (Group 07):** Krishna Sikheriya (IIT2023139, Team Leader) · Lokesh Bawariya (IIT2023138) · Naitik Jain (IIB2023036)  
**Supervisor:** Dr. Nikhilanand Arya, Assistant Professor, Department of Information Technology  
**Evaluation:** B.Tech 7th-Semester Capstone Project Defense (2026–27) · IIIT Allahabad  

---

## Quick Navigation Index

- **Module 1: Foundational Architecture & LLM Role** (Q1 – Q3)
- **Module 2: Biostatistics, Disproportionality & Woolf CIs** (Q4 – Q6)
- **Module 3: Benchmark Scale, PRR Dilution & Dual Metrics** (Q7 – Q9)
- **Module 4: Epistemic Defenses, Indication Concordance & Case Walkthroughs** (Q10 – Q12)
- **Module 5: Engineering Integrity, Local Ollama & Reproducibility** (Q13 – Q14)

---

# Module 1: Foundational Architecture & LLM Role

---

### Q1: "Why use an agent or multi-source pipeline at all? Can't we just give an LLM (like GPT-4 or Gemini) a zero-shot prompt with the drug and adverse event?"

#### The 30-Second Elevator Defense:
> "Generative LLMs tested without tools suffer from three fatal clinical failure modes: uncalibrated self-confidence, historical regulatory confusion, and parametric memory leakage. In our head-to-head empirical baseline, single-shot Gemini generated a 25.0% over-caution rate on negative controls, falsely escalating *Liraglutide + Pancreatic Cancer* based on 2013 historical alarms rather than a decade of negative cardiovascular trials and zero FAERS disproportionality. PharmaGuard replaces ungrounded text generation with deterministic evidence fusion and hard empirical safety stops."

#### Detailed Step-by-Step Evidence & Mathematical Grounding:
1. **Clinical Literature Evidence:** Omar et al. (2025, *Communications Medicine*, Nature Portfolio) benchmarked foundation models in clinical assurance tasks, proving that LLMs frequently output $>0.85$ self-confidence scores that have zero correlation with true clinical risk.
2. **The Liraglutide Failure Mode:**
   - In 2013, the FDA and EMA issued safety communications regarding GLP-1 receptor agonists and pancreatic cancer. Over the subsequent decade, multiple large prospective Cardiovascular Outcome Trials (CVOTs)—such as the LEADER trial ($N=9,340$, Marso et al., *NEJM* 2016)—established no causal relationship.
   - When queried, **Single-Shot Gemini** escalates the pair because its parametric weights memorized the high-profile 2013 alerts.
   - In contrast, **PharmaGuard** queries openFDA FAERS, finds $\text{PRR} = 1.08$ with Woolf lower bound $<1.0$ (`NO_SIGNAL`), and **Gate 1 immediately halts execution**, returning `DO_NOT_ESCALATE` with $\text{Confidence} = 0.000$.
3. **The Empirical Comparison ($N=15$ Core Baseline):**
   - **Single-Shot Baseline:** Strict Precision $0.875$, Lenient Precision $0.700$, Over-Caution Rate **$25.0\%$** (2/8 negative controls flagged).
   - **PharmaGuard:** Strict Precision **$1.000$**, Lenient Precision **$0.875$**, Over-Caution Rate **$12.5\%$** (halved).

---

### Q2: "What is the difference between your deterministic `FixedPipelineAgent` and the `PharmaGuardAgent` (LangGraph ReAct loop)? Why not just use ReAct everywhere?"

#### The 30-Second Elevator Defense:
> "In postmarketing drug safety surveillance, regulatory bodies like the US FDA and EMA require byte-level audit reproducibility and invariant execution trails. In our independent audit (DECISIONS.md §24), we found that unconstrained ReAct generative reasoning departed from deterministic safety gating in 4 out of 15 pairs (73.3% agreement). We maintain the FixedPipelineAgent for regulatory compliance and audit guarantees, while the LangGraph ReAct agent serves exploratory clinical research."

#### Detailed Step-by-Step Evidence:
- **Audit Findings (`scripts/verify_react_agreement.py`):**
  - Evaluated on 15 core pairs: 11 agreed, 4 diverged in synthesized recommendations (`montelukast`, `liraglutide`, `atorvastatin::dementia`, `albuterol`).
  - *Root Cause:* Generative LLMs inside an unconstrained loop inject freeform prior clinical opinions (e.g., treating observational commentary as hard evidence).
  - *Architectural Standard:* To prevent this, both agents share the exact same closed-form mathematical scoring formulas, but `FixedPipelineAgent` enforces a fixed, unskippable execution sequence (FAERS $\to$ ChEMBL $\to$ PubMed $\to$ Scoring Gates).

---

### Q3: "How do you prove that your LLM isn't just memorizing famous Boxed Warnings and regurgitating training data (parametric leakage)?"

#### The 30-Second Elevator Defense:
> "We explicitly proved that unconstrained LLMs leak regulatory training data, and we built an automated maker-checker critic (MARCH framework pattern) to detect and penalize it. When forced to reason without lookups, the LLM falsely upgraded Montelukast's biological plausibility by quoting the 2020 FDA Black Box Warning. Our Adversarial Mechanistic Critic achieved 100% detection sensitivity (4/4 cases), counterfactually stripping leaked scores down to zero."

#### Step-by-Step Experimental Demonstration:
1. **The 'Perfect Score' Red Flag (`DECISIONS.md §19`):**
   - Running the pipeline in `force_agent` mode (letting the LLM generate plausibility scores without human lookup tables) produced a superficially attractive $1.000$ Strict Recall ($15/15$).
   - Investigation proved this was an architectural failure: the model achieved $1.000$ recall solely because for *Montelukast + Suicidal Ideation*, it cited the 2020 FDA Boxed Warning and observational trial names in its pharmacological rationale, upgrading plausibility from `LOW (0.00)` to `MODERATE (0.50)`.
2. **The Blind Maker-Checker Critic (`_critique_plausibility_leakage()` in `chembl_tool.py`):**
   - We implemented a blind adversarial critic prompt inspired by the MARCH assurance framework.
   - The critic inspects the rationale for epistemic leakage markers (regulatory agency names, boxed warning citations, postmarketing phrases) without knowing the ground-truth label.
   - Tested across 4 documented leak cases (`outputs/critic_probe/`): achieved **4/4 (100%) detection sensitivity**, automatically catching the leak and downgrading plausibility back to `LOW (0.00)`.

---

# Module 2: Biostatistics, Disproportionality & Woolf CIs

---

### Q4: "Walk us through the exact mathematics of your PRR, ROR, and Woolf 95% Confidence Interval. Why is the lower bound crucial?"

#### The 30-Second Elevator Defense:
> "Raw reporting ratios can be wildly misleading with small sample counts. A drug with 2 reports out of 2 total co-occurrences has a PRR of infinity, but is statistically meaningless. PharmaGuard computes the 2x2 contingency table, calculates the Proportional Reporting Ratio and Reporting Odds Ratio, and inverts Woolf's asymptotic variance on the log scale. If the 95% lower confidence interval drops below 1.0, any signal—even if PRR exceeds 4.0—is downgraded to prevent small-sample false alarms."

#### Step-by-Step Mathematical Derivation:

Consider the standard $2 \times 2$ pharmacovigilance contingency matrix:

$$\begin{array}{|c|c|c|c|}
\hline
& \textbf{Adverse Event } (E) & \textbf{All Other Events } (\neg E) & \textbf{Total} \\
\hline
\textbf{Target Drug } (D) & a & b & a + b \\
\hline
\textbf{All Other Drugs } (\neg D) & c & d & c + d \\
\hline
\textbf{Total} & a + c & b + d & N = a + b + c + d \\
\hline
\end{array}$$

1. **Proportional Reporting Ratio (PRR, Evans et al. 2001):**
   $$\text{PRR} = \frac{a / (a + b)}{c / (c + d)}$$
   Measures the proportion of reports for drug $D$ that mention event $E$, relative to the proportion of reports for all other drugs mentioning event $E$.

2. **Reporting Odds Ratio (ROR, van Puijenbroek et al. 2002):**
   $$\text{ROR} = \frac{a / b}{c / d} = \frac{a \cdot d}{b \cdot c}$$

3. **Woolf Standard Error & 95% Log-Confidence Interval:**
   Because reporting ratios are positively skewed and bounded by zero, variance is estimated on the natural logarithmic scale $\ln(\text{PRR})$:
   $$\text{SE}(\ln \text{PRR}) = \sqrt{\frac{1}{a} - \frac{1}{a+b} + \frac{1}{c} - \frac{1}{c+d}}$$
   Under the asymptotic normality of $\ln(\text{PRR})$, the $95\%$ Confidence Interval is:
   $$\text{CI}_{95\%} = \exp\left( \ln(\text{PRR}) \pm 1.96 \cdot \text{SE}(\ln \text{PRR}) \right)$$
   $$\text{PRR}_{\text{lower}} = \exp\left( \ln(\text{PRR}) - 1.96 \cdot \text{SE}(\ln \text{PRR}) \right)$$

4. **The Downgrade Gating Rule (`DECISIONS.md §8`):**
   $$\text{If } \text{PRR} \ge 4.0 \text{ but } \text{PRR}_{\text{lower}} < 1.0 \implies \text{Downgrade STRONG (1.00) to MODERATE (0.66)}$$
   $$\text{If } a < 3 \implies \text{Force NO\_SIGNAL (0.00)}$$
   *Why this matters:* If $\text{PRR}_{\text{lower}} < 1.0$, the observed disproportionality is statistically indistinguishable from background reporting noise at the $\alpha = 0.05$ significance level.

---

### Q5: "Why did you use Wilson score intervals rather than standard Wald or bootstrap intervals in your benchmark tables?"

#### The 30-Second Elevator Defense:
> "Standard Wald intervals fail at boundary proportions ($\hat{p}=1.0$ or $0.0$), producing zero variance. Furthermore, non-parametric bootstrap resampling on samples with zero false positives produces a degenerate [1.000, 1.000] interval because every resampled fold contains zero false positives—a known mathematical boundary artifact. Wilson score intervals invert the score test under the binomial distribution, providing mathematically honest and defensible coverage even at small sample sizes."

#### Step-by-Step Mathematical Derivation:

1. **Failure of the Wald Interval:**
   $$\text{Wald Interval} = \hat{p} \pm z_{1-\alpha/2} \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}$$
   When our system achieves perfect Strict Precision ($\hat{p} = 1.000$ with $0$ false positives):
   $$\sqrt{\frac{1.0 \cdot (1 - 1.0)}{n}} = \sqrt{0} = 0 \implies [1.000, 1.000]$$
   This claims zero statistical uncertainty, which is mathematically false and academically dishonest for small sample sizes.

2. **Failure of Non-Parametric Percentile Bootstrap at Boundaries:**
   - Let empirical sample $X = \{1, 1, 1, \dots, 1\}$ ($FP = 0$).
   - Any bootstrap resample $X^*_b$ drawn with replacement from $X$ will exclusively contain $1$s.
   - Therefore, $\hat{p}^*_b = 1.000$ for all $B = 1000$ replicates, yielding $Q_{0.025} = 1.000$ and $Q_{0.975} = 1.000$.
   - Citing $[1.000, 1.000]$ as 'proven perfection' is a recognized methodological error (`DECISIONS.md §16`).

3. **The Wilson Score Solution (Wilson 1927):**
   Inverting the test statistic under $H_0: p = p_0$ gives the quadratic equation:
   $$\frac{(\hat{p} - p)^2}{p(1-p)/n} \le z^2$$
   Solving for $p$ yields the asymmetric Wilson score bounds:
   $$w = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
   For $n=15$ and $\hat{p} = 1.000$ ($z = 1.96$):
   $$w_{\text{lower}} = \frac{1.0 + \frac{1.96^2}{30} - 1.96 \sqrt{0 + \frac{1.96^2}{4 \cdot 15^2}}}{1 + \frac{1.96^2}{15}} = \frac{1.0 + 0.128 - 0.251}{1 + 0.256} = \frac{0.877}{1.256} \approx \mathbf{0.610}$$
   The Wilson interval correctly and honestly reports $[0.610, 1.000]$, expressing proper small-sample uncertainty.

---

### Q6: "How did you derive the composite confidence weights (0.40 FAERS, 0.40 PubMed, 0.20 ChEMBL)? Did you optimize them on your test data?"

#### The 30-Second Elevator Defense:
> "No. Optimizing linear weights on a 15-pair or 50-pair benchmark would be severe methodological overfitting. The weights are pre-registered expert heuristic priors grounded in clinical epidemiology: epidemiological reporting (FAERS, 40%) and clinical trial literature (PubMed, 40%) are primary clinical evidence streams, while molecular mechanism of action (ChEMBL, 20%) acts as a biological plausibility moderator."

#### Step-by-Step Methodological Grounding:
- **The Anti-Tuning Discipline (`DECISIONS.md §18`):**
  - Tuning $\alpha, \beta, \gamma$ via grid-search or logistic regression on $n \le 50$ would produce an artificially inflated $F_1$ that collapses on external datasets.
  - The weights reflect Bayesian evidence synthesis:
    $$\text{Confidence} = 0.40 \cdot S_{\text{FAERS}} + 0.40 \cdot S_{\text{PubMed}} + 0.20 \cdot S_{\text{ChEMBL}}$$
  - **Symmetry of Orthogonal Evidence:** FAERS ($40\%$) and PubMed ($40\%$) represent empirical patient populations. ChEMBL ($20\%$) cannot generate an alert alone, but can modulate borderline signals (e.g. lifting a $0.50$ to $0.70$ or dampening a signal below $0.70$).
  - **Leave-One-Out (LOO) Robustness:** In our Phase 4 Leave-One-Out cross-validation across all 15 folds, the mean Strict $F_1$ remained $0.9226 \pm 0.0225$, demonstrating that the heuristic boundaries are stable across individual sample removals.

---

# Module 3: Benchmark Scale, PRR Dilution & Dual Metrics

---

### Q7: "On your 100-pair OMOP benchmark, your Strict Recall is only 0.060 (3/50). Does that mean PharmaGuard fails on OMOP?"

#### The 30-Second Elevator Defense:
> "Quite the opposite: this is one of our most important scientific findings. On OMOP, PharmaGuard achieved 100% Strict Specificity—all 50 negative controls were completely cleared with zero false alarms. Strict Recall dropped on positive controls because OMOP consists of widely prescribed chronic medications (amlodipine, sertraline, nifedipine) where massive prescription volume creates 'PRR Denominator Dilution,' depressing the raw PRR into the 1.1–1.9 range despite thousands of real reports. PharmaGuard's tri-source fusion safely routed these chronic toxicities into MONITOR rather than dropping them, which is exactly why Lenient Recall is 0.280 with 93.3% precision."

#### Step-by-Step Mathematical Proof of Denominator Dilution:

1. **The Mathematical Mechanics:**
   $$\text{PRR} = \frac{a / (a + b)}{c / (c + d)}$$
   - Let Drug $D$ be a high-utilization chronic therapy (e.g., *Amlodipine*, prescribed to tens of millions of hypertensive patients over decades).
   - In FAERS, the total reported adverse events for Amlodipine across all categories ($a + b$) is enormous ($a + b \approx 350,000+$).
   - Suppose Amlodipine causes a severe adverse event $E$ with $a = 2,500$ spontaneous reports. This is a massive, life-threatening signal.
   - However, the ratio $a / (a + b) = 2,500 / 350,000 \approx 0.00714$.
   - If the background reporting rate across all other drugs $c / (c + d) \approx 0.00500$:
     $$\text{PRR} = \frac{0.00714}{0.00500} = \mathbf{1.428}$$
2. **The Clinical Failure of Single-Source Thresholds:**
   - Any classical regulatory system using the static Evans threshold ($\text{PRR} \ge 2.0$) **drops this signal immediately**.
   - Despite $a = 2,500$ reports, $\text{CI}_{\text{lower}} = 1.37 > 1.0$, and established pharmacology, the static threshold categorizes it as `WEAK` or `NO_SIGNAL`.
3. **How PharmaGuard Protects the Patient:**
   - Because $S_{\text{FAERS}} = 0.33$ (`WEAK`), the pair cannot reach the $0.70$ threshold required for `ESCALATE`.
   - However, PubMed assigns Grade A ($S_{\text{PubMed}} = 1.00$) and ChEMBL provides receptor plausibility ($S_{\text{ChEMBL}} = 0.50$):
     $$\text{Confidence} = 0.40(0.33) + 0.40(1.00) + 0.20(0.50) = 0.132 + 0.400 + 0.100 = \mathbf{0.632}$$
   - Because $0.632 \ge 0.35$, PharmaGuard routes the drug to **`MONITOR`**.
   - It is never dismissed, and the clinical safety team is instructed to maintain quarterly surveillance.

---

### Q8: "Why do you need both Strict and Lenient metrics? Isn't having two metrics just cherry-picking to make numbers look better?"

#### The 30-Second Elevator Defense:
> "In clinical pharmacovigilance, an escalation decision is not binary—it represents operational triage. ESCALATE means immediate regulatory intervention and Dear Healthcare Provider letters. MONITOR means active watchlist surveillance. If we only reported Strict metrics, placing a real toxicity under active MONITOR would be penalized as a complete failure (False Negative). Reporting both Strict and Lenient metrics is standard pharmacovigilance practice (DECISIONS.md §14) to simultaneously measure high regulatory precision and patient safety protection."

#### Methodological Dual-Metric Mapping:

```
                      ┌─────────────────────────────────────────┐
                      │            Evaluation Metric            │
                      └────────────────────┬────────────────────┘
                         ┌─────────────────┴─────────────────┐
                         ▼                                   ▼
                ┌─────────────────┐                 ┌─────────────────┐
                │  Strict Metric  │                 │ Lenient Metric  │
                │(High Conviction)│                 │ (Safety Net)    │
                └────────┬────────┘                 └────────┬────────┘
                         │                                   │
Positive Prediction:     ESCALATE only                       ESCALATE or MONITOR
Negative Prediction:     MONITOR or DO_NOT_ESCALATE          DO_NOT_ESCALATE only
```

- **Operational Meaning of Strict Mode:**
  - Measures whether PharmaGuard can issue unhesitating, top-priority alerts with **zero false alarms**.
  - Across all 165 pairs, PharmaGuard achieved **1.0000 Strict Precision** (Core: 6/6, Blockbusters: 10/10, OMOP: 3/3). Not a single negative control was escalated.
- **Operational Meaning of Lenient Mode:**
  - Measures whether any true safety signal was completely discarded into the trash bin (`DO_NOT_ESCALATE`).
  - PharmaGuard achieved **1.0000 Lenient Recall** on Core (7/7) and **0.9200 Recall** on Top Prescribed Blockbusters (23/25 Boxed Warnings caught).

---

### Q9: "How does your Top Prescribed Blockbuster benchmark ($n=50$) differ from the Core benchmark ($n=15$)?"

#### The 30-Second Elevator Defense:
> "The 15-pair Core benchmark was our frozen methodological testbed covering edge cases like zero reports and polypharmacy. The 50-pair Blockbuster benchmark evaluates everyday clinical practice: 25 confirmed, high-mortality FDA Boxed Warnings across the most prescribed drug classes in America (Statins, ACE inhibitors, Antibiotics, Opioids, Antidepressants) against 25 balanced negative controls. PharmaGuard achieved an outstanding 0.9388 Lenient F1 score and 92.0% recall on Boxed Warnings while maintaining 96.0% specificity."

#### Master Cross-Benchmark Comparison Table:

| Benchmark Cohort | Sample Size ($N$) | Strict Precision | Strict Recall | Strict $F_1$ | Lenient Precision | Lenient Recall | Lenient Specificity | Lenient $F_1$ |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Core Showcase** | $15$ | **1.0000** | **0.8571** | **0.9231** | **0.8750** | **1.0000** | **0.8750** | **0.9333** |
| **Top Prescribed Blockbusters** | $50$ | **1.0000** | **0.4000** | **0.5714** | **0.9583** | **0.9200** | **0.9600** | **0.9388** |
| **OMOP Expanded Reference** | $100$ | **1.0000** | **0.0600** | **0.1132** | **0.9333** | **0.2800** | **0.9800** | **0.4308** |

---

# Module 4: Epistemic Defenses, Indication Concordance & Case Walkthroughs

---

### Q10: "If your Indication Concordance layer detects confounding by indication, why is it scoring-inert (weight = 0.000)? Why not discount the confidence score by 15%?"

#### The 30-Second Elevator Defense:
> "Because pharmacoepidemiological consensus (Walker 1996, Psaty 1999, Bate & Evans 2009) is unanimous: there is no universal scalar constant for confounding by indication. When we pre-registered and evaluated a 15% discount factor on 40 held-out pairs, it yielded a low-power null result (4/40 triggers, 0 decision boundary shifts). Worse, when we attempted chronic gate discounts, it caused an immediate false-positive regression on Atorvastatin and Dementia. Keeping the flag scoring-inert provides transparent audit provenance without overfitting the model."

#### The 3 Architectural Pillars of the Isolation Wall:
1. **The 'Atorvastatin Regression Trap' (`DECISIONS.md §32`):**
   - In Sprint 4, an automated chronic conditioning gate was proposed to rescue diluted OMOP signals.
   - When deployed, it immediately caused an unexpected false-positive regression on `atorvastatin::dementia` in the Core benchmark: because Atorvastatin is a chronic cardiovascular drug, the chronic relaxation boosted background noise into a false alarm.
2. **Empirical Held-Out Validation (`DECISIONS.md §36`):**
   - Tested 40 untouched OMOP pairs (20 positive, 20 negative) with a pre-registered 15% discount ($\delta = 0.85$).
   - The flag fired on only 4 pairs. In all 4 cases, confidence adjustments did not cross the $0.70$ or $0.35$ decision boundaries.
   - Result: 0 metric changes, 0 regressions, but 0 improvements. Applying a score penalty on 4 cases is ungrounded statistical guesswork.
3. **The Design Solution:**
   - The 7 Indication Concordance rules (`IND-CONF-01` to `07`) run live and attach a structured warning badge (`CONCORDANT` vs. `DISCORDANT`) to the clinical report.
   - Clinicians are alerted that the adverse event overlaps with the treated disease, but mathematical scoring remains pure and uncorrupted.

---

### Q11: "Explain the Montelukast case study. Why does PharmaGuard output `MONITOR` instead of `ESCALATE`, even though the FDA issued a Boxed Warning for suicidal ideation?"

#### The 30-Second Elevator Defense:
> "Because PharmaGuard refuses to hallucinate biological certainty. Montelukast has an established epidemiological signal in FAERS and PubMed, but mechanistically it is a peripheral CysLT1 receptor antagonist with no confirmed central neuroreceptor mechanism. Our ChEMBL engine accurately assigns plausibility=LOW (0.00), which dampens the composite confidence to 0.664—just below the 0.70 ESCALATE cutoff. Triaging Montelukast as MONITOR is clinically and epistemically correct: it keeps the drug under active surveillance without fabricating an unproven biochemical mechanism."

#### Step-by-Step Score Breakdown for Montelukast + Suicidal Ideation:

$$\begin{array}{llll}
\textbf{Evidence Stream} & \textbf{Raw Tool Output} & \textbf{Mapped Score} & \textbf{Weighted Value} \\
\hline
\text{openFDA FAERS} & \text{PRR} = 3.65, \, n = 852, \, \text{CI}_{\text{lower}} = 3.41 & S_{\text{FAERS}} = 0.66 \, (\text{MODERATE}) & 0.40 \times 0.66 = 0.264 \\
\text{PubMed NCBI} & \text{Epidemiological cohorts, Boxed Warning} & S_{\text{PubMed}} = 1.00 \, (\text{Grade A}) & 0.40 \times 1.00 = 0.400 \\
\text{ChEMBL MoA} & \text{Selective CysLT}_1 \text{ antagonist (peripheral)} & S_{\text{ChEMBL}} = 0.00 \, (\text{LOW}) & 0.20 \times 0.00 = 0.000 \\
\hline
\textbf{Composite Confidence} & & & \mathbf{0.664}
\end{array}$$

- **Escalation Gating Logic:**
  - $\text{Confidence} = 0.664 < 0.700 \implies$ Does not meet the `ESCALATE` threshold.
  - $\text{Confidence} = 0.664 \ge 0.350 \implies$ Triggers **`MONITOR`**.
- **Clinical Alignment:** The FDA's own Boxed Warning review explicitly notes that despite epidemiological signals, the biological mechanism linking leukotriene antagonism to central suicidality remains unknown. PharmaGuard's triage perfectly reflects state-of-the-art pharmacovigilance.

---

### Q12: "Explain the Metformin and Hypoglycaemia case study. How does your system prevent a false alarm when there are 9,344 FAERS reports?"

#### The 30-Second Elevator Defense:
> "Metformin is a classic example of polypharmacy confounding. Spontaneous reporting contains 9,344 reports of hypoglycaemia with metformin because diabetic patients frequently take metformin alongside sulfonylureas or insulin. As a monotherapy, metformin suppresses hepatic gluconeogenesis via AMPK and does not stimulate insulin secretion—it cannot cause primary hypoglycaemia. PharmaGuard's ChEMBL and PubMed tools score plausibility and literature as zero, de-escalating the signal to MONITOR and eliminating false alarms."

#### Step-by-Step De-Escalation Breakdown:

$$\begin{array}{llll}
\textbf{Evidence Stream} & \textbf{Raw Tool Output} & \textbf{Mapped Score} & \textbf{Weighted Value} \\
\hline
\text{openFDA FAERS} & \text{PRR} = 10.73, \, n = 9,344 & S_{\text{FAERS}} = 1.00 \, (\text{STRONG}) & 0.40 \times 1.00 = 0.400 \\
\text{PubMed NCBI} & \text{Observational / Polypharmacy reports} & S_{\text{PubMed}} = 0.00 \, (\text{Grade C}) & 0.40 \times 0.00 = 0.000 \\
\text{ChEMBL MoA} & \text{AMPK activator, no insulin stimulation} & S_{\text{ChEMBL}} = 0.00 \, (\text{LOW}) & 0.20 \times 0.00 = 0.000 \\
\hline
\textbf{Composite Confidence} & & & \mathbf{0.400}
\end{array}$$

- **Decision Outcome:**
  - Confidence drops to $0.400$ ($< 0.70$) $\implies$ Successfully blocked from `ESCALATE`.
  - In Strict mode, this counts as a True Negative ($\text{FP} = 0$).
  - When the optional confounding de-biasing tool is applied (`DECISIONS.md §28`), co-medication discounting drops confidence to $0.080$, completely routing it to `DO_NOT_ESCALATE`.

---

# Module 5: Engineering Integrity, Local Ollama & Reproducibility

---

### Q13: "How do you guarantee that your results are 100% reproducible and didn't drift over the semester?"

#### The 30-Second Elevator Defense:
> "We enforce a strict Zero Live API Dependency during benchmark evaluation. Every tool query is hashed using deterministic SHA-256 keys into persistent diskcache databases. We run 242 automated pytest unit and regression tests that verify byte-identical output schemas, formula invariants, and cached responses in 103 seconds. The entire project can be reproduced from a clean clone with zero internet connection."

#### Verification Protocols:
1. **Deterministic Cache Schema (`pharmaguard/utils/cache.py`):**
   - Diskcache keys follow strict namespaces: `faers::<drug>::<event>`, `pubmed_grade::<drug>::<event>`, `atc::<drug>`.
   - Prevents spontaneous reporting count shifts from live FDA updates from invalidating published benchmarks.
2. **Automated Continuous Testing:**
   - **242 / 242 tests passing** via `pytest`.
   - Covers schema validation, Woolf confidence intervals, Evans disproportionality bounds, ATC hierarchy resolution, and critic probe invariants.

---

### Q14: "How did you solve the rate limit and cost issues of running 165 pairs against LLM APIs?"

#### The 30-Second Elevator Defense:
> "We implemented a dual-backend architecture supporting both Cloud Gemini and an on-device Ollama daemon running `qwen2.5:7b`. Evaluating 165 pairs across multiple tools with cloud APIs would have triggered rate limits and recurring costs. By executing inference locally via `http://localhost:11434`, we evaluated our entire 50-pair Blockbuster and 100-pair OMOP cohorts with zero API cost, unmetered speed, and complete patient data privacy."

#### Backend Architecture Highlights:
- **Zero-Rate-Limit Infrastructure:** Local Ollama backend achieves unmetered throughput without 15 RPM free-tier ceilings.
- **Strict Typing:** All outputs strictly validated against Pydantic v2 data models (`TriageReport`, `LeakageCritique`).
- **Seamless Toggling:** Switch between Local Ollama and Cloud Gemini via a single configuration flag (`config.yaml`).

---

## 🎯 Final Defense Presentation Tip for Krishna, Lokesh & Naitik

When the evaluation committee asks a challenging question:
1. **Acknowledge the core clinical tension:** (e.g., *"That is a fundamental challenge in pharmacovigilance..."*)
2. **State the mathematical or architectural principle first:** (e.g., *"PharmaGuard handles this through the Gate 1 empirical stop..."*)
3. **Anchor in concrete empirical numbers:** (e.g., *"Across our 100-pair OMOP benchmark, this preserved 100% Strict Specificity..."*)
4. **Offer a live demo verification:** (e.g., *"We can run this live on localhost:8501 right now to inspect the contingency table."*)
