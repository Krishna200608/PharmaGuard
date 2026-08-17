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
# Page config -- must come before any other st.* call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PharmaGuard | Evaluation Dashboard",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Design system CSS
# Philosophy: hierarchy through type weight/size, minimal color, status-only.
# MONITOR is neutral/gray -- NOT a warning or failure color.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; font-size: 14px; color: #1a1a1a; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stDeployButton { display: none; }
div[data-testid="stToolbar"] { display: none; }
header[data-testid="stHeader"] { background: transparent; }
.stApp { background: #fafaf9; }
.block-container { padding-top: 1.5rem !important; }
.stTabs [data-baseweb="tab-list"] { gap:0; border-bottom:1.5px solid #e5e5e5; background:transparent; padding:0; margin-bottom:8px; }
.stTabs [data-baseweb="tab"] { background:transparent; border:none; border-bottom:2px solid transparent; padding:10px 22px; font-size:13px; font-weight:500; color:#888; margin-bottom:-1.5px; }
.stTabs [aria-selected="true"] { background:transparent!important; border-bottom:2px solid #1a1a1a!important; color:#1a1a1a!important; font-weight:600; }
.pg-card { background:#fff; border:1px solid #e5e5e5; border-radius:8px; padding:22px 26px; min-height:100px; }
.pg-label { font-size:10.5px; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:#999; margin-bottom:7px; }
.pg-value { font-size:30px; font-weight:700; color:#1a1a1a; line-height:1; font-variant-numeric:tabular-nums; }
.pg-sub { font-size:11.5px; color:#aaa; margin-top:5px; }
.pg-note { font-size:10.5px; color:#ccc; margin-top:4px; line-height:1.4; }
.pg-headline { font-size:54px; font-weight:800; letter-spacing:-.03em; color:#1a1a1a; line-height:1; }
.pg-headline-sub { font-size:15px; color:#999; margin-top:8px; }
.pg-hr { border:none; border-top:1px solid #e8e8e8; margin:20px 0; }
.pg-header { border-bottom:1px solid #e5e5e5; margin-bottom:24px; padding-bottom:14px; }
.pg-title { font-size:20px; font-weight:700; color:#1a1a1a; margin:0 0 3px 0; letter-spacing:-.01em; }
.pg-subtitle { font-size:13px; color:#888; margin:0; }
.b-esc { background:#f0f8f0; color:#2a5f2a; border:1px solid #b3d9b3; font-weight:600; padding:2px 7px; border-radius:4px; font-size:11px; white-space:nowrap; }
.b-mon { background:#f5f5f5; color:#555; border:1px solid #d8d8d8; font-weight:600; padding:2px 7px; border-radius:4px; font-size:11px; white-space:nowrap; }
.b-dne { background:#f8f8f8; color:#999; border:1px solid #e2e2e2; font-weight:500; padding:2px 7px; border-radius:4px; font-size:11px; white-space:nowrap; }
.b-pos { background:#edf3ff; color:#2b45a8; border:1px solid #bfcfee; font-weight:500; padding:2px 7px; border-radius:4px; font-size:11px; }
.b-neg { background:#f5f5f5; color:#666; border:1px solid #ddd; font-weight:500; padding:2px 7px; border-radius:4px; font-size:11px; }
.b-zero { background:#fdf4ef; color:#7a4426; border:1px solid #dbbba3; font-weight:500; padding:2px 7px; border-radius:4px; font-size:11px; }
.b-ga { background:#edf3ff; color:#2b45a8; border:1px solid #bfcfee; font-weight:700; padding:2px 6px; border-radius:3px; font-size:11px; }
.b-gb { background:#f5f5f5; color:#555; border:1px solid #ddd; font-weight:700; padding:2px 6px; border-radius:3px; font-size:11px; }
.b-gc { background:#f8f8f8; color:#bbb; border:1px solid #e2e2e2; font-weight:700; padding:2px 6px; border-radius:3px; font-size:11px; }
.th { font-size:10px; font-weight:600; letter-spacing:.07em; text-transform:uppercase; color:#bbb; padding:3px 0; }
.mono { font-family:'JetBrains Mono','Courier New',monospace; font-size:12.5px; }
.rationale { background:#f7f7f6; border-left:3px solid #d5d5d5; padding:12px 16px; font-size:13px; line-height:1.7; color:#333; border-radius:0 4px 4px 0; margin:8px 0; }
.cmp-col { background:#fff; border:1px solid #e5e5e5; border-radius:8px; padding:20px 22px; }
.cmp-title { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.08em; color:#aaa; margin-bottom:14px; }
.mt { width:100%; border-collapse:collapse; font-size:13px; }
.mt th { text-align:left; padding:5px 8px; font-size:10px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:#bbb; border-bottom:1px solid #eee; }
.mt td { padding:8px 8px; border-bottom:1px solid #f3f3f3; color:#444; }
.mt td.num { text-align:right; font-family:'JetBrains Mono',monospace; color:#1a1a1a; }
.mt tr:last-child td { border-bottom:none; }
.spot-header { background:#fff; border:1px solid #e5e5e5; border-radius:8px; padding:18px 22px; margin-bottom:14px; }
.spot-drug { font-size:19px; font-weight:700; color:#1a1a1a; }
.spot-event { font-size:13.5px; color:#888; }
.conclusion { background:#f1f6f1; border-left:3px solid #78a878; padding:12px 16px; font-size:13px; line-height:1.65; color:#2a3a2a; border-radius:0 4px 4px 0; margin-top:8px; }
.callout { background:#f5f5f5; border:1px solid #e5e5e5; border-radius:6px; padding:12px 16px; font-size:12.5px; color:#555; line-height:1.6; }
</style>
""", unsafe_allow_html=True)


# ===========================================================================
# DATA LOADING -- pure JSON reads, ZERO network calls
# ===========================================================================

@st.cache_data
def load_ground_truth() -> dict:
    if not GROUND_TRUTH_PATH.exists():
        return {}
    with open(GROUND_TRUTH_PATH, encoding="utf-8") as fh:
        raw = json.load(fh)
    return {
        f"{p['drug_canonical']}::{p['event_meddra_pt']}": p
        for p in raw.get("pairs", [])
    }


def _run_idx(name: str) -> int:
    m = re.search(r"eval-run-(\d+)-", name)
    return int(m.group(1)) if m else 999


@st.cache_data
def load_reports(directory: Path) -> list:
    reports = []
    for path in sorted(directory.glob("eval-run-*_report.json"),
                       key=lambda p: _run_idx(p.name)):
        try:
            with open(path, encoding="utf-8") as fh:
                rpt = json.load(fh)
            rpt["_src"] = path.name
            reports.append(rpt)
        except (json.JSONDecodeError, OSError):
            pass
    return reports


@st.cache_data
def build_df(reports: list, gt: dict) -> pd.DataFrame:
    rows = []
    for r in reports:
        drug = r.get("drug", "")
        event = r.get("event", "")
        entry = gt.get(f"{drug}::{event}", {})
        expected = entry.get("expected_escalation", "")
        actual = r.get("triage", {}).get("escalation", "")
        rows.append({
            "idx": _run_idx(r.get("_src", "")),
            "drug": drug,
            "event": event.replace("_", " "),
            "category": entry.get("category", ""),
            "signal": r.get("signal_stats", {}).get("prr_score_label", ""),
            "grade": r.get("literature", {}).get("evidence_grade", ""),
            "plausibility": r.get("mechanism", {}).get("biological_plausibility", ""),
            "confidence": r.get("triage", {}).get("confidence"),
            "escalation": actual,
            "expected": expected,
            "match": actual == expected,
            "_r": r,
            "_gt": entry,
        })
    return pd.DataFrame(rows).sort_values("idx").reset_index(drop=True)


# Hard-coded from DECISIONS.md section 16 -- not recomputed live
PROD = {
    "s_prec": 1.000, "s_rec": 0.857, "s_spec": 1.000, "s_f1": 0.923,
    "l_prec": 0.875, "l_rec": 1.000, "l_spec": 0.875, "l_f1": 0.933,
    "ocr": 12.5,
}
BASE = {
    "s_prec": 0.875, "s_rec": 1.000, "s_spec": 0.875, "s_f1": 0.933,
    "l_prec": 0.700, "l_rec": 1.000, "l_spec": 0.625, "l_f1": 0.824,
    "ocr": 25.0,
}


# ===========================================================================
# RENDERING HELPERS
# ===========================================================================

def esc_badge(e: str) -> str:
    cls = {"ESCALATE": "b-esc", "MONITOR": "b-mon", "DO_NOT_ESCALATE": "b-dne"}.get(e, "b-dne")
    return f'<span class="{cls}">{e}</span>'


def cat_badge(c: str) -> str:
    m = {
        "confirmed_positive": ("b-pos", "Confirmed Positive"),
        "genuine_negative_control": ("b-neg", "Genuine Negative"),
        "zero_report_edge_case": ("b-zero", "Zero Report"),
    }
    cls, label = m.get(c, ("b-neg", c))
    return f'<span class="{cls}">{label}</span>'


def grade_badge(g: str) -> str:
    cls = {"A": "b-ga", "B": "b-gb", "C": "b-gc"}.get(g, "b-gc")
    return f'<span class="{cls}">{g}</span>'


def signal_span(s: str) -> str:
    color = {"STRONG": "#1a5c1a", "MODERATE": "#333", "NO_SIGNAL": "#bbb"}.get(s, "#bbb")
    wt = {"STRONG": "600", "MODERATE": "500", "NO_SIGNAL": "400"}.get(s, "400")
    return f'<span style="color:{color};font-weight:{wt};font-size:12px;">{s}</span>'


def conf_chart(r: dict, key: str) -> None:
    """Horizontal bar chart decomposing the 3-component confidence formula:
       confidence = 0.40 * PRR_score + 0.40 * evidence_grade_score + 0.20 * plausibility_score
    """
    ss = r.get("signal_stats", {})
    lit = r.get("literature", {})
    mech = r.get("mechanism", {})
    prr_raw = ss.get("prr_score", 0) or 0
    grade_raw = lit.get("grade_score", 0) or 0
    plaus_raw = mech.get("plausibility_score", 0) or 0
    w_prr = 0.40 * prr_raw
    w_grade = 0.40 * grade_raw
    w_plaus = 0.20 * plaus_raw
    total = w_prr + w_grade + w_plaus
    labels = ["FAERS PRR x0.40", "PubMed Grade x0.40", "Plausibility x0.20"]
    vals = [w_prr, w_grade, w_plaus]
    raws = [prr_raw, grade_raw, plaus_raw]
    colors = ["#4a7fc1", "#6b9ad4", "#9bbce8"]
    fig = go.Figure()
    for lbl, val, raw, col in zip(labels, vals, raws, colors):
        fig.add_trace(go.Bar(
            y=[lbl], x=[val], orientation="h", marker_color=col,
            text=f"raw={raw:.2f} -> {val:.3f}", textposition="outside",
            hovertemplate=f"{lbl}<br>Raw: {raw:.2f} -> Weighted: {val:.3f}<extra></extra>",
        ))
    fig.add_shape(type="line", x0=total, x1=total, y0=-0.6, y1=2.6,
                  line=dict(color="#1a1a1a", width=1.5, dash="dot"))
    fig.add_annotation(x=total, y=2.75, text=f"Sum = {total:.3f}", showarrow=False,
                       font=dict(size=11, color="#1a1a1a", family="JetBrains Mono"),
                       xanchor="center")
    fig.update_layout(
        barmode="overlay",
        xaxis=dict(range=[0, 1.08], title=None,
                   tickfont=dict(size=10, family="JetBrains Mono"),
                   gridcolor="#f0f0f0", showgrid=True),
        yaxis=dict(title=None, tickfont=dict(size=11, family="Inter")),
        height=190, margin=dict(l=4, r=88, t=32, b=4),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, font=dict(family="Inter"),
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


# ===========================================================================
# VIEW 1 -- OVERVIEW
# ===========================================================================

def view_overview() -> None:
    st.markdown(
        '<div class="pg-header">'
        '<div class="pg-title">PharmaGuard &mdash; Evaluation Overview</div>'
        '<div class="pg-subtitle">Sprint 3 final benchmark &middot; 15 drug-event pairs &middot; plausibility ratings v1.0</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    m = PROD
    col_main, col_right = st.columns([2.2, 1], gap="large")
    with col_main:
        st.markdown(
            f'<div class="pg-card" style="padding:30px 34px;">'
            f'<div class="pg-label">Strict Recall &mdash; Primary Benchmark Result</div>'
            f'<div class="pg-headline">{m["s_rec"]:.3f}</div>'
            f'<div class="pg-headline-sub">6 of 7 confirmed positives correctly escalated</div>'
            f'<div class="pg-note" style="margin-top:10px;font-size:12px;color:#bbb;">'
            f'Lenient Recall: <strong style="color:#888;">1.000</strong> (7/7) &mdash; '
            f'signal never missed; confidence appropriately modulated'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    with col_right:
        st.markdown(
            f'<div class="pg-card"><div class="pg-label">Over-Caution Rate</div>'
            f'<div class="pg-value">12.5%</div>'
            f'<div class="pg-sub">1 of 8 negatives &rarr; MONITOR</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="pg-card"><div class="pg-label">False Positives</div>'
            f'<div class="pg-value">FP = 0</div>'
            f'<div class="pg-sub">Wilson CI: 0.610&ndash;1.000</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown("<hr class='pg-hr'>", unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px;color:#bbb;margin:0 0 10px 0;font-weight:600;letter-spacing:.05em;text-transform:uppercase;">Strict metrics</p>',
                unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="small")
    strict_cards = [
        ("Strict Precision", f"{m['s_prec']:.3f}", "Wilson 95% CI: 0.610-1.000",
         "Bootstrap 1.000-1.000 is boundary artifact &mdash; not proven perfect"),
        ("Strict Specificity", f"{m['s_spec']:.3f}", "Wilson 95% CI: 0.676-1.000",
         "0 spurious escalations on negative controls"),
        ("Strict F1", f"{m['s_f1']:.3f}", "Bootstrap 95% CI: 0.727-1.000", ""),
        ("Pairs Evaluated", "15", "7 positives &middot; 5 genuine neg &middot; 3 zero-report", ""),
    ]
    for col, (label, val, sub, note) in zip([c1, c2, c3, c4], strict_cards):
        with col:
            st.markdown(
                f'<div class="pg-card"><div class="pg-label">{label}</div>'
                f'<div class="pg-value">{val}</div><div class="pg-sub">{sub}</div>'
                + (f'<div class="pg-note">{note}</div>' if note else "")
                + "</div>",
                unsafe_allow_html=True,
            )
    st.markdown("<hr class='pg-hr'>", unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px;color:#bbb;margin:0 0 10px 0;font-weight:600;letter-spacing:.05em;text-transform:uppercase;">Lenient metrics (MONITOR counts as TP)</p>',
                unsafe_allow_html=True)
    l1, l2, l3, l4 = st.columns(4, gap="small")
    lenient_cards = [
        ("Lenient Precision", f"{m['l_prec']:.3f}", "Wilson 95% CI: 0.529-0.978"),
        ("Lenient Recall", f"{m['l_rec']:.3f}", "Wilson 95% CI: 0.646-1.000"),
        ("Lenient Specificity", f"{m['l_spec']:.3f}", "Wilson 95% CI: 0.529-0.978"),
        ("Lenient F1", f"{m['l_f1']:.3f}", "Bootstrap 95% CI: 0.769-1.000"),
    ]
    for col, (label, val, sub) in zip([l1, l2, l3, l4], lenient_cards):
        with col:
            st.markdown(
                f'<div class="pg-card"><div class="pg-label">{label}</div>'
                f'<div class="pg-value">{val}</div><div class="pg-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="callout"><strong>Strict vs. lenient:</strong> The single strict FN is '
        'montelukast::suicidal_ideation (MONITOR, not ESCALATE). Curated plausibility=LOW correctly '
        'modulates confidence to 0.664 &mdash; below the 0.70 ESCALATE threshold &mdash; despite '
        'FAERS MODERATE signal and PubMed Grade A evidence. Pharmacovigilance-correct behavior. '
        'Under lenient metrics it remains a True Positive. See the Disagreement Spotlight tab.</div>',
        unsafe_allow_html=True,
    )


# ===========================================================================
# VIEW 2 -- PER-PAIR TABLE + DRILL-DOWN
# ===========================================================================

def view_per_pair(df: pd.DataFrame) -> None:
    st.markdown(
        '<div class="pg-header"><div class="pg-title">Per-Pair Evaluation</div>'
        '<div class="pg-subtitle">All 15 evaluated drug-event pairs &middot; expand any row to see full evidence</div></div>',
        unsafe_allow_html=True,
    )
    fc1, fc2, fc3 = st.columns([1.4, 1.4, 1])
    with fc1:
        cat_f = st.selectbox("Category", ["All", "confirmed_positive",
                                           "genuine_negative_control", "zero_report_edge_case"],
                             label_visibility="collapsed")
    with fc2:
        esc_f = st.selectbox("Escalation", ["All", "ESCALATE", "MONITOR", "DO_NOT_ESCALATE"],
                             label_visibility="collapsed")
    with fc3:
        only_dis = st.checkbox("Disagreements only", value=False)
    fdf = df.copy()
    if cat_f != "All":
        fdf = fdf[fdf["category"] == cat_f]
    if esc_f != "All":
        fdf = fdf[fdf["escalation"] == esc_f]
    if only_dis:
        fdf = fdf[~fdf["match"]]
    st.markdown(
        f'<p style="font-size:11.5px;color:#ccc;margin:6px 0 10px;">Showing {len(fdf)} of {len(df)} pairs</p>',
        unsafe_allow_html=True,
    )
    COLS = [0.28, 1.3, 1.55, 1.35, 1.0, 0.65, 1.1, 0.85, 1.05, 1.05]
    HEADERS = ["#", "Drug", "Event", "Category", "Signal", "Grade",
               "Plausibility", "Conf", "Got", "Expected"]
    hcols = st.columns(COLS)
    for col, h in zip(hcols, HEADERS):
        col.markdown(f'<div class="th">{h}</div>', unsafe_allow_html=True)
    st.markdown('<div style="border-top:1px solid #e8e8e8;margin-bottom:3px;"></div>', unsafe_allow_html=True)
    for _, row in fdf.iterrows():
        r = row["_r"]
        ss = r.get("signal_stats", {})
        mech = r.get("mechanism", {})
        lit = r.get("literature", {})
        flag = "" if row["match"] else "!! "
        rcols = st.columns(COLS)
        rcols[0].markdown(f'<span style="font-size:11px;color:#ccc;font-family:monospace;">{flag}{row["idx"]}</span>', unsafe_allow_html=True)
        rcols[1].markdown(f'<span style="font-size:13px;font-weight:500;">{row["drug"]}</span>', unsafe_allow_html=True)
        rcols[2].markdown(f'<span style="font-size:12.5px;color:#555;">{row["event"]}</span>', unsafe_allow_html=True)
        rcols[3].markdown(cat_badge(row["category"]), unsafe_allow_html=True)
        rcols[4].markdown(signal_span(row["signal"]), unsafe_allow_html=True)
        rcols[5].markdown(grade_badge(row["grade"]), unsafe_allow_html=True)
        plaus = row["plausibility"]
        pc = {"HIGH": "#2a5a2a", "MODERATE": "#444", "LOW": "#bbb"}.get(plaus, "#bbb")
        pw = {"HIGH": "600", "MODERATE": "500", "LOW": "400"}.get(plaus, "400")
        rcols[6].markdown(f'<span style="color:{pc};font-weight:{pw};font-size:12px;">{plaus}</span>', unsafe_allow_html=True)
        conf = row["confidence"]
        rcols[7].markdown(f'<span class="mono">{f"{conf:.3f}" if conf is not None else "--"}</span>', unsafe_allow_html=True)
        rcols[8].markdown(esc_badge(row["escalation"]), unsafe_allow_html=True)
        rcols[9].markdown(esc_badge(row["expected"]), unsafe_allow_html=True)
        with st.expander(f"  {row['drug']}  -  {row['event']}  -- full evidence breakdown"):
            d1, d2 = st.columns(2, gap="medium")
            with d1:
                st.markdown('<div class="pg-label" style="margin-top:4px;">FAERS Signal</div>', unsafe_allow_html=True)
                prr = ss.get("prr")
                prr_disp = f"{prr:.2f}" if prr is not None else "n/a (zero co-occurrences)"
                rc = ss.get("report_count", 0)
                st.markdown(
                    f'<div class="mono" style="font-size:12.5px;color:#333;margin-bottom:10px;">'
                    f'PRR = {prr_disp}  |  Reports = {rc:,}<br>Signal: {signal_span(row["signal"])}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="pg-label">PubMed Evidence Summary</div>', unsafe_allow_html=True)
                ev = re.sub(r"^Final Grade:\s*\w+\n?", "", lit.get("evidence_summary", "")).strip()
                st.markdown(f'<div class="rationale">{ev}</div>', unsafe_allow_html=True)
            with d2:
                st.markdown('<div class="pg-label" style="margin-top:4px;">Mechanistic Plausibility</div>', unsafe_allow_html=True)
                plaus_rat = mech.get("plausibility_rationale", "")
                plaus_src = mech.get("plausibility_source", "")
                st.markdown(
                    f'<div class="rationale">{plaus_rat}</div>'
                    f'<div style="font-size:10.5px;color:#ccc;margin-top:3px;">source: {plaus_src}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="pg-label" style="margin-top:12px;">Confidence Decomposition</div>', unsafe_allow_html=True)
                conf_chart(r, key=f"cp_{row['idx']}")
        st.markdown('<div style="border-top:1px solid #f4f4f4;margin:2px 0;"></div>', unsafe_allow_html=True)


# ===========================================================================
# VIEW 3 -- DISAGREEMENT SPOTLIGHT
# ===========================================================================

def view_disagreements(reports: list) -> None:
    st.markdown(
        '<div class="pg-header"><div class="pg-title">Disagreement Spotlight</div>'
        '<div class="pg-subtitle">Two pairs where PharmaGuard outputs MONITOR rather than the expected label &mdash; '
        'both are correct, intended outcomes, not misses</div></div>',
        unsafe_allow_html=True,
    )
    montelukast_r = next((r for r in reports if "montelukast" in r.get("run_id", "")), None)
    metformin_r = next((r for r in reports if "metformin" in r.get("run_id", "")), None)
    cases = [
        {
            "report": montelukast_r,
            "drug": "montelukast", "event": "suicidal ideation",
            "category": "confirmed_positive", "expected": "ESCALATE", "got": "MONITOR",
            "epidemiology": (
                "FDA Boxed Warning (March 2020) for serious neuropsychiatric events including suicidal ideation. "
                "The FAERS signal is MODERATE (PRR=3.37, 1,259 reports) and PubMed returns Grade A evidence -- "
                "two abstracts contain ROR statistics with 95% CIs."
            ),
            "conclusion": (
                "MONITOR is the pharmacovigilance-correct output when a genuine epidemiological signal coexists "
                "with unresolved mechanistic uncertainty. The system correctly reflects that the mechanism is not "
                "established, not that the signal is absent. Under lenient scoring this is still a True Positive."
            ),
        },
        {
            "report": metformin_r,
            "drug": "metformin", "event": "hypoglycaemia",
            "category": "genuine_negative_control", "expected": "DO_NOT_ESCALATE", "got": "MONITOR",
            "epidemiology": (
                "FAERS contains approximately 9,340 reports for metformin + hypoglycaemia (MedDRA PT), "
                "PRR=10.73 (STRONG). This signal is heavily confounded: hypoglycemia in diabetic patients "
                "overwhelmingly results from concomitant insulin or sulfonylurea use, not from metformin monotherapy."
            ),
            "conclusion": (
                "MONITOR is the over-cautious but safety-correct outcome when 9,000+ spontaneous reports exist "
                "even after mechanistic de-weighting. The 0.40xPRR_score term floors confidence at 0.40, "
                "preventing DO_NOT_ESCALATE despite plausibility=LOW and Grade C. Architectural property, not a bug. "
                "Under strict metrics: FP=1. Under lenient: TN."
            ),
        },
    ]
    for i, case in enumerate(cases):
        if i > 0:
            st.markdown("<hr class='pg-hr'>", unsafe_allow_html=True)
        rpt = case["report"]
        if rpt is None:
            st.warning(f"Report for {case['drug']} not found in {OUTPUTS_DIR}")
            continue
        triage = rpt.get("triage", {})
        ss = rpt.get("signal_stats", {})
        lit = rpt.get("literature", {})
        mech = rpt.get("mechanism", {})
        conf = triage.get("confidence")
        conf_d = f"{conf:.3f}" if conf is not None else "--"
        signal = ss.get("prr_score_label", "--")
        grade = lit.get("evidence_grade", "--")
        plaus = mech.get("biological_plausibility", "--")
        ev_sum = re.sub(r"^Final Grade:\s*\w+\n?", "", lit.get("evidence_summary", "")).strip()
        plaus_r = mech.get("plausibility_rationale", "")
        st.markdown(
            f'<div class="spot-header">'
            f'<div style="display:flex;align-items:baseline;gap:14px;">'
            f'<div class="spot-drug">{case["drug"]}</div>'
            f'<div class="spot-event">+ {case["event"]}</div></div>'
            f'<div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;">'
            f'{cat_badge(case["category"])}'
            f'<span style="font-size:12px;color:#bbb;">expected:</span> {esc_badge(case["expected"])}'
            f'<span style="font-size:12px;color:#bbb;">&rarr; got:</span> {esc_badge(case["got"])}'
            f'<span style="font-size:12px;color:#bbb;margin-left:6px;">'
            f'Signal: {signal} | Grade: {grade} | Plausibility: {plaus} | '
            f'Confidence: <span class="mono">{conf_d}</span></span></div></div>',
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns(2, gap="medium")
        with col_a:
            st.markdown('<div class="pg-label">Epidemiological Evidence</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="rationale">{case["epidemiology"]}</div>', unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="pg-label">PubMed Evidence Summary (actual output)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="rationale">{ev_sum}</div>', unsafe_allow_html=True)
        with col_b:
            st.markdown('<div class="pg-label">Mechanistic Plausibility (actual rationale)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="rationale">{plaus_r}</div>', unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="pg-label">Why MONITOR Is Correct Here</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="conclusion">{case["conclusion"]}</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        conf_chart(rpt, key=f"spot_{case['drug']}")
    st.markdown("<hr class='pg-hr'>", unsafe_allow_html=True)
    st.markdown(
        '<div class="callout"><strong>Design note: Strict/Lenient dual-metric framework.</strong> '
        'These two cases are why PharmaGuard reports both metrics as first-class outputs. '
        'Strict metrics correctly show reduced confidence under genuine uncertainty (FN=1, FP=0). '
        'Lenient metrics correctly show the signal was never dismissed (TP=7, FP=1). '
        'A single-metric evaluation would obscure this distinction &mdash; see DECISIONS.md section 14.</div>',
        unsafe_allow_html=True,
    )


# ===========================================================================
# VIEW 4 -- BASELINE COMPARISON
# ===========================================================================

def view_baseline(prod_reports: list, base_reports: list) -> None:
    st.markdown(
        '<div class="pg-header"><div class="pg-title">Baseline Comparison</div>'
        '<div class="pg-subtitle">PharmaGuard (tool-grounded, 3-source pipeline) vs. single-shot LLM baseline (no tools)</div></div>',
        unsafe_allow_html=True,
    )

    def _table(d: dict, is_prod: bool) -> str:
        title = ("PharmaGuard &mdash; Tool-Grounded" if is_prod
                 else "Single-Shot LLM Baseline &mdash; No Tools")
        icon = "[P]" if is_prod else "[B]"
        return (
            f'<div class="cmp-col"><div class="cmp-title">{icon} {title}</div>'
            f'<table class="mt"><thead><tr><th>Metric</th>'
            f'<th style="text-align:right">Strict</th>'
            f'<th style="text-align:right">Lenient</th></tr></thead><tbody>'
            f'<tr><td>Precision</td><td class="num">{d["s_prec"]:.3f}</td><td class="num">{d["l_prec"]:.3f}</td></tr>'
            f'<tr><td>Recall</td><td class="num">{d["s_rec"]:.3f}</td><td class="num">{d["l_rec"]:.3f}</td></tr>'
            f'<tr><td>Specificity</td><td class="num">{d["s_spec"]:.3f}</td><td class="num">{d["l_spec"]:.3f}</td></tr>'
            f'<tr><td>F1</td><td class="num">{d["s_f1"]:.3f}</td><td class="num">{d["l_f1"]:.3f}</td></tr>'
            f'<tr><td>Over-Caution Rate</td><td class="num" colspan="2" style="text-align:right">{d["ocr"]:.1f}%</td></tr>'
            f'</tbody></table></div>'
        )

    mc1, mc2 = st.columns(2, gap="medium")
    with mc1:
        st.markdown(_table(PROD, True), unsafe_allow_html=True)
    with mc2:
        st.markdown(_table(BASE, False), unsafe_allow_html=True)
    st.markdown("<hr class='pg-hr'>", unsafe_allow_html=True)
    st.markdown(
        '<div class="pg-title" style="font-size:16px;margin-bottom:3px;">Key Illustration: liraglutide + pancreatic cancer</div>'
        '<div class="pg-subtitle" style="margin-bottom:18px;">Clearest single example of what tool-grounded triage adds over ungrounded LLM recall</div>',
        unsafe_allow_html=True,
    )
    prod_lira = next((r for r in prod_reports if "liraglutide" in r.get("run_id", "")), None)
    base_lira = next((r for r in base_reports if "liraglutide" in r.get("run_id", "")), None)
    if not prod_lira or not base_lira:
        st.error("Could not find liraglutide reports -- run the evaluation pipeline first.")
        return
    lc1, lc2 = st.columns(2, gap="medium")

    def _case_col(col, title, rpt, expected, notes, col_key):
        triage = rpt.get("triage", {})
        esc = triage.get("escalation", "--")
        conf = triage.get("confidence")
        trace = triage.get("agent_reasoning_trace", [])
        conf_d = f"{conf:.3f}" if conf is not None else "--"
        with col:
            st.markdown(
                f'<div class="cmp-col"><div class="cmp-title">{title}</div>'
                f'<div style="display:flex;gap:10px;align-items:center;margin-bottom:4px;">'
                f'{esc_badge(esc)}'
                f'<span style="font-size:12px;color:#bbb;">expected: {expected}</span></div>'
                f'<div class="mono" style="font-size:12px;color:#bbb;margin-bottom:12px;">confidence = {conf_d}</div>',
                unsafe_allow_html=True,
            )
            if trace:
                st.markdown(
                    f'<div class="rationale" style="font-size:12.5px;">{"<br>".join(trace)}</div>',
                    unsafe_allow_html=True,
                )
            if notes:
                items = "".join(f"<li>{n}</li>" for n in notes)
                st.markdown(
                    f'<ul style="font-size:12px;color:#999;margin:10px 0 0;padding-left:18px;line-height:1.7;">{items}</ul>',
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

    _case_col(lc1, "PharmaGuard &mdash; Tool-Grounded", prod_lira, "DO_NOT_ESCALATE",
              ["FAERS: 0 co-occurrences &rarr; NO_SIGNAL gate &rarr; DO_NOT_ESCALATE",
               "Confidence 0.300 = 0.40x0 + 0.40x0.5 + 0.20x0.5",
               "FAERS disproportionality overrides literature plausibility",
               "FDA/EMA 2014 joint review: no causal link established"], "lira_prod")
    _case_col(lc2, "Single-Shot LLM Baseline &mdash; No Tools", base_lira, "DO_NOT_ESCALATE",
              ["No FAERS query &mdash; no signal check performed",
               "Confidence 0.85 is raw LLM self-report, not formula-grounded",
               "Recalls historical regulatory concern, not its resolution",
               "Confuses 'this was investigated' with 'this was confirmed'"], "lira_base")
    st.markdown("<hr class='pg-hr'>", unsafe_allow_html=True)
    st.markdown(
        '<div class="callout"><strong>Note: metformin::hypoglycaemia.</strong> '
        'Both systems output MONITOR &mdash; but for fundamentally different reasons. '
        'The baseline does so via ungrounded clinical caution. '
        'PharmaGuard does so because a 9,340-report STRONG FAERS signal (PRR=10.73) '
        'floors the 0.40xPRR_score term at 0.40, while correctly assigning plausibility=LOW and Grade C '
        'to discount the confounded polypharmacy signal. '
        'See DECISIONS.md section 21 and the Disagreement Spotlight tab.</div>',
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
            f"No reports found in {OUTPUTS_DIR}.\n\n"
            "Run 'python scripts/run_eval.py' first to generate evaluation outputs."
        )
        st.stop()
    tab1, tab2, tab3, tab4 = st.tabs([
        "  Overview  ",
        "  Per-Pair Table  ",
        "  Disagreement Spotlight  ",
        "  Baseline Comparison  ",
    ])
    with tab1:
        view_overview()
    with tab2:
        view_per_pair(df)
    with tab3:
        view_disagreements(prod_reports)
    with tab4:
        view_baseline(prod_reports, base_reports)


if __name__ == "__main__":
    main()
