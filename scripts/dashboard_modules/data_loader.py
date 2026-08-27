"""
PharmaGuard Data Loader
=======================
Pure JSON file ingestion and DataFrame builder.
HARD INVARIANT: ZERO network calls at runtime.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import pandas as pd
import streamlit as st

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pharmaguard.agent.output_schema import compute_source_agreement

# Verified benchmark values from DECISIONS.md §16
PROD_METRICS = {
    's_prec': 1.000, 's_rec': 0.857, 's_spec': 1.000, 's_f1': 0.923,
    'l_prec': 0.875, 'l_rec': 1.000, 'l_spec': 0.875, 'l_f1': 0.933,
    'ocr': 12.5,
}

BASE_METRICS = {
    's_prec': 0.875, 's_rec': 1.000, 's_spec': 0.875, 's_f1': 0.933,
    'l_prec': 0.700, 'l_rec': 1.000, 'l_spec': 0.625, 'l_f1': 0.824,
    'ocr': 25.0,
}


def run_idx(name: str) -> int:
    """Extract evaluation run index from filename."""
    m = re.search(r'eval-run-(\d+)-', name)
    return int(m.group(1)) if m else 999


@st.cache_data
def load_ground_truth(path: Path) -> dict:
    """Load curated 15-pair ground truth dataset."""
    if not path.exists():
        return {}
    with open(path, encoding='utf-8') as fh:
        raw = json.load(fh)
    return {
        f"{p['drug_canonical']}::{p['event_meddra_pt']}": p
        for p in raw.get('pairs', [])
    }


@st.cache_data
def load_reports(directory: Path) -> list:
    """Load evaluation JSON reports sorted by run index."""
    reports = []
    for path in sorted(directory.glob('eval-run-*_report.json'), key=lambda p: run_idx(p.name)):
        try:
            with open(path, encoding='utf-8') as fh:
                rpt = json.load(fh)
            rpt['_src'] = path.name
            reports.append(rpt)
        except (json.JSONDecodeError, OSError):
            pass
    return reports


@st.cache_data
def build_df(reports: list, gt: dict) -> pd.DataFrame:
    """Build flattened comparison DataFrame from reports and ground truth."""
    rows = []
    for r in reports:
        drug = r.get('drug', '')
        event = r.get('event', '')
        entry = gt.get(f'{drug}::{event}', {})
        expected = entry.get('expected_escalation', '')
        actual = r.get('triage', {}).get('escalation', '')

        prr_s = r.get('signal_stats', {}).get('prr_score', 0.0) or 0.0
        grade_s = r.get('literature', {}).get('grade_score', 0.0) or 0.0
        plaus_s = r.get('mechanism', {}).get('plausibility_score', 0.0) or 0.0
        agr = r.get('triage', {}).get('source_agreement') or compute_source_agreement(prr_s, grade_s, plaus_s)

        rows.append({
            'idx': run_idx(r.get('_src', '')),
            'drug': drug,
            'event': event.replace('_', ' '),
            'category': entry.get('category', ''),
            'signal': r.get('signal_stats', {}).get('prr_score_label', ''),
            'report_count': r.get('signal_stats', {}).get('report_count', 0),
            'prr': r.get('signal_stats', {}).get('prr'),
            'grade': r.get('literature', {}).get('evidence_grade', ''),
            'plausibility': r.get('mechanism', {}).get('biological_plausibility', ''),
            'source_agreement': agr,
            'confidence': r.get('triage', {}).get('confidence'),
            'escalation': actual,
            'expected': expected,
            'match': actual == expected,
            '_r': r,
            '_gt': entry,
        })
    return pd.DataFrame(rows).sort_values('idx').reset_index(drop=True)