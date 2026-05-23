"""ManiSkill state-only HDF5 dataset for FGLC Step 11+.

Source: docs/STEP11_PLAN.md §C C.1 Transition schema, TASK D3
Loads pre-collected HDF5 episodes from collect_maniskill.py output.

HDF5 layout (per split file):
  /episodes/<episode_id>/
      state:  float32 (T, D_x)
      action: float32 (T, D_a)
      reward: float32 (T,)
      done:   bool    (T,)

Eval-only metadata (NOT in model input) stored in attrs or separate group:
  /eval_only/<episode_id>/
      regime_id, ood_type, true_mass, true_friction, seed, ...
"""

from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import Dataset

from fglc.schemas.visibility import assert_no_forbidden_fields


class ManiSkillStateOnlyDataset(Dataset):
    """Load ManiSkill state-only episodes from a pre-collected HDF5 file.

    Each item returns a dict with keys: state, action, reward, done.
    All FORBIDDEN_AGENT_FIELDS are excluded from returned dicts.
    """

    def __init__(self, h5_path: str, max_episodes: int | None = None) -> None:
        """
        Args:
            h5_path: Path to HDF5 file (from collect_maniskill.py).
            max_episodes: If set, truncate dataset to first N episodes.
        """
        import h5py  # local import — optional dep in non-ManiSkill CI

        self._h5_path = h5_path
        self._episode_keys: list[str] = []
        self._cache: dict[str, dict[str, torch.Tensor]] = {}

        with h5py.File(h5_path, "r") as f:
            ep_group = f.get("episodes", f)
            keys = sorted(ep_group.keys(), key=lambda k: int(k) if k.isdigit() else k)
            if max_episodes is not None:
                keys = keys[:max_episodes]
            self._episode_keys = list(keys)

            for key in self._episode_keys:
                ep = ep_group[key]
                batch = {
                    "state": torch.from_numpy(ep["state"][:].astype(np.float32)),
                    "action": torch.from_numpy(ep["action"][:].astype(np.float32)),
                    "reward": torch.from_numpy(ep["reward"][:].astype(np.float32)),
                    "done": torch.from_numpy(ep["done"][:].astype(bool)),
                }
                assert_no_forbidden_fields(batch, context=f"ManiSkillStateOnlyDataset.load[{key}]")
                self._cache[key] = batch

    def __len__(self) -> int:
        return len(self._episode_keys)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        key = self._episode_keys[index]
        return self._cache[key]

    @property
    def h5_path(self) -> str:
        return self._h5_path
