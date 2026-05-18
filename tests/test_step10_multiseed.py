"""STEP 10 multiseed launcher and eval config tests.

Source: TASK_1129_step10_n5_multiseed
Gate: RH-STAT-01 prerequisite
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "risk_hunt" / "run_multiseed_training.py"
CONFIG_PATH = REPO_ROOT / "configs" / "lr_eval_step10_multiseed.yaml"


def test_multiseed_script_exists() -> None:
    assert SCRIPT_PATH.is_file()


def test_multiseed_eval_config_exists() -> None:
    assert CONFIG_PATH.is_file()


def test_multiseed_eval_config_has_5_seeds() -> None:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    agents = config["agents"]
    assert len(agents) == 5
    assert [agent["id"] for agent in agents] == [
        "FRCG-LR-seed42",
        "FRCG-LR-seed123",
        "FRCG-LR-seed456",
        "FRCG-LR-seed789",
        "FRCG-LR-seed999",
    ]
    assert [agent["ckpt_path"] for agent in agents] == [
        "outputs/checkpoints/pretrain_v0_4_seed42/checkpoint_best.pt",
        "outputs/checkpoints/pretrain_v0_4_seed123/checkpoint_best.pt",
        "outputs/checkpoints/pretrain_v0_4_seed456/checkpoint_best.pt",
        "outputs/checkpoints/pretrain_v0_4_seed789/checkpoint_best.pt",
        "outputs/checkpoints/pretrain_v0_4_seed999/checkpoint_best.pt",
    ]


def test_multiseed_script_dry_run(tmp_path: pathlib.Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--dry-run", "--seeds", "42"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "[multiseed] seed=42" in result.stdout
    assert "DRY RUN:" in result.stdout
    assert "scripts/02_train_text_smoke.py" in result.stdout
