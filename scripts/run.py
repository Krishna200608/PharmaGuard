"""
PharmaGuard Environment & Service Launcher Forwarder
===================================================
Forwards execution to root run.py.

Usage:
    python scripts/run.py
"""
import sys
from pathlib import Path
import runpy

ROOT_RUN = Path(__file__).resolve().parents[1] / "run.py"

if __name__ == "__main__":
    runpy.run_path(str(ROOT_RUN), run_name="__main__")
