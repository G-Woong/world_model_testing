from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


def _load_runner_module() -> Any:
    path = Path("scripts/10_run_lr_real_eval.py")
    spec = importlib.util.spec_from_file_location("lr_real_eval_runner_step4_b4", path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


lr_real = _load_runner_module()
_TracingAgent = lr_real._TracingAgent


def _obs() -> PublicObservation:
    return PublicObservation(
        instruction="click submit",
        history_public=[],
        candidate_actions_public=[CandidateAction("a1", "click", {})],
    )


class HypothesisAgent:
    baseline_id = "STUB"
    last_predicted_wrong = False
    last_wrong_prob = 0.25
    last_F_t = 0.0
    _last_tau_f = 0.5
    _last_selected_hypothesis_id = "grammar_3"
    _last_selected_hypothesis_confidence = 0.75

    def act(self, obs: PublicObservation) -> tuple[CandidateAction, ComputeBudgetLog]:
        del obs
        return CandidateAction("a1", "click", {}), ComputeBudgetLog(0, 0, 1, 0, 0.0)


class NoHypothesisAgent:
    baseline_id = "STUB"
    last_predicted_wrong = False
    last_wrong_prob = 0.25
    last_F_t = 0.0
    _last_tau_f = 0.5

    def act(self, obs: PublicObservation) -> tuple[CandidateAction, ComputeBudgetLog]:
        del obs
        return CandidateAction("a1", "click", {}), ComputeBudgetLog(0, 0, 1, 0, 0.0)


def test_per_step_records_selected_hypothesis_id_when_agent_emits() -> None:
    agent = _TracingAgent(HypothesisAgent())

    agent.act(_obs())

    assert agent.records[0]["selected_hypothesis_id"] == "grammar_3"


def test_per_step_records_selected_hypothesis_confidence() -> None:
    agent = _TracingAgent(HypothesisAgent())

    agent.act(_obs())

    assert agent.records[0]["selected_hypothesis_confidence"] == 0.75


def test_per_step_null_when_agent_does_not_emit() -> None:
    agent = _TracingAgent(NoHypothesisAgent())

    agent.act(_obs())

    assert agent.records[0]["selected_hypothesis_id"] is None
