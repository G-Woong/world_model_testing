"""FalsificationDetectorHead — Learned sequential falsification detector.

Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md FALS-03
Architecture: BOCPD run-length posterior + effect residual + persistent h_t
Reference: Adams & MacKay (2007). Bayesian Online Changepoint Detection. arXiv:0710.3742.

Design note (CRITICAL-2 bypass, preflight checkpoint-0):
falsification.py:66-67 has a {0,6} short-circuit on the DETERMINISTIC scorer.
This head bypasses it by taking h_t + z_state + effect_residual + F_t_deterministic
as inputs. F_t_deterministic may be zero for effect_type {0,6}, but the head
can LEARN that zero F_t on a long wrong-hypothesis run is informative.
The deterministic falsification_score() is preserved unchanged as a feature source.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F
from torch import Tensor, nn


@dataclass
class LFDOutput:
    """Output of FalsificationDetectorHead for one forward pass."""
    wrong_prob_learned: Tensor      # [batch] — P(wrong hypothesis | history)
    run_length_posterior: Tensor    # [batch, max_run_length] — BOCPD posterior
    cusum_stat_t: Tensor            # [batch] — soft accumulated score


class FalsificationDetectorHead(nn.Module):
    """Learned falsification detector with BOCPD run-length posterior.

    Input: [h_t | z_state | effect_residual | F_t_deterministic]
    Output: LFDOutput (wrong_prob_learned, run_length_posterior, cusum_stat_t)

    Persistent h_t enables episode-level evidence accumulation.
    """

    def __init__(
        self,
        h_dim: int = 128,
        z_state_dim: int = 32,
        max_run_length: int = 20,
        effect_input_dim: int = 16,
    ) -> None:
        super().__init__()
        self.h_dim = h_dim
        self.max_run_length = max_run_length

        # Input: h_t (h_dim) + z_state (z_state_dim) + effect_residual (effect_input_dim) + F_t (1)
        input_dim = h_dim + z_state_dim + effect_input_dim + 1
        self.input_proj = nn.Linear(input_dim, h_dim)
        self.gru_cell = nn.GRUCell(h_dim, h_dim)
        self.wrong_prob_head = nn.Linear(h_dim, 1)
        self.run_length_head = nn.Linear(h_dim, max_run_length)
        self.cusum_head = nn.Linear(h_dim, 1)

        # Effect residual encoder: maps raw effect signal to effect_input_dim
        self.effect_encoder = nn.Sequential(
            nn.Linear(1, effect_input_dim),
            nn.ReLU(),
        )

    def forward(
        self,
        h_t: Tensor,                     # [batch, h_dim] from HistoryEncoder
        z_state: Tensor,                 # [batch, z_state_dim] from LatentPosterior
        effect_scalar: Tensor,           # [batch, 1] normalized effect residual
        F_t_deterministic: Tensor,       # [batch] from falsification_score() — may be 0
        head_h0: Tensor | None = None,   # [batch, h_dim] head's own recurrent state
    ) -> tuple[LFDOutput, Tensor]:
        """Forward pass. Returns (LFDOutput, head_h_next)."""
        batch_size = h_t.shape[0]
        device = h_t.device

        # Encode effect scalar
        effect_emb = self.effect_encoder(effect_scalar)  # [batch, effect_input_dim]

        # Concatenate inputs
        F_t = F_t_deterministic.reshape(batch_size, 1)  # [batch, 1]
        x = torch.cat([h_t, z_state, effect_emb, F_t], dim=-1)  # [batch, input_dim]
        x = self.input_proj(x)  # [batch, h_dim]

        # GRU step with optional carry-over
        if head_h0 is None:
            head_h0 = torch.zeros(batch_size, self.h_dim, device=device, dtype=x.dtype)
        head_h_next = self.gru_cell(x, head_h0)  # [batch, h_dim]

        # Head outputs
        wrong_logit = self.wrong_prob_head(head_h_next).squeeze(-1)       # [batch]
        wrong_prob = torch.sigmoid(wrong_logit)
        run_length_logits = self.run_length_head(head_h_next)             # [batch, max_run_length]
        run_length_posterior = self._bocpd_run_length_update(run_length_logits, wrong_logit)
        cusum_stat = self.cusum_head(head_h_next).squeeze(-1)             # [batch]

        return LFDOutput(
            wrong_prob_learned=wrong_prob,
            run_length_posterior=run_length_posterior,
            cusum_stat_t=cusum_stat,
        ), head_h_next

    def _bocpd_run_length_update(
        self,
        prior_logits: Tensor,          # [batch, max_run_length]
        new_evidence_score: Tensor,    # [batch]
    ) -> Tensor:
        """Approximate BOCPD run-length posterior update.

        Soft version: prior logits shifted toward short run when evidence is high.
        Returns normalized posterior [batch, max_run_length].
        """
        # Hazard-based shift: high evidence → shifts mass toward run-length=1
        hazard = torch.sigmoid(new_evidence_score).unsqueeze(1)  # [batch, 1]
        positions = torch.arange(self.max_run_length, device=prior_logits.device).float()
        # Down-weight long runs when evidence is high (hazard-weighted penalty)
        shift_penalty = hazard * positions.unsqueeze(0) * 0.1   # [batch, max_run_length]
        adjusted_logits = prior_logits - shift_penalty
        return F.softmax(adjusted_logits, dim=-1)
