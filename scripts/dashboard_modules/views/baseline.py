"""
View 4: Baseline Comparison
===========================
Tool-grounded PharmaGuard vs. Single-Shot LLM Baseline and Liraglutide case study.
Card-based comparative layout with dual-theme compatibility and aligned tabular metrics.
"""
from __future__ import annotations

import streamlit as st
from ..components import esc_badge
from ..data_loader import BASE_METRICS, PROD_METRICS


def view_baseline(prod_reports: list, base_reports: list, theme: str = "light") -> None:
    """Render the Baseline Comparison tab."""
    st.markdown(
        '<div class="pg-header">'
        '<div class="pg-title">Baseline Comparison</div>'
        '<div class="pg-subtitle">'
        'PharmaGuard (tool-grounded, 3-source pipeline) vs. Single-Shot LLM Baseline (no tools)'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    def _table(d: dict, is_prod: bool) -> str:
        title = 'PharmaGuard · Tool-Grounded' if is_prod else 'Single-Shot LLM Baseline · No Tools'
        tag_color = 'var(--primary)' if is_prod else 'var(--text-secondary)'
        return (
            f'<div class="pg-card" style="margin-bottom:8px;">'
            f'<div style="font-size:15px; font-weight:700; color:{tag_color}; margin-bottom:12px;">{title}</div>'
            f'<div class="pg-table-container" style="margin-bottom:0px;">'
            f'<table class="pg-cmp-table">'
            f'<thead><tr><th>Metric</th><th style="text-align:right">Strict</th><th style="text-align:right">Lenient</th></tr></thead>'
            f'<tbody>'
            f'<tr><td>Precision</td><td class="num">{d["s_prec"]:.3f}</td><td class="num">{d["l_prec"]:.3f}</td></tr>'
            f'<tr><td>Recall</td><td class="num">{d["s_rec"]:.3f}</td><td class="num">{d["l_rec"]:.3f}</td></tr>'
            f'<tr><td>Specificity</td><td class="num">{d["s_spec"]:.3f}</td><td class="num">{d["l_spec"]:.3f}</td></tr>'
            f'<tr><td>F1 Score</td><td class="num">{d["s_f1"]:.3f}</td><td class="num">{d["l_f1"]:.3f}</td></tr>'
            f'<tr><td>Over-Caution Rate</td><td class="num" colspan="2" style="text-align:right">{d["ocr"]:.1f}%</td></tr>'
            f'</tbody>'
            f'</table>'
            f'</div>'
            f'</div>'
        )

    mc1, mc2 = st.columns(2, gap='large')
    with mc1:
        st.markdown(_table(PROD_METRICS, True), unsafe_allow_html=True)
    with mc2:
        st.markdown(_table(BASE_METRICS, False), unsafe_allow_html=True)

    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="pg-title" style="font-size:18px; margin-bottom:4px;">Key Illustration: liraglutide + pancreatic cancer</div>'
        '<div class="pg-subtitle" style="margin-bottom:18px;">Clearest single example of what tool-grounded triage adds over ungrounded LLM recall</div>',
        unsafe_allow_html=True,
    )

    prod_lira = next((r for r in prod_reports if 'liraglutide' in r.get('run_id', '')), None)
    base_lira = next((r for r in base_reports if 'liraglutide' in r.get('run_id', '')), None)
    if not prod_lira or not base_lira:
        st.error('Could not find liraglutide reports in outputs/ — run the evaluation pipeline first.')
        return

    lc1, lc2 = st.columns(2, gap='large')

    def _case_col(col, title, rpt, expected, notes, is_prod=True):
        triage = rpt.get('triage', {})
        esc = triage.get('escalation', '—')
        conf = triage.get('confidence')
        trace = triage.get('agent_reasoning_trace', [])
        conf_d = f'{conf:.3f}' if conf is not None else '—'
        tag_color = 'var(--primary)' if is_prod else 'var(--text-secondary)'
        with col:
            st.markdown(
                f'<div class="pg-card">'
                f'<div style="font-size:15px; font-weight:700; color:{tag_color}; margin-bottom:10px;">{title}</div>'
                f'<div style="display:flex; gap:10px; align-items:center; margin-bottom:6px;">'
                f'{esc_badge(esc)}'
                f'<span style="font-size:13px; color:var(--text-dim);">expected: {expected}</span>'
                f'</div>'
                f'<div class="pg-mono" style="font-size:13px; color:var(--text-muted); margin-bottom:12px;">confidence = <b>{conf_d}</b></div>'
                + (f'<div class="pg-quote-box" style="font-size:13px; margin-bottom:12px;">{"<br>".join(trace)}</div>' if trace else '')
                + (f'<ul style="font-size:13.5px; color:var(--text-secondary); margin:10px 0 0; padding-left:20px; line-height:1.65;">{"".join(f"<li style='margin-bottom:5px;'>{n}</li>" for n in notes)}</ul>' if notes else '')
                + '</div>',
                unsafe_allow_html=True,
            )

    _case_col(lc1, 'PharmaGuard · Tool-Grounded', prod_lira, 'DO_NOT_ESCALATE',
              ['FAERS: 0 co-occurrences → NO_SIGNAL gate → DO_NOT_ESCALATE',
               'Confidence 0.300 = 0.40×0 + 0.40×0.5 + 0.20×0.5',
               'FAERS disproportionality overrides literature plausibility',
               'FDA/EMA 2014 joint review: no causal link established'],
              is_prod=True)

    _case_col(lc2, 'Single-Shot LLM Baseline · No Tools', base_lira, 'DO_NOT_ESCALATE',
              ['No FAERS query — no signal check performed',
               'Confidence 0.85 is raw LLM self-report, not formula-grounded',
               'Recalls historical regulatory concern, not its resolution',
               "Confuses 'this was investigated' with 'this was confirmed'"],
              is_prod=False)

    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="pg-callout">'
        '<strong>Note: metformin::hypoglycaemia.</strong> '
        'Both systems output MONITOR — but for fundamentally different reasons. '
        'The baseline does so via ungrounded clinical caution. '
        'PharmaGuard does so because a 9,340-report STRONG FAERS signal (PRR=10.73) '
        'floors the 0.40×PRR_score term at 0.40, while correctly assigning plausibility=LOW and Grade C '
        'to discount the confounded polypharmacy signal. '
        'See DECISIONS.md §21 and the Disagreement Spotlight tab.'
        '</div>',
        unsafe_allow_html=True,
    )
