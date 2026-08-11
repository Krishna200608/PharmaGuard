Last updated: 2026-08-10 | Sprint: Sprint 1 (Transitioning to Sprint 2) | Updated by: Antigravity

# ARCHITECTURE

## System Design and Agent Flow
- **Primary Flow**: LangGraph ReAct orchestration loop (to be implemented in Sprint 2).
- **Fallback Flow**: Fixed-order pipeline (\OpenFDA\ ? \ChEMBL\ ? \PubMed\ ? synthesize). Configurable via \config.yaml\ (\gent.mode\). No agent discretion over order in fallback mode.

## Key Components and Data Flow
- **Input**: Drug and Event strings.
- **Tools**:
  - \FaersLegacySource\: Calls OpenFDA legacy \/drug/event.json\ endpoint. Computes PRR, ROR, and lower CIs (Woolf log-CI). 
  - \ChemblTool\: Pre-resolved static metadata lookup. Evaluates plausibility (human-curated or fallback agent-derived).
  - \PubMedTool\: E-utilities search and XML abstract extraction. Grades evidence using an LLM evaluated against a text rubric (\prompts/evidence_grading_rubric.txt\).
- **Synthesis & Output**: Output is marshalled into a strict Pydantic model \TriageReport\. Used by the evaluation harness.

## Confidence Formula and Escalation
The confidence formula is completely deterministic:
\confidence = 0.40 × PRR_score + 0.40 × grade_score + 0.20 × plausibility_score\

**Escalation Logic Thresholds**:
1. \NO_SIGNAL\ (FAERS report_count == 0 or PRR < 2.0 after CI) ? \DO_NOT_ESCALATE\ (Hard Gate).
2. \confidence >= 0.70\ AND \signal_strength\ is STRONG/MODERATE ? \ESCALATE\.
3. \confidence >= 0.35\ ? \MONITOR\.
4. Otherwise ? \DO_NOT_ESCALATE\.

## Tech Stack
Verified from \equirements.txt\:
- \langchain>=0.2.0\, \langgraph>=0.1.0\, \langchain-google-genai>=1.0.0\
- \pydantic>=2.0.0\ (schema validation)
- \diskcache>=5.6.0\ (persistent rate limit shielding)
- \equests>=2.31.0\ (HTTP queries)
- \pytest>=8.0.0\ (Testing)
- \pandas>=2.0.0\, \matplotlib>=3.8.0\ (Evaluation)

## Caching and Rate-Limit Strategy
All external calls are fronted by \ToolCache\ (via \diskcache\). 
- \FaersLegacySource\ routes all paths through a centralized \_finalize()\ method to ensure cache writing is never skipped.
- \PubMedTool\ explicitly caches the semantic LLM grading independently of the abstract fetching, uniquely hashing against the rubric version.
