"""Tests for HistoryEncoder backward compatibility (TASK_LFD_002).

Source: .agent_tasks/codex_queue/TASK_LFD_002_history_encoder_persistent_ht.md
"""
from __future__ import annotations

import torch

from frcgw.models.encoders import HistoryEncoder
from frcgw.schemas.step_schema import PublicHistoryItem


def _make_history(n: int = 2) -> list[PublicHistoryItem]:
    return [
        PublicHistoryItem(step_index=i, action_summary=f"click {i}", effect_summary="state_change")
        for i in range(n)
    ]


def test_forward_default_return_tensor_not_tuple() -> None:
    """Default call (return_hidden=False) returns a Tensor, not a tuple."""
    enc = HistoryEncoder(vocab_size=64, embed_dim=16, hidden_dim=32)
    history = [_make_history(2)]
    with torch.no_grad():
        result = enc(history)
    assert isinstance(result, torch.Tensor), f"Expected Tensor, got {type(result)}"
    assert result.shape == (1, 32)


def test_forward_return_hidden_true_is_tuple() -> None:
    """return_hidden=True returns (Tensor, Tensor) tuple."""
    enc = HistoryEncoder(vocab_size=64, embed_dim=16, hidden_dim=32)
    history = [_make_history(2)]
    with torch.no_grad():
        result = enc(history, return_hidden=True)
    assert isinstance(result, tuple) and len(result) == 2
    out, h_next = result
    assert isinstance(out, torch.Tensor)
    assert isinstance(h_next, torch.Tensor)


def test_forward_h0_none_same_as_default() -> None:
    """Explicit h0=None produces identical output to default call."""
    enc = HistoryEncoder(vocab_size=64, embed_dim=16, hidden_dim=32)
    enc.eval()
    history = [_make_history(3)]
    with torch.no_grad():
        out_default = enc(history)
        out_explicit = enc(history, h0=None)
    assert torch.allclose(out_default, out_explicit), "h0=None should match default (no h0)"


def test_model_output_h_t_next_none_by_default() -> None:
    """TextFRCGModel.forward without h_t returns h_t_next=None."""
    from frcgw.models.text_frcg_model import TextFRCGModel
    from frcgw.schemas.step_schema import PublicObservation

    model = TextFRCGModel()
    obs = PublicObservation(instruction="test", history_public=[], candidate_actions_public=[])
    with torch.no_grad():
        out = model.forward(obs)
    assert out.h_t_next is None, "h_t_next should be None when h_t not passed"


def test_model_output_h_t_next_not_none_with_h_t() -> None:
    """TextFRCGModel.forward with h_t returns h_t_next Tensor."""
    from frcgw.models.text_frcg_model import TextFRCGModel
    from frcgw.schemas.step_schema import PublicObservation

    model = TextFRCGModel()
    obs = PublicObservation(instruction="test", history_public=[], candidate_actions_public=[])
    h_t = torch.zeros(1, 1, model.cfg["hidden_dim"])
    with torch.no_grad():
        out = model.forward(obs, h_t=h_t)
    assert out.h_t_next is not None, "h_t_next should be set when h_t is passed"
    assert out.h_t_next.shape == (1, 1, model.cfg["hidden_dim"])
