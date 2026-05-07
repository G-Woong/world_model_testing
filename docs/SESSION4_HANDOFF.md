# SESSION 4 → SESSION 5 Handoff

> 본 문서는 다음 Cursor 세션이 이전 대화 맥락 없이 단독으로 Session 5 (small smoke
> dataset 생성 및 검증)를 시작할 수 있도록 작성된 인계 문서다. 본 문서만으로 Session 5의
> 모든 결정 근거가 추적 가능해야 한다.

---

## 1. 본 세션에서 생성/수정한 파일

### 생성

| 경로 | 목적 |
|---|---|
| `falsifiable_regime_world_model/rg4f/dataset_io.py` | manifest.json / index.jsonl / episode npz / episode_meta.json 의 단일 source-of-truth 로더. Session 3 schema의 필수 key 그룹 정의 (`REQUIRED_NPZ_KEYS_FLAT`, `REQUIRED_NPZ_GROUPS`), `IndexEntry` / `EpisodeBundle` dataclass, `iter_episodes` 등을 노출. inspect / validate / plot 세 script가 모두 이 모듈만 import 한다. |
| `scripts/validate_dataset.py` | dataset 전체 invariant 검증 도구. directory / split coverage / npz schema / shape / numeric / sparse coupling / 8개 split별 OOD invariant / determinism (옵션) 모두 PASS/WARN/FAIL로 기록. exit code: FAIL 있으면 1, strict + WARN이면 1, 그 외 0. |
| `scripts/inspect_episode.py` | 단일 episode를 사람이 직접 확인하는 도구. metadata / transition summary / step-level (action / state / regime / target_band / cost) / local grid ASCII / field·task debug 출력. `--episode-path` 직접 지정 또는 `--root --split --index` 모두 지원. |
| `scripts/plot_dataset_stats.py` | (선택) split별 episode length / reward / change_point / action / family 분포 통계를 CSV로 저장. matplotlib 가능 시 PNG 3개(episode length, total reward, change_point boxplot)도 함께 저장. seaborn 미사용. |
| `docs/SESSION4_HANDOFF.md` | 본 문서. |

### 수정

본 세션은 Session 3 산출물을 단 한 줄도 수정하지 않았다.

- `falsifiable_regime_world_model/rg4f/{types,config,map_generator,observation,fields,tasks,env,serialization}.py` — 0줄 변경.
- `scripts/generate_dataset.py` — 0줄 변경.
- `configs/dataset_default.yaml` — 0줄 변경.
- `ref/PART0~3` — 0줄 변경.
- `requirements.txt` — 0줄 변경.

dataset 저장 포맷 / `RG4FEnv` reset/step/info 컨트랙트는 그대로 유지된다.

### Session 4가 명시적으로 수행하지 않은 것

PART0 §3 / 사용자 요구사항 §0 정합:

- world model / RSSM / GRU-lite / DreamerV3 / SOTA 코드 0줄.
- planner / agent / allocator 코드 0줄.
- 학습 loop, optimizer, training run 0줄.
- 대규모 dataset 생성 0회 (smoke 단위만, 모든 명령 5초 이내 종료).
- env API / serialization API 변경 0회.
- ref/PART0~3 / requirements.txt / Session 3 산출물의 핵심 schema 변경 0회.

---

## 2. `validate_dataset.py` 사용법

### 2.1 기본 명령

```powershell
.\.venv\Scripts\python.exe scripts\validate_dataset.py --root data\rg4f
```

8개 split을 모두 스캔하고 split별 최대 10개 episode를 deep inspect한다. PASS/WARN/FAIL
요약을 stdout에 출력하고 exit code로 결과를 알린다.

### 2.2 strict 명령

```powershell
.\.venv\Scripts\python.exe scripts\validate_dataset.py --root data\rg4f --strict --max-episodes-per-split 5
```

`--strict`: WARN 하나라도 있으면 exit code 1로 처리. `--max-episodes-per-split`은 split별
deep inspect 최대 episode 수 (0이면 모두).

### 2.3 json report 명령

```powershell
.\.venv\Scripts\python.exe scripts\validate_dataset.py --root data\rg4f `
  --json-report data\rg4f\validation_report.json --verbose
```

`--verbose`: 표 형태의 모든 check를 stdout에 출력. `--json-report`: 모든 check 결과를
지정한 path에 json으로 dump.

### 2.4 determinism check

```powershell
.\.venv\Scripts\python.exe scripts\validate_dataset.py --root data\rg4f `
  --check-determinism --config configs\dataset_default.yaml
```

`--check-determinism`은 `scripts/generate_dataset.py`를 임시 디렉토리 두 곳에 같은 seed
(`777`)로 두 번 호출하여 모든 npz가 byte-equal한지 비교한다. 임시 디렉토리는 검사 후
자동 삭제. timeout 60초.

### 2.5 단일 split 검증

```powershell
.\.venv\Scripts\python.exe scripts\validate_dataset.py --root data\rg4f --split ood_room_perm
```

### 2.6 PASS / WARN / FAIL 기준

| status | 의미 | exit code 영향 |
|---|---|---|
| `PASS` | 해당 invariant 충족 | 0 |
| `WARN` | 권장 사항 위반 (의심스럽지만 schema에는 부합). 예: ood_obs_shift의 channel_perm이 identity, train_distribution 외 episode count 등. | strict 모드에서만 1 |
| `FAIL` | schema / contract / 핵심 invariant 위반. 즉시 1. | 항상 1 |

---

## 3. `inspect_episode.py` 사용법

### 3.1 기본 명령

```powershell
.\.venv\Scripts\python.exe scripts\inspect_episode.py --root data\rg4f --split train --index 0
```

기본은 step `[0, 10)` 범위의 step-level 로그 + episode metadata + transition summary.
ASCII grid / scalar / target_band 등은 옵션으로 켠다.

### 3.2 step range 확인

```powershell
.\.venv\Scripts\python.exe scripts\inspect_episode.py --root data\rg4f --split train --index 0 `
  --step 30 --num-steps 15 --show-info --show-scalar
```

`--step`: 시작 step. `--num-steps`: 몇 개를 출력. `--show-info`: target_band / cost /
miscontrol_p / field 동적값 출력. `--show-scalar`: scalar 14차원 + true_state 5개 출력.

### 3.3 local grid 확인

```powershell
.\.venv\Scripts\python.exe scripts\inspect_episode.py --root data\rg4f --split train --index 0 `
  --num-steps 5 --show-grid
```

`--show-grid`: 매 step마다 5×5 ASCII grid 출력. 매핑은 `@ agent / + door / * task_object /
S stele / A altar / ? cue / # wall / - corridor / . floor / ' ' empty`.

### 3.4 field / task 확인

```powershell
.\.venv\Scripts\python.exe scripts\inspect_episode.py --root data\rg4f --split ood_room_perm --index 0 `
  --num-steps 3 --show-task --show-fields
```

`--show-fields`: invisible field static (family / source / radius / coupled_states +
sparse OK 여부) + 마지막 step의 mu/sigma. `--show-task`: room→task assignment + target band
활성 step 통계 + task별 진입 step 수.

### 3.5 직접 npz 경로 지정

```powershell
.\.venv\Scripts\python.exe scripts\inspect_episode.py `
  --episode-path data\rg4f\train\episodes\train_000000.npz `
  --meta-path data\rg4f\train\episodes\train_000000.meta.json `
  --num-steps 5 --show-info
```

index.jsonl 우회 시 사용. 단독 npz도 검사 가능.

### 3.6 저장 옵션

```powershell
.\.venv\Scripts\python.exe scripts\inspect_episode.py --root data\rg4f --split train --index 0 `
  --num-steps 5 --show-grid --show-info --save-ascii outputs\episode_inspect.txt
```

`--save-ascii`: 출력을 그대로 텍스트 파일에 저장 (stdout과 동일 내용).

---

## 4. validate가 검증하는 invariant 목록

본 절은 validate_dataset.py가 자동 검증하는 invariant를 카테고리별로 정리한다.

### 4.1 directory / file structure (`directory.*`)
- `directory.root_exists`: `--root` 디렉토리 존재.
- `directory.manifest_present`: `<root>/manifest.json` 존재.
- `directory.split_dir`: 각 expected split 폴더 + `index.jsonl` + `episodes/` 존재.

### 4.2 split coverage (`split_coverage.*`)
- `split_coverage.all_present`: 8개 split (`train`, `valid`, `test_id`, `ood_room_perm`,
  `ood_factor_recomb`, `ood_param_shift`, `ood_obs_shift`, `ood_field_placement`)이 모두
  발견되는가.

### 4.3 npz schema (`npz.required_keys_present`, `npz.group.*`)
사용자 요구사항 §2.3의 24개 필수 항목을 모두 검사:
- `observations_local_grid`, `observations_scalar`, `observations_event_token`,
- `actions_raw`, `actions_effective`, `rewards`, `dones`, `truncateds`,
- `next_observations_local_grid`, `next_observations_scalar`, `next_observations_event_token`,
- `true_state`, **`true_regime` 그룹** (`control_mode`, `mobility_mode`, `miscontrol_p`,
  `periodic_slip`),
- `change_point`, `reveal_or_shift` (+ `reveal_event` / `shift_event` 분리),
- `task_id`, `room_id`, **`target_band` 그룹** (`active`, `state_dim`, `center`, `half_width`,
  `kind`),
- **`field_info` 그룹** (`mu`, `sigma`),
- `agent_position`, `completed_tasks`, `failure_count`, `tick_cost`, `latency_cost`,
  `reset_flag`,
- 추가 cost decomposition (`failure_cost`, `reset_cost`, `task_reward`, `completion_reward`).

### 4.4 shape invariants (`shape.*`)
- `shape.timesteps_consistent`: 모든 (T, ...) array의 T가 일치.
- `shape.local_grid_shape`: `(T, n, n, 10)`. n ∈ {3, 5, 7}.
- `shape.local_obs_size_matches_expected`: manifest의 `rg4f_config.local_obs_size`와 일치
  (불일치 시 WARN).
- `shape.scalar_dim`: `(T, 14)`.
- `shape.true_state`: `(T, 5)`.
- `shape.next_local_matches_obs`: next_obs.shape == obs.shape.
- `shape.action_mask`: 저장된 경우 `(T, 16)` 검증 (현재 Session 3는 미저장).

### 4.5 numeric validity (`numeric.*`)
- `numeric.no_nan_inf`: 모든 float array에 NaN/Inf 없음.
- `numeric.true_state_range`: `|x|` max가 1.05 이하 (PASS), 1.5 이하 (WARN), 그 이상 (FAIL).
  state clip은 [-1, 1]이지만 single step 안에서 ε 정도 벗어날 수 있음.
- `numeric.binary_dtype.{change_point,reveal_event,shift_event,reset_flag,dones,truncateds}`:
  bool dtype 강제.
- `numeric.reveal_or_shift_enum`: 값이 {0, 1, 2}.
- `numeric.actions_*_range`: 0 이상 16 미만.
- `numeric.task_id_range`: -1..3.
- `numeric.room_id_range`: -1..6.
- `numeric.reset_flag_always_false`: step 결과의 `reset_flag`는 항상 False (Session 3 contract).

### 4.6 split-specific OOD invariants (`split_specific.*`)
- `split_specific.id_not_ood` (train/valid/test_id): meta.is_ood=False.
- `split_specific.ood_metadata` (모든 OOD): meta.is_ood=True 및 meta.ood_type 일치.
- `split_specific.room_perm.disjoint_from_train` (ood_room_perm): episode의
  forced_permutation이 manifest의 `train_pool`에 들어있지 않음.
- `split_specific.room_perm.in_ood_pool`: `ood_pool` 안에 있는지 (없으면 WARN).
- `split_specific.factor_recomb.families_in_ood_pool` (ood_factor_recomb): episode의
  field_info_static의 family ID가 manifest의 split_summary.field_family_pool ⊂.
- `split_specific.param_shift.differs_from_train` (ood_param_shift): meta의
  rg4f_kwargs_override가 비어있지 않고, drift_strength / shift_probability /
  field_radius_max 중 적어도 하나가 train base와 실제로 다름.
- `split_specific.obs_shift.channel_perm_valid` (ood_obs_shift): meta의 obs_channel_perm이
  10차원의 정확한 permutation이며 identity가 아님.
- `split_specific.obs_shift.no_dynamics_change`: rg4f_kwargs_override가 비어 있어야 함.
- `split_specific.field_placement.relocate_flag` (ood_field_placement):
  meta.relocate_fields_room_center=True.
- `split_specific.field_placement.source_in_grid`: 모든 source_position이 grid 안.

### 4.7 sparse coupling (`sparse_coupling.le2`)
- 각 episode의 모든 invisible field에 대해 `len(coupled_states) ≤ 2` (PART0 §3 §10).

### 4.8 determinism (`determinism.*`, 옵션)
- `--check-determinism` 시: generator를 두 번 호출하여 모든 npz가 byte-equal.

---

## 5. Smoke test 결과

모든 명령은 Windows PowerShell + `.venv\Scripts\python.exe`로 실행.

### 5.1 small dataset 생성

```powershell
.\.venv\Scripts\python.exe scripts\generate_dataset.py --config configs\dataset_default.yaml `
  --num-train 2 --num-valid 1 --num-test 1 --num-ood-per-type 1 --max-steps 50 --overwrite
```

- 8개 split 모두 생성 성공. 총 0.13초.

### 5.2 validate (strict + json report)

```powershell
.\.venv\Scripts\python.exe scripts\validate_dataset.py --root data\rg4f --strict `
  --max-episodes-per-split 3 --json-report data\rg4f\validation_report.json --verbose
```

- 결과: **PASS=156, WARN=0, FAIL=0**, exit code 0.
- `data/rg4f/validation_report.json` 작성 (모든 check 결과 포함).
- 각 OOD split의 invariant 모두 PASS:
  - `ood_room_perm`: forced_permutation `(3,1,2,0)`이 train_pool에 없음.
  - `ood_factor_recomb`: family `[3, 3]` ⊂ ood_pool `[2, 3]`.
  - `ood_param_shift`: 5개 override key 모두 base와 다름 (drift_strength_multiplier=2.0
    적용 확인).
  - `ood_obs_shift`: channel_perm `[5,9,7,0,4,3,6,1,2,8]`이 valid permutation, 비-identity.
  - `ood_field_placement`: relocate_fields_room_center=True.
- sparse coupling: 모든 episode의 모든 invisible field가 `|coupled_states| ≤ 2`.

### 5.3 inspect (train + OOD)

```powershell
# train
.\.venv\Scripts\python.exe scripts\inspect_episode.py --root data\rg4f --split train --index 0 `
  --num-steps 5 --show-grid --show-scalar --show-info

# ood_room_perm
.\.venv\Scripts\python.exe scripts\inspect_episode.py --root data\rg4f --split ood_room_perm --index 0 `
  --num-steps 3 --show-task --show-fields
```

train episode:
- `permutation_id=13`, `forced_permutation=[2,0,3,1]`.
- `local_grid` shape `(50, 5, 5, 10)`, scalar shape `(50, 14)`.
- step 4에서 `raw=A` → `eff=W` (miscontrol slip 발생). `miscontrol_p=0.300`,
  `periodic_slip=True` (config의 `enable_periodic_slip=True`이므로 t=0,4,8,...에서 high-p).
- field_info_mu/sigma 모두 finite, sparse OK.

ood_room_perm episode:
- `forced_permutation=[3,1,2,0]` (train_pool 밖, ood_pool 안).
- `initial_regime.control_mode=4` (REV) 즉 모든 방향 반대.
- 1개의 INTERACTION_INTERFERENCE field (`coupled_states=['noise', 'interaction']`,
  `|·|=2`, sparse=OK).
- room→task assignment: `NORTH→D`, `SOUTH→B`, `EAST→C`, `WEST→A` (기본 train과 다른 permutation).

### 5.4 determinism check

```powershell
.\.venv\Scripts\python.exe scripts\validate_dataset.py --root data\rg4f `
  --check-determinism --config configs\dataset_default.yaml --max-episodes-per-split 1
```

- 결과: **PASS=146, WARN=0, FAIL=0**.
- generator를 두 번 같은 seed (`777`)로 호출하여 임시 디렉토리 a/b에 dataset 생성.
- 모든 split의 모든 npz가 byte-equal. SHA1 기반 split_seed_root 결정성 확인.
- 임시 디렉토리는 검사 후 자동 삭제.

### 5.5 plot_dataset_stats

```powershell
.\.venv\Scripts\python.exe scripts\plot_dataset_stats.py --root data\rg4f `
  --out outputs\dataset_stats --max-episodes-per-split 5
```

- `outputs/dataset_stats/summary.csv` 작성 (split당 1행, 16개 column).
- split별 distribution CSV 8개 작성.
- PNG 3개: `episode_length_hist.png`, `reward_total_hist.png`, `change_point_boxplot.png`.
- matplotlib 3.10의 `tick_labels` API로 호환 (Deprecation warning 제거).

### 5.6 발견한 이슈와 수정

본 세션에서 dataset 자체의 schema 또는 generator 코드 결함은 발견되지 않았다.
사소한 wrap만:

1. **(자체 fix됨) plot_dataset_stats의 matplotlib 3.9+ deprecation**: `boxplot(labels=...)`
   가 `tick_labels=...`로 이름이 바뀌었다. try/except로 양쪽 호환되도록 수정.
2. **Session 3 generator 코드 수정 0회**: validate / inspect script는 모두 Session 3가
   저장한 schema 그대로를 그대로 사용 가능. 조정 불필요.

---

## 6. Known limitations / warnings (Session 3 인수인계 §8 재검토)

본 세션에서 검증하면서 다시 확인한 ambiguity. Session 5/6에서 의식해야 한다.

### 6.1 train family filter 부재

- 현재 `train`/`valid`/`test_id`는 4개 모든 invisible field family를 허용한다 (Session 3 §4.3).
  yaml의 `split_policy.factor_recomb.train_field_families: [0, 1]`은 metadata 라벨일
  뿐 강제되지 않는다.
- 따라서 train에 family 2/3 (interaction_interference, control_interference)도 등장 가능.
  ood_factor_recomb의 disjoint 의미가 PART3 의도(train에서 본 적 없는 조합)와는 약간
  다르다. 현재 ood_factor_recomb는 "train에는 있을 수도 있는 family인데, OOD에서는
  pool=[2,3]만 강제"가 정확한 의미.
- validate_dataset은 ood_factor_recomb episode의 field family ⊂ ood_pool만 검증한다
  (train family와의 disjoint는 검증하지 않는다 — config의 의도가 아니므로).
- Session 5/6의 결정 사항:
  - 안 1: yaml에 `train_apply_family_filter: bool` 추가 + generator에서도 train family
    filter 강제. 진정한 disjoint 보장.
  - 안 2: 현재 정책 유지 + 본 ambiguity를 paper의 OOD protocol 설명에 솔직히 명시.

### 6.2 channel permutation의 의미 한계

- ood_obs_shift는 `local_grid`의 마지막 axis(10채널)를 결정적 random permutation으로
  섞는다 (Session 3 §4.5). 이는 "channel index 변경"이지 "visual variant" (다른
  스프라이트 / 색깔) 가 아니다.
- novelty detector가 false positive를 내야 하는 조건은 만족 (channel 위치가
  바뀌면 raw mismatch가 발생). 그러나 PART3 obs_shift OOD의 원래 의도(예: 같은 의미를
  가진 다른 스프라이트)와는 표현 방식이 다르다.
- ASCII rendering: inspect_episode의 `--show-grid`는 channel 0~9을 고정 mapping으로
  그리므로, ood_obs_shift episode에서는 ASCII가 의미상 깨질 수 있다 (channel이 바뀐
  후의 raw layer 값을 fixed semantics로 그리기 때문). 이를 metadata 헤더에 NOTE로
  표시한다.
- Session 6에서 진짜 visual variant (예: cue 채널의 값 분포 변경)를 추가하려면
  observation.py + map_generator.py를 손대야 한다 (Session 5의 범위는 아님).

### 6.3 change_point = shift_event 정의 한계

- Session 2 결정: `change_point = shift_event`. control_mode의 abrupt mid-episode remap
  shift는 미구현 (initial sampling 후 episode 동안 고정).
- 따라서 본 dataset의 `change_point` 라벨은 (a) `apply_event_shift`가 field mu를
  점프시킨 step, (b) Task C `on_enter_room`이 `initial_d`를 강제 set한 step, 두 종류만
  잡는다.
- inspect_episode에서 change_point=True인 step은 reveal_event/shift_event 분리도 함께
  출력한다. 따라서 사용자는 본 ground-truth가 무엇을 의미하는지 시각적으로 파악 가능.
- Session 6에서 control_mode mid-episode remap 추가 여부 결정.

### 6.4 object dtype field 부재

- Session 3는 모든 array를 numeric (float32/int32/bool)로 저장하고 string/list-of-dict는
  episode_meta.json으로 분리했다. 따라서 npz 안에 object dtype은 없다.
- validate_dataset의 `numeric.no_nan_inf` 검사는 dtype.kind ∈ ("b","i","u","f","c")만
  허용하므로 object array가 들어오면 자동 FAIL. 이는 의도적 안전장치.

### 6.5 local_grid ASCII rendering 한계

- inspect_episode의 ASCII grid는 channel별로 priority queue (agent > door > task_object >
  stele > altar > cue > wall > corridor > floor > traversable)로 그린다.
- 한계 1: channel별 임계값을 0.5 fixed로 두므로, soft mask cue (vision-level dependent)는
  cue 값이 0.5 미만이면 보이지 않을 수 있다. 이는 "cue가 가려진" 상태와 시각적으로 구별
  불가능 — 의도. 정확한 cue 값을 보려면 `--show-info` (mu/sigma는 출력하지만 obs는 별도)나
  npz를 직접 print 한다.
- 한계 2: channel permutation이 적용된 ood_obs_shift episode는 ASCII가 의미상 깨질 수
  있음. metadata 헤더의 NOTE에서 명시. 정확한 디버깅이 필요하면 `meta.obs_channel_perm`을
  보고 inverse permutation을 적용해야 한다 (현재 inspect_episode은 자동 적용하지 않음 —
  Session 5/6에서 옵션으로 추가 검토 가능).

---

## 7. Session 5 목표 — Small smoke dataset 생성 및 검증

PART0 Session 5 정의:

Session 5는 **실제 작은 규모의 smoke dataset을 한 번 생성하고 inspect/validate를 통해
환경+generator+config가 end-to-end로 일관되는지 확인**한다.

### 7.1 Session 5에서 해야 할 것

1. small dataset 재생성 (split당 50~200 episode 수준):
   ```powershell
   .\.venv\Scripts\python.exe scripts\generate_dataset.py --config configs\dataset_default.yaml `
     --num-train 100 --num-valid 30 --num-test 30 --num-ood-per-type 30 `
     --max-steps 200 --overwrite --output-root data\smoke
   ```
2. validate 통과 확인:
   ```powershell
   .\.venv\Scripts\python.exe scripts\validate_dataset.py --root data\smoke `
     --strict --max-episodes-per-split 20 `
     --json-report data\smoke\validation_report.json
   ```
3. 여러 split episode inspect (split당 1~2개 수동 확인).
4. dataset statistics 요약 (`scripts/plot_dataset_stats.py --root data\smoke`).
5. determinism check: 같은 yaml + 같은 seed로 두 번 → 같은 dataset.
6. 발견한 모든 이슈를 `docs/SMOKE_REPORT.md`에 기록 (PART0 Session 5 §완료 기준).
7. 명백한 generator/env 결함만 최소 수정. 단, 결함 수정 시 `docs/SMOKE_REPORT.md`에
   "수정 이유 / 영향 / backward compatibility"를 기록.

### 7.2 Session 5에서 금지할 것

PART0 §3 / SESSION1_HANDOFF §6 그대로:

- world model / RSSM / GRU-lite / DreamerV3 / SOTA 코드 절대 금지.
- planner / agent / allocator / world model rollout / falsification metric 코드 금지.
- 학습 loop, optimizer, training run 금지.
- 대규모 dataset 생성 금지 (split당 1k 이상은 시간 / disk 검토 후 별도 페이즈).
- env API / serialization API / dataset schema 변경 금지 (필요 시 본 문서 먼저 갱신).

### 7.3 Session 5가 본 세션의 산출물에 어떻게 의존하는가

- `scripts/validate_dataset.py`의 invariant 목록은 Session 5 smoke의 PASS 기준.
- `scripts/inspect_episode.py`의 출력 포맷은 SMOKE_REPORT의 episode 샘플로 직접 복사 가능.
- `scripts/plot_dataset_stats.py`의 summary.csv는 SMOKE_REPORT의 표로 그대로 사용 가능.
- `falsifiable_regime_world_model/rg4f/dataset_io.py`는 SMOKE_REPORT 작성 시 npz를 빠르게
  로드하는 라이브러리로 사용 가능.

### 7.4 Session 5 시작 전 권장 순서

1. 본 문서 §4 (validate invariant 목록) + §6 (known limitations) 먼저 읽기.
2. `data\smoke` 디렉토리에 dataset 생성 (split당 50~100).
3. `validate_dataset --strict` 통과 확인. FAIL/WARN이 있으면 원인 추적 후 수정.
4. 각 split에서 1개 episode를 inspect로 확인 (특히 ood_room_perm / ood_param_shift /
   ood_obs_shift은 metadata 차이가 잘 드러나는지 확인).
5. `plot_dataset_stats` 통계 + 결과를 `docs/SMOKE_REPORT.md`에 정리.

---

## 8. Self-Audit 결과

| Check | Status | Evidence |
|---|---|---|
| Session 1/2/3 산출물을 모두 읽었는가 | PASS | PART0/Plan/SESSION1_HANDOFF/SESSION2_HANDOFF/SESSION3_HANDOFF + types/config/serialization/generate_dataset/dataset_default.yaml + 실제 manifest.json + train_000000 npz/meta 모두 Read 도구로 확인. |
| 기존 ref/PART0~3와 requirements.txt를 수정하지 않았는가 | PASS | 이 파일 외에 docs / ref / requirements 어떤 것도 수정 0줄. |
| world model / planner / agent 코드를 만들지 않았는가 | PASS | torch import 0회. world_model/planner/agent 디렉토리 없음. dataset_io.py / 3개 script 모두 numpy + 표준 라이브러리만 사용. |
| dataset generator 저장 포맷을 불필요하게 깨지 않았는가 | PASS | `falsifiable_regime_world_model/rg4f/serialization.py` / `scripts/generate_dataset.py` / `configs/dataset_default.yaml` 모두 0줄 변경. 모든 검증/inspection은 기존 schema 그대로 동작. |
| scripts/validate_dataset.py를 생성했는가 | PASS | 본 세션 신규 작성. 156개 PASS/0 WARN/0 FAIL로 smoke dataset 검증 통과. |
| scripts/inspect_episode.py를 생성했는가 | PASS | 본 세션 신규 작성. train + ood_room_perm 모두 정상 출력 확인. |
| directory/file structure 검증이 가능한가 | PASS | `directory.root_exists` / `manifest_present` / `split_dir` / `index.npz_files_exist`. |
| npz schema invariant 검증이 가능한가 | PASS | `npz.required_keys_present` + `npz.group.{true_regime,target_band,field_info}`. 사용자 §2.3의 24항목 그대로 검증. |
| shape invariant 검증이 가능한가 | PASS | `shape.timesteps_consistent` / `local_grid_shape` / `scalar_dim` / `true_state` / `next_local_matches_obs` / `action_mask`. |
| numeric validity 검증이 가능한가 | PASS | `numeric.no_nan_inf` + true_state 범위 + binary dtype + reveal_or_shift enum + actions/task/room range. |
| local_obs_size 기본값 5 및 3/5/7 허용을 검증하는가 | PASS | `shape.local_obs_size_in_3_5_7` (FAIL on others) + `shape.local_obs_size_matches_expected` (manifest의 expected와 비교, WARN). |
| ood_room_perm disjoint를 검증하는가 | PASS | `split_specific.room_perm.disjoint_from_train` + `in_ood_pool`. smoke에서 forced_permutation `(3,1,2,0)`이 train_pool에 없음 PASS. |
| ood_factor_recomb 차이를 검증하는가 | PASS | `split_specific.factor_recomb.families_in_ood_pool`. smoke에서 `[3,3] ⊂ [2,3]` PASS. |
| ood_param_shift 차이를 검증하는가 | PASS | `split_specific.param_shift.differs_from_train`. smoke에서 5개 override key 모두 base와 다름 PASS. |
| ood_obs_shift metadata를 검증하는가 | PASS | `split_specific.obs_shift.channel_perm_valid` + `no_dynamics_change`. smoke에서 perm `[5,9,7,0,4,3,6,1,2,8]` valid PASS. |
| ood_field_placement 차이를 검증하는가 | PASS | `split_specific.field_placement.relocate_flag` + `source_in_grid`. smoke에서 relocate=True PASS. |
| sparse coupling invariant를 검증하는가 | PASS | `sparse_coupling.le2`. 모든 smoke episode의 모든 field가 `|coupled_states| ≤ 2` PASS. |
| inspect_episode.py로 episode 사람이 확인 가능한가 | PASS | metadata / transition summary / step-level / ASCII grid / field·task debug 모두 출력. train + ood_room_perm 둘 다 정상. |
| smoke validate/inspect를 실행했는가 | PASS | §5에 모든 명령 + 결과 기록. validate strict 통과 (156 PASS / 0 WARN / 0 FAIL). |
| docs/SESSION4_HANDOFF.md를 작성했는가 | PASS | 본 문서. |

---

## 9. 본 문서가 Session 5에 던지는 단 한 줄 요약

> **small smoke dataset만 만든다. 본 세션이 만든 `validate_dataset --strict`가 새
> dataset에서도 PASS / 0 FAIL이어야 하고, `inspect_episode`로 사람이 episode를 직접 본 뒤
> `docs/SMOKE_REPORT.md`에 결과를 정리하는 것이 끝이다. 모델/planner/SOTA/대규모
> 실험은 절대 건드리지 않는다.**
