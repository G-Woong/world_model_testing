"""Reward and value heads for the base world model.

Source: docs/idea/04_BASE_WORLD_MODEL.md, docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md
"""

from __future__ import annotations

import torch
from torch import Tensor, nn


class RewardHead(nn.Module):
    """Predict rewards from latent state, action, and belief."""

    def __init__(
        self,
        K: int = 6,
        d: int = 32,
        D_a: int = 4,
        h_dim: int = 128,
        hidden: int = 64,
    ) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(K * d + D_a + h_dim, hidden),
            nn.SiLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, z_flat: Tensor, action: Tensor, h: Tensor) -> Tensor:
        head_input = torch.cat((z_flat, action, h), dim=-1)
        return self.net(head_input).squeeze(-1)


class ValueHead(nn.Module):
    """Predict values from latent state and belief."""

    def __init__(
        self,
        K: int = 6,
        d: int = 32,
        h_dim: int = 128,
        hidden: int = 64,
    ) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(K * d + h_dim, hidden),
            nn.SiLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, z_flat: Tensor, h: Tensor) -> Tensor:
        head_input = torch.cat((z_flat, h), dim=-1)
        return self.net(head_input).squeeze(-1)
