"""scripts/lifecycle_trash_v2.py — Controlled automation rollout: trash + cache cleanup.

Policy source:
  docs/orchestration/15_lifecycle_automation_v2_plan.md §3, §5, §8
  docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md §Phase F-G

Phase 3 trash/restore CLI consumes lifecycle_audit_v2 module (classifier re-use).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys

# ── Classifier import ────────────────────────────────────────────────────────

def _load_audit_mod():
    _here = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(
        "lifecycle_audit_v2", _here / "lifecycle_audit_v2.py"
    )
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses.__module__ lookup succeeds
    sys.modules["lifecycle_audit_v2"] = mod
    spec.loader.exec_module(mod)
    return mod


_audit = _load_audit_mod()
Classification = _audit.Classification
classify_path = _audit.classify_path
CLASSIFIER_VERSION = _audit.CLASSIFIER_VERSION
_is_protected = _audit._is_protected
_norm = _audit._norm
EXCLUDE_PREFIXES = _audit.EXCLUDE_PREFIXES
_collect_changed = _audit._collect_changed
_collect_repo = _audit._collect_repo
_is_auto_safe_cache = _audit._is_auto_safe_cache

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

MANIFEST_SCHEMA_VERSION = "1.0.0"
MAX_FILES = 50
MAX_BYTES = 5_242_880  # 5 MB

_EXTRA_EXCLUDE = frozenset({".lifecycle_trash/", ".git/", "data/", ".venv/"})


# ── Safety helpers ────────────────────────────────────────────────────────────

def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_windows_junction(path: pathlib.Path) -> bool:
    try:
        return bool(os.lstat(path).st_file_attributes & 0x400)
    except (AttributeError, OSError):
        return False


def _git_staged_files(repo_root: pathlib.Path) -> set[str]:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=10,
        )
        return {_norm(ln.strip()) for ln in r.stdout.splitlines() if ln.strip()}
    except Exception:
        return set()


def _git_ls_files(repo_root: pathlib.Path) -> set[str]:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files"],
            capture_output=True, text=True, timeout=15,
        )
        return {_norm(ln.strip()) for ln in r.stdout.splitlines() if ln.strip()}
    except Exception:
        return set()


def _git_is_dirty(repo_root: pathlib.Path) -> bool:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        return bool(r.stdout.strip())
    except Exception:
        return False


def _is_safe_to_trash(
    rel: str, abs_path: pathlib.Path, repo_root: pathlib.Path, staged: set[str]
) -> tuple[bool, str]:
    norm = _norm(rel)
    for pfx in list(EXCLUDE_PREFIXES) + list(_EXTRA_EXCLUDE):
        if norm.startswith(_norm(pfx)):
            return False, f"excluded prefix: {pfx}"
    prot, reason = _is_protected(rel)
    if prot:
        return False, f"PROTECTED: {reason}"
    try:
        abs_path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False, "path traversal: outside repo root"
    if abs_path.is_symlink():
        return False, "symlink: skipped"
    if _is_windows_junction(abs_path):
        return False, "windows junction: skipped"
    if norm in staged:
        return False, "staged file: skip"
    return True, ""


def _trash_path_for(rel: str, run_dir: pathlib.Path) -> pathlib.Path:
    safe = rel.replace("/", "__").replace("\\", "__")
    return run_dir / "files" / safe


def _run_id() -> str:
    return "run_" + _dt.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")


def _run_dir_for(repo_root: pathlib.Path, run_id: str) -> pathlib.Path:
    month = _dt.datetime.utcnow().strftime("%Y-%m")
    return repo_root / ".lifecycle_trash" / month / run_id


# ── Restore.ps1 generator ────────────────────────────────────────────────────

def _write_restore_ps1(run_dir: pathlib.Path, manifest_path: pathlib.Path) -> None:
    ps1 = run_dir / "restore.ps1"
    rel = manifest_path.name
    content = (
        "# Auto-generated restore wrapper\n"
        "# Usage: powershell -ExecutionPolicy Bypass -File <this> -DryRun:$false -ConfirmRestore\n"
        "$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path\n"
        "$repoRoot  = (Resolve-Path (Join-Path $scriptDir '..' '..')).Path\n"
        f'$manifest  = Join-Path $scriptDir "{rel}"\n'
        "$restore   = Join-Path $repoRoot 'scripts' 'lifecycle_restore_v2.ps1'\n"
        "& $restore -Manifest $manifest @args\n"
    )
    ps1.write_text(content, encoding="utf-8")


# ── Preview writers ───────────────────────────────────────────────────────────

def _write_trash_preview(out_dir: pathlib.Path, prefix: str, obj: dict) -> None:
    (out_dir / f"{prefix}.json").write_text(
        json.dumps(obj, indent=2) + "\n", encoding="utf-8"
    )
    dry = obj.get("dry_run", True)
    lines = [
        f"# Lifecycle Trash — {'Preview' if dry else 'Result'}",
        "",
        f"**dry_run**: {str(dry).lower()}  **run_id**: `{obj.get('run_id', '')}`  "
        f"**actions_taken**: {obj.get('actions_taken', 0)}",
        "",
        "| original_path | class | sha256_before |",
        "|---|---|---|",
    ]
    for f in obj.get("files", []):
        sha = (f.get("sha256_before") or "")[:12] + "..."
        lines.append(f"| `{f['original_path']}` | {f['classification']} | `{sha}` |")
    for f in obj.get("archive_preview_only", []):
        lines.append(f"| `{f['path']}` | ARCHIVE_READY | preview_only |")
    lines += ["", f"_generated: {_dt.datetime.utcnow().isoformat()}Z_"]
    (out_dir / f"{prefix}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Trash subcommand ──────────────────────────────────────────────────────────

def cmd_trash(args: argparse.Namespace) -> int:
    apply_mode = args.apply
    if apply_mode and not args.confirm_controlled_trash:
        print("[EXIT-2] --apply requires --confirm-controlled-trash.", file=sys.stderr)
        return 2

    repo_root = (args.root if hasattr(args, "root") and args.root else REPO_ROOT).resolve()
    out_dir = repo_root / "outputs" / "lifecycle"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect candidates
    audit_path = getattr(args, "audit", None)
    if audit_path:
        p = pathlib.Path(audit_path)
        if not p.exists():
            print(f"[EXIT-1] Audit file not found: {p}", file=sys.stderr)
            return 1
        raw = json.loads(p.read_text(encoding="utf-8"))
        all_rels = [c["path"] for c in raw.get("candidates", [])]
    elif getattr(args, "scope", "changed") == "changed":
        all_rels = _collect_changed(repo_root)
    else:
        all_rels = _collect_repo(repo_root)

    staged = _git_staged_files(repo_root)
    run_id = _run_id()
    run_dir = _run_dir_for(repo_root, run_id)

    files_to_move: list[dict] = []
    archive_preview_only: list[dict] = []
    protected_skipped: list[str] = []
    manual_skipped: list[str] = []
    unknown_skipped: list[str] = []
    errors: list[str] = []

    for rel in all_rels:
        abs_p = repo_root / rel
        if not abs_p.is_file():
            continue
        cand = classify_path(rel, repo_root)
        cls = cand.classification
        if cls == Classification.PROTECTED:
            protected_skipped.append(rel)
            continue
        if cls == Classification.ARCHIVE_READY:
            archive_preview_only.append({"path": rel, "reason": cand.reason})
            continue
        if cls == Classification.MANUAL_ONLY:
            manual_skipped.append(rel)
            continue
        if cls == Classification.UNKNOWN:
            unknown_skipped.append(rel)
            continue
        if cls != Classification.AUTO_SAFE_TEMP:
            continue

        ok, reason = _is_safe_to_trash(rel, abs_p, repo_root, staged)
        if not ok:
            if "PROTECTED" in reason:
                protected_skipped.append(rel)
            elif "staged" in reason:
                manual_skipped.append(rel)
            else:
                unknown_skipped.append(rel)
            continue

        files_to_move.append({
            "rel": rel,
            "abs_p": abs_p,
            "classification": cls.value,
            "reason": cand.reason,
            "size_bytes": abs_p.stat().st_size,
        })

    # Apply file count limit
    if len(files_to_move) > MAX_FILES:
        print(
            f"[WARN] {len(files_to_move)} candidates > max_files={MAX_FILES}; truncating",
            file=sys.stderr,
        )
        files_to_move = files_to_move[:MAX_FILES]

    # Apply byte limit (trim until under limit)
    total_bytes = sum(f["size_bytes"] for f in files_to_move)
    if total_bytes > MAX_BYTES:
        trimmed: list[dict] = []
        acc = 0
        for f in files_to_move:
            if acc + f["size_bytes"] > MAX_BYTES:
                print(f"[WARN] max_bytes exceeded; skipping {f['rel']}", file=sys.stderr)
                continue
            trimmed.append(f)
            acc += f["size_bytes"]
        files_to_move = trimmed

    # Build manifest file entries with sha256
    git_tracked = _git_ls_files(repo_root)
    manifest_files: list[dict] = []

    for f in files_to_move:
        rel = f["rel"]
        abs_p: pathlib.Path = f["abs_p"]
        try:
            sha_before = _sha256(abs_p)
        except Exception as e:
            errors.append(f"sha256 read error for {rel}: {e}")
            continue
        tp = _trash_path_for(rel, run_dir)
        pre_existing = None
        if tp.exists():
            counter = 1
            new_tp = tp.with_name(tp.stem + f"__{counter}" + tp.suffix)
            while new_tp.exists():
                counter += 1
                new_tp = tp.with_name(tp.stem + f"__{counter}" + tp.suffix)
            pre_existing = str(tp.relative_to(repo_root)).replace("\\", "/")
            tp = new_tp
        manifest_files.append({
            "original_path": rel,
            "trash_path": str(tp.relative_to(repo_root)).replace("\\", "/"),
            "classification": f["classification"],
            "reason": f["reason"],
            "sha256_before": sha_before,
            "sha256_after": None,
            "size_bytes": f["size_bytes"],
            "git_tracked": _norm(rel) in git_tracked,
            "pre_existing_in_trash": pre_existing,
            "restore_command": (
                "powershell -ExecutionPolicy Bypass -File scripts/lifecycle_restore_v2.ps1"
                " -Manifest <self>"
            ),
        })

    manifest: dict = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": _dt.datetime.utcnow().isoformat() + "Z",
        "dry_run": not apply_mode,
        "actions_taken": 0,
        "classifier_version": CLASSIFIER_VERSION,
        "policy": {
            "max_files": MAX_FILES,
            "max_bytes": MAX_BYTES,
            "allowed_classifications": ["AUTO_SAFE_TEMP"],
        },
        "files": manifest_files,
        "protected_skipped": protected_skipped,
        "manual_skipped": manual_skipped,
        "unknown_skipped": unknown_skipped,
        "archive_preview_only": archive_preview_only,
        "errors": errors,
    }

    if not apply_mode:
        _write_trash_preview(out_dir, "latest_trash_preview", manifest)
        print(
            f"lifecycle_trash_v2 trash -- dry-run"
            f"  candidates={len(manifest_files)}"
            f"  archive_preview={len(archive_preview_only)}"
            f"  protected_skipped={len(protected_skipped)}"
        )
        print(f"  output: {out_dir / 'latest_trash_preview.json'}")
        return 0

    # Verify trash_path safety gate
    for mf in manifest_files:
        if not mf["trash_path"].startswith(".lifecycle_trash/"):
            print(
                f"[EXIT-3] trash_path not under .lifecycle_trash/: {mf['trash_path']}",
                file=sys.stderr,
            )
            return 3

    (run_dir / "files").mkdir(parents=True, exist_ok=True)

    actions_taken = 0
    for mf in manifest_files:
        abs_src = repo_root / mf["original_path"]
        abs_dst = repo_root / mf["trash_path"]
        abs_dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(abs_src), str(abs_dst))
            sha_after = _sha256(abs_dst)
            mf["sha256_after"] = sha_after
            if sha_after != mf["sha256_before"]:
                errors.append(f"sha256 mismatch after move: {mf['original_path']}")
                continue
            actions_taken += 1
        except Exception as e:
            errors.append(f"move error for {mf['original_path']}: {e}")

    manifest["dry_run"] = False
    manifest["actions_taken"] = actions_taken
    manifest["errors"] = errors

    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _write_restore_ps1(run_dir, manifest_path)
    _write_trash_preview(out_dir, "latest_trash_preview", manifest)

    print(
        f"lifecycle_trash_v2 trash -- APPLIED"
        f"  moved={actions_taken}  errors={len(errors)}"
        f"  manifest={manifest_path}"
    )
    return 0 if not errors else 1


# ── Cache cleanup subcommand ──────────────────────────────────────────────────

def cmd_cleanup_cache(args: argparse.Namespace) -> int:
    apply_mode = args.apply
    if apply_mode and not args.confirm_cache_cleanup:
        print("[EXIT-2] --apply requires --confirm-cache-cleanup.", file=sys.stderr)
        return 2

    repo_root = (args.root if hasattr(args, "root") and args.root else REPO_ROOT).resolve()
    out_dir = repo_root / "outputs" / "lifecycle"
    out_dir.mkdir(parents=True, exist_ok=True)

    if apply_mode and not args.allow_dirty and _git_is_dirty(repo_root):
        print(
            "[EXIT-4] Working tree is dirty; commit or stash before cache cleanup.",
            file=sys.stderr,
        )
        return 4

    all_rels = _collect_repo(repo_root)
    tracked = _git_ls_files(repo_root)

    candidates: list[dict] = []
    for rel in all_rels:
        hit, reason = _is_auto_safe_cache(rel)
        if not hit:
            continue
        if _norm(rel) in tracked:
            continue  # tracked: never delete
        abs_p = repo_root / rel
        if abs_p.is_file():
            candidates.append({"path": rel, "reason": reason, "size_bytes": abs_p.stat().st_size})
        elif abs_p.is_dir():
            candidates.append({"path": rel, "reason": reason, "size_bytes": 0})

    obj: dict = {
        "dry_run": not apply_mode,
        "actions_taken": 0,
        "candidates": candidates,
        "errors": [],
    }

    if not apply_mode:
        json_out = out_dir / "latest_cache_cleanup_preview.json"
        md_out = out_dir / "latest_cache_cleanup_preview.md"
        json_out.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
        lines = [
            "# Cache Cleanup — Dry-Run Preview",
            "",
            f"**candidates**: {len(candidates)}  **dry_run**: true",
            "",
            "| path | reason |",
            "|---|---|",
        ]
        for c in candidates:
            lines.append(f"| `{c['path']}` | {c['reason']} |")
        lines += ["", f"_generated: {_dt.datetime.utcnow().isoformat()}Z_"]
        md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"lifecycle_trash_v2 cleanup-cache -- dry-run  candidates={len(candidates)}")
        print(f"  output: {json_out}")
        return 0

    # Apply: delete cache dirs/files
    errors: list[str] = []
    actions_taken = 0
    deleted_roots: set[str] = set()

    for cand in candidates:
        rel = cand["path"]
        if _norm(rel) in tracked:
            continue
        abs_p = repo_root / rel
        norm = _norm(rel)

        # Find cache root dir to delete whole tree
        cache_root: pathlib.Path | None = None
        for marker in (".pytest_cache/", "__pycache__/", "/.pytest_cache/", "/__pycache__/"):
            idx = norm.find(marker)
            if idx != -1:
                root_rel = norm[: idx + len(marker)].rstrip("/")
                cache_root = repo_root / root_rel
                break

        if cache_root and str(cache_root) not in deleted_roots:
            deleted_roots.add(str(cache_root))
            if cache_root.exists():
                try:
                    shutil.rmtree(str(cache_root))
                    actions_taken += 1
                except Exception as e:
                    errors.append(f"rmtree error: {cache_root}: {e}")
        elif cache_root is None:
            if abs_p.exists():
                try:
                    if abs_p.is_dir():
                        shutil.rmtree(str(abs_p))
                    else:
                        abs_p.unlink()
                    actions_taken += 1
                except Exception as e:
                    errors.append(f"delete error: {rel}: {e}")

    obj["dry_run"] = False
    obj["actions_taken"] = actions_taken
    obj["errors"] = errors

    (out_dir / "latest_cache_cleanup_result.json").write_text(
        json.dumps(obj, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "latest_cache_cleanup_result.md").write_text(
        f"# Cache Cleanup Result\n\nactions_taken={actions_taken}  errors={len(errors)}\n",
        encoding="utf-8",
    )
    print(
        f"lifecycle_trash_v2 cleanup-cache -- APPLIED"
        f"  deleted={actions_taken}  errors={len(errors)}"
    )
    return 0 if not errors else 1


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Lifecycle trash v2 — controlled automation rollout (Phase 3)."
    )
    sub = p.add_subparsers(dest="subcommand", required=True)

    t = sub.add_parser("trash", help="Move AUTO_SAFE_TEMP files to .lifecycle_trash/")
    t.add_argument("--scope", choices=["changed", "repo"], default="changed")
    t.add_argument("--audit", metavar="PATH", help="Use pre-computed audit JSON")
    t.add_argument("--apply", action="store_true")
    t.add_argument("--confirm-controlled-trash", action="store_true")
    t.add_argument("--root", type=pathlib.Path, default=None,
                   help="Repository root (default: auto-detected)")

    c = sub.add_parser("cleanup-cache", help="Delete cache dirs (pytest_cache/__pycache__/etc)")
    c.add_argument("--apply", action="store_true")
    c.add_argument("--confirm-cache-cleanup", action="store_true")
    c.add_argument("--allow-dirty", action="store_true",
                   help="Skip dirty working tree check (hook use only)")
    c.add_argument("--root", type=pathlib.Path, default=None,
                   help="Repository root (default: auto-detected)")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.subcommand == "trash":
        return cmd_trash(args)
    if args.subcommand == "cleanup-cache":
        return cmd_cleanup_cache(args)
    print(f"Unknown subcommand: {args.subcommand}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
