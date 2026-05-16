"""frcgw.gui_env.lr_integration — Run 4C GUI-LR smoke adapter.

Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §5.1
Phase: 9 (Run 4C GUI smoke, conditional)
Run: 4 — minimal smoke adapter only. Full integration is Run 5+.

Maps GUIObservation public fields to EvidenceFeatures and runs one LR score call.
FORBIDDEN: true_grammar, true_regime, oracle labels in inference input.
"""
from __future__ import annotations

from typing import Any, Optional

from frcgw.falsification.lr_scorer import (
    EvidenceFeatures,
    EvidenceLikelihood,
    FalsificationResult,
    HypothesisCandidate,
    HypothesisTrace,
    LikelihoodRatioFalsificationScorer,
)
from frcgw.gui_env.leakage_audit import FORBIDDEN_GUI_AGENT_FIELDS, GUILeakageError
from frcgw.gui_env.event_schema import GUIObservation
from frcgw.schemas.visibility import _collect_field_names


def _assert_gui_obs_safe(obs: GUIObservation) -> None:
    """Raise GUILeakageError if obs contains any forbidden GUI fields."""
    names = _collect_field_names(obs)
    violations = sorted(names & FORBIDDEN_GUI_AGENT_FIELDS)
    if violations:
        raise GUILeakageError(violations)


def evidence_from_gui_obs(obs: GUIObservation) -> EvidenceFeatures:
    """Build EvidenceFeatures from a public GUIObservation.

    Allowed: obs.effect_description, obs.action_taken, obs.visible_text, obs.url.
    Forbidden: true_grammar, true_regime, oracle labels — never in GUIObservation.
    """
    _assert_gui_obs_safe(obs)

    effect_desc: str = obs.effect_description or ""
    effect_type: str = _infer_effect_type(effect_desc)
    no_effect_flag: bool = effect_type in ("no_effect", "no_change", "noop")

    return EvidenceFeatures(
        effect_type=effect_type,
        dom_diff_summary=effect_desc[:200],
        accessibility_diff_summary="",
        visual_diff_score=0.0,
        precondition_status="unknown",
        no_effect_flag=no_effect_flag,
        delayed_effect_flag=False,
        noisy_observation_flag=False,
        progress_delta=0.0,
        failure_reason=None,
    )


def _infer_effect_type(effect_desc: str) -> str:
    """Derive a coarse effect_type string from a public effect_description."""
    desc = effect_desc.lower()
    if not desc or desc in ("none", "no change", "no_change"):
        return "no_effect"
    if "error" in desc or "fail" in desc:
        return "error_effect"
    if "nav" in desc or "page" in desc or "url" in desc:
        return "navigation_effect"
    return "generic_effect"


def gui_lr_smoke(
    obs: GUIObservation,
    h_exec_id: str = "gui_exec_hypothesis",
    h_alt_id: str = "gui_alt_hypothesis",
    h_exec_meta: Optional[dict] = None,
    h_alt_meta: Optional[dict] = None,
) -> FalsificationResult:
    """Run one LR score call from a GUIObservation.

    Validates that obs contains no hidden labels, converts to EvidenceFeatures,
    and computes F_t. For smoke testing only — no phase gate produced.

    Returns:
        FalsificationResult with F_t, degenerate flag, calibration_features.
    """
    evidence = evidence_from_gui_obs(obs)

    h_exec = HypothesisCandidate(
        hypothesis_id=h_exec_id,
        regime_id="gui_regime",
        control_grammar_id="gui_grammar_exec",
        prior_logprob=-0.5,
        metadata=h_exec_meta or {},
    )
    h_alt = HypothesisCandidate(
        hypothesis_id=h_alt_id,
        regime_id="gui_regime",
        control_grammar_id="gui_grammar_alt",
        prior_logprob=-0.5,
        metadata=h_alt_meta or {"expected_effect_type": "no_effect", "expected_no_effect_flag": True},
    )

    el = EvidenceLikelihood()
    exec_ls = el.score(evidence, h_exec, None, None)
    alt_ls = el.score(evidence, h_alt, None, None)

    trace = HypothesisTrace(
        selected_hypothesis_id=h_exec_id,
        hypothesis_type="gui_predicted",
        confidence=0.6,
        source="gui_lr_smoke",
        is_oracle_label=False,
    )

    return LikelihoodRatioFalsificationScorer().score(
        h_exec_trace=trace,
        exec_likelihood=exec_ls,
        alt_likelihoods=[alt_ls],
        alt_candidates=[h_alt],
    )
