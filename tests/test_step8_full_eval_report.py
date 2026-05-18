from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.evaluation.ablations import (
    ABLATION_REGISTRY,
    LeakageSanityProbeAblation,
)
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


SCRIPT_PATH = ROOT / "scripts" / "run_step8_full_eval_report.py"


def _load_report_module() -> Any:
    spec = importlib.util.spec_from_file_location("step8_full_eval_report", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_metrics(input_dir: Path, agent_id: str, seed: int, split: str, base: float) -> None:
    run_dir = input_dir / f"{agent_id}_seed{seed}_{split}"
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "agents": {
            agent_id: {
                "task_success_rate": {"value": base},
                "C3_falsification_precision": {"value": base + 0.01},
                "C3_falsification_recall": {"value": base + 0.02},
                "ood_shift_f1": {"f1": base + 0.03},
                "C6_progress_per_compute": {"value": base + 0.04},
                "false_planning_call_rate": {"value": base + 0.05},
            }
        }
    }
    (run_dir / "metrics.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_config(tmp_path: Path, input_dir: Path) -> Path:
    config_path = tmp_path / "step8_full_report.yaml"
    config_path.write_text(
        f"step8_ablation_out_dir: {input_dir.as_posix()}\n",
        encoding="utf-8",
    )
    return config_path


def test_summary_json_schema(tmp_path: Path) -> None:
    module = _load_report_module()
    input_dir = tmp_path / "p3_lr_real_eval_step8_ablations"
    out_dir = tmp_path / "p3_lr_real_eval_step8_full_report"
    config_path = _write_config(tmp_path, input_dir)
    seeds = [0, 1, 2, 3, 4]
    splits = ["test_id", "test_ood"]

    for seed in seeds:
        for split in splits:
            _write_metrics(input_dir, "FRCG-LR", seed, split, 0.10 + seed / 10)

    assert (
        module.main(
            [
                "--config",
                str(config_path),
                "--agents",
                "FRCG-LR",
                "--out-dir",
                str(out_dir),
                "--seeds",
                *[str(seed) for seed in seeds],
                "--splits",
                *splits,
            ]
        )
        == 0
    )

    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert set(summary) == {"agents", "positive_control", "metadata"}
    assert "FRCG-LR" in summary["agents"]
    agent_summary = summary["agents"]["FRCG-LR"]
    assert set(agent_summary["mean"]) == set(module.SUMMARY_METRICS)
    assert set(agent_summary["std"]) == set(module.SUMMARY_METRICS)
    assert agent_summary["n_seeds"] == 5
    assert agent_summary["count_missing"] == 0
    assert set(agent_summary["splits"]) == set(splits)
    assert agent_summary["mean"]["task_success_rate"] == pytest.approx(0.30)
    assert (out_dir / "summary_human.md").exists()


def test_abl040_isolated(tmp_path: Path) -> None:
    module = _load_report_module()
    input_dir = tmp_path / "p3_lr_real_eval_step8_ablations"
    out_dir = tmp_path / "p3_lr_real_eval_step8_full_report"
    config_path = _write_config(tmp_path, input_dir)
    _write_metrics(input_dir, "FRCG-LR", 0, "test_id", 0.2)
    _write_metrics(input_dir, "ABL-040", 0, "test_id", 0.9)

    module.main(
        [
            "--config",
            str(config_path),
            "--agents",
            "FRCG-LR",
            "ABL-040",
            "--out-dir",
            str(out_dir),
            "--seeds",
            "0",
            "--splits",
            "test_id",
        ]
    )

    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert "ABL-040" in summary["positive_control"]
    assert "ABL-040" not in summary["agents"]
    assert "FRCG-LR" in summary["agents"]


def test_injection_applied() -> None:
    class MockAgent:
        baseline_id = "mock"

        def __init__(self) -> None:
            self._last_selected_hypothesis_id = "base_hypothesis"

        def act(
            self,
            obs: PublicObservation,
            eval_labels: dict | None = None,
        ) -> tuple[CandidateAction, ComputeBudgetLog]:
            del obs, eval_labels
            self._last_selected_hypothesis_id = "base_hypothesis"
            return CandidateAction("a0", "click", {}), ComputeBudgetLog(0, 0, 1, 0, 0.0)

    obs = PublicObservation(
        instruction="test",
        candidate_actions_public=[CandidateAction("a0", "click", {})],
    )
    base_agent = MockAgent()
    base_agent.act(obs, {"true_control_grammar": "oracle_grammar"})
    assert base_agent._last_selected_hypothesis_id == "base_hypothesis"

    wrapped_inner = MockAgent()
    wrapped = LeakageSanityProbeAblation(
        wrapped_inner,
        ABLATION_REGISTRY["leakage_sanity_probe"],
    )
    wrapped.act(obs, {"true_control_grammar": "oracle_grammar"})

    assert wrapped._injection_applied_count > 0
    assert wrapped_inner._last_selected_hypothesis_id == "oracle_grammar"
