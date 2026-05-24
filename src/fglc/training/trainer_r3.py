"""Stage 1 trainer for the R3 base world model.

Source: docs/idea/10_LOSS_DESIGN.md Stage 1.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F
from torch import Tensor, nn
from torch.utils.data import DataLoader

from fglc.models import BeliefMemory, Encoder, GroupedDynamics, RewardHead, ValueHead


@dataclass
class TrainerConfig:
    batch_size: int = 16
    train_horizon: int = 8
    epochs: int = 1
    learning_rate: float = 3.0e-4
    optimizer: str = "adam"
    loss_weights: dict[str, float] = field(
        default_factory=lambda: {
            "lambda_reward": 1.0,
            "lambda_value": 1.0,
            "lambda_calibration": 0.0,
        }
    )
    device: str = "cpu"


def gaussian_nll(target: Tensor, mu: Tensor, log_sigma: Tensor) -> Tensor:
    var = torch.exp(2 * log_sigma)
    return (
        0.5
        * (
            math.log(2 * math.pi)
            + 2 * log_sigma
            + (target - mu).pow(2) / var
        )
    ).mean()


def compute_mc_return(reward: Tensor) -> Tensor:
    mc = torch.zeros_like(reward)
    cumsum = torch.zeros(reward.shape[0], device=reward.device)
    for t in range(reward.shape[1] - 1, -1, -1):
        cumsum = cumsum + reward[:, t]
        mc[:, t] = cumsum
    return mc


class TrainerR3:
    """Trainer for Stage 1 dynamics, reward, and value losses."""

    def __init__(
        self,
        model_config: dict[str, Any],
        trainer_config: TrainerConfig,
        device: str | None = None,
    ) -> None:
        self.model_config = model_config
        self.config = trainer_config
        requested_device = device or trainer_config.device
        if requested_device == "cuda" and not torch.cuda.is_available():
            requested_device = "cpu"
        self.device = torch.device(requested_device)
        if self.device.type == "cuda":
            torch.cuda.set_per_process_memory_fraction(0.85)
            torch.cuda.reset_peak_memory_stats(self.device)

        self.encoder: Encoder
        self.belief: BeliefMemory
        self.dynamics: GroupedDynamics
        self.reward_head: RewardHead
        self.value_head: ValueHead
        self.modules = nn.ModuleList()
        self.optimizer = self.build()
        self.history: dict[str, list[float]] = {
            "train_loss": [],
            "train_nll": [],
            "val_nll": [],
        }
        self.stagnant_epochs = 0
        self.epoch = 0
        self.wall_clock_minutes = 0.0

    def build(self) -> torch.optim.Optimizer:
        D_x = int(self.model_config.get("D_x", self.model_config.get("state_dim", 8)))
        D_a = int(self.model_config.get("D_a", self.model_config.get("action_dim", 4)))
        K = int(self.model_config.get("K", 6))
        d = int(self.model_config.get("d", 32))
        h_dim = int(self.model_config.get("h_dim", 128))
        encoder_hidden = int(self.model_config.get("encoder_hidden", 256))
        dynamics_hidden = int(self.model_config.get("dynamics_hidden", 64))

        self.encoder = Encoder(D_x=D_x, K=K, d=d, hidden=encoder_hidden)
        self.belief = BeliefMemory(K=K, d=d, D_a=D_a, h_dim=h_dim)
        self.dynamics = GroupedDynamics(
            K=K,
            d=d,
            D_a=D_a,
            h_dim=h_dim,
            hidden=dynamics_hidden,
        )
        self.reward_head = RewardHead(K=K, d=d, D_a=D_a, h_dim=h_dim)
        self.value_head = ValueHead(K=K, d=d, h_dim=h_dim)
        self.modules = nn.ModuleList(
            [
                self.encoder,
                self.belief,
                self.dynamics,
                self.reward_head,
                self.value_head,
            ]
        ).to(self.device)

        if self.config.optimizer.lower() != "adam":
            raise ValueError(f"unsupported optimizer: {self.config.optimizer!r}")
        return torch.optim.Adam(self.modules.parameters(), lr=self.config.learning_rate)

    def train(self, train_loader: DataLoader, val_loader: DataLoader) -> dict[str, Any]:
        start = time.perf_counter()
        initial_train_nll = self.evaluate_nll(train_loader)
        best_val = float("inf")
        stagnant = 0

        for epoch_idx in range(1, self.config.epochs + 1):
            train_stats = self._run_train_epoch(train_loader)
            val_nll = self.evaluate_nll(val_loader)
            self.history["train_loss"].append(train_stats["loss"])
            self.history["train_nll"].append(train_stats["nll"])
            self.history["val_nll"].append(val_nll)

            if val_nll < best_val:
                best_val = val_nll
                stagnant = 0
            else:
                stagnant += 1
            self.epoch = epoch_idx

        self.stagnant_epochs = stagnant
        self.wall_clock_minutes = (time.perf_counter() - start) / 60.0
        final_train_nll = self.evaluate_nll(train_loader)
        final_val_nll = self.evaluate_nll(val_loader)
        return {
            "train_nll": final_train_nll,
            "val_nll": final_val_nll,
            "id_nll": final_val_nll,
            "val_train_nll_gap": final_val_nll - final_train_nll,
            "stagnant_epochs": self.stagnant_epochs,
            "epoch": self.epoch,
            "wall_clock_minutes": self.wall_clock_minutes,
            "vram_peak_mib": self.vram_peak_mib,
            "initial_train_nll": initial_train_nll,
            "history": self.history,
        }

    @property
    def vram_peak_mib(self) -> float:
        if self.device.type != "cuda":
            return 0.0
        return float(torch.cuda.max_memory_allocated(self.device) / (1024**2))

    def _run_train_epoch(self, loader: DataLoader) -> dict[str, float]:
        self.modules.train()
        total_loss = 0.0
        total_nll = 0.0
        total_count = 0
        for batch in loader:
            self.optimizer.zero_grad(set_to_none=True)
            losses = self._compute_losses(batch)
            losses["loss"].backward()
            self.optimizer.step()
            batch_size = int(batch["state"].shape[0])
            total_loss += float(losses["loss"].detach().cpu()) * batch_size
            total_nll += float(losses["dyn"].detach().cpu()) * batch_size
            total_count += batch_size
        return {
            "loss": total_loss / max(total_count, 1),
            "nll": total_nll / max(total_count, 1),
        }

    def _compute_losses(self, batch: dict[str, Tensor]) -> dict[str, Tensor]:
        state = batch["state"].to(self.device)
        action = batch["action"].to(self.device)
        reward = batch["reward"].to(self.device)

        z = self.encoder(state)
        h = self.belief(z, action, reward)
        mu, log_sigma = self.dynamics(z, action, h)
        z_next_target = z[:, 1:].detach()
        L_dyn = gaussian_nll(z_next_target, mu[:, :-1], log_sigma[:, :-1])

        z_flat = z.flatten(-2, -1)
        r_hat = self.reward_head(z_flat, action, h)
        v_hat = self.value_head(z_flat, h)
        mc_return = compute_mc_return(reward)
        L_reward = F.mse_loss(r_hat, reward)
        L_value = F.mse_loss(v_hat, mc_return)

        lambda_reward = float(self.config.loss_weights.get("lambda_reward", 1.0))
        lambda_value = float(self.config.loss_weights.get("lambda_value", 1.0))
        L_total = L_dyn + lambda_reward * L_reward + lambda_value * L_value
        return {
            "loss": L_total,
            "dyn": L_dyn,
            "reward": L_reward,
            "value": L_value,
        }

    @torch.no_grad()
    def evaluate_nll(self, loader: DataLoader) -> float:
        self.modules.eval()
        total_nll = 0.0
        total_count = 0
        for batch in loader:
            losses = self._compute_losses(batch)
            batch_size = int(batch["state"].shape[0])
            total_nll += float(losses["dyn"].detach().cpu()) * batch_size
            total_count += batch_size
        return total_nll / max(total_count, 1)

    def _config_hash(self) -> str:
        payload = json.dumps(self.model_config, sort_keys=True).encode("utf-8")
        return f"sha256:{hashlib.sha256(payload).hexdigest()[:16]}"

    def save_state(self, path: Path | str) -> None:
        """Save encoder/belief/dynamics/heads state_dict for R4 frozen reuse.

        Source: docs/idea/12_TRAINING_STAGES.md Stage 2 (R4 freeze policy).
        """
        torch.save(
            {
                "encoder": self.encoder.state_dict(),
                "belief": self.belief.state_dict(),
                "dynamics": self.dynamics.state_dict(),
                "reward_head": self.reward_head.state_dict(),
                "value_head": self.value_head.state_dict(),
                "config_hash": self._config_hash(),
            },
            path,
        )

    def load_state(self, path: Path | str, freeze: bool = True) -> None:
        """Load R3 checkpoint and optionally freeze all parameters for R4 eval.

        Source: docs/idea/12_TRAINING_STAGES.md Stage 2 (R4 freeze policy).
        """
        ckpt = torch.load(path, map_location=self.device)
        self.encoder.load_state_dict(ckpt["encoder"])
        self.belief.load_state_dict(ckpt["belief"])
        self.dynamics.load_state_dict(ckpt["dynamics"])
        self.reward_head.load_state_dict(ckpt["reward_head"])
        self.value_head.load_state_dict(ckpt["value_head"])
        if freeze:
            for mod in [self.encoder, self.belief, self.dynamics, self.reward_head, self.value_head]:
                for p in mod.parameters():
                    p.requires_grad_(False)
            self.modules.eval()

    @torch.no_grad()
    def evaluate_kstep_nll_slope(self, loader: DataLoader) -> float:
        self.modules.eval()
        values: list[tuple[float, float]] = []
        for k in (1, 2, 4, 8):
            nll = self._evaluate_kstep_nll(loader, k)
            if nll is not None:
                values.append((float(k), nll))
        if len(values) < 2:
            return 0.0
        x_mean = sum(k for k, _ in values) / len(values)
        y_mean = sum(nll for _, nll in values) / len(values)
        denom = sum((k - x_mean) ** 2 for k, _ in values)
        if denom == 0.0:
            return 0.0
        return sum((k - x_mean) * (nll - y_mean) for k, nll in values) / denom

    def _evaluate_kstep_nll(self, loader: DataLoader, k: int) -> float | None:
        total_nll = 0.0
        total_count = 0
        for batch in loader:
            state = batch["state"].to(self.device)
            action = batch["action"].to(self.device)
            reward = batch["reward"].to(self.device)
            z = self.encoder(state)
            if z.shape[1] <= k:
                continue
            h = self.belief(z, action, reward)
            mu, log_sigma = self.dynamics(z, action, h)
            nll = gaussian_nll(z[:, k:].detach(), mu[:, :-k], log_sigma[:, :-k])
            batch_size = int(state.shape[0])
            total_nll += float(nll.detach().cpu()) * batch_size
            total_count += batch_size
        if total_count == 0:
            return None
        return total_nll / total_count
