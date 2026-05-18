"""Tests for STEP 6 falsification-enabled training configs.

Verifies:
1. STEP 6 configs have l_falsification=1.0.
2. STEP 5 ABL-016 configs are unchanged (l_falsification=0.0).
3. STEP 6 eval config points to falsification checkpoint.
4. STEP 6 eval config out_dir does not conflict with STEP 5 outputs.
"""
from pathlib import Path

import pytest
import yaml


CONFIGS_DIR = Path(__file__).resolve().parents[1] / "configs"


def _load(name: str) -> dict:
    path = CONFIGS_DIR / name
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def test_falsification_stage1_config_l_falsification_is_1():
    cfg = _load("train_text_v0_3_falsification.yaml")
    assert cfg["objective_weights"]["l_falsification"] == 1.0, (
        "STEP 6 Stage 1 config must have l_falsification=1.0"
    )


def test_falsification_stage2_config_l_falsification_is_1():
    cfg = _load("train_text_v0_3_falsification_stage2.yaml")
    assert cfg["objective_weights"]["l_falsification"] == 1.0, (
        "STEP 6 Stage 2 config must have l_falsification=1.0"
    )


def test_step5_abl016_stage1_config_unchanged():
    """ABL-016 control (STEP 5) must remain l_falsification=0.0."""
    cfg = _load("train_text_v0_3.yaml")
    assert cfg["objective_weights"]["l_falsification"] == 0.0, (
        "STEP 5 Stage 1 (ABL-016 control) must have l_falsification=0.0 — immutable"
    )


def test_step5_abl016_stage2_config_unchanged():
    """ABL-016 control Stage 2 must remain l_falsification=0.0."""
    cfg = _load("train_text_v0_3_stage2.yaml")
    assert cfg["objective_weights"]["l_falsification"] == 0.0, (
        "STEP 5 Stage 2 (ABL-016 control) must have l_falsification=0.0 — immutable"
    )


def test_falsification_eval_config_ckpt_path():
    cfg = _load("lr_eval_real_v0_3_falsification.yaml")
    for agent in cfg.get("agents", []):
        ckpt = agent.get("ckpt_path")
        if ckpt is not None:
            assert "pretrain_v0_3_falsification" in ckpt, (
                f"Agent {agent.get('id')} ckpt_path should point to falsification checkpoint, got: {ckpt}"
            )


def test_falsification_eval_config_out_dir_not_step5():
    cfg = _load("lr_eval_real_v0_3_falsification.yaml")
    out_dir = cfg.get("out_dir", "")
    forbidden_patterns = ["step5", "p3_lr_real_eval_step4"]
    for pat in forbidden_patterns:
        assert pat not in out_dir, (
            f"STEP 6 eval out_dir must not conflict with STEP 5 outputs, found '{pat}' in '{out_dir}'"
        )


def test_falsification_stage1_config_phase_is_step6():
    cfg = _load("train_text_v0_3_falsification.yaml")
    assert "STEP6" in cfg.get("phase", "") or "step6" in cfg.get("phase", "").lower(), (
        "STEP 6 Stage 1 config phase should reference STEP6"
    )


def test_falsification_stage1_config_max_steps():
    cfg = _load("train_text_v0_3_falsification.yaml")
    assert cfg["max_steps"] >= 300, "STEP 6 Stage 1 should have max_steps >= 300"


def test_falsification_stage2_config_max_steps():
    cfg = _load("train_text_v0_3_falsification_stage2.yaml")
    assert cfg["max_steps"] >= 800, "STEP 6 Stage 2 should have max_steps >= 800"
