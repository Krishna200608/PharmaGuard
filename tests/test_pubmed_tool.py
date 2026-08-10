import pytest
from pharmaguard.tools.pubmed_tool import PubMedTool
from pharmaguard.tools.cache import ToolCache
from pharmaguard.utils.prompt_loader import PromptLoader

@pytest.fixture
def pubmed_tool(tmp_path):
    cache = ToolCache(cache_dir=tmp_path)
    loader = PromptLoader()
    
    # Mock LLM that returns "A" only if "statistically significant" is in text
    def mock_llm(abstracts, pmids, rubric):
        has_stats = any("statistically significant" in a.lower() for a in abstracts)
        if has_stats:
            return "A", pmids, "Found significant association"
        return "C", [], "No association"
        
    return PubMedTool(cache=cache, prompt_loader=loader, llm_inference_fn=mock_llm)

def test_grade_evidence_c(pubmed_tool):
    abstracts = ["This paper talks about unrelated things.", "Nothing to see here."]
    pmids = ["1", "2"]
    grade, supporting, summary = pubmed_tool._grade_evidence(abstracts, pmids, "query1")
    assert grade == "C"
    assert len(supporting) == 0

def test_adversarial_regression_avoids_or_substring(pubmed_tool):
    # This text contains " or ", " hr ", " rr " in non-statistical context
    abstracts = [
        "Patients were scheduled for surgery or discharged. "
        "The hr department was busy. The rr interval was normal."
    ]
    pmids = ["1"]
    grade, supporting, summary = pubmed_tool._grade_evidence(abstracts, pmids, "query2")
    
    # It should NOT grade A purely due to substring matches
    assert grade != "A"
    assert grade == "C"

def test_grade_evidence_a(pubmed_tool):
    abstracts = [
        "The association was statistically significant with p < 0.05.",
        "Unrelated."
    ]
    pmids = ["1", "2"]
    grade, supporting, summary = pubmed_tool._grade_evidence(abstracts, pmids, "query3")
    assert grade == "A"
    assert "1" in supporting
    assert "2" in supporting
