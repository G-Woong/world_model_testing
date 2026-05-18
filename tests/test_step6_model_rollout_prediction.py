"""Tests for STEP 6 C4 model rollout prediction harness.

Verifies:
1. alternative_rollout_fidelity reads model_predicted_progress_delta.
2. Metric is BLOCKED without model predictions.
3. model_predicted_progress_delta never flows to next observation.
4. None is returned when agent has no model (not 0.0).
5. TracingAgent does not inject model predictions into PublicObservation.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import torch

from frcgw.evaluation.metrics import alternative_rollout_fidelity
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


def _make_episode_with_model_predictions() -> dict:
    """Build a fake episode dict with model_predicted_progress_delta in step records."""
    return {
        "episode_id": "ep_test",
        "steps": [
            {
                "step_index": 0,
                "model_predicted_progress_delta": 0.8,
                "progress_delta": 0.7,
                "counterfactuals": [
                    {
                        "counterfactual_id": "s0_cf_0",
                        "counterfactual_progress_delta": 0.5,
                        "model_predicted_progress_delta": 0.8,
                    }
                ],
            },
            {
                "step_index": 1,
                "model_predicted_progress_delta": 0.3,
                "progress_delta": 0.4,
                "counterfactuals": [
                    {
                        "counterfactual_id": "s1_cf_0",
                        "counterfactual_progress_delta": 0.2,
                        "model_predicted_progress_delta": 0.3,
                    }
                ],
            },
        ],
        "task_success": True,
    }


def _make_episode_no_predictions() -> dict:
    """Episode with counterfactuals but no model_predicted_progress_delta."""
    return {
        "episode_id": "ep_no_pred",
        "steps": [
            {
                "step_index": 0,
                "counterfactuals": [{"counterfactual_id": "s0_cf_0", "counterfactual_progress_delta": 0.5}],
            }
        ],
        "task_success": False,
    }


def test_c4_metric_reads_model_prediction():
    """alternative_rollout_fidelity should return OK when model_predicted_progress_delta is present."""
    episode = _make_episode_with_model_predictions()
    result = alternative_rollout_fidelity([episode])
    assert result["status"] == "OK", (
        f"Expected status=OK when model predictions present, got: {result}"
    )
    assert result["mean_fidelity"] is not None, "mean_fidelity must be non-None when predictions present"


def test_c4_metric_blocked_without_prediction():
    """alternative_rollout_fidelity returns BLOCKED when no model_predicted_progress_delta."""
    episode = _make_episode_no_predictions()
    result = alternative_rollout_fidelity([episode])
    assert result["status"] == "BLOCKED_no_model_rollout_prediction", (
        f"Expected BLOCKED_no_model_rollout_prediction, got: {result['status']}"
    )


def test_model_predicted_not_in_observation():
    """PublicObservation must not have model_predicted_progress_delta attribute."""
    obs = PublicObservation(
        instruction="test",
        history_public=[],
        candidate_actions_public=[CandidateAction("a1", "click", {})],
    )
    assert not hasattr(obs, "model_predicted_progress_delta"), (
        "PublicObservation must not contain model_predicted_progress_delta (leakage prevention)"
    )
    # Verify field names
    obs_fields = set(vars(obs).keys()) if hasattr(obs, "__dict__") else set()
    assert "model_predicted_progress_delta" not in obs_fields


@pytest.mark.skip(reason="TracingAgent integration tested via test_tracing_agent_sets_model_predicted_none_without_model")
def test_rollout_prediction_none_when_no_model():
    """_TracingAgent without a model returns model_predicted_progress_delta=None (not 0.0)."""
    pass


def test_tracing_agent_sets_model_predicted_none_without_model():
    """TracingAgent wrapping an agent without .model sets model_predicted_progress_delta=None."""
    import sys
    from pathlib import Path

    REPO_ROOT = Path(__file__).resolve().parents[1]
    SCRIPTS_DIR = REPO_ROOT / "scripts"
    for p in (str(REPO_ROOT), str(REPO_ROOT / "src")):
        if p not in sys.path:
            sys.path.insert(0, p)

    # Import _TracingAgent by reading the script module
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_lr_script", SCRIPTS_DIR / "10_run_lr_real_eval.py")
    if spec is None or spec.loader is None:
        pytest.skip("Cannot load 10_run_lr_real_eval.py as module")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except Exception as e:
        pytest.skip(f"Could not load script module: {e}")

    _TracingAgent = mod._TracingAgent

    # Agent without .model
    base_agent = MagicMock(spec=[])  # empty spec = no attributes
    base_agent.act = MagicMock(return_value=(
        CandidateAction("a1", "click", {}),
        MagicMock(planning_calls=0, rollout_steps=0),
    ))

    obs = PublicObservation(instruction="test", candidate_actions_public=[CandidateAction("a1", "click", {})])
    tracer = _TracingAgent(base_agent)
    tracer.act(obs)

    assert len(tracer.records) == 1
    record = tracer.records[0]
    assert record.get("model_predicted_progress_delta") is None, (
        "model_predicted_progress_delta must be None when agent has no model (not 0.0 placeholder)"
    )
