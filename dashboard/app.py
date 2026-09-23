"""
PharmaGuard Dashboard entry point forwarder.
Allows 'streamlit run dashboard/app.py' as well as 'streamlit run scripts/dashboard.py'.
"""
import runpy
from pathlib import Path

_dashboard_script = Path(__file__).resolve().parent.parent / "scripts" / "dashboard.py"
runpy.run_path(str(_dashboard_script), run_name="__main__")
