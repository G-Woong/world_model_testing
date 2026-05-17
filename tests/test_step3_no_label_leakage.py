from __future__ import annotations

import dataclasses
import random
from typing import Any

from frcgw.schemas.step_schema import PublicObservation
from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS
from frcgw.text_env.collector import CollectorConfig, collect_episode
from frcgw.text_env.generator import EpisodeSpecGenerator, TaskFamily


def _collect(family: str = TaskFamily.MODAL_BLOCKER, *, ood_type: str | None = None):
    gen = EpisodeSpecGenerator(seed=211)
    spec = gen.generate(family=family)
    if ood_type is not None:
        spec = dataclasses.replace(spec, ood_type=ood_type)
    runner = _FixedRunner(_ProbePolicy())
    episode = collect_episode(
        spec,
        runner,
        random.Random(spec.seed),
        CollectorConfig(split_id="test_ood" if ood_type else "test_id"),
    )
    return episode, runner.policy


def _all_public_values(value: Any) -> list[str]:
    if dataclasses.is_dataclass(value):
        return _all_public_values(dataclasses.asdict(value))
    if isinstance(value, dict):
        values: list[str] = []
        for key, item in value.items():
            values.append(str(key))
            values.extend(_all_public_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_all_public_values(item))
        return values
    if value is None:
        return []
    return [str(value)]


class _ProbePolicy:
    policy_id = "random_constrained_probe"
    last_selected_hypothesis_id = None
    last_selected_hypothesis_type = None
    last_selected_hypothesis_confidence = None
    last_selected_hypothesis_source = None

    def __init__(self) -> None:
        self.seen_observations: list[PublicObservation] = []

    def select(self, obs, history, state, engine, rng):
        self.seen_observations.append(obs)
        return rng.choice(obs.candidate_actions_public).action_type


class _FixedRunner:
    def __init__(self, policy: _ProbePolicy) -> None:
        self.policy = policy

    def sample_policy(self, spec):
        return self.policy

    def policy_mixture_snapshot(self) -> dict[str, float]:
        return {self.policy.policy_id: 1.0}


def test_public_input_does_not_contain_eval_labels() -> None:
    episode, _ = _collect()
    eval_field_names = {
        "evaluation_labels",
        "eval_labels",
        "hypothesis_update_timestamp",
        "recovery_timestamp",
        "true_wrong_hypothesis",
        "correct_hypothesis_id",
        "evidence_timestamp",
    }

    for step in episode.steps:
        public = dataclasses.asdict(step.public_observation)
        assert eval_field_names.isdisjoint(_all_public_values(public))


def test_public_input_does_not_contain_ood_type() -> None:
    episode, _ = _collect(TaskFamily.NESTED_SCROLL, ood_type="grammar_shift")

    for step in episode.steps:
        public_text = " ".join(_all_public_values(step.public_observation))
        assert "ood_type" not in public_text
        assert "grammar_shift" not in public_text


def test_candidate_actions_do_not_contain_oracle_labels() -> None:
    episode, _ = _collect()

    for step in episode.steps:
        for action in step.public_observation.candidate_actions_public:
            action_dict = dataclasses.asdict(action)
            assert set(action_dict).isdisjoint(FORBIDDEN_AGENT_FIELDS)
            assert set(_all_public_values(action_dict)).isdisjoint(FORBIDDEN_AGENT_FIELDS)


def test_eval_labels_not_passed_to_non_oracle_agent() -> None:
    _, policy = _collect()

    assert policy.seen_observations
    assert policy.last_selected_hypothesis_id is None
    for obs in policy.seen_observations:
        text = " ".join(_all_public_values(obs))
        assert "evaluation_labels" not in text
        assert "true_wrong_hypothesis" not in text


def test_visibility_forbidden_fields_still_mirror_hook() -> None:
    assert "ood_type" in FORBIDDEN_AGENT_FIELDS
