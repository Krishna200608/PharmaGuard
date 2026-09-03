"""
ReAct Orchestrator - Sprint 2 LangGraph implementation.
"""
import os
import json
import logging
from typing import TypedDict, Annotated, Sequence, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END


from pharmaguard.utils.prompt_loader import PromptLoader
from pharmaguard.agent.transcript_logger import TranscriptLogger
from pharmaguard.tools.signal_source import FaersLegacySource
from pharmaguard.tools.chembl_tool import ChemblTool
from pharmaguard.tools.pubmed_tool import PubMedTool
from pharmaguard.tools.cache import ToolCache
from pharmaguard.agent.output_schema import (
    TriageReport, TriageOutput, SignalStatsOutput, MechanismOutput, LiteratureOutput,
    SignalStrength, EscalationDecision, PlausibilityLevel,
    compute_prr_score, compute_prr_score_ci_based, compute_confidence, derive_escalation, EvidenceGrade, PlausibilitySource,
    LeakageCritique

)
from pharmaguard.utils.config_loader import load_config

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from typing import Literal

class GradeOutput(BaseModel):
    grade: Literal["A", "B", "C"] = Field(description="The evidence grade based on the rubric. Must be A, B, or C.")
    explanation: str = Field(description="Explanation for why this grade was assigned.")

class PlausibilityLLMOutput(BaseModel):
    plausibility: Literal["HIGH", "MODERATE", "LOW"] = Field(description="The plausibility level. Must be HIGH, MODERATE, or LOW.")
    explanation: str = Field(description="Explanation for why this plausibility was assigned.")

def extract_text(content) -> str:
    if isinstance(content, str): return content
    if isinstance(content, list): return " ".join([part.get("text", "") for part in content if isinstance(part, dict) and "text" in part])
    return str(content)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    run_id: str
    drug: str
    event: str
    signal_stats: Optional[Any]
    mechanism: Optional[Any]
    literature: Optional[Any]
    agent_reasoning_trace: list[str]

class PharmaGuardAgent:
    def __init__(self, run_id: str, cache_dir: str = ".cache/pharmaguard"):
        self.run_id = run_id
        self.config = load_config()
        self.cache = ToolCache(cache_dir=Path(cache_dir)) if self.config.cache.enabled else None
        self.prompt_loader = PromptLoader()
        self.tlog = TranscriptLogger(run_id=run_id)
        
        self.llm = ChatGoogleGenerativeAI(model=self.config.agent.llm_model, temperature=0.0)
        
        # We need LLM fns for the tools
        def pubmed_llm_fn(abstracts: list[str], pmids: list[str], rubric: str):
            sys_msg = SystemMessage(content=rubric)
            user_msg = HumanMessage(content=f"Abstracts:\n{json.dumps(abstracts)}\nPMIDs:\n{json.dumps(pmids)}")
            structured_llm = self.llm.with_structured_output(GradeOutput)
            result = structured_llm.invoke([sys_msg, user_msg])
            text_content = f"Final Grade: {result.grade}\nExplanation: {result.explanation}"
            return result.grade, pmids, text_content
            
        def chembl_llm_fn(moa: str, event: str):
            prompt = f"Given MoA: {moa}, how plausible is {event}? Explain first, then assign HIGH, MODERATE, or LOW."
            structured_llm = self.llm.with_structured_output(PlausibilityLLMOutput)
            result = structured_llm.invoke([HumanMessage(content=prompt)])

            if result.plausibility == "HIGH": level = PlausibilityLevel.HIGH
            elif result.plausibility == "MODERATE": level = PlausibilityLevel.MODERATE
            else: level = PlausibilityLevel.LOW
            return level, result.explanation

        self.faers = FaersLegacySource(cache=self.cache)

        critic_cfg = getattr(self.config.plausibility, "leakage_critic", None)
        critic_enabled = getattr(critic_cfg, "enabled", False) if critic_cfg else False
        critic_action = getattr(critic_cfg, "action", "flag") if critic_cfg else "flag"

        def critic_llm_fn(rationale: str):
            critic_prompt = self.prompt_loader.get("leakage_critic").replace("{rationale}", rationale)
            structured_llm = self.llm.with_structured_output(LeakageCritique)
            return structured_llm.invoke([HumanMessage(content=critic_prompt)])

        self.chembl = ChemblTool(
            cache=self.cache,
            prompts_version=self.prompt_loader.version,
            force_agent_derivation=(self.config.plausibility.source == "force_agent"),
            llm_inference_fn=chembl_llm_fn,
            leakage_critic_enabled=critic_enabled,
            leakage_critic_action=critic_action,
            critic_llm_fn=critic_llm_fn if critic_enabled else None,
        )
        self.pubmed = PubMedTool(
            cache=self.cache,
            prompt_loader=self.prompt_loader,
            llm_inference_fn=pubmed_llm_fn
        )
        
        self.tools = [
            self._faers_tool(),
            self._chembl_tool(),
            self._pubmed_tool()
        ]
        
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
    def _faers_tool(self):
        @tool("faers_signal_tool")
        def faers_signal_tool(drug: str, event: str) -> dict:
            """Fetch FAERS signal statistics."""
            self.tlog.log_action("faers_signal_tool", {"drug": drug, "event": event})
            stats = self.faers.get_signal_stats(drug, event)
            d = stats.__dict__.copy()
            if hasattr(d["data_pulled_at"], "isoformat"):
                d["data_pulled_at"] = d["data_pulled_at"].isoformat()
            self.tlog.log_observation("faers_signal_tool", d, cache_hit=False) # Simplified
            return d
        return faers_signal_tool

    def _chembl_tool(self):
        @tool("chembl_mechanism_tool")
        def chembl_mechanism_tool(drug: str, event: str) -> dict:
            """Fetch ChEMBL mechanism and biological plausibility."""
            self.tlog.log_action("chembl_mechanism_tool", {"drug": drug, "event": event})
            plaus = self.chembl.get_plausibility(drug, event)
            entry = self.chembl.get_drug_entry(drug)
            d = {
                "chembl_id": getattr(plaus, "chembl_id", None),
                "moa": getattr(plaus, "moa", None),
                "level": getattr(plaus.level, "value", plaus.level),
                "score": plaus.score,
                "source": plaus.plausibility_source,
                "rationale": plaus.rationale,
                "leak_detected": getattr(plaus, "leak_detected", None),
                "leak_phrases": getattr(plaus, "leak_phrases", None),
            }
            if plaus.curated_reference:
                d["curated_reference"] = getattr(plaus.curated_reference, "value", plaus.curated_reference)
                d["agreement"] = plaus.agreement
            self.tlog.log_observation("chembl_mechanism_tool", d, cache_hit=False)
            return d
        return chembl_mechanism_tool

    def _pubmed_tool(self):
        @tool("pubmed_evidence_tool")
        def pubmed_evidence_tool(drug: str, event: str) -> dict:
            """Fetch PubMed evidence grading."""
            self.tlog.log_action("pubmed_evidence_tool", {"drug": drug, "event": event})
            res = self.pubmed.search_and_grade(drug, event)
            d = {
                "query": res.query,
                "abstracts_retrieved": res.abstracts_retrieved,
                "grade": res.evidence_grade,
                "supporting_pmids": res.supporting_pmids,
                "summary": res.evidence_summary
            }
            self.tlog.log_observation("pubmed_evidence_tool", d, cache_hit=False)
            return d
        return pubmed_evidence_tool

    def build_graph(self) -> StateGraph:
        graph = StateGraph(AgentState)
        
        def agent_node(state: AgentState):
            sys_prompt = self.prompt_loader.get("react_system")
            format_prompt = self.prompt_loader.get("react_tool_call_format")
            messages = [SystemMessage(content=f"{sys_prompt}\n\n{format_prompt}")] + list(state["messages"])
            resp = self.llm_with_tools.invoke(messages)
            
            # Log thought if text is present
            text_content = extract_text(resp.content)
            if text_content:
                self.tlog.log_thought(text_content)
                state["agent_reasoning_trace"].append(text_content)
            
            return {"messages": [resp], "agent_reasoning_trace": state["agent_reasoning_trace"]}

        def tool_node(state: AgentState):
            last_msg = state["messages"][-1]
            tool_responses = []
            updates = {}
            for tool_call in last_msg.tool_calls:
                name = tool_call["name"]
                args = tool_call["args"]
                tool_instance = next(t for t in self.tools if t.name == name)
                res = tool_instance.invoke(args)
                
                # update state
                if name == "faers_signal_tool":
                    updates["signal_stats"] = res
                elif name == "chembl_mechanism_tool":
                    updates["mechanism"] = res
                elif name == "pubmed_evidence_tool":
                    updates["literature"] = res
                    
                tool_responses.append(ToolMessage(content=json.dumps(res), tool_call_id=tool_call["id"]))
            return {"messages": tool_responses, **updates}

        def should_continue(state: AgentState):
            last_msg = state["messages"][-1]
            if getattr(last_msg, "tool_calls", []):
                return "tools"
            return END

        graph.add_node("agent", agent_node)
        graph.add_node("tools", tool_node)
        
        graph.set_entry_point("agent")
        graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
        graph.add_edge("tools", "agent")
        
        return graph.compile()

    def _build_error_fallback_report(self, drug: str, event: str, stage: str, error_msg: str) -> TriageReport:
        """
        Construct a graceful fallback TriageReport reusing the standard null_reason
        contract when an unexpected orchestrator exception occurs during ReAct execution.
        """
        now = datetime.now(timezone.utc)
        s_out = SignalStatsOutput(
            prr=None,
            ror=None,
            prr_lower_ci=None,
            ror_lower_ci=None,
            report_count=0,
            source_endpoint="react_error_fallback",
            data_pulled_at=now,
            null_reason=f"ReAct agent error at stage '{stage}': {error_msg}",
            prr_score=0.0,
            prr_score_label=SignalStrength.NO_SIGNAL,
            ci_downgraded=False,
        )
        m_out = MechanismOutput(
            chembl_id=None,
            moa=None,
            biological_plausibility=PlausibilityLevel.UNKNOWN,
            plausibility_score=0.0,
            plausibility_source=PlausibilitySource.UNKNOWN,
            plausibility_rationale=f"ReAct agent error at stage '{stage}': {error_msg}",
        )
        l_out = LiteratureOutput(
            pubmed_query="",
            abstracts_retrieved=0,
            evidence_grade=EvidenceGrade.C,
            grade_score=0.0,
            supporting_pmids=[],
            evidence_summary=f"ReAct agent error at stage '{stage}': {error_msg}",
        )
        t_out = TriageOutput(
            signal_strength=SignalStrength.NO_SIGNAL,
            evidence_grade=EvidenceGrade.C,
            escalation=EscalationDecision.DO_NOT_ESCALATE,
            confidence=0.0,
            prompts_version=self.prompt_loader.version,
            agent_reasoning_trace=[f"ERROR: PharmaGuardAgent (ReAct) failed at stage '{stage}' for {drug}::{event}: {error_msg}"],
        )
        return TriageReport(
            run_id=self.run_id,
            prompts_version=self.prompt_loader.version,
            drug=drug,
            event=event,
            signal_stats=s_out,
            mechanism=m_out,
            literature=l_out,
            triage=t_out,
        )

    def run(self, drug: str, event: str) -> TriageReport:
        stage = "graph_execution"
        try:
            graph = self.build_graph()
            initial_state = {
                "messages": [HumanMessage(content=f"Evaluate drug: {drug}, event: {event}")],
                "run_id": self.run_id,
                "drug": drug,
                "event": event,
                "signal_stats": None,
                "mechanism": None,
                "literature": None,
                "agent_reasoning_trace": []
            }
            
            final_state = graph.invoke(initial_state, {"recursion_limit": 15})
            
            # After tool calling, we synthesize
            stage = "synthesis"
            synth_prompt = self.prompt_loader.get("synthesis")
            messages = list(final_state["messages"]) + [HumanMessage(content=synth_prompt)]
            synth_resp = self.llm.invoke(messages)
            text_content = extract_text(synth_resp.content)
            self.tlog.log_final_answer(text_content)
            final_state["agent_reasoning_trace"].append(text_content)
            
            self.tlog.finalize()
            
            stage = "report_assembly"
            return self._assemble_report(final_state)
        except Exception as exc:
            logger.error(
                "Unexpected failure in PharmaGuardAgent (ReAct) at stage '%s' for pair %s::%s: %s",
                stage, drug, event, exc, exc_info=True
            )
            try:
                self.tlog.log_thought(f"ERROR: PharmaGuardAgent (ReAct) failed at stage '{stage}' for {drug}::{event}: {exc}")
                self.tlog.log_final_answer(f"Failed at stage '{stage}': {exc}")
                self.tlog.finalize()
            except Exception as log_exc:
                logger.warning("Failed to finalize transcript logger for %s::%s: %s", drug, event, log_exc)
            
            return self._build_error_fallback_report(drug, event, stage, str(exc))
        
    def _assemble_report(self, state: AgentState) -> TriageReport:
        # 1. Parse Faers
        ss_dict = state.get("signal_stats") or {}
        rc = ss_dict.get("report_count", 0)
        prr = ss_dict.get("prr")
        prr_lci = ss_dict.get("prr_lower_ci")
        sig_cfg = getattr(self.config, "signal_detection", None)
        if sig_cfg and getattr(sig_cfg, "ci_based_gate", None) and sig_cfg.ci_based_gate.enabled:
            prr_score, ss_label, ci_downgraded = compute_prr_score_ci_based(rc, prr, prr_lci)
        else:
            prr_score, ss_label, ci_downgraded = compute_prr_score(rc, prr, prr_lci)


        # 2. Parse Chembl (pre-extract for confounding check)
        m_dict = state.get("mechanism") or {}
        
        # Confounding assessment & discounting (if enabled)
        discount_factor = 1.0
        confounding_res = None
        confounding_cfg = getattr(self.config, "confounding", None)
        if confounding_cfg and confounding_cfg.enabled and prr_score > 0:
            from pharmaguard.tools.confounding import ConfoundingTool
            c_tool = ConfoundingTool(llm=self.llm, prompt_loader=self.prompt_loader)
            confounding_res = c_tool.assess(state["drug"], state["event"], m_dict.get("moa") or "", rc, prr)
            discount_factor = confounding_res.discount_factor

        adjusted_prr_score = round(prr_score * discount_factor, 4)

        data_pulled = ss_dict.get("data_pulled_at")
        if data_pulled and hasattr(data_pulled, "isoformat"):
            pulled_dt = data_pulled
        elif data_pulled and isinstance(data_pulled, str):
            pulled_dt = datetime.fromisoformat(data_pulled)
        else:
            pulled_dt = datetime.now(timezone.utc)

        s_out = SignalStatsOutput(
            prr=prr,
            ror=ss_dict.get("ror"),
            prr_lower_ci=prr_lci,
            ror_lower_ci=ss_dict.get("ror_lower_ci"),
            report_count=rc,
            source_endpoint=ss_dict.get("source_endpoint", "unknown"),
            data_pulled_at=pulled_dt,
            null_reason=ss_dict.get("null_reason"),
            prr_score=adjusted_prr_score,
            prr_score_label=ss_label,
            ci_downgraded=ci_downgraded,
            discount_factor=discount_factor if (confounding_cfg and confounding_cfg.enabled) else None,
            is_confounded=confounding_res.is_confounded if confounding_res else None,
            confounding_drugs=confounding_res.confounding_drugs if confounding_res else None,
            confounding_explanation=confounding_res.confounding_explanation if confounding_res else None,
        )
        
        plaus = m_dict.get("level", PlausibilityLevel.UNKNOWN)
        m_out = MechanismOutput(
            chembl_id=m_dict.get("chembl_id"),
            moa=m_dict.get("moa"),
            biological_plausibility=PlausibilityLevel(plaus) if plaus else PlausibilityLevel.UNKNOWN,
            plausibility_score=m_dict.get("score", 0.0),
            plausibility_source=PlausibilitySource(m_dict.get("source", "unknown")),
            plausibility_rationale=m_dict.get("rationale", ""),
            curated_reference=PlausibilityLevel(m_dict["curated_reference"]) if m_dict.get("curated_reference") else None,
            plausibility_agreement=m_dict.get("agreement"),
            leak_detected=m_dict.get("leak_detected"),
            leak_phrases=m_dict.get("leak_phrases"),
        )
        
        # 3. Parse PubMed
        l_dict = state.get("literature") or {}
        eg_str = l_dict.get("grade", "C")
        l_out = LiteratureOutput(
            pubmed_query=l_dict.get("query", ""),
            abstracts_retrieved=l_dict.get("abstracts_retrieved", 0),
            evidence_grade=EvidenceGrade(eg_str) if eg_str else EvidenceGrade.C,
            grade_score=1.0 if eg_str == "A" else (0.5 if eg_str == "B" else 0.0),
            supporting_pmids=l_dict.get("supporting_pmids", []),
            evidence_summary=l_dict.get("summary", "")
        )
        
        # 4. Triage Final
        conf = compute_confidence(adjusted_prr_score, eg_str, plaus)
        esc = derive_escalation(conf, ss_label)
        
        t_out = TriageOutput(
            signal_strength=ss_label,
            evidence_grade=EvidenceGrade(eg_str),
            escalation=esc,
            confidence=conf,
            prompts_version=self.prompt_loader.version,
            agent_reasoning_trace=state.get("agent_reasoning_trace", [])
        )
        
        return TriageReport(
            run_id=self.run_id,
            prompts_version=self.prompt_loader.version,
            drug=state["drug"],
            event=state["event"],
            signal_stats=s_out,
            mechanism=m_out,
            literature=l_out,
            triage=t_out
        )