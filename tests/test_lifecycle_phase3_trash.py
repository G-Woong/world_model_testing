"""tests/test_lifecycle_phase3_trash.py — Phase 3 trash + cache-cleanup contract tests.

Verifies 13 trash contract tests + 4 cache-cleanup contract tests.
Policy: docs/orchestration/15_lifecycle_automation_v2_plan.md §3, §5, §8
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

_SCRIPT = (
    pathlib.Path(__file__).resolve().parent.parent / "scripts" / "lifecycle_trash_v2.py"
)


def _load_mod():
    spec = importlib.util.spec_from_file_location("lifecycle_trash_v2", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lifecycle_trash_v2"] = mod
    spec.loader.exec_module(mod)
    return mod


_mod = _load_mod()
main = _mod.main
MAX_BYTES = _mod.MAX_BYTES
MAX_FILES = _mod.MAX_FILES
MANIFEST_SCHEMA_VERSION = _mod.MANIFEST_SCHEMA_VERSION


def _make_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a minimal fake repo with outputs/lifecycle dir."""
    (tmp_path / "outputs" / "lifecycle").mkdir(parents=True)
    return tmp_path


def _auto_safe_temp_file(repo: pathlib.Path, name: str = "cleanup_audit_temp.json") -> pathlib.Path:
    """Create a file matching AUTO_SAFE_TEMP pattern."""
    p = repo / "outputs" / name
    p.write_text('{"test": true}', encoding="utf-8")
    return p


def _review_copies_file(repo: pathlib.Path, name: str, content: str = "x") -> pathlib.Path:
    """Create a file under cleanup_audit/review_copies/ (AUTO_SAFE_TEMP pattern)."""
    d = repo / "outputs" / "cleanup_audit" / "review_copies"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(content, encoding="utf-8")
    return p


# ── Test 1 ───────────────────────────────────────────────────────────────────

def test_protected_path_cannot_be_trashed(tmp_path):
    repo = _make_repo(tmp_path)
    pcr = repo / "paper_context_ref"
    pcr.mkdir()
    (pcr / "foo.md").write_text("protected", encoding="utf-8")

    rc = main(["trash", "--scope", "repo", "--root", str(repo)])
    assert rc == 0
    preview = json.loads(
        (repo / "outputs" / "lifecycle" / "latest_trash_preview.json").read_text(encoding="utf-8")
    )
    trashed_paths = {f["original_path"] for f in preview["files"]}
    assert not any("paper_context_ref" in p for p in trashed_paths)
    assert any("paper_context_ref" in p for p in preview.get("protected_skipped", []))


# ── Test 2 ───────────────────────────────────────────────────────────────────

def test_manual_only_cannot_be_trashed(tmp_path):
    repo = _make_repo(tmp_path)
    # Windows-safe dir name (no colons)
    d = repo / "outputs" / "cleanup_audit" / "2026-05-17"
    d.mkdir(parents=True)
    (d / "final_cleanup_plan.json").write_text("{}", encoding="utf-8")

    rc = main(["trash", "--scope", "repo", "--root", str(repo)])
    assert rc == 0
    preview = json.loads(
        (repo / "outputs" / "lifecycle" / "latest_trash_preview.json").read_text(encoding="utf-8")
    )
    trashed = {f["original_path"] for f in preview["files"]}
    assert not any("final_cleanup_plan.json" in p for p in trashed)
    assert any(
        "final_cleanup_plan.json" in p for p in preview.get("manual_skipped", [])
    )


# ── Test 3 ───────────────────────────────────────────────────────────────────

def test_unknown_cannot_be_trashed(tmp_path):
    repo = _make_repo(tmp_path)
    unknown_dir = repo / "some_random_dir"
    unknown_dir.mkdir()
    (unknown_dir / "mystery.bin").write_text("data", encoding="utf-8")

    rc = main(["trash", "--scope", "repo", "--root", str(repo)])
    assert rc == 0
    preview = json.loads(
        (repo / "outputs" / "lifecycle" / "latest_trash_preview.json").read_text(encoding="utf-8")
    )
    trashed = {f["original_path"] for f in preview["files"]}
    assert "some_random_dir/mystery.bin" not in trashed
    assert "some_random_dir/mystery.bin" in preview.get("unknown_skipped", [])


# ── Test 4 ───────────────────────────────────────────────────────────────────

def test_auto_safe_temp_dry_run_creates_preview_only(tmp_path):
    repo = _make_repo(tmp_path)
    p = _auto_safe_temp_file(repo)

    rc = main(["trash", "--scope", "repo", "--root", str(repo)])
    assert rc == 0

    preview_json = repo / "outputs" / "lifecycle" / "latest_trash_preview.json"
    assert preview_json.exists(), "Preview JSON must be created in dry-run"
    preview_md = repo / "outputs" / "lifecycle" / "latest_trash_preview.md"
    assert preview_md.exists(), "Preview MD must be created in dry-run"

    # File must NOT have been moved
    assert p.exists(), "Dry-run must not move any files"

    data = json.loads(preview_json.read_text(encoding="utf-8"))
    assert data["dry_run"] is True
    assert data["actions_taken"] == 0


# ── Test 5 ───────────────────────────────────────────────────────────────────

def test_apply_requires_confirm_controlled_trash(tmp_path):
    repo = _make_repo(tmp_path)
    rc = main(["trash", "--apply", "--root", str(repo)])
    assert rc == 2, "Missing --confirm-controlled-trash must yield exit 2"


# ── Test 6 ───────────────────────────────────────────────────────────────────

def test_manifest_contains_sha256_fields(tmp_path):
    repo = _make_repo(tmp_path)
    _auto_safe_temp_file(repo)

    rc = main([
        "trash", "--scope", "repo", "--apply", "--confirm-controlled-trash",
        "--root", str(repo),
    ])
    assert rc == 0

    # Find manifest
    trash_root = repo / ".lifecycle_trash"
    manifests = list(trash_root.rglob("manifest.json"))
    assert manifests, "manifest.json must be created after --apply"
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))

    assert manifest["files"], "manifest.files must be non-empty after apply"
    for f in manifest["files"]:
        assert f["sha256_before"], "sha256_before must be non-empty"
        assert f["sha256_after"], "sha256_after must be non-empty"
        assert f["sha256_before"] == f["sha256_after"], "sha256 must match (integrity)"


# ── Test 7 ───────────────────────────────────────────────────────────────────

def test_restore_ps1_is_generated(tmp_path):
    repo = _make_repo(tmp_path)
    _auto_safe_temp_file(repo)

    rc = main([
        "trash", "--scope", "repo", "--apply", "--confirm-controlled-trash",
        "--root", str(repo),
    ])
    assert rc == 0

    trash_root = repo / ".lifecycle_trash"
    restore_scripts = list(trash_root.rglob("restore.ps1"))
    assert restore_scripts, "restore.ps1 must be generated alongside manifest.json"


# ── Test 8 ───────────────────────────────────────────────────────────────────

def test_path_traversal_is_blocked(tmp_path):
    """Symlink pointing outside repo root must be skipped."""
    repo = _make_repo(tmp_path)
    outside = tmp_path.parent / "outside_repo_target.txt"
    outside.write_text("outside", encoding="utf-8")

    link_dir = repo / "outputs" / "cleanup_audit" / "review_copies"
    link_dir.mkdir(parents=True, exist_ok=True)
    link = link_dir / "traversal_link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation not supported or requires elevated privileges")

    rc = main(["trash", "--scope", "repo", "--root", str(repo)])
    assert rc == 0
    preview = json.loads(
        (repo / "outputs" / "lifecycle" / "latest_trash_preview.json").read_text(encoding="utf-8")
    )
    trashed = {f["original_path"] for f in preview["files"]}
    assert not any("traversal_link" in p for p in trashed), \
        "Symlink to outside repo must not appear in files[]"


# ── Test 9 ───────────────────────────────────────────────────────────────────

def test_symlink_is_skipped(tmp_path):
    """Symlink file (even inside repo) must be skipped."""
    repo = _make_repo(tmp_path)
    target = repo / "outputs" / "some_real_file.txt"
    target.write_text("real content", encoding="utf-8")

    link_dir = repo / "outputs" / "cleanup_audit" / "review_copies"
    link_dir.mkdir(parents=True, exist_ok=True)
    link = link_dir / "symlink_file.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation not supported or requires elevated privileges")

    rc = main(["trash", "--scope", "repo", "--root", str(repo)])
    assert rc == 0
    preview = json.loads(
        (repo / "outputs" / "lifecycle" / "latest_trash_preview.json").read_text(encoding="utf-8")
    )
    trashed = {f["original_path"] for f in preview["files"]}
    assert not any("symlink_file" in p for p in trashed), "Symlink must be skipped"


# ── Test 10 ──────────────────────────────────────────────────────────────────

def test_archive_ready_is_preview_only(tmp_path):
    repo = _make_repo(tmp_path)
    gate_dir = repo / "outputs" / "phase_gates"
    gate_dir.mkdir(parents=True)
    (gate_dir / "P1.passed").write_bytes(b"")

    plans_dir = repo / "plans"
    plans_dir.mkdir()
    (plans_dir / "P1_DATA_PLAN.md").write_text("# P1 plan", encoding="utf-8")

    rc = main(["trash", "--scope", "repo", "--root", str(repo)])
    assert rc == 0
    preview = json.loads(
        (repo / "outputs" / "lifecycle" / "latest_trash_preview.json").read_text(encoding="utf-8")
    )
    trashed_paths = {f["original_path"] for f in preview["files"]}
    archive_paths = {f["path"] for f in preview.get("archive_preview_only", [])}
    assert "plans/P1_DATA_PLAN.md" not in trashed_paths, \
        "ARCHIVE_READY must not appear in files[]"
    assert "plans/P1_DATA_PLAN.md" in archive_paths, \
        "ARCHIVE_READY must appear in archive_preview_only[]"


# ── Test 11 ──────────────────────────────────────────────────────────────────

def test_staged_file_is_skipped(tmp_path, monkeypatch):
    """File present in git diff --cached must be skipped."""
    repo = _make_repo(tmp_path)
    p = _auto_safe_temp_file(repo)
    rel = "outputs/cleanup_audit_temp.json"

    # Monkeypatch _git_staged_files to return our file as staged
    monkeypatch.setattr(_mod, "_git_staged_files", lambda _root: {rel})

    rc = main(["trash", "--scope", "repo", "--root", str(repo)])
    assert rc == 0
    preview = json.loads(
        (repo / "outputs" / "lifecycle" / "latest_trash_preview.json").read_text(encoding="utf-8")
    )
    trashed = {f["original_path"] for f in preview["files"]}
    assert rel not in trashed, "Staged file must be skipped"
    assert p.exists(), "Staged file must not be moved"


# ── Test 12 ──────────────────────────────────────────────────────────────────

def test_manifest_schema_version_present(tmp_path):
    repo = _make_repo(tmp_path)
    _auto_safe_temp_file(repo)

    rc = main([
        "trash", "--scope", "repo", "--apply", "--confirm-controlled-trash",
        "--root", str(repo),
    ])
    assert rc == 0

    trash_root = repo / ".lifecycle_trash"
    manifests = list(trash_root.rglob("manifest.json"))
    assert manifests
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert manifest.get("manifest_schema_version") == MANIFEST_SCHEMA_VERSION


# ── Test 13 ──────────────────────────────────────────────────────────────────

def test_max_bytes_enforced(tmp_path):
    """Total candidate size > MAX_BYTES should result in trimmed manifest."""
    repo = _make_repo(tmp_path)

    # Create two files: each just above half of MAX_BYTES → total > MAX_BYTES
    half = MAX_BYTES // 2 + 1024
    _review_copies_file(repo, "big_file_a.bin", "x" * half)
    _review_copies_file(repo, "big_file_b.bin", "x" * half)

    rc = main(["trash", "--scope", "repo", "--root", str(repo)])
    assert rc == 0
    preview = json.loads(
        (repo / "outputs" / "lifecycle" / "latest_trash_preview.json").read_text(encoding="utf-8")
    )
    # With two files each of half+1KB, only one fits under MAX_BYTES
    assert len(preview["files"]) < 2, \
        "max_bytes gate must trim candidates that would exceed the limit"


# ── Cache cleanup Test 14 ─────────────────────────────────────────────────────

def test_cache_dry_run_does_not_delete(tmp_path):
    repo = _make_repo(tmp_path)
    cache_dir = repo / ".pytest_cache" / "v" / "cache"
    cache_dir.mkdir(parents=True)
    cached_file = cache_dir / "lastfailed"
    cached_file.write_bytes(b"{}")

    rc = main(["cleanup-cache", "--root", str(repo)])
    assert rc == 0
    assert cached_file.exists(), "Dry-run must not delete any cache file"
    preview_json = repo / "outputs" / "lifecycle" / "latest_cache_cleanup_preview.json"
    assert preview_json.exists()
    data = json.loads(preview_json.read_text(encoding="utf-8"))
    assert data["dry_run"] is True
    assert data["actions_taken"] == 0


# ── Cache cleanup Test 15 ─────────────────────────────────────────────────────

def test_cache_apply_requires_confirm_cache_cleanup(tmp_path):
    repo = _make_repo(tmp_path)
    rc = main(["cleanup-cache", "--apply", "--root", str(repo)])
    assert rc == 2, "--apply without --confirm-cache-cleanup must yield exit 2"


# ── Cache cleanup Test 16 ─────────────────────────────────────────────────────

def test_tracked_file_is_never_deleted(tmp_path, monkeypatch):
    """A file returned by git ls-files must not be deleted even in apply mode."""
    repo = _make_repo(tmp_path)
    cache_dir = repo / ".pytest_cache"
    cache_dir.mkdir()
    tracked = cache_dir / "tracked_config"
    tracked.write_bytes(b"tracked")
    rel = ".pytest_cache/tracked_config"

    # Monkeypatch git calls so working tree appears clean and this file is tracked
    monkeypatch.setattr(_mod, "_git_is_dirty", lambda _r: False)
    monkeypatch.setattr(_mod, "_git_ls_files", lambda _r: {rel})

    rc = main([
        "cleanup-cache", "--apply", "--confirm-cache-cleanup", "--root", str(repo)
    ])
    assert rc == 0
    assert tracked.exists(), "Tracked file must never be deleted by cache cleanup"


# ── Cache cleanup Test 17 ─────────────────────────────────────────────────────

def test_dirty_working_tree_rejects_cache_cleanup(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    monkeypatch.setattr(_mod, "_git_is_dirty", lambda _r: True)

    rc = main([
        "cleanup-cache", "--apply", "--confirm-cache-cleanup", "--root", str(repo)
    ])
    assert rc == 4, "Dirty working tree must block cache cleanup --apply (exit 4)"
