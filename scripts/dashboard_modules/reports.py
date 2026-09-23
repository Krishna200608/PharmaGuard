"""
Clinical Report Generator
=========================
Generates standardized, regulatory-compliant Pharmacovigilance Safety Briefing
dossiers in Markdown and structured text from PharmaGuard TriageReports.

Owner: Krishna Sikheriya (IIT2023139)
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pharmaguard.agent.output_schema import TriageReport, EscalationDecision


def generate_clinical_dossier_markdown(report: TriageReport) -> str:
    """
    Generate an exhaustive, publication-grade Clinical Safety Briefing & Triage Dossier
    suitable for regulatory pharmacovigilance review, clinical safety boards, or paper exhibits.
    """
    drug_name = report.drug.title()
    event_name = report.event.title()
    decision_val = report.triage.escalation.value
    confidence_val = report.triage.confidence
    run_id = report.run_id
    timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Verification hash of key fields for provenance
    audit_payload = f"{drug_name}|{event_name}|{decision_val}|{confidence_val:.4f}|{run_id}"
    audit_hash = hashlib.sha256(audit_payload.encode("utf-8")).hexdigest()[:16].upper()

    # Actionable guidance text based on tier
    if decision_val == "ESCALATE":
        action_header = "🚨 HIGH-PRIORITY REGULATORY ESCALATION"
        action_desc = (
            "This signal exceeds pre-registered disproportionality and multimodal confidence thresholds. "
            "Recommended immediate action: convene internal Pharmacovigilance Risk Assessment Board, "
            "initiate formal signal validation dossier, and evaluate necessity of Dear Healthcare Provider (DHCP) communication."
        )
    elif decision_val == "MONITOR":
        action_header = "👁️ ACTIVE PHARMACOVIGILANCE WATCHLIST SURVEILLANCE"
        action_desc = (
            "This signal exhibits notable disproportionality or clinical literature evidence but lacks sufficient "
            "receptor-level plausibility or statistical conviction for urgent escalation. "
            "Recommended action: retain on quarterly active surveillance watchlist; request updated FAERS cut in next quarterly reporting cycle."
        )
    else:  # DO_NOT_ESCALATE
        action_header = "✅ BENIGN / NO SAFETY ESCALATION REQUIRED"
        action_desc = (
            "Empirical gating (Gate 1) or low composite confidence demonstrates that this association is either "
            "unsubstantiated by real-world spontaneous reports, or explained by background reporting noise. "
            "Recommended action: archive signal review; no regulatory label intervention warranted."
        )

    # Signal stats extraction
    prr_str = f"{report.signal_stats.prr:.3f}" if report.signal_stats.prr is not None else "N/A"
    prr_ci_str = f"{report.signal_stats.prr_lower_ci:.3f}" if report.signal_stats.prr_lower_ci is not None else "N/A"
    ror_str = f"{report.signal_stats.ror:.3f}" if report.signal_stats.ror is not None else "N/A"
    ror_ci_str = f"{report.signal_stats.ror_lower_ci:.3f}" if report.signal_stats.ror_lower_ci is not None else "N/A"
    n_reports = f"{report.signal_stats.report_count:,}"
    sig_label = report.triage.signal_strength.value
    ci_down = "Yes (Downgraded due to Lower CI < 1.0/2.0)" if report.signal_stats.ci_downgraded else "No"

    # Mechanism extraction
    chembl_id = report.mechanism.chembl_id or "Unannotated"
    moa_text = report.mechanism.moa or "Mechanism not annotated in ChEMBL"
    plaus_level = report.mechanism.biological_plausibility.value
    plaus_score = f"{report.mechanism.plausibility_score:.2f}"
    plaus_src = report.mechanism.plausibility_source.value
    plaus_rationale = report.mechanism.plausibility_rationale or "None provided."

    # Literature extraction
    ev_grade = report.triage.evidence_grade.value
    abs_screened = report.literature.abstracts_retrieved
    pmids = report.literature.supporting_pmids or []
    pmid_str = ", ".join([f"[PMID {p}](https://pubmed.ncbi.nlm.nih.gov/{p}/)" for p in pmids]) if pmids else "None retrieved"
    lit_summary = report.literature.evidence_summary or "No clinical literature evidence summarized."

    # Indication concordance extraction
    ic = report.indication_concordance
    if ic and getattr(ic, "concordant", False):
        ic_status = "⚠️ CONCORDANT (Potential Channeling Bias / Confounding by Indication)"
        ic_cat = getattr(ic, "overlap_category", "Indication Overlap")
        ic_rat = getattr(ic, "clinical_rationale", "Adverse event category overlaps with primary treated disease domain.")
        ic_disc = f"{getattr(ic, 'discount_factor', 0.85):.2f}x (Applied strictly as informational flag)"
    else:
        ic_status = "✅ DISCORDANT / CLEAR (Non-Confounded Safety Signal)"
        ic_cat = "None"
        ic_rat = "Adverse event does not overlap with the drug's approved indication domain."
        ic_disc = "N/A (Scoring-Inert Isolation Wall preserved)"

    # Agreement
    agreement = getattr(report, "cross_source_agreement", "N/A")

    # Build Markdown Document
    doc = f"""# 🛡️ PharmaGuard — Clinical Safety Briefing & Triage Dossier
**Autonomous Multi-Source Pharmacovigilance Signal Surveillance**

---

### Executive Dossier Metadata
- **Candidate Drug–Event Pair:** **{drug_name}** $\\\\longleftrightarrow$ **{event_name}**
- **Surveillance Run ID:** `{run_id}`
- **Dossier Generation Timestamp:** `{timestamp_str}`
- **Cryptographic Audit Signature:** `SHA256:{audit_hash}`
- **System Version:** PharmaGuard Orchestrator v1.0 (FixedPipeline / ReAct Engine)

---

## 1. Executive Triage Recommendation

| Parameter | Clinical Finding | Operational Definition |
|---|---|---|
| **Triage Verdict** | **`{decision_val}`** | {action_header} |
| **Calibrated Confidence** | **`{confidence_val:.4f}`** | Linear multi-source evidence fusion ($[0.0000, 1.0000]$) |
| **Evidence Concordance** | **`{agreement}`** | Cross-source agreement heuristic ($\\\\max \\\\ge 0.66 \\\\land \\\\min \\\\le 0.33$) |
| **Channeling Bias Status** | **{ic_status.split(' ')[1]}** | WHO ATC disease-context indication overlap |

> **Operational Directive:**  
> {action_desc}

---

## 2. Quantitative Disproportionality Statistics (openFDA FAERS)

The quantitative signal detection engine evaluates spontaneous adverse drug reaction co-occurrences against background reporting rates across all FDA FAERS submissions using classical $2 \\times 2$ contingency table analysis:

| Statistical Metric | Observed Value | Clinical Reference Benchmark |
|---|:---:|---|
| **Spontaneous Report Count ($a$)** | **{n_reports}** | Threshold: $\\\\ge 3$ reports required for signal consideration |
| **Proportional Reporting Ratio (PRR)** | **{prr_str}** | Evans et al. (2001) criterion: $\\\\text{{PRR}} \\\\ge 2.0$ |
| **PRR 95% Lower Confidence Interval** | **{prr_ci_str}** | Woolf log-scale standard error: Lower Bound $> 1.0$ required |
| **Reporting Odds Ratio (ROR)** | **{ror_str}** | van Puijenbroek et al. (2002) disproportionality odds |
| **ROR 95% Lower Confidence Interval** | **{ror_ci_str}** | Asymptotic logit confidence floor |
| **Assigned Signal Strength Tier** | **`{sig_label}`** | Quantitative FAERS weight contribution: $0.40 \\\\times S_{{\\\\text{{FAERS}}}}$ |
| **Woolf CI Downgrade Triggered** | **{ci_down}** | Gating safety check against small-sample variance instability |

---

## 3. Receptor-Level Mechanism of Action (EMBL-EBI ChEMBL)

Biological plausibility assesses whether the drug's molecular pharmacology and target receptor binding provide a mechanistic explanation for the adverse event:

- **Target Identifier:** `{chembl_id}`
- **Annotated Mechanism of Action:** {moa_text}
- **Biological Plausibility Rating:** **`{plaus_level}`** (Sub-score: `{plaus_score}`)
- **Provenance Source:** `{plaus_src}`
- **Pharmacological Assessment Rationale:**
  > {plaus_rationale}

---

## 4. Peer-Reviewed Clinical Literature Evidence (NCBI PubMed)

Literature evidence is retrieved live via NCBI Entrez E-utilities and graded against our standardized epidemiological clinical rubric (v1.0):

- **Epidemiological Evidence Tier:** **`Grade {ev_grade}`**
- **Clinical Abstracts Screened:** **{abs_screened}**
- **Supporting Peer-Reviewed Citations:** {pmid_str}
- **Evidence Synthesis Summary:**
  > {lit_summary}

---

## 5. Disease Context & Indication Concordance (WHO ATC)

Evaluates whether the reported adverse event overlaps with the underlying disease the medication was prescribed to treat (confounding by indication or channeling bias):

- **Concordance Determination:** {ic_status}
- **Clinical Overlap Category:** {ic_cat}
- **Discount Factor Adjustment:** {ic_disc}
- **Pharmacoepidemiologic Context Rationale:**
  > {ic_rat}

*Note on Scoring-Inert Isolation Wall:* In accordance with pre-registered architectural decisions (`DECISIONS.md §35`), indication concordance serves as high-visibility provenance for clinical reviewers, preserving the mathematical determinism of core scoring without overfitting benchmark thresholds.

---

## 6. Audit Provenance & Scoring Decomposition

### Closed-Form Confidence Calculation:
$$\\\\text{{Confidence}} = 0.40 \\\\cdot S_{{\\\\text{{FAERS}}}} + 0.40 \\\\cdot S_{{\\\\text{{PubMed}}}} + 0.20 \\\\cdot S_{{\\\\text{{ChEMBL}}}}$$

$$\\\\text{{Confidence}} = 0.40 \\\\cdot ({report.signal_stats.prr_score:.2f}) + 0.40 \\\\cdot ({report.triage.evidence_grade.value}) + 0.20 \\\\cdot ({report.mechanism.plausibility_score:.2f}) = \\\\mathbf{{{confidence_val:.4f}}}$$

### Gate Execution Trace:
"""
    # Append reasoning trace
    for trace_item in report.triage.agent_reasoning_trace:
        doc += f"- `{trace_item}`\n"

    doc += f"""
---
*PharmaGuard Pharmacovigilance Signal Triage Orchestrator &middot; Group 07, IIIT Allahabad &middot; Academic Defense Exhibit*  
*Report Cryptographic Signature: `SHA256:{audit_hash}`*
"""
    return doc
