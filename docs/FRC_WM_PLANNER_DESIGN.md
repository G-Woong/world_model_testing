# FRC-WM Planner Design — Session 11-13 (Ours)

> 본 문서는 본 논문의 핵심 알고리즘 **FRC-WM (Falsification-driven Regime-Conditioned World Model)** planner의 구현 설계를 닫는다.
>
> **참조:** PART2 §3.7~§3.14, PART3 §3.22~§3.25, docs/PLANNER_INTERFACE_DESIGN.md, docs/PLANNER_BASELINES_DESIGN.md.

---

## 1. 한 줄 요약

> FRC-WM은 매 step **현재 가설이 틀렸을 가능성(falsification)** 을 점수화하고, 그것이 **실제 행동을 바꿀 만큼 중요한지(action relevance)** 판단한 뒤, 그때만 **alternative-regime rollout으로 compute를 재배치**하는 planner다.

낮은 falsification에서는 reactive로 동작 → compute가 거의 안 든다. 높은 falsification + 큰 action relevance에서만 alternative rollout + 큰 horizon으로 reallocation. PART2 §3.9 "compute reallocation" 명제의 직접 구현이다.

---

## 2. 알고리즘 흐름 (코드 1:1)

`FRCWMPlanner.select_action(env_obs, belief, planner_state)` 의 9단계.

```
1) context.push(pred_state, obs_state, cp_prob, mismatch_prob, regime_entropy)
   → recent W=5 step evidence buffer 갱신
2) prelim = compute_falsification_score(belief, context, weights, ...)
   → preliminary F_t (rollout disagreement 없이; cheap)
3) if prelim.score < τ_F:                      # low falsification
       reactive 1-step → return
4) stage 결정:
   - score >= avoid_risk_threshold (0.85) → "extreme"  → horizon=15, n_cand=12
   - score >= extreme_falsification (0.70) → "high"     → horizon=15, n_cand=12
   - else                                       → "medium"  → horizon=5,  n_cand=4
5) candidate generation:
   - first action grid (action_mask 기반) + (필요시) random sampling
6) rollout_cur = adapter.imagine_from_belief(belief, candidates, horizon, ...)
7) if stage in ("high", "extreme"):
       rollout_alt = adapter.imagine_alternative(belief, candidates, horizon, ...,
                                                 latent_perturb_std=0.5,
                                                 regime_topk_index=1)
8) relevance = compute_action_relevance(rollout_cur, rollout_alt, ...)
   disagreement = compute_alternative_disagreement(rollout_cur, [rollout_alt])
   final = compute_falsification_score(..., rollout_disagreement=disagreement[reward_gap])
   → 최종 F_t* (PART2 §3.7 likelihood ratio + cp + disagreement 결합)
9) decision mode 선택:
   - extreme + avoid_mode_enabled                 → "avoid"   (best risk-adjusted action)
   - flip + correct_mode_enabled + mismatch high  → "correct" (state-adjust action)
   - flip + alternative used                       → "plan_alternative"
   - high regime entropy + low value gap + explore → "explore_for_information"
   - budget exhausted + score>0.5 + delay enabled  → "delay"  (WAIT)
   - default                                       → "plan_current"
```

---

## 3. Falsification Score 정의

### 3.1 5-factor weighted aggregation

```python
F_t = (
    w_change       * change_risk         # cp_logit > τ_cp 일 때 sigmoid 점수
  + w_mismatch     * mismatch_risk       # window mean mismatch_prob, max with sigmoid(logit-τ)
  + w_reveal       * reveal_risk         # sigmoid(reveal_logit), 약하게 가중
  + w_regime_unc   * regime_uncertainty  # entropy(regime_logits) / log(K)
  + w_disagreement * rollout_disagreement # current vs alternative reward gap (≥0, normalized)
)
F_t = clip(F_t / sum(weights), 0, 1)
```

기본 weights: `(0.30, 0.20, 0.15, 0.20, 0.15)` (yaml에서 변경 가능).

### 3.2 사용 가능 신호 (PART2 §3.7)

| 신호 | 출처 | 비고 |
|---|---|---|
| change_risk | `change_point_logit` | no_change_point variant이면 0 |
| mismatch_risk | `raw_eff_mismatch_logit` + recent window mean | dense head |
| reveal_risk | `reveal_logit` | reveal-only weight (낮음, PART1 §3.5 reveal != shift) |
| regime_uncertainty | `regime_logits` entropy | no_regime variant이면 0 |
| rollout_disagreement | `compute_alternative_disagreement` | high/extreme stage에서만 계산 |
| recent_pred_error | context.pred_error_ema | 부수 진단 (현재 구현은 reason dict로만 노출) |

### 3.3 금지된 신호 (oracle leakage)

- ground-truth `info["change_point"]` / `info["true_regime"]` / `info["reveal_event"]` / `info["shift_event"]`
- collector metadata: `b_use_label_oracle`, `task_order_str`, `task_budgets`
- 학습용 `target_band` 직접 input (info에 노출되지만 planner는 사용 금지)

→ 본 구현은 위 어느 키도 `select_action`에서 읽지 않는다. info는 trace 기록용으로만 사용 (rollout_runner의 `_summarize_info` 함수만 접근).

### 3.4 reason dict (paper trace 분석용)

```python
final.reason = {
    "change_risk": ..., "mismatch_risk": ..., "reveal_risk": ...,
    "regime_uncertainty": ..., "rollout_disagreement": ...,
    "cp_prob": ..., "mismatch_prob": ..., "pred_error_ema": ...,
}
```

---

## 4. Action Relevance 정의

### 4.1 value gap + action flip (PART2 §3.8.3)

```python
delta = max(0, max(Q_alt) - max(Q_cur))                # value gap
flip  = (argmax(Q_alt) != argmax(Q_cur))               # action flip
relevance_per_candidate = clip((Q_alt - max(Q_cur)) / norm, 0, 1)
```

- `relevance_value_gap_norm: 1.0` (yaml). discounted reward range를 적당히 normalize.
- `relevance_use_action_flip: True`이면 flip이 있을 때 alternative best가 final pick.

### 4.2 alternative가 없을 때

medium stage에서는 alternative rollout을 안 하므로 `compute_action_relevance(..., rollout_alternative=None)` 호출 → current candidate value의 `(max - min) / norm`을 relevance proxy로 사용. paper trace에는 "no alternative" 표시.

### 4.3 reason dict

```python
{
    "action_relevance_max": float,
    "action_relevance_value_gap": float,
    "action_flip": bool,
    "best_index": int,
}
```

---

## 5. Compute Reallocation

### 5.1 stage 결정 룰

| stage | falsification score 범위 | horizon | n_candidates | n_alt_samples | use_alt? |
|---|---|---:|---:|---:|:-:|
| low | < 0.30 (`τ_F`) | 1 | (reactive) | 0 | ✗ |
| medium | 0.30 ~ 0.70 | 5 (`base_horizon`) | 4 (`base_rollouts`) | 0 | ✗ |
| high | 0.70 ~ 0.85 | 15 (`extreme_horizon`) | 12 (`extreme_rollouts`) | 4 | ✓ |
| extreme | ≥ 0.85 (`avoid_risk_threshold`) | 15 | 12 | 4 | ✓ |

### 5.2 PART2 §3.9.4 cell

| `F_t*` | `Δ_t` | 본 구현 동작 |
|:-:|:-:|---|
| low | low | reactive (compute 거의 0) |
| high | low | medium / high stage planning, 단 alternative는 안 굴림 또는 ignore (action 안 바뀌므로 cur best 유지) |
| low | high | medium stage planning만 (alternative 없음). |
| high | high | high/extreme stage + alternative rollout + 행동이 flip되면 plan_alternative / correct mode |

### 5.3 budget exhausted handling

`accountant.can_plan(steps)=False`이면:
- low/medium에서 시도 중이면: reactive fallback → mode="delay" (delay enabled시) 또는 reactive
- alternative rollout 시도 중이면: skip → current rollout만 사용

---

## 6. Alternative Hypothesis Rollout 방식

### 6.1 본 구현 (oracle 없음)

```python
adapter.imagine_alternative(
    belief, candidates,
    horizon=H, n_samples=S, n_candidates=C,
    latent_perturb_std=0.5,        # initial z + N(0, σ²I)
    regime_topk_index=1,            # prior_std *= (1 + 0.5*1) = 1.5
)
```

- **stochastic z perturbation:** 초기 z를 Gaussian noise로 흔들어 alternative posterior에서 sampling한 것처럼.
- **prior_std inflation:** prior_std를 키워 trajectory diversity 유도.

### 6.2 정식 regime conditioning은 미구현 (Session 14+)

학습된 RSSM이 regime을 input으로 받지 않으므로 (regime은 *output head*다), 정식 regime conditioning은 학습 단에서 input embedding을 추가해야 한다. 본 세션은 backbone을 변경하지 않는 원칙(PART0 §1.4)에 따라 latent perturbation으로 대체.

→ Session 14에서 학습 시 regime embedding을 RSSM input에 추가한 backbone variant를 학습하면, `imagine_alternative`에 regime_index 인자를 받아 정식 conditioning으로 교체 가능. 그 변경은 본 인터페이스 (`adapter.imagine_alternative` signature)와 backward-compatible.

---

## 7. Decision Modes

PART2 §3.11~§3.14 (adaptation/correction + adaptation modes).

| mode | 의미 | 트리거 조건 | action 결정 |
|---|---|---|---|
| `reactive` | 현재 정책으로 행동 | `prelim < τ_F` | head-greedy 1-step |
| `plan_current` | 현재 가설로 horizon planning | medium stage, alt 미사용 | argmax(score_rollout(rollout_cur)) |
| `plan_alternative` | alternative 가설까지 비교 | high/extreme + flip | argmax(rollout_alt value if flip) |
| `correct` | 기존 가설 틀렸다 보고 행동 수정 | flip + mismatch_risk > 0.5 | state-adjust action (priority: drift, interaction, mobility) |
| `avoid` | 위험 행동 회피 | extreme stage | best risk-adjusted action (value − risk) |
| `delay` | 정보 부족 → 안전한 지연 | budget exhausted + score > 0.5 | `Action.WAIT` (15) |
| `explore_for_information` | 정보 얻기 위한 행동 | high regime entropy + low value gap | argmax(rollout_alt) (info-gain proxy) |

각 mode는 trace의 `step.decision_mode`로 기록되어 사후 분석 가능.

---

## 8. Wrong-Hypothesis Persistence Metric

PART3 §3.25.10 정의에 1:1 대응.

```python
# rollout_runner._summarize_info에서 info["true_regime"]["control_mode"] 기록
# compute_episode_metrics에서:
for s in trace.steps:
    pred_regime = s.head_pred_summary["regime_argmax"]
    true_regime = s.info_summary["true_regime"]["control_mode"]
    if pred_regime != true_regime:
        whp += 1
result.wrong_hypothesis_persistence = whp
```

추가:
```python
# recovery_delay_after_change:
on info["change_point"] = True:
    last_change_step = step
    wait until (pred_regime == true_regime):
        recovery_delays.append(step - last_change_step)
result.recovery_delay_after_change = mean(recovery_delays)  # NaN if no recovery observed
```

**Ours가 paper-main 우위를 보여야 하는 metric:**
- `wrong_hypothesis_persistence_mean` ↓
- `recovery_delay_after_change_mean` ↓
- `action_flip_rate` (FRC가 alternative로 flip한 비율) ↑ (단 false positive는 ↓)
- `false_planning_call_rate` ↓
- `compute_normalized_return` ↑

---

## 9. NeurIPS Claim Connection

| Claim (paper-main) | 본 구현이 검증 가능 | 핵심 metric |
|---|---|---|
| C1. wrong-hypothesis persistence가 실제 closed-loop 비용을 만든다 | ✓ | WHPT mean × episode_return 상관 |
| C2. falsification + action relevance 결합이 단순 uncertainty gate보다 우월 | ✓ | Ours vs uncertainty_gate compute_normalized_return |
| C3. compute reallocation이 amount 증가보다 효율적 | ✓ | Ours rollout_steps_mean < always_plan AND Ours return_mean ≥ always_plan |
| C4. regime supervision (full vs no_regime)이 mismatch / WHPT에 결정적 | ✓ | Ours×full vs Ours×no_regime |
| C5. cp head는 자체 ablation보다 planner falsification gate signal로 작동 | ✓ | Ours×full vs Ours×no_change_point의 small drift OOD |
| C6. small drift OOD에서 event_only가 약함, Ours는 robust | ✓ | ood_param_shift split의 Ours vs event_only |
| C7. adaptive_lookahead와 차이는 horizon 조절이 아니라 hypothesis switch | ✓ | Ours vs adaptive_lookahead의 action_flip_rate, WHPT |

---

## 10. Known Limitations

### 10.1 backbone 변경 없음

- regime conditioning이 input이 아니므로 alternative rollout이 latent perturbation으로 모의된다. 이는 *완벽한 alternative regime simulation*이 아니라 *self-consistent stochastic alternative*다. 정식 conditioning은 Session 14+ backbone 학습 시 추가 가능.

### 10.2 single-factor regime supervision

- 학습 단계에서 `regime_head`가 control_mode 5 class만 감독한다 (`RegimeConfig.multi_factor=False`). vision/mobility/interaction/noise별 factorized regime은 미구현. Ours는 그래도 작동하지만 "factor recombination OOD" (PART3 §3.24.2)에서 monolithic regime의 약점을 그대로 가짐.

### 10.3 cp threshold tuning

- yaml의 `cp_logit_threshold=1.26`은 Session 10 진단에서 **valid** split의 best F1로 결정한 값. test/OOD에서 다시 튜닝하면 leakage이므로 본 yaml에 박아두었다. 단 이 threshold가 여러 OOD에서 동일하게 잘 작동한다는 보장은 없다 — 결과가 OOD에서 약하면 paper에서 "threshold transferability is limited"로 정직하게 보고해야 한다.

### 10.4 Q-value head 부재

- value head가 없으므로 candidate "value"는 reward sum × done masking으로 근사. PART2 §3.8.3의 `Q(s, r, a)`보다 약한 근사. 결과가 약하면 Session 14에서 value head를 추가 학습하는 것이 자연스러운 다음 단계.

### 10.5 soft-to-hard threshold annealing 미적용

- PART2 §3.13.2: 학습 초기 collapse 방지를 위한 soft allocation. 본 평가에서는 frozen checkpoint이고 hard threshold만 사용한다. 평가 시점이라 annealing이 필요 없지만, *Ours가 학습-시 allocator collapse 때문에 약하다는 가능성*은 본 평가로 검증할 수 없음.

### 10.6 OOD environment 변형 단순화

- `_build_env_config_for_split`은 `ood_param_shift`만 자동 (drift / shift × 2). 다른 OOD (room_perm / factor_recomb / obs_shift / field_placement)는 dataset generator의 split policy를 정확히 재현하지 못한다 (RG4FConfig override만 가능). 따라서 결과는 generator splits의 *근사*이며 절대 비교는 dataset 기반 evaluator (Session 14)에서 한다.

---

## 11. yaml entry 예시

```yaml
- name: ours_frc
  kind: ours_frc
  planner:
    horizon: 10
    candidate_action_count: 8
    num_rollouts_per_candidate: 1
    max_planning_calls_per_episode: 600
    compute_budget_total: 200000
    enable_alternative_rollout: true
    num_alternative_samples: 4
    alt_latent_perturb_std: 0.5
    alt_regime_topk: 2
    device: auto
    sampling_seed: 0
  frc:
    falsification_threshold: 0.30          # τ_F
    cp_logit_threshold: 1.26                # Session 10 valid best F1 logit
    mismatch_logit_threshold: -0.30
    reveal_logit_threshold: -0.77
    falsification_window: 5
    relevance_threshold: 0.10
    relevance_use_action_flip: true
    relevance_value_gap_norm: 1.0
    base_horizon: 5
    extreme_horizon: 15
    base_rollouts: 4
    extreme_rollouts: 12
    extreme_falsification: 0.70
    avoid_risk_threshold: 0.85
    enable_correct_mode: true
    enable_avoid_mode: true
    enable_delay_mode: true
    enable_explore_mode: true
```

---

## 12. 본 세션이 *하지 않은* 것

- 정식 regime conditioning (backbone 변경)
- value head 추가 (학습 변경)
- soft-to-hard threshold annealing (eval에서 불필요)
- monolithic vs factorized regime 학습 ablation
- dataset 기반 evaluator (Session 14+)
- multi-step lookahead의 candidate beam search (단순 first-action grid + random tail로 충분)
- explanation faithfulness intervention (PART3 §3.25.13) — 별도 평가 script
