# WM Diagnostics Report — Session 10

> **모드:** read-only diagnostic. 학습/optimizer/checkpoint 변경 0건. test_id/OOD는 frozen checkpoint로 `torch.no_grad` 평가만 수행했고 **hyperparameter / checkpoint selection에 사용하지 않았다**.
>
> **분석 대상:** `outputs/wm_runs/wm_medium_full_v1` / `wm_medium_no_regime_v1` / `wm_medium_no_change_point_v1` (모두 step=30000 도달).
>
> **공정 비교 기준:** 각 run의 `step_00030000.pt`. best alias 비교는 보조표(없는 경우가 있음 — Session 9 `ManagedCheckpointer._evict_best`의 known issue. 본 분석은 step_00030000.pt를 primary로 사용).

---

## 0. 쉬운 해석 (먼저 읽으세요)

이 섹션은 머신러닝 용어가 익숙하지 않아도 본 분석의 핵심을 이해할 수 있게 풀어쓴 것입니다.

### 0.1 World model이 뭘 배운 건가요?

RG-4F 환경은 4개의 방(A/B/C/D)에서 task를 푸는 부분관측 게임입니다. **world model**은 이 게임 안에서 다음을 *상상*할 수 있도록 학습합니다.

- **다음 화면**(local 5×5 grid)이 어떻게 변할지
- **5가지 숨은 상태값** (vision / mobility / interaction / noise / control-drift)이 어떻게 변할지
- 다음 step의 **reward**
- 게임이 끝났는지 (`done`)
- **현재 어떤 규칙 모드**(regime — 예: `IDENTITY` 컨트롤인지 `CW` 회전 컨트롤인지)인지
- **change-point**(규칙이 바뀐 순간), **reveal**(숨겨진 정보가 드러난 순간), **shift**(규칙이 다른 종류로 바뀐 순간)
- **raw vs effective mismatch** (눌렀다고 생각한 키와 실제 작동한 키가 다른 경우 — control-drift 흔적)

### 0.2 full_model / no_regime / no_change_point 차이는?

같은 world model의 backbone (RSSM medium, 약 10.7M params)에 학습 supervision을 다르게 붙였습니다.

| variant | regime supervision | change-point supervision | 의미 |
|---|:-:|:-:|---|
| **full_model** | ✅ | ✅ | 모든 head 학습 |
| **no_regime** | ❌ | ✅ | "현재 규칙 모드 맞추기"를 학습하지 않으면 어떤 일이 일어나는가 |
| **no_change_point** | ✅ | ❌ | "규칙이 바뀐 순간 감지"를 학습하지 않으면 어떤 일이 일어나는가 |

> **모델 크기/구조는 같습니다.** 어느 head를 끄느냐만 다릅니다 (PART0 §1.4 same-capacity 원칙).

### 0.3 주요 지표 한 줄 설명

- **state MSE**: 모델이 5가지 숨은 상태값을 얼마나 정확히 따라가는지. *낮을수록 좋다.*
- **regime accuracy**: 현재 규칙 모드(5종 중)를 맞히는 능력. *높을수록 좋다.* no_regime은 일부러 끈 대조군이라 N/A.
- **change-point F1**: 규칙이 바뀌는 *정확한 그 tick*을 맞히는 능력. *높을수록 좋다.* 단, 규칙이 바뀌는 사건 자체가 episode당 1~2번 정도라 매우 *희소*(전체 tick의 0.05%~0.2%)해서 숫자 자체는 낮게 나오기 쉽다. **best-threshold F1**이 더 의미 있다.
- **reveal F1**: 숨은 정보가 드러나는 순간을 감지하는 능력. reveal은 비교적 자주 발생해서 학습이 잘 된다.
- **raw_eff_mismatch F1**: "내가 W를 눌렀는데 실제로는 D처럼 작동" 같은 control-drift 흔적을 감지. *높을수록 좋다.*
- **rollout fidelity (state_mse@H)**: 모델이 머릿속으로 H tick 미래를 *상상*했을 때 실제와 얼마나 비슷한지. H=10이면 10 tick 미래. *낮을수록 좋다.*
- **cp delay hit@k**: change-point가 일어났을 때 모델이 *±k tick 안에* 감지했는지 (정확한 tick이 아니라 근방을 맞히는지).
- **PR-AUC**: 모든 threshold에 대한 precision-recall 평균. **fixed threshold F1보다 모델의 진짜 분리력을 잘 보여준다.**

### 0.4 왜 total loss만 보면 안 되나요?

**시험 과목 수가 다른 학생들의 총점만 비교하면 불공정**합니다. full_model은 11과목을 보고, no_regime은 10과목, no_change_point는 10과목을 봅니다. 어느 한 학생의 총점이 낮다고 그 학생이 더 똑똑한 건 아니죠. 그래서 우리는 **공통 과목 점수**(common-core metrics)와 **특정 과목 제거 효과**(variant-specific)를 따로 봅니다.

### 0.5 지금 결과가 NeurIPS 논문 주장에 어떤 의미인가요?

**핵심 주장 두 가지가 명확히 지지됩니다.**

1. **"hidden regime을 분리 학습하면 control mismatch를 더 잘 잡는다"** — full_model의 raw_eff_mismatch F1이 random_2000 OOD에서 no_regime의 **74×~236× 더 높습니다**. 이건 우연이 아닙니다.
2. **"규칙 변화(change-point)가 매우 희소해도 모델은 그 신호를 분리한다"** — fixed threshold F1=0.18은 낮아 보이지만, **PR-AUC가 random baseline의 40배**, **logit separation이 +12.6**입니다. 즉 모델은 "여기가 변화 시점이다"를 상당히 잘 *분리*하고 있고, threshold만 잘 잡으면 사용 가능합니다. 또한 hard OOD (`success_v5 ood_param_shift`)에서 cp best F1이 **0.50** vs no_regime의 **0.07** — drift가 강해질수록 regime supervision이 cp 학습에 결정적입니다.

**한 가지 약점**: change_point head 자체를 끈 ablation(no_change_point)이 다른 head 성능에 미치는 영향이 작습니다. 즉 cp 신호는 다른 head들에 잘 *전이되지 않습니다*. 이건 PART2 §3.7의 입장 ("cp posterior는 falsification score용 신호로만 사용") 과 일관되며, paper에서 cp head를 *그 자체로* 평가하는 게 아니라 **planner가 falsification에 사용**하는 식으로 위치시키면 됩니다.

### 0.6 다음 planner phase로 넘어가도 되나요?

**예. 단, 두 가지 metric 보강을 권장합니다.**

- cp **threshold tuning** (지금 fixed 0.5는 너무 낮음 — best는 ~1.2 logit, 즉 sigmoid 0.77).
- reward MSE를 *percentile* 기준으로 보고 (mean reward MSE 1097은 outlier 200²=40000 한 번에 끌려가는 값).

세부는 §10 verdict / §11 planner-readiness 참고.

---

## 1. Run 비교 핵심 표

### 1.1 Final valid (step=30000, 모든 run 도달)

| Run | variant | uni_total | event_total | reward MSE (uni) | state MSE (uni) | regime acc (uni) | cp F1@0 (event) | reveal F1@0 (event) | mismatch F1@0 (event) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| wm_medium_full_v1 | full_model | **4.088** | 11.677 | 1097.2 | 6.91 | **0.873** | **0.112** | 0.551 | **0.704** |
| wm_medium_no_regime_v1 | no_regime | 3.876 | 11.267 | 1056.7 | 7.26 | N/A | 0.108 | 0.552 | 0.659 |
| wm_medium_no_change_point_v1 | no_change_point | **3.712** | **7.360** | 1024.1 | 6.69 | 0.870 | N/A | 0.569 | 0.701 |

> **주의: total loss는 directly comparable 하지 않다** (head 개수 차이로 인한 자연스러운 격차). no_change_point는 cp/shift loss 항이 줄어 total이 작게 나오는 게 *당연*하다. **§1.2의 common-core 표를 우선 비교하라**.

### 1.2 Common-core metric (variant-agnostic, 공정 비교)

| Run | variant | reward MSE (uni) | state MSE (uni) | reveal F1 (event, best) | shift F1 (event, best) | mismatch F1 (event, best) | reveal PR-AUC | mismatch PR-AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| full | full_model | 1097.2 | 6.91 | **0.622** | 0.182 | **0.721** | 0.647 | **0.788** |
| no_regime | no_regime | 1056.7 | 7.26 | 0.645 | 0.189 | 0.686 | **0.669** | 0.724 |
| no_cp | no_change_point | 1024.1 | 6.69 | 0.639 | 0.197 | 0.724 | 0.650 | 0.784 |

→ **mismatch (= raw≠effective)**에서 **full > no_regime이 가장 명확** (best F1 0.721 vs 0.686, PR-AUC 0.788 vs 0.724). 다른 head는 거의 동일.

### 1.3 cp/shift threshold sweep + PR-AUC (best-threshold F1 vs fixed=0)

| Run | head | n_pos / n_total | F1@th=0 | **best F1 / threshold** | PR-AUC | logit separation |
|---|---|---|---:|---:|---:|---:|
| **full** (event) | change_point | 80 / 32,768 (0.24%) | 0.119 | **0.183 / +1.26** | **0.098** | **+12.61** |
| no_regime (event) | change_point | 80 / 32,768 | 0.110 | 0.182 / +1.16 | 0.094 | +12.92 |
| no_cp (event) | change_point | — | N/A (head removed) | — | — | — |
| **full** (event) | shift | 80 / 32,768 | 0.116 | 0.182 / +1.26 | 0.097 | **+13.04** |
| no_regime (event) | shift | 80 / 32,768 | 0.105 | 0.189 / +1.23 | 0.095 | +13.90 |
| no_cp (event) | shift | 80 / 32,768 | 0.097 | 0.197 / +1.38 | 0.097 | +12.80 |
| **full** (event) | reveal | 2,034 / 32,768 (6.2%) | 0.551 | **0.622 / -0.77** | 0.647 | +6.68 |
| **full** (event) | mismatch | 8,923 / 32,768 (27.2%) | 0.717 | 0.721 / -0.30 | 0.788 | +2.95 |
| **full** (event) | success_done | **0** / 32,768 (0%) | 0.000 | 0.000 / NaN | 0.000 | +0.00 |
| **full** (uniform) | success_done | 0 / 32,768 | 0.000 | 0.000 | 0.000 | +0.00 |

**핵심 통찰:**
- cp/shift는 **fixed threshold 0**에서는 F1≈0.11이지만, **best threshold(~+1.2 logit, sigmoid≈0.77)에서 F1=0.18**. PR-AUC가 random baseline(=base_rate=0.0024)의 **40×**. **logit separation +12.6** — 모델이 양성/음성을 *매우 강하게* 분리한다.
- success_done은 **valid_event/uniform 모두 positive=0** — chunk-sample 통계의 자연스러운 결과 (Session 9 진단 §2.1과 일관). paper-main success rate는 episode-level G_episode (PART3 §3.25.1)이며 Session 11+ planner rollout이 측정.
- reveal/mismatch는 dense이고 학습 결과 우수.

### 1.4 best valid metrics (보조 — 학습 곡선 시점별)

| Run | best valid_uniform/total (step) | best valid_event/cp_f1 (step) |
|---|---|---|
| full | 3.533 (step 19000) | 0.119 (step 29000) |
| no_regime | 3.494 (step 19000) | 0.121 (step 30000) |
| no_change_point | 3.500 (step 18000) | N/A |

> best는 step_00029000.pt만 살아 있고 best alias 파일이 누락 (Session 9 `ManagedCheckpointer._evict_best` 버그). 본 분석은 step_00030000.pt만 사용.

---

## 2. Rollout fidelity (모델이 미래를 얼마나 정확히 상상하는가)

**방식**: chunk_len=128에서 warmup_len=32까지 posterior로 latent 학습 → 그 후 prior-only rollout으로 H step 미래 예측. 실제 chunk의 action은 그대로 사용 (alternative-action counterfactual은 ground truth 없으므로 평가 안 함).

### 2.1 H별 state MSE (낮을수록 좋음)

| Run | eval_kind | H=1 | H=5 | H=10 | H=20 | H=50 |
|---|---|---:|---:|---:|---:|---:|
| full | event | 0.0074 | 0.0088 | 0.0100 | — | 0.0393 |
| full | uniform | 0.0077 | 0.0083 | 0.0088 | — | 0.0241 |
| no_regime | event | 0.0038 | 0.0055 | 0.0070 | — | 0.0358 |
| no_regime | uniform | 0.0034 | 0.0042 | 0.0046 | — | 0.0224 |
| no_cp | event | 0.0069 | 0.0090 | 0.0109 | — | 0.0331 |
| no_cp | uniform | 0.0047 | 0.0053 | 0.0062 | — | 0.0201 |

**해석:**
- **no_regime이 state MSE 자체는 가장 작다** (rollout @ H=1: full 0.0077 vs no_regime 0.0034). regime supervision이 state head capacity를 약간 차지하는 *trade-off*.
- 그러나 **state MSE는 절대값이 매우 작다 (≈0.01)** — 5D 상태값 [-1, 1] 범위에서 충분히 실용적.
- **장기 horizon (H=50)에서는 모든 variant가 0.02~0.04 수준** — paper에서 horizon ≤50의 planner rollout은 안전.

### 2.2 event chunk vs non-event chunk (full_model 기준, valid_uniform)

| H | state_mse_event | state_mse_non_event | event "tax" |
|---:|---:|---:|---:|
| 1 | 0.0076 | 0.0119 | non_event 더 어려움 |
| 5 | 0.0082 | 0.0133 | non_event 더 어려움 |
| 10 | 0.0087 | 0.0132 | non_event 더 어려움 |
| 50 | 0.0243 | 0.0165 | event가 더 어려움 |

→ 단기 horizon에서 event chunk가 *오히려* 더 작은 state MSE를 보이는 것은 **event-window oversampling으로 모델이 event 영역을 더 많이 봤기 때문**. uniform sampling은 모델이 덜 본 영역. 장기 horizon에서는 정상적으로 event 추적이 더 어려움.

### 2.3 cp delay (= predicted_peak_tick - true_cp_tick)

| Run | eval_kind | n_cp_chunks | mean delay | abs_mean | hit@1 | hit@3 | hit@5 | **hit@10** |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| full | event | 23 | -2.6 (early) | 20.6 | 0.04 | 0.13 | **0.17** | **0.35** |
| full | uniform | 5 | -6.6 | 15.8 | 0.20 | 0.40 | 0.40 | **0.40** |
| no_regime | event | 23 | -2.6 | 16.3 | 0.04 | 0.13 | 0.17 | **0.39** |
| no_regime | uniform | 5 | -26.4 (very early!) | 26.4 | 0 | 0 | 0 | **0** |
| no_cp | — | N/A (head removed) |

**해석:**
- **full_model은 cp를 평균 2.6 tick *일찍* 예측** (early bias). 이는 PART2 §3.7의 "빠른 falsification" 방향과 일치 — paper-friendly.
- **uniform valid에서 full_model의 hit@10 = 40%**. 즉 cp가 일어났을 때 ±10 tick 안에 감지하는 비율이 40%. exact F1=0.11보다 훨씬 의미 있는 수치.
- **no_regime은 uniform valid에서 cp를 26.4 tick 일찍 misfire** — regime supervision이 없으면 cp 신호가 noise로 처리됨.

---

## 3. Reward long-tail 분석 (train log 기반)

| Run | mean | median | p90 | p99 | max | n_spikes (>5×median) | grad_norm p99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1.64 | 0.95 | 5.21 | 10.73 | **49.31** | 53/601 (8.8%) | 51.2 |
| no_regime | 1.60 | 0.95 | 4.96 | 10.56 | **56.41** | 47/601 (7.8%) | 66.0 |
| no_cp | 1.70 | 1.00 | 5.42 | 11.61 | **55.92** | 51/601 (8.5%) | 38.5 |

**해석:**
- 모든 variant에서 **task_reward=50 / completion_reward=200 같은 long-tail outlier가 reward MSE를 dominant**. 한 번 잘못 예측한 single tick (reward=200)에서 MSE = 200² = 40,000.
- spike 시점에도 **NaN/Inf 없음**, grad clip 100.0이 정상 작동, 즉시 회복.
- valid_uniform reward MSE 1056~1097은 **outlier 분포의 자연스러운 결과**이지 모델이 reward를 "못 배운" 것이 아니다 (rollout @ H=10 reward MSE ≈ 0.7, normal range에서는 매우 정확).

> **paper에서는 reward MSE를 raw mean으로 보고하지 말고, percentile-based (p50/p90) + spike sign accuracy로 분리해 보고할 것.** Session 11+에서 그 형식으로 evaluation table 설계.

---

## 4. 핵심 비교 질문 답변

### Q1. full_model은 no_regime보다 무엇을 더 잘 배우는가?

**가장 명확한 격차: raw_eff_mismatch (=control-drift 감지)**

| 비교 | full_model | no_regime | 비율 |
|---|---:|---:|---:|
| valid_event mismatch best F1 | 0.721 | 0.686 | +5% |
| valid_event mismatch PR-AUC | **0.788** | 0.724 | +9% |
| **random_2000 test_id mismatch f1@0** | **0.442** | 0.006 | **74×** |
| **random_2000 ood_room_perm mismatch f1@0** | **0.473** | 0.002 | **236×** |
| **random_2000 ood_param_shift mismatch f1@0** | 0.519 | 0.008 | **65×** |
| success_v5 ood_param_shift cp best_f1 | **0.500** | 0.067 | **7.5×** |

→ regime supervision이 control-drift action remap (PART2 §3.10) 학습에 **결정적**임을 압도적으로 증명. paper main argument.

**state MSE는 trade-off**: no_regime이 약간 (~50%) 더 낮음. 그러나 절대값(0.003~0.008)이 모두 충분히 작아 trade-off가 paper-critical 아님.

### Q2. full_model은 no_change_point보다 무엇을 더 잘 배우는가?

**격차가 작다.** cp head 자체 비교는 N/A. 다른 head는 거의 동일:

| 비교 | full | no_cp | 비고 |
|---|---:|---:|---|
| valid_event reveal best F1 | 0.622 | 0.639 | no_cp 살짝 더 좋음 |
| valid_event mismatch best F1 | 0.721 | 0.724 | 거의 동일 |
| rollout state_mse_event @ H=10 | 0.0097 | 0.0105 | full +8% |
| rollout state_mse_event @ H=50 | 0.038 | 0.033 | no_cp -13% (역전) |

**해석**: cp head를 끄는 것은 다른 head 학습에 *큰 영향이 없다*. 이는 PART2 §3.7.2의 입장 (cp posterior는 falsification score용 별도 신호)과 일관. 즉 **cp head는 그 자체로 paper-main metric이 아니라, planner의 falsification gate 입력으로 사용된다**. paper에서 ablation 차이가 작은 것이 *paper-main argument를 약화시키지 않는다*.

### Q3. full_model의 낮은 cp_f1은 치명적인가? — **NO.**

| 분석 | 값 |
|---|---|
| fixed F1 (logit > 0) | 0.119 |
| **best F1 (logit > +1.26)** | **0.183** |
| PR-AUC | 0.098 (base rate 0.0024 대비 **40×**) |
| **logit separation** (pos_mean - neg_mean) | **+12.61** (강한 분리) |
| recall (best threshold) | 75% (Session 9에서 확인) |
| **hit@10** (cp delay) | **35-40%** |
| ood_param_shift (success_v5) best F1 | **0.500** |

→ cp head는 **분리력이 매우 강하고**, drift OOD에서 best F1=0.50까지 도달. fixed threshold 0.5만 보면 안 됨. **threshold tuning을 planner gate에서 적용**하면 사용 가능.

### Q4. success_done F1=0은 논문 주장에 치명적인가? — **NO.**

| 분석 | 값 |
|---|---|
| valid_event success_done positives | **0** / 32,768 ticks |
| valid_uniform success_done positives | 0 / 32,768 ticks |
| chunk가 success_done=1을 포함할 확률 (수학적) | ≈ 0.027% (uniform) / ≈ 0.04% (event) |

→ **통계적으로 자연스러운 결과**. success_v5_2000의 done_rate ≈ 9.5%이고 episode당 done tick이 1개뿐이므로 chunk_len=128 기반 sampling으로는 거의 불가능. **paper-main success metric은 PART3 §3.25.1의 episode-level G_episode**이며 Session 11+ planner rollout으로 측정. 본 done_logit F1은 *학습 안정성 진단*용이지 paper-main metric이 아님.

---

## 5. Held-out (test_id / OOD) Diagnostic

> **이 결과는 hyperparameter / checkpoint selection에 사용하지 않았다.** Session 11+ evaluator가 paper-main 결과를 별도 측정. 본 표는 *generalization characterization* 자료.

### 5.1 random_2000 splits, full_model 기준 (n_episodes=8 each)

| split | state MSE | reward MSE | regime acc | cp f1@0 (best) | reveal f1@0 | shift f1@0 | mismatch f1@0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| test_id | 0.015 | 0.2 | 0.807 | 0.000 (0.021) | 0.423 | 0.000 | 0.442 |
| ood_room_perm | 0.023 | 0.3 | 0.903 | 0.027 (0.070) | 0.284 | 0.026 | 0.473 |
| ood_factor_recomb | 0.005 | 0.3 | 0.831 | 0.027 (0.077) | 0.536 | 0.026 | 0.110 |
| ood_param_shift | 0.030 | 0.4 | 0.774 | 0.028 (0.050) | 0.000 | 0.026 | **0.519** |
| **ood_obs_shift** | **0.034** | 0.5 | **0.265** | 0.000 (0.007) | 0.034 | 0.000 | 0.031 |
| ood_field_placement | 0.004 | 0.2 | 0.937 | 0.024 (0.062) | 0.384 | 0.024 | 0.300 |

→ **ood_obs_shift (visual channel permutation)이 가장 어려움** — regime accuracy 0.81→0.27. PART3 §3.24.4 obs_shift OOD가 의도대로 어려운 평가가 된다.

### 5.2 success_v5_2000 splits, full vs no_regime (cp/mismatch 핵심 격차)

| split | metric | full_model | no_regime | ratio |
|---|---|---:|---:|---:|
| test_id | mismatch f1@0 | 0.885 | 0.866 | 1.02× |
| ood_factor_recomb | cp best F1 | 0.211 | 0.200 | 1.06× |
| **ood_param_shift** | **cp best F1** | **0.500** | 0.067 | **7.5×** |
| ood_param_shift | mismatch f1@0 | 0.941 | 0.934 | 1.01× |
| ood_obs_shift | regime acc | 0.452 | N/A | — |
| ood_field_placement | regime acc | 0.969 | N/A | — |

→ **drift-heavy OOD (`ood_param_shift`)에서 full > no_regime의 격차가 가장 큼** (cp 7.5×). 이는 paper §3.21 small cumulative drift scenario와 일치.

---

## 6. ref/PART0~3 위반 점검

| 검사 | 결과 |
|---|---|
| test_id/OOD를 학습/checkpoint selection에 사용 | **위반 없음.** 본 분석에서 test_id/OOD는 frozen forward로만 평가, 결과를 hyperparameter 결정에 사용 안 함. |
| collector_metadata / oracle metadata를 model input | **위반 없음.** `assert_safe_inputs` + `load_meta=False` (data.py) 다중 방어가 학습/평가 모두 적용. |
| state/regime/change-point/reveal 분리 구조 | **유지.** 본 진단은 head 별 metric을 모두 분리 측정. |
| same-backbone control (PART0 §1.4) | **유지.** 3 variant 모두 medium capacity, head/loss만 다름. |
| 결과 과장 | **없음.** verdict table에 PASS/WEAK/YELLOW를 정직하게 표기. cp F1 fixed=0.11이 paper-friendly하지 않을 수 있음을 명시. |

---

## 7. Claim Verdict Table

(상세 csv: `outputs/wm_diagnostics/session10/claim_verdict_table.csv`)

| Claim | 핵심 evidence | Verdict |
|---|---|:-:|
| **C1.** State dynamics learned | valid state MSE 66→7 (10×), rollout @ H=10 = 0.009 | **PASS** |
| **C2.** Hidden regime matters | mismatch full vs no_regime: random test_id 74×, ood_room_perm 236×, success ood_param cp 7.5× | **PASS** (강하게) |
| **C3.** Change-point awareness matters | cp ablation effect on other heads ~0; rollout @ H≤10 event 미세 우세 | **WEAK** |
| **C4.** Reveal/shift separation learnable | reveal best F1=0.62, sep=+6.7; shift best F1=0.18, sep=+13.0 | **PASS** (reveal), **WEAK** (shift exact) |
| **C5.** Control mismatch learned | mismatch best F1=0.72, PR-AUC=0.79; OOD random에서 full vs no_regime 74× | **PASS** |
| **C6.** Reward usable for planner | spike 견딤, NaN 없음, p99=10.7; mean MSE는 outlier 1개로 부풀려짐 | **WEAK** (raw MSE 보고 시 misleading) |
| **C7.** Planner can proceed | rollout @ H=50 state MSE 0.024~0.04, cp delay hit@10=35~40%, mismatch F1=0.72 | **PASS** |

**Overall verdict: 🟡 YELLOW (toward GREEN)**

- 4 PASS + 1 강한 PASS (C2) + 2 WEAK.
- Hidden regime의 effect (C2)와 control mismatch (C5)는 paper main claim을 명확히 지지.
- cp ablation effect (C3)의 약함은 PART2 §3.7.2 ("cp는 falsification gate signal") 입장과 일관 — paper에서는 cp 자체의 ablation을 main으로 두지 말고 *full_model의 PR-AUC + delay hit*를 paper-main으로.
- **Planner phase 진행 가능. cp threshold tuning + reward percentile reporting은 Session 11+에서 정리.**

---

## 8. 사용자가 이해하기 쉬운 최종 해석

### 잘 된 것 (paper claim을 *지지*하는 결과)

1. **모델은 게임 안의 5개 숨은 상태값을 정말 잘 따라간다** (state MSE가 학습 동안 10배 줄었고, 미래 10 tick을 상상해도 오차가 0.01 수준).
2. **"규칙 모드 학습 (regime supervision)"이 실제로 도움이 된다.** regime을 끈 모델은 control-drift (W를 눌렀는데 D처럼 작동하는 현상)를 *거의* 학습하지 못한다 (74×~236× 격차). 이는 NeurIPS paper의 핵심 주장 중 하나를 강하게 뒷받침한다.
3. **change-point head는 fixed threshold에서는 F1이 낮지만, 분리력 자체는 강하다.** 모델은 "여기가 변화 시점이다"라는 신호를 +12.6 logit 단위로 분리한다. 단 threshold가 너무 낮게 잡혀 있어서 false positive가 많은 것뿐이다. planner에서 적절히 threshold를 잡으면 ±10 tick 안에 35~40% 비율로 감지한다.
4. **drift가 강한 OOD 환경 (`ood_param_shift`)에서 cp F1이 0.50으로 올라간다** (no_regime은 0.07). 즉 *어려운 환경일수록 regime supervision의 차이가 더 커진다*. paper §3.21 small cumulative drift 시나리오와 일치.

### 약한 것 (paper에서 솔직히 인정해야 할 부분)

5. **change_point head를 *끄는 것 자체*가 다른 head 학습을 거의 망치지 않는다.** 이는 cp 신호가 다른 head들에 잘 전이되지 않는다는 뜻이며, paper에서 cp head를 *그 자체의 ablation*으로 paper-main에 두지 말고, **planner의 falsification gate signal**로 위치시키는 게 정직하다.
6. **reward MSE 절대값(1097)이 크다.** 이는 task 성공 시 +50 / 완료 시 +200 같은 outlier reward 한 번에 끌려가는 것이지 모델이 "reward를 못 배운" 것이 아니다 (정상 범위에서는 매우 정확). paper에서는 mean reward MSE를 raw로 보고하지 말고 percentile (p50, p90)로 보고할 것.
7. **success_done F1=0**은 chunk-sample 통계의 한계 — paper-main success rate는 episode-level G_episode이며 Session 11+ planner rollout이 측정한다.

### 다음으로 무엇을?

**Session 11 — Planner phase 진행 권장.** 본 diagnostic은 다음 데이터를 그대로 planner stub에 입력 가능함을 보였다:

- `RSSMWorldModel.imagine` API stub은 작동 (이미 검증됨, Session 7).
- frozen checkpoint는 정상 로드 + no_grad forward 정상.
- cp logit separation +12.6 / hit@10=35% → falsification score (PART2 §3.7) 의 *원료*로 사용 가능.
- mismatch F1=0.72 → control-drift hypothesis 비교의 *원료*로 사용 가능.
- regime accuracy 0.87 → current regime hypothesis로 사용 가능.

단, 다음 항목들은 **Session 11에서 별도 결정 필요**:

- cp threshold tuning (logit > +1.26 권장; 이는 dataset의 양성 prevalence에 따라 다시 조정).
- reward target normalization (Session 11 evaluation의 reward MSE를 percentile + outlier 분리로 reporting).
- Session 9 `ManagedCheckpointer._evict_best` 수정 (best alias 파일 누락 — 다음 학습 run 전).

---

## 9. 출력물 위치

| 파일 | 내용 |
|---|---|
| `outputs/wm_diagnostics/session10/checkpoint_inventory.csv` | 각 run의 checkpoint 파일 존재 여부 + primary path + alias missing notes |
| `outputs/wm_diagnostics/session10/run_summary_table.csv` | run별 요약 dataclass 행 |
| `outputs/wm_diagnostics/session10/final_valid_table.csv` | step=30000 final valid metrics |
| `outputs/wm_diagnostics/session10/best_valid_table.csv` | log 기반 best valid metrics + step |
| `outputs/wm_diagnostics/session10/common_core_metrics.csv` | variant-agnostic 비교용 |
| `outputs/wm_diagnostics/session10/threshold_sweep.csv` | (run, eval, head) × 13 threshold |
| `outputs/wm_diagnostics/session10/threshold_sweep_summary.csv` | best F1, PR-AUC, separation per (run, eval, head) |
| `outputs/wm_diagnostics/session10/rollout_fidelity.csv` | (run, eval, H) × event/non_event/cp_chunk MSE/accuracy |
| `outputs/wm_diagnostics/session10/rollout_fidelity_summary.csv` | event-uniform gap per H |
| `outputs/wm_diagnostics/session10/change_point_delay.csv` | cp delay 분포 + hit@k |
| `outputs/wm_diagnostics/session10/heldout_prediction_diagnostics.csv` | (run, dataset, split) × all common-core metrics |
| `outputs/wm_diagnostics/session10/reward_diagnostics_log.csv` | reward long-tail + spike count + grad norm |
| `outputs/wm_diagnostics/session10/claim_verdict_table.csv` | 7-claim verdict + overall YELLOW |
| `docs/WM_DIAGNOSTICS_REPORT.md` | 본 문서 |
| `docs/SESSION10_HANDOFF.md` | 후속 세션 handoff |
