from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from frcgw.models.text_frcg_model import TextFRCGModel
from frcgw.planning.alternative_proposer import HypothesisId
from frcgw.planning.planner import PlanMetadata, PlannerState, text_frcg_plan
from frcgw.planning.rewrite import rewrite_action, validate_rewrite
from frcgw.schemas.step_schema import CandidateAction, PublicObservation
from frcgw.schemas.visibility import HiddenLabelLeakageError


def test_rewrite_action_returns_candidate() -> None:
    model = TextFRCGModel()
    cands = [CandidateAction("a1", "click", {}), CandidateAction("a2", "submit", {})]
    h_star = HypothesisId(0, 0, 0)
    cand, conf = rewrite_action("submit form", h_star, cands, model)
    assert cand in cands
    assert 0.0 <= conf <= 1.0


def test_rewrite_different_grammar_changes_ranking() -> None:
    model = TextFRCGModel()
    cands = [
        CandidateAction("a1", "click", {}),
        CandidateAction("a2", "submit", {}),
        CandidateAction("a3", "search", {}),
    ]
    cand_a, conf_a = rewrite_action("submit form", HypothesisId(0, 0, 0), cands, model)
    cand_b, conf_b = rewrite_action("submit form", HypothesisId(0, 7, 7), cands, model)
    if cand_a == cand_b:
        assert conf_a != conf_b
    else:
        assert cand_a != cand_b


def test_rewrite_invalid_not_in_candidates() -> None:
    pub = PublicObservation(instruction="x", candidate_actions_public=[])
    valid, reason = validate_rewrite(CandidateAction("X", "X", {}), pub, 0.9)
    assert valid is False
    assert reason == "not_in_candidates"


def test_rewrite_low_confidence_fallback() -> None:
    candidate = CandidateAction("a1", "click", {})
    pub = PublicObservation(instruction="x", candidate_actions_public=[candidate])
    valid, reason = validate_rewrite(candidate, pub, confidence=0.1, tau_r=0.5)
    assert valid is False
    assert reason == "low_confidence"


def test_validate_rewrite_valid() -> None:
    candidate = CandidateAction("a1", "click", {})
    pub = PublicObservation(instruction="x", candidate_actions_public=[candidate])
    valid, reason = validate_rewrite(candidate, pub, confidence=0.9, tau_r=0.5)
    assert valid is True
    assert reason == "ok"


def test_planner_no_hidden_fields() -> None:
    pub = PublicObservation(instruction="search", history_public=[])
    model = TextFRCGModel()
    planner_state = PlannerState()
    cands = [CandidateAction("a1", "search", {})]
    action, meta = text_frcg_plan(pub, 0, cands, model, planner_state)
    assert isinstance(action, CandidateAction)
    assert isinstance(meta, PlanMetadata)


def test_planner_assert_fires_on_leakage() -> None:
    pub = PublicObservation(instruction="x", dom_snapshot_public={"true_regime": "y"})
    model = TextFRCGModel()
    planner_state = PlannerState()
    cands = [CandidateAction("a1", "search", {})]
    with pytest.raises(HiddenLabelLeakageError):
        text_frcg_plan(pub, 0, cands, model, planner_state)


def test_h_exec_tracking() -> None:
    planner_state = PlannerState()
    planner_state.update(0, 5)
    assert planner_state.get_current(0) == 5
    assert planner_state.get_current(99) == 0
