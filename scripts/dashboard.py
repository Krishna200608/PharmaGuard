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

from pathlib import Path
import streamlit as st

from dashboard_modules.data_loader import build_df, load_ground_truth, load_reports
from dashboard_modules.styles import inject_dashboard_styles
from dashboard_modules.views import (
    view_baseline,
    view_disagreements,
    view_overview,
    view_per_pair,
)

# ---------------------------------------------------------------------------
# Paths & Page Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
BASELINE_DIR = OUTPUTS_DIR / "baseline"
GROUND_TRUTH_PATH = REPO_ROOT / "pharmaguard" / "data" / "ground_truth.json"
FAVICON_PATH = REPO_ROOT / "assets" / "Logos" / "Logo_1.png"
LOGO_PATH = REPO_ROOT / "assets" / "Logos" / "Logo_2.png"

st.set_page_config(
    page_title="PharmaGuard | Evaluation Dashboard",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    """Load data and render tabbed evaluation views."""
    # Top theme switcher bar
    c_nav, c_theme = st.columns([0.68, 0.32])
    with c_theme:
        theme_sel = st.segmented_control(
            "Theme",
            options=["☀️ Light", "🌙 Dark", "🖥️ System"],
            default="☀️ Light",
            key="ui_theme_mode",
            label_visibility="collapsed",
        )

    theme_map = {"☀️ Light": "light", "🌙 Dark": "dark", "🖥️ System": "system"}
    active_theme = theme_map.get(theme_sel or "☀️ Light", "light")

    inject_dashboard_styles(theme=active_theme)

    gt = load_ground_truth(GROUND_TRUTH_PATH)
    prod_reports = load_reports(OUTPUTS_DIR)
    base_reports = load_reports(BASELINE_DIR)
    df = build_df(prod_reports, gt)

    if not prod_reports:
        st.error(
            f"No reports found in {OUTPUTS_DIR}.\n\n"
            "Run 'python scripts/run_eval.py' first to generate evaluation outputs."
        )
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs([
        "Overview",
        "Per-Pair Table",
        "Disagreement Spotlight",
        "Baseline Comparison",
    ])
    with tab1:
        view_overview(LOGO_PATH)
    with tab2:
        view_per_pair(df, theme=active_theme)
    with tab3:
        view_disagreements(prod_reports, OUTPUTS_DIR, theme=active_theme)
    with tab4:
        view_baseline(prod_reports, base_reports, theme=active_theme)


if __name__ == "__main__":
    main()
