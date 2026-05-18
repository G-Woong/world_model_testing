"""Tests for STEP 8 faithful retrain ablation configs."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIGS_DIR = ROOT / "configs"

ALLOWED_TOP_LEVEL_DIFFS = {
    "phase",
    "manifest_dir",
    "checkpoint_dir",
    "ablation",
    "notes",
}


def _load_config(name: str) -> dict[str, Any]:
    loaded = yaml.safe_load((CONFIGS_DIR / name).read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def test_abl015_config_diff_isolation() -> None:
    stage2 = _load_config("train_text_v0_4_long_stage2.yaml")
    abl015 = _load_config("train_text_v0_4_abl015.yaml")

    assert set(abl015) == set(stage2)
    assert set(abl015["objective_weights"]) == set(stage2["objective_weights"])
    assert stage2["objective_weights"]["l_control_grammar"] == 1.0
    assert abl015["objective_weights"]["l_control_grammar"] == 0.0

    for key in ALLOWED_TOP_LEVEL_DIFFS:
        assert abl015[key] != stage2[key]

    normalized = copy.deepcopy(abl015)
    for key in ALLOWED_TOP_LEVEL_DIFFS:
        normalized[key] = stage2[key]
    normalized["objective_weights"]["l_control_grammar"] = stage2["objective_weights"][
        "l_control_grammar"
    ]

    assert normalized == stage2


def test_abl015_ablation_field_set() -> None:
    cfg = _load_config("train_text_v0_4_abl015.yaml")
    assert cfg["ablation"] == "ABL-015"
