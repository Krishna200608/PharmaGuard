"""
SignalDataSource — Abstract interface for FAERS/ADE signal data sources.

Design note: FAERS is mid-migration to the AEMS platform (legacy endpoint guaranteed
through end-of-2026). The abstraction here means swapping the backend is a new
concrete class — zero changes to orchestration or evaluation code.

Owner: Krishna Sikheriya (IIT2023139)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class SignalStats:
    """
    Holds disproportionality signal statistics for a (drug, event) pair.

    Null contract:
      - report_count == 0  → prr, ror, prr_lower_ci, ror_lower_ci are all None.
      - null_reason        → populated with a human-readable explanation.
      - PRR_score will be 0.0 in all null/zero-count cases.

    data_pulled_at: UTC timestamp of the actual live API call (or the timestamp of
    the cache-entry creation for cache hits). Always present for reproducibility.
    """
    drug: str
    event: str
    report_count: int
    prr: Optional[float]
    ror: Optional[float]
    prr_lower_ci: Optional[float]
    ror_lower_ci: Optional[float]
    source_endpoint: str          # "openfda_legacy" | "aems" | "mock_test"
    data_pulled_at: datetime      # UTC
    null_reason: Optional[str] = field(default=None)


class SignalDataSource(ABC):
    """
    Abstract base class for adverse-event signal data sources.

    Concrete implementations:
      - FaersLegacySource  → openFDA legacy /drug/event endpoint (current)
      - AemsSource         → AEMS platform (future swap, same interface)
      - MockSignalSource   → test doubles for unit tests (no network)
    """

    @abstractmethod
    def get_signal_stats(self, drug: str, event: str) -> SignalStats:
        """
        Query the data source for co-occurrence counts and disproportionality
        statistics for the given (drug, event) pair.

        Implementations MUST:
          - Return a SignalStats with report_count=0 and null_reason set
            when no records are found (do not raise on zero results).
          - Set data_pulled_at to the actual API call time (UTC), even on
            cache hits — the cache layer handles timestamp preservation.
          - Set source_endpoint to a string identifying this backend.
        """
        ...


class FaersLegacySource(SignalDataSource):
    """
    Concrete implementation against the openFDA legacy /drug/event endpoint.

    PRR  = (a / (a+b)) / (c / (c+d))
    ROR  = (a/b) / (c/d)

    where:
      a = reports with THIS drug AND THIS event
      b = reports with THIS drug, WITHOUT this event
      c = reports WITHOUT this drug, WITH this event
      d = reports with NEITHER

    Approximate CI uses the Woolf log-CI method (standard for FAERS analyses).
    PRR counts all drug mentions, not just primary-suspect reports (standard simplification,
    worth stating explicitly rather than leaving implicit).

    Rate limiting and disk caching are supported natively if a ToolCache is provided.
    """

    BASE_URL: str = "https://api.fda.gov/drug/event.json"

    def __init__(self, cache=None):
        import os
        self._cache = cache
        self._api_key = os.getenv("OPENFDA_API_KEY", "")

    def _fetch_count(self, query_params: dict) -> int:
        import requests
        import logging
        params = dict(query_params)
        if self._api_key:
            params["api_key"] = self._api_key
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=15)
            if resp.status_code == 404:
                return 0
            resp.raise_for_status()
            return resp.json().get('meta', {}).get('results', {}).get('total', 0)
        except requests.RequestException as e:
            logging.getLogger(__name__).warning(f"openFDA query failed: {e}")
            return 0

    def _finalize(self, drug: str, event: str, stats: SignalStats) -> SignalStats:
        """Helper to ensure all returns are consistently cache-written."""
        if self._cache:
            dump = stats.__dict__.copy()
            dump["data_pulled_at"] = dump["data_pulled_at"].isoformat()
            self._cache.set(self._cache.faers_key(drug, event), dump)
        return stats

    def get_signal_stats(self, drug: str, event: str) -> SignalStats:
        """
        Fetch disproportionality statistics from the openFDA legacy endpoint.
        """
        import math
        
        if self._cache:
            cached = self._cache.get(self._cache.faers_key(drug, event))
            if cached:
                # Deserialize ISO formatted datetime if necessary
                if isinstance(cached.get("data_pulled_at"), str):
                    cached["data_pulled_at"] = datetime.fromisoformat(cached["data_pulled_at"])
                return SignalStats(**cached)
        
        # 1. Fetch co-occurrence count first. If 0, short-circuit.
        from pharmaguard.utils.text import normalize_term
        ndrug = normalize_term(drug)
        nevent = normalize_term(event)
        
        q_both = {'search': f'(patient.drug.medicinalproduct:"{ndrug}") AND (patient.reaction.reactionmeddrapt:"{nevent}")', 'limit': 1}
        a = self._fetch_count(q_both)
        
        if a == 0:
            return self._finalize(drug, event, SignalStats(
                drug=drug,
                event=event,
                report_count=0,
                prr=None,
                ror=None,
                prr_lower_ci=None,
                ror_lower_ci=None,
                source_endpoint="openfda_legacy",
                data_pulled_at=datetime.now(timezone.utc),
                null_reason="Zero co-occurrences found in FAERS."
            ))
            
        # 2. Fetch marginal and total counts
        q_drug = {'search': f'patient.drug.medicinalproduct:"{ndrug}"', 'limit': 1}
        q_event = {'search': f'patient.reaction.reactionmeddrapt:"{nevent}"', 'limit': 1}
        q_total = {'limit': 1}
        
        n_drug = self._fetch_count(q_drug)
        n_event = self._fetch_count(q_event)
        n_total = self._fetch_count(q_total)
        
        # 3. Calculate contingency table cells
        b = n_drug - a
        c = n_event - a
        d = n_total - a - b - c
        
        if b <= 0 or c <= 0 or d <= 0:
            return self._finalize(drug, event, SignalStats(
                drug=drug,
                event=event,
                report_count=a,
                prr=None,
                ror=None,
                prr_lower_ci=None,
                ror_lower_ci=None,
                source_endpoint="openfda_legacy",
                data_pulled_at=datetime.now(timezone.utc),
                null_reason="Insufficient data for disproportionality calculation."
            ))
            
        # 4. Compute statistics
        prr = (a / (a + b)) / (c / (c + d))
        ror = (a / b) / (c / d)
        
        se_log_prr = math.sqrt(1/a - 1/(a+b) + 1/c - 1/(c+d))
        prr_lower_ci = math.exp(math.log(prr) - 1.96 * se_log_prr)
        
        se_log_ror = math.sqrt(1/a + 1/b + 1/c + 1/d)
        ror_lower_ci = math.exp(math.log(ror) - 1.96 * se_log_ror)
        
        return self._finalize(drug, event, SignalStats(
            drug=drug,
            event=event,
            report_count=a,
            prr=prr,
            ror=ror,
            prr_lower_ci=prr_lower_ci,
            ror_lower_ci=ror_lower_ci,
            source_endpoint="openfda_legacy",
            data_pulled_at=datetime.now(timezone.utc),
            null_reason=None
        ))

    # Note: MockSignalSource below

class MockSignalSource(SignalDataSource):
    """
    In-memory test double. Accepts a dict of (drug, event) → SignalStats
    at construction. Used exclusively in unit tests — never in production runs.
    """

    def __init__(self, fixture: dict[tuple[str, str], SignalStats]):
        self._fixture = fixture

    def get_signal_stats(self, drug: str, event: str) -> SignalStats:
        key = (drug.lower(), event.lower())
        if key in self._fixture:
            return self._fixture[key]
        return SignalStats(
            drug=drug,
            event=event,
            report_count=0,
            prr=None,
            ror=None,
            prr_lower_ci=None,
            ror_lower_ci=None,
            source_endpoint="mock_test",
            data_pulled_at=datetime.now(timezone.utc),
            null_reason="No fixture entry found for this (drug, event) pair.",
        )
