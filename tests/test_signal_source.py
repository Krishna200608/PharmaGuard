"""
Unit tests for signal_source.py — runnable independently, no agent loop required.

Tests cover:
  - SignalStats null contract (zero-report pairs)
  - MockSignalSource fixture lookup and miss behaviour
  - FaersLegacySource raises NotImplementedError (stub compliance)

Owner: Krishna Sikheriya (IIT2023139)
"""

import pytest
from datetime import datetime, timezone

from pharmaguard.tools.signal_source import (
    FaersLegacySource,
    MockSignalSource,
    SignalStats,
)


# --- Fixtures ---

def _make_stat(**kwargs) -> SignalStats:
    defaults = dict(
        drug="testdrug",
        event="testevent",
        report_count=0,
        prr=None,
        ror=None,
        prr_lower_ci=None,
        ror_lower_ci=None,
        source_endpoint="mock_test",
        data_pulled_at=datetime.now(timezone.utc),
        null_reason="test fixture",
    )
    defaults.update(kwargs)
    return SignalStats(**defaults)


# --- Null contract ---

def test_zero_report_stat_has_null_fields():
    stat = _make_stat(report_count=0)
    assert stat.prr is None
    assert stat.ror is None
    assert stat.prr_lower_ci is None
    assert stat.null_reason is not None


def test_positive_report_stat_has_values():
    stat = _make_stat(
        report_count=312,
        prr=4.21,
        ror=4.35,
        prr_lower_ci=2.87,
        ror_lower_ci=2.99,
        null_reason=None,
    )
    assert stat.prr == 4.21
    assert stat.null_reason is None


# --- MockSignalSource ---

def test_mock_source_returns_fixture_on_hit():
    stat = _make_stat(drug="ozempic", event="pancreatitis", report_count=312, prr=4.21, ror=4.35, prr_lower_ci=2.87, ror_lower_ci=2.99, null_reason=None)
    source = MockSignalSource({("ozempic", "pancreatitis"): stat})
    result = source.get_signal_stats("ozempic", "pancreatitis")
    assert result.report_count == 312
    assert result.prr == 4.21


def test_mock_source_case_insensitive():
    stat = _make_stat(drug="ozempic", event="pancreatitis", report_count=5, prr=2.1, ror=2.2, prr_lower_ci=1.1, ror_lower_ci=1.2, null_reason=None)
    source = MockSignalSource({("ozempic", "pancreatitis"): stat})
    result = source.get_signal_stats("Ozempic", "Pancreatitis")
    assert result.report_count == 5


def test_mock_source_miss_returns_zero_report():
    source = MockSignalSource({})
    result = source.get_signal_stats("unknowndrug", "unknownevent")
    assert result.report_count == 0
    assert result.prr is None
    assert result.null_reason is not None
    assert result.source_endpoint == "mock_test"


# --- FaersLegacySource stub ---

def test_faers_legacy_raises_not_implemented():
    source = FaersLegacySource()
    with pytest.raises(NotImplementedError):
        source.get_signal_stats("ozempic", "pancreatitis")
