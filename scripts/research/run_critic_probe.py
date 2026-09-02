"""
Adversarial Leakage Critic Probe Runner.

Re-evaluates the four documented leak cases from DECISIONS.md §17 and §19
using the newly implemented adversarial critic agent.

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

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from pharmaguard.agent.output_schema import LeakageCritique
from pharmaguard.utils.config_loader import load_config
from pharmaguard.utils.prompt_loader import PromptLoader

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROBE_CASES = [
    {
        "drug": "topiramate",
        "event": "hypohidrosis",
        "reference_section": "DECISIONS.md §17 (Probe Case 1)",
        "original_plausibility": "HIGH",
        "rationale": (
            "The mechanism of action includes carbonic anhydrase II and IV inhibition, "
            "which is the primary pharmacological profile of topiramate. Carbonic anhydrase "
            "inhibitors are well-documented to cause hypohidrosis (decreased sweating) and "
            "hyperthermia, particularly in pediatric populations, due to the inhibition of "
            "carbonic anhydrase in the sweat glands."
        ),
    },
    {
        "drug": "tamsulosin",
        "event": "intraoperative_floppy_iris_syndrome",
        "reference_section": "DECISIONS.md §17 (Probe Case 2)",
        "original_plausibility": "HIGH",
        "rationale": (
            "Intraoperative floppy iris syndrome (IFIS) is a well-documented clinical "
            "complication strongly associated with the use of alpha-1 adrenergic receptor "
            "antagonists, particularly tamsulosin, which targets the alpha-1A receptor subtype. "
            "The mechanism involves the blockade of alpha-1 receptors in the iris dilator muscle, "
            "leading to poor pupil dilation and iris instability during cataract surgery."
        ),
    },
    {
        "drug": "terbinafine",
        "event": "ageusia",
        "reference_section": "DECISIONS.md §17 (Probe Case 3)",
        "original_plausibility": "MODERATE",
        "rationale": (
            "Ageusia (loss of taste) is a well-documented, though relatively uncommon, side effect "
            "associated with terbinafine, a squalene monooxygenase inhibitor. While the exact mechanism "
            "is not fully understood, it is thought to be related to the drug's affinity for zinc or "
            "its accumulation in the taste buds, leading to reversible dysgeusia or ageusia in some patients."
        ),
    },
    {
        "drug": "montelukast",
        "event": "suicidal_ideation",
        "reference_section": "DECISIONS.md §19 & Ablation Report eval-run-0",
        "original_plausibility": "MODERATE",
        "rationale": (
            "The FDA has issued a boxed warning for montelukast, a prominent leukotriene receptor "
            "antagonist, due to the risk of serious neuropsychiatric events, including suicidal "
            "ideation and behavior. While the exact mechanism remains under investigation, clinical "
            "data and post-marketing surveillance have established a recognized association between "
            "the drug class and these adverse effects."
        ),
    },
]


def run_critic_probe():
    load_dotenv()
    config = load_config()
    prompt_loader = PromptLoader()

    critic_prompt_template = prompt_loader.get("leakage_critic")
    llm = ChatGoogleGenerativeAI(model=config.agent.llm_model, temperature=0.0)
    structured_critic = llm.with_structured_output(LeakageCritique)

    probe_results = []

    print("\n" + "=" * 90)
    print("PHARMAGUARD ADVERSARIAL LEAKAGE CRITIC PROBE EVALUATION (4 Documented Cases)")
    print("=" * 90)

    for case in PROBE_CASES:
        pair_str = f"{case['drug']}::{case['event']}"
        prompt = critic_prompt_template.replace("{rationale}", case["rationale"])

        logger.info(f"Critiquing {pair_str}...")
        critique: LeakageCritique = structured_critic.invoke([HumanMessage(content=prompt)])

        res_dict = {
            "drug": case["drug"],
            "event": case["event"],
            "reference_section": case["reference_section"],
            "original_plausibility": case["original_plausibility"],
            "original_rationale": case["rationale"],
            "critic_evaluation": {
                "leaked": critique.leaked,
                "leak_phrases": critique.leak_phrases,
                "mechanistic_only_score": critique.mechanistic_only_score,
                "rationale_critique": critique.rationale_critique,
            },
        }
        probe_results.append(res_dict)

        print(f"\nCase: {pair_str} ({case['reference_section']})")
        print(f"  Original Plausibility Score: {case['original_plausibility']}")
        print(f"  Leakage Detected by Critic:  {critique.leaked}")
        print(f"  Flagged Leak Phrases:        {critique.leak_phrases}")
        print(f"  Mechanistic-Only Score:      {critique.mechanistic_only_score}")
        if critique.rationale_critique:
            print(f"  Critic Notes:                {critique.rationale_critique}")

    # Write to outputs/experiments/critic_probe/leakage_critique_results.json
    out_dir = REPO_ROOT / "outputs" / "experiments" / "critic_probe"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "leakage_critique_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"probe_cases": probe_results}, f, indent=2)
    logger.info(f"Saved critique results to {out_file}")

    print("\n" + "=" * 90)
    print(f"Probe completed. All {len(probe_results)} cases evaluated and saved to {out_file}.")
    print("=" * 90 + "\n")

    return probe_results


if __name__ == "__main__":
    run_critic_probe()