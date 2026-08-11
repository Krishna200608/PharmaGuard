"""
Run Pilot Set - tests the orchestrator against the pilot dataset.
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

def run_pilot():
    load_dotenv()
    
    project_root = Path(__file__).resolve().parents[1]
    pilot_file = project_root / "pharmaguard" / "data" / "pilot_set.json"
    
    if not pilot_file.exists():
        logger.error(f"Pilot file not found at {pilot_file}")
        return
        
    with open(pilot_file, "r") as f:
        pilot_data = json.load(f)
        
    pairs = pilot_data.get("pairs", [])
    if not pairs:
        logger.error("No pairs found in pilot set.")
        return
        
    config = load_config()
    mode = config.agent.mode
    logger.info(f"Running in mode: {mode}")
    
    for i, pair in enumerate(pairs):
        drug = pair["drug"]
        event = pair["event"]
        run_id = f"pilot-run-{i}-{drug.replace(' ', '')}-{event.replace(' ', '')}"
        
        logger.info(f"Testing Pair {i+1}: {drug} + {event} -> run_id: {run_id}")
        
        if mode == "react":
            agent = PharmaGuardAgent(run_id=run_id)
        else:
            agent = FixedPipelineAgent(run_id=run_id)
            
        try:
            report = agent.run(drug, event)
            logger.info(f"Generated report successfully. Signal Strength: {report.triage.signal_strength}, Escalation: {report.triage.escalation}")
            
            # Save the final report
            output_dir = project_root / "outputs"
            output_dir.mkdir(exist_ok=True)
            with open(output_dir / f"{run_id}_report.json", "w", encoding="utf-8") as rf:
                rf.write(report.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Error running agent on {drug} + {event}: {e}")

if __name__ == "__main__":
    run_pilot()
