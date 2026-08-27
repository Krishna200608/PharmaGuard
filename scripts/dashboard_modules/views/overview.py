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
from ..data_loader import PROD_METRICS


def view_overview(logo_path: Path | None = None, stability_path: Path | None = None) -> None:
    """Render the Overview tab with benchmark cards and LOO stability block."""
    if logo_path and logo_path.exists():
        c_logo, c_title = st.columns([0.06, 0.94], gap='medium')
        with c_logo:
            st.image(str(logo_path), width=54)
        with c_title:
            st.markdown(
                '<div class="pg-header" style="margin-bottom: 0px; border-bottom: none; padding-bottom: 0px;">'
                '<div class="pg-title">PharmaGuard — Evaluation Overview</div>'
                '<div class="pg-subtitle">Sprint 3 final benchmark · 15 drug–event pairs · plausibility ratings v1.0</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="pg-header">'
            '<div class="pg-title">PharmaGuard — Evaluation Overview</div>'
            '<div class="pg-subtitle">Sprint 3 final benchmark · 15 drug–event pairs · plausibility ratings v1.0</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    m = PROD_METRICS

    col_hero, col_flank = st.columns([2.1, 1.1], gap='large')
    with col_hero:
        st.markdown(
            f'<div class="pg-hero-card">'
            f'<div class="pg-stat-label">Strict Recall — Primary Benchmark Result</div>'
            f'<div class="pg-hero-value">{m["s_rec"]:.3f}</div>'
            f'<div class="pg-hero-sub">6 of 7 confirmed positives correctly escalated</div>'
            f'<div class="pg-hero-note">'
            f'Lenient Recall: <strong style="color:var(--text);">1.000</strong> (7/7) — '
            f'signal is never missed; confidence is modulated under mechanistic uncertainty.'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_flank:
        st.markdown(
            f'<div class="pg-card">'
            f'<div class="pg-stat-label">Over-Caution Rate</div>'
            f'<div class="pg-stat-value">12.5%</div>'
            f'<div class="pg-stat-sub">1 of 8 negative controls → MONITOR</div>'
            f'<div style="height: 14px; border-bottom: 1px solid var(--divider); margin-bottom: 12px;"></div>'
            f'<div class="pg-stat-label">Spurious False Alarms</div>'
            f'<div class="pg-stat-value">FP = 0</div>'
            f'<div class="pg-stat-sub">Strict Wilson 95% CI: 0.610–1.000</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)

    st.markdown('<div class="pg-section-label">Strict Evaluation Metrics</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap='medium')
    strict_metrics = [
        ('Strict Precision', f"{m['s_prec']:.3f}", 'Wilson 95% CI: 0.610–1.000',
         'Bootstrap 1.000–1.000 is boundary artifact'),
        ('Strict Specificity', f"{m['s_spec']:.3f}", 'Wilson 95% CI: 0.676–1.000',
         '0 spurious escalations on negative controls'),
        ('Strict F1', f"{m['s_f1']:.3f}", 'Bootstrap 95% CI: 0.727–1.000', 'Harmonic mean under strict gating'),
        ('Pairs Evaluated', '15', '7 confirmed pos · 5 genuine neg', '3 zero-report edge cases included'),
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
        ('Lenient Precision', f"{m['l_prec']:.3f}", 'Wilson 95% CI: 0.529–0.978', 'Includes modulated signals'),
        ('Lenient Recall', f"{m['l_rec']:.3f}", 'Wilson 95% CI: 0.646–1.000', '7 of 7 true signals captured'),
        ('Lenient Specificity', f"{m['l_spec']:.3f}", 'Wilson 95% CI: 0.529–0.978', '7 of 8 negative controls cleared'),
        ('Lenient F1', f"{m['l_f1']:.3f}", 'Bootstrap 95% CI: 0.769–1.000', 'Harmonic mean under lenient scoring'),
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

    # ── LEAVE-ONE-OUT STABILITY BLOCK ──
    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)
    st.markdown('<div class="pg-section-label">Leave-One-Out (LOO) Stability Analysis (15 Iterations)</div>', unsafe_allow_html=True)

    if stability_path is None:
        stability_path = Path(__file__).resolve().parents[3] / "outputs" / "stability" / "loo_analysis.json"

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
            'LOO stability analysis not yet generated — run <code>python scripts/stability_analysis.py</code>'
            '</div>',
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