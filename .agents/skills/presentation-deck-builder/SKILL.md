---
name: presentation-deck-builder
description: >-
  Slide structure guidelines, 16:9 widescreen layout discipline, and visual
  pacing for PharmaGuard mid-semester and capstone defense presentations.
---

# Presentation Deck Builder — PharmaGuard Defense Scaffold

> ⚠️ **UNVERIFIED DRAFT SCAFFOLD:** This skill is a presentation design scaffold written before defense slide drafting has commenced. It outlines recommended slide pacing, widescreen layout discipline, and narrative structure for academic defenses.

---

## 1. Purpose & Audience

This skill guides the construction of academic slide decks (e.g. generated via `python-pptx` or formatted for PowerPoint/Keynote) for the **PharmaGuard 7th-Semester Capstone Defense** before supervisor **Dr. Nikhilanand Arya** (IIIT Allahabad).

---

## 2. Core Visual & Layout Discipline

1. **Aspect Ratio:** Strictly **16:9 widescreen** (`Inches(13.333)` $\times$ `Inches(7.5)`).
2. **Type-Led Hierarchy:**
   - Slide Title: 22–24pt Bold (Dark Slate `#0F172A`).
   - Category / Sub-header: 12–14pt Medium (Slate `#64748B`).
   - Body & Metric Text: 13–15pt Regular / 28–36pt Hero Numbers.
   - Monospace for Data / Terms: JetBrains Mono / Consolas (`#334155`).
3. **Restrained Status Palette:**
   - Primary Accent: Navy / Deep Slate (`#1E293B` / `#2563EB`).
   - Escalated Signal: Forest Green (`#166534`).
   - Monitored / Neutral: Slate Gray (`#475569`). *Never color MONITOR as red/failure.*
   - Inactive / Background: Light Gray (`#F8FAFC`, `#E2E8F0`).
4. **Density & White Space:**
   - Avoid walls of bullet points. Use 2-column or 3-column card layouts with subtle hairlines.
   - Highlight one core finding or metric per slide.

---

## 3. Recommended 10–12 Slide Defense Narrative

| Slide # | Slide Title | Core Message / Content |
| :---: | :--- | :--- |
| **1** | Title Slide | Project Title, Student Info (Krishna Sikheriya, IIT2023139), Supervisor (Dr. Nikhilanand Arya), Department of IT. |
| **2** | The Problem | Pharmacovigilance triage bottleneck; why pure LLMs fail (hallucinations, uncalibrated self-confidence, historical confusion). |
| **3** | PharmaGuard Architecture | 3 data streams (FAERS, ChEMBL, PubMed), deterministic confidence formula, and the hard `NO_SIGNAL` safety gate. |
| **4** | Benchmark Methodology | 15 ground-truth pairs across 3 classes: Confirmed Positives ($n=7$), Genuine Negative Controls ($n=5$), Zero-Report Controls ($n=3$). |
| **5** | Primary Benchmark Results | Strict Recall: **0.857** (6/7), Lenient Recall: **1.000** (7/7), Over-Caution Rate: **12.5%** vs. Baseline 25.0%. |
| **6** | Dual-Metric Framework | Why reporting Strict + Lenient together is scientifically necessary; explaining the two documented `MONITOR` cases. |
| **7** | Case Study 1: Montelukast | Epidemiological signal (Grade A / Boxed Warning) vs. mechanistic uncertainty (`plausibility=LOW`); why `MONITOR` is correct. |
| **8** | Case Study 2: Metformin | Confounded FAERS polypharmacy signal (~9,340 reports) de-weighted by low plausibility and Grade C PubMed evidence. |
| **9** | Baseline Comparison | Side-by-side comparison with Single-Shot LLM; Liraglutide case study showing tool-grounded `DO_NOT_ESCALATE`. |
| **10** | Epistemic Findings & Leakage | The ablation study warning: why 1.000 strict recall in `force_agent` is a leakage failure mode, not a success. |
| **11** | Live Dashboard Demo | Highlighting the Streamlit presentation interface (zero-live-API constraint). |
| **12** | Future Scope & Conclusion | MedDRA canonicalization, anti-leakage guards, multi-database expansion, Q&A. |
