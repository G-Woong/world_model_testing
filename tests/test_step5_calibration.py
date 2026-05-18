from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.eval_runner import EvaluationResult


def _load_runner_module() -> Any:
    path = Path("scripts/10_run_lr_real_eval.py")
    spec = importlib.util.spec_from_file_location("lr_real_eval_runner_step5_c5", path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


lr_real = _load_runner_module()
_build_metrics_with_blocked_markers = lr_real._build_metrics_with_blocked_markers
_compute_c5_calibration_audit = lr_real._compute_c5_calibration_audit
_write_manifest = lr_real._write_manifest


def _dataset_audit() -> dict[str, Any]:
    return {
        "recovery_timestamp_coverage": 1,
        "hypothesis_update_timestamp_coverage": 1,
        "selected_hypothesis_confidence_coverage": 1,
        "counterfactual_coverage": 0,
        "ood_split_exists": False,
        "total_episodes_sampled": 1,
    }


def _config(ckpt_path: str | None) -> dict[str, Any]:
    return {
        "dataset_path": "data/frcgw_text/v0_3/test_id.jsonl",
        "split": "test_id",
        "seeds": [0],
        "agents": [
            {
                "id": "FRCG-LR",
                "class": "TextFRCGModelAgent",
                "ckpt_path": ckpt_path,
            }
        ],
        "metrics": ["falsification_calibration"],
        "forbidden_sources": [],
    }


def _result(
    agent_id: str,
    wrong_probs: list[float],
    f_t_values: list[float] | None = None,
    calibration: float = 0.025,
) -> EvaluationResult:
    f_t_values = f_t_values or [0.4] * len(wrong_probs)
    result = EvaluationResult(
        agent_id=agent_id,
        split="test_id",
        seed=0,
        metrics={"falsification_calibration": calibration},
        compute_log=ComputeBudgetLog(0, 0, 0, 0, 0.0),
        n_episodes=1,
        report_path=None,
    )
    result._real_eval_step_records = [  # type: ignore[attr-defined]
        {"wrong_prob": wrong_prob, "f_t": f_t}
        for wrong_prob, f_t in zip(wrong_probs, f_t_values)
    ]
    return result


def test_unique_2_marked_degenerate() -> None:
    wrong_probs = [0.034, 0.219089] * 4

    audit = _compute_c5_calibration_audit(wrong_probs)

    assert audit["unique_wrong_prob_count"] == 2
    assert audit["C5_calibration_status"] == "DEGENERATE_PREDICTOR"


def test_random_init_degenerate_or_untrained(tmp_path: Path) -> None:
    high_prob = (0.012 * 4) ** 0.5
    wrong_probs = [0.0, high_prob] * 4
    result = _result("FRCG-LR", wrong_probs)

    metrics = _build_metrics_with_blocked_markers(
        [("FRCG-LR", 0, result)],
        _config(None),
        _dataset_audit(),
    )
    manifest = _write_manifest(
        _config(None),
        tmp_path,
        metrics,
        "none_read",
        _dataset_audit(),
        write=False,
    )

    assert metrics["C5_calibration_audit"]["unique_wrong_prob_count"] == 2
    assert metrics["C5_calibration_audit"]["variance_wrong_prob"] == pytest.approx(0.012)
    assert metrics["C5_calibration_status"] == "DEGENERATE_OR_UNTRAINED"
    assert manifest["C5_calibration_status"] == "DEGENERATE_OR_UNTRAINED"


def test_ok_condition() -> None:
    wrong_probs = [0.0, 0.01, 0.02, 0.03, 0.37, 0.43, 0.76, 0.78]
    f_t_values = [0.4] * len(wrong_probs)

    audit = _compute_c5_calibration_audit(wrong_probs, f_t_values)

    assert audit["unique_wrong_prob_count"] == 8
    assert audit["mean_wrong_prob"] == pytest.approx(0.3)
    assert audit["mean_f_t"] == pytest.approx(0.4)
    assert audit["C5_calibration_status"] == "OK"


def test_abl017_counter_evidence_preserved() -> None:
    wrong_probs = [0.0, 0.01, 0.02, 0.03, 0.37, 0.43, 0.76, 0.78]
    config = {
        "dataset_path": "data/frcgw_text/v0_3/test_id.jsonl",
        "agents": [
            {
                "id": "ABL-017",
                "class": "TextFRCGModelAgent",
                "ablation": "no_intent_action_mapping",
                "ckpt_path": "trained.ckpt",
            }
        ],
    }
    result = _result("ABL-017", wrong_probs, calibration=0.123)

    metrics = _build_metrics_with_blocked_markers(
        [("ABL-017", 0, result)],
        config,
        _dataset_audit(),
    )

    assert metrics["C5_calibration_status"] == "OK"
    assert metrics["agents"]["ABL-017"]["C5_calibration_ece"] == {
        "value": pytest.approx(0.123),
        "status": "OK",
    }


def test_claim_block_on_degenerate() -> None:
    result = _result("FRCG-LR", [0.034, 0.219089] * 4)

    metrics = _build_metrics_with_blocked_markers(
        [("FRCG-LR", 0, result)],
        _config("trained.ckpt"),
        _dataset_audit(),
    )

    c5 = metrics["agents"]["FRCG-LR"]["C5_calibration_ece"]
    assert metrics["C5_calibration_status"] == "DEGENERATE_PREDICTOR"
    assert c5["status"].startswith("BLOCKED")
    assert c5["value"] is None
