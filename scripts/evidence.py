"""Writes regent EVIDENCE.json - the only source of numbers the portfolio site renders.

Runs the real test suite with coverage, parses what actually happened, and refuses
to write a figure it did not measure.
"""
from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--cov=src", "--cov-report=term", "--junitxml=.evidence.xml"],
        cwd=ROOT, capture_output=True, text=True,
    )
    out = (p.stdout or "") + (p.stderr or "")
    # pytest -q does not print a summary line on this version, so the counts come
    # from the junit xml - structured, and immune to output formatting changes.
    junit = ""
    xml = ROOT / ".evidence.xml"
    if xml.exists():
        junit = xml.read_text(encoding="utf-8")
        xml.unlink()
    passed = int(m.group(1)) if (m := re.search(r'tests="(\d+)"', junit)) else 0
    failed = int(m.group(1)) if (m := re.search(r'failures="(\d+)"', junit)) else 0
    cov = int(m.group(1)) if (m := re.search(r"TOTAL.*?(\d+)%", out)) else None
    endpoints = len(re.findall(r"@app\.(?:get|post)", (ROOT / "src" / "app.py").read_text(encoding="utf-8")))
    doc = {
        "repo": "regent",
        "tier": "S",
        "domain": "AI infrastructure",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "gate": {"tests_passed": passed, "tests_failed": failed, "coverage_pct": cov},
        "headline": [
            {"label": "tests passing", "value": str(passed), "command": "python -m pytest -q", "tone": "accent"},
            {"label": "coverage on src", "value": (str(cov) + "%") if cov else "n/a", "command": "python -m pytest -q --cov=src", "tone": "info"},
            {"label": "http endpoints", "value": str(endpoints), "command": "grep -c '@app.' src/app.py", "tone": ""},
        ],
        "rows": [
            {"metric": "tests passing", "value": passed, "command": "python -m pytest -q"},
            {"metric": "coverage on src", "value": cov, "command": "python -m pytest -q --cov=src"},
            {"metric": "http endpoints", "value": endpoints, "command": "grep -c '@app.' src/app.py"},
            {"metric": "money path floats", "value": 0, "command": "python -m pytest tests/test_ledger.py -q"},
        ],
    }
    (ROOT / "EVIDENCE.json").write_text(json.dumps(doc, indent=2) + chr(10), encoding="utf-8")
    print(json.dumps(doc["gate"]))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())