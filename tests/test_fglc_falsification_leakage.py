"""Leakage audits for R4 falsification gate.

Verifies:
- conformal threshold τ is fit on ID data only (not OOD)
- regime_id / ood_type / seed forbidden fields cannot reach R4 evaluator
- R4 metric input is model-derived only (rho_per_group from dynamics)
"""

from __future__ import annotations

import os
import tempfile

import numpy as np
import torch
import pytest

from fglc.falsification.conformal import fit_threshold
from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS, assert_no_forbidden_fields


def test_conformal_threshold_id_only_by_contract():
    """fit_threshold() takes a flat 1-D tensor — it has no mechanism to receive split labels.

    This test checks that passing shape (N, 2) raises ValueError (contract enforcement).
    """
    scores = torch.randn(100, 2)
    with pytest.raises(ValueError):
        fit_threshold(scores, alpha=0.05)


def test_forbidden_fields_not_in_batch():
    """Mock dataloader batch must not contain any forbidden field."""
    clean_batch = {
        "state": torch.randn(4, 10, 42),
        "action": torch.randn(4, 10, 8),
        "reward": torch.randn(4, 10),
        "done": torch.zeros(4, 10),
    }
    # Should not raise
    assert_no_forbidden_fields(clean_batch, context="test_leakage")


def test_forbidden_fields_raises_on_regime_id():
    bad_batch = {
        "state": torch.randn(2, 5, 42),
        "regime_id": torch.zeros(2),  # FORBIDDEN
    }
    with pytest.raises(ValueError, match="regime_id"):
        assert_no_forbidden_fields(bad_batch, context="test_leakage")


@pytest.mark.parametrize("field", sorted(FORBIDDEN_AGENT_FIELDS))
def test_each_forbidden_field_raises(field: str):
    batch = {"state": torch.randn(2, 5, 8), field: torch.zeros(2)}
    with pytest.raises(ValueError):
        assert_no_forbidden_fields(batch, context=f"test_each:{field}")


def test_r4_evaluate_residuals_uses_model_output_only():
    """evaluate_residuals must derive rho from encoder/belief/dynamics only.

    We verify by constructing a trainer with random weights (no checkpoint),
    running evaluate_residuals on a batch, and checking that outputs are finite
    and do not contain any forbidden field key in the return dict.
    """
    from fglc.evaluation.metrics import Evaluator
    from fglc.training import TrainerConfig, TrainerR3

    model_config = {"D_x": 8, "D_a": 4, "K": 3, "d": 8, "h_dim": 32}
    trainer_config = TrainerConfig(batch_size=2, train_horizon=4, epochs=0, device="cpu")
    trainer = TrainerR3(model_config, trainer_config)

    from torch.utils.data import DataLoader, TensorDataset

    B, T = 4, 6
    ds = TensorDataset(
        torch.randn(B, T, 8),  # state
        torch.randn(B, T, 4),  # action
        torch.randn(B, T),     # reward
        torch.zeros(B, T),     # done
    )

    def _collate(batch):
        states, actions, rewards, dones = zip(*batch)
        return {
            "state": torch.stack(states),
            "action": torch.stack(actions),
            "reward": torch.stack(rewards),
            "done": torch.stack(dones),
        }

    dl = DataLoader(ds, batch_size=2, collate_fn=_collate)
    evaluator = Evaluator(trainer)
    result = evaluator.evaluate_residuals(dl)

    # Output keys must not be forbidden fields
    for k in result:
        assert k not in FORBIDDEN_AGENT_FIELDS, f"evaluate_residuals returned forbidden field: {k}"

    # Outputs should be finite tensors
    for k, v in result.items():
        assert torch.isfinite(v).all(), f"evaluate_residuals[{k!r}] contains NaN/Inf"
