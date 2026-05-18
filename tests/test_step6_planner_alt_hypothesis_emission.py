"""Tests for STEP 6 planner alt-hypothesis emission fix (B2).

Verifies:
1. propose() is called before falsification_score() in text_frcg_plan().
2. alt_ids passed to falsification_score() are non-empty ints.
3. Early return (F_t <= tau_f) still works after reorder.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import torch

from frcgw.planning.planner import PlannerState, text_frcg_plan
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


def _make_mock_model() -> MagicMock:
    """Create a minimal mock TextFRCGModel that returns deterministic tensors."""
    model = MagicMock()
    model_out = MagicMock()
    model_out.shared_h = torch.zeros(1, 32)
    model_out.z_state = torch.zeros(1, 32)
    model_out.z_regime_logits = torch.zeros(1, 8)
    model_out.z_grammar_logits = torch.zeros(1, 8)
    model_out.z_change_logits = torch.zeros(1, 12)
    model_out.z_reveal_shift_logits = torch.zeros(1, 3)
    model_out.posterior_entropy = torch.zeros(1)
    model_out.aux_precondition = torch.zeros(1)
    model_out.aux_failure_risk = torch.zeros(1)
    model.forward.return_value = model_out

    rollout_result = MagicMock()
    rollout_result.effect_logits = torch.zeros(1, 7)
    rollout_result.progress_pred = torch.tensor([0.5])
    rollout_result.failed_score = torch.tensor([0.1])
    model.world_model_heads.forward_given_action.return_value = rollout_result
    model.world_model_heads.rollout_step.return_value = rollout_result
    return model


def _make_obs() -> PublicObservation:
    return PublicObservation(
        instruction="test",
        history_public=[],
        candidate_actions_public=[CandidateAction("a1", "click", {})],
    )


def test_planner_alt_hypotheses_non_empty_after_fix():
    """After B2 fix, falsification_score() should receive non-empty alt_ids."""
    model = _make_mock_model()
    obs = _make_obs()
    planner_state = PlannerState()

    alt_ids_captured = []

    original_fs = None
    import frcgw.planning.planner as planner_module

    original_fs = planner_module.falsification_score

    def capturing_fs(m, sh, zs, at, h_exec, alt_hypothesis_ids, evidence, **kwargs):
        alt_ids_captured.extend(alt_hypothesis_ids)
        return original_fs(m, sh, zs, at, h_exec, alt_hypothesis_ids, evidence, **kwargs)

    with patch.object(planner_module, "falsification_score", side_effect=capturing_fs):
        text_frcg_plan(obs, 0, list(obs.candidate_actions_public), model, planner_state)

    assert len(alt_ids_captured) > 0, (
        "After B2 fix, alt_ids passed to falsification_score must be non-empty"
    )


def test_planner_alt_hypothesis_ids_are_ints():
    """Alt IDs passed to falsification_score must be integers (not HypothesisId objects)."""
    model = _make_mock_model()
    obs = _make_obs()
    planner_state = PlannerState()

    alt_ids_captured = []

    import frcgw.planning.planner as planner_module

    original_fs = planner_module.falsification_score

    def capturing_fs(m, sh, zs, at, h_exec, alt_hypothesis_ids, evidence, **kwargs):
        alt_ids_captured.extend(alt_hypothesis_ids)
        return original_fs(m, sh, zs, at, h_exec, alt_hypothesis_ids, evidence, **kwargs)

    with patch.object(planner_module, "falsification_score", side_effect=capturing_fs):
        text_frcg_plan(obs, 0, list(obs.candidate_actions_public), model, planner_state)

    if alt_ids_captured:
        for alt_id in alt_ids_captured:
            assert isinstance(alt_id, int), (
                f"alt_id must be int, got {type(alt_id)}: {alt_id}"
            )


def test_planner_early_exit_preserved():
    """When F_t <= tau_f, planner returns early with planned=False."""
    model = _make_mock_model()
    obs = _make_obs()
    planner_state = PlannerState()

    import frcgw.planning.planner as planner_module
    import frcgw.planning.decision_gate as gate_module

    # Force F_t = 0.0 (below tau_f = 0.0) → early exit
    with patch.object(planner_module, "falsification_score", return_value=torch.tensor(-1.0)):
        action, meta = text_frcg_plan(
            obs, 0, list(obs.candidate_actions_public), model, planner_state
        )

    assert meta.planned is False, "Early exit should set planned=False when F_t <= tau_f"
    assert meta.reason == "low_F_t", f"Expected reason='low_F_t', got: {meta.reason}"


def test_planner_alt_hypotheses_called_before_falsification_score():
    """propose() must be invoked before falsification_score() (call order check)."""
    model = _make_mock_model()
    obs = _make_obs()
    planner_state = PlannerState()

    call_order = []

    import frcgw.planning.planner as planner_module

    original_propose = planner_module.propose
    original_fs = planner_module.falsification_score

    def tracking_propose(*args, **kwargs):
        call_order.append("propose")
        return original_propose(*args, **kwargs)

    def tracking_fs(*args, **kwargs):
        call_order.append("falsification_score")
        return original_fs(*args, **kwargs)

    with patch.object(planner_module, "propose", side_effect=tracking_propose), \
         patch.object(planner_module, "falsification_score", side_effect=tracking_fs):
        text_frcg_plan(obs, 0, list(obs.candidate_actions_public), model, planner_state)

    assert "propose" in call_order, "propose() must be called"
    assert "falsification_score" in call_order, "falsification_score() must be called"
    propose_idx = call_order.index("propose")
    fs_idx = call_order.index("falsification_score")
    assert propose_idx < fs_idx, (
        f"propose() (idx={propose_idx}) must run BEFORE falsification_score() (idx={fs_idx})"
    )
