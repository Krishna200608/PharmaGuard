import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from pharmaguard.tools.signal_source import FaersLegacySource
stats = FaersLegacySource(cache=None).get_signal_stats("albuterol", "suicidal ideation")
print(f"REPORT COUNT: {stats.report_count}")
print(f"PRR: {stats.prr}")
print(f"NULL REASON: {stats.null_reason}")
