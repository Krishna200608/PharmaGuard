"""
ChEMBL tool — static lookup + agent-derived plausibility (cache-routed).

Design decisions:
  1. Pre-resolved ChEMBL IDs in data/chembl_lookup.json — no live fuzzy
     name-matching during a triage run. Deliberate reliability tradeoff (brief §arch req 2).
     Do NOT replace with dynamic resolution without approval.
  2. Plausibility is drug+EVENT keyed (data/plausibility_ratings.json).
     Human-curated entries (Naitik Jain) are the production default.
  3. force_agent_derivation mode: bypasses the lookup and calls the LLM-derived
     path even for curated pairs — used ONLY in evaluation ablation runs.
     Controlled via config.yaml plausibility.source setting.
  4. Agent-derived calls go through the cache layer (same rate-limit protections
     as FAERS and PubMed). Cache key includes prompts_version.

Owner: Krishna Sikheriya (IIT2023139)
Plausibility data owner: Naitik Jain (IIB2023036) — do not edit plausibility_ratings.json
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from pharmaguard.tools.cache import ToolCache

logger = logging.getLogger(__name__)

# --- Paths ---
_DATA_DIR = Path(__file__).resolve().parents[2] / "pharmaguard" / "data"
_CHEMBL_LOOKUP_PATH = _DATA_DIR / "chembl_lookup.json"
_PLAUSIBILITY_RATINGS_PATH = _DATA_DIR / "plausibility_ratings.json"


class PlausibilityLevel(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


PLAUSIBILITY_SCORE_MAP: dict[PlausibilityLevel, float] = {
    PlausibilityLevel.HIGH: 1.0,
    PlausibilityLevel.MODERATE: 0.5,
    PlausibilityLevel.LOW: 0.0,
    PlausibilityLevel.UNKNOWN: 0.0,
}


@dataclass
class ChemblEntry:
    """Structured representation of one entry in chembl_lookup.json."""
    chembl_id: str
    canonical_name: str
    trade_names: list[str]
    mechanism_of_action: str
    target_name: str
    target_class: str
    resolved_at: str
    chembl_url: str


@dataclass
class PlausibilityResult:
    """
    Output of the plausibility lookup/derivation step.

    plausibility_source:
      "human_curated"  — entry found in plausibility_ratings.json
      "agent_derived"  — LLM derived from MoA text (cache-backed)
      "unknown"        — drug not in chembl_lookup.json at all
    """
    level: PlausibilityLevel
    score: float
    rationale: str
    plausibility_source: str          # "human_curated" | "agent_derived" | "unknown"
    curated_reference: Optional[PlausibilityLevel] = None   # populated only in force_agent mode
    agreement: Optional[bool] = None                        # populated only in force_agent mode


class ChemblTool:
    """
    Provides:
      - drug metadata lookup from the pre-resolved static table
      - plausibility rating for (drug, event) pairs via human-curated lookup
        or (on miss / force_agent mode) LLM derivation from MoA text

    The LLM inference path is injected at construction so this class has no
    direct dependency on LangChain/Gemini — unit tests can pass a stub.
    """

    def __init__(
        self,
        cache: ToolCache,
        prompts_version: str,
        force_agent_derivation: bool = False,
        llm_inference_fn=None,         # callable(moa: str, event: str) -> PlausibilityLevel
    ):
        self._cache = cache
        self._prompts_version = prompts_version
        self._force_agent = force_agent_derivation
        self._llm_fn = llm_inference_fn

        self._chembl_lookup = self._load_json(_CHEMBL_LOOKUP_PATH).get("drugs", {})
        self._plausibility_ratings = self._load_json(_PLAUSIBILITY_RATINGS_PATH).get("entries", {})

    # ------------------------------------------------------------------
    # Drug metadata
    # ------------------------------------------------------------------

    def get_drug_entry(self, drug_canonical: str) -> Optional[ChemblEntry]:
        """
        Return ChEMBL metadata for a drug by its canonical name (lowercase).
        Returns None if the drug is not in the pre-resolved lookup table.
        """
        raw = self._chembl_lookup.get(drug_canonical.lower())
        if raw is None:
            logger.warning("Drug '%s' not found in chembl_lookup.json", drug_canonical)
            return None
        return ChemblEntry(**raw)

    # ------------------------------------------------------------------
    # Plausibility
    # ------------------------------------------------------------------

    def get_plausibility(self, drug_canonical: str, event_meddra_pt: str) -> PlausibilityResult:
        """
        Returns a PlausibilityResult for the (drug, event) pair.

        Logic:
          - If force_agent_derivation=False (default production mode):
              1. Check plausibility_ratings.json → return human-curated entry if found.
              2. On miss: call agent-derived path (cache-backed).
          - If force_agent_derivation=True (ablation/evaluation mode):
              1. Call agent-derived path regardless.
              2. Also load human-curated entry if it exists.
              3. Populate curated_reference and agreement on the result.
        """
        lookup_key = f"{drug_canonical.lower()}::{event_meddra_pt.lower()}"
        curated_entry = self._plausibility_ratings.get(lookup_key)

        if self._force_agent:
            return self._derive_plausibility_with_comparison(
                drug_canonical, event_meddra_pt, lookup_key, curated_entry
            )

        # Default: curated first, agent on miss
        if curated_entry:
            level = PlausibilityLevel(curated_entry["plausibility"])
            return PlausibilityResult(
                level=level,
                score=PLAUSIBILITY_SCORE_MAP[level],
                rationale=curated_entry.get("rationale", ""),
                plausibility_source="human_curated",
            )

        logger.info(
            "Plausibility miss for '%s::%s' — falling back to agent derivation.",
            drug_canonical, event_meddra_pt
        )
        return self._derive_plausibility(drug_canonical, event_meddra_pt)

    def _derive_plausibility(
        self, drug_canonical: str, event_meddra_pt: str
    ) -> PlausibilityResult:
        """
        LLM-derived plausibility from ChEMBL MoA text.
        Routes through the cache layer — same rate-limit protection as all tools.
        """
        cache_key = self._cache.plausibility_key(
            drug_canonical, event_meddra_pt, self._prompts_version
        )
        cached = self._cache.get(cache_key)
        if cached:
            return PlausibilityResult(**cached, plausibility_source="agent_derived")

        entry = self.get_drug_entry(drug_canonical)
        if entry is None or self._llm_fn is None:
            result = PlausibilityResult(
                level=PlausibilityLevel.UNKNOWN,
                score=0.0,
                rationale="Drug not found in ChEMBL lookup or LLM not configured.",
                plausibility_source="unknown",
            )
            return result

        level = self._llm_fn(entry.mechanism_of_action, event_meddra_pt)
        result_data = {
            "level": level.value,
            "score": PLAUSIBILITY_SCORE_MAP[level],
            "rationale": f"Agent-derived from MoA: '{entry.mechanism_of_action}'",
        }
        self._cache.set(cache_key, result_data)
        return PlausibilityResult(**result_data, plausibility_source="agent_derived")

    def _derive_plausibility_with_comparison(
        self,
        drug_canonical: str,
        event_meddra_pt: str,
        lookup_key: str,
        curated_entry: Optional[dict],
    ) -> PlausibilityResult:
        """
        force_agent mode: derive via LLM, then compare against curated entry (if any).
        Populates curated_reference and agreement for ablation analysis.
        """
        agent_result = self._derive_plausibility(drug_canonical, event_meddra_pt)

        if curated_entry:
            curated_level = PlausibilityLevel(curated_entry["plausibility"])
            agent_result.curated_reference = curated_level
            agent_result.agreement = (agent_result.level == curated_level)
            logger.info(
                "Ablation | %s | agent=%s curated=%s agree=%s",
                lookup_key, agent_result.level, curated_level, agent_result.agreement
            )
        return agent_result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_json(path: Path) -> dict:
        if not path.exists():
            logger.warning("Expected data file not found: %s", path)
            return {}
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
