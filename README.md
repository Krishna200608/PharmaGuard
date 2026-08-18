# PharmaGuard 🛡️

**Pharmacovigilance Signal Triage Orchestrator**  
*7th-Semester B.Tech IT Capstone Project · IIIT Allahabad*  
**Author:** Krishna Sikheriya (IIT2023139) · **Supervisor:** Dr. Nikhilanand Arya

---

## What is PharmaGuard?

PharmaGuard is an automated triage system designed to evaluate potential drug–adverse event safety signals. Given a drug and an adverse event, it synthesizes evidence from three independent public data sources:

1. **openFDA / FAERS** — Statistical disproportionality ($2 \times 2$ contingency table, PRR, ROR, $95\%$ lower CI).
2. **ChEMBL** — Pharmacological mechanism-of-action lookup and biological plausibility assessment.
3. **PubMed** — Literature evidence retrieval and automated grade extraction (Grade A/B/C).

The system combines these signals using a deterministic formula to output a triaged decision: **`ESCALATE`**, **`MONITOR`**, or **`DO_NOT_ESCALATE`**. The central thesis of the project is that **tool-grounded evidence synthesis** prevents the ungrounded clinical hallucinations and historical regulatory confusions inherent to single-shot LLMs.

---

## Where to Go Next (Documentation Roadmap)

To explore the project in depth, refer to the following canonical documents:

- 📖 **[UNDERSTAND.md](docs/context/UNDERSTAND.md)** — **Start here.** A plain-language, conceptual walkthrough of how the pipeline works, the strict/lenient evaluation framework, and why imperfect results (`6/7` strict recall) reflect honest pharmacovigilance reasoning.
- 📋 **[DECISIONS.md](docs/context/DECISIONS.md)** — Complete chronological record of all 22 architectural decisions, empirical audits (MedDRA Preferred Term canonicalization, memorization probes), and research findings.
- 📊 **[PROGRESS.md](docs/context/PROGRESS.md)** — Sprint-by-sprint changelog, verified benchmark metrics with exact Wilson and Bootstrap 95% confidence intervals, and step-by-step reproduction steps.
- 🏛️ **[ARCHITECTURE.md](docs/context/ARCHITECTURE.md)** — Technical component specifications, deterministic scoring formulas, and data schemas.

---

## Quickstart & Evaluation

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/Krishna200608/PharmaGuard.git
cd PharmaGuard

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows (use `source .venv/bin/activate` on Linux/macOS)

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (copy and add API keys)
cp .env.example .env
```

### 2. Run the Benchmark Pipeline

```bash
# Run full 15-pair evaluation against openFDA, ChEMBL, and PubMed
python scripts/run_eval.py

# Compute Strict and Lenient evaluation metrics with 95% CIs
python scripts/evaluator.py --outputs-dir outputs --title "PharmaGuard Final"

# Run single-shot baseline for comparison
python scripts/baseline.py
```

### 3. Launch the Evaluation Dashboard

The repository includes a standalone presentation and evaluation dashboard built with Streamlit and Plotly. It reads exclusively from pre-committed local run reports with **zero live API calls at runtime**:

```bash
streamlit run scripts/dashboard.py
```

---

## Project Status

- **Sprint 3 (Completed & Verified):** 15-pair benchmark locked with verified reproducibility (`6/7` Strict Recall, `7/7` Lenient Recall, `12.5%` Over-Caution Rate, `FP = 0`).
- **Mid-Semester Milestone:** Dashboard presentation and capstone defense preparation.
