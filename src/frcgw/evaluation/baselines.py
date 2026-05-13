"""Baseline agents for P3 evaluation.

Source docs:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7 BASE-001~028
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15 lines 993~1009
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod

from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


FORBIDDEN_AGENT_KEYS = {
    "true_regime",
    "true_control_grammar",
    "true_change_point",
    "true_reveal_vs_shift",
    "true_wrong_hypothesis",
    "counterfactual_action_effects",
    "oracle_regime_action",
    "oracle_grammar_action",
    "oracle_best_action",
    "split_id",
    "ood_type",
    "template_id",
    "seed",
    "policy_id",
    "audit_metadata",
}


def _noop_action() -> CandidateAction:
    return CandidateAction("noop", "noop", {})


def _first_candidate(obs: PublicObservation) -> CandidateAction:
    if obs.candidate_actions_public:
        return obs.candidate_actions_public[0]
    return _noop_action()


def _heuristic_best_action(obs: PublicObservation) -> CandidateAction:
    if not obs.candidate_actions_public:
        return _noop_action()
    return max(obs.candidate_actions_public, key=lambda action: len(action.action_id))


def _budget(
    *,
    planning_calls: int,
    rollout_steps: int,
    candidate_actions_scored: int,
    top_k_alternatives: int = 0,
) -> ComputeBudgetLog:
    return ComputeBudgetLog(
        planning_calls=planning_calls,
        rollout_steps=rollout_steps,
        candidate_actions_scored=candidate_actions_scored,
        top_k_alternatives=top_k_alternatives,
        wall_clock_seconds=0.0,
    )


class BaselineAgent(ABC):
    baseline_id: str

    @abstractmethod
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        ...

    def reset(self) -> None:
        """Reset any per-episode state."""
        pass


class FrozenBaseAgent(BaselineAgent):
    baseline_id = "BASE-001"

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _first_candidate(obs), _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=1,
        )


class ReactiveAgent(BaselineAgent):
    baseline_id = "BASE-002"

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _first_candidate(obs), _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=1,
        )


class RetryAfterFailureAgent(BaselineAgent):
    baseline_id = "BASE-003"

    def __init__(self) -> None:
        self._last_action_type: str | None = None

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        last_effect = ""
        if obs.history_public:
            last_effect = obs.history_public[-1].effect_summary or ""

        if "fail" in last_effect.lower() and len(obs.candidate_actions_public) > 1:
            action = obs.candidate_actions_public[1]
        else:
            action = _first_candidate(obs)

        self._last_action_type = action.action_type
        return action, _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=2,
        )

    def reset(self) -> None:
        self._last_action_type = None


class VerifierOnlyAgent(BaselineAgent):
    baseline_id = "BASE-005"

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _heuristic_best_action(obs), _budget(
            planning_calls=1,
            rollout_steps=0,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class NextStateWMOnlyAgent(BaselineAgent):
    baseline_id = "BASE-009"

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        if obs.candidate_actions_public:
            basis = len(obs.instruction) + len(obs.history_public) * 997
            rng = random.Random(basis)
            action = max(obs.candidate_actions_public, key=lambda _action: rng.random())
        else:
            action = _noop_action()

        return action, _budget(
            planning_calls=1,
            rollout_steps=len(obs.candidate_actions_public),
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class AlwaysPlanAgent(BaselineAgent):
    baseline_id = "BASE-010"

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _heuristic_best_action(obs), _budget(
            planning_calls=1,
            rollout_steps=0,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class UncertaintyGatedAgent(BaselineAgent):
    baseline_id = "BASE-012"

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        should_plan = len(obs.history_public) % 3 == 0
        if should_plan:
            return _heuristic_best_action(obs), _budget(
                planning_calls=1,
                rollout_steps=0,
                candidate_actions_scored=len(obs.candidate_actions_public),
            )

        return _first_candidate(obs), _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=1,
        )


class RandomAlternativePlannerAgent(BaselineAgent):
    baseline_id = "BASE-014"

    def __init__(self) -> None:
        self._rng = random.Random(0)

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        if obs.candidate_actions_public:
            action = self._rng.choice(obs.candidate_actions_public)
        else:
            action = _noop_action()

        return action, _budget(
            planning_calls=1,
            rollout_steps=0,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class OracleAgent(BaselineAgent):
    baseline_id = "BASE-016/017"

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        if eval_labels is None or not obs.candidate_actions_public:
            action = _first_candidate(obs)
        elif eval_labels.get("correct_hypothesis_id"):
            action = obs.candidate_actions_public[-1]
        else:
            action = obs.candidate_actions_public[0]

        return action, _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=1 if obs.candidate_actions_public else 0,
        )


__all__ = [
    "FORBIDDEN_AGENT_KEYS",
    "BaselineAgent",
    "FrozenBaseAgent",
    "ReactiveAgent",
    "RetryAfterFailureAgent",
    "VerifierOnlyAgent",
    "NextStateWMOnlyAgent",
    "AlwaysPlanAgent",
    "UncertaintyGatedAgent",
    "RandomAlternativePlannerAgent",
    "OracleAgent",
]
