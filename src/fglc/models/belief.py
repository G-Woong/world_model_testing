"""GRU belief memory for the base world model.

Source: docs/idea/04_BASE_WORLD_MODEL.md, docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md
"""

from __future__ import annotations

import torch
from torch import Tensor, nn


class BeliefMemory(nn.Module):
    """Track recurrent belief state from latent groups and previous feedback."""

    def __init__(
        self,
        K: int = 6,
        d: int = 32,
        D_a: int = 4,
        h_dim: int = 128,
    ) -> None:
        super().__init__()
        self.K = K
        self.d = d
        self.D_a = D_a
        self.gru = nn.GRU(
            input_size=K * d + D_a + 1,
            hidden_size=h_dim,
            num_layers=1,
            batch_first=True,
        )

    def forward(self, z: Tensor, action: Tensor, reward: Tensor) -> Tensor:
        B, T, _, _ = z.shape
        z_flat = torch.reshape(z, (B, T, self.K * self.d))

        prev_action = torch.zeros_like(action)
        prev_action[:, 1:] = action[:, :-1]

        prev_reward = torch.zeros_like(reward)
        prev_reward[:, 1:] = reward[:, :-1]
        prev_reward = prev_reward.unsqueeze(-1)

        gru_input = torch.cat((z_flat, prev_action, prev_reward), dim=-1)
        h, _ = self.gru(gru_input)
        return h
