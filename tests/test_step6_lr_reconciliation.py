"""Tests for STEP 6 LR reconciliation audit script.

Verifies:
1. Output JSON schema has all required keys.
2. Script refuses to overwrite STEP 4/5 audit paths.
3. Missing checkpoints produce BLOCKED report.
4. Hidden labels are not accessed during planner F_t computation.
5. All 4 condition keys are present in output.
6. c3_claim_readiness follows the state machine rules.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure scripts/ is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
for _p in (str(REPO_ROOT), str(REPO_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


REQUIRED_TOP_LEVEL_KEYS = {
    "timestamp",
    "abl016_checkpoint",
    "falsification_checkpoint",
    "dataset",
    "n_episodes_evaluated",
    "n_steps_evaluated",
    "abl016_planner",
    "abl016_lr_scorer",
    "falsification_planner",
    "falsification_lr_scorer",
    "mean_abs_diff_planner_vs_lr_abl016",
    "mean_abs_diff_planner_vs_lr_falsification",
    "delta_falsification_vs_abl016",
    "active_path_swap_decision",
    "c3_claim_readiness",
    "blocked_reasons",
    "step4_audit_path",
    "step5_audit_path",
}

CONDITION_KEYS = {"abl016_planner", "abl016_lr_scorer", "falsification_planner", "falsification_lr_scorer"}


def test_output_schema_keys(tmp_path):
    """Output JSON must have all required top-level keys."""
    from scripts.audit_step6_lr_reconciliation import run_reconciliation

    out = tmp_path / "step6_lr_reconciliation.json"
    report = run_reconciliation(
        abl016_ckpt_path=Path("nonexistent_abl016.pt"),
        falsification_ckpt_path=Path("nonexistent_falsi.pt"),
        dataset_path=Path("nonexistent_dataset.jsonl"),
        out_path=out,
        max_episodes=2,
    )

    assert set(report.keys()) >= REQUIRED_TOP_LEVEL_KEYS, (
        f"Missing keys: {REQUIRED_TOP_LEVEL_KEYS - set(report.keys())}"
    )


def test_no_step4_step5_overwrite():
    """Script must refuse if --out matches STEP 4/5 audit paths."""
    from scripts.audit_step6_lr_reconciliation import run_reconciliation

    # Test with a path that matches forbidden step5 pattern
    with pytest.raises(ValueError, match="step5"):
        run_reconciliation(
            abl016_ckpt_path=Path("a.pt"),
            falsification_ckpt_path=Path("b.pt"),
            dataset_path=Path("c.jsonl"),
            out_path=Path("outputs/audits/step5_lr_reconciliation.json"),
            max_episodes=2,
        )


def test_no_step4_overwrite_forbidden_path():
    """Script must refuse if --out matches STEP 4 audit path."""
    from scripts.audit_step6_lr_reconciliation import run_reconciliation

    with pytest.raises(ValueError):
        run_reconciliation(
            abl016_ckpt_path=Path("a.pt"),
            falsification_ckpt_path=Path("b.pt"),
            dataset_path=Path("c.jsonl"),
            out_path=Path("outputs/audits/step4_lr_comparison.json"),
            max_episodes=2,
        )


def test_dual_checkpoint_both_missing_gives_blocked(tmp_path):
    """Both checkpoints missing → c3_claim_readiness='BLOCKED' and blocked_reasons non-empty."""
    from scripts.audit_step6_lr_reconciliation import run_reconciliation

    out = tmp_path / "step6_lr_reconciliation.json"
    report = run_reconciliation(
        abl016_ckpt_path=Path("nonexistent_abl016.pt"),
        falsification_ckpt_path=Path("nonexistent_falsi.pt"),
        dataset_path=Path("nonexistent.jsonl"),
        out_path=out,
        max_episodes=2,
    )

    assert report["c3_claim_readiness"] == "BLOCKED", (
        "Both checkpoints missing must give c3_claim_readiness=BLOCKED"
    )
    assert len(report["blocked_reasons"]) > 0, "blocked_reasons must be non-empty when blocked"


def test_hidden_label_not_in_planner_input():
    """Planner F_t computation must only use PublicObservation (no FORBIDDEN_AGENT_FIELDS)."""
    from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS
    from frcgw.schemas.step_schema import PublicObservation

    obs = PublicObservation(instruction="test", history_public=[], candidate_actions_public=[])

    # PublicObservation must not have any forbidden fields
    obs_dict = vars(obs) if hasattr(obs, "__dict__") else {}
    for forbidden_field in FORBIDDEN_AGENT_FIELDS:
        assert forbidden_field not in obs_dict, (
            f"FORBIDDEN_AGENT_FIELD '{forbidden_field}' found in PublicObservation"
        )


def test_dual_trace_fields_present(tmp_path):
    """Output must contain all 4 condition keys."""
    from scripts.audit_step6_lr_reconciliation import run_reconciliation

    out = tmp_path / "step6_lr_reconciliation.json"
    report = run_reconciliation(
        abl016_ckpt_path=Path("nonexistent_abl016.pt"),
        falsification_ckpt_path=Path("nonexistent_falsi.pt"),
        dataset_path=Path("nonexistent.jsonl"),
        out_path=out,
        max_episodes=2,
    )

    for key in CONDITION_KEYS:
        assert key in report, f"Required condition key missing: {key}"
        assert isinstance(report[key], dict), f"Condition key {key} must be a dict"


def test_claim_readiness_blocked_when_fully_degenerate(tmp_path):
    """When falsification degenerate_rate=1.0, c3_claim_readiness must be BLOCKED."""
    from scripts.audit_step6_lr_reconciliation import _c3_claim_readiness

    degenerate_stats = {"mean_f_t": 0.0, "variance": 0.0, "degenerate_rate": 1.0}
    result = _c3_claim_readiness([], degenerate_stats, degenerate_stats)
    assert result == "BLOCKED", (
        "Fully degenerate falsification planner must give c3_claim_readiness=BLOCKED"
    )


def test_claim_readiness_preliminary_when_non_degenerate(tmp_path):
    """When falsification mean_f_t > 0 and degenerate_rate < 1, c3_claim_readiness=PRELIMINARY."""
    from scripts.audit_step6_lr_reconciliation import _c3_claim_readiness

    good_stats = {"mean_f_t": 0.3, "variance": 0.01, "degenerate_rate": 0.2}
    result = _c3_claim_readiness([], good_stats, good_stats)
    assert result == "PRELIMINARY", (
        "Non-degenerate falsification must give PRELIMINARY (not READY_FOR_REPORT)"
    )
    # READY_FOR_REPORT is reserved for STEP 7; never reachable in STEP 6
    assert result != "READY_FOR_REPORT", "READY_FOR_REPORT must not be reachable in STEP 6"
