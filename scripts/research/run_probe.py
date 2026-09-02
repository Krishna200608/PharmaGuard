"""
Probe Script: Memorization-vs-Reasoning Evaluation on Obscure Pharmacological Pairs.
Evaluates 3 non-headline, mechanistically-grounded pairs outside the 15-pair benchmark.
"""
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import sys

project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from pharmaguard.agent.fixed_pipeline import FixedPipelineAgent
from pharmaguard.utils.config_loader import load_config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROBE_PAIRS = [
    {
        "drug": "topiramate",
        "event": "hypohidrosis",
        "rationale_hypothesis": "Carbonic anhydrase (CA-II/IV) inhibition in eccrine sweat glands suppresses sweat secretion."
    },
    {
        "drug": "tamsulosin",
        "event": "intraoperative_floppy_iris_syndrome",
        "rationale_hypothesis": "Alpha-1A adrenoreceptor blockade in iris dilator muscle causes loss of muscular tone and surgical prolapse."
    },
    {
        "drug": "terbinafine",
        "event": "ageusia",
        "rationale_hypothesis": "Squalene epoxidase inhibition and lingual lipophilic accumulation with zinc cofactor interference in taste buds."
    }
]

def run_probe():
    load_dotenv()
    output_dir = project_root / "outputs" / "experiments" / "probe"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("PHARMAGUARD MEMORIZATION-VS-REASONING PROBE (SUPPLEMENTARY CASE STUDY)")
    print("=" * 70)
    
    results = []
    
    for i, item in enumerate(PROBE_PAIRS):
        drug = item["drug"]
        event = item["event"]
        run_id = f"probe-run-{i}-{drug}-{event}"
        print(f"\n[{i+1}/3] Running Probe: {drug} + {event}")
        
        # Initialize pipeline agent in force_agent plausibility mode
        agent = FixedPipelineAgent(run_id=run_id)
        agent.chembl._force_agent = True
        
        report = agent.run(drug, event)
        
        # Save JSON output
        report_path = output_dir / f"{run_id}_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
            
        entry = agent.chembl.get_drug_entry(drug)
        moa = entry.mechanism_of_action if entry else "N/A"
        
        results.append({
            "drug": drug,
            "event": event,
            "input_moa": moa,
            "plausibility_level": report.mechanism.biological_plausibility.value if hasattr(report.mechanism.biological_plausibility, 'value') else report.mechanism.biological_plausibility,
            "plausibility_score": report.mechanism.plausibility_score,
            "plausibility_rationale": report.mechanism.plausibility_rationale,
            "faers_rc": report.signal_stats.report_count,
            "faers_prr": report.signal_stats.prr,
            "faers_signal": report.signal_stats.prr_score_label.value if hasattr(report.signal_stats.prr_score_label, 'value') else report.signal_stats.prr_score_label,
            "pubmed_count": report.literature.abstracts_retrieved,
            "pubmed_grade": report.literature.evidence_grade.value if hasattr(report.literature.evidence_grade, 'value') else report.literature.evidence_grade,
            "confidence": report.triage.confidence,
            "escalation": report.triage.escalation.value if hasattr(report.triage.escalation, 'value') else report.triage.escalation
        })
        
    print("\n" + "=" * 70)
    print("PROBE RESULTS SUMMARY")
    print("=" * 70)
    for r in results:
        print(f"\n>>> Pair: {r['drug']} + {r['event']}")
        print(f"Input MoA: {r['input_moa']}")
        print(f"Agent Plausibility: {r['plausibility_level']} (score: {r['plausibility_score']})")
        print(f"Verbatim Rationale:\n  \"{r['plausibility_rationale']}\"")
        prr_str = f"{r['faers_prr']:.2f}" if r['faers_prr'] is not None else "None"
        print(f"FAERS: Reports={r['faers_rc']}, PRR={prr_str} (Signal: {r['faers_signal']})")
        print(f"PubMed: Abstracts={r['pubmed_count']}, Grade={r['pubmed_grade']}")
        print(f"Final Triage: Confidence={r['confidence']:.3f}, Escalation={r['escalation']}")

if __name__ == "__main__":
    run_probe()
