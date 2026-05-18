"""Tests for STEP 6 C1 persistence_v1 metric dispatch (B5 fix).

Verifies:
1. wrong_grammar_persistence_v1 is in METRIC_FUNCTIONS.
2. It is callable.
3. It returns a dict with required keys.
"""
from __future__ import annotations

import pytest


def test_persistence_v1_in_metric_functions():
    """compute_wrong_grammar_persistence_v1 must be dispatched in METRIC_FUNCTIONS."""
    from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS

    assert "wrong_grammar_persistence_v1" in METRIC_FUNCTIONS, (
        "C1 persistence_v1 metric must be registered in METRIC_FUNCTIONS (B5 fix)"
    )


def test_persistence_v1_callable():
    """METRIC_FUNCTIONS['wrong_grammar_persistence_v1'] must be callable."""
    from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS

    fn = METRIC_FUNCTIONS["wrong_grammar_persistence_v1"]
    assert callable(fn), "wrong_grammar_persistence_v1 must be callable"


def test_persistence_v1_returns_dict():
    """compute_wrong_grammar_persistence_v1([]) returns dict with required keys."""
    from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS

    result = METRIC_FUNCTIONS["wrong_grammar_persistence_v1"]([])
    assert isinstance(result, dict), f"wrong_grammar_persistence_v1 must return dict, got {type(result)}"

    required_keys = {"mean_persistence", "median", "count_blocked", "count_episodes", "status"}
    assert required_keys <= set(result.keys()), (
        f"Missing keys: {required_keys - set(result.keys())}"
    )


def test_persistence_v1_blocked_on_empty():
    """On empty input, status must be BLOCKED (not an error)."""
    from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS

    result = METRIC_FUNCTIONS["wrong_grammar_persistence_v1"]([])
    assert result["status"] == "BLOCKED", (
        f"Empty input must return status=BLOCKED, got: {result['status']}"
    )


def test_persistence_v1_is_compute_wrong_grammar_persistence_v1():
    """METRIC_FUNCTIONS must dispatch to compute_wrong_grammar_persistence_v1 specifically."""
    from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS
    from frcgw.evaluation.metrics import compute_wrong_grammar_persistence_v1

    assert METRIC_FUNCTIONS["wrong_grammar_persistence_v1"] is compute_wrong_grammar_persistence_v1, (
        "METRIC_FUNCTIONS must reference compute_wrong_grammar_persistence_v1 from metrics.py"
    )


def test_legacy_persistence_still_dispatched():
    """Legacy wrong_control_grammar_persistence must still be in METRIC_FUNCTIONS."""
    from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS

    assert "wrong_control_grammar_persistence" in METRIC_FUNCTIONS, (
        "Legacy persistence metric must remain in METRIC_FUNCTIONS (backward compatibility)"
    )
