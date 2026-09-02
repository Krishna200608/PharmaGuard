"""
Run Evaluation Set - tests the orchestrator against the full 15-pair ground truth.
"""
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from pharmaguard.utils.config_loader import load_config
from pharmaguard.agent.react_agent import PharmaGuardAgent
from pharmaguard.agent.fixed_pipeline import FixedPipelineAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_evaluation_set(eval_file: Path = None, output_dir: Path = None):
    load_dotenv()
    
    project_root = Path(__file__).resolve().parents[1]
    if eval_file is None:
        eval_file = project_root / "pharmaguard" / "data" / "ground_truth.json"
    
    if not eval_file.exists():
        logger.error(f"Ground truth file not found at {eval_file}")
        return
        
    with open(eval_file, "r", encoding="utf-8") as f:
        eval_data = json.load(f)
        
    pairs = eval_data.get("pairs", [])
    if not pairs:
        logger.error("No pairs found in ground truth set.")
        return
        
    config = load_config()
    mode = config.agent.mode
    logger.info(f"Running in mode: {mode}")
    
    if output_dir is None:
        output_dir = project_root / config.paths.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, pair in enumerate(pairs):
        drug = pair["drug_canonical"]
        event = pair["event_meddra_pt"]
        # Generate safe filenames like run_pilot.py
        run_id = f"eval-run-{i}-{drug.replace(' ', '')}-{event.replace(' ', '')}"
        
        logger.info(f"Testing Pair {i+1}/{len(pairs)}: {drug} + {event} -> run_id: {run_id}")
        
        if mode == "react":
            agent = PharmaGuardAgent(run_id=run_id)
        else:
            agent = FixedPipelineAgent(run_id=run_id)
            
        try:
            report = agent.run(drug, event)
            logger.info(f"Generated report successfully. Signal Strength: {report.triage.signal_strength}, Escalation: {report.triage.escalation}")
            
            with open(output_dir / f"{run_id}_report.json", "w", encoding="utf-8") as rf:
                rf.write(report.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Error running agent on {drug} + {event}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run evaluation set against a ground truth file.")
    parser.add_argument("--eval-file", type=Path, default=None, help="Path to ground truth JSON file.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory to save report JSON files.")
    args = parser.parse_args()
    run_evaluation_set(eval_file=args.eval_file, output_dir=args.output_dir)
