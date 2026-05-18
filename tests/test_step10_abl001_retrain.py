from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_abl001_train_config_exists() -> None:
    assert (REPO_ROOT / "configs" / "train_text_v0_4_abl001.yaml").exists()


def test_abl001_eval_config_exists() -> None:
    assert (REPO_ROOT / "configs" / "lr_eval_step10_abl001.yaml").exists()


def test_abl001_retrain_script_exists() -> None:
    assert (REPO_ROOT / "scripts" / "risk_hunt" / "run_abl001_retrain.py").exists()


def test_abl001_eval_config_has_regime_metric() -> None:
    config_path = REPO_ROOT / "configs" / "lr_eval_step10_abl001.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert "regime_shift_f1" in config["metrics"]
