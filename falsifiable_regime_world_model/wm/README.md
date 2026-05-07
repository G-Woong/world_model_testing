# `falsifiable_regime_world_model.wm` — RSSM/Dreamer-style World Model

> **Session 7 산출물.** RG-4F 환경의 *wrong-hypothesis-aware planning* 메커니즘 검증을 위해, 표준 RSSM/Dreamer-style backbone과 prediction head 구조 + loss 인터페이스를 제공한다. 본 패키지에는 학습 루프 / dataset loader / planner / evaluator가 들어 있지 **않다** (Session 8/9/11+).

## 1. 본 패키지가 다루는 범위

| 포함 | 미포함 |
| --- | --- |
| RSSM core (deterministic h + stochastic z) | training loop / optimizer.step |
| observation encoder (CNN + scalar MLP + event embedding) | dataset loader / replay / event-window sampler |
| prediction head (obs / reward / done / state / regime / change-point / reveal / shift / mismatch) | planner / falsification / action relevance / compute reallocation |
| loss component (MSE / BCE+pos_weight / focal / KL with free nats + balancing) | rollout-based action relevance / value gap |
| forward / imagine API (interface) | evaluation rollout / OOD evaluator |

## 2. PART0 정합성

본 backbone은 **mechanism novelty가 아니라 controlled backbone** 이다. PART0 §1.4 same-capacity 원칙에 따라:

- 모든 baseline / ablation은 본 패키지의 동일 RSSM capacity 위에서만 비교된다.
- variant ablation(`no_regime`, `no_change_point`, `no_reveal`, `no_state_aux`)은 **head/loss를 끄는 방식**으로 만들고, RSSM backbone capacity는 절대 바꾸지 않는다.
- planner / fixed-k / always-plan / uncertainty gate / event-only gate는 학습 variant가 아니라 **동일 checkpoint 위에서 evaluation 시점에 swap** 한다 → 본 패키지는 그 swap point만 만든다 (`predict_heads`, `imagine`).

## 3. Forward API contract (절대 변경 금지)

`RSSMWorldModel.forward(batch)`의 input batch:

```text
batch = {
  "local_grid"  : float32 (B, T, H=5, W=5, C=10)
  "scalar"      : float32 (B, T, S=14)
  "event_token" : long    (B, T)         # 0..12 (EventToken enum)
  "action_raw"  : long    (B, T)         # a_{0..T-1}
  # optional
  "action_prev_raw" : long (B, T)        # a_{t-1} 명시적 alignment (없으면 shift right)
}
```

forward output dict:

| key | shape | 의미 |
| --- | --- | --- |
| `h` | (B, T, deter) | RSSM deterministic state |
| `z` | (B, T, stoch) | RSSM stochastic latent (posterior sample) |
| `prior_mean` / `prior_std` | (B, T, stoch) | p(z_t \| h_t) |
| `post_mean` / `post_std` | (B, T, stoch) | q(z_t \| h_t, e_t) |
| `obs_local_pred` | (B, T, H, W, C) | local_grid reconstruction |
| `obs_scalar_pred` | (B, T, S) | scalar reconstruction |
| `reward_pred` | (B, T) | reward 예측 |
| `done_logit` | (B, T) | done logit (BCE-with-logits) |
| `state_pred` | (B, T, 5) | true_state regression |
| `regime_logits` | (B, T, R=5) | control_mode classification |
| `change_point_logit` | (B, T) | change-point binary logit |
| `reveal_logit` | (B, T) | reveal_event binary logit |
| `shift_logit` | (B, T) | shift_event binary logit |
| `raw_eff_mismatch_logit` | (B, T) | raw≠effective binary logit |

## 4. 입력 / 학습 target / 평가 metadata 분리 (반드시 준수)

| 분류 | 키 | 사용 위치 |
| --- | --- | --- |
| **모델 입력 (허용)** | `local_grid`, `scalar`, `event_token`, `action_raw` (+ 이전 latent) | encoder / RSSM 입력 |
| **학습 target (supervised)** | `obs_local_target`, `obs_scalar_target`, `reward`, `done`, `true_state`, `true_regime_control_mode`, `change_point`, `reveal_event`, `shift_event`, `raw_eff_mismatch` | `compute_total_loss` |
| **평가/감사 전용 (모델 입력/target 모두 금지)** | `collector_metadata`, `collector_mode`, `task_order_str`, `b_use_label_oracle`, `privilege_level`, `task_attempt_ticks`, `task_timeout`, `forced_permutation` (raw), `target_band_center`, `stele_positive_k`, `piece_weight_j` 등 | dataset 감사 / OOD diagnostic |

> `true_regime` / `change_point` / `reveal` / `shift`는 **target으로만** 사용하며 planner/evaluation 입력으로 직접 제공하면 안 된다 (PART0 §3.3 / §3.5 reveal-vs-shift, PART2 §3.7 falsification).

## 5. variant ablation (학습 시점)

`WMConfig.apply_variant(name)`을 호출하여 head/loss를 끈다.

| variant | regime | change_point | reveal | shift | state |
| --- | :-: | :-: | :-: | :-: | :-: |
| `full_model` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `no_regime` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `no_change_point` | ✅ | ❌ | ✅ | ✅ | ✅ |
| `no_reveal` (optional) | ✅ | ✅ | ❌ | ✅ | ✅ |
| `no_state_aux` (optional) | ✅ | ✅ | ✅ | ✅ | ❌ |

> fixed-k, always-plan, uncertainty gate, novelty gate, event-only gate, no-action-relevance, adaptive lookahead 등은 **학습 variant가 아니라 evaluation-time planner swap** 이다. checkpoint 수를 폭증시키지 않기 위해 본 패키지의 variant는 위 5개로 제한된다.

## 6. Smoke import / shape check

PyTorch가 설치된 환경(`requirements.txt` 기준)에서:

```bash
python -c "from falsifiable_regime_world_model.wm import RSSMWorldModel, WMConfig; print('wm import ok')"
python scripts/check_wm_shapes.py --config configs/wm_debug.yaml
python scripts/check_wm_shapes.py --config configs/wm_medium.yaml
```

`scripts/check_wm_shapes.py`는 dataset loader 없이 synthetic tensor만 사용하여 forward/loss shape을 검증한다 (PART0 §3 학습 금지 원칙 준수).

## 7. 다음 세션 (handoff)

- **Session 8 — Dataset loader / event-window sampler.** RG-4F npz schema → batch dict 변환, change-point/shift event-window oversampling, padding mask sample_weight 생성.
- **Session 9 — Training loop.** optimizer / lr scheduler / EMA / dataset stage mix(random_2000 vs success_curriculum_v5_2000) / checkpoint variant 학습.
- **Session 11 — Planner.** `RSSMWorldModel.imagine` 위에 alternative-regime conditioning, current-vs-alternative rollout 비교, falsification score, action relevance, compute reallocation.
