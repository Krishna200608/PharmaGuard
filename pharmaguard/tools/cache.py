"""
Cache layer — disk-backed, shared across all PharmaGuard tool calls.

Design decisions:
  - Uses diskcache.Cache (pip: diskcache) — persistent across runs, handles
    concurrent access safely, supports TTL per key.
  - Every tool call MUST go through this layer before hitting a live API.
    This is not optional given Gemini Flash free-tier rate limits.
  - Agent-derived plausibility calls also route through here, keyed with
    the prompts version to auto-invalidate on rubric updates.

Key format conventions:
  - FAERS:      "faers::{drug_lower}::{event_lower}"
  - PubMed:     "pubmed::{query_hash}"
  - Plausibility: "plausibility::{drug_lower}::{event_lower}::{prompts_version}"

Owner: Krishna Sikheriya (IIT2023139)
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional

import diskcache  # pip install diskcache

logger = logging.getLogger(__name__)

# Default cache directory — overridden by config.yaml at runtime
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "pharmaguard"

# Default TTL: 7 days (FAERS data is stable; PubMed abstracts don't change)
DEFAULT_TTL_SECONDS: int = 7 * 24 * 60 * 60

# Internal schema version to auto-invalidate cached logic/parsing outputs.
# Bump this whenever the underlying parsing or schema logic changes.
CACHE_SCHEMA_VERSION = "v7"

class ToolCache:
    """
    Thin wrapper around diskcache.Cache that enforces key conventions,
    logs all hits and misses, and exposes a simple get/set interface.

    Usage:
        cache = ToolCache()
        key = cache.faers_key("ozempic", "pancreatitis")
        result = cache.get(key)
        if result is None:
            result = live_api_call(...)
            cache.set(key, result)
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl: int = DEFAULT_TTL_SECONDS,
    ):
        self._dir = cache_dir or DEFAULT_CACHE_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._cache = diskcache.Cache(str(self._dir))
        self._ttl = ttl
        logger.info("ToolCache initialised at %s (TTL=%ds)", self._dir, ttl)

    # ------------------------------------------------------------------
    # Key builders — enforce naming conventions in one place
    # ------------------------------------------------------------------

    @staticmethod
    def faers_key(drug: str, event: str) -> str:
        return f"faers::{drug.lower().strip()}::{event.lower().strip()}::{CACHE_SCHEMA_VERSION}"

    @staticmethod
    def pubmed_key(query: str) -> str:
        """Hash the full query string so long queries don't blow key limits."""
        digest = hashlib.sha256(query.encode()).hexdigest()[:16]
        return f"pubmed::{digest}"

    @staticmethod
    def pubmed_grade_key(query: str, prompts_version: str) -> str:
        """Cache the LLM grading step separately to avoid re-fetching abstracts."""
        digest = hashlib.sha256(query.encode()).hexdigest()[:16]
        return f"pubmed_grade::{digest}::{prompts_version}::{CACHE_SCHEMA_VERSION}"

    @staticmethod
    def plausibility_key(drug: str, event: str, prompts_version: str) -> str:
        """
        Includes prompts_version and CACHE_SCHEMA_VERSION so rubric/logic updates auto-invalidate cached
        agent-derived plausibility scores without touching FAERS/PubMed cache.
        """
        return (
            f"plausibility::{drug.lower().strip()}"
            f"::{event.lower().strip()}"
            f"::{prompts_version}"
            f"::{CACHE_SCHEMA_VERSION}"
        )

    # ------------------------------------------------------------------
    # Core get/set
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        value = self._cache.get(key)
        if value is not None:
            logger.debug("CACHE HIT  | %s", key)
        else:
            logger.debug("CACHE MISS | %s", key)
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._cache.set(key, value, expire=ttl or self._ttl)
        logger.debug("CACHE SET  | %s (TTL=%ds)", key, ttl or self._ttl)

    def invalidate(self, key: str) -> None:
        """Explicitly evict a key (e.g. after a known data refresh)."""
        self._cache.delete(key)
        logger.info("CACHE EVICT | %s", key)

    def clear_all(self) -> None:
        """Nuclear option — wipe the entire cache. Use only in tests."""
        self._cache.clear()
        logger.warning("CACHE CLEARED — all entries evicted.")

    def stats(self) -> dict:
        return {
            "cache_dir": str(self._dir),
            "size_bytes": self._cache.volume(),
            "entry_count": len(self._cache),
        }

    def close(self) -> None:
        self._cache.close()
