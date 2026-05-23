"""Per-episode data quality validators for Step 11 ManiSkill collection.

Source: docs/STEP11_PLAN.md §F.3 Per-episode inline validation
10 reject reasons checked per episode before it enters the storage queue.

Usage:
    from fglc.data.validators import validate_episode, EpisodeRejectReason
    result = validate_episode(states, actions, rewards, dones, min_episode_len=10)
    if result is not None:
        # quarantine episode, log result
"""

from __future__ import annotations

import hashlib
from enum import Enum

import numpy as np


class EpisodeRejectReason(str, Enum):
    ALL_STATE_STATIC = "all_state_static"
    ALL_ACTION_ZERO = "all_action_zero"
    NO_TRANSITION = "no_transition"
    REWARD_FLAT = "reward_flat"
    EPISODE_TOO_SHORT = "episode_too_short"
    EPISODE_SHORT = "episode_short"
    NO_DONE_SIGNAL = "no_done_signal"
    DONE_FLOOD = "done_flood"
    NUMERICAL_INVALID = "numerical_invalid"
    EPISODE_DUPLICATE = "episode_duplicate"


def validate_episode(
    states: np.ndarray,
    actions: np.ndarray,
    rewards: np.ndarray,
    dones: np.ndarray,
    min_episode_len: int = 10,
    seen_state_hashes: set[str] | None = None,
) -> EpisodeRejectReason | None:
    """Validate one episode. Returns None if OK, else the reject reason.

    Args:
        states:   float32 array of shape (T, D_x)
        actions:  float32 array of shape (T, D_a)
        rewards:  float32 array of shape (T,)
        dones:    bool array   of shape (T,)
        min_episode_len: minimum accepted episode length (exclusive)
        seen_state_hashes: optional mutable set for duplicate state-trajectory hashes
    """
    T = len(states)

    # 1. episode_too_short: len < 2
    if T < 2:
        return EpisodeRejectReason.EPISODE_TOO_SHORT

    # 2. episode_short: len < min_episode_len
    if T < min_episode_len:
        return EpisodeRejectReason.EPISODE_SHORT

    # 3. numerical_invalid: NaN or Inf anywhere
    if (
        np.any(~np.isfinite(states))
        or np.any(~np.isfinite(actions))
        or np.any(~np.isfinite(rewards))
    ):
        return EpisodeRejectReason.NUMERICAL_INVALID

    # 4. all_state_static: all states nearly identical
    if np.std(states, axis=0).max() < 1e-4:
        return EpisodeRejectReason.ALL_STATE_STATIC

    # 5. all_action_zero: all actions near zero
    if np.abs(actions).max() < 1e-3:
        return EpisodeRejectReason.ALL_ACTION_ZERO

    # 6. no_transition: consecutive state differences near zero
    state_diffs = np.linalg.norm(np.diff(states, axis=0), axis=1)
    if state_diffs.mean() < 1e-4:
        return EpisodeRejectReason.NO_TRANSITION

    # 7. reward_flat: zero variance in rewards
    if np.std(rewards) < 1e-6:
        return EpisodeRejectReason.REWARD_FLAT

    # 8. no_done_signal: done never fires (all False)
    if not np.any(dones):
        return EpisodeRejectReason.NO_DONE_SIGNAL

    # 9. done_flood: done fires at every step except possibly the last
    if np.all(dones[:-1]):
        return EpisodeRejectReason.DONE_FLOOD

    # 10. episode_duplicate: exact duplicate state trajectory hash
    if seen_state_hashes is not None:
        state_hash = hashlib.sha1(states.tobytes()).hexdigest()
        if state_hash in seen_state_hashes:
            return EpisodeRejectReason.EPISODE_DUPLICATE
        seen_state_hashes.add(state_hash)

    return None
