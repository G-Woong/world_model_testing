from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.evaluation import eval_runner
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.schemas.step_schema import CandidateAction
from scripts import audit_step5_lr_reconciliation as audit


def _raw_step(step_index: int = 0, *, effect_type: str = "state_change") -> dict[str, Any]:
    return {
        "step_id": f"ep0_step_{step_index:03d}",
        "step_index": step_index,
        "public_observation": {
            "instruction": "open the panel",
            "history_public": [
                {
                    "step_index": max(0, step_index - 1),
                    "action_summary": "wait",
                    "effect_summary": effect_type,
                }
            ],
            "candidate_actions_public": [
                {
                    "action_id": "open",
                    "action_type": "click",
                    "action_params": {"target": "panel"},
                }
            ],
        },
        "action": {
            "action_id": "open",
            "action_type": "click",
            "selected_hypothesis_id": "h_model",
            "selected_hypothesis_type": "predicted",
            "selected_hypothesis_confidence": 0.7,
            "selected_hypothesis_source": "test",
        },
        "observed_effect_public": {
            "effect_type": effect_type,
            "dom_diff_public": {"panel": "open"},
            "text_diff_public": "panel opened",
        },
    }


def _write_dataset(tmp_path: Path, steps: list[dict[str, Any]] | None = None) -> Path:
    dataset = tmp_path / "test_id.jsonl"
    dataset.write_text(
        json.dumps({"episode_id": "ep0", "steps": steps or [_raw_step()]}) + "\n",
        encoding="utf-8",
    )
    return dataset


class _FakeAgent:
    def __init__(self, f_t_values: list[float]) -> None:
        self._f_t_values = f_t_values
        self._index = 0
        self.last_F_t = 0.0

    def reset(self) -> None:
        self._index = 0

    def act(self, obs: Any) -> None:
        del obs
        self.last_F_t = self._f_t_values[min(self._index, len(self._f_t_values) - 1)]
        self._index += 1


def _patch_trained_run(
    monkeypatch: pytest.MonkeyPatch,
    planner_f_t: float,
    lr_f_t: float,
) -> None:
    monkeypatch.setattr(audit, "_load_trained_agent", lambda ckpt_path: _FakeAgent([planner_f_t]))
    monkeypatch.setattr(audit, "_load_lr_components", lambda: ({"loaded": True}, None))
    monkeypatch.setattr(
        audit,
        "_lr_scorer_f_t",
        lambda step_record, lr_components, lr_import_error: (lr_f_t, True, None),
    )


def test_audit_json_written_on_ckpt_not_found(tmp_path: Path) -> None:
    dataset = _write_dataset(tmp_path)
    out_path = tmp_path / "step5.json"

    exit_code = audit.main(
        [
            "--dataset",
            str(dataset),
            "--ckpt-path",
            str(tmp_path / "missing_checkpoint.pt"),
            "--out",
            str(out_path),
        ]
    )

    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["status"] == "CKPT_NOT_FOUND"
    assert report["mean_abs_diff_trained"] is None


def test_dual_trace_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = _write_dataset(tmp_path)
    ckpt_path = tmp_path / "checkpoint.pt"
    ckpt_path.write_bytes(b"exists")
    out_path = tmp_path / "step5.json"
    _patch_trained_run(monkeypatch, planner_f_t=0.25, lr_f_t=0.2)

    report = audit.run_reconciliation(dataset, ckpt_path, out_path, max_episodes=1)

    assert report["status"] == "OK"
    assert report["steps"]
    assert "F_t_planner" in report["steps"][0]
    assert "F_t_lr_scorer" in report["steps"][0]


def test_degenerate_counter_fix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = _write_dataset(tmp_path, [_raw_step(index) for index in range(3)])

    class ZeroFtAgent:
        baseline_id = "ZERO_FT"
        last_predicted_wrong = False
        last_wrong_prob = 0.5
        last_F_t = 0.0

        def act(self, obs: Any) -> tuple[CandidateAction, ComputeBudgetLog]:
            del obs
            self.last_F_t = 0.0
            return CandidateAction("open", "click", {}), ComputeBudgetLog(0, 0, 0, 0, 0.0)

    monkeypatch.setitem(
        eval_runner.METRIC_FUNCTIONS,
        "debug_degenerate_f_t_count",
        lambda episodes: episodes[0]["degenerate_f_t_count"],
    )
    runner = eval_runner.EvaluationRunner({"metrics": ["debug_degenerate_f_t_count"]})

    result = runner.run(ZeroFtAgent(), dataset, "test_id", seed=0)

    assert result.metrics["debug_degenerate_f_t_count"] == 3.0


def test_c3_claim_blocked_on_divergence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _write_dataset(tmp_path)
    ckpt_path = tmp_path / "checkpoint.pt"
    ckpt_path.write_bytes(b"exists")
    out_path = tmp_path / "step5.json"
    _patch_trained_run(monkeypatch, planner_f_t=1.0, lr_f_t=0.0)

    report = audit.run_reconciliation(dataset, ckpt_path, out_path, max_episodes=1)

    assert report["interpretation"] == "DIVERGENCE_PERSISTS"
    assert report["C3_claim_status"] == "PRELIMINARY"


def test_no_step4_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = _write_dataset(tmp_path)
    step4_path = tmp_path / "step4_lr_comparison.json"
    original = '{"status": "existing"}\n'
    step4_path.write_text(original, encoding="utf-8")
    monkeypatch.setattr(audit, "STEP4_COMPARISON_PATH", str(step4_path))

    audit.run_reconciliation(
        dataset,
        tmp_path / "missing_checkpoint.pt",
        tmp_path / "step5.json",
        max_episodes=1,
    )

    assert step4_path.read_text(encoding="utf-8") == original
