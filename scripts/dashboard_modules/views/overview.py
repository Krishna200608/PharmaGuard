"""
View 1: Overview
================
High-level benchmark metrics (Strict & Lenient Recall, Precision, Wilson CIs).
"""
from __future__ import annotations

from pathlib import Path
import streamlit as st
from ..data_loader import PROD_METRICS


def view_overview(logo_path: Path | None = None) -> None:
    """Render the Overview tab."""
    if logo_path and logo_path.exists():
        c_logo, c_title = st.columns([0.07, 0.93], gap='medium')
        with c_logo:
            st.image(str(logo_path), width=54)
        with c_title:
            st.markdown(
                '<div class="pg-header" style="margin-bottom: 0px;">'
                '<div class="pg-title">PharmaGuard — Evaluation Overview</div>'
                '<div class="pg-subtitle">Sprint 3 final benchmark · 15 drug–event pairs · plausibility ratings v1.0</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="pg-header">'
            '<div class="pg-title">PharmaGuard — Evaluation Overview</div>'
            '<div class="pg-subtitle">Sprint 3 final benchmark · 15 drug–event pairs · plausibility ratings v1.0</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    m = PROD_METRICS

    col_hero, col_flank = st.columns([2.3, 1], gap='large')
    with col_hero:
        st.markdown(
            f'<div style="padding: 6px 0;">'
            f'<div class="pg-stat-label">Strict Recall — Primary Benchmark Result</div>'
            f'<div class="pg-hero-value">{m["s_rec"]:.3f}</div>'
            f'<div class="pg-hero-sub">6 of 7 confirmed positives correctly escalated</div>'
            f'<div class="pg-hero-note">'
            f'Lenient Recall: <strong style="color:#0f172a;">1.000</strong> (7/7) — '
            f'signal is never missed; confidence is modulated under mechanistic uncertainty.'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_flank:
        st.markdown(
            f'<div style="border-left: 1px solid #e2e8f0; padding-left: 24px;">'
            f'<div class="pg-stat-label">Over-Caution Rate</div>'
            f'<div class="pg-stat-value">12.5%</div>'
            f'<div class="pg-stat-sub">1 of 8 negative controls → MONITOR</div>'
            f'<div style="height: 18px;"></div>'
            f'<div class="pg-stat-label">Spurious False Alarms</div>'
            f'<div class="pg-stat-value">FP = 0</div>'
            f'<div class="pg-stat-sub">Strict Wilson 95% CI: 0.610–1.000</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)

    st.markdown('<div class="pg-section-label">Strict Evaluation Metrics</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap='medium')
    strict_metrics = [
        ('Strict Precision', f"{m['s_prec']:.3f}", 'Wilson 95% CI: 0.610–1.000',
         'Bootstrap 1.000–1.000 is a boundary artifact — not proven perfect'),
        ('Strict Specificity', f"{m['s_spec']:.3f}", 'Wilson 95% CI: 0.676–1.000',
         '0 spurious escalations on negative controls'),
        ('Strict F1', f"{m['s_f1']:.3f}", 'Bootstrap 95% CI: 0.727–1.000', ''),
        ('Pairs Evaluated', '15', '7 confirmed pos · 5 genuine neg · 3 zero-report', ''),
    ]
    for col, (label, val, sub, note) in zip([c1, c2, c3, c4], strict_metrics):
        with col:
            st.markdown(
                f'<div class="pg-stat-label">{label}</div>'
                f'<div class="pg-stat-value">{val}</div>'
                f'<div class="pg-stat-sub">{sub}</div>'
                + (f'<div class="pg-stat-note">{note}</div>' if note else '')
                + '<div style="height: 8px;"></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)

    st.markdown('<div class="pg-section-label">Lenient Evaluation Metrics (MONITOR counts as True Positive)</div>', unsafe_allow_html=True)
    l1, l2, l3, l4 = st.columns(4, gap='medium')
    lenient_metrics = [
        ('Lenient Precision', f"{m['l_prec']:.3f}", 'Wilson 95% CI: 0.529–0.978'),
        ('Lenient Recall', f"{m['l_rec']:.3f}", 'Wilson 95% CI: 0.646–1.000'),
        ('Lenient Specificity', f"{m['l_spec']:.3f}", 'Wilson 95% CI: 0.529–0.978'),
        ('Lenient F1', f"{m['l_f1']:.3f}", 'Bootstrap 95% CI: 0.769–1.000'),
    ]
    for col, (label, val, sub) in zip([l1, l2, l3, l4], lenient_metrics):
        with col:
            st.markdown(
                f'<div class="pg-stat-label">{label}</div>'
                f'<div class="pg-stat-value">{val}</div>'
                f'<div class="pg-stat-sub">{sub}</div>'
                f'<div style="height: 8px;"></div>',
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
