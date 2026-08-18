"""
PharmaGuard Dashboard UI Components
===================================
HTML badge formatters, signal tags, and Plotly confidence breakdown charts.
Clean one-way dependency: components.py does NOT import from any view modules.
"""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def esc_badge(e: str) -> str:
    """Render colored badge for ESCALATE / MONITOR / DO_NOT_ESCALATE."""
    cls = {'ESCALATE': 'b-esc', 'MONITOR': 'b-mon', 'DO_NOT_ESCALATE': 'b-dne'}.get(e, 'b-dne')
    return f'<span class="{cls}">{e}</span>'


def cat_badge(c: str) -> str:
    """Render colored badge for ground truth category."""
    m = {
        'confirmed_positive': ('b-pos', 'Confirmed Positive'),
        'genuine_negative_control': ('b-neg', 'Genuine Negative'),
        'zero_report_edge_case': ('b-zero', 'Zero Report'),
    }
    cls, label = m.get(c, ('b-neg', c))
    return f'<span class="{cls}">{label}</span>'


def grade_badge(g: str) -> str:
    """Render colored badge for PubMed evidence grade A/B/C."""
    cls = {'A': 'b-ga', 'B': 'b-gb', 'C': 'b-gc'}.get(g, 'b-gc')
    return f'<span class="{cls}">{g}</span>'


def signal_span(s: str, report_count: int | None = 0) -> str:
    """Render colored FAERS signal strength with inline report count."""
    color = {'STRONG': '#15803d', 'MODERATE': '#334155', 'NO_SIGNAL': '#94a3b8'}.get(s, '#94a3b8')
    wt = {'STRONG': '700', 'MODERATE': '600', 'NO_SIGNAL': '500'}.get(s, '500')
    rc_str = f' ({report_count:,})' if report_count is not None else ''
    return (
        f'<span style="color:{color};font-weight:{wt};font-size:12px;white-space:nowrap;">'
        f'{s}<span style="font-weight:400;font-size:11px;color:#64748b;">{rc_str}</span></span>'
    )


def render_conf_chart(r: dict, key: str) -> None:
    """Render horizontal stacked confidence decomposition Plotly chart."""
    ss = r.get('signal_stats', {})
    lit = r.get('literature', {})
    mech = r.get('mechanism', {})
    prr_raw = ss.get('prr_score', 0) or 0
    grade_raw = lit.get('grade_score', 0) or 0
    plaus_raw = mech.get('plausibility_score', 0) or 0
    w_prr = 0.40 * prr_raw
    w_grade = 0.40 * grade_raw
    w_plaus = 0.20 * plaus_raw
    total = w_prr + w_grade + w_plaus

    labels = ['FAERS PRR ×0.40', 'PubMed Grade ×0.40', 'Plausibility ×0.20']
    vals = [w_prr, w_grade, w_plaus]
    raws = [prr_raw, grade_raw, plaus_raw]
    colors = ['#2563eb', '#0d9488', '#6366f1']

    fig = go.Figure()
    for lbl, val, raw, col in zip(labels, vals, raws, colors):
        fig.add_trace(go.Bar(
            y=[lbl], x=[val], orientation='h', marker_color=col,
            text=f' raw={raw:.2f} → <b>{val:.3f}</b>',
            textposition='outside',
            textfont=dict(size=11, color='#0f172a', family='JetBrains Mono'),
            hovertemplate=f'<b>{lbl}</b><br>Raw Score: {raw:.2f}<br>Weighted: {val:.3f}<extra></extra>',
        ))

    fig.add_shape(type='line', x0=total, x1=total, y0=-0.6, y1=2.6,
                  line=dict(color='#0f172a', width=2, dash='dash'))
    fig.add_annotation(x=total, y=2.85, text=f'Total Σ = <b>{total:.3f}</b>', showarrow=False,
                       font=dict(size=12, color='#0f172a', family='JetBrains Mono'),
                       xanchor='center')

    fig.update_layout(
        barmode='overlay',
        xaxis=dict(range=[0, 1.12], title=None,
                   tickfont=dict(size=11, family='JetBrains Mono', color='#334155'),
                   gridcolor='#e2e8f0', showgrid=True),
        yaxis=dict(title=None,
                   tickfont=dict(size=12, family='Inter', color='#0f172a')),
        height=190, margin=dict(l=6, r=90, t=36, b=6),
        paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
        showlegend=False, font=dict(family='Inter'),
    )
    st.plotly_chart(fig, key=key)
