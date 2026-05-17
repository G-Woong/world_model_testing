"""scripts/archive_sweep_v2.py — rule-based archive sweep engine (Phase 5).

Policy source:
  docs/orchestration/14_REPORT_LIFECYCLE_POLICY.md §3.5
  docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md §Phase G
  .self_evolving_memory/decisions/decision_memory.yaml DEC-003

Subcommands:
  sweep   -- scan ARCHIVE_READY files and optionally git mv them
  restore -- shim (use git mv manually for now)

Exit codes:
  0  success
  1  one or more file errors (best-effort, others moved)
  2  --apply used without --confirm-auto-archive
  3  destination safety violation
  4  dirty/staged conflict blocked apply
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys

MANIFEST_SCHEMA_VERSION = "1.1.0"
MAX_FILES = 50
MAX_BYTES = 5 * 1024 * 1024  # 5 MB per file

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_ARCHIVE_MONTH = "2026-05"  # current archiving epoch

# Destination mapping per rule
_RULE_DESTINATIONS: dict[str, str] = {
    "rule_a": f"plans/archive/{_ARCHIVE_MONTH}",
    "rule_b": f"docs/orchestration/archive/{_ARCHIVE_MONTH}",
    "rule_c": f".agent_tasks/archive/{_ARCHIVE_MONTH}/codex_done",
    "rule_d": f".agent_tasks/archive/{_ARCHIVE_MONTH}/p3_impl",
    "rule_e": f"docs/orchestration/archive/{_ARCHIVE_MONTH}/session_reports",
}

# Self-evolving status per rule (lightweight; no text extraction)
_RULE_STATUS: dict[str, str] = {
    "rule_a": "no_value_remaining",
    "rule_b": "no_value_remaining",
    "rule_c": "no_value_remaining",
    "rule_d": "no_value_remaining",
    "rule_e": "extract_then_archive",
}

_RULE_ABSORBED_BY: dict[str, str] = {
    "rule_a": "plans/PHASE_PROGRESS.md",
    "rule_b": "docs/orchestration/decision_logs or plans/PHASE_PROGRESS.md",
    "rule_c": "docs/orchestration/session_reports latest or paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP.md",
    "rule_d": "paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP.md",
    "rule_e": "docs/orchestration/session_reports latest precompact_handoff",
}


# ── Module loading ─────────────────────────────────────────────────────────────

def _load_audit_mod():
    script = REPO_ROOT / "scripts" / "lifecycle_audit_v2.py"
    spec = importlib.util.spec_from_file_location("lifecycle_audit_v2", script)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lifecycle_audit_v2"] = mod
    spec.loader.exec_module(mod)
    return mod


# ── Rule detection ─────────────────────────────────────────────────────────────

def _norm(p: str) -> str:
    return p.replace("\\", "/")


def _detect_rule(rel: str, repo_root: pathlib.Path) -> str | None:
    """Return 'rule_a'..'rule_e' or None if not ARCHIVE_READY."""
    norm = _norm(rel)
    basename = norm.rsplit("/", 1)[-1]

    # Rule A: plans/P<N>*.md with gate sentinel
    if re.match(r"plans/P\d+.*\.md$", norm, re.IGNORECASE) and "PHASE_PROGRESS" not in norm:
        m = re.match(r"plans/P(\d+)", norm)
        if m:
            phase = int(m.group(1))
            if (repo_root / "outputs" / "phase_gates" / f"P{phase}.passed").exists():
                return "rule_a"

    # Rule B: docs/orchestration/PHASE<N>_GATE_REPORT.md
    if re.match(r"docs/orchestration/PHASE\w+_GATE_REPORT\.md$", norm):
        return "rule_b"

    # Rule C: .agent_tasks/codex_done/TASK_*_RESULT.md
    if re.match(r"\.agent_tasks/codex_done/TASK_\d+.*_RESULT\.md$", norm):
        return "rule_c"

    # Rule D: .agent_tasks/codex_archive/**/*.md
    if norm.startswith(".agent_tasks/codex_archive/") and norm.endswith(".md"):
        return "rule_d"

    # Rule E: superseded precompact_handoff
    if re.match(r"docs/orchestration/session_reports/\d{4}-\d{2}/.*_precompact_handoff\.md$", norm):
        folder = (repo_root / norm).parent
        if folder.is_dir():
            candidates = sorted(p.name for p in folder.glob("*_precompact_handoff.md"))
            if candidates and basename != candidates[-1]:
                return "rule_e"

    return None


def _destination(rel: str, rule: str) -> str:
    basename = _norm(rel).rsplit("/", 1)[-1]
    dest_dir = _RULE_DESTINATIONS[rule]
    return f"{dest_dir}/{basename}"


# ── Safety gates ───────────────────────────────────────────────────────────────

def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_git_tracked(rel: str, repo_root: pathlib.Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", rel],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def _is_staged(rel: str, repo_root: pathlib.Path) -> bool:
    """Return True if file has staged changes (user is actively working on it)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=10,
        )
        staged = {_norm(p.strip()) for p in result.stdout.splitlines() if p.strip()}
        return _norm(rel) in staged
    except Exception:
        return False


def _dest_under_archive(dest: str) -> bool:
    return "archive/" in _norm(dest)


def _no_path_traversal(dest: str, repo_root: pathlib.Path) -> bool:
    try:
        abs_dest = (repo_root / dest).resolve()
        abs_dest.relative_to(repo_root.resolve())
        return True
    except ValueError:
        return False


def _safety_check(rel: str, dest: str, src_path: pathlib.Path, repo_root: pathlib.Path) -> str | None:
    """Return error string or None if safe."""
    if not _dest_under_archive(dest):
        return f"destination not under archive/: {dest}"
    if not _no_path_traversal(dest, repo_root):
        return f"path traversal detected: {dest}"
    if src_path.is_symlink():
        return f"symlink blocked: {rel}"
    if _is_staged(rel, repo_root):
        return f"file is staged (user work in progress): {rel}"
    size = src_path.stat().st_size
    if size > MAX_BYTES:
        return f"file too large ({size} > {MAX_BYTES}): {rel}"
    return None


# ── Path collection ────────────────────────────────────────────────────────────

def _collect_changed(repo_root: pathlib.Path) -> list[str]:
    env = os.environ.get("LIFECYCLE_AUDIT_CHANGED_PATHS", "").strip()
    if not env:
        return _collect_repo(repo_root)
    paths: list[str] = []
    for raw in env.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        p = pathlib.Path(raw)
        if p.is_absolute():
            try:
                rel = p.relative_to(repo_root).as_posix()
            except ValueError:
                continue
        else:
            rel = _norm(raw)
        paths.append(rel)
    return sorted(set(paths))


def _collect_repo(repo_root: pathlib.Path) -> list[str]:
    exclude = (
        ".git/", ".venv/", "node_modules/", "data/",
        ".lifecycle_trash/", "outputs/lifecycle/",
    )
    results: list[str] = []
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(repo_root).as_posix()
        except ValueError:
            continue
        if any(_norm(rel).startswith(_norm(e)) for e in exclude):
            continue
        results.append(rel)
    return sorted(results)


# ── Apply logic ────────────────────────────────────────────────────────────────

def _git_mv(src: str, dst: str, repo_root: pathlib.Path) -> None:
    dst_path = repo_root / dst
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "mv", src, dst],
        check=True, capture_output=True, timeout=30,
    )


def _shutil_mv(src_path: pathlib.Path, dst_path: pathlib.Path) -> None:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.move(str(src_path), str(dst_path))


# ── Main sweep logic ──────────────────────────────────────────────────────────

def sweep(
    scope: str,
    dry_run: bool,
    confirm: bool,
    repo_root: pathlib.Path,
) -> int:
    if not dry_run and not confirm:
        print("ERROR: --apply requires --confirm-auto-archive flag.", file=sys.stderr)
        return 2

    audit_mod = _load_audit_mod()
    classify_path = audit_mod.classify_path
    Classification = audit_mod.Classification

    if scope == "changed":
        paths = _collect_changed(repo_root)
    else:
        paths = _collect_repo(repo_root)

    # Filter ARCHIVE_READY
    candidates = []
    for rel in paths:
        src_path = repo_root / rel
        if not src_path.exists() or src_path.is_dir():
            continue
        cand = classify_path(rel, repo_root)
        if cand.classification is not Classification.ARCHIVE_READY:
            continue
        rule = _detect_rule(rel, repo_root)
        if rule is None:
            continue
        candidates.append((rel, rule))

    if len(candidates) > MAX_FILES:
        print(
            f"ERROR: {len(candidates)} ARCHIVE_READY files exceeds MAX_FILES={MAX_FILES}. "
            "Run with --scope changed or raise MAX_FILES.",
            file=sys.stderr,
        )
        return 1

    run_id = f"run_{_dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}"
    files_out = []
    errors = []

    for rel, rule in candidates:
        src_path = repo_root / rel
        dest = _destination(rel, rule)
        dest_path = repo_root / dest

        err = _safety_check(rel, dest, src_path, repo_root)
        if err:
            errors.append({"path": rel, "error": err})
            continue

        sha_before = _sha256(src_path)
        tracked = _is_git_tracked(rel, repo_root)

        entry = {
            "original_path": rel,
            "archive_path": dest,
            "category": f"plans_phase_gate_passed" if rule == "rule_a" else rule,
            "archive_reason": _rule_reason(rule, rel, repo_root),
            "absorbed_by": _RULE_ABSORBED_BY[rule],
            "claim_relation": None,
            "self_evolving_summary_status": _RULE_STATUS[rule],
            "sha256_before": sha_before,
            "sha256_after": None,
            "size_bytes": src_path.stat().st_size,
            "git_tracked": tracked,
            "move_method": "git_mv" if tracked else "shutil_move",
            "auto_archived": not dry_run,
            "restore_command": f"git mv {dest} {rel}",
        }

        if not dry_run:
            try:
                if tracked:
                    _git_mv(rel, dest, repo_root)
                else:
                    _shutil_mv(src_path, dest_path)
                if dest_path.exists():
                    entry["sha256_after"] = _sha256(dest_path)
                    if entry["sha256_after"] != sha_before:
                        errors.append({"path": rel, "error": "sha256 mismatch after move"})
                        continue
            except Exception as exc:
                errors.append({"path": rel, "error": str(exc)})
                entry["auto_archived"] = False

        files_out.append(entry)

    # Write manifest
    manifest = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "run_id": run_id,
        "scope": scope,
        "dry_run": dry_run,
        "actions_taken": sum(1 for e in files_out if e.get("auto_archived")),
        "classifier_version": audit_mod.CLASSIFIER_VERSION,
        "policy": {
            "max_files": MAX_FILES,
            "max_bytes": MAX_BYTES,
            "allowed_classifications": ["ARCHIVE_READY"],
        },
        "files": files_out,
        "protected_skipped": [],
        "manual_skipped": [],
        "unknown_skipped": [],
        "errors": errors,
    }

    out_dir = repo_root / "outputs" / "lifecycle"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "archive_sweep_latest.json"
    json_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Archive Sweep v2 — Manifest",
        "",
        f"**run_id**: `{run_id}`  **scope**: `{scope}`  "
        f"**dry_run**: `{dry_run}`  **actions_taken**: `{manifest['actions_taken']}`",
        "",
        "## Files",
        "",
        "| original_path | archive_path | rule | status |",
        "|---|---|---|---|",
    ]
    for e in files_out:
        rule_label = e.get("archive_reason", "")[:40]
        status = "MOVED" if e.get("auto_archived") else ("DRY-RUN" if dry_run else "FAILED")
        md_lines.append(
            f"| `{e['original_path']}` | `{e['archive_path']}` | {rule_label} | {status} |"
        )
    if errors:
        md_lines += ["", "## Errors", ""]
        for err in errors:
            md_lines.append(f"- `{err['path']}`: {err['error']}")
    md_lines += ["", f"_generated: {_dt.datetime.utcnow().isoformat()}Z_"]

    md_path = out_dir / "archive_sweep_latest.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # Console summary
    moved = manifest["actions_taken"]
    total = len(files_out)
    print(
        f"archive_sweep_v2 -- scope={scope}  dry_run={dry_run}  "
        f"candidates={total}  moved={moved}  errors={len(errors)}"
    )
    if dry_run and total > 0:
        print("  (pass --apply --confirm-auto-archive to execute moves)")
    for err in errors:
        print(f"  ERROR: {err['path']}: {err['error']}", file=sys.stderr)

    return 0 if not errors else 1


def _rule_reason(rule: str, rel: str, repo_root: pathlib.Path) -> str:
    norm = _norm(rel)
    if rule == "rule_a":
        m = re.match(r"plans/P(\d+)", norm)
        phase = m.group(1) if m else "?"
        return f"phase gate sentinel exists: P{phase}.passed"
    if rule == "rule_b":
        return "PHASE gate report (historical, auto-archive eligible)"
    if rule == "rule_c":
        return "completed codex task result (auto-archive eligible)"
    if rule == "rule_d":
        return "codex_archive dir (auto-archive under date)"
    if rule == "rule_e":
        folder = (repo_root / norm).parent
        if folder.is_dir():
            candidates = sorted(p.name for p in folder.glob("*_precompact_handoff.md"))
            latest = candidates[-1] if candidates else "unknown"
        else:
            latest = "unknown"
        return f"superseded precompact handoff (latest: {latest})"
    return "unknown rule"


# ── CLI ────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="archive_sweep_v2 — rule-based ARCHIVE_READY git mv engine (Phase 5)"
    )
    sub = p.add_subparsers(dest="cmd")

    sw = sub.add_parser("sweep", help="Scan and optionally archive ARCHIVE_READY files")
    sw.add_argument("--dry-run", action="store_true", default=True)
    sw.add_argument("--apply", action="store_true", dest="apply")
    sw.add_argument("--scope", choices=["changed", "repo"], default="changed")
    sw.add_argument(
        "--confirm-auto-archive", action="store_true", dest="confirm",
        help="Required safety gate when using --apply",
    )
    sw.add_argument("--root", type=pathlib.Path, default=REPO_ROOT)

    rs = sub.add_parser("restore", help="Restore shim — use git mv manually")
    rs.add_argument("archive_path", nargs="?")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.cmd == "restore":
        print(
            "restore shim: use `git mv <archive_path> <original_path>` directly, "
            "or check outputs/lifecycle/archive_sweep_latest.json for restore_command entries.",
            file=sys.stderr,
        )
        return 0

    if args.cmd != "sweep":
        build_parser().print_help()
        return 0

    dry_run = not args.apply
    return sweep(
        scope=args.scope,
        dry_run=dry_run,
        confirm=args.confirm,
        repo_root=args.root.resolve(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
