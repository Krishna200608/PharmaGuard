"""
Fixed Pipeline Orchestrator - Sprint 2 Fallback Implementation.
Runs a strict, deterministic sequence: Faers -> Chembl -> PubMed.
"""
import logging
from datetime import datetime, timezone
from typing import Any
from pathlib import Path

from pharmaguard.utils.config_loader import load_config
from pharmaguard.utils.prompt_loader import PromptLoader
from pharmaguard.agent.transcript_logger import TranscriptLogger
from pharmaguard.tools.cache import ToolCache
from pharmaguard.tools.signal_source import FaersLegacySource
from pharmaguard.tools.chembl_tool import ChemblTool
from pharmaguard.tools.pubmed_tool import PubMedTool
from pharmaguard.agent.output_schema import (
    TriageReport, TriageOutput, SignalStatsOutput, MechanismOutput, LiteratureOutput,
    compute_prr_score, compute_confidence, derive_escalation, SignalStrength, EvidenceGrade, PlausibilityLevel, EscalationDecision, PlausibilitySource
)

logger = logging.getLogger(__name__)

class FixedPipelineAgent:
    def __init__(self, run_id: str, cache_dir: str = ".cache/pharmaguard"):
        self.run_id = run_id
        self.config = load_config()
        self.cache = ToolCache(cache_dir=Path(cache_dir)) if self.config.cache.enabled else None
        self.prompt_loader = PromptLoader()
        self.tlog = TranscriptLogger(run_id=run_id)
        
        # In fixed pipeline we can either use the exact same LLM fn or mock it 
        # based on config. We assume we still want to use LLM for PubMed grading.
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import SystemMessage, HumanMessage
        import json
        
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.0)
        
        def pubmed_llm_fn(abstracts: list[str], pmids: list[str], rubric: str):
            sys_msg = SystemMessage(content=rubric)
            user_msg = HumanMessage(content=f"Abstracts:\n{json.dumps(abstracts)}\nPMIDs:\n{json.dumps(pmids)}")
            resp = self.llm.invoke([sys_msg, user_msg])
            if "Grade: A" in resp.content or "GRADE A" in resp.content.upper(): grade = "A"
            elif "Grade: B" in resp.content or "GRADE B" in resp.content.upper(): grade = "B"
            else: grade = "C"
            return grade, pmids, resp.content
            
        def chembl_llm_fn(moa: str, event: str):
            prompt = f"Given MoA: {moa}, how plausible is {event}? Return HIGH, MODERATE, or LOW."
            resp = self.llm.invoke([HumanMessage(content=prompt)])
            if "HIGH" in resp.content.upper(): return PlausibilityLevel.HIGH
            if "MODERATE" in resp.content.upper(): return PlausibilityLevel.MODERATE
            return PlausibilityLevel.LOW

        self.faers = FaersLegacySource(cache=self.cache)
        self.chembl = ChemblTool(
            cache=self.cache,
            prompts_version=self.prompt_loader.version,
            force_agent_derivation=(self.config.plausibility.source == "force_agent"),
            llm_inference_fn=chembl_llm_fn
        )
        self.pubmed = PubMedTool(
            cache=self.cache,
            prompt_loader=self.prompt_loader,
            llm_inference_fn=pubmed_llm_fn
        )

    def run(self, drug: str, event: str) -> TriageReport:
        self.tlog.log_thought("Starting Fixed Pipeline. Step 1: FAERS")
        
        # 1. FAERS
        self.tlog.log_action("faers_signal_tool", {"drug": drug, "event": event})
        stats = self.faers.get_signal_stats(drug, event)
        ss_dict = stats.__dict__.copy()
        if hasattr(ss_dict.get("data_pulled_at"), "isoformat"):
            ss_dict["data_pulled_at"] = ss_dict["data_pulled_at"].isoformat()
        self.tlog.log_observation("faers_signal_tool", ss_dict, cache_hit=False)

        # 2. ChEMBL
        self.tlog.log_thought("Step 2: ChEMBL")
        self.tlog.log_action("chembl_mechanism_tool", {"drug": drug, "event": event})
        plaus = self.chembl.get_plausibility(drug, event)
        entry = self.chembl.get_drug_entry(drug)
        m_dict = {
            "chembl_id": entry.chembl_id if entry else None,
            "moa": entry.mechanism_of_action if entry else None,
            "level": plaus.level.value,
            "score": plaus.score,
            "source": plaus.plausibility_source,
            "rationale": plaus.rationale
        }
        if plaus.curated_reference:
            m_dict["curated_reference"] = plaus.curated_reference.value
            m_dict["agreement"] = plaus.agreement
        self.tlog.log_observation("chembl_mechanism_tool", m_dict, cache_hit=False)

        # 3. PubMed
        self.tlog.log_thought("Step 3: PubMed")
        self.tlog.log_action("pubmed_evidence_tool", {"drug": drug, "event": event})
        res = self.pubmed.search_and_grade(drug, event)
        l_dict = {
            "query": res.query,
            "abstracts_retrieved": res.abstracts_retrieved,
            "grade": res.evidence_grade,
            "supporting_pmids": res.supporting_pmids,
            "summary": res.evidence_summary
        }
        self.tlog.log_observation("pubmed_evidence_tool", l_dict, cache_hit=False)

        self.tlog.log_thought("Synthesizing Final Report")
        
        # Build final report
        rc = ss_dict.get("report_count", 0)
        prr = ss_dict.get("prr")
        prr_lci = ss_dict.get("prr_lower_ci")
        prr_score, ss_label, ci_downgraded = compute_prr_score(rc, prr, prr_lci)
        
        s_out = SignalStatsOutput(
            prr=prr,
            ror=ss_dict.get("ror"),
            prr_lower_ci=prr_lci,
            ror_lower_ci=ss_dict.get("ror_lower_ci"),
            report_count=rc,
            source_endpoint=ss_dict.get("source_endpoint", "unknown"),
            data_pulled_at=datetime.fromisoformat(ss_dict["data_pulled_at"]) if "data_pulled_at" in ss_dict else datetime.now(timezone.utc),
            null_reason=ss_dict.get("null_reason"),
            prr_score=prr_score,
            prr_score_label=ss_label,
            ci_downgraded=ci_downgraded
        )
        
        plaus_level = m_dict.get("level", PlausibilityLevel.UNKNOWN)
        m_out = MechanismOutput(
            chembl_id=m_dict.get("chembl_id"),
            moa=m_dict.get("moa"),
            biological_plausibility=PlausibilityLevel(plaus_level) if plaus_level else PlausibilityLevel.UNKNOWN,
            plausibility_score=m_dict.get("score", 0.0),
            plausibility_source=PlausibilitySource(m_dict.get("source", "unknown")),
            plausibility_rationale=m_dict.get("rationale", ""),
            curated_reference=PlausibilityLevel(m_dict["curated_reference"]) if m_dict.get("curated_reference") else None,
            plausibility_agreement=m_dict.get("agreement")
        )
        
        eg_str = l_dict.get("grade", "C")
        l_out = LiteratureOutput(
            pubmed_query=l_dict.get("query", ""),
            abstracts_retrieved=l_dict.get("abstracts_retrieved", 0),
            evidence_grade=EvidenceGrade(eg_str) if eg_str else EvidenceGrade.C,
            grade_score=1.0 if eg_str == "A" else (0.5 if eg_str == "B" else 0.0),
            supporting_pmids=l_dict.get("supporting_pmids", []),
            evidence_summary=l_dict.get("summary", "")
        )
        
        conf = compute_confidence(prr_score, eg_str, plaus_level)
        esc = derive_escalation(conf, ss_label)
        
        reasoning = ["Determined using fixed deterministic pipeline: FAERS -> ChEMBL -> PubMed"]
        
        t_out = TriageOutput(
            signal_strength=ss_label,
            evidence_grade=EvidenceGrade(eg_str),
            escalation=esc,
            confidence=conf,
            prompts_version=self.prompt_loader.version,
            agent_reasoning_trace=reasoning
        )
        
        report = TriageReport(
            run_id=self.run_id,
            prompts_version=self.prompt_loader.version,
            drug=drug,
            event=event,
            signal_stats=s_out,
            mechanism=m_out,
            literature=l_out,
            triage=t_out
        )
        
        self.tlog.log_final_answer("\n".join(reasoning))
        self.tlog.finalize()
        
        return report
