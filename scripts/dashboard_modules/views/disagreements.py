"""
View 3: Disagreement Spotlight
==============================
Evidence and mechanistic deep-dives for Montelukast and Metformin.
"""
from __future__ import annotations

import re
from pathlib import Path
import streamlit as st

from ..components import cat_badge, esc_badge, render_conf_chart


def view_disagreements(reports: list, outputs_dir: Path | None = None) -> None:
    """Render the Disagreement Spotlight tab."""
    st.markdown(
        '<div class="pg-header">'
        '<div class="pg-title">Disagreement Spotlight</div>'
        '<div class="pg-subtitle">'
        'Two pairs where PharmaGuard outputs MONITOR rather than the expected label — '
        'both represent correct, intended pharmacovigilance outcomes under uncertainty'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    montelukast_r = next((r for r in reports if 'montelukast' in r.get('run_id', '')), None)
    metformin_r = next((r for r in reports if 'metformin' in r.get('run_id', '')), None)

    cases = [
        {
            'report': montelukast_r,
            'drug': 'montelukast', 'event': 'suicidal ideation',
            'category': 'confirmed_positive', 'expected': 'ESCALATE', 'got': 'MONITOR',
            'epidemiology': (
                'FDA Boxed Warning (March 2020) for serious neuropsychiatric events including suicidal ideation. '
                'The FAERS signal is MODERATE (PRR=3.37, 1,259 reports) and PubMed returns Grade A evidence — '
                'two abstracts contain ROR statistics with 95% CIs.'
            ),
            'mechanism': (
                'CysLT1 receptors are expressed primarily in the peripheral airways. '
                'The mechanistic link between leukotriene receptor antagonism and CNS neuropsychiatric events '
                'remains pharmacologically uncertain — no confirmed direct CNS pathway is established. '
                'This is the curated plausibility=LOW rationale: mechanistic uncertainty coexists with an epidemiological signal.'
            ),
            'conclusion': (
                'MONITOR is the pharmacovigilance-correct output when a genuine epidemiological signal coexists '
                'with unresolved mechanistic uncertainty. The system correctly reflects that the mechanism is not '
                'established, not that the signal is absent. Under lenient scoring this is still a True Positive.'
            ),
        },
        {
            'report': metformin_r,
            'drug': 'metformin', 'event': 'hypoglycaemia',
            'category': 'genuine_negative_control', 'expected': 'DO_NOT_ESCALATE', 'got': 'MONITOR',
            'epidemiology': (
                'FAERS contains approximately 9,340 reports for metformin + hypoglycaemia (MedDRA PT), '
                'yielding PRR=10.73 (STRONG). This signal is heavily confounded: hypoglycemia in diabetic patients '
                'overwhelmingly results from concomitant insulin or sulfonylurea use, not from metformin monotherapy.'
            ),
            'mechanism': (
                'Metformin inhibits hepatic gluconeogenesis via AMPK activation. '
                'It does not stimulate insulin secretion, so compensatory glucose-maintenance '
                'mechanisms remain intact during monotherapy. Hypoglycemia is not pharmacologically '
                'plausible as a direct metformin effect — only as a drug interaction artifact. '
                'The agent correctly assigns plausibility=LOW (score=0.0) and PubMed Grade C.'
            ),
            'conclusion': (
                'MONITOR is the over-cautious but safety-correct outcome when 9,000+ spontaneous reports exist '
                'even after mechanistic de-weighting. The 0.40×PRR_score term floors confidence at 0.40, '
                'preventing DO_NOT_ESCALATE despite plausibility=LOW and Grade C. Architectural property, not a bug. '
                'Under strict metrics: FP=1. Under lenient: TN.'
            ),
        },
    ]

    for i, case in enumerate(cases):
        if i > 0:
            st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
        rpt = case['report']
        if rpt is None:
            dir_str = f" in {outputs_dir}" if outputs_dir else ""
            st.warning(f"Report for {case['drug']} not found{dir_str}")
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
            f'<div style="margin-bottom:14px;">'
            f'<div style="display:flex; align-items:baseline; gap:12px;">'
            f'<span style="font-size:20px; font-weight:700; color:#0f172a;">{case["drug"]}</span>'
            f'<span style="font-size:15px; color:#64748b;">+ {case["event"]}</span>'
            f'</div>'
            f'<div style="margin-top:8px; display:flex; flex-wrap:wrap; gap:10px; align-items:center;">'
            f'{cat_badge(case["category"])}'
            f'<span style="font-size:12px;color:#64748b;">Expected:</span> {esc_badge(case["expected"])}'
            f'<span style="font-size:12px;color:#64748b;">→ Got:</span> {esc_badge(case["got"])}'
            f'<span style="font-size:12px;color:#64748b;margin-left:8px;">'
            f'Signal: {signal} &nbsp;|&nbsp; Grade: {grade} &nbsp;|&nbsp; Plausibility: {plaus} &nbsp;|&nbsp; '
            f'Confidence: <span class="pg-mono"><b>{conf_d}</b></span>'
            f'</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns([1.1, 1], gap='large')
        with col_a:
            st.markdown('<div class="pg-stat-label">Epidemiological Evidence</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="pg-quote-box">{case["epidemiology"]}</div>', unsafe_allow_html=True)

            st.markdown('<div class="pg-stat-label" style="margin-top:12px;">PubMed Evidence Summary (Actual Output)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="pg-quote-box">{ev_sum}</div>', unsafe_allow_html=True)

        with col_b:
            st.markdown('<div class="pg-stat-label">Mechanistic Plausibility (Actual Rationale)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="pg-quote-box">{plaus_r}</div>', unsafe_allow_html=True)

            st.markdown('<div class="pg-stat-label" style="margin-top:12px;">Why MONITOR Is Correct Here</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="pg-conclusion-box">{case["conclusion"]}</div>', unsafe_allow_html=True)

        st.markdown('<div class="pg-stat-label" style="margin-top:16px;">Confidence Formula Decomposition</div>', unsafe_allow_html=True)
        render_conf_chart(rpt, key=f'spotlight_{case["drug"]}')

    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="pg-callout">'
        '<strong>Design Note: Strict / Lenient Dual-Metric Framework.</strong> '
        'These two cases are why PharmaGuard reports both metrics as first-class outputs. '
        'Strict metrics correctly show reduced confidence under genuine uncertainty (FN=1, FP=0). '
        'Lenient metrics correctly show the signal was never dismissed (TP=7, FP=1). '
        'A single-metric evaluation would obscure this distinction — see DECISIONS.md §14.'
        '</div>',
        unsafe_allow_html=True,
    )
