from __future__ import annotations

from unittest.mock import MagicMock

import pytest

torch = pytest.importorskip("torch")

from frcgw.planning.decision_gate import GateConfig
from frcgw.planning.falsification import FalsificationEvidence
from frcgw.planning.planner import PlannerState, text_frcg_plan
from frcgw.schemas.step_schema import CandidateAction, PublicHistoryItem, PublicObservation


def _make_mock_model() -> MagicMock:
    model = MagicMock()
    model_out = MagicMock()
    model_out.shared_h = torch.zeros(1, 32)
    model_out.z_state = torch.zeros(1, 32)
    model_out.z_regime_logits = torch.zeros(1, 8)
    model_out.z_grammar_logits = torch.zeros(1, 8)
    model_out.z_change_logits = torch.zeros(1, 12)
    model_out.z_reveal_shift_logits = torch.zeros(1, 3)
    model_out.posterior_entropy = torch.zeros(1)
    model_out.aux_precondition = torch.zeros(1)
    model_out.aux_failure_risk = torch.zeros(1)
    model.forward.return_value = model_out
    return model


def _obs() -> PublicObservation:
    return PublicObservation(
        instruction="test",
        history_public=[
            PublicHistoryItem(
                step_index=0,
                action_summary="clicked",
                effect_summary="no_state_change",
            )
        ],
        candidate_actions_public=[CandidateAction("a1", "click", {})],
    )


def _capture_evidence(monkeypatch: pytest.MonkeyPatch, cfg: GateConfig) -> FalsificationEvidence:
    import frcgw.planning.planner as planner_module

    captured: list[FalsificationEvidence] = []

    def fake_falsification_score(*args, **kwargs):
        captured.append(args[6])
        return torch.tensor(-1.0)

    obs = _obs()
    monkeypatch.setattr(planner_module, "falsification_score", fake_falsification_score)
    text_frcg_plan(
        obs,
        0,
        list(obs.candidate_actions_public),
        _make_mock_model(),
        PlannerState(),
        cfg,
    )
    assert captured
    return captured[0]


def test_proxy_flag_default_true() -> None:
    assert GateConfig().use_no_state_change_proxy is True


def test_proxy_flag_false_changes_effect_type(monkeypatch: pytest.MonkeyPatch) -> None:
    evidence = _capture_evidence(
        monkeypatch,
        GateConfig(use_no_state_change_proxy=False),
    )

    assert evidence.observed_effect_type == 0
    assert evidence.observed_failed_action is False


def test_text_frcg_plan_with_proxy_on(monkeypatch: pytest.MonkeyPatch) -> None:
    evidence = _capture_evidence(monkeypatch, GateConfig(use_no_state_change_proxy=True))

    assert evidence.observed_effect_type == 3
    assert evidence.observed_failed_action is True


def test_text_frcg_plan_with_proxy_off(monkeypatch: pytest.MonkeyPatch) -> None:
    action, metadata = text_frcg_plan(
        _obs(),
        0,
        list(_obs().candidate_actions_public),
        _make_mock_model(),
        PlannerState(),
        GateConfig(use_no_state_change_proxy=False),
    )

    assert action.action_id == "a1"
    assert metadata.planned is False
