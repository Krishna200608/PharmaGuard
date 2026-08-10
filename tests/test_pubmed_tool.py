import pytest
from pharmaguard.tools.pubmed_tool import PubMedTool
from pharmaguard.tools.cache import ToolCache
from pharmaguard.utils.prompt_loader import PromptLoader

@pytest.fixture
def pubmed_tool(tmp_path):
    cache = ToolCache(cache_dir=tmp_path)
    # Using a dummy prompt loader
    loader = PromptLoader()
    return PubMedTool(cache=cache, prompt_loader=loader)

def test_grade_evidence_c(pubmed_tool):
    abstracts = ["This paper talks about unrelated things.", "Nothing to see here."]
    pmids = ["1", "2"]
    grade, supporting, summary = pubmed_tool._grade_evidence(abstracts, pmids)
    assert grade == "C"
    assert len(supporting) == 0

def test_grade_evidence_b(pubmed_tool):
    abstracts = ["A case report describing a patient who developed a side effect.", "Unrelated."]
    pmids = ["1", "2"]
    grade, supporting, summary = pubmed_tool._grade_evidence(abstracts, pmids)
    assert grade == "B"
    assert "1" in supporting

def test_grade_evidence_a(pubmed_tool):
    abstracts = [
        "The association was statistically significant with p < 0.05.",
        "We found an odds ratio of 2.5 (95% ci).",
        "Unrelated."
    ]
    pmids = ["1", "2", "3"]
    grade, supporting, summary = pubmed_tool._grade_evidence(abstracts, pmids)
    assert grade == "A"
    assert "1" in supporting
    assert "2" in supporting
