"""Tests for HistoryEncoder persistent h_t carry-over (TASK_LFD_002).

Source: .agent_tasks/codex_queue/TASK_LFD_002_history_encoder_persistent_ht.md
"""
from __future__ import annotations

import torch

from frcgw.models.encoders import HistoryEncoder
from frcgw.schemas.step_schema import PublicHistoryItem


def _make_history(n: int = 3) -> list[PublicHistoryItem]:
    return [
        PublicHistoryItem(step_index=i, action_summary=f"click action_{i}", effect_summary="state_change")
        for i in range(n)
    ]


def test_h_t_carry_over_changes_output() -> None:
    """Forward with non-zero h0 produces different output than zero-init."""
    enc = HistoryEncoder(vocab_size=64, embed_dim=16, hidden_dim=32)
    enc.eval()
    history = [_make_history(3)]

    with torch.no_grad():
        out_zero, h_next = enc(history, h0=None, return_hidden=True)
        # Use h_next as h0 for second call (same input)
        out_carry, _ = enc(history, h0=h_next, return_hidden=True)

    # Outputs should differ when h0 differs
    assert not torch.allclose(out_zero, out_carry), (
        "h_t carry-over should produce different output than zero-init"
    )


def test_h_t_episode_reset_to_none() -> None:
    """Resetting h_t to None reproduces zero-init output."""
    enc = HistoryEncoder(vocab_size=64, embed_dim=16, hidden_dim=32)
    enc.eval()
    history = [_make_history(2)]

    with torch.no_grad():
        out1, _ = enc(history, h0=None, return_hidden=True)
        out2, _ = enc(history, h0=None, return_hidden=True)

    assert torch.allclose(out1, out2), "Same input with h0=None should give same output"


def test_h_t_shape_correct() -> None:
    """h_t_next has shape [1, batch, hidden_dim]."""
    enc = HistoryEncoder(vocab_size=64, embed_dim=16, hidden_dim=32)
    batch_size = 4
    histories = [_make_history(2) for _ in range(batch_size)]

    with torch.no_grad():
        _, h_next = enc(histories, return_hidden=True)

    assert h_next.shape == (1, batch_size, 32), f"Expected (1, {batch_size}, 32), got {h_next.shape}"


def test_h_t_nonzero_after_nonempty_history() -> None:
    """h_t_next is not all zeros after processing a non-empty history."""
    enc = HistoryEncoder(vocab_size=64, embed_dim=16, hidden_dim=32)
    history = [_make_history(3)]

    with torch.no_grad():
        _, h_next = enc(history, return_hidden=True)

    assert h_next.abs().sum().item() > 0, "h_t_next should be non-zero for non-empty history"
