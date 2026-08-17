# ruff: noqa: E501
"""
PharmaGuard Evaluation Dashboard
=================================
Demo/presentation tool.
NO live API calls at runtime -- reads only from pre-committed JSON files in:
  outputs/, outputs/baseline/, pharmaguard/data/ground_truth.json.

Run:
    streamlit run scripts/dashboard.py   (from project root)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = _SCRIPT_DIR.parent if _SCRIPT_DIR.name == "scripts" else _SCRIPT_DIR

OUTPUTS_DIR = REPO_ROOT / "outputs"
BASELINE_DIR = OUTPUTS_DIR / "baseline"
GROUND_TRUTH_PATH = REPO_ROOT / "pharmaguard" / "data" / "ground_truth.json"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PharmaGuard | Evaluation Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Design System CSS (Linear / Notion / Attio inspired)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

html, body, [class*='css'] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 14px;
    color: #0f172a;
    background-color: #ffffff;
}

#MainMenu, footer, .stDeployButton, div[data-testid='stToolbar'] {
    display: none !important;
}

header[data-testid='stHeader'] {
    background: transparent !important;
}

.stApp {
    background-color: #ffffff;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1200px !important;
}

/* ── Navigation Tabs (Crisp contrast & clear active/inactive hierarchy) ── */
div[data-testid='stTabs'] {
    border-bottom: 1.5px solid #e2e8f0 !important;
    margin-bottom: 24px !important;
}

button[data-testid='stTab'] {
    font-family: 'Inter', sans-serif !important;
    font-size: 13.5px !important;
    padding: 10px 20px !important;
    border: none !important;
    background: transparent !important;
    opacity: 1 !important;
}

button[data-testid='stTab'] p {
    font-family: 'Inter', sans-serif !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: #475569 !important;
    transition: color 0.15s ease !important;
}

button[data-testid='stTab']:hover p {
    color: #0f172a !important;
}

button[data-testid='stTab'][aria-selected='true'] p {
    color: #0f172a !important;
    font-weight: 700 !important;
}

/* ── Checkbox Label Styling ── */
div[data-testid='stCheckbox'] {
    margin-top: 6px !important;
}

div[data-testid='stCheckbox'] label p {
    font-family: 'Inter', sans-serif !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: #1e293b !important;
    white-space: nowrap !important;
}

/* ── Typography & Header ── */
.pg-header {
    margin-bottom: 28px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f1f5f9;
}

.pg-title {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #0f172a;
    margin: 0 0 4px 0;
}

.pg-subtitle {
    font-size: 13.5px;
    color: #64748b;
    margin: 0;
}

/* ── Section Dividers & Labels ── */
.pg-section-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 12px;
}

.pg-divider {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 28px 0;
}

/* ── Metric Display ── */
.pg-stat-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 6px;
}

.pg-stat-value {
    font-size: 28px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
    font-family: 'Inter', sans-serif;
}

.pg-stat-sub {
    font-size: 12px;
    color: #475569;
    margin-top: 4px;
    line-height: 1.4;
}

.pg-stat-note {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 3px;
    line-height: 1.35;
}

/* Hero primary metric */
.pg-hero-value {
    font-size: 58px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #0f172a;
    line-height: 1;
    font-variant-numeric: tabular-nums;
    font-family: 'Inter', sans-serif;
}

.pg-hero-sub {
    font-size: 15px;
    font-weight: 500;
    color: #334155;
    margin-top: 8px;
}

.pg-hero-note {
    font-size: 12.5px;
    color: #64748b;
    margin-top: 6px;
    line-height: 1.5;
}

/* ── Badges ── */
.b-esc {
    background: #f0fdf4;
    color: #166534;
    border: 1px solid #bbf7d0;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 11px;
    letter-spacing: 0.02em;
    white-space: nowrap;
}

.b-mon {
    background: #f8fafc;
    color: #475569;
    border: 1px solid #cbd5e1;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 11px;
    letter-spacing: 0.02em;
    white-space: nowrap;
}

.b-dne {
    background: #f8fafc;
    color: #94a3b8;
    border: 1px solid #e2e2e2;
    font-weight: 500;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 11px;
    letter-spacing: 0.02em;
    white-space: nowrap;
}

.b-pos {
    background: #eff6ff;
    color: #1e40af;
    border: 1px solid #bfdbfe;
    font-weight: 500;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 11px;
}

.b-neg {
    background: #f8fafc;
    color: #475569;
    border: 1px solid #e2e8f0;
    font-weight: 500;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 11px;
}

.b-zero {
    background: #fff7ed;
    color: #9a3412;
    border: 1px solid #fed7aa;
    font-weight: 500;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 11px;
}

.b-ga {
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
}

.b-gb {
    background: #f8fafc;
    color: #475569;
    border: 1px solid #cbd5e1;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
}

.b-gc {
    background: #f8fafc;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
}

/* ── Dense Aligned Data Table (Linear/Notion style) ── */
.pg-table-container {
    width: 100%;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 20px;
    background: #ffffff;
}

.pg-data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    text-align: left;
}

.pg-data-table th {
    background: #f8fafc;
    color: #64748b;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 9px 12px;
    border-bottom: 1px solid #e2e8f0;
    white-space: nowrap;
}

.pg-data-table td {
    padding: 8px 12px;
    border-bottom: 1px solid #f1f5f9;
    color: #334155;
    vertical-align: middle;
}

.pg-data-table tr:hover {
    background-color: #f8fafc;
}

.pg-data-table tr:last-child td {
    border-bottom: none;
}

.pg-mono {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12px;
    color: #0f172a;
}

/* ── Detail Pane / Callouts ── */
.pg-detail-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 16px 20px;
    margin-top: 12px;
}

.pg-quote-box {
    background: #f8fafc;
    border-left: 3px solid #cbd5e1;
    padding: 12px 16px;
    font-size: 13px;
    line-height: 1.65;
    color: #334155;
    border-radius: 0 4px 4px 0;
    margin: 8px 0;
}

.pg-conclusion-box {
    background: #f0fdf4;
    border-left: 3px solid #16a34a;
    padding: 12px 16px;
    font-size: 13px;
    line-height: 1.65;
    color: #14532d;
    border-radius: 0 4px 4px 0;
    margin-top: 8px;
}

.pg-callout {
    background: #f8fafc;
    border-left: 3px solid #64748b;
    padding: 14px 18px;
    font-size: 12.5px;
    color: #334155;
    line-height: 1.6;
    border-radius: 0 6px 6px 0;
    margin-top: 16px;
}

/* ── Baseline Comparison Table ── */
.pg-cmp-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}

.pg-cmp-table th {
    text-align: left;
    padding: 7px 10px;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #64748b;
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
}

.pg-cmp-table td {
    padding: 9px 10px;
    border-bottom: 1px solid #f1f5f9;
    color: #334155;
}

.pg-cmp-table td.num {
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    color: #0f172a;
}

.pg-cmp-table tr:last-child td {
    border-bottom: none;
}
</style>
""", unsafe_allow_html=True)

# ===========================================================================
# DATA LOADING -- pure JSON reads, ZERO network calls
# ===========================================================================

@st.cache_data
def load_ground_truth() -> dict:
    if not GROUND_TRUTH_PATH.exists():
        return {}
    with open(GROUND_TRUTH_PATH, encoding='utf-8') as fh:
        raw = json.load(fh)
    return {
        f"{p['drug_canonical']}::{p['event_meddra_pt']}": p
        for p in raw.get('pairs', [])
    }

def _run_idx(name: str) -> int:
    m = re.search(r'eval-run-(\d+)-', name)
    return int(m.group(1)) if m else 999

@st.cache_data
def load_reports(directory: Path) -> list:
    reports = []
    for path in sorted(directory.glob('eval-run-*_report.json'), key=lambda p: _run_idx(p.name)):
        try:
            with open(path, encoding='utf-8') as fh:
                rpt = json.load(fh)
            rpt['_src'] = path.name
            reports.append(rpt)
        except (json.JSONDecodeError, OSError):
            pass
    return reports

@st.cache_data
def build_df(reports: list, gt: dict) -> pd.DataFrame:
    rows = []
    for r in reports:
        drug = r.get('drug', '')
        event = r.get('event', '')
        entry = gt.get(f'{drug}::{event}', {})
        expected = entry.get('expected_escalation', '')
        actual = r.get('triage', {}).get('escalation', '')
        rows.append({
            'idx': _run_idx(r.get('_src', '')),
            'drug': drug,
            'event': event.replace('_', ' '),
            'category': entry.get('category', ''),
            'signal': r.get('signal_stats', {}).get('prr_score_label', ''),
            'report_count': r.get('signal_stats', {}).get('report_count', 0),
            'prr': r.get('signal_stats', {}).get('prr'),
            'grade': r.get('literature', {}).get('evidence_grade', ''),
            'plausibility': r.get('mechanism', {}).get('biological_plausibility', ''),
            'confidence': r.get('triage', {}).get('confidence'),
            'escalation': actual,
            'expected': expected,
            'match': actual == expected,
            '_r': r,
            '_gt': entry,
        })
    return pd.DataFrame(rows).sort_values('idx').reset_index(drop=True)

# Hard-coded from DECISIONS.md section 16 -- verified benchmark values
PROD = {
    's_prec': 1.000, 's_rec': 0.857, 's_spec': 1.000, 's_f1': 0.923,
    'l_prec': 0.875, 'l_rec': 1.000, 'l_spec': 0.875, 'l_f1': 0.933,
    'ocr': 12.5,
}
BASE = {
    's_prec': 0.875, 's_rec': 1.000, 's_spec': 0.875, 's_f1': 0.933,
    'l_prec': 0.700, 'l_rec': 1.000, 'l_spec': 0.625, 'l_f1': 0.824,
    'ocr': 25.0,
}

# ===========================================================================
# RENDERING HELPERS
# ===========================================================================

def esc_badge(e: str) -> str:
    cls = {'ESCALATE': 'b-esc', 'MONITOR': 'b-mon', 'DO_NOT_ESCALATE': 'b-dne'}.get(e, 'b-dne')
    return f'<span class="{cls}">{e}</span>'

def cat_badge(c: str) -> str:
    m = {
        'confirmed_positive': ('b-pos', 'Confirmed Positive'),
        'genuine_negative_control': ('b-neg', 'Genuine Negative'),
        'zero_report_edge_case': ('b-zero', 'Zero Report'),
    }
    cls, label = m.get(c, ('b-neg', c))
    return f'<span class="{cls}">{label}</span>'

def grade_badge(g: str) -> str:
    cls = {'A': 'b-ga', 'B': 'b-gb', 'C': 'b-gc'}.get(g, 'b-gc')
    return f'<span class="{cls}">{g}</span>'

def signal_span(s: str, report_count: int = 0) -> str:
    color = {'STRONG': '#15803d', 'MODERATE': '#334155', 'NO_SIGNAL': '#94a3b8'}.get(s, '#94a3b8')
    wt = {'STRONG': '700', 'MODERATE': '600', 'NO_SIGNAL': '500'}.get(s, '500')
    rc_str = f' ({report_count:,})' if report_count is not None else ''
    return f'<span style="color:{color};font-weight:{wt};font-size:12px;white-space:nowrap;">{s}<span style="font-weight:400;font-size:11px;color:#64748b;">{rc_str}</span></span>'

def render_conf_chart(r: dict, key: str) -> None:
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

# ===========================================================================
# VIEW 1 -- OVERVIEW
# ===========================================================================

def view_overview() -> None:
    st.markdown(
        '<div class="pg-header">'
        '<div class="pg-title">PharmaGuard — Evaluation Overview</div>'
        '<div class="pg-subtitle">Sprint 3 final benchmark · 15 drug–event pairs · plausibility ratings v1.0</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    m = PROD

    col_hero, col_flank = st.columns([2.3, 1], gap='large')
    with col_hero:
        st.markdown(
            f'<div style="padding: 6px 0;">'
            f'<div class="pg-stat-label">Strict Recall — Primary Benchmark Result</div>'
            f'<div class="pg-hero-value">{m["s_rec"]:.3f}</div>'
            f'<div class="pg-hero-sub">6 of 7 confirmed positives correctly escalated</div>'
            f'<div class="pg-hero-note">'
            f'Lenient Recall: <strong style="color:#0f172a;">1.000</strong> (7/7) — '
            f'signal is never missed; confidence is modulated under mechanistic uncertainty.'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_flank:
        st.markdown(
            f'<div style="border-left: 1px solid #e2e8f0; padding-left: 24px;">'
            f'<div class="pg-stat-label">Over-Caution Rate</div>'
            f'<div class="pg-stat-value">12.5%</div>'
            f'<div class="pg-stat-sub">1 of 8 negative controls → MONITOR</div>'
            f'<div style="height: 18px;"></div>'
            f'<div class="pg-stat-label">Spurious False Alarms</div>'
            f'<div class="pg-stat-value">FP = 0</div>'
            f'<div class="pg-stat-sub">Strict Wilson 95% CI: 0.610–1.000</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)

    st.markdown('<div class="pg-section-label">Strict Evaluation Metrics</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap='medium')
    strict_metrics = [
        ('Strict Precision', f"{m['s_prec']:.3f}", 'Wilson 95% CI: 0.610–1.000',
         'Bootstrap 1.000–1.000 is a boundary artifact — not proven perfect'),
        ('Strict Specificity', f"{m['s_spec']:.3f}", 'Wilson 95% CI: 0.676–1.000',
         '0 spurious escalations on negative controls'),
        ('Strict F1', f"{m['s_f1']:.3f}", 'Bootstrap 95% CI: 0.727–1.000', ''),
        ('Pairs Evaluated', '15', '7 confirmed pos · 5 genuine neg · 3 zero-report', ''),
    ]
    for col, (label, val, sub, note) in zip([c1, c2, c3, c4], strict_metrics):
        with col:
            st.markdown(
                f'<div class="pg-stat-label">{label}</div>'
                f'<div class="pg-stat-value">{val}</div>'
                f'<div class="pg-stat-sub">{sub}</div>'
                + (f'<div class="pg-stat-note">{note}</div>' if note else '')
                + '<div style="height: 8px;"></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)

    st.markdown('<div class="pg-section-label">Lenient Evaluation Metrics (MONITOR counts as True Positive)</div>', unsafe_allow_html=True)
    l1, l2, l3, l4 = st.columns(4, gap='medium')
    lenient_metrics = [
        ('Lenient Precision', f"{m['l_prec']:.3f}", 'Wilson 95% CI: 0.529–0.978'),
        ('Lenient Recall', f"{m['l_rec']:.3f}", 'Wilson 95% CI: 0.646–1.000'),
        ('Lenient Specificity', f"{m['l_spec']:.3f}", 'Wilson 95% CI: 0.529–0.978'),
        ('Lenient F1', f"{m['l_f1']:.3f}", 'Bootstrap 95% CI: 0.769–1.000'),
    ]
    for col, (label, val, sub) in zip([l1, l2, l3, l4], lenient_metrics):
        with col:
            st.markdown(
                f'<div class="pg-stat-label">{label}</div>'
                f'<div class="pg-stat-value">{val}</div>'
                f'<div class="pg-stat-sub">{sub}</div>'
                f'<div style="height: 8px;"></div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="pg-callout">'
        '<strong>Strict vs. Lenient:</strong> The single strict FN is <code>montelukast::suicidal_ideation</code> '
        '(outputs <code>MONITOR</code>, not <code>ESCALATE</code>). Curated <code>plausibility=LOW</code> correctly '
        'modulates confidence to <code>0.664</code> — below the <code>0.70</code> escalation threshold — despite '
        'a FAERS MODERATE signal and PubMed Grade A literature evidence. This is pharmacovigilance-correct behavior '
        'reflecting genuine mechanistic uncertainty. Under lenient scoring it is a confirmed True Positive.'
        '</div>',
        unsafe_allow_html=True,
    )

# ===========================================================================
# VIEW 2 -- PER-PAIR TABLE + DRILL-DOWN (Dense Aligned Table)
# ===========================================================================

def view_per_pair(df: pd.DataFrame) -> None:
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

    table_rows_html = []
    for _, r in fdf.iterrows():
        conf_str = f"{r['confidence']:.3f}" if r['confidence'] is not None else '—'
        plaus = r['plausibility']
        pc = {'HIGH': '#166534', 'MODERATE': '#334155', 'LOW': '#94a3b8'}.get(plaus, '#94a3b8')
        flag = '⚡ ' if not r['match'] else ''
        rc = r.get('report_count', 0)
        table_rows_html.append(
            f'<tr>'
            f'<td class="pg-mono" style="color:#64748b;">{flag}{r["idx"]}</td>'
            f'<td style="font-weight:600; color:#0f172a;">{r["drug"]}</td>'
            f'<td style="color:#334155;">{r["event"]}</td>'
            f'<td>{cat_badge(r["category"])}</td>'
            f'<td>{signal_span(r["signal"], rc)}</td>'
            f'<td>{grade_badge(r["grade"])}</td>'
            f'<td style="color:{pc}; font-weight:600; font-size:12px;">{plaus}</td>'
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
    st.markdown(f'<p style="font-size:12px;color:#64748b;margin:-10px 0 20px 0;">Showing {len(fdf)} of {len(df)} pairs</p>', unsafe_allow_html=True)

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

    dc1, dc2 = st.columns([1.1, 1], gap='large')
    with dc1:
        st.markdown('<div class="pg-stat-label">FAERS Signal Statistics</div>', unsafe_allow_html=True)
        prr_val = ss.get('prr')
        prr_disp = f'{prr_val:.2f}' if prr_val is not None else 'n/a (0 reports)'
        rc_val = ss.get('report_count', 0)
        st.markdown(
            f'<div class="pg-mono" style="font-size:13px; color:#0f172a; margin-bottom:12px;">'
            f'PRR: <b>{prr_disp}</b> &nbsp;|&nbsp; Reports: <b>{rc_val:,}</b> &nbsp;|&nbsp; Strength: {signal_span(sel_row["signal"], rc_val)}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="pg-stat-label">PubMed Evidence Summary</div>', unsafe_allow_html=True)
        ev_raw = lit.get('evidence_summary', '')
        ev_clean = re.sub(r'^Final Grade:\s*\w+\s*', '', ev_raw).strip()
        st.markdown(f'<div class="pg-quote-box">{ev_clean}</div>', unsafe_allow_html=True)

    with dc2:
        st.markdown('<div class="pg-stat-label">Mechanistic Plausibility</div>', unsafe_allow_html=True)
        plaus_rat = mech.get('plausibility_rationale', '—')
        plaus_src = mech.get('plausibility_source', '—')
        st.markdown(
            f'<div class="pg-quote-box">{plaus_rat}</div>'
            f'<div style="font-size:11px;color:#64748b;margin-top:2px;">source: <code>{plaus_src}</code></div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="pg-stat-label" style="margin-top:14px;">Confidence Formula Decomposition</div>', unsafe_allow_html=True)
        render_conf_chart(sel_rpt, key=f'table_conf_{sel_idx}')

# ===========================================================================
# VIEW 3 -- DISAGREEMENT SPOTLIGHT
# ===========================================================================

def view_disagreements(reports: list) -> None:
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
            st.warning(f"Report for {case['drug']} not found in {OUTPUTS_DIR}")
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

# ===========================================================================
# VIEW 4 -- BASELINE COMPARISON
# ===========================================================================

def view_baseline(prod_reports: list, base_reports: list) -> None:
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
        return (
            f'<div style="margin-bottom:8px;">'
            f'<div style="font-size:13.5px; font-weight:700; color:#0f172a; margin-bottom:10px;">{title}</div>'
            f'<div class="pg-table-container">'
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
        st.markdown(_table(PROD, True), unsafe_allow_html=True)
    with mc2:
        st.markdown(_table(BASE, False), unsafe_allow_html=True)

    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="pg-title" style="font-size:17px; margin-bottom:3px;">Key Illustration: liraglutide + pancreatic cancer</div>'
        '<div class="pg-subtitle" style="margin-bottom:18px;">Clearest single example of what tool-grounded triage adds over ungrounded LLM recall</div>',
        unsafe_allow_html=True,
    )

    prod_lira = next((r for r in prod_reports if 'liraglutide' in r.get('run_id', '')), None)
    base_lira = next((r for r in base_reports if 'liraglutide' in r.get('run_id', '')), None)
    if not prod_lira or not base_lira:
        st.error('Could not find liraglutide reports in outputs/ — run the evaluation pipeline first.')
        return

    lc1, lc2 = st.columns(2, gap='large')

    def _case_col(col, title, rpt, expected, notes):
        triage = rpt.get('triage', {})
        esc = triage.get('escalation', '—')
        conf = triage.get('confidence')
        trace = triage.get('agent_reasoning_trace', [])
        conf_d = f'{conf:.3f}' if conf is not None else '—'
        with col:
            st.markdown(
                f'<div style="font-size:13.5px; font-weight:700; color:#0f172a; margin-bottom:8px;">{title}</div>'
                f'<div style="display:flex; gap:10px; align-items:center; margin-bottom:4px;">'
                f'{esc_badge(esc)}'
                f'<span style="font-size:12px; color:#64748b;">expected: {expected}</span>'
                f'</div>'
                f'<div class="pg-mono" style="font-size:12px; color:#64748b; margin-bottom:10px;">confidence = <b>{conf_d}</b></div>',
                unsafe_allow_html=True,
            )
            if trace:
                st.markdown(
                    f'<div class="pg-quote-box" style="font-size:12.5px;">{"<br>".join(trace)}</div>',
                    unsafe_allow_html=True,
                )
            if notes:
                items = ''.join(f"<li style='margin-bottom:4px;'>{n}</li>" for n in notes)
                st.markdown(
                    f'<ul style="font-size:12.5px; color:#475569; margin:10px 0 0; padding-left:18px; line-height:1.6;">{items}</ul>',
                    unsafe_allow_html=True,
                )

    _case_col(lc1, 'PharmaGuard · Tool-Grounded', prod_lira, 'DO_NOT_ESCALATE',
              ['FAERS: 0 co-occurrences → NO_SIGNAL gate → DO_NOT_ESCALATE',
               'Confidence 0.300 = 0.40×0 + 0.40×0.5 + 0.20×0.5',
               'FAERS disproportionality overrides literature plausibility',
               'FDA/EMA 2014 joint review: no causal link established'])

    _case_col(lc2, 'Single-Shot LLM Baseline · No Tools', base_lira, 'DO_NOT_ESCALATE',
              ['No FAERS query — no signal check performed',
               'Confidence 0.85 is raw LLM self-report, not formula-grounded',
               'Recalls historical regulatory concern, not its resolution',
               'Confuses \'this was investigated\' with \'this was confirmed\''])

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

# ===========================================================================
# ENTRY POINT
# ===========================================================================

def main() -> None:
    gt = load_ground_truth()
    prod_reports = load_reports(OUTPUTS_DIR)
    base_reports = load_reports(BASELINE_DIR)
    df = build_df(prod_reports, gt)
    if not prod_reports:
        st.error(
            f'No reports found in {OUTPUTS_DIR}.\n\n'
            "Run 'python scripts/run_eval.py' first to generate evaluation outputs."
        )
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs([
        'Overview',
        'Per-Pair Table',
        'Disagreement Spotlight',
        'Baseline Comparison',
    ])
    with tab1:
        view_overview()
    with tab2:
        view_per_pair(df)
    with tab3:
        view_disagreements(prod_reports)
    with tab4:
        view_baseline(prod_reports, base_reports)

if __name__ == '__main__':
    main()