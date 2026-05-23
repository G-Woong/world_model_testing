"""Tests for TASK_LFD_006: EvaluationLabels detector output contract.

Source: .agent_tasks/codex_queue/TASK_LFD_006_evaluation_labels_detector_output.md
Gate-B: detection_delay_gt → FORBIDDEN_AGENT_FIELDS (2026-05-19)
"""
from __future__ import annotations

import dataclasses

from frcgw.schemas.step_schema import EvaluationLabels, PublicObservation
from frcgw.schemas.visibility import (
    FORBIDDEN_AGENT_FIELDS,
    HiddenLabelLeakageError,
    assert_agent_observation_safe,
)


# ---------------------------------------------------------------------------
# EvaluationLabels schema tests
# ---------------------------------------------------------------------------

def test_eval_labels_has_detector_fields() -> None:
    """EvaluationLabels has all four LFD detector output fields."""
    fields = {f.name for f in dataclasses.fields(EvaluationLabels)}
    assert "detector_wrong_prob_learned" in fields
    assert "detector_cusum_stat" in fields
    assert "detector_run_length_posterior" in fields
    assert "detection_delay_gt" in fields


def test_eval_labels_detector_fields_default_none() -> None:
    """All four detector fields default to None."""
    labels = EvaluationLabels()
    assert labels.detector_wrong_prob_learned is None
    assert labels.detector_cusum_stat is None
    assert labels.detector_run_length_posterior is None
    assert labels.detection_delay_gt is None


def test_eval_labels_detector_fields_settable() -> None:
    """Detector fields can be set during evaluation recording."""
    labels = EvaluationLabels(
        detector_wrong_prob_learned=0.87,
        detector_cusum_stat=3.14,
        detector_run_length_posterior=[0.1, 0.4, 0.3, 0.2],
        detection_delay_gt=3,
    )
    assert labels.detector_wrong_prob_learned == 0.87
    assert labels.detector_cusum_stat == 3.14
    assert labels.detector_run_length_posterior == [0.1, 0.4, 0.3, 0.2]
    assert labels.detection_delay_gt == 3


# ---------------------------------------------------------------------------
# Gate-B: detection_delay_gt forbidden field contract
# ---------------------------------------------------------------------------

def test_detection_delay_gt_in_forbidden_fields() -> None:
    """detection_delay_gt must be in FORBIDDEN_AGENT_FIELDS (Gate-B)."""
    assert "detection_delay_gt" in FORBIDDEN_AGENT_FIELDS, (
        "Gate-B violated: detection_delay_gt not in FORBIDDEN_AGENT_FIELDS. "
        "This oracle-derived field must never enter inference input."
    )


def test_public_observation_lacks_detector_fields() -> None:
    """PublicObservation does not have detector output fields as struct fields."""
    pub_fields = {f.name for f in dataclasses.fields(PublicObservation)}
    assert "detection_delay_gt" not in pub_fields
    assert "detector_wrong_prob_learned" not in pub_fields
    assert "detector_cusum_stat" not in pub_fields
    assert "detector_run_length_posterior" not in pub_fields


def test_assert_observation_safe_blocks_detection_delay_gt() -> None:
    """assert_agent_observation_safe raises if detection_delay_gt appears in obs dict."""
    # Simulate a contaminated obs that somehow contains detection_delay_gt in nested dict
    contaminated = PublicObservation(
        instruction="search",
        dom_snapshot_public={"detection_delay_gt": 3},
    )
    try:
        assert_agent_observation_safe(contaminated)
        assert False, "Should have raised HiddenLabelLeakageError for detection_delay_gt"
    except HiddenLabelLeakageError as e:
        assert "detection_delay_gt" in str(e)


def test_assert_observation_safe_passes_clean_obs() -> None:
    """Clean PublicObservation (no forbidden fields) passes leakage check."""
    clean = PublicObservation(
        instruction="search",
        dom_snapshot_public={"page_title": "Search", "n_results": 42},
    )
    assert_agent_observation_safe(clean)  # must not raise


# ---------------------------------------------------------------------------
# Bucket separation: detector output stays in EvaluationLabels only
# ---------------------------------------------------------------------------

def test_training_labels_lacks_detector_fields() -> None:
    """TrainingLabels must not have detector output fields (wrong bucket)."""
    from frcgw.schemas.step_schema import TrainingLabels
    train_fields = {f.name for f in dataclasses.fields(TrainingLabels)}
    assert "detection_delay_gt" not in train_fields
    assert "detector_wrong_prob_learned" not in train_fields
    assert "detector_cusum_stat" not in train_fields


def test_step_record_eval_labels_contains_detector_fields() -> None:
    """StepRecord.evaluation_labels contains the LFD detector fields (integration)."""
    from frcgw.schemas.step_schema import (
        ActionRecord,
        PublicEffect,
        StepRecord,
        TrainingLabels,
    )
    step = StepRecord(
        step_id="s0",
        episode_id="ep0",
        step_index=0,
        public_observation=PublicObservation(instruction="test"),
        action=ActionRecord(action_id="a0", action_type="click"),
        observed_effect_public=PublicEffect(effect_type="state_change"),
        training_labels=TrainingLabels(
            true_regime="search_form",
            true_control_grammar="direct_search",
            true_change_point="0",
            true_reveal_vs_shift="none",
            true_action_effect_type="state_change",
            true_failed_action=False,
            failure_reason=None,
            progress_delta=0.0,
        ),
        evaluation_labels=EvaluationLabels(
            detection_delay_gt=2,
            detector_wrong_prob_learned=0.75,
        ),
    )
    assert step.evaluation_labels.detection_delay_gt == 2
    assert step.evaluation_labels.detector_wrong_prob_learned == 0.75
    # Public observation must not have these fields
    assert_agent_observation_safe(step.public_observation)
