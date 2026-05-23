"""Grouped latent encoder for the base world model.

Source: docs/idea/04_BASE_WORLD_MODEL.md, docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md
"""

from __future__ import annotations

import torch
from torch import Tensor, nn


class Encoder(nn.Module):
    """Encode state sequences into grouped latent tensors."""

    def __init__(self, D_x: int, K: int = 6, d: int = 32, hidden: int = 256) -> None:
        super().__init__()
        self.K = K
        self.d = d
        self.net = nn.Sequential(
            nn.Linear(D_x, hidden),
            nn.LayerNorm(hidden),
            nn.SiLU(),
            nn.Linear(hidden, hidden),
            nn.LayerNorm(hidden),
            nn.SiLU(),
            nn.Linear(hidden, K * d),
        )

    def forward(self, state: Tensor) -> Tensor:
        B, T, _ = state.shape
        z_flat = self.net(state)
        return torch.reshape(z_flat, (B, T, self.K, self.d))
