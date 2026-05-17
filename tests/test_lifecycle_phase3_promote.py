"""tests/test_lifecycle_phase3_promote.py — Phase 3 memory promote contract tests (3).

Policy: docs/orchestration/16_self_evolving_memory_architecture_plan.md §4, §6
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import textwrap

import pytest

_SCRIPT = (
    pathlib.Path(__file__).resolve().parent.parent
    / "scripts"
    / "lifecycle_memory_promote.py"
)


def _load_mod():
    spec = importlib.util.spec_from_file_location("lifecycle_memory_promote", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lifecycle_memory_promote"] = mod
    spec.loader.exec_module(mod)
    return mod


_mod = _load_mod()
promote = _mod.promote
_parse_sigs = _mod._parse_sigs
_recurring_sigs_in_md = _mod._recurring_sigs_in_md
_parse_error_memory = _mod._parse_error_memory


# ── Test 24 ──────────────────────────────────────────────────────────────────

def test_no_promote_when_sig_null(tmp_path, monkeypatch):
    """If all hook log rows have sig=null, no promotion should happen."""
    hook_log = tmp_path / "hook_execution_log.md"
    hook_log.write_text(
        "| timestamp_utc | hook_script | trigger_event | duration_ms | exit_code | notes |\n"
        "|---|---|---|---|---|---|\n"
        "| 2026-05-17T08:00:00Z | stop_lifecycle_automation | Stop | 300 | 0 | actions=0 sig=null |\n"
        "| 2026-05-17T08:05:00Z | stop_lifecycle_automation | Stop | 310 | 0 | actions=0 sig=null |\n",
        encoding="utf-8",
    )
    error_memory = tmp_path / "error_memory.yaml"
    error_memory.write_text("errors:\n", encoding="utf-8")
    recurring = tmp_path / "recurring_errors.md"
    recurring.write_text("# Recurring Errors\n\n(none)\n", encoding="utf-8")

    monkeypatch.setattr(_mod, "HOOK_LOG", hook_log)
    monkeypatch.setattr(_mod, "ERROR_MEMORY", error_memory)
    monkeypatch.setattr(_mod, "RECURRING_ERRORS", recurring)

    sigs = _parse_sigs(hook_log, 20)
    assert sigs == [], "sig=null rows must produce no signatures"

    rc = promote(sigs)
    assert rc == 0
    # error_memory.yaml should NOT have new entries
    entries = _parse_error_memory(error_memory)
    assert len(entries) == 0, "No entries must be added when sigs is empty"
    assert "(none)" in recurring.read_text(encoding="utf-8"), \
        "recurring_errors.md must be unchanged"


# ── Test 25 ──────────────────────────────────────────────────────────────────

def test_promote_after_two_same_signature(tmp_path, monkeypatch):
    """Signature appearing >= 2x must be promoted to error_memory + recurring_errors."""
    hook_log = tmp_path / "hook_execution_log.md"
    hook_log.write_text(
        "| timestamp_utc | hook_script | trigger_event | duration_ms | exit_code | notes |\n"
        "|---|---|---|---|---|---|\n"
        "| 2026-05-17T08:00:00Z | stop | Stop | 300 | 0 | sig=audit_exit_1 |\n"
        "| 2026-05-17T08:05:00Z | stop | Stop | 310 | 0 | sig=audit_exit_1 |\n",
        encoding="utf-8",
    )
    error_memory = tmp_path / "error_memory.yaml"
    error_memory.write_text("errors:\n", encoding="utf-8")
    recurring = tmp_path / "recurring_errors.md"
    recurring.write_text(
        "# Recurring Errors\n\n"
        "| signature | first_seen | count | status |\n"
        "|---|---|---|---|\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(_mod, "HOOK_LOG", hook_log)
    monkeypatch.setattr(_mod, "ERROR_MEMORY", error_memory)
    monkeypatch.setattr(_mod, "RECURRING_ERRORS", recurring)

    sigs = _parse_sigs(hook_log, 20)
    assert sigs.count("audit_exit_1") >= 2

    rc = promote(sigs)
    assert rc == 0

    # error_memory.yaml must have a new entry
    entries = _parse_error_memory(error_memory)
    sig_entries = [e for e in entries if e.get("signature") == "audit_exit_1"]
    assert sig_entries, "error_memory.yaml must contain entry for promoted signature"

    # recurring_errors.md must have a row for the signature
    content = recurring.read_text(encoding="utf-8")
    assert "audit_exit_1" in content, \
        "recurring_errors.md must contain the promoted signature"


# ── Test 26 ──────────────────────────────────────────────────────────────────

def test_no_duplicate_promotion(tmp_path, monkeypatch):
    """Re-occurring signature already in recurring_errors.md must not be duplicated."""
    hook_log = tmp_path / "hook_execution_log.md"
    hook_log.write_text(
        "| timestamp_utc | hook_script | trigger_event | duration_ms | exit_code | notes |\n"
        "|---|---|---|---|---|---|\n"
        "| 2026-05-17T08:00:00Z | stop | Stop | 300 | 0 | sig=known_error |\n"
        "| 2026-05-17T08:05:00Z | stop | Stop | 310 | 0 | sig=known_error |\n"
        "| 2026-05-17T08:10:00Z | stop | Stop | 320 | 0 | sig=known_error |\n",
        encoding="utf-8",
    )
    error_memory = tmp_path / "error_memory.yaml"
    error_memory.write_text("errors:\n", encoding="utf-8")

    # Pre-populate recurring_errors.md with the signature already present
    recurring = tmp_path / "recurring_errors.md"
    recurring.write_text(
        "# Recurring Errors\n\n"
        "| signature | first_seen | count | status |\n"
        "|---|---|---|---|\n"
        "| `known_error` | 2026-05-16 | 2 | OPEN |\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(_mod, "HOOK_LOG", hook_log)
    monkeypatch.setattr(_mod, "ERROR_MEMORY", error_memory)
    monkeypatch.setattr(_mod, "RECURRING_ERRORS", recurring)

    sigs = _parse_sigs(hook_log, 20)
    rc = promote(sigs)
    assert rc == 0

    # recurring_errors.md must still have exactly ONE row for known_error
    content = recurring.read_text(encoding="utf-8")
    count = content.count("`known_error`")
    assert count == 1, \
        f"Signature must appear exactly once in recurring_errors.md, got {count}"
