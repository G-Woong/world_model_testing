from __future__ import annotations

import sys
from pathlib import Path

import yaml

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.evaluation.ablations import REAL_NO_GATE_ABLATION_CONFIG, RealNoGateAblation
from frcgw.evaluation.eval_runner import AGENT_CLASSES


CONFIG_PATH = Path("configs/lr_eval_step10_fair_compute.yaml")


def test_real_no_gate_ablation_class_exists() -> None:
    assert RealNoGateAblation.__name__ == "RealNoGateAblation"
    assert AGENT_CLASSES["RealNoGateAblation"] is RealNoGateAblation


def test_real_no_gate_ablation_id() -> None:
    assert REAL_NO_GATE_ABLATION_CONFIG.ablation_id == "real_no_gate"
    assert RealNoGateAblation.ablation_id == "real_no_gate"


def test_fair_compute_eval_config_exists() -> None:
    assert CONFIG_PATH.exists()


def test_fair_compute_config_has_fair_ppc() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

    assert "fair_ppc" in config["metrics"]
