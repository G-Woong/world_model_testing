"""frcgw.models.latent_heads -- LatentPosterior and AuxHeads for P3 tiny text model.

Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md MOD-07-010, MOD-07-011-014, MOD-07-015-017
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor, nn


@dataclass
class LatentSample:
    """Posterior latent outputs for P3 tiny FRCG models.

    Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
    """

    z_state: Tensor
    z_regime_logits: Tensor
    z_grammar_logits: Tensor
    z_change_logits: Tensor
    z_reveal_shift_logits: Tensor
    shared_h: Tensor
    posterior_entropy: Tensor
    aux_precondition: Tensor
    aux_failure_risk: Tensor


class AuxHeads(nn.Module):
    """Auxiliary precondition and failure-risk heads for shared latent features.

    Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
    """

    def __init__(self, input_dim: int = 128) -> None:
        super().__init__()
        self.precondition_head = nn.Linear(input_dim, 1)
        self.failure_risk_head = nn.Linear(input_dim, 1)

    def forward(self, shared_h: Tensor) -> tuple[Tensor, Tensor]:
        precondition = torch.sigmoid(self.precondition_head(shared_h)).squeeze(-1)
        failure_risk = torch.sigmoid(self.failure_risk_head(shared_h)).squeeze(-1)
        return precondition, failure_risk


class LatentPosterior(nn.Module):
    """Posterior latent heads over public text and history representations.

    Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
    """

    def __init__(
        self,
        input_dim: int = 256,
        hidden_dim: int = 128,
        z_state_dim: int = 32,
        n_regimes: int = 8,
        n_grammars: int = 8,
        n_change_types: int = 12,
        n_reveal_shift: int = 3,
    ) -> None:
        super().__init__()
        self.shared_mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.z_state_head = nn.Linear(hidden_dim, z_state_dim)
        self.z_regime_head = nn.Linear(hidden_dim, n_regimes)
        self.z_grammar_head = nn.Linear(hidden_dim, n_grammars)
        self.z_change_head = nn.Linear(hidden_dim, n_change_types)
        self.z_reveal_shift_head = nn.Linear(hidden_dim, n_reveal_shift)
        self.aux_heads = AuxHeads(hidden_dim)

    def forward(self, text_h: Tensor, hist_h: Tensor) -> LatentSample:
        shared_h = self.shared_mlp(torch.cat([text_h, hist_h], dim=-1))
        z_regime_logits = self.z_regime_head(shared_h)
        z_grammar_logits = self.z_grammar_head(shared_h)
        regime_probs = torch.softmax(z_regime_logits, dim=-1)
        grammar_probs = torch.softmax(z_grammar_logits, dim=-1)
        posterior_entropy = (
            -(regime_probs * torch.log(regime_probs.clamp_min(1e-8))).sum(dim=-1)
            -(grammar_probs * torch.log(grammar_probs.clamp_min(1e-8))).sum(dim=-1)
        )
        aux_precondition, aux_failure_risk = self.aux_heads(shared_h)
        return LatentSample(
            z_state=self.z_state_head(shared_h),
            z_regime_logits=z_regime_logits,
            z_grammar_logits=z_grammar_logits,
            z_change_logits=self.z_change_head(shared_h),
            z_reveal_shift_logits=self.z_reveal_shift_head(shared_h),
            shared_h=shared_h,
            posterior_entropy=posterior_entropy,
            aux_precondition=aux_precondition,
            aux_failure_risk=aux_failure_risk,
        )
