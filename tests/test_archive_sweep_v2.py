"""tests/test_archive_sweep_v2.py — contract tests for archive_sweep_v2.py.

Policy: docs/orchestration/14_REPORT_LIFECYCLE_POLICY.md §3.5
        docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md §Phase G
        .self_evolving_memory/decisions/decision_memory.yaml DEC-003
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

_SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "archive_sweep_v2.py"
_AUDIT_SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "lifecycle_audit_v2.py"
_HOOK = pathlib.Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "stop_lifecycle_automation.ps1"
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load_sweep():
    spec = importlib.util.spec_from_file_location("archive_sweep_v2", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["archive_sweep_v2"] = mod
    spec.loader.exec_module(mod)
    return mod


_sweep = _load_sweep()


def _make_gate(repo: pathlib.Path, n: int) -> None:
    g = repo / "outputs" / "phase_gates"
    g.mkdir(parents=True, exist_ok=True)
    (g / f"P{n}.passed").write_bytes(b"")


def _make_lifecycle_out(repo: pathlib.Path) -> None:
    (repo / "outputs" / "lifecycle").mkdir(parents=True, exist_ok=True)


# ── 1. Script exists ──────────────────────────────────────────────────────────

def test_archive_sweep_script_exists():
    assert _SCRIPT.exists(), f"Missing: {_SCRIPT}"


# ── 2. Dry-run moves nothing ─────────────────────────────────────────────────

def test_archive_sweep_dry_run_moves_nothing(tmp_path):
    _make_lifecycle_out(tmp_path)
    _make_gate(tmp_path, 1)
    plan = tmp_path / "plans" / "P1_TEST_PLAN.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("test plan", encoding="utf-8")

    rc = _sweep.sweep("repo", dry_run=True, confirm=False, repo_root=tmp_path)
    assert rc == 0
    assert plan.exists(), "dry-run must not move any files"


# ── 3. --apply requires --confirm-auto-archive ───────────────────────────────

def test_archive_sweep_apply_requires_confirm_flag(tmp_path):
    _make_lifecycle_out(tmp_path)
    rc = _sweep.sweep("repo", dry_run=False, confirm=False, repo_root=tmp_path)
    assert rc == 2


# ── 4. Protected paths never archived ────────────────────────────────────────

def test_archive_sweep_protected_paths_never_archived(tmp_path):
    _make_lifecycle_out(tmp_path)
    protected_paths = [
        "paper_context_ref/00_CONTEXT_INDEX.md",
        "src/frcgw/schemas/visibility.py",
        "tests/test_visibility_contract.py",
        "evidence_cards/C3_falsification.md",
        "claim_status.json",
        "ablation_results.json",
    ]
    for rel in protected_paths:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("protected", encoding="utf-8")

    rc = _sweep.sweep("repo", dry_run=True, confirm=False, repo_root=tmp_path)
    assert rc == 0
    for rel in protected_paths:
        assert (tmp_path / rel).exists(), f"Protected file must not be touched: {rel}"

    manifest = json.loads(
        (tmp_path / "outputs" / "lifecycle" / "archive_sweep_latest.json").read_text(encoding="utf-8")
    )
    archived_paths = {e["original_path"] for e in manifest["files"]}
    for rel in protected_paths:
        assert rel not in archived_paths, f"Protected path appeared in files[]: {rel}"


# ── 5. PHASE_PROGRESS never archived ─────────────────────────────────────────

def test_archive_sweep_phase_progress_never_archived(tmp_path):
    _make_lifecycle_out(tmp_path)
    _make_gate(tmp_path, 3)
    pp = tmp_path / "plans" / "PHASE_PROGRESS.md"
    pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text("progress", encoding="utf-8")

    rc = _sweep.sweep("repo", dry_run=True, confirm=False, repo_root=tmp_path)
    assert rc == 0
    assert pp.exists()
    manifest = json.loads(
        (tmp_path / "outputs" / "lifecycle" / "archive_sweep_latest.json").read_text(encoding="utf-8")
    )
    archived = {e["original_path"] for e in manifest["files"]}
    assert "plans/PHASE_PROGRESS.md" not in archived


# ── 6. Active evidence never archived ────────────────────────────────────────

def test_archive_sweep_active_evidence_never_archived(tmp_path):
    _make_lifecycle_out(tmp_path)
    for name in ("claim_status.json", "ablation_results.json"):
        f = tmp_path / name
        f.write_text("{}", encoding="utf-8")

    rc = _sweep.sweep("repo", dry_run=True, confirm=False, repo_root=tmp_path)
    assert rc == 0
    manifest = json.loads(
        (tmp_path / "outputs" / "lifecycle" / "archive_sweep_latest.json").read_text(encoding="utf-8")
    )
    archived = {e["original_path"] for e in manifest["files"]}
    assert "claim_status.json" not in archived
    assert "ablation_results.json" not in archived


# ── 7. Rule A: plans with gate sentinel ──────────────────────────────────────

def test_archive_sweep_rule_a_plans_with_gate_sentinel(tmp_path):
    _make_lifecycle_out(tmp_path)
    _make_gate(tmp_path, 3)
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_names = [
        "P3_TEXT_MODEL_PLAN.md",
        "P3_GATE_REPORT.md",
        "P3_EVAL_GATE_REPORT.md",
    ]
    for name in plan_names:
        (plans_dir / name).write_text("content", encoding="utf-8")

    rc = _sweep.sweep("repo", dry_run=True, confirm=False, repo_root=tmp_path)
    assert rc == 0
    manifest = json.loads(
        (tmp_path / "outputs" / "lifecycle" / "archive_sweep_latest.json").read_text(encoding="utf-8")
    )
    archived = {e["original_path"] for e in manifest["files"]}
    for name in plan_names:
        assert f"plans/{name}" in archived, f"Expected plans/{name} in archive candidates"


# ── 8. Rule B: PHASE gate reports ────────────────────────────────────────────

def test_archive_sweep_rule_b_phase_gate_reports(tmp_path):
    _make_lifecycle_out(tmp_path)
    docs_dir = tmp_path / "docs" / "orchestration"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for name in ("PHASE1_GATE_REPORT.md", "PHASE2_GATE_REPORT.md", "PHASE3B_GATE_REPORT.md"):
        (docs_dir / name).write_text("gate report", encoding="utf-8")

    rc = _sweep.sweep("repo", dry_run=True, confirm=False, repo_root=tmp_path)
    assert rc == 0
    manifest = json.loads(
        (tmp_path / "outputs" / "lifecycle" / "archive_sweep_latest.json").read_text(encoding="utf-8")
    )
    archived = {e["original_path"] for e in manifest["files"]}
    for name in ("PHASE1_GATE_REPORT.md", "PHASE2_GATE_REPORT.md", "PHASE3B_GATE_REPORT.md"):
        assert f"docs/orchestration/{name}" in archived


# ── 9. Rule C: codex_done results ────────────────────────────────────────────

def test_archive_sweep_rule_c_codex_done(tmp_path):
    _make_lifecycle_out(tmp_path)
    done_dir = tmp_path / ".agent_tasks" / "codex_done"
    done_dir.mkdir(parents=True, exist_ok=True)
    result_name = "TASK_1002_C3_world_model_RESULT.md"
    (done_dir / result_name).write_text("result", encoding="utf-8")

    rc = _sweep.sweep("repo", dry_run=True, confirm=False, repo_root=tmp_path)
    assert rc == 0
    manifest = json.loads(
        (tmp_path / "outputs" / "lifecycle" / "archive_sweep_latest.json").read_text(encoding="utf-8")
    )
    archived = {e["original_path"] for e in manifest["files"]}
    assert f".agent_tasks/codex_done/{result_name}" in archived


# ── 10. Rule D: codex_archive dir ────────────────────────────────────────────

def test_archive_sweep_rule_d_codex_archive(tmp_path):
    _make_lifecycle_out(tmp_path)
    arc_dir = tmp_path / ".agent_tasks" / "codex_archive" / "p3_impl"
    arc_dir.mkdir(parents=True, exist_ok=True)
    (arc_dir / "TASK_C3.md").write_text("task", encoding="utf-8")

    rc = _sweep.sweep("repo", dry_run=True, confirm=False, repo_root=tmp_path)
    assert rc == 0
    manifest = json.loads(
        (tmp_path / "outputs" / "lifecycle" / "archive_sweep_latest.json").read_text(encoding="utf-8")
    )
    archived = {e["original_path"] for e in manifest["files"]}
    assert ".agent_tasks/codex_archive/p3_impl/TASK_C3.md" in archived


# ── 11. Manifest has all required fields ─────────────────────────────────────

def test_archive_sweep_manifest_has_required_fields(tmp_path):
    _make_lifecycle_out(tmp_path)
    _make_gate(tmp_path, 2)
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    (plans_dir / "P2_TEXT_ONLY_DATA_PLAN.md").write_text("plan", encoding="utf-8")

    rc = _sweep.sweep("repo", dry_run=True, confirm=False, repo_root=tmp_path)
    assert rc == 0
    manifest = json.loads(
        (tmp_path / "outputs" / "lifecycle" / "archive_sweep_latest.json").read_text(encoding="utf-8")
    )

    top_required = {
        "manifest_schema_version", "run_id", "scope", "dry_run",
        "actions_taken", "classifier_version", "policy", "files",
        "protected_skipped", "manual_skipped", "unknown_skipped", "errors",
    }
    assert top_required.issubset(manifest.keys())

    file_required = {
        "original_path", "archive_path", "archive_reason", "absorbed_by",
        "self_evolving_summary_status", "sha256_before", "sha256_after",
        "size_bytes", "git_tracked", "move_method", "auto_archived", "restore_command",
    }
    for entry in manifest["files"]:
        assert file_required.issubset(entry.keys()), f"Missing fields in entry: {entry}"
        assert entry["restore_command"] != ""
        assert entry["self_evolving_summary_status"] in ("no_value_remaining", "extract_then_archive")


# ── 12. Destination always under archive/YYYY-MM ─────────────────────────────

def test_archive_sweep_destination_under_archive_yyyy_mm(tmp_path):
    _make_lifecycle_out(tmp_path)
    _make_gate(tmp_path, 1)
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    (plans_dir / "P1_PLAN.md").write_text("plan", encoding="utf-8")

    rc = _sweep.sweep("repo", dry_run=True, confirm=False, repo_root=tmp_path)
    assert rc == 0
    manifest = json.loads(
        (tmp_path / "outputs" / "lifecycle" / "archive_sweep_latest.json").read_text(encoding="utf-8")
    )
    for entry in manifest["files"]:
        assert "archive/" in entry["archive_path"], (
            f"archive_path must be under archive/: {entry['archive_path']}"
        )


# ── 13. Path traversal blocked ────────────────────────────────────────────────

def test_archive_sweep_path_traversal_blocked():
    dest = "../outside/the/repo/evil.md"
    result = _sweep._no_path_traversal(dest, REPO_ROOT)
    assert not result, "Path traversal must be blocked"


# ── 14. Symlink blocked ───────────────────────────────────────────────────────

def test_archive_sweep_symlink_blocked(tmp_path):
    _make_lifecycle_out(tmp_path)
    _make_gate(tmp_path, 1)
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    real = tmp_path / "real_plan.md"
    real.write_text("real", encoding="utf-8")
    try:
        link = plans_dir / "P1_SYMLINK_PLAN.md"
        link.symlink_to(real)
        link_exists = True
    except OSError:
        link_exists = False

    if not link_exists:
        pytest.skip("symlinks not supported on this system")

    err = _sweep._safety_check(
        "plans/P1_SYMLINK_PLAN.md",
        "plans/archive/2026-05/P1_SYMLINK_PLAN.md",
        link,
        tmp_path,
    )
    assert err is not None and "symlink" in err.lower()


# ── 15. Rule A destination is plans/archive/YYYY-MM ─────────────────────────

def test_archive_sweep_rule_a_destination():
    dest = _sweep._destination("plans/P3_GATE_REPORT.md", "rule_a")
    assert dest.startswith("plans/archive/")
    assert dest.endswith("P3_GATE_REPORT.md")


# ── 16. Hook invokes archive_sweep ───────────────────────────────────────────

def test_hook_invokes_archive_sweep():
    src = _HOOK.read_text(encoding="utf-8")
    assert "archive_sweep_v2.py" in src, (
        "stop_lifecycle_automation.ps1 must reference archive_sweep_v2.py for Phase 5"
    )


# ── 17. ARCHIVE_READY allowed in hook --apply lines ──────────────────────────

def test_hook_archive_apply_signature_only_for_archive_ready():
    src = _HOOK.read_text(encoding="utf-8")
    non_comment = "\n".join(
        ln for ln in src.splitlines()
        if not ln.lstrip().startswith("#")
    )
    apply_lines = [ln for ln in non_comment.splitlines() if "--apply" in ln]
    # Each --apply line must be for trash, cleanup-cache, or archive sweep
    for ln in apply_lines:
        allowed = "trash" in ln or "cleanup-cache" in ln or "sweep" in ln
        assert allowed, f"--apply must only appear with trash/cleanup-cache/sweep: {ln!r}"
    # MANUAL_ONLY and UNKNOWN must never appear on --apply lines
    for ln in apply_lines:
        for cls in ("MANUAL_ONLY", "UNKNOWN"):
            assert cls not in ln, f"--apply must not appear alongside {cls}: {ln!r}"
