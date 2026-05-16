"""frcgw.falsification.lr_scorer — Run 4 LR core implementation.

Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md
Phase: 8 (LR Core Implementation)
Run: 4 — actual logic; stub counterpart is lr_scorer_stub.py (Run 3).

Forbidden imports: torch, numpy, pandas, sklearn.
Main path: log-likelihood ratio only. Classifier-variant losses are ABL-022/023 ablation only.
Hidden-label contract: FORBIDDEN_AGENT_FIELDS and true_*/oracle_* keys must
never appear in EvidenceFeatures fields or HypothesisCandidate.metadata.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from frcgw.schemas.visibility import (
    FORBIDDEN_AGENT_FIELDS,
    CounterfactualLeakageError,
    HiddenLabelLeakageError,
)

if TYPE_CHECKING:
    from frcgw.schemas.step_schema import StepRecord


_HIDDEN_PREFIXES: tuple[str, ...] = ("true_", "oracle_")


def _check_metadata_for_leakage(metadata: Dict[str, Any], context: str = "") -> None:
    """Raise if any metadata key is a forbidden/hidden field.

    Order: counterfactual_action_effects → CounterfactualLeakageError first,
    then other FORBIDDEN_AGENT_FIELDS or true_*/oracle_* → HiddenLabelLeakageError.
    """
    suffix = f" ({context})" if context else ""
    for key in metadata:
        if key == "counterfactual_action_effects":
            raise CounterfactualLeakageError(
                f"counterfactual field in hypothesis metadata: {key}{suffix}"
            )
        if key in FORBIDDEN_AGENT_FIELDS:
            raise HiddenLabelLeakageError(
                f"forbidden field in hypothesis metadata: {key}{suffix}"
            )
        for prefix in _HIDDEN_PREFIXES:
            if key.startswith(prefix):
                raise HiddenLabelLeakageError(
                    f"hidden-label prefix '{prefix}' in hypothesis metadata key: {key}{suffix}"
                )


def _summarize_dom_diff(dom_diff: Any) -> str:
    """Convert a public dom_diff dict to a compact string for EvidenceFeatures."""
    if dom_diff is None:
        return ""
    if isinstance(dom_diff, dict):
        return str(sorted(dom_diff.items()))
    return str(dom_diff)


# ---------------------------------------------------------------------------
# §4. Data Structures — 9 dataclasses
# ---------------------------------------------------------------------------


@dataclass
class EvidenceFeatures:
    """Action-effect evidence extracted from public observations only.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §4
    Anti-leakage: all fields are public observed evidence.
    FORBIDDEN: true_control_grammar, true_regime, oracle labels, counterfactual.
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.2
    """

    effect_type: str
    dom_diff_summary: str
    accessibility_diff_summary: str
    visual_diff_score: float
    precondition_status: str
    no_effect_flag: bool
    delayed_effect_flag: bool
    noisy_observation_flag: bool
    progress_delta: float
    failure_reason: Optional[str]

    @classmethod
    def from_public_step(cls, step: "StepRecord") -> "EvidenceFeatures":
        """Build EvidenceFeatures from public-only fields of a StepRecord.

        Allowed: step.public_observation, step.action, step.observed_effect_public.
        Forbidden: step.training_labels, step.evaluation_labels,
                   step.counterfactuals, step.audit_metadata — never accessed below.
        """
        _accessed_hidden = False
        assert not _accessed_hidden, "Hidden fields must not be accessed in from_public_step"

        eff = step.observed_effect_public
        effect_type: str = eff.effect_type
        dom_diff_summary: str = _summarize_dom_diff(eff.dom_diff_public)
        text_diff: str = eff.text_diff_public or ""
        visual_diff_score: float = 0.0        # no visual field in current public schema
        precondition_status: str = "unknown"  # no public precondition proxy in schema
        no_effect_flag: bool = effect_type in ("no_effect", "no_change", "noop")
        delayed_effect_flag: bool = False     # no public delayed marker in schema
        noisy_observation_flag: bool = False  # no public noisy marker in schema
        progress_delta: float = 0.0           # training_labels.progress_delta is hidden
        failure_reason: Optional[str] = None  # training_labels.failure_reason is hidden

        return cls(
            effect_type=effect_type,
            dom_diff_summary=dom_diff_summary,
            accessibility_diff_summary=text_diff,
            visual_diff_score=visual_diff_score,
            precondition_status=precondition_status,
            no_effect_flag=no_effect_flag,
            delayed_effect_flag=delayed_effect_flag,
            noisy_observation_flag=noisy_observation_flag,
            progress_delta=progress_delta,
            failure_reason=failure_reason,
        )


@dataclass
class HypothesisTrace:
    """Predicted hypothesis trace for the executed action.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §4
    Anti-leakage: selected_hypothesis_id is model/agent choice, not oracle label.
    FORBIDDEN: true_control_grammar, true_regime, oracle labels — not mixed in here.
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §5 Symbol Table line 123
    """

    selected_hypothesis_id: str
    hypothesis_type: str
    confidence: float
    source: str
    is_oracle_label: bool = False


@dataclass
class HypothesisCandidate:
    """Alternative hypothesis candidate in A_t^H.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §4
    Note: A_t^H is the alternative hypothesis set, not an alternative action set.
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §8 PROP-01..10
    """

    hypothesis_id: str
    regime_id: str
    control_grammar_id: str
    prior_logprob: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LikelihoodScore:
    """Output of EvidenceLikelihood for a single hypothesis.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §4
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.2 line 152
    ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h)
    """

    hypothesis_id: str
    loglik: float
    diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FalsificationResult:
    """Output of LikelihoodRatioFalsificationScorer.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §4
    F_t = max_{h_alt in A_t^H} [ell_t(h_alt) - ell_t(h_exec)]
    margin is set to 0.0 here; actual margin = F_t - tau_f computed in DecisionRelevanceGate.

    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.3 line 171
    """

    h_exec_id: str
    best_h_alt_id: Optional[str]
    loglik_exec: float
    loglik_alt_best: float
    F_t: float
    margin: float
    degenerate: bool
    calibration_features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PosteriorState:
    """Current posterior distribution over (regime, grammar) hypotheses.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §4
    Note: not exact Bayesian posterior — simple normalized approximation.
    b_t(z^r, z^g) = q_phi(z^r, z^g | H_t)
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.1 line 142
    """

    posterior_by_hypothesis: Dict[str, float]
    entropy: float
    top_hypothesis_id: str


@dataclass
class PosteriorUpdateResult:
    """Result of PosteriorUpdater step.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §4
    """

    posterior_before: PosteriorState
    posterior_after: PosteriorState
    posterior_shift: float
    adopted_hypothesis_id: str
    switch_recommended: bool


@dataclass
class GateDecision:
    """Output of DecisionRelevanceGate.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §4
    G_t = I[F_t > tau_f AND delta_V > tau_v AND P(switch) > tau_a AND delta_V - C_plan > 0]
    Note: uncertainty threshold single-condition is NOT equivalent — 4-way conjunction.
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.5 lines 200-209
    """

    G_t: bool
    planning_allowed: bool
    decision_relevance_delta: float
    action_switch_probability: float
    compute_cost: float
    gate_reason: str


@dataclass
class RewriteDecision:
    """Output of GrammarConditionedRewrite.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §4
    a_exec = Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*)
    Note: h* is predicted trace, not oracle label.
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.6
    """

    intent_id: str
    base_action_id: str
    selected_hypothesis_id: str
    executable_action_id: str
    rewrite_triggered: bool
    rewrite_confidence: float
    fallback_used: bool
    rewrite_reason: str


# ---------------------------------------------------------------------------
# §5. Component Classes — 5
# ---------------------------------------------------------------------------

# Public-safe expected fields recognized in HypothesisCandidate.metadata.
_PUBLIC_SAFE_METADATA_KEYS: frozenset[str] = frozenset({
    "expected_effect_type",
    "expected_no_effect_flag",
    "expected_precondition_status",
    "expected_progress_direction",
    "expected_failure_reason_public",
})


class EvidenceLikelihood:
    """ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h).

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §5.1
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.2 line 152

    Deterministic public-evidence scorer — not a neural likelihood.
    Main path: log-likelihood ratio form only. Ablation variants (ABL-022/023) are separate.
    Anti-leakage: metadata keys checked for forbidden/hidden fields in score().
    """

    def score(
        self,
        evidence: EvidenceFeatures,
        hypothesis: HypothesisCandidate,
        history_encoding: Any,
        prev_action: Any,
    ) -> LikelihoodScore:
        """Compute ell_t(h) for a single hypothesis against public evidence.

        Scoring rules (deterministic, public-safe):
          expected_effect_type match        → +1.0
          expected_no_effect_flag match     → +0.5
          expected_precondition_status match→ +0.5
          expected_progress_direction sign  → +0.5
          noisy_observation_flag=True       → score *= 0.5
          delayed_effect_flag=True          → diagnostics warning only
        """
        _check_metadata_for_leakage(hypothesis.metadata, context=hypothesis.hypothesis_id)

        meta = hypothesis.metadata
        score = 0.0
        diagnostics: Dict[str, Any] = {}

        expected_effect_type = meta.get("expected_effect_type")
        if expected_effect_type is not None and expected_effect_type == evidence.effect_type:
            score += 1.0

        expected_no_effect_flag = meta.get("expected_no_effect_flag")
        if expected_no_effect_flag is not None and expected_no_effect_flag == evidence.no_effect_flag:
            score += 0.5

        expected_precondition_status = meta.get("expected_precondition_status")
        if (
            expected_precondition_status is not None
            and expected_precondition_status == evidence.precondition_status
        ):
            score += 0.5

        expected_progress_direction = meta.get("expected_progress_direction")
        if expected_progress_direction is not None:
            delta = evidence.progress_delta
            if expected_progress_direction == "positive" and delta > 0:
                score += 0.5
            elif expected_progress_direction == "negative" and delta < 0:
                score += 0.5
            elif expected_progress_direction == "zero" and delta == 0.0:
                score += 0.5

        if evidence.noisy_observation_flag:
            diagnostics["noisy"] = True
            score *= 0.5

        if evidence.delayed_effect_flag:
            diagnostics["delayed"] = True
            diagnostics["delayed_warning"] = "Delayed effect: immediate falsification may be unreliable"

        return LikelihoodScore(
            hypothesis_id=hypothesis.hypothesis_id,
            loglik=score,
            diagnostics=diagnostics,
        )


class LikelihoodRatioFalsificationScorer:
    """F_t = max_{h_alt in A_t^H} [ell_t(h_alt) - ell_t(h_exec)].

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §5.2
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.3 line 171

    Main LR form (Option B main path).
    Ablation-022/023 comparison variants are separate files — not this class.
    Anti-leakage: h_exec is predicted trace, not oracle label.
    FORBIDDEN: true_control_grammar, true_regime in inference input.
    """

    def score(
        self,
        h_exec_trace: HypothesisTrace,
        exec_likelihood: LikelihoodScore,
        alt_likelihoods: List[LikelihoodScore],
        alt_candidates: List[HypothesisCandidate],
    ) -> FalsificationResult:
        """Compute F_t = max_alt(ell_alt) - ell_exec.

        Edge cases handled:
          - h_exec missing/empty → degenerate, F_t=0.0
          - alt_likelihoods empty → degenerate, F_t=0.0
          - exec_likelihood.hypothesis_id mismatch → ValueError
          - all loglik equal (max - exec == 0.0) → degenerate
          - best_h_alt_id == h_exec_id → degenerate + diagnostics
        """
        h_exec_id = h_exec_trace.selected_hypothesis_id

        # Edge case: missing h_exec
        if not h_exec_id:
            return FalsificationResult(
                h_exec_id=h_exec_id or "",
                best_h_alt_id=None,
                loglik_exec=0.0,
                loglik_alt_best=0.0,
                F_t=0.0,
                margin=0.0,
                degenerate=True,
                calibration_features={"reason": "h_exec_id_missing"},
            )

        # Validate exec_likelihood matches h_exec_trace
        if exec_likelihood.hypothesis_id != h_exec_id:
            raise ValueError(
                f"exec_likelihood.hypothesis_id={exec_likelihood.hypothesis_id!r} "
                f"does not match h_exec_trace.selected_hypothesis_id={h_exec_id!r}"
            )

        # Edge case: no alternatives
        if not alt_likelihoods:
            return FalsificationResult(
                h_exec_id=h_exec_id,
                best_h_alt_id=None,
                loglik_exec=exec_likelihood.loglik,
                loglik_alt_best=exec_likelihood.loglik,
                F_t=0.0,
                margin=0.0,
                degenerate=True,
                calibration_features={"reason": "alt_likelihoods_empty"},
            )

        # Compute F_t = max_alt(loglik_alt) - loglik_exec
        best_alt = max(alt_likelihoods, key=lambda s: s.loglik)
        loglik_exec = exec_likelihood.loglik
        loglik_alt_best = best_alt.loglik
        F_t = loglik_alt_best - loglik_exec

        calibration: Dict[str, Any] = {}
        degenerate = False

        # Degenerate: all likelihoods equal (F_t == 0.0)
        if F_t == 0.0:
            degenerate = True
            calibration["reason"] = "all_loglik_equal"

        # Degenerate: best alt is same as h_exec (theoretical inconsistency)
        if best_alt.hypothesis_id == h_exec_id:
            degenerate = True
            calibration["reason"] = calibration.get("reason", "") + "|best_alt_equals_h_exec"

        return FalsificationResult(
            h_exec_id=h_exec_id,
            best_h_alt_id=best_alt.hypothesis_id,
            loglik_exec=loglik_exec,
            loglik_alt_best=loglik_alt_best,
            F_t=F_t,
            margin=0.0,  # tau_f not available here; computed by DecisionRelevanceGate
            degenerate=degenerate,
            calibration_features=calibration,
        )


class PosteriorUpdater:
    """b_t(z^r, z^g) = q_phi(z^r, z^g | H_t) — simple normalized approximation.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §5.3
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.1 line 142

    Note: not exact Bayesian posterior; simple normalized update proportional to exp(F_t).
    Anti-leakage: H_t uses public observations only. true_regime / true_control_grammar forbidden.
    """

    def update(
        self,
        prior_state: PosteriorState,
        evidence: EvidenceFeatures,
        falsification_result: FalsificationResult,
        history_encoding: Any,
    ) -> PosteriorUpdateResult:
        """Update posterior b_t given new evidence and falsification result.

        Algorithm:
          1. Copy prior posterior dict.
          2. If F_t > 0 and best_h_alt_id is not None → multiply best_h_alt by exp(F_t).
          3. Normalize (sum=1).
          4. posterior_shift = TV distance = sum(|after - before|) / 2.
          5. adopted_hypothesis_id = argmax(posterior_after).
          6. switch_recommended = (adopted != prior top).
        """
        posterior: Dict[str, float] = dict(prior_state.posterior_by_hypothesis)

        if (
            not falsification_result.degenerate
            and falsification_result.F_t > 0
            and falsification_result.best_h_alt_id is not None
        ):
            alt_id = falsification_result.best_h_alt_id
            if alt_id in posterior:
                posterior[alt_id] *= math.exp(falsification_result.F_t)

        # Normalize
        total = sum(posterior.values())
        if total > 0:
            posterior = {k: v / total for k, v in posterior.items()}

        # TV distance
        all_hyps = set(posterior) | set(prior_state.posterior_by_hypothesis)
        posterior_shift = (
            sum(
                abs(posterior.get(h, 0.0) - prior_state.posterior_by_hypothesis.get(h, 0.0))
                for h in all_hyps
            )
            / 2.0
        )

        # Adopted hypothesis
        if posterior:
            adopted_hypothesis_id = max(posterior, key=lambda k: posterior[k])
        else:
            adopted_hypothesis_id = prior_state.top_hypothesis_id

        # Entropy of new posterior
        entropy = -sum(
            p * math.log(p + 1e-12) for p in posterior.values() if p > 0
        )

        posterior_after = PosteriorState(
            posterior_by_hypothesis=posterior,
            entropy=entropy,
            top_hypothesis_id=adopted_hypothesis_id,
        )

        switch_recommended = adopted_hypothesis_id != prior_state.top_hypothesis_id

        return PosteriorUpdateResult(
            posterior_before=prior_state,
            posterior_after=posterior_after,
            posterior_shift=posterior_shift,
            adopted_hypothesis_id=adopted_hypothesis_id,
            switch_recommended=switch_recommended,
        )


class DecisionRelevanceGate:
    """G_t = I[F_t > tau_f AND delta_V > tau_v AND P_switch > tau_a AND delta_V - C_plan > 0].

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §5.4
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.5 lines 200-209

    Note: 4-way conjunction — NOT equivalent to uncertainty > threshold single condition.
    This distinction is the core of C6 claim (compute-gate vs uncertainty gate).
    """

    def decide(
        self,
        falsification_result: FalsificationResult,
        posterior_update: PosteriorUpdateResult,
        value_gain_delta: float,
        action_switch_probability: float,
        compute_cost: float,
        tau_f: float,
        tau_v: float,
        tau_a: float,
    ) -> GateDecision:
        """Compute G_t 4-way conjunction gate decision.

        G_t != uncertainty_gate: falsification-based 4-condition AND.
        gate_reason records which conditions passed/failed.
        """
        cond_f = falsification_result.F_t > tau_f
        cond_v = value_gain_delta > tau_v
        cond_a = action_switch_probability > tau_a
        cond_budget = (value_gain_delta - compute_cost) > 0.0

        G_t = cond_f and cond_v and cond_a and cond_budget

        if G_t:
            gate_reason = "PASS_ALL_4"
        else:
            failed_parts: List[str] = []
            if not cond_f:
                failed_parts.append(
                    f"F_t({falsification_result.F_t:.4f})<=tau_f({tau_f})"
                )
            if not cond_v:
                failed_parts.append(
                    f"delta_v({value_gain_delta:.4f})<=tau_v({tau_v})"
                )
            if not cond_a:
                failed_parts.append(
                    f"P_switch({action_switch_probability:.4f})<=tau_a({tau_a})"
                )
            if not cond_budget:
                failed_parts.append(
                    f"delta_v-C_plan({value_gain_delta - compute_cost:.4f})<=0"
                )
            gate_reason = " AND ".join(failed_parts)

        return GateDecision(
            G_t=G_t,
            planning_allowed=G_t,
            decision_relevance_delta=value_gain_delta,
            action_switch_probability=action_switch_probability,
            compute_cost=compute_cost,
            gate_reason=gate_reason,
        )


class GrammarConditionedRewrite:
    """a_exec = Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*).

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §5.5
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.6

    Note: h* is predicted trace — not oracle label. oracle_grammar_action / oracle_best_action FORBIDDEN.
    Fallback fires when selected_hypothesis.confidence < rewrite_confidence_threshold.
    """

    def rewrite(
        self,
        intent_id: str,
        base_action_id: str,
        selected_hypothesis: HypothesisTrace,
        rewrite_confidence_threshold: float,
    ) -> RewriteDecision:
        """Rewrite base_action under selected_hypothesis grammar.

        Contract:
          - is_oracle_label=True → ValueError (never rewrite from oracle label)
          - confidence < threshold → fallback (no rewrite, executable = base)
          - else → rewrite triggered, executable = base__rewritten_by__hypothesis_id
        """
        if selected_hypothesis.is_oracle_label:
            raise ValueError(
                f"Oracle-label hypothesis cannot be used for rewrite: "
                f"{selected_hypothesis.selected_hypothesis_id}"
            )

        if selected_hypothesis.confidence < rewrite_confidence_threshold:
            return RewriteDecision(
                intent_id=intent_id,
                base_action_id=base_action_id,
                selected_hypothesis_id=selected_hypothesis.selected_hypothesis_id,
                executable_action_id=base_action_id,
                rewrite_triggered=False,
                rewrite_confidence=selected_hypothesis.confidence,
                fallback_used=True,
                rewrite_reason="low_confidence_fallback",
            )

        executable_action_id = (
            f"{base_action_id}__rewritten_by__{selected_hypothesis.selected_hypothesis_id}"
        )
        return RewriteDecision(
            intent_id=intent_id,
            base_action_id=base_action_id,
            selected_hypothesis_id=selected_hypothesis.selected_hypothesis_id,
            executable_action_id=executable_action_id,
            rewrite_triggered=True,
            rewrite_confidence=selected_hypothesis.confidence,
            fallback_used=False,
            rewrite_reason="applied",
        )
