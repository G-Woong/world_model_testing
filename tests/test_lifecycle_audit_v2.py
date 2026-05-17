"""tests/test_lifecycle_audit_v2.py — contract tests for lifecycle_audit_v2.py.

Verifies the 10-item classification contract + no-subprocess + no-destructive-API.
Policy: docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md §8
"""
from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

_SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "lifecycle_audit_v2.py"


def _load_mod():
    import sys as _sys
    spec = importlib.util.spec_from_file_location("lifecycle_audit_v2", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    _sys.modules["lifecycle_audit_v2"] = mod  # required for dataclasses __module__ lookup
    spec.loader.exec_module(mod)
    return mod


_mod = _load_mod()
classify_path = _mod.classify_path
Classification = _mod.Classification
main = _mod.main
REPO_ROOT = _mod.REPO_ROOT


# ── Test 1 ───────────────────────────────────────────────────────────────────
def test_paper_context_ref_protected():
    c = classify_path("paper_context_ref/03_CORE_CONCEPT_TAXONOMY.md", REPO_ROOT)
    assert c.classification == Classification.PROTECTED


# ── Test 2 ───────────────────────────────────────────────────────────────────
def test_src_frcgw_protected():
    c = classify_path("src/frcgw/schemas/visibility.py", REPO_ROOT)
    assert c.classification == Classification.PROTECTED


# ── Test 3 ───────────────────────────────────────────────────────────────────
def test_pycache_auto_safe_cache():
    c = classify_path("__pycache__/foo.pyc", REPO_ROOT)
    assert c.classification == Classification.AUTO_SAFE_CACHE


# ── Test 4 ───────────────────────────────────────────────────────────────────
def test_pytest_cache_auto_safe_cache():
    c = classify_path(".pytest_cache/v/cache/lastfailed", REPO_ROOT)
    assert c.classification == Classification.AUTO_SAFE_CACHE


# ── Test 5 ───────────────────────────────────────────────────────────────────
def test_phase_progress_protected():
    c = classify_path("plans/PHASE_PROGRESS.md", REPO_ROOT)
    assert c.classification == Classification.PROTECTED


# ── Test 6 ───────────────────────────────────────────────────────────────────
def test_evidence_cards_protected():
    c = classify_path(
        "docs/orchestration/lr_alignment/evidence_cards/c3_falsification.md",
        REPO_ROOT,
    )
    assert c.classification == Classification.PROTECTED


# ── Test 7 ───────────────────────────────────────────────────────────────────
def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_apply_exits_two(capsys):
    result = main(["--apply"])
    assert result == 2


# ── Test 8 ───────────────────────────────────────────────────────────────────
def test_json_output_required_fields(tmp_path):
    (tmp_path / "outputs" / "lifecycle").mkdir(parents=True)

    rc = main(["--dry-run", "--scope", "repo", "--json", "--root", str(tmp_path)])
    assert rc == 0

    data = json.loads(
        (tmp_path / "outputs" / "lifecycle" / "latest_audit.json").read_text(encoding="utf-8")
    )
    required = {"dry_run", "scope", "actions_taken", "counts", "candidates", "classifier_version"}
    assert required.issubset(data.keys()), f"missing fields: {required - data.keys()}"
    assert data["dry_run"] is True
    assert data["actions_taken"] == 0


# ── Test 9 ───────────────────────────────────────────────────────────────────
def test_archive_ready_no_actions(tmp_path):
    gate_dir = tmp_path / "outputs" / "phase_gates"
    gate_dir.mkdir(parents=True)
    (gate_dir / "P1.passed").write_bytes(b"")

    c = classify_path("plans/P1_PLAN.md", tmp_path)
    assert c.classification == Classification.ARCHIVE_READY
    assert c.allowed_action == "auto_archive"


# ── Test 10 ──────────────────────────────────────────────────────────────────
def test_lifecycle_v2_plans_manual_only():
    for num in range(15, 20):
        rel = f"docs/orchestration/{num:02d}_test_lifecycle_plan.md"
        c = classify_path(rel, REPO_ROOT)
        assert c.classification == Classification.MANUAL_ONLY, (
            f"Expected MANUAL_ONLY for {rel}, got {c.classification}"
        )


def test_unknown_file_classification():
    c = classify_path("some_random_dir/completely_unknown_file.bin", REPO_ROOT)
    assert c.classification == Classification.UNKNOWN


# ── Test: new protected paths (Phase 5) ──────────────────────────────────────
def test_claim_status_json_protected():
    c = classify_path("claim_status.json", REPO_ROOT)
    assert c.classification == Classification.PROTECTED


def test_ablation_results_json_protected():
    c = classify_path("ablation_results.json", REPO_ROOT)
    assert c.classification == Classification.PROTECTED


def test_evidence_cards_dir_protected():
    c = classify_path("evidence_cards/C3_falsification.md", REPO_ROOT)
    assert c.classification == Classification.PROTECTED


# ── Test: Rule B — PHASE gate reports (Phase 5) ───────────────────────────────
def test_phase_gate_report_archive_ready():
    for name in (
        "docs/orchestration/PHASE1_GATE_REPORT.md",
        "docs/orchestration/PHASE2_GATE_REPORT.md",
        "docs/orchestration/PHASE3_GATE_REPORT.md",
        "docs/orchestration/PHASE3B_GATE_REPORT.md",
    ):
        c = classify_path(name, REPO_ROOT)
        assert c.classification == Classification.ARCHIVE_READY, (
            f"Expected ARCHIVE_READY for {name}, got {c.classification}"
        )


# ── Test: Rule C — codex_done results (Phase 5) ───────────────────────────────
def test_codex_done_result_archive_ready():
    c = classify_path(".agent_tasks/codex_done/TASK_1002_C3_world_model_RESULT.md", REPO_ROOT)
    assert c.classification == Classification.ARCHIVE_READY


def test_codex_done_non_result_not_archive_ready():
    c = classify_path(".agent_tasks/codex_done/some_other_file.md", REPO_ROOT)
    assert c.classification != Classification.ARCHIVE_READY


# ── Test: Rule D — codex_archive dir (Phase 5) ────────────────────────────────
def test_codex_archive_dir_archive_ready():
    c = classify_path(".agent_tasks/codex_archive/p3_impl/TASK_C3.md", REPO_ROOT)
    assert c.classification == Classification.ARCHIVE_READY


# ── Test: Rule E — superseded precompact handoff (Phase 5) ───────────────────
def test_superseded_precompact_handoff_archive_ready(tmp_path):
    folder = tmp_path / "docs" / "orchestration" / "session_reports" / "2026-05"
    folder.mkdir(parents=True)
    (folder / "2026-05-15_precompact_handoff.md").write_text("old", encoding="utf-8")
    (folder / "2026-05-17_precompact_handoff.md").write_text("new", encoding="utf-8")

    c = classify_path(
        "docs/orchestration/session_reports/2026-05/2026-05-15_precompact_handoff.md",
        tmp_path,
    )
    assert c.classification == Classification.ARCHIVE_READY


def test_latest_precompact_handoff_not_archive_ready(tmp_path):
    folder = tmp_path / "docs" / "orchestration" / "session_reports" / "2026-05"
    folder.mkdir(parents=True)
    (folder / "2026-05-15_precompact_handoff.md").write_text("old", encoding="utf-8")
    (folder / "2026-05-17_precompact_handoff.md").write_text("new", encoding="utf-8")

    c = classify_path(
        "docs/orchestration/session_reports/2026-05/2026-05-17_precompact_handoff.md",
        tmp_path,
    )
    assert c.classification != Classification.ARCHIVE_READY


# ── Contract: no subprocess ───────────────────────────────────────────────────
def test_no_subprocess_import():
    src = _SCRIPT.read_text(encoding="utf-8")
    assert "import subprocess" not in src
    assert "from subprocess" not in src


# ── Contract: no destructive file API ────────────────────────────────────────
def test_no_destructive_api():
    src = _SCRIPT.read_text(encoding="utf-8")
    forbidden = [
        "shutil.move",
        "shutil.rmtree",
        "os.remove(",
        "os.unlink(",
        ".unlink(",
        "os.rmdir(",
        ".rmdir(",
    ]
    for api in forbidden:
        assert api not in src, f"Forbidden destructive API found: {api!r}"
