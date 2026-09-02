"""
Publication Figure Generator: Multi-Source Evidence Attribution Waterfalls.

Generates publication-ready static figures (PNG and PDF, 300 DPI) depicting
the deterministic evidence decomposition and threshold gating for key
evaluation pairs in PharmaGuard.

Regulatory Grounding & Context:
This feature operationalizes the transparency and auditability standards outlined in:
  US Food and Drug Administration (FDA) & European Medicines Agency (EMA),
  "Guiding Principles for Artificial Intelligence in Drug Development",
  published jointly in January 2026.
Principle 4 ("Transparency and Traceability") explicitly requires that AI-assisted
postmarketing safety decisions decompose composite inferences into independently
verifiable, auditable evidence sources rather than presenting ungrounded, opaque scores.

Owner: Krishna Sikheriya (IIT2023139)
"""

import json
import logging
from pathlib import Path
import sys

# Ensure UTF-8 stdout
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import matplotlib.pyplot as plt
import matplotlib.patches as patches

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def generate_waterfall_chart(
    report: dict,
    pair_name: str,
    output_prefix: str,
    output_dir: Path,
    discount_applied: bool = False,
    raw_prr_override: float = None,
):
    """
    Renders a publication-quality horizontal evidence waterfall chart matching
    the color palette, typography, and visual hierarchy of the interactive dashboard.
    Saves both 300 DPI PNG and vector PDF formats.
    """
    ss = report.get("signal_stats", {})
    lit = report.get("literature", {})
    mech = report.get("mechanism", {})
    triage = report.get("triage", {})

    prr_raw = raw_prr_override if raw_prr_override is not None else (ss.get("prr_score", 0.0) or 0.0)
    grade_raw = lit.get("grade_score", 0.0) or 0.0
    plaus_raw = mech.get("plausibility_score", 0.0) or 0.0

    w_prr = 0.40 * prr_raw
    w_grade = 0.40 * grade_raw
    w_plaus = 0.20 * plaus_raw
    total_conf = w_prr + w_grade + w_plaus

    sig_strength = ss.get("prr_score_label") or triage.get("signal_strength", "UNKNOWN")
    if hasattr(sig_strength, "value"):
        sig_strength = sig_strength.value
    sig_strength = str(sig_strength)

    esc_decision = triage.get("escalation", "UNKNOWN")
    if hasattr(esc_decision, "value"):
        esc_decision = esc_decision.value
    esc_decision = str(esc_decision)

    # Categories & Weights
    labels = [
        "FAERS PRR\n(w = 0.40)",
        "PubMed Grade\n(w = 0.40)",
        "ChEMBL Plausibility\n(w = 0.20)",
    ]
    vals = [w_prr, w_grade, w_plaus]
    raws = [prr_raw, grade_raw, plaus_raw]
    colors = ["#1769AA", "#168A55", "#4F46E5"]  # Blue, Green, Indigo/Purple

    fig, ax = plt.subplots(figsize=(8.5, 3.2), dpi=300)

    y_pos = [2, 1, 0]
    bars = ax.barh(y_pos, vals, height=0.48, color=colors, edgecolor="none", zorder=3)

    # Bar annotations
    for bar, val, raw in zip(bars, vals, raws):
        w = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2.0
        ann_text = f" raw = {raw:.2f}  →  +{val:.3f}"
        ax.text(
            w + 0.02,
            y,
            ann_text,
            va="center",
            ha="left",
            fontsize=10,
            fontfamily="sans-serif",
            fontweight="bold",
            color="#1E293B",
        )

    # Threshold guidelines
    ax.axvline(0.35, color="#F59E0B", linestyle=":", linewidth=1.2, zorder=2, label="Monitor Threshold (0.35)")
    ax.axvline(0.70, color="#EF4444", linestyle="--", linewidth=1.2, zorder=2, label="Escalate Threshold (0.70)")

    # Total Confidence vertical line & value badge
    ax.axvline(total_conf, color="#0F172A", linestyle="-", linewidth=2.0, zorder=4)
    ax.set_ylim(-0.6, 2.65)
    ax.text(
        total_conf,
        2.38,
        f"Total Σ = {total_conf:.3f}",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color="#0F172A",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#F1F5F9", edgecolor="#CBD5E1", lw=1),
        zorder=5,
    )

    # Clean single-line header above axes
    fig.suptitle(pair_name, x=0.25, y=0.96, ha="left", fontsize=11.5, fontweight="bold", color="#0F172A")

    # Gate & threshold status annotation
    gate_status = "BLOCKED (Hard Gate)" if sig_strength == "NO_SIGNAL" else "PASS"
    if total_conf >= 0.70 and sig_strength in ("STRONG", "MODERATE"):
        thresh_info = f"{total_conf:.2f} ≥ 0.70 → {esc_decision}"
    elif total_conf >= 0.35:
        thresh_info = f"0.35 ≤ {total_conf:.2f} < 0.70 → {esc_decision}"
    else:
        thresh_info = f"{total_conf:.2f} < 0.35 → {esc_decision}"

    gate_str = f"Safety Gate: signal_strength={sig_strength} ({gate_status})  |  Decision Logic: {thresh_info}"
    if discount_applied:
        df_val = ss.get('discount_factor', 0.2)
        gate_str = f"[Polypharmacy Discount Factor = {df_val:.2f}]  |  " + gate_str

    fig.text(
        0.10,
        0.05,
        gate_str,
        fontsize=8.5,
        fontfamily="monospace",
        color="#475569",
        va="bottom",
    )
    fig.text(
        0.10,
        0.015,
        "Multi-Source Evidence Attribution & Gating (Traceability per FDA/EMA Jan 2026 AI Guiding Principles)",
        fontsize=7.5,
        color="#94A3B8",
        style="italic",
        va="bottom",
    )

    # Axes formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10, fontweight="medium", color="#1E293B")
    ax.set_xlim(0, 1.25)
    ax.set_xlabel("Confidence Contribution Score", fontsize=10, labelpad=6, color="#475569")

    ax.grid(axis="x", linestyle="--", alpha=0.35, zorder=1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")

    plt.subplots_adjust(left=0.25, right=0.93, top=0.82, bottom=0.22)

    # Export PNG & PDF
    png_path = output_dir / f"{output_prefix}.png"
    pdf_path = output_dir / f"{output_prefix}.pdf"

    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.savefig(pdf_path, format="pdf", bbox_inches="tight")
    plt.close(fig)

    logger.info(f"Exported figure to {png_path} and {pdf_path}")
    return png_path, pdf_path


def export_all_figures():
    out_dir = REPO_ROOT / "outputs" / "research" / "paper_figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    core_dir = REPO_ROOT / "outputs" / "core"

    # 1. Montelukast :: suicidal_ideation (Flagship Strict FN Disagreement Case)
    montelukast_file = core_dir / "eval-run-0-montelukast-suicidal_ideation_report.json"
    with open(montelukast_file, "r", encoding="utf-8") as f:
        montelukast_data = json.load(f)

    generate_waterfall_chart(
        report=montelukast_data,
        pair_name="Montelukast & Suicidal Ideation (Strict FN Case)",
        output_prefix="figure_waterfall_montelukast_strict_fn",
        output_dir=out_dir,
    )

    # 2. Metformin :: hypoglycaemia (Polypharmacy Confounded Case - Baseline vs Discounted)
    metformin_base_file = core_dir / "eval-run-8-metformin-hypoglycaemia_report.json"
    with open(metformin_base_file, "r", encoding="utf-8") as f:
        metformin_base_data = json.load(f)

    generate_waterfall_chart(
        report=metformin_base_data,
        pair_name="Metformin & Hypoglycaemia (Confounded Baseline - Lenient FP)",
        output_prefix="figure_waterfall_metformin_baseline",
        output_dir=out_dir,
    )

    metformin_discount_file = REPO_ROOT / "outputs" / "experiments" / "confounding_probe" / "metformin_confounding_report.json"
    if metformin_discount_file.exists():
        with open(metformin_discount_file, "r", encoding="utf-8") as f:
            metformin_disc_data = json.load(f)
        generate_waterfall_chart(
            report=metformin_disc_data,
            pair_name="Metformin & Hypoglycaemia (Confounding Discounted - Resolved)",
            output_prefix="figure_waterfall_metformin_discounted",
            output_dir=out_dir,
            discount_applied=True,
            raw_prr_override=metformin_disc_data["signal_stats"]["prr_score"],
        )

    # 3. Ciprofloxacin :: tendon_rupture (Concordant Positive Control)
    cipro_file = core_dir / "eval-run-1-ciprofloxacin-tendon_rupture_report.json"
    with open(cipro_file, "r", encoding="utf-8") as f:
        cipro_data = json.load(f)

    generate_waterfall_chart(
        report=cipro_data,
        pair_name="Ciprofloxacin & Tendon Rupture (Concordant Strong Positive)",
        output_prefix="figure_waterfall_ciprofloxacin_positive",
        output_dir=out_dir,
    )

    print("\n" + "=" * 80)
    print("PHARMAGUARD PUBLICATION FIGURES EXPORT COMPLETE")
    print("=" * 80)
    print(f"Figures saved to: {out_dir}")
    for ext in ["*.png", "*.pdf"]:
        for p in sorted(out_dir.glob(ext)):
            print(f"  - {p.name} ({p.stat().st_size:,} bytes)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    export_all_figures()