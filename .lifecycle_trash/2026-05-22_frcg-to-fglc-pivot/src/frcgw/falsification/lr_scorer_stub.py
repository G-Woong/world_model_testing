"""frcgw.falsification.lr_scorer_stub — Run 3 signature stub.

Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md
Phase: 5 (LR Implementation Contract)
Run: 3 — signature stub only. Implement actual logic in Run 4 (Phase 8).

이 파일은 구현 로직을 포함하지 않는다.
14개 symbol의 타입 서명과 docstring만 정의한다.
실제 F_t / posterior / likelihood / rewrite 계산 로직은 Run 4에서 구현한다.

금지 사항 (Run 3):
- 외부 ML 라이브러리 import (torch, numpy, pandas, sklearn)
- 실제 계산 로직 작성
- hidden label 접근
- FORBIDDEN_AGENT_FIELDS 접근
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# §4. Data Structures — 9개 dataclass
# ---------------------------------------------------------------------------


@dataclass
class EvidenceFeatures:
    """Action-effect evidence extracted from public observations.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §4
    Anti-leakage: 이 dataclass의 모든 필드는 public observed evidence만 포함한다.
    FORBIDDEN: true_control_grammar, true_regime, oracle labels, counterfactual 접근 금지.

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


@dataclass
class HypothesisTrace:
    """Predicted hypothesis trace for the executed action.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §4
    Anti-leakage: selected_hypothesis_id는 model/agent 선택이지 oracle label이 아니다.
    FORBIDDEN: true_control_grammar, true_regime, oracle labels와 혼동 금지.

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
    Note: A_t^H는 alternative hypothesis set이지 alternative action set이 아니다.

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
    Note: exact Bayesian posterior가 아님. learned approximation.
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
    Note: uncertainty threshold 단일 조건이 아님. 4-way conjunction.

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
    Note: h*는 predicted trace이지 oracle label이 아니다.

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
# §5. Component Classes — 5개
# ---------------------------------------------------------------------------


class EvidenceLikelihood:
    """ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h).

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §5.1
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.2 line 152

    Anti-leakage: EvidenceFeatures는 public observed evidence만 사용한다.
    FORBIDDEN: true_control_grammar, oracle labels, counterfactual 접근 금지.

    Failure modes (Run 4 구현 시 처리):
    - no_effect_flag=True: evidence 신호 없음
    - delayed_effect_flag=True: 지연 effect — 즉각 falsification 불가
    - noisy_observation_flag=True: noisy evidence — loglik 신뢰도 하락
    - H_t에 FORBIDDEN_AGENT_FIELDS 포함: LEAKAGE ERROR
    - h가 oracle label일 때: FORBIDDEN
    """

    def score(
        self,
        evidence: EvidenceFeatures,
        hypothesis: HypothesisCandidate,
        history_encoding: Any,
        prev_action: Any,
    ) -> LikelihoodScore:
        """Compute ell_t(h) for a single hypothesis.

        Run 3 stub: 실제 계산 로직은 Run 4 (Phase 8)에서 구현한다.
        """
        raise NotImplementedError(
            "Run 3 signature stub only; implement in Run 4."
        )


class LikelihoodRatioFalsificationScorer:
    """F_t = max_{h_alt in A_t^H} [ell_t(h_alt) - ell_t(h_exec)].

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §5.2
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.3 line 171

    Main LR form (Option B main path). BCE는 main path가 아니라 ABL-022/ABL-023 ablation.
    BCE is comparison/ablation only — not the main falsification method.

    Anti-leakage: h_exec는 predicted trace이지 oracle label이 아니다.
    FORBIDDEN: true_control_grammar, true_regime inference input 금지.

    Failure modes (Run 4 구현 시 처리):
    - h_exec missing: F_t = UNDEFINED → fallback to 0 + BLOCKER 경고
    - H_alt empty: F_t = 0 (no alternative → no falsification)
    - all loglik equal: F_t = 0 → degenerate=True
    - F_t always zero: P3_EVAL BLOCKED 재현 조건 (CRITICAL)
    - F_t always high: always-plan ablation 경계
    - best alt = h_exec: 이론적 불일치 → 경고 로그
    - degenerate likelihood scale: 로그 변환 재확인 필요
    """

    def score(
        self,
        h_exec_trace: HypothesisTrace,
        exec_likelihood: LikelihoodScore,
        alt_likelihoods: List[LikelihoodScore],
        alt_candidates: List[HypothesisCandidate],
    ) -> FalsificationResult:
        """Compute F_t = max_alt(ell_alt) - ell_exec.

        Run 3 stub: 실제 계산 로직은 Run 4 (Phase 8)에서 구현한다.
        BCE variant는 ABL-022/023으로만 사용됨 — 이 method가 main path.
        """
        raise NotImplementedError(
            "Run 3 signature stub only; implement in Run 4."
        )


class PosteriorUpdater:
    """b_t(z^r, z^g) = q_phi(z^r, z^g | H_t) — learned approximation.

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §5.3
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.1 line 142

    Note: exact Bayesian posterior가 아님. learned approximation.
    H_t = history encoder + latent posterior module의 출력.

    Anti-leakage: H_t에는 공개 observation만 포함. true_regime, true_control_grammar 금지.

    Failure modes (Run 4 구현 시 처리):
    - posterior collapse: 단일 hypothesis에 집중 (Locatello impossibility 관련)
    - over-switching: evidence 없이 hypothesis 전환
    - under-switching: strong evidence에도 전환 없음
    - switch without evidence: spurious update → leakage probe 트리거
    - no switch despite strong evidence: F_t 높지만 posterior 고정
    """

    def update(
        self,
        prior_state: PosteriorState,
        evidence: EvidenceFeatures,
        falsification_result: FalsificationResult,
        history_encoding: Any,
    ) -> PosteriorUpdateResult:
        """Update posterior b_t given new evidence.

        Run 3 stub: 실제 계산 로직은 Run 4 (Phase 8)에서 구현한다.
        """
        raise NotImplementedError(
            "Run 3 signature stub only; implement in Run 4."
        )


class DecisionRelevanceGate:
    """G_t = I[F_t > tau_f AND delta_V > tau_v AND P_switch > tau_a AND delta_V - C_plan > 0].

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §5.4
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.5 lines 200-209

    Note: uncertainty > threshold 단일 조건이 아님. 4-way conjunction.
    Note: uncertainty gate (BASE-012)와의 구분이 C6 핵심 claim.

    Failure modes (Run 4 구현 시 처리):
    - G_t always 0 (never fires): tau 너무 높거나 F_t 항상 낮음 → planning_calls=0 재현
    - G_t always 1 (always fires): threshold 너무 낮음 → always-plan (ABL-034) 경계
    - delta_V - C_plan < 0 항상: planning 비용이 항상 이득 초과
    - uncertainty-gate collapse: G_t가 uncertainty gate와 동일 → C6 붕괴
    - false planning call: G_t=1이지만 hypothesis switch 불필요
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
        """Compute G_t gate decision.

        Run 3 stub: 실제 계산 로직은 Run 4 (Phase 8)에서 구현한다.
        G_t != uncertainty_gate: falsification-based 4-way conjunction.
        """
        raise NotImplementedError(
            "Run 3 signature stub only; implement in Run 4."
        )


class GrammarConditionedRewrite:
    """a_exec = Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*).

    Source MD: docs/orchestration/lr_alignment/05_lr_implementation_contract.md §5.5
    Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.6

    Note: h*는 predicted trace이지 oracle label이 아니다.
    Note: rewrite_confidence < tau_r이면 fallback rule 발동.

    Anti-leakage: selected_hypothesis h*는 model 선택. oracle_grammar_action, oracle_best_action 금지.

    Failure modes (Run 4 구현 시 처리):
    - no-op rewrite: a_exec == a_base 항상 → ABL-035와 동일 상태
    - harmful rewrite: precondition_check(a_exec) == INVALID
    - unnecessary rewrite: G_t=0임에도 rewrite 발동
    - fallback never used: rewrite_confidence 항상 >= tau_r
    - fallback always used: rewrite_confidence 항상 < tau_r
    """

    def rewrite(
        self,
        intent_id: str,
        base_action_id: str,
        selected_hypothesis: HypothesisTrace,
        rewrite_confidence_threshold: float,
    ) -> RewriteDecision:
        """Rewrite base_action under selected_hypothesis.

        Run 3 stub: 실제 계산 로직은 Run 4 (Phase 8)에서 구현한다.
        h*는 predicted trace — oracle label 접근 금지.
        """
        raise NotImplementedError(
            "Run 3 signature stub only; implement in Run 4."
        )
