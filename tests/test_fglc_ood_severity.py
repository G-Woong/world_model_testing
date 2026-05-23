"""OOD severity gate tests using ManiSkill stub episodes.

Source: docs/STEP11_PLAN.md §I.2 TASK D5, §G Checkpoint 4

Tests that:
  - ID and OOD (mass=1.5 / friction=5.0) yield measurably different state trajectories
    when using synthetic-but-representative episodes.
  - WelfordStats incremental tracking matches batch stats.
"""

from __future__ import annotations

import numpy as np
import pytest


def _make_id_episodes(n: int = 5, T: int = 30, D_x: int = 42, D_a: int = 8) -> list:
    rng = np.random.default_rng(42)
    return [
        {
            "state":  rng.normal(loc=0.0, scale=1.0, size=(T, D_x)).astype(np.float32),
            "action": rng.normal(size=(T, D_a)).astype(np.float32),
            "reward": rng.normal(size=(T,)).astype(np.float32),
            "done":   np.array([False] * (T - 1) + [True]),
        }
        for _ in range(n)
    ]


def _make_ood_episodes(n: int = 5, T: int = 30, D_x: int = 42, D_a: int = 8, scale: float = 3.0) -> list:
    """OOD episodes with larger state delta (simulates higher mass/friction dynamics)."""
    rng = np.random.default_rng(99)
    return [
        {
            "state":  rng.normal(loc=0.0, scale=scale, size=(T, D_x)).astype(np.float32),
            "action": rng.normal(size=(T, D_a)).astype(np.float32),
            "reward": rng.normal(size=(T,)).astype(np.float32),
            "done":   np.array([False] * (T - 1) + [True]),
        }
        for _ in range(n)
    ]


class TestOODSeverityMetrics:
    def test_ood_delta_larger_than_id(self):
        """OOD episodes should have larger state_delta_norm_mean than ID."""
        from fglc.data.manifest import build_dataset_stats, verify_ood_severity

        id_eps = _make_id_episodes()
        ood_eps = _make_ood_episodes(scale=3.0)
        id_stats = build_dataset_stats(id_eps, "train_id")
        ood_stats = build_dataset_stats(ood_eps, "ood_mass_low")
        ok, gap = verify_ood_severity(id_stats, ood_stats, delta_min=0.01)
        assert ok, f"OOD severity FAIL: gap={gap:.5f} < 0.01"

    def test_same_episodes_no_severity(self):
        """Identical ID episodes used as OOD should NOT pass severity gate."""
        from fglc.data.manifest import build_dataset_stats, verify_ood_severity

        id_eps = _make_id_episodes()
        id_stats = build_dataset_stats(id_eps, "train_id")
        # Use same data → gap ≈ 0
        ok, gap = verify_ood_severity(id_stats, id_stats, delta_min=0.01)
        assert not ok, "Same data passed OOD severity gate (gap should be 0)"
        assert gap < 1e-9

    def test_build_dataset_stats_delta_norms_positive(self):
        """state_delta_norm stats should all be >= 0."""
        from fglc.data.manifest import build_dataset_stats

        eps = _make_id_episodes()
        stats = build_dataset_stats(eps, "train_id")
        assert stats["state_delta_norm_mean"] >= 0
        assert stats["state_delta_norm_p50"] >= 0
        assert stats["state_delta_norm_p95"] >= stats["state_delta_norm_p50"]


class TestWelfordStats:
    def test_mean_matches_numpy(self):
        from fglc.data.stats import WelfordStats

        rng = np.random.default_rng(7)
        data = rng.normal(size=(100, 8)).astype(np.float32)
        ws = WelfordStats(8)
        for row in data:
            ws.update(row)
        np.testing.assert_allclose(ws.mean, data.mean(axis=0), atol=1e-4)

    def test_std_matches_numpy(self):
        from fglc.data.stats import WelfordStats

        rng = np.random.default_rng(13)
        data = rng.normal(scale=2.0, size=(200, 4)).astype(np.float32)
        ws = WelfordStats(4)
        for row in data:
            ws.update(row)
        np.testing.assert_allclose(ws.std, data.std(axis=0, ddof=1), atol=1e-3)

    def test_single_sample_variance_zero(self):
        from fglc.data.stats import WelfordStats

        ws = WelfordStats(3)
        ws.update(np.array([1.0, 2.0, 3.0]))
        assert np.all(ws.variance == 0.0)
