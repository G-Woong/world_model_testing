from __future__ import annotations

import dataclasses

from frcgw.schemas.step_schema import (
    ActionRecord,
    CandidateAction,
    CounterfactualRecord,
    EvaluationLabels,
    PublicEffect,
    PublicHistoryItem,
    PublicObservation,
    StepRecord,
    TrainingLabels,
)
from frcgw.schemas.validation import validate_counterfactual_exclusion


_COUNTERFACTUAL_FIELD_NAMES = {
    "counterfactual_id",
    "source_step_id",
    "candidate_action",
    "hypothesis_id",
    "counterfactual_effect_type",
    "counterfactual_progress_delta",
    "counterfactual_failure_risk",
    "is_oracle_best",
    "counterfactuals",
    "counterfactual_action_effects",
}


def _make_counterfactual() -> CounterfactualRecord:
    return CounterfactualRecord(
        counterfactual_id="step_0_cf_0",
        source_step_id="step_0",
        candidate_action=CandidateAction(action_id="wait", action_type="wait"),
        hypothesis_id="counterfactual_simulation",
        counterfactual_effect_type="no_state_change",
        counterfactual_progress_delta=0.0,
        counterfactual_failure_risk=0.0,
        is_oracle_best=True,
    )


def _make_public_observation() -> PublicObservation:
    return PublicObservation(
        instruction="Complete the task.",
        history_public=[
            PublicHistoryItem(
                step_index=0,
                action_summary="open_dropdown",
                effect_summary="state_change",
            )
        ],
        candidate_actions_public=[
            CandidateAction(action_id="open_dropdown", action_type="open_dropdown"),
            CandidateAction(action_id="wait", action_type="wait"),
        ],
    )


def _make_step_with_counterfactuals() -> StepRecord:
    return StepRecord(
        step_id="step_0",
        episode_id="ep_0",
        step_index=0,
        public_observation=_make_public_observation(),
        action=ActionRecord(action_id="act_0", action_type="open_dropdown"),
        observed_effect_public=PublicEffect(effect_type="state_change"),
        training_labels=TrainingLabels(
            true_regime="required_dropdown",
            true_control_grammar="required_dropdown_then_search",
            true_change_point="0",
            true_reveal_vs_shift="none",
            true_action_effect_type="none",
            true_failed_action=False,
            failure_reason=None,
            progress_delta=0.2,
        ),
        evaluation_labels=EvaluationLabels(),
        counterfactuals=[_make_counterfactual()],
    )


def test_counterfactual_does_not_appear_in_public_observation() -> None:
    public = dataclasses.asdict(_make_step_with_counterfactuals().public_observation)

    assert set(public).isdisjoint(_COUNTERFACTUAL_FIELD_NAMES)


def test_counterfactual_does_not_appear_in_candidate_actions() -> None:
    obs = _make_public_observation()

    for action in obs.candidate_actions_public:
        assert set(dataclasses.asdict(action)).isdisjoint(_COUNTERFACTUAL_FIELD_NAMES)


def test_counterfactual_does_not_appear_in_history_public() -> None:
    obs = _make_public_observation()

    for history_item in obs.history_public:
        assert set(dataclasses.asdict(history_item)).isdisjoint(
            _COUNTERFACTUAL_FIELD_NAMES
        )


def test_validate_counterfactual_exclusion_still_passes_on_v0_3() -> None:
    step = _make_step_with_counterfactuals()

    result = validate_counterfactual_exclusion(step.public_observation)

    assert result.passed, result.errors
