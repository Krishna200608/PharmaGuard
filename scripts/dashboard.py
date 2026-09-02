# ruff: noqa: E501
"""
PharmaGuard Evaluation Dashboard
=================================
Demo/presentation tool.
NO live API calls at runtime -- reads only from pre-committed JSON files in:
  outputs/core/, outputs/experiments/baseline/, pharmaguard/data/ground_truth.json.

Run:
    streamlit run scripts/dashboard.py   (from project root)
"""
from __future__ import annotations

import importlib
from pathlib import Path
import sys
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import dashboard_modules.styles as _styles_mod
importlib.reload(_styles_mod)
from dashboard_modules.styles import inject_dashboard_styles

import dashboard_modules.components as _comp_mod
importlib.reload(_comp_mod)

import dashboard_modules.data_loader as _data_mod
importlib.reload(_data_mod)
from dashboard_modules.data_loader import build_df, load_ground_truth, load_reports

import dashboard_modules.views.overview as _v_overview
importlib.reload(_v_overview)
from dashboard_modules.views.overview import view_overview

import dashboard_modules.views.per_pair as _v_per_pair
importlib.reload(_v_per_pair)
from dashboard_modules.views.per_pair import view_per_pair

import dashboard_modules.views.disagreements as _v_disagreements
importlib.reload(_v_disagreements)
from dashboard_modules.views.disagreements import view_disagreements

import dashboard_modules.views.baseline as _v_baseline
importlib.reload(_v_baseline)
from dashboard_modules.views.baseline import view_baseline

import dashboard_modules.views.probes as _v_probes
importlib.reload(_v_probes)
from dashboard_modules.views.probes import view_probes

import dashboard_modules.views.omop_pilot as _v_omop_pilot
importlib.reload(_v_omop_pilot)
from dashboard_modules.views.omop_pilot import view_omop_pilot

# ---------------------------------------------------------------------------
# Paths & Page Configuration
# ---------------------------------------------------------------------------
OUTPUTS_DIR = REPO_ROOT / "outputs" / "core"
BASELINE_DIR = REPO_ROOT / "outputs" / "experiments" / "baseline"
OMOP_DIR = REPO_ROOT / "outputs" / "research" / "omop_pilot"
STABILITY_PATH = REPO_ROOT / "outputs" / "research" / "stability" / "loo_analysis.json"
GROUND_TRUTH_PATH = REPO_ROOT / "pharmaguard" / "data" / "ground_truth.json"
FAVICON_PATH = REPO_ROOT / "assets" / "Logos" / "Logo_1.png"
LOGO_PATH = REPO_ROOT / "assets" / "Logos" / "Logo_2.png"

st.set_page_config(
    page_title="PharmaGuard | Evaluation Dashboard",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else ":material/shield:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

THEME_OPTIONS = [
    ":material/light_mode: Light",
    ":material/dark_mode: Dark",
    ":material/desktop_windows: System",
]

THEME_MAP = {
    ":material/light_mode: Light": "light",
    ":material/dark_mode: Dark": "dark",
    ":material/desktop_windows: System": "light",
}


def main() -> None:
    """Load data and render tabbed evaluation views."""
    # ── Persistent theme state ──
    if "theme_choice" not in st.session_state:
        st.session_state["theme_choice"] = ":material/light_mode: Light"

    if st.session_state.get("theme_widget") is None:
        st.session_state["theme_widget"] = st.session_state["theme_choice"]

    # ── Top bar with theme switcher ──
    _, c_theme = st.columns([0.65, 0.35])
    with c_theme:
        theme_sel = st.segmented_control(
            "Theme",
            options=THEME_OPTIONS,
            key="theme_widget",
            label_visibility="collapsed",
        )

    # Protect against None deselect state
    if theme_sel in THEME_OPTIONS:
        st.session_state["theme_choice"] = theme_sel
    else:
        theme_sel = st.session_state["theme_choice"]

    active_theme = THEME_MAP.get(theme_sel, "light")

    # ── Inject themed CSS ──
    inject_dashboard_styles(theme=active_theme)

    # ── Load evaluation dataset ──
    gt = load_ground_truth(GROUND_TRUTH_PATH)
    prod_reports = load_reports(OUTPUTS_DIR)
    base_reports = load_reports(BASELINE_DIR)
    omop_reports = load_reports(OMOP_DIR)
    df = build_df(prod_reports, gt)

    if not prod_reports:
        st.error(
            f"No reports found in {OUTPUTS_DIR}.\n\n"
            "Run 'python scripts/run_eval.py' first to generate evaluation outputs."
        )
        st.stop()

    # ── Tabs & Views ──
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Overview",
        "Per-Pair Table",
        "Disagreement Spotlight",
        "Baseline Comparison",
        "Methodology Probes",
        "OMOP Pilot",
    ])
    with tab1:
        view_overview(LOGO_PATH, STABILITY_PATH)
    with tab2:
        view_per_pair(df, theme=active_theme)
    with tab3:
        view_disagreements(prod_reports, OUTPUTS_DIR, theme=active_theme)
    with tab4:
        view_baseline(prod_reports, base_reports, theme=active_theme)
    with tab5:
        view_probes(REPO_ROOT, theme=active_theme)
    with tab6:
        view_omop_pilot(omop_reports, OMOP_DIR, theme=active_theme, repo_root=REPO_ROOT)


if __name__ == "__main__":
    main()