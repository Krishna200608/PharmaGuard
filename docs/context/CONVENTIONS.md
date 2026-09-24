Last updated: 2026-08-29 | Sprint: Completed Capstone Benchmark | Updated by: Antigravity

# CONVENTIONS

## Team Ownership Rules

- **Krishna Sikheriya (IIT2023139)**: Owns 100% of the project. This includes core framework engineering, agent logic, orchestration, data curation, the evaluation harness, and documentation. No other collaborators are active.

## Data Curation & Anti-Circularity Rule

- **MoA Curation (DECISIONS.md section 1.1)**: Mechanism of Action (MoA) text must be authored or reviewed strictly for general pharmacology **WITHOUT** looking at which adverse event it will be evaluated against. General pharmacology is written first, and only paired with `ground_truth.json` afterward.
- **Why**: Prevents data leakage and circularity. If an adverse-event-specific mechanism (e.g., "causes mitochondrial dysfunction" for hepatotoxicity) is planted directly into the MoA field, the LLM is just being handed the answer. All ChEMBL MoA text additions must adhere to this rule.

## Cache Invalidation & Schema Versioning

- **CACHE_SCHEMA_VERSION**: Set in `pharmaguard/tools/cache.py` (currently `v7`).
- **When to bump**: You MUST bump this version string whenever you change:
  1. The underlying Pydantic output schemas (`TriageReport`, `SignalStatsOutput`, etc.)
  2. Data parsing or extraction logic (e.g., how the PRR score is calculated)
  3. Curated data content (e.g., correcting an MoA string in `chembl_lookup.json`)
- **Why**: Bumping the schema version auto-invalidates old cached outputs across FAERS, PubMed, and LLM derivation without requiring a manual `rm -rf .cache`.

## Coding Style Patterns

- **Typing**: Strict type hinting is enforced throughout the codebase (Pydantic, Enum, Optional, tuple, dict[str, float], etc.).
- **Docstrings**: Plain ASCII Python docstrings without esoteric formatting. Every schema and tool method requires explicitly documented mechanics. Docstrings reflect exactly what the code does; when a rule is modified, its respective docstring is always rewritten.
- **Dependency Inversion**: Components utilize standard software engineering decoupling (e.g., passing `ToolCache` as an instantiated dependency inside `FaersLegacySource.__init__` rather than globally initializing it).

## Testing Approach

PharmaGuard maintains a comprehensive pytest suite (245 unit tests across 18 test files, all passing in ~50s).

- **Tool Mocks and Fixtures**: External HTTP requests are rigorously mocked out using monkeypatch.
- **Adversarial Edge Cases**: Tests actively target adversarial data to expose heuristic vulnerabilities (e.g., `test_adversarial_regression_avoids_or_substring`, `test_adversarial_plausibility_extraction`).
- **Scoring Inertness & CI/CD**: Gating rules, indication concordance scoring-inertness, and CI-based alternative gates are validated against automated regression suites.

### Key Test File Inventory

- `test_output_schema.py`: Tests the deterministic PRR formula (including CI-downgrade logic), the confidence weighted sum, and the exact escalation rules (including the NO_SIGNAL hard gate).
- `test_canonicalize.py`: Tests the two-stage biomedical NLP term canonicalization, brand-to-INN mapping, lay term normalization, US/UK orthographic reconciliation, and fuzzy sequence matching thresholds.
- `test_clinical_dossier.py`: Tests the ICH E2C(R2) and CIOMS VIII regulatory briefing dossier generator, confirming mathematical consistency, Evans et al. triad table rendering, and emoji-free clinical typography.
- `test_indication_concordance_inertness.py` & `test_indication_discount.py`: Verifies the scoring-inertness of indication concordance flags in production and validates the research discount factor.
- `test_disease_context.py`: Tests WHO ATC classification lookups, ChEMBL fallback hierarchies, and indication metadata resolution.
- `test_confounding.py`: Tests polypharmacy confounding assessment, co-prescription extraction, and signal discounting logic.
- `test_signal_source.py`: Tests `SignalStats` null contract (zero-report pairs), query normalization, and mock source behaviours.
- `test_chembl_tool.py`: Tests static ChEMBL lookup, curated plausibility retrieval, and LLM-derived plausibility fallbacks.
- `test_pubmed_tool.py`: Tests E-utilities query generation, rubric grading logic, and adversarial text handling.
- `test_cache.py`: Tests cache key construction (including deterministic hashing and schema version inclusion) and hit/miss behavior.
- `test_agent_parsers.py`: Tests the agent's ability to extract structured JSON/Enums from raw LLM output.
- `test_stratified_evaluation.py` & `test_source_ablation.py`: Tests ATC therapeutic area stratification and multi-source ablation metrics.
- `test_stability_repeated_runs.py` & `test_reproducibility_manifest.py`: Tests stochastic run stability and automated artifact provenance indexing.

