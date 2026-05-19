"""Tests for v0_5 intra-episode regime switch generator (TASK_LFD_004).

Source: .agent_tasks/codex_queue/TASK_LFD_004_v0_5_intra_episode_switch.md
"""
from __future__ import annotations

from frcgw.text_env.generator import EpisodeSpecGenerator, ID_GRAMMAR_FAMILIES


def test_generate_v0_5_switch_step_in_range() -> None:
    """regime_switch_step is in [2, max_steps-2]."""
    gen = EpisodeSpecGenerator(seed=42, max_steps=12)
    for _ in range(20):
        spec = gen.generate_v0_5()
        assert spec.regime_switch_step is not None
        assert 2 <= spec.regime_switch_step <= spec.max_steps - 2, (
            f"switch_step={spec.regime_switch_step} outside [2, {spec.max_steps - 2}]"
        )


def test_generate_v0_5_regime_changes() -> None:
    """hidden_regime != hidden_regime_after for v0_5 episodes."""
    gen = EpisodeSpecGenerator(seed=42, max_steps=12)
    for _ in range(20):
        spec = gen.generate_v0_5()
        assert spec.hidden_regime_after is not None
        assert spec.hidden_regime != spec.hidden_regime_after, (
            f"Regime should change: {spec.hidden_regime} == {spec.hidden_regime_after}"
        )


def test_generate_v0_4_backward_compat() -> None:
    """v0_4 generate() produces regime_switch_step=None and hidden_regime_after=None."""
    gen = EpisodeSpecGenerator(seed=42, max_steps=12)
    for _ in range(10):
        spec = gen.generate()
        assert spec.regime_switch_step is None, (
            f"v0_4 episode should have regime_switch_step=None, got {spec.regime_switch_step}"
        )
        assert spec.hidden_regime_after is None, (
            f"v0_4 episode should have hidden_regime_after=None"
        )


def test_v0_5_regime_switch_episode_count_nonzero() -> None:
    """generate_v0_5_batch produces nonzero switch episodes."""
    gen = EpisodeSpecGenerator(seed=0, max_steps=12)
    batch = gen.generate_v0_5_batch(n=50)
    switch_count = sum(1 for s in batch if s.regime_switch_step is not None)
    assert switch_count > 0, "v0_5 batch should have at least one switch episode"
    assert switch_count == len(batch), "All v0_5 episodes should have a switch step"


def test_v0_5_ood_type_set() -> None:
    """v0_5 episodes have ood_type='regime_switch'."""
    gen = EpisodeSpecGenerator(seed=0, max_steps=10)
    spec = gen.generate_v0_5()
    assert spec.ood_type == "regime_switch"


def test_v0_5_regime_switch_not_in_public_instruction() -> None:
    """Public instruction does not contain hidden regime tokens."""
    gen = EpisodeSpecGenerator(seed=0, max_steps=12)
    spec = gen.generate_v0_5()
    regime_token = str(spec.hidden_regime_after)
    assert regime_token not in spec.public_instruction, (
        f"Public instruction should not contain hidden_regime_after token '{regime_token}'"
    )
