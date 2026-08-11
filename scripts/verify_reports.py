import json
from pathlib import Path

print("--- Verifying UTF-8 Encoding ---")
project_root = Path(__file__).resolve().parents[1]
outputs_dir = project_root / "outputs"

files = [
    outputs_dir / "pilot-run-0-semaglutide-pancreatitis_report.json",
    outputs_dir / "pilot-run-1-metformin-lactic_acidosis_report.json",
    outputs_dir / "pilot-run-2-atorvastatin-common_cold_report.json"
]

for file in files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"OK: {file} is valid UTF-8")
    except Exception as e:
        print(f"FAILED: {file} - {e}")
        continue
        
    print(f"\n--- Grade extraction check for {file} ---")
    lit = data.get("literature", {})
    grade = lit.get("evidence_grade", "NONE")
    summary = lit.get("evidence_summary", "NONE")
    if summary is None: summary = "NONE"
    
    print(f"Stored Grade : {grade}")
    print(f"Summary Tail : {summary[-150:] if len(summary) > 150 else summary}")
