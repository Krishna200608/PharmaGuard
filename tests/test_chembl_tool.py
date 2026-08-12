import pytest
from pharmaguard.tools.chembl_tool import ChemblTool, PlausibilityLevel, PlausibilityResult
from pharmaguard.tools.cache import ToolCache

@pytest.fixture
def chembl_tool(tmp_path):
    cache = ToolCache(cache_dir=tmp_path)
    
    def mock_llm(moa, event):
        return PlausibilityLevel.MODERATE, "Mock agent explanation."
        
    return ChemblTool(
        cache=cache,
        prompts_version="v1.0",
        force_agent_derivation=False,
        llm_inference_fn=mock_llm
    )

def test_drug_lookup_hit(chembl_tool):
    entry = chembl_tool.get_drug_entry("semaglutide")
    assert entry is not None
    assert entry.canonical_name == "Semaglutide"

def test_drug_lookup_miss(chembl_tool):
    entry = chembl_tool.get_drug_entry("unknown_drug")
    assert entry is None

def test_plausibility_human_curated(chembl_tool):
    result = chembl_tool.get_plausibility("semaglutide", "pancreatitis")
    assert result.plausibility_source == "human_curated"
    assert result.level == PlausibilityLevel.HIGH
    assert result.score == 1.0

def test_plausibility_miss_falls_back_to_agent(chembl_tool):
    result = chembl_tool.get_plausibility("semaglutide", "unknown_event")
    assert result.plausibility_source == "agent_derived"
    assert result.level == PlausibilityLevel.MODERATE
    assert result.score == 0.5

def test_force_agent_mode(tmp_path):
    cache = ToolCache(cache_dir=tmp_path)
    def mock_llm(moa, event):
        return PlausibilityLevel.LOW, "Mock agent explanation (LOW)." # Disagrees with HIGH
        
    tool = ChemblTool(
        cache=cache,
        prompts_version="v1.0",
        force_agent_derivation=True,
        llm_inference_fn=mock_llm
    )
    
    result = tool.get_plausibility("semaglutide", "pancreatitis")
    assert result.plausibility_source == "agent_derived"
    assert result.level == PlausibilityLevel.LOW
    assert result.curated_reference == PlausibilityLevel.HIGH
    assert result.agreement is False
