from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.eval_runner import EvaluationResult


def _load_runner_module() -> Any:
    path = Path("scripts/10_run_lr_real_eval.py")
    spec = importlib.util.spec_from_file_location("lr_real_eval_runner_step4_b5", path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


lr_real = _load_runner_module()
_build_metrics_with_blocked_markers = lr_real._build_metrics_with_blocked_markers
_compute_c5_calibration_audit = lr_real._compute_c5_calibration_audit
_write_ece_degenerate_predictor_audit = lr_real._write_ece_degenerate_predictor_audit


def _dataset_audit() -> dict[str, Any]:
    return {
        "recovery_timestamp_coverage": 0,
        "hypothesis_update_timestamp_coverage": 0,
        "selected_hypothesis_confidence_coverage": 1,
        "counterfactual_coverage": 0,
        "ood_split_exists": False,
        "total_episodes_sampled": 1,
    }


def _result(wrong_probs: list[float]) -> EvaluationResult:
    result = EvaluationResult(
        agent_id="STUB",
        split="test_id",
        seed=0,
        metrics={"falsification_calibration": 0.025},
        compute_log=ComputeBudgetLog(0, 0, 0, 0, 0.0),
        n_episodes=1,
        report_path=None,
    )
    result._real_eval_step_records = [  # type: ignore[attr-defined]
        {"wrong_prob": wrong_prob}
        for wrong_prob in wrong_probs
    ]
    return result


def test_c5_status_degenerate_when_wrong_prob_constant() -> None:
    audit = _compute_c5_calibration_audit([0.0] * 50)

    assert audit["C5_calibration_status"] == "DEGENERATE_PREDICTOR"


def test_c5_status_ok_when_wrong_prob_distributed() -> None:
    audit = _compute_c5_calibration_audit([0.1, 0.9, 0.5, 0.3, 0.7])

    assert audit["C5_calibration_status"] == "OK"


def test_ece_artifact_audit_json_written(tmp_path: Path) -> None:
    audit = _compute_c5_calibration_audit([0.0] * 3)

    path = _write_ece_degenerate_predictor_audit(audit, tmp_path)

    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "C5_calibration_status" in data
    assert "variance_wrong_prob" in data


def test_c5_claim_blocked_when_degenerate(tmp_path: Path) -> None:
    metrics = _build_metrics_with_blocked_markers(
        [("STUB", 0, _result([0.0] * 50))],
        {},
        _dataset_audit(),
    )
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")
    written = json.loads(metrics_path.read_text(encoding="utf-8"))

    c5 = written["agents"]["STUB"]["C5_calibration_ece"]
    assert written["C5_calibration_status"] == "DEGENERATE_PREDICTOR"
    assert c5["status"] == "BLOCKED_DEGENERATE_PREDICTOR"
    assert c5["value"] is None
