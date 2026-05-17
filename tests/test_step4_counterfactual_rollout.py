from __future__ import annotations

import copy
import random
from pathlib import Path

from frcgw.schemas.step_schema import CounterfactualRecord
from frcgw.text_env.collector import CollectorConfig, collect_episode
from frcgw.text_env.counterfactual_rollout import generate_counterfactuals
from frcgw.text_env.generator import EpisodeSpecGenerator, TaskFamily, build_initial_state
from frcgw.text_env.grammar import GrammarEngine


def _state_engine(family: str = TaskFamily.REQUIRED_DROPDOWN):
    gen = EpisodeSpecGenerator(seed=1039)
    spec = gen.generate(family=family)
    state = build_initial_state(spec)
    engine = GrammarEngine(spec.hidden_control_grammar)
    return state, engine


class _FirstActionPolicy:
    policy_id = "first_action_probe"
    last_selected_hypothesis_id = None
    last_selected_hypothesis_type = None
    last_selected_hypothesis_confidence = None
    last_selected_hypothesis_source = None

    def select(self, obs, history, state, engine, rng):
        return obs.candidate_actions_public[0].action_type


class _FixedRunner:
    def __init__(self, policy) -> None:
        self.policy = policy

    def sample_policy(self, spec):
        return self.policy

    def policy_mixture_snapshot(self) -> dict[str, float]:
        return {self.policy.policy_id: 1.0}


def _rollout(
    *,
    family: str = TaskFamily.REQUIRED_DROPDOWN,
    actual_action_id: str = "open_dropdown",
    top_k: int = 3,
    seed: int = 7,
) -> list[CounterfactualRecord]:
    state, engine = _state_engine(family)
    return generate_counterfactuals(
        pre_state=state,
        actual_action_id=actual_action_id,
        candidates=list(state.public_actions),
        engine=engine,
        top_k=top_k,
        rng=random.Random(seed),
    )


def test_counterfactuals_non_empty_when_alt_candidates_exist() -> None:
    gen = EpisodeSpecGenerator(seed=1045, max_steps=1)
    spec = gen.generate(family=TaskFamily.SEARCH_FORM)
    episode = collect_episode(
        spec,
        _FixedRunner(_FirstActionPolicy()),
        random.Random(spec.seed),
        CollectorConfig(split_id="test"),
    )

    assert len(episode.steps[0].public_observation.candidate_actions_public) == 3
    assert len(episode.steps[0].counterfactuals) >= 1


def test_counterfactuals_empty_when_no_alternatives() -> None:
    state, engine = _state_engine(TaskFamily.SEARCH_FORM)
    only_candidate = [state.public_actions[0]]

    records = generate_counterfactuals(
        pre_state=state,
        actual_action_id=only_candidate[0].action_id,
        candidates=only_candidate,
        engine=engine,
        rng=random.Random(1),
    )

    assert records == []


def test_top_k_limit_respected() -> None:
    records = _rollout(top_k=2)

    assert len(records) <= 2


def test_counterfactual_rollout_is_deterministic_for_seed() -> None:
    first = _rollout(seed=13)
    second = _rollout(seed=13)

    assert first == second


def test_counterfactual_engine_state_unchanged_after_rollout() -> None:
    state, engine = _state_engine()
    rules_before = copy.deepcopy(engine._rules)

    generate_counterfactuals(
        pre_state=state,
        actual_action_id="open_dropdown",
        candidates=list(state.public_actions),
        engine=engine,
        rng=random.Random(3),
    )

    assert engine._rules == rules_before


def test_is_oracle_best_exactly_one_true_when_non_empty() -> None:
    records = _rollout()

    assert records
    assert sum(1 for record in records if record.is_oracle_best) == 1


def test_counterfactual_effect_type_is_public_safe_enum() -> None:
    public_safe = {
        "state_change",
        "no_state_change",
        "blocker_removed",
        "delayed_effect",
        "task_complete",
    }

    assert {record.counterfactual_effect_type for record in _rollout()} <= public_safe


def test_counterfactual_failure_risk_in_unit_interval() -> None:
    records = _rollout()

    assert records
    for record in records:
        assert 0.0 <= record.counterfactual_failure_risk <= 1.0


def test_v0_2_data_not_overwritten() -> None:
    data_dir = Path("data/frcgw_text/v0_2")
    exists_before = data_dir.exists()
    mtime_before = data_dir.stat().st_mtime_ns if exists_before else None

    _rollout()

    assert data_dir.exists() is exists_before
    if exists_before:
        assert data_dir.stat().st_mtime_ns == mtime_before
