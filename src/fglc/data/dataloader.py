"""DataLoader construction for FGLC synthetic data."""

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

    D_x = int(dataset_config["D_x"])
    D_a = int(dataset_config["D_a"])
    episode_len = int(dataset_config["episode_len"])
    sigma = float(dataset_config["sigma"])
    seed = int(config.get("seed", 42))
    batch_size = int(trainer_config["batch_size"])
    train_horizon = int(trainer_config["train_horizon"])

    datasets = {
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

    return {
        name: DataLoader(
            _HorizonDataset(dataset, train_horizon),
            batch_size=batch_size,
            shuffle=(name == "train_id"),
            num_workers=0,
        )
        for name, dataset in datasets.items()
    }
