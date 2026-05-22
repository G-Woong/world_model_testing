"""Lexical leakage scan: visible_text, instruction, history must not contain hidden tokens."""
from __future__ import annotations

import random

import pytest

from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS, assert_agent_observation_safe
from frcgw.text_env.collector import CollectorConfig, build_public_observation, collect_episode
from frcgw.text_env.generator import (
    EpisodeSpecGenerator,
    TaskFamily,
    build_initial_state,
)
from frcgw.text_env.grammar import ControlGrammar
from frcgw.text_env.policies import PolicyMixtureRunner


# Hidden tokens that must NEVER appear in public text
_HIDDEN_GRAMMAR_TOKENS = [v.value for v in ControlGrammar]
_HIDDEN_REGIME_TOKENS = [f.value for f in TaskFamily]

# Additional forbidden content tokens
_FORBIDDEN_CONTENT_TOKENS = [
    "true_regime",
    "true_control_grammar",
    "oracle_",
    "policy_id",
    "split_id",
    "template_id",
    "counterfactual",
]


def _collect_mini_batch(n: int = 20, seed: int = 99) -> list:
    gen = EpisodeSpecGenerator(seed=seed)
    config = CollectorConfig(split_id="train")
    runner = PolicyMixtureRunner(rng=random.Random(seed))
    episodes = []
    for family in TaskFamily:
        for _ in range(n // len(list(TaskFamily)) + 1):
            spec = gen.generate(family=family)
            ep = collect_episode(spec, runner, random.Random(spec.seed), config)
            episodes.append(ep)
            if len(episodes) >= n:
                break
        if len(episodes) >= n:
            break
    return episodes


class TestPublicObservationLeakage:
    def test_assert_agent_observation_safe_passes_all_steps(self):
        episodes = _collect_mini_batch(20)
        for ep in episodes:
            for step in ep.steps:
                assert_agent_observation_safe(step.public_observation)

    def test_no_grammar_token_in_instruction(self):
        episodes = _collect_mini_batch(20)
        for ep in episodes:
            for step in ep.steps:
                text = step.public_observation.instruction.lower()
                for token in _HIDDEN_GRAMMAR_TOKENS:
                    assert token.lower() not in text, (
                        f"Grammar token {token!r} found in instruction: {text[:120]!r}"
                    )

    def test_no_forbidden_content_in_instruction(self):
        episodes = _collect_mini_batch(20)
        for ep in episodes:
            for step in ep.steps:
                text = step.public_observation.instruction.lower()
                for token in _FORBIDDEN_CONTENT_TOKENS:
                    assert token.lower() not in text, (
                        f"Forbidden token {token!r} in instruction: {text[:120]!r}"
                    )

    def test_no_hidden_token_in_history_action_summary(self):
        episodes = _collect_mini_batch(20)
        for ep in episodes:
            for step in ep.steps:
                for item in step.public_observation.history_public:
                    summary = (item.action_summary or "").lower()
                    for token in _HIDDEN_GRAMMAR_TOKENS:
                        assert token.lower() not in summary, (
                            f"Grammar token {token!r} in action_summary: {summary!r}"
                        )

    def test_no_hidden_token_in_history_effect_summary(self):
        episodes = _collect_mini_batch(20)
        for ep in episodes:
            for step in ep.steps:
                for item in step.public_observation.history_public:
                    summary = (item.effect_summary or "").lower()
                    for token in _HIDDEN_GRAMMAR_TOKENS:
                        assert token.lower() not in summary, (
                            f"Grammar token {token!r} in effect_summary: {summary!r}"
                        )

    def test_policy_id_not_in_public_observation(self):
        episodes = _collect_mini_batch(20)
        for ep in episodes:
            for step in ep.steps:
                obs = step.public_observation
                obs_str = str(obs)
                assert "policy_id" not in obs_str or "policy_id" not in obs.__dataclass_fields__

    def test_split_id_template_id_seed_not_in_obs_fields(self):
        from frcgw.schemas.step_schema import PublicObservation
        obs_fields = set(PublicObservation.__dataclass_fields__.keys())
        for forbidden in ("split_id", "template_id", "seed", "policy_id"):
            assert forbidden not in obs_fields, (
                f"Forbidden field {forbidden!r} present in PublicObservation schema"
            )

    def test_leakage_auditor_passes_all_steps(self):
        from frcgw.data.leakage_auditor import LeakageAuditor
        auditor = LeakageAuditor()
        episodes = _collect_mini_batch(20)
        for ep in episodes:
            for step in ep.steps:
                result = auditor.audit_agent_input(step.public_observation)
                assert result.passed, f"Leakage: {result.violations}"
