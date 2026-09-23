"""
View 1: Overview
================
High-level benchmark metrics (Strict & Lenient Recall, Precision, Wilson CIs).
Structured card layouts with subtle depth hierarchy and theme adaptability.
Includes Leave-One-Out (LOO) stability analysis block.
"""
from __future__ import annotations

import json
from pathlib import Path
import streamlit as st
from ..components import render_therapeutic_stratification_table
from ..data_loader import PROD_METRICS, get_stratified_evaluation


def view_overview(
    logo_path: Path | None = None,
    stability_path: Path | None = None,
    theme: str = "light",
    reports_dir: Path | None = None,
    gt_path: Path | None = None,
    metrics: dict | None = None,
    cohort_name: str = "Core Benchmark",
    cohort_desc: str = "Sprint 3 final benchmark · 15 drug–event pairs · plausibility ratings v1.0",
) -> None:
    """Render the Overview tab with benchmark cards, LOO stability, and therapeutic area stratification."""
    if logo_path and logo_path.exists():
        c_logo, c_title = st.columns([0.06, 0.94], gap='medium')
        with c_logo:
            st.image(str(logo_path), width=54)
        with c_title:
            st.markdown(
                '<div class="pg-header" style="margin-bottom: 0px; border-bottom: none; padding-bottom: 0px;">'
                f'<div class="pg-title">PharmaGuard — {cohort_name} Overview</div>'
                f'<div class="pg-subtitle">{cohort_desc}</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="pg-header">'
            f'<div class="pg-title">PharmaGuard — {cohort_name} Overview</div>'
            f'<div class="pg-subtitle">{cohort_desc}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    m = metrics if metrics is not None else PROD_METRICS

    # Extract dynamic counts
    s_tp = m.get('s_tp', 6 if m == PROD_METRICS else int(round(m['s_rec'] * m.get('total', 15) / 2)))
    s_fn = m.get('s_fn', 1 if m == PROD_METRICS else 0)
    pos_total = s_tp + s_fn if (s_tp + s_fn) > 0 else int(m.get('total', 15) / 2)
    l_tp = m.get('l_tp', 7 if m == PROD_METRICS else int(round(m['l_rec'] * pos_total)))
    s_fp = m.get('s_fp', 0)
    s_tn = m.get('s_tn', 8 if m == PROD_METRICS else (m.get('total', 15) - pos_total))
    neg_total = s_tn + s_fp
    l_fp = m.get('l_fp', 1 if m == PROD_METRICS else (neg_total - int(round(m['l_spec'] * neg_total))))
    total_n = m.get('total', pos_total + neg_total)

    s_ci = m.get('s_ci', [0.610, 1.000])
    l_ci = m.get('l_ci', [0.646, 1.000])

    col_hero, col_flank = st.columns([2.1, 1.1], gap='large')
    with col_hero:
        st.markdown(
            f'<div class="pg-hero-card">'
            f'<div class="pg-stat-label">Strict Recall — Primary Benchmark Result</div>'
            f'<div class="pg-hero-value">{m["s_rec"]:.3f}</div>'
            f'<div class="pg-hero-sub">{s_tp} of {pos_total} confirmed positives correctly escalated</div>'
            f'<div class="pg-hero-note">'
            f'Lenient Recall: <strong style="color:var(--text);">{m["l_rec"]:.3f}</strong> ({l_tp}/{pos_total}) — '
            f'signal capture under dual-metric standard; confidence modulated under mechanistic uncertainty.'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_flank:
        st.markdown(
            f'<div class="pg-card">'
            f'<div class="pg-stat-label">Over-Caution Rate</div>'
            f'<div class="pg-stat-value">{m.get("ocr", 0.0)}%</div>'
            f'<div class="pg-stat-sub">{l_fp} of {neg_total} negative controls → MONITOR</div>'
            f'<div style="height: 14px; border-bottom: 1px solid var(--divider); margin-bottom: 12px;"></div>'
            f'<div class="pg-stat-label">Spurious False Alarms</div>'
            f'<div class="pg-stat-value">FP = {s_fp}</div>'
            f'<div class="pg-stat-sub">Strict Wilson 95% CI: {s_ci[0]:.3f}–{s_ci[1]:.3f}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)

    st.markdown('<div class="pg-section-label">Strict Evaluation Metrics</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap='medium')
    strict_metrics = [
        ('Strict Precision', f"{m['s_prec']:.3f}", f"Wilson 95% CI: {s_ci[0]:.3f}–{s_ci[1]:.3f}",
         'Zero false-alarm escalations' if s_fp == 0 else f'{s_fp} false alarms'),
        ('Strict Specificity', f"{m['s_spec']:.3f}", f"{s_tn} of {neg_total} negative controls cleared",
         '0 spurious escalations on negative controls' if s_fp == 0 else ''),
        ('Strict F1', f"{m['s_f1']:.3f}", 'Harmonic mean under strict gating', 'Strict policy: ESCALATE only'),
        ('Pairs Evaluated', str(total_n), f"{pos_total} positive controls · {neg_total} negative controls",
         'Balanced evaluation cohort' if pos_total == neg_total else f'{total_n} total evaluated pairs'),
    ]
    for col, (label, val, sub, note) in zip([c1, c2, c3, c4], strict_metrics):
        with col:
            st.markdown(
                f'<div class="pg-stat-card">'
                f'<div>'
                f'<div class="pg-stat-label">{label}</div>'
                f'<div class="pg-stat-value">{val}</div>'
                f'</div>'
                f'<div>'
                f'<div class="pg-stat-sub">{sub}</div>'
                f'<div class="pg-stat-note">{note}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)

    st.markdown('<div class="pg-section-label">Lenient Evaluation Metrics (MONITOR counts as True Positive)</div>', unsafe_allow_html=True)
    l1, l2, l3, l4 = st.columns(4, gap='medium')
    lenient_metrics = [
        ('Lenient Precision', f"{m['l_prec']:.3f}", f"{l_tp} true positive signals captured", 'Includes modulated signals'),
        ('Lenient Recall', f"{m['l_rec']:.3f}", f"Wilson 95% CI: {l_ci[0]:.3f}–{l_ci[1]:.3f}", f'{l_tp} of {pos_total} true signals flagged'),
        ('Lenient Specificity', f"{m['l_spec']:.3f}", f"{neg_total - l_fp} of {neg_total} negative controls cleared", f'{l_fp} negative controls monitored'),
        ('Lenient F1', f"{m['l_f1']:.3f}", 'Harmonic mean under lenient scoring', 'Dual-metric evaluation standard'),
    ]
    for col, (label, val, sub, note) in zip([l1, l2, l3, l4], lenient_metrics):
        with col:
            st.markdown(
                f'<div class="pg-stat-card">'
                f'<div>'
                f'<div class="pg-stat-label">{label}</div>'
                f'<div class="pg-stat-value">{val}</div>'
                f'</div>'
                f'<div>'
                f'<div class="pg-stat-sub">{sub}</div>'
                f'<div class="pg-stat-note">{note}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if "Core" in cohort_name:
        # ── LEAVE-ONE-OUT STABILITY BLOCK ──
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
        st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
        st.markdown('<div class="pg-section-label">Leave-One-Out (LOO) Stability Analysis (15 Iterations)</div>', unsafe_allow_html=True)

        if stability_path is None:
            stability_path = Path(__file__).resolve().parents[3] / "outputs" / "research" / "stability" / "loo_analysis.json"

        stability_data = None
        if stability_path and stability_path.exists():
            try:
                with open(stability_path, "r", encoding="utf-8") as f:
                    stability_data = json.load(f)
            except Exception:
                stability_data = None

        if stability_data and "summary" in stability_data:
            summ = stability_data["summary"]
            brittle = stability_data.get("brittle_pairs", {})
            s_f1 = summ.get("strict", {}).get("f1", {})
            l_f1 = summ.get("lenient", {}).get("f1", {})

            s_f1_mean = s_f1.get("mean", 0.0)
            s_f1_sd = s_f1.get("sd", 0.0)
            s_f1_min = s_f1.get("min", 0.0)
            s_f1_max = s_f1.get("max", 0.0)

            l_f1_mean = l_f1.get("mean", 0.0)
            l_f1_sd = l_f1.get("sd", 0.0)
            l_f1_min = l_f1.get("min", 0.0)
            l_f1_max = l_f1.get("max", 0.0)

            s_brittle_list = brittle.get("strict_brittle_pairs", ["None"])
            s_brittle_str = s_brittle_list[0] if s_brittle_list else "None"
            s_swing = brittle.get("max_strict_f1_swing", 0.0)

            l_brittle_list = brittle.get("lenient_brittle_pairs", ["None"])
            l_brittle_str = l_brittle_list[0] if l_brittle_list else "None"
            l_swing = brittle.get("max_lenient_f1_swing", 0.0)

            b1, b2, b3, b4 = st.columns(4, gap='medium')
            loo_cards = [
                ('Strict F1 (Mean ± SD)', f"{s_f1_mean:.3f} ± {s_f1_sd:.3f}",
                 f"Range: {s_f1_min:.3f}–{s_f1_max:.3f} (15 folds)", 'Consistent across single-pair exclusions'),
                ('Strict Most Brittle Pair', s_brittle_str,
                 f"Max swing: ΔF1 = +{s_swing:.3f} (to 1.000)", 'Removing single strict FN eliminates FN penalty'),
                ('Lenient F1 (Mean ± SD)', f"{l_f1_mean:.3f} ± {l_f1_sd:.3f}",
                 f"Range: {l_f1_min:.3f}–{l_f1_max:.3f} (15 folds)", 'Robust ceiling under lenient modulation'),
                ('Lenient Most Brittle Pair', l_brittle_str,
                 f"Max swing: ΔF1 = +{l_swing:.3f} (to 1.000)", 'Removing single lenient FP eliminates FP penalty'),
            ]
            for col, (label, val, sub, note) in zip([b1, b2, b3, b4], loo_cards):
                with col:
                    st.markdown(
                        f'<div class="pg-stat-card">'
                        f'<div>'
                        f'<div class="pg-stat-label">{label}</div>'
                        f'<div class="pg-stat-value" style="font-size:15px;word-break:break-all;">{val}</div>'
                        f'</div>'
                        f'<div>'
                        f'<div class="pg-stat-sub">{sub}</div>'
                        f'<div class="pg-stat-note">{note}</div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown(
                '<div style="font-family:\'JetBrains Mono\', monospace; font-size:12px; color:var(--text-dim); padding: 12px 0;">'
                'LOO stability analysis not yet generated — run <code>python scripts/research/stability_analysis.py</code>'
                '</div>',
                unsafe_allow_html=True,
            )

        # ── THERAPEUTIC AREA STRATIFICATION (WHO ATC LEVEL 1) ──
        repo_root = Path(__file__).resolve().parents[3]
        if reports_dir is None:
            reports_dir = repo_root / "outputs" / "core"
        if gt_path is None:
            gt_path = repo_root / "pharmaguard" / "data" / "ground_truth.json"

        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
        st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
        strat_data = get_stratified_evaluation(reports_dir, gt_path)
        render_therapeutic_stratification_table(
            strat_data,
            title="Performance by Therapeutic Area (WHO ATC Level 1 — Core Benchmark)",
            theme=theme,
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
    else:
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
        st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="pg-card" style="margin-top: 14px;">'
            f'<div class="pg-stat-label">Cohort Architecture & Evidence Drill-Down</div>'
            f'<div style="font-size: 13.5px; color: var(--text); margin-top: 6px; line-height: 1.6;">'
            f'This secondary evaluation cohort (<strong>{total_n} pairs</strong>) was benchmarked using local <strong>Ollama (qwen2.5:7b)</strong> and multi-source evidence synthesis. '
            f'Detailed per-pair signals, PubMed evidence grades, and ChEMBL plausibility rationales are available in the <strong>Per-Pair Table</strong> tab.'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )