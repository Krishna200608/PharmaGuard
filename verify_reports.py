import json

print("--- Verifying UTF-8 Encoding ---")
for file in ["outputs/pilot-run-0-semaglutide-pancreatitis_report.json",
             "outputs/pilot-run-1-metformin-lactic_acidosis_report.json",
             "outputs/pilot-run-2-atorvastatin-common_cold_report.json"]:
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
