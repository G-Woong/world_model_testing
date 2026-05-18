"""Tests for STEP 6 ablation execution matrix integrity.

Verifies:
1. 14 critical ablation IDs are registered as wrappers.
2. inference-time ablations are all dispatch-ready.
3. ABL-040 is isolated as positive-control.
4. ABL-016 control_evidence_ref is set (depends on Task 2).
5. Matrix document exists.
"""
from __future__ import annotations

from pathlib import Path

import pytest


CRITICAL_ABL_WRAPPER_IDS = {
    "no_control_grammar",          # ABL-002 (in matrix as ABL-001 = no_regime is separate)
    "merged_regime_control_grammar",  # ABL-003
    "collapsed_latent",            # ABL-006
    "no_action_effect_log",        # ABL-011
    "no_control_grammar_loss",     # ABL-015
    "no_falsification",            # ABL-016
    "no_intent_action_mapping",    # ABL-017
    "no_falsification_score_gate", # ABL-022
    "uncertainty_instead_of_falsification",  # ABL-023
    "no_alternative_hypothesis",   # ABL-024
    "no_compute_gate",             # ABL-033
    "always_plan_no_gate",         # ABL-034
    "no_rewrite",                  # ABL-035
    "no_counterfactual_target",    # ABL-036
    "leakage_sanity_probe",        # ABL-040
}

INFERENCE_TIME_ABL_IDS = {
    "collapsed_latent",            # ABL-006
    "no_action_effect_log",        # ABL-011
    "no_intent_action_mapping",    # ABL-017
    "no_falsification_score_gate", # ABL-022
    "uncertainty_instead_of_falsification",  # ABL-023
    "no_alternative_hypothesis",   # ABL-024
    "no_compute_gate",             # ABL-033
    "always_plan_no_gate",         # ABL-034
    "no_rewrite",                  # ABL-035
    "no_counterfactual_target",    # ABL-036
}


def test_14_critical_ablations_registered():
    """All 14 critical ablation IDs must be registered as wrapper entries."""
    from frcgw.evaluation.ablations import _WRAPPERS

    for abl_id in CRITICAL_ABL_WRAPPER_IDS:
        assert abl_id in _WRAPPERS, (
            f"Critical ablation '{abl_id}' is not registered in _WRAPPERS"
        )


def test_inference_time_ablations_dispatch_ready():
    """9 directly-executable inference-time ablations must all be in _WRAPPERS."""
    from frcgw.evaluation.ablations import _WRAPPERS

    for abl_id in INFERENCE_TIME_ABL_IDS:
        assert abl_id in _WRAPPERS, (
            f"Inference-time ablation '{abl_id}' not in _WRAPPERS — cannot dispatch"
        )


def test_abl040_is_positive_control_isolated():
    """ABL-040 must be the positive-control (leakage sanity probe), not a performance ablation."""
    from frcgw.evaluation.ablations import ABLATION_REGISTRY, _WRAPPERS

    cfg = ABLATION_REGISTRY.get("leakage_sanity_probe")
    assert cfg is not None, "leakage_sanity_probe must be in ABLATION_REGISTRY"

    desc = cfg.description.lower()
    assert any(word in desc for word in ("leakage", "oracle", "sanity")), (
        f"ABL-040 description must reference leakage/oracle/sanity, got: {cfg.description}"
    )

    # Verify ABL-040 expected_collapse shows INCREASE (positive control)
    assert "task_success_rate" in cfg.expected_collapse, (
        "ABL-040 must have task_success_rate in expected_collapse (increase expected)"
    )
    assert cfg.expected_collapse["task_success_rate"] == "increase", (
        "ABL-040 expected_collapse['task_success_rate'] must be 'increase' (positive control)"
    )


def test_abl016_control_evidence_ref_consistent():
    """ABL-016 control_evidence_ref must be set (requires Task 2 completion)."""
    from frcgw.evaluation.ablations import ABLATION_REGISTRY

    cfg = ABLATION_REGISTRY["no_falsification"]
    assert cfg.control_evidence_ref is not None, (
        "ABL-016 control_evidence_ref must be registered (see 29_step6_abl016_control_registration.md)"
    )
    assert "pretrain_v0_3" in cfg.control_evidence_ref, (
        f"ABL-016 control_evidence_ref must reference STEP 5 checkpoint, got: {cfg.control_evidence_ref}"
    )


def test_matrix_file_exists():
    """Ablation execution matrix document must exist."""
    matrix_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "orchestration"
        / "lr_alignment"
        / "27_step6_ablation_execution_matrix.md"
    )
    assert matrix_path.exists(), (
        f"Ablation execution matrix not found: {matrix_path}"
    )
    content = matrix_path.read_text(encoding="utf-8")
    assert len(content) > 100, "Matrix document must be non-trivially non-empty"
    assert "ABL-016" in content, "Matrix must reference ABL-016"
    assert "positive-control" in content, "Matrix must label ABL-040 as positive-control"
