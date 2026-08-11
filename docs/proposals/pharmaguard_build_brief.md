<role>
You are acting as technical lead and pair programmer inside this Antigravity workspace, building the PharmaGuard capstone project. You have file system access to this repo — read problem_statement_report.md, mdt_dataset_report.md, and any existing proposal docs directly for background before writing any code. This message is the authoritative build brief. Where it conflicts with older docs (e.g. "PharmAgent," "Option 2," "Pick A" naming), this message wins — the project's canonical name is PharmaGuard, and this is the confirmed final direction.
</role>

<decision>
Direction is CONFIRMED and FINAL: PharmaGuard — a ReAct-based pharmacovigilance triage agent combining OpenFDA/FAERS signal detection, ChEMBL mechanism-of-action lookup, and PubMed evidence grading. Do not ask which direction to build or present alternatives — that decision is closed. Do not start scaffolding files yet either — first produce a plan per <process> below and wait for my explicit go-ahead.
</decision>

<hard_constraints>
- Free-tier only: Gemini Flash API. Treat rate limits as tight (roughly 10-15 RPM, daily cap dynamic and lower than it looks on paper) — build caching and exponential backoff from day one, not as a later fix.
- Public APIs only: openFDA legacy drug/event endpoint, ChEMBL REST API, PubMed E-utilities (I will register an NCBI API key).
- No GPU/Colab dependency needed for this architecture — do not introduce one.
- Team: 3 people. I (Krishna) own ~70-80% of core technical work. Two teammates will own clearly separated modules: (1) ground-truth data curation + single-shot baseline, (2) evaluation harness + documentation. Structure the codebase so those modules have a genuinely separable interface I can hand off — not deeply coupled to agent internals.
- Timeline: 16-week semester. Mid-sem (~week 8-9) needs a working end-to-end demo on 8-10 drug-event pairs. End-sem (~week 15-16) needs full evaluation on 15-20 verified pairs (not 25) with baseline comparison. Build in that priority order — a working narrower pipeline beats a broader half-working one at every checkpoint.
</hard_constraints>

<architecture_requirements>
1. OpenFDA/FAERS tool: implement behind an abstracted SignalDataSource interface, not a hardcoded direct call — FAERS is mid-migration to the AEMS platform, and the legacy endpoint is only guaranteed compatible through end of 2026. Include PRR/ROR disproportionality calculation.
2. ChEMBL tool: pre-resolve ChEMBL IDs for our fixed drug set into a static local lookup table rather than live fuzzy name-matching. This is a deliberate reliability tradeoff, not a shortcut to fix later — do not "improve" it into dynamic resolution without asking me.
3. PubMed tool: E-utilities search + abstract fetch. I will define the evidence-grading rubric — implement it as an isolated, swappable function so I can iterate on the rubric without touching orchestration code.
4. Orchestration: build the LangGraph ReAct loop as primary, but structure the code so a fixed-order pipeline (OpenFDA → ChEMBL → PubMed → synthesize, no agent discretion over order) is a config-level fallback, not a separate rewrite. I'll decide which mode we ship for mid-sem by week 6.
5. Caching: cache every tool call by query key, on disk, from the first version. Not optional given free-tier limits.
6. Agent output: structured, versioned JSON from the start — not just human-readable text — so the evaluation module (teammate-owned) can consume it without understanding agent internals.
</architecture_requirements>

<process>
Before writing any implementation code:
1. Read the repo's existing docs and summarize your understanding of the confirmed scope back to me in a few sentences. Flag anything in this brief that conflicts with what's already in the docs.
2. Propose a file/folder structure reflecting the module separation above (core agent / data curation / evaluation harness), briefly justified.
3. Propose the exact schema for: the SignalDataSource abstraction, the static ChEMBL lookup table format, and the structured JSON output of one triage run. Short schema snippets only, not full implementations.
4. Stop and wait for my explicit confirmation before scaffolding files.

Once confirmed, build incrementally in this order: tool wrappers with unit tests (individually runnable outside the agent loop) → caching layer → ReAct orchestration → mid-sem demo path on a small pilot set. Do not start evaluation/scaling code before the mid-sem path is solid.
</process>

<checkpoints>
Flag explicitly, without waiting for me to ask, if:
- A free-tier rate limit is actually blocking dev iteration speed — don't silently route around it, surface it so we can decide on Flash vs. Flash-Lite tradeoffs together.
- ReAct tool-call reliability looks shaky once we're testing on the pilot set — this is the trigger point to discuss falling back to the fixed-pipeline mode.
- ChEMBL or PubMed responses are inconsistent enough to threaten the mid-sem demo date.
</checkpoints>

<first_response_requirement>
End your first response with your scope-understanding summary and proposed file structure — not a question about which direction to build. The direction is decided; the only open questions at this stage are implementation details.
</first_response_requirement>