"""Tests for split integrity: seed pool disjoint, OOD severity gate.

Source: docs/STEP11_PLAN.md §I.2 TASK D5, §G Checkpoint 3
"""

from __future__ import annotations

import numpy as np
import pytest


class TestSeedPoolDisjoint:
    def test_default_split_pools_are_disjoint(self):
        """All 5 default split seed pools have no pairwise overlap."""
        from fglc.data.manifest import verify_split_integrity

        split_configs = {
            "train_id":         {"seed_pool": list(range(42, 92)),   "ood_params": {}},
            "val_id":           {"seed_pool": list(range(200, 210)),  "ood_params": {}},
            "test_id":          {"seed_pool": list(range(300, 310)),  "ood_params": {}},
            "ood_mass_low":     {"seed_pool": list(range(500, 510)),  "ood_params": {"object_mass": 1.5}},
            "ood_friction_low": {"seed_pool": list(range(600, 610)),  "ood_params": {"joint_friction": 5.0}},
        }
        ok, violations = verify_split_integrity(split_configs)
        assert ok, f"Seed pool violations: {violations}"
        assert violations == []

    def test_overlapping_pools_detected(self):
        """verify_split_integrity returns False + violation when pools overlap."""
        from fglc.data.manifest import verify_split_integrity

        configs = {
            "a": {"seed_pool": [1, 2, 3], "ood_params": {}},
            "b": {"seed_pool": [3, 4, 5], "ood_params": {}},
        }
        ok, violations = verify_split_integrity(configs)
        assert not ok
        assert len(violations) == 1
        assert "a" in violations[0] and "b" in violations[0]

    def test_no_overlap_returns_empty_violations(self):
        from fglc.data.manifest import verify_split_integrity

        configs = {
            "x": {"seed_pool": [10, 20, 30], "ood_params": {}},
            "y": {"seed_pool": [40, 50, 60], "ood_params": {}},
        }
        ok, violations = verify_split_integrity(configs)
        assert ok
        assert violations == []


class TestOODSeverityGate:
    def _make_stats(self, delta_norm_mean: float) -> dict:
        return {
            "split": "stub",
            "n_episodes": 3,
            "D_x": 42,
            "D_a": 8,
            "state_mean": [0.0] * 42,
            "state_std": [1.0] * 42,
            "action_mean": [0.0] * 8,
            "action_std": [1.0] * 8,
            "state_delta_norm_mean": delta_norm_mean,
            "state_delta_norm_p50": delta_norm_mean,
            "state_delta_norm_p95": delta_norm_mean * 2,
            "reward_mean": 0.0,
            "reward_std": 0.1,
            "reward_min": -1.0,
            "reward_max": 1.0,
            "episode_length_mean": 50.0,
            "episode_length_min": 30,
            "episode_length_max": 70,
            "episode_length_stdev": 10.0,
            "nan_inf_count": 0,
        }

    def test_large_gap_passes(self):
        from fglc.data.manifest import verify_ood_severity

        id_stats = self._make_stats(0.05)
        ood_stats = self._make_stats(0.15)
        ok, gap = verify_ood_severity(id_stats, ood_stats, delta_min=0.01)
        assert ok
        assert abs(gap - 0.10) < 1e-9

    def test_small_gap_fails(self):
        from fglc.data.manifest import verify_ood_severity

        id_stats = self._make_stats(0.10)
        ood_stats = self._make_stats(0.105)
        ok, gap = verify_ood_severity(id_stats, ood_stats, delta_min=0.01)
        assert not ok

    def test_gap_is_absolute_value(self):
        """Gap computation uses absolute difference."""
        from fglc.data.manifest import verify_ood_severity

        id_stats = self._make_stats(0.15)
        ood_stats = self._make_stats(0.05)
        ok, gap = verify_ood_severity(id_stats, ood_stats, delta_min=0.01)
        assert ok
        assert abs(gap - 0.10) < 1e-9


class TestBuildDatasetStats:
    def _make_episodes(self, n: int = 3, T: int = 20, D_x: int = 42, D_a: int = 8) -> list:
        rng = np.random.default_rng(77)
        eps = []
        for _ in range(n):
            s = rng.normal(size=(T, D_x)).astype(np.float32)
            a = rng.normal(size=(T, D_a)).astype(np.float32)
            r = rng.normal(size=(T,)).astype(np.float32)
            d = np.zeros(T, dtype=bool); d[-1] = True
            eps.append({"state": s, "action": a, "reward": r, "done": d})
        return eps

    def test_stats_keys_present(self):
        from fglc.data.manifest import build_dataset_stats

        episodes = self._make_episodes()
        stats = build_dataset_stats(episodes, "train_id")
        required = [
            "split", "n_episodes", "D_x", "D_a",
            "state_mean", "state_std", "action_mean", "action_std",
            "state_delta_norm_mean", "state_delta_norm_p50", "state_delta_norm_p95",
            "reward_mean", "reward_std", "reward_min", "reward_max",
            "episode_length_mean", "episode_length_min", "episode_length_max",
            "episode_length_stdev", "nan_inf_count",
        ]
        for k in required:
            assert k in stats, f"Missing key: {k}"

    def test_nan_inf_count_zero_for_clean_data(self):
        from fglc.data.manifest import build_dataset_stats

        episodes = self._make_episodes()
        stats = build_dataset_stats(episodes, "train_id")
        assert stats["nan_inf_count"] == 0

    def test_dim_correct(self):
        from fglc.data.manifest import build_dataset_stats

        episodes = self._make_episodes(D_x=42, D_a=8)
        stats = build_dataset_stats(episodes, "train_id")
        assert stats["D_x"] == 42
        assert stats["D_a"] == 8
        assert len(stats["state_mean"]) == 42
        assert len(stats["action_mean"]) == 8


class TestTrajectoryHashAudit:
    def _episode(self, offset: float) -> dict:
        state = (np.arange(12, dtype=np.float32).reshape(3, 4) + offset).astype(np.float32)
        action = np.zeros((3, 2), dtype=np.float32)
        reward = np.zeros(3, dtype=np.float32)
        done = np.array([False, False, True], dtype=bool)
        return {"state": state, "action": action, "reward": reward, "done": done}

    def test_no_hash_duplicate_in_clean_splits(self):
        from scripts.fglc.build_split import audit_trajectory_hashes

        result = audit_trajectory_hashes({
            "train_id": [self._episode(0.0), self._episode(10.0)],
            "val_id": [self._episode(20.0)],
        })
        assert result["hash_intra_duplicate_count"] == 0
        assert result["hash_inter_duplicate_count"] == 0
        assert result["hash_collision_pairs"] == []

    def test_hash_duplicate_detected_intra(self):
        from scripts.fglc.build_split import audit_trajectory_hashes

        dup = self._episode(0.0)
        result = audit_trajectory_hashes({
            "train_id": [dup, {"state": dup["state"].copy(), "action": dup["action"], "reward": dup["reward"], "done": dup["done"]}],
        })
        assert result["hash_intra_duplicate_count"] > 0
        assert result["hash_inter_duplicate_count"] == 0
        assert result["hash_collision_pairs"]

    def test_hash_duplicate_detected_inter(self):
        from scripts.fglc.build_split import audit_trajectory_hashes

        dup = self._episode(0.0)
        result = audit_trajectory_hashes({
            "train_id": [dup],
            "val_id": [{"state": dup["state"].copy(), "action": dup["action"], "reward": dup["reward"], "done": dup["done"]}],
        })
        assert result["hash_intra_duplicate_count"] == 0
        assert result["hash_inter_duplicate_count"] > 0
        assert result["hash_collision_pairs"]
