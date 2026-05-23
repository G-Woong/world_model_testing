"""scripts/audit_stale_reports.py — dry-run audit of stale report candidates.

Policy source: docs/orchestration/14_REPORT_LIFECYCLE_POLICY.md
Read-only by contract. No --apply available in this round.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import enum
import json
import pathlib
import re
import sys

REPO_ROOT_HINT = pathlib.Path(__file__).resolve().parent.parent

CANDIDATE_PATTERNS = (
    "plans/*PLAN*.md",
    "plans/*_GATE_REPORT.md",
    "plans/*PROGRESS*.md",
    "plans/*HANDOFF*.md",
    "plans/PLUGIN_AUDIT_REPORT.md",
    "plans/codex/*.md",
    "docs/orchestration/PHASE*_GATE_REPORT.md",
    "docs/orchestration/session_reports/*/*.md",
    "docs/orchestration/decision_logs/*/session_*.md",
    ".agent_tasks/codex_done/*_RESULT.md",
)

EXCLUDE_PATH_PREFIXES = (
    "paper_context_ref/",
    ".venv/",
    ".venv.bak.20260516/",
    "node_modules/",
    ".git/",
    "docs/orchestration/archive/",
    "plans/archive/",
)

EXCLUDE_NAME_PATTERNS = ("_TEMPLATE", "INDEX.md")


class Category(str, enum.Enum):
    PLAN = "PLAN"
    GATE_REPORT = "GATE_REPORT"
    PROGRESS = "PROGRESS"
    SESSION = "SESSION"
    DECISION = "DECISION"
    RESULT = "RESULT"
    HANDOFF = "HANDOFF"
    OTHER = "OTHER"


@dataclasses.dataclass(frozen=True)
class Candidate:
    abs_path: pathlib.Path
    rel_path: str
    size_bytes: int
    mtime_iso: str
    category: Category
    sentinel_hint: str | None
    ssot_absorbed: str  # YES / NO / UNKNOWN / NEEDS_REVIEW / NEVER


def classify(rel_path: str) -> Category:
    p = rel_path.replace("\\", "/").lower()
    if "codex_done" in p and "_result.md" in p:
        return Category.RESULT
    if "session_reports" in p:
        return Category.SESSION
    if "decision_logs" in p and "session_" in p:
        return Category.DECISION
    if "gate_report" in p:
        return Category.GATE_REPORT
    if "handoff" in p:
        return Category.HANDOFF
    if "progress" in p:
        return Category.PROGRESS
    if "plan" in p:
        return Category.PLAN
    return Category.OTHER


def _load_sentinels(repo_root: pathlib.Path) -> list[pathlib.Path]:
    gates_dir = repo_root / "outputs" / "phase_gates"
    if not gates_dir.exists():
        return []
    return sorted(gates_dir.glob("*.passed"))


def sentinel_for(rel_path: str, repo_root: pathlib.Path) -> str | None:
    gates = _load_sentinels(repo_root)
    norm = rel_path.replace("\\", "/")
    for gate in gates:
        stem = gate.stem
        pat = r"(?<=[/_\-])" + re.escape(stem) + r"(?=[_.\-/]|$)"
        if re.search(pat, norm, re.IGNORECASE):
            return gate.relative_to(repo_root).as_posix()
    return None


def ssot_absorption(category: Category, rel_path: str, repo_root: pathlib.Path) -> str:
    if "PHASE_PROGRESS" in rel_path:
        return "NEVER"
    for pat in EXCLUDE_NAME_PATTERNS:
        if pat in rel_path:
            return "NEVER"
    s = sentinel_for(rel_path, repo_root)
    if s and (repo_root / s).exists():
        return "YES"
    if category in (Category.RESULT, Category.SESSION, Category.DECISION):
        return "NEEDS_REVIEW"
    return "UNKNOWN"


def is_excluded(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/")
    for prefix in EXCLUDE_PATH_PREFIXES:
        if norm.startswith(prefix):
            return True
    for pat in EXCLUDE_NAME_PATTERNS:
        if pat in rel_path:
            return True
    return False


def find_candidates(
    repo_root: pathlib.Path, only_category: Category | None
) -> list[Candidate]:
    seen: set[str] = set()
    result: list[Candidate] = []
    for pattern in CANDIDATE_PATTERNS:
        for path in repo_root.glob(pattern):
            if not path.is_file():
                continue
            try:
                rel = path.relative_to(repo_root).as_posix()
            except ValueError:
                continue
            if is_excluded(rel):
                continue
            if rel in seen:
                continue
            cat = classify(rel)
            if only_category is not None and cat != only_category:
                continue
            seen.add(rel)
            st = path.stat()
            result.append(
                Candidate(
                    abs_path=path,
                    rel_path=rel,
                    size_bytes=st.st_size,
                    mtime_iso=_dt.datetime.fromtimestamp(st.st_mtime)
                    .date()
                    .isoformat(),
                    category=cat,
                    sentinel_hint=sentinel_for(rel, repo_root),
                    ssot_absorbed=ssot_absorption(cat, rel, repo_root),
                )
            )
    return sorted(result, key=lambda c: (c.category.value, c.rel_path))


def render_text(
    candidates: list[Candidate],
    archive_dir_hint: pathlib.Path,
    repo_root: pathlib.Path,
) -> str:
    per_cat: dict[str, int] = {}
    rows: list[str] = []
    for c in candidates:
        per_cat[c.category.value] = per_cat.get(c.category.value, 0) + 1
        sentinel_str = f"  sentinel={c.sentinel_hint}" if c.sentinel_hint else ""
        tag = f"[{c.category.value}]"
        rows.append(
            f"{tag:<12}  {c.rel_path:<55}  {c.size_bytes:>7} B  {c.mtime_iso}"
            f"  ssot={c.ssot_absorbed}{sentinel_str}"
        )
    lines = [
        "audit_stale_reports.py -- dry-run, no actions taken",
        f"repo_root        : {repo_root}",
        f"archive_dir_hint : {archive_dir_hint}",
        "",
        *rows,
        "",
        "per_category: "
        + "  ".join(f"{k}:{v}" for k, v in sorted(per_cat.items())),
        f"total candidates :  {len(candidates)}",
        "actions taken    :   0   (dry-run only; --apply unavailable)",
    ]
    return "\n".join(lines) + "\n"


def render_json(
    candidates: list[Candidate],
    archive_dir_hint: pathlib.Path,
) -> str:
    per_cat: dict[str, int] = {}
    for c in candidates:
        per_cat[c.category.value] = per_cat.get(c.category.value, 0) + 1
    data = {
        "dry_run": True,
        "actions_taken": 0,
        "count": len(candidates),
        "archive_dir_hint": str(archive_dir_hint),
        "per_category": per_cat,
        "candidates": [
            {
                "rel_path": c.rel_path,
                "size_bytes": c.size_bytes,
                "mtime_iso": c.mtime_iso,
                "category": c.category.value,
                "sentinel_hint": c.sentinel_hint,
                "ssot_absorbed": c.ssot_absorbed,
            }
            for c in candidates
        ],
    }
    return json.dumps(data, indent=2) + "\n"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Dry-run audit per 14_REPORT_LIFECYCLE_POLICY.md"
    )
    p.add_argument("--root", type=pathlib.Path, default=REPO_ROOT_HINT)
    p.add_argument("--json", action="store_true", dest="json_out")
    p.add_argument("--archive-dir", type=pathlib.Path, default=None)
    p.add_argument(
        "--category",
        choices=[c.value for c in Category if c is not Category.OTHER],
    )
    p.add_argument("--no-git-check", action="store_true")
    p.add_argument("--apply", action="store_true", help=argparse.SUPPRESS)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.apply:
        print(
            "--apply intentionally not implemented"
            " (see 14_REPORT_LIFECYCLE_POLICY.md §6)",
            file=sys.stderr,
        )
        return 2
    repo_root = args.root.resolve()
    if not args.no_git_check and not (repo_root / ".git").exists():
        print(f"warning: {repo_root} not a git repo", file=sys.stderr)
    archive_hint = args.archive_dir or (
        repo_root
        / "docs"
        / "orchestration"
        / "archive"
        / _dt.date.today().strftime("%Y-%m")
    )
    only_cat = Category(args.category) if args.category else None
    candidates = find_candidates(repo_root, only_cat)
    if args.json_out:
        sys.stdout.write(render_json(candidates, archive_hint))
    else:
        sys.stdout.write(render_text(candidates, archive_hint, repo_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
