from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import torch
import yaml

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.eval_runner import EvaluationResult
from frcgw.evaluation.frcg_agent import TextFRCGModelAgent
from frcgw.planning.decision_gate import GateConfig
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


def _load_runner_module() -> Any:
    path = Path("scripts/10_run_lr_real_eval.py")
    spec = importlib.util.spec_from_file_location("lr_real_eval_runner_step3", path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


lr_real = _load_runner_module()
_TracingAgent = lr_real._TracingAgent
_attach_trace_records = lr_real._attach_trace_records


class StubModel:
    def to(self, device: str) -> "StubModel":
        del device
        return self

    def eval(self) -> None:
        pass

    def forward(self, obs: PublicObservation) -> Any:
        del obs
        return SimpleNamespace(z_grammar_logits=torch.tensor([[8.0, 0.0]]))


def _obs() -> PublicObservation:
    return PublicObservation(
        instruction="click submit",
        history_public=[],
        candidate_actions_public=[CandidateAction("a1", "click", {})],
    )


def _patch_plan(monkeypatch: pytest.MonkeyPatch, f_t: float) -> None:
    import frcgw.evaluation.frcg_agent as frcg_agent_module

    def fake_text_frcg_plan(
        obs: PublicObservation,
        step_idx: int,
        candidates: list[CandidateAction],
        model: Any,
        planner_state: Any,
        cfg: GateConfig,
    ) -> tuple[CandidateAction, Any]:
        del obs, step_idx, model, planner_state, cfg
        return candidates[0], SimpleNamespace(planned=False, F_t=f_t)

    monkeypatch.setattr(frcg_agent_module, "text_frcg_plan", fake_text_frcg_plan)


def _dataset_path(tmp_path: Path) -> Path:
    path = tmp_path / "episodes.jsonl"
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
                "eval_labels": {"true_wrong_hypothesis": True},
                "targets": {"true_action_effect_type": "unknown"},
            }
        ],
    }
    path.write_text(json.dumps(episode) + "\n", encoding="utf-8")
    return path


def test_predicted_wrong_equals_F_t_greater_than_tau_f(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_plan(monkeypatch, f_t=0.7)
    agent = TextFRCGModelAgent(model=StubModel(), gate_config=GateConfig(tau_f=0.5))

    agent.act(_obs())

    assert agent.last_predicted_wrong is True
    assert agent.last_F_t == 0.7
    assert agent.last_tau_f == 0.5


def test_predicted_wrong_false_when_F_t_below_tau_f(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_plan(monkeypatch, f_t=0.3)
    agent = TextFRCGModelAgent(model=StubModel(), gate_config=GateConfig(tau_f=0.5))

    agent.act(_obs())

    assert agent.last_predicted_wrong is False


def test_wrong_prob_equals_sigmoid_of_F_t_minus_tau_f(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_plan(monkeypatch, f_t=0.5)
    agent = TextFRCGModelAgent(model=StubModel(), gate_config=GateConfig(tau_f=0.5))

    agent.act(_obs())

    assert abs(agent.last_wrong_prob - 0.5) < 1e-6


def test_per_step_records_non_null_tau_f() -> None:
    class StubAgent:
        baseline_id = "STUB"
        last_predicted_wrong = True
        last_wrong_prob = 0.75
        last_F_t = 0.7
        _last_tau_f = 0.5

        def act(self, obs: PublicObservation) -> tuple[CandidateAction, ComputeBudgetLog]:
            del obs
            return CandidateAction("a1", "click", {}), ComputeBudgetLog(0, 0, 1, 0, 0.0)

    agent = _TracingAgent(StubAgent())

    agent.act(_obs())

    assert agent.records[0]["tau_f"] == 0.5


def test_per_step_records_f_t_from_plan_meta(tmp_path: Path) -> None:
    result = EvaluationResult(
        agent_id="STUB",
        split="test_id",
        seed=0,
        metrics={},
        compute_log=ComputeBudgetLog(0, 0, 0, 0, 0.0),
        n_episodes=1,
        report_path=None,
    )
    trace_records = [
        {
            "action_id": "a1",
            "action_type": "click",
            "f_t": 0.7,
            "tau_f": 0.5,
            "predicted_wrong": True,
            "wrong_prob": 0.55,
        }
    ]

    _attach_trace_records(result, _dataset_path(tmp_path), trace_records)

    record = result._real_eval_step_records[0]  # type: ignore[attr-defined]
    assert record["f_t"] == 0.7
    assert record["tau_f"] == 0.5


def test_manifest_uses_v0_2_dataset_path() -> None:
    cfg = yaml.safe_load(Path("configs/lr_eval_real_v0_2.yaml").read_text(encoding="utf-8"))

    assert cfg["dataset_path"] == "data/frcgw_text/v0_2/test_id.jsonl"


def test_abl023_predicted_wrong_does_not_collapse_to_full_model() -> None:
    from frcgw.evaluation import ablations

    if not issubclass(ablations.UncertaintyInsteadOfFalsificationAblation, TextFRCGModelAgent):
        pytest.skip("ABL-023 is independent; no regression risk.")

    assert ablations.UncertaintyInsteadOfFalsificationAblation.act is not TextFRCGModelAgent.act
