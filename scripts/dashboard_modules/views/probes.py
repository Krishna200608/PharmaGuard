"""
View 5: Methodology Audits & Epistemic Self-Probes
=================================================
Targeted honesty probes and adversarial audits:
  - Section A: Adversarial Leakage Critic (DECISIONS.md §19, §27)
  - Section B: Polypharmacy Confounding Self-Probe (DECISIONS.md §21, §28)
  - Section C: Before/After Spotlight on Metformin::Hypoglycaemia

CRITICAL SCOPE DISTINCTION:
These analyses are isolated methodology audits on select probe pairs to test
internal consistency and epistemic honesty. They are NOT part of the frozen
15-pair benchmark.
Uses Google Material Icons instead of platform emojis.
"""
from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

from ..components import render_conf_chart, esc_badge, material_icon


def view_probes(repo_root: Path | None = None, theme: str = "light") -> None:
    """Render the Methodology Probes view with graceful fallbacks and Google Material Icons."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[3]
    elif (repo_root / "outputs").is_dir() is False and repo_root.name == "core":
        repo_root = repo_root.parents[1]

    is_dark = (theme == "dark")

    st.markdown(
        '<div class="pg-header">'
        '<div class="pg-title">Methodology Audits & Epistemic Self-Probes</div>'
        '<div class="pg-subtitle">Adversarial leakage criticism · polypharmacy confounding de-biasing · honesty self-probes</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Top Scope Disclaimer Banner ──
    banner_bg = "rgba(242, 184, 75, 0.08)" if is_dark else "rgba(245, 158, 11, 0.06)"
    banner_bd = "#F2B84B" if is_dark else "#D97706"
    banner_title_color = "#FCD34D" if is_dark else "#B45309"
    banner_txt_color = "#E2E8F0" if is_dark else "#334155"
    warn_icon = material_icon("warning", size=19, color=banner_title_color, extra_style="vertical-align:-4px;")

    st.markdown(
        f'<div style="background:{banner_bg}; border-left:4px solid {banner_bd}; border-top:1px solid {banner_bd}; '
        f'border-right:1px solid {banner_bd}; border-bottom:1px solid {banner_bd}; border-radius:0 8px 8px 0; '
        f'padding:16px 20px; margin-bottom:24px;">'
        f'<div style="font-weight:700; font-size:13.5px; color:{banner_title_color}; letter-spacing:0.04em; margin-bottom:6px; display:inline-flex; align-items:center;">'
        f'{warn_icon}METHODOLOGICAL AUDIT & ISOLATED SELF-PROBE NOTICE'
        f'</div>'
        f'<div style="font-size:13px; line-height:1.6; color:{banner_txt_color};">'
        f'The evaluations displayed in this panel represent <strong>targeted epistemic self-probes and adversarial stress-tests</strong> '
        f'executed on specific edge-case pairs (as documented in <code>DECISIONS.md</code> §17, §19, §21, §27, and §28).<br>'
        f'<strong>These probes are NOT part of the frozen 15-pair production benchmark</strong> and are intentionally isolated to verify '
        f'parametric leakage resistance, polypharmacy discounting, and model honesty without mutating production results.'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # Section A: Adversarial Leakage Critic
    # -----------------------------------------------------------------------
    st.markdown('<div class="pg-section-label">Section A — Adversarial Mechanistic Critic (DECISIONS.md §19, §27)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:13.5px; color:var(--text-secondary); margin-bottom:14px; line-height:1.5;">'
        'Inspired by information-asymmetry verification patterns (such as the <strong>MARCH framework, ACL 2026</strong>), '
        'an independent adversarial critic reviews the primary agent\'s free-text rationale without access to the drug name, '
        'event term, or primary score. The critic identifies memorized regulatory warnings, clinical trial citations, or '
        'parametric recall phrases, re-evaluating the plausibility based solely on genuinely deduced biochemical mechanisms.'
        '</div>',
        unsafe_allow_html=True,
    )

    critic_file = repo_root / "outputs" / "experiments" / "critic_probe" / "leakage_critique_results.json"
    if not critic_file.exists():
        st.info("Adversarial critic results not yet generated. Run `python scripts/research/run_critic_probe.py`.")
    else:
        try:
            with open(critic_file, "r", encoding="utf-8") as f:
                critic_data = json.load(f)
            cases = critic_data.get("probe_cases", [])

            # High-level summary callout for montelukast with Google Material Star icon
            primary_color = "#818CF8" if is_dark else "#4F46E5"
            star_icon = material_icon("star", size=17, color=primary_color, extra_style="vertical-align:-3px;")
            st.markdown(
                f'<div style="background:rgba(79, 70, 229, 0.08); border-left:3.5px solid {primary_color}; padding:12px 16px; '
                f'border-radius:0 6px 6px 0; margin-bottom:16px; font-size:13px; color:var(--text); line-height:1.5;">'
                f'<span style="font-weight:700; color:{primary_color}; display:inline-flex; align-items:center; margin-right:4px;">'
                f'{star_icon}Flagship Epistemic Result (Montelukast):</span> When the critic strips away the memorized '
                f'FDA boxed warning justification from the agent\'s rationale, the mechanistic plausibility rating '
                f'<strong>drops from MODERATE (0.50) to LOW (0.00)</strong>. This confirms that without regulatory leakage, '
                f'Montelukast\'s signal is naturally restrained by mechanistic uncertainty, resolving the Sprint 3 ablation gap (§19).'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Table for critic cases
            rows_html = []
            for c in cases:
                drug = c.get("drug", "")
                event = c.get("event", "").replace("_", " ")
                orig_p = c.get("original_plausibility", "")
                crit = c.get("critic_evaluation", {})
                leaked = crit.get("leaked", False)
                phrases = crit.get("leak_phrases", [])
                mech_only = crit.get("mechanistic_only_score", "")
                notes = crit.get("rationale_critique", "")

                leak_badge = '<span class="b-zero" style="font-weight:700;">LEAK DETECTED</span>' if leaked else '<span class="b-esc">CLEAN</span>'
                highlight_style = "background:rgba(129, 140, 248, 0.06); font-weight:600;" if drug == "montelukast" else ""

                phrases_chips = "".join([
                    f'<span style="background:rgba(239, 68, 68, 0.12); color:#EF4444; padding:2px 6px; border-radius:4px; '
                    f'font-size:11px; margin-right:4px; display:inline-block; margin-bottom:3px; font-family:\'JetBrains Mono\', monospace;">'
                    f'"{p}"</span>'
                    for p in phrases
                ]) if phrases else "<em>None</em>"

                rows_html.append(
                    f'<tr style="{highlight_style}">'
                    f'<td style="font-weight:600; color:var(--text);">{drug}</td>'
                    f'<td style="color:var(--text-secondary);">{event}</td>'
                    f'<td style="text-align:center;">{orig_p}</td>'
                    f'<td style="text-align:center;">{leak_badge}</td>'
                    f'<td style="max-width:320px;">{phrases_chips}</td>'
                    f'<td style="text-align:center; font-weight:700; color:var(--text);">{mech_only}</td>'
                    f'<td style="font-size:12px; color:var(--text-dim); max-width:280px;">{notes}</td>'
                    f'</tr>'
                )

                st.markdown(
                f'<div class="pg-table-container">'
                f'<table class="pg-data-table">'
                f'<thead><tr>'
                f'<th>Drug</th><th>Event</th><th style="text-align:center;">Original Plaus</th>'
                f'<th style="text-align:center;">Leak Status</th><th>Flagged Leak Phrases</th>'
                f'<th style="text-align:center;">Mechanistic-Only</th><th>Critic Audit Notes</th>'
                f'</tr></thead>'
                f'<tbody>{"".join(rows_html)}</tbody>'
                f'</table>'
                f'</div>',
                unsafe_allow_html=True,
            )

        except Exception as err:
            st.error(f"Failed to render critic probe results: {err}")

    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Section B: Confounding Self-Probe
    # -----------------------------------------------------------------------
    st.markdown('<div class="pg-section-label">Section B — Polypharmacy Confounding Self-Probe (DECISIONS.md §21, §28)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:13.5px; color:var(--text-secondary); margin-bottom:14px; line-height:1.5;">'
        'Spontaneous reporting systems (FAERS) frequently attribute adverse events to benign drugs when those drugs are '
        'routinely co-prescribed alongside potent causative medications. We evaluate a confounding de-biasing tool across 4 real, '
        'verified drug–event pairs.'
        '</div>',
        unsafe_allow_html=True,
    )

    # Epistemic finding disclosure
    st.markdown(
        '<div class="pg-quote-box">'
        '<strong>Honest Epistemic Finding (§28 Disclosure):</strong> The confounding evaluator exhibits prominent markers of '
        'pre-trained clinical knowledge recall (e.g. <em>"a classic example of confounding by co-medication"</em>, <em>"common clinical practice"</em>) '
        'rather than de-convolving co-prescription rates from raw patient records alone. While highly effective as an expert heuristic '
        'discounting layer, it inherits the same circularity limitation as generative plausibility derivation (§17).'
        '</div>',
        unsafe_allow_html=True,
    )

    confound_file = repo_root / "outputs" / "experiments" / "confounding_probe" / "confounding_self_probe.json"
    if not confound_file.exists():
        st.info("Confounding self-probe results not yet generated. Run `python scripts/research/run_confounding_probe.py`.")
    else:
        try:
            with open(confound_file, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            c_cases = c_data.get("probe_cases", [])

            # Summary Grid
            cols = st.columns(4, gap="medium")
            for col, c in zip(cols, c_cases):
                drug = c.get("drug", "")
                event = c.get("event", "").replace("_", " ")
                rc = c.get("report_count", 0)
                prr = c.get("prr", 0.0)
                ass = c.get("assessment", {})
                df_val = ass.get("discount_factor", 1.0)
                is_conf = ass.get("is_confounded", False)
                status_txt = "CONFOUNDED" if is_conf else "GENUINE"

                with col:
                    st.markdown(
                        f'<div class="pg-stat-card">'
                        f'<div>'
                        f'<div class="pg-stat-label">{drug}</div>'
                        f'<div style="font-size:14px; font-weight:600; color:var(--text); margin-bottom:4px;">{event}</div>'
                        f'<div class="pg-stat-value" style="font-size:20px; color:#F59E0B;">{df_val:.2f}</div>'
                        f'<div class="pg-stat-sub">Discount Factor ({status_txt})</div>'
                        f'</div>'
                        f'<div>'
                        f'<div class="pg-stat-note">Reports: {rc:,} · PRR: {prr:.2f}</div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

            # Detailed Expanders
            for c in c_cases:
                drug = c.get("drug", "")
                event = c.get("event", "").replace("_", " ")
                ass = c.get("assessment", {})
                df_val = ass.get("discount_factor", 1.0)
                drugs = ass.get("confounding_drugs", [])
                expl = ass.get("confounding_explanation", "")

                with st.expander(f"Clinical Rationale: {drug} + {event} (Discount = {df_val:.2f})"):
                    st.markdown(f"**Identified Confounders:** `{', '.join(drugs)}`")
                    st.markdown(f'<div class="pg-quote-box">{expl}</div>', unsafe_allow_html=True)

        except Exception as err:
            st.error(f"Failed to render confounding self-probe: {err}")

    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Section C: Before/After Spotlight on Metformin
    # -----------------------------------------------------------------------
    st.markdown('<div class="pg-section-label">Section C — Confounding Impact: Before vs. After (Metformin & Hypoglycaemia)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:13.5px; color:var(--text-secondary); margin-bottom:14px; line-height:1.5;">'
        'Direct resolution of the false-positive failure case documented in §21. '
        'Because metformin is widely co-prescribed with insulin secretagogues, raw FAERS produced an inflated PRR of 10.73, '
        'pushing baseline confidence to 0.4000 (MONITOR). Applying the 0.20 discount factor drops confidence to 0.0800, '
        'correctly routing the signal to DO_NOT_ESCALATE without altering formula weights.'
        '</div>',
        unsafe_allow_html=True,
    )

    base_file = repo_root / "outputs" / "core" / "eval-run-8-metformin-hypoglycaemia_report.json"
    disc_file = repo_root / "outputs" / "experiments" / "confounding_probe" / "metformin_confounding_report.json"

    if not base_file.exists() or not disc_file.exists():
        st.info("Before/after evaluation reports not found. Run `python scripts/research/run_confounding_evaluation.py`.")
    else:
        try:
            with open(base_file, "r", encoding="utf-8") as f:
                base_rpt = json.load(f)
            with open(disc_file, "r", encoding="utf-8") as f:
                disc_rpt = json.load(f)

            cancel_icon = material_icon("cancel", size=16, color="#EF4444", extra_style="vertical-align:-3px;")
            check_icon = material_icon("check_circle", size=16, color="#22C77A", extra_style="vertical-align:-3px;")

            # Before / After Comparison Table
            st.markdown(
                f'<div class="pg-table-container" style="margin-bottom:18px;">'
                f'<table class="pg-data-table">'
                f'<thead><tr>'
                f'<th>Pipeline State</th>'
                f'<th style="text-align:center;">Discount Factor</th>'
                f'<th style="text-align:center;">Adjusted PRR Score</th>'
                f'<th style="text-align:right;">Confidence</th>'
                f'<th style="text-align:center;">Escalation</th>'
                f'<th>Ground Truth Concordance</th>'
                f'</tr></thead>'
                f'<tbody>'
                f'<tr>'
                f'<td style="font-weight:600;">Baseline (Frozen §18)</td>'
                f'<td style="text-align:center;" class="pg-mono">1.00 (None)</td>'
                f'<td style="text-align:center;" class="pg-mono">1.00</td>'
                f'<td style="text-align:right;" class="pg-mono">0.4000</td>'
                f'<td style="text-align:center;">{esc_badge("MONITOR")}</td>'
                f'<td style="color:#EF4444; font-weight:600; vertical-align:middle;">'
                f'<span style="display:inline-flex; align-items:center;">{cancel_icon}False Positive (Lenient Over-Caution)</span></td>'
                f'</tr>'
                f'<tr style="background:rgba(34, 199, 122, 0.06);">'
                f'<td style="font-weight:600;">Confounding-Discounted</td>'
                f'<td style="text-align:center;" class="pg-mono">0.20</td>'
                f'<td style="text-align:center;" class="pg-mono">0.20</td>'
                f'<td style="text-align:right;" class="pg-mono">0.0800</td>'
                f'<td style="text-align:center;">{esc_badge("DO_NOT_ESCALATE")}</td>'
                f'<td style="color:#22C77A; font-weight:600; vertical-align:middle;">'
                f'<span style="display:inline-flex; align-items:center;">{check_icon}Exact Ground Truth Match (Negative Control Cleared)</span></td>'
                f'</tr>'
                f'</tbody>'
                f'</table>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Side-by-side Evidence Waterfall charts
            col_b, col_a = st.columns(2, gap="large")
            with col_b:
                st.markdown('<div style="font-weight:700; font-size:14px; margin-bottom:8px; color:var(--text);">Baseline Evidence Attribution (No Discount)</div>', unsafe_allow_html=True)
                render_conf_chart(base_rpt, key="probe_waterfall_metformin_baseline", theme=theme)
            with col_a:
                st.markdown('<div style="font-weight:700; font-size:14px; margin-bottom:8px; color:var(--text);">Discounted Evidence Attribution (0.20 Multiplier)</div>', unsafe_allow_html=True)
                render_conf_chart(disc_rpt, key="probe_waterfall_metformin_discounted", theme=theme)

        except Exception as err:
            st.error(f"Failed to render before/after comparison: {err}")