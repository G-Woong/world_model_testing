"""frcgw.text_env.policies — Policy classes and mixture runner.

Source docs:
- paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md §8, §19
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md §7 buckets, §10
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §4 visibility
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod

from frcgw.schemas.step_schema import CandidateAction, PublicHistoryItem, PublicObservation
from frcgw.text_env.grammar import GrammarEngine
from frcgw.text_env.state import TextEpisodeSpec, TextState


class Policy(ABC):
    policy_id: str

    @abstractmethod
    def select(
        self,
        obs: PublicObservation,
        history: list[PublicHistoryItem],
        state: TextState,          # hidden fields available to collector; NOT written to obs
        engine: GrammarEngine,
        rng: random.Random,
    ) -> str:
        """Return action_type string. Must not write hidden tokens to obs."""


class OraclePolicy(Policy):
    """Always selects the correct next action according to the hidden grammar."""
    policy_id = "oracle"

    def select(self, obs, history, state, engine, rng):
        recovery = engine.label_recovery_action(state._hidden_preconditions)
        if recovery and recovery in {a.action_type for a in obs.candidate_actions_public}:
            return recovery
        return obs.candidate_actions_public[0].action_type


class WrongGrammarPolicy(Policy):
    """Repeatedly selects the final action without satisfying preconditions.

    This produces wrong-grammar failure trajectories with
    repeated_invalid_mapping_flag=True.
    """
    policy_id = "wrong_grammar"

    def select(self, obs, history, state, engine, rng):
        rules = engine._rules
        final = rules["final_action"]
        if final in {a.action_type for a in obs.candidate_actions_public}:
            return final
        return rng.choice(obs.candidate_actions_public).action_type


class RetryPolicy(Policy):
    """Repeats the last action (or picks arbitrarily on first step)."""
    policy_id = "retry"

    def select(self, obs, history, state, engine, rng):
        if history:
            last = history[-1].action_summary
            if last in {a.action_type for a in obs.candidate_actions_public}:
                return last
        return rng.choice(obs.candidate_actions_public).action_type


class RecoveryPolicy(Policy):
    """Wrong grammar first, then switches to correct grammar after evidence.

    Produces true_valid_hypothesis_switch=True trajectories.
    """
    policy_id = "recovery"

    def __init__(self, switch_after_failures: int = 2) -> None:
        self._switch_after = switch_after_failures

    def select(self, obs, history, state, engine, rng):
        failed_count = sum(
            1 for h in history
            if h.effect_summary == "no_state_change"
        )
        if failed_count < self._switch_after:
            # Wrong grammar phase
            wp = WrongGrammarPolicy()
            return wp.select(obs, history, state, engine, rng)
        # Recovery phase — switch to oracle
        op = OraclePolicy()
        return op.select(obs, history, state, engine, rng)


class RandomConstrainedPolicy(Policy):
    """Uniformly random over candidate actions."""
    policy_id = "random_constrained"

    def select(self, obs, history, state, engine, rng):
        return rng.choice(obs.candidate_actions_public).action_type


# ---------------------------------------------------------------------------
# PolicyMixtureRunner
# ---------------------------------------------------------------------------

_DEFAULT_MIXTURE: dict[str, float] = {
    "oracle":             0.20,
    "wrong_grammar":      0.25,
    "retry":              0.25,
    "recovery":           0.20,
    "random_constrained": 0.10,
}

_POLICY_INSTANCES: dict[str, Policy] = {
    "oracle":             OraclePolicy(),
    "wrong_grammar":      WrongGrammarPolicy(),
    "retry":              RetryPolicy(),
    "recovery":           RecoveryPolicy(),
    "random_constrained": RandomConstrainedPolicy(),
}


class PolicyMixtureRunner:
    """Samples a policy per episode according to the mixture distribution.

    coverage_oversample() preferentially samples a policy that fills
    under-represented coverage buckets (12.md §16).
    """

    def __init__(
        self,
        mixture: dict[str, float] | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self._mixture = mixture or dict(_DEFAULT_MIXTURE)
        self._rng = rng or random.Random()
        self._counts: dict[str, int] = {k: 0 for k in self._mixture}

    def sample_policy(self, spec: TextEpisodeSpec) -> Policy:
        policy_id = self._weighted_sample(self._mixture)
        self._counts[policy_id] = self._counts.get(policy_id, 0) + 1
        return _POLICY_INSTANCES[policy_id]

    def coverage_oversample(
        self,
        current_coverage: dict[str, float],
        targets: dict[str, float],
    ) -> Policy | None:
        """Return a priority policy if any coverage bucket is below 80% of target."""
        _bucket_to_policy = {
            "failed_action_ratio":            "wrong_grammar",
            "recovery_ratio":                 "recovery",
            "repeated_wrong_mapping_ratio":   "wrong_grammar",
            "shift_ratio":                    "recovery",
        }
        for bucket, policy_id in _bucket_to_policy.items():
            target = targets.get(bucket, 0.0)
            current = current_coverage.get(bucket, 0.0)
            if target > 0 and current < 0.8 * target:
                return _POLICY_INSTANCES[policy_id]
        return None

    def policy_mixture_snapshot(self) -> dict:
        total = sum(self._counts.values()) or 1
        return {k: round(v / total, 4) for k, v in self._counts.items()}

    def _weighted_sample(self, weights: dict[str, float]) -> str:
        keys = list(weights.keys())
        vals = [weights[k] for k in keys]
        return self._rng.choices(keys, weights=vals, k=1)[0]
