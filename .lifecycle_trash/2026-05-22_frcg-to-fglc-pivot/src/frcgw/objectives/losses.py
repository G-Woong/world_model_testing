"""frcgw.objectives.losses -- 6 main + 4 aux losses for P3 text model.

Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md L-MAIN-001..006, L-AUX-001..005
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import Tensor
import torch.nn.functional as F

from frcgw.data.text_dataset import BatchTargets
from frcgw.models.falsification_head import LFDOutput
from frcgw.models.text_frcg_model import ModelOutput
from frcgw.models.world_model_heads import RolloutResult
from frcgw.schemas.visibility import HiddenLabelLeakageError, assert_agent_observation_safe


REGIME_VOCAB: dict[str, int] = {
    "search_form": 0,
    "required_dropdown": 1,
    "modal_blocker": 2,
    "nested_scroll": 3,
    "permission_gate": 4,
    "filter_accordion": 5,
    "pagination_vs_infinite": 6,
    "loading_delayed": 7,
}

GRAMMAR_VOCAB: dict[str, int] = {
    "direct_search": 0,
    "required_dropdown_then_search": 1,
    "modal_confirm_then_action": 2,
    "container_scroll_then_select": 3,
    "wait_until_enabled_then_click": 4,
    "permission_accept_then_action": 5,
    "filter_open_then_select": 6,
    "pagination_or_infinite_scroll": 7,
}

REVEAL_SHIFT_VOCAB: dict[str, int] = {"none": 0, "reveal": 1, "shift": 2}

# SSoT alignment: planner.py::_effect_type_id, _PUBLIC_EFFECT_TYPES in
# counterfactual_rollout.py. n_effect_types=7 (indices 0-6).
EFFECT_TYPE_VOCAB: dict[str, int] = {
    # legacy (preserved for backward compat)
    "none": 0,
    "no_change": 0,
    "reveal": 1,
    "shift": 2,
    "failed": 3,
    "delayed": 4,
    "noisy": 5,
    "no_op_valid": 6,
    # v0_3 / _PUBLIC_EFFECT_TYPES strings (must match planner.py::_effect_type_id)
    "no_state_change": 0,
    "state_change": 1,
    "blocker_removed": 2,
    "delayed_effect": 4,
    "task_complete": 5,
}

DEFAULT_WEIGHTS: dict[str, float] = {
    "l_action_effect": 1.0,
    "l_progress": 0.5,
    "l_regime": 1.0,
    "l_control_grammar": 1.0,
    "l_falsification": 1.0,
    "l_intent_action_mapping": 0.5,
    "l_change_point": 0.3,
    "l_reveal_shift": 0.3,
    "l_failed_action": 0.3,
    "l_temporal_consistency": 0.1,
    # LFD losses (active only when lfd_output is provided)
    "l_seq_falsification": 1.0,
    "l_run_length_posterior": 0.5,
}


@dataclass
class LossDict:
    l_action_effect: Tensor
    l_progress: Tensor
    l_regime: Tensor
    l_control_grammar: Tensor
    l_falsification: Tensor
    l_intent_action_mapping: Tensor
    l_change_point: Tensor
    l_reveal_shift: Tensor
    l_failed_action: Tensor
    l_temporal_consistency: Tensor
    l_seq_falsification: Tensor
    l_run_length_posterior: Tensor
    l_total: Tensor
    weights: dict[str, float]


def assert_no_objective_leakage(public_input: Any) -> None:
    if isinstance(public_input, BatchTargets):
        raise HiddenLabelLeakageError("targets must not be passed as public_input")
    assert_agent_observation_safe(public_input)


def L_action_effect(effect_logits: Tensor, targets: list[BatchTargets]) -> Tensor:
    return F.cross_entropy(effect_logits, _class_targets(targets, "true_action_effect_type", EFFECT_TYPE_VOCAB, effect_logits))


def L_progress(progress_pred: Tensor, targets: list[BatchTargets]) -> Tensor:
    y = torch.tensor([float(t.progress_delta) for t in targets], dtype=progress_pred.dtype, device=progress_pred.device)
    return F.mse_loss(progress_pred.reshape(-1), y)


def L_regime(regime_logits: Tensor, targets: list[BatchTargets]) -> Tensor:
    return F.cross_entropy(regime_logits, _class_targets(targets, "true_regime", REGIME_VOCAB, regime_logits))


def L_control_grammar(grammar_logits: Tensor, targets: list[BatchTargets]) -> Tensor:
    return F.cross_entropy(grammar_logits, _class_targets(targets, "true_control_grammar", GRAMMAR_VOCAB, grammar_logits))


def L_falsification(F_t: Tensor | None, targets: list[BatchTargets]) -> Tensor:
    labeled = [(idx, t) for idx, t in enumerate(targets) if t.true_wrong_hypothesis is not None]
    if F_t is None or not labeled:
        return _zero(F_t)
    scores = F_t.reshape(-1)
    idx = torch.tensor([i for i, _ in labeled], dtype=torch.long, device=F_t.device)
    y = torch.tensor(
        [float(bool(t.true_wrong_hypothesis)) for _, t in labeled],
        dtype=F_t.dtype,
        device=F_t.device,
    )
    return F.binary_cross_entropy(torch.sigmoid(scores.index_select(0, idx)), y)


def L_intent_action_mapping(rewrite_logits: Tensor | None, targets: list[BatchTargets]) -> Tensor:
    return _zero(rewrite_logits)


def L_change_point(change_logits: Tensor, targets: list[BatchTargets]) -> Tensor:
    y = torch.tensor([int(t.true_change_point) for t in targets], dtype=torch.long, device=change_logits.device)
    return F.cross_entropy(change_logits, y)


def L_reveal_shift(reveal_logits: Tensor, targets: list[BatchTargets]) -> Tensor:
    return F.cross_entropy(reveal_logits, _class_targets(targets, "true_reveal_vs_shift", REVEAL_SHIFT_VOCAB, reveal_logits))


def L_failed_action(failed_score: Tensor, targets: list[BatchTargets]) -> Tensor:
    y = torch.tensor([float(bool(t.true_failed_action)) for t in targets], dtype=failed_score.dtype, device=failed_score.device)
    return F.binary_cross_entropy(failed_score.reshape(-1).clamp(1.0e-7, 1.0 - 1.0e-7), y)


def L_temporal_consistency(posterior_entropy: Tensor | None) -> Tensor:
    """Penalize sudden upward jumps in posterior entropy across a batch.

    Replaces _zero() placeholder (TASK_LFD_005).
    Treats consecutive batch items as a pseudo-sequence (proxy for per-episode
    temporal consistency). For single-step or None input: returns zero gracefully.

    Loss = mean(ReLU(entropy[t] - entropy[t-1] - margin)) over batch pairs.
    """
    if posterior_entropy is None:
        return _zero(None)
    entropy = posterior_entropy.reshape(-1)
    if entropy.numel() <= 1:
        return entropy.new_zeros(())
    margin = 0.1
    jumps = F.relu(entropy[1:] - entropy[:-1] - margin)
    return jumps.mean()


def L_seq_falsification(
    lfd_wrong_probs: Tensor | None,
    targets: list[BatchTargets],
) -> Tensor:
    """Cumulative BCE on LFD wrong_prob_learned across batch steps.

    Source: TASK_LFD_005, paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md L-LFD-001
    Supervises FalsificationDetectorHead.wrong_prob_learned on true_wrong_hypothesis labels.

    Note on gradient conflict with L_falsification: both supervise on the same
    true_wrong_hypothesis label. L_falsification targets the deterministic F_t score
    (world model head gradients); L_seq_falsification targets wrong_prob_learned
    (FalsificationDetectorHead gradients). Shared upstream encoder receives both
    gradient signals. If empirically conflicting, use l_falsification weight=0
    when lfd_output is active (run ablation to verify).
    """
    labeled = [(idx, t) for idx, t in enumerate(targets) if t.true_wrong_hypothesis is not None]
    if lfd_wrong_probs is None or not labeled:
        return _zero(lfd_wrong_probs)
    probs = lfd_wrong_probs.reshape(-1)
    idx = torch.tensor([i for i, _ in labeled], dtype=torch.long, device=probs.device)
    y = torch.tensor(
        [float(bool(t.true_wrong_hypothesis)) for _, t in labeled],
        dtype=probs.dtype,
        device=probs.device,
    )
    return F.binary_cross_entropy(
        probs.index_select(0, idx).clamp(1.0e-7, 1.0 - 1.0e-7), y
    )


def L_run_length_posterior(
    run_length_posterior: Tensor | None,
    targets: list[BatchTargets],
) -> Tensor:
    """Cross-entropy from BOCPD run-length posterior to soft target distribution.

    Source: TASK_LFD_005, Adams & MacKay (2007) BOCPD
    Soft target: Gaussian-like around expected run length derived from
    true_wrong_hypothesis. wrong=True → short run (switch happened recently),
    wrong=False → longer run (stable hypothesis).
    unknown → uniform (returns zero contribution).
    """
    if run_length_posterior is None:
        return _zero(run_length_posterior)
    batch_size, max_rl = run_length_posterior.shape
    device = run_length_posterior.device
    dtype = run_length_posterior.dtype

    soft_targets: list[Tensor] = []
    for t in targets:
        if t.true_wrong_hypothesis is True:
            expected_rl = 1  # recent switch → short run length
        elif t.true_wrong_hypothesis is False:
            expected_rl = min(max_rl - 1, 5)  # stable → longer run
        else:
            # No label: contribute uniform (zero KL from uniform target)
            soft_targets.append(torch.ones(max_rl, device=device, dtype=dtype) / max_rl)
            continue
        positions = torch.arange(max_rl, device=device, dtype=dtype)
        sigma = 1.5
        target = torch.exp(-0.5 * ((positions - expected_rl) / sigma) ** 2)
        soft_targets.append(target / target.sum())

    if not soft_targets:
        return run_length_posterior.new_zeros(())

    target_tensor = torch.stack(soft_targets)  # [batch, max_rl]
    log_posterior = torch.log(run_length_posterior.clamp(min=1.0e-8))
    # Forward cross-entropy: -sum(target * log(posterior)) per item, then mean
    return -(target_tensor * log_posterior).sum(dim=-1).mean()


def compute_total_loss(
    model_output: ModelOutput,
    world_model_output: RolloutResult | None,
    F_t: Tensor | None,
    targets: list[BatchTargets],
    weights: dict[str, float] | None = None,
    public_input: list[Any] | None = None,
    lfd_output: LFDOutput | None = None,
) -> LossDict:
    if public_input is not None:
        for item in public_input:
            assert_no_objective_leakage(item)

    active_weights = dict(DEFAULT_WEIGHTS)
    if weights is not None:
        active_weights.update(weights)

    if world_model_output is None:
        l_action_effect = _zero(model_output.z_state)
        l_progress = _zero(model_output.z_state)
        l_failed_action = _zero(model_output.z_state)
    else:
        l_action_effect = L_action_effect(world_model_output.effect_logits, targets)
        l_progress = L_progress(world_model_output.progress_pred, targets)
        l_failed_action = L_failed_action(world_model_output.failed_score, targets)

    # LFD losses: active when lfd_output is provided (v0_5 training); zero otherwise.
    if lfd_output is not None:
        l_seq_falsification = L_seq_falsification(lfd_output.wrong_prob_learned, targets)
        l_run_length_posterior = L_run_length_posterior(lfd_output.run_length_posterior, targets)
    else:
        l_seq_falsification = _zero(model_output.z_state)
        l_run_length_posterior = _zero(model_output.z_state)

    losses = {
        "l_action_effect": l_action_effect,
        "l_progress": l_progress,
        "l_regime": L_regime(model_output.z_regime_logits, targets),
        "l_control_grammar": L_control_grammar(model_output.z_grammar_logits, targets),
        "l_falsification": L_falsification(F_t, targets),
        "l_intent_action_mapping": L_intent_action_mapping(None, targets),
        "l_change_point": L_change_point(model_output.z_change_logits, targets),
        "l_reveal_shift": L_reveal_shift(model_output.z_reveal_shift_logits, targets),
        "l_failed_action": l_failed_action,
        "l_temporal_consistency": L_temporal_consistency(model_output.posterior_entropy),
        "l_seq_falsification": l_seq_falsification,
        "l_run_length_posterior": l_run_length_posterior,
    }
    l_total = sum(float(active_weights[name]) * loss for name, loss in losses.items())
    return LossDict(l_total=l_total, weights=active_weights, **losses)


def _class_targets(
    targets: list[BatchTargets],
    attr: str,
    vocab: dict[str, int],
    ref: Tensor,
) -> Tensor:
    labels = []
    for target in targets:
        value = str(getattr(target, attr))
        if value not in vocab:
            raise KeyError(f"unknown {attr} label: {value}")
        labels.append(vocab[value])
    return torch.tensor(labels, dtype=torch.long, device=ref.device)


def _zero(ref: Tensor | None) -> Tensor:
    if ref is None:
        return torch.tensor(0.0)
    return ref.new_zeros(())
