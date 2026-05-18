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
from frcgw.evaluation.metrics import FORBIDDEN_AGENT_KEYS


def _load_module(module_name: str, path: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


lr_real = _load_module("lr_real_eval_runner_step8", "scripts/10_run_lr_real_eval.py")
c3_audit = _load_module("audit_step8_c3_root_cause", "scripts/audit_step8_c3_root_cause.py")


REQUIRED_TRACE_FIELDS = {
    "planner_F_t",
    "lr_scorer_F_t",
    "effect_type",
    "predicted_wrong",
    "wrong_prob",
    "h_exec_id",
    "h_alt_best_id",
    "degenerate_reason",
}


def _dataset_path(tmp_path: Path, effect_type: str = "state_change") -> Path:
    path = tmp_path / "episodes.jsonl"
    episode = {
        "episode_id": "ep0",
        "steps": [
            {
                "step_id": "ep0:0",
                "step_index": 0,
                "public_input": {
                    "instruction": "open panel",
                    "history_public": [
                        {
                            "step_index": 0,
                            "action_summary": "click",
                            "effect_summary": effect_type,
                        }
                    ],
                    "candidate_actions_public": [
                        {
                            "action_id": "a1",
                            "action_type": "click",
                            "action_params": {},
                        }
                    ],
                },
                "eval_labels": {"true_wrong_hypothesis": True},
                "targets": {"true_action_effect_type": "state_change"},
            }
        ],
    }
    path.write_text(json.dumps(episode) + "\n", encoding="utf-8")
    return path


def _result() -> EvaluationResult:
    return EvaluationResult(
        agent_id="STUB",
        split="test_id",
        seed=0,
        metrics={},
        compute_log=ComputeBudgetLog(0, 0, 0, 0, 0.0),
        n_episodes=1,
        report_path=None,
    )


def _write_trace(eval_dir: Path, rows: list[dict[str, Any]]) -> Path:
    per_step = eval_dir / "per_step"
    per_step.mkdir(parents=True)
    path = per_step / "STUB_seed0.jsonl"
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    return path


def test_trace_fields_present(tmp_path: Path) -> None:
    result = _result()
    trace_records = [
        {
            "action_id": "a1",
            "action_type": "click",
            "planner_F_t": 0.4,
            "lr_scorer_F_t": 0.3,
            "effect_type": "state_change",
            "f_t": 0.4,
            "tau_f": 0.5,
            "predicted_wrong": True,
            "wrong_prob": 0.45,
            "h_exec_id": 2,
            "h_alt_best_id": 5,
            "planning_calls": 0,
            "rollout_steps": 0,
        }
    ]

    lr_real._attach_trace_records(result, _dataset_path(tmp_path), trace_records)
    out_dir = tmp_path / "out"
    lr_real._write_per_step_jsonl(result, "STUB", 0, "test_id", out_dir)

    row = json.loads((out_dir / "per_step" / "STUB_seed0.jsonl").read_text(encoding="utf-8"))
    assert REQUIRED_TRACE_FIELDS <= set(row)
    assert row["planner_F_t"] == 0.4
    assert row["lr_scorer_F_t"] == 0.3
    assert row["effect_type"] == "state_change"
    assert row["predicted_wrong"] is True
    assert row["h_exec_id"] == 2
    assert row["h_alt_best_id"] == 5
    assert row["degenerate_reason"] is None
    assert not (set(row) & FORBIDDEN_AGENT_KEYS)


def test_degenerate_reason_explicit(tmp_path: Path) -> None:
    dataset = _dataset_path(tmp_path)
    eval_dir = tmp_path / "eval"
    _write_trace(
        eval_dir,
        [
            {
                "planner_F_t": 0.0,
                "lr_scorer_F_t": 0.0,
                "effect_type": "state_change",
                "predicted_wrong": False,
            },
            {
                "planner_F_t": 0.0,
                "lr_scorer_F_t": 0.0,
                "effect_type": "state_change",
                "predicted_wrong": False,
            },
        ],
    )

    report = c3_audit.run_audit(dataset, None, eval_dir, tmp_path / "audit.json")

    assert report["planner_F_t_variance"] == 0.0
    assert report["lr_scorer_F_t_variance"] == 0.0
    assert report["degenerate_reason"] == "mapping_miss"
    assert report["c3_status"] == "BLOCKED"


def test_mapping_coverage_non_zero(tmp_path: Path) -> None:
    dataset = _dataset_path(tmp_path, effect_type="no_state_change")
    eval_dir = tmp_path / "eval"
    _write_trace(
        eval_dir,
        [
            {
                "planner_F_t": 0.0,
                "lr_scorer_F_t": 0.5,
                "effect_type": "none",
                "predicted_wrong": False,
            },
            {
                "planner_F_t": 1.0,
                "lr_scorer_F_t": 1.5,
                "effect_type": "no_state_change",
                "predicted_wrong": True,
            },
        ],
    )

    report = c3_audit.run_audit(dataset, None, eval_dir, tmp_path / "audit.json")

    assert report["mapping_coverage"] == 0.0
    assert report["degenerate_reason"] == "zero_short_circuit"
    assert report["c3_status"] == "BLOCKED"
