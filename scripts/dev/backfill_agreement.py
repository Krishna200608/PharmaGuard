"""
Developer utility for retroactively computing cross-source evidence agreement
for the 15 benchmark pairs without modifying frozen JSON files.

Owner: Krishna Sikheriya (IIT2023139)
"""

import json
from pathlib import Path
import sys

# Ensure UTF-8 stdout on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pharmaguard.agent.output_schema import TriageReport, compute_source_agreement


def backfill_agreement():
    outputs_dir = REPO_ROOT / "outputs" / "core"
    if not outputs_dir.exists():
        outputs_dir = REPO_ROOT / "outputs"
    report_files = sorted(list(outputs_dir.glob("eval-run-*_report.json")))
    if not report_files:
        print(f"No reports found in {outputs_dir}")
        return

    print("=" * 95)
    print("PHARMAGUARD CROSS-SOURCE EVIDENCE AGREEMENT AUDIT (n=15)")
    print("=" * 95)
    print(
        f"{'Pair':<42} | {'PRR':<5} | {'Grade':<5} | {'Plaus':<5} | {'Source Agreement':<16} | {'Escalation':<15}"
    )
    print("-" * 95)

    concordant_count = 0
    discordant_count = 0

    table_records = []

    for r_file in report_files:
        with open(r_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            report = TriageReport(**data)

        pair = f"{report.drug}::{report.event}"
        prr_s = report.signal_stats.prr_score
        gr_s = report.literature.grade_score
        pl_s = report.mechanism.plausibility_score
        agreement = report.source_agreement
        esc = (
            report.triage.escalation.value
            if hasattr(report.triage.escalation, "value")
            else str(report.triage.escalation)
        )

        if agreement == "CONCORDANT":
            concordant_count += 1
        else:
            discordant_count += 1

        table_records.append({
            "pair": pair,
            "prr": prr_s,
            "grade": gr_s,
            "plaus": pl_s,
            "agreement": agreement,
            "escalation": esc
        })

        print(
            f"{pair:<42} | {prr_s:<5.2f} | {gr_s:<5.2f} | {pl_s:<5.2f} | {agreement:<16} | {esc:<15}"
        )

    print("-" * 95)
    print(f"Total: {len(report_files)} pairs | CONCORDANT: {concordant_count} | DISCORDANT: {discordant_count}")
    print("=" * 95)

    return table_records


if __name__ == "__main__":
    backfill_agreement()