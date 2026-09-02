import json
from pathlib import Path

print("--- Verifying UTF-8 Encoding ---")
project_root = Path(__file__).resolve().parents[2]
outputs_dir = project_root / "outputs" / "core"

files = list(outputs_dir.glob("eval-run-*_report.json"))

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
