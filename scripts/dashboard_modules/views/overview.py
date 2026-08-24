"""
View 1: Overview
================
High-level benchmark metrics (Strict & Lenient Recall, Precision, Wilson CIs).
Structured card layouts with subtle depth hierarchy and theme adaptability.
"""
from __future__ import annotations

from pathlib import Path
import streamlit as st
from ..data_loader import PROD_METRICS


def view_overview(logo_path: Path | None = None) -> None:
    """Render the Overview tab."""
    if logo_path and logo_path.exists():
        c_logo, c_title = st.columns([0.06, 0.94], gap='medium')
        with c_logo:
            st.image(str(logo_path), width=58)
        with c_title:
            st.markdown(
                '<div class="pg-header" style="margin-bottom: 0px; border-bottom: none; padding-bottom: 0px;">'
                '<div class="pg-title">PharmaGuard — Evaluation Overview</div>'
                '<div class="pg-subtitle">Sprint 3 final benchmark · 15 drug–event pairs · plausibility ratings v1.0</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div style="height: 18px;"></div>', unsafe_allow_html=True)
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
            f'Lenient Recall: <strong style="color:var(--pg-text-primary);">1.000</strong> (7/7) — '
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
            f'<div style="height: 16px; border-bottom: 1px solid var(--pg-divider); margin-bottom: 14px;"></div>'
            f'<div class="pg-stat-label">Spurious False Alarms</div>'
            f'<div class="pg-stat-value">FP = 0</div>'
            f'<div class="pg-stat-sub">Strict Wilson 95% CI: 0.610–1.000</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
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
                f'<div class="pg-stat-label">{label}</div>'
                f'<div class="pg-stat-value">{val}</div>'
                f'<div class="pg-stat-sub">{sub}</div>'
                f'<div class="pg-stat-note">{note}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
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
                f'<div class="pg-stat-label">{label}</div>'
                f'<div class="pg-stat-value">{val}</div>'
                f'<div class="pg-stat-sub">{sub}</div>'
                f'<div class="pg-stat-note">{note}</div>'
                f'</div>',
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
