import torch

from fglc.data.dataloader import make_dataloaders
from fglc.data.state_only_dataset import SyntheticToyDataset
from fglc.schemas.visibility import assert_no_forbidden_fields


def _dataset_config() -> dict:
    return {
        "phase": "R3",
        "seed": 42,
        "device": "cuda",
        "dataset": {
            "type": "synthetic_toy",
            "D_x": 8,
            "D_a": 4,
            "episode_len": 64,
            "n_episode_train": 32,
            "n_episode_val": 8,
            "n_episode_ood_mass": 16,
            "n_episode_ood_friction": 16,
            "ood_mass_scale": 2.0,
            "ood_friction_scale": 0.5,
            "sigma": 0.1,
        },
        "model": {
            "K": 6,
            "d": 32,
            "h_dim": 128,
            "encoder_hidden": 256,
            "dynamics_hidden": 64,
        },
        "trainer": {
            "batch_size": 16,
            "train_horizon": 8,
            "epochs": 5,
            "learning_rate": 3.0e-4,
            "optimizer": "adam",
            "loss_weights": {
                "lambda_reward": 1.0,
                "lambda_value": 1.0,
                "lambda_calibration": 0.0,
            },
        },
        "metric": {
            "primary": "id_nll",
            "gate_threshold_id_nll": 0.5,
            "gate_threshold_ood_id_gap": 0.05,
        },
    }


def _make_dataset(n_episodes: int = 32) -> SyntheticToyDataset:
    return SyntheticToyDataset(
        n_episodes=n_episodes,
        episode_len=64,
        D_x=8,
        D_a=4,
        sigma=0.1,
        seed=42,
    )


def test_four_split_shapes():
    config = _dataset_config()
    dcfg = config["dataset"]
    split_specs = {
        "train_id": (dcfg["n_episode_train"], 1.0, 1.0),
        "val_id": (dcfg["n_episode_val"], 1.0, 1.0),
        "ood_mass": (dcfg["n_episode_ood_mass"], dcfg["ood_mass_scale"], 1.0),
        "ood_friction": (
            dcfg["n_episode_ood_friction"],
            1.0,
            dcfg["ood_friction_scale"],
        ),
    }

    for offset, (_, (n_episodes, mass, friction)) in enumerate(split_specs.items()):
        dataset = SyntheticToyDataset(
            n_episodes=n_episodes,
            episode_len=dcfg["episode_len"],
            D_x=dcfg["D_x"],
            D_a=dcfg["D_a"],
            mass=mass,
            friction=friction,
            sigma=dcfg["sigma"],
            seed=config["seed"] + offset,
        )
        assert len(dataset) == n_episodes
        assert dataset._state.shape == (n_episodes, 64, 8)
        assert dataset._action.shape == (n_episodes, 64, 4)
        assert dataset._reward.shape == (n_episodes, 64)
        assert dataset._done.shape == (n_episodes, 64)


def test_forbidden_field_absent():
    batch = _make_dataset()[0]
    assert set(batch) == {"state", "action", "reward", "done"}
    assert_no_forbidden_fields(batch)


def test_episode_len_consistent():
    batch = _make_dataset()[0]
    assert batch["state"].shape[0] == 64
    assert batch["action"].shape[0] == 64
    assert batch["reward"].shape[0] == 64
    assert batch["done"].shape[0] == 64


def test_dx_da_consistent():
    batch = _make_dataset()[0]
    assert batch["state"].shape[-1] == 8
    assert batch["action"].shape[-1] == 4


def test_reward_is_negative():
    reward = _make_dataset()[0]["reward"]
    assert torch.all(reward <= 0)


def test_dataloader_batch_shape():
    loaders = make_dataloaders(_dataset_config())
    batch = next(iter(loaders["train_id"]))

    assert batch["state"].shape == (16, 8, 8)
    assert batch["action"].shape == (16, 8, 4)
    assert batch["reward"].shape == (16, 8)
    assert batch["done"].shape == (16, 8)
    assert_no_forbidden_fields(batch)
