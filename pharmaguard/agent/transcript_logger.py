"""
TranscriptLogger — writes raw per-run ReAct tool-call transcripts to disk.

Separate from TriageReport.triage.agent_reasoning_trace (the summarised version).
Raw transcripts are for debugging ReAct reliability without burning API calls on re-runs.

Output path: run_logs/{run_id}/raw_transcript.jsonl
             run_logs/{run_id}/cache_hits.json

The run_logs/ directory is gitignored. Never include raw transcripts in evaluation
outputs — the evaluation harness reads TriageReport JSON files only.

Owner: Krishna Sikheriya (IIT2023139)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_RUN_LOGS_DIR = Path(__file__).resolve().parents[2] / "run_logs"


class TranscriptLogger:
    """
    Append-only JSONL logger for raw ReAct steps.

    Usage:
        tlog = TranscriptLogger(run_id="abc-123")
        tlog.log_thought("I need to check FAERS first.")
        tlog.log_action("faers_signal_tool", {"drug": "Ozempic", "event": "Pancreatitis"})
        tlog.log_observation("faers_signal_tool", {"prr": 4.21}, cache_hit=False)
        tlog.finalize(cache_hits_summary={...})
    """

    def __init__(self, run_id: str):
        self._run_id = run_id
        self._run_dir = _RUN_LOGS_DIR / run_id
        self._run_dir.mkdir(parents=True, exist_ok=True)
        self._transcript_path = self._run_dir / "raw_transcript.jsonl"
        self._cache_hits_path = self._run_dir / "cache_hits.json"
        self._step = 0
        self._cache_hits: dict[str, bool] = {}
        logger.debug("TranscriptLogger initialised at %s", self._run_dir)

    # ------------------------------------------------------------------
    # Step loggers
    # ------------------------------------------------------------------

    def log_thought(self, content: str) -> None:
        self._append({"type": "thought", "content": content})

    def log_action(self, tool: str, input_data: dict[str, Any]) -> None:
        self._append({"type": "action", "tool": tool, "input": input_data})

    def log_observation(
        self, tool: str, output_data: Any, cache_hit: bool = False
    ) -> None:
        self._cache_hits[tool] = cache_hit
        self._append({
            "type": "observation",
            "tool": tool,
            "output": output_data,
            "cache_hit": cache_hit,
        })

    def log_final_answer(self, summary: str) -> None:
        self._append({"type": "final_answer", "content": summary})

    # ------------------------------------------------------------------
    # Finalize
    # ------------------------------------------------------------------

    def finalize(self) -> None:
        """Write the cache hits summary JSON. Call once at end of run."""
        with open(self._cache_hits_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "run_id": self._run_id,
                    "finalized_at": datetime.now(timezone.utc).isoformat(),
                    "tool_cache_hits": self._cache_hits,
                    "total_steps": self._step,
                },
                fh,
                indent=2,
            )
        logger.debug("Transcript finalized: %s steps logged.", self._step)

    @property
    def transcript_path(self) -> Path:
        return self._transcript_path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _append(self, data: dict[str, Any]) -> None:
        self._step += 1
        record = {
            "step": self._step,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        with open(self._transcript_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
