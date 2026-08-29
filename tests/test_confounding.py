"""
Unit tests for pharmaguard.tools.confounding (ConfoundingAssessment and ConfoundingTool).
"""

from unittest.mock import MagicMock
import pytest
from pydantic import ValidationError
from langchain_core.messages import HumanMessage

from pharmaguard.tools.confounding import ConfoundingAssessment, ConfoundingTool
from pharmaguard.utils.prompt_loader import PromptLoader


# ----------------------------------------------------------------------
# 1. Model Validation Tests (ConfoundingAssessment)
# ----------------------------------------------------------------------

def test_confounding_assessment_valid():
    """Verify ConfoundingAssessment accepts valid parameters within bounds [0.0, 1.0]."""
    assessment = ConfoundingAssessment(
        is_confounded=True,
        confounding_drugs=["insulin", "sulfonylureas"],
        discount_factor=0.25,
        confounding_explanation="Polypharmacy with insulin drives hypoglycaemia reports."
    )
    assert assessment.is_confounded is True
    assert assessment.confounding_drugs == ["insulin", "sulfonylureas"]
    assert assessment.discount_factor == 0.25
    assert "Polypharmacy" in assessment.confounding_explanation

    # Boundary cases: 0.0 and 1.0
    a_min = ConfoundingAssessment(
        is_confounded=True,
        discount_factor=0.0,
        confounding_explanation="Zero causal attribution."
    )
    assert a_min.discount_factor == 0.0
    assert a_min.confounding_drugs == []  # default_factory test

    a_max = ConfoundingAssessment(
        is_confounded=False,
        discount_factor=1.0,
        confounding_explanation="Fully unconfounded signal."
    )
    assert a_max.discount_factor == 1.0


def test_confounding_assessment_discount_factor_upper_bound():
    """Verify discount_factor > 1.0 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ConfoundingAssessment(
            is_confounded=False,
            discount_factor=1.05,
            confounding_explanation="Out of bounds above 1.0."
        )
    assert "discount_factor" in str(exc_info.value)


def test_confounding_assessment_discount_factor_lower_bound():
    """Verify discount_factor < 0.0 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ConfoundingAssessment(
            is_confounded=True,
            discount_factor=-0.1,
            confounding_explanation="Out of bounds below 0.0."
        )
    assert "discount_factor" in str(exc_info.value)


# ----------------------------------------------------------------------
# 2. ConfoundingTool.assess() Success & Prompt Substitution
# ----------------------------------------------------------------------

@pytest.fixture
def mock_llm_and_structured():
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    return mock_llm, mock_structured


def test_confounding_tool_assess_success(mock_llm_and_structured):
    """Verify ConfoundingTool.assess() substitutes prompt placeholders and returns structured model."""
    mock_llm, mock_structured = mock_llm_and_structured
    expected_response = ConfoundingAssessment(
        is_confounded=True,
        confounding_drugs=["insulin", "glimepiride"],
        discount_factor=0.30,
        confounding_explanation="Widely co-prescribed in type 2 diabetes management."
    )
    mock_structured.invoke.return_value = expected_response

    prompt_loader = PromptLoader()
    tool = ConfoundingTool(llm=mock_llm, prompt_loader=prompt_loader)

    result = tool.assess(
        drug="metformin",
        event="hypoglycaemia",
        moa="Inhibits hepatic gluconeogenesis",
        report_count=9344,
        prr=10.73
    )

    # Verify structured output requested on LLM
    mock_llm.with_structured_output.assert_called_once_with(ConfoundingAssessment)

    # Verify prompt argument passed to invoke
    assert mock_structured.invoke.call_count == 1
    call_args = mock_structured.invoke.call_args[0][0]
    assert len(call_args) == 1
    assert isinstance(call_args[0], HumanMessage)

    prompt_text = call_args[0].content
    assert "Candidate Drug: metformin" in prompt_text
    assert "Reported Adverse Event: hypoglycaemia" in prompt_text
    assert "Mechanism of Action (MoA): Inhibits hepatic gluconeogenesis" in prompt_text
    assert "FAERS Total Co-occurrence Reports: 9344" in prompt_text
    assert "FAERS Proportional Reporting Ratio (PRR): 10.73" in prompt_text

    # Verify returned result
    assert result == expected_response
    assert result.is_confounded is True
    assert result.discount_factor == 0.30
    assert result.confounding_drugs == ["insulin", "glimepiride"]


# ----------------------------------------------------------------------
# 3. ConfoundingTool.assess() Exception Fallback Path
# ----------------------------------------------------------------------

def test_confounding_tool_assess_exception_fallback(mock_llm_and_structured):
    """Verify ConfoundingTool.assess() safely falls back when LLM invocation raises."""
    mock_llm, mock_structured = mock_llm_and_structured
    mock_structured.invoke.side_effect = RuntimeError("API connection timeout")

    prompt_loader = PromptLoader()
    tool = ConfoundingTool(llm=mock_llm, prompt_loader=prompt_loader)

    result = tool.assess(
        drug="metformin",
        event="hypoglycaemia",
        moa="Inhibits hepatic gluconeogenesis",
        report_count=9344,
        prr=10.73
    )

    # Safe fallback guarantees
    assert isinstance(result, ConfoundingAssessment)
    assert result.is_confounded is False
    assert result.confounding_drugs == []
    assert result.discount_factor == 1.0
    assert result.confounding_explanation.startswith("Assessment failed with error: API connection timeout")


# ----------------------------------------------------------------------
# 4. Edge Cases: prr=None and moa=None/Empty
# ----------------------------------------------------------------------

def test_confounding_tool_assess_prr_none(mock_llm_and_structured):
    """Verify prr=None is formatted as 'N/A' in prompt substitution without crashing."""
    mock_llm, mock_structured = mock_llm_and_structured
    mock_structured.invoke.return_value = ConfoundingAssessment(
        is_confounded=False,
        confounding_drugs=[],
        discount_factor=1.0,
        confounding_explanation="Zero reports in FAERS."
    )

    prompt_loader = PromptLoader()
    tool = ConfoundingTool(llm=mock_llm, prompt_loader=prompt_loader)

    result = tool.assess(
        drug="albuterol",
        event="suicidal_ideation",
        moa="Beta-2 adrenergic agonist",
        report_count=0,
        prr=None
    )

    prompt_text = mock_structured.invoke.call_args[0][0][0].content
    assert "FAERS Proportional Reporting Ratio (PRR): N/A" in prompt_text
    assert "FAERS Total Co-occurrence Reports: 0" in prompt_text
    assert result.is_confounded is False


def test_confounding_tool_assess_moa_none_or_empty(mock_llm_and_structured):
    """Verify None or empty moa is substituted with 'Not available' without crashing."""
    mock_llm, mock_structured = mock_llm_and_structured
    mock_structured.invoke.return_value = ConfoundingAssessment(
        is_confounded=False,
        confounding_drugs=[],
        discount_factor=1.0,
        confounding_explanation="No MoA available."
    )

    prompt_loader = PromptLoader()
    tool = ConfoundingTool(llm=mock_llm, prompt_loader=prompt_loader)

    # Test with moa=None
    tool.assess(drug="drugA", event="eventA", moa=None, report_count=10, prr=2.5)
    prompt_none = mock_structured.invoke.call_args[0][0][0].content
    assert "Mechanism of Action (MoA): Not available" in prompt_none
    assert "FAERS Proportional Reporting Ratio (PRR): 2.50" in prompt_none

    # Test with moa=""
    tool.assess(drug="drugB", event="eventB", moa="", report_count=5, prr=1.5)
    prompt_empty = mock_structured.invoke.call_args[0][0][0].content
    assert "Mechanism of Action (MoA): Not available" in prompt_empty