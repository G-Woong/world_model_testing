"""Tests for threshold_free_c3_auroc and evidence_accumulation_quality metrics.

Source: TASK_1123_step10_threshold_free_c3
Gate: O-EVAL prerequisite
"""
from __future__ import annotations

import pytest

from frcgw.evaluation.metrics import (
    evidence_accumulation_quality,
    fair_ppc,
    threshold_free_c3_auroc,
)


def _make_episode(steps: list[dict]) -> dict:
    return {"steps": steps, "total_progress": 1.0, "compute_log": {}}


def _make_step(wrong_prob: float, true_wrong: bool | None = None) -> dict:
    step: dict = {"wrong_prob": wrong_prob}
    if true_wrong is not None:
        step["eval_labels"] = {"true_wrong_hypothesis": true_wrong}
    return step


# --- threshold_free_c3_auroc ---

def test_auroc_no_positives_returns_zero() -> None:
    eps = [_make_episode([_make_step(0.8, False), _make_step(0.2, False)])]
    result = threshold_free_c3_auroc(eps)
    assert result["auroc"] == 0.0
    assert result["n_positive"] == 0


def test_auroc_perfect_classifier() -> None:
    # wrong_prob=1.0 for positive, 0.0 for negative
    steps = [_make_step(1.0, True), _make_step(0.0, False), _make_step(1.0, True), _make_step(0.0, False)]
    eps = [_make_episode(steps)]
    result = threshold_free_c3_auroc(eps)
    assert result["auroc"] >= 0.99, f"Expected AUROC≈1.0, got {result['auroc']}"
    assert result["n_positive"] == 2
    assert result["n_total"] == 4


def test_auroc_random_classifier_approx_half() -> None:
    import random
    random.seed(42)
    steps = []
    for _ in range(200):
        twh = random.random() > 0.5
        wp = random.random()
        steps.append(_make_step(wp, twh))
    eps = [_make_episode(steps)]
    result = threshold_free_c3_auroc(eps)
    # Random classifier: AUROC ≈ 0.5 ± 0.1
    assert 0.4 <= result["auroc"] <= 0.6, f"Random AUROC should be ≈0.5, got {result['auroc']}"


def test_auroc_no_labels_returns_zero() -> None:
    steps = [{"wrong_prob": 0.8}, {"wrong_prob": 0.2}]
    eps = [_make_episode(steps)]
    result = threshold_free_c3_auroc(eps)
    assert result["auroc"] == 0.0
    assert result["n_total"] == 0


def test_auroc_in_metric_functions() -> None:
    from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS
    assert "threshold_free_c3_auroc" in METRIC_FUNCTIONS
    assert "fair_ppc" in METRIC_FUNCTIONS
    assert "evidence_accumulation_quality" in METRIC_FUNCTIONS


# --- evidence_accumulation_quality ---

def test_evidence_accumulation_returns_schema() -> None:
    steps = [_make_step(0.8, True), _make_step(0.2, False), _make_step(0.9, True)]
    eps = [_make_episode(steps)]
    result = evidence_accumulation_quality(eps, window=2)
    assert "instantaneous_auroc" in result
    assert "window_auroc" in result
    assert "window_size" in result
    assert result["window_size"] == 2.0


def test_evidence_accumulation_window1_equals_instantaneous() -> None:
    steps = [_make_step(0.9, True), _make_step(0.1, False), _make_step(0.8, True), _make_step(0.2, False)]
    eps = [_make_episode(steps)]
    r_inst = evidence_accumulation_quality(eps, window=1)
    # window=1 should be same as instantaneous
    assert abs(r_inst["window_auroc"] - r_inst["instantaneous_auroc"]) < 0.01


# --- fair_ppc ---

def test_fair_ppc_returns_schema() -> None:
    eps = [{"total_progress": 1.0, "compute_log": {"wall_clock_seconds": 1.0,
            "planning_calls": 2, "rollout_steps": 3, "candidate_actions_scored": 1}}]
    result = fair_ppc(eps)
    assert "ppc_wall_clock" in result
    assert "ppc_self_report" in result
    assert result["ppc_wall_clock"] == pytest.approx(1.0)


def test_fair_ppc_zero_wall_clock() -> None:
    eps = [{"total_progress": 1.0, "compute_log": {"wall_clock_seconds": 0.0,
            "planning_calls": 2, "rollout_steps": 3, "candidate_actions_scored": 1}}]
    result = fair_ppc(eps)
    assert result["ppc_wall_clock"] == 0.0
    assert result["ppc_self_report"] > 0.0
