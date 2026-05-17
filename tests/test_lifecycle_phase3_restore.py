"""tests/test_lifecycle_phase3_restore.py — Phase 3 restore contract tests (7).

Tests lifecycle_restore_v2.ps1 via subprocess on Windows PowerShell.
Policy: docs/orchestration/15_lifecycle_automation_v2_plan.md §5
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_RESTORE_PS1 = _REPO_ROOT / "scripts" / "lifecycle_restore_v2.ps1"
_TRASH_SCRIPT = _REPO_ROOT / "scripts" / "lifecycle_trash_v2.py"

MANIFEST_SCHEMA_VERSION = "1.0.0"


def _load_trash_mod():
    spec = importlib.util.spec_from_file_location("lifecycle_trash_v2", _TRASH_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lifecycle_trash_v2"] = mod
    spec.loader.exec_module(mod)
    return mod


_trash_mod = _load_trash_mod()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run_restore(manifest_path: pathlib.Path, repo_root: pathlib.Path,
                 extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    # Note: pass -DryRun 0 (not -DryRun:$false) for subprocess compat on Windows.
    # PowerShell parameter binder converts 0 -> $false correctly.
    cmd = [
        "powershell", "-NonInteractive", "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", str(_RESTORE_PS1),
        "-Manifest", str(manifest_path),
        "-RepoRoot", str(repo_root),
    ]
    if extra_args:
        cmd += extra_args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def _make_manifest(
    repo_root: pathlib.Path,
    run_dir: pathlib.Path,
    files: list[dict],
    *,
    dry_run: bool = False,
) -> pathlib.Path:
    """Write a minimal manifest.json for testing."""
    (run_dir / "files").mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "run_id": "run_test",
        "created_at": "2026-05-17T00:00:00Z",
        "dry_run": dry_run,
        "actions_taken": len(files),
        "classifier_version": "v2.0.0-phase1",
        "policy": {"max_files": 50, "max_bytes": 5242880, "allowed_classifications": ["AUTO_SAFE_TEMP"]},
        "files": files,
        "protected_skipped": [],
        "manual_skipped": [],
        "unknown_skipped": [],
        "archive_preview_only": [],
        "errors": [],
    }
    path = run_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


# ── Test 18 ──────────────────────────────────────────────────────────────────

def test_restore_dry_run_does_not_move(tmp_path):
    """DryRun:$true (default) must not move any file from trash to original."""
    repo = tmp_path / "repo"
    repo.mkdir()
    run_dir = repo / ".lifecycle_trash" / "2026-05" / "run_test"

    content = b"hello restore test"
    sha = _sha256(content)
    trash_file = run_dir / "files" / "outputs__myfile.txt"
    trash_file.parent.mkdir(parents=True)
    trash_file.write_bytes(content)

    files = [{
        "original_path": "outputs/myfile.txt",
        "trash_path": ".lifecycle_trash/2026-05/run_test/files/outputs__myfile.txt",
        "classification": "AUTO_SAFE_TEMP",
        "reason": "test",
        "sha256_before": sha,
        "sha256_after": sha,
        "size_bytes": len(content),
        "git_tracked": False,
        "pre_existing_in_trash": None,
        "restore_command": "test",
    }]
    manifest = _make_manifest(repo, run_dir, files)

    result = _run_restore(manifest, repo)
    assert result.returncode == 0, f"Dry-run must exit 0\nstdout:{result.stdout}\nstderr:{result.stderr}"
    assert trash_file.exists(), "Dry-run must not move file out of trash"
    original = repo / "outputs" / "myfile.txt"
    assert not original.exists(), "Dry-run must not create file at original_path"


# ── Test 19 ──────────────────────────────────────────────────────────────────

def test_restore_apply_requires_confirm_restore(tmp_path):
    """-DryRun:$false without -ConfirmRestore must exit 1."""
    repo = tmp_path / "repo"
    repo.mkdir()
    run_dir = repo / ".lifecycle_trash" / "2026-05" / "run_test"
    manifest = _make_manifest(repo, run_dir, [])

    result = _run_restore(manifest, repo, ["-Apply"])
    assert result.returncode == 1, \
        f"Missing -ConfirmRestore must exit 1\nstdout:{result.stdout}\nstderr:{result.stderr}"


# ── Test 20 ──────────────────────────────────────────────────────────────────

def test_restore_blocks_repo_outside_paths(tmp_path):
    """original_path that resolves outside repo root must be blocked."""
    repo = tmp_path / "repo"
    repo.mkdir()
    run_dir = repo / ".lifecycle_trash" / "2026-05" / "run_test"

    content = b"outside"
    sha = _sha256(content)
    trash_file = run_dir / "files" / "outside_file.txt"
    trash_file.parent.mkdir(parents=True)
    trash_file.write_bytes(content)

    files = [{
        "original_path": "../outside_repo_target.txt",  # path traversal
        "trash_path": ".lifecycle_trash/2026-05/run_test/files/outside_file.txt",
        "classification": "AUTO_SAFE_TEMP",
        "reason": "test",
        "sha256_before": sha,
        "sha256_after": sha,
        "size_bytes": len(content),
        "git_tracked": False,
        "pre_existing_in_trash": None,
        "restore_command": "test",
    }]
    manifest = _make_manifest(repo, run_dir, files)

    result = _run_restore(manifest, repo, ["-Apply", "-ConfirmRestore"])
    # Either exits 1 (error count > 0) or exits 0 but file is NOT outside repo
    outside_target = tmp_path / "outside_repo_target.txt"
    assert not outside_target.exists(), \
        "Restore must never write outside repo root"


# ── Test 21 ──────────────────────────────────────────────────────────────────

def test_restore_blocks_overwrite_unless_force(tmp_path):
    """If original_path already exists, skip without -ForceRestore."""
    repo = tmp_path / "repo"
    repo.mkdir()
    run_dir = repo / ".lifecycle_trash" / "2026-05" / "run_test"

    content = b"trash content"
    sha = _sha256(content)
    trash_file = run_dir / "files" / "outputs__existing.txt"
    trash_file.parent.mkdir(parents=True)
    trash_file.write_bytes(content)

    # Pre-create the original file
    orig_dir = repo / "outputs"
    orig_dir.mkdir(parents=True, exist_ok=True)
    orig_file = orig_dir / "existing.txt"
    orig_file.write_text("original content", encoding="utf-8")

    files = [{
        "original_path": "outputs/existing.txt",
        "trash_path": ".lifecycle_trash/2026-05/run_test/files/outputs__existing.txt",
        "classification": "AUTO_SAFE_TEMP",
        "reason": "test",
        "sha256_before": sha,
        "sha256_after": sha,
        "size_bytes": len(content),
        "git_tracked": False,
        "pre_existing_in_trash": None,
        "restore_command": "test",
    }]
    manifest = _make_manifest(repo, run_dir, files)

    result = _run_restore(manifest, repo, ["-Apply", "-ConfirmRestore"])
    assert result.returncode == 0, f"Should exit 0 (skipped)\nstdout:{result.stdout}"
    # Original file must not be overwritten
    assert orig_file.read_text(encoding="utf-8") == "original content", \
        "Without -ForceRestore, existing file must not be overwritten"
    # Trash file should still be there (not moved)
    assert trash_file.exists(), \
        "Trash file should remain when original exists and no -ForceRestore"


# ── Test 22 ──────────────────────────────────────────────────────────────────

def test_restore_reports_sha256_mismatch(tmp_path):
    """If sha256_after in manifest doesn't match actual trash file, report error."""
    repo = tmp_path / "repo"
    repo.mkdir()
    run_dir = repo / ".lifecycle_trash" / "2026-05" / "run_test"

    content = b"real content"
    wrong_sha = "0" * 64  # tampered sha256_after
    correct_sha = _sha256(content)
    trash_file = run_dir / "files" / "outputs__mismatch.txt"
    trash_file.parent.mkdir(parents=True)
    trash_file.write_bytes(content)

    files = [{
        "original_path": "outputs/mismatch.txt",
        "trash_path": ".lifecycle_trash/2026-05/run_test/files/outputs__mismatch.txt",
        "classification": "AUTO_SAFE_TEMP",
        "reason": "test",
        "sha256_before": correct_sha,
        "sha256_after": wrong_sha,  # tampered
        "size_bytes": len(content),
        "git_tracked": False,
        "pre_existing_in_trash": None,
        "restore_command": "test",
    }]
    manifest = _make_manifest(repo, run_dir, files)

    result = _run_restore(manifest, repo, ["-Apply", "-ConfirmRestore"])
    assert result.returncode == 1, \
        f"sha256 mismatch must exit 1\nstdout:{result.stdout}\nstderr:{result.stderr}"
    assert "mismatch" in result.stdout.lower() or "mismatch" in result.stderr.lower(), \
        "sha256 mismatch must be reported"


# ── Test 23 ──────────────────────────────────────────────────────────────────

def test_roundtrip_with_temp_file(tmp_path):
    """Full roundtrip: trash an AUTO_SAFE_TEMP file then restore it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "outputs" / "lifecycle").mkdir(parents=True)

    # Create AUTO_SAFE_TEMP file
    original_content = b"roundtrip test content 12345"
    original_sha = _sha256(original_content)
    temp_file = repo / "outputs" / "cleanup_audit_temp.json"
    temp_file.write_bytes(original_content)

    # Step 1: trash (Python)
    rc = _trash_mod.main([
        "trash", "--scope", "repo", "--apply", "--confirm-controlled-trash",
        "--root", str(repo),
    ])
    assert rc == 0, "Trash apply must succeed"
    assert not temp_file.exists(), "File must be moved to trash after apply"

    # Find manifest
    manifests = list((repo / ".lifecycle_trash").rglob("manifest.json"))
    assert manifests, "manifest.json must exist after trash apply"
    manifest_path = manifests[0]
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_data["files"], "Manifest must contain the trashed file"

    # Step 2: restore (PowerShell)
    result = _run_restore(manifest_path, repo, ["-Apply", "-ConfirmRestore"])
    assert result.returncode == 0, \
        f"Restore must succeed\nstdout:{result.stdout}\nstderr:{result.stderr}"

    # Verify file restored to original location with correct content
    assert temp_file.exists(), "File must be restored to original location"
    restored_sha = _sha256(temp_file.read_bytes())
    assert restored_sha == original_sha, \
        "Restored file sha256 must match original sha256"
