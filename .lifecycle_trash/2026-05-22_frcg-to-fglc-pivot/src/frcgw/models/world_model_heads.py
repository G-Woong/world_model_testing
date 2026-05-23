"""frcgw.models.world_model_heads -- WorldModelHeads for P3 tiny FRCG text model.

Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md MOD-07-018, MOD-07-021
Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md L-MAIN-001, L-MAIN-002
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

import torch
from torch import Tensor, nn


@dataclass
class RolloutResult:
    effect_logits: Tensor
    progress_pred: Tensor
    failed_score: Tensor


def _hash_token(token: str, vocab_size: int) -> int:
    """Hash a token into the fixed vocabulary range using MD5."""
    return int(hashlib.md5(token.encode()).hexdigest(), 16) % vocab_size


class WorldModelHeads(nn.Module):
    """Action-conditioned world-model prediction heads."""

    def __init__(
        self,
        d_model: int = 128,
        z_state_dim: int = 32,
        action_embed_dim: int = 64,
        hypothesis_embed_dim: int = 32,
        n_effect_types: int = 7,
        n_hypotheses: int = 64,
        vocab_size: int = 4096,
    ) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.n_hypotheses = n_hypotheses
        self.action_embedding = nn.Embedding(vocab_size, action_embed_dim)
        self.hypothesis_embedding = nn.Embedding(n_hypotheses, hypothesis_embed_dim)
        input_dim = d_model + z_state_dim + action_embed_dim + hypothesis_embed_dim
        self.effect_head = nn.Linear(input_dim, n_effect_types)
        self.progress_head = nn.Sequential(nn.Linear(input_dim, 64), nn.ReLU(), nn.Linear(64, 1))
        self.failure_head = nn.Linear(input_dim, 1)

    def _action_ids(self, action_type: str | list[str], batch_size: int, device: torch.device) -> Tensor:
        actions = [action_type] if isinstance(action_type, str) else list(action_type)
        if len(actions) == 1 and batch_size != 1:
            actions = actions * batch_size
        if len(actions) != batch_size:
            raise ValueError("action_type batch length must match shared_h batch length")
        return torch.tensor([_hash_token(action, self.vocab_size) for action in actions], dtype=torch.long, device=device)

    def _hypothesis_ids(self, hypothesis_id: int | list[int], batch_size: int, device: torch.device) -> Tensor:
        ids = [hypothesis_id] if isinstance(hypothesis_id, int) else list(hypothesis_id)
        if len(ids) == 1 and batch_size != 1:
            ids = ids * batch_size
        if len(ids) != batch_size:
            raise ValueError("hypothesis_id batch length must match shared_h batch length")
        return torch.tensor(ids, dtype=torch.long, device=device).clamp(min=0, max=self.n_hypotheses - 1)

    def forward_given_action(
        self,
        shared_h: Tensor,
        z_state: Tensor,
        action_type: str | list[str],
        hypothesis_id: int | list[int],
    ) -> RolloutResult:
        batch_size = shared_h.shape[0]
        device = shared_h.device
        action_emb = self.action_embedding(self._action_ids(action_type, batch_size, device))
        hypothesis_emb = self.hypothesis_embedding(self._hypothesis_ids(hypothesis_id, batch_size, device))
        x = torch.cat([shared_h, z_state, action_emb, hypothesis_emb], dim=-1)
        effect_logits = self.effect_head(x)
        progress_pred = self.progress_head(x).squeeze(-1)
        failed_score = torch.sigmoid(self.failure_head(x)).squeeze(-1)
        return RolloutResult(effect_logits, progress_pred, failed_score)

    def rollout_step(
        self,
        shared_h: Tensor,
        z_state: Tensor,
        action_type: str | list[str],
        hypothesis_id: int | list[int],
        H: int = 1,
    ) -> RolloutResult:
        return self.forward_given_action(shared_h, z_state, action_type, hypothesis_id)
