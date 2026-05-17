"""tests/test_lifecycle_phase2_hooks.py — Phase 2 hook contract tests.

Verifies:
  - stop_lifecycle_automation.ps1 exists and satisfies safety invariants
  - settings.json Stop chain wires lifecycle hook before auto-commit
  - pre_tool_guard.ps1 has plan-path WARN-only (no exit 1 in new block)
  - hook_execution_log.md file exists

Policy: docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md §Phase D/E
"""
from __future__ import annotations

import json
import re
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / ".claude" / "hooks" / "stop_lifecycle_automation.ps1"
SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.json"
PRE_TOOL_GUARD = REPO_ROOT / ".claude" / "hooks" / "pre_tool_guard.ps1"
HOOK_LOG = REPO_ROOT / ".self_evolving_memory" / "hooks" / "hook_execution_log.md"


# ── 1. Hook script exists ─────────────────────────────────────────────────────

def test_hook_script_exists():
    assert HOOK_PATH.exists(), f"Missing: {HOOK_PATH}"


# ── 2. Hook references lifecycle_audit_v2.py ──────────────────────────────────

def test_hook_calls_lifecycle_audit_v2():
    src = HOOK_PATH.read_text(encoding="utf-8")
    assert "lifecycle_audit_v2.py" in src, (
        "stop_lifecycle_automation.ps1 must reference lifecycle_audit_v2.py"
    )


# ── 3. Hook uses --dry-run flag ───────────────────────────────────────────────

def test_hook_uses_dry_run_flag():
    src = HOOK_PATH.read_text(encoding="utf-8")
    assert "--dry-run" in src, (
        "stop_lifecycle_automation.ps1 must pass --dry-run to lifecycle_audit_v2.py"
    )


# ── 4. Hook uses --scope changed ─────────────────────────────────────────────

def test_hook_uses_scope_changed():
    src = HOOK_PATH.read_text(encoding="utf-8")
    assert "--scope changed" in src, (
        "stop_lifecycle_automation.ps1 must pass --scope changed"
    )


# ── 5. Hook has no destructive commands ──────────────────────────────────────

_DESTRUCTIVE = re.compile(
    r"Remove-Item|rm\s|del\s|rmdir|Move-Item|Rename-Item"
    r"|git\s+mv|git\s+rm|git\s+commit|git\s+push",
    re.IGNORECASE,
)

def test_hook_no_destructive_commands():
    src = HOOK_PATH.read_text(encoding="utf-8")
    # Strip comment lines before checking
    non_comment_lines = [
        ln for ln in src.splitlines()
        if not ln.lstrip().startswith("#")
    ]
    non_comment_src = "\n".join(non_comment_lines)
    match = _DESTRUCTIVE.search(non_comment_src)
    assert match is None, (
        f"Destructive command found in stop_lifecycle_automation.ps1: {match.group()!r}"
    )


# ── 6. Hook always exits 0 (no exit 1) ───────────────────────────────────────

def test_hook_exits_zero_always():
    src = HOOK_PATH.read_text(encoding="utf-8")
    assert "exit 0" in src, "stop_lifecycle_automation.ps1 must have 'exit 0'"
    # No non-comment 'exit 1' allowed
    non_comment_lines = [
        ln for ln in src.splitlines()
        if not ln.lstrip().startswith("#")
    ]
    non_comment_src = "\n".join(non_comment_lines)
    assert "exit 1" not in non_comment_src, (
        "stop_lifecycle_automation.ps1 must NOT contain 'exit 1' — always exit 0"
    )


# ── 7. settings.json Stop chain contains lifecycle hook entry ─────────────────

def test_settings_has_lifecycle_hook():
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    stop_entries = settings.get("hooks", {}).get("Stop", [])
    cmds = []
    for entry in stop_entries:
        for h in entry.get("hooks", []):
            cmds.append(h.get("command", ""))
    found = any("stop_lifecycle_automation.ps1" in c for c in cmds)
    assert found, (
        "settings.json Stop chain must contain a stop_lifecycle_automation.ps1 entry"
    )


# ── 8. lifecycle hook comes BEFORE auto-commit in Stop array ─────────────────

def test_stop_hook_order_lifecycle_before_auto_commit():
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    stop_entries = settings.get("hooks", {}).get("Stop", [])

    lifecycle_idx = None
    autocommit_idx = None
    for i, entry in enumerate(stop_entries):
        for h in entry.get("hooks", []):
            cmd = h.get("command", "")
            if "stop_lifecycle_automation.ps1" in cmd:
                lifecycle_idx = i
            if "stop_auto_commit.ps1" in cmd:
                autocommit_idx = i

    assert lifecycle_idx is not None, "stop_lifecycle_automation.ps1 not found in Stop chain"
    assert autocommit_idx is not None, "stop_auto_commit.ps1 not found in Stop chain"
    assert lifecycle_idx < autocommit_idx, (
        f"lifecycle hook (idx={lifecycle_idx}) must come BEFORE auto-commit (idx={autocommit_idx})"
    )


# ── 9. pre_tool_guard.ps1 plan-path WARN has no exit 1 ───────────────────────

def test_pre_tool_guard_plan_path_warn_only():
    src = PRE_TOOL_GUARD.read_text(encoding="utf-8")

    # The new block must exist (identified by its unique marker text)
    assert "Plan-like path WARN" in src or "inAllowedRoot" in src, (
        "pre_tool_guard.ps1 must contain the plan-path WARN block "
        "(marker: 'Plan-like path WARN' or 'inAllowedRoot')"
    )

    # Extract the plan-path block by finding its start and end
    start_markers = ["Plan-like path WARN", "isPlanLike"]
    block_start = -1
    for marker in start_markers:
        idx = src.find(marker)
        if idx != -1:
            block_start = idx
            break

    assert block_start != -1, "Could not locate plan-path WARN block in pre_tool_guard.ps1"

    # Take the block from its start to the closing brace (≈50 chars context)
    # Find the enclosing 'if ($isPlanLike' block end
    block_region = src[block_start : block_start + 800]

    # The plan-path block must NOT contain 'exit 1'
    assert "exit 1" not in block_region, (
        "Plan-path WARN block in pre_tool_guard.ps1 must NOT contain 'exit 1' "
        "(Phase 2 is WARN-only, no BLOCK)"
    )


# ── 10. hook_execution_log.md exists ─────────────────────────────────────────

def test_self_evolving_memory_hook_log_path_exists():
    assert HOOK_LOG.exists(), (
        f"Missing: {HOOK_LOG} — must be created as part of Phase 1 skeleton"
    )
