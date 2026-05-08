"""P1 gate test: episode and step schema validation.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §0.4
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §5.2-5.3, §6.2
"""
from __future__ import annotations

from frcgw.schemas.step_schema import (
    StepRecord,
    PublicObservation,
    ActionRecord,
    PublicEffect,
    TrainingLabels,
    EvaluationLabels,
)
from frcgw.schemas.episode_schema import EpisodeRecord, AuditMetadata
from frcgw.schemas.validation import validate_step_schema, validate_episode_schema


def _make_step(step_id: str = "s1", episode_id: str = "ep1", step_index: int = 0) -> StepRecord:
    return StepRecord(
        step_id=step_id,
        episode_id=episode_id,
        step_index=step_index,
        public_observation=PublicObservation(instruction="click login"),
        action=ActionRecord(action_id="a1", action_type="click"),
        observed_effect_public=PublicEffect(effect_type="dom_change"),
        training_labels=TrainingLabels(
            true_regime="default",
            true_control_grammar="direct_click",
            true_change_point="none",
            true_reveal_vs_shift="reveal",
            true_action_effect_type="success",
            true_failed_action=False,
            failure_reason=None,
            progress_delta=0.1,
        ),
        evaluation_labels=EvaluationLabels(),
    )


def _make_episode() -> EpisodeRecord:
    return EpisodeRecord(
        episode_id="ep1",
        dataset_version="v0.1",
        schema_version="v1",
        generator_version="v0.1",
        split_id="train",
        task_family="login",
        public_instruction="Log into the website",
        steps=[_make_step()],
        final_success=True,
        total_progress=1.0,
    )


def test_valid_step_passes():
    result = validate_step_schema(_make_step())
    assert result.passed, result.errors


def test_valid_episode_passes():
    result = validate_episode_schema(_make_episode())
    assert result.passed, result.errors


def test_step_missing_step_id_fails():
    step = _make_step(step_id="")
    result = validate_step_schema(step)
    assert not result.passed
    assert any("step_id" in e for e in result.errors)


def test_step_missing_episode_id_fails():
    step = _make_step(episode_id="")
    result = validate_step_schema(step)
    assert not result.passed


def test_step_negative_step_index_fails():
    step = _make_step()
    step.step_index = -1
    result = validate_step_schema(step)
    assert not result.passed


def test_episode_missing_episode_id_fails():
    ep = _make_episode()
    ep.episode_id = ""
    result = validate_episode_schema(ep)
    assert not result.passed


def test_episode_missing_public_instruction_fails():
    ep = _make_episode()
    ep.public_instruction = ""
    result = validate_episode_schema(ep)
    assert not result.passed


def test_episode_missing_dataset_version_fails():
    ep = _make_episode()
    ep.dataset_version = ""
    result = validate_episode_schema(ep)
    assert not result.passed


def test_episode_with_multiple_steps_passes():
    ep = _make_episode()
    ep.steps = [_make_step(step_id=f"s{i}", step_index=i) for i in range(3)]
    result = validate_episode_schema(ep)
    assert result.passed, result.errors


def test_episode_step_with_forbidden_field_fails():
    ep = _make_episode()
    ep.steps[0].public_observation = PublicObservation(
        instruction="click",
        dom_snapshot_public={"true_regime": "modal"},
    )
    result = validate_episode_schema(ep)
    assert not result.passed
