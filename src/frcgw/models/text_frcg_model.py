"""frcgw.models.text_frcg_model -- TextFRCGModel top-level wrapper for P3.

Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md MOD-07-003, MOD-07-007, MOD-07-010-021
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import Tensor, nn

from frcgw.models.encoders import HistoryEncoder, TextStateEncoder
from frcgw.models.latent_heads import LatentPosterior
from frcgw.models.world_model_heads import WorldModelHeads, _hash_token
from frcgw.schemas.step_schema import PublicObservation


@dataclass
class ModelOutput:
    z_state: Tensor
    z_regime_logits: Tensor
    z_grammar_logits: Tensor
    z_change_logits: Tensor
    z_reveal_shift_logits: Tensor
    shared_h: Tensor
    posterior_entropy: Tensor
    aux_precondition: Tensor
    aux_failure_risk: Tensor


class TextFRCGModel(nn.Module):
    """Top-level public-observation model for the P3 text-only FRCG path."""

    def __init__(self, cfg: dict[str, Any] | None = None) -> None:
        super().__init__()
        self.cfg = self.get_default_cfg()
        if cfg is not None:
            self.cfg.update(cfg)

        self.text_encoder = TextStateEncoder(
            vocab_size=self.cfg["vocab_size"],
            embed_dim=self.cfg["embed_dim"],
            d_model=self.cfg["d_model"],
            nhead=self.cfg["nhead"],
            num_layers=self.cfg["num_layers"],
            dim_feedforward=self.cfg["dim_feedforward"],
            dropout=self.cfg["dropout"],
            max_seq_len=self.cfg["max_seq_len"],
        )
        self.history_encoder = HistoryEncoder(
            vocab_size=self.cfg["vocab_size"],
            embed_dim=self.cfg["embed_dim"],
            hidden_dim=self.cfg["hidden_dim"],
        )
        self.latent_posterior = LatentPosterior(
            input_dim=self.cfg["d_model"] + self.cfg["hidden_dim"],
            hidden_dim=self.cfg["hidden_dim"],
            z_state_dim=self.cfg["z_state_dim"],
            n_regimes=self.cfg["n_regimes"],
            n_grammars=self.cfg["n_grammars"],
            n_change_types=self.cfg["n_change_types"],
            n_reveal_shift=self.cfg["n_reveal_shift"],
        )
        self.world_model_heads = WorldModelHeads(
            d_model=self.cfg["hidden_dim"],
            z_state_dim=self.cfg["z_state_dim"],
            action_embed_dim=self.cfg["action_embed_dim"],
            hypothesis_embed_dim=self.cfg["hypothesis_embed_dim"],
            n_effect_types=self.cfg["n_effect_types"],
            n_hypotheses=self.cfg["n_regimes"] * self.cfg["n_grammars"],
            vocab_size=self.cfg["vocab_size"],
        )

    @staticmethod
    def get_default_cfg() -> dict[str, Any]:
        return {
            "vocab_size": 4096,
            "embed_dim": 64,
            "d_model": 128,
            "nhead": 4,
            "num_layers": 2,
            "dim_feedforward": 256,
            "dropout": 0.0,
            "max_seq_len": 128,
            "hidden_dim": 128,
            "z_state_dim": 32,
            "n_regimes": 8,
            "n_grammars": 8,
            "n_change_types": 12,
            "n_reveal_shift": 3,
            "n_effect_types": 7,
            "action_embed_dim": 64,
            "hypothesis_embed_dim": 32,
        }

    def forward(self, public_input: PublicObservation | list[PublicObservation]) -> ModelOutput:
        public_batch = [public_input] if isinstance(public_input, PublicObservation) else list(public_input)
        instructions = [pub.instruction for pub in public_batch]
        histories = [pub.history_public for pub in public_batch]
        dom_texts = [self._public_dom_text(pub) for pub in public_batch]

        text_h = self.text_encoder(instructions, dom_texts)
        hist_h = self.history_encoder(histories)
        sample = self.latent_posterior(text_h, hist_h)
        return ModelOutput(
            z_state=sample.z_state,
            z_regime_logits=sample.z_regime_logits,
            z_grammar_logits=sample.z_grammar_logits,
            z_change_logits=sample.z_change_logits,
            z_reveal_shift_logits=sample.z_reveal_shift_logits,
            shared_h=sample.shared_h,
            posterior_entropy=sample.posterior_entropy,
            aux_precondition=sample.aux_precondition,
            aux_failure_risk=sample.aux_failure_risk,
        )

    def action_embed(self, action_type: str) -> Tensor:
        device = self.world_model_heads.action_embedding.weight.device
        action_id = _hash_token(action_type, self.cfg["vocab_size"])
        ids = torch.tensor([action_id], dtype=torch.long, device=device)
        return self.world_model_heads.action_embedding(ids)

    def grammar_embed(self, grammar_id: int) -> Tensor:
        device = self.world_model_heads.hypothesis_embedding.weight.device
        grammar_id = max(0, min(int(grammar_id), self.world_model_heads.n_hypotheses - 1))
        ids = torch.tensor([grammar_id], dtype=torch.long, device=device)
        return self.world_model_heads.hypothesis_embedding(ids)

    @staticmethod
    def _public_dom_text(pub: PublicObservation) -> str:
        parts: list[str] = []
        if pub.dom_snapshot_public:
            parts.append(str(pub.dom_snapshot_public))
        if pub.accessibility_tree_public:
            parts.append(str(pub.accessibility_tree_public))
        return " ".join(parts)
