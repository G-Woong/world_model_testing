"""scripts/lifecycle_audit_v2.py — dry-run lifecycle classification engine.

Policy source:
  docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md §8
  docs/orchestration/15_lifecycle_automation_v2_plan.md §4
  docs/orchestration/14_REPORT_LIFECYCLE_POLICY.md §2

Phase 1: dry-run only. No --apply. No subprocess. No file moves or deletes.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import enum
import json
import os
import pathlib
import re
import sys

CLASSIFIER_VERSION = "v2.0.0-phase1"

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# §7 Protected directories — any file underneath is PROTECTED
_PROTECTED_DIRS = (
    "paper_context_ref",
    "src/frcgw",
    "tests",
    "configs",
    "outputs/phase_gates",
    "outputs/runs/p3_lr_eval",
    "outputs/runs/p3_ablations",
    "outputs/runs/p3_lr_smoke",
    "docs/orchestration/lr_alignment/evidence_cards",
    ".claude",
    ".self_evolving_memory",
)

# §7 Protected exact relative paths
_PROTECTED_EXACT = (
    "scripts/run_codex_task.ps1",
    "scripts/apply_reviewed_cleanup.ps1",
    "scripts/audit_stale_reports.py",
    "docs/orchestration/lr_alignment/12_run6_lr_eval_report.md",
    "docs/orchestration/lr_alignment/13_claim_survivability_decision_report.md",
    "plans/PHASE_PROGRESS.md",
    "CLAUDE.md",
    "CLAUDE.local.md",
    ".mcp.json",
    ".agent_tasks/codex_prompt_template.md",
)

# Scope walk exclusions — never classify files under these prefixes
EXCLUDE_PREFIXES = (
    ".git/",
    ".venv/",
    ".venv.bak.20260516/",
    "node_modules/",
    "data/",
    ".lifecycle_trash/",
    "outputs/lifecycle/",
)

# Manual-only source directories
_MANUAL_DIRS = (
    "docs/orchestration/session_reports",
    "docs/orchestration/decision_logs",
    ".agent_tasks/codex_done",
)

# Manual-only exact basenames (근거 artifact — preview only)
_MANUAL_BASENAMES = frozenset({
    "final_cleanup_plan.json",
    "final_cleanup_plan.md",
    "candidate_manifest.json",
    "candidate_manifest.md",
    "human_decision_template.csv",
    "cleanup_commands_preview.ps1",
})


class Classification(str, enum.Enum):
    PROTECTED = "PROTECTED"
    AUTO_SAFE_CACHE = "AUTO_SAFE_CACHE"
    AUTO_SAFE_TEMP = "AUTO_SAFE_TEMP"
    ARCHIVE_READY = "ARCHIVE_READY"
    MANUAL_ONLY = "MANUAL_ONLY"
    UNKNOWN = "UNKNOWN"


_RISK: dict[Classification, str] = {
    Classification.PROTECTED: "critical",
    Classification.AUTO_SAFE_CACHE: "low",
    Classification.AUTO_SAFE_TEMP: "low",
    Classification.ARCHIVE_READY: "medium",
    Classification.MANUAL_ONLY: "medium",
    Classification.UNKNOWN: "medium",
}

_ACTION: dict[Classification, str] = {
    Classification.PROTECTED: "none",
    Classification.AUTO_SAFE_CACHE: "preview_delete_cache",
    Classification.AUTO_SAFE_TEMP: "preview_delete_cache",
    Classification.ARCHIVE_READY: "preview_archive",
    Classification.MANUAL_ONLY: "manual_review",
    Classification.UNKNOWN: "manual_review",
}


@dataclasses.dataclass(frozen=True)
class Candidate:
    path: str
    classification: Classification
    reason: str
    risk_level: str
    allowed_action: str
    protected: bool


def _norm(p: str) -> str:
    return p.replace("\\", "/")


def _under_dir(prefix: str, rel: str) -> bool:
    n = _norm(rel)
    p = _norm(prefix)
    return n == p or n.startswith(p + "/")


# ── Classification predicates ────────────────────────────────────────────────

def _is_protected(rel: str) -> tuple[bool, str]:
    norm = _norm(rel)
    for d in _PROTECTED_DIRS:
        if _under_dir(d, rel):
            return True, f"matched protected dir: {d}/**"
    for f in _PROTECTED_EXACT:
        if norm == _norm(f):
            return True, f"matched protected file: {f}"
    # docs/orchestration/NN_*.md where NN in 00..14
    m = re.match(r"docs/orchestration/(\d{2})_", norm)
    if m and 0 <= int(m.group(1)) <= 14:
        return True, f"matched protected: docs/orchestration/{int(m.group(1)):02d}_*.md (00-14)"
    return False, ""


def _is_auto_safe_cache(rel: str) -> tuple[bool, str]:
    norm = _norm(rel)
    if norm.startswith(".pytest_cache/") or "/.pytest_cache/" in norm:
        return True, "matched: .pytest_cache in path"
    if norm.startswith("__pycache__/") or "/__pycache__/" in norm:
        return True, "matched: __pycache__ in path"
    if _under_dir("src/frcgw.egg-info", rel):
        return True, "matched: src/frcgw.egg-info/**"
    if norm.endswith(".pyc") or norm.endswith(".pyo"):
        return True, "matched: compiled Python artifact (.pyc/.pyo)"
    return False, ""


def _is_auto_safe_temp(rel: str) -> tuple[bool, str]:
    norm = _norm(rel)
    if "cleanup_audit" in norm and "review_copies" in norm:
        return True, "matched: cleanup_audit/review_copies staging area"
    if norm == "outputs/cleanup_audit_temp.json":
        return True, "matched: cleanup_audit_temp.json staging file"
    return False, ""


def _is_archive_ready(rel: str, repo_root: pathlib.Path) -> tuple[bool, str]:
    norm = _norm(rel)
    if not re.match(r"plans/P\d+.*\.md$", norm, re.IGNORECASE):
        return False, ""
    if "PHASE_PROGRESS" in norm:
        return False, ""
    m = re.match(r"plans/P(\d+)", norm)
    if m:
        phase = int(m.group(1))
        gate = repo_root / "outputs" / "phase_gates" / f"P{phase}.passed"
        if gate.exists():
            return True, f"phase gate sentinel exists: P{phase}.passed"
    return False, ""


def _is_manual_only(rel: str) -> tuple[bool, str]:
    norm = _norm(rel)
    for d in _MANUAL_DIRS:
        if _under_dir(d, rel):
            return True, f"matched manual-only dir: {d}/**"
    if re.match(r"docs/orchestration/PHASE\d+_GATE_REPORT\.md", norm):
        return True, "matched: PHASE gate report (manual review required)"
    # lifecycle v2 plans 15-19
    m = re.match(r"docs/orchestration/(1[5-9])_.*\.md$", norm)
    if m:
        return True, f"matched: docs/orchestration/{m.group(1)}_*.md (lifecycle v2 plan, manual review)"
    basename = norm.rsplit("/", 1)[-1]
    if basename in _MANUAL_BASENAMES:
        return True, f"matched: manual-only artifact: {basename}"
    return False, ""


# ── Public classifier ────────────────────────────────────────────────────────

def classify_path(rel: str, repo_root: pathlib.Path) -> Candidate:
    """Classify one relative path. Priority: PROTECTED > CACHE > TEMP > ARCHIVE > MANUAL > UNKNOWN."""
    for check, cls in (
        (_is_protected(rel), Classification.PROTECTED),
        (_is_auto_safe_cache(rel), Classification.AUTO_SAFE_CACHE),
        (_is_auto_safe_temp(rel), Classification.AUTO_SAFE_TEMP),
    ):
        hit, reason = check
        if hit:
            return Candidate(
                path=rel, classification=cls, reason=reason,
                risk_level=_RISK[cls], allowed_action=_ACTION[cls],
                protected=(cls is Classification.PROTECTED),
            )

    hit, reason = _is_archive_ready(rel, repo_root)
    if hit:
        cls = Classification.ARCHIVE_READY
        return Candidate(path=rel, classification=cls, reason=reason,
                         risk_level=_RISK[cls], allowed_action=_ACTION[cls], protected=False)

    hit, reason = _is_manual_only(rel)
    if hit:
        cls = Classification.MANUAL_ONLY
        return Candidate(path=rel, classification=cls, reason=reason,
                         risk_level=_RISK[cls], allowed_action=_ACTION[cls], protected=False)

    cls = Classification.UNKNOWN
    return Candidate(path=rel, classification=cls, reason="no rule matched",
                     risk_level=_RISK[cls], allowed_action=_ACTION[cls], protected=False)


# ── Path collection ──────────────────────────────────────────────────────────

def _is_excluded(rel: str) -> bool:
    norm = _norm(rel)
    return any(norm.startswith(_norm(p)) for p in EXCLUDE_PREFIXES)


def _collect_repo(repo_root: pathlib.Path) -> list[str]:
    results: list[str] = []
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(repo_root).as_posix()
        except ValueError:
            continue
        if not _is_excluded(rel):
            results.append(rel)
    return sorted(results)


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
        if not _is_excluded(rel):
            paths.append(rel)
    return sorted(paths)


# ── Output rendering ─────────────────────────────────────────────────────────

def _counts(candidates: list[Candidate]) -> dict[str, int]:
    c: dict[str, int] = {cls.value: 0 for cls in Classification}
    for cand in candidates:
        c[cand.classification.value] += 1
    return c


def _to_dict(c: Candidate) -> dict:
    return {
        "path": c.path,
        "classification": c.classification.value,
        "reason": c.reason,
        "risk_level": c.risk_level,
        "allowed_action": c.allowed_action,
        "protected": c.protected,
    }


def _json_obj(candidates: list[Candidate], scope: str) -> dict:
    return {
        "dry_run": True,
        "scope": scope,
        "actions_taken": 0,
        "counts": _counts(candidates),
        "candidates": [_to_dict(c) for c in candidates],
        "classifier_version": CLASSIFIER_VERSION,
        "audit_ts_utc": _dt.datetime.utcnow().isoformat() + "Z",
    }


def _md_report(candidates: list[Candidate], scope: str, cnts: dict[str, int]) -> str:
    lines = [
        "# Lifecycle Audit v2 — Dry-Run Report",
        "",
        f"**scope**: `{scope}`  **classifier**: `{CLASSIFIER_VERSION}`  "
        "**actions_taken**: 0  **dry_run**: true",
        "",
        "## Counts",
        "",
        "| Classification | Count |",
        "|---|---|",
    ]
    for cls_name, cnt in sorted(cnts.items()):
        lines.append(f"| {cls_name} | {cnt} |")
    lines += [
        "",
        "## Candidates",
        "",
        "| path | class | risk | action | reason |",
        "|---|---|---|---|---|",
    ]
    for c in candidates:
        lines.append(
            f"| `{c.path}` | {c.classification.value} | {c.risk_level}"
            f" | {c.allowed_action} | {c.reason} |"
        )
    lines += ["", f"_generated: {_dt.datetime.utcnow().isoformat()}Z_"]
    return "\n".join(lines) + "\n"


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Lifecycle audit v2 - dry-run classification engine. "
            "Policy: docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md"
        )
    )
    p.add_argument(
        "--dry-run", action="store_true", default=True,
        help="Dry-run mode (default and only mode in Phase 1).",
    )
    p.add_argument(
        "--scope", choices=["changed", "repo"], default="repo",
        help=(
            "changed: uses LIFECYCLE_AUDIT_CHANGED_PATHS env var (fallback to repo). "
            "repo: full repository walk."
        ),
    )
    p.add_argument("--json", action="store_true", dest="json_out",
                   help="Print JSON summary to stdout.")
    p.add_argument("--root", type=pathlib.Path, default=REPO_ROOT,
                   help="Repository root (default: auto-detected from script location).")
    p.add_argument("--apply", action="store_true", help=argparse.SUPPRESS)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.apply:
        print(
            "--apply is not implemented in Phase 1. "
            "See docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md §Phase-G.",
            file=sys.stderr,
        )
        return 2

    repo_root = args.root.resolve()

    if args.scope == "changed":
        paths = _collect_changed(repo_root)
        scope_label = "changed"
    else:
        paths = _collect_repo(repo_root)
        scope_label = "repo"

    candidates = [classify_path(rel, repo_root) for rel in paths]
    cnts = _counts(candidates)

    obj = _json_obj(candidates, scope_label)
    md = _md_report(candidates, scope_label, cnts)

    out_dir = repo_root / "outputs" / "lifecycle"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest_audit.json").write_text(
        json.dumps(obj, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "latest_audit.md").write_text(md, encoding="utf-8")

    if args.json_out:
        sys.stdout.write(json.dumps(obj, indent=2) + "\n")
    else:
        print(
            f"lifecycle_audit_v2 -- dry-run  scope={scope_label}"
            f"  files={len(candidates)}  actions=0"
        )
        for cls_name, cnt in sorted(cnts.items()):
            if cnt > 0:
                print(f"  {cls_name}: {cnt}")
        print(f"  output: {out_dir / 'latest_audit.json'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
