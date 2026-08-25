"""
PharmaGuard Dashboard Styles & Design System
============================================
Centralized dual-theme CSS with Python token injection.
Styles both Streamlit native widgets (segmented control / button groups, selectboxes,
dropdowns, tabs, checkboxes) and custom PharmaGuard UI elements (cards, badges, tables, metrics).
"""
from __future__ import annotations
import streamlit as st


def get_theme_css(theme: str = "light") -> str:
    """Return complete themed CSS string for either 'light' or 'dark' mode."""
    is_dark = (theme == "dark")

    if is_dark:
        bg             = "#080D16"
        surface        = "#101824"
        surface2       = "#121B29"
        border         = "#263245"
        border_hover   = "#3B4D66"
        divider        = "#182230"
        text           = "#F3F6FA"
        text_sec       = "#A8B3C3"
        text_muted     = "#738096"
        primary        = "#818CF8"
        shadow         = "0 4px 16px rgba(0,0,0,0.4)"
        shadow_sm      = "0 1px 4px rgba(0,0,0,0.3)"
        quote_bg       = "rgba(18,27,41,0.8)"
        quote_bd       = "#263245"
        quote_txt      = "#D5DBE5"
        callout_bg     = "rgba(21,31,46,0.7)"
        callout_bd     = "#818CF8"
        th_bg          = "#121B29"
        th_txt         = "#A8B3C3"
        row_hover      = "#151F2E"
        input_bg       = "#101824"
        input_bd       = "#263245"
        popover_bg     = "#101824"
        popover_bd     = "#263245"
        opt_hover      = "#182335"
        opt_sel_bg     = "rgba(102, 114, 255, 0.22)"
        opt_sel_txt    = "#FFFFFF"
        code_bg        = "rgba(129,140,248,0.12)"
        code_txt       = "#A5B4FC"
        code_bd        = "rgba(129,140,248,0.28)"
        # Toggle / Button Group
        toggle_tray       = "#101824"
        toggle_tray_bd    = "#263245"
        btn_inactive_bg   = "transparent"
        btn_inactive_txt  = "#C8D3E0"
        btn_active_bg     = "rgba(102,114,255,0.25)"
        btn_active_bd     = "rgba(102,114,255,0.65)"
        btn_active_txt    = "#818CF8"
        btn_hover_bg      = "#182335"
        btn_hover_txt     = "#F3F6FA"
        # Tabs
        tab_inactive   = "#C8D3E0"
        tab_hover      = "#F3F6FA"
        tab_active     = "#818CF8"
        # Badges
        success_bg = "rgba(34,199,122,0.12)";  success_bd = "rgba(34,199,122,0.3)";  success_txt = "#6ee7b7"
        warning_bg = "rgba(242,184,75,0.12)";  warning_bd = "rgba(242,184,75,0.3)";  warning_txt = "#fcd34d"
        danger_bg  = "rgba(255,77,77,0.12)";   danger_bd  = "rgba(255,77,77,0.3)";   danger_txt  = "#fca5a5"
        info_bg    = "rgba(78,161,255,0.12)";  info_bd    = "rgba(78,161,255,0.3)";  info_txt    = "#93c5fd"
        mon_bg = "rgba(168,179,195,0.12)"; mon_txt = "#A8B3C3"; mon_bd = "rgba(168,179,195,0.3)"
        dne_bg = "rgba(115,128,150,0.15)"; dne_txt = "#738096"; dne_bd = "rgba(115,128,150,0.3)"
        neg_bg = "rgba(168,179,195,0.1)";  neg_txt = "#A8B3C3"; neg_bd = "rgba(168,179,195,0.25)"
        gb_bg  = "rgba(168,179,195,0.12)"; gb_txt  = "#A8B3C3"; gb_bd  = "rgba(168,179,195,0.3)"
        gc_bg  = "rgba(115,128,150,0.15)"; gc_txt  = "#738096"; gc_bd  = "rgba(115,128,150,0.25)"
    else:
        bg             = "#F7F9FC"
        surface        = "#FFFFFF"
        surface2       = "#F2F5F9"
        border         = "#D9E1EA"
        border_hover   = "#B8C6D6"
        divider        = "#E4E9F0"
        text           = "#172033"
        text_sec       = "#53657D"
        text_muted     = "#7C8A9D"
        primary        = "#4F46E5"
        shadow         = "0 4px 14px rgba(15,23,42,0.06)"
        shadow_sm      = "0 1px 3px rgba(15,23,42,0.05)"
        quote_bg       = "#F2F5F9"
        quote_bd       = "#D9E1EA"
        quote_txt      = "#334155"
        callout_bg     = "#F8FAFC"
        callout_bd     = "#4F46E5"
        th_bg          = "#F2F5F9"
        th_txt         = "#53657D"
        row_hover      = "#F8FAFC"
        input_bg       = "#FFFFFF"
        input_bd       = "#D9E1EA"
        popover_bg     = "#FFFFFF"
        popover_bd     = "#D9E1EA"
        opt_hover      = "#F2F5F9"
        opt_sel_bg     = "#EEF2FF"
        opt_sel_txt    = "#4F46E5"
        code_bg        = "#F2F5F9"
        code_txt       = "#334155"
        code_bd        = "#D9E1EA"
        # Toggle / Button Group
        toggle_tray       = "#EAEFF5"
        toggle_tray_bd    = "#D9E1EA"
        btn_inactive_bg   = "transparent"
        btn_inactive_txt  = "#53657D"
        btn_active_bg     = "#FFFFFF"
        btn_active_bd     = "#C7D2E0"
        btn_active_txt    = "#4F46E5"
        btn_hover_bg      = "#F2F5F9"
        btn_hover_txt     = "#172033"
        # Tabs
        tab_inactive   = "#53657D"
        tab_hover      = "#172033"
        tab_active     = "#4F46E5"
        # Badges
        success_bg = "#F0FDF4"; success_bd = "#BBF7D0"; success_txt = "#166534"
        warning_bg = "#FFFBEB"; warning_bd = "#FDE68A"; warning_txt = "#92400E"
        danger_bg  = "#FEF2F2"; danger_bd  = "#FECACA"; danger_txt  = "#991B1B"
        info_bg    = "#EFF6FF"; info_bd    = "#BFDBFE"; info_txt    = "#1E40AF"
        mon_bg = "#F2F5F9"; mon_txt = "#53657D"; mon_bd = "#D9E1EA"
        dne_bg = "#F2F5F9"; dne_txt = "#7C8A9D"; dne_bd = "#D9E1EA"
        neg_bg = "#F2F5F9"; neg_txt = "#53657D"; neg_bd = "#D9E1EA"
        gb_bg  = "#F2F5F9"; gb_txt  = "#53657D"; gb_bd  = "#D9E1EA"
        gc_bg  = "#F2F5F9"; gc_txt  = "#7C8A9D"; gc_bd  = "#D9E1EA"

    css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ── Base Reset & App Background ── */
html, body {{
    background-color: {bg} !important;
    color: {text} !important;
}}
.stApp {{
    background-color: {bg} !important;
}}
.stApp, .stApp p, .stApp span, .stApp div, .stApp label, .stApp h1, .stApp h2, .stApp h3 {{
    color: {text};
}}
.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 1260px !important;
    margin: 0 auto !important;
}}
#MainMenu, footer, .stDeployButton, div[data-testid='stToolbar'], header[data-testid='stHeader'] {{
    display: none !important;
}}

/* ═══════════════════════════════════════════════════════════════════
   STREAMLIT NATIVE WIDGET STYLING
   Comprehensive selectors covering both stSegmentedControl & stButtonGroup
   and all popup elements across Streamlit versions
   ═══════════════════════════════════════════════════════════════════ */

/* ── Segmented Control / Button Group (Theme Switcher) ── */
div[data-testid='stSegmentedControl'],
div[data-testid='stButtonGroup'],
div[data-baseweb='button-group'],
html body div[data-testid='stSegmentedControl'],
html body div[data-testid='stButtonGroup'] {{
    background: {toggle_tray} !important;
    background-color: {toggle_tray} !important;
    border: 1px solid {toggle_tray_bd} !important;
    border-radius: 10px !important;
    padding: 3px !important;
    box-shadow: none !important;
}}

div[data-testid='stSegmentedControl'] > div,
div[data-testid='stButtonGroup'] > div,
div[data-baseweb='button-group'] > div {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}

/* Inactive buttons (all buttons by default) */
div[data-testid='stSegmentedControl'] button,
div[data-testid='stButtonGroup'] button,
html body div[data-testid='stSegmentedControl'] button,
html body div[data-testid='stButtonGroup'] button,
button[role='radio'] {{
    background: {btn_inactive_bg} !important;
    background-color: {btn_inactive_bg} !important;
    border: 1px solid transparent !important;
    border-radius: 7px !important;
    padding: 5px 14px !important;
    box-shadow: none !important;
    color: {btn_inactive_txt} !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    cursor: pointer !important;
}}

div[data-testid='stSegmentedControl'] button *,
div[data-testid='stButtonGroup'] button *,
button[role='radio'] *,
button[role='radio'] p,
button[role='radio'] span,
button[role='radio'] div {{
    background: transparent !important;
    background-color: transparent !important;
    color: {btn_inactive_txt} !important;
    box-shadow: none !important;
}}

/* Inactive button Hover */
div[data-testid='stSegmentedControl'] button:hover,
div[data-testid='stButtonGroup'] button:hover,
button[role='radio']:hover {{
    background: {btn_hover_bg} !important;
    background-color: {btn_hover_bg} !important;
    color: {btn_hover_txt} !important;
}}
div[data-testid='stSegmentedControl'] button:hover *,
div[data-testid='stButtonGroup'] button:hover *,
button[role='radio']:hover * {{
    color: {btn_hover_txt} !important;
}}

/* Active button */
div[data-testid='stSegmentedControl'] button[aria-checked='true'],
div[data-testid='stButtonGroup'] button[aria-checked='true'],
div[data-testid='stSegmentedControl'] button[aria-pressed='true'],
div[data-testid='stButtonGroup'] button[aria-pressed='true'],
button[role='radio'][aria-checked='true'],
html body div[data-testid='stSegmentedControl'] button[aria-checked='true'],
html body div[data-testid='stButtonGroup'] button[aria-checked='true'] {{
    background: {btn_active_bg} !important;
    background-color: {btn_active_bg} !important;
    border: 1px solid {btn_active_bd} !important;
    color: {btn_active_txt} !important;
    font-weight: 700 !important;
    box-shadow: {shadow_sm} !important;
}}

div[data-testid='stSegmentedControl'] button[aria-checked='true'] *,
div[data-testid='stButtonGroup'] button[aria-checked='true'] *,
button[role='radio'][aria-checked='true'] *,
button[role='radio'][aria-checked='true'] span,
button[role='radio'][aria-checked='true'] p,
button[role='radio'][aria-checked='true'] div {{
    background: transparent !important;
    background-color: transparent !important;
    color: {btn_active_txt} !important;
    font-weight: 700 !important;
}}

/* ── Selectbox (Closed and Open Input Field) ── */
div[data-testid='stSelectbox'],
div[data-baseweb='select'] {{
    color: {text} !important;
}}

div[data-testid='stSelectbox'] > div > div,
div[data-baseweb='select'] > div,
html body div[data-baseweb='select'] > div {{
    background: {input_bg} !important;
    background-color: {input_bg} !important;
    border: 1px solid {input_bd} !important;
    border-radius: 8px !important;
    color: {text} !important;
}}

/* All text, values, placeholders, and inputs inside the selectbox trigger */
div[data-testid='stSelectbox'] *,
div[data-baseweb='select'] *,
div[data-baseweb='select'] div,
div[data-baseweb='select'] span,
div[data-baseweb='select'] p,
div[data-baseweb='select'] input,
html body div[data-baseweb='select'] *,
html body div[data-baseweb='select'] input {{
    color: {text} !important;
    -webkit-text-fill-color: {text} !important;
}}

div[data-baseweb='select'] input {{
    background: transparent !important;
    background-color: transparent !important;
}}

div[data-baseweb='select'] svg {{
    fill: {text_sec} !important;
    color: {text_sec} !important;
}}

/* ── Selectbox Dropdown Menu & Popover (Mounted to body) ── */
div[data-baseweb='popover'],
div[data-baseweb='popover'] > div,
div[data-baseweb='popover'] > div > div,
div[data-baseweb='menu'],
div[data-baseweb='menu'] > div,
ul[role='listbox'],
div[role='listbox'],
html body div[data-baseweb='popover'],
html body div[data-baseweb='menu'],
html body ul[role='listbox'],
html body div[role='listbox'] {{
    background: {popover_bg} !important;
    background-color: {popover_bg} !important;
    border: 1px solid {popover_bd} !important;
    border-radius: 8px !important;
    box-shadow: {shadow} !important;
    padding: 4px 0 !important;
    color: {text} !important;
}}

/* Options (both div[role='option'] and li[role='option']) */
[role='option'],
li[role='option'],
div[role='option'],
html body [role='option'],
html body li[role='option'],
html body div[role='option'] {{
    background: {popover_bg} !important;
    background-color: {popover_bg} !important;
    color: {text} !important;
    font-size: 13.5px !important;
    padding: 9px 14px !important;
    border: none !important;
    cursor: pointer !important;
    transition: background 0.1s ease !important;
}}

[role='option'] *,
[role='option'] > div,
[role='option'] > div > div,
[role='option'] > span,
[role='option'] > p,
html body [role='option'] * {{
    background: transparent !important;
    background-color: transparent !important;
    color: {text} !important;
    -webkit-text-fill-color: {text} !important;
}}

/* Option Hover */
[role='option']:hover,
li[role='option']:hover,
div[role='option']:hover,
html body [role='option']:hover {{
    background: {opt_hover} !important;
    background-color: {opt_hover} !important;
}}
[role='option']:hover *,
html body [role='option']:hover * {{
    background: transparent !important;
    color: {text} !important;
    -webkit-text-fill-color: {text} !important;
}}

/* Option Selected in dropdown list */
[role='option'][aria-selected='true'],
li[role='option'][aria-selected='true'],
div[role='option'][aria-selected='true'],
html body [role='option'][aria-selected='true'] {{
    background: {opt_sel_bg} !important;
    background-color: {opt_sel_bg} !important;
    color: {opt_sel_txt} !important;
    font-weight: 700 !important;
}}

[role='option'][aria-selected='true'] *,
[role='option'][aria-selected='true'] span,
[role='option'][aria-selected='true'] p,
[role='option'][aria-selected='true'] div,
html body [role='option'][aria-selected='true'] *,
html body [role='option'][aria-selected='true'] span,
html body [role='option'][aria-selected='true'] p,
html body [role='option'][aria-selected='true'] div {{
    background: transparent !important;
    background-color: transparent !important;
    color: {opt_sel_txt} !important;
    -webkit-text-fill-color: {opt_sel_txt} !important;
    font-weight: 700 !important;
}}

/* ── Checkbox ── */
div[data-testid='stCheckbox'] {{
    margin-top: 6px !important;
}}
div[data-testid='stCheckbox'] label,
div[data-testid='stCheckbox'] label p,
div[data-testid='stCheckbox'] label span {{
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: {text_sec} !important;
}}

/* ── Navigation Tabs ── */
div[data-testid='stTabs'] {{
    border-bottom: 1.5px solid {divider} !important;
    margin-bottom: 24px !important;
}}
[data-baseweb='tab-highlight'] {{
    background: {primary} !important;
    background-color: {primary} !important;
    height: 2.5px !important;
}}
[data-baseweb='tab-border'] {{
    background-color: {divider} !important;
}}
button[data-testid='stTab'] {{
    background: transparent !important;
    border: none !important;
    padding: 10px 18px !important;
    opacity: 1 !important;
    cursor: pointer !important;
}}
button[data-testid='stTab'] p,
button[data-testid='stTab'] span,
button[data-testid='stTab'] div {{
    font-size: 14px !important;
    font-weight: 500 !important;
    color: {tab_inactive} !important;
    transition: color 0.15s ease !important;
}}
button[data-testid='stTab']:hover p,
button[data-testid='stTab']:hover span,
button[data-testid='stTab']:hover div {{
    color: {tab_hover} !important;
}}
button[data-testid='stTab'][aria-selected='true'] p,
button[data-testid='stTab'][aria-selected='true'] span,
button[data-testid='stTab'][aria-selected='true'] div {{
    color: {tab_active} !important;
    font-weight: 700 !important;
}}

/* ═══════════════════════════════════════════════════════════════════
   CUSTOM PHARMAGUARD ELEMENTS
   ═══════════════════════════════════════════════════════════════════ */

/* ── Typography ── */
.pg-header {{ margin-bottom: 22px; padding-bottom: 14px; border-bottom: 1px solid {divider}; }}
.pg-title {{ font-size: 26px; font-weight: 700; letter-spacing: -0.025em; color: {text}; margin: 0 0 4px 0; }}
.pg-subtitle {{ font-size: 14.5px; color: {text_sec}; margin: 0; line-height: 1.45; }}
.pg-section-label {{ font-size: 12px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: {primary}; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }}
.pg-divider {{ border: none; border-top: 1px solid {divider}; margin: 26px 0; }}

/* ── Cards ── */
.pg-card {{ background: {surface}; border: 1px solid {border}; border-radius: 11px; padding: 20px 22px; box-shadow: {shadow_sm}; transition: border-color 0.15s ease; height: 100%; }}
.pg-card:hover {{ border-color: {border_hover}; }}
.pg-hero-card {{ background: {surface}; border: 1px solid {border}; border-top: 3.5px solid {primary}; border-radius: 11px; padding: 24px 26px; box-shadow: {shadow}; height: 100%; }}
.pg-stat-card {{ background: {surface}; border: 1px solid {border}; border-radius: 10px; padding: 16px 18px; box-shadow: {shadow_sm}; height: 100%; min-height: 140px; display: flex; flex-direction: column; justify-content: space-between; transition: border-color 0.15s ease; }}
.pg-stat-card:hover {{ border-color: {border_hover}; }}

/* ── Metrics ── */
.pg-stat-label {{ font-size: 12px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: {text_muted}; margin-bottom: 4px; }}
.pg-stat-value {{ font-size: 30px; font-weight: 800; color: {text}; line-height: 1.1; font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }}
.pg-stat-sub {{ font-size: 13.5px; color: {text_sec}; margin-top: 4px; line-height: 1.4; }}
.pg-stat-note {{ font-size: 12px; color: {text_muted}; margin-top: 4px; line-height: 1.35; }}
.pg-hero-value {{ font-size: 58px; font-weight: 800; letter-spacing: -0.035em; color: {text}; line-height: 1; font-variant-numeric: tabular-nums; margin: 8px 0; }}
.pg-hero-sub {{ font-size: 15.5px; font-weight: 600; color: {text_sec}; margin-top: 6px; }}
.pg-hero-note {{ font-size: 13.5px; color: {text_muted}; margin-top: 8px; line-height: 1.5; }}

/* ── Badges ── */
.b-esc  {{ background: {success_bg}; color: {success_txt}; border: 1px solid {success_bd}; font-weight: 600; padding: 3px 8px; border-radius: 5px; font-size: 12px; white-space: nowrap; }}
.b-mon  {{ background: {mon_bg}; color: {mon_txt}; border: 1px solid {mon_bd}; font-weight: 600; padding: 3px 8px; border-radius: 5px; font-size: 12px; white-space: nowrap; }}
.b-dne  {{ background: {dne_bg}; color: {dne_txt}; border: 1px solid {dne_bd}; font-weight: 500; padding: 3px 8px; border-radius: 5px; font-size: 12px; white-space: nowrap; }}
.b-pos  {{ background: {info_bg}; color: {info_txt}; border: 1px solid {info_bd}; font-weight: 500; padding: 3px 8px; border-radius: 5px; font-size: 12px; white-space: nowrap; }}
.b-neg  {{ background: {neg_bg}; color: {neg_txt}; border: 1px solid {neg_bd}; font-weight: 500; padding: 3px 8px; border-radius: 5px; font-size: 12px; white-space: nowrap; }}
.b-zero {{ background: {warning_bg}; color: {warning_txt}; border: 1px solid {warning_bd}; font-weight: 500; padding: 3px 8px; border-radius: 5px; font-size: 12px; white-space: nowrap; }}
.b-ga   {{ background: {info_bg}; color: {info_txt}; border: 1px solid {info_bd}; font-weight: 700; padding: 2px 7px; border-radius: 4px; font-size: 12px; }}
.b-gb   {{ background: {gb_bg}; color: {gb_txt}; border: 1px solid {gb_bd}; font-weight: 700; padding: 2px 7px; border-radius: 4px; font-size: 12px; }}
.b-gc   {{ background: {gc_bg}; color: {gc_txt}; border: 1px solid {gc_bd}; font-weight: 700; padding: 2px 7px; border-radius: 4px; font-size: 12px; }}

/* ── Data Table ── */
.pg-table-container {{ width: 100%; border: 1px solid {border}; border-radius: 9px; overflow-x: auto; -webkit-overflow-scrolling: touch; margin-bottom: 18px; background: {surface}; box-shadow: {shadow_sm}; }}
.pg-data-table {{ width: 100%; min-width: 980px; border-collapse: collapse; font-size: 13.5px; text-align: left; }}
.pg-data-table th {{ background: {th_bg}; color: {th_txt}; font-size: 12px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; padding: 10px 12px; border-bottom: 1px solid {border}; white-space: nowrap; }}
.pg-data-table td {{ padding: 9px 12px; border-bottom: 1px solid {divider}; color: {text_sec}; vertical-align: middle; }}
.pg-data-table tr:hover td {{ background-color: {row_hover}; }}
.pg-data-table tr:last-child td {{ border-bottom: none; }}
.pg-mono {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; color: {text}; font-variant-numeric: tabular-nums; }}

/* ── Callouts ── */
.pg-quote-box {{ background: {quote_bg}; border-left: 3.5px solid {quote_bd}; padding: 13px 16px; font-size: 13.5px; line-height: 1.6; color: {quote_txt}; border-radius: 0 6px 6px 0; margin: 8px 0; border-top: 1px solid {border}; border-right: 1px solid {border}; border-bottom: 1px solid {border}; }}
.pg-conclusion-box {{ background: {success_bg}; border-left: 3.5px solid {success_bd}; padding: 13px 16px; font-size: 13.5px; line-height: 1.6; color: {success_txt}; border-radius: 0 6px 6px 0; margin-top: 8px; border-top: 1px solid {success_bd}; border-right: 1px solid {success_bd}; border-bottom: 1px solid {success_bd}; }}
.pg-callout {{ background: {callout_bg}; border-left: 3.5px solid {callout_bd}; padding: 15px 18px; font-size: 13.5px; color: {text_sec}; line-height: 1.6; border-radius: 0 8px 8px 0; margin-top: 16px; border-top: 1px solid {border}; border-right: 1px solid {border}; border-bottom: 1px solid {border}; }}

/* ── Comparison Table ── */
.pg-cmp-table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
.pg-cmp-table th {{ text-align: left; padding: 9px 12px; font-size: 12px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: {th_txt}; border-bottom: 1px solid {border}; background: {th_bg}; }}
.pg-cmp-table td {{ padding: 9px 12px; border-bottom: 1px solid {divider}; color: {text_sec}; }}
.pg-cmp-table td.num {{ text-align: right; font-family: 'JetBrains Mono', monospace; font-weight: 600; color: {text}; }}
.pg-cmp-table tr:last-child td {{ border-bottom: none; }}

/* ── Inline code ── */
code {{ background-color: {code_bg} !important; color: {code_txt} !important; border: 1px solid {code_bd} !important; padding: 2px 6px !important; border-radius: 4px !important; font-family: 'JetBrains Mono', monospace !important; font-size: 12.5px !important; }}
</style>
"""
    return css


def inject_dashboard_styles(theme: str = "light") -> None:
    """Inject customized CSS styling into Streamlit DOM."""
    st.markdown(get_theme_css(theme), unsafe_allow_html=True)