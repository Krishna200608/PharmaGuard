"""
PubMed tool — E-utilities search + abstract fetch + evidence grading.

Design decisions:
  - Evidence grading rubric is loaded from prompts/evidence_grading_rubric.txt
    at runtime, not hardcoded here. Iterate on the rubric file without touching
    this module.
  - Grading function (_grade_evidence) is isolated and independently testable —
    pass it a list of abstract strings, get back a grade and supporting PMIDs.
  - All API calls are cache-backed via ToolCache.
  - NCBI API key loaded from environment (set NCBI_API_KEY in .env).
    Without a key, E-utilities rate limit is 3 req/s. With key: 10 req/s.

Owner: Krishna Sikheriya (IIT2023139)
"""

import logging
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

import requests

from pharmaguard.tools.cache import ToolCache
from pharmaguard.utils.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
MAX_ABSTRACTS = 5       # per brief: fetch top-N, not unbounded
REQUEST_DELAY = 0.35    # seconds between calls (safe for 3 req/s without key)


@dataclass
class PubMedResult:
    """Output of one PubMed evidence lookup."""
    query: str
    abstracts_retrieved: int
    pmids: list[str]
    abstracts: list[str]            # parallel list with pmids
    evidence_grade: str             # "A" | "B" | "C"
    supporting_pmids: list[str]     # subset of pmids that supported the grade
    evidence_summary: str           # 1-2 sentence human-readable summary


class PubMedTool:
    """
    Queries PubMed E-utilities for literature evidence on a (drug, event) pair
    and grades the evidence using the loaded rubric.
    """

    def __init__(self, cache: ToolCache, prompt_loader: PromptLoader, llm_inference_fn=None):
        self._cache = cache
        self._prompt_loader = prompt_loader
        self._api_key = os.getenv("NCBI_API_KEY", "")
        self._llm_fn = llm_inference_fn
        if not self._api_key:
            logger.warning(
                "NCBI_API_KEY not set — rate limited to 3 req/s. "
                "Add key to .env for 10 req/s."
            )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def search_and_grade(self, drug: str, event: str) -> PubMedResult:
        """
        Build a PubMed query from (drug, event), fetch abstracts, and grade evidence.
        Results are cache-backed by query hash.
        """
        query = self._build_query(drug, event)
        cache_key = self._cache.pubmed_key(query)
        cached = self._cache.get(cache_key)
        if cached:
            return PubMedResult(**cached)

        pmids = self._esearch(query)
        abstracts = self._efetch_abstracts(pmids[:MAX_ABSTRACTS])
        grade, supporting_pmids, summary = self._grade_evidence(abstracts, pmids[:MAX_ABSTRACTS], query)

        result = PubMedResult(
            query=query,
            abstracts_retrieved=len(abstracts),
            pmids=pmids[:MAX_ABSTRACTS],
            abstracts=abstracts,
            evidence_grade=grade,
            supporting_pmids=supporting_pmids,
            evidence_summary=summary,
        )
        self._cache.set(cache_key, result.__dict__)
        return result

    # ------------------------------------------------------------------
    # Internal: query construction
    # ------------------------------------------------------------------

    @staticmethod
    def _build_query(drug: str, event: str) -> str:
        """
        Build a PubMed search query combining drug name and adverse event term.
        Uses MeSH-friendly construction; no controlled vocabulary enforcement
        at this stage (future improvement if recall is low).
        """
        return f'"{drug}"[tiab] AND "{event}"[tiab] AND "adverse"[tiab]'

    # ------------------------------------------------------------------
    # Internal: E-utilities calls
    # ------------------------------------------------------------------

    def _esearch(self, query: str) -> list[str]:
        """Return up to MAX_ABSTRACTS PMIDs for the query."""
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": MAX_ABSTRACTS,
            "retmode": "json",
        }
        if self._api_key:
            params["api_key"] = self._api_key

        try:
            time.sleep(REQUEST_DELAY)
            resp = requests.get(f"{EUTILS_BASE}/esearch.fcgi", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            pmids = data.get("esearchresult", {}).get("idlist", [])
            logger.debug("ESearch '%s' → %d PMIDs", query, len(pmids))
            return pmids
        except requests.RequestException as exc:
            logger.error("ESearch failed for query '%s': %s", query, exc)
            return []

    def _efetch_abstracts(self, pmids: list[str]) -> list[str]:
        """Fetch abstract text for a list of PMIDs. Returns parallel list."""
        if not pmids:
            return []
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "rettype": "abstract",
            "retmode": "xml",
        }
        if self._api_key:
            params["api_key"] = self._api_key

        try:
            time.sleep(REQUEST_DELAY)
            resp = requests.get(f"{EUTILS_BASE}/efetch.fcgi", params=params, timeout=15)
            resp.raise_for_status()
            return self._parse_abstracts_xml(resp.text)
        except requests.RequestException as exc:
            logger.error("EFetch failed for PMIDs %s: %s", pmids, exc)
            return []

    @staticmethod
    def _parse_abstracts_xml(xml_text: str) -> list[str]:
        """Extract AbstractText elements from PubMed XML response."""
        abstracts = []
        try:
            root = ET.fromstring(xml_text)
            for article in root.findall(".//PubmedArticle"):
                abstract_el = article.find(".//AbstractText")
                abstracts.append(
                    abstract_el.text.strip() if abstract_el is not None and abstract_el.text else ""
                )
        except ET.ParseError as exc:
            logger.error("XML parse error on PubMed response: %s", exc)
        return abstracts

    # ------------------------------------------------------------------
    # Internal: evidence grading (isolated, independently testable)
    # ------------------------------------------------------------------

    def _grade_evidence(
        self, abstracts: list[str], pmids: list[str], query: str
    ) -> tuple[str, list[str], str]:
        """
        Grade evidence quality from a list of abstract texts.

        Returns: (grade: "A"|"B"|"C", supporting_pmids: list, summary: str)

        Grade definitions (from prompts/evidence_grading_rubric.txt):
          A — ≥2 abstracts contain statistically significant association
              (language: "significant", "p <", "OR", "RR", "HR", "risk")
          B — ≥1 abstract with association OR case report language
              ("case report", "we report", "describe a patient", "adverse event")
          C — No supporting language found in any retrieved abstract

        The rubric text is loaded from prompts/ — this function implements
        the rubric, but the rubric itself is defined in the prompt file so it
        can be iterated without touching this code.
        """
        if not abstracts:
            return "C", [], "No abstracts retrieved from PubMed for this query."

        cache_key = self._cache.pubmed_grade_key(query, self._prompt_loader.version)
        cached = self._cache.get(cache_key)
        if cached:
            return cached["grade"], cached["supporting"], cached["summary"]

        if self._llm_fn is None:
            # Fallback for testing if LLM is not provided
            return "C", [], "LLM not configured for semantic grading."

        try:
            rubric = self._prompt_loader.get("evidence_grading_rubric")
        except FileNotFoundError:
            return "C", [], "Grading rubric file missing."

        # We pass the abstracts, PMIDs, and rubric to the LLM function
        # The LLM function is expected to return (grade, supporting_pmids, summary)
        grade, supporting, summary = self._llm_fn(abstracts, pmids, rubric)
        
        result_data = {
            "grade": grade,
            "supporting": supporting,
            "summary": summary
        }
        self._cache.set(cache_key, result_data)
        logger.info("Evidence grade (LLM derived): %s | supporting PMIDs: %s", grade, supporting)
        return grade, supporting, summary
