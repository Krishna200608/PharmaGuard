"""
View 6: OMOP Pilot Benchmark
============================
Secondary 32-pair evaluation benchmark derived from the OMOP reference set (Ryan et al. 2013).
Surfaces Stage 2 results, endpoint-specific metrics, and the PRR-magnitude hard gate finding (DECISIONS.md §31).
Uses the exact same visual design language, cards, theme handling, and waterfall decomposition charts.
"""
from __future__ import annotations

import re
from pathlib import Path
import streamlit as st

from ..components import cat_badge, esc_badge, grade_badge, material_icon, render_conf_chart
from ..data_loader import OMOP_METRICS


def view_omop_pilot(
    reports: list,
    omop_dir: Path | None = None,
    theme: str = "light",
    repo_root: Path | None = None,
) -> None:
    """Render the OMOP Pilot evaluation view."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[3]
    elif (repo_root / "outputs").is_dir() is False and repo_root.name == "core":
        repo_root = repo_root.parents[1]

    is_dark = (theme == "dark")

    # -----------------------------------------------------------------------
    # a. Header
    # -----------------------------------------------------------------------
    st.markdown(
        '<div class="pg-header">'
        '<div class="pg-title">OMOP Reference Set Pilot — Secondary External-Validity Benchmark</div>'
        '<div class="pg-subtitle">'
        '32-pair secondary pilot · 4 clinical endpoints · OHDSI OMOP Reference Set (Ryan et al. 2013) · PRR-gate finding'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # b. Amber Notice Banner
    # -----------------------------------------------------------------------
    banner_bg = "rgba(242, 184, 75, 0.08)" if is_dark else "rgba(245, 158, 11, 0.06)"
    banner_bd = "#F2B84B" if is_dark else "#D97706"
    banner_title_color = "#FCD34D" if is_dark else "#B45309"
    banner_txt_color = "#E2E8F0" if is_dark else "#334155"
    warn_icon = material_icon("warning", size=19, color=banner_title_color, extra_style="vertical-align:-4px;")

    st.markdown(
        f'<div style="background:{banner_bg}; border-left:4px solid {banner_bd}; border-top:1px solid {banner_bd}; '
        f'border-right:1px solid {banner_bd}; border-bottom:1px solid {banner_bd}; border-radius:0 8px 8px 0; '
        f'padding:16px 20px; margin-bottom:24px;">'
        f'<div style="font-weight:700; font-size:13.5px; color:{banner_title_color}; letter-spacing:0.04em; margin-bottom:6px; display:inline-flex; align-items:center;">'
        f'{warn_icon}SECONDARY EXTERNAL-VALIDITY PILOT NOTICE (DECISIONS.md §31, §15)'
        f'</div>'
        f'<div style="font-size:13px; line-height:1.6; color:{banner_txt_color};">'
        f'This panel displays results from an independent <strong>32-pair secondary pilot benchmark</strong> derived from the '
        f'standard OMOP reference set (Ryan et al., <em>Drug Safety</em> 2013; proxy MedDRA PT mappings).<br>'
        f'<strong>These 32 pairs are NOT part of the frozen 15-pair production benchmark.</strong> In accordance with project '
        f'anti-overfitting discipline (<code>DECISIONS.md §15</code> and <code>§31</code>), <strong>scoring weights (0.40 / 0.40 / 0.20) '
        f'and escalation thresholds (0.70 / 0.35) were strictly frozen before evaluation and were NOT retroactively tuned on this dataset.</strong>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if not reports:
        dir_str = f" in <code>{omop_dir}</code>" if omop_dir else ""
        st.warning(
            f"No OMOP pilot evaluation reports found{dir_str}.<br>"
            "Run <code>python scripts/research/run_omop_pilot_eval.py</code> to execute the 32-pair OMOP Stage 2 evaluation."
        )
        return

    m = OMOP_METRICS

    # -----------------------------------------------------------------------
    # c. Aggregate Metric Cards
    # -----------------------------------------------------------------------
    col_hero, col_flank = st.columns([2.1, 1.1], gap='large')
    with col_hero:
        st.markdown(
            f'<div class="pg-hero-card">'
            f'<div class="pg-stat-label">Strict Recall — OMOP Pilot Result</div>'
            f'<div class="pg-hero-value">{m["s_rec"]:.3f}</div>'
            f'<div class="pg-hero-sub">1 of 16 confirmed positives reached strict ESCALATE (15 missed strict)</div>'
            f'<div class="pg-hero-note">'
            f'Lenient Recall: <strong style="color:var(--text);">{m["l_rec"]:.3f}</strong> (9/16) — 8 positives rescued as MONITOR. '
            f'Negative control specificity is perfect at <strong style="color:var(--text);">{m["s_spec"]:.3f}</strong> (16/16 cleared).'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_flank:
        st.markdown(
            f'<div class="pg-card">'
            f'<div class="pg-stat-label">Over-Caution Rate</div>'
            f'<div class="pg-stat-value">{m["ocr"]:.1f}%</div>'
            f'<div class="pg-stat-sub">0 of 16 negative controls → MONITOR</div>'
            f'<div style="height: 14px; border-bottom: 1px solid var(--divider); margin-bottom: 12px;"></div>'
            f'<div class="pg-stat-label">Spurious False Alarms</div>'
            f'<div class="pg-stat-value">FP = 0</div>'
            f'<div class="pg-stat-sub">Strict Wilson 95% CI: 0.806–1.000</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)

    st.markdown('<div class="pg-section-label">Strict Evaluation Metrics (Primary)</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap='medium')
    strict_metrics = [
        ('Strict Precision', f"{m['s_prec']:.3f}", 'Wilson 95% CI: 0.207–1.000', 'TP=1, FP=0 (clean precision)'),
        ('Strict Specificity', f"{m['s_spec']:.3f}", 'Wilson 95% CI: 0.806–1.000', '16 of 16 negative controls cleared'),
        ('Strict F1', f"{m['s_f1']:.3f}", 'Bootstrap 95% CI: 0.000–0.333', 'Harmonic mean under strict gating'),
        ('Pairs Evaluated', f"{m['pairs']}", f"{m['pos_count']} confirmed pos · {m['neg_count']} neg ctrl", '4 clinical endpoints (8 pairs each)'),
    ]
    for col, (label, val, sub, note) in zip([c1, c2, c3, c4], strict_metrics):
        with col:
            st.markdown(
                f'<div class="pg-stat-card">'
                f'<div>'
                f'<div class="pg-stat-label">{label}</div>'
                f'<div class="pg-stat-value">{val}</div>'
                f'</div>'
                f'<div>'
                f'<div class="pg-stat-sub">{sub}</div>'
                f'<div class="pg-stat-note">{note}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)

    st.markdown('<div class="pg-section-label">Lenient Evaluation Metrics (MONITOR counts as True Positive)</div>', unsafe_allow_html=True)
    l1, l2, l3, l4 = st.columns(4, gap='medium')
    lenient_metrics = [
        ('Lenient Precision', f"{m['l_prec']:.3f}", 'Wilson 95% CI: 0.701–1.000', 'TP=9, FP=0 (no false alarms)'),
        ('Lenient Recall', f"{m['l_rec']:.3f}", 'Wilson 95% CI: 0.332–0.769', '9 of 16 true signals captured (7 missed)'),
        ('Lenient Specificity', f"{m['l_spec']:.3f}", 'Wilson 95% CI: 0.806–1.000', '16 of 16 negative controls cleared'),
        ('Lenient F1', f"{m['l_f1']:.3f}", 'Bootstrap 95% CI: 0.455–0.883', 'Harmonic mean under lenient scoring'),
    ]
    for col, (label, val, sub, note) in zip([l1, l2, l3, l4], lenient_metrics):
        with col:
            st.markdown(
                f'<div class="pg-stat-card">'
                f'<div>'
                f'<div class="pg-stat-label">{label}</div>'
                f'<div class="pg-stat-value">{val}</div>'
                f'</div>'
                f'<div>'
                f'<div class="pg-stat-sub">{sub}</div>'
                f'<div class="pg-stat-note">{note}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # -----------------------------------------------------------------------
    # d. Category Breakdown Table (4 Clinical Endpoints)
    # -----------------------------------------------------------------------
    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
    st.markdown('<div class="pg-section-label">Performance Breakdown by Clinical Endpoint</div>', unsafe_allow_html=True)

    endpoint_rows = [
        ("Hepatotoxicity (Acute Liver Injury)", "4", "4", "1/4 (25.0%)", "3/4 (75.0%)", "4/4 (100.0%)", "Isoniazid escalated; Carbamazepine & Allopurinol monitored; Captopril missed (marginal conf 0.332)"),
        ("Acute Kidney Injury (Acute Renal Failure)", "4", "4", "0/4 (0.0%)", "4/4 (100.0%)", "4/4 (100.0%)", "All 4 positives (Lisinopril, Naproxen, Acyclovir, Hydrochlorothiazide) correctly triaged as MONITOR"),
        ("Myocardial Infarction (Acute MI)", "4", "4", "0/4 (0.0%)", "1/4 (25.0%)", "4/4 (100.0%)", "Indomethacin monitored; Amlodipine, Dipyridamole, Nifedipine zeroed by PRR < 2.0 gate"),
        ("Gastrointestinal Haemorrhage (Upper GI Bleed)", "4", "4", "0/4 (0.0%)", "1/4 (25.0%)", "4/4 (100.0%)", "Ketoprofen monitored; SSRIs (Citalopram, Fluoxetine, Sertraline) zeroed by PRR < 2.0 gate"),
    ]

    table_html = (
        '<div class="pg-card" style="margin-bottom:12px;">'
        '<div class="pg-table-container" style="margin-bottom:0px;">'
        '<table class="pg-cmp-table">'
        '<thead><tr>'
        '<th>Clinical Endpoint</th>'
        '<th style="text-align:center">Pos</th>'
        '<th style="text-align:center">Neg</th>'
        '<th style="text-align:right">Strict Recall</th>'
        '<th style="text-align:right">Lenient Recall</th>'
        '<th style="text-align:right">Specificity</th>'
        '<th>Endpoint Outcome Summary</th>'
        '</tr></thead>'
        '<tbody>'
    )
    for ep, pos, neg, s_rec, l_rec, spec, notes in endpoint_rows:
        table_html += (
            f'<tr>'
            f'<td style="font-weight:600; color:var(--text);">{ep}</td>'
            f'<td class="num" style="text-align:center">{pos}</td>'
            f'<td class="num" style="text-align:center">{neg}</td>'
            f'<td class="num" style="font-weight:600;">{s_rec}</td>'
            f'<td class="num" style="font-weight:600;">{l_rec}</td>'
            f'<td class="num" style="color:var(--text);">{spec}</td>'
            f'<td style="font-size:12.5px; color:var(--text-secondary);">{notes}</td>'
            f'</tr>'
        )
    table_html += '</tbody></table></div></div>'
    st.markdown(table_html, unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # e. Root Cause: The PRR-Magnitude Gate Section & Disagreements Table
    # -----------------------------------------------------------------------
    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
    st.markdown('<div class="pg-section-label">Root Cause: The PRR-Magnitude Hard Gate (DECISIONS.md §31)</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="pg-card" style="margin-bottom:16px;">'
        f'<div style="font-size:14px; line-height:1.65; color:var(--text-secondary); margin-bottom:12px;">'
        f'The primary driver of the <strong>7 DO_NOT_ESCALATE disagreements</strong> on confirmed positive controls is the unconditional '
        f'PRR magnitude floor in <code>pharmaguard/agent/output_schema.py</code> (<code>compute_prr_score()</code>):<br>'
        f'<div style="margin:8px 0; padding:10px 14px; background:var(--surface2); border-left:3px solid var(--primary); border-radius:4px; font-family:var(--font-mono); font-size:13px; color:var(--text);">'
        f'PRR &lt; 2.0 &nbsp;&implies;&nbsp; SignalStrength = NO_SIGNAL &nbsp;(score = 0.0) &nbsp;&implies;&nbsp; Gate 1 Override: DO_NOT_ESCALATE'
        f'</div>'
        f'When <code>SignalStrength == NO_SIGNAL</code>, <code>derive_escalation()</code> unconditionally forces '
        f'<strong>DO_NOT_ESCALATE</strong>, overriding biological plausibility and PubMed literature grading regardless of confidence.'
        f'</div>'
        f'<div style="font-size:13px; line-height:1.6; color:var(--text-muted);">'
        f'<strong>Epidemiological Context:</strong> For widely prescribed chronic medications (antihypertensives like amlodipine/nifedipine and '
        f'antidepressants like citalopram/fluoxetine/sertraline), massive reporting denominator volumes dilute disproportionality point estimates '
        f'into the 1.16–1.90 range. However, their 95% lower confidence intervals strictly clear 1.0 (1.066–1.795), confirming genuine '
        f'statistical disproportionality above background.'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    disagreements = [
        {
            "drug": "amlodipine", "event": "myocardial_infarction",
            "prr": "1.271", "ci": "1.235", "count": "4,610",
            "plaus": "LOW (0.0)", "grade": "B (0.5)", "conf": "0.200",
            "decision": "DO_NOT_ESCALATE",
            "cause": "Gate 1 Hard Override (PRR < 2.0)",
            "cause_type": "gate",
        },
        {
            "drug": "dipyridamole", "event": "myocardial_infarction",
            "prr": "1.807", "ci": "1.456", "count": "81",
            "plaus": "HIGH (1.0)", "grade": "B (0.5)", "conf": "0.400",
            "decision": "DO_NOT_ESCALATE",
            "cause": "Gate 1 Hard Override (PRR < 2.0)",
            "cause_type": "gate",
        },
        {
            "drug": "nifedipine", "event": "myocardial_infarction",
            "prr": "1.738", "ci": "1.618", "count": "743",
            "plaus": "LOW (0.0)", "grade": "A (1.0)", "conf": "0.400",
            "decision": "DO_NOT_ESCALATE",
            "cause": "Gate 1 Hard Override (PRR < 2.0)",
            "cause_type": "gate",
        },
        {
            "drug": "citalopram", "event": "gastrointestinal_haemorrhage",
            "prr": "1.904", "ci": "1.795", "count": "1,108",
            "plaus": "HIGH (1.0)", "grade": "C (0.0)", "conf": "0.200",
            "decision": "DO_NOT_ESCALATE",
            "cause": "Gate 1 Hard Override (PRR < 2.0)",
            "cause_type": "gate",
        },
        {
            "drug": "fluoxetine", "event": "gastrointestinal_haemorrhage",
            "prr": "1.162", "ci": "1.066", "count": "521",
            "plaus": "HIGH (1.0)", "grade": "C (0.0)", "conf": "0.200",
            "decision": "DO_NOT_ESCALATE",
            "cause": "Gate 1 Hard Override (PRR < 2.0)",
            "cause_type": "gate",
        },
        {
            "drug": "sertraline", "event": "gastrointestinal_haemorrhage",
            "prr": "1.601", "ci": "1.513", "count": "1,191",
            "plaus": "HIGH (1.0)", "grade": "C (0.0)", "conf": "0.200",
            "decision": "DO_NOT_ESCALATE",
            "cause": "Gate 1 Hard Override (PRR < 2.0)",
            "cause_type": "gate",
        },
        {
            "drug": "captopril", "event": "hepatotoxicity",
            "prr": "2.239", "ci": "1.501", "count": "24",
            "plaus": "LOW (0.0)", "grade": "B (0.5)", "conf": "0.332",
            "decision": "DO_NOT_ESCALATE",
            "cause": "Marginal Confidence (0.332 < 0.35 threshold)",
            "cause_type": "margin",
        },
    ]

    dis_table_html = (
        '<div class="pg-card" style="margin-bottom:16px;">'
        '<div style="font-size:14px; font-weight:700; color:var(--text); margin-bottom:10px;">All 7 Missed Confirmed Positive Controls</div>'
        '<div class="pg-table-container" style="margin-bottom:0px;">'
        '<table class="pg-cmp-table">'
        '<thead><tr>'
        '<th>Drug & Adverse Event</th>'
        '<th style="text-align:right">FAERS PRR</th>'
        '<th style="text-align:right">Lower 95% CI</th>'
        '<th style="text-align:right">Reports</th>'
        '<th style="text-align:center">Plausibility</th>'
        '<th style="text-align:center">Literature</th>'
        '<th style="text-align:right">Confidence</th>'
        '<th style="text-align:center">Decision</th>'
        '<th>Root Cause Analysis</th>'
        '</tr></thead>'
        '<tbody>'
    )
    for d in disagreements:
        tag_bg = "rgba(255, 77, 77, 0.12)" if d["cause_type"] == "gate" else "rgba(242, 184, 75, 0.12)"
        tag_color = "#fca5a5" if (is_dark and d["cause_type"] == "gate") else ("#ef4444" if d["cause_type"] == "gate" else ("#fcd34d" if is_dark else "#d97706"))
        tag_bd = "rgba(255, 77, 77, 0.3)" if d["cause_type"] == "gate" else "rgba(242, 184, 75, 0.3)"

        dis_table_html += (
            f'<tr>'
            f'<td><strong style="color:var(--text);">{d["drug"]}</strong> <span style="font-size:12px; color:var(--text-secondary);">+ {d["event"].replace("_", " ")}</span></td>'
            f'<td class="num">{d["prr"]}</td>'
            f'<td class="num">{d["ci"]}</td>'
            f'<td class="num">{d["count"]}</td>'
            f'<td style="text-align:center; font-size:12.5px;">{d["plaus"]}</td>'
            f'<td style="text-align:center; font-size:12.5px;">{d["grade"]}</td>'
            f'<td class="num" style="font-weight:600;">{d["conf"]}</td>'
            f'<td style="text-align:center;">{esc_badge(d["decision"])}</td>'
            f'<td><span style="display:inline-block; padding:3px 8px; border-radius:4px; font-size:11.5px; font-weight:600; background:{tag_bg}; color:{tag_color}; border:1px solid {tag_bd};">{d["cause"]}</span></td>'
            f'</tr>'
        )
    dis_table_html += '</tbody></table></div></div>'
    st.markdown(dis_table_html, unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # f. Confidence Formula Decomposition Spotlights (Representative Pairs)
    # -----------------------------------------------------------------------
    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
    st.markdown('<div class="pg-section-label">Representative Disagreement Spotlights & Confidence Decompositions</div>', unsafe_allow_html=True)

    citalopram_r = next((r for r in reports if 'citalopram' in r.get('run_id', '')), None)
    captopril_r = next((r for r in reports if 'captopril' in r.get('run_id', '')), None)

    spotlight_cases = [
        {
            'report': citalopram_r,
            'drug': 'citalopram', 'event': 'gastrointestinal haemorrhage',
            'category': 'omop_confirmed_positive', 'expected': 'ESCALATE', 'got': 'DO_NOT_ESCALATE',
            'title': 'Case 1 — Gate 1 Hard Override: citalopram + gastrointestinal haemorrhage',
            'epidemiology': (
                'FAERS spontaneous reporting contains 1,108 cases yielding PRR = 1.904 with a 95% lower CI of 1.795. '
                'Because the point estimate (1.904) falls marginally below the fixed 2.0 threshold, the statistical signal '
                'is categorized as NO_SIGNAL (score = 0.0), even though disproportionality is statistically significant.'
            ),
            'mechanism': (
                'SSRIs inhibit the serotonin transporter (SERT) on platelets, depleting platelet intracellular serotonin stores '
                'and impairing normal aggregation and hemostasis. The agent derived HIGH biological plausibility (score = 1.0) '
                'and PubMed returned Grade C literature. Raw formula confidence reached 0.200.'
            ),
            'why_gate': (
                'Gate 1 Hard Override: Because SignalStrength == NO_SIGNAL, derive_escalation() unconditionally forced '
                'DO_NOT_ESCALATE. The biological plausibility contribution (0.20×1.0 = 0.20) was completely overridden by the '
                'sub-2.0 PRR cutoff.'
            ),
        },
        {
            'report': captopril_r,
            'drug': 'captopril', 'event': 'hepatotoxicity',
            'category': 'omop_confirmed_positive', 'expected': 'ESCALATE', 'got': 'DO_NOT_ESCALATE',
            'title': 'Case 2 — Marginal Confidence Cutoff: captopril + hepatotoxicity',
            'epidemiology': (
                'FAERS spontaneous reporting contains 24 reports yielding PRR = 2.239 (95% lower CI: 1.501), '
                'classified as WEAK signal (score = 0.33). PubMed literature search retrieved 5 abstracts with multiple '
                'case reports and association findings, evaluated as Grade B (score = 0.5).'
            ),
            'mechanism': (
                'Hepatotoxicity is a rare, idiosyncratic adverse reaction to ACE inhibitors unrelated to primary ACE inhibition. '
                'The agent derived LOW biological plausibility (score = 0.0). Composite confidence computed to '
                '0.40×0.33 + 0.40×0.50 + 0.20×0.0 = 0.132 + 0.200 = 0.332.'
            ),
            'why_gate': (
                'Marginal Confidence Cutoff: Unlike Case 1, Gate 1 did not fire (signal is WEAK). However, composite confidence (0.332) '
                'narrowly fell short of the 0.35 MONITOR threshold by just 0.018 points, routing the signal to DO_NOT_ESCALATE.'
            ),
        },
    ]

    for idx, sc in enumerate(spotlight_cases):
        if idx > 0:
            st.markdown('<div style="height: 10px;"></div><hr class="pg-divider">', unsafe_allow_html=True)
        rpt = sc['report']
        if rpt is None:
            st.warning(f"Report for {sc['drug']} not found in OMOP pilot outputs.")
            continue

        triage = rpt.get('triage', {})
        ss = rpt.get('signal_stats', {})
        lit = rpt.get('literature', {})
        mech = rpt.get('mechanism', {})
        conf = triage.get('confidence')
        conf_d = f'{conf:.3f}' if conf is not None else '—'
        signal = ss.get('prr_score_label', '—')
        grade = lit.get('evidence_grade', '—')
        plaus = mech.get('biological_plausibility', '—')
        ev_raw = lit.get('evidence_summary', '')
        ev_sum = re.sub(r'^Final Grade:\s*\w+\s*', '', ev_raw).strip()
        plaus_r = mech.get('plausibility_rationale', '')

        st.markdown(
            f'<div class="pg-hero-card" style="margin-bottom:16px;">'
            f'<div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">'
            f'<div>'
            f'<span style="font-size:22px; font-weight:700; color:var(--text);">{sc["drug"]}</span> '
            f'<span style="font-size:16.5px; color:var(--text-secondary);">+ {sc["event"]}</span>'
            f'</div>'
            f'<div><span class="b-pos">OMOP Positive Control</span></div>'
            f'</div>'
            f'<div style="margin-top:10px; display:flex; flex-wrap:wrap; gap:12px; align-items:center;">'
            f'<span style="font-size:13px;color:var(--text-muted);">Expected:</span> {esc_badge(sc["expected"])}'
            f'<span style="font-size:13px;color:var(--text-muted);">→ Got:</span> {esc_badge(sc["got"])}'
            f'<span style="font-size:13px;color:var(--text-secondary);margin-left:8px;">'
            f'Signal: <b>{signal}</b> &nbsp;|&nbsp; Grade: <b>{grade}</b> &nbsp;|&nbsp; Plausibility: <b>{plaus}</b> &nbsp;|&nbsp; '
            f'Confidence: <span class="pg-mono"><b>{conf_d}</b></span>'
            f'</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns([1.1, 1], gap='large')
        with col_a:
            st.markdown(
                f'<div class="pg-card" style="margin-bottom:14px;">'
                f'<div class="pg-stat-label">Epidemiological Evidence</div>'
                f'<div class="pg-quote-box">{sc["epidemiology"]}</div>'
                f'<div style="height:10px;"></div>'
                f'<div class="pg-stat-label">PubMed Evidence Summary</div>'
                f'<div class="pg-quote-box">{ev_sum}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_b:
            st.markdown(
                f'<div class="pg-card" style="margin-bottom:14px;">'
                f'<div class="pg-stat-label">Mechanistic Plausibility</div>'
                f'<div class="pg-quote-box">{plaus_r}</div>'
                f'<div style="height:10px;"></div>'
                f'<div class="pg-stat-label">Disagreement Root Cause</div>'
                f'<div class="pg-conclusion-box">{sc["why_gate"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="pg-card">'
            f'<div class="pg-stat-label" style="margin-bottom:10px;">Confidence Formula Decomposition</div>',
            unsafe_allow_html=True,
        )
        render_conf_chart(rpt, key=f'omop_spotlight_{sc["drug"]}', theme=theme)
        st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Design Note Callout
    # -----------------------------------------------------------------------
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="pg-callout">'
        '<strong>Methodological Takeaway: Static Threshold Limitations in High-Utilization Cohorts.</strong> '
        'The OMOP pilot empirically demonstrates that static PRR &ge; 2.0 thresholds calibrated on acute, high-disproportionality signals '
        'do not generalize seamlessly to chronic, high-utilization medications exhibiting modest relative risk despite statistical significance '
        'and high biological plausibility. This finding is formally documented as an external-validity boundary in DECISIONS.md §31.'
        '</div>',
        unsafe_allow_html=True,
    )
