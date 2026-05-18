"""Tests for STEP 5 pretraining configs and monitoring hooks."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from frcgw.training.monitoring import (  # noqa: E402
    check_f_t_variance,
    check_grad_norm,
    check_losses_finite,
)


def _load_config(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_v0_3_config_schema() -> None:
    cfg = _load_config("configs/train_text_v0_3.yaml")
    assert cfg["max_steps"] == 200
    assert cfg["max_epochs"] == 3
    assert cfg["seed"] == 42
    assert cfg["data_config"]


def test_stage2_config_schema() -> None:
    cfg = _load_config("configs/train_text_v0_3_stage2.yaml")
    assert cfg["max_steps"] == 500
    assert cfg["max_epochs"] == 5
    assert cfg["seed"] == 42


def test_monitoring_losses_finite() -> None:
    assert check_losses_finite([1.0, 0.5, 0.2]) is True
    assert check_losses_finite([float("nan")]) is False


def test_monitoring_grad_norm() -> None:
    assert check_grad_norm(50.0) is True
    assert check_grad_norm(101.0) is False


def test_monitoring_f_t_variance() -> None:
    assert check_f_t_variance([0.0, 0.02, 0.04]) == "OK"
    assert check_f_t_variance([1.0, 1.0 + 1e-7, 1.0 + 2e-7]) == "DEGENERATE_LOW_VARIANCE"
    assert check_f_t_variance([math.nan, 1.0, 2.0]) == "DEGENERATE_LOW_VARIANCE"
    assert check_f_t_variance([1.0, 2.0]) == "INSUFFICIENT_DATA"
