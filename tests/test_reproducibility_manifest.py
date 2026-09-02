"""
tests/test_reproducibility_manifest.py - Tests for PharmaGuard Reproducibility Manifest.

Validates:
- Manifest covers every single JSON file under outputs/ (1-to-1 match with disk).
- Missing provenance fields are explicitly null and recorded in missing_fields.
- Complete research artifacts have status COMPLETE with 0 missing fields.
- Frozen evaluation reports have status PARTIAL with explicit missing fields.
- Markdown summary report exists and is formatted properly.
"""

import json
from pathlib import Path
import pytest

from scripts.research.build_reproducibility_manifest import (
    REPO_ROOT,
    OUTPUTS_DIR,
    build_manifest,
    write_manifest_files,
)


@pytest.fixture(scope="module")
def manifest_payload():
    """Build manifest once for testing."""
    return build_manifest()


def test_manifest_covers_all_json_files(manifest_payload):
    """Manifest must cover 100% of JSON files under outputs/ with zero omissions."""
    disk_json_files = {p.relative_to(REPO_ROOT).as_posix() for p in OUTPUTS_DIR.rglob("*.json")}
    manifest_files = {a["file_path"] for a in manifest_payload["artifacts"]}

    # Both sets must be identical
    assert disk_json_files == manifest_files
    assert len(manifest_payload["artifacts"]) == len(disk_json_files)


def test_complete_provenance_research_artifacts(manifest_payload):
    """Research experiments from R0/R1 must have COMPLETE status and 0 missing fields."""
    complete_paths = [
        "outputs/research/stability/repeated_run_variance.json",
        "outputs/research/stability/repeated_run_variance_confounding.json",
        "outputs/research/source_ablation/ablation_results.json",
        "outputs/research/source_ablation/threshold_sensitivity.json",
        "outputs/research/source_ablation/counterfactual_margins.json",
    ]
    by_path = {a["file_path"]: a for a in manifest_payload["artifacts"]}

    for cp in complete_paths:
        assert cp in by_path
        entry = by_path[cp]
        assert entry["provenance_status"] == "COMPLETE"
        assert entry["missing_fields"] == []
        assert entry["provenance"]["git_commit_hash"] is not None
        assert entry["provenance"]["model_name"] == "gemini-3.1-flash-lite"
        assert entry["provenance"]["prompts_version"] == "v1.1"
        assert entry["provenance"]["cache_schema_version"] == "v7"
        assert isinstance(entry["provenance"]["config_snapshot"], dict)


def test_partial_provenance_frozen_reports(manifest_payload):
    """Frozen production reports must have PARTIAL status and explicitly null missing fields."""
    by_path = {a["file_path"]: a for a in manifest_payload["artifacts"]}
    sample_path = "outputs/core/eval-run-0-montelukast-suicidal_ideation_report.json"

    assert sample_path in by_path
    entry = by_path[sample_path]
    assert entry["provenance_status"] == "PARTIAL"
    assert "git_commit_hash" in entry["missing_fields"]
    assert "config_snapshot" in entry["missing_fields"]
    assert entry["provenance"]["git_commit_hash"] is None
    assert entry["provenance"]["config_snapshot"] is None
    assert entry["provenance"]["run_id"] == "eval-run-0-montelukast-suicidal_ideation"
    assert entry["provenance"]["prompts_version"] == "v1.0"


def test_missing_fields_are_explicit_nulls(manifest_payload):
    """Every missing field listed in missing_fields must be explicitly None in provenance dict."""
    for entry in manifest_payload["artifacts"]:
        prov = entry["provenance"]
        for mf in entry["missing_fields"]:
            assert prov.get(mf) is None, f"Field {mf} listed as missing but is not None in {entry['file_path']}!"


def test_markdown_report_generation(tmp_path, manifest_payload):
    """Verify Markdown report generation and file writing."""
    json_path = tmp_path / "manifest.json"
    md_path = tmp_path / "manifest.md"

    write_manifest_files(manifest_payload, json_path, md_path)

    assert json_path.exists()
    assert md_path.exists()

    md_content = md_path.read_text(encoding="utf-8")
    assert "# PharmaGuard Reproducibility & Provenance Manifest" in md_content
    assert "## 1. Executive Summary & Provenance Health" in md_content
    assert "outputs/research/stability/repeated_run_variance.json" in md_content