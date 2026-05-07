"""Scoring: falsification score, action relevance, alternative-hypothesis disagreement.

PART2 §3.7~§3.9 알고리즘을 구현한다.

핵심 신호:
- falsification: current hypothesis가 틀렸을 가능성 (∈ [0, 1]).
  - mismatch_prob, change_point_prob, reveal_prob, regime_entropy, current_vs_alt disagreement
- action_relevance: action 선택이 hypothesis 차이로 갈리는가 (∈ [0, 1]).
  - rollout 기반 candidate별 expected return의 분산 / argmax flip
- compute_alternative_disagreement: current rollout vs alternative rollout 간 차이 진단.

oracle 금지:
- true_regime / true_cp / b_use_label_oracle 등은 절대 input으로 받지 않는다.
- 모델이 추정한 head output (mismatch_logit / cp_logit / regime_logits)만 사용한다.

PART2 §3.7.3: posterior shift만으로 falsification을 정의하면 순환논리가 된다. 본 구현은
recent observation-action evidence (window) 기반 prediction error + cp posterior + alt
disagreement를 결합한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
from torch import Tensor

from .interface import BeliefState, RolloutPrediction


# =============================================================================
# 1. FalsificationContext — recent window 기반 evidence 누적
# =============================================================================


@dataclass
class FalsificationContext:
    """recent W step의 evidence buffer.

    Attributes
    ----------
    window_size       : W
    pred_state_history: 최근 step에서 head가 예측한 state (np.ndarray) list
    pred_reward_history: 최근 head reward 예측 list
    obs_state_history : 실제 env가 보여준 다음 obs의 scalar state portion (=true_state proxy
                        가 아니라 obs의 state portion. obs.scalar[0:5]는 5D 상태값이다.)
    cp_prob_history   : 최근 head cp probability list
    mismatch_prob_history: 최근 head mismatch probability list
    regime_entropy_history: 최근 head regime entropy list
    """

    window_size: int = 5
    pred_state_history: List[np.ndarray] = field(default_factory=list)
    pred_reward_history: List[float] = field(default_factory=list)
    obs_state_history: List[np.ndarray] = field(default_factory=list)
    cp_prob_history: List[float] = field(default_factory=list)
    mismatch_prob_history: List[float] = field(default_factory=list)
    regime_entropy_history: List[float] = field(default_factory=list)
    pred_error_ema: float = 0.0
    ema_alpha: float = 0.3

    def push(
        self,
        *,
        pred_state: Optional[np.ndarray] = None,
        pred_reward: Optional[float] = None,
        obs_state: Optional[np.ndarray] = None,
        cp_prob: Optional[float] = None,
        mismatch_prob: Optional[float] = None,
        regime_entropy: Optional[float] = None,
    ) -> None:
        if pred_state is not None:
            self.pred_state_history.append(np.asarray(pred_state, dtype=np.float32))
        if pred_reward is not None:
            self.pred_reward_history.append(float(pred_reward))
        if obs_state is not None:
            self.obs_state_history.append(np.asarray(obs_state, dtype=np.float32))
        if cp_prob is not None:
            self.cp_prob_history.append(float(cp_prob))
        if mismatch_prob is not None:
            self.mismatch_prob_history.append(float(mismatch_prob))
        if regime_entropy is not None:
            self.regime_entropy_history.append(float(regime_entropy))
        # window trim
        for buf in (
            self.pred_state_history, self.pred_reward_history,
            self.obs_state_history, self.cp_prob_history,
            self.mismatch_prob_history, self.regime_entropy_history,
        ):
            if len(buf) > self.window_size:
                del buf[: len(buf) - self.window_size]
        # EMA prediction error 갱신
        if len(self.pred_state_history) >= 2 and len(self.obs_state_history) >= 1:
            # 이전 step의 예측과 현재 obs state의 거리
            err = float(np.mean(np.abs(self.pred_state_history[-2] - self.obs_state_history[-1])))
            self.pred_error_ema = (1.0 - self.ema_alpha) * self.pred_error_ema + self.ema_alpha * err

    def mean(self, name: str) -> float:
        buf = getattr(self, f"{name}_history", None)
        if not buf:
            return 0.0
        return float(np.mean(buf))


# =============================================================================
# 2. FalsificationResult
# =============================================================================


@dataclass
class FalsificationResult:
    """falsification 결과 묶음.

    Attributes
    ----------
    score : ∈ [0, 1] — 종합 falsification score (가중 평균)
    reason: per-factor diagnostic dict — paper trace에 사용
    """
    score: float = 0.0
    reason: Dict[str, float] = field(default_factory=dict)


# =============================================================================
# 3. compute_falsification_score
# =============================================================================


def _sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-x)))


def _entropy_from_logits(logits: np.ndarray) -> float:
    """categorical entropy (nats)."""
    logits = np.asarray(logits, dtype=np.float64)
    m = logits.max()
    p = np.exp(logits - m)
    p = p / (p.sum() + 1e-12)
    return float(-(p * np.log(p + 1e-12)).sum())


def compute_falsification_score(
    *,
    belief: BeliefState,
    context: FalsificationContext,
    weights: Sequence[float] = (0.30, 0.20, 0.15, 0.20, 0.15),
    cp_logit_threshold: float = 1.26,
    mismatch_logit_threshold: float = -0.30,
    use_change_point: bool = True,
    use_regime: bool = True,
    rollout_disagreement: Optional[float] = None,
) -> FalsificationResult:
    """current hypothesis가 틀렸을 가능성을 점수화.

    weights tuple 순서:
        (change_risk, mismatch_risk, reveal_risk, regime_uncertainty, rollout_disagreement)

    Parameters
    ----------
    belief                  : 현재 belief (head outputs 포함).
    context                 : 최근 window evidence buffer.
    weights                 : 위 5개 factor 가중치. 합이 1일 필요는 없으나 정규화함.
    cp_logit_threshold      : Session 10 진단 best F1 threshold (sigmoid≈0.78). diagnostic용.
    mismatch_logit_threshold: 같은 식으로 valid에서 결정한 값.
    use_change_point        : no_change_point variant이면 False — change_risk = 0.
    use_regime              : no_regime variant이면 False — regime_uncertainty = 0.
    rollout_disagreement    : current vs alternative rollout reward gap (∈ [0, 1] normalized).
                              None이면 0.

    Returns
    -------
    FalsificationResult.
    """
    head = belief.head_outputs

    # 1) change risk
    change_risk = 0.0
    cp_prob = 0.0
    if use_change_point and "change_point_logit" in head:
        cp_logit = float(head["change_point_logit"].item())
        cp_prob = _sigmoid(cp_logit)
        # threshold-shifted: logit이 threshold 이상이면 strong evidence
        change_risk = max(0.0, _sigmoid(cp_logit - float(cp_logit_threshold)))

    # 2) mismatch risk (recent window의 mean mismatch_prob)
    mismatch_risk = 0.0
    mismatch_prob = 0.0
    if "raw_eff_mismatch_logit" in head:
        m_logit = float(head["raw_eff_mismatch_logit"].item())
        mismatch_prob = _sigmoid(m_logit)
        # mismatch는 dense — recent window 평균을 사용
        recent_m = context.mean("mismatch_prob")
        mismatch_risk = max(0.0, _sigmoid(m_logit - float(mismatch_logit_threshold)))
        # window EMA가 더 강한 신호이면 그것도 반영
        mismatch_risk = max(mismatch_risk, float(recent_m))

    # 3) reveal risk (single-step reveal보다 약하게; reveal은 state update 신호)
    reveal_risk = 0.0
    if "reveal_logit" in head:
        rev_prob = _sigmoid(float(head["reveal_logit"].item()))
        # reveal은 falsification에 약하게 기여 (PART1 §3.5: reveal != shift)
        reveal_risk = float(rev_prob)

    # 4) regime uncertainty (entropy of regime_logits)
    regime_unc = 0.0
    if use_regime and "regime_logits" in head:
        regime_logits = head["regime_logits"].detach().cpu().numpy().reshape(-1)
        ent = _entropy_from_logits(regime_logits)
        # max entropy = log(K); normalize
        max_ent = float(np.log(max(2, regime_logits.size)))
        regime_unc = ent / max_ent if max_ent > 0 else 0.0

    # 5) rollout disagreement (current vs alternative)
    disagreement = float(rollout_disagreement) if rollout_disagreement is not None else 0.0

    # weighted average
    w = np.asarray(list(weights) + [0.0] * (5 - len(weights)), dtype=np.float64)[:5]
    w = w / max(1e-12, w.sum())
    factors = np.array([change_risk, mismatch_risk, reveal_risk, regime_unc, disagreement])
    score = float(np.dot(w, factors))
    score = float(np.clip(score, 0.0, 1.0))

    return FalsificationResult(
        score=score,
        reason={
            "change_risk": float(change_risk),
            "mismatch_risk": float(mismatch_risk),
            "reveal_risk": float(reveal_risk),
            "regime_uncertainty": float(regime_unc),
            "rollout_disagreement": float(disagreement),
            "cp_prob": float(cp_prob),
            "mismatch_prob": float(mismatch_prob),
            "pred_error_ema": float(context.pred_error_ema),
        },
    )


# =============================================================================
# 4. ActionRelevanceResult + compute_action_relevance
# =============================================================================


@dataclass
class ActionRelevanceResult:
    """per-candidate action relevance 점수."""
    relevance: np.ndarray         # (C,) normalized ∈ [0,1]
    value: np.ndarray             # (C,) candidate expected return
    risk: np.ndarray              # (C,) candidate-level risk
    info_gain_proxy: np.ndarray   # (C,)
    best_index: int = 0
    flip_from_argmax_current: bool = False
    value_gap: float = 0.0


def compute_action_relevance(
    *,
    rollout_current: RolloutPrediction,
    rollout_alternative: Optional[RolloutPrediction] = None,
    gamma: float = 0.99,
    relevance_value_gap_norm: float = 1.0,
    use_action_flip: bool = True,
) -> ActionRelevanceResult:
    """rollout 기반 candidate value gap / action flip 점수 (PART2 §3.8.3).

    relevance_i = clip( (Q_alt(a_i) - Q_cur(a_i_argmax)) / norm , 0, 1 )

    Parameters
    ----------
    rollout_current     : current hypothesis rollout (C candidate)
    rollout_alternative : alternative hypothesis rollout (같은 candidate set; None이면
                          current만 사용해 max-min gap을 relevance proxy로).
    """
    cur_value = rollout_current.candidate_value(gamma=gamma).detach().cpu().numpy()   # (C,)
    cur_argmax = int(np.argmax(cur_value))
    cur_max = float(cur_value[cur_argmax])

    if rollout_alternative is not None:
        alt_value = rollout_alternative.candidate_value(gamma=gamma).detach().cpu().numpy()
        alt_argmax = int(np.argmax(alt_value))
        alt_max = float(alt_value[alt_argmax])
        # delta_t (PART2 §3.8.3)
        delta = max(0.0, alt_max - cur_max)
        flip = bool(alt_argmax != cur_argmax)
        # per-candidate relevance: alt value 가 current best보다 높을수록 relevance 큼
        rel_raw = np.maximum(alt_value - cur_max, 0.0)
        norm = max(1e-6, float(relevance_value_gap_norm))
        relevance = np.clip(rel_raw / norm, 0.0, 1.0)
        value_for_pick = alt_value if (flip and use_action_flip) else cur_value
        risk = (
            np.std(np.stack([cur_value, alt_value]), axis=0).astype(np.float64)
            if cur_value.shape == alt_value.shape else np.zeros_like(cur_value)
        )
        info_gain = np.abs(alt_value - cur_value) if cur_value.shape == alt_value.shape else np.zeros_like(cur_value)
        best = int(np.argmax(value_for_pick))
        return ActionRelevanceResult(
            relevance=relevance.astype(np.float32),
            value=value_for_pick.astype(np.float32),
            risk=risk.astype(np.float32),
            info_gain_proxy=info_gain.astype(np.float32),
            best_index=best,
            flip_from_argmax_current=flip,
            value_gap=float(delta),
        )

    # alternative 없음 → current candidate 간 spread를 relevance로
    spread = float(np.max(cur_value) - np.min(cur_value))
    norm = max(1e-6, float(relevance_value_gap_norm))
    relevance = np.clip((cur_value - np.min(cur_value)) / max(1e-6, spread), 0.0, 1.0) * (
        min(1.0, spread / norm)
    )
    return ActionRelevanceResult(
        relevance=relevance.astype(np.float32),
        value=cur_value.astype(np.float32),
        risk=np.zeros_like(cur_value, dtype=np.float32),
        info_gain_proxy=np.zeros_like(cur_value, dtype=np.float32),
        best_index=cur_argmax,
        flip_from_argmax_current=False,
        value_gap=spread,
    )


# =============================================================================
# 5. AlternativeRollouts + compute_alternative_disagreement
# =============================================================================


@dataclass
class AlternativeRollouts:
    """current rollout + alternative rollout 묶음."""
    current: RolloutPrediction
    alternatives: List[RolloutPrediction] = field(default_factory=list)


def compute_alternative_disagreement(
    *,
    current: RolloutPrediction,
    alternatives: Sequence[RolloutPrediction],
    gamma: float = 0.99,
    norm: float = 5.0,
) -> Dict[str, float]:
    """current vs alternative rollout 간 disagreement diagnostic.

    Returns
    -------
    dict with keys:
        predicted_reward_gap        : alternative best - current best (clip ≥0) / norm
        predicted_state_disagreement: per-candidate state pred L1 distance mean / 5
        predicted_regime_uncertainty: alternative regime entropy mean (nats / max_ent)
        predicted_change_risk       : alternative cp probability mean
    """
    cur_val = current.candidate_value(gamma=gamma).max().item()
    alt_max = -float("inf")
    state_disagree_list = []
    regime_unc_list = []
    cp_risk_list = []
    for alt in alternatives:
        alt_val = alt.candidate_value(gamma=gamma).max().item()
        if alt_val > alt_max:
            alt_max = alt_val
        # state pred disagreement
        if current.state_pred is not None and alt.state_pred is not None:
            sd = (current.state_pred.detach().cpu() - alt.state_pred.detach().cpu()).abs().mean().item()
            state_disagree_list.append(float(sd))
        # regime entropy of alternative
        if alt.regime_logits is not None:
            r = alt.regime_logits.detach().cpu().numpy()
            r_flat = r.reshape(-1, r.shape[-1])
            entropies = []
            for row in r_flat:
                entropies.append(_entropy_from_logits(row))
            max_ent = float(np.log(max(2, r.shape[-1])))
            regime_unc_list.append(float(np.mean(entropies) / max_ent if max_ent > 0 else 0.0))
        # cp risk of alternative
        if alt.change_point_logit is not None:
            c = torch.sigmoid(alt.change_point_logit).detach().cpu().numpy()
            cp_risk_list.append(float(c.mean()))
    if alt_max == -float("inf"):
        alt_max = cur_val
    gap = max(0.0, alt_max - cur_val)
    out = {
        "predicted_reward_gap": float(np.clip(gap / max(1e-6, float(norm)), 0.0, 1.0)),
        "predicted_state_disagreement": float(np.mean(state_disagree_list)) if state_disagree_list else 0.0,
        "predicted_regime_uncertainty": float(np.mean(regime_unc_list)) if regime_unc_list else 0.0,
        "predicted_change_risk": float(np.mean(cp_risk_list)) if cp_risk_list else 0.0,
    }
    return out


__all__ = [
    "FalsificationContext",
    "FalsificationResult",
    "compute_falsification_score",
    "ActionRelevanceResult",
    "compute_action_relevance",
    "AlternativeRollouts",
    "compute_alternative_disagreement",
]
