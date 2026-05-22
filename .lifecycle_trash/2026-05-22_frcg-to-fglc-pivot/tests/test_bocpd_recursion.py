"""Tests for BOCPD run-length posterior behavior (TASK_LFD_003).

Source: .agent_tasks/codex_queue/TASK_LFD_003_bocpd_run_length_head.md
Reference: Adams & MacKay (2007). Bayesian Online Changepoint Detection.
"""
from __future__ import annotations

import torch

from frcgw.models.falsification_head import FalsificationDetectorHead


def test_bocpd_update_preserves_normalization() -> None:
    """run_length_posterior sums to 1 after _bocpd_run_length_update."""
    head = FalsificationDetectorHead(h_dim=16, z_state_dim=8, max_run_length=8, effect_input_dim=4)
    prior_logits = torch.randn(3, 8)
    evidence_score = torch.tensor([0.5, 1.5, -0.3])
    posterior = head._bocpd_run_length_update(prior_logits, evidence_score)
    sums = posterior.sum(dim=-1)
    assert torch.allclose(sums, torch.ones_like(sums), atol=1e-5), f"Posterior sums: {sums}"


def test_run_length_posterior_shifts_on_high_evidence() -> None:
    """High evidence score shifts posterior toward shorter run lengths."""
    head = FalsificationDetectorHead(h_dim=16, z_state_dim=8, max_run_length=8, effect_input_dim=4)
    prior_logits = torch.zeros(1, 8)  # uniform prior

    low_evidence = torch.tensor([0.0])
    high_evidence = torch.tensor([5.0])

    post_low = head._bocpd_run_length_update(prior_logits, low_evidence)
    post_high = head._bocpd_run_length_update(prior_logits, high_evidence)

    # With high evidence: penalty increases for long runs → more mass at short runs
    # post_high[0, 0] should be >= post_low[0, 0] (more mass at run length 0)
    assert post_high[0, 0].item() >= post_low[0, 0].item() - 0.01, (
        "High evidence should not decrease mass at shortest run length"
    )
    # Mass at longest run should decrease with high evidence
    assert post_high[0, -1].item() <= post_low[0, -1].item() + 0.01, (
        "High evidence should not increase mass at longest run length"
    )


def test_bocpd_posterior_range() -> None:
    """All posterior values are in [0, 1]."""
    head = FalsificationDetectorHead(h_dim=16, z_state_dim=8, max_run_length=10, effect_input_dim=4)
    prior_logits = torch.randn(5, 10)
    evidence_score = torch.randn(5)
    posterior = head._bocpd_run_length_update(prior_logits, evidence_score)
    assert (posterior >= 0).all() and (posterior <= 1).all()
