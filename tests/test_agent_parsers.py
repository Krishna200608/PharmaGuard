import pytest
from unittest.mock import MagicMock
from pydantic import BaseModel, Field
from typing import Literal
import os
from dotenv import load_dotenv

load_dotenv()

from pharmaguard.agent.fixed_pipeline import FixedPipelineAgent, GradeOutput
from pharmaguard.agent.fixed_pipeline import PlausibilityLLMOutput
from pharmaguard.agent.output_schema import PlausibilityLevel

def test_adversarial_grade_extraction():
    agent = FixedPipelineAgent("test-run")
    
    # Mock the structured LLM invoke
    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = GradeOutput(
        grade="B",
        explanation="Grade A Criteria: Needs RCTs. Final Grade: B"
    )
    
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    agent.llm = mock_llm
    
    pubmed_fn = agent.faers.pubmed_tool._llm_fn if hasattr(agent, 'faers') and hasattr(agent.faers, 'pubmed_tool') else agent.pubmed._llm_fn
    
    grade, pmids, text_content = pubmed_fn(["abstract"], ["1"], "rubric")
    
    # It should extract B correctly even though "Grade A" is in the explanation text
    assert grade == "B"

def test_adversarial_plausibility_extraction():
    agent = FixedPipelineAgent("test-run")
    
    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = PlausibilityLLMOutput(
        plausibility="LOW",
        explanation="It might look HIGH on first glance, but it is actually LOW."
    )
    
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    agent.llm = mock_llm
    
    chembl_fn = agent.chembl._llm_fn
    
    level, explanation = chembl_fn("moa", "event")

    # It should extract LOW correctly despite "HIGH" appearing in explanation
    assert level == PlausibilityLevel.LOW
    # And the explanation string should be passed through, not discarded
    assert isinstance(explanation, str)
    assert len(explanation) > 0
