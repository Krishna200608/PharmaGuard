"""
TriageReport — Pydantic output schema and deterministic confidence formula.

All fields are typed and versioned. The evaluation harness (Teammate 2)
consumes these JSON files directly — it has no dependency on agent internals.

Confidence formula (deterministic — not LLM self-reported):
  confidence = 0.40 × prr_score + 0.40 × grade_score + 0.20 × plausibility_score

Weights are constants here, also mirrored in config.yaml for visibility.

Owner: Krishna Sikheriya (IIT2023139)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


# ------------------------------------------------------------------
# Sub-enums
# ------------------------------------------------------------------

class SignalStrength(str, Enum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    NO_SIGNAL = "NO_SIGNAL"


class EvidenceGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class PlausibilityLevel(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class EscalationDecision(str, Enum):
    ESCALATE = "ESCALATE"
    MONITOR = "MONITOR"
    DO_NOT_ESCALATE = "DO_NOT_ESCALATE"


class PlausibilitySource(str, Enum):
    HUMAN_CURATED = "human_curated"
    AGENT_DERIVED = "agent_derived"
    UNKNOWN = "unknown"


# ------------------------------------------------------------------
# PRR score computation (deterministic, with fallthrough on CI failure)
# ------------------------------------------------------------------

PRR_SCORE_WEIGHTS = {"w_signal": 0.40, "w_grade": 0.40, "w_plausibility": 0.20}


def compute_prr_score(
    report_count: int,
    prr: Optional[float],
    prr_lower_ci: Optional[float],
) -> tuple[float, SignalStrength, bool]:
    """
    Compute PRR_score using the tiered table with explicit CI-downgrade fallthrough.

    PRR magnitude sets the ceiling; failing the CI gate drops the result one tier.
    Evaluated top-to-bottom — first matching row wins.

    Returns: (prr_score: float, label: SignalStrength, ci_downgraded: bool)

    Table (each row: condition → score, label):
      report_count == 0 or prr is None            → 0.0, NO_SIGNAL, False
      prr ≥ 5.0 AND lower_ci ≥ 2.0                → 1.0, STRONG, False
      prr ≥ 5.0 AND lower_ci < 2.0 [CI fail]      → 0.66, MODERATE, True  (downgraded from STRONG)
      3.0 ≤ prr < 5.0 AND lower_ci ≥ 1.5          → 0.66, MODERATE, False
      3.0 ≤ prr < 5.0 AND lower_ci < 1.5 [CI fail]→ 0.33, WEAK, True     (downgraded from MODERATE)
      2.0 ≤ prr < 3.0 AND lower_ci ≥ 1.0          → 0.33, WEAK, False
      2.0 ≤ prr < 3.0 AND lower_ci < 1.0 [CI fail]→ 0.0, NO_SIGNAL, True (downgraded from WEAK)
      prr < 2.0 (any CI)                           → 0.0, NO_SIGNAL, False
    """
    if report_count == 0 or prr is None or prr_lower_ci is None:
        return 0.0, SignalStrength.NO_SIGNAL, False

    # Top bucket
    if prr >= 5.0:
        if prr_lower_ci >= 2.0:
            return 1.0, SignalStrength.STRONG, False
        else:
            return 0.66, SignalStrength.MODERATE, True   # CI-downgraded from STRONG

    # Middle bucket
    if 3.0 <= prr < 5.0:
        if prr_lower_ci >= 1.5:
            return 0.66, SignalStrength.MODERATE, False
        else:
            return 0.33, SignalStrength.WEAK, True       # CI-downgraded from MODERATE

    # Lower bucket
    if 2.0 <= prr < 3.0:
        if prr_lower_ci >= 1.0:
            return 0.33, SignalStrength.WEAK, False
        else:
            return 0.0, SignalStrength.NO_SIGNAL, True   # CI-downgraded from WEAK

    # Below minimum threshold
    return 0.0, SignalStrength.NO_SIGNAL, False


_GRADE_SCORE_MAP: dict[str, float] = {"A": 1.0, "B": 0.5, "C": 0.0}
_PLAUSIBILITY_SCORE_MAP: dict[str, float] = {
    "HIGH": 1.0, "MODERATE": 0.5, "LOW": 0.0, "UNKNOWN": 0.0
}


def compute_confidence(
    prr_score: float, grade: str, plausibility: str
) -> float:
    """
    confidence = 0.40 × PRR_score + 0.40 × grade_score + 0.20 × plausibility_score

    All three sub-scores are deterministic (no LLM self-reporting).
    Weights are defined in PRR_SCORE_WEIGHTS and config.yaml.
    """
    grade_score = _GRADE_SCORE_MAP.get(grade, 0.0)
    plaus_score = _PLAUSIBILITY_SCORE_MAP.get(plausibility, 0.0)
    return round(
        PRR_SCORE_WEIGHTS["w_signal"] * prr_score
        + PRR_SCORE_WEIGHTS["w_grade"] * grade_score
        + PRR_SCORE_WEIGHTS["w_plausibility"] * plaus_score,
        4,
    )


def derive_escalation(confidence: float, signal_strength: SignalStrength) -> EscalationDecision:
    """
    Deterministic escalation decision from confidence score and signal strength label.

    Rules:
      confidence ≥ 0.70 AND strength ∈ {STRONG, MODERATE}  → ESCALATE
      confidence ≥ 0.35                                     → MONITOR
      otherwise                                             → DO_NOT_ESCALATE
    """
    # Gate 1: NO_SIGNAL hard-stop. Must run before confidence checks.
    # Rationale: literature + plausibility are corroborating inputs, not primary signals.
    # A zero-report pair (confidence achievable = 0.60 from grade-A + HIGH plausibility)
    # must not escalate — it is a hypothesis, not a verified disproportionality signal.
    if signal_strength == SignalStrength.NO_SIGNAL:
        return EscalationDecision.DO_NOT_ESCALATE

    # Gate 2: strong signal + high confidence -> escalate
    if confidence >= 0.70 and signal_strength in (SignalStrength.STRONG, SignalStrength.MODERATE):
        return EscalationDecision.ESCALATE

    # Gate 3: mid-range confidence -> monitor
    if confidence >= 0.35:
        return EscalationDecision.MONITOR

    return EscalationDecision.DO_NOT_ESCALATE


# ------------------------------------------------------------------
# Pydantic output schema
# ------------------------------------------------------------------

class SignalStatsOutput(BaseModel):
    prr: Optional[float]
    ror: Optional[float]
    prr_lower_ci: Optional[float]
    ror_lower_ci: Optional[float]
    report_count: int
    source_endpoint: str
    data_pulled_at: datetime
    null_reason: Optional[str] = None
    prr_score: float
    prr_score_label: SignalStrength
    ci_downgraded: bool = False


class MechanismOutput(BaseModel):
    chembl_id: Optional[str]
    moa: Optional[str]
    biological_plausibility: PlausibilityLevel
    plausibility_score: float
    plausibility_source: PlausibilitySource
    plausibility_rationale: str
    # Populated only in force_agent ablation mode
    curated_reference: Optional[PlausibilityLevel] = None
    plausibility_agreement: Optional[bool] = None


class LiteratureOutput(BaseModel):
    pubmed_query: str
    abstracts_retrieved: int
    evidence_grade: EvidenceGrade
    grade_score: float
    supporting_pmids: list[str]
    evidence_summary: str


class TriageOutput(BaseModel):
    signal_strength: SignalStrength
    evidence_grade: EvidenceGrade
    escalation: EscalationDecision
    confidence: float
    prompts_version: str
    agent_reasoning_trace: list[str]   # summarised steps; raw transcript in run_logs/


class TriageReport(BaseModel):
    schema_version: str = "1.1"
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    prompts_version: str

    # Input
    drug: str
    event: str

    # Tool outputs
    signal_stats: SignalStatsOutput
    mechanism: MechanismOutput
    literature: LiteratureOutput

    # Final triage
    triage: TriageOutput

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)
