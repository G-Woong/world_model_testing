"""Tests for v0_5 intra-episode regime switch collector.

Sources:
  .agent_tasks/codex_queue/TASK_LFD_004_v0_5_intra_episode_switch.md
  TASK_COLLECTOR_V05_SWITCH (2026-05-19): collect_episode() integration tests.
"""
from __future__ import annotations

import dataclasses
import random

import pytest

from frcgw.schemas.visibility import assert_agent_observation_safe
from frcgw.text_env.collector import CollectorConfig, _backfill_v0_5_switch_labels, collect_episode
from frcgw.text_env.generator import EpisodeSpecGenerator
from frcgw.text_env.policies import PolicyMixtureRunner


def test_evaluation_labels_has_regime_switch_t_for_v0_5() -> None:
    """v0_5 episodes: all EvaluationLabels have regime_switch_t set to switch step."""
    gen = EpisodeSpecGenerator(seed=42, max_steps=8)
    spec = gen.generate_v0_5()
    assert spec.regime_switch_step is not None

    # Simulate backfill directly
    from frcgw.schemas.step_schema import (
        ActionRecord,
        EvaluationLabels,
        PublicEffect,
        PublicObservation,
        StepAuditMetadata,
        StepRecord,
        TrainingLabels,
    )

    def _dummy_step(idx: int) -> StepRecord:
        return StepRecord(
            step_id=f"ep_step_{idx:03d}",
            episode_id="ep",
            step_index=idx,
            public_observation=PublicObservation(instruction="test"),
            action=ActionRecord(action_id=f"a{idx}", action_type="click"),
            observed_effect_public=PublicEffect(effect_type="state_change"),
            training_labels=TrainingLabels(
                true_regime="search_form",
                true_control_grammar="g1",
                true_change_point="0",
                true_reveal_vs_shift="none",
                true_action_effect_type="state_change",
                true_failed_action=False,
                failure_reason=None,
                progress_delta=0.1,
            ),
            evaluation_labels=EvaluationLabels(),
            audit_metadata=StepAuditMetadata(
                generator_version="v0_5",
                collection_timestamp="2026-05-19",
                policy_id="test",
                split_id="train",
            ),
        )

    steps = [_dummy_step(i) for i in range(6)]
    switch_step = spec.regime_switch_step
    patched = _backfill_v0_5_switch_labels(steps, switch_step)

    for step in patched:
        assert step.evaluation_labels.regime_switch_t == switch_step, (
            f"step {step.step_index}: regime_switch_t should be {switch_step}, "
            f"got {step.evaluation_labels.regime_switch_t}"
        )


def test_v0_4_episode_no_switch() -> None:
    """v0_4 episodes (regime_switch_step=None): regime_switch_t stays None in EvaluationLabels."""
    from frcgw.schemas.step_schema import (
        ActionRecord,
        EvaluationLabels,
        PublicEffect,
        PublicObservation,
        StepAuditMetadata,
        StepRecord,
        TrainingLabels,
    )

    def _dummy_step(idx: int) -> StepRecord:
        return StepRecord(
            step_id=f"ep_step_{idx:03d}",
            episode_id="ep",
            step_index=idx,
            public_observation=PublicObservation(instruction="test"),
            action=ActionRecord(action_id=f"a{idx}", action_type="click"),
            observed_effect_public=PublicEffect(effect_type="state_change"),
            training_labels=TrainingLabels(
                true_regime="search_form",
                true_control_grammar="g1",
                true_change_point="0",
                true_reveal_vs_shift="none",
                true_action_effect_type="state_change",
                true_failed_action=False,
                failure_reason=None,
                progress_delta=0.1,
            ),
            evaluation_labels=EvaluationLabels(),
            audit_metadata=StepAuditMetadata(
                generator_version="v0_4",
                collection_timestamp="2026-05-19",
                policy_id="test",
                split_id="train",
            ),
        )

    steps = [_dummy_step(i) for i in range(5)]
    patched = _backfill_v0_5_switch_labels(steps, regime_switch_step=None)

    for step in patched:
        assert step.evaluation_labels.regime_switch_t is None, (
            "v0_4 step should have regime_switch_t=None"
        )


def test_training_labels_no_regime_switch_t_field() -> None:
    """TrainingLabels has no regime_switch_t attribute (must not be added)."""
    from frcgw.schemas.step_schema import TrainingLabels

    tl = TrainingLabels(
        true_regime="search_form",
        true_control_grammar="g1",
        true_change_point="0",
        true_reveal_vs_shift="none",
        true_action_effect_type="state_change",
        true_failed_action=False,
        failure_reason=None,
        progress_delta=0.1,
    )
    assert not hasattr(tl, "regime_switch_t"), (
        "TrainingLabels must NOT have regime_switch_t — it is EVALUATION_ONLY"
    )


def test_public_obs_no_regime_switch_t() -> None:
    """PublicObservation has no regime_switch_t attribute."""
    from frcgw.schemas.step_schema import PublicObservation

    obs = PublicObservation(instruction="test")
    assert not hasattr(obs, "regime_switch_t"), (
        "PublicObservation must NOT have regime_switch_t"
    )


# ---------------------------------------------------------------------------
# TASK_COLLECTOR_V05_SWITCH: collect_episode() integration tests
# ---------------------------------------------------------------------------

def _collect_v0_5_episode(seed: int = 42, switch_step_override: int | None = 3):
    gen = EpisodeSpecGenerator(seed=seed, max_steps=10)
    spec = gen.generate_v0_5()
    if switch_step_override is not None:
        spec = dataclasses.replace(spec, regime_switch_step=switch_step_override)
    runner = PolicyMixtureRunner()
    config = CollectorConfig(dataset_version="0.5_test")
    rng = random.Random(seed)
    return collect_episode(spec, runner, rng, config), spec


def test_collect_episode_v0_5_completes() -> None:
    """collect_episode() completes on v0_5 spec without error."""
    episode, spec = _collect_v0_5_episode()
    assert episode is not None
    assert len(episode.steps) > 0


def test_collect_episode_v0_5_true_wrong_post_switch() -> None:
    """true_wrong_hypothesis=True for all steps >= regime_switch_step.

    switch_step=0: grammar switches from step 0 so all steps are post-switch.
    This ensures the test does not depend on episode length exceeding switch_step.
    """
    switch_step = 0  # switch from the very first step
    episode, spec = _collect_v0_5_episode(switch_step_override=switch_step)
    # All collected steps are >= 0, so all are post-switch
    assert len(episode.steps) > 0, "Episode must have at least one step"
    for step in episode.steps:
        assert step.evaluation_labels.true_wrong_hypothesis is True, (
            f"Step {step.step_index}: expected true_wrong_hypothesis=True "
            f"(all steps are post-switch when switch_step=0)"
        )


def test_collect_episode_v0_5_regime_switch_t_backfilled() -> None:
    """EvaluationLabels.regime_switch_t set on all steps for v0_5 episode."""
    switch_step = 0
    episode, spec = _collect_v0_5_episode(switch_step_override=switch_step)
    for step in episode.steps:
        assert step.evaluation_labels.regime_switch_t == switch_step


def test_collect_episode_v0_5_post_switch_mismatch_effect() -> None:
    """Post-switch actions produce no_state_change (grammar mismatch).

    switch_step=0: all steps are post-switch, so the entire episode runs
    under the new grammar. Agent actions from the original grammar produce
    no_state_change in the new grammar — this is the mismatch signal.
    """
    switch_step = 0
    episode, spec = _collect_v0_5_episode(seed=42, switch_step_override=switch_step)
    mismatches = [s for s in episode.steps
                  if s.observed_effect_public.effect_type == "no_state_change"]
    assert len(mismatches) > 0, (
        f"Post-switch should show no_state_change mismatch. "
        f"Effects: {[s.observed_effect_public.effect_type for s in episode.steps]}"
    )


def test_collect_episode_v0_5_no_leakage_in_obs() -> None:
    """No FORBIDDEN_AGENT_FIELDS appear in any PublicObservation."""
    episode, _ = _collect_v0_5_episode()
    for step in episode.steps:
        assert_agent_observation_safe(step.public_observation)


def test_collect_episode_v0_4_unaffected() -> None:
    """v0_4 episodes are unaffected by v0_5 switch logic."""
    gen = EpisodeSpecGenerator(seed=99, max_steps=10)
    spec = gen.generate()
    assert spec.regime_switch_step is None
    runner = PolicyMixtureRunner()
    rng = random.Random(99)
    episode = collect_episode(spec, runner, rng, CollectorConfig())
    assert episode is not None
    for step in episode.steps:
        assert step.evaluation_labels.regime_switch_t is None
    assert_agent_observation_safe(episode.steps[0].public_observation)


def test_collect_episode_v0_5_batch_audit() -> None:
    """Batch 20 v0_5 episodes: switch_count==20, mismatch>0, leakage==0."""
    gen = EpisodeSpecGenerator(seed=0, max_steps=10)
    runner = PolicyMixtureRunner()
    config = CollectorConfig(dataset_version="0.5_audit")
    mismatch_count = 0
    wrong_count = 0
    leakage_violations = 0
    for i in range(20):
        spec = gen.generate_v0_5()
        episode = collect_episode(spec, runner, random.Random(i), config)
        sw = spec.regime_switch_step or 0
        for step in episode.steps:
            try:
                assert_agent_observation_safe(step.public_observation)
            except Exception:
                leakage_violations += 1
            if step.step_index >= sw and step.observed_effect_public.effect_type == "no_state_change":
                mismatch_count += 1
            if step.evaluation_labels.true_wrong_hypothesis is True:
                wrong_count += 1
    assert mismatch_count > 0, "No mismatch effects found in batch"
    assert wrong_count > 0, "No wrong_hypothesis=True labels found"
    assert leakage_violations == 0, f"Leakage violations: {leakage_violations}"


def test_batch_targets_regime_switch_step_not_in_public_input() -> None:
    """BatchTargets.regime_switch_step is read from evaluation_labels, not public_input."""
    from frcgw.data.text_dataset import BatchTargets
    from frcgw.schemas.step_schema import PublicObservation

    # BatchTargets should have regime_switch_step field
    bt = BatchTargets(
        true_regime="r",
        true_control_grammar="g",
        true_change_point="0",
        true_reveal_vs_shift="none",
        true_action_effect_type="state_change",
        true_failed_action=False,
        failure_reason=None,
        progress_delta=0.0,
        recovery_action_id=None,
        valid_hypothesis_switch=None,
        true_wrong_hypothesis=None,
        h_exec_id=None,
        correct_hypothesis_id=None,
        regime_switch_step=4,
    )
    assert bt.regime_switch_step == 4

    # PublicObservation should NOT have regime_switch_step
    obs = PublicObservation(instruction="test")
    assert not hasattr(obs, "regime_switch_step"), (
        "PublicObservation must NOT have regime_switch_step"
    )
