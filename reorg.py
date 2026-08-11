import os
import shutil
from pathlib import Path

root = Path("d:/Research Project/PharmaGuard")

# Rename Docs and Context to temp names to avoid case-insensitive collisions
if (root / "Docs").exists():
    os.rename(root / "Docs", root / "DocsTemp")
if (root / "Context").exists():
    os.rename(root / "Context", root / "ContextTemp")

# Create directories
for d in ["scripts", "docs/context", "docs/proposals", "configs"]:
    (root / d).mkdir(parents=True, exist_ok=True)

# Move files
moves = [
    ("test_faers.py", "tests/test_faers.py"),
    ("test_openfda.py", "tests/test_openfda.py"),
    ("run_pilot.py", "scripts/run_pilot.py"),
    ("check_albuterol.py", "scripts/check_albuterol.py"),
    ("verify_reports.py", "scripts/verify_reports.py"),
    ("evaluator.py", "scripts/evaluator.py"),
    ("NOTES.md", "docs/NOTES.md"),
    ("config.yaml", "configs/config.yaml")
]

for src, dst in moves:
    src_path = root / src
    dst_path = root / dst
    if src_path.exists():
        shutil.move(str(src_path), str(dst_path))

# Move temp contents
docs_temp = root / "DocsTemp"
if docs_temp.exists():
    for f in docs_temp.iterdir():
        shutil.move(str(f), str(root / "docs" / "proposals" / f.name))
    docs_temp.rmdir()

context_temp = root / "ContextTemp"
if context_temp.exists():
    for f in context_temp.iterdir():
        shutil.move(str(f), str(root / "docs" / "context" / f.name))
    context_temp.rmdir()

print("Reorganization complete!")
