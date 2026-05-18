"""Tests for STEP 6 ABL-016 control evidence registration.

Verifies:
1. ABLATION_REGISTRY["no_falsification"].control_evidence_ref is registered.
2. tdd_ref is ABL-016 (SSoT naming correction from ABL-010 error).
3. NoFalsificationAblation.act() behavior is unchanged.
4. AblationConfig.control_evidence_ref is optional (existing ablations unaffected).
"""
from __future__ import annotations

import pytest


def test_abl016_control_evidence_ref_registered():
    """STEP 5 checkpoint must be registered as ABL-016 control evidence."""
    from frcgw.evaluation.ablations import ABLATION_REGISTRY

    cfg = ABLATION_REGISTRY["no_falsification"]
    assert cfg.control_evidence_ref is not None, (
        "ABL-016 control_evidence_ref must be set (STEP 5 checkpoint path)"
    )
    assert "pretrain_v0_3" in cfg.control_evidence_ref, (
        f"ABL-016 control_evidence_ref should reference pretrain_v0_3 checkpoint, got: {cfg.control_evidence_ref}"
    )


def test_abl016_tdd_ref_is_ABL016():
    """SSoT correction: ABL-016 is the correct ID (not ABL-010)."""
    from frcgw.evaluation.ablations import ABLATION_REGISTRY

    cfg = ABLATION_REGISTRY["no_falsification"]
    assert cfg.tdd_ref == "ABL-016", (
        f"SSoT naming: no_falsification must map to ABL-016, got: {cfg.tdd_ref}"
    )


def test_abl016_dispatch_behavior_unchanged():
    """Adding control_evidence_ref metadata must not change NoFalsificationAblation.act() behavior."""
    from unittest.mock import MagicMock
    from frcgw.evaluation.ablations import ABLATION_REGISTRY, apply_ablation
    from frcgw.evaluation.compute_budget import ComputeBudgetLog
    from frcgw.schemas.step_schema import CandidateAction, PublicObservation

    base_agent = MagicMock()
    base_agent.act.return_value = (
        CandidateAction("a1", "click", {}),
        ComputeBudgetLog(planning_calls=1, rollout_steps=3, candidate_actions_scored=2, top_k_alternatives=2, wall_clock_seconds=0.0),
    )

    abl_cfg = ABLATION_REGISTRY["no_falsification"]
    agent = apply_ablation(base_agent, abl_cfg)
    obs = PublicObservation(instruction="test", candidate_actions_public=[CandidateAction("a1", "click", {})])
    action, log = agent.act(obs)

    assert isinstance(action, CandidateAction), "act() must return CandidateAction"
    assert isinstance(log, ComputeBudgetLog), "act() must return ComputeBudgetLog"
    assert log.planning_calls == 0, "NoFalsificationAblation must force planning_calls=0"


def test_ablation_config_control_evidence_ref_optional():
    """AblationConfig.control_evidence_ref is optional; existing ablations must still work."""
    from frcgw.evaluation.ablations import AblationConfig

    cfg = AblationConfig(
        ablation_id="test_optional",
        tdd_ref="TEST-001",
        severity="standard",
        description="Test optional field",
        expected_collapse={},
        masking={},
        # control_evidence_ref intentionally omitted
    )
    assert cfg.control_evidence_ref is None, "control_evidence_ref should default to None"
