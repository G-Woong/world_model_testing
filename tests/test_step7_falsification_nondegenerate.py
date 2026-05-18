"""Falsification does not short-circuit non-trivial v0_3 effects."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

torch = pytest.importorskip("torch")

from frcgw.planning.falsification import FalsificationEvidence, falsification_score


def _make_rollout(n_effect_types: int = 7):
    rollout = MagicMock()
    rollout.effect_logits = torch.randn(1, n_effect_types)
    rollout.progress_pred = torch.tensor([0.5])
    rollout.failed_score = torch.tensor([0.1])
    return rollout


def _make_model(n_effect_types: int = 7):
    model = MagicMock()
    model.world_model_heads.forward_given_action.side_effect = (
        lambda sh, zs, action, hid: _make_rollout(n_effect_types)
    )
    return model


@pytest.mark.parametrize(
    "effect_str,effect_id",
    [
        ("state_change", 1),
        ("blocker_removed", 2),
        ("delayed_effect", 4),
        ("task_complete", 5),
    ],
)
def test_falsification_not_short_circuited_for_nontrivial_effects(
    effect_str: str,
    effect_id: int,
) -> None:
    model = _make_model()
    shared_h = torch.zeros(1, 32)
    z_state = torch.zeros(1, 32)
    evidence = FalsificationEvidence(
        observed_effect_type=effect_id,
        observed_progress_delta=0.3,
        observed_failed_action=False,
    )

    falsification_score(
        model,
        shared_h,
        z_state,
        "click",
        h_exec_id=0,
        alt_hypothesis_ids=[1, 2],
        evidence=evidence,
    )

    assert model.world_model_heads.forward_given_action.called, (
        f"Short-circuit fired for {effect_str} (id={effect_id}): model was not called"
    )


def test_falsification_short_circuits_for_no_state_change() -> None:
    model = _make_model()
    shared_h = torch.zeros(1, 32)
    z_state = torch.zeros(1, 32)
    evidence = FalsificationEvidence(
        observed_effect_type=0,
        observed_progress_delta=0.0,
        observed_failed_action=False,
    )

    result = falsification_score(
        model,
        shared_h,
        z_state,
        "click",
        h_exec_id=0,
        alt_hypothesis_ids=[1, 2],
        evidence=evidence,
    )

    assert not model.world_model_heads.forward_given_action.called
    assert result.item() == 0.0
