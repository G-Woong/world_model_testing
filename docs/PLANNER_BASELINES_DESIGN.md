# Planner Baselines Design — Session 11-13

> 본 문서는 Ours(FRC-WM)의 비교 대상으로 사용할 **6개 baseline planner**의 설계와 공정 비교 규칙을 닫는다.
>
> **참조:** PART3 §3.22, docs/WM_ARCHITECTURE_DESIGN.md §12, docs/SESSION10_HANDOFF.md §12.

---

## 1. baseline 6종 요약

| # | 이름 | kind (yaml) | 핵심 행동 | 사용 head | 상대적 compute | 목적 |
|---|---|---|---|---|---|---|
| 1 | Reactive | `reactive` | 매 step head-greedy 1-step lookahead | reward, state | 매 step C×1 step | planning 자체의 이득 기준점 |
| 2 | Fixed-k | `fixed_k` | 매 k step마다 horizon planning | reward, done, state | k당 1번 C×H | 단순 주기 baseline |
| 3 | Always-plan | `always_plan` | 매 step horizon planning | 모든 head | 매 step 1번 C×H | "많이 생각하면 무조건 좋은가" |
| 4 | Uncertainty Gate | `uncertainty_gate` | uncertainty > τ 일 때 planning | regime_logits / latent_var / reward | 이벤트 시 1번 C×H | adaptive computation류 |
| 5 | Adaptive Lookahead | `adaptive_lookahead` | uncertainty 따라 horizon/rollouts 조절 | regime_logits / latent_var | low: short H, high: long H | 단순 horizon 적응 |
| 6 | Event-only | `event_only` | reveal/mismatch event 시 planning | reveal_logit, mismatch_logit | 이벤트 시 1번 C×H | "이벤트 감지만으로 충분한가" |

`+ Ours: FRC-WM` (`ours_frc`) — 별도 `FRC_WM_PLANNER_DESIGN.md`.

---

## 2. 각 baseline 상세

### 2.1 ReactivePlanner

**참조:** PART3 §3.22.1.

```python
ReactivePlanner.select_action:
    candidates = enumerate_action_candidates(action_space, horizon=1, action_mask)
    rollout    = adapter.imagine_from_belief(belief, candidates, H=1, S=1)
    score      = adapter.score_rollout(rollout)
    return argmax(score)
```

- **head greedy 1-step lookahead.** rollout=1 candidate × 1 sample × 1 step.
- planning_calls는 매 step 1로 기록되지만 budget이 매우 작다 (보통 16 step/step).
- fallback: action_mask가 모두 0이거나 budget이 음수면 `WAIT`.

**기대:** local cue가 충분하고 drift가 약한 *easy case*에서는 어느 정도 작동. hidden regime / delayed effect가 있는 hard case에서는 약함 (PART3 §3.26.2).

---

### 2.2 FixedKPlanner

**참조:** PART3 §3.22.2.

```python
if step_index % k == 0:
    do_planning(horizon=H, candidates=C, samples=S)
else:
    reactive_1_step()
```

- `baseline.fixed_k_period: 5` (default).
- planning이 *주기적*으로 들어가 compute가 일정. fair comparison의 핵심 baseline.
- cp/reveal/mismatch 신호를 보지 않는다.

**기대:** in-domain에서는 reactive보다 살짝 우위. wrong-hypothesis가 길게 지속되는 OOD에서는 시점 어긋남으로 약함.

---

### 2.3 AlwaysPlanPlanner

**참조:** PART3 §3.22.3.

```python
do_planning(horizon=H, candidates=C, samples=S)   # 매 step
```

- **매 step planning.** compute가 매우 큼.
- success_rate는 일반적으로 가장 높지만 compute_normalized_return에서 손해.
- 본 baseline이 compute frontier에서 dominate하지 않아야 Ours의 reallocation 주장이 성립.

---

### 2.4 UncertaintyGatePlanner

**참조:** PART3 §3.22.4.

uncertainty signal:
- `regime_entropy` (default; no_regime variant이면 fallback)
- `reward_var` — single-step variance proxy (|reward_pred|)
- `latent_var` — `post_std.mean()`
- `done_uncertainty` — bernoulli entropy from done_logit

```python
unc = compute_uncertainty(belief, signal=baseline.uncertainty_signal,
                          fallback=baseline.uncertainty_fallback)
if unc >= baseline.uncertainty_threshold:
    do_planning(...)
else:
    reactive_1_step()
```

- threshold tuning은 *valid에서만* 결정 (yaml에 박아둠). test/OOD에서 다시 튜닝하면 leakage.
- cp/reveal/mismatch는 사용하지 않는다 (별도 variant인 event_only가 사용).

**기대:** uncertainty 높을 때만 planning하므로 compute는 always_plan보다 적다. 단 uncertainty가 높아도 *action이 안 바뀌면* 낭비 (PART2 §3.8.1).

---

### 2.5 AdaptiveLookaheadPlanner

**참조:** PART3 §3.22.7.

```python
unc = compute_uncertainty(belief, signal=...)
if unc >= baseline.adaptive_threshold:
    horizon = baseline.adaptive_high_horizon       # 예: 15
    n_cand  = baseline.adaptive_high_rollouts      # 예: 12
else:
    horizon = baseline.adaptive_low_horizon        # 예: 5
    n_cand  = baseline.adaptive_low_rollouts       # 예: 4
do_planning(horizon=horizon, candidates=n_cand)
```

- 매 step planning은 한다. *얼마나 멀리/많이 보는지*만 조절.
- Ours와 가장 가까운 비교 대상 (PART3 §3.28.4): "더 멀리 볼지"를 조절하지만 "어떤 hypothesis 아래에서 볼지"는 못 바꾼다.
- 차이는 WHPT, action_flip_precision, planning-usefulness ratio에서 드러나야 한다.

---

### 2.6 EventOnlyPlanner

**참조:** PART3 §3.22.6.

```python
reveal_p   = sigmoid(belief.head_outputs["reveal_logit"])     # if available
mismatch_p = sigmoid(belief.head_outputs["raw_eff_mismatch_logit"])  # if available
shift_p    = sigmoid(belief.head_outputs["shift_logit"])       # if available
score = max(over signals in baseline.event_signals)
if score >= baseline.event_threshold:
    do_planning(...)
else:
    reactive_1_step()
```

- `baseline.event_signals: [reveal_prob, mismatch_prob]` (default).
- **change_point head 직접 사용은 별도 variant로 분리** (Ours에서 falsification factor로 사용). event_only는 reveal/mismatch만 본다 → "이벤트 감지만으로 충분한가" 검증.
- abrupt shift에는 강하지만 small cumulative drift에는 취약 (PART3 §3.21.2).

---

## 3. 각 baseline이 사용하는 model head

| Baseline | reward | state | regime | cp | reveal | shift | mismatch |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Reactive | ✓ | ✓ |  |  |  |  |  |
| Fixed-k | ✓ | ✓ |  |  |  |  |  |
| Always-plan | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (only via score 차감) |
| Uncertainty Gate | ✓ | ✓ | ✓ (entropy) |  |  |  |  |
| Adaptive Lookahead | ✓ | ✓ | ✓ (entropy) |  |  |  |  |
| Event-only | ✓ | ✓ |  |  | ✓ | (옵션) | ✓ |
| **Ours (FRC-WM)** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**no_regime variant 위에서:** UncertaintyGate / AdaptiveLookahead의 `regime_entropy` signal이 자동으로 `reward_var` 또는 `latent_var`로 fallback. 이것은 **공정 비교**를 위한 graceful degrade이다 — fallback이 없으면 no_regime에서 baseline이 강제 fail하여 비교 의미가 사라진다.

**no_change_point variant 위에서:** Ours만 `frc.use_change_point=False`로 자동 toggle (cp factor=0). 다른 baseline은 cp head를 안 썼으므로 영향 없음.

---

## 4. 각 baseline의 compute budget 처리

모든 baseline은 동일 `ComputeAccountant`를 공유한다.

| metric | 정의 | accounting |
|---|---|---|
| `planning_calls` | episode 동안 imagine 호출 수 | `record_planning(rollout_steps, n_rollouts)` 호출마다 +1 |
| `imagined_rollouts` | candidate × sample 합 | `+= n_rollouts` |
| `rollout_steps` | imagined 미래 step 수 | `+= rollout_steps` (=C×S×H) |

**budget 한도 적용:**
- `compute_budget_total > 0`이면 episode 누적 한도. 초과 시 `can_plan() → False` → planner는 reactive fallback 또는 WAIT.
- `compute_budget_per_step > 0`이면 step당 한도.
- `max_planning_calls_per_episode > 0`이면 호출 횟수 한도.

**main 평가 default:**
- `horizon=10`, `candidate_action_count=8`, `num_rollouts_per_candidate=1` → planning 1번당 80 step.
- `compute_budget_total=200000` → ≈2500 planning calls 정도까지 허용 (episode 600 step 기준 always_plan 가능).

---

## 5. Ours와의 공정 비교 규칙

**PART3 §3.27 statistical protocol + §7 평가 설계 공정성**:

1. **동일 checkpoint** — 같은 `step_00030000.pt` 위에서 모든 planner를 평가.
2. **동일 env config** — split별 동일 `RG4FConfig`, 동일 seed range.
3. **동일 budget** — `compute_budget_total`을 같은 값으로 고정. always_plan이 한도를 먼저 소진하면 후반부에서 reactive로 강제 fallback.
4. **동일 action space** — 모든 planner가 16 action vocab + action_mask 사용.
5. **Ours만 oracle 사용 금지** — alternative rollout은 latent perturbation만 사용. true_regime 주입 금지.
6. **head 비활성 시 N/A 또는 fallback** — 위 §3 표 참조.
7. **compute-normalized metric 필수** — `compute_normalized_return = return / max(1, rollout_steps)`. raw return만 보면 always_plan이 unfairly winner.
8. **seed별 confidence interval** — main config는 seeds=[0,1,2], OOD config는 seeds=[0,1,2,3,4]. metric은 bootstrap CI 95%.
9. **OOD split별 separately 보고** — aggregate 평균만 보지 말 것.
10. **threshold는 valid에서만** — uncertainty_threshold / event_threshold / Ours의 falsification_threshold는 모두 yaml에 박아둠. test/OOD에서 재튜닝 금지.

---

## 6. yaml entry 예시

```yaml
planners:
  - name: uncertainty_gate
    kind: uncertainty_gate
    planner:                       # PlannerConfig
      horizon: 10
      candidate_action_count: 8
      num_rollouts_per_candidate: 1
      compute_budget_total: 200000
      max_planning_calls_per_episode: 600
      device: auto
      sampling_seed: 0
    baseline:                      # BaselinePlannerConfig
      uncertainty_signal: regime_entropy
      uncertainty_threshold: 0.5
      uncertainty_fallback: reward_var
```

---

## 7. 구현 위치

- `falsifiable_regime_world_model/planner/baselines.py` — 6 baseline class.
- `falsifiable_regime_world_model/planner/policies.py` — `select_reactive_action` (모든 baseline의 fallback).
- `falsifiable_regime_world_model/planner/config.py` — `BaselinePlannerConfig` dataclass.

---

## 8. 본 세션이 *하지 않은* 것

- **Sparse imagination류 baseline (PART3 §3.22.8)** — 일부 state/action 후보만 sample하는 방식. action_subset config를 통해 부분적으로 가능하지만 별도 baseline class로는 두지 않았다. 필요 시 PlannerConfig.action_subset으로 yaml에서 구성 가능.
- **Risk-only gate (PART3 §3.23.5)** — UncertaintyGate의 변형으로 yaml에서 signal=`done_uncertainty`+`mismatch_prob`로 흉내 가능. 별도 class는 두지 않음.
- **No memory ablation (PART3 §3.23.6)** — backbone 자체를 수정해야 하는 ablation으로, 별도 학습 checkpoint 필요. 본 세션 범위 외.
