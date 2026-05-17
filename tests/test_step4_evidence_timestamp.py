from __future__ import annotations

import dataclasses

from frcgw.evaluation.metrics import wrong_control_grammar_persistence
from frcgw.schemas.step_schema import (
    ActionRecord,
    CandidateAction,
    EvaluationLabels,
    PublicEffect,
    PublicHistoryItem,
    PublicObservation,
    StepAuditMetadata,
    StepRecord,
    TrainingLabels,
)
from frcgw.text_env.collector import _backfill_episode_timestamps


def _make_step(
    index: int,
    *,
    action_type: str = "wait",
    valid_switch: bool = False,
    true_wrong: bool = False,
    progress_delta: float = 0.0,
    recovery_action_id: str | None = None,
) -> StepRecord:
    return StepRecord(
        step_id=f"ep0_step_{index:03d}",
        episode_id="ep0",
        step_index=index,
        public_observation=PublicObservation(
            instruction="test",
            history_public=[
                PublicHistoryItem(
                    step_index=max(0, index - 1),
                    action_summary="wait",
                    effect_summary="no_state_change",
                )
            ],
            candidate_actions_public=[CandidateAction("wait", "wait")],
        ),
        action=ActionRecord(action_id=f"a{index}", action_type=action_type),
        observed_effect_public=PublicEffect(effect_type="no_state_change"),
        training_labels=TrainingLabels(
            true_regime="search_form",
            true_control_grammar="direct_search",
            true_change_point=str(index),
            true_reveal_vs_shift="none",
            true_action_effect_type="none",
            true_failed_action=False,
            failure_reason=None,
            progress_delta=progress_delta,
            recovery_action_id=recovery_action_id,
            valid_hypothesis_switch=valid_switch,
        ),
        evaluation_labels=EvaluationLabels(
            true_wrong_hypothesis=true_wrong,
            evidence_timestamp=index,
        ),
        audit_metadata=StepAuditMetadata(
            generator_version="test",
            collection_timestamp="2026-01-01T00:00:00+00:00",
            policy_id="test",
            split_id="train",
        ),
    )


def test_evidence_timestamp_is_first_true_wrong_step() -> None:
    steps = [_make_step(i, true_wrong=(i >= 2)) for i in range(5)]

    patched = _backfill_episode_timestamps(steps, None)

    assert {step.evaluation_labels.evidence_timestamp for step in patched} == {2}


def test_evidence_timestamp_none_when_no_true_wrong_in_episode() -> None:
    steps = [_make_step(i, true_wrong=False) for i in range(4)]

    patched = _backfill_episode_timestamps(steps, None)

    assert all(step.evaluation_labels.evidence_timestamp is None for step in patched)


def test_evidence_timestamp_not_in_public_observation() -> None:
    step = _make_step(0, true_wrong=True)

    public_observation = dataclasses.asdict(step.public_observation)

    assert "evidence_timestamp" not in public_observation


def test_evidence_timestamp_not_in_history_public() -> None:
    step = _make_step(1, true_wrong=True)

    history_public = dataclasses.asdict(step.public_observation)["history_public"]

    assert history_public
    assert all("evidence_timestamp" not in item for item in history_public)


def test_evidence_timestamp_not_in_candidate_actions() -> None:
    step = _make_step(0, true_wrong=True)

    candidate_actions = dataclasses.asdict(step.public_observation)["candidate_actions_public"]

    assert candidate_actions
    assert all("evidence_timestamp" not in action for action in candidate_actions)


def test_evidence_timestamp_leq_hypothesis_update_when_both_present() -> None:
    steps = [
        _make_step(0),
        _make_step(1),
        _make_step(2, true_wrong=True),
        _make_step(3, valid_switch=True),
    ]

    patched = _backfill_episode_timestamps(steps, None)

    labels = patched[0].evaluation_labels
    assert labels.evidence_timestamp is not None
    assert labels.hypothesis_update_timestamp is not None
    assert labels.evidence_timestamp <= labels.hypothesis_update_timestamp


def test_evidence_timestamp_leq_recovery_when_both_present() -> None:
    steps = [
        _make_step(0),
        _make_step(1, true_wrong=True),
        _make_step(
            2,
            action_type="close_modal",
            progress_delta=0.5,
            recovery_action_id="close_modal",
        ),
    ]

    patched = _backfill_episode_timestamps(steps, None)

    labels = patched[0].evaluation_labels
    assert labels.evidence_timestamp is not None
    assert labels.recovery_timestamp is not None
    assert labels.evidence_timestamp <= labels.recovery_timestamp


def test_c1_persistence_changes_after_evidence_timestamp_fix() -> None:
    steps = [
        _make_step(0),
        _make_step(1),
        _make_step(2, true_wrong=True),
        _make_step(3, true_wrong=True),
        _make_step(4, valid_switch=True),
    ]
    old_update_labels = steps[4].evaluation_labels

    patched = _backfill_episode_timestamps(steps, None)
    new_update_labels = patched[4].evaluation_labels

    assert [step.evaluation_labels.evidence_timestamp for step in steps] == list(range(5))
    assert new_update_labels.evidence_timestamp == 2

    old_persistence = wrong_control_grammar_persistence(
        [
            {
                "eval_labels": {
                    "evidence_timestamp": old_update_labels.evidence_timestamp,
                    "hypothesis_update_timestamp": 4,
                }
            }
        ]
    )
    new_persistence = wrong_control_grammar_persistence(
        [
            {
                "eval_labels": {
                    "evidence_timestamp": new_update_labels.evidence_timestamp,
                    "hypothesis_update_timestamp": new_update_labels.hypothesis_update_timestamp,
                }
            }
        ]
    )

    assert old_persistence == 0.0
    assert new_persistence == 2.0
    assert new_persistence != old_persistence
