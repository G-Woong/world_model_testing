"""Tests for P3 loss functions and objective leakage guard.

Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
"""
from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from frcgw.data.text_dataset import BatchTargets
from frcgw.models.text_frcg_model import TextFRCGModel
from frcgw.models.world_model_heads import RolloutResult
from frcgw.objectives.losses import (
    L_falsification,
    L_intent_action_mapping,
    compute_total_loss,
)
from frcgw.objectives.rewards import (
    R_compute_cost,
    R_failed_action_penalty,
    R_progress,
    R_repeated_failure_penalty,
)
from frcgw.schemas.step_schema import PublicObservation
from frcgw.schemas.visibility import HiddenLabelLeakageError


def make_target(**kwargs) -> BatchTargets:
    defaults = dict(
        true_regime="search_form",
        true_control_grammar="direct_search",
        true_change_point="0",
        true_reveal_vs_shift="none",
        true_action_effect_type="none",
        true_failed_action=False,
        failure_reason=None,
        progress_delta=0.0,
        recovery_action_id=None,
        valid_hypothesis_switch=None,
        true_wrong_hypothesis=False,
        h_exec_id=None,
        correct_hypothesis_id=None,
    )
    defaults.update(kwargs)
    return BatchTargets(**defaults)


def _synthetic_outputs(batch_size: int = 2):
    from frcgw.models.text_frcg_model import ModelOutput

    model_output = ModelOutput(
        z_state=torch.randn(batch_size, 32, requires_grad=True),
        z_regime_logits=torch.randn(batch_size, 8, requires_grad=True),
        z_grammar_logits=torch.randn(batch_size, 8, requires_grad=True),
        z_change_logits=torch.randn(batch_size, 12, requires_grad=True),
        z_reveal_shift_logits=torch.randn(batch_size, 3, requires_grad=True),
        shared_h=torch.randn(batch_size, 128, requires_grad=True),
        posterior_entropy=torch.rand(batch_size, requires_grad=True),
        aux_precondition=torch.rand(batch_size, requires_grad=True),
        aux_failure_risk=torch.rand(batch_size, requires_grad=True),
    )
    world_output = RolloutResult(
        effect_logits=torch.randn(batch_size, 7, requires_grad=True),
        progress_pred=torch.randn(batch_size, requires_grad=True),
        failed_score=torch.sigmoid(torch.randn(batch_size, requires_grad=True)),
    )
    targets = [
        make_target(),
        make_target(
            true_regime="modal_blocker",
            true_control_grammar="modal_confirm_then_action",
            true_change_point="3",
            true_reveal_vs_shift="reveal",
            true_action_effect_type="reveal",
            true_failed_action=True,
            progress_delta=0.5,
            true_wrong_hypothesis=True,
        ),
    ][:batch_size]
    return model_output, world_output, targets


def test_each_loss_nonneg_finite() -> None:
    model_output, world_output, targets = _synthetic_outputs()
    loss_dict = compute_total_loss(model_output, world_output, torch.zeros(2), targets)
    for name, value in loss_dict.__dict__.items():
        if name == "weights":
            continue
        assert torch.isfinite(value)
        assert value.item() >= 0.0


def test_total_loss_has_grad() -> None:
    model = TextFRCGModel()
    pub = PublicObservation(instruction="test", history_public=[])
    out = model(pub)
    world_out = model.world_model_heads.forward_given_action(out.shared_h, out.z_state, "click", 0)
    F_t = torch.zeros(1, requires_grad=True)
    loss_dict = compute_total_loss(out, world_out, F_t, [make_target()])
    loss_dict.l_total.backward()
    assert any(p.grad is not None for p in model.parameters() if p.requires_grad)


def test_recovery_mask() -> None:
    target = make_target(recovery_action_id=None)
    assert L_intent_action_mapping(torch.randn(1, 4), [target]).item() == 0.0


def test_no_op_valid_not_false_positive() -> None:
    target = make_target(true_action_effect_type="no_op_valid", true_wrong_hypothesis=False)
    loss_low_score = L_falsification(torch.tensor([-5.0]), [target])
    loss_high_score = L_falsification(torch.tensor([5.0]), [target])
    assert loss_low_score < loss_high_score


def test_weight_config_applied() -> None:
    model_output, world_output, targets = _synthetic_outputs()
    default_loss = compute_total_loss(model_output, world_output, torch.zeros(2), targets)
    changed_loss = compute_total_loss(
        model_output,
        world_output,
        torch.zeros(2),
        targets,
        weights={"l_regime": 0.25},
    )
    assert not torch.allclose(default_loss.l_total, changed_loss.l_total)


def test_assert_fires_on_leakage() -> None:
    model_output, world_output, targets = _synthetic_outputs(batch_size=1)
    leaky_obs = PublicObservation(instruction="x", dom_snapshot_public={"true_regime": "x"})
    with pytest.raises(HiddenLabelLeakageError):
        compute_total_loss(model_output, world_output, torch.zeros(1), targets, public_input=[leaky_obs])


def test_falsification_none_returns_zero() -> None:
    model_output, world_output, targets = _synthetic_outputs(batch_size=1)
    loss_dict = compute_total_loss(model_output, world_output, None, targets)
    assert loss_dict.l_falsification.item() == 0.0


def test_rewards_basic() -> None:
    assert R_progress(0.5) == 0.5
    assert R_failed_action_penalty(True) == -0.3
    assert R_repeated_failure_penalty(3) == pytest.approx(-0.3)
    assert R_compute_cost(3, 1, 0.1) == pytest.approx(0.3)
