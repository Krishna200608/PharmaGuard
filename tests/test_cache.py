"""
Unit tests for cache.py — key builders, get/set/invalidate, stats.

Uses a temporary directory so tests don't pollute the project cache.

Owner: Krishna Sikheriya (IIT2023139)
"""

import pytest
from pathlib import Path
from pharmaguard.tools.cache import ToolCache, CACHE_SCHEMA_VERSION


@pytest.fixture
def tmp_cache(tmp_path) -> ToolCache:
    cache = ToolCache(cache_dir=tmp_path / "test_cache", ttl=60)
    yield cache
    cache.close()


def test_cache_miss_returns_none(tmp_cache):
    assert tmp_cache.get("nonexistent::key") is None


def test_cache_set_and_get(tmp_cache):
    tmp_cache.set("faers::ozempic::pancreatitis::v3", {"prr": 4.21})
    result = tmp_cache.get("faers::ozempic::pancreatitis::v3")
    assert result == {"prr": 4.21}


def test_cache_invalidate(tmp_cache):
    tmp_cache.set("faers::ozempic::pancreatitis::v3", {"prr": 4.21})
    tmp_cache.invalidate("faers::ozempic::pancreatitis::v3")
    assert tmp_cache.get("faers::ozempic::pancreatitis::v3") is None


def test_faers_key_format(tmp_cache):
    key = ToolCache.faers_key("Ozempic", "Pancreatitis")
    assert key == f"faers::ozempic::pancreatitis::{CACHE_SCHEMA_VERSION}"


def test_pubmed_key_is_deterministic():
    key1 = ToolCache.pubmed_key("semaglutide pancreatitis adverse")
    key2 = ToolCache.pubmed_key("semaglutide pancreatitis adverse")
    assert key1 == key2


def test_plausibility_key_includes_version():
    key = ToolCache.plausibility_key("semaglutide", "pancreatitis", "v1.0")
    assert "v1.0" in key
    key2 = ToolCache.plausibility_key("semaglutide", "pancreatitis", "v1.1")
    assert key != key2   # version bump invalidates key


def test_cache_stats(tmp_cache):
    tmp_cache.set("test::key", "value")
    stats = tmp_cache.stats()
    assert stats["entry_count"] == 1
    assert "cache_dir" in stats
