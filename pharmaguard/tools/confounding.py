"""
Confounding Assessment Tool — detects polypharmacy and co-prescription confounding.

Provides structured evaluation of whether statistical disproportionality signals
in FAERS are driven by concomitant medications or clinical indication confounding.

Owner: Krishna Sikheriya (IIT2023139)
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class ConfoundingAssessment(BaseModel):
    """
    Structured output from the confounding assessment LLM evaluator.
    """
    is_confounded: bool = Field(
        description="True if the FAERS disproportionality signal is significantly driven by co-medications or indication confounding."
    )
    confounding_drugs: list[str] = Field(
        default_factory=list,
        description="List of concomitant medications or drug classes that independently cause or contribute to the adverse event."
    )
    discount_factor: float = Field(
        ge=0.0,
        le=1.0,
        description="Multiplier (0.0 to 1.0) representing the fraction of the statistical signal genuinely attributable to the candidate drug."
    )
    confounding_explanation: str = Field(
        description="Clinical and pharmacological rationale explaining the confounding assessment."
    )


class ConfoundingTool:
    """
    Evaluates whether a high FAERS disproportionality signal is confounded by polypharmacy.
    """

    def __init__(self, llm, prompt_loader):
        self._llm = llm
        self._prompt_loader = prompt_loader

    def assess(
        self,
        drug: str,
        event: str,
        moa: str,
        report_count: int,
        prr: Optional[float]
    ) -> ConfoundingAssessment:
        prompt_template = self._prompt_loader.get("confounding_assessment")
        prr_str = f"{prr:.2f}" if prr is not None else "N/A"
        prompt = (
            prompt_template
            .replace("{drug}", drug)
            .replace("{event}", event)
            .replace("{moa}", moa or "Not available")
            .replace("{report_count}", str(report_count))
            .replace("{prr}", prr_str)
        )

        structured_llm = self._llm.with_structured_output(ConfoundingAssessment)
        try:
            return structured_llm.invoke([HumanMessage(content=prompt)])
        except Exception as e:
            logger.warning("Confounding assessment failed for %s::%s: %s", drug, event, e)
            return ConfoundingAssessment(
                is_confounded=False,
                confounding_drugs=[],
                discount_factor=1.0,
                confounding_explanation=f"Assessment failed with error: {e}"
            )