"""Tests for GUI replay determinism."""
from __future__ import annotations

from frcgw.gui_env.replay_validator import GUIReplayResult, GUIReplayValidator


def _trace() -> list[dict[str, object]]:
    return [
        {"type": "NAVIGATE", "url": "https://mve.local/account"},
        {"type": "CLICK", "element_id": "account_menu"},
        {"type": "CLICK", "element_id": "login_button"},
    ]


def test_same_seed_same_result():
    validator = GUIReplayValidator()
    first = validator.validate_result(42, _trace())
    second = validator.validate_result(42, _trace())
    assert first == second
    assert validator.validate(42, _trace()) is True


def test_different_seed_may_differ():
    validator = GUIReplayValidator()
    first = validator.validate_result(42, _trace())
    second = validator.validate_result(99, _trace())
    assert isinstance(first.outcome_hash, str)
    assert isinstance(second.outcome_hash, str)
    assert first.is_valid is True
    assert second.is_valid is True


def test_empty_trace_valid():
    result = GUIReplayValidator().validate_result(42, [])
    assert result.is_valid is True
    assert result.mismatch_step is None


def test_replay_result_fields():
    result = GUIReplayValidator().validate_result(42, _trace())
    assert isinstance(result, GUIReplayResult)
    assert hasattr(result, "is_valid")
    assert hasattr(result, "outcome_hash")
