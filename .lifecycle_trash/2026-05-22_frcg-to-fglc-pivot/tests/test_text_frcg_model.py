from __future__ import annotations

import inspect

import pytest

torch = pytest.importorskip("torch")

from frcgw.models.encoders import HistoryEncoder, TextStateEncoder
from frcgw.models.latent_heads import AuxHeads, LatentPosterior, LatentSample
from frcgw.models.text_frcg_model import ModelOutput, TextFRCGModel
from frcgw.schemas.step_schema import PublicHistoryItem, PublicObservation


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


def test_model_output_keys() -> None:
    model = TextFRCGModel()
    pub = PublicObservation(instruction="click button", history_public=[])
    out = model(pub)
    assert isinstance(out, ModelOutput)
    assert out.z_state.shape[1] == 32
    assert out.z_regime_logits.shape[1] == 8
    assert out.z_grammar_logits.shape[1] == 8
    assert out.z_change_logits.shape[1] == 12
    assert out.z_reveal_shift_logits.shape[1] == 3
    assert out.shared_h.shape[1] == 128
    assert out.posterior_entropy.shape[0] == 1


def test_world_model_heads_shape() -> None:
    model = TextFRCGModel()
    pub = PublicObservation(instruction="test", history_public=[])
    out = model(pub)
    result = model.world_model_heads.forward_given_action(out.shared_h, out.z_state, "click", 0)
    assert result.effect_logits.shape == (1, 7)
    assert result.progress_pred.shape == (1,)
    assert result.failed_score.shape == (1,)


def test_forward_batch() -> None:
    model = TextFRCGModel()
    pubs = [PublicObservation(instruction=f"action {i}", history_public=[]) for i in range(4)]
    out = model(pubs)
    assert out.z_state.shape == (4, 32)
    assert out.posterior_entropy.shape == (4,)


def test_forward_no_hidden_fields() -> None:
    sig = inspect.signature(TextFRCGModel.forward)
    assert "true_regime" not in sig.parameters
    assert "true_control_grammar" not in sig.parameters


def test_deterministic_model_seed() -> None:
    model = TextFRCGModel()
    pub = PublicObservation(instruction="test", history_public=[])
    torch.manual_seed(42)
    out1 = model(pub)
    model.eval()
    with torch.no_grad():
        out2 = model(pub)
    assert torch.allclose(out1.z_state.detach(), out2.z_state.detach())


def test_action_embed_shape() -> None:
    model = TextFRCGModel()
    emb = model.action_embed("click")
    assert emb.shape[-1] == 64


def test_grammar_embed_shape() -> None:
    model = TextFRCGModel()
    emb = model.grammar_embed(0)
    assert emb.shape[-1] == 32
