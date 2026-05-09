from __future__ import annotations

import inspect

import pytest

torch = pytest.importorskip("torch")

from frcgw.models.encoders import HistoryEncoder, TextStateEncoder
from frcgw.models.latent_heads import AuxHeads, LatentPosterior, LatentSample
from frcgw.schemas.step_schema import PublicHistoryItem


def test_text_state_encoder_shape() -> None:
    encoder = TextStateEncoder()
    out = encoder(["click the button", "search for products"])
    assert out.shape == (2, 128)


def test_text_state_encoder_single_string() -> None:
    encoder = TextStateEncoder()
    out = encoder("hello world")
    assert out.shape in {(1, 128), (128,)}


def test_history_encoder_empty_history() -> None:
    encoder = HistoryEncoder()
    out = encoder([[]])
    assert out.shape == (1, 128)
    assert (out == 0).all()


def test_history_encoder_nonempty() -> None:
    encoder = HistoryEncoder()
    hist = [[PublicHistoryItem(0, "click submit", "no_change")]]
    out = encoder(hist)
    assert out.shape == (1, 128)


def test_latent_posterior_output_keys() -> None:
    lp = LatentPosterior()
    text_h = torch.randn(2, 128)
    hist_h = torch.randn(2, 128)
    sample = lp(text_h, hist_h)
    assert isinstance(sample, LatentSample)
    assert sample.z_state.shape == (2, 32)
    assert sample.z_regime_logits.shape == (2, 8)
    assert sample.z_grammar_logits.shape == (2, 8)
    assert sample.z_change_logits.shape == (2, 12)
    assert sample.z_reveal_shift_logits.shape == (2, 3)
    assert sample.shared_h.shape == (2, 128)
    assert sample.posterior_entropy.shape == (2,)


def test_latent_posterior_entropy_positive() -> None:
    lp = LatentPosterior()
    sample = lp(torch.randn(2, 128), torch.randn(2, 128))
    assert (sample.posterior_entropy >= 0).all()


def test_aux_heads_shapes() -> None:
    aux = AuxHeads()
    shared_h = torch.randn(3, 128)
    pre, fail = aux(shared_h)
    assert pre.shape in {(3,), (3, 1)}
    assert fail.shape in {(3,), (3, 1)}
    assert (pre >= 0).all() and (pre <= 1).all()
    assert (fail >= 0).all() and (fail <= 1).all()


def test_deterministic_given_seed() -> None:
    encoder = TextStateEncoder()
    torch.manual_seed(42)
    out1 = encoder(["test"])
    torch.manual_seed(42)
    out2 = encoder(["test"])
    assert torch.allclose(out1, out2)


def test_no_hidden_fields_required() -> None:
    hidden_fields = {
        "true_regime",
        "true_control_grammar",
        "true_wrong_hypothesis",
        "training_labels",
        "evaluation_labels",
        "counterfactuals",
    }
    for cls in (TextStateEncoder, HistoryEncoder, LatentPosterior):
        params = set(inspect.signature(cls.forward).parameters)
        assert hidden_fields.isdisjoint(params)
