"""Tests that all 9 garbage reject reasons fire correctly.

Source: docs/STEP11_PLAN.md §F.3, §I.2 TASK D2
Validates EpisodeRejectReason enum + validate_episode() function with
synthetic garbage datasets for each rejection case.
"""

from __future__ import annotations

import numpy as np
import pytest

from fglc.data.validators import EpisodeRejectReason, validate_episode

# Default valid episode params
_T = 20
_Dx = 42
_Da = 8


def _valid_episode(T=_T, Dx=_Dx, Da=_Da):
    """Generate a valid episode with clear dynamics signal."""
    np.random.seed(0)
    states = np.random.randn(T, Dx).astype(np.float32) * 0.1
    # Ensure state std > 1e-4 and consecutive diffs > 1e-4
    for t in range(1, T):
        states[t] = states[t - 1] + np.random.randn(Dx).astype(np.float32) * 0.05
    actions = np.random.randn(T, Da).astype(np.float32) * 0.3
    rewards = np.random.randn(T).astype(np.float32) * 0.1 + 0.5
    dones = np.zeros(T, dtype=bool)
    dones[-1] = True
    return states, actions, rewards, dones


def test_valid_episode_passes():
    states, actions, rewards, dones = _valid_episode()
    result = validate_episode(states, actions, rewards, dones)
    assert result is None, f"Valid episode rejected: {result}"


def test_episode_too_short_len1():
    states, actions, rewards, dones = _valid_episode(T=1)
    result = validate_episode(states, actions, rewards, dones)
    assert result == EpisodeRejectReason.EPISODE_TOO_SHORT


def test_episode_short_below_min():
    """Episode with len < min_episode_len (default=10) but >= 2."""
    states, actions, rewards, dones = _valid_episode(T=5)
    result = validate_episode(states, actions, rewards, dones, min_episode_len=10)
    assert result == EpisodeRejectReason.EPISODE_SHORT


def test_episode_short_exactly_min_passes():
    """Episode with len == min_episode_len should pass the length check."""
    states, actions, rewards, dones = _valid_episode(T=10)
    result = validate_episode(states, actions, rewards, dones, min_episode_len=10)
    assert result is None, f"Episode of exact min_len rejected: {result}"


def test_numerical_invalid_nan_in_states():
    states, actions, rewards, dones = _valid_episode()
    states[5, 3] = float("nan")
    result = validate_episode(states, actions, rewards, dones)
    assert result == EpisodeRejectReason.NUMERICAL_INVALID


def test_numerical_invalid_inf_in_actions():
    states, actions, rewards, dones = _valid_episode()
    actions[2, 1] = float("inf")
    result = validate_episode(states, actions, rewards, dones)
    assert result == EpisodeRejectReason.NUMERICAL_INVALID


def test_numerical_invalid_inf_in_rewards():
    states, actions, rewards, dones = _valid_episode()
    rewards[3] = float("-inf")
    result = validate_episode(states, actions, rewards, dones)
    assert result == EpisodeRejectReason.NUMERICAL_INVALID


def test_all_state_static():
    """All states equal -> all_state_static reject."""
    states, actions, rewards, dones = _valid_episode()
    states[:] = 0.5
    result = validate_episode(states, actions, rewards, dones)
    assert result == EpisodeRejectReason.ALL_STATE_STATIC


def test_all_action_zero():
    """All actions near zero -> all_action_zero reject."""
    states, actions, rewards, dones = _valid_episode()
    actions[:] = 1e-5
    result = validate_episode(states, actions, rewards, dones)
    assert result == EpisodeRejectReason.ALL_ACTION_ZERO


def test_no_transition():
    """mean consecutive L2 diff < 1e-4 triggers no_transition.

    Construction: only feature 0 varies linearly from 0 to a=5e-4 over T steps.
    - std(states[:,0]) = 5e-4 * 0.303 ~= 1.52e-4 > 1e-4  -> ALL_STATE_STATIC doesn't fire
    - consecutive diff = 5e-4/19 ~= 2.6e-5 < 1e-4/sqrt(1) -> NO_TRANSITION fires
    """
    T, Da = _T, _Da
    Dx = _Dx

    states = np.zeros((T, Dx), dtype=np.float32)
    a_end = 5e-4  # linear increase for feature 0 only
    states[:, 0] = np.linspace(0.0, a_end, T, dtype=np.float32)

    # Valid actions / rewards / dones (so only NO_TRANSITION fires)
    _, actions, rewards, dones = _valid_episode()

    result = validate_episode(states, actions, rewards, dones)
    assert result == EpisodeRejectReason.NO_TRANSITION, (
        f"Expected NO_TRANSITION, got {result}. "
        f"max_std={np.std(states, axis=0).max():.2e}, "
        f"mean_diff={np.linalg.norm(np.diff(states, axis=0), axis=1).mean():.2e}"
    )


def test_reward_flat():
    """Constant reward -> reward_flat reject."""
    states, actions, rewards, dones = _valid_episode()
    rewards[:] = 0.42
    result = validate_episode(states, actions, rewards, dones)
    assert result == EpisodeRejectReason.REWARD_FLAT


def test_no_done_signal():
    """No done=True ever -> no_done_signal reject."""
    states, actions, rewards, dones = _valid_episode()
    dones[:] = False
    result = validate_episode(states, actions, rewards, dones)
    assert result == EpisodeRejectReason.NO_DONE_SIGNAL


def test_done_flood():
    """Done fires at every step except last -> done_flood reject."""
    states, actions, rewards, dones = _valid_episode()
    dones[:-1] = True
    dones[-1] = False
    result = validate_episode(states, actions, rewards, dones)
    assert result == EpisodeRejectReason.DONE_FLOOD


def test_all_nine_reject_reasons_in_enum():
    """All 9 reject reasons must be present in the enum."""
    expected = {
        "all_state_static",
        "all_action_zero",
        "no_transition",
        "reward_flat",
        "episode_too_short",
        "episode_short",
        "no_done_signal",
        "done_flood",
        "numerical_invalid",
    }
    actual = {r.value for r in EpisodeRejectReason}
    assert actual == expected, f"Enum mismatch: missing={expected-actual}, extra={actual-expected}"
