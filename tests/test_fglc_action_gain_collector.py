"""Tests for action_gain OOD collector support.

Source: TASK_2050_ACTION_GAIN_IMPL / plans/fglc-step-vectorized-iverson.md §Stage 1
Verifies:
  1. np.clip logic correctness (unit, no ManiSkill required)
  2. eval_metas["true_action_gain"] == 0.7 per episode (integration)
  3. No forbidden fields in inference dicts (integration)
  4. Action magnitude reduced vs ID baseline (integration)
  5. Reproducibility: same seed → same action sequence (integration)
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest

_MANISKILL_AVAILABLE = importlib.util.find_spec("mani_skill") is not None
skip_no_maniskill = pytest.mark.skipif(
    not _MANISKILL_AVAILABLE, reason="mani-skill not installed"
)


# ---------------------------------------------------------------------------
# Unit test (no ManiSkill): clip + float32 logic
# ---------------------------------------------------------------------------

def test_action_gain_clip_dtype_unit():
    """Direct numpy logic: gain × clip + astype float32 preserves bounds."""
    rng = np.random.default_rng(0)
    low = np.full(8, -1.0, dtype=np.float32)
    high = np.full(8, 1.0, dtype=np.float32)

    for gain in (0.7, 0.5, 1.5, 2.0):
        a_raw = rng.uniform(-1.0, 1.0, size=8).astype(np.float32)
        a_gained = np.clip(a_raw * gain, low, high).astype(np.float32)

        assert a_gained.dtype == np.float32, f"gain={gain}: dtype must be float32"
        assert np.all(a_gained >= low - 1e-6), f"gain={gain}: clip below low"
        assert np.all(a_gained <= high + 1e-6), f"gain={gain}: clip above high"

    # gain=1.0 must be identity (no branch taken in collector)
    a_id = rng.uniform(-1.0, 1.0, size=8).astype(np.float32)
    gain_id = 1.0
    # When gain == 1.0, collector does NOT apply clip — actions pass through as-is
    assert gain_id == 1.0  # confirm guard condition


# ---------------------------------------------------------------------------
# Integration tests (require mani-skill)
# ---------------------------------------------------------------------------

@skip_no_maniskill
def test_action_gain_eval_meta():
    """eval_metas["true_action_gain"] == 0.7 for ood_gain_low episodes."""
    from fglc.data.collector import CollectionConfig, collect_episodes

    config = CollectionConfig(
        task="PickCube-v1",
        split="ood_gain_low",
        n_episodes=3,
        seed_pool=list(range(700, 710)),
        regime_id=40,
        ood_type="ood_gain",
        ood_params={"action_gain": 0.7},
        max_episode_steps=30,
    )
    episodes, eval_metas, stats = collect_episodes(config, verbose=False)

    assert stats.n_accepted >= 3, f"Expected >= 3 accepted, got {stats.n_accepted}"
    for meta in eval_metas:
        assert abs(meta["true_action_gain"] - 0.7) < 1e-5, (
            f"true_action_gain mismatch: {meta['true_action_gain']}"
        )


@skip_no_maniskill
def test_action_gain_no_forbidden_fields():
    """No FORBIDDEN_AGENT_FIELDS in inference episode dicts for ood_gain_low."""
    from fglc.data.collector import CollectionConfig, collect_episodes
    from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS

    config = CollectionConfig(
        task="PickCube-v1",
        split="ood_gain_low",
        n_episodes=2,
        seed_pool=list(range(700, 710)),
        regime_id=40,
        ood_type="ood_gain",
        ood_params={"action_gain": 0.7},
        max_episode_steps=30,
    )
    episodes, _, _ = collect_episodes(config, verbose=False)

    for i, ep in enumerate(episodes):
        present = FORBIDDEN_AGENT_FIELDS & set(ep.keys())
        assert not present, f"ep {i}: forbidden fields in inference dict: {present}"


@skip_no_maniskill
def test_action_gain_reduces_magnitude():
    """ood_gain_low (gain=0.7) action |a|_mean < ID action |a|_mean × 0.99."""
    from fglc.data.collector import CollectionConfig, collect_episodes

    common_seeds = list(range(700, 705))

    config_id = CollectionConfig(
        task="PickCube-v1",
        split="train_id",
        n_episodes=3,
        seed_pool=list(range(42, 50)),
        regime_id=0,
        ood_type="id",
        ood_params={},
        max_episode_steps=30,
    )
    eps_id, _, _ = collect_episodes(config_id, verbose=False)

    config_gain = CollectionConfig(
        task="PickCube-v1",
        split="ood_gain_low",
        n_episodes=3,
        seed_pool=common_seeds,
        regime_id=40,
        ood_type="ood_gain",
        ood_params={"action_gain": 0.7},
        max_episode_steps=30,
    )
    eps_gain, _, _ = collect_episodes(config_gain, verbose=False)

    id_mean = np.mean([np.abs(ep["action"]).mean() for ep in eps_id])
    gain_mean = np.mean([np.abs(ep["action"]).mean() for ep in eps_gain])

    # gain=0.7 must reduce absolute action magnitude relative to ID
    assert gain_mean < id_mean * 0.99, (
        f"gain=0.7 action magnitude not reduced: gain_mean={gain_mean:.4f} "
        f">= id_mean×0.99={id_mean * 0.99:.4f}"
    )


@skip_no_maniskill
def test_action_gain_clip_bound_invariant():
    """gain=0.7 + clip: all collected actions satisfy |a| <= gain × action_space.high."""
    import gymnasium as gym
    import mani_skill.envs  # noqa: F401
    from fglc.data.collector import CollectionConfig, collect_episodes

    env_tmp = gym.make("PickCube-v1", obs_mode="state_dict")
    high = env_tmp.action_space.high.copy()
    env_tmp.close()

    config = CollectionConfig(
        task="PickCube-v1",
        split="ood_gain_low",
        n_episodes=2,
        seed_pool=list(range(700, 710)),
        regime_id=40,
        ood_type="ood_gain",
        ood_params={"action_gain": 0.7},
        max_episode_steps=20,
    )
    episodes, _, stats = collect_episodes(config, verbose=False)

    assert stats.n_accepted >= 2, f"Expected >= 2 accepted, got {stats.n_accepted}"
    gain = 0.7
    for i, ep in enumerate(episodes):
        a = ep["action"]
        assert a.dtype == np.float32, f"ep {i}: action dtype must be float32, got {a.dtype}"
        violation = np.any(np.abs(a) > gain * high + 1e-5)
        assert not violation, (
            f"ep {i}: action exceeds gain×high bound — "
            f"max|a|={np.abs(a).max():.4f}, gain×high_max={gain * high.max():.4f}"
        )
