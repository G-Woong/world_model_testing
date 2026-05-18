from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.evaluation import eval_runner
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.eval_runner import EvaluationRunner
from frcgw.evaluation.frcg_agent import TextFRCGModelAgent
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "risk_hunt" / "compute_foresight_causal.py"


def _load_compute_module() -> Any:
    spec = importlib.util.spec_from_file_location("compute_foresight_causal", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_foresight_causal_script_exists() -> None:
    assert SCRIPT_PATH.exists()


def test_action_changed_attr_default() -> None:
    agent = TextFRCGModelAgent()

    assert hasattr(agent, "last_action_changed_by_rollout")
    assert agent.last_action_changed_by_rollout is False


def test_eval_runner_records_field(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, list[dict[str, Any]]] = {}

    def capture_metric(episodes: list[dict[str, Any]]) -> float:
        captured["episodes"] = episodes
        return 0.0

    class StubAgent:
        baseline_id = "STUB"
        last_action_changed_by_rollout = False

        def act(self, obs: PublicObservation) -> tuple[CandidateAction, ComputeBudgetLog]:
            del obs
            self.last_action_changed_by_rollout = True
            return CandidateAction("a1", "click", {}), ComputeBudgetLog(0, 0, 1, 0, 0.0)

    monkeypatch.setitem(eval_runner.METRIC_FUNCTIONS, "capture_foresight", capture_metric)
    dataset_path = tmp_path / "episodes.jsonl"
    episode = {
        "episode_id": "ep0",
        "steps": [
            {
                "step_index": 0,
                "public_input": {
                    "instruction": "click submit",
                    "history_public": [],
                    "candidate_actions_public": [
                        {"action_id": "a1", "action_type": "click", "action_params": {}}
                    ],
                },
                "eval_labels": {},
                "targets": {"progress_delta": 0.0},
            }
        ],
    }
    dataset_path.write_text(json.dumps(episode) + "\n", encoding="utf-8")

    EvaluationRunner({"metrics": ["capture_foresight"]}).run(
        StubAgent(),
        dataset_path,
        "text_id",
        0,
    )

    scored_episode = captured["episodes"][0]
    step_result = scored_episode["steps"][0]
    assert step_result["action_changed_by_rollout"] is True
    assert scored_episode["total_action_changes"] == 1


def test_compute_foresight_causal_empty_dir(tmp_path: Path) -> None:
    module = _load_compute_module()

    result = module.compute(str(tmp_path))

    assert result == {
        "divergence_rate": 0.0,
        "changed_steps": 0,
        "total_steps": 0,
    }
