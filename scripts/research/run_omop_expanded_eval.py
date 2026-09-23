"""
Run OMOP Expanded 100-Pair Evaluation Benchmark.
================================================
Executes the PharmaGuard multi-source pharmacovigilance triage pipeline
against the expanded 100-pair OMOP reference benchmark dataset.

Ground Truth:
  pharmaguard/data/ground_truth_omop_expanded.json (100 pairs across 4 endpoints:
    - Acute Liver Injury (hepatotoxicity) - 25 pairs
    - Acute Renal Failure (acute_kidney_injury) - 25 pairs
    - Acute Myocardial Infarction (myocardial_infarction) - 25 pairs
    - Upper Gastrointestinal Bleeding (gastrointestinal_haemorrhage) - 25 pairs)

Outputs:
  outputs/research/omop_expanded/ (strictly isolated from core evaluation outputs)

Usage:
  python scripts/research/run_omop_expanded_eval.py [--limit N] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import sys
import time
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(find_dotenv())

from pharmaguard.agent.fixed_pipeline import FixedPipelineAgent
from pharmaguard.agent.react_agent import PharmaGuardAgent
from pharmaguard.utils.config_loader import load_config
from pharmaguard.utils.llm_factory import check_ollama_status

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("omop_expanded_eval")

DEFAULT_EVAL_FILE = REPO_ROOT / "pharmaguard" / "data" / "ground_truth_omop_expanded.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "research" / "omop_expanded"


def wilson_score_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate Wilson score 95% confidence interval for a binomial proportion."""
    if trials == 0:
        return 0.0, 0.0
    z = 1.95996
    p = successes / trials
    denom = 1 + z**2 / trials
    centre = (p + z**2 / (2 * trials)) / denom
    spread = (z * math.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2))) / denom
    return max(0.0, centre - spread), min(1.0, centre + spread)


def evaluate_batch(
    eval_file: Path = DEFAULT_EVAL_FILE,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    delay_seconds: float = 0.2,
    limit: int | None = None,
    dry_run: bool = False,
    provider: str = "auto",
) -> dict:
    """Run full pipeline evaluation across OMOP expanded pairs and save individual TriageReports."""
    eval_file = Path(eval_file)
    output_dir = Path(output_dir)

    if not eval_file.exists():
        logger.error("OMOP expanded ground truth file not found at %s", eval_file)
        return {}

    with open(eval_file, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    pairs = eval_data.get("pairs", [])
    if not pairs:
        logger.error("No pairs found in OMOP expanded dataset.")
        return {}

    if limit is not None and limit > 0:
        logger.info("Limiting evaluation to first %d pairs (out of %d)", limit, len(pairs))
        pairs = pairs[:limit]

    config = load_config()
    ollama_online, loaded_models = check_ollama_status()
    logger.info("Ollama status: %s | models: %s", "Online" if ollama_online else "Offline", loaded_models)

    # Determine provider routing
    selected_provider = provider.lower()
    if selected_provider == "auto":
        selected_provider = "ollama" if ollama_online else "google"

    config.agent.llm_provider = selected_provider
    logger.info("Active LLM provider for evaluation: %s", selected_provider)
    logger.info("Evaluating %d pairs -> Output: %s", len(pairs), output_dir)

    if dry_run:
        logger.info("Dry-run mode: verified %d pairs in %s. Exiting without execution.", len(pairs), eval_file)
        return {"dry_run": True, "pairs_count": len(pairs), "provider": selected_provider}

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = len(pairs)

    for i, pair in enumerate(pairs):
        drug = pair["drug_canonical"]
        event = pair["event_meddra_pt"]
        expected = pair.get("expected_escalation", "UNKNOWN")
        category = pair.get("category", "unknown")

        safe_drug = drug.replace(" ", "_")
        safe_event = event.replace(" ", "_")
        run_id = f"omop-exp-{i:03d}-{safe_drug}-{safe_event}"

        logger.info(
            "[%d/%d] Pair: %s + %s (Expected: %s, Endpoint: %s)",
            i + 1, total, drug, event, expected, event
        )

        agent = FixedPipelineAgent(run_id=run_id, config=config)

        try:
            report = agent.run(drug, event)
            dec = report.triage.escalation.value
            conf = report.triage.confidence
            sig = report.triage.signal_strength.value
            gr = report.triage.evidence_grade.value
            plaus = report.mechanism.biological_plausibility.value

            logger.info(
                "[%d/%d] -> Decision: %s | Conf: %.4f | Sig: %s | Grade: %s | Plaus: %s",
                i + 1, total, dec, conf, sig, gr, plaus
            )

            report_path = output_dir / f"{run_id}_report.json"
            with open(report_path, "w", encoding="utf-8") as rf:
                rf.write(report.model_dump_json(indent=2))

            results.append({
                "run_id": run_id,
                "drug": drug,
                "event": event,
                "expected": expected,
                "actual": dec,
                "confidence": conf,
                "signal": sig,
                "grade": gr,
                "plausibility": plaus,
                "category": category,
            })
        except Exception as exc:
            logger.error("Error evaluating %s + %s: %s", drug, event, exc, exc_info=True)

        if delay_seconds > 0 and i < total - 1:
            time.sleep(delay_seconds)

    # ── Compute Summary Metrics ──
    strict_tp = sum(1 for r in results if r["expected"] == "ESCALATE" and r["actual"] == "ESCALATE")
    strict_fp = sum(1 for r in results if r["expected"] == "DO_NOT_ESCALATE" and r["actual"] == "ESCALATE")
    strict_tn = sum(1 for r in results if r["expected"] == "DO_NOT_ESCALATE" and r["actual"] != "ESCALATE")
    strict_fn = sum(1 for r in results if r["expected"] == "ESCALATE" and r["actual"] != "ESCALATE")

    lenient_tp = sum(1 for r in results if r["expected"] == "ESCALATE" and r["actual"] in ("ESCALATE", "MONITOR"))
    lenient_fp = sum(1 for r in results if r["expected"] == "DO_NOT_ESCALATE" and r["actual"] in ("ESCALATE", "MONITOR"))
    lenient_tn = sum(1 for r in results if r["expected"] == "DO_NOT_ESCALATE" and r["actual"] == "DO_NOT_ESCALATE")
    lenient_fn = sum(1 for r in results if r["expected"] == "ESCALATE" and r["actual"] == "DO_NOT_ESCALATE")

    def safe_div(num, den):
        return num / den if den > 0 else 0.0

    def calc_f1(p, r):
        return safe_div(2 * p * r, p + r)

    s_prec = safe_div(strict_tp, strict_tp + strict_fp)
    s_rec = safe_div(strict_tp, strict_tp + strict_fn)
    s_spec = safe_div(strict_tn, strict_tn + strict_fp)
    s_f1 = calc_f1(s_prec, s_rec)

    l_prec = safe_div(lenient_tp, lenient_tp + lenient_fp)
    l_rec = safe_div(lenient_tp, lenient_tp + lenient_fn)
    l_spec = safe_div(lenient_tn, lenient_tn + lenient_fp)
    l_f1 = calc_f1(l_prec, l_rec)

    summary = {
        "benchmark": eval_file.stem,
        "total_evaluated": len(results),
        "strict": {
            "TP": strict_tp, "FP": strict_fp, "TN": strict_tn, "FN": strict_fn,
            "precision": round(s_prec, 4), "recall": round(s_rec, 4),
            "specificity": round(s_spec, 4), "f1": round(s_f1, 4),
            "recall_wilson_ci": [round(x, 4) for x in wilson_score_interval(strict_tp, strict_tp + strict_fn)],
        },
        "lenient": {
            "TP": lenient_tp, "FP": lenient_fp, "TN": lenient_tn, "FN": lenient_fn,
            "precision": round(l_prec, 4), "recall": round(l_rec, 4),
            "specificity": round(l_spec, 4), "f1": round(l_f1, 4),
            "recall_wilson_ci": [round(x, 4) for x in wilson_score_interval(lenient_tp, lenient_tp + lenient_fn)],
        },
        "results": results,
    }

    summary_path = output_dir / "evaluation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as sf:
        json.dump(summary, sf, indent=2)

    logger.info("Evaluation complete! Summary written to %s", summary_path)
    logger.info("Strict F1: %.4f (P: %.4f, R: %.4f) | Lenient F1: %.4f (P: %.4f, R: %.4f)",
                s_f1, s_prec, s_rec, l_f1, l_prec, l_rec)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run PharmaGuard on OMOP expanded 100-pair benchmark.")
    parser.add_argument("--eval-file", type=Path, default=DEFAULT_EVAL_FILE, help="Path to ground truth JSON.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Path to output directory.")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay seconds between queries (default 0.2s with local Ollama).")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pairs to evaluate.")
    parser.add_argument("--dry-run", action="store_true", help="Validate dataset without executing pipeline.")
    parser.add_argument(
        "--provider",
        type=str,
        default="auto",
        choices=["auto", "ollama", "google"],
        help="LLM provider: 'ollama', 'google', or 'auto' (default: ollama if running, else google).",
    )
    args = parser.parse_args()

    evaluate_batch(
        eval_file=args.eval_file,
        output_dir=args.output_dir,
        delay_seconds=args.delay,
        limit=args.limit,
        dry_run=args.dry_run,
        provider=args.provider,
    )


if __name__ == "__main__":
    main()
