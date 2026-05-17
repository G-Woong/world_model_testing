"""scripts/lifecycle_memory_promote.py — Recurring error promotion from hook_execution_log.md.

Policy source:
  docs/orchestration/16_self_evolving_memory_architecture_plan.md §4 (recurring schema), §6

Phase 3: reads hook_execution_log.md, finds sig=<X> with occurrence_count >= 2,
promotes to error_memory.yaml + recurring_errors.md.
No fake error generation. Always exit 0 (hook-safe).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import pathlib
import re
import sys
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK_LOG = REPO_ROOT / ".self_evolving_memory" / "hooks" / "hook_execution_log.md"
ERROR_MEMORY = REPO_ROOT / ".self_evolving_memory" / "errors" / "error_memory.yaml"
RECURRING_ERRORS = REPO_ROOT / ".self_evolving_memory" / "errors" / "recurring_errors.md"


# ── YAML helpers (no external dependency) ────────────────────────────────────

def _parse_error_memory(path: pathlib.Path) -> list[dict]:
    """Minimal parser for the known error_memory.yaml schema."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    entries: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        if re.match(r"^\s{2}- id:", line):
            if current is not None:
                entries.append(current)
            val = line.split(":", 1)[1].strip().strip('"')
            current = {"id": val}
        elif current is not None and re.match(r"^\s{4}\w", line):
            m = re.match(r"^\s{4}(\w+):\s*(.*)", line)
            if m:
                key, val = m.group(1), m.group(2).strip().strip('"')
                if val == "null":
                    current[key] = None
                elif val.lstrip("-").isdigit():
                    current[key] = int(val)
                else:
                    current[key] = val
    if current is not None:
        entries.append(current)
    return entries


def _next_err_id(entries: list[dict]) -> str:
    nums = []
    for e in entries:
        m = re.match(r"ERR-(\d+)", str(e.get("id", "")))
        if m:
            nums.append(int(m.group(1)))
    return f"ERR-{(max(nums) + 1):03d}" if nums else "ERR-002"


def _write_error_memory(entries: list[dict]) -> None:
    lines = [
        "# errors/error_memory.yaml — recurring error pattern log",
        "# schema per entry:",
        "#   id, first_seen, last_seen, occurrence_count, description,",
        "#   resolution_status, resolution, regression_test,",
        "#   do_not_repeat_rule, escalation_rule, notes",
        "#   (legacy: count, signature)",
        "",
        "errors:",
    ]
    scalar_keys = (
        "signature", "first_seen", "last_seen", "count", "occurrence_count",
        "description", "resolution_status", "resolution",
        "regression_test", "do_not_repeat_rule", "escalation_rule",
    )
    block_keys = ("notes",)
    for e in entries:
        lines.append(f"  - id: {e.get('id', '')}")
        for k in scalar_keys:
            if k not in e:
                continue
            v = e[k]
            if v is None:
                lines.append(f"    {k}: null")
            elif isinstance(v, int):
                lines.append(f"    {k}: {v}")
            elif isinstance(v, str) and len(v) <= 80 and "\n" not in v:
                lines.append(f'    {k}: "{v}"')
            elif isinstance(v, str):
                lines.append(f"    {k}: >")
                for part in v.splitlines():
                    lines.append(f"      {part}")
            else:
                lines.append(f"    {k}: {v}")
        for k in block_keys:
            if k not in e:
                continue
            v = e[k]
            if v is None:
                lines.append(f"    {k}: null")
            elif isinstance(v, str):
                lines.append(f"    {k}: >")
                for part in v.splitlines():
                    lines.append(f"      {part}")
    ERROR_MEMORY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_sigs(log_path: pathlib.Path, max_rows: int) -> list[str]:
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()
    table_rows = [ln for ln in lines if ln.startswith("|") and "---" not in ln]
    # Drop header row (contains column names)
    if table_rows and any(h in table_rows[0].lower() for h in ("hook_name", "timestamp_utc")):
        table_rows = table_rows[1:]
    recent = table_rows[-max_rows:] if max_rows > 0 else table_rows
    sigs: list[str] = []
    for row in recent:
        m = re.search(r"sig=([^\s|]+)", row)
        if m:
            sig = m.group(1)
            if sig not in ("null", ""):
                sigs.append(sig)
    return sigs


def _recurring_sigs_in_md(path: pathlib.Path) -> set[str]:
    if not path.exists():
        return set()
    found: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.search(r"`([^`]+)`", line)
        if m and m.group(1) not in ("sig", "signature"):
            found.add(m.group(1))
    return found


# ── Promotion logic ───────────────────────────────────────────────────────────

def promote(sigs: list[str]) -> int:
    counts = Counter(sigs)
    to_promote = [sig for sig, cnt in counts.items() if cnt >= 2]
    if not to_promote:
        print("lifecycle_memory_promote: no signatures with occurrence_count >= 2")
        return 0

    entries = _parse_error_memory(ERROR_MEMORY)
    recurring = _recurring_sigs_in_md(RECURRING_ERRORS)
    today = _dt.date.today().isoformat()
    promoted = 0

    for sig in to_promote:
        # Update or insert in error_memory.yaml
        found_entry = None
        for e in entries:
            if e.get("signature") == sig:
                found_entry = e
                break
        if found_entry is not None:
            found_entry["occurrence_count"] = int(
                found_entry.get("occurrence_count") or found_entry.get("count") or 1
            ) + 1
            found_entry["last_seen"] = today
        else:
            new_id = _next_err_id(entries)
            entries.append({
                "id": new_id,
                "signature": sig,
                "first_seen": today,
                "last_seen": today,
                "occurrence_count": counts[sig],
                "description": f"Recurring hook signature: {sig}",
                "resolution_status": "OPEN",
                "resolution": None,
                "regression_test": None,
                "do_not_repeat_rule": None,
                "escalation_rule": None,
                "notes": f"Auto-promoted from hook_execution_log.md (seen {counts[sig]}x)",
            })

        # Append row to recurring_errors.md (no duplicate)
        if sig not in recurring:
            content = (
                RECURRING_ERRORS.read_text(encoding="utf-8")
                if RECURRING_ERRORS.exists() else ""
            )
            if not content.endswith("\n"):
                content += "\n"
            row = f"| `{sig}` | {today} | {counts[sig]} | OPEN |"
            RECURRING_ERRORS.write_text(content + row + "\n", encoding="utf-8")
            recurring.add(sig)
            promoted += 1
            print(f"  [PROMOTED] {sig}")
        else:
            print(f"  [SKIP] already in recurring_errors.md: {sig}")

    _write_error_memory(entries)
    print(f"lifecycle_memory_promote: promoted={promoted} new signatures")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Promote recurring hook signatures to error memory."
    )
    p.add_argument(
        "--max-rows", type=int, default=20,
        help="Number of recent hook log rows to scan (default: 20)",
    )
    args = p.parse_args(argv)
    sigs = _parse_sigs(HOOK_LOG, args.max_rows)
    return promote(sigs)


if __name__ == "__main__":
    raise SystemExit(main())
