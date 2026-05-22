"""Tests for FalsificationDetectorHead (TASK_LFD_003).

Source: .agent_tasks/codex_queue/TASK_LFD_003_bocpd_run_length_head.md
"""
from __future__ import annotations

import torch

from frcgw.models.falsification_head import FalsificationDetectorHead, LFDOutput


def _make_head(batch: int = 2) -> tuple[FalsificationDetectorHead, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    head = FalsificationDetectorHead(h_dim=32, z_state_dim=16, max_run_length=10, effect_input_dim=8)
    h_t = torch.randn(batch, 32)
    z_state = torch.randn(batch, 16)
    effect_scalar = torch.randn(batch, 1)
    F_t = torch.randn(batch)
    return head, h_t, z_state, effect_scalar, F_t


def test_wrong_prob_range() -> None:
    """wrong_prob_learned is in [0, 1]."""
    head, h_t, z_state, eff, F_t = _make_head()
    with torch.no_grad():
        out, _ = head(h_t, z_state, eff, F_t)
    assert out.wrong_prob_learned.shape == (2,)
    assert (out.wrong_prob_learned >= 0).all() and (out.wrong_prob_learned <= 1).all()


def test_run_length_posterior_sums_to_one() -> None:
    """run_length_posterior rows sum to 1 (softmax)."""
    head, h_t, z_state, eff, F_t = _make_head()
    with torch.no_grad():
        out, _ = head(h_t, z_state, eff, F_t)
    sums = out.run_length_posterior.sum(dim=-1)
    assert torch.allclose(sums, torch.ones_like(sums), atol=1e-5), f"Posterior rows should sum to 1, got {sums}"


def test_run_length_posterior_nonuniform() -> None:
    """Posterior should not be uniform after processing evidence."""
    head, h_t, z_state, eff, F_t = _make_head(batch=1)
    # Use high F_t to trigger hazard shift
    F_t_high = torch.tensor([5.0])
    with torch.no_grad():
        out, _ = head(h_t, z_state, eff, F_t_high)
    posterior = out.run_length_posterior[0]
    uniform = torch.ones(10) / 10
    # Should not be identical to uniform
    assert not torch.allclose(posterior, uniform, atol=1e-3), "Posterior should be non-uniform with high F_t"


def test_cusum_stat_t_is_scalar_per_batch() -> None:
    """cusum_stat_t has shape [batch]."""
    head, h_t, z_state, eff, F_t = _make_head(batch=4)
    with torch.no_grad():
        out, _ = head(h_t, z_state, eff, F_t)
    assert out.cusum_stat_t.shape == (4,)


def test_gradient_flows_to_wrong_prob_head() -> None:
    """Gradient flows through wrong_prob_learned."""
    head, h_t, z_state, eff, F_t = _make_head()
    out, _ = head(h_t, z_state, eff, F_t)
    loss = out.wrong_prob_learned.sum()
    loss.backward()
    assert head.wrong_prob_head.weight.grad is not None
    assert head.wrong_prob_head.weight.grad.abs().sum().item() > 0


def test_gradient_flows_to_run_length_head() -> None:
    """Gradient flows through run_length_posterior."""
    head, h_t, z_state, eff, F_t = _make_head()
    out, _ = head(h_t, z_state, eff, F_t)
    loss = out.run_length_posterior.sum()
    loss.backward()
    assert head.run_length_head.weight.grad is not None


def test_head_h_next_shape_correct() -> None:
    """head_h_next has shape [batch, h_dim]."""
    head, h_t, z_state, eff, F_t = _make_head(batch=3)
    with torch.no_grad():
        _, h_next = head(h_t, z_state, eff, F_t)
    assert h_next.shape == (3, 32)


def test_wrong_prob_changes_across_steps_with_mismatch() -> None:
    """wrong_prob is non-constant over 5 sequential steps with mismatch evidence."""
    head = FalsificationDetectorHead(h_dim=32, z_state_dim=16, max_run_length=10, effect_input_dim=8)
    h_t = torch.randn(1, 32)
    z_state = torch.randn(1, 16)
    head_h = None
    probs = []
    for _ in range(5):
        eff = torch.tensor([[1.0]])  # persistent mismatch signal
        F_t = torch.tensor([1.0])
        with torch.no_grad():
            out, head_h = head(h_t, z_state, eff, F_t, head_h0=head_h)
        probs.append(out.wrong_prob_learned.item())

    assert len(set(probs)) > 1, "wrong_prob should vary across steps with mismatch evidence"


def test_model_with_lfd_head_returns_lfd_output() -> None:
    """TextFRCGModel with use_lfd_head=True returns lfd_output when return_lfd=True."""
    from frcgw.models.text_frcg_model import TextFRCGModel
    from frcgw.schemas.step_schema import PublicObservation

    model = TextFRCGModel(use_lfd_head=True)
    obs = PublicObservation(instruction="test", history_public=[], candidate_actions_public=[])
    with torch.no_grad():
        out = model.forward(obs, return_lfd=True)
    assert out.lfd_output is not None
    assert isinstance(out.lfd_output, LFDOutput)


def test_model_without_lfd_head_returns_none() -> None:
    """TextFRCGModel without LFD head returns lfd_output=None even with return_lfd=True."""
    from frcgw.models.text_frcg_model import TextFRCGModel
    from frcgw.schemas.step_schema import PublicObservation

    model = TextFRCGModel(use_lfd_head=False)
    obs = PublicObservation(instruction="test", history_public=[], candidate_actions_public=[])
    with torch.no_grad():
        out = model.forward(obs, return_lfd=True)
    assert out.lfd_output is None
