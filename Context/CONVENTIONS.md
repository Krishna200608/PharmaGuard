Last updated: 2026-08-10 | Sprint: Sprint 1 (Transitioning to Sprint 2) | Updated by: Antigravity

# CONVENTIONS

## File and Folder Structure
- pharmaguard/agent/: Core ReAct orchestrator loop, LLM setup, and output_schema.py.
- pharmaguard/tools/: Distinct tool wrappers (signal_source.py, chembl_tool.py, pubmed_tool.py, cache.py).
- pharmaguard/data/: Datasets, including pre-resolved ChEMBL lookups and ground truth data.
- pharmaguard/utils/: Support functions like prompt_loader.py and config_loader.py.
- pharmaguard/prompts/: Text files containing versioned prompts (e.g., evidence_grading_rubric.txt). 
- 	ests/: Comprehensive test suite (pytest) covering agent edge-cases.
- outputs/: Destination for final output TriageReport JSONs to be graded by the evaluator.

## Coding Style Patterns
- **Typing**: Strict type hinting is enforced throughout the codebase (Pydantic, Enum, Optional, 	uple, dict[str, float], etc.). 
- **Docstrings**: Plain ASCII Python docstrings without esoteric formatting. Every schema and tool method requires explicitly documented mechanics. Docstrings reflect exactly what the code does; when a rule is modified, its respective docstring is always rewritten.
- **Dependency Inversion**: Components utilize standard software engineering decoupling (e.g., passing ToolCache as an instantiated dependency inside FaersLegacySource.__init__ rather than globally initializing it).

## Testing Approach
- **Tool Mocks and Fixtures**: External HTTP requests are rigorously mocked out using monkeypatch (e.g., intercepting equests.get or _fetch_count). 
- **Behavioral Tests**: For stateful interactions like caching, behavior tests explicitly assert execution conditions (e.g., checking that call_count == 4 on the first call and does not increase on the subsequent identical call, rather than just asserting outputs match).
- **Adversarial Edge Cases**: Tests actively target adversarial data to expose heuristic vulnerabilities (e.g., 	est_adversarial_regression_avoids_or_substring).

## Team Ownership Rules
- **Krishna (Core Technical)**: Owns ~70-80% of core framework engineering, which includes agent logic, orchestration, configuration loops, and tool wrapper architecture.
- **Teammate 1 (Data & Baseline)**: Owns ground-truth curation, extending data/plausibility_ratings.json, and creating single-shot baseline functionality.
- **Teammate 2 (Evaluation & Docs)**: Owns the evaluation harness (specifically evaluator.py) to parse TriageReport outputs using strict/lenient evaluation logic as defined in NOTES.md.
