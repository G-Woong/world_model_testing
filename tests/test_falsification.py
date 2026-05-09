from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from frcgw.models.latent_heads import LatentSample
from frcgw.models.world_model_heads import RolloutResult
from frcgw.planning.alternative_proposer import HypothesisId, enumerate_hypotheses, log_prior, propose
from frcgw.planning.falsification import FalsificationEvidence, falsification_score, log_likelihood


class _FakeWorldModelHeads:
    def __init__(self, rollouts: dict[int, RolloutResult]) -> None:
        self.rollouts = rollouts

    def forward_given_action(self, shared_h, z_state, action_type, hypothesis_id):
        return self.rollouts[int(hypothesis_id)]


class _FakeModel:
    def __init__(self, rollouts: dict[int, RolloutResult]) -> None:
        self.world_model_heads = _FakeWorldModelHeads(rollouts)


def _rollout(effect_score: float, progress: float = 0.0, failed_score: float = 0.1) -> RolloutResult:
    logits = torch.full((1, 7), -5.0)
    logits[0, 1] = effect_score
    return RolloutResult(
        effect_logits=logits,
        progress_pred=torch.tensor([progress]),
        failed_score=torch.tensor([failed_score]),
    )


def _latent_sample() -> LatentSample:
    return LatentSample(
        z_state=torch.zeros(1, 32),
        z_regime_logits=torch.tensor([[3.0, 2.0, 1.0, 0.0, -1.0, -2.0, -3.0, -4.0]]),
        z_grammar_logits=torch.tensor([[0.0, 1.0, 2.0, 3.0, -1.0, -2.0, -3.0, -4.0]]),
        z_change_logits=torch.zeros(1, 12),
        z_reveal_shift_logits=torch.zeros(1, 3),
        shared_h=torch.zeros(1, 128),
        posterior_entropy=torch.zeros(1),
        aux_precondition=torch.zeros(1),
        aux_failure_risk=torch.zeros(1),
    )


def test_falsification_positive_when_alt_better() -> None:
    model = _FakeModel({0: _rollout(-4.0), 1: _rollout(6.0)})
    evidence = FalsificationEvidence(observed_effect_type=1, observed_progress_delta=0.0, observed_failed_action=False)

    score = falsification_score(model, torch.zeros(1, 128), torch.zeros(1, 32), "click", 0, [1], evidence)

    assert score > 0


def test_falsification_negative_when_exec_correct() -> None:
    model = _FakeModel({0: _rollout(6.0), 1: _rollout(-4.0)})
    evidence = FalsificationEvidence(observed_effect_type=1, observed_progress_delta=0.0, observed_failed_action=False)

    score = falsification_score(model, torch.zeros(1, 128), torch.zeros(1, 32), "click", 0, [1], evidence)

    assert score <= 0


def test_no_op_valid_not_driven_up() -> None:
    model = _FakeModel({0: _rollout(-4.0), 1: _rollout(6.0)})
    evidence = FalsificationEvidence(observed_effect_type=6, observed_progress_delta=0.0, observed_failed_action=False)

    score = falsification_score(model, torch.zeros(1, 128), torch.zeros(1, 32), "click", 0, [1], evidence)

    assert score.item() == 0.0


def test_falsification_scalar() -> None:
    model = _FakeModel({0: _rollout(-4.0), 1: _rollout(6.0)})
    evidence = FalsificationEvidence(observed_effect_type=1, observed_progress_delta=0.0, observed_failed_action=False)

    score = falsification_score(model, torch.zeros(1, 128), torch.zeros(1, 32), "click", 0, [1], evidence)

    assert score.ndim == 0 or score.shape == () or score.numel() == 1


def test_propose_returns_k_hypotheses() -> None:
    proposed = propose(_latent_sample(), None, None, None, None, None, k=3, mode="posterior_only")

    assert len(proposed) == 3
    assert all(isinstance(h, HypothesisId) for h in proposed)
    assert all(0 <= h.regime_id <= 7 and 0 <= h.grammar_id <= 7 for h in proposed)


def test_modes_differ() -> None:
    latent_sample = _latent_sample()

    posterior_a = propose(latent_sample, None, None, None, None, None, k=3, mode="posterior_only")
    posterior_b = propose(latent_sample, None, None, None, None, None, k=3, mode="posterior_only")
    torch.manual_seed(1)
    random_a = propose(latent_sample, None, None, None, None, None, k=3, mode="random")
    torch.manual_seed(2)
    random_b = propose(latent_sample, None, None, None, None, None, k=3, mode="random")

    assert posterior_a == posterior_b
    assert random_a != random_b


def test_enumerate_hypotheses() -> None:
    hypotheses = enumerate_hypotheses(8, 8)
    combined_ids = [h.combined_id for h in hypotheses]

    assert len(hypotheses) == 64
    assert len(set(combined_ids)) == 64
    assert all(h.combined_id == h.regime_id * 8 + h.grammar_id for h in hypotheses)


def test_log_likelihood_finite() -> None:
    evidence = FalsificationEvidence(observed_effect_type=1, observed_progress_delta=0.0, observed_failed_action=False)

    ell = log_likelihood(_rollout(6.0), evidence)

    assert ell.ndim == 0
    assert torch.isfinite(ell)


def test_no_evidence_empty_alts() -> None:
    model = _FakeModel({0: _rollout(6.0)})
    evidence = FalsificationEvidence(observed_effect_type=1, observed_progress_delta=0.0, observed_failed_action=False)

    score = falsification_score(model, torch.zeros(1, 128), torch.zeros(1, 32), "click", 0, [], evidence)

    assert score.item() == 0.0
