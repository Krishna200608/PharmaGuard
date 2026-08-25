"""
Streamlit Community Cloud Entrypoint
====================================
PharmaGuard Multi-Agent Pharmacovigilance Evaluation Dashboard.
Auto-detected by Streamlit Community Cloud when deploying from GitHub.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure root and scripts/ directory are on PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard import main  # noqa: E402

if __name__ == "__main__":
    main()