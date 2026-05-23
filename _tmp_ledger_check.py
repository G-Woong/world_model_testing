import json
from pathlib import Path
from fglc.repair.ledger import REQUIRED_KEYS, validate_ledger_line, VALID_RESULTS, VALID_STOP_CONDITIONS

errors = 0
total = 0
for ledger in sorted(Path("outputs/repair").glob("*/ledger.jsonl")):
    for i, line in enumerate(ledger.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        d = json.loads(line)
        try:
            validate_ledger_line(d)
            assert d["result"] in VALID_RESULTS, f"invalid result: {d['result']}"
            sc = d["stop_condition_hit"]
            assert sc is None or sc in VALID_STOP_CONDITIONS, f"invalid stop: {sc}"
            total += 1
            print(f"PASS {ledger.parent.name} line {i}")
        except Exception as e:
            print(f"FAIL {ledger.parent.name} line {i}: {e}")
            errors += 1

print(f"\nTotal: {total} lines checked, {errors} errors")
