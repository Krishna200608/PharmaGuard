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
from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

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
from dashboard_modules.data_loader import build_df, load_ground_truth, load_reports, load_cohort_metrics

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

import dashboard_modules.views.live_triage as _v_live_triage
importlib.reload(_v_live_triage)
from dashboard_modules.views.live_triage import view_live_triage

# ---------------------------------------------------------------------------
# Paths & Page Configuration
# ---------------------------------------------------------------------------
OUTPUTS_DIR = REPO_ROOT / "outputs" / "core"
BASELINE_DIR = REPO_ROOT / "outputs" / "experiments" / "baseline"
OMOP_DIR = REPO_ROOT / "outputs" / "research" / "omop_pilot"
STABILITY_PATH = REPO_ROOT / "outputs" / "research" / "stability" / "loo_analysis.json"
GROUND_TRUTH_PATH = REPO_ROOT / "pharmaguard" / "data" / "ground_truth.json"

TOP_PRESCRIBED_DIR = REPO_ROOT / "outputs" / "research" / "top_prescribed"
TOP_PRESCRIBED_GT = REPO_ROOT / "pharmaguard" / "data" / "ground_truth_top_prescribed_boxed_warnings.json"
TOP_PRESCRIBED_SUMMARY = TOP_PRESCRIBED_DIR / "evaluation_summary.json"

OMOP_EXPANDED_DIR = REPO_ROOT / "outputs" / "research" / "omop_expanded"
OMOP_EXPANDED_GT = REPO_ROOT / "pharmaguard" / "data" / "ground_truth_omop_expanded.json"
OMOP_EXPANDED_SUMMARY = OMOP_EXPANDED_DIR / "evaluation_summary.json"

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

COHORT_OPTIONS = [
    ":material/stars: Core Showcase (15 Pairs)",
    ":material/verified: Top Prescribed Boxed Warnings (50 Pairs)",
    ":material/dataset: OMOP Expanded Reference (100 Pairs)",
]


def main() -> None:
    """Load data and render tabbed evaluation views."""
    # ── Persistent theme state ──
    if "theme_choice" not in st.session_state:
        st.session_state["theme_choice"] = ":material/light_mode: Light"

    if st.session_state.get("theme_widget") is None:
        st.session_state["theme_widget"] = st.session_state["theme_choice"]

    # ── Top bar with cohort & theme switchers ──
    c_cohort, _, c_theme = st.columns([0.48, 0.17, 0.35], vertical_alignment="center")
    with c_cohort:
        cohort_sel = st.selectbox(
            "Benchmark Cohort",
            options=COHORT_OPTIONS,
            key="cohort_choice",
            label_visibility="collapsed",
            help="Switch benchmark cohort for Overview and Per-Pair Table.",
        )
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

    # ── Load Core evaluation dataset ──
    gt_core = load_ground_truth(GROUND_TRUTH_PATH)
    prod_reports = load_reports(OUTPUTS_DIR)
    base_reports = load_reports(BASELINE_DIR)
    omop_pilot_reports = load_reports(OMOP_DIR)
    df_core = build_df(prod_reports, gt_core)

    if not prod_reports:
        st.error(
            f"No reports found in {OUTPUTS_DIR}.\n\n"
            "Run 'python scripts/run_eval.py' first to generate evaluation outputs."
        )
        st.stop()

    # ── Load Secondary evaluation cohorts ──
    gt_top = load_ground_truth(TOP_PRESCRIBED_GT)
    top_reports = load_reports(TOP_PRESCRIBED_DIR)
    df_top = build_df(top_reports, gt_top)
    m_top = load_cohort_metrics(TOP_PRESCRIBED_SUMMARY)

    gt_omop = load_ground_truth(OMOP_EXPANDED_GT)
    omop_exp_reports = load_reports(OMOP_EXPANDED_DIR)
    df_omop = build_df(omop_exp_reports, gt_omop)
    m_omop = load_cohort_metrics(OMOP_EXPANDED_SUMMARY)

    # Determine active cohort context
    if "Top Prescribed" in cohort_sel:
        active_df = df_top
        active_reports = top_reports
        active_metrics = m_top
        active_cohort_name = "Top Prescribed Blockbusters (50 Pairs)"
        active_cohort_desc = "50 blockbuster outpatient medications · 25 FDA Boxed Warnings · 25 balanced negative controls"
        active_reports_dir = TOP_PRESCRIBED_DIR
        active_gt_path = TOP_PRESCRIBED_GT
    elif "OMOP Expanded" in cohort_sel:
        active_df = df_omop
        active_reports = omop_exp_reports
        active_metrics = m_omop
        active_cohort_name = "OMOP Expanded Reference (100 Pairs)"
        active_cohort_desc = "100 reference pairs from OHDSI OMOP · 4 severe organ toxicity phenotypes · 50 positive & 50 negative controls"
        active_reports_dir = OMOP_EXPANDED_DIR
        active_gt_path = OMOP_EXPANDED_GT
    else:
        active_df = df_core
        active_reports = prod_reports
        active_metrics = None  # defaults to PROD_METRICS
        active_cohort_name = "Core Benchmark (15 Pairs)"
        active_cohort_desc = "Sprint 3 final benchmark · 15 drug–event pairs · plausibility ratings v1.0"
        active_reports_dir = OUTPUTS_DIR
        active_gt_path = GROUND_TRUTH_PATH

    # ── Tabs & Views ──
    tab_live, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        ":material/bolt: Live Signal Triage",
        ":material/analytics: Overview",
        ":material/table_chart: Per-Pair Table",
        ":material/warning: Disagreement Spotlight",
        ":material/compare_arrows: Baseline Comparison",
        ":material/biotech: Methodology Probes",
        ":material/dataset: OMOP Pilot",
    ])
    with tab_live:
        view_live_triage(theme=active_theme, repo_root=REPO_ROOT)
    with tab1:
        view_overview(
            LOGO_PATH,
            STABILITY_PATH,
            theme=active_theme,
            metrics=active_metrics,
            cohort_name=active_cohort_name,
            cohort_desc=active_cohort_desc,
            reports_dir=active_reports_dir,
            gt_path=active_gt_path,
        )
    with tab2:
        view_per_pair(active_df, theme=active_theme, cohort_name=active_cohort_name)
    with tab3:
        view_disagreements(prod_reports, OUTPUTS_DIR, theme=active_theme)
    with tab4:
        view_baseline(prod_reports, base_reports, theme=active_theme)
    with tab5:
        view_probes(REPO_ROOT, theme=active_theme)
    with tab6:
        view_omop_pilot(omop_pilot_reports, OMOP_DIR, theme=active_theme, repo_root=REPO_ROOT)


if __name__ == "__main__":
    main()