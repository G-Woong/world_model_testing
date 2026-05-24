"""R4 runner integration tests with ManiSkill-style stub dataset.

Verifies:
- evaluate_residuals produces correct shapes and keys
- STAGE2_CANONICAL_METRIC_KEYS all present in compute_r4_metrics output
- No forbidden fields in R4 runner input path
- save_state / load_state round-trip
"""

from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest
import torch


def _make_stub_h5(path: str, n_episodes: int = 4, T: int = 12, D_x: int = 42, D_a: int = 8):
    import h5py

    rng = np.random.default_rng(99)
    with h5py.File(path, "w") as f:
        ep_group = f.create_group("episodes")
        for ep_id in range(n_episodes):
            ep = ep_group.create_group(str(ep_id))
            ep.create_dataset("state", data=rng.normal(size=(T, D_x)).astype(np.float32))
            ep.create_dataset("action", data=rng.normal(size=(T, D_a)).astype(np.float32))
            ep.create_dataset("reward", data=rng.normal(size=(T,)).astype(np.float32))
            dones = np.zeros(T, dtype=bool)
            dones[-1] = True
            ep.create_dataset("done", data=dones)


@pytest.fixture()
def r4_stub_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        splits = ("train_id", "val_id", "test_id", "ood_mass", "ood_friction", "ood_gain")
        for split in splits:
            _make_stub_h5(os.path.join(tmpdir, f"{split}.h5"), n_episodes=4)

        config = {
            "seed": 0,
            "device": "cpu",
            "dataset": {
                "type": "maniskill_state_only",
                "task": "PickCube-v1",
                "D_x": 42,
                "D_a": 8,
                "episode_len": 12,
                "n_episode_train": 4,
                "n_episode_val": 4,
                "n_episode_ood_mass": 4,
                "n_episode_ood_friction": 4,
                "n_episode_ood_gain": 4,
                "data_root": tmpdir,
                "train_id_h5": os.path.join(tmpdir, "train_id.h5"),
                "val_id_h5": os.path.join(tmpdir, "val_id.h5"),
                "test_id_h5": os.path.join(tmpdir, "test_id.h5"),
                "ood_mass_h5": os.path.join(tmpdir, "ood_mass.h5"),
                "ood_friction_h5": os.path.join(tmpdir, "ood_friction.h5"),
                "ood_gain_h5": os.path.join(tmpdir, "ood_gain.h5"),
                "ood_mass_value": 1.5,
                "ood_friction_value": 5.0,
                "ood_gain_value": 0.7,
            },
            "model": {"D_x": 42, "D_a": 8, "K": 3, "d": 8, "h_dim": 32},
            "trainer": {
                "batch_size": 2,
                "train_horizon": 6,
                "epochs": 1,
                "learning_rate": 3e-4,
                "optimizer": "adam",
                "loss_weights": {},
            },
        }
        yield config, tmpdir


def _make_trainer(config: dict):
    from fglc.training import TrainerConfig, TrainerR3

    tc = TrainerConfig(
        batch_size=config["trainer"]["batch_size"],
        train_horizon=config["trainer"]["train_horizon"],
        epochs=config["trainer"]["epochs"],
        learning_rate=config["trainer"]["learning_rate"],
        optimizer=config["trainer"]["optimizer"],
        device="cpu",
    )
    return TrainerR3(config["model"], tc)


def test_evaluate_residuals_shapes(r4_stub_env):
    config, _ = r4_stub_env
    from fglc.data.dataloader import make_dataloaders
    from fglc.evaluation.metrics import Evaluator

    dataloaders = make_dataloaders(config)
    trainer = _make_trainer(config)
    evaluator = Evaluator(trainer)
    result = evaluator.evaluate_residuals(dataloaders["test_id"])

    K = config["model"]["K"]
    d = config["model"]["d"]
    N = result["F_total"].shape[0]

    assert result["rho_per_group"].shape == (N, K, d), f"unexpected rho shape: {result['rho_per_group'].shape}"
    assert result["F_per_group"].shape == (N, K)
    assert result["F_total"].shape == (N,)
    assert result["raw_nll_step"].shape == (N,)


def test_evaluate_residuals_finite(r4_stub_env):
    config, _ = r4_stub_env
    from fglc.data.dataloader import make_dataloaders
    from fglc.evaluation.metrics import Evaluator

    dataloaders = make_dataloaders(config)
    trainer = _make_trainer(config)
    evaluator = Evaluator(trainer)
    result = evaluator.evaluate_residuals(dataloaders["test_id"])

    for k, v in result.items():
        assert torch.isfinite(v).all(), f"evaluate_residuals[{k!r}] has NaN/Inf"


def test_r4_metrics_contain_all_canonical_keys(r4_stub_env):
    config, _ = r4_stub_env
    from fglc.data.dataloader import make_dataloaders
    from fglc.evaluation.falsification_metrics import compute_r4_metrics
    from fglc.evaluation.metrics import STAGE2_CANONICAL_METRIC_KEYS, Evaluator

    dataloaders = make_dataloaders(config)
    trainer = _make_trainer(config)
    evaluator = Evaluator(trainer)

    eval_data = {
        split: evaluator.evaluate_residuals(dl)
        for split, dl in dataloaders.items()
    }
    metrics = compute_r4_metrics(eval_data, calibration_split="test_id", alpha=0.05)

    missing = STAGE2_CANONICAL_METRIC_KEYS - metrics.keys()
    assert not missing, f"Missing STAGE2 canonical keys: {sorted(missing)}"


def test_r4_no_forbidden_field_in_input(r4_stub_env):
    config, _ = r4_stub_env
    from fglc.data.dataloader import make_dataloaders
    from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS

    dataloaders = make_dataloaders(config)
    for split_name, dl in dataloaders.items():
        for batch in dl:
            violations = FORBIDDEN_AGENT_FIELDS & batch.keys()
            assert not violations, (
                f"Forbidden fields in {split_name} batch: {sorted(violations)}"
            )
            break  # one batch per split is enough


def test_save_load_state_round_trip(r4_stub_env, tmp_path):
    config, _ = r4_stub_env
    trainer = _make_trainer(config)

    ckpt_path = tmp_path / "r3_test.pt"
    trainer.save_state(ckpt_path)
    assert ckpt_path.exists()

    # Load into a fresh trainer — weights should match
    trainer2 = _make_trainer(config)
    trainer2.load_state(ckpt_path, freeze=True)

    for (n1, p1), (n2, p2) in zip(
        trainer.encoder.named_parameters(), trainer2.encoder.named_parameters()
    ):
        assert torch.allclose(p1, p2), f"Parameter {n1} mismatch after load_state"

    # After freeze, parameters should not require grad
    for p in trainer2.encoder.parameters():
        assert not p.requires_grad, "Frozen parameters must have requires_grad=False"
