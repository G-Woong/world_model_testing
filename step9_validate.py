import json
from pathlib import Path

REQUIRED_KEYS = [
    "loop_id","iter","run_id","git_sha","config_hash",
    "config_path","phase","split",
    "metrics_before","metrics_after","deltas",
    "failed_metric","diagnosed_cause",
    "candidate_chosen","result",
    "stop_condition_hit","next_action",
    "wall_clock_minutes","vram_peak_mib",
]
VALID_RESULTS = {"accept","reject","inconclusive"}
VALID_STOP = {"max_iter","wall_clock","target_reached","consecutive_inconclusive","hook_blocked",None}

all_files = sorted(Path("outputs/repair").glob("*.jsonl"))
print(f"Files found: {len(all_files)}")
total_errors = 0
for f in all_files:
    lines = [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"--- {f.name} ({len(lines)} lines) ---")
    for i, line in enumerate(lines):
        d = json.loads(line)
        missing = set(REQUIRED_KEYS) - set(d)
        result = d.get("result")
        stop = d.get("stop_condition_hit")
        result_ok = result in VALID_RESULTS
        stop_ok = stop in VALID_STOP
        ok = not missing and result_ok and stop_ok
        status = "PASS" if ok else "FAIL"
        print(f"  [{i}] {status} result={result} stop={stop} keys_ok={not missing} result_ok={result_ok} stop_ok={stop_ok}")
        if missing:
            print(f"      MISSING KEYS: {sorted(missing)}")
            total_errors += 1
        if not result_ok:
            print(f"      INVALID result: {result!r}")
            total_errors += 1
        if not stop_ok:
            print(f"      INVALID stop: {stop!r}")
            total_errors += 1

print(f"\nTotal validation errors: {total_errors}")
