"""Per-group MLP dynamics for the base world model.

Source: docs/idea/04_BASE_WORLD_MODEL.md, docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md
"""

from __future__ import annotations

import torch
from torch import Tensor, nn


class GroupedDynamics(nn.Module):
    """Predict per-latent-group dynamics parameters."""

    def __init__(
        self,
        K: int = 6,
        d: int = 32,
        D_a: int = 4,
        h_dim: int = 128,
        hidden: int = 64,
    ) -> None:
        super().__init__()
        self.K = K
        self.d = d
        input_dim = d + h_dim + D_a
        self.group_mlps = nn.ModuleList(
            [
                nn.Sequential(
                    nn.Linear(input_dim, hidden),
                    nn.SiLU(),
                    nn.Linear(hidden, 2 * d),
                )
                for _ in range(K)
            ]
        )

    def forward(self, z: Tensor, action: Tensor, h: Tensor) -> tuple[Tensor, Tensor]:
        outputs = []
        for group_idx, mlp in enumerate(self.group_mlps):
            group_input = torch.cat((z[:, :, group_idx], action, h), dim=-1)
            outputs.append(mlp(group_input))

        out = torch.stack(outputs, dim=2)
        mu = out[..., : self.d]
        log_sigma = out[..., self.d :]
        return mu, log_sigma
