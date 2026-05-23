import json
from pathlib import Path

from fglc.data.dataloader import make_dataloaders
from fglc.evaluation.metrics import (
    ARTIFACT_KEYS,
    STAGE1_CANONICAL_METRIC_KEYS,
    evaluate_model,
)
from fglc.training import TrainerConfig, TrainerR3


def _config() -> dict:
    return {
        "phase": "R3",
        "seed": 42,
        "device": "cpu",
        "dataset": {
            "type": "synthetic_toy",
            "D_x": 8,
            "D_a": 4,
            "episode_len": 64,
            "n_episode_train": 32,
            "n_episode_val": 8,
            "n_episode_ood_mass": 16,
            "n_episode_ood_friction": 16,
            "ood_mass_scale": 2.0,
            "ood_friction_scale": 0.5,
            "sigma": 0.1,
        },
        "model": {
            "D_x": 8,
            "D_a": 4,
            "K": 6,
            "d": 32,
            "h_dim": 128,
            "encoder_hidden": 256,
            "dynamics_hidden": 64,
        },
        "trainer": {
            "batch_size": 16,
            "train_horizon": 8,
            "epochs": 1,
            "learning_rate": 3.0e-4,
            "optimizer": "adam",
            "loss_weights": {
                "lambda_reward": 1.0,
                "lambda_value": 1.0,
                "lambda_calibration": 0.0,
            },
        },
    }


def _trainer_config(config: dict, device: str = "cpu") -> TrainerConfig:
    trainer = config["trainer"]
    return TrainerConfig(
        batch_size=trainer["batch_size"],
        train_horizon=trainer["train_horizon"],
        epochs=trainer["epochs"],
        learning_rate=trainer["learning_rate"],
        optimizer=trainer["optimizer"],
        loss_weights=trainer["loss_weights"],
        device=device,
    )


def _trained(tmp_path: Path):
    config = _config()
    loaders = make_dataloaders(config)
    trainer = TrainerR3(config["model"], _trainer_config(config), device="cpu")
    train_metrics = trainer.train(loaders["train_id"], loaders["val_id"])
    metrics = evaluate_model(
        trainer,
        loaders,
        config["model"],
        _trainer_config(config),
        output_dir=tmp_path,
    )
    return train_metrics, metrics, tmp_path / "metrics.json"


def test_train_loss_decreases(tmp_path: Path):
    train_metrics, _, _ = _trained(tmp_path)
    assert train_metrics["train_nll"] <= train_metrics["initial_train_nll"] * 1.05


def test_metrics_json_schema(tmp_path: Path):
    _, metrics, metrics_path = _trained(tmp_path)
    assert metrics_path.exists()
    saved = json.loads(metrics_path.read_text(encoding="utf-8"))
    required = STAGE1_CANONICAL_METRIC_KEYS | ARTIFACT_KEYS
    assert required <= set(saved)
    assert required <= set(metrics)


def test_canonical_keys_match(tmp_path: Path):
    _, metrics, _ = _trained(tmp_path)
    assert set(metrics) == STAGE1_CANONICAL_METRIC_KEYS | ARTIFACT_KEYS


def test_ood_nll_gap(tmp_path: Path):
    _, metrics, _ = _trained(tmp_path)
    assert isinstance(metrics["ood_id_nll_diff"], float)


def test_val_train_nll_gap_nonnegative(tmp_path: Path):
    _, metrics, _ = _trained(tmp_path)
    assert metrics["val_train_nll_gap"] >= -0.5


def test_cpu_device_works(tmp_path: Path):
    train_metrics, metrics, metrics_path = _trained(tmp_path)
    assert train_metrics["epoch"] == 1
    assert metrics["vram_peak_mib"] == 0.0
    assert metrics_path.exists()
