# RG4F 2000T Dataset Command Prep — 사용자 직접 실행용 명령 확정

> 본 문서는 `random_2000`과 `success_curriculum_v5_2000` full dataset 생성 직전,
> Cursor가 (a) random_biased collector 정상 동작 검증, (b) 2000 tick에서 코드가
> 깨지지 않는지 소량 smoke check, (c) 사용자가 직접 실행할 안전한 full 생성/검증
> 명령 정리만 수행한 결과를 기록한다.
>
> **Cursor는 full dataset을 직접 생성하지 않았다.** Cursor가 생성한 root는 `*_check`
> suffix가 붙은 소량 smoke 2개뿐이며, full root (`data/rg4f_random_2000`,
> `data/rg4f_success_curriculum_v5_2000`)는 Cursor가 만들지 않는다. 사용자가 직접
> 본 보고서의 §6 명령으로 실행한다.
>
> 모든 기존 dataset (1500/1000/600 모두) **0줄 변경 / 0 파일 삭제**.

---

## 1. random_biased Collector 존재/복구 여부

### 1.1 코드 검증 (수정 0줄)

`scripts/generate_dataset.py`의 random_biased 체인이 모두 그대로 유지됨:

| 항목 | 위치 | 상태 |
|---|---|---|
| `_RandomBehaviorPolicy` 클래스 | L263 | ✓ 존재 |
| `_build_action_probs("random_biased")` | L201 | ✓ movement 55% / E 15% / state-adjust 30% / WAIT 0% |
| `_make_policy("random_biased")` → `_RandomBehaviorPolicy(probs)` | L1149-1151 | ✓ dispatch 정상 |
| CLI `--behavior-policy random_biased` 허용 | argparse L? + main() L1086+ | ✓ allowed list `random_uniform | random_biased | task_probe | task_success_curriculum` |
| yaml `generation.behavior_policy: random_biased` default | L37 | ✓ 유지 |
| schema/index/manifest 호환 | env.reset/step/info 동일 | ✓ task_probe / task_success_curriculum과 동일 contract |

→ random_biased collector는 **task_probe 및 task_success_curriculum 추가 과정에서 변질되지 않음**. 복구 작업 불필요.

### 1.2 동적 검증

소량 smoke (10 train + 6 OOD × 2000 step)으로 직접 검증:
- 명령: `python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\smoke_random_2000_check --num-train 10 --num-valid 2 --num-test 2 --num-ood-per-type 2 --max-steps 2000 --behavior-policy random_biased --overwrite`
- 결과: **소요 7.11초**, 22 episodes 정상 생성.

---

## 2. 수정 파일 목록

**0개. 본 세션에서 코드/yaml/dataset 모든 변경 없음.**

| 카테고리 | 변경 |
|---|---|
| `scripts/generate_dataset.py` | 0줄 변경 |
| `scripts/plot_dataset_stats.py` | 0줄 변경 |
| `scripts/validate_dataset.py` | 0줄 변경 |
| `scripts/inspect_episode.py` | 0줄 변경 |
| `scripts/_p1_check_family_disjoint.py` | 0줄 변경 |
| `configs/dataset_default.yaml` | 0줄 변경 |
| `falsifiable_regime_world_model/rg4f/**` | 0줄 변경 |
| `ref/PART0~3` | 0줄 변경 |
| `requirements.txt` | 0줄 변경 |

생성한 파일:
- `data/smoke_random_2000_check/` (smoke 22 episodes, 7.11초)
- `data/smoke_success_curriculum_v5_2000_check/` (smoke 55 episodes, 14.08초)
- `outputs/smoke_random_2000_check_stats/` (summary.csv + per_task_summary.csv + collector_summary.csv)
- `outputs/smoke_success_curriculum_v5_2000_check_stats/` (동일)
- `docs/RG4F_2000_DATASET_COMMAND_PREP_REPORT.md` (본 문서)

---

## 3. Smoke dataset Root 목록 (Cursor 생성)

| Root | 목적 | num_train | max_steps | behavior_policy | wall-clock |
|---|---|---:|---:|---|---:|
| `data/smoke_random_2000_check` | random_biased 2000T 코드 sanity | 10 | 2000 | random_biased | 7.11s |
| `data/smoke_success_curriculum_v5_2000_check` | task_success_curriculum 2000T 코드 sanity | 20 | 2000 | task_success_curriculum | 14.08s |

**두 root 모두 `_check` suffix가 붙어 있어 사용자 full root와 명확히 구분된다.**

---

## 4. smoke_random_2000_check 결과

### 4.1 strict validation
```
=== Validation summary === PASS: 326  WARN: 0  FAIL: 0
```

### 4.2 P1 family disjoint
```
train               {0,1}    observed {0,1}     PASS  VIS=6, FRIC=4
valid               {0,1}    observed {1}       PASS  FRIC=2
test_id             {0,1}    observed {1}       PASS  FRIC=3
ood_factor_recomb   {2,3}    observed {3}       PASS  CTRL_INTF=3
others              4 family 자유              PASS
OVERALL: PASS
```

(2~3 ep/split 표본이라 family 분포가 sparse하지만 모두 allowed pool 안)

### 4.3 핵심 stats (summary.csv 발췌)

| split | n_episodes | len_mean | reward_mean | completed_count_final | all_tasks | reveal_mean | change_point_mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 10 | 2000 | -2605.3 | 0.10 | 0.000 | 44.7 | 0.70 |
| valid | 2 | 2000 | -2430.1 | 0.00 | 0.000 | 2.0 | 1.00 |
| test_id | 2 | 2000 | -2422.1 | 0.00 | 0.000 | 2.5 | 2.00 |
| ood_factor_recomb | 2 | 2000 | -2537.0 | 0.00 | 0.000 | 450.5 | 2.50 |

→ random_biased는 의도대로 **broad dynamics**를 만든다. 성공률 매우 낮음 (train all_tasks=0.0, completed_count=0.10). truncated_rate=1.000 (모든 episode가 max 2000에 도달). 이는 정상 — random은 dynamics pretraining용이지 success 만들기가 아님.

### 4.4 task_order metadata (random_biased에서는 미사용)

random_biased는 collector_metadata를 생성하지 않으므로 `most_common_collector_mode_ratio = 0`, `task_order_entropy = 0`. 정상 동작.

---

## 5. smoke_success_curriculum_v5_2000_check 결과

### 5.1 strict validation
```
=== Validation summary === PASS: 682  WARN: 0  FAIL: 0
```

### 5.2 P1 family disjoint
```
train               {0,1}    observed {0,1}     PASS  VIS=11, FRIC=10
valid               {0,1}    observed {0,1}     PASS  VIS=3, FRIC=3
test_id             {0,1}    observed {0,1}     PASS  VIS=2, FRIC=4
ood_factor_recomb   {2,3}    observed {2,3}     PASS  INT_INTF=2, CTRL_INTF=6
others              4 family 자유              PASS
OVERALL: PASS
```

### 5.3 핵심 stats (summary.csv 발췌)

| split | n_episodes | len_mean | completed_count_final | all_tasks_rate | A | B | C | D | reveal_mean | task_order_entropy | most_common_order |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **train** | **20** | **1765.6** | **1.25** | **0.20** | **0.25** | **0.25** | **0.35** | **0.40** | **190.9** | **3.05** | **0.20** |
| valid | 5 | 1750 | 1.20 | 0.20 | 0.20 | 0.40 | 0.20 | 0.40 | 63.6 | 2.32 | 0.20 |
| test_id | 5 | 1723.8 | 1.60 | 0.20 | 0.40 | 0.20 | 0.60 | 0.40 | 548.0 | 1.92 | 0.40 |
| ood_factor_recomb | 5 | 1741.6 | 1.20 | 0.20 | 0.40 | 0.40 | 0.20 | 0.20 | 7.4 | 1.37 | 0.60 |

### 5.4 핵심 관찰

- **task_order metadata 정상 기록**: train (20 ep)에서 task_order_entropy=3.05, most_common_task_order_ratio=0.20 (≤0.35 ✓).
- **collector_summary.csv 생성됨**: episode_meta의 `collector_metadata.collector_mode` / `task_order_str` 모두 split별 distribution으로 집계.
- **2000 tick 효과**: 1500 tick 기준 (n=80) train all_tasks=0.125 → 2000 tick (n=20) train all_tasks=0.20. 단 표본 작아 노이즈 큼. **full 5000 ep로 가야 통계적 의미**.
- **truncated_rate**: train 0.80, test_id 0.80, ood_factor_recomb 0.80 → 일부 episode가 4-task 모두 완료로 조기 종료 (done_rate 0.20). 1500 (train 0.875)보다 truncated 비율 약간 감소.
- **reveal_mean**: train 190.9 (1500의 115.3 대비 ×1.66 폭증), test_id 548.0 (이상 큼 — 4 task 깨고 남은 시간에 더 많은 reveal_event 누적).

→ **2000 tick에서 코드 깨짐 없음 + task_order metadata 유지 + P1 disjoint 유지**. full 5000 ep 생성 준비 완료.

### 5.5 표본 작음의 한계 명시

- 본 smoke는 train 20 ep / OOD 5 ep × split 표본. 통계 노이즈가 매우 큼.
- 최종 train per-task rate (0.30+)와 train all_tasks_rate (0.10~0.25)는 사용자 full 실행 후에 직접 확인해야 한다.
- 본 smoke 결과를 agent 성능 또는 paper metric으로 인용하지 말 것.

---

## 6. 기존 1500 / 1000 / 600 dataset 보존 여부

```powershell
$paths = @('data\rg4f', 'data\smoke', 'data\smoke_p1_filtered', 'data\smoke_taskprobe_1000',
           'data\smoke_success_curriculum_1500', 'data\smoke_success_curriculum_v5_1500',
           'data\rg4f_random_2000', 'data\rg4f_success_curriculum_v5_2000')
foreach ($p in $paths) { "$p`tmanifest=$(Test-Path "$p\manifest.json")" }
```

결과:

| Path | manifest.json 존재? | 본 세션에서 변경? |
|---|:---:|:---:|
| `data/rg4f` (random_biased_600 full) | True | **변경 0** |
| `data/smoke` (Session 5 smoke) | True | **변경 0** |
| `data/smoke_p1_filtered` | True | **변경 0** |
| `data/smoke_taskprobe_1000` | True | **변경 0** |
| `data/smoke_success_curriculum_1500` (v4) | True | **변경 0** |
| `data/smoke_success_curriculum_v5_1500` | True | **변경 0** |
| `data/rg4f_random_2000` | False | (사용자 full 생성 대기 중) |
| `data/rg4f_success_curriculum_v5_2000` | True (max_steps=200, train=5만 — 사용자 placeholder) | **변경 0** (Cursor가 만들지 않음) |

### 6.1 `data/rg4f_success_curriculum_v5_2000`에 대한 주의

- 본 세션 시작 시점에 이미 manifest.json이 존재. 내용 검사 결과: `max_steps=200, counts={train:5, valid:0, test_id:0, ...}` — 즉 사용자가 이전 세션에서 직접 만든 작은 placeholder.
- **Cursor는 이 root를 본 세션에서 만들지 않았으며 건드리지 않았다**.
- **사용자가 §7.1 명령으로 full 5000 ep × 2000 tick 실행 시 `--overwrite`로 placeholder를 덮어쓰는 것이 의도된 동작**. 단 사용자 결정에 따라 다른 root 이름으로 변경 가능.

---

## 7. 사용자가 직접 실행할 Full 생성 명령 (Cursor 직접 실행 금지)

> **Cursor는 본 세션에서 아래 명령들을 절대 실행하지 않았다.** 본 명령은 사용자가
> 직접 PowerShell 터미널에 입력하여 실행한다.

### 7.1 success_curriculum_v5_2000 full 생성

```powershell
python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\rg4f_success_curriculum_v5_2000 --num-train 5000 --num-valid 500 --num-test 500 --num-ood-per-type 500 --max-steps 2000 --behavior-policy task_success_curriculum --overwrite
```

총: **8,500 episodes / max 17,000,000 transitions** / 디스크 약 5~7 GB / 소요 약 60~150분.

### 7.2 random_2000 full 생성

```powershell
python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\rg4f_random_2000 --num-train 5000 --num-valid 500 --num-test 500 --num-ood-per-type 500 --max-steps 2000 --behavior-policy random_biased --overwrite
```

총: **8,500 episodes / max 17,000,000 transitions** / 디스크 약 4~6 GB / 소요 약 30~80분 (random은 task_probe보다 빠름).

### 7.3 root 이름 규칙 강제

- **금지**: `--output-root data\rg4f_success_curriculum_v5_1500 --max-steps 2000` (1500 root에 2000 horizon 데이터를 넣으면 root 이름과 horizon이 불일치 → 실험 관리 혼란).
- **금지**: `--output-root data\rg4f_random_1500 --max-steps 2000`.
- **권장**: root 이름의 마지막 숫자가 max_steps와 일치하도록 항상 `*_2000` suffix 사용.

---

## 8. 사용자가 직접 실행할 검증 명령

### 8.1 success_curriculum_v5_2000 full 검증 (5단계)

```powershell
python scripts\validate_dataset.py --root data\rg4f_success_curriculum_v5_2000 --strict --max-episodes-per-split 100 --json-report data\rg4f_success_curriculum_v5_2000\validation_report.json
python scripts\validate_dataset.py --root data\rg4f_success_curriculum_v5_2000 --check-determinism --config configs\dataset_default.yaml --max-episodes-per-split 3
python scripts\plot_dataset_stats.py --root data\rg4f_success_curriculum_v5_2000 --out outputs\rg4f_success_curriculum_v5_2000_stats --max-episodes-per-split 500
python scripts\_p1_check_family_disjoint.py data\rg4f_success_curriculum_v5_2000
python scripts\inspect_episode.py --root data\rg4f_success_curriculum_v5_2000 --split train --index 0 --num-steps 200 --show-grid --show-scalar --show-info
```

### 8.2 random_2000 full 검증 (4단계)

```powershell
python scripts\validate_dataset.py --root data\rg4f_random_2000 --strict --max-episodes-per-split 100 --json-report data\rg4f_random_2000\validation_report.json
python scripts\validate_dataset.py --root data\rg4f_random_2000 --check-determinism --config configs\dataset_default.yaml --max-episodes-per-split 3
python scripts\plot_dataset_stats.py --root data\rg4f_random_2000 --out outputs\rg4f_random_2000_stats --max-episodes-per-split 500
python scripts\_p1_check_family_disjoint.py data\rg4f_random_2000
```

---

## 9. 두 Dataset의 역할 분리

### 9.1 `data/rg4f_random_2000`

**역할**:
- **broad dynamics pretraining**: 5-state vector transition / control-drift remap / mobility cooldown / invisible field drift / event-triggered shift / sparse coupling 관측의 다양성 확보.
- **실패/방황/잘못된 interaction/cooldown_blocked/raw≠eff** 같은 negative trajectory 학습.
- **scripted collector 편향 완화**: success_curriculum의 weak_oracle 구조 의존성을 상쇄.

**학습 사용**:
- ✅ `train` / `valid` 만 학습 input.
- ❌ `test_id` / `ood_*` 모두 학습 금지.

### 9.2 `data/rg4f_success_curriculum_v5_2000`

**역할**:
- **rare success / near-success / reward transition / value / action-relevance** 보강.
- weak_oracle scripted collector 기반 trajectory.
- task_order diversity 확보 (entropy ≥ 3.0).
- **evaluation agent 아님**.

**학습 사용**:
- ✅ `train` / `valid` 만 학습 input.
- ❌ `test_id` / `ood_*` 모두 학습 금지.
- ❌ `collector_metadata.collector_mode`, `task_order_str`, `b_use_label_oracle`, `task_attempt_ticks` 등 **privilege metadata는 model input으로 절대 넣지 말 것**. 이는 dataset 감사용일 뿐 학습 input 아님.

### 9.3 평가 단계

- 학습된 RSSM/Dreamer-style world model + planner가 **oracle 없이** `test_id` / `ood_*` 환경에서 직접 rollout.
- collector success rate는 dataset의 신호 분포일 뿐 agent 성능 아님.
- 평가 metric은 학습 후 evaluator가 환경에서 직접 측정한 것만 인용.

---

## 10. 1500 vs 2000 비교 양식 (사용자 full 실행 후 입력)

> Cursor는 full 2000을 생성하지 않았으므로 본 비교는 **사용자가 직접 full 실행 후
> 채워 넣을 양식**으로만 제공한다.

### 10.1 train split 비교표

| metric | success_v5_1500 (기존, 80 ep) | success_v5_2000_full (사용자 실행 후 입력) | random_2000_full (사용자 실행 후 입력) | 해석 |
|---|---:|---:|---:|---|
| `len_mean` | 1414.15 | (입력) | (입력) | early termination 비율 |
| `all_tasks_completed_rate` | 0.1250 | (입력, 권장 0.10~0.25) | (입력, 매우 낮을 것) | 4-task 성공 비율 |
| `done_rate` | 0.1250 | (입력) | (입력) | 자연 종료 |
| `truncated_rate` | 0.875 | (입력, 권장 0.60~0.90) | (입력, ~1.00 예상) | max tick 잘림 |
| `task_A_completed_rate` | 0.2625 | (입력) | (입력) | A 완료율 |
| `task_B_completed_rate` | 0.2250 | (입력) | (입력) | B 완료율 |
| `task_C_completed_rate` | 0.2375 | (입력) | (입력) | C 완료율 |
| `task_D_completed_rate` | 0.3375 | (입력) | (입력) | D 완료율 |
| `completed_count_final_mean` | 1.0625 | (입력) | (입력) | 평균 완료 수 |
| `reveal_mean` | 115.31 | (입력, 1.5×~2× 1500) | (입력, ~50) | task event |
| `change_point_mean` | 0.9375 | (입력, 권장 1.0~2.0) | (입력) | regime shift |
| `shift_mean` | 0.9375 | (입력) | (입력) | (= change_point) |
| `raw_eff_mismatch_count_mean` | 628.08 | (입력) | (입력) | control-drift remap effect |
| `task_order_entropy` | 4.07 | (입력, ≥ 3.0) | N/A (random은 미사용) | order diversity |
| `most_common_task_order_ratio` | 0.1625 | (입력, ≤ 0.35) | N/A | 단일 order 지배도 |
| `most_common_collector_mode_ratio` | 0.3125 | (입력, ≤ 0.50) | N/A | mode 분배 |

### 10.2 판정 기준

- **success_v5_2000 train all_tasks_completed_rate 권장 범위**: 0.10 ~ 0.25
  - 0.10 미만: 2000 tick에도 충분한 success 없음 → 1500 유지 또는 추가 budget 분석
  - 0.25 초과: 성공만 많은 dataset → 학습 시 over-fitting 우려, mix 비율 조정
- **truncated_rate 권장 범위**: 0.60 ~ 0.90 (실패/방황 trajectory 일부 유지 필수)
  - 0.60 미만: 성공 과다, dynamics 다양성 약화
  - 0.90 초과: 1500과 차이 없음 → 2000 채택 이점 약함
- **task_order_entropy ≥ 3.0**: order diversity 유지
- **most_common_task_order_ratio ≤ 0.35**: 단일 order 지배 없음
- **change_point_mean**: ID train/test 1.0~2.0, ood_param_shift 2.0~4.0, 5.0 초과 시 wrong-hypothesis persistence 문제 약화 위험

### 10.3 1500 유지 vs 2000 채택 결정

- 위 판정 기준을 기반으로 사용자가 full 실행 후 두 dataset 비교하여 결정.
- 만약 2000이 1500과 큰 차이가 없으면 1500 유지 + reveal/change-point는 학습 단계에서 event-window sampling, pos_weight/focal loss로 처리.
- 만약 2000이 의미 있게 더 풍부한 success/event signal을 주면 채택.

---

## 11. Change-point 빈도 평가 기준

| 환경 | change_point_mean 권장 | 의미 |
|---|---:|---|
| ID train/test (family={0,1}) | 1.0 ~ 2.0 | 적절 |
| ood_param_shift (×2.0 multiplier) | 2.0 ~ 4.0 | 적절 (drift 강화 의도) |
| 다른 OOD splits | 1.0 ~ 3.0 | 적절 |
| 모든 split | < 1.0 | **너무 적음** — wrong-hypothesis persistence 학습 supervision 부족 |
| 모든 split | > 5.0 | **너무 잦음** — wrong-hypothesis persistence 문제 사라짐 (regime이 매번 바뀌어 belief가 무의미) |

### 11.1 본 smoke 결과 (1500과 비교)

| split | 1500 change_point | 2000_check change_point | 변화 |
|---|---:|---:|---|
| train (random_biased) | 0.43 | 0.70 | 약간 증가 (자연스러움 — 더 긴 episode → event 더 많음) |
| train (success_curr v5) | 0.94 | 0.75 | 약간 감소 (success episode가 조기 종료되어 event 누적 줄음) |

### 11.2 만약 full 2000에서도 change_point < 1.0이면

본 보고서의 권장: **데이터 생성 자체를 무리하게 바꾸지 말고**, 월드모델 학습 단계에서:
1. **event-window sampling**: change_point=True 인 step 주변을 oversample
2. **pos_weight / focal loss**: change-point head의 loss에 양성 클래스 가중치
3. **multi-step prediction**: 단일 step 대신 ±k window 안에서 change-point 발생 여부 예측

→ 본 세션에서 `shift_probability` 등을 임의로 키워서 데이터 분포를 다시 바꾸지 마라. 1500/v5 비교가 꼬인다.

---

## 12. 학습용 Split 사용 원칙 (반드시 준수)

### 12.1 학습 input으로 사용 가능

| dataset | split |
|---|---|
| `data/rg4f_random_2000` | `train`, `valid` |
| `data/rg4f_success_curriculum_v5_2000` | `train`, `valid` |

### 12.2 학습 input으로 사용 절대 금지

| dataset | split |
|---|---|
| 모든 dataset | `test_id`, `ood_room_perm`, `ood_factor_recomb`, `ood_param_shift`, `ood_obs_shift`, `ood_field_placement` |

### 12.3 평가는 별도 환경에서

- 학습된 RSSM/Dreamer-style world model + planner가 `test_id` / OOD 환경에서 **oracle 없이 직접 rollout**.
- collector success rate를 agent 성능으로 보고 금지.
- weak_oracle metadata 어떤 것도 model input으로 안 들어감.

---

## 13. 학습 Stage Mix 제안 (초기 권장)

### Stage 1 — Dynamics warmup
- `data/rg4f_random_2000` 100% (train + valid)
- 목적: state transition / control-drift / mobility cooldown / invisible field 동역학 broad coverage
- 학습 epoch: 전체의 ~30~40%

### Stage 2 — Mixed world model training
- `data/rg4f_random_2000` 50% + `data/rg4f_success_curriculum_v5_2000` 50%
- 목적: dynamics + reveal/interaction/near-success 혼합 학습
- 학습 epoch: 전체의 ~30~40%

### Stage 3 — Value/action-relevance emphasis
- `data/rg4f_random_2000` 30% + `data/rg4f_success_curriculum_v5_2000` 70%
- 목적: value head / action relevance / change-point F1 강화
- 학습 epoch: 전체의 ~20~30%

### 비율 결정 방식
- 위 비율은 **초기 제안**. 최종은 학습 후 validation rollout fidelity / reward prediction MSE / change-point F1 / action relevance metric을 ablation으로 비교하여 결정.

---

## 14. weak-oracle Collector Metadata 경고 (반복 명시)

`success_curriculum_v5_2000` 의 episode_meta에는 다음 metadata가 기록된다:

```json
"collector_metadata": {
  "collector_mode": "all_task_random_order",
  "task_order_planned": [2, 0, 3, 1],
  "task_order_str": "CADB",
  "task_attempt_ticks": {"A": 73, "B": 92, "C": 33, "D": 7},
  "task_timeout": {"A": 0, "B": 0, "C": 0, "D": 0},
  "task_retry_count": {"A": 0, "B": 0, "C": 0, "D": 0},
  "task_budgets": {"A": 420, "B": 480, "C": 360, "D": 200},
  "privilege_level": "weak_oracle",
  "b_use_label_oracle": true
}
```

이 metadata는:
- ✅ **dataset 감사 / 편향 분석 / order diversity 검증용**으로 사용
- ❌ **model input feature로 절대 사용 금지**: 학습 시 어떤 head에도 들어가면 안 됨 (oracle leak)

학습 dataset loader 작성 시 npz의 numeric arrays만 input으로 사용하고, episode_meta.json의 `collector_metadata`는 **무시 또는 별도 분석용 streamlist에만 사용**.

---

## 15. 최종 판정

### **2000 생성 준비 완료 — Cursor smoke check 모두 PASS, 사용자가 §7 명령으로 직접 full 생성 가능.**

근거:
1. `random_biased` collector 정상 동작 확인 (코드 0줄 변경, smoke PASS=326).
2. `task_success_curriculum` 2000T 정상 동작 확인 (smoke PASS=682, P1 disjoint OVERALL PASS, task_order_entropy 3.05, most_common_order 0.20).
3. 기존 dataset (1500/1000/600 모두) 0줄 변경 / 0 파일 삭제 확인.
4. **Cursor는 full root (`data/rg4f_random_2000`, `data/rg4f_success_curriculum_v5_2000`)를 직접 생성하지 않음** — `data/rg4f_success_curriculum_v5_2000`은 사용자가 이전 세션에서 만든 placeholder (max_steps=200, train=5)로 본 세션 0줄 건드리지 않음.
5. 사용자 직접 실행 명령 (`§7.1`, `§7.2`)과 검증 명령 (`§8`)을 정확히 작성, root 이름 규칙 (`*_2000`) 강제.
6. random vs success_curriculum 역할 분리, train/valid만 학습 사용 원칙, weak_oracle metadata 학습 input 금지 원칙 모두 명시.

### 다음 단계

1. **사용자가 §7.1 / §7.2 명령으로 full dataset 생성** (소요 ~30~150분 each).
2. **사용자가 §8 명령으로 full 검증**.
3. **§10 비교표를 사용자가 채워 1500 vs 2000 채택 결정**.
4. **WM Session 1 (architecture plan)**: 2개 dataset의 stage mix를 학습 plan에 반영.

---

## 16. Self-Audit

| Check | Status | Evidence |
|---|---|---|
| random_biased collector가 동작하는가 | PASS | smoke_random_2000_check 정상 생성 + strict PASS=326. 코드 L201, L263, L1149 모두 그대로 유지. |
| 기존 1500 dataset을 덮어쓰지 않았는가 | PASS | `Test-Path data\smoke_success_curriculum_v5_1500\manifest.json = True`. LastWriteTime 변경 없음. |
| full success_v5_2000을 직접 생성하지 않았는가 | PASS | Cursor가 본 세션에서 실행한 generate_dataset 명령은 모두 `*_check` suffix root + 소량 (10~20 ep). full root `data/rg4f_success_curriculum_v5_2000`은 본 세션 0줄 변경 (LastWriteTime 2026-04-26 5:58, 본 세션 시작 전). |
| full random_2000을 직접 생성하지 않았는가 | PASS | `data/rg4f_random_2000\manifest.json = False` (root 자체 미존재). Cursor 실행 0건. |
| smoke_random_2000_check만 수행했는가 | PASS | num_train=10, num_valid=2, num_test=2, num_ood_per_type=2 (총 22 ep). max_steps=2000. |
| smoke_success_curriculum_v5_2000_check만 수행했는가 | PASS | num_train=20, num_valid=5, num_test=5, num_ood_per_type=5 (총 55 ep). max_steps=2000. |
| smoke validation FAIL=0인가 | PASS | random_check PASS=326/FAIL=0, success_check PASS=682/FAIL=0. |
| P1 family disjoint가 smoke에서 유지되는가 | PASS | 두 smoke 모두 OVERALL PASS. train/valid/test_id ⊂ {0,1}, ood_factor_recomb ⊂ {2,3}. |
| 사용자가 직접 실행할 full 생성 명령을 정확히 작성했는가 | PASS | §7.1 (success_v5_2000), §7.2 (random_2000). num_train=5000, num_valid=500, num_test=500, num_ood_per_type=500, max_steps=2000, 정확한 --behavior-policy. |
| root 이름이 `*_2000`으로 정확한가 | PASS | `data/rg4f_random_2000`, `data/rg4f_success_curriculum_v5_2000`. 1500 root에 2000 horizon 넣는 명령은 §7.3에서 명시적 금지. |
| train/valid만 학습에 쓰도록 명시했는가 | PASS | §12.1 표 + §13 stage mix. |
| test/OOD를 학습 금지로 명시했는가 | PASS | §12.2 표 + §12.3 평가는 별도 환경. |
| weak-oracle metadata를 model input에서 제외해야 한다고 명시했는가 | PASS | §14 명시 + §9.2 dataset 역할 정의에서 반복. |
| RG4F_2000_DATASET_COMMAND_PREP_REPORT.md를 작성했는가 | PASS | 본 문서. |

**14 항목 모두 PASS.**
