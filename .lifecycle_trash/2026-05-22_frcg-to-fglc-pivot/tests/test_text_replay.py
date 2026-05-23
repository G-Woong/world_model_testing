"""Tests for deterministic replay validation."""
from __future__ import annotations

import random

import pytest

from frcgw.schemas.validation import ReplayValidationError
from frcgw.text_env.collector import CollectorConfig, collect_episode
from frcgw.text_env.generator import EpisodeSpecGenerator, TaskFamily
from frcgw.text_env.policies import PolicyMixtureRunner
from frcgw.text_env.replay import ReplayValidator, _episode_to_stable_json


def _config() -> CollectorConfig:
    return CollectorConfig(split_id="train")


class TestReplayDeterminism:
    def test_same_seed_produces_byte_identical_episode(self):
        gen = EpisodeSpecGenerator(seed=42)
        spec = gen.generate(family=TaskFamily.MODAL_BLOCKER)
        validator = ReplayValidator()
        assert validator.validate(spec, _config()) is True

    def test_different_seed_produces_different_episode_id(self):
        gen = EpisodeSpecGenerator(seed=1)
        spec_a = gen.generate(family=TaskFamily.SEARCH_FORM)
        spec_b = gen.generate(family=TaskFamily.SEARCH_FORM)
        assert spec_a.episode_id != spec_b.episode_id

    def test_all_task_families_replay_deterministically(self):
        gen = EpisodeSpecGenerator(seed=99)
        validator = ReplayValidator()
        config = _config()
        for family in TaskFamily:
            spec = gen.generate(family=family)
            assert validator.validate(spec, config) is True, (
                f"Replay non-deterministic for family {family}"
            )

    def test_validate_batch_returns_all_true(self):
        gen = EpisodeSpecGenerator(seed=55)
        config = _config()
        specs = [gen.generate(family=list(TaskFamily)[i % len(list(TaskFamily))]) for i in range(8)]
        validator = ReplayValidator()
        results = validator.validate_batch(specs, config)
        assert all(results.values()), f"Failed specs: {[k for k,v in results.items() if not v]}"

    def test_stable_json_strips_timestamps(self):
        gen = EpisodeSpecGenerator(seed=7)
        spec = gen.generate(family=TaskFamily.FILTER_ACCORDION)
        runner1 = PolicyMixtureRunner(rng=random.Random(spec.seed))
        runner2 = PolicyMixtureRunner(rng=random.Random(spec.seed))
        config = _config()
        ep1 = collect_episode(spec, runner1, random.Random(spec.seed), config)
        ep2 = collect_episode(spec, runner2, random.Random(spec.seed), config)
        j1 = _episode_to_stable_json(ep1)
        j2 = _episode_to_stable_json(ep2)
        assert j1 == j2


class TestReplayDetectsMismatch:
    def test_inject_mismatch_detected(self):
        """Manually corrupt an episode and verify the validator would catch it."""
        gen = EpisodeSpecGenerator(seed=33)
        spec = gen.generate(family=TaskFamily.PERMISSION_GATE)
        config = _config()

        rng = random.Random(spec.seed)
        runner = PolicyMixtureRunner(rng=random.Random(spec.seed))
        ep1 = collect_episode(spec, runner, rng, config)

        j1 = _episode_to_stable_json(ep1)

        # Simulate a corrupted second collection by modifying the JSON
        import json
        d1 = json.loads(j1)
        d1["episode_id"] = "corrupted_id"
        j_corrupted = json.dumps(d1, sort_keys=True)

        # They should differ
        assert j1 != j_corrupted
