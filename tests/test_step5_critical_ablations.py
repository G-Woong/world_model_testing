from __future__ import annotations

from frcgw.evaluation.ablations import ABLATION_REGISTRY, _WRAPPERS, apply_ablation
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.schemas.step_schema import CandidateAction, PublicHistoryItem, PublicObservation


class CapturingAgent:
    baseline_id = "mock-agent"

    def __init__(self) -> None:
        self.received_obs: PublicObservation | None = None
        self._last_selected_hypothesis_id: str | None = None

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        self.received_obs = obs
        return obs.candidate_actions_public[0], ComputeBudgetLog(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=1,
            top_k_alternatives=0,
            wall_clock_seconds=0.0,
        )


def _obs() -> PublicObservation:
    return PublicObservation(
        instruction="find the visible result",
        dom_snapshot_public={"visible": True},
        accessibility_tree_public={"role": "root"},
        screenshot_ref="screen-1",
        history_public=[
            PublicHistoryItem(
                step_index=0,
                action_summary="clicked search",
                effect_summary="some_effect",
            ),
            PublicHistoryItem(
                step_index=1,
                action_summary="opened details",
                effect_summary="another_effect",
            ),
        ],
        candidate_actions_public=[
            CandidateAction("direct_search", "click", {"target": "search"}),
            CandidateAction("open_filter", "click", {"target": "filter"}),
        ],
    )


def test_abl011_registered() -> None:
    assert "no_action_effect_log" in ABLATION_REGISTRY
    assert "no_action_effect_log" in _WRAPPERS


def test_abl015_registered() -> None:
    assert "no_control_grammar_loss" in ABLATION_REGISTRY
    assert "no_control_grammar_loss" in _WRAPPERS


def test_abl040_registered() -> None:
    assert "leakage_sanity_probe" in ABLATION_REGISTRY
    assert "leakage_sanity_probe" in _WRAPPERS


def test_abl011_dispatch_zeros_effect_summary() -> None:
    inner_agent = CapturingAgent()
    agent = apply_ablation(inner_agent, ABLATION_REGISTRY["no_action_effect_log"])
    obs = _obs()

    agent.act(obs)

    assert inner_agent.received_obs is not None
    assert inner_agent.received_obs is not obs
    assert all(item.effect_summary is None for item in inner_agent.received_obs.history_public)
    assert [item.effect_summary for item in obs.history_public] == [
        "some_effect",
        "another_effect",
    ]


def test_abl040_leakage_probe_overrides_hypothesis() -> None:
    inner_agent = CapturingAgent()
    agent = apply_ablation(inner_agent, ABLATION_REGISTRY["leakage_sanity_probe"])

    agent.act(_obs(), eval_labels={"true_control_grammar": "direct_search"})

    assert inner_agent._last_selected_hypothesis_id == "direct_search"
