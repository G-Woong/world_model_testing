"""Validate and print STEP 8 faithful retrain commands."""
from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE2_CONFIG_PATH = REPO_ROOT / "configs" / "train_text_v0_4_long_stage2.yaml"
ABL015_CONFIG_PATH = REPO_ROOT / "configs" / "train_text_v0_4_abl015.yaml"

TRAINING_COMMAND = (
    "python scripts/02_train_text_smoke.py "
    "--config configs/train_text_v0_4_abl015.yaml "
    "--model-config configs/model_text.yaml "
    "--output-dir outputs/runs/p3_train_v0_4_abl015"
)
EXPECTED_CHECKPOINT_PATH = (
    "outputs/checkpoints/abl015_no_control_grammar_loss/checkpoint_best.pt"
)

ALLOWED_TOP_LEVEL_DIFFS = {
    "phase",
    "manifest_dir",
    "checkpoint_dir",
    "ablation",
    "notes",
}

# ABL-001/003 faithful retrain: STEP 9 queue. Not implemented here.


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"Missing config: {path.relative_to(REPO_ROOT).as_posix()}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"Config is not a mapping: {path.relative_to(REPO_ROOT).as_posix()}")
    return loaded


def _objective_weight(config: dict[str, Any], name: str) -> float:
    weights = config.get("objective_weights")
    if not isinstance(weights, dict):
        raise ValueError("Config objective_weights must be a mapping")
    value = weights.get(name)
    if not isinstance(value, (int, float)):
        raise ValueError(f"objective_weights.{name} must be numeric")
    return float(value)


def _normalized_for_stage2_comparison(
    abl015: dict[str, Any],
    stage2: dict[str, Any],
) -> dict[str, Any]:
    normalized = copy.deepcopy(abl015)
    for key in ALLOWED_TOP_LEVEL_DIFFS:
        normalized[key] = stage2.get(key)
    normalized["objective_weights"]["l_control_grammar"] = stage2["objective_weights"][
        "l_control_grammar"
    ]
    return normalized


def validate_abl015_config() -> None:
    stage2 = _load_config(STAGE2_CONFIG_PATH)
    abl015 = _load_config(ABL015_CONFIG_PATH)

    stage2_control = _objective_weight(stage2, "l_control_grammar")
    abl015_control = _objective_weight(abl015, "l_control_grammar")
    if stage2_control != 1.0:
        raise ValueError("Stage B objective_weights.l_control_grammar must be 1.0")
    if abl015_control != 0.0:
        raise ValueError("ABL-015 objective_weights.l_control_grammar must be 0.0")

    expected_values = {
        "phase": "CC-P3-STEP8-ABL015",
        "manifest_dir": "outputs/runs/p3_train_v0_4_abl015",
        "checkpoint_dir": "outputs/checkpoints/abl015_no_control_grammar_loss",
        "ablation": "ABL-015",
        "notes": (
            "ABL-015: no L_control_grammar faithful retrain. SSoT: "
            "10_EVALUATION_BASELINE_ABLATION.md 짠8 ABL-015. "
            "l_control_grammar=0.0, all other weights identical to Stage B."
        ),
    }
    for key, expected in expected_values.items():
        if abl015.get(key) != expected:
            raise ValueError(f"ABL-015 {key} mismatch: {abl015.get(key)!r}")

    normalized = _normalized_for_stage2_comparison(abl015, stage2)
    if normalized != stage2:
        raise ValueError(
            "ABL-015 config must differ from Stage B only by "
            "objective_weights.l_control_grammar and approved metadata fields"
        )


def main() -> int:
    try:
        validate_abl015_config()
    except ValueError as exc:
        print(f"Config validation failed: {exc}", file=sys.stderr)
        return 1

    print("ABL-015 config validation passed.")
    print(f"Training command: {TRAINING_COMMAND}")
    print(f"Expected checkpoint path: {EXPECTED_CHECKPOINT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
