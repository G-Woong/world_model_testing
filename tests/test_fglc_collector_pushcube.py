"""PushCube-v1 collector integration probe tests.

Requires mani-skill installed. Tests verify no AttributeError on mass OOD apply,
correct shapes, and no forbidden fields in collected episodes.
Source: plans/fglc-step-vectorized-iverson.md §K TASK Q6 REQUIRED_TESTS [T1]
"""

from __future__ import annotations

import importlib

import pytest

_MANISKILL_AVAILABLE = importlib.util.find_spec("mani_skill") is not None
skip_no_maniskill = pytest.mark.skipif(
    not _MANISKILL_AVAILABLE, reason="mani-skill not installed"
)


@skip_no_maniskill
def test_pushcube_collect_5ep_probe():
    """PushCube-v1 5ep probe: no AttributeError, D_x > 0, D_a == 8."""
    from fglc.data.collector import CollectionConfig, collect_episodes

    config = CollectionConfig(
        task="PushCube-v1",
        split="train_id",
        n_episodes=5,
        seed_pool=list(range(1042, 1055)),
        regime_id=0,
        ood_type="id",
        ood_params={},
        max_episode_steps=50,
    )
    episodes, eval_metas, stats = collect_episodes(config, verbose=False)

    assert stats.n_accepted >= 5, f"Expected >= 5 accepted, got {stats.n_accepted}"
    assert len(episodes) >= 5
    for i, ep in enumerate(episodes[:5]):
        assert ep["state"].ndim == 2, f"ep {i} state not 2D"
        D_x = ep["state"].shape[1]
        assert D_x > 0, f"ep {i} D_x must be positive, got {D_x}"
        assert ep["action"].shape[1] == 8, f"ep {i} D_a mismatch: {ep['action'].shape}"
        assert ep["reward"].ndim == 1
        assert ep["done"].ndim == 1


@skip_no_maniskill
def test_pushcube_ood_mass_collect_3ep():
    """PushCube-v1 ood_mass_low 3ep probe: no AttributeError from _apply_ood."""
    from fglc.data.collector import CollectionConfig, collect_episodes

    config = CollectionConfig(
        task="PushCube-v1",
        split="ood_mass_low",
        n_episodes=3,
        seed_pool=list(range(1800, 1815)),
        regime_id=10,
        ood_type="ood_mass",
        ood_params={"object_mass": 1.5},
        max_episode_steps=50,
    )
    episodes, eval_metas, stats = collect_episodes(config, verbose=False)

    assert stats.n_accepted >= 3, f"Expected >= 3 accepted, got {stats.n_accepted}"
    for meta in eval_metas:
        assert abs(meta["true_mass"] - 1.5) < 1e-5, f"true_mass mismatch: {meta['true_mass']}"


@skip_no_maniskill
def test_pushcube_no_forbidden_fields():
    """PushCube-v1 collected episodes must have no FORBIDDEN_AGENT_FIELDS."""
    from fglc.data.collector import CollectionConfig, collect_episodes
    from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS

    config = CollectionConfig(
        task="PushCube-v1",
        split="train_id",
        n_episodes=2,
        seed_pool=list(range(1042, 1050)),
        regime_id=0,
        ood_type="id",
        ood_params={},
        max_episode_steps=30,
    )
    episodes, _, _ = collect_episodes(config, verbose=False)
    for ep in episodes:
        present = FORBIDDEN_AGENT_FIELDS & set(ep.keys())
        assert not present, f"Forbidden fields in PushCube episode: {present}"
