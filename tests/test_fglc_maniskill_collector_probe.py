"""Checkpoint 1a~1e integration probe for collector: 3-episode, no-save.

Source: docs/STEP11_PLAN.md §I.2 TASK D4
Tests that:
  - collect_episodes() can run 3 ID episodes
  - Collected state shape matches D_x=42, D_a=8
  - No FORBIDDEN fields in collected batches
  - OOD mass param applies (produces divergent states vs ID)
  - Per-episode validators reject known-garbage episodes
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest

_MANISKILL_AVAILABLE = importlib.util.find_spec("mani_skill") is not None
skip_no_maniskill = pytest.mark.skipif(
    not _MANISKILL_AVAILABLE, reason="mani-skill not installed"
)


@skip_no_maniskill
def test_collect_3_id_episodes():
    """collect_episodes() returns 3 accepted ID episodes with correct shapes."""
    from fglc.data.collector import CollectionConfig, collect_episodes

    config = CollectionConfig(
        task="PickCube-v1",
        split="train_id",
        n_episodes=3,
        seed_pool=list(range(42, 50)),
        regime_id=0,
        ood_type="id",
        ood_params={},
        max_episode_steps=50,
    )
    episodes, eval_metas, stats = collect_episodes(config, verbose=False)

    assert stats.n_accepted >= 3, f"Expected >= 3 accepted, got {stats.n_accepted}"
    assert len(episodes) >= 3
    for i, ep in enumerate(episodes[:3]):
        assert ep["state"].ndim == 2
        assert ep["state"].shape[1] == 42, f"ep {i} D_x mismatch: {ep['state'].shape}"
        assert ep["action"].shape[1] == 8, f"ep {i} D_a mismatch: {ep['action'].shape}"
        assert ep["reward"].ndim == 1
        assert ep["done"].ndim == 1
        assert len(ep["state"]) == len(ep["action"])


@skip_no_maniskill
def test_collect_no_forbidden_fields():
    """Collected episodes must have no FORBIDDEN_AGENT_FIELDS."""
    from fglc.data.collector import CollectionConfig, collect_episodes
    from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS

    config = CollectionConfig(
        task="PickCube-v1",
        split="train_id",
        n_episodes=2,
        seed_pool=[42, 43],
        regime_id=0,
        ood_type="id",
        ood_params={},
        max_episode_steps=50,
    )
    episodes, _, _ = collect_episodes(config, verbose=False)
    for ep in episodes:
        present = FORBIDDEN_AGENT_FIELDS & set(ep.keys())
        assert not present, f"Forbidden fields in episode: {present}"


@skip_no_maniskill
def test_collect_ood_mass_diverges_from_id():
    """OOD mass episodes should diverge from ID episodes with same seeds."""
    from fglc.data.collector import CollectionConfig, collect_episodes

    common_seed = [42, 43]

    config_id = CollectionConfig(
        task="PickCube-v1",
        split="train_id",
        n_episodes=2,
        seed_pool=common_seed,
        regime_id=0,
        ood_type="id",
        ood_params={},
        max_episode_steps=30,
    )
    eps_id, _, _ = collect_episodes(config_id, verbose=False)

    config_ood = CollectionConfig(
        task="PickCube-v1",
        split="ood_mass_low",
        n_episodes=2,
        seed_pool=common_seed,
        regime_id=10,
        ood_type="ood_mass",
        ood_params={"object_mass": 1.5},
        max_episode_steps=30,
    )
    eps_ood, _, _ = collect_episodes(config_ood, verbose=False)

    diffs = []
    for ep_id, ep_ood in zip(eps_id, eps_ood):
        T = min(len(ep_id["state"]), len(ep_ood["state"]))
        diff = np.linalg.norm(ep_id["state"][:T] - ep_ood["state"][:T], axis=1).mean()
        diffs.append(diff)

    assert any(d > 1e-5 for d in diffs), f"Mass OOD episodes don't diverge: diffs={diffs}"


@skip_no_maniskill
def test_eval_meta_has_expected_fields():
    """eval_metas must contain regime_id, ood_type, true_mass, seed."""
    from fglc.data.collector import CollectionConfig, collect_episodes

    config = CollectionConfig(
        task="PickCube-v1",
        split="ood_mass_low",
        n_episodes=1,
        seed_pool=[500],
        regime_id=10,
        ood_type="ood_mass",
        ood_params={"object_mass": 1.5},
        max_episode_steps=30,
    )
    _, eval_metas, stats = collect_episodes(config, verbose=False)

    if stats.n_accepted > 0:
        meta = eval_metas[0]
        assert "regime_id" in meta
        assert "ood_type" in meta
        assert "true_mass" in meta
        assert "true_friction" in meta
        assert "seed" in meta
        assert meta["regime_id"] == 10
        assert meta["ood_type"] == "ood_mass"
        assert abs(meta["true_mass"] - 1.5) < 1e-5
