"""
verify_react_agreement.py - Post-hoc read-only audit script for ReAct agent recommendations.

This script audits the alignment between the ReAct agent's free-text synthesized
recommendation (extracted from triage.agent_reasoning_trace[0]) and the official,
deterministically calculated triage.escalation field across all 15 benchmark pairs.

Per DECISIONS.md section 9 and 16, reported escalation decisions in PharmaGuard
are computed via a deterministic multi-source formula on retrieved evidence rather
than adopting unconstrained generative LLM output directly. This script quantifies
the divergence between generative synthesis and deterministic gating.

Artifact output: outputs/react_agent_agreement_report.json
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


NORMALIZATION_MAP = {
    "ESCALATE": "ESCALATE",
    "MONITOR": "MONITOR",
    "DO_NOT_ESCALATE": "DO_NOT_ESCALATE",
    "NO_ESCALATION": "DO_NOT_ESCALATE",
    "DISCARD": "DO_NOT_ESCALATE",
    "DISMISS": "DO_NOT_ESCALATE",
    "NO ACTION REQUIRED": "DO_NOT_ESCALATE",
    "NO_ACTION_REQUIRED": "DO_NOT_ESCALATE",
    "NONE": "DO_NOT_ESCALATE",
}


def clean_markdown_fences(raw_text: str) -> str:
    """Strip leading and trailing markdown code fences from LLM responses."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def extract_raw_recommendation(parsed_json: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract the raw recommendation from parsed JSON.
    Returns (raw_rec_str, error_message).
    """
    if not isinstance(parsed_json, dict):
        return None, f"Expected dict, got {type(parsed_json).__name__}"
    
    rec_val = parsed_json.get("triage_recommendation")
    if rec_val is None:
        rec_val = parsed_json.get("recommendation") or parsed_json.get("status")
        if rec_val is None:
            return None, "Missing 'triage_recommendation' key in JSON"

    if isinstance(rec_val, str):
        return rec_val.strip(), None
    elif isinstance(rec_val, dict):
        status = rec_val.get("status") or rec_val.get("recommendation")
        if status is not None:
            return str(status).strip(), None
        return json.dumps(rec_val), None
    else:
        return str(rec_val).strip(), None


def normalize_recommendation(raw_rec: str) -> str:
    """Normalize free-text recommendation string to canonical categories."""
    if not raw_rec:
        return "UNMAPPED:EMPTY"
    
    clean_key = raw_rec.strip().upper().replace("-", "_")
    if clean_key in NORMALIZATION_MAP:
        return NORMALIZATION_MAP[clean_key]
    
    alt_key = re.sub(r"\s+", "_", clean_key)
    if alt_key in NORMALIZATION_MAP:
        return NORMALIZATION_MAP[alt_key]

    return f"UNMAPPED:{raw_rec}"


def audit_react_agreement() -> Dict[str, Any]:
    """Run read-only audit comparing agent stated recommendation to reported escalation."""
    root_dir = Path(__file__).resolve().parents[1]
    gt_path = root_dir / "pharmaguard" / "data" / "ground_truth.json"
    react_dir = root_dir / "outputs" / "react_agent"
    fixed_dir = root_dir / "outputs"

    if not gt_path.exists():
        print(f"Error: Ground truth file not found at {gt_path}", file=sys.stderr)
        sys.exit(1)

    with open(gt_path, "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    pairs = gt_data.get("pairs", [])
    results: List[Dict[str, Any]] = []

    matches = 0
    mismatches = 0
    parse_fails = 0
    unmapped = 0

    print("| drug_event | agent_stated | reported_escalation | agreement |")
    print("| :--- | :--- | :--- | :--- |")

    for i, p in enumerate(pairs):
        drug = p["drug_canonical"]
        event = p["event_meddra_pt"]
        pair_id = f"{drug}::{event}"
        run_id = f"eval-run-{i}-{drug.replace(' ', '')}-{event.replace(' ', '')}"

        react_file = react_dir / f"{run_id}_report.json"
        fixed_file = fixed_dir / f"{run_id}_report.json"

        if not react_file.exists():
            print(f"| {pair_id} | MISSING_FILE | UNKNOWN | PARSE_FAIL |")
            parse_fails += 1
            results.append({
                "pair_index": i + 1,
                "drug": drug,
                "event": event,
                "drug_event": pair_id,
                "agent_stated_raw": None,
                "agent_stated_normalized": "PARSE_FAIL",
                "reported_escalation": None,
                "fixed_pipeline_escalation": None,
                "agreement": "PARSE_FAIL",
                "error": f"File {react_file.name} does not exist"
            })
            continue

        with open(react_file, "r", encoding="utf-8") as rf:
            react_data = json.load(rf)

        fixed_escalation = None
        if fixed_file.exists():
            with open(fixed_file, "r", encoding="utf-8") as ff:
                fixed_data = json.load(ff)
                fixed_escalation = fixed_data.get("triage", {}).get("escalation")

        reported_escalation = react_data.get("triage", {}).get("escalation")
        traces = react_data.get("triage", {}).get("agent_reasoning_trace", [])

        raw_trace = traces[0] if traces else ""
        cleaned_json_str = clean_markdown_fences(raw_trace)

        raw_rec: Optional[str] = None
        norm_rec: str = "PARSE_FAIL"
        agreement: str = "PARSE_FAIL"
        err_msg: Optional[str] = None

        try:
            parsed_json = json.loads(cleaned_json_str)
            extracted_val, ext_err = extract_raw_recommendation(parsed_json)
            if ext_err:
                err_msg = ext_err
                norm_rec = "PARSE_FAIL"
                agreement = "PARSE_FAIL"
                parse_fails += 1
            else:
                raw_rec = extracted_val
                norm_rec = normalize_recommendation(extracted_val or "")
                if norm_rec.startswith("UNMAPPED:"):
                    agreement = "UNMAPPED"
                    unmapped += 1
                elif norm_rec == reported_escalation:
                    agreement = "MATCH"
                    matches += 1
                else:
                    agreement = "MISMATCH"
                    mismatches += 1
        except Exception as e:
            err_msg = str(e)
            norm_rec = "PARSE_FAIL"
            agreement = "PARSE_FAIL"
            parse_fails += 1

        print(f"| {pair_id} | {norm_rec} | {reported_escalation} | {agreement} |")

        results.append({
            "pair_index": i + 1,
            "drug": drug,
            "event": event,
            "drug_event": pair_id,
            "agent_stated_raw": raw_rec,
            "agent_stated_normalized": norm_rec,
            "reported_escalation": reported_escalation,
            "fixed_pipeline_escalation": fixed_escalation,
            "agreement": agreement,
            "error": err_msg
        })

    total_pairs = len(pairs)
    pct = (matches / total_pairs * 100.0) if total_pairs > 0 else 0.0

    print()
    print(f"Agreement: {matches}/{total_pairs} ({pct:.1f}%)")

    report_payload = {
        "metadata": {
            "description": "Post-hoc audit comparing ReAct agent raw stated recommendations against deterministically reported escalations",
            "total_pairs": total_pairs,
            "matches": matches,
            "mismatches": mismatches,
            "parse_fails": parse_fails,
            "unmapped": unmapped,
            "agreement_rate_pct": round(pct, 2)
        },
        "pairs": results
    }

    out_file = root_dir / "outputs" / "react_agent_agreement_report.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as out_f:
        json.dump(report_payload, out_f, indent=2)

    return report_payload


if __name__ == "__main__":
    audit_react_agreement()
