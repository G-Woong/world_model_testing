"""frcgw.planning.rewrite -- Grammar-conditioned action rewrite (RW-02 + RW-06).

Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md RW-02, RW-06
"""
from __future__ import annotations

import hashlib

import torch
import torch.nn.functional as F

from frcgw.models.text_frcg_model import TextFRCGModel
from frcgw.planning.alternative_proposer import HypothesisId
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


def _hash_action_embedding(action_type: str, dim: int, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
    digest = hashlib.sha256(action_type.encode("utf-8")).digest()
    values = []
    while len(values) < dim:
        for byte in digest:
            values.append((byte / 127.5) - 1.0)
            if len(values) == dim:
                break
        digest = hashlib.sha256(digest).digest()
    emb = torch.tensor(values, device=device, dtype=dtype)
    return F.normalize(emb, dim=0)


def rewrite_action(
    instruction: str,
    h_star: HypothesisId,
    candidates: list[CandidateAction],
    model: TextFRCGModel,
) -> tuple[CandidateAction | None, float]:
    """Return (best_candidate, confidence) based on grammar-conditioned ranking.

    Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md RW-02
    """
    del instruction
    if not candidates:
        return None, 0.0

    grammar_emb = model.grammar_embed(h_star.combined_id).squeeze(0)
    grammar_emb = F.normalize(grammar_emb, dim=0)
    scores = torch.stack(
        [
            torch.dot(
                _hash_action_embedding(candidate.action_type, grammar_emb.numel(), grammar_emb.device, grammar_emb.dtype),
                grammar_emb,
            )
            for candidate in candidates
        ]
    )
    top_idx = int(torch.argmax(scores).item())
    confidence = 1.0 if len(candidates) == 1 else float(torch.softmax(scores, dim=0)[top_idx].item())
    return candidates[top_idx], confidence


def validate_rewrite(
    candidate: CandidateAction | None,
    public_obs: PublicObservation,
    confidence: float,
    tau_r: float = 0.5,
) -> tuple[bool, str]:
    """Validate rewrite output (RW-06 fallback check).

    Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md RW-06
    """
    if candidate is None:
        return False, "no_candidate"
    candidate_ids = {c.action_id for c in public_obs.candidate_actions_public}
    if candidate.action_id not in candidate_ids:
        return False, "not_in_candidates"
    if confidence < tau_r:
        return False, "low_confidence"
    return True, "ok"
