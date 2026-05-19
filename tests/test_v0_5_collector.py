"""Tests for v0_5 intra-episode regime switch collector (TASK_LFD_004).

Source: .agent_tasks/codex_queue/TASK_LFD_004_v0_5_intra_episode_switch.md
"""
from __future__ import annotations

import random

import pytest

from frcgw.text_env.collector import CollectorConfig, _backfill_v0_5_switch_labels
from frcgw.text_env.generator import EpisodeSpecGenerator


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
