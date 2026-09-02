"""
Confounding Self-Probe Runner (Mandatory Epistemic Audit).

Tests whether the LLM confounding assessment exhibits the same parametric recall
and training-data memorization ("well-known", textbook drug interaction recall)
documented in DECISIONS.md §17 for biological plausibility.

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

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from pharmaguard.tools.confounding import ConfoundingTool, ConfoundingAssessment
from pharmaguard.tools.signal_source import FaersLegacySource
from pharmaguard.tools.chembl_tool import ChemblTool
from pharmaguard.tools.cache import ToolCache
from pharmaguard.utils.config_loader import load_config
from pharmaguard.utils.prompt_loader import PromptLoader

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CANDIDATES = [
    {
        "drug": "metformin",
        "event": "hypoglycaemia",
        "context": "Documented §21 failure case (T2D first-line biguanide)",
    },
    {
        "drug": "semaglutide",
        "event": "hypoglycaemia",
        "context": "GLP-1 agonist with glucose-dependent insulin secretion (not in 15-pair benchmark)",
    },
    {
        "drug": "rosiglitazone",
        "event": "hypoglycaemia",
        "context": "PPAR-gamma agonist (euglycemic monotherapy; not in 15-pair benchmark for this event)",
    },
    {
        "drug": "warfarin",
        "event": "gastrointestinal_haemorrhage",
        "context": "Vitamin K antagonist confounded/amplified by concurrent NSAID/antiplatelet use",
        "moa_override": "Vitamin K epoxide reductase (VKOR) inhibitor; inhibits gamma-carboxylation of clotting factors II, VII, IX, X."
    },
]


def run_confounding_self_probe():
    load_dotenv()
    config = load_config()
    cache = ToolCache()
    prompt_loader = PromptLoader()
    faers = FaersLegacySource(cache=cache)
    chembl = ChemblTool(cache=cache, prompts_version=prompt_loader.version)

    llm = ChatGoogleGenerativeAI(model=config.agent.llm_model, temperature=0.0)
    c_tool = ConfoundingTool(llm=llm, prompt_loader=prompt_loader)

    probe_results = []

    print("\n" + "=" * 90)
    print("PHARMAGUARD CONFOUNDING SELF-PROBE EVALUATION (MANDATORY EPISTEMIC AUDIT)")
    print("=" * 90)

    for cand in CANDIDATES:
        drug = cand["drug"]
        event = cand["event"]
        stats = faers.get_signal_stats(drug, event)

        moa = cand.get("moa_override")
        if not moa:
            entry = chembl.get_drug_entry(drug)
            moa = entry.mechanism_of_action if entry else "N/A"

        logger.info(f"Assessing confounding for {drug}::{event} (reports={stats.report_count}, PRR={stats.prr:.2f})...")
        assessment: ConfoundingAssessment = c_tool.assess(
            drug=drug,
            event=event,
            moa=moa,
            report_count=stats.report_count,
            prr=stats.prr,
        )

        res = {
            "drug": drug,
            "event": event,
            "context": cand["context"],
            "report_count": stats.report_count,
            "prr": round(stats.prr, 4) if stats.prr is not None else None,
            "moa": moa,
            "assessment": assessment.model_dump(),
        }
        probe_results.append(res)

        print(f"\nCandidate: {drug}::{event}")
        print(f"  Context:             {cand['context']}")
        print(f"  FAERS Statistics:    Reports = {stats.report_count:,} | PRR = {stats.prr:.2f}")
        print(f"  Is Confounded:       {assessment.is_confounded}")
        print(f"  Discount Factor:     {assessment.discount_factor:.2f}")
        print(f"  Confounding Drugs:   {assessment.confounding_drugs}")
        print(f"  Full Rationale Text:\n    \"{assessment.confounding_explanation}\"")

    out_dir = REPO_ROOT / "outputs" / "experiments" / "confounding_probe"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "confounding_self_probe.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"probe_cases": probe_results}, f, indent=2)
    logger.info(f"Saved self-probe results to {out_file}")

    print("\n" + "=" * 90)
    print("Self-probe complete. Inspect verbatim rationales for parametric/textbook recall markers.")
    print("=" * 90 + "\n")

    return probe_results


if __name__ == "__main__":
    run_confounding_self_probe()