"""
Clinical Report Generator
=========================
Generates standardized, regulatory-compliant Pharmacovigilance Safety Briefing
dossiers in Markdown and structured text from PharmaGuard TriageReports.
Adheres to ICH E2C(R2), CIOMS VIII, and Evans et al. (2001) signal triage standards.

Owner: Krishna Sikheriya (IIT2023139)
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pharmaguard.agent.output_schema import TriageReport


_GRADE_SCORE_MAP = {"A": 1.0, "B": 0.5, "C": 0.0}


def generate_clinical_dossier_markdown(report: TriageReport | dict) -> str:
    """
    Generate an exhaustive, publication-grade Clinical Safety Briefing & Triage Dossier
    suitable for regulatory pharmacovigilance review, clinical safety boards, or paper exhibits.
    Accepts either a validated TriageReport model or a raw serialized report dict.
    Strictly devoid of emojis; uses standard regulatory badges and formal clinical typography.
    """
    if isinstance(report, dict):
        report = TriageReport.model_validate(report)

    drug_name = report.drug.title()
    event_name = report.event.title()
    decision_val = report.triage.escalation.value
    confidence_val = report.triage.confidence
    run_id = report.run_id
    timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Numeric sub-scores for mathematical decomposition
    prr_score_val = report.signal_stats.prr_score if report.signal_stats.prr_score is not None else 0.0
    grade_score_val = _GRADE_SCORE_MAP.get(report.triage.evidence_grade.value, 0.0)
    plaus_score_val = report.mechanism.plausibility_score if report.mechanism.plausibility_score is not None else 0.0

    # Verification hash of key fields for provenance
    audit_payload = f"{drug_name}|{event_name}|{decision_val}|{confidence_val:.4f}|{run_id}"
    audit_hash = hashlib.sha256(audit_payload.encode("utf-8")).hexdigest()[:16].upper()

    # Actionable guidance text based on tier (Formal regulatory language, NO emojis)
    if decision_val == "ESCALATE":
        action_header = "[ESCALATE] - PRIORITY 1: REGULATORY SIGNAL ESCALATION"
        urgency_label = "PRIORITY 1: URGENT REGULATORY ACTION"
        action_desc = (
            "This safety signal exceeds pre-registered disproportionality and multimodal confidence thresholds. "
            "Recommended immediate action: convene internal Pharmacovigilance Risk Assessment Committee (PRAC), "
            "initiate formal signal validation dossier, review cumulative postmarketing safety database, and evaluate "
            "necessity of Dear Healthcare Provider (DHCP) communication and product label updates (SmPC Section 4.4/4.8)."
        )
    elif decision_val == "MONITOR":
        action_header = "[MONITOR] - PRIORITY 2: ACTIVE WATCHLIST SURVEILLANCE"
        urgency_label = "PRIORITY 2: ACTIVE SURVEILLANCE"
        action_desc = (
            "This safety signal exhibits notable disproportionality or clinical literature evidence but lacks sufficient "
            "receptor-level plausibility or statistical conviction for immediate escalation. "
            "Recommended action: place on active pharmacovigilance surveillance watchlist; request updated cumulative "
            "FAERS extract in next quarterly reporting cycle, and monitor targeted electronic health record (EHR) registries."
        )
    else:  # DO_NOT_ESCALATE
        action_header = "[DO_NOT_ESCALATE] - ROUTINE: NO SAFETY ESCALATION REQUIRED"
        urgency_label = "ROUTINE: NO SAFETY ESCALATION"
        action_desc = (
            "Empirical gating (Gate 1 floor) or composite confidence confirms that this association is either "
            "unsubstantiated by real-world spontaneous reports, or consistent with background reporting rates. "
            "Recommended action: archive signal evaluation; continue routine passive surveillance without labeling intervention."
        )

    # Signal stats extraction
    prr = report.signal_stats.prr
    prr_lower_ci = report.signal_stats.prr_lower_ci
    ror = report.signal_stats.ror
    ror_lower_ci = report.signal_stats.ror_lower_ci
    report_count = report.signal_stats.report_count

    prr_str = f"{prr:.3f}" if prr is not None else "N/A"
    prr_ci_str = f"{prr_lower_ci:.3f}" if prr_lower_ci is not None else "N/A"
    ror_str = f"{ror:.3f}" if ror is not None else "N/A"
    ror_ci_str = f"{ror_lower_ci:.3f}" if ror_lower_ci is not None else "N/A"
    n_reports = f"{report_count:,}"
    sig_label = report.triage.signal_strength.value
    ci_down = "Triggered (Downgraded due to Woolf Lower CI < 1.0/2.0)" if report.signal_stats.ci_downgraded else "Not Triggered (Stable Variance)"

    # Evans et al. 2001 Criteria Check: PRR >= 2.0, N >= 3, Lower CI > 1.0
    evans_passed = (
        prr is not None
        and prr >= 2.0
        and prr_lower_ci is not None
        and prr_lower_ci > 1.0
        and report_count >= 3
    )
    evans_status = "[COMPLIANT] Meets Evans Criteria (PRR >= 2.0, N >= 3, Lower CI > 1.0)" if evans_passed else "[NON-COMPLIANT] Does Not Meet Evans Criteria"

    # Mechanism extraction
    chembl_id = report.mechanism.chembl_id or "Unannotated"
    moa_text = report.mechanism.moa or "Mechanism not annotated in ChEMBL"
    plaus_level = report.mechanism.biological_plausibility.value
    plaus_score = f"{report.mechanism.plausibility_score:.2f}"
    plaus_src_raw = report.mechanism.plausibility_source.value
    if plaus_src_raw == "human_curated":
        plaus_src_desc = "Human-Curated Gold Standard Reference (Static Rubric)"
    elif plaus_src_raw == "agent_derived":
        plaus_src_desc = "Autonomous Agent Biochemical Inference (ChEMBL Target MoA)"
    else:
        plaus_src_desc = plaus_src_raw.replace("_", " ").title()

    plaus_rationale = report.mechanism.plausibility_rationale or "No pharmacological rationale provided."

    # Literature extraction
    ev_grade = report.triage.evidence_grade.value
    abs_screened = report.literature.abstracts_retrieved
    pmids = report.literature.supporting_pmids or []
    pmid_str = ", ".join([f"[PMID {p}](https://pubmed.ncbi.nlm.nih.gov/{p}/)" for p in pmids]) if pmids else "None retrieved"
    lit_summary = report.literature.evidence_summary or "No clinical literature evidence summarized."

    # Indication concordance extraction
    ic = report.indication_concordance
    if ic and getattr(ic, "concordant", False):
        ic_status = "[CONCORDANT] Identified Potential Channeling Bias / Confounding by Indication"
        ic_bias_flag = "CONCORDANT (Potential Confounding Present)"
        ic_cat = getattr(ic, "overlap_category", "Indication Overlap")
        ic_rat = getattr(ic, "clinical_rationale", getattr(ic, "rationale", "Adverse event category overlaps with primary treated disease domain."))
        ic_disc = f"{getattr(ic, 'discount_factor', 0.85):.2f}x (Reported strictly as informational surveillance flag)"
    else:
        ic_status = "[DISCORDANT] Non-Confounded Drug-Safety Association"
        ic_bias_flag = "DISCORDANT (Unconfounded Signal)"
        ic_cat = "None (Independent Pathological Phenomenon)"
        ic_rat = "Reported adverse event does not overlap with the drug's primary therapeutic indication domain."
        ic_disc = "N/A (Scoring-Inert Isolation Wall preserved)"

    # Agreement
    agreement = getattr(report, "cross_source_agreement", "N/A")

    # Build Markdown Document with clean, publication-grade clinical layout
    doc = f"""# PharmaGuard Clinical Safety Briefing & Signal Triage Dossier
**Autonomous Multi-Stream Pharmacovigilance Surveillance | ICH E2C(R2) & CIOMS VIII Standard**

---

### Document Control & Surveillance Metadata

| Metadata Field | Parameter Value | Technical Context |
|---|---|---|
| **Candidate Drug Substance** | **{drug_name}** | Primary active pharmaceutical ingredient |
| **Adverse Drug Reaction (ADR)** | **{event_name}** | MedDRA Preferred Term (PT) |
| **Surveillance Run ID** | `{run_id}` | Deterministic pipeline execution handle |
| **Generation Timestamp** | `{timestamp_str}` | ISO 8601 UTC timestamp |
| **Cryptographic Provenance** | `SHA256:{audit_hash}` | Cryptographic audit integrity checksum |
| **System Orchestration** | PharmaGuard FixedPipeline Engine v1.0 | Tri-Stream Multi-Source Deterministic Gating |

---

## 1. Executive Regulatory Triage Recommendation

| Evaluation Metric | Clinical Finding | Operational Definition |
|---|---|---|
| **Triage Verdict** | **`{decision_val}`** | {action_header} |
| **Urgency Tier** | **{urgency_label}** | Regulatory response prioritization |
| **Calibrated Confidence** | **`{confidence_val:.4f}`** | Linear multi-source evidence fusion ($[0.0000, 1.0000]$) |
| **Cross-Stream Agreement** | **`{agreement}`** | Multi-modal concordance metric ($\\\\max \\\\ge 0.66 \\\\land \\\\min \\\\le 0.33$) |
| **Channeling Bias Status** | **{ic_bias_flag}** | WHO ATC disease-context indication overlap audit |

> **Operational Regulatory Directive:**  
> {action_desc}

---

## 2. Quantitative Disproportionality Statistics (openFDA FAERS)

Quantitative signal disproportionality evaluates spontaneous adverse event reporting rates against background submission volumes across all FDA FAERS records using classical $2 \\times 2$ contingency table analysis:

| Statistical Parameter | Observed Value | Regulatory / Reference Standard | Status / Compliance |
|---|:---:|---|:---:|
| **Spontaneous Report Count ($a$)** | **{n_reports}** | Signal Floor: $a \\\\ge 3$ reports | {'Meets Floor' if report_count >= 3 else 'Sub-Threshold'} |
| **Proportional Reporting Ratio (PRR)** | **{prr_str}** | Evans et al. (2001) threshold: $\\\\text{{PRR}} \\\\ge 2.0$ | {'Signal Detected' if prr is not None and prr >= 2.0 else 'Below Threshold'} |
| **PRR 95% Lower Confidence Bound** | **{prr_ci_str}** | Woolf log-scale standard error: Lower Bound $> 1.0$ | {'Significant' if prr_lower_ci is not None and prr_lower_ci > 1.0 else 'Inconclusive'} |
| **Reporting Odds Ratio (ROR)** | **{ror_str}** | van Puijenbroek et al. (2002) disproportionality odds | - |
| **ROR 95% Lower Confidence Bound** | **{ror_ci_str}** | Wald asymptotic logit confidence limit | - |
| **Assigned Signal Strength Tier** | **`{sig_label}`** | Quantitative weight contribution: $0.40 \\\\times S_{{\\\\text{{FAERS}}}}$ | Sub-Score: `{prr_score_val:.2f}` |
| **Woolf CI Downgrade Triggered** | **{ci_down}** | Gating safety check against small-sample variance instability | - |
| **Evans (2001) Triad Status** | **{evans_status}** | Joint criteria: $a \\\\ge 3 \\\\land \\\\text{{PRR}} \\\\ge 2.0 \\\\land \\\\text{{CI}}_{{\\\\text{{lower}}}} > 1.0$ | - |

---

## 3. Receptor-Level Mechanism of Action (EMBL-EBI ChEMBL)

Biological plausibility assesses whether the drug's molecular pharmacology and target receptor engagement provide a valid mechanistic pathway for the adverse event:

- **Target Identifier:** `{chembl_id}`
- **Annotated Mechanism of Action:** {moa_text}
- **Biological Plausibility Rating:** **`[{plaus_level}]`** (Normalized Sub-Score: $S_{{\\\\text{{ChEMBL}}}} = {plaus_score}$)
- **Provenance Source:** {plaus_src_desc}
- **Pharmacological Assessment Rationale:**
  > {plaus_rationale}

---

## 4. Peer-Reviewed Clinical Literature Evidence (NCBI PubMed)

Literature evidence is retrieved live via NCBI Entrez E-utilities and graded against our standardized epidemiological clinical rubric (v1.0):

- **Epidemiological Evidence Tier:** **`[Grade {ev_grade}]`** (Normalized Sub-Score: $S_{{\\\\text{{PubMed}}}} = {grade_score_val:.2f}$)
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

$$\\\\text{{Confidence}} = 0.40 \\\\cdot ({prr_score_val:.2f}) + 0.40 \\\\cdot ({grade_score_val:.2f}) + 0.20 \\\\cdot ({plaus_score_val:.2f}) = \\\\mathbf{{{confidence_val:.4f}}}$$

### Component Sub-Score Breakdown:

| Evidence Stream | Metric Source | Primary Finding | Normalized Sub-Score | Weight | Weighted Contribution |
|---|---|---|:---:|:---:|:---:|
| **Spontaneous FAERS** | openFDA API | `{sig_label}` | `{prr_score_val:.2f}` | 40% | `{(0.40 * prr_score_val):.4f}` |
| **Clinical Literature** | NCBI PubMed | `Grade {ev_grade}` | `{grade_score_val:.2f}` | 40% | `{(0.40 * grade_score_val):.4f}` |
| **Receptor Plausibility** | EMBL-EBI ChEMBL | `{plaus_level}` | `{plaus_score_val:.2f}` | 20% | `{(0.20 * plaus_score_val):.4f}` |
| **Composite Multi-Source Total** | **Linear Evidence Fusion** | - | - | **100%** | **`{confidence_val:.4f}`** |

### Gate Execution Trace:
"""
    # Append reasoning trace
    for trace_item in report.triage.agent_reasoning_trace:
        doc += f"- `{trace_item}`\n"

    doc += f"""
---

### Regulatory Reviewer Sign-Off & Verification Block

```text
[ ] SIGNAL VALIDATED: Proceed to full Benefit-Risk Evaluation (BRE)
[ ] REFINE SURVEILLANCE: Retain on Active Watchlist with Quarterly Refresh
[ ] SIGNAL REFUTED: Spurious association; close surveillance docket

Lead Safety Reviewer: ___________________________  Date: ______________
Medical Monitor:      ___________________________  Date: ______________
Quality Assurance:    ___________________________  Audit SHA256: {audit_hash}
```

*PharmaGuard Pharmacovigilance Signal Triage Orchestrator | Group 07, IIIT Allahabad | Academic Defense Exhibit*  
*Report Cryptographic Signature: `SHA256:{audit_hash}`*
"""
    return doc

