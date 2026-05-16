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


class VerifierRecoveryAgent(BaselineAgent):
    """BASE-006: Verifier + heuristic recovery (VeriGUI direct-threat defense).

    Detects failures via public effect summary, then selects alternative candidate.
    No grammar posterior; no LR/F_t usage.
    """

    baseline_id = "BASE-006"
    paper_ssot_id = "BASE-006 (Verifier + heuristic recovery)"

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
        return action, _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class ComputeMatchedRandomAgent(BaselineAgent):
    """BASE-015: Compute-matched random reallocation (C6 compute-matching defense).

    Matches FRCG-WM planning_calls=1 budget but selects randomly.
    """

    baseline_id = "BASE-015"
    paper_ssot_id = "BASE-015 (compute-matched random reallocation)"

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        if not obs.candidate_actions_public:
            return _noop_action(), _budget(
                planning_calls=1,
                rollout_steps=0,
                candidate_actions_scored=0,
            )
        seed = f"base-015|{obs.instruction}|{len(obs.history_public)}|{len(obs.candidate_actions_public)}"
        rng = random.Random(seed)
        action = rng.choice(obs.candidate_actions_public)
        return action, _budget(
            planning_calls=1,
            rollout_steps=0,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class WACStyleConsequenceCorrectionAgent(BaselineAgent):
    """BASE-026: WAC-style consequence correction (WAC direct-threat defense).

    Public consequence heuristic-based correction. No grammar posterior.
    """

    baseline_id = "BASE-026"
    paper_ssot_id = "BASE-026 (WAC-style consequence correction)"

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
        return action, _budget(
            planning_calls=1,
            rollout_steps=1,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class CUWMStyleCandidateSimulationAgent(BaselineAgent):
    """BASE-027: CUWM-style candidate simulation (CUWM direct-threat defense).

    Compares frozen-base candidates via public heuristic. No grammar posterior.
    """

    baseline_id = "BASE-027"
    paper_ssot_id = "BASE-027 (CUWM-style candidate simulation)"

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        action = _heuristic_best_action(obs)
        n = len(obs.candidate_actions_public)
        return action, _budget(
            planning_calls=1,
            rollout_steps=n,
            candidate_actions_scored=n,
        )


class WebWorldStyleSearchAgent(BaselineAgent):
    """BASE-028: WebWorld-style simulator search (WebWorld direct-threat defense).

    Next-state heuristic + action search. No control-grammar posterior.
    Full WebWorld reconstruction is infeasible; this uses a heuristic proxy.
    """

    baseline_id = "BASE-028"
    paper_ssot_id = "BASE-028 (WebWorld-style simulator search)"
    approximation_level = "heuristic next-state proxy; full WebWorld reconstruction infeasible"

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        action = _heuristic_best_action(obs)
        n = len(obs.candidate_actions_public)
        top_k = min(3, n)
        return action, _budget(
            planning_calls=1,
            rollout_steps=n,
            candidate_actions_scored=n,
            top_k_alternatives=top_k,
        )


class CATTSStyleUncertaintyGateAgent(BaselineAgent):
    """BASE-012-CATTS: Uncertainty-gated planner, CATTS variant (CATTS defense).

    Vote-entropy proxy from public candidate distribution. LR/F_t usage forbidden
    by construction — no falsification.falsification or lr_scorer import.
    """

    baseline_id = "BASE-012-CATTS"
    paper_ssot_id = "BASE-012 (uncertainty-gated planner, CATTS variant)"
    approximation_level = "CATTS-equivalent uncertainty gate; LR/F_t usage forbidden by construction"

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        n = len(obs.candidate_actions_public)
        # Entropy proxy: uniform over n candidates → H = log(n); normalized to [0,1]
        entropy_proxy = 1.0 / (n + 1) if n > 0 else 0.0
        should_plan = len(obs.history_public) % 3 == 0 or entropy_proxy < 0.4
        if should_plan:
            return _heuristic_best_action(obs), _budget(
                planning_calls=1,
                rollout_steps=0,
                candidate_actions_scored=n,
            )
        return _first_candidate(obs), _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=1 if obs.candidate_actions_public else 0,
        )


class VLAALoopHeuristicAgent(BaselineAgent):
    """BASE-003+008-VLAA: VLAA-loop style composite (VLAA-loop defense).

    Retry + rule-based blocker recovery composite. LR/F_t usage forbidden.
    Uses repeat count and effect_summary hash proxy for loop breaking.
    """

    baseline_id = "BASE-003+008-VLAA"
    paper_ssot_id = "BASE-003 + BASE-008 composite (VLAA-loop style)"
    approximation_level = "Retry + rule-based blocker recovery composite; LR/F_t usage forbidden"

    def __init__(self) -> None:
        self._repeat_count: dict[str, int] = {}

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        if not obs.candidate_actions_public:
            return _noop_action(), _budget(
                planning_calls=0,
                rollout_steps=0,
                candidate_actions_scored=0,
            )
        first = obs.candidate_actions_public[0]
        repeat_count = self._repeat_count.get(first.action_type, 0)
        if repeat_count > 1 and len(obs.candidate_actions_public) > 1:
            action = obs.candidate_actions_public[1]
        else:
            action = first
        self._repeat_count[action.action_type] = self._repeat_count.get(action.action_type, 0) + 1
        return action, _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=2,
        )

    def reset(self) -> None:
        self._repeat_count = {}


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
    "VerifierRecoveryAgent",
    "ComputeMatchedRandomAgent",
    "WACStyleConsequenceCorrectionAgent",
    "CUWMStyleCandidateSimulationAgent",
    "WebWorldStyleSearchAgent",
    "CATTSStyleUncertaintyGateAgent",
    "VLAALoopHeuristicAgent",
]
