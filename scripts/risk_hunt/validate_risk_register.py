"""STEP 10 risk register schema validator.

Parses docs/orchestration/risk_hunt/01_global_risk_register.md
and validates the 11-field schema for each risk.

Usage:
    python scripts/risk_hunt/validate_risk_register.py             # write JSON
    python scripts/risk_hunt/validate_risk_register.py --dry-run   # stdout only
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
REGISTER_PATH = REPO_ROOT / "docs" / "orchestration" / "risk_hunt" / "01_global_risk_register.md"

VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
VALID_STATUSES = {"OPEN", "TESTING", "MITIGATED", "REJECTED", "BLOCKED_WITH_EVIDENCE", "ACTIVE_CONSTRAINT"}
EXPECTED_CATEGORIES = {
    "CORE", "THR", "FORE", "PCG", "LAT", "REG", "DUP", "ENV", "OXE", "CF",
    "ARC", "LOSS", "LONG", "EVAL", "DTB", "FAI", "STAT", "REV", "NOV", "LEAK",
}

# 11-field labels (as numbered in risk register)
FIELD_LABELS = [
    "Risk ID",
    "Risk statement",
    "Severity",
    "Affected claim",
    "Current evidence",
    "Why this kills the paper",
    "Required test",
    "Candidate fix idea",
    "Codex implementation task",
    "Stop condition",
    "Status",
]


def _extract_risks(text: str) -> list[dict]:
    """Extract risk sections (### RH-CAT-NN) and their numbered fields."""
    risks = []
    # Split on lines starting with ### RH-
    sections = re.split(r"\n(?=### RH-)", text)
    for section in sections:
        m = re.match(r"### (RH-([A-Z]+)-(\d+))", section)
        if not m:
            continue
        risk_id = m.group(1)
        category = m.group(2)
        lines = section.splitlines()
        fields: dict[str, str] = {"risk_id": risk_id, "category": category}
        for i, label in enumerate(FIELD_LABELS, start=1):
            # Match numbered list item: "N. **Label**: value" or "N. **Label**"
            pattern = rf"{i}\.\s+\*\*{re.escape(label)}\*\*[:\s]+(.*)"
            found = None
            for line in lines:
                fm = re.search(pattern, line)
                if fm:
                    found = fm.group(1).strip()
                    break
            fields[f"field_{i}"] = found or ""
        risks.append(fields)
    return risks


def _validate_risk(risk: dict) -> list[str]:
    errors = []
    rid = risk["risk_id"]

    # Check Risk ID format
    if not re.match(r"RH-[A-Z]+-\d+", rid):
        errors.append(f"{rid}: invalid Risk ID format")

    # All fields non-empty
    for i, label in enumerate(FIELD_LABELS, start=1):
        val = risk.get(f"field_{i}", "")
        if not val:
            errors.append(f"{rid}: field_{i} ({label}) is empty")

    # Severity check
    severity = risk.get("field_3", "")
    if severity and severity not in VALID_SEVERITIES:
        errors.append(f"{rid}: invalid Severity '{severity}'")

    # Status check
    status = risk.get("field_11", "")
    if status and status not in VALID_STATUSES:
        errors.append(f"{rid}: invalid Status '{status}'")

    return errors


def run_validation() -> dict:
    if not REGISTER_PATH.exists():
        return {
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "error": f"Register not found: {REGISTER_PATH}",
            "schema_valid": False,
            "gate_o_risk_pass": False,
        }

    text = REGISTER_PATH.read_text(encoding="utf-8")
    risks = _extract_risks(text)

    all_errors: list[str] = []
    for risk in risks:
        all_errors.extend(_validate_risk(risk))

    category_counts: dict[str, int] = {}
    for risk in risks:
        cat = risk["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    severity_counts: dict[str, int] = {s: 0 for s in VALID_SEVERITIES}
    for risk in risks:
        sev = risk.get("field_3", "")
        if sev in severity_counts:
            severity_counts[sev] += 1

    status_counts: dict[str, int] = {}
    for risk in risks:
        st = risk.get("field_11", "")
        if st:
            status_counts[st] = status_counts.get(st, 0) + 1

    schema_valid = len(all_errors) == 0
    missing_cats = EXPECTED_CATEGORIES - set(category_counts.keys())
    gate_pass = len(risks) >= 50 and schema_valid and not missing_cats

    return {
        "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_risks": len(risks),
        "valid_risks": len(risks) - len(set(e.split(":")[0] for e in all_errors)),
        "invalid_risks": all_errors[:50],  # cap to 50 errors
        "category_counts": category_counts,
        "missing_categories": sorted(missing_cats),
        "severity_counts": severity_counts,
        "status_counts": status_counts,
        "schema_valid": schema_valid,
        "gate_o_risk_pass": gate_pass,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate risk register 11-field schema")
    parser.add_argument("--dry-run", action="store_true", help="Print JSON to stdout only")
    args = parser.parse_args()

    result = run_validation()

    if args.dry_run:
        print(json.dumps(result, indent=2))
        if not result.get("gate_o_risk_pass"):
            sys.exit(1)
        return

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = REPO_ROOT / "outputs" / "risk_hunt" / "audits"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"risk_register_{ts}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Validation written to: {out_path}")
    print(json.dumps(result, indent=2))

    if not result.get("gate_o_risk_pass"):
        sys.exit(1)


if __name__ == "__main__":
    main()
