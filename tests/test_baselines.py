from __future__ import annotations

import pytest

from frcgw.evaluation.baselines import (
    FORBIDDEN_AGENT_KEYS,
    AlwaysPlanAgent,
    BaselineAgent,
    CATTSStyleUncertaintyGateAgent,
    ComputeMatchedRandomAgent,
    CUWMStyleCandidateSimulationAgent,
    FrozenBaseAgent,
    NextStateWMOnlyAgent,
    OracleAgent,
    RandomAlternativePlannerAgent,
    ReactiveAgent,
    RetryAfterFailureAgent,
    UncertaintyGatedAgent,
    VerifierOnlyAgent,
    VerifierRecoveryAgent,
    VLAALoopHeuristicAgent,
    WACStyleConsequenceCorrectionAgent,
    WebWorldStyleSearchAgent,
)
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.schemas.step_schema import CandidateAction, PublicHistoryItem, PublicObservation


AGENT_CASES: list[tuple[type[BaselineAgent], str, int, int]] = [
    (FrozenBaseAgent, "BASE-001", 0, 0),
    (ReactiveAgent, "BASE-002", 0, 0),
    (RetryAfterFailureAgent, "BASE-003", 0, 0),
    (VerifierOnlyAgent, "BASE-005", 1, 0),
    (NextStateWMOnlyAgent, "BASE-009", 1, 2),
    (AlwaysPlanAgent, "BASE-010", 1, 0),
    (UncertaintyGatedAgent, "BASE-012", 1, 0),
    (RandomAlternativePlannerAgent, "BASE-014", 1, 0),
    (OracleAgent, "BASE-016/017", 0, 0),
    # Run 5 direct-threat baselines
    (VerifierRecoveryAgent, "BASE-006", 0, 0),
    (ComputeMatchedRandomAgent, "BASE-015", 1, 0),
    (WACStyleConsequenceCorrectionAgent, "BASE-026", 1, 1),
    (CUWMStyleCandidateSimulationAgent, "BASE-027", 1, 2),
    (WebWorldStyleSearchAgent, "BASE-028", 1, 2),
    (CATTSStyleUncertaintyGateAgent, "BASE-012-CATTS", 1, 0),
    (VLAALoopHeuristicAgent, "BASE-003+008-VLAA", 0, 0),
]


def _obs(
    *,
    candidates: list[CandidateAction] | None = None,
    history: list[PublicHistoryItem] | None = None,
) -> PublicObservation:
    return PublicObservation(
        instruction="click the right item",
        dom_snapshot_public={"visible": True},
        accessibility_tree_public={"role": "root"},
        screenshot_ref="screen-1",
        history_public=history or [],
        candidate_actions_public=candidates
        if candidates is not None
        else [
            CandidateAction("a", "click", {"target": "left"}),
            CandidateAction("longer-action-id", "click", {"target": "right"}),
        ],
    )


@pytest.mark.parametrize(
    ("agent_cls", "baseline_id", "planning_calls", "rollout_steps"),
    AGENT_CASES,
)
def test_baseline_agents_return_action_and_budget(
    agent_cls: type[BaselineAgent],
    baseline_id: str,
    planning_calls: int,
    rollout_steps: int,
) -> None:
    agent = agent_cls()

    action, log = agent.act(_obs())

    assert agent.baseline_id == baseline_id
    assert isinstance(action, CandidateAction)
    assert isinstance(log, ComputeBudgetLog)
    assert log.planning_calls == planning_calls
    assert log.rollout_steps == rollout_steps


@pytest.mark.parametrize("agent_cls", [case[0] for case in AGENT_CASES])
def test_baseline_agents_do_not_raise_with_empty_candidates(
    agent_cls: type[BaselineAgent],
) -> None:
    action, log = agent_cls().act(_obs(candidates=[]))

    assert isinstance(action, CandidateAction)
    assert action.action_id == "noop"
    assert isinstance(log, ComputeBudgetLog)


def test_retry_after_failure_uses_next_candidate_and_reset_clears_state() -> None:
    agent = RetryAfterFailureAgent()
    obs = _obs(
        history=[
            PublicHistoryItem(
                step_index=0,
                action_summary="clicked left",
                effect_summary="failed validation",
            )
        ]
    )

    action, _log = agent.act(obs)

    assert action.action_id == "longer-action-id"
    assert agent._last_action_type == "click"

    agent.reset()

    assert agent._last_action_type is None


def test_oracle_agent_without_eval_labels_falls_back() -> None:
    action, log = OracleAgent().act(_obs(), eval_labels=None)

    assert action.action_id == "a"
    assert log.planning_calls == 0


def test_oracle_agent_with_eval_labels_returns_valid_action() -> None:
    obs = _obs()

    action, log = OracleAgent().act(obs, eval_labels={"correct_hypothesis_id": "h1"})

    assert action in obs.candidate_actions_public
    assert action.action_id == "longer-action-id"
    assert log.rollout_steps == 0


def test_agents_do_not_store_forbidden_keys_as_instance_attributes() -> None:
    for agent_cls, _baseline_id, _planning_calls, _rollout_steps in AGENT_CASES:
        agent = agent_cls()
        agent.act(_obs())

        assert FORBIDDEN_AGENT_KEYS.isdisjoint(vars(agent))


def test_frozen_base_agent_has_zero_planning_budget() -> None:
    _action, log = FrozenBaseAgent().act(_obs())

    assert log.planning_calls == 0


def test_catts_and_vlaa_do_not_import_lr_scorer() -> None:
    import ast
    import inspect

    import frcgw.evaluation.baselines as baselines_mod

    source = inspect.getsource(baselines_mod)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert "lr_scorer" not in module, f"lr_scorer imported via 'from' in baselines: {module}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert "lr_scorer" not in alias.name, f"lr_scorer imported in baselines: {alias.name}"


def test_direct_threat_baselines_do_not_read_forbidden_eval_labels() -> None:
    direct_threat_agents = [
        WACStyleConsequenceCorrectionAgent(),
        CUWMStyleCandidateSimulationAgent(),
        WebWorldStyleSearchAgent(),
    ]
    hidden_labels = {k: "hidden_value" for k in FORBIDDEN_AGENT_KEYS}
    for agent in direct_threat_agents:
        action, log = agent.act(_obs(), eval_labels=hidden_labels)
        assert isinstance(action, CandidateAction)
        assert isinstance(log, ComputeBudgetLog)
        assert FORBIDDEN_AGENT_KEYS.isdisjoint(vars(agent))
