# SESSION 3 → SESSION 4 Handoff

> 본 문서는 다음 Cursor 세션이 이전 대화 맥락 없이 단독으로 Session 4 (inspection /
> validation script 구현)를 시작할 수 있도록 작성된 인계 문서다. 본 문서만으로 Session
> 4의 모든 결정 근거가 추적 가능해야 한다.

---

## 1. 본 세션에서 생성/수정한 파일

### 생성

| 경로 | 목적 |
|---|---|
| `configs/dataset_default.yaml` | dataset generator의 default config. project / generation / environment / splits / split_policy / metadata 5개 섹션. RG4F_Environment_Plan §9 / 사용자 요구사항 §3 모두 반영. |
| `scripts/generate_dataset.py` | yaml + CLI를 받아 train/valid/test_id/5개 OOD split의 episode dataset을 디스크에 저장하는 메인 스크립트. behavior policy(random_uniform/random_biased), split-aware permutation pool, OOD 차별화 정책을 모두 책임. |
| `falsifiable_regime_world_model/rg4f/serialization.py` | `EpisodeBuffer` 클래스. step-단위 transition을 모아 numeric `np.savez_compressed` 친화적 array dict + episode_meta dict로 변환. info dict 전체를 object dtype으로 dump하지 않는다. |
| `docs/SESSION3_HANDOFF.md` | 본 문서. |

### 수정 (backward-compatible)

| 경로 | 수정 이유 |
|---|---|
| `falsifiable_regime_world_model/rg4f/config.py` | `RG4FConfig.forced_permutation: Optional[Tuple[int,int,int,int]] = None` 필드 추가. None이면 기존 random shuffle (Session 2 호환). 외부에서 split-aware permutation을 강제 주입하기 위함. `__post_init__`에서 길이 4 + 정확한 (0,1,2,3) permutation 검증. |
| `falsifiable_regime_world_model/rg4f/map_generator.py` | `sample_room_task_permutation(rng, forced=None)` 시그니처 확장. forced가 주어지면 그 값을 사용. `build_episode`가 `config.forced_permutation`을 그대로 forwarding. 기존 reset/step API는 변경 없음. |

### 수정 안 함

- `ref/PART0_IMPLEMENTATION_STRATEGY.md`, `ref/PART1_PROBLEM_FRAMING.md`,
  `ref/PART2_ALGORITHM.md`, `ref/PART3_EXPERIMENT_DESIGN.md` — 0줄 변경.
- `docs/RG4F_Environment_Plan.md`, `docs/SESSION1_HANDOFF.md`, `docs/SESSION2_HANDOFF.md` — 0줄 변경.
- `requirements.txt` — 0줄 변경. Session 3는 `numpy 2.1.3` / `pyyaml 6.0.3` /
  `tqdm 4.67.3`만 사용.
- `falsifiable_regime_world_model/rg4f/{types,observation,fields,tasks,env}.py` — 0줄 변경.
  reset/step/observe/info API 컨트랙트 그대로 유지.

### Session 3에서 명시적으로 수행하지 않은 것 (PART0 §3 / 사용자 요구사항 §1)

- `scripts/inspect_episode.py`, `scripts/validate_dataset.py` 어떤 것도 생성하지 않음 (Session 4 책임).
- 모델 / agent / planner / world model / RSSM / GRU-lite / DreamerV3 / SOTA backbone 코드 0줄.
- 학습 loop, optimizer, training run 0줄.
- 대규모 dataset 생성 (smoke 단위만, 모든 명령 5초 이내 종료).

---

## 2. Dataset generator 사용법

### 2.1 기본 실행

```powershell
.\.venv\Scripts\python.exe scripts\generate_dataset.py --config configs\dataset_default.yaml
```

이는 `configs/dataset_default.yaml` 기본값 (`num_train=20`, `num_valid=5`,
`num_test=5`, `num_ood_per_type=5`, `episode_max_steps=200`)으로 8개 split 모두 생성한다.

### 2.2 dry-run (config 검증만)

```powershell
.\.venv\Scripts\python.exe scripts\generate_dataset.py --config configs\dataset_default.yaml --dry-run
```

dry-run은 다음을 stdout에 출력하고 IO 없이 종료:
- 입력 config 경로 / output_root / master_seed
- train_pool / ood_pool 의 disjoint 확인
- 변환된 RG4FConfig 모든 필드의 resolved 값
- 각 split의 SplitPlan 요약 (perm_pool_size, rg4f_override, field_family_pool,
  obs_channel_perm, relocate_fields_room_center)

### 2.3 small smoke dataset (사용자 요구사항 §8)

```powershell
.\.venv\Scripts\python.exe scripts\generate_dataset.py --config configs\dataset_default.yaml `
  --num-train 2 --num-valid 1 --num-test 1 --num-ood-per-type 1 --max-steps 50 --overwrite
```

### 2.4 단일 split만 생성

```powershell
.\.venv\Scripts\python.exe scripts\generate_dataset.py --config configs\dataset_default.yaml `
  --split train --num-train 5 --max-steps 100 --overwrite
```

### 2.5 CLI 전체 옵션

| 옵션 | 의미 |
|---|---|
| `--config <path>` | yaml config 경로 (필수) |
| `--output-root <path>` | yaml의 `project.output_root` override |
| `--seed <int>` | yaml의 `generation.seed` override |
| `--num-train <int>` | yaml의 `generation.num_train` override |
| `--num-valid <int>` | yaml의 `generation.num_valid` override |
| `--num-test <int>` | yaml의 `generation.num_test` (test_id) override |
| `--num-ood-per-type <int>` | 5개 OOD split 각각의 episode 수 |
| `--max-steps <int>` | yaml의 `generation.episode_max_steps` override |
| `--overwrite` | 기존 output_root가 있으면 split 폴더만 삭제 후 덮어쓰기 |
| `--dry-run` | config plan만 출력. 어떤 IO도 일으키지 않음 |
| `--split <name>` | 단일 split만 생성 (yaml의 splits 리스트 안에 있어야 함) |

### 2.6 overwrite 주의사항

- `--overwrite` 또는 yaml의 `project.overwrite=true` 없이 `output_root`가 이미 존재하면
  exit code 2와 명확한 에러 메시지로 중단한다 (실수로 기존 데이터를 덮어쓰지 않게).
- `--overwrite`는 yaml의 `splits` 리스트에 명시된 split 폴더와 `manifest.json`만 삭제한다.
  `output_root` 안의 다른 user 파일은 건드리지 않는다.

---

## 3. 저장 구조

### 3.1 디렉토리 트리

```
data/rg4f/
  manifest.json
  train/
    index.jsonl
    episodes/
      train_000000.npz
      train_000000.meta.json
      train_000001.npz
      train_000001.meta.json
  valid/
    index.jsonl
    episodes/
      valid_000000.npz
      valid_000000.meta.json
  test_id/
    index.jsonl
    episodes/...
  ood_room_perm/
    index.jsonl
    episodes/...
  ood_factor_recomb/
    index.jsonl
    episodes/...
  ood_param_shift/
    index.jsonl
    episodes/...
  ood_obs_shift/
    index.jsonl
    episodes/...
  ood_field_placement/
    index.jsonl
    episodes/...
```

### 3.2 episode npz key (저장된 모든 numeric array)

| key | shape | dtype | 의미 |
|---|---|---|---|
| `observations_local_grid` | `(T, n, n, 10)` | `float32` | 현재 obs의 local window. n=local_obs_size. C=10 (LOCAL_CHANNELS). |
| `observations_scalar` | `(T, 14)` | `float32` | 현재 obs의 scalar 벡터. |
| `observations_event_token` | `(T,)` | `int32` | 현재 obs의 event token. |
| `next_observations_local_grid` | `(T, n, n, 10)` | `float32` | 다음 obs의 local window. |
| `next_observations_scalar` | `(T, 14)` | `float32` | 다음 obs의 scalar. |
| `next_observations_event_token` | `(T,)` | `int32` | 다음 obs의 event token. |
| `actions_raw` | `(T,)` | `int32` | agent가 보낸 raw action. |
| `actions_effective` | `(T,)` | `int32` | control-drift remap + miscontrol slip 적용 후 실제 효과 action. |
| `rewards` | `(T,)` | `float32` | step별 합산 reward (`task_reward + completion_reward − Σ λ * cost`). |
| `dones` | `(T,)` | `bool` | terminated 플래그. |
| `truncateds` | `(T,)` | `bool` | truncated 플래그. |
| `true_state` | `(T, 5)` | `float32` | (vision, mobility, interaction, noise, control_drift). obs에 노출되지 않는 5차원 hidden state ground-truth. |
| `true_regime_control_mode` | `(T,)` | `int32` | `ControlMode` enum (0=IDENTITY/1=CW/2=LR/3=UD/4=REV). |
| `true_regime_mobility_mode` | `(T,)` | `int32` | `MobilityMode` enum. |
| `true_regime_miscontrol_p` | `(T,)` | `float32` | 본 step의 miscontrol 확률 (periodic slip 적용 후). |
| `true_regime_periodic_slip` | `(T,)` | `bool` | 본 step이 periodic slip이 발동한 step인지. |
| `change_point` | `(T,)` | `bool` | regime transition (현재 정의: shift_event와 동일). |
| `reveal_event` | `(T,)` | `bool` | hidden state가 새로 드러난 event (PART0 §3 §8 분리 라벨). |
| `shift_event` | `(T,)` | `bool` | regime/parameter가 변한 event (분리 라벨). |
| `reveal_or_shift` | `(T,)` | `int32` | 인코딩: 0=none, 1=reveal, 2=shift. |
| `task_id` | `(T,)` | `int32` | 현재 활성 task. 방 밖이면 -1. |
| `room_id` | `(T,)` | `int32` | 현재 위치한 영역. `RoomID` enum. |
| `event_token` | `(T,)` | `int32` | step에서 발생한 가장 의미 있는 event. |
| `target_band_active` | `(T,)` | `bool` | 본 step에 활성 target band가 있는지. |
| `target_band_state_dim` | `(T,)` | `int32` | active일 때 어느 state dim에 적용되는지. inactive면 -1. |
| `target_band_center` | `(T,)` | `float32` | band center τ. |
| `target_band_half_width` | `(T,)` | `float32` | band half-width α. |
| `target_band_kind` | `(T,)` | `int32` | 인코딩: 0=none, 1=match_to_band, 2=maximize, 3=threshold, 4=derivative_zero. |
| `field_info_mu` | `(T, F)` | `float32` | 모든 invisible field의 step별 mu. F = episode 시작 시 결정된 field 수. |
| `field_info_sigma` | `(T, F)` | `float32` | 동일 구조의 sigma. |
| `agent_position` | `(T, 2)` | `int32` | (row, col). |
| `completed_tasks` | `(T,)` | `int32` | 0..4. |
| `failure_count` | `(T,)` | `int32` | interaction failure 누적. |
| `tick_cost` | `(T,)` | `float32` | 본 step의 step_cost (config.step_cost echo). |
| `latency_cost` | `(T,)` | `float32` | reward decomposition의 latency_cost. |
| `failure_cost` | `(T,)` | `float32` | reward decomposition의 failure_cost. |
| `reset_cost` | `(T,)` | `float32` | reward decomposition의 reset_cost. |
| `task_reward` | `(T,)` | `float32` | reward decomposition의 task_reward. |
| `completion_reward` | `(T,)` | `float32` | 4 task 모두 완료 시 부과되는 reward. |
| `reset_flag` | `(T,)` | `bool` | reset 직후 step이면 True. step 결과에서는 항상 False. |

**중요**: 모든 array는 numeric (float32/int32/bool). object dtype 사용 안 함. info dict
전체를 그대로 dump하지도 않는다 (사용자 요구사항 §2).

### 3.3 episode_meta.json schema (각 episode npz와 같은 폴더에 저장)

| key | type | 의미 |
|---|---|---|
| `episode_length` | int | T |
| `episode_seed` | int | 본 episode가 사용한 env reset seed |
| `permutation` | dict[int, int] | 본 episode의 room_id → task_id assignment |
| `initial_regime` | dict | reset 직후 regime ground-truth 요약 |
| `num_invisible_fields` | int | F |
| `field_info_static` | list[dict] | 각 field의 정적 정보: family, source_row, source_col, radius, sigma_init, coupled_states |
| `obs_local_shape` | list[int] | (n, n, C) |
| `obs_scalar_dim` | int | scalar 벡터 길이 (14) |
| `split` | str | split 이름 |
| `is_ood` | bool | OOD split 여부 |
| `ood_type` | str / null | "room_perm" / "factor_recomb" / "param_shift" / "obs_shift" / "field_placement" / null |
| `permutation_id` | int | 4! = 24 permutation 중 lexicographic index |
| `forced_permutation` | list[int] | 본 episode에 강제된 4-tuple |
| `env_seed` | int | env.reset 호출 시 사용한 seed |
| `action_seed` | int | behavior policy의 action sampling seed |
| `behavior_policy` | str | "random_uniform" / "random_biased" |
| `action_probs` | list[float] | 본 episode의 16-action 확률 분포 |
| `rg4f_kwargs_override` | dict | 본 split의 RG4FConfig override 키 |
| `field_family_pool` | list[int] / null | ood_factor_recomb 전용 |
| `obs_channel_perm` | list[int] / null | ood_obs_shift 전용. 적용된 channel permutation |
| `relocate_fields_room_center` | bool | ood_field_placement에서 True |
| `debug_trace` | list[dict] | optional. step별 (miscontrolled, move_attempted, …) flag |

### 3.4 index.jsonl schema (split별 한 줄당 한 episode)

```json
{
  "episode_id": "train_000000",
  "split": "train",
  "is_ood": false,
  "ood_type": null,
  "npz_path": "train/episodes/train_000000.npz",
  "meta_path": "train/episodes/train_000000.meta.json",
  "episode_length": 200,
  "permutation_id": 17,
  "forced_permutation": [3, 2, 0, 1],
  "env_seed": 581102213,
  "num_invisible_fields": 1
}
```

`npz_path` / `meta_path`는 모두 `output_root` 기준 상대경로 (forward-slash 통일).

### 3.5 manifest.json schema (output_root 직속)

| key | 의미 |
|---|---|
| `generator_version` | "session3-v1" |
| `config_path` | 본 generation에서 사용한 yaml 경로 |
| `output_root` | 절대경로 |
| `master_seed` | generation.seed 또는 CLI override |
| `max_steps` | episode_max_steps |
| `behavior_policy` | "random_uniform" / "random_biased" |
| `splits` | yaml의 splits 리스트 |
| `counts` | split별 요청된 episode 수 |
| `train_pool` | 24개 permutation 중 train 전용 K개 |
| `ood_pool` | train 전용 외 나머지 |
| `ood_room_perm_disjoint_from_train` | bool. yaml의 정책과 실제 disjoint 여부의 AND |
| `rg4f_config` | resolved RG4FConfig 모든 필드의 dict |
| `save_debug_trace` / `save_index_jsonl` / `save_episode_metadata` | metadata flag echo |
| `split_summaries` | split별 요약 (num_episodes, successful, perm_pool_size, override 등) |
| `elapsed_seconds` | generation 총 wall-clock 시간 |

---

## 4. split 구현 방식

### 4.1 train / valid / test_id

- 같은 distribution. 같은 RG4FConfig (yaml override 없음).
- 같은 `train_perm_pool` (24개 중 절반, 기본 12개)에서 episode마다 uniform sampling.
- master_seed → split별 SHA1-hash 기반 `split_seed_root` → 각 episode의 env_seed/action_seed.
- valid / test_id는 train과 다른 split_seed_root이므로 같은 yaml에서 disjoint한 episode seed pool.

### 4.2 ood_room_perm

- `train_perm_pool`과 disjoint한 `ood_perm_pool` (24개 중 나머지, 기본 12개) 사용.
- 24개 permutation은 `master_seed`에서 파생된 master rng로 한 번 shuffle 후 `train_fraction_of_24_permutations` 비율로 split. 같은 master_seed → 같은 분리.
- manifest.json의 `ood_room_perm_disjoint_from_train` 키로 invariant 표시.
- 검증: train의 모든 episode forced_permutation이 train_pool에 속하고, ood_room_perm의
  모든 episode forced_permutation이 ood_pool에 속함을 smoke test에서 확인.

### 4.3 ood_factor_recomb

- yaml의 `split_policy.factor_recomb.train_field_families` / `ood_field_families`로 정의된
  family ID 집합 사용. 기본값:
  - train: `[0, 1]` = `{VISIBILITY, FRICTION}`
  - ood_factor_recomb: `[2, 3]` = `{INTERACTION_INTERFERENCE, CONTROL_INTERFERENCE}`
- `_run_one_episode` 안에서 reset 직후 `_filter_invisible_fields_by_family`로 family pool에 들지 않는 fields를 제거. 모두 제거되면 reseed해서 최대 8회 재시도.
- 결과: 본 split의 모든 episode_meta의 `field_info_static`에서 family ID는 ood_pool 안 것만 포함.
- **참고**: 현재 `train`/`valid`/`test_id`는 family filter를 적용하지 않고 4개 모든 family를
  허용한다 (yaml의 `train_field_families`는 metadata 라벨 + ood_factor_recomb의 disjoint
  대비 기준). Session 4의 `validate_dataset`이 이 정책을 명확히 검증해야 한다.

### 4.4 ood_param_shift

- yaml의 `param_shift.drift_strength_multiplier` / `shift_probability_multiplier`로
  RG4FConfig override:
  - `field_mu_drift_sigma` ← train * `drift_strength_multiplier` (기본 2.0)
  - `shift_prob_per_room_entry` / `per_checkpoint` / `per_stele_activation` ← train *
    `shift_probability_multiplier` (max 1.0 clip)
  - `field_radius_max` ← train * `drift_strength_multiplier`
- 기본 train 값에서 2배. metadata `rg4f_kwargs_override`에 모든 override가 기록됨.
- `train` distribution과 같은 family/coupling shape이지만 수치 범위가 다름 → PART3
  parameter shift OOD 정의에 부합.

### 4.5 ood_obs_shift

- yaml의 `obs_shift.visual_channel_permutation: true`일 때 `local_grid`의 마지막 axis(C=10)를 결정적 random permutation으로 섞는다.
- master_seed에서 파생된 별도 rng로 한 번만 sampling → split 내 모든 episode 동일한 permutation 사용.
- underlying dynamics는 변하지 않는다 (env 안의 channel 의미는 그대로). 모델이 보는 channel
  위치만 다름 → novelty detector가 false positive를 내야 하는 split.
- metadata의 `obs_channel_perm` 필드에 적용된 permutation 기록.

### 4.6 ood_field_placement

- yaml의 `field_placement.placement_prior_shift: true`일 때 `_run_one_episode` 안에서
  reset 직후 `_maybe_relocate_fields_to_room_centers` 호출. invisible field source의
  `Position`을 4개 task 방의 interior 중심부 (3×3 neighborhood) 안으로 이동.
- 다른 모든 속성(family, radius, mu, sigma, coupling)은 그대로 유지.
- train의 default placement는 grid 어디든 random uniform이므로 placement prior가 명확히 다름.
- metadata의 `relocate_fields_room_center=True`로 표시.

---

## 5. behavior policy

### 5.1 지원 policy

이 generator는 model/planner/agent가 아니다. 단순한 data collection policy만 지원한다.

| policy | 설명 |
|---|---|
| `random_uniform` | 16개 action 모두 균일 확률 (1/16). |
| `random_biased` | movement(W/A/S/D) 55%, E 15%, state adjust(±5 dim) 30%, WAIT 0%. |

`random_biased`의 정확한 분배:
- `W=A=S=D` 각 0.55/4 = 0.1375
- `E` = 0.15
- `V_PLUS=V_MINUS=...=D_PLUS=D_MINUS` 각 0.30/10 = 0.030
- `WAIT` = 0.0 (data collection 관점에서 의미 있는 step 위주)

### 5.2 metadata에 저장되는 항목

각 episode_meta.json에 다음을 기록:
- `behavior_policy: str`
- `action_probs: list[float]` (16-dim 분포)
- `actions_raw` (npz)
- `actions_effective` (npz, control-drift remap 후)

### 5.3 이것이 planner/agent가 아니라 data collection policy임을 명시

- 본 policy는 환경을 굴려 transition을 모으는 단순 sampler다.
- 학습된 policy가 아니며, value/return을 추정하지 않는다.
- planner / agent / world model rollout / falsification metric 계산은 일절 하지 않는다.
- Session 4 이후 페이즈에서 controlled backbone + mechanism 기반 planner가 별도로 작성된다.
- 이 generator로 만든 dataset은 world model **supervised pretraining** 용도다.

### 5.4 `task_probe` policy는 미구현 (Session 4+ 필요 시 추가)

PART0 §3 §6 ("agent/planner 코드 구현 금지")에 정합. 단순한 분포 기반 policy로 충분히
diverse한 transition을 모을 수 있음을 smoke test에서 확인.

---

## 6. Smoke test 결과

모든 명령은 Windows PowerShell + `.venv\Scripts\python.exe`로 실행. 30초 이상 걸린 명령
없음 (대부분 5초 이내).

### 6.1 Dry-run

```powershell
.\.venv\Scripts\python.exe scripts\generate_dataset.py --config configs\dataset_default.yaml --dry-run
```

결과 요약:
- train_pool 12개 / ood_pool 12개 (`ood_use_disjoint_permutations=True`)
- `disjoint check: train ∩ ood = []` (빈 집합)
- 모든 RG4FConfig 필드의 resolved 값 출력 (`local_obs_size=5`, `field_mu_drift_sigma=0.01`,
  `miscontrol_p_low=0.05`, `shift_prob_per_*=0.05` 등)
- 8개 split 각각의 plan 출력 (perm_pool_size, rg4f_override, field_family_pool, obs_channel_perm, relocate_fields_room_center)

### 6.2 Small smoke dataset 생성

```powershell
.\.venv\Scripts\python.exe scripts\generate_dataset.py --config configs\dataset_default.yaml `
  --num-train 2 --num-valid 1 --num-test 1 --num-ood-per-type 1 --max-steps 50 --overwrite
```

결과:
- 8개 split, 총 9개 episode (train 2, 나머지 1) 생성. 총 0.13초.
- 모든 split의 `index.jsonl` line 수 = 요청한 episode 수.
- 모든 episode_meta.json + npz 짝 존재.
- manifest.json 존재.

### 6.3 npz key + shape 검증

```powershell
.\.venv\Scripts\python.exe -c "import numpy as np; d=np.load('data/rg4f/train/episodes/train_000000.npz'); ..."
```

- 40개 numeric array 모두 정확한 shape/dtype 저장.
- `observations_local_grid.shape == (50, 5, 5, 10)` (T=50, n=5, C=10).
- `true_state.shape == (50, 5)`. object dtype 0회.

### 6.4 disjoint 검증

```python
manifest['ood_room_perm_disjoint_from_train'] == True
set(map(tuple, train_pool)) & set(map(tuple, ood_pool)) == set()
# train의 모든 forced_permutation이 train_pool 안에 있음 확인
# ood_room_perm의 모든 forced_permutation이 ood_pool 안 + train_pool 밖
```

### 6.5 OOD 차별화 검증

| split | metadata | 실제 효과 |
|---|---|---|
| `ood_room_perm` | `forced_permutation` ∈ `ood_pool` | train pool과 disjoint |
| `ood_factor_recomb` | `field_family_pool=[2,3]` | 모든 episode field family ⊂ {2,3} (filter 적용 후) |
| `ood_param_shift` | `rg4f_kwargs_override` | drift/shift 2배 적용된 RG4FConfig |
| `ood_obs_shift` | `obs_channel_perm=[5,9,7,0,4,3,6,1,2,8]` | local_grid 채널 순서 다름 |
| `ood_field_placement` | `relocate_fields_room_center=true` | source_position이 4개 방 중심부 |

### 6.6 deterministic replay 검증

별도 process 두 번 같은 seed (`777`)로 실행:
- 모든 npz array가 byte-level로 동일 (`np.array_equal` all True).
- 처음에는 `abs(hash(plan.name))`가 PYTHONHASHSEED에 의존해서 깨졌다 → SHA1 기반 결정적
  변환으로 fix (commit at `_generate_split` split_seed_root 계산).

### 6.7 local_obs_size ablation 검증

```python
for sz in (3, 5, 7):
    cfg = base_cfg
    cfg['environment']['local_obs_size'] = sz
    # generate small dataset
    npz['observations_local_grid'].shape == (T, sz, sz, 10)
```

- `sz=3` → `(20, 3, 3, 10)` ✓
- `sz=5` → `(20, 5, 5, 10)` ✓ (메인 default)
- `sz=7` → `(20, 7, 7, 10)` ✓

### 6.8 overwrite 보호 검증

기존 `data/rg4f` 존재 상태에서 `--overwrite` 없이 실행 → exit code 2 + 명확한 에러 메시지
("output_root … already exists. Use --overwrite or set project.overwrite=true."). 정상 동작.

### 6.9 발견한 이슈와 수정

1. **(fix됨) Determinism 깨짐**: `abs(hash(plan.name))`가 PYTHONHASHSEED에 의존.
   `hashlib.sha1(plan.name.encode()).digest()[:4]`로 변경. 같은 yaml + 같은 seed → 같은
   dataset 보장.
2. **(fix됨) ood_factor_recomb family filter 무효화**: `_run_one_episode`가 reset을 다시
   호출해서 외부 filter가 풀렸다. `_run_one_episode`가 직접 `field_family_pool` 인자를
   받아 reset 직후 filter + 최대 8회 reseed 재시도하도록 변경.
3. **(설계 결정) field_info dynamic vs static 분리**: episode 시작 시 결정되는 family /
   source_position / radius / coupled_states는 episode_meta.json에, step별 갱신되는 mu /
   sigma는 npz의 `field_info_mu`/`field_info_sigma` (T, F) array로 저장. F는 episode별 가변.
4. **(설계 결정) reveal_or_shift / target_band_kind는 string 인코딩 대신 int 인코딩**:
   object dtype을 피하고 numpy로 직접 indexing 가능.

---

## 7. 핵심 확인 포인트 4가지에 대한 답

| 확인 포인트 | 결과 | 근거 |
|---|---|---|
| 1. ood_room_perm이 train permutation과 진짜 disjoint한지 | PASS | smoke §6.4. manifest의 `ood_room_perm_disjoint_from_train=true`. train_pool ∩ ood_pool = ∅. 실제 episode forced_permutation이 양쪽 pool에 분리되어 들어감. |
| 2. episode npz + index.jsonl + manifest.json이 저장되는지 | PASS | smoke §6.2. 모든 split에 `episodes/<name>.npz` + `episodes/<name>.meta.json` + `index.jsonl` 존재. root에 `manifest.json` 존재. |
| 3. local_obs_size 기본값 5와 [3,5,7] ablation이 유지되는지 | PASS | smoke §6.7. yaml default `local_obs_size=5`, `local_obs_ablation_values=[3,5,7]`. 세 값 모두 npz `local_grid` shape이 `(T, sz, sz, 10)`로 동작. RG4FConfig.__post_init__가 값을 강제. |
| 4. inspect/validate script나 model/planner 코드까지 과하게 만들지 않았는지 | PASS | `scripts/inspect_episode.py` / `scripts/validate_dataset.py` 둘 다 미생성. `falsifiable_regime_world_model/` 안에 model/planner/agent 디렉토리 없음. torch/dreamer import 0회. |

---

## 8. Session 3에서 드러난 알려진 미해결 ambiguity / TODO

### 8.1 ood_factor_recomb의 train family filter 부재

- 현재 train/valid/test_id는 4개 모든 family를 허용한다. yaml의 `train_field_families=[0,1]`은
  metadata 라벨일 뿐 강제되지 않는다. 따라서 train에서도 family 2/3이 등장 가능.
- 엄밀한 disjoint를 보장하려면 train/valid/test_id에도 family filter를 적용해야 한다 (Session 4의
  validate_dataset이 이 정책을 어떻게 강제할지 결정 필요).
- 결정 1 안: yaml에 `train_apply_family_filter: bool` 추가하여 train도 filter 가능하게.
- 결정 2 안 (현재): train은 4개 family 자유, ood_factor_recomb만 disjoint pool. train과
  ood_factor_recomb의 family 분포가 겹칠 수 있음을 명시 + Session 4가 이를 invariant로 검증.

### 8.2 obs_channel_perm은 의미 채널까지 섞는다

- 현재 channel permutation은 10개 LOCAL_CHANNELS (wall, floor, corridor, door, task_object,
  stele, altar, cue, agent, traversable) 모두에 적용된다. 이는 환경의 visual style 변화라기
  보단 channel index 변경이다.
- PART3의 obs_shift OOD 의도(visual variant)와는 다르며, novelty detector가 false positive를 내야 한다는 측면은 그대로 유효 (channel 위치 변경 = surface novelty, dynamics 동일).
- Session 4의 `validate_dataset`은 ood_obs_shift의 underlying rule이 train과 동일함을
  metadata 비교로 검증해야 한다.

### 8.3 reveal_event vs shift_event 정의의 한계

- 현재 env (Session 2 결정): `change_point = shift_event`. control_mode의 abrupt mid-episode
  remap shift는 미구현 (initial sampling 후 episode 동안 고정).
- 이로 인해 이 generator가 만든 dataset의 `change_point` 라벨은 field-level shift와
  task-level state shift만 캡처한다 (Task C `on_enter_room`의 initial_d 강제, `apply_event_shift`의
  field mu jump).
- Session 4의 inspect_episode가 reveal/shift trajectory를 시각화할 때 이 한계를 명시해야 한다.
  Session 6 환경 감사에서 abrupt control_mode shift 추가 여부 결정.

### 8.4 episode 단위 random-access loader 미구현

- 사용자 요구사항에서 선택 사항으로 `falsifiable_regime_world_model/rg4f/dataset.py` (npz
  random-access loader)를 언급했으나 본 세션에서는 만들지 않았다. Session 4의 inspect/validate
  script가 직접 `np.load` + json 읽기로 동작하므로 dataset.py가 반드시 필요하지는 않다.
- 향후 학습 페이즈에서 PyTorch DataLoader가 필요해지면 이 파일을 추가.

---

## 9. Session 4 목표 — Inspection / Validation script 구현

Session 4가 책임지는 것 (PART0 §2 / 사용자 요구사항 §9.7):

1. **`scripts/inspect_episode.py`**:
   - 임의 npz + meta.json을 받아 trajectory 시각화 / 통계 출력.
   - step별 (action_raw, action_effective, true_state, true_regime, change_point, reveal/shift,
     target band 충족 여부, reward decomposition)을 사람이 읽을 수 있게 출력.
   - 환경 ASCII 렌더 (`env.render_ascii()`) 또는 matplotlib trajectory plot은 선택.
   - 본 generator의 npz schema (§3.2)와 episode_meta.json (§3.3)에 맞춰 작성.

2. **`scripts/validate_dataset.py`**:
   - split 단위 invariant 검증. PASS/FAIL을 stdout + exit code + 보고서 파일로.
   - 검증 항목:
     - split별 episode 수 (manifest의 counts와 일치).
     - **train_pool과 ood_room_perm 간 disjoint** (§4.2).
     - **ood_factor_recomb의 모든 episode field family ⊂ ood_field_families** (§4.3).
     - ood_param_shift의 manifest `rg4f_kwargs_override`가 train보다 큼.
     - ood_obs_shift의 metadata `obs_channel_perm` 존재 + dynamics는 train과 동일.
     - ood_field_placement의 metadata `relocate_fields_room_center=true`.
     - invisible field coupling sparse 조건: `len(coupled_states) ≤ 2` for all fields.
     - seed 고정 시 episode 재현 가능 (별도 process로 동일 yaml + 같은 seed → 같은 dataset).

3. **(선택) `scripts/plot_dataset_stats.py`**:
   - episode length 분포 / reward 분포 / change_point 빈도 / event_token 빈도 등 통계 plot.

Session 4가 책임지지 않는 것 (PART0 §3 / 사용자 요구사항 §9.7):

- model 학습, planner / agent 구현, 대규모 실험.
- DreamerV3 / RSSM SOTA / GRU-lite 코드.
- 새로운 환경 기능 추가 (env API 변경 금지; 필요하면 본 문서 먼저 갱신).

### 9.1 Session 4가 본 세션의 산출물에 어떻게 의존하는가

- npz key는 §3.2의 표 그대로. column 추가는 backward-compatible 하게만 (끝에 append).
- episode_meta.json key는 §3.3 그대로.
- index.jsonl은 한 줄당 한 episode의 lookup.
- manifest.json의 `train_pool` / `ood_pool` / `rg4f_config`는 invariant 검증의 ground-truth.

### 9.2 Session 4 시작 전 권장 순서

1. 본 문서 §3 (저장 구조) + §4 (split 구현 방식)을 먼저 읽는다.
2. `scripts/generate_dataset.py`의 `_run_one_episode`와 `EpisodeBuffer.finalize`를 읽어
   npz가 어떻게 만들어지는지 확인.
3. `scripts/inspect_episode.py` 작성 (단일 npz read + sequential print).
4. `scripts/validate_dataset.py` 작성 (manifest + 모든 index.jsonl 읽기 + invariant 검증).
5. small smoke dataset에 두 script를 돌려 PASS 확인 → `docs/SESSION4_HANDOFF.md` 작성.

---

## 10. Self-Audit 결과

| Check | Status | Evidence |
|---|---|---|
| Session 1/2 산출물을 모두 읽었는가 | PASS | PART0/Plan/SESSION1_HANDOFF/SESSION2_HANDOFF + PART1/2/3 + types/config/map_generator/observation/fields/env 모두 Read 도구로 확인. |
| 기존 ref/PART0~3와 requirements.txt를 수정하지 않았는가 | PASS | git 변경 없음. 본 세션은 docs/SESSION3_HANDOFF.md 신규 작성 외에 docs/* 어떤 파일도 수정하지 않음. |
| world model / planner / agent 코드를 만들지 않았는가 | PASS | torch import 0회. world_model/planner/agent 디렉토리 부재. EpisodeBuffer는 단순 numpy 변환 헬퍼. |
| scripts/inspect_episode.py와 validate_dataset.py를 만들지 않았는가 | PASS | scripts 디렉토리에는 generate_dataset.py만 존재. |
| configs/dataset_default.yaml을 생성했는가 | PASS | configs/dataset_default.yaml 존재 (project/generation/environment/splits/split_policy/metadata 5개 섹션). |
| scripts/generate_dataset.py를 생성했는가 | PASS | scripts/generate_dataset.py 존재. CLI: --config / --output-root / --seed / --num-* / --max-steps / --overwrite / --dry-run / --split. |
| RG4FConfig를 yaml/dict에서 로드 가능하게 했는가 | PASS | Session 2에서 이미 `from_dict`가 있었고 Session 3는 unknown key 거부 정책을 그대로 유지. yaml의 friendly key는 generator의 `_yaml_env_to_rg4f_kwargs`가 RG4FConfig 정확한 필드명으로 변환. |
| local_obs_size 기본값 5를 유지했는가 | PASS | yaml `environment.local_obs_size: 5`. RG4FConfig.local_obs_size default=5. smoke test §6.7에서 npz shape이 (T,5,5,10) 확인. |
| local_obs_ablation_values [3,5,7]을 config에 반영했는가 | PASS | yaml `environment.local_obs_ablation_values: [3,5,7]`. RG4FConfig.__post_init__가 3,5,7 모두 포함을 강제. smoke test §6.7에서 세 값 모두 동작 확인. |
| train/valid/test_id/OOD split을 모두 지원하는가 | PASS | yaml `splits` 8개. SplitPlan 객체로 각 split의 정책 분리. smoke test §6.2에서 8개 split 모두 episode 생성. |
| ood_room_perm이 train permutation과 disjoint한가 | PASS | smoke §6.4. `ood_room_perm_disjoint_from_train=true`. train_pool ∩ ood_pool = ∅. ood_room_perm episode의 forced_permutation이 ood_pool에 속하고 train_pool에 없음. |
| episode npz와 index.jsonl을 저장하는가 | PASS | smoke §6.2 / §6.3. `train/episodes/train_000000.npz` (40 numeric array) + `train/index.jsonl` (한 줄당 1 episode). |
| manifest.json을 저장하는가 | PASS | smoke §6.4. `data/rg4f/manifest.json` 존재 (8288 bytes). 17개 top-level key. |
| random_uniform/random_biased behavior policy를 지원하는가 | PASS | `_build_action_probs(policy)` 함수. random_biased 분포 = (movement 55%, E 15%, state-adjust 30%, WAIT 0%). metadata에 `behavior_policy` + `action_probs` 저장. |
| dry-run이 동작하는가 | PASS | smoke §6.1. dry-run 출력에 train_pool/ood_pool/disjoint check + 8개 split의 plan. IO 0회. |
| small smoke dataset 생성이 동작하는가 | PASS | smoke §6.2. `--num-train 2 --num-valid 1 --num-test 1 --num-ood-per-type 1 --max-steps 50 --overwrite` 명령이 0.13초에 9개 episode 완료. |
| docs/SESSION3_HANDOFF.md를 작성했는가 | PASS | 본 문서. |

---

## 11. 본 문서가 Session 4에 던지는 단 한 줄 요약

> **inspect_episode.py와 validate_dataset.py만 만든다. Session 3가 만든 npz/meta/index/
> manifest의 schema (§3) + split 구현 (§4) + behavior policy (§5)에 맞춰 invariant를
> 검증하면 끝이다. 모델/planner/SOTA/대규모 실험은 절대 건드리지 않는다.**
