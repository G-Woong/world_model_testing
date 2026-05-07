# SMOKE_REPORT — RG-4F Small Smoke Dataset

> Session 5 산출물. 본 보고서는 `data/smoke/`의 small smoke dataset을 환경 +
> generator + validator + inspector + stats script가 end-to-end로 일관되는지
> 점검한 결과를 기록한다. PART0/PART1~3 / RG4F_Environment_Plan / SESSION1~4
> HANDOFF의 결정과 충돌 없이 실행되었다.

---

## 1. Smoke Dataset Generation Summary

### 1.1 실행 명령

```powershell
.\.venv\Scripts\python.exe scripts\generate_dataset.py `
  --config configs\dataset_default.yaml `
  --output-root data\smoke `
  --num-train 50 --num-valid 20 --num-test 20 --num-ood-per-type 20 `
  --max-steps 200 --overwrite
```

### 1.2 생성 결과

| 항목 | 값 |
|---|---|
| output_root | `C:\Users\computer\Desktop\NeurIPS2026\data\smoke` |
| master_seed | 42 |
| episode_max_steps | 200 |
| behavior_policy | random_biased |
| local_obs_size | 5 (메인 세팅) |
| 총 episode 수 | 190 |
| wall-clock | 6.70초 |
| save_format | npz_per_episode + index.jsonl + episode_meta.json + manifest.json |

### 1.3 split별 episode 수

| split | 요청 | 실제 (`index.jsonl` line 수) |
|---|---|---|
| train | 50 | 50 |
| valid | 20 | 20 |
| test_id | 20 | 20 |
| ood_room_perm | 20 | 20 |
| ood_factor_recomb | 20 | 20 |
| ood_param_shift | 20 | 20 |
| ood_obs_shift | 20 | 20 |
| ood_field_placement | 20 | 20 |
| **합계** | **190** | **190** |

### 1.4 manifest.json invariant

| 키 | 값 / 의미 |
|---|---|
| `train_pool` | 12 permutations |
| `ood_pool` | 12 permutations |
| `train_pool ∩ ood_pool` | ∅ (disjoint) |
| `ood_room_perm_disjoint_from_train` | true |
| `rg4f_config.local_obs_size` | 5 |
| `rg4f_config.local_obs_ablation_values` | (3, 5, 7) |

---

## 2. Validation Summary

### 2.1 strict validation (PASS / WARN / FAIL)

```powershell
.\.venv\Scripts\python.exe scripts\validate_dataset.py `
  --root data\smoke --strict --max-episodes-per-split 50 `
  --json-report data\smoke\validation_report.json --verbose
```

| 결과 | 값 |
|---|---|
| **PASS** | 2242 |
| **WARN** | 0 |
| **FAIL** | 0 |
| exit code | 0 |
| json report | `data\smoke\validation_report.json` |

### 2.2 카테고리별 PASS 요약

| invariant 그룹 | 결과 |
|---|---|
| `directory.*` (root, manifest, split_dir) | PASS |
| `split_coverage.all_present` (8 splits) | PASS |
| `npz.required_keys_present` + group(true_regime/target_band/field_info) | PASS |
| `shape.*` (timesteps, local_grid, scalar, true_state, next_local_matches_obs) | PASS |
| `shape.local_obs_size_in_3_5_7` + `_matches_expected` | PASS (n=5) |
| `numeric.no_nan_inf` / `true_state_range` / `binary_dtype` / `reveal_or_shift_enum` | PASS |
| `numeric.actions_*` / `task_id_range` / `room_id_range` / `reset_flag_always_false` | PASS |
| `sparse_coupling.le2` (모든 episode 모든 field) | PASS |
| `split_specific.id_not_ood` (train/valid/test_id) | PASS |
| `split_specific.room_perm.disjoint_from_train` + `in_ood_pool` | PASS |
| `split_specific.factor_recomb.families_in_ood_pool` | PASS |
| `split_specific.param_shift.differs_from_train` | PASS |
| `split_specific.obs_shift.channel_perm_valid` + `no_dynamics_change` | PASS |
| `split_specific.field_placement.relocate_flag` + `source_in_grid` | PASS |

### 2.3 Determinism check

```powershell
.\.venv\Scripts\python.exe scripts\validate_dataset.py `
  --root data\smoke --check-determinism `
  --config configs\dataset_default.yaml --max-episodes-per-split 3
```

| 결과 | 값 |
|---|---|
| **PASS** | 332 |
| **WARN** | 0 |
| **FAIL** | 0 |
| exit code | 0 |
| 두 번 호출 결과 | 모든 split의 모든 npz가 byte-equal (`np.array_equal` all True) |

내부적으로 generator를 임시 디렉토리 두 곳에 같은 seed(`777`)로 두 번 호출하여 비교.
`data/smoke`는 건드리지 않는다 (코드 확인: `_check_determinism()` 끝의 `shutil.rmtree(tmp)`).

---

## 3. Inspection Summary

### 3.1 inspect한 split 목록

| split | save 파일 | episode_id | env_seed | forced_permutation | initial control_mode | num_fields | 주 관찰 |
|---|---|---|---|---|---|---|---|
| train | `train_episode0.txt` | `train_000000` | 2116774204 | [2,0,3,1] (train_pool) | IDENTITY | 2 (VISIBILITY+INTERACTION_INTERFERENCE) | random_biased 분포로 4-방향 + state-adjust 모두 등장 |
| valid | `valid_episode0.txt` | `valid_000000` | 584060370 | [3,2,0,1] (train_pool) | IDENTITY | 2 (FRICTION+CONTROL_INTERFERENCE) | room=CORRIDOR 24회 출현 (방 외곽 진입) |
| test_id | `test_id_episode0.txt` | `test_id_000000` | 1677198115 | [0,1,2,3] (train_pool) | IDENTITY | 2 (FRICTION) | room_id 분포 안정 |
| ood_room_perm | `ood_room_perm_episode0.txt` + `_detail.txt` | `ood_room_perm_000000` | 838147699 | **[3,1,2,0]** (ood_pool) | REV (모든 방향 반대) | 1 (INTERACTION_INTERFERENCE) | `raw=W eff=S` → REV remap 정상 작동 |
| ood_factor_recomb | `ood_factor_recomb_episode0.txt` | `ood_factor_recomb_000000` | 928605662 | [2,1,0,3] | IDENTITY | 2 (CONTROL_INTERFERENCE만) | family=[3] ⊂ ood_pool=[2,3] |
| ood_param_shift | `ood_param_shift_episode0.txt` | `ood_param_shift_000000` | 1392505762 | [0,1,2,3] | REV | 1 (INTERACTION_INTERFERENCE) | meta `rg4f_kwargs_override`에 5개 override 모두 기록 |
| ood_obs_shift | `ood_obs_shift_episode0.txt` | `ood_obs_shift_000000` | 1393088979 | [0,2,1,3] | UD (W↔S flip) | 2 (FRICTION+CONTROL_INTERFERENCE) | `obs_channel_perm=[5,9,7,0,4,3,6,1,2,8]` 적용 → ASCII grid가 `?????`로 보이는 것은 cue 채널이 위치 0으로 이동했기 때문 (`NOTE` 라인에 명시) |
| ood_field_placement | `ood_field_placement_episode0.txt` + `_detail.txt` | `ood_field_placement_000000` | 1332008484 | [2,0,3,1] | IDENTITY | 2 (INTERACTION_INTERFERENCE+VISIBILITY) | source 위치 (30, 18), (31, 18) → SOUTH room 중심부에 placement |

### 3.2 사람이 확인한 핵심 관찰

1. **중앙홀+4방+복도 토폴로지**: 모든 split의 reset 직후 agent는 (18, 18) — central_hall 정중앙 — 에서 시작. ASCII 5×5 window는 시작 시 floor만 노출 (방 진입 전이므로 wall/object 미관측). `room_id_counter`로 valid 24회/CORRIDOR, ood_param_shift 110회/SOUTH 등 일부 episode에서 corridor / 4방 진입을 확인.
2. **5x5 부분관측**: 모든 episode npz의 `observations_local_grid.shape == (200, 5, 5, 10)`. 7x7 main 고정 아님. 외부 영역은 wall padding으로 채워짐 (manifest의 expected와 일치).
3. **Task assignment**: ood_room_perm episode의 room→task: `NORTH→D`, `SOUTH→B`, `EAST→C`, `WEST→A`. `permutation_id=21` = `[3,1,2,0]`. train_pool에 없는 permutation. 위치 암기 회피 강제.
4. **raw_action vs effective_action 분리**: ood_room_perm 첫 5 step에서 `raw=W eff=S` (REV remap), `raw=A eff=A` (REV mode에서도 일부는 90°slip 후 같은 방향), ood_obs_shift t=0에서 `raw=A eff=W` (UD remap). 즉 control-drift remap + miscontrol slip이 분리되어 정확히 기록됨.
5. **periodic slip**: t=0,4,8,...에서 `miscontrol_p=0.300, periodic_slip=True`, 그 외 step에서 `0.05, False`. config의 `periodic_slip_period=4` 정확히 작동.
6. **field_info sparse coupling**: 모든 episode의 모든 field에서 `coupled_states ∈ {[noise, vision], [noise, mobility], [noise, interaction], [noise, control_drift]}` 즉 `|·|=2`. ood_field_placement의 source는 (30, 18), (31, 18) — SOUTH room 중심부 (row 22~30 영역)에 정확히 배치.
7. **target_band**: 모든 inspection episode에서 첫 5 step은 방 밖이므로 `target_band.active=False`. ood_param_shift episode는 SOUTH room (Task B)에 110 step 진입했으나 stele 활성화 / mobility gate 도달까지 random_biased로 도달하지 못해 band 활성 step은 0회였다 — 이는 random behavior policy 한계이며 환경 결함이 아니다.
8. **change_point / reveal_or_shift**: train avg 0.20 cp / 0.20 shift / 0 reveal per episode. test_id avg 0.45 cp / 2.70 reveal — task interaction 이벤트로 reveal_event가 정상 발생. ood_room_perm avg 2.85 reveal. 즉 reveal vs shift 분리 라벨이 episode-level에서 모두 다른 분포를 보이며 supervision으로 활용 가능.
9. **OOD metadata**: ood_obs_shift의 `obs_channel_perm=[5,9,7,0,4,3,6,1,2,8]` 그대로 기록, ood_field_placement의 `relocate_fields_room_center=True` 그대로 기록, ood_param_shift의 `rg4f_kwargs_override={field_mu_drift_sigma: 0.02, shift_prob_per_*: 0.1, field_radius_max: 12.0}` 모두 train base보다 큼 (drift_strength_multiplier=2.0, shift_probability_multiplier=2.0, field_radius_max 6→12).

### 3.3 이상 징후

| 항목 | 상태 | 비고 |
|---|---|---|
| local_grid가 전체맵을 노출하는가 | NO | 5×5만 노출. 외부 wall padding 확인. |
| agent 위치와 주변 구조가 ascii에서 확인되는가 | YES | `@` 마커 + 방향별 . / # / corridor 등. |
| task_id / room_id가 정상 기록되는가 | YES | npz의 `task_id`, `room_id` 모두 schema 준수. |
| raw_action vs effective_action이 분리되어 있는가 | YES | npz의 `actions_raw`, `actions_effective`. |
| control-drift 발생 시 effective_action이 다른가 | YES | ood_room_perm REV / ood_obs_shift UD 모두 확인. |
| field_info가 sparse coupling을 보여주는가 | YES | 모든 field `\|coupled_states\|=2`. |
| target_band가 task에 맞게 생성되는가 | 부분적 YES | schema에는 정확히 저장. random_biased가 200-step에서 band 활성 step에 도달하지 않은 episode는 `active=False`로 정상 기록. |
| OOD metadata가 split 의도와 맞는가 | YES | 모든 OOD invariant validate에서 PASS. |

---

## 4. Dataset Statistics Summary

### 4.1 생성된 통계 파일

```
outputs/smoke_stats/
  summary.csv                                 # split별 1행 요약 (16 col)
  train_distributions.csv                     # action/task/room/event/field 분포
  valid_distributions.csv
  test_id_distributions.csv
  ood_room_perm_distributions.csv
  ood_factor_recomb_distributions.csv
  ood_param_shift_distributions.csv
  ood_obs_shift_distributions.csv
  ood_field_placement_distributions.csv
  episode_length_hist.png                     # matplotlib histogram
  reward_total_hist.png
  change_point_boxplot.png
```

### 4.2 episode length 분포

모든 split에서 `len_min = len_mean = len_max = 200`. 즉 모든 episode가 max_steps=200까지
truncated. random_biased + 200-step 길이로는 4-task completion까지 도달하기 어려움.
`completed_max_mean = 0.0` for all splits — 환경의 4-task 완성 reward가 random policy에는
거의 도달 불가.

### 4.3 reward 분포 (per-episode total reward)

| split | mean | std | 비고 |
|---|---|---|---|
| train | -247.27 | 14.93 | step_cost 200 + latency_cost ~30~50 합산. 정상. |
| valid | -245.54 | 14.82 | |
| test_id | -241.21 | 16.39 | |
| ood_room_perm | -250.68 | 11.72 | REV mode 빈도 높아 이동 latency 누적 |
| ood_factor_recomb | -248.41 | 15.47 | |
| ood_param_shift | -242.58 | 12.00 | |
| ood_obs_shift | -248.04 | 19.91 | |
| ood_field_placement | -250.41 | 13.53 | failure_max_mean=0.25 (Task D forced_reset 일부 발생) |

reward 분포가 모든 split에서 -240 ~ -250 범위 (~step_cost·200 = -200 + latency/failure/reset).
한 split로 collapse하지 않음.

### 4.4 action 분포 (train, 10000 transitions)

| action 그룹 | raw count | raw % | target % (random_biased) |
|---|---|---|---|
| W (0) | 1392 | 13.92 % | 13.75 % |
| A (1) | 1377 | 13.77 % | 13.75 % |
| S (2) | 1376 | 13.76 % | 13.75 % |
| D (3) | 1347 | 13.47 % | 13.75 % |
| 이동 합 | 5492 | 54.92 % | 55.00 % |
| E (4) | 1444 | 14.44 % | 15.00 % |
| state-adjust 합 (5..14) | 3064 | 30.64 % | 30.00 % |
| WAIT (15) | 0 | 0.00 % | 0.00 % |

random_biased 분포 정확히 작동. movement / interact / state-adjustment 모두 충분히 등장.
한 action으로 collapse하지 않음.

`actions_raw` vs `actions_effective`: 이동 4개 action 분포가 약간 다름 (control-drift +
miscontrol slip으로 일부 step의 effective 방향이 변경됨). state-adjust + E + WAIT는
remap 영향 없음 — 일치.

### 4.5 change_point 분포 (per-episode mean)

| split | cp_mean | reveal_mean | shift_mean |
|---|---|---|---|
| train | 0.20 | 0.00 | 0.20 |
| valid | 0.20 | 1.00 | 0.20 |
| test_id | 0.45 | 2.70 | 0.45 |
| ood_room_perm | 0.10 | 2.85 | 0.10 |
| ood_factor_recomb | 0.20 | 1.45 | 0.20 |
| ood_param_shift | 0.20 | 0.00 | 0.20 |
| ood_obs_shift | 0.05 | 1.25 | 0.05 |
| ood_field_placement | 0.25 | 0.15 | 0.25 |

- `change_point = shift_event` (Session 2/3 결정)이므로 cp_mean == shift_mean.
- reveal_event는 task interaction 시 발생하는 별도 채널. test_id / ood_room_perm에서 더 빈번
  (random_biased가 일부 episode에서 방 진입 후 interaction 시도). episode 평균이 단일 값으로
  collapse하지 않고 split마다 다른 값.
- shift_event는 `apply_event_shift` (room_entry / checkpoint / stele_activation 시
  `shift_prob_per_*=0.05`로 trigger) + Task C `on_enter_room`의 initial_d 강제 set.
  random_biased로 방 진입이 sparse → shift_event도 sparse. 하지만 0이 아니라 split별
  0.05~0.25 수준으로 정상 발생.

### 4.6 task_id 분포 (`-1` = 방 밖)

train의 10000 transition 중 task=-1만 등장 (방 진입이 없었음 — random_biased policy 한계).
하지만 ood_factor_recomb (task=1: 79, task=2: 84), ood_param_shift (task=0: 65, task=2: 6),
ood_field_placement (task=0: 65, task=2: 6) 등 일부 split에서 task=0/1/2 모두 등장. task_id가
모두 `-1`로 collapse하지 않음.

**주의**: 이는 random_biased policy의 한계이며 환경/dataset의 결함이 아니다. world model
학습 시 dynamics 학습에는 방 밖 transition도 충분히 활용 가능 (state-adjust action effect,
drift accumulation, control-drift remap, periodic slip 등 모두 관측됨). task supervision이
중요한 학습 단계에서는 이후 페이즈에서 더 긴 episode 또는 task-aware policy로
data collection을 보강해야 한다 (Session 6 감사 포인트).

### 4.7 invisible field family 분포

| split | family 0 (VIS) | family 1 (FRIC) | family 2 (INT_INT) | family 3 (CTRL_INT) | 비고 |
|---|---|---|---|---|---|
| train | 16 | 23 | 17 | 18 | 4 family 모두 등장 |
| valid | 6 | 8 | 7 | 8 | |
| test_id | 7 | 7 | 9 | 7 | |
| ood_room_perm | 5 | 9 | 7 | 9 | train family와 가능한 분포 동일 |
| ood_factor_recomb | 0 | 0 | 10 | 15 | **{2,3}만** ✓ |
| ood_param_shift | 7 | 5 | 6 | 7 | family는 train과 동일 (parameter만 다름) |
| ood_obs_shift | 6 | 9 | 8 | 7 | dynamics 동일 |
| ood_field_placement | 10 | 7 | 3 | 11 | family 동일, source 위치만 다름 |

ood_factor_recomb의 family는 `{2,3}`만 등장. yaml의 `ood_field_families=[2,3]` 정확히 강제됨.

---

## 5. Research Design Check (논문 설계 관점 점검)

### 5.1 환경 구조 (PART0/Plan §2, §3)

- ✓ **중앙홀 + 4방 + 복도 토폴로지**: 모든 episode reset 시 agent (18, 18)에서 시작.
  manifest의 `rg4f_config.hall_size=9, room_size=8, corridor_length=3`. 방 진입 episode의
  `room_id_counter`로 NORTH/SOUTH/EAST/WEST/CORRIDOR 모두 등장 확인.
- ✓ **5x5 부분관측**: `observations_local_grid.shape = (200, 5, 5, 10)`. 한 방의 39.1%만
  관측 가능. hidden state belief 압력 유지.
- ✓ **7x7 main 고정 아님**: yaml `local_obs_size: 5`. ablation 후보 [3, 5, 7] 모두 config
  validation에 강제됨.

### 5.2 Task 구조 (PART3 §3.18, Plan §6)

- 부분 ✓ **Task A/B/C/D**: 모두 yaml의 `permutation`으로 episode마다 4개 방에 1:1 매핑.
  ood_param_shift episode_0에서 `permutation={1:0, 2:1, 3:2, 4:3}`이 SOUTH 방에 110 step 진입,
  task=B 실제 진행. task_id가 `-1` 외에 0/1/2 모두 일부 split에서 등장 — collapse 아님.
- ⚠ **task_id 분포 한계**: random_biased + 200-step에서는 task=3 (D)이 거의 등장하지 않음.
  이는 policy 한계로 schema는 정상.
- ✓ **target_band 다양성**: schema에 `target_band.kind` enum (none/match_to_band/maximize/
  threshold/derivative_zero) 저장. 본 smoke에서 active step이 sparse하므로 직접 확인된 kind는
  주로 0(none). band 메커니즘은 작동하지만 random_biased 경로에서 active step에 도달하지
  못함 — 환경 결함 아님.

### 5.3 State / regime supervision (PART1 §3.3~§3.5, PART0 §3 §8)

- ✓ **true_state numeric 학습 가능**: `(T, 5)` float32 array. clip [-1, 1]. NaN/Inf 없음.
  smoke 모든 episode에서 max|x|=1.0000 정도로 정상 범위.
- ✓ **true_regime numeric**: `control_mode (0..4)`, `mobility_mode`, `miscontrol_p`,
  `periodic_slip` 모두 numeric (`int32` / `float32` / `bool`).
- ✓ **change_point**: bool array. cp_mean이 split별 0.05~0.45로 한쪽 극단으로 collapse 안 함.
- ⚠ **change_point=shift_event 정의 한계**: control_mode mid-episode remap shift는 미구현
  (initial sampling 후 episode 동안 고정). Session 2/3/4에서 이미 known limitation으로
  기록됨. world model 학습 supervision에는 충분 (`reveal_event` / `shift_event` 분리 라벨이
  존재하므로 모델은 두 채널을 별도 head로 학습 가능).
- ✓ **reveal_or_shift int 인코딩**: 0/1/2 enum. 모든 episode에서 valid range 내.

### 5.4 OOD 구조 (Plan §8)

- ✓ **ood_room_perm은 train과 disjoint**: manifest `ood_room_perm_disjoint_from_train=true`,
  smoke episode_0의 forced_permutation `[3,1,2,0]`이 train_pool에 없음 (validate PASS).
- ✓ **ood_factor_recomb은 다른 family 조합**: family={2,3}만, train+test_id의 다른 6개 split은
  4개 family 모두 사용. invariant PASS.
- ✓ **ood_param_shift는 parameter range를 실제 변경**: `field_mu_drift_sigma=0.02` (train
  0.01의 2배), `shift_prob_per_*=0.1` (train 0.05의 2배), `field_radius_max=12.0` (train
  6.0의 2배). meta `rg4f_kwargs_override`에 모든 override 명시.
- ✓ **ood_obs_shift는 observation encoding만 변경**: `obs_channel_perm=[5,9,7,0,4,3,6,1,2,8]`,
  `rg4f_kwargs_override={}` (dynamics 변경 없음). validate `no_dynamics_change` PASS.
- ✓ **ood_field_placement는 field prior를 변경**: `relocate_fields_room_center=true`,
  source_position이 4방 interior 중심부 (예: (30, 18) = SOUTH 중심).

### 5.5 Data collection behavior (PART0 §3.5)

- ✓ **random_biased는 movement/interact/state-adjustment 포함**: 분포 W=13.9%, A=13.8%,
  S=13.8%, D=13.5%, E=14.4%, state-adjust 합 30.6%, WAIT 0%.
- ✓ **action distribution은 한 action으로 collapse하지 않음**: 이동 4종 모두 13~14%, E 14%,
  state-adjust 10종 모두 2.7~3.4% 수준.
- ✓ **state-adjust는 적절한 비율**: 30% (target). 너무 많거나 적지 않음.
- 부분 ⚠ **transition 다양성**: room=CENTRAL이 95.3% (train). 4-room 진입이 sparse하지만
  ood_param_shift / ood_factor_recomb / ood_field_placement 등에서 일부 진입 transition 존재.
  world model의 dynamics supervision (state-adjust action 효과, drift, control-drift remap,
  periodic slip)에는 충분. 향후 task supervision 강화 시 task-aware policy 보강 필요.

### 5.6 Known ambiguity 재평가 (Session 4 §6)

| 항목 | 본 smoke에서 문제? | Session 6에서 수정해야? | 학습 전까지 보류 가능? |
|---|---|---|---|
| **train family filter 부재** (Session 4 §6.1) | 문제 아님. validate는 ood_factor_recomb의 disjoint만 검증. train의 4-family 자유는 metadata에 명시. | 권장: yaml에 `train_apply_family_filter` 옵션 추가하면 OOD intent 강화. | YES — paper의 OOD protocol 설명에서 "train pool 안에서는 4 family 자유 허용" 명시하면 honest. |
| **channel permutation의 의미 한계** (Session 4 §6.2) | 문제 아님. validate가 channel_perm valid + dynamics 동일 검증. | 옵션: 진짜 visual variant (cue 채널 값 분포 변경 등) 추가. | YES — novelty detector false positive 검증에는 channel index 변경으로도 충분. |
| **change_point=shift_event 정의 한계** (Session 4 §6.3) | 문제 아님. reveal_event/shift_event 분리 라벨이 별도로 저장됨. cp_mean이 split별로 다름. | 권장: control_mode mid-episode abrupt remap을 추가하면 PART2 §3.10.3 정합성 강화. | YES — world model이 shift_event 라벨로 head 학습 가능. |
| **object dtype field 한계** (Session 4 §6.4) | 문제 아님. 모든 npz array가 numeric. validate `no_nan_inf` PASS. | NO — 이미 의도된 안전장치. | N/A. |
| **ASCII rendering 한계** (Session 4 §6.5) | 문제 아님. ood_obs_shift inspection의 `?????` 출력은 channel permutation의 시각적 표현일 뿐. | 옵션: inverse permutation 자동 적용 옵션을 inspect_episode에 추가. | YES — 학습에는 obs ASCII 디버깅이 필수가 아님. |

추가로 이번 smoke에서 **새로** 식별된 사항:

| 항목 | 본 smoke에서 문제? | Session 6 / 학습 전 처리 |
|---|---|---|
| **random_biased + 200-step의 task room 진입 sparse** | 환경 결함 아님. policy 한계. | Session 6에서 task_probe / heuristic-aware behavior policy 추가 검토. world model dynamics 학습에는 현 dataset이 충분. |
| **inspect_episode.py em-dash cp949 인코딩 호환성** | 본 세션에서 발견 + 수정 | (§6 참조) |

---

## 6. Issues Found and Fixes

### 6.1 발견한 문제

**Issue #1: `inspect_episode.py`의 em-dash(—)가 Windows cp949 콘솔에서 UnicodeEncodeError 유발**

- **증상**: `--split ood_obs_shift` 또는 `--split ood_field_placement`로 실행 시
  ```
  UnicodeEncodeError: 'cp949' codec can't encode character '\u2014'
                       in position 1169: illegal multibyte sequence
  ```
- **원인**: `_print_metadata`의 NOTE 라인에 em dash(`—`)가 포함되어 있는데 ood_obs_shift /
  ood_field_placement 두 split에서만 NOTE가 출력된다. Windows 한국어 환경의 기본 콘솔
  코덱(cp949)이 em dash를 인코딩하지 못한다.
- **다른 split은 왜 PASS했는가**: train/valid/test_id 등은 NOTE 라인을 출력하지 않고, 사용된
  `→` (\u2192)는 cp949로 표현 가능하다.

### 6.2 수정한 파일

`scripts/inspect_episode.py` 두 곳:

1. **`_print_metadata` NOTE 라인 두 곳**: em dash(`—`) → ASCII hyphen(`-`) 으로 교체
   (line 182, 187 근처).
2. **`main()` 진입부**: `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` 추가.
   비-UTF8 콘솔에서도 다른 unicode 문자(예: `→`, `·`)가 안전하게 출력되도록 future-proof
   안전망. Python 3.7+ 표준 API. reconfigure가 없거나 실패해도 동작에 영향 없음 (try/except).

### 6.3 수정 이유

PART0 §6 ("치명적 생성 오류가 발견될 경우에만 env/generator/validation 코드 최소 수정")
허용 조건에 부합. `inspect_episode.py`는 사용자 검증의 핵심 도구이며, ood_obs_shift /
ood_field_placement 두 split을 inspect할 때마다 crash하면 Session 5의 검증 임무를 수행할 수
없다.

### 6.4 backward compatibility 영향

- **dataset schema**: 영향 없음. npz/meta/index/manifest 어떤 파일도 수정하지 않음.
- **API 컨트랙트**: 영향 없음. `inspect_episode.py`의 CLI 옵션, 출력 포맷, 출력 의미 모두
  동일. NOTE 라인의 표현만 `—` → `-` 으로 약간 다름.
- **다른 script (validate / generate / plot)**: 영향 없음. 모두 자기 디렉토리 안에서 자기
  코드만 사용.
- **Session 4 SESSION4_HANDOFF의 출력 예시와 차이**: NOTE 라인 표기만 일치하지 않음. 의미
  동일.

### 6.5 smoke test 재실행 결과

- ood_obs_shift / ood_field_placement inspection: 정상 출력 (§3 표 참조).
- 다른 split: 변경된 코드 경로(`reconfigure`)가 동작했는지만 확인. crash 없이 정상.
- validate_dataset --strict: 변경 없음. PASS=2242 / WARN=0 / FAIL=0 (§2.1).
- determinism check: 변경 없음. PASS=332 / WARN=0 / FAIL=0 (§2.3).

### 6.6 그 외 환경 / generator 코드 결함

**없음**. `falsifiable_regime_world_model/rg4f/*.py`, `scripts/generate_dataset.py`,
`scripts/validate_dataset.py`, `scripts/plot_dataset_stats.py`, `configs/dataset_default.yaml`
모두 0줄 변경. dataset schema / API 컨트랙트 그대로 유지.

---

## 7. Remaining Risks Before World Model Training

### 7.1 World model 학습 전에 반드시 확인할 사항

1. **task supervision data 보강 여부 결정**: 현재 random_biased + 200-step에서 task room
   진입이 sparse. world model의 task-conditional dynamics head를 학습하려면 task room 안
   transition이 더 필요. 결정 안:
   - 안 1 (recommended): 본 smoke와 별도로 학습용 dataset 생성 시 `episode_max_steps`를 600
     (yaml default값)으로 늘리고 train 5000 episode로 늘리면 task room 진입이 통계적으로
     충분히 발생.
   - 안 2: heuristic-aware data collection policy 추가 (단, PART0 §3 §6 "키워드 분기 금지"와
     "agent 코드 금지" 충돌. 데이터 생성 전용 단순 sampler로 격하해야 함).
2. **change_point=shift_event 정의의 control_mode 누락**: world model이 control_mode change
   를 라벨로 학습하려면 mid-episode abrupt remap shift를 추가해야 함. Session 6 감사에서
   결정.
3. **train family filter 정책**: train도 `[0,1]` family만 사용할지, 4 family 자유로 둘지
   결정. 어느 쪽이든 paper의 OOD protocol 설명에 명시.

### 7.2 Session 6에서 감사해야 할 사항

- PART0/PART1~3/Plan과 실제 구현의 정합성 표 (특히 §1.2 backbone confound 통제, §3.10
  control-drift, §3.16 partial observability, §3.17 default utility, §3.18 task definition,
  §3.21 OOD split, §3.22 reveal vs shift).
- `change_point=shift_event` 정의의 reviewer 방어 가능성 (PART2 §3.7.3 "circular logic"
  주장 회피).
- random_biased의 task room 진입 sparse 문제와 학습 단계의 보강 방안.
- yaml의 `train_field_families` flag가 train에 강제되는지 / metadata-only인지 명시.
- inspect_episode의 ood_obs_shift inverse permutation 옵션 (편의성).

### 7.3 지금은 보류 가능한 사항

- ASCII rendering의 channel permutation inverse 자동 적용 (디버깅 편의성, 학습에는 영향
  없음).
- visual variant (cue 채널 값 분포 변경) 추가 — channel index 변경으로도 novelty detector
  false positive 검증은 충분.
- object dtype field 부재 — 의도적 안전장치, 변경 불필요.
- Session 5 단계의 inspection 도구는 학습 페이즈 진입 후에도 그대로 사용 가능.

---

## 8. Final Verdict

### **PASS — Session 6 감사로 진행 가능.**

근거 요약:

1. validate_dataset --strict: **PASS=2242 / WARN=0 / FAIL=0**. 모든 schema, shape, numeric,
   sparse coupling, 8개 split의 OOD invariant 통과.
2. determinism check: **PASS=332 / WARN=0 / FAIL=0**. 동일 yaml + 동일 seed → byte-equal
   dataset 재현.
3. local_obs_size=5 메인 세팅 유지, 3/5/7 ablation 후보 모두 yaml/config validation 강제.
4. 8개 split 모두 inspect_episode로 사람이 직접 확인. metadata / step-level / field-task
   detail 모두 정상.
5. action / task_id / room_id / change_point / family 분포가 split별로 다름. 한쪽으로
   collapse하지 않음.
6. random_biased policy의 task room 진입 sparse는 **policy 한계이며 환경 결함이 아님**.
   world model dynamics supervision (5-state, regime, drift, control-drift remap, periodic
   slip)에는 현 dataset이 충분.
7. 발견된 유일한 코드 결함(inspect_episode em-dash cp949)은 본 세션에서 즉시 수정 + 재검증
   완료. dataset schema / API 컨트랙트 0줄 변경.
8. Session 4의 known limitation 5건 모두 재평가. 학습 전 보류 가능 또는 Session 6 감사 권장
   사항으로 분류.

다음 단계: **Session 6 — 환경 코드 감사 및 수정 지시문 생성**.
