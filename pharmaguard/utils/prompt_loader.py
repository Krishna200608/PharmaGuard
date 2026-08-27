"""
PromptLoader — loads versioned prompt templates from the prompts/ directory.

All agent and tool modules call this; none of them contain hardcoded prompt strings.
Versioning: prompts_version.txt contains the current version string.
Any change to a prompt file MUST be accompanied by a version bump.

Owner: Krishna Sikheriya (IIT2023139)
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "pharmaguard" / "prompts"
_VERSION_FILE = _PROMPTS_DIR / "prompts_version.txt"


class PromptLoader:
    """
    Loads prompt templates from pharmaguard/prompts/ at runtime.

    Available prompt keys:
      "react_system"            → react_system.txt
      "react_tool_call_format"  → react_tool_call_format.txt
      "evidence_grading_rubric" → evidence_grading_rubric.txt
      "synthesis"               → synthesis_prompt.txt
      "baseline_single_shot"    → baseline_single_shot.txt

    Usage:
        loader = PromptLoader()
        system_prompt = loader.get("react_system")
        print(loader.version)   # e.g. "v1.0"
    """

    _KEY_TO_FILE: dict[str, str] = {
        "react_system": "react_system.txt",
        "react_tool_call_format": "react_tool_call_format.txt",
        "evidence_grading_rubric": "evidence_grading_rubric.txt",
        "synthesis": "synthesis_prompt.txt",
        "baseline_single_shot": "baseline_single_shot.txt",
        "leakage_critic": "leakage_critic.txt",
        "confounding_assessment": "confounding_assessment.txt",
    }

    def __init__(self):
        self._cache: dict[str, str] = {}
        self._version = self._load_version()

    @property
    def version(self) -> str:
        return self._version

    def get(self, key: str) -> str:
        """
        Return the prompt template for the given key.
        Templates are cached in-memory after first load (they don't change mid-run).
        Raises KeyError if the key is not registered in _KEY_TO_FILE.
        Raises FileNotFoundError if the corresponding .txt file is missing.
        """
        if key not in self._KEY_TO_FILE:
            raise KeyError(
                f"Unknown prompt key '{key}'. "
                f"Available keys: {list(self._KEY_TO_FILE.keys())}"
            )
        if key not in self._cache:
            filepath = _PROMPTS_DIR / self._KEY_TO_FILE[key]
            if not filepath.exists():
                raise FileNotFoundError(
                    f"Prompt file missing: {filepath}. "
                    f"Create it before running the agent."
                )
            self._cache[key] = filepath.read_text(encoding="utf-8").strip()
            logger.debug("Loaded prompt '%s' from %s", key, filepath)
        return self._cache[key]

    def _load_version(self) -> str:
        if _VERSION_FILE.exists():
            return _VERSION_FILE.read_text(encoding="utf-8").strip()
        logger.warning(
            "prompts_version.txt not found at %s — defaulting to 'v0.0'", _VERSION_FILE
        )
        return "v0.0"
