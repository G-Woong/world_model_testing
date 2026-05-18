"""Tests for STEP 8 long-horizon training configs and monitoring helpers."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import frcgw.training.train_text as train_text  # noqa: E402
from frcgw.training.monitoring import build_nan_repair_lr  # noqa: E402


CONFIGS_DIR = ROOT / "configs"


def _load_config(name: str) -> dict:
    return yaml.safe_load((CONFIGS_DIR / name).read_text(encoding="utf-8")) or {}


def test_stage_a_config_schema() -> None:
    cfg = _load_config("train_text_v0_4_long.yaml")
    required_keys = {
        "version",
        "phase",
        "seed",
        "batch_size",
        "max_steps",
        "max_epochs",
        "lr",
        "weight_decay",
        "model_config",
        "data_config",
        "dataset_version",
        "dataset_root",
        "split",
        "objective_weights",
        "manifest_dir",
        "checkpoint_dir",
        "monitoring",
        "gate_thresholds",
        "forbidden_fields",
    }
    assert required_keys <= set(cfg)
    assert cfg["max_steps"] == 1000
    assert cfg["max_epochs"] == 3
    assert cfg["dataset_version"] == "v0_4"
    assert cfg["dataset_root"] == "data/frcgw_text/v0_4"
    assert cfg["objective_weights"]["l_falsification"] == 1.0
    assert cfg["monitoring"]["nan_check"] is True
    assert cfg["monitoring"]["f_t_variance_check"] is True


def test_stage_b_config_has_higher_budget() -> None:
    stage_a = _load_config("train_text_v0_4_long.yaml")
    stage_b = _load_config("train_text_v0_4_long_stage2.yaml")
    assert stage_b["max_steps"] > stage_a["max_steps"]
    assert stage_b["max_epochs"] > stage_a["max_epochs"]
    assert stage_b["warm_start_checkpoint"] == (
        "outputs/checkpoints/pretrain_v0_4_long_stageA/checkpoint_best.pt"
    )


def test_monitoring_nan_repair_lr() -> None:
    assert build_nan_repair_lr(0.001, attempt=0) == 0.0005
    with pytest.raises(ValueError):
        build_nan_repair_lr(0.001, attempt=1)


def test_gradient_clipping_in_train_text() -> None:
    source = inspect.getsource(train_text.train_one_epoch)
    assert "clip_grad_norm_" in source
