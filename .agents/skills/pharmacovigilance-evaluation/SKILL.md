---
name: pharmacovigilance-evaluation
description: >-
  Procedures, statistical standards, and evaluation protocols for PharmaGuard
  pharmacovigilance signal triage benchmarking. Covers 2x2 contingency tables,
  PRR/ROR calculation, MedDRA PT validation, the dual-metric framework (Strict vs.
  Lenient), Wilson and Bootstrap confidence intervals, escalation gating rules,
  and anti-leakage audit discipline.
---

# Pharmacovigilance Evaluation & Benchmark Protocol

This skill codifies the evaluation methodology, statistical standards, and audit discipline for the **PharmaGuard** triage pipeline. It is grounded directly in the project's design decisions, empirical audits, and benchmark results documented in `docs/context/DECISIONS.md` and `docs/context/PROGRESS.md`.

---

## 1. Core Philosophy: Grounded Triage vs. Parametric Recall

PharmaGuard is an automated triage layer that evaluates drug–adverse event pairs using three independent data streams. The central hypothesis is that **tool-grounded evidence synthesis** prevents the ungrounded clinical hallucinations and historical regulatory confusions inherent to single-shot LLMs (`DECISIONS.md §12`).

- **Deterministic Composite Score:** Confidence is computed via a fixed mathematical formula, not an LLM self-assessment.
- **Safety-First Pharmacovigilance:** Spurious false alarms (`FP`) must be minimized without silently dropping emerging signals (`FN`).

---

## 2. Data Streams & Score Formulations

### A. FAERS Statistical Disproportionality

Disproportionality is calculated from openFDA spontaneous adverse event reports using a standard $2 \times 2$ contingency table:

| | Target Adverse Event ($E$) | All Other Adverse Events ($\neg E$) | Total Reports |
| :--- | :---: | :---: | :---: |
| **Target Drug ($D$)** | $a$ | $b$ | $a + b$ |
| **All Other Drugs ($\neg D$)** | $c$ | $d$ | $c + d$ |

#### Key Metrics & Formulas:
1. **Proportional Reporting Ratio (PRR):**
   $$\text{PRR} = \frac{a / (a + b)}{c / (c + d)}$$
2. **Reporting Odds Ratio (ROR):**
   $$\text{ROR} = \frac{a \cdot d}{b \cdot c}$$
3. **Standard Error & 95% Confidence Interval for $\ln(\text{PRR})$:**
   $$\text{SE}(\ln \text{PRR}) = \sqrt{\frac{1}{a} - \frac{1}{a+b} + \frac{1}{c} - \frac{1}{c+d}}$$
   $$\text{PRR}_{95\%\text{ Lower}} = \exp\left(\ln(\text{PRR}) - 1.96 \cdot \text{SE}(\ln \text{PRR})\right)$$

#### Classification Thresholds & Discretization ($S_{\text{FAERS}}$):
A signal requires an absolute report floor of $a \ge 3$. If $a < 3$, it is classified as `NO_SIGNAL`.

| Signal Label | Criteria | Raw Sub-Score ($S_{\text{FAERS}}$) |
| :--- | :--- | :---: |
| **`STRONG`** | $\text{PRR} \ge 4.0$ and $a \ge 10$ and $\text{PRR}_{\text{lower}} \ge 2.0$ | `1.0` |
| **`MODERATE`** | $\text{PRR} \ge 2.0$ and $a \ge 3$ and $\text{PRR}_{\text{lower}} \ge 1.0$ | `0.66` |
| **`WEAK`** | $\text{PRR} \ge 1.5$ and $a \ge 3$ | `0.33` |
| **`NO_SIGNAL`** | $\text{PRR} < 1.5$ or $a < 3$ or $a = 0$ | `0.0` |

*Note on Lower CI Downgrade:* If $\text{PRR}_{\text{lower}} < 1.0$, a `STRONG` signal is downgraded to `MODERATE` to protect against small-sample instability (`DECISIONS.md §8`).

---

### B. ChEMBL Biological Plausibility

Evaluates whether the drug's known mechanism of action (MoA) biologically supports the adverse event.

- **Source Hierarchy (`lookup_first`):**
  1. Primary: Curated human expert lookup table (`plausibility_ratings.json`).
  2. Fallback: LLM-derived biological plausibility prompt using raw ChEMBL MoA and target descriptions.
- **Score Mapping ($S_{\text{Plausibility}}$):**
  - **`HIGH`** $\to$ `1.0` (Established receptor/enzyme pathway).
  - **`MODERATE`** $\to$ `0.5` (Indirect, theoretical, or tissue-specific link).
  - **`LOW`** / **`UNKNOWN`** $\to$ `0.0` (No biological or pharmacological link).

---

### C. PubMed Literature Evidence

Searches biomedical literature (`"[drug]"[tiab] AND "[event]"[tiab] AND "adverse"[tiab]`), retrieves up to 5 abstracts, and assigns an evidence grade.

- **Grade Mapping ($S_{\text{PubMed}}$):**
  - **`Grade A`** $\to$ `1.0`: Peer-reviewed clinical trials or systematic reviews with statistically significant metrics ($p < 0.05$, ROR/PRR 95% CIs, odds ratios).
  - **`Grade B`** $\to$ `0.5`: Observational studies, case series, or documented adverse event language lacking formal significance testing.
  - **`Grade C`** $\to$ `0.0`: Negative findings, unconfirmed commentary, or zero relevant abstracts.

---

## 3. Confidence Formula & Triage Decision Rules

### Composite Confidence Score:
$$\text{Confidence} = 0.40 \cdot S_{\text{FAERS}} + 0.40 \cdot S_{\text{PubMed}} + 0.20 \cdot S_{\text{Plausibility}}$$

$$\text{Confidence} \in [0.000, 1.000]$$

### Escalation Hierarchy (Evaluated Top-to-Bottom):

1. **Hard Safety Gate (Zero-Report / No-Signal Override):**
   $$\text{If } \text{FAERS} == \text{NO\_SIGNAL} \implies \mathbf{DO\_NOT\_ESCALATE}$$
   *Regardless of confidence score.* Prevents theoretical or literature-only concerns from triggering false alarms on drugs with no real-world postmarketing signals (`DECISIONS.md §5`).
2. **Escalate Gate:**
   $$\text{If } \text{Confidence} \ge 0.70 \text{ and } \text{FAERS} \in \{\text{STRONG}, \text{MODERATE}\} \implies \mathbf{ESCALATE}$$
3. **Monitor Gate:**
   $$\text{If } \text{Confidence} \ge 0.35 \implies \mathbf{MONITOR}$$
4. **Default:**
   $$\text{Otherwise} \implies \mathbf{DO\_NOT\_ESCALATE}$$

*Note:* Thresholds ($0.70$ and $0.35$) are established heuristic priors (`DECISIONS.md §18`). Formal empirical tuning is out of scope for small $n$ ($n \le 20$) to prevent validation overfitting.

---

## 4. MedDRA Preferred Term (PT) Validation Rules

Spontaneous reporting systems (openFDA/FAERS) strictly adhere to MedDRA ontology standards (`DECISIONS.md §21`). When designing or evaluating benchmark pairs:

1. **Preferred Term (PT) vs. Lowest Level Term (LLT):** Always query openFDA using exact MedDRA Preferred Terms. Queries on colloquial phrases or LLTs will return false zero-counts.
2. **British vs. US English Orthography:** MedDRA standardizes clinical terms in British English.
   - *Example:* `HYPOGLYCAEMIA` (9,344 FAERS reports) vs. `hypoglycemia` (0 reports).
   - *Example:* `ANAEMIA` vs. `anemia`, `DIARRHOEA` vs. `diarrhea`.
3. **Canonical Oncology Terminology:** Ensure tumor outcomes use valid MedDRA PTs.
   - *Example:* `PANCREATIC CARCINOMA` / `PANCREATIC NEOPLASM` vs colloquial `pancreatic_cancer` (`DECISIONS.md §22`).

---

## 5. Dual-Metric Evaluation Framework

PharmaGuard reports both **Strict** and **Lenient** metrics as first-class outputs. Neither metric alone captures the full operational performance (`DECISIONS.md §14`, `PROGRESS.md`).

```
                    ┌─────────────────────────┐
                    │     Evaluation Mode     │
                    └────────────┬────────────┘
               ┌─────────────────┴─────────────────┐
               ▼                                   ▼
      ┌─────────────────┐                 ┌─────────────────┐
      │  Strict Metric  │                 │ Lenient Metric  │
      │ (High Precision)│                 │  (High Safety)  │
      └────────┬────────┘                 └────────┬────────┘
               │                                   │
      Positive: ESCALATE only             Positive: ESCALATE + MONITOR
      Negative: MONITOR + DO_NOT_ESCALATE Negative: DO_NOT_ESCALATE
```

### Purpose of Dual Metrics:
- **Strict Metrics (Point: Precision=1.000, Recall=0.857, F1=0.923):** Measures crisp, unhesitating escalation. Captures genuine pharmacological uncertainty (e.g. `montelukast::suicidal_ideation` scoring `MONITOR` due to `plausibility=LOW`, recorded strictly as $\text{FN}=1$).
- **Lenient Metrics (Point: Precision=0.875, Recall=1.000, F1=0.933):** Measures signal detection safety. Confirms that no real safety signal was dismissed ($\text{FN}=0$, $\text{Recall}=1.000$).
- **Over-Caution Rate (OCR):** Percentage of negative controls triaged as `MONITOR` (PharmaGuard = $12.5\%$ [1/8], Single-Shot Baseline = $25.0\%$ [2/8]).

### Statistical Uncertainty & Confidence Interval Rules:
1. **Wilson Score 95% Intervals:** Primary measure of small-sample binomial uncertainty (e.g. Strict Recall Wilson: `[0.487, 0.974]`).
2. **Non-Parametric Bootstrap ($B=1000, \text{seed}=42$):** Reports empirical distribution.
3. **Boundary Artifact Warning:** At small $n$ with zero false positives ($\text{FP}=0$), bootstrap resampling on precision/specificity yields `[1.000, 1.000]`. This is a mathematical boundary artifact of resampling zero-count empirical sets, **NOT** evidence of proven perfection (`PROGRESS.md`, `DECISIONS.md §16`). Wilson score intervals must always accompany bootstrap reports.

---

## 6. Anti-Leakage & Memorization Probe Discipline

When auditing or evaluating LLM-based plausibility or triage agents:

### ⚠️ The "Perfect Score" Red Flag (`DECISIONS.md §19`)
- Running in `force_agent` mode (LLM deriving plausibility without lookup tables) produced a superficially attractive $1.000$ Strict Recall ($15/15$).
- **Failure Mode:** Investigation proved the LLM achieved this by retrieving leaked regulatory knowledge (citing FDA Boxed Warnings and clinical trial names in its rationale) rather than performing biochemical reasoning.
- **Rule:** A $1.000$ Strict Recall achieved via regulatory leakage is an architectural failure, not an improvement. The production configuration remains `lookup_first`.
- **Epistemic Boundary:** Agent-derived plausibility must always be characterized as **grounded pharmacological knowledge retrieval and pathway synthesis**, never as de novo algorithmic reasoning from first principles (`DECISIONS.md §17`).
