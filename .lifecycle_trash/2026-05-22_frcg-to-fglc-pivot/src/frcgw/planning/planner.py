"""frcgw.planning.planner -- text_frcg_plan closed-loop step function.

Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md 12
"""
from __future__ import annotations

from dataclasses import dataclass

from frcgw.models.latent_heads import LatentSample
from frcgw.models.text_frcg_model import ModelOutput, TextFRCGModel
from frcgw.planning.alternative_proposer import HypothesisId, propose
from frcgw.planning.decision_gate import GateConfig, GateInput, decide
from frcgw.planning.falsification import FalsificationEvidence, falsification_score
from frcgw.planning.rewrite import rewrite_action, validate_rewrite
from frcgw.schemas.step_schema import CandidateAction, PublicObservation
from frcgw.schemas.visibility import assert_agent_observation_safe


@dataclass
class PlanMetadata:
    planned: bool
    reason: str
    h_star: HypothesisId | None = None
    F_t: float = 0.0
    delta_V: float = 0.0


class PlannerState:
    """Tracks h_exec per step index. NOT backed by EvaluationLabels at inference."""

    def __init__(self) -> None:
        self._current_by_step: dict[int, int] = {}

    def get_current(self, step_idx: int) -> int:
        return self._current_by_step.get(step_idx, 0)

    def update(self, step_idx: int, hypothesis_id: int) -> None:
        self._current_by_step[step_idx] = hypothesis_id


def _latent_sample_from_output(model_out: ModelOutput) -> LatentSample:
    return LatentSample(
        z_state=model_out.z_state,
        z_regime_logits=model_out.z_regime_logits,
        z_grammar_logits=model_out.z_grammar_logits,
        z_change_logits=model_out.z_change_logits,
        z_reveal_shift_logits=model_out.z_reveal_shift_logits,
        shared_h=model_out.shared_h,
        posterior_entropy=model_out.posterior_entropy,
        aux_precondition=model_out.aux_precondition,
        aux_failure_risk=model_out.aux_failure_risk,
    )


def _effect_type_id(effect_summary: str | None) -> int:
    key = (effect_summary or "none").strip().lower()
    # Legacy keys preserved for backward compat with training-proxy ABL data.
    # SSoT for public strings: counterfactual_rollout.py::_PUBLIC_EFFECT_TYPES.
    # n_effect_types=7 (indices 0-6); task_complete=5 avoids the {0, 6} short-circuit.
    mapping = {
        "none": 0,
        "no_change": 0,
        "reveal": 1,
        "shift": 2,
        "failed": 3,
        "delayed": 4,
        "noisy": 5,
        "no_op_valid": 6,
        "no_state_change": 0,
        "state_change": 1,
        "blocker_removed": 2,
        "delayed_effect": 4,
        "task_complete": 5,
    }
    return mapping.get(key, 0)


def _last_effect_summary(public_obs: PublicObservation) -> str | None:
    if not public_obs.history_public:
        return "none"
    return public_obs.history_public[-1].effect_summary or "none"


def _value_for_hypothesis(
    model: TextFRCGModel,
    model_out: ModelOutput,
    action_type: str,
    hypothesis_id: int,
) -> float:
    rollout = model.world_model_heads.rollout_step(
        model_out.shared_h,
        model_out.z_state,
        action_type,
        hypothesis_id,
        H=1,
    )
    return float(rollout.progress_pred.squeeze().item())


def text_frcg_plan(
    public_obs: PublicObservation,
    step_idx: int,
    candidates: list[CandidateAction],
    model: TextFRCGModel,
    planner_state: PlannerState,
    cfg: GateConfig | None = None,
    use_no_state_change_proxy: bool = True,
) -> tuple[CandidateAction, PlanMetadata]:
    """Closed-loop planning step.

    Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md 12
    """
    assert_agent_observation_safe(public_obs)
    base_action = candidates[0] if candidates else CandidateAction("noop", "noop", {})
    model_out = model.forward(public_obs)
    cfg = cfg or GateConfig()
    use_no_state_change_proxy = bool(cfg.use_no_state_change_proxy) and use_no_state_change_proxy
    effect_text = _last_effect_summary(public_obs)
    # fix-2a: derive observed_failed_action from public effect_summary (inference-safe proxy).
    # no_state_change → type 3 (failed proxy) to bypass falsification short-circuit on type 0.
    # Rationale: "action executed under wrong grammar but produced no visible change" is
    # functionally equivalent to a failed action for falsification scoring purposes.
    _effect_key = (effect_text or "none").lower()
    _no_effect_keys = {"none", "no_change", "no_state_change"}
    if use_no_state_change_proxy:
        _obs_effect_type_id = 3 if _effect_key == "no_state_change" else _effect_type_id(effect_text)
    else:
        _obs_effect_type_id = _effect_type_id(effect_text)
    _failed_keywords = {"failed", "failed_action", "blocked", "no_op_valid", "no_change"}
    if use_no_state_change_proxy:
        _observed_failed = any(kw in _effect_key for kw in _failed_keywords) or _effect_key == "no_state_change"
    else:
        _observed_failed = any(kw in _effect_key for kw in _failed_keywords)
    _observed_progress = 0.0 if _effect_key in _no_effect_keys else 1.0
    evidence = FalsificationEvidence(_obs_effect_type_id, _observed_progress, _observed_failed)
    h_exec_id = planner_state.get_current(step_idx)

    # STEP 6 B2 fix: propose() must run BEFORE falsification_score() so alt_ids is non-empty.
    # posterior_only: prior-ranked alts; evidence-blind by design at inference.
    latent_sample = _latent_sample_from_output(model_out)
    alt_hypotheses = propose(
        latent_sample,
        model=None,
        shared_h=None,
        z_state=None,
        action_type=None,
        evidence=None,
        mode="posterior_only",
        k=3,
    )
    alt_ids = [h.combined_id for h in alt_hypotheses if isinstance(h.combined_id, int)]

    F_t_tensor = falsification_score(
        model,
        model_out.shared_h,
        model_out.z_state,
        base_action.action_type,
        h_exec_id,
        alt_ids,
        evidence,
    )
    F_t = float(F_t_tensor.item())
    if F_t <= cfg.tau_f:
        return base_action, PlanMetadata(planned=False, reason="low_F_t", F_t=F_t)

    h_exec_value = _value_for_hypothesis(model, model_out, base_action.action_type, h_exec_id)
    alt_values = [
        _value_for_hypothesis(model, model_out, base_action.action_type, h.combined_id)
        for h in alt_hypotheses
    ]
    if alt_values:
        best_idx = max(range(len(alt_values)), key=lambda idx: alt_values[idx])
        best_alt_value = alt_values[best_idx]
        h_star = alt_hypotheses[best_idx]
    else:
        best_alt_value = h_exec_value
        h_star = None

    delta_V = best_alt_value - h_exec_value
    P_switch = 1.0 if h_star is not None and h_star.combined_id != h_exec_id else 0.0
    C_plan = cfg.C_plan_beta * len(alt_hypotheses) * 1
    gate_input = GateInput(
        F_t=F_t,
        delta_V=delta_V,
        P_switch=P_switch,
        C_plan=C_plan,
        posterior_entropy=float(model_out.posterior_entropy.squeeze().item()),
    )
    gate_out = decide(gate_input, cfg)
    if not gate_out.should_plan or h_star is None:
        return base_action, PlanMetadata(planned=False, reason=gate_out.reason, F_t=F_t, delta_V=delta_V)

    rewrite_result, confidence = rewrite_action(public_obs.instruction, h_star, candidates, model)
    valid, reason = validate_rewrite(rewrite_result, public_obs, confidence, tau_r=cfg.tau_r)
    if valid:
        assert rewrite_result is not None
        # fix-2b: update h_exec for next step so P_switch is correctly re-evaluated.
        planner_state.update(step_idx + 1, h_star.combined_id)
        return rewrite_result, PlanMetadata(
            planned=True,
            reason="planned",
            h_star=h_star,
            F_t=F_t,
            delta_V=delta_V,
        )
    return base_action, PlanMetadata(
        planned=False,
        reason=f"rewrite_invalid:{reason}",
        F_t=F_t,
        delta_V=delta_V,
    )
