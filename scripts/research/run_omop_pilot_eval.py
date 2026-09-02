"""
Run OMOP Reference Set Pilot Evaluation.

Evaluates the PharmaGuard triage pipeline (FixedPipelineAgent / PharmaGuardAgent)
against the 32-pair OMOP secondary pilot benchmark dataset.

Ground Truth Source:
  pharmaguard/data/ground_truth_omop_pilot.json (32 pairs across 4 clinical endpoints:
  hepatotoxicity, acute_kidney_injury, myocardial_infarction, gastrointestinal_haemorrhage)

Output Directory:
  outputs/research/omop_pilot/ (strictly isolated from production outputs/)

Methodological Limitations Disclosed:
  1. Proxy MedDRA PT Mappings:
     - OMOP Acute Liver Failure 1 -> hepatotoxicity
     - OMOP Acute Renal Failure 1 -> acute_kidney_injury
     - OMOP Acute myocardial Infarction  1 -> myocardial_infarction
     - HOI Upper GI #3 -> gastrointestinal_haemorrhage
  2. Ground Truth Uncertainty:
     - Hoffman et al. (Drug Safety 2016) demonstrated that some OMOP negative
       controls are contested/misclassified in clinical literature. This pilot
       inherits this known limitation.

Owner: Krishna Sikheriya (IIT2023139)
"""

import argparse
import json
import logging
import os
from pathlib import Path
import sys
import time

from dotenv import load_dotenv

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pharmaguard.utils.config_loader import load_config
from pharmaguard.agent.react_agent import PharmaGuardAgent
from pharmaguard.agent.fixed_pipeline import FixedPipelineAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("omop_pilot_eval")

DEFAULT_EVAL_FILE = REPO_ROOT / "pharmaguard" / "data" / "ground_truth_omop_pilot.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "research" / "omop_pilot"


def run_omop_pilot_evaluation(
    eval_file: Path = DEFAULT_EVAL_FILE,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    delay_seconds: float = 3.0,
    pairs_limit: int = None,
):
    """
    Execute full pipeline evaluation across OMOP pilot pairs and save individual TriageReports.
    """
    load_dotenv(REPO_ROOT / ".env")

    eval_file = Path(eval_file)
    output_dir = Path(output_dir)

    if not eval_file.exists():
        logger.error("OMOP pilot ground truth file not found at %s", eval_file)
        return

    with open(eval_file, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    pairs = eval_data.get("pairs", [])
    if not pairs:
        logger.error("No pairs found in OMOP pilot ground truth set.")
        return

    if pairs_limit is not None and pairs_limit > 0:
        logger.info("Limiting evaluation to first %d pairs (out of %d)", pairs_limit, len(pairs))
        pairs = pairs[:pairs_limit]

    config = load_config()
    mode = config.agent.mode
    logger.info("Running OMOP pilot evaluation in mode: %s on %d pairs", mode, len(pairs))
    logger.info("Output directory: %s", output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    total_pairs = len(pairs)
    for i, pair in enumerate(pairs):
        drug = pair["drug_canonical"]
        event = pair["event_meddra_pt"]
        category = pair.get("category", "unknown")
        expected = pair.get("expected_escalation", "UNKNOWN")

        # Standard safe run_id format matching production runner
        run_id = f"eval-run-{i}-{drug.replace(' ', '')}-{event.replace(' ', '')}"

        logger.info(
            "[%d/%d] Testing Pair: %s + %s (Exp: %s, Cat: %s) -> run_id: %s",
            i + 1, total_pairs, drug, event, expected, category, run_id
        )

        if mode == "react":
            agent = PharmaGuardAgent(run_id=run_id)
        else:
            agent = FixedPipelineAgent(run_id=run_id)

        try:
            report = agent.run(drug, event)
            logger.info(
                "Generated report for %s + %s -> Signal: %s, Escalation: %s, Confidence: %.4f",
                drug, event, report.triage.signal_strength, report.triage.escalation, report.triage.confidence
            )

            report_path = output_dir / f"{run_id}_report.json"
            with open(report_path, "w", encoding="utf-8") as rf:
                rf.write(report.model_dump_json(indent=2))
        except Exception as e:
            logger.error("Error running agent on %s + %s: %s", drug, event, e, exc_info=True)

        # Rate-limit pacing between live API queries
        if delay_seconds > 0 and i < total_pairs - 1:
            logger.debug("Pacing delay: sleeping %.1fs before next pair...", delay_seconds)
            time.sleep(delay_seconds)

    logger.info("OMOP pilot evaluation run complete. %d reports written to %s", total_pairs, output_dir)


def main():
    parser = argparse.ArgumentParser(description="Run PharmaGuard evaluation on OMOP reference set pilot.")
    parser.add_argument(
        "--eval-file",
        type=Path,
        default=DEFAULT_EVAL_FILE,
        help="Path to OMOP pilot ground truth JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to save report JSON files.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Inter-pair delay in seconds for API rate-limit pacing (default: 3.0s).",
    )
    parser.add_argument(
        "--pairs-limit",
        type=int,
        default=None,
        help="Limit number of pairs evaluated (e.g. for smoke testing).",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run quick smoke test on first 2 pairs with 1.0s delay.",
    )
    args = parser.parse_args()

    if args.smoke_test:
        logger.info("Executing in SMOKE TEST mode (2 pairs, 1.0s delay)")
        run_omop_pilot_evaluation(
            eval_file=args.eval_file,
            output_dir=args.output_dir,
            delay_seconds=1.0,
            pairs_limit=2,
        )
    else:
        run_omop_pilot_evaluation(
            eval_file=args.eval_file,
            output_dir=args.output_dir,
            delay_seconds=args.delay,
            pairs_limit=args.pairs_limit,
        )


if __name__ == "__main__":
    main()
