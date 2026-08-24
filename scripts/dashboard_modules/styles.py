"""
PharmaGuard Dashboard Styles & Theme System
===========================================
High-contrast, dual-theme CSS design system for the Streamlit evaluation dashboard.
Supports Light, Dark, and System modes with Linear/Vercel-inspired typography and micro-depth cues.
"""
from __future__ import annotations

import streamlit as st


def get_theme_css(theme: str = "light") -> str:
    """Generate scoped CSS variables and rules based on active theme."""
    is_dark = (theme == "dark")
    is_system = (theme == "system")

    # Semantic design tokens
    if is_dark:
        root_vars = """
        --pg-bg: #090d16;
        --pg-app-bg: #090d16;
        --pg-card-bg: #111827;
        --pg-card-bg-subtle: #1a2234;
        --pg-card-border: rgba(51, 65, 85, 0.7);
        --pg-card-border-hover: rgba(99, 102, 241, 0.5);
        --pg-text-primary: #f8fafc;
        --pg-text-secondary: #cbd5e1;
        --pg-text-muted: #818cf8;
        --pg-text-dim: #94a3b8;
        --pg-accent: #6366f1;
        --pg-accent-glow: rgba(99, 102, 241, 0.18);
        --pg-accent-border: rgba(99, 102, 241, 0.4);
        --pg-divider: #1e293b;
        --pg-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
        --pg-shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.25);
        --pg-quote-bg: rgba(26, 34, 52, 0.6);
        --pg-quote-border: #475569;
        --pg-quote-text: #e2e8f0;
        --pg-conclusion-bg: rgba(20, 83, 45, 0.2);
        --pg-conclusion-border: #22c55e;
        --pg-conclusion-text: #bbf7d0;
        --pg-callout-bg: rgba(30, 41, 59, 0.6);
        --pg-callout-border: #6366f1;
        --pg-table-header-bg: #151d2e;
        --pg-table-header-text: #94a3b8;
        --pg-table-row-hover: #172033;
        --pg-table-row-alt: #0e1422;
        --pg-input-bg: #111827;
        --pg-input-border: #334155;
        --pg-input-text: #f8fafc;
        """
    else:
        root_vars = """
        --pg-bg: #f8fafc;
        --pg-app-bg: #ffffff;
        --pg-card-bg: #ffffff;
        --pg-card-bg-subtle: #f8fafc;
        --pg-card-border: #e2e8f0;
        --pg-card-border-hover: rgba(79, 70, 229, 0.4);
        --pg-text-primary: #0f172a;
        --pg-text-secondary: #334155;
        --pg-text-muted: #4f46e5;
        --pg-text-dim: #64748b;
        --pg-accent: #4f46e5;
        --pg-accent-glow: rgba(79, 70, 229, 0.08);
        --pg-accent-border: rgba(79, 70, 229, 0.25);
        --pg-divider: #e2e8f0;
        --pg-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        --pg-shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.04);
        --pg-quote-bg: #f8fafc;
        --pg-quote-border: #cbd5e1;
        --pg-quote-text: #334155;
        --pg-conclusion-bg: #f0fdf4;
        --pg-conclusion-border: #16a34a;
        --pg-conclusion-text: #14532d;
        --pg-callout-bg: #f8fafc;
        --pg-callout-border: #4f46e5;
        --pg-table-header-bg: #f8fafc;
        --pg-table-header-text: #475569;
        --pg-table-row-hover: #f1f5f9;
        --pg-table-row-alt: #ffffff;
        --pg-input-bg: #ffffff;
        --pg-input-border: #cbd5e1;
        --pg-input-text: #0f172a;
        """

    system_media_query = ""
    if is_system:
        system_media_query = """
        @media (prefers-color-scheme: dark) {
            :root {
                --pg-bg: #090d16;
                --pg-app-bg: #090d16;
                --pg-card-bg: #111827;
                --pg-card-bg-subtle: #1a2234;
                --pg-card-border: rgba(51, 65, 85, 0.7);
                --pg-card-border-hover: rgba(99, 102, 241, 0.5);
                --pg-text-primary: #f8fafc;
                --pg-text-secondary: #cbd5e1;
                --pg-text-muted: #818cf8;
                --pg-text-dim: #94a3b8;
                --pg-accent: #6366f1;
                --pg-accent-glow: rgba(99, 102, 241, 0.18);
                --pg-accent-border: rgba(99, 102, 241, 0.4);
                --pg-divider: #1e293b;
                --pg-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
                --pg-shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.25);
                --pg-quote-bg: rgba(26, 34, 52, 0.6);
                --pg-quote-border: #475569;
                --pg-quote-text: #e2e8f0;
                --pg-conclusion-bg: rgba(20, 83, 45, 0.2);
                --pg-conclusion-border: #22c55e;
                --pg-conclusion-text: #bbf7d0;
                --pg-callout-bg: rgba(30, 41, 59, 0.6);
                --pg-callout-border: #6366f1;
                --pg-table-header-bg: #151d2e;
                --pg-table-header-text: #94a3b8;
                --pg-table-row-hover: #172033;
                --pg-table-row-alt: #0e1422;
                --pg-input-bg: #111827;
                --pg-input-border: #334155;
                --pg-input-text: #f8fafc;
            }
            .stApp {
                background-color: var(--pg-bg) !important;
            }
            body, [class*='css'] {
                color: var(--pg-text-primary) !important;
            }
        }
        """

    badge_esc_bg = 'rgba(34, 197, 94, 0.15)' if is_dark else '#f0fdf4'
    badge_esc_txt = '#4ade80' if is_dark else '#166534'
    badge_esc_bd = 'rgba(74, 222, 128, 0.35)' if is_dark else '#bbf7d0'

    badge_mon_bg = 'rgba(148, 163, 184, 0.15)' if is_dark else '#f8fafc'
    badge_mon_txt = '#cbd5e1' if is_dark else '#475569'
    badge_mon_bd = 'rgba(148, 163, 184, 0.35)' if is_dark else '#cbd5e1'

    badge_dne_bg = 'rgba(71, 85, 105, 0.2)' if is_dark else '#f8fafc'
    badge_dne_txt = '#94a3b8' if is_dark else '#94a3b8'
    badge_dne_bd = 'rgba(71, 85, 105, 0.4)' if is_dark else '#e2e8f0'

    badge_pos_bg = 'rgba(59, 130, 246, 0.15)' if is_dark else '#eff6ff'
    badge_pos_txt = '#60a5fa' if is_dark else '#1e40af'
    badge_pos_bd = 'rgba(96, 165, 250, 0.35)' if is_dark else '#bfdbfe'

    badge_neg_bg = 'rgba(148, 163, 184, 0.12)' if is_dark else '#f8fafc'
    badge_neg_txt = '#cbd5e1' if is_dark else '#475569'
    badge_neg_bd = 'rgba(148, 163, 184, 0.3)' if is_dark else '#e2e8f0'

    badge_zero_bg = 'rgba(249, 115, 22, 0.15)' if is_dark else '#fff7ed'
    badge_zero_txt = '#fb923c' if is_dark else '#9a3412'
    badge_zero_bd = 'rgba(251, 146, 60, 0.35)' if is_dark else '#fed7aa'

    badge_ga_bg = 'rgba(59, 130, 246, 0.2)' if is_dark else '#eff6ff'
    badge_ga_txt = '#93c5fd' if is_dark else '#1d4ed8'
    badge_ga_bd = 'rgba(147, 197, 253, 0.4)' if is_dark else '#bfdbfe'

    badge_gb_bg = 'rgba(148, 163, 184, 0.15)' if is_dark else '#f8fafc'
    badge_gb_txt = '#cbd5e1' if is_dark else '#475569'
    badge_gb_bd = 'rgba(148, 163, 184, 0.3)' if is_dark else '#cbd5e1'

    badge_gc_bg = 'rgba(71, 85, 105, 0.2)' if is_dark else '#f8fafc'
    badge_gc_txt = '#94a3b8' if is_dark else '#94a3b8'
    badge_gc_bd = 'rgba(71, 85, 105, 0.3)' if is_dark else '#e2e8f0'

    css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {{
    {root_vars}
}}

{system_media_query}

/* ── Base Setup ── */
html, body, [class*='css'] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 15px;
    color: var(--pg-text-primary);
    background-color: var(--pg-bg);
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
}}

/* Completely disable header overlay interception */
#MainMenu, footer, .stDeployButton, div[data-testid='stToolbar'], header[data-testid='stHeader'] {{
    display: none !important;
}}

.stApp {{
    background-color: var(--pg-bg) !important;
    transition: background-color 0.2s ease, color 0.2s ease;
}}

.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 1240px !important;
}}

/* ── Streamlit Form Control Styling (Theme Consistent) ── */
div[data-testid='stSelectbox'] label p,
div[data-testid='stSegmentedControl'] label p {{
    font-family: 'Inter', sans-serif !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    color: var(--pg-text-secondary) !important;
}}

div[data-testid='stSelectbox'] > div > div {{
    background-color: var(--pg-card-bg) !important;
    color: var(--pg-text-primary) !important;
    border: 1px solid var(--pg-card-border) !important;
    border-radius: 7px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}}

div[data-testid='stSelectbox'] > div > div:hover {{
    border-color: var(--pg-accent) !important;
}}

div[data-testid='stSelectbox'] svg {{
    fill: var(--pg-text-dim) !important;
}}

div[data-testid='stCheckbox'] {{
    margin-top: 4px !important;
}}

div[data-testid='stCheckbox'] label p {{
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: var(--pg-text-secondary) !important;
    white-space: nowrap !important;
}}

/* Streamlit segmented control container - full interactivity */
div[data-testid='stSegmentedControl'] {{
    background-color: var(--pg-card-bg) !important;
    border: 1px solid var(--pg-card-border) !important;
    border-radius: 8px !important;
    padding: 3px !important;
    position: relative !important;
    z-index: 100 !important;
}}

div[data-testid='stSegmentedControl'] button {{
    border-radius: 6px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    pointer-events: auto !important;
}}

/* ── Navigation Tabs ── */
div[data-testid='stTabs'] {{
    border-bottom: 1.5px solid var(--pg-divider) !important;
    margin-bottom: 24px !important;
}}

div[data-baseweb="tab-highlight"] {{
    background-color: var(--pg-accent) !important;
    pointer-events: none !important;
}}

button[data-testid='stTab'] {{
    font-family: 'Inter', sans-serif !important;
    font-size: 14.5px !important;
    padding: 10px 20px !important;
    border: none !important;
    background: transparent !important;
    opacity: 1 !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1.5px !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
}}

button[data-testid='stTab'] p {{
    font-family: 'Inter', sans-serif !important;
    font-size: 14.5px !important;
    font-weight: 500 !important;
    color: var(--pg-text-dim) !important;
    transition: color 0.15s ease !important;
}}

button[data-testid='stTab']:hover p {{
    color: var(--pg-text-primary) !important;
}}

button[data-testid='stTab'][aria-selected='true'] p {{
    color: var(--pg-text-primary) !important;
    font-weight: 700 !important;
}}

/* ── Typography & Header ── */
.pg-header {{
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--pg-divider);
}}

.pg-title {{
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.025em;
    color: var(--pg-text-primary);
    margin: 0 0 4px 0;
}}

.pg-subtitle {{
    font-size: 14.5px;
    color: var(--pg-text-dim);
    margin: 0;
    line-height: 1.45;
}}

/* ── Section Dividers & Labels ── */
.pg-section-label {{
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--pg-text-muted);
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}}

.pg-divider {{
    border: none;
    border-top: 1px solid var(--pg-divider);
    margin: 28px 0;
}}

/* ── Modern Card Containers (Visual Depth) ── */
.pg-card {{
    background: var(--pg-card-bg);
    border: 1px solid var(--pg-card-border);
    border-radius: 10px;
    padding: 20px 22px;
    box-shadow: var(--pg-shadow-sm);
    transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
    height: 100%;
    position: relative;
    overflow: hidden;
}}

.pg-card:hover {{
    border-color: var(--pg-card-border-hover);
}}

.pg-hero-card {{
    background: var(--pg-card-bg);
    border: 1px solid var(--pg-card-border);
    border-top: 3.5px solid var(--pg-accent);
    border-radius: 10px;
    padding: 24px 26px;
    box-shadow: var(--pg-shadow);
    height: 100%;
}}

.pg-stat-card {{
    background: var(--pg-card-bg);
    border: 1px solid var(--pg-card-border);
    border-radius: 9px;
    padding: 16px 18px;
    box-shadow: var(--pg-shadow-sm);
    height: 100%;
    transition: border-color 0.15s ease;
}}

.pg-stat-card:hover {{
    border-color: var(--pg-card-border-hover);
}}

/* ── Metric Display ── */
.pg-stat-label {{
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--pg-text-dim);
    margin-bottom: 6px;
}}

.pg-stat-value {{
    font-size: 32px;
    font-weight: 800;
    color: var(--pg-text-primary);
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.02em;
}}

.pg-stat-sub {{
    font-size: 13.5px;
    color: var(--pg-text-secondary);
    margin-top: 5px;
    line-height: 1.4;
}}

.pg-stat-note {{
    font-size: 12px;
    color: var(--pg-text-dim);
    margin-top: 4px;
    line-height: 1.35;
}}

/* Hero primary metric */
.pg-hero-value {{
    font-size: 64px;
    font-weight: 800;
    letter-spacing: -0.035em;
    color: var(--pg-text-primary);
    line-height: 1;
    font-variant-numeric: tabular-nums;
    font-family: 'Inter', sans-serif;
}}

.pg-hero-sub {{
    font-size: 16px;
    font-weight: 600;
    color: var(--pg-text-secondary);
    margin-top: 10px;
}}

.pg-hero-note {{
    font-size: 14px;
    color: var(--pg-text-dim);
    margin-top: 8px;
    line-height: 1.55;
}}

/* ── Badges ── */
.b-esc {{
    background: {badge_esc_bg};
    color: {badge_esc_txt};
    border: 1px solid {badge_esc_bd};
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 12px;
    letter-spacing: 0.02em;
    white-space: nowrap;
}}

.b-mon {{
    background: {badge_mon_bg};
    color: {badge_mon_txt};
    border: 1px solid {badge_mon_bd};
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 12px;
    letter-spacing: 0.02em;
    white-space: nowrap;
}}

.b-dne {{
    background: {badge_dne_bg};
    color: {badge_dne_txt};
    border: 1px solid {badge_dne_bd};
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 12px;
    letter-spacing: 0.02em;
    white-space: nowrap;
}}

.b-pos {{
    background: {badge_pos_bg};
    color: {badge_pos_txt};
    border: 1px solid {badge_pos_bd};
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 12px;
    white-space: nowrap;
}}

.b-neg {{
    background: {badge_neg_bg};
    color: {badge_neg_txt};
    border: 1px solid {badge_neg_bd};
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 12px;
    white-space: nowrap;
}}

.b-zero {{
    background: {badge_zero_bg};
    color: {badge_zero_txt};
    border: 1px solid {badge_zero_bd};
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 12px;
    white-space: nowrap;
}}

.b-ga {{
    background: {badge_ga_bg};
    color: {badge_ga_txt};
    border: 1px solid {badge_ga_bd};
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 12px;
}}

.b-gb {{
    background: {badge_gb_bg};
    color: {badge_gb_txt};
    border: 1px solid {badge_gb_bd};
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 12px;
}}

.b-gc {{
    background: {badge_gc_bg};
    color: {badge_gc_txt};
    border: 1px solid {badge_gc_bd};
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 12px;
}}

/* ── Dense Aligned Data Table ── */
.pg-table-container {{
    width: 100%;
    border: 1px solid var(--pg-card-border);
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 20px;
    background: var(--pg-card-bg);
    box-shadow: var(--pg-shadow-sm);
}}

.pg-data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    text-align: left;
}}

.pg-data-table th {{
    background: var(--pg-table-header-bg);
    color: var(--pg-table-header-text);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 11px 14px;
    border-bottom: 1px solid var(--pg-card-border);
    white-space: nowrap;
}}

.pg-data-table td {{
    padding: 10px 14px;
    border-bottom: 1px solid var(--pg-divider);
    color: var(--pg-text-secondary);
    vertical-align: middle;
}}

.pg-data-table tr:hover td {{
    background-color: var(--pg-table-row-hover);
}}

.pg-data-table tr:last-child td {{
    border-bottom: none;
}}

.pg-mono {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 13px;
    color: var(--pg-text-primary);
}}

/* ── Detail Pane / Callouts ── */
.pg-detail-box {{
    background: var(--pg-quote-bg);
    border: 1px solid var(--pg-card-border);
    border-radius: 8px;
    padding: 18px 22px;
    margin-top: 12px;
}}

.pg-quote-box {{
    background: var(--pg-quote-bg);
    border-left: 3.5px solid var(--pg-quote-border);
    padding: 13px 18px;
    font-size: 13.5px;
    line-height: 1.65;
    color: var(--pg-quote-text);
    border-radius: 0 6px 6px 0;
    margin: 8px 0;
    border-top: 1px solid var(--pg-card-border);
    border-right: 1px solid var(--pg-card-border);
    border-bottom: 1px solid var(--pg-card-border);
}}

.pg-conclusion-box {{
    background: var(--pg-conclusion-bg);
    border-left: 3.5px solid var(--pg-conclusion-border);
    padding: 13px 18px;
    font-size: 13.5px;
    line-height: 1.65;
    color: var(--pg-conclusion-text);
    border-radius: 0 6px 6px 0;
    margin-top: 8px;
    border-top: 1px solid rgba(34, 197, 94, 0.2);
    border-right: 1px solid rgba(34, 197, 94, 0.2);
    border-bottom: 1px solid rgba(34, 197, 94, 0.2);
}}

.pg-callout {{
    background: var(--pg-callout-bg);
    border-left: 3.5px solid var(--pg-accent);
    padding: 16px 20px;
    font-size: 13.5px;
    color: var(--pg-text-secondary);
    line-height: 1.65;
    border-radius: 0 8px 8px 0;
    margin-top: 18px;
    border-top: 1px solid var(--pg-card-border);
    border-right: 1px solid var(--pg-card-border);
    border-bottom: 1px solid var(--pg-card-border);
}}

/* ── Baseline Comparison Table ── */
.pg-cmp-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}}

.pg-cmp-table th {{
    text-align: left;
    padding: 9px 12px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--pg-table-header-text);
    border-bottom: 1px solid var(--pg-card-border);
    background: var(--pg-table-header-bg);
}}

.pg-cmp-table td {{
    padding: 10px 12px;
    border-bottom: 1px solid var(--pg-divider);
    color: var(--pg-text-secondary);
}}

.pg-cmp-table td.num {{
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    color: var(--pg-text-primary);
}}

.pg-cmp-table tr:last-child td {{
    border-bottom: none;
}}
</style>
"""
    return css


def inject_dashboard_styles(theme: str = "light") -> None:
    """Inject customized high-contrast CSS styling into Streamlit DOM."""
    st.markdown(get_theme_css(theme), unsafe_allow_html=True)
