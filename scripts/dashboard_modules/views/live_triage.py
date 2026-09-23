"""
View: Live Signal Triage
========================
Executive real-time pharmacovigilance screening across OpenFDA FAERS,
ChEMBL mechanisms, and PubMed literature. Powered by local Ollama (qwen2.5:7b)
for completely unmetered, zero-quota live inference.

Strictly uses Google Material Symbols (no emojis). Dual-theme compatible.
Owner: Krishna Sikheriya (IIT2023139)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import streamlit as st

from pharmaguard.agent.fixed_pipeline import FixedPipelineAgent
from pharmaguard.agent.output_schema import TriageReport, EscalationDecision
from pharmaguard.utils.config_loader import load_config
from pharmaguard.utils.llm_factory import check_ollama_status

logger = logging.getLogger(__name__)

PRESET_PAIRS = [
    ("-- Select Benchmark Preset --", "", ""),
    ("Montelukast — Suicidal Ideation (Boxed Warning)", "montelukast", "suicidal ideation"),
    ("Ciprofloxacin — Tendon Rupture (Boxed Warning)", "ciprofloxacin", "tendon rupture"),
    ("Rosiglitazone — Myocardial Infarction (CV Risk)", "rosiglitazone", "myocardial infarction"),
    ("Metformin — Hypoglycaemia (Negative Control)", "metformin", "hypoglycaemia"),
    ("Lisinopril — Cough (Class Effect)", "lisinopril", "cough"),
    ("Atorvastatin — Rhabdomyolysis (Myopathy)", "atorvastatin", "rhabdomyolysis"),
    ("Amoxicillin — Anaphylaxis (Immunologic)", "amoxicillin", "anaphylaxis"),
    ("Aspirin — GI Haemorrhage (Known Bleeding)", "aspirin", "gastrointestinal haemorrhage"),
    ("Diphenhydramine — Somnolence (Sedation Control)", "diphenhydramine", "somnolence"),
]


def _format_decision_badge(decision: EscalationDecision | str, theme: str = "light") -> str:
    """Return styled HTML pill badge for the decision using Material Symbol."""
    d_str = str(decision.value if isinstance(decision, EscalationDecision) else decision)
    is_dark = (theme == "dark")

    if d_str == "ESCALATE":
        bg = "rgba(239, 68, 68, 0.15)" if is_dark else "#FEF2F2"
        bd = "rgba(239, 68, 68, 0.35)" if is_dark else "#FECACA"
        fg = "#F87171" if is_dark else "#991B1B"
        icon = "warning"
    elif d_str == "MONITOR":
        bg = "rgba(245, 158, 11, 0.15)" if is_dark else "#FFFBEB"
        bd = "rgba(245, 158, 11, 0.35)" if is_dark else "#FDE68A"
        fg = "#FBBF24" if is_dark else "#92400E"
        icon = "visibility"
    else:  # DO_NOT_ESCALATE
        bg = "rgba(16, 185, 129, 0.15)" if is_dark else "#F0FDF4"
        bd = "rgba(16, 185, 129, 0.35)" if is_dark else "#BBF7D0"
        fg = "#34D399" if is_dark else "#166534"
        icon = "check_circle"

    return (
        f'<span style="background:{bg}; border:1px solid {bd}; color:{fg}; '
        f'padding:4px 12px; border-radius:6px; font-weight:700; font-size:12.5px; '
        f'display:inline-flex; align-items:center; gap:6px; letter-spacing:0.04em;">'
        f'<span class="material-symbols-outlined" style="font-size:15px;">{icon}</span> {d_str}'
        f'</span>'
    )


def view_live_triage(theme: str = "light", repo_root: Path | None = None) -> None:
    """Render the Live Signal Triage tab with professional, balanced styling."""
    is_dark = (theme == "dark")
    surface = "#101824" if is_dark else "#FFFFFF"
    surface2 = "#121B29" if is_dark else "#F2F5F9"
    border = "#263245" if is_dark else "#D9E1EA"
    text = "#F3F6FA" if is_dark else "#172033"
    text_sec = "#A8B3C3" if is_dark else "#53657D"
    text_muted = "#738096" if is_dark else "#7C8A9D"
    primary = "#818CF8" if is_dark else "#4F46E5"
    shadow = "0 4px 16px rgba(0,0,0,0.3)" if is_dark else "0 2px 8px rgba(15,23,42,0.06)"

    # ── Session State ──
    if "live_history" not in st.session_state:
        st.session_state["live_history"] = []
    if "current_report" not in st.session_state:
        st.session_state["current_report"] = None
    if "current_report_json" not in st.session_state:
        st.session_state["current_report_json"] = None

    # ── Header ──
    st.markdown(
        '<div class="pg-header" style="margin-bottom: 16px;">'
        '<div class="pg-title" style="display:flex; align-items:center; gap:8px;">'
        '<span class="material-symbols-outlined" style="font-size:24px; color:var(--primary);">bolt</span>'
        'Live Signal Triage'
        '</div>'
        '<div class="pg-subtitle">'
        'Real-time multi-source pharmacovigilance screening via OpenFDA FAERS, ChEMBL, and PubMed.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Backend Control & Status ──
    ollama_online, loaded_models = check_ollama_status()
    has_qwen = any("qwen2.5:7b" in m or m == "qwen2.5:7b" for m in loaded_models)

    c_stat, c_prov = st.columns([1.6, 1.4], gap="medium")
    with c_stat:
        if ollama_online and has_qwen:
            st.markdown(
                f'<div style="background:{surface}; border:1px solid {border}; border-radius:8px; '
                f'padding:8px 14px; display:flex; align-items:center; gap:8px; height:42px;">'
                f'<span class="material-symbols-outlined" style="color:#10B981; font-size:18px;">check_circle</span>'
                f'<span style="font-size:13px; font-weight:600; color:{text};">Ollama 0.34</span>'
                f'<span style="color:{text_muted};">&middot;</span>'
                f'<code style="font-size:12px;">qwen2.5:7b</code>'
                f'<span style="color:{text_muted};">&middot;</span>'
                f'<span style="font-size:12px; color:{text_sec};">Local &middot; Unlimited RPM</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        elif ollama_online:
            st.markdown(
                f'<div style="background:{surface}; border:1px solid {border}; border-radius:8px; '
                f'padding:8px 14px; display:flex; align-items:center; gap:8px; height:42px;">'
                f'<span class="material-symbols-outlined" style="color:#F59E0B; font-size:18px;">info</span>'
                f'<span style="font-size:13px; font-weight:600; color:{text};">Ollama Online</span>'
                f'<span style="font-size:12px; color:{text_sec};">Model: {loaded_models[0] if loaded_models else "None"}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="background:{surface}; border:1px solid rgba(239,68,68,0.4); border-radius:8px; '
                f'padding:8px 14px; display:flex; align-items:center; gap:8px; height:42px;">'
                f'<span class="material-symbols-outlined" style="color:#EF4444; font-size:18px;">error</span>'
                f'<span style="font-size:13px; font-weight:600; color:#EF4444;">Ollama Offline</span>'
                f'<span style="font-size:12px; color:{text_sec};">&middot; Start via <code>ollama serve</code></span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with c_prov:
        provider_choice = st.selectbox(
            "Backend",
            options=[
                "Ollama — qwen2.5:7b (Local / Unmetered)",
                "Gemini 3.1 Flash (Cloud API)",
            ],
            index=0,
            label_visibility="collapsed",
        )
        is_ollama = "Ollama" in provider_choice

    # ── Pipeline Configuration ──
    with st.expander("Pipeline Configuration", expanded=False, icon=":material/tune:"):
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            use_cache = st.checkbox("Disk Cache", value=True, help="Serve cached external API and model responses.")
        with col_c2:
            ci_gate = st.checkbox("CI Signal Gate", value=False, help="Evans et al. 2001 floor requirement.")
        with col_c3:
            concordance_discount = st.checkbox("Indication Discount (0.85x)", value=False, help="Confounding-by-indication adjustment.")

    st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)

    # ── Input Interface ──
    preset_labels = [p[0] for p in PRESET_PAIRS]
    selected_preset = st.selectbox(
        "Benchmark Presets",
        options=preset_labels,
        index=0,
        label_visibility="collapsed",
    )

    default_drug = ""
    default_event = ""
    for label, drug, event in PRESET_PAIRS:
        if label == selected_preset and drug:
            default_drug = drug
            default_event = event
            break

    c_in1, c_in2, c_btn = st.columns([1.4, 1.4, 0.7], gap="medium")
    with c_in1:
        drug_input = st.text_input(
            "Drug Name",
            value=default_drug,
            placeholder="e.g., montelukast",
        )
    with c_in2:
        event_input = st.text_input(
            "Adverse Event",
            value=default_event,
            placeholder="e.g., suicidal ideation",
        )
    with c_btn:
        st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
        run_clicked = st.button(
            "Run Triage",
            type="primary",
            icon=":material/play_arrow:",
            width="stretch",
        )

    # ── Live Execution ──
    if run_clicked:
        clean_drug = drug_input.strip().lower()
        clean_event = event_input.strip().lower()

        if not clean_drug or not clean_event:
            st.error("Specify both drug name and adverse event.")
        elif is_ollama and not ollama_online:
            st.error("Ollama daemon is offline. Run 'ollama serve' in terminal.")
        else:
            cfg = load_config()
            cfg.agent.llm_provider = "ollama" if is_ollama else "google"
            cfg.agent.ollama_model = "qwen2.5:7b"
            cfg.cache.enabled = use_cache
            cfg.signal_detection.ci_based_gate.enabled = ci_gate
            cfg.indication_concordance.discount_enabled = concordance_discount

            run_id = f"live-{clean_drug.replace(' ', '')}-{clean_event.replace(' ', '')}-{int(datetime.now().timestamp())}"
            cache_dir = ".cache/pharmaguard_ollama" if is_ollama else ".cache/pharmaguard"

            with st.status("Executing Multi-Stream Triage Screening...", expanded=True) as status:
                status.write(":material/query_stats: FAERS Disproportionality Mining (PRR, ROR)...")
                status.write(":material/biotech: ChEMBL Pharmacological Targets & Plausibility...")
                status.write(
                    f":material/menu_book: PubMed Retrieval & Evidence Grading via {'local Ollama (qwen2.5:7b)' if is_ollama else 'Gemini Flash'}..."
                )

                try:
                    agent = FixedPipelineAgent(
                        run_id=run_id,
                        cache_dir=cache_dir,
                        config=cfg,
                    )
                    report: TriageReport = agent.run(clean_drug, clean_event)

                    status.write(":material/shield: Synthesizing multi-source signals and applying escalation gates...")
                    status.update(
                        label="Triage Complete",
                        state="complete",
                        expanded=False,
                    )

                    st.session_state["current_report"] = report
                    st.session_state["current_report_json"] = report.model_dump_json(indent=2)

                    history_entry = {
                        "Time": datetime.now().strftime("%H:%M:%S"),
                        "Drug": report.drug,
                        "Event": report.event,
                        "Backend": "Ollama (qwen2.5:7b)" if is_ollama else "Gemini Flash",
                        "Decision": report.triage.escalation.value,
                        "Confidence": f"{report.triage.confidence:.4f}",
                        "Signal": report.triage.signal_strength.value,
                        "Grade": report.triage.evidence_grade.value,
                        "Plausibility": report.mechanism.biological_plausibility.value,
                    }
                    st.session_state["live_history"].insert(0, history_entry)

                except Exception as exc:
                    status.update(label="Triage Failed", state="error", expanded=True)
                    st.error(f"Execution error: {exc}")
                    logger.exception("Live triage error: %s", exc)

    # ── Results Presentation ──
    report: TriageReport | None = st.session_state.get("current_report")
    if report:
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

        decision_val = report.triage.escalation.value
        conf_val = report.triage.confidence
        decision_badge_html = _format_decision_badge(decision_val, theme=theme)

        # Verdict Hero Card
        st.markdown(
            f'<div style="background:{surface}; border:1px solid {border}; border-radius:10px; '
            f'padding:18px 22px; box-shadow:{shadow}; margin-bottom:16px;">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">'
            f'<div>'
            f'<div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:{text_muted}; margin-bottom:4px;">'
            f'Triage Recommendation'
            f'</div>'
            f'<div style="font-size:24px; font-weight:800; color:{text}; margin-bottom:8px;">'
            f'{report.drug.title()} &middot; <span style="font-weight:600; color:{text_sec};">{report.event.title()}</span>'
            f'</div>'
            f'<div>{decision_badge_html}</div>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:{text_muted}; margin-bottom:4px;">'
            f'Calibrated Confidence'
            f'</div>'
            f'<div style="font-size:34px; font-weight:800; font-family:\'JetBrains Mono\', monospace; color:{primary}; line-height:1;">'
            f'{conf_val:.4f}'
            f'</div>'
            f'<div style="font-size:11.5px; color:{text_muted}; margin-top:4px;">'
            f'Signal 40% &middot; Lit 40% &middot; MoA 20%'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # 4 Pillar Metric Cards
        c_p1, c_p2, c_p3, c_p4 = st.columns(4, gap="medium")

        with c_p1:
            prr_val = f"{report.signal_stats.prr:.2f}" if report.signal_stats.prr else "N/A"
            prr_ci = f"{report.signal_stats.prr_lower_ci:.2f}" if report.signal_stats.prr_lower_ci else "N/A"
            n_rep = report.signal_stats.report_count
            sig_label = report.triage.signal_strength.value

            st.markdown(
                f'<div class="pg-card" style="padding:14px;">'
                f'<div class="pg-stat-label" style="display:flex; align-items:center; gap:5px;">'
                f'<span class="material-symbols-outlined" style="font-size:15px;">query_stats</span> FAERS Disproportionality'
                f'</div>'
                f'<div class="pg-stat-value" style="font-size:20px;">{sig_label}</div>'
                f'<div class="pg-stat-sub">PRR <strong>{prr_val}</strong> (95% CI: {prr_ci})</div>'
                f'<div class="pg-stat-note">{n_rep:,} cases</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with c_p2:
            gr_val = report.triage.evidence_grade.value
            abs_n = report.literature.abstracts_retrieved
            pmids_n = len(report.literature.supporting_pmids)

            st.markdown(
                f'<div class="pg-card" style="padding:14px;">'
                f'<div class="pg-stat-label" style="display:flex; align-items:center; gap:5px;">'
                f'<span class="material-symbols-outlined" style="font-size:15px;">menu_book</span> PubMed Evidence'
                f'</div>'
                f'<div class="pg-stat-value" style="font-size:20px;">Grade {gr_val}</div>'
                f'<div class="pg-stat-sub">Screened: <strong>{abs_n}</strong> abstracts</div>'
                f'<div class="pg-stat-note">{pmids_n} supporting citations</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with c_p3:
            plaus_val = report.mechanism.biological_plausibility.value
            chembl_id = report.mechanism.chembl_id or "Unannotated"
            moa_text = report.mechanism.moa or "Mechanism not annotated"

            st.markdown(
                f'<div class="pg-card" style="padding:14px;">'
                f'<div class="pg-stat-label" style="display:flex; align-items:center; gap:5px;">'
                f'<span class="material-symbols-outlined" style="font-size:15px;">biotech</span> ChEMBL Plausibility'
                f'</div>'
                f'<div class="pg-stat-value" style="font-size:20px;">{plaus_val}</div>'
                f'<div class="pg-stat-sub">Target: <code>{chembl_id}</code></div>'
                f'<div class="pg-stat-note" style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{moa_text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with c_p4:
            ic = report.indication_concordance
            if ic and getattr(ic, "concordant", False):
                ic_label = "Concordant"
                ic_sub = f"Discount: {getattr(ic, 'discount_factor', 0.85):.2f}x"
                ic_note = getattr(ic, "overlap_category", "Indication Overlap")
            else:
                ic_label = "Clear"
                ic_sub = "No overlap detected"
                ic_note = "Non-confounded signal"

            st.markdown(
                f'<div class="pg-card" style="padding:14px;">'
                f'<div class="pg-stat-label" style="display:flex; align-items:center; gap:5px;">'
                f'<span class="material-symbols-outlined" style="font-size:15px;">health_and_safety</span> Indication Context'
                f'</div>'
                f'<div class="pg-stat-value" style="font-size:20px;">{ic_label}</div>'
                f'<div class="pg-stat-sub">{ic_sub}</div>'
                f'<div class="pg-stat-note">{ic_note}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        # ── Evidence & Audit Trace Expanders ──
        with st.expander("Clinical Literature Evidence", expanded=True, icon=":material/article:"):
            st.markdown(
                f'<div class="pg-quote-box" style="margin-top:0;">'
                f'{report.literature.evidence_summary}'
                f'</div>',
                unsafe_allow_html=True,
            )
            if report.literature.supporting_pmids:
                code_bg_val = "rgba(129, 140, 248, 0.16)" if is_dark else "#EEF2FF"
                code_bd_val = "rgba(129, 140, 248, 0.35)" if is_dark else "#C7D2FE"
                pmid_links = [
                    f'<a href="https://pubmed.ncbi.nlm.nih.gov/{p}/" target="_blank" style="text-decoration:none;">'
                    f'<span style="background:{code_bg_val}; border:1px solid {code_bd_val}; color:{primary}; padding:3px 9px; border-radius:5px; font-family:\'JetBrains Mono\', monospace; font-size:12px; font-weight:600; display:inline-block; margin:2px 3px;">'
                    f'PMID {p}'
                    f'</span></a>'
                    for p in report.literature.supporting_pmids
                ]
                st.markdown(
                    f'<div style="margin-top:12px; font-size:13px; color:{text_sec};">'
                    f'<strong style="color:{text};">Citations:</strong> {" ".join(pmid_links)}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        with st.expander("Pharmacological Plausibility & Mechanism", expanded=False, icon=":material/science:"):
            st.markdown(
                f'<div class="pg-callout" style="margin-top:0;">'
                f'<strong style="color:{text};">Plausibility:</strong> {report.mechanism.biological_plausibility.value} '
                f'(Score: {report.mechanism.plausibility_score:.2f} &middot; Source: {report.mechanism.plausibility_source.value})<br><br>'
                f'<strong style="color:{text};">Target / MoA:</strong> {report.mechanism.moa or "None"}<br>'
                f'<strong style="color:{text};">Rationale:</strong> {report.mechanism.plausibility_rationale}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with st.expander("Agent Reasoning Trace", expanded=False, icon=":material/terminal:"):
            for step in report.triage.agent_reasoning_trace:
                st.markdown(f"- `{step}`")

        with st.expander("TriageReport JSON & Export", expanded=False, icon=":material/data_object:"):
            c_dl, _ = st.columns([0.25, 0.75])
            with c_dl:
                st.download_button(
                    label="Download Report JSON",
                    data=st.session_state["current_report_json"],
                    file_name=f"{report.run_id}_report.json",
                    mime="application/json",
                    icon=":material/download:",
                )
            st.code(st.session_state["current_report_json"], language="json")

    # ── Session Run History ──
    if st.session_state["live_history"]:
        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        c_h_head, c_h_clear = st.columns([0.85, 0.15])
        with c_h_head:
            st.markdown(
                f'<div style="font-size:15px; font-weight:700; color:{text}; display:flex; align-items:center; gap:6px;">'
                f'<span class="material-symbols-outlined" style="font-size:18px; color:var(--primary);">history</span>'
                f'Session Triage History ({len(st.session_state["live_history"])} runs)'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c_h_clear:
            if st.button("Clear", icon=":material/delete:", width="stretch"):
                st.session_state["live_history"] = []
                st.rerun()

        rows_html = []
        for r in st.session_state["live_history"]:
            dec_badge = _format_decision_badge(r.get("Decision", ""), theme=theme)
            rows_html.append(
                f"<tr>"
                f"<td class='pg-mono' style='font-size:12px; color:{text_muted};'>{r.get('Time', '')}</td>"
                f"<td style='font-weight:700; color:{text};'>{r.get('Drug', '').title()}</td>"
                f"<td style='color:{text_sec};'>{r.get('Event', '').title()}</td>"
                f"<td style='font-size:12px; color:{text_muted};'>{r.get('Backend', '')}</td>"
                f"<td>{dec_badge}</td>"
                f"<td class='pg-mono' style='font-weight:700; color:{primary};'>{r.get('Confidence', '')}</td>"
                f"<td style='font-size:12.5px; font-weight:600; color:{text};'>{r.get('Signal', '')}</td>"
                f"<td style='font-size:12.5px; color:{text_sec};'>Grade {r.get('Grade', '')}</td>"
                f"<td style='font-size:12.5px; color:{text_sec};'>{r.get('Plausibility', '')}</td>"
                f"</tr>"
            )

        table_html = (
            f'<div class="pg-table-container">'
            f'<table class="pg-data-table">'
            f'<thead><tr>'
            f'<th>Time</th><th>Drug</th><th>Adverse Event</th><th>Backend</th>'
            f'<th>Decision</th><th>Confidence</th><th>Signal</th><th>Evidence</th><th>Plausibility</th>'
            f'</tr></thead>'
            f'<tbody>{"".join(rows_html)}</tbody>'
            f'</table></div>'
        )
        st.markdown(table_html, unsafe_allow_html=True)
