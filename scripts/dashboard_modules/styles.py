"""
PharmaGuard Dashboard Styles
============================
Design system and CSS injection for the Streamlit dashboard (Linear / Notion inspired).
"""
from __future__ import annotations

import streamlit as st


def inject_dashboard_styles() -> None:
    """Inject customized high-contrast CSS styling into Streamlit DOM."""
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
