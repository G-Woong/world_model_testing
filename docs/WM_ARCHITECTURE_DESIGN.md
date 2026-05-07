# WM Architecture Design — RSSM/Dreamer-style Backbone for Wrong-Hypothesis-Aware Planning

> **Session 7 산출물.** 본 문서는 RG-4F 환경의 NeurIPS 2026 메인트랙 실험에서 사용할 world model의 backbone, head, loss, variant, forward/imagine API, 학습 sampler 요구사항, 데이터셋 사용 원칙을 모두 닫는다. 본 문서는 **architecture novelty를 주장하지 않는다.** 본 backbone은 *wrong-hypothesis-aware planning* 메커니즘 검증을 위한 **controlled backbone**이다 (PART0 §1.1–1.4).
>
> Session 7은 코드 골격 + config + 본 문서까지만 만든다. training loop / dataset loader / planner / evaluator는 일절 만들지 않는다.

---

## 1. 논문 contribution과 backbone 역할 분리

### 1.1 본 논문 contribution

본 논문의 novelty는 다음 메커니즘 묶음이다 (PART1 §3.1, PART2 §3.7~§3.14, PART0 §1.1).

- hidden state / hidden regime / change-point의 명시적 분리
- reveal vs shift 구분
- current vs alternative regime hypothesis 비교
- falsification score (likelihood ratio + change-point posterior)
- action relevance (value gap / action flip)
- compute *re*allocation (current rollout → alternative rollout)
- control-drift와 mobility의 분리 (이산 remap/약한 miscontrol vs latency/cooldown)
- adaptation vs correction의 cost-sensitive 선택
- default utility + local override (target band)
- sparse invisible field coupling
- small drift / abrupt shift의 동시 처리
- wrong-hypothesis persistence time(WHPT) 감소

### 1.2 backbone의 역할 (NOT contribution)

본 패키지(`falsifiable_regime_world_model.wm`)가 만드는 RSSM/Dreamer-style backbone은 위 메커니즘이 작동할 수 있는 **공통 표준 기반**이다. 다음 조건을 반드시 만족해야 한다.

1. 모든 baseline / ablation은 본 backbone을 **동일 capacity / 동일 hyperparameter / 동일 학습 schedule** 로 공유한다 (PART0 §1.4 same-capacity 원칙).
2. backbone은 어떤 mechanism도 직접 박지 않는다. 모든 mechanism은 head + loss + planner(Session 11+) 위에 얹힌다.
3. 본 backbone은 SOTA backbone 코드(DreamerV3 등)의 복붙이 아니다 (PART0 §3.1, §3.2).
4. variant ablation은 head/loss를 끄는 방식이며, backbone capacity는 변하지 않는다.

> 따라서 본 문서는 “더 강한 RSSM을 만드는 방법”을 다루지 않는다. 본 문서는 “표준 RSSM 위에 wrong-hypothesis-aware mechanism을 검증할 수 있는 supervision 구조와 forward/imagine 인터페이스를 만드는 방법”을 다룬다.

---

## 2. 데이터셋 사용 원칙

### 2.1 두 학습 dataset

| dataset | 역할 | behavior policy | 학습 사용 split |
| --- | --- | --- | --- |
| `data/rg4f_random_2000` | broad dynamics / 실패 / 방황 / control-drift / cooldown / field drift | `random_biased` | `train`, `valid`만 |
| `data/rg4f_success_curriculum_v5_2000` | rare success / near-success / reward / value / action-relevance 보강 | `task_success_curriculum` (weak-oracle scripted) | `train`, `valid`만 |

### 2.2 왜 두 dataset을 둘 다 쓰는가

- **`random_2000`**: PART2 §3.10의 control-drift remap, mobility cooldown, invisible field drift, sparse coupling을 broad하게 노출시키기 위해 필요하다. truncated_rate ≈ 1.0이고 task success는 ≤ 3% 수준으로 매우 낮지만, reveal/change_point/shift event signal은 보존된다 (`reveal_mean ≈ 84/episode`, `change_point_mean ≈ 1.05/episode`). reward는 거의 step_cost+latency 누적이라 reward head가 cost 분해를 학습할 수 있다.
- **`success_curriculum_v5_2000`**: reward / done / state / regime supervision을 쓸만한 trajectory가 없는 random_2000을 보완한다. all_tasks_completed_rate ≈ 9.5% 수준의 success/near-success episode가 보존되어 있으며, task_order_entropy ≈ 4.4(이론 max log2(24)≈4.58) / most_common_task_order_ratio ≈ 0.14로 fixed-order bias가 제거되어 있다.

### 2.3 학습 금지 사항

- **test_id / OOD split은 학습 input으로 절대 사용 금지** (모든 OOD는 평가 전용).
- **outputs/*_stats** 폴더는 통계 확인용이며 학습 input이 아니다.
- success curriculum은 weak-oracle scripted collector로 만든 학습 보강 데이터다. **collector success rate를 agent 성능으로 인용 금지**.
- 평가는 본 패키지의 학습 후 별도 evaluator(Session 14+)가 oracle 없이 test_id/OOD에서 직접 rollout한다.

### 2.4 stage mix (Session 9가 채울 placeholder)

| Stage | 구성 | 목적 |
| --- | --- | --- |
| 1 — dynamics warmup | random_2000 100% | state transition / control-drift / mobility cooldown / field broad coverage |
| 2 — mixed WM training | random_2000 50% + success_curriculum_v5_2000 50% | reveal / interaction / near-success 혼합 |
| 3 — value/action-relevance emphasis | random_2000 30% + success_curriculum_v5_2000 70% | reward / done / regime / change_point 강화 |

> 비율은 초기 제안이다. 최종은 Session 9에서 ablation으로 결정한다.

---

## 3. 입력 / 학습 target / 평가-only metadata 표

| 분류 | 키 | 본 패키지에서 어떻게 쓰는가 | 절대 위반 |
| --- | --- | --- | --- |
| **모델 입력 (forward에 들어감)** | `local_grid` (B,T,5,5,10) float | encoder CNN | 변경 시 schema 깨짐 |
| | `scalar` (B,T,14) float | encoder MLP | obs scalar dim 14 고정 |
| | `event_token` (B,T) long | encoder embedding (vocab=13) | EventToken enum 고정 |
| | `action_raw` (B,T) long | RSSM GRU 입력 (한 step shift) | vocab=16 고정 |
| | `action_prev_raw` (B,T) long, optional | a_{t-1} 명시적 alignment | 미제공 시 자동 shift |
| **학습 target (loss target)** | `obs_local_target`, `obs_scalar_target` | 보통 = 다음 step 또는 현재 step obs (Session 8 결정) | encoder 입력으로 동시 사용 안 함 |
| | `reward` (B,T) | reward_head MSE | task+cost decomposed reward |
| | `done` (B,T) | done_head BCE | terminated || truncated |
| | `true_state` (B,T,5) | state_head MSE | 5D 상태 regression |
| | `true_regime_control_mode` (B,T) long | regime_head CE (5 class) | 현재는 control_mode만 supervised |
| | `change_point` (B,T) | change_point_head BCE+pos_weight (+focal) | tick-level 희소 |
| | `reveal_event` (B,T) | reveal_head BCE | event-rich |
| | `shift_event` (B,T) | shift_head BCE+pos_weight (+focal) | change_point와 분리 기록 |
| | `raw_eff_mismatch` (B,T) = (action_raw ≠ action_effective) | mismatch_head BCE | control-drift auxiliary |
| **평가/감사-only (입력/target 모두 금지)** | `collector_metadata`, `collector_mode`, `task_order_str`, `task_order_planned`, `b_use_label_oracle`, `privilege_level`, `task_attempt_ticks`, `task_timeout`, `task_retry_count`, `task_budgets`, `forced_permutation` (raw), `target_band_center`, `stele_positive_k`, `piece_weight_j`, `permutation_id` 등 | dataset 감사 / 분석 metadata | 모델 input/target에 절대 들어가면 안 됨 (oracle leak) |

> `true_regime`, `change_point`, `reveal_event`, `shift_event`, `true_state`는 supervised target으로는 사용 가능하다. **그러나 planner/evaluation 입력으로 직접 제공하면 안 된다** (PART2 §3.7 falsification은 모델이 추정해야 하는 latent다).

---

## 4. RSSM / Dreamer-style architecture diagram (text)

```
            ┌─────────────────── observation o_t = (local_grid, scalar, event_token) ───────────────────┐
            │                                                                                          │
            │   CNN(local_grid)        MLP(scalar)        EmbeddingLookup(event_token)                 │
            │        │                       │                       │                                 │
            │        └────────► concat ◄─────┘                       │                                 │
            │                       │                                │                                 │
            │                       ▼                                ▼                                 │
            │              fuse-MLP → e_t (B, T, F=feature_dim)  (encoder.feature_dim)                 │
            └─────────────────────────────┬─────────────────────────────────────────────────────────────┘
                                          │
              ┌── prev z_{t-1} (stoch_dim) ─┴── prev action_emb (a_{t-1}) ──┐
              │                                                            │
              ▼                                                            ▼
              ┌────────── input-proj MLP (z_{t-1}, action_emb) ───────────┐
              │                                                            │
              ▼                                                            │
              GRUCell ── h_{t-1} ───────────────────────────────────► h_t  │
                                                                           │
                                  prior      p(z_t | h_t)  ◄─ PriorMLP(h_t)
                                  posterior  q(z_t | h_t, e_t) ◄─ PostMLP([h_t, e_t])
                                                                           │
                                                                           ▼
                                                              z_t ~ q (학습) | p (imagine)
                                                                           │
                                                                           ▼
                                                features = concat(h_t, z_t) ∈ R^{deter+stoch}
                                                                           │
                                ┌──────┬──────┬──────┬──────┬──────┬──────┴──────┬──────┬──────┐
                                ▼      ▼      ▼      ▼      ▼      ▼             ▼      ▼      ▼
                          obs_recon  reward  done  state  regime  change_pt  reveal  shift  mismatch
                            (CNN/      (1)    (1)   (5)    (5)      (1)        (1)     (1)    (1)
                            MLP dec)
                                       Optional: action_relevance_proxy(1)
```

- batch-first (B, T, ...) 형식.
- `feature_dim = deter_dim + stoch_dim` 가 모든 head의 공통 입력 차원이다.
- prior/posterior 모두 diagonal Gaussian. KL은 Dreamer 방식 (free nats + KL balancing).
- imagine rollout은 posterior를 사용하지 않고 prior만 사용한다.

---

## 5. latent h_t / z_t / 목적

| 변수 | 의미 | 차원 (debug / medium) |
| --- | --- | --- |
| `h_t` | deterministic recurrent state. 과거 belief의 누적. | 256 / 512 |
| `z_t` | stochastic latent. 현재 step의 새로운 정보를 흡수 (posterior) 또는 prior에서 sampling. | 64 / 128 |
| `features` = concat(h, z) | 모든 head의 공통 입력. | 320 / 640 |

`h_t`는 GRUCell로 계산된다: `h_t = GRU(h_{t-1}, input_proj([z_{t-1}, action_emb_{t-1}]))`. 입력에 action embedding을 함께 넣는 것은 PART2 §3.10의 control-drift hypothesis 비교에서 **같은 z_{t-1}이라도 다른 action에서 다른 transition을 만들어야 함**을 학습 signal로 노출시키기 위함이다.

---

## 6. heads 목록

| head | 출력 shape | loss | 비고 |
| --- | --- | --- | --- |
| obs_recon_local | (B, T, 5, 5, 10) | MSE | small map이라 transposed-conv 대신 fully-connected decoder |
| obs_recon_scalar | (B, T, 14) | MSE | scalar reconstruction |
| reward | (B, T) | MSE | task+cost decomposed reward 예측 |
| done | (B, T) | BCE-with-logits | terminated || truncated |
| state | (B, T, 5) | MSE | 5D true_state regression |
| regime | (B, T, R=5) | CE | control_mode 5-class (`IDENTITY/CW/LR/UD/REV`) |
| change_point | (B, T) | BCE + pos_weight + (옵션) focal | tick-level 희소 → λ=5.0, pos_weight=50 |
| reveal | (B, T) | BCE | reveal_mean 풍부 → 별도 weighting 없음 |
| shift | (B, T) | BCE + pos_weight + (옵션) focal | change_point와 분리 기록 |
| raw_eff_mismatch | (B, T) | BCE | `action_raw ≠ action_effective` (control-drift auxiliary) |
| **action_relevance_proxy** (optional, default off) | (B, T) | MSE | supervised proxy 수준만. 실제 action relevance는 Session 13의 rollout-based value gap / action flip이 담당. |

> regime는 현재 *single factor (control_mode)* 만 supervised한다. multi-factor regime (vision/mobility/interaction/noise/control)은 Session 8 후보 (코드 변경 없이 `RegimeConfig.multi_factor=True` 옵션 + 추가 head로 확장 가능).

---

## 7. loss decomposition

```
L_total =
   λ_obs_local    · L_obs_local         (MSE)
 + λ_obs_scalar   · L_obs_scalar         (MSE)
 + λ_reward       · L_reward             (MSE)
 + λ_done         · L_done               (BCE-with-logits)
 + λ_state        · L_state              (MSE on 5D)
 + λ_regime       · L_regime             (CE on 5 classes)
 + λ_change_point · L_change_point        (BCE + pos_weight + optional focal)
 + λ_reveal       · L_reveal              (BCE)
 + λ_shift        · L_shift               (BCE + pos_weight + optional focal)
 + λ_mismatch     · L_mismatch            (BCE)
 + β              · L_KL  (free nats + KL balancing, Dreamer-style)
```

**KL loss** (`losses.kl_loss_dreamer`):
```
KL_total = kl_balance · KL(stop_grad(q) || p) + (1 − kl_balance) · KL(q || stop_grad(p))
KL_per_step ← clamp_min(KL_per_step.sum(stoch_dim), free_nats)
```
- `kl_balance = 0.8` (DreamerV3 표준값).
- `free_nats = 1.0`.
- `β = 1.0` (medium 기준).

각 component는 `WMLossOutput.components`로 분해 보고된다 (Session 9 logging이 사용).

---

## 8. change-point imbalance 대응 설계

### 8.1 데이터 분포 사실

| split | dataset | change_point_mean (per ep) | tick-level positive rate |
| --- | --- | ---: | ---: |
| ID train | random_2000 | ≈ 1.05 | ≈ 0.052% |
| ID train | success_v5_2000 | ≈ 0.92 | ≈ 0.049% (epi len ≈ 1900) |
| ood_param_shift | random_2000 | ≈ 2.00 | ≈ 0.10% |
| ood_param_shift | success_v5_2000 | ≈ 1.75 | ≈ 0.09% |

### 8.2 본 세션이 head/loss 단에서 처리하는 것

- `cp_pos_weight=50.0`, `shift_pos_weight=50.0`: BCE의 양성 가중치.
- `cp_use_focal=True` (medium config): `(1 − p_t)^γ`로 modulation. γ=2.0.
- `λ_change_point = λ_shift = 5.0`: 다른 head 대비 ×5 가중.
- `change_point` / `shift`는 **분리 head로 별도 기록**한다 (수치적으로 유사하지만 의미가 다름; PART1 §3.5 reveal-vs-shift).

### 8.3 본 세션이 처리하지 않는 것 (Session 8로 위임)

- **event-window sampling**: change_point=1 또는 shift=1 step 주변 ±k window를 oversample. 본 모듈의 `compute_total_loss`는 `sample_weight: (B, T) float`을 받을 수 있도록 인터페이스가 열려 있다. Session 8의 sampler가 weight tensor를 만들어 넘기면 된다.
- **multi-step prediction** (∃ change_point in ±k window): single-step 대신 window 안에서 한 번이라도 발생하면 1로 라벨링 — Session 8의 dataset target 변환에서 처리.
- **negative oversampling** (정상 step도 충분히 보장): Session 8.

---

## 9. model variants / ablation plan

### 9.1 학습 variant (checkpoint를 새로 만들어야 함)

| variant | regime | change_point | reveal | shift | state | 의미 |
| --- | :-: | :-: | :-: | :-: | :-: | --- |
| `full_model` | ✅ | ✅ | ✅ | ✅ | ✅ | 메인 모델 |
| `no_regime` | ❌ | ✅ | ✅ | ✅ | ✅ | regime head/loss 제거 (PART3 §3.23.1) |
| `no_change_point` | ✅ | ❌ | ✅ | ✅ | ✅ | change_point head/loss 제거 (PART3 §3.23.2) |
| `no_reveal` (optional) | ✅ | ✅ | ❌ | ✅ | ✅ | reveal head/loss 제거 |
| `no_state_aux` (optional) | ✅ | ✅ | ✅ | ✅ | ❌ | 5D state auxiliary 제거 |

> **backbone capacity는 모든 variant에서 동일** (PART0 §1.4). variant는 head/loss만 끈다.

### 9.2 학습 variant가 *아닌* 것 (동일 checkpoint 재사용)

다음은 *evaluation-time planner / allocator swap* 으로 처리하며 본 패키지에서 새 checkpoint를 만들지 않는다. checkpoint 폭증을 피하기 위함.

- Reactive policy (PART3 §3.22.1)
- Fixed-k planner (§3.22.2)
- Always-plan (§3.22.3)
- Uncertainty gate (§3.22.4)
- Novelty-style mismatch gate (§3.22.5)
- Event-only gate (§3.22.6)
- Adaptive lookahead (§3.22.7)
- No action relevance / action relevance only (§3.22.9)
- Risk-only gate (§3.23.5)
- No adaptation/correction distinction (§3.23.9)

> 이 baseline들은 `RSSMWorldModel.imagine` + `predict_heads` 위에서 swappable allocator/planner를 만들어 평가한다 (Session 11+).

---

## 10. forward API contract (절대 변경 금지)

### 10.1 `RSSMWorldModel.forward(batch, initial_state=None)`

input batch:

```python
batch = {
    "local_grid":  Tensor[B, T, 5, 5, 10] float32,
    "scalar":      Tensor[B, T, 14]       float32,
    "event_token": Tensor[B, T]           long,    # 0..12
    "action_raw":  Tensor[B, T]           long,    # 0..15
    # optional:
    "action_prev_raw": Tensor[B, T] long,           # a_{t-1} 명시; 없으면 자동 shift
}
```

output dict (key contract; Session 9 training step / Session 11 planner와 정확히 일치해야 함):

```python
out = {
    # RSSM
    "h":          Tensor[B, T, deter_dim],
    "z":          Tensor[B, T, stoch_dim],
    "prior_mean": Tensor[B, T, stoch_dim],
    "prior_std":  Tensor[B, T, stoch_dim],
    "post_mean":  Tensor[B, T, stoch_dim],
    "post_std":   Tensor[B, T, stoch_dim],

    # Heads (해당 head가 ON일 때만)
    "obs_local_pred":         Tensor[B, T, 5, 5, 10],
    "obs_scalar_pred":        Tensor[B, T, 14],
    "reward_pred":            Tensor[B, T],
    "done_logit":             Tensor[B, T],
    "state_pred":             Tensor[B, T, 5],
    "regime_logits":          Tensor[B, T, 5],
    "change_point_logit":     Tensor[B, T],
    "reveal_logit":           Tensor[B, T],
    "shift_logit":            Tensor[B, T],
    "raw_eff_mismatch_logit": Tensor[B, T],
    # optional:
    "action_rel_proxy_pred":  Tensor[B, T],
}
```

### 10.2 `compute_total_loss(forward_out, target, cfg.loss, sample_weight=None)`

target dict의 key 이름 (Session 8 loader가 만든다):

```python
target = {
    "obs_local_target":  Tensor[B, T, 5, 5, 10] float32,
    "obs_scalar_target": Tensor[B, T, 14]       float32,
    "reward":            Tensor[B, T]           float32,
    "done":              Tensor[B, T]           float32 or bool,
    "true_state":        Tensor[B, T, 5]        float32,
    "true_regime_control_mode": Tensor[B, T]    long (0..4),
    "change_point":      Tensor[B, T]           float32 or bool,
    "reveal_event":      Tensor[B, T]           float32 or bool,
    "shift_event":       Tensor[B, T]           float32 or bool,
    "raw_eff_mismatch":  Tensor[B, T]           float32 or bool,
}
```

`sample_weight: Tensor[B, T] float`은 (a) padding mask, (b) event-window oversampling weight, (c) chunk overlap mask 등을 종합하여 Session 8이 생성한다.

---

## 11. planner imagine API stub 설계

### 11.1 현재 (Session 7) stub

`RSSMWorldModel.imagine(action_sequence_raw, initial_state)`은 다음을 반환한다.

```python
{
    "h":  Tensor[B, H, deter_dim],
    "z":  Tensor[B, H, stoch_dim],
    + heads (WMHeads.forward와 동일 key 구조)
}
```

- prior-only rollout (single hypothesis). encoder 호출 없음.
- alternative regime conditioning은 *없음* — Session 7은 인터페이스만 둔다.

### 11.2 Session 11에서 확장할 항목

- `imagine(action_seq, initial_state, regime_hypothesis=None)`: regime hypothesis embedding을 받아 prior conditioning에 주입.
- current vs alternative rollout 비교: `imagine_current` / `imagine_alternative` 두 호출의 reward / done / state / regime 예측을 비교.
- value head 또는 action relevance head 추가: 현재는 `action_relevance_proxy`만 supervised proxy로 두었음. 실제 rollout 기반 value gap / action flip은 Session 13.

---

## 12. baseline / checkpoint 학습 수 최소화 전략

PART3 §3.22, §3.23은 다음 baseline / ablation을 요구한다.

- §3.22: Reactive / Fixed-k / Always-plan / Uncertainty gate / Novelty gate / Event-only gate / Adaptive lookahead / Sparse imagination 류 / FRC-WM full + 변형들
- §3.23: no regime / no change-point / raw mismatch only / no action relevance / risk-only gate / no memory / monolithic regime / no faithfulness / no adaptation-correction / no sparse coupling

만약 모든 baseline을 별도로 학습하면 checkpoint 수가 폭발한다. 본 backbone은 다음 전략으로 학습 checkpoint 수를 최소화한다.

| 그룹 | 학습 checkpoint | 비고 |
| --- | --- | --- |
| **WM 학습 variant** (§9.1) | 5개 (full / no_regime / no_change_point / no_reveal / no_state_aux) | 같은 capacity, head/loss만 다름 |
| **Planner / allocator baseline** | 0개 (full_model 위에서 evaluation swap) | Reactive / Fixed-k / Always-plan / Uncertainty gate / Novelty gate / Event-only / Adaptive lookahead / no_action_relevance / risk-only / always-correct / always-adapt |
| **Backbone-level ablation** | 추가 학습 가능 (선택) | no memory (memory size 0), monolithic regime (head=monolithic single class), no sparse coupling (이건 환경이 만들어야 함; 학습 변수 아님) |

> 메인 실험에서는 **WM 학습 5 variant** + **planner-side baseline 다수**로 reviewer defense (PART3 §3.28)를 닫는다. Session 9가 학습 schedule을 5 variant에 맞게 만든다.

---

## 13. weak-oracle collector 관련 주의점

`success_curriculum_v5_2000`은 weak-oracle scripted collector (`task_success_curriculum`)로 만들어진 dataset이다 (SUCCESS_CURRICULUM_V5_AUDIT_REPORT §4.1). 다음 주의점을 본 backbone은 코드 레벨에서 강제한다.

- `collector_metadata.collector_mode`, `task_order_str`, `task_order_planned`, `task_attempt_ticks`, `task_timeout`, `task_retry_count`, `task_budgets`, `privilege_level`, `b_use_label_oracle`은 **모델 입력 / 학습 target / planner 입력 어디에도 들어가지 않는다.** 본 패키지의 forward batch는 위 키를 받지 않는다 (오타로 들어와도 `batch[...]` 접근에서 KeyError 발생).
- `episode_meta.json`의 정적 metadata (`permutation`, `field_info_static`, `forced_permutation`)은 평가/감사용이며 학습 input이 아니다.
- collector의 success rate는 dataset의 신호 분포일 뿐 agent 성능이 아니다 (PART0 §3.7).

---

## 14. Session 8 — Loader / Sampler 요구사항 (이번 세션에서 미구현, 본 표가 contract)

| 항목 | 요구 | 비고 |
| --- | --- | --- |
| input batch dict 키 | `local_grid`, `scalar`, `event_token`, `action_raw`, `action_prev_raw` | dtype은 §10.1과 동일 |
| target dict 키 | `obs_local_target`, `obs_scalar_target`, `reward`, `done`, `true_state`, `true_regime_control_mode`, `change_point`, `reveal_event`, `shift_event`, `raw_eff_mismatch` | dtype은 §10.2와 동일 |
| `done` 정의 | `dones \|\| truncateds` (npz는 분리 저장) | bool→float 변환 |
| `raw_eff_mismatch` 계산 | `(actions_raw != actions_effective).float()` | npz의 두 array로 즉시 계산 가능 |
| chunk_len / batch_size | yaml의 `trainer.chunk_len`, `trainer.batch_size` 사용 | episode 길이가 부족하면 padding mask 적용 |
| padding mask | `sample_weight`에 1.0(valid) / 0.0(pad) | 마지막 episode가 chunk_len에 못 미치면 pad |
| **event-window sampling** | change_point=1 또는 shift=1 step의 ±k window를 oversample. 또는 sample_weight를 키워서 가중. | k 권장 시작값 = 5. Session 8에서 ablation. |
| chunk overlap | (선택) chunk 시작 위치를 random offset으로 jitter | random_2000은 episode 길이 2000 / chunk 128일 때 1872 위치 가능 |
| stage mix | random_2000 vs success_curriculum_v5_2000 비율 | §2.4 참고 |
| split 강제 | `train`, `valid`만 사용. `test_id`/`ood_*`는 절대 yield 금지 | hard guard 권장 |
| collector_metadata 차단 | `episode_meta.collector_metadata` 필드는 batch dict에 절대 포함 금지 | hard guard 권장 (가능하면 unit test) |
| 결정성 | 동일 master_seed에서 동일 batch 순서 재현 | dataset의 episode-level determinism은 이미 검증됨 |

---

## 15. Session 9 — Training Loop 요구사항 (이번 세션에서 미구현)

| 항목 | 요구 | 비고 |
| --- | --- | --- |
| optimizer | AdamW (DreamerV3 표준 또는 RAdam) | medium: lr 3e-4 권장 시작값 |
| lr scheduler | linear warmup 1k step + constant 또는 cosine | Session 9 ablation |
| grad_clip | yaml `trainer.grad_clip` (default 100.0) | |
| precision | yaml `trainer.precision` (`fp32`/`bf16`/`fp16`) | medium은 `bf16` 권장 |
| EMA / target | (선택) target encoder/decoder EMA | DreamerV3는 사용 안 함 |
| variant dispatch | yaml `variants` 키에서 선택 + `WMConfig.apply_variant` | 5개 variant 학습 |
| logging | `WMLossOutput.components` + `diagnostics`를 step별로 기록 | tensorboard / wandb |
| checkpoint 정책 | variant × seed (≥3 seed) | seed ≥ 10은 final paper number, seed 3은 학습 단계 |
| early stop | valid total loss + change_point F1 + reward MSE | metric 정의는 Session 9에서 확정 |
| train/valid only | Session 8 loader가 강제 | training script에서도 추가 guard |
| compute budget | medium 기준 추정 wall-clock: 단일 RTX 4090 24GB 기준 ≈ N hours/variant | Session 9에서 실측 |

---

## 16. 데이터 분포 기반 설계 반영 요약

| 데이터 사실 | 설계 반영 |
| --- | --- |
| random_2000은 거의 모두 truncated, task success 거의 없음 | reward는 task+cost decomposed로 학습. step_cost / latency 누적이 dominant이므로 reward head MSE는 이를 학습. |
| random_2000은 reveal_mean ≈ 84, change_point_mean ≈ 1.05/episode | reveal head는 충분히 dense. change_point는 희소 → pos_weight + focal. |
| success_curriculum_v5_2000은 reveal_mean ≈ 127, all_tasks ≈ 9.5%, near-success 풍부 | reward / done / state / regime 학습 보강. |
| ood_param_shift에서 change_point ≈ 2.0/episode | pos_weight 50은 ID/OOD 모두 적절. OOD에서 학습은 안 하지만 evaluation 시 모델이 더 자주 양성 신호를 봄. |
| raw≠effective mismatch는 random_2000 ≈ 407/ep, success_v5 ≈ 775/ep | mismatch_head는 충분한 양성 → λ=0.5 (auxiliary로 충분). |
| change-point는 tick-level imbalance가 큼 | (loss) pos_weight + focal, (sampler) event-window oversampling — 후자는 Session 8. |
| reveal은 충분히 많음 | reveal_pos_weight=1.0. |
| shift_mean ≈ change_point_mean | 두 head를 분리 기록 (목적이 다름; PART1 §3.5). |
| task_order_entropy ≈ 4.4 (high) | dataset이 fixed-order에 over-fit하지 않음 → backbone에 task_order metadata 입력 불필요. |
| test_id/OOD는 학습 금지 | Session 8 loader가 강제. |

---

## 17. 본 세션이 *하지 않은 것* (다음 세션 위임)

- training loop / optimizer.step (Session 9)
- dataset loader (Session 8)
- event-window sampler 구현 (Session 8)
- planner / falsification score / action relevance 계산 (Session 11+)
- evaluator / OOD rollout (Session 14+)
- DreamerV3 외부 repo 복붙 (영원히 금지; PART0 §3.1, §3.2)
- full dataset 생성/수정 (이번 세션 변경 없음; manifest는 사용자가 이미 생성한 것을 사용)
- 환경 / generator / dataset schema 변경 (변경 없음)

---

## 18. 본 세션 산출물 (생성/수정 파일)

| 경로 | 종류 | 내용 |
| --- | --- | --- |
| `configs/wm_debug.yaml` | 신규 | RSSM medium-of-debug capacity. shape sanity / 8GB GPU / overfit check 전용 |
| `configs/wm_medium.yaml` | 신규 | 논문 main 결과의 단일 backbone capacity. paper_main=true |
| `falsifiable_regime_world_model/wm/__init__.py` | 신규 | wm 패키지 public API |
| `falsifiable_regime_world_model/wm/config.py` | 신규 | `WMConfig` + 하위 dataclass (yaml 매핑) |
| `falsifiable_regime_world_model/wm/modules.py` | 신규 | encoder / decoder / action embedding / MLP 유틸 |
| `falsifiable_regime_world_model/wm/rssm.py` | 신규 | RSSM core (h+z), prior, posterior, observe/imagine sequence |
| `falsifiable_regime_world_model/wm/heads.py` | 신규 | 모든 prediction head + `RSSMWorldModel` top-level |
| `falsifiable_regime_world_model/wm/losses.py` | 신규 | loss component 함수 + `compute_total_loss` |
| `falsifiable_regime_world_model/wm/README.md` | 신규 | wm 패키지 사용법 / API contract / variant 표 |
| `scripts/check_wm_shapes.py` | 신규 | synthetic shape sanity check (no dataset / no training) |
| `docs/WM_ARCHITECTURE_DESIGN.md` | 신규 | 본 문서 |
| `docs/SESSION7_HANDOFF.md` | 신규 | Session 8/9에 넘기는 contract |

본 세션은 `falsifiable_regime_world_model/rg4f/**`, `scripts/{generate_dataset,validate_dataset,inspect_episode,plot_dataset_stats,_p1_check_family_disjoint}.py`, `configs/dataset_default.yaml`, `ref/PART0~3`, `data/**`, `outputs/**`를 변경하지 않았다.
