"""Synthetic state-only toy dataset for FGLC.

Source: docs/ROADMAP/03_PHASE_R2_DATA_PIPELINE.md,
docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md Step 10 synthetic
"""

from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import Dataset

from fglc.schemas.visibility import assert_no_forbidden_fields


class SyntheticToyDataset(Dataset):
    """Deterministic synthetic trajectory dataset with state/action/reward/done."""

    def __init__(
        self,
        n_episodes: int,
        episode_len: int,
        D_x: int,
        D_a: int,
        mass: float = 1.0,
        friction: float = 1.0,
        sigma: float = 0.1,
        seed: int = 42,
    ) -> None:
        self.n_episodes = n_episodes
        self.episode_len = episode_len
        self.D_x = D_x
        self.D_a = D_a

        rng = np.random.default_rng(seed)
        A = rng.normal(0.0, 0.1, size=(D_x, D_x)).astype(np.float32)
        B = rng.normal(0.0, 0.1, size=(D_x, D_a)).astype(np.float32)
        A = A - np.eye(D_x, dtype=np.float32) * 0.5

        states = np.zeros((n_episodes, episode_len, D_x), dtype=np.float32)
        actions = rng.uniform(-1.0, 1.0, size=(n_episodes, episode_len, D_a)).astype(
            np.float32
        )
        rewards = np.zeros((n_episodes, episode_len), dtype=np.float32)
        done = np.zeros((n_episodes, episode_len), dtype=bool)

        x_t = rng.normal(0.0, 1.0, size=(n_episodes, D_x)).astype(np.float32)
        for t in range(episode_len):
            a_t = actions[:, t, :]
            states[:, t, :] = x_t
            rewards[:, t] = -0.1 * np.sum(x_t**2, axis=-1) - 0.01 * np.sum(
                a_t**2, axis=-1
            )
            noise = rng.normal(0.0, sigma, size=(n_episodes, D_x)).astype(np.float32)
            x_t = mass * (x_t @ A.T) + friction * (a_t @ B.T) + noise

        self._state = torch.from_numpy(states)
        self._action = torch.from_numpy(actions)
        self._reward = torch.from_numpy(rewards)
        self._done = torch.from_numpy(done)

    def __len__(self) -> int:
        return self.n_episodes

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        batch = {
            "state": self._state[index],
            "action": self._action[index],
            "reward": self._reward[index],
            "done": self._done[index],
        }
        assert_no_forbidden_fields(batch, context="SyntheticToyDataset.__getitem__")
        return batch
