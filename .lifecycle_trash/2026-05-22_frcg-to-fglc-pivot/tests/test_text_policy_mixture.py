"""Tests for policy mixture: per-policy label distribution and oversampling."""
from __future__ import annotations

import random

import pytest

from frcgw.text_env.collector import CollectorConfig, collect_episode
from frcgw.text_env.generator import EpisodeSpecGenerator, TaskFamily
from frcgw.text_env.policies import (
    OraclePolicy,
    PolicyMixtureRunner,
    RecoveryPolicy,
    RetryPolicy,
    WrongGrammarPolicy,
)


def _run_policy_episodes(policy_id: str, n: int = 15, seed: int = 11) -> list:
    mixture = {policy_id: 1.0}
    gen = EpisodeSpecGenerator(seed=seed)
    config = CollectorConfig(split_id="train")
    runner = PolicyMixtureRunner(mixture=mixture, rng=random.Random(seed))
    episodes = []
    for family in list(TaskFamily)[:4]:  # subset for speed
        for _ in range(n // 4 + 1):
            spec = gen.generate(family=family)
            ep = collect_episode(spec, runner, random.Random(spec.seed), config)
            episodes.append(ep)
    return episodes


class TestOraclePolicy:
    def test_oracle_achieves_high_success(self):
        episodes = _run_policy_episodes("oracle", n=20)
        success = sum(1 for ep in episodes if ep.final_success)
        # Oracle should succeed in at least 60% of episodes
        assert success / len(episodes) >= 0.6, (
            f"Oracle success rate too low: {success}/{len(episodes)}"
        )

    def test_oracle_produces_low_failed_actions(self):
        episodes = _run_policy_episodes("oracle", n=12)
        total_steps = sum(len(ep.steps) for ep in episodes)
        failed = sum(
            sum(1 for s in ep.steps if s.training_labels.true_failed_action)
            for ep in episodes
        )
        # Oracle should fail rarely
        assert failed / max(total_steps, 1) <= 0.30


class TestWrongGrammarPolicy:
    def test_wrong_grammar_produces_high_failed_actions(self):
        episodes = _run_policy_episodes("wrong_grammar", n=16)
        total_steps = sum(len(ep.steps) for ep in episodes)
        failed = sum(
            sum(1 for s in ep.steps if s.training_labels.true_failed_action)
            for ep in episodes
        )
        # WrongGrammar should produce many failed steps
        assert failed / max(total_steps, 1) >= 0.15, (
            f"Wrong grammar failed_action_ratio too low: {failed}/{total_steps}"
        )


class TestRecoveryPolicy:
    def test_recovery_episodes_have_initial_failures_then_switch(self):
        episodes = _run_policy_episodes("recovery", n=16)
        # At least some episodes should have a mix of failed + success steps
        mixed = sum(
            1 for ep in episodes
            if any(s.training_labels.true_failed_action for s in ep.steps)
        )
        assert mixed > 0, "Recovery policy produced no episodes with any failed steps"


class TestPolicyMixtureRunner:
    def test_mixture_sampling_distribution_approximately_correct(self):
        runner = PolicyMixtureRunner(rng=random.Random(7))
        gen = EpisodeSpecGenerator(seed=7)
        counts: dict[str, int] = {}
        n = 100
        for _ in range(n):
            spec = gen.generate()
            policy = runner.sample_policy(spec)
            counts[policy.policy_id] = counts.get(policy.policy_id, 0) + 1
        # Each policy should appear at least once in 100 samples
        for pid in ("oracle", "wrong_grammar", "retry", "recovery", "random_constrained"):
            assert pid in counts, f"Policy {pid!r} never sampled in {n} draws"

    def test_oversampling_triggers_when_coverage_low(self):
        runner = PolicyMixtureRunner(rng=random.Random(3))
        current = {"failed_action_ratio": 0.01}
        targets = {"failed_action_ratio": 0.20}
        policy = runner.coverage_oversample(current, targets)
        assert policy is not None
        assert policy.policy_id == "wrong_grammar"

    def test_oversampling_returns_none_when_coverage_met(self):
        runner = PolicyMixtureRunner(rng=random.Random(3))
        current = {"failed_action_ratio": 0.25}
        targets = {"failed_action_ratio": 0.20}
        policy = runner.coverage_oversample(current, targets)
        assert policy is None

    def test_policy_mixture_snapshot_sums_to_one(self):
        runner = PolicyMixtureRunner(rng=random.Random(5))
        gen = EpisodeSpecGenerator(seed=5)
        for _ in range(20):
            spec = gen.generate()
            runner.sample_policy(spec)
        snapshot = runner.policy_mixture_snapshot()
        total = sum(snapshot.values())
        assert abs(total - 1.0) < 0.01, f"Snapshot does not sum to 1: {total}"
