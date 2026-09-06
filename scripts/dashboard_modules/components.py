"""
PharmaGuard Dashboard UI Components
===================================
HTML badge formatters, signal tags, Plotly confidence breakdown charts,
and Google Material Icons SVG formatters.
Clean one-way dependency: components.py does NOT import from any view modules.
Fully theme-aware for Light, Dark, and System modes with centralized tokens.
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


def agreement_badge(agr: str) -> str:
    """Render colored badge for CONCORDANT / DISCORDANT evidence profiles."""
    cls = 'b-zero' if agr == 'DISCORDANT' else 'b-neg'
    return f'<span class="{cls}" style="font-weight:600;font-size:11px;letter-spacing:0.02em;">{agr}</span>'


def material_icon(name: str, size: int = 18, color: str = "currentColor", extra_style: str = "") -> str:
    """Render authentic Google Material Icon via inline SVG for instant, font-independent rendering."""
    paths = {
        "warning": "m40-120 440-760 440 760H40Zm138-80h604L480-720 178-200Zm302-40q17 0 28.5-11.5T520-280q0-17-11.5-28.5T480-320q-17 0-28.5 11.5T440-280q0 17 11.5 28.5T480-240Zm-40-120h80v-200h-80v200Z",
        "star": "m233-120 65-281L80-590l288-25 112-265 112 265 288 25-218 189 65 281-247-149-247 149Z",
        "cancel": "m336-280 144-144 144 144 56-56-144-144 144-144-56-56-144 144-144-144-56 56 144 144-144 144 56 56ZM480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Z",
        "check_circle": "m424-296 282-282-56-56-226 226-114-114-56 56 170 170Zm56 216q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Z",
        "shield": "m480-80-360-160v-320q0-185 150-310.5T480-920q120 0 270 125.5T900-560v320L480-80Zm0-84q134-58 227-167t93-229v-264L480-804 160-664v264q0 120 93 229t227 167Zm0-396Z",
    }
    path_d = paths.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" height="{size}px" viewBox="0 -960 960 960" width="{size}px" '
        f'fill="{color}" style="vertical-align:-3px; margin-right:4px; display:inline-block; {extra_style}">'
        f'<path d="{path_d}"/>'
        f'</svg>'
    )


def signal_span(s: str, report_count: int | None = 0, theme: str = "light") -> str:
    """Render colored FAERS signal strength with inline report count."""
    is_dark = (theme == "dark")
    if is_dark:
        color = {'STRONG': '#22C77A', 'MODERATE': '#A8B3C3', 'NO_SIGNAL': '#738096'}.get(s, '#738096')
        count_color = '#738096'
    else:
        color = {'STRONG': '#168A55', 'MODERATE': '#53657D', 'NO_SIGNAL': '#7C8A9D'}.get(s, '#7C8A9D')
        count_color = '#7C8A9D'

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
        colors = ['#4EA1FF', '#22C77A', '#6672FF']
        text_color = '#F3F6FA'
        tick_x_color = '#A8B3C3'
        tick_y_color = '#F3F6FA'
        grid_color = 'rgba(255, 255, 255, 0.08)'
        dash_color = '#F3F6FA'
    else:
        colors = ['#1769AA', '#168A55', '#4F46E5']
        text_color = '#172033'
        tick_x_color = '#53657D'
        tick_y_color = '#172033'
        grid_color = 'rgba(15, 23, 42, 0.08)'
        dash_color = '#172033'

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
            range=[0, 1.25], title=None,
            tickfont=dict(size=12, family='JetBrains Mono', color=tick_x_color),
            gridcolor=grid_color, showgrid=True
        ),
        yaxis=dict(
            title=None,
            tickfont=dict(size=13, family='Inter', color=tick_y_color)
        ),
        height=200, margin=dict(l=6, r=130, t=38, b=8),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False, font=dict(family='Inter'),
    )
    st.plotly_chart(fig, key=key)


def stratum_status_badge(is_exploratory: bool, theme: str = "light") -> str:
    """Render subtle status badge for ATC strata: [Reportable] or [Exploratory]."""
    is_dark = (theme == "dark")
    if is_exploratory:
        bg = "rgba(245, 158, 11, 0.12)" if is_dark else "rgba(245, 158, 11, 0.10)"
        color = "#FCD34D" if is_dark else "#B45309"
        border = "rgba(245, 158, 11, 0.40)" if is_dark else "rgba(217, 119, 6, 0.35)"
        return f'<span style="display:inline-block; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600; font-family:var(--font-mono); background:{bg}; color:{color}; border:1px solid {border};">Exploratory</span>'
    else:
        bg = "rgba(16, 185, 129, 0.12)" if is_dark else "rgba(16, 185, 129, 0.10)"
        color = "#6EE7B7" if is_dark else "#047857"
        border = "rgba(16, 185, 129, 0.40)" if is_dark else "rgba(5, 150, 105, 0.35)"
        return f'<span style="display:inline-block; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600; font-family:var(--font-mono); background:{bg}; color:{color}; border:1px solid {border};">Reportable</span>'


def render_therapeutic_stratification_table(
    strat_data: dict,
    title: str = "Performance by Therapeutic Area (WHO ATC Level 1)",
    theme: str = "light",
) -> None:
    """
    Render a responsive, theme-aware table of WHO ATC Level 1 therapeutic area strata.
    Displays Code, Therapeutic Area, n, Status ([Reportable] vs [Exploratory]),
    Strict F1 (with TP/FP/TN/FN), Lenient F1 (with TP/FP/TN/FN), and Wilson CI details.
    Includes honest scientific notes on small-sample strata (n < 5).
    """
    if not strat_data or "strata" not in strat_data:
        st.info("No therapeutic area stratification data available.")
        return

    strata = strat_data["strata"]
    coverage = strat_data.get("coverage", {})

    st.markdown(f'<div class="pg-section-label">{title}</div>', unsafe_allow_html=True)

    rows_html = []
    for code, s_info in sorted(strata.items()):
        name = s_info.get("name", f"Stratum {code}")
        n = s_info.get("n", 0)
        is_expl = s_info.get("is_exploratory", n < 5)
        status_html = stratum_status_badge(is_expl, theme=theme)

        st_tier = s_info.get("strict", {})
        ln_tier = s_info.get("lenient", {})

        st_f1 = st_tier.get("f1")
        st_f1_str = f"{st_f1:.3f}" if st_f1 is not None else '<span style="color:var(--text-muted);">N/A</span>'

        ln_f1 = ln_tier.get("f1")
        ln_f1_str = f"{ln_f1:.3f}" if ln_f1 is not None else '<span style="color:var(--text-muted);">N/A</span>'

        st_mat = f"TP:{st_tier.get('TP', 0)} FP:{st_tier.get('FP', 0)} TN:{st_tier.get('TN', 0)} FN:{st_tier.get('FN', 0)}"
        ln_mat = f"TP:{ln_tier.get('TP', 0)} FP:{ln_tier.get('FP', 0)} TN:{ln_tier.get('TN', 0)} FN:{ln_tier.get('FN', 0)}"

        rows_html.append(
            f'<tr>'
            f'<td style="font-family:var(--font-mono); font-weight:700; text-align:center; color:var(--text);">{code}</td>'
            f'<td style="font-weight:600; color:var(--text);">{name}</td>'
            f'<td class="num" style="text-align:center; font-weight:600;">{n}</td>'
            f'<td style="text-align:center;">{status_html}</td>'
            f'<td class="num" style="text-align:right; font-weight:700;">'
            f'<div>{st_f1_str}</div>'
            f'<div style="font-size:11px; font-weight:400; color:var(--text-muted); font-family:var(--font-mono);">{st_mat}</div>'
            f'</td>'
            f'<td class="num" style="text-align:right; font-weight:700;">'
            f'<div>{ln_f1_str}</div>'
            f'<div style="font-size:11px; font-weight:400; color:var(--text-muted); font-family:var(--font-mono);">{ln_mat}</div>'
            f'</td>'
            f'</tr>'
        )

    table_body = "".join(rows_html)
    cov_pct = coverage.get("resolution_percentage", 100.0) if coverage else 100.0
    total_drugs = coverage.get("total_unique_drugs", len(strata)) if coverage else len(strata)

    table_full = (
        f'<div class="pg-card" style="margin-bottom:14px;">'
        f'<div class="pg-table-container" style="margin-bottom:0px;">'
        f'<table class="pg-cmp-table">'
        f'<thead><tr>'
        f'<th style="text-align:center; width:60px;">ATC L1</th>'
        f'<th>Therapeutic Area</th>'
        f'<th style="text-align:center; width:50px;">n</th>'
        f'<th style="text-align:center; width:120px;">Status</th>'
        f'<th style="text-align:right; width:170px;">Strict F1 (Counts)</th>'
        f'<th style="text-align:right; width:170px;">Lenient F1 (Counts)</th>'
        f'</tr></thead>'
        f'<tbody>{table_body}</tbody>'
        f'</table>'
        f'</div>'
        f'</div>'
    )
    st.markdown(table_full, unsafe_allow_html=True)

    expl_text = (
        '<strong>Sample Size & Confidence Interval Discipline:</strong> '
        'Strata marked <span style="font-family:var(--font-mono); font-size:12px; font-weight:600;">[Exploratory]</span> have <em>n</em> &lt; 5 pairs. '
        'Analytical Wilson score 95% confidence intervals on small sample sizes are inherently wide '
        '(e.g., a single observation 1/1 yields Wilson 95% CI [0.207, 1.000]), making metric ranking uninformative. '
        'ATC classification reflects drug therapeutic category, not patient-level indication or confounding adjustment.'
    )
    if coverage and "resolution_percentage" in coverage:
        expl_text += f'<br><span style="color:var(--text-muted); font-size:12px;">ATC Annotation Coverage: {cov_pct:.1f}% ({total_drugs} unique benchmark drugs resolved).</span>'

    st.markdown(
        f'<div class="pg-callout" style="margin-top:0px; margin-bottom:16px;">{expl_text}</div>',
        unsafe_allow_html=True,
    )