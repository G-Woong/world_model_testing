"""Tests for GUI leakage audit contract."""
from __future__ import annotations

import pytest

from frcgw.gui_env.leakage_audit import (
    FORBIDDEN_GUI_AGENT_FIELDS,
    GUILeakageError,
    audit_gui_observation,
)
from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS


def test_clean_observation_passes():
    result = audit_gui_observation({
        "observation_id": "obs-1",
        "visible_text": "Login",
        "clickable_elements": ["login_button"],
    })
    assert result.passed is True
    assert result.violations == []


def test_forbidden_field_raises():
    with pytest.raises(GUILeakageError) as exc_info:
        audit_gui_observation({"visible_text": "x", "true_grammar": "modal"})
    assert exc_info.value.violations == ["true_grammar"]


def test_multiple_violations_reported():
    with pytest.raises(GUILeakageError) as exc_info:
        audit_gui_observation({
            "true_grammar": "modal",
            "nested": {"oracle_target": "confirm"},
        })
    assert len(exc_info.value.violations) >= 2
    assert {"true_grammar", "oracle_target"} <= set(exc_info.value.violations)


def test_visibility_forbidden_fields_covered():
    assert FORBIDDEN_AGENT_FIELDS <= FORBIDDEN_GUI_AGENT_FIELDS
