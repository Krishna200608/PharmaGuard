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

    Rate limiting and disk caching are handled by the caller (cache.py wrapper),
    not inside this class. This class is a pure data-fetching concern.
    """

    BASE_URL: str = "https://api.fda.gov/drug/event.json"

    def get_signal_stats(self, drug: str, event: str) -> SignalStats:
        """
        Fetch disproportionality statistics from the openFDA legacy endpoint.

        Implementation note: full implementation in Sprint 1.
        Stub signature here ensures interface compliance is testable from day 1.
        """
        raise NotImplementedError(
            "FaersLegacySource.get_signal_stats — to be implemented in Sprint 1."
        )


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
