"""
View 2: Per-Pair Table & Evidence Inspector
===========================================
Dense aligned data table with category/escalation filters and full inspector.
Theme-aware typography and interactive confidence decomposition charts.
"""
from __future__ import annotations

import re
import pandas as pd
import streamlit as st

from ..components import cat_badge, esc_badge, grade_badge, render_conf_chart, signal_span


def view_per_pair(df: pd.DataFrame, theme: str = "light") -> None:
    """Render the Per-Pair evaluation table and drill-down evidence inspector."""
    st.markdown(
        '<div class="pg-header">'
        '<div class="pg-title">Per-Pair Evaluation</div>'
        '<div class="pg-subtitle">All 15 evaluated drug–event pairs · dense aligned data table with full evidence inspection</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    fc1, fc2, fc3 = st.columns([1.2, 1.2, 1.6])
    with fc1:
        cat_f = st.selectbox('Category Filter', ['All', 'confirmed_positive',
                                                 'genuine_negative_control', 'zero_report_edge_case'],
                             label_visibility='collapsed')
    with fc2:
        esc_f = st.selectbox('Escalation Filter', ['All', 'ESCALATE', 'MONITOR', 'DO_NOT_ESCALATE'],
                             label_visibility='collapsed')
    with fc3:
        only_dis = st.checkbox('Disagreements only', value=False)

    fdf = df.copy()
    if cat_f != 'All':
        fdf = fdf[fdf['category'] == cat_f]
    if esc_f != 'All':
        fdf = fdf[fdf['escalation'] == esc_f]
    if only_dis:
        fdf = fdf[~fdf['match']]

    is_dark = (theme == "dark")
    plaus_colors = {
        'HIGH': '#4ade80' if is_dark else '#166534',
        'MODERATE': '#cbd5e1' if is_dark else '#334155',
        'LOW': '#94a3b8',
    }

    table_rows_html = []
    for _, r in fdf.iterrows():
        conf_str = f"{r['confidence']:.3f}" if r['confidence'] is not None else '—'
        plaus = r['plausibility']
        pc = plaus_colors.get(plaus, '#94a3b8')
        flag = '<span style="color:#f59e0b;font-weight:700;margin-right:2px;" title="Disagreement">!</span> ' if not r['match'] else ''
        rc = r.get('report_count', 0)
        table_rows_html.append(
            f'<tr>'
            f'<td class="pg-mono" style="color:var(--pg-text-dim);">{flag}{r["idx"]}</td>'
            f'<td style="font-weight:600; color:var(--pg-text-primary);">{r["drug"]}</td>'
            f'<td style="color:var(--pg-text-secondary);">{r["event"]}</td>'
            f'<td>{cat_badge(r["category"])}</td>'
            f'<td>{signal_span(r["signal"], rc, theme=theme)}</td>'
            f'<td>{grade_badge(r["grade"])}</td>'
            f'<td style="color:{pc}; font-weight:600; font-size:13px;">{plaus}</td>'
            f'<td class="pg-mono">{conf_str}</td>'
            f'<td>{esc_badge(r["escalation"])}</td>'
            f'<td>{esc_badge(r["expected"])}</td>'
            f'</tr>'
        )

    table_html = f"""
    <div class="pg-table-container">
        <table class="pg-data-table">
            <thead>
                <tr>
                    <th style="width:40px;">#</th>
                    <th>Drug</th>
                    <th>Event</th>
                    <th>Category</th>
                    <th>FAERS Signal (Count)</th>
                    <th>PubMed</th>
                    <th>Plausibility</th>
                    <th>Confidence</th>
                    <th>Escalation</th>
                    <th>Expected</th>
                </tr>
            </thead>
            <tbody>
                {''.join(table_rows_html)}
            </tbody>
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:13px;color:var(--pg-text-dim);margin:-10px 0 20px 0;">Showing {len(fdf)} of {len(df)} pairs</p>', unsafe_allow_html=True)

    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
    st.markdown('<div class="pg-section-label">Evidence & Confidence Breakdown Inspector</div>', unsafe_allow_html=True)

    pair_options = [r['idx'] for _, r in fdf.iterrows()]
    if not pair_options:
        st.info('No drug–event pairs match current filters.')
        return

    pair_labels = {
        r['idx']: f"#{r['idx']:02d} — {r['drug']} + {r['event']}  [{r['escalation']}]"
        for _, r in fdf.iterrows()
    }
    sel_idx = st.selectbox(
        'Select pair for deep-dive evidence inspection:',
        options=pair_options,
        format_func=lambda x: pair_labels.get(x, str(x)),
    )

    sel_row = fdf[fdf['idx'] == sel_idx].iloc[0]
    sel_rpt = sel_row['_r']
    ss = sel_rpt.get('signal_stats', {})
    lit = sel_rpt.get('literature', {})
    mech = sel_rpt.get('mechanism', {})

    prr_raw = ss.get('prr')
    prr_formatted = f"{prr_raw:.2f}" if isinstance(prr_raw, (int, float)) else "n/a (0 reports)"
    rc_val = ss.get('report_count', 0)

    dc1, dc2 = st.columns([1.1, 1], gap='large')
    with dc1:
        st.markdown(
            f'<div class="pg-card" style="margin-bottom:14px;">'
            f'<div class="pg-stat-label">FAERS Signal Statistics</div>'
            f'<div class="pg-mono" style="font-size:14px; color:var(--pg-text-primary); margin:8px 0 14px 0;">'
            f'PRR: <b>{prr_formatted}</b> &nbsp;|&nbsp; Reports: <b>{rc_val:,}</b> &nbsp;|&nbsp; Strength: {signal_span(sel_row["signal"], rc_val, theme=theme)}'
            f'</div>'
            f'<div class="pg-stat-label">PubMed Evidence Summary</div>'
            f'<div class="pg-quote-box">{re.sub(r"^Final Grade:\s*\w+\s*", "", lit.get("evidence_summary", "")).strip()}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with dc2:
        plaus_rat = mech.get('plausibility_rationale', '—')
        plaus_src = mech.get('plausibility_source', '—')
        st.markdown(
            f'<div class="pg-card" style="margin-bottom:14px;">'
            f'<div class="pg-stat-label">Mechanistic Plausibility</div>'
            f'<div class="pg-quote-box">{plaus_rat}</div>'
            f'<div style="font-size:12px;color:var(--pg-text-dim);margin-top:2px;margin-bottom:12px;">source: <code>{plaus_src}</code></div>'
            f'<div class="pg-stat-label" style="margin-top:14px;">Confidence Formula Decomposition</div>',
            unsafe_allow_html=True,
        )
        render_conf_chart(sel_rpt, key=f'table_conf_{sel_idx}', theme=theme)
        st.markdown('</div>', unsafe_allow_html=True)
