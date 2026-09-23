"""
Comprehensive Offline Benchmark Runner for PharmaGuard.
======================================================
Executes multi-source triage across both secondary evaluation cohorts
using local Ollama (qwen2.5:7b) with zero external API costs:

  Cohort A: Top Prescribed Blockbuster Boxed Warnings (50 pairs)
            Outputs -> outputs/research/top_prescribed/
  Cohort B: OMOP Reference Expanded Benchmark (100 pairs)
            Outputs -> outputs/research/omop_expanded/

Usage:
  python scripts/research/run_full_offline_benchmarks.py [--limit N] [--cohort {all,top,omop}]
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.research.run_omop_expanded_eval import evaluate_batch
from pharmaguard.utils.llm_factory import check_ollama_status

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("full_offline_benchmarks")

DATA_DIR = REPO_ROOT / "pharmaguard" / "data"
OUTPUTS_DIR = REPO_ROOT / "outputs" / "research"

TOP_PRESCRIBED_FILE = DATA_DIR / "ground_truth_top_prescribed_boxed_warnings.json"
OMOP_EXPANDED_FILE = DATA_DIR / "ground_truth_omop_expanded.json"

TOP_OUTPUT_DIR = OUTPUTS_DIR / "top_prescribed"
OMOP_OUTPUT_DIR = OUTPUTS_DIR / "omop_expanded"


def print_summary_table(results_dict: dict[str, dict]):
    """Print an ASCII comparison table of benchmark results."""
    print("\n" + "=" * 80)
    print("PHARMAGUARD OFFLINE BENCHMARK EVALUATION SUMMARY")
    print("=" * 80)
    print(f"{'Benchmark Cohort':<30} | {'Pairs':<6} | {'Strict F1':<10} | {'Lenient F1':<10} | {'Recall 95% CI'}")
    print("-" * 80)
    for name, s in results_dict.items():
        if not s or "strict" not in s:
            print(f"{name:<30} | {'ERR':<6} | {'N/A':<10} | {'N/A':<10} | N/A")
            continue
        pairs_n = s.get("total_evaluated", 0)
        s_f1 = f"{s['strict']['f1']:.4f}"
        l_f1 = f"{s['lenient']['f1']:.4f}"
        ci = s['strict']['recall_wilson_ci']
        ci_str = f"[{ci[0]:.2f}, {ci[1]:.2f}]"
        print(f"{name:<30} | {pairs_n:<6} | {s_f1:<10} | {l_f1:<10} | {ci_str}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run PharmaGuard offline benchmarks.")
    parser.add_argument("--cohort", choices=["all", "top", "omop"], default="all", help="Which cohort to evaluate.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pairs per cohort (for quick testing).")
    parser.add_argument("--provider", default="ollama", choices=["ollama", "google", "auto"], help="LLM provider.")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between pairs in seconds.")
    args = parser.parse_args()

    ollama_online, models = check_ollama_status()
    logger.info("Ollama daemon online: %s | models: %s", ollama_online, models)
    if args.provider == "ollama" and not ollama_online:
        logger.error("Ollama is not running on http://localhost:11434. Please start it with 'ollama serve'.")
        sys.exit(1)

    summaries = {}
    start_total = time.time()

    # 1. Run Top Prescribed Blockbuster Boxed Warnings
    if args.cohort in ("all", "top"):
        logger.info("\n>>> STARTING COHORT: Top Prescribed Blockbuster Boxed Warnings (50 pairs)")
        t0 = time.time()
        s_top = evaluate_batch(
            eval_file=TOP_PRESCRIBED_FILE,
            output_dir=TOP_OUTPUT_DIR,
            delay_seconds=args.delay,
            limit=args.limit,
            provider=args.provider,
        )
        summaries["Top Prescribed (50 Pairs)"] = s_top
        logger.info("Cohort completed in %.1fs", time.time() - t0)

    # 2. Run OMOP Reference Expanded Benchmark
    if args.cohort in ("all", "omop"):
        logger.info("\n>>> STARTING COHORT: OMOP Reference Expanded Benchmark (100 pairs)")
        t0 = time.time()
        s_omop = evaluate_batch(
            eval_file=OMOP_EXPANDED_FILE,
            output_dir=OMOP_OUTPUT_DIR,
            delay_seconds=args.delay,
            limit=args.limit,
            provider=args.provider,
        )
        summaries["OMOP Expanded (100 Pairs)"] = s_omop
        logger.info("Cohort completed in %.1fs", time.time() - t0)

    logger.info("All selected cohorts completed in %.1fs", time.time() - start_total)
    print_summary_table(summaries)


if __name__ == "__main__":
    main()
