"""EvidenceFeatures derives public-only proxy values."""
from __future__ import annotations

from unittest.mock import MagicMock

from frcgw.falsification.lr_scorer import EvidenceFeatures


def _make_public_effect(effect_type: str, text_diff=None, dom_diff=None):
    eff = MagicMock()
    eff.effect_type = effect_type
    eff.text_diff_public = text_diff
    eff.dom_diff_public = dom_diff
    return eff


def _make_step(effect_type: str, text_diff=None, dom_diff=None):
    step = MagicMock()
    step.observed_effect_public = _make_public_effect(effect_type, text_diff, dom_diff)
    return step


def test_progress_delta_nonzero_when_text_diff_present() -> None:
    step = _make_step("state_change", text_diff="some change occurred", dom_diff=None)
    features = EvidenceFeatures.from_public_step(step)
    assert features.progress_delta > 0.0


def test_progress_delta_nonzero_when_dom_diff_present() -> None:
    step = _make_step("state_change", text_diff=None, dom_diff={"added": ["div#1"]})
    features = EvidenceFeatures.from_public_step(step)
    assert features.progress_delta > 0.0


def test_precondition_satisfied_for_blocker_removed() -> None:
    step = _make_step("blocker_removed", text_diff="Modal closed", dom_diff=None)
    features = EvidenceFeatures.from_public_step(step)
    assert features.precondition_status == "satisfied"


def test_precondition_satisfied_for_task_complete() -> None:
    step = _make_step("task_complete", text_diff="Task done", dom_diff=None)
    features = EvidenceFeatures.from_public_step(step)
    assert features.precondition_status == "satisfied"


def test_precondition_unmet_for_no_state_change() -> None:
    step = _make_step("no_state_change", text_diff=None, dom_diff=None)
    features = EvidenceFeatures.from_public_step(step)
    assert features.precondition_status == "unmet"


def test_no_effect_flag_for_no_state_change() -> None:
    step = _make_step("no_state_change", text_diff=None, dom_diff=None)
    features = EvidenceFeatures.from_public_step(step)
    assert features.no_effect_flag is True


def test_no_effect_flag_false_for_state_change() -> None:
    step = _make_step("state_change", text_diff="changed", dom_diff=None)
    features = EvidenceFeatures.from_public_step(step)
    assert features.no_effect_flag is False


def test_no_training_labels_accessed() -> None:
    step = _make_step("state_change", text_diff="delta", dom_diff=None)
    features = EvidenceFeatures.from_public_step(step)
    assert features.effect_type == "state_change"
    assert isinstance(features.progress_delta, float)
    assert isinstance(features.precondition_status, str)
