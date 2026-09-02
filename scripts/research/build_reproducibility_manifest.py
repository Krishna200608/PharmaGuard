"""
scripts/research/build_reproducibility_manifest.py - Consolidated Provenance Manifest.

Scans every JSON artifact under outputs/ (frozen run reports, diagnostic probes,
evaluations, and research experiments), extracts whatever provenance fields are present,
and records explicit nulls and missing-field lists for older or partial artifacts.

Outputs:
  - outputs/research/reproducibility_manifest.json (machine-readable index)
  - outputs/research/reproducibility_manifest.md   (human-readable summary table)

Owner: Krishna Sikheriya (IIT2023139)
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pharmaguard.tools.cache import CACHE_SCHEMA_VERSION

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reproducibility_manifest")

OUTPUTS_DIR = REPO_ROOT / "outputs"
DEFAULT_JSON_OUT = OUTPUTS_DIR / "research" / "reproducibility_manifest.json"
DEFAULT_MD_OUT = OUTPUTS_DIR / "research" / "reproducibility_manifest.md"

CORE_PROVENANCE_FIELDS = [
    "git_commit_hash",
    "timestamp",
    "model_name",
    "prompts_version",
    "cache_schema_version",
    "config_snapshot",
]


def get_git_commit(repo_root: Path) -> Optional[str]:
    """Retrieve the current Git commit hash of the repository."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception as e:
        logger.warning("Failed to retrieve git commit hash: %s", e)
        return None


def classify_artifact(rel_posix: str) -> Tuple[str, str]:
    """
    Classify an artifact file into (artifact_type, broad_category).
    """
    parts = rel_posix.split("/")
    filename = parts[-1]

    # outputs/core/...
    if len(parts) >= 3 and parts[1] == "core":
        if filename.startswith("eval-run-"):
            return "production_report", "production_benchmark"
        return "core_report", "production_benchmark"

    # outputs/experiments/...
    if len(parts) >= 3 and parts[1] == "experiments":
        folder = parts[2]
        if folder == "baseline":
            return "baseline_report", "evaluation_run"
        elif folder == "ablation":
            return "ablation_report", "evaluation_run"
        elif folder == "react_agent":
            if filename in ("agreement_report.json", "react_agent_agreement_report.json"):
                return "agent_agreement_audit", "evaluation_run"
            return "react_agent_report", "evaluation_run"
        elif folder == "probe":
            return "diagnostic_probe_report", "diagnostic_probe"
        elif folder == "critic_probe":
            return "critic_probe_results", "diagnostic_probe"
        elif folder == "confounding_probe":
            if "self_probe" in filename:
                return "confounding_self_probe", "diagnostic_probe"
            return "confounding_probe_report", "diagnostic_probe"
        return "experiment_artifact", "evaluation_run"

    # outputs/research/...
    if len(parts) >= 3 and parts[1] == "research":
        if len(parts) > 3:
            res_sub = parts[2]
            if res_sub == "stability":
                if filename == "loo_analysis.json":
                    return "stability_analysis", "stability_evaluation"
                return "research_stability_experiment", "research_experiment"
            elif res_sub == "source_ablation":
                return "research_ablation_experiment", "research_experiment"
            elif res_sub == "error_taxonomy":
                return "research_taxonomy_experiment", "research_experiment"
            elif res_sub == "omop_pilot":
                return "omop_pilot_report", "research_experiment"
        if filename == "reproducibility_manifest.json":
            return "reproducibility_manifest", "meta_manifest"
        return "research_experiment", "research_experiment"

    # Legacy fallbacks
    if len(parts) == 2:  # outputs/<file>
        if filename.startswith("eval-run-"):
            return "production_report", "production_benchmark"
        elif filename in ("agreement_report.json", "react_agent_agreement_report.json"):
            return "agent_agreement_audit", "evaluation_run"
        return "root_output", "other"

    folder = parts[1]
    if folder == "baseline":
        return "baseline_report", "evaluation_run"
    elif folder == "ablation":
        return "ablation_report", "evaluation_run"
    elif folder == "react_agent":
        if filename in ("agreement_report.json", "react_agent_agreement_report.json"):
            return "agent_agreement_audit", "evaluation_run"
        return "react_agent_report", "evaluation_run"
    elif folder == "probe":
        return "diagnostic_probe_report", "diagnostic_probe"
    elif folder == "critic_probe":
        return "critic_probe_results", "diagnostic_probe"
    elif folder == "confounding_probe":
        if "self_probe" in filename:
            return "confounding_self_probe", "diagnostic_probe"
        return "confounding_probe_report", "diagnostic_probe"
    elif folder == "stability":
        return "stability_analysis", "stability_evaluation"

    return "unknown", "other"


def extract_artifact_provenance(
    file_path: Path,
    repo_root: Path,
    manifest_target: Path,
    current_commit: Optional[str],
    current_time: str,
) -> Dict[str, Any]:
    """
    Extract provenance fields from a single JSON artifact, explicitly noting missing fields.
    """
    rel_posix = file_path.relative_to(repo_root).as_posix()
    artifact_type, broad_category = classify_artifact(rel_posix)

    # Special handling for the self-indexing manifest
    if file_path == manifest_target:
        file_size = 0  # Will be written on disk
        prov_dict = {
            "experiment_id": "meta-reproducibility-manifest-r1",
            "run_id": None,
            "git_commit_hash": current_commit,
            "timestamp": current_time,
            "model_name": None,
            "prompts_version": None,
            "cache_schema_version": CACHE_SCHEMA_VERSION,
            "config_snapshot": None,
            "schema_version": "1.0",
        }
        missing = ["model_name", "prompts_version", "config_snapshot"]
        status = "PARTIAL"
        return {
            "file_path": rel_posix,
            "file_size_bytes": file_size,
            "artifact_type": artifact_type,
            "broad_category": broad_category,
            "provenance_status": status,
            "provenance": prov_dict,
            "missing_fields": missing,
            "notes": "Self-indexing metadata manifest consolidating provenance across all repository outputs.",
        }

    file_size = file_path.stat().st_size
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        prov_dict = {
            "experiment_id": None,
            "run_id": None,
            "git_commit_hash": None,
            "timestamp": None,
            "model_name": None,
            "prompts_version": None,
            "cache_schema_version": None,
            "config_snapshot": None,
            "schema_version": None,
        }
        return {
            "file_path": rel_posix,
            "file_size_bytes": file_size,
            "artifact_type": artifact_type,
            "broad_category": broad_category,
            "provenance_status": "MINIMAL",
            "provenance": prov_dict,
            "missing_fields": CORE_PROVENANCE_FIELDS,
            "notes": "Non-dictionary JSON artifact with zero top-level provenance keys.",
        }

    # Extract provenance
    exp_id = data.get("experiment_id")
    run_id = data.get("run_id")
    git_hash = data.get("git_commit_hash")

    # Timestamps can appear as timestamp, timestamp_start, or generated_at_utc
    ts = data.get("timestamp") or data.get("timestamp_start")
    if not ts and "metadata" in data and isinstance(data["metadata"], dict):
        ts = data["metadata"].get("generated_at_utc") or data["metadata"].get("timestamp")

    model_name = data.get("model_name")
    prompts_ver = data.get("prompts_version")
    cache_schema = data.get("cache_schema_version")
    config_snap = data.get("config_snapshot")
    schema_ver = data.get("schema_version")

    prov_dict = {
        "experiment_id": exp_id,
        "run_id": run_id,
        "git_commit_hash": git_hash,
        "timestamp": ts,
        "model_name": model_name,
        "prompts_version": prompts_ver,
        "cache_schema_version": cache_schema,
        "config_snapshot": config_snap,
        "schema_version": schema_ver,
    }

    # Identify missing core fields
    missing = [f for f in CORE_PROVENANCE_FIELDS if prov_dict.get(f) is None]

    if len(missing) == 0:
        status = "COMPLETE"
    elif len(missing) < len(CORE_PROVENANCE_FIELDS):
        status = "PARTIAL"
    else:
        status = "MINIMAL"

    notes = ""
    if status == "COMPLETE":
        notes = "Full provenance recorded: commit hash, model, prompts, cache schema, config snapshot."
    elif status == "PARTIAL":
        if run_id and prompts_ver:
            notes = "Frozen execution report (predates git_commit_hash / config_snapshot tracking convention)."
        else:
            notes = "Intermediate probe or summary report with partial timestamp/metadata."
    else:
        notes = "Legacy diagnostic probe with raw metrics; missing all core provenance fields."

    return {
        "file_path": rel_posix,
        "file_size_bytes": file_size,
        "artifact_type": artifact_type,
        "broad_category": broad_category,
        "provenance_status": status,
        "provenance": prov_dict,
        "missing_fields": missing,
        "notes": notes,
    }


def build_manifest(repo_root: Optional[Path] = None, json_out: Optional[Path] = None) -> Dict[str, Any]:
    """
    Build the complete queryable reproducibility manifest across all JSON files under outputs/.
    """
    if repo_root is None:
        repo_root = REPO_ROOT
    if json_out is None:
        json_out = DEFAULT_JSON_OUT

    outputs_dir = repo_root / "outputs"
    current_commit = get_git_commit(repo_root)
    current_time = datetime.now(timezone.utc).isoformat()

    # Discover all JSON files under outputs/
    existing_files = sorted(list(outputs_dir.rglob("*.json")))

    # Ensure target manifest is present in scan list if not already on disk
    file_set = set(existing_files)
    if json_out not in file_set:
        file_set.add(json_out)
    sorted_files = sorted(list(file_set), key=lambda p: p.relative_to(repo_root).as_posix())

    artifacts_index: List[Dict[str, Any]] = []
    for f in sorted_files:
        entry = extract_artifact_provenance(
            file_path=f,
            repo_root=repo_root,
            manifest_target=json_out,
            current_commit=current_commit,
            current_time=current_time,
        )
        artifacts_index.append(entry)

    # Compute summary statistics
    total_artifacts = len(artifacts_index)
    status_counts = {"COMPLETE": 0, "PARTIAL": 0, "MINIMAL": 0}
    category_counts: Dict[str, int] = {}
    type_counts: Dict[str, int] = {}
    status_by_type: Dict[str, Dict[str, int]] = {}

    for entry in artifacts_index:
        st = entry["provenance_status"]
        status_counts[st] = status_counts.get(st, 0) + 1

        bcat = entry["broad_category"]
        category_counts[bcat] = category_counts.get(bcat, 0) + 1

        atype = entry["artifact_type"]
        type_counts[atype] = type_counts.get(atype, 0) + 1

        status_by_type.setdefault(atype, {"COMPLETE": 0, "PARTIAL": 0, "MINIMAL": 0})
        status_by_type[atype][st] += 1

    payload = {
        "manifest_metadata": {
            "schema_version": "1.0",
            "generated_at_utc": current_time,
            "repository_head_commit": current_commit,
            "total_artifacts_indexed": total_artifacts,
            "active_cache_schema_version": CACHE_SCHEMA_VERSION,
            "core_provenance_fields_specification": CORE_PROVENANCE_FIELDS,
        },
        "summary_statistics": {
            "provenance_completeness": status_counts,
            "completeness_percentages": {
                st: round((cnt / total_artifacts) * 100, 2)
                for st, cnt in status_counts.items()
            },
            "by_broad_category": category_counts,
            "by_artifact_type": type_counts,
            "status_by_artifact_type": status_by_type,
        },
        "artifacts": artifacts_index,
    }

    return payload


def generate_markdown_report(manifest_data: Dict[str, Any]) -> str:
    """Generate comprehensive human-readable Markdown summary report."""
    meta = manifest_data["manifest_metadata"]
    stats = manifest_data["summary_statistics"]
    status_counts = stats["provenance_completeness"]
    pcts = stats["completeness_percentages"]

    lines = [
        "# PharmaGuard Reproducibility & Provenance Manifest",
        "",
        f"**Generated:** `{meta['generated_at_utc']}`  ",
        f"**Repository HEAD Commit:** `{meta['repository_head_commit']}`  ",
        f"**Total Artifacts Indexed:** `{meta['total_artifacts_indexed']}`  ",
        f"**Active Tool Cache Schema:** `{meta['active_cache_schema_version']}`  ",
        "",
        "---",
        "",
        "## 1. Executive Summary & Provenance Health",
        "",
        "This manifest indexes every evaluation, diagnostic probe, and research experiment artifact in the repository. "
        "Missing fields in legacy frozen artifacts are recorded as explicit nulls rather than backfilled with estimates.",
        "",
        "| Provenance Completeness | Artifact Count | Percentage | Description |",
        "| :--- | :---: | :---: | :--- |",
        f"| **COMPLETE** | **{status_counts['COMPLETE']}** | **{pcts['COMPLETE']}%** | All 6 core fields present (`commit`, `timestamp`, `model`, `prompts`, `cache_schema`, `config_snapshot`) |",
        f"| **PARTIAL** | **{status_counts['PARTIAL']}** | **{pcts['PARTIAL']}%** | Partial provenance (frozen run reports with `run_id`, `timestamp`, `prompts_version`) |",
        f"| **MINIMAL** | **{status_counts['MINIMAL']}** | **{pcts['MINIMAL']}%** | Legacy probe / audit artifacts with raw metrics only |",
        f"| **TOTAL** | **{meta['total_artifacts_indexed']}** | **100.0%** | Comprehensive index of all JSON outputs |",
        "",
        "---",
        "",
        "## 2. Provenance Breakdown by Artifact Type",
        "",
        "| Artifact Type | Broad Category | Total | Complete | Partial | Minimal | Missing Fields Pattern |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :--- |",
    ]

    for atype, counts in sorted(stats["status_by_artifact_type"].items()):
        tot = counts["COMPLETE"] + counts["PARTIAL"] + counts["MINIMAL"]
        # Determine typical missing fields pattern
        sample_missing = []
        for a in manifest_data["artifacts"]:
            if a["artifact_type"] == atype:
                sample_missing = a["missing_fields"]
                bcat = a["broad_category"]
                break
        missing_str = ", ".join(sample_missing) if sample_missing else "None (Fully specified)"
        lines.append(
            f"| `{atype}` | `{bcat}` | {tot} | {counts['COMPLETE']} | {counts['PARTIAL']} | {counts['MINIMAL']} | `{missing_str}` |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Provenance Architecture & Historical Evolution",
        "",
        "PharmaGuard's provenance tracking evolved across three distinct architectural phases:",
        "",
        "1. **Phase 1: Frozen Postmarketing Evaluation Reports (August 14–21, 2026)**",
        "   - **Files:** `outputs/core/eval-run-*_report.json`, `outputs/experiments/baseline/`, `outputs/experiments/ablation/`, `outputs/experiments/react_agent/` (60 files)",
        "   - **Fields Present:** `run_id`, `timestamp`, `prompts_version` (`v1.0`), `schema_version` (`1.1`).",
        "   - **Missing Fields:** `git_commit_hash`, `model_name`, `cache_schema_version`, `config_snapshot`.",
        "   - **Design Rationale:** These frozen evaluation reports predate the formal configuration snapshotting convention introduced in R0. Per project integrity rules, these files remain immutable.",
        "",
        "2. **Phase 2: Diagnostic Safety Probes & Audits (August 20–27, 2026)**",
        "   - **Files:** `outputs/experiments/critic_probe/`, `outputs/experiments/confounding_probe/`, `outputs/experiments/probe/`, `outputs/research/stability/loo_analysis.json` (8 files)",
        "   - **Characteristics:** Focused on internal probe cases and post-hoc qualitative audits; metrics were output without standardized experiment metadata wrappers.",
        "",
        "3. **Phase 3: Formal R0 & R1 Research Experiments (August 28–30, 2026)**",
        "   - **Files:** `outputs/research/stability/*.json`, `outputs/research/source_ablation/*.json`, `outputs/research/omop_pilot/*.json`, `outputs/research/error_taxonomy/*.json` (37 files)",
        "   - **Fields Present:** `experiment_id`, `git_commit_hash`, `timestamp`, `model_name` (`gemini-3.1-flash-lite`), `prompts_version` (`v1.1`), `cache_schema_version` (`v7`), `config_snapshot`.",
        "   - **Completeness:** 100% complete provenance specification with reproducible hyperparameter and cache tracking.",
        "",
        "---",
        "",
        "## 4. Complete Queryable Artifact Index",
        "",
        "| Artifact Path | Type | Status | Git Commit | Timestamp | Prompts | Cache | Notes |",
        "| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :--- |",
    ])

    for a in manifest_data["artifacts"]:
        prov = a["provenance"]
        git_str = f"`{prov['git_commit_hash'][:8]}`" if prov["git_commit_hash"] else "—"
        ts_str = prov["timestamp"][:19] if prov["timestamp"] else "—"
        prompts_str = f"`{prov['prompts_version']}`" if prov["prompts_version"] else "—"
        cache_str = f"`{prov['cache_schema_version']}`" if prov["cache_schema_version"] else "—"
        note_snippet = a["notes"].split("(")[0].strip() if a["notes"] else ""

        lines.append(
            f"| [`{a['file_path']}`]({a['file_path']}) | `{a['artifact_type']}` | **{a['provenance_status']}** | {git_str} | {ts_str} | {prompts_str} | {cache_str} | {note_snippet} |"
        )

    lines.append("")
    return "\n".join(lines)


def write_manifest_files(
    manifest_data: Dict[str, Any],
    json_path: Path,
    md_path: Path,
) -> Tuple[Path, Path]:
    """Write both JSON and Markdown manifest files to disk."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    logger.info("Wrote JSON manifest to %s (%d bytes)", json_path, json_path.stat().st_size)

    md_content = generate_markdown_report(manifest_data)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info("Wrote Markdown report to %s (%d bytes)", md_path, md_path.stat().st_size)

    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(description="Build PharmaGuard Reproducibility Manifest")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT, help="Path for output JSON manifest")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT, help="Path for output Markdown manifest")
    args = parser.parse_args()

    manifest_data = build_manifest(REPO_ROOT, args.json_out)
    write_manifest_files(manifest_data, args.json_out, args.md_out)

    meta = manifest_data["manifest_metadata"]
    stats = manifest_data["summary_statistics"]
    print("\n" + "=" * 80)
    print("PHARMAGUARD REPRODUCIBILITY MANIFEST BUILT SUCCESSFULLY")
    print("=" * 80)
    print(f"Total Artifacts Indexed: {meta['total_artifacts_indexed']}")
    print(f"Complete Provenance:     {stats['provenance_completeness']['COMPLETE']} ({stats['completeness_percentages']['COMPLETE']}%)")
    print(f"Partial Provenance:      {stats['provenance_completeness']['PARTIAL']} ({stats['completeness_percentages']['PARTIAL']}%)")
    print(f"Minimal Provenance:      {stats['provenance_completeness']['MINIMAL']} ({stats['completeness_percentages']['MINIMAL']}%)")
    print(f"JSON Artifact:           {args.json_out}")
    print(f"Markdown Artifact:       {args.md_out}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()