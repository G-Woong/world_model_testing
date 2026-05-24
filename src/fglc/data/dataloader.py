"""DataLoader construction for FGLC synthetic and ManiSkill data.

Supports dataset.type: synthetic_toy | maniskill_state_only
"""

from __future__ import annotations

from collections.abc import Mapping

import torch
from torch.utils.data import DataLoader, Dataset

from fglc.data.state_only_dataset import SyntheticToyDataset
from fglc.schemas.visibility import assert_no_forbidden_fields


class _HorizonDataset(Dataset):
    def __init__(self, dataset: Dataset, horizon: int) -> None:
        self.dataset = dataset
        self.horizon = horizon

    def __len__(self) -> int:
        return len(self.dataset)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        episode = self.dataset[index]
        batch = {
            "state": episode["state"][: self.horizon],
            "action": episode["action"][: self.horizon],
            "reward": episode["reward"][: self.horizon],
            "done": episode["done"][: self.horizon],
        }
        assert_no_forbidden_fields(batch, context="_HorizonDataset.__getitem__")
        return batch


def make_dataloaders(config: dict) -> dict[str, DataLoader]:
    dataset_config: Mapping[str, object] = config["dataset"]
    trainer_config: Mapping[str, object] = config["trainer"]

    batch_size = int(trainer_config["batch_size"])
    train_horizon = int(trainer_config["train_horizon"])
    dataset_type = str(dataset_config.get("type", "synthetic_toy"))

    if dataset_type == "maniskill_state_only":
        datasets = _make_maniskill_datasets(dataset_config)
    else:
        datasets = _make_synthetic_datasets(dataset_config, config)

    return {
        name: DataLoader(
            _HorizonDataset(dataset, train_horizon),
            batch_size=batch_size,
            shuffle=(name == "train_id"),
            num_workers=0,
        )
        for name, dataset in datasets.items()
    }


def _make_synthetic_datasets(
    dataset_config: Mapping[str, object], config: dict
) -> dict[str, Dataset]:
    D_x = int(dataset_config["D_x"])
    D_a = int(dataset_config["D_a"])
    episode_len = int(dataset_config["episode_len"])
    sigma = float(dataset_config["sigma"])
    seed = int(config.get("seed", 42))

    return {
        "train_id": SyntheticToyDataset(
            n_episodes=int(dataset_config["n_episode_train"]),
            episode_len=episode_len,
            D_x=D_x,
            D_a=D_a,
            sigma=sigma,
            seed=seed,
        ),
        "val_id": SyntheticToyDataset(
            n_episodes=int(dataset_config["n_episode_val"]),
            episode_len=episode_len,
            D_x=D_x,
            D_a=D_a,
            sigma=sigma,
            seed=seed + 1,
        ),
        "ood_mass": SyntheticToyDataset(
            n_episodes=int(dataset_config["n_episode_ood_mass"]),
            episode_len=episode_len,
            D_x=D_x,
            D_a=D_a,
            mass=float(dataset_config["ood_mass_scale"]),
            sigma=sigma,
            seed=seed + 2,
        ),
        "ood_friction": SyntheticToyDataset(
            n_episodes=int(dataset_config["n_episode_ood_friction"]),
            episode_len=episode_len,
            D_x=D_x,
            D_a=D_a,
            friction=float(dataset_config["ood_friction_scale"]),
            sigma=sigma,
            seed=seed + 3,
        ),
    }


def _make_maniskill_datasets(
    dataset_config: Mapping[str, object],
) -> dict[str, Dataset]:
    """Build ManiSkill datasets from h5 paths.

    NOTE (2026-05-24): n_episode_train / n_episode_val / n_episode_ood_* fields
    in dataset_config are advisory and NOT used here. Runtime episode count is
    determined by the h5 file itself. SoT: data/fglc/<task>/manifest.json.
    """
    from fglc.data.maniskill_dataset import ManiSkillStateOnlyDataset

    split_h5_keys = {
        "train_id": "train_id_h5",
        "val_id": "val_id_h5",
        "test_id": "test_id_h5",
        "ood_mass": "ood_mass_h5",
        "ood_friction": "ood_friction_h5",
    }
    datasets: dict[str, Dataset] = {}
    for split, h5_key in split_h5_keys.items():
        h5_path = str(dataset_config[h5_key])
        datasets[split] = ManiSkillStateOnlyDataset(h5_path=h5_path)
    return datasets
