---
name: academic-paper-writer
description: >-
  Structural patterns, formatting conventions, and methodological write-up
  standards for PharmaGuard capstone and conference paper drafting.
---

# Academic Paper Writer — PharmaGuard Research Writing Scaffold

> ⚠️ **UNVERIFIED DRAFT SCAFFOLD:** This skill is a structural scaffold written before formal manuscript drafting has commenced. It outlines established formatting and reporting conventions and should be updated and refined once active paper writing begins.

---

## 1. Scope & Target Venues

This skill guides the preparation of academic manuscripts and capstone reports for **PharmaGuard**, targeting biomedical informatics, AI in healthcare, and pharmacovigilance venues (e.g., IEEE BIBM, ACM CHIL, JAMIA, or undergraduate capstone symposiums).

---

## 2. Recommended Manuscript Structure

1. **Title & Abstract:**
   - Structured abstract: Background, Objective, Methods, Results (Strict/Lenient metrics with 95% CIs), Conclusion.
   - Explicitly highlight tool-grounded triage vs. parametric memory recall.
2. **Introduction:**
   - Postmarketing surveillance bottlenecks and FAERS spontaneous reporting scale.
   - Limitation of pure LLMs in clinical safety: hallucinated safety signals, historical regulatory confusion, uncalibrated confidence.
   - Core research question: Can a deterministic, multi-source grounded agent improve pharmacovigilance triage precision over single-shot models?
3. **Related Work:**
   - Pharmacovigilance signal detection algorithms (PRR, ROR, BCPNN, MGPS).
   - LLMs in biomedicine & clinical NLP (retrieval-augmented generation, tool-use agents).
   - Memorization and epistemic leakage in biomedical foundation models.
4. **Methods & System Architecture:**
   - Formal definition of the 3 data streams (openFDA FAERS, ChEMBL MoA, PubMed E-utilities).
   - Deterministic scoring formulation and the hard `NO_SIGNAL` safety gate.
   - Ground truth curation protocol ($n=15$: Confirmed Positives, Genuine Negative Controls, Zero-Report Edge Cases).
   - Strict vs. Lenient evaluation framework definition.
5. **Experimental Results & Benchmark:**
   - Main benchmark table comparing PharmaGuard vs. Single-Shot LLM Baseline.
   - Reporting both Wilson 95% CIs and Bootstrap ($B=1000$) distributions.
   - Boundary artifact disclosure for $0/N$ zero-error metrics.
   - Over-Caution Rate (OCR) comparison on genuine negative controls.
6. **Case Studies & Error Analysis:**
   - `montelukast::suicidal_ideation`: Mechanistic uncertainty dampening confidence below escalation threshold.
   - `metformin::hypoglycaemia`: Confounded polypharmacy signal handling via low plausibility and Grade C evidence.
   - `liraglutide::pancreatic_cancer`: Historical regulatory concern vs. tool-grounded `NO_SIGNAL` resolution.
7. **Discussion & Epistemic Boundaries:**
   - Mechanistic reasoning vs. parametric retrieval (the memorization probe findings, `DECISIONS.md §17`).
   - The danger of "perfect" metric scores derived from regulatory leakage (`DECISIONS.md §19`).
8. **Limitations & Future Work:**
   - Benchmark sample size ($n=15$) and heuristic escalation thresholds.
   - MedDRA ontology canonicalization (LLT to PT mapping).
   - Future integration of global databases (EudraVigilance, WHO VigiBase).
9. **Conclusion:**
   - Summary of key contributions and reproducible benchmark verification.

---

## 3. Mathematical & Empirical Reporting Standards

- **Metric Tables:** Always report Strict and Lenient metrics side-by-side. Never report single aggregate numbers.
- **Equations:** State the exact linear confidence combination:
  $$\text{Confidence} = 0.40 \cdot S_{\text{FAERS}} + 0.40 \cdot S_{\text{PubMed}} + 0.20 \cdot S_{\text{Plausibility}}$$
- **Confidence Intervals:** Format as `Point [95% CI Bootstrap: L - U / Wilson: L - U]`.
- **Verbatim Rationale Quotes:** When citing agent rationales or baseline outputs, quote verbatim from committed `outputs/` reports.
