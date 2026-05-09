"""frcgw.planning.alternative_proposer -- Alternative hypothesis proposer (PROP-03).

Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md PROP-03
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor
import torch.nn.functional as F

from frcgw.models.latent_heads import LatentSample
from frcgw.models.text_frcg_model import TextFRCGModel
from frcgw.planning.falsification import FalsificationEvidence, log_likelihood


@dataclass(frozen=True)
class HypothesisId:
    regime_id: int
    grammar_id: int
    combined_id: int


def enumerate_hypotheses(n_regimes: int = 8, n_grammars: int = 8) -> list[HypothesisId]:
    """Return all n_regimes * n_grammars hypothesis candidates."""
    return [
        HypothesisId(regime_id=r, grammar_id=g, combined_id=r * n_grammars + g)
        for r in range(n_regimes)
        for g in range(n_grammars)
    ]


def log_prior(latent_sample: LatentSample, hypothesis: HypothesisId) -> Tensor:
    """log p(h) = log_softmax(z_regime)[regime_id] + log_softmax(z_grammar)[grammar_id]."""
    log_regime = F.log_softmax(latent_sample.z_regime_logits, dim=-1)[..., hypothesis.regime_id]
    log_grammar = F.log_softmax(latent_sample.z_grammar_logits, dim=-1)[..., hypothesis.grammar_id]
    prior = log_regime + log_grammar
    return prior.squeeze() if prior.numel() == 1 else prior


def propose(
    latent_sample: LatentSample,
    model: TextFRCGModel | None,
    shared_h: Tensor | None,
    z_state: Tensor | None,
    action_type: str | None,
    evidence: FalsificationEvidence | None,
    k: int = 3,
    mode: str = "hybrid",
    n_regimes: int = 8,
    n_grammars: int = 8,
    alpha_b: float = 1.0,
    alpha_l: float = 1.0,
    oracle_hypothesis_id: int | None = None,
) -> list[HypothesisId]:
    """Propose top-k alternative hypotheses.

    Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md PROP-03
    """
    hypotheses = enumerate_hypotheses(n_regimes, n_grammars)
    if k <= 0:
        return []

    if mode == "oracle":
        if oracle_hypothesis_id is None:
            raise ValueError("oracle mode requires oracle_hypothesis_id")
        matches = [h for h in hypotheses if h.combined_id == oracle_hypothesis_id]
        if not matches:
            raise ValueError("oracle_hypothesis_id is outside the hypothesis space")
        return matches * k

    if mode == "hybrid" and any(item is None for item in (model, shared_h, z_state, action_type, evidence)):
        mode = "posterior_only"

    scores: list[Tensor] = []
    for hypothesis in hypotheses:
        if mode == "hybrid":
            assert model is not None
            assert shared_h is not None
            assert z_state is not None
            assert action_type is not None
            assert evidence is not None
            rollout = model.world_model_heads.forward_given_action(shared_h, z_state, action_type, hypothesis.combined_id)
            score = alpha_b * log_prior(latent_sample, hypothesis) + alpha_l * log_likelihood(rollout, evidence)
        elif mode == "posterior_only":
            score = log_prior(latent_sample, hypothesis)
        elif mode == "random":
            score = torch.randn((), dtype=latent_sample.z_regime_logits.dtype, device=latent_sample.z_regime_logits.device)
        else:
            raise ValueError(f"unknown propose mode: {mode}")
        scores.append(score.squeeze() if score.numel() == 1 else score.max())

    top_indices = torch.stack(scores).topk(min(k, len(hypotheses))).indices.tolist()
    return [hypotheses[int(idx)] for idx in top_indices]
