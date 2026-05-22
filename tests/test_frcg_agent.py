from __future__ import annotations

from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.frcg_agent import TextFRCGModelAgent
from frcgw.models.text_frcg_model import TextFRCGModel
from frcgw.planning.decision_gate import GateConfig
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


def _obs(
    *,
    candidates: list[CandidateAction] | None = None,
) -> PublicObservation:
    return PublicObservation(
        instruction="click the right item",
        dom_snapshot_public={"visible": True},
        accessibility_tree_public={"role": "root"},
        candidate_actions_public=candidates
        if candidates is not None
        else [
            CandidateAction("a", "click", {"target": "left"}),
            CandidateAction("b", "click", {"target": "right"}),
        ],
    )


def test_text_frcg_model_agent_constructs_without_checkpoint() -> None:
    agent = TextFRCGModelAgent()

    assert isinstance(agent.model, TextFRCGModel)
    assert agent.baseline_id == "FRCG-FULL"


def test_act_returns_candidate_action_and_compute_budget_log() -> None:
    action, log = TextFRCGModelAgent().act(_obs())

    assert isinstance(action, CandidateAction)
    assert isinstance(log, ComputeBudgetLog)


def test_act_with_empty_candidates_returns_noop_action() -> None:
    action, log = TextFRCGModelAgent().act(_obs(candidates=[]))

    assert action == CandidateAction("noop", "noop", {})
    assert isinstance(log, ComputeBudgetLog)


def test_act_with_two_candidates_returns_one_of_them() -> None:
    obs = _obs()

    action, _log = TextFRCGModelAgent(gate_config=GateConfig(gate_mode="never_plan")).act(obs)

    assert action in obs.candidate_actions_public


def test_planning_calls_is_zero_or_one_per_step() -> None:
    _action, log = TextFRCGModelAgent().act(_obs())

    assert log.planning_calls in {0, 1}


def test_reset_clears_episode_state() -> None:
    agent = TextFRCGModelAgent()
    agent.act(_obs())

    agent.reset()

    assert agent._step_idx == 0
    assert agent._last_F_t == 0.0
    assert agent.last_predicted_wrong is False


def test_last_predicted_wrong_is_bool_and_last_f_t_is_float() -> None:
    agent = TextFRCGModelAgent()

    agent.act(_obs())

    assert isinstance(agent.last_predicted_wrong, bool)
    assert isinstance(agent.last_F_t, float)


def test_eval_labels_are_accepted_and_do_not_affect_action_selection() -> None:
    obs = _obs()
    agent = TextFRCGModelAgent(gate_config=GateConfig(gate_mode="never_plan"))

    action_without_labels, _log = agent.act(obs)
    agent.reset()
    action_with_labels, _log = agent.act(obs, eval_labels={"oracle_best_action": "click"})

    assert action_with_labels == action_without_labels


def test_forbidden_named_extra_observation_attribute_is_not_read() -> None:
    obs = _obs()
    obs.oracle_best_action = "hidden-label"  # type: ignore[attr-defined]

    action, log = TextFRCGModelAgent(gate_config=GateConfig(gate_mode="never_plan")).act(obs)

    assert isinstance(action, CandidateAction)
    assert isinstance(log, ComputeBudgetLog)


def test_never_plan_gate_config_reports_zero_planning_calls() -> None:
    _action, log = TextFRCGModelAgent(
        gate_config=GateConfig(gate_mode="never_plan")
    ).act(_obs())

    assert log.planning_calls == 0


def test_always_plan_gate_config_reports_one_planning_call() -> None:
    _action, log = TextFRCGModelAgent(
        gate_config=GateConfig(gate_mode="always_plan")
    ).act(_obs())

    assert log.planning_calls == 1
