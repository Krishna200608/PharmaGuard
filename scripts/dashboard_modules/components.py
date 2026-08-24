"""
PharmaGuard Dashboard UI Components
===================================
HTML badge formatters, signal tags, and Plotly confidence breakdown charts.
Clean one-way dependency: components.py does NOT import from any view modules.
Fully theme-aware for Light, Dark, and System modes.
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


def signal_span(s: str, report_count: int | None = 0, theme: str = "light") -> str:
    """Render colored FAERS signal strength with inline report count."""
    is_dark = (theme == "dark")
    if is_dark:
        color = {'STRONG': '#4ade80', 'MODERATE': '#cbd5e1', 'NO_SIGNAL': '#94a3b8'}.get(s, '#94a3b8')
        count_color = '#94a3b8'
    else:
        color = {'STRONG': '#15803d', 'MODERATE': '#334155', 'NO_SIGNAL': '#94a3b8'}.get(s, '#94a3b8')
        count_color = '#64748b'

    wt = {'STRONG': '700', 'MODERATE': '600', 'NO_SIGNAL': '500'}.get(s, '500')
    rc_str = f' ({report_count:,})' if report_count is not None else ''
    return (
        f'<span style="color:{color};font-weight:{wt};font-size:13px;white-space:nowrap;">'
        f'{s}<span style="font-weight:400;font-size:12px;color:{count_color};">{rc_str}</span></span>'
    )


def render_conf_chart(r: dict, key: str, theme: str = "light") -> None:
    """Render horizontal stacked confidence decomposition Plotly chart with theme styling."""
    is_dark = (theme == "dark")

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

    if is_dark:
        colors = ['#3b82f6', '#14b8a6', '#818cf8']
        text_color = '#f8fafc'
        tick_x_color = '#94a3b8'
        tick_y_color = '#f8fafc'
        grid_color = 'rgba(255, 255, 255, 0.08)'
        dash_color = '#f8fafc'
    else:
        colors = ['#2563eb', '#0d9488', '#6366f1']
        text_color = '#0f172a'
        tick_x_color = '#334155'
        tick_y_color = '#0f172a'
        grid_color = 'rgba(15, 23, 42, 0.08)'
        dash_color = '#0f172a'

    fig = go.Figure()
    for lbl, val, raw, col in zip(labels, vals, raws, colors):
        fig.add_trace(go.Bar(
            y=[lbl], x=[val], orientation='h', marker_color=col,
            text=f' raw={raw:.2f} → <b>{val:.3f}</b>',
            textposition='outside',
            textfont=dict(size=12, color=text_color, family='JetBrains Mono'),
            hovertemplate=f'<b>{lbl}</b><br>Raw Score: {raw:.2f}<br>Weighted: {val:.3f}<extra></extra>',
            cliponaxis=False,
        ))

    fig.add_shape(
        type='line', x0=total, x1=total, y0=-0.6, y1=2.6,
        line=dict(color=dash_color, width=2, dash='dash')
    )
    fig.add_annotation(
        x=total, y=2.85, text=f'Total Σ = <b>{total:.3f}</b>', showarrow=False,
        font=dict(size=13, color=text_color, family='JetBrains Mono'),
        xanchor='center'
    )

    fig.update_layout(
        barmode='overlay',
        xaxis=dict(
            range=[0, 1.22], title=None,
            tickfont=dict(size=12, family='JetBrains Mono', color=tick_x_color),
            gridcolor=grid_color, showgrid=True
        ),
        yaxis=dict(
            title=None,
            tickfont=dict(size=13, family='Inter', color=tick_y_color)
        ),
        height=200, margin=dict(l=6, r=120, t=38, b=8),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False, font=dict(family='Inter'),
    )
    st.plotly_chart(fig, key=key)
