"""R3SmokeRunner integration test with ManiSkill-style stub dataset.

Source: docs/STEP11_PLAN.md §I.2 TASK D6
Verifies:
  - R3SmokeRunner can run 1-epoch forward pass on ManiSkill config
  - Output RunnerOutput has required metric keys
  - metrics.json artifact is written with all STAGE1 canonical keys
"""

from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest
import torch


def _make_stub_h5(path: str, n_episodes: int = 4, T: int = 20, D_x: int = 42, D_a: int = 8) -> None:
    import h5py

    rng = np.random.default_rng(42)
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
def stub_h5_dir_and_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        splits = ("train_id", "val_id", "test_id", "ood_mass", "ood_friction")
        for split in splits:
            _make_stub_h5(os.path.join(tmpdir, f"{split}.h5"), n_episodes=4)

        config = {
            "seed": 42,
            "device": "cpu",
            "dataset": {
                "type": "maniskill_state_only",
                "task": "PickCube-v1",
                "D_x": 42,
                "D_a": 8,
                "episode_len": 20,
                "n_episode_train": 4,
                "n_episode_val": 4,
                "n_episode_ood_mass": 4,
                "n_episode_ood_friction": 4,
                "data_root": tmpdir,
                "train_id_h5": os.path.join(tmpdir, "train_id.h5"),
                "val_id_h5": os.path.join(tmpdir, "val_id.h5"),
                "test_id_h5": os.path.join(tmpdir, "test_id.h5"),
                "ood_mass_h5": os.path.join(tmpdir, "ood_mass.h5"),
                "ood_friction_h5": os.path.join(tmpdir, "ood_friction.h5"),
                "ood_mass_value": 1.5,
                "ood_friction_value": 5.0,
            },
            "model": {
                "D_x": 42,
                "D_a": 8,
                "K": 6,
                "d": 32,
                "h_dim": 128,
                "D_z": 192,
            },
            "trainer": {
                "batch_size": 2,
                "train_horizon": 4,
                "epochs": 1,
                "learning_rate": 3e-4,
                "optimizer": "adam",
                "loss_weights": {
                    "lambda_reward": 1.0,
                    "lambda_value": 1.0,
                    "lambda_calibration": 0.0,
                },
            },
            "metric": {
                "primary": "id_nll",
                "gate_threshold_id_nll": 0.5,
                "gate_threshold_ood_id_gap": 0.05,
            },
        }
        yield tmpdir, config


class TestR3RunnerManiSkill:
    def test_make_dataloaders_maniskill_branch(self, stub_h5_dir_and_config):
        """make_dataloaders returns 5 DataLoaders for maniskill_state_only config."""
        from torch.utils.data import DataLoader

        from fglc.data.dataloader import make_dataloaders

        _, config = stub_h5_dir_and_config
        loaders = make_dataloaders(config)
        assert set(loaders.keys()) >= {"train_id", "val_id", "ood_mass", "ood_friction"}
        assert all(isinstance(v, DataLoader) for v in loaders.values())

    def test_one_batch_forward_no_nan(self, stub_h5_dir_and_config):
        """One batch forward through encoder should produce finite output."""
        from fglc.data.dataloader import make_dataloaders
        from fglc.models import Encoder

        _, config = stub_h5_dir_and_config
        mc = config["model"]
        D_x, K, d = mc["D_x"], mc["K"], mc["d"]

        enc = Encoder(D_x, K=K, d=d)
        loaders = make_dataloaders(config)
        batch = next(iter(loaders["train_id"]))

        s = batch["state"]  # (B, T, D_x)
        z = enc(s)  # (B, T, K, d)
        assert torch.isfinite(z).all(), "Encoder output has non-finite values"
        assert z.shape == (s.shape[0], s.shape[1], K, d)

    def test_trainer_r3_smoke_maniskill(self, stub_h5_dir_and_config):
        """TrainerR3 can run 1 epoch on ManiSkill stub data."""
        from fglc.data.dataloader import make_dataloaders
        from fglc.training import TrainerConfig, TrainerR3

        _, config = stub_h5_dir_and_config
        loaders = make_dataloaders(config)

        t_cfg = TrainerConfig(
            batch_size=2,
            train_horizon=4,
            epochs=1,
            learning_rate=3e-4,
            optimizer="adam",
            loss_weights={"lambda_reward": 1.0, "lambda_value": 1.0, "lambda_calibration": 0.0},
            device="cpu",
        )
        trainer = TrainerR3(config["model"], t_cfg, device="cpu")
        out = trainer.train(loaders["train_id"], loaders["val_id"])
        assert "wall_clock_minutes" in out
        assert "history" in out
        assert "train_loss" in out["history"]

    def test_evaluate_model_produces_canonical_keys(self, stub_h5_dir_and_config):
        """evaluate_model produces all STAGE1_CANONICAL_METRIC_KEYS."""
        import tempfile
        from pathlib import Path

        from fglc.data.dataloader import make_dataloaders
        from fglc.evaluation.metrics import STAGE1_CANONICAL_METRIC_KEYS, evaluate_model
        from fglc.training import TrainerConfig, TrainerR3

        tmpdir, config = stub_h5_dir_and_config
        loaders = make_dataloaders(config)

        t_cfg = TrainerConfig(
            batch_size=2,
            train_horizon=4,
            epochs=1,
            learning_rate=3e-4,
            optimizer="adam",
            loss_weights={"lambda_reward": 1.0, "lambda_value": 1.0, "lambda_calibration": 0.0},
            device="cpu",
        )
        trainer = TrainerR3(config["model"], t_cfg, device="cpu")
        trainer.train(loaders["train_id"], loaders["val_id"])

        out_dir = Path(tmpdir) / "metrics_out"
        metrics = evaluate_model(trainer, loaders, config["model"], t_cfg, output_dir=out_dir)

        for key in STAGE1_CANONICAL_METRIC_KEYS:
            assert key in metrics, f"Missing canonical key: {key}"

        assert (out_dir / "metrics.json").exists()
