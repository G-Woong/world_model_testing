"""P1 gate test: counterfactual records are excluded from inference input.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §10
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §5.7, §6.2
"""
from __future__ import annotations

import pytest
from frcgw.schemas.step_schema import (
    StepRecord,
    PublicObservation,
    ActionRecord,
    PublicEffect,
    TrainingLabels,
    EvaluationLabels,
    CounterfactualRecord,
    CandidateAction,
)
from frcgw.schemas.validation import validate_counterfactual_exclusion
from frcgw.schemas.visibility import CounterfactualLeakageError, assert_agent_observation_safe


def _make_cf_record() -> CounterfactualRecord:
    return CounterfactualRecord(
        counterfactual_id="cf1",
        source_step_id="s1",
        candidate_action=CandidateAction(action_id="ca1", action_type="click"),
        hypothesis_id="h1",
        counterfactual_effect_type="no_effect",
        counterfactual_progress_delta=0.0,
        counterfactual_failure_risk=0.8,
        is_oracle_best=False,
    )


def _make_step_with_cf() -> StepRecord:
    return StepRecord(
        step_id="s1",
        episode_id="ep1",
        step_index=0,
        public_observation=PublicObservation(instruction="click"),
        action=ActionRecord(action_id="a1", action_type="click"),
        observed_effect_public=PublicEffect(effect_type="dom_change"),
        training_labels=TrainingLabels(
            true_regime="r1",
            true_control_grammar="g1",
            true_change_point="none",
            true_reveal_vs_shift="reveal",
            true_action_effect_type="success",
            true_failed_action=False,
            failure_reason=None,
            progress_delta=0.1,
        ),
        evaluation_labels=EvaluationLabels(),
        counterfactuals=[_make_cf_record()],
    )


def test_batch_without_counterfactuals_passes():
    batch = {"input_ids": [1, 2, 3], "labels": [0, 1, 0]}
    result = validate_counterfactual_exclusion(batch)
    assert result.passed, result.errors


def test_none_batch_passes():
    result = validate_counterfactual_exclusion(None)
    assert result.passed


def test_batch_with_counterfactual_action_effects_fails():
    batch = {"input_ids": [1], "counterfactual_action_effects": []}
    result = validate_counterfactual_exclusion(batch)
    assert not result.passed


def test_batch_with_counterfactuals_key_fails():
    batch = {"input_ids": [1], "counterfactuals": [_make_cf_record()]}
    result = validate_counterfactual_exclusion(batch)
    assert not result.passed


def test_counterfactual_action_effects_in_obs_raise_counterfactual_error():
    obs = {"instruction": "click", "counterfactual_action_effects": []}
    with pytest.raises(CounterfactualLeakageError):
        assert_agent_observation_safe(obs)


def test_counterfactual_record_can_be_stored_in_step():
    """CounterfactualRecord exists on StepRecord but must not reach inference input."""
    step = _make_step_with_cf()
    assert len(step.counterfactuals) == 1
    # public_observation itself is safe — no counterfactual fields
    assert_agent_observation_safe(step.public_observation)


def test_public_observation_without_cf_fields_passes_exclusion():
    obs = PublicObservation(instruction="navigate to home")
    result = validate_counterfactual_exclusion({"obs": vars(obs)})
    assert result.passed, result.errors
