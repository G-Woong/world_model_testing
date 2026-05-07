# Planner Interface Design — Session 11-13

> 본 문서는 학습된 RSSM world model checkpoint 위에 얹히는 **planner-side interface 계층**의 설계를 닫는다. 모든 baseline / FRC-WM가 공유하는 *공통 abstract API*와 *데이터 객체*를 정의하며, oracle/metadata leakage 방지 규칙을 한 곳에 모은다.
>
> **참조:** PART2 §3.7~§3.14, PART3 §3.22~§3.25, docs/WM_ARCHITECTURE_DESIGN.md §11, docs/WM_DIAGNOSTICS_REPORT.md §11.

---

## 1. 목적

학습된 RSSM checkpoint(예: `outputs/wm_runs/wm_medium_full_v1/checkpoints/step_00030000.pt`)를 planner가 다음 5가지 질문에 일관되게 답할 수 있도록 감싼다.

1. **encode** — 환경 obs를 latent feature로 만든다.
2. **belief update** — 새 obs를 받아 posterior로 latent state를 갱신한다.
3. **imagine current** — 현재 가설로 horizon만큼 미래를 상상한다.
4. **imagine alternative** — 대안 가설로 미래를 상상한다 (oracle 사용 금지).
5. **score** — rollout을 candidate value(+risk)로 환산한다.

이 5단계가 PART2 §3.14의 알고리즘 step 1~7에 1:1 대응한다.

---

## 2. checkpoint load 방식

```python
adapter = WorldModelAdapter.load_from_checkpoint(
    "outputs/wm_runs/wm_medium_full_v1/checkpoints/step_00030000.pt",
    wm_config_path="configs/wm_medium.yaml",
    variant="full_model",   # full_model | no_regime | no_change_point
    device="auto",          # auto | cuda | cpu
)
```

내부 동작:
1. `WMConfig.from_yaml(wm_config_path).apply_variant(variant)` — variant에 맞춰 head ON/OFF.
2. `wm.checkpointing.load_checkpoint(map_location=device)` — atomic load.
3. `RSSMWorldModel(cfg).load_state_dict(state["model"], strict=False)` — head 비활성으로 인한 graceful missing은 허용, 그 외 unexpected key는 에러.
4. `model.eval()` — dropout/BN 끔.
5. adapter는 head ON 표 (`has_regime_head`, `has_change_point_head`, …)를 노출 → planner가 사용 가능 head를 판단 가능.

**Best alias 누락 대응:** Session 9 `ManagedCheckpointer._evict_best` 버그(WM_DIAGNOSTICS_REPORT §1.4)로 best alias가 일부 run에서 없으나, `step_00030000.pt`(또는 `last.pt`)는 항상 존재한다. 본 인터페이스는 별칭에 의존하지 않는다.

---

## 3. obs schema (planner input)

planner는 RG4F obs dict의 **3개 키**만 읽는다. 나머지(action_mask)는 baseline에서 valid action 필터에만 사용한다.

| key | shape | dtype | 용도 |
| --- | --- | --- | --- |
| `local_grid` | (5, 5, 10) | float32 | encoder CNN |
| `scalar` | (14,) | float32 | encoder MLP. 첫 5개는 5D 상태값(planner trace의 obs_state로 사용) |
| `event_token` | scalar | int32 | encoder embedding |
| `action_mask` | (16,) | float32 | (선택) baseline의 valid action gate |

**절대 금지** — `info` dict의 `true_state` / `true_regime` / `change_point` / `reveal_event` / `shift_event` / `target_band` / `field_info` 등은 planner input으로 들어가면 안 된다. 이는 metric 계산용으로만 trace에 기록한다.

---

## 4. belief update 방식

```python
belief: BeliefState = adapter.update_belief(
    prev_belief=belief_prev,    # 첫 step: None (zero-state)
    obs=env_obs,
    prev_action=last_action,    # 첫 step: None → 0 padding
    step_index=t,
)
```

내부 동작:
1. `prev_belief is None`이면 `model.initial_state(batch_size=1)`로 초기화.
2. encoder로 `feat_t = encoder(local_grid, scalar, event_token)`.
3. action embedding으로 `prev_action_emb = action_emb(prev_action_raw)`.
4. `rssm.posterior_step(prev_state, prev_action_emb, feat_t)` → 새 RSSMState.
5. `predict_heads(h, z)`로 모든 ON head 평가 → `belief.head_outputs`.
6. `BeliefState(h, z, prior_mean, prior_std, post_mean, post_std, head_outputs, ...)` 반환.

`belief.head_outputs`의 키는 head ON에 따라:
- `state_pred (1,5)` / `reward_pred (1,)` / `done_logit (1,)` / `regime_logits (1,R)` /
  `change_point_logit (1,)` / `reveal_logit (1,)` / `shift_logit (1,)` /
  `raw_eff_mismatch_logit (1,)` / `obs_local_pred` / `obs_scalar_pred`.

---

## 5. imagine API

### 5.1 current hypothesis

```python
rollout: RolloutPrediction = adapter.imagine_from_belief(
    belief, action_sequences,    # (CS, H) np.int64
    horizon=H, n_samples=S, n_candidates=C,
)
```

- 1 batch에 `C × S` rollout을 한 번에 굴린다 (broadcast).
- prior-only rollout (no encoder call within the rollout).
- 각 candidate의 reward·state·regime·cp·reveal·shift·mismatch 예측이 `(C*S, H, ...)` shape으로 반환.
- compute accounting: `rollout_steps = C * S * H`.

### 5.2 alternative hypothesis (oracle 금지)

```python
alt: RolloutPrediction = adapter.imagine_alternative(
    belief, action_sequences,
    horizon=H, n_samples=S, n_candidates=C,
    latent_perturb_std=0.5,         # stochastic z perturbation
    regime_topk_index=1,             # 1 = 첫 alternative
)
```

**alternative 생성 메커니즘:**
1. **stochastic z perturbation (always):** 초기 `z`를 `latent_perturb_std × N(0, I)` 로 흔들어 alternative latent posterior에서 sampling한 것처럼 굴린다. → "model이 스스로 의심하는 대안"이 만들어진다.
2. **prior_std inflation (regime_topk_index 주어진 경우):** prior_std를 약간 키워 alternative trajectory diversity를 유도. regime conditioning을 모델이 받지 않으므로 정식 conditioning 대신 latent uncertainty inflation 사용.

**금지된 메커니즘:**
- `info["true_regime"]`을 input으로 주입 → oracle leakage, 실험 무효.
- `b_use_label_oracle`, `task_order_str`, `collector_metadata` 등 사용 → 학습 데이터 collector 전용 metadata, planner 사용 불가.

### 5.3 score

```python
value: torch.Tensor = adapter.score_rollout(rollout, gamma=0.99, risk_weight=0.0)
# value shape: (C,)
```

- 기본은 discounted reward sum (done masking으로 self-truncation).
- `risk_weight > 0`이면 `mismatch_prob + cp_prob`의 평균을 risk로 차감.
- candidate 단위 점수 → planner는 argmax로 best action 선택.

---

## 6. current vs alternative hypothesis rollout

planner 측 알고리즘 (FRC-WM에서 사용):

```python
rollout_cur = adapter.imagine_from_belief(belief, action_seqs, ...)
rollout_alt = adapter.imagine_alternative(belief, action_seqs, ...)

relevance = compute_action_relevance(
    rollout_current=rollout_cur,
    rollout_alternative=rollout_alt,
    relevance_value_gap_norm=1.0,
    use_action_flip=True,
)
disagreement = compute_alternative_disagreement(
    current=rollout_cur, alternatives=[rollout_alt],
)
```

`relevance.flip_from_argmax_current=True` + `relevance.value_gap > τ_Δ`이면 PART2 §3.8.3의 `Δ_t^{flip}` 조건이 성립한다 → action choice가 갈리는 decision-relevant 순간.

`disagreement["predicted_reward_gap"]`은 falsification score 재계산에 들어간다 (PART2 §3.7 `B_t`의 rollout-based proxy).

---

## 7. compute budget interface

`PlannerConfig` + `ComputeAccountant`로 budget을 통제한다.

```yaml
horizon: 10
candidate_action_count: 8
num_rollouts_per_candidate: 1
max_planning_calls_per_episode: 600
compute_budget_total: 200000        # episode 누적 rollout step 한도 (0=unlimited)
compute_budget_per_step: 0          # step 한도 (0=unlimited)
```

`ComputeAccountant.can_plan(expected_rollout_steps)` → 현재 step에서 추가 rollout이 가능한지 확인. 모든 baseline + FRC가 같은 함수를 호출하므로 fair comparison이 가능하다.

`record_planning(rollout_steps, n_rollouts)`은 `total_rollout_steps`, `total_planning_calls`, `total_imagined_rollouts`를 누적한다 → metric에 그대로 사용.

---

## 8. trace schema

`PlannerTrace`는 episode 단위, `StepTrace`는 step 단위 dataclass.

**StepTrace 필수 필드:**
- `step`, `action`, `decision_mode`, `used_planning`, `planning_calls`, `rollout_steps`,
  `candidate_count`, `horizon`
- `reward`, `cumulative_reward`, `terminated`, `truncated`
- `falsification_score`, `action_relevance` (FRC; baseline은 0)
- `head_pred_summary` — head 예측 요약 (planner가 무엇을 보고 결정했는지 사후 분석)
- `info_summary` — env info 요약 (true_state / true_regime / change_point / reveal / shift /
  task_id / room_id / completed_tasks / fail_count). **Metric 계산용; planner는 이 값을
  보지 않는다.**
- `decision_reason` — per-mode score / threshold / stage 등 사후 해석용 dict

직렬화: `trace.write_jsonl(path)` → 한 line = header / step / summary.

---

## 9. oracle / metadata leakage 방지 규칙

본 인터페이스가 강제하는 5가지 가드.

1. `WorldModelAdapter.encode_observation` / `update_belief`는 `local_grid`, `scalar`,
   `event_token`만 읽는다. 다른 obs 키나 info 키는 의도적으로 무시한다.
2. `BasePlanner.select_action`은 `(env_obs, belief, planner_state)`만 받고 `info`는 받지
   않는다. → 모든 planner 구현이 동일한 input 계약을 따른다.
3. `imagine_alternative`는 `latent perturbation` + `prior_std inflation`만 사용한다.
   ground-truth regime을 conditioning으로 받는 API는 만들지 않았다.
4. `info["true_*"]` / `info["change_point"]` / `info["reveal_event"]` / `info["shift_event"]`
   / `info["target_band"]` / `info["field_info"]`는 trace 기록용으로만 사용한다 (metric에서
   reads back).
5. `BaselinePlannerConfig.uncertainty_signal == "regime_entropy"`는 head output (logits)
   기반 entropy일 뿐, ground-truth regime을 사용하지 않는다.

**Self-audit (Cursor 스모크에서 검증)**: `head_outputs`가 `regime_logits`, `change_point_logit`, `mismatch_logit`을 노출하지만, 이 값은 모두 forward(belief)의 결과이지 info에서 읽은 값이 아니다.

---

## 10. variant ablation 자동 fallback

`adapter.has_*` 표를 보고 planner는 사용 가능 head만 활용한다. 사용 불가 head는 N/A 또는 fallback signal.

| Variant | regime_logits | change_point_logit | reveal_logit | mismatch_logit |
| --- | :-: | :-: | :-: | :-: |
| `full_model` | ✓ | ✓ | ✓ | ✓ |
| `no_regime` | ✗ | ✓ | ✓ | ✓ |
| `no_change_point` | ✓ | ✗ | ✓ | ✓ |

planner가 사용 불가 head를 silent ignore (raise 안 함) — fair comparison 보장.

- `UncertaintyGatePlanner.uncertainty_signal == "regime_entropy"` & no_regime → fallback `reward_var` 또는 `latent_var`.
- `EventOnlyPlanner.event_signals` 중 사용 불가 head는 0으로 처리.
- `FRCWMPlanner` — `frc.use_change_point=False`로 자동 toggle. falsification_weights의 cp 항이 0이 됨.

---

## 11. 본 세션이 *하지 않은* 것 (다음 세션 위임)

- alternative regime의 정식 conditioning (regime embedding을 RSSM prior에 주입) — 학습된 모델이 이 input을 받지 않으므로, 학습 단에서 변경 필요 (Session 14+).
- Q-value head — 현재는 reward sum이 candidate value. value head가 필요하면 학습 단에서 supervised proxy 추가 (Session 14+).
- soft-to-hard threshold annealing (PART2 §3.13.3) — eval 시점에는 hard threshold만 적용. annealing은 학습 시 allocator collapse 방지용이며 평가에서는 yaml 고정값 사용.
- WM 자체 변형 (no_reveal, no_state_aux variant 평가) — 추가 checkpoint가 필요하므로 별도 학습 후 yaml에 model entry 추가.

---

## 12. 본 세션이 생성한 파일 (interface 부분)

- `falsifiable_regime_world_model/planner/__init__.py`
- `falsifiable_regime_world_model/planner/config.py`
- `falsifiable_regime_world_model/planner/interface.py`
- `falsifiable_regime_world_model/planner/world_model_adapter.py`
- `falsifiable_regime_world_model/planner/action_space.py`
- `falsifiable_regime_world_model/planner/trace.py`
- `falsifiable_regime_world_model/planner/scoring.py`
- `falsifiable_regime_world_model/planner/policies.py`
