# RG4F_EXECUTION_GUIDE — 실행 가이드

> Session 6 산출물 (3/4). 본 문서는 사용자가 RG-4F 환경/데이터셋 파이프라인을
> 실제 PowerShell 터미널에서 어떻게 실행하고, 어디를 보고 정상/비정상을 판단해야
> 하는지를 명령어 중심으로 정리한다. 모든 명령은 Windows PowerShell + 프로젝트
> 가상환경 (`.\.venv\Scripts\Activate.ps1`)을 전제로 한다.

---

## 1. 가상환경 확인

### 1.1 명령

```powershell
cd C:\Users\computer\Desktop\NeurIPS2026
.\.venv\Scripts\Activate.ps1
where.exe python
python -c "import sys; print(sys.executable)"
pip check
```

### 1.2 정상 기준

| 항목 | 정상 |
|---|---|
| `where.exe python` 첫 줄 | `C:\Users\computer\Desktop\NeurIPS2026\.venv\Scripts\python.exe` |
| `python -c "import sys; print(sys.executable)"` | 동일 경로 |
| `pip check` 출력 | `No broken requirements found.` (또는 metadata 정도의 일부 WARN; ImportError 없음) |
| 핵심 dependency import 가능 | `python -c "import numpy, yaml, tqdm; print(numpy.__version__)"` → `2.1.3` 등 |

### 1.3 비정상 시 조치

- python 경로가 `.venv` 밖이면: `.\.venv\Scripts\Activate.ps1`을 다시 실행하거나 `.\.venv\Scripts\python.exe`를 절대 경로로 호출.
- `pip check`에 broken requirement: `requirements.txt`는 본 6세션 동안 변경 금지이므로 `.venv`를 새로 만든 뒤 `pip install -r requirements.txt`로 재구성.

---

## 2. 빠른 smoke dataset 재생성

### 2.1 명령

```powershell
python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\smoke --num-train 50 --num-valid 20 --num-test 20 --num-ood-per-type 20 --max-steps 200 --overwrite
```

### 2.2 수행 시간 (참고)

- 환경: i7-class CPU + numpy 2.1.3 + 단일 프로세스.
- 예상 소요시간: **6~10초** (smoke 190 episodes × 200 steps).
- Session 5의 실측: 6.70초.

### 2.3 출력 확인

| 경로 | 내용 |
|---|---|
| `data\smoke\manifest.json` | generation metadata. `master_seed`, `train_pool` (12 perms), `ood_pool` (12 perms), `rg4f_config` (resolved RG4FConfig fields), `split_summaries` (8 splits) |
| `data\smoke\<split>\index.jsonl` | split별 episode lookup. 한 줄 = 1 episode |
| `data\smoke\<split>\episodes\<id>.npz` | 한 episode의 numeric arrays (observations / actions / rewards / true_state / true_regime / change_point / reveal_event / shift_event / target_band_* / field_info_mu/sigma / 등) |
| `data\smoke\<split>\episodes\<id>.meta.json` | 한 episode의 정적 metadata (forced_permutation, env_seed, action_seed, behavior_policy, field_info_static, debug_trace) |

### 2.4 정상 판단 체크리스트

```powershell
# 8개 split 모두 존재하는지
Get-ChildItem data\smoke -Directory | Format-Table Name

# 각 split의 episode 수 (index.jsonl line count)
Get-ChildItem data\smoke -Directory | ForEach-Object { 
    $n = (Get-Content "data\smoke\$($_.Name)\index.jsonl" | Measure-Object -Line).Lines
    "$($_.Name): $n episodes"
}

# manifest의 train_pool / ood_pool 분리 확인
python -c "import json; m = json.load(open('data/smoke/manifest.json', encoding='utf-8')); print('train_pool=', len(m['train_pool']), 'ood_pool=', len(m['ood_pool']), 'disjoint=', m['ood_room_perm_disjoint_from_train'])"
```

기대 결과:
- 8개 split 폴더 모두 존재 (train, valid, test_id, ood_room_perm, ood_factor_recomb, ood_param_shift, ood_obs_shift, ood_field_placement).
- train: 50 episodes / valid: 20 / test_id: 20 / 각 OOD: 20 (총 190).
- `train_pool=12 ood_pool=12 disjoint=True`.

---

## 3. Strict validation

### 3.1 명령

```powershell
python scripts\validate_dataset.py --root data\smoke --strict --max-episodes-per-split 50 --json-report data\smoke\validation_report.json
```

### 3.2 정상 기준

| 항목 | 값 |
|---|---|
| 표 마지막 줄 | `=== Validation summary === PASS: 2242  WARN: 0  FAIL: 0` |
| exit code | 0 |
| `data\smoke\validation_report.json` 생성 | 357 KB 수준 |

### 3.3 검증 invariant

`validate_dataset.py`가 자동 검증하는 항목 (categories):

- `directory.*`: root, manifest, split 폴더, `episodes/` subdir, `index.jsonl` 존재
- `split_coverage.all_present`: 8개 split 모두 발견
- `npz.required_keys_present` + `npz.group.*`: schema 필수 key (true_regime / target_band / field_info / agent_position / 등) 그룹별 검증
- `shape.*`: T 일관성, local_grid `(T, H, W, C=10)` square + `H ∈ {3, 5, 7}`, scalar `(T, 14)`, true_state `(T, 5)`, next_observations shape 일치
- `numeric.no_nan_inf`, `numeric.true_state_range` (max|x|<1.05), `numeric.binary_dtype.*` (change_point/reveal/shift/dones는 bool), `numeric.reveal_or_shift_enum` (∈ {0,1,2}), `numeric.actions_*_range` (∈ [0, 16)), `numeric.task_id_range` (∈ [-1, 3]), `numeric.room_id_range` (∈ [-1, 6]), `numeric.reset_flag_always_false`
- `sparse_coupling.le2`: 모든 episode의 모든 invisible field가 `|coupled_states| ≤ 2`
- `split_specific.id_not_ood` (train/valid/test_id의 is_ood=False)
- `split_specific.room_perm.disjoint_from_train` + `in_ood_pool`
- `split_specific.factor_recomb.families_in_ood_pool` (ood family ⊂ {2, 3})
- `split_specific.param_shift.differs_from_train` (override가 실제로 base와 다른 값을 가짐)
- `split_specific.obs_shift.channel_perm_valid` + `no_dynamics_change`
- `split_specific.field_placement.relocate_flag` + `source_in_grid`

### 3.4 비정상 시

- WARN 발생: `--strict` 모드에서는 exit code 1로 처리. WARN이면 일반적으로 수정 권장이지만 학습 진입 차단은 아니다. ENV_AUDIT_REPORT.md에 비교 후 분류.
- FAIL 발생: exit code 1 + 분류된 invariant 위반. 학습 진입 전 반드시 수정. `--verbose`로 자세한 위반 항목 확인:
  ```powershell
  python scripts\validate_dataset.py --root data\smoke --strict --max-episodes-per-split 50 --verbose
  ```

---

## 4. Determinism check

### 4.1 명령

```powershell
python scripts\validate_dataset.py --root data\smoke --check-determinism --config configs\dataset_default.yaml --max-episodes-per-split 3
```

### 4.2 정상 기준

| 항목 | 값 |
|---|---|
| 표 마지막 줄 | `=== Validation summary === PASS: 332  WARN: 0  FAIL: 0` |
| exit code | 0 |
| `determinism.equal_output` | PASS (`two runs of generator with same seed produce identical npz`) |

### 4.3 어떻게 검증하는가

`_check_determinism()`이 임시 디렉토리 두 곳(`tmpdir/a`, `tmpdir/b`)에 generator를 같은 seed=777로 두 번 호출하여 모든 npz의 모든 array를 `np.array_equal`로 byte-equal 비교한다. 검사 후 임시 디렉토리는 자동 삭제.

### 4.4 비정상 시

- subprocess timeout 60초 초과: 더 짧은 max_steps로 재시도하거나 generator의 무한루프 의심.
- npz array differs: 환경 코드에 비결정적 randomness가 들어갔을 가능성. `env.py`의 모든 `rng` 사용처가 외부에서 받은 generator만 쓰는지 확인. global random / time / hostname 의존 검출.

---

## 5. Episode inspection

### 5.1 train episode 1개 확인

```powershell
python scripts\inspect_episode.py --root data\smoke --split train --index 0 --num-steps 5 --show-grid --show-scalar --show-info --save-ascii outputs\smoke_inspections\train_episode0.txt
```

### 5.2 OOD episode 1개 확인 (room_perm + field detail)

```powershell
python scripts\inspect_episode.py --root data\smoke --split ood_room_perm --index 0 --num-steps 5 --show-grid --show-task --show-fields --save-ascii outputs\smoke_inspections\ood_room_perm_episode0_detail.txt
```

### 5.3 무엇을 봐야 하는가

| 확인 항목 | 정상 값 |
|---|---|
| local grid가 5x5인지 | metadata `local_obs_size: 5 (full local_grid shape=[200, 5, 5, 10])` |
| raw_action vs effective_action 분리 | step 출력의 `raw=W eff=A` 같이 두 값이 서로 다른 step이 통계적으로 등장 |
| control-drift remap 동작 | OOD inspect: `control_mode=REV` (또는 CW/LR/UD)일 때 `raw=W eff=S` 같이 변환됨 |
| field_info sparse coupling | `coupled_states ∈ {[noise, vision], [noise, mobility], [noise, interaction], [noise, control_drift]}`, 즉 `|·| = 2` |
| target_band 활성 여부 | `target_band.active=True` 시 `kind ∈ {match_to_band, maximize, threshold, derivative_zero}` 하나, `state_dim` ∈ [0, 4], `half_width=0.02` 등 |
| task_id / room_id 정상 | task_id ∈ {-1, 0, 1, 2, 3}, room_id ∈ {0, 1, 2, 3, 4, 5, 6} |
| ASCII grid 의미 | `@`=agent, `+`=door, `*`=task_object, `S`=stele, `A`=altar, `?`=cue, `#`=wall, `-`=corridor, `.`=floor |

### 5.4 ood_obs_shift 검사 시 주의

ood_obs_shift는 channel permutation으로 cue 채널이 다른 위치에 가 있어 ASCII grid의 cue 표시가 `.....`처럼 보일 수 있다. NOTE 라인이 출력되며, 이는 정상 (Session 5에서 em-dash → ASCII hyphen으로 micro-fix 완료).

---

## 6. 통계 생성

### 6.1 명령

```powershell
python scripts\plot_dataset_stats.py --root data\smoke --out outputs\smoke_stats --max-episodes-per-split 50
```

### 6.2 출력 파일

| 파일 | 내용 |
|---|---|
| `outputs\smoke_stats\summary.csv` | split별 1행 요약. column: `split, num_episodes, len_min, len_mean, len_max, reward_mean, reward_std, completed_max_mean, failure_max_mean, change_point_mean, reveal_mean, shift_mean, action_W%, action_E%, action_state_adjust%, num_invisible_fields_mean` |
| `outputs\smoke_stats\<split>_distributions.csv` | split별 action / task_id / room_id / event_token / field family count 분포 |
| `outputs\smoke_stats\episode_length_hist.png` | 전체 episode length 분포 |
| `outputs\smoke_stats\reward_total_hist.png` | per-episode total reward 분포 (split overlay) |
| `outputs\smoke_stats\change_point_boxplot.png` | split별 change_point per episode 분포 |

### 6.3 정상 기준

| 항목 | 정상 |
|---|---|
| action distribution | movement (W/A/S/D 합) ≈ 55%, E ≈ 15%, state-adjust 합 ≈ 30%, WAIT = 0% |
| reward 분포 | NaN/Inf 없음. 한 split로 collapse 안 함. smoke에서 mean 약 -240 ~ -250 (200-step + step_cost=1 + latency 누적) |
| task_id 분포 | random_biased + 200-step에서는 task=-1이 주를 이룸 (방 밖). 일부 split (ood_factor_recomb 등)에서 task=0/1/2 등장이 정상 |
| change_point | 모두 0이 아님. split별 mean 0.05~0.45 (smoke 기준). 학습용 full dataset에서는 더 두꺼워짐 |
| reveal vs shift | `reveal_mean`과 `shift_mean`이 split별로 다르며, train/test_id/OOD에서 각각 상이한 분포 |

### 6.4 비정상 시

- task_id가 모두 -1: random_biased + 짧은 episode_max_steps의 한계. 학습용 full dataset에서 600-step + 5000 episodes로 해결.
- action이 한쪽으로 collapse: behavior_policy yaml 값 또는 `_build_action_probs` 코드 검토.
- change_point가 모두 0: shift_event가 한 번도 발생 안 함. yaml `shift_probability`가 너무 낮거나 enable_event_triggered_shift=false일 가능성.

---

## 7. 옵션 조절 가이드

`configs/dataset_default.yaml`의 옵션을 사용자가 어떻게 조절할지 정리한다. **모든 수치는 yaml로만 흘러야 한다 (PART0 §3 §4 magic number 금지).**

### 7.1 옵션 표

| 목적 | 옵션 | 기본값 | 조절 방향 | 주의 |
|---|---|---|---|---|
| 출력 디렉토리 | `project.output_root` | `data/rg4f` | smoke=`data/smoke`, full=`data/rg4f` | CLI `--output-root`로 override 가능 |
| 덮어쓰기 | `project.overwrite` | `false` | smoke 반복 실행 시 CLI `--overwrite` 사용 권장 | 기존 dataset 보호용 |
| 학습 episodes | `generation.num_train` | 20 (yaml) | smoke=50, full=5000 | CLI `--num-train`이 우선 |
| 검증 episodes | `generation.num_valid` | 5 | smoke=20, full=500 | CLI `--num-valid` |
| In-distribution test episodes | `generation.num_test` | 5 | smoke=20, full=500 | CLI `--num-test` |
| OOD per-type episodes | `generation.num_ood_per_type` | 5 | smoke=20, full=500. 5종 OOD 각각 적용 | CLI `--num-ood-per-type` |
| Episode 최대 step | `generation.episode_max_steps` | 200 | smoke=200, full=600 (RG4FConfig default) | CLI `--max-steps`. 길수록 task room 진입 통계가 두꺼워짐 |
| Local 관측 크기 (메인) | `environment.local_obs_size` | 5 | **메인=5 고정**. ablation 시만 3 또는 7 | `__post_init__`이 `{3, 5, 7}` 외 값 거부 |
| Ablation 후보 | `environment.local_obs_ablation_values` | `[3, 5, 7]` | 변경 비권장 | 3과 5와 7이 모두 포함되어야 함 (`__post_init__` 강제) |
| Drift 강도 | `environment.drift_strength` | 0.01 | full default 유지. ood_param_shift는 ×2.0 | yaml friendly key → `field_mu_drift_sigma` 변환 |
| Shift 확률 | `environment.shift_probability` | 0.05 | full default 유지. ood_param_shift는 ×2.0 | 모든 `shift_prob_per_*`에 동일 적용 |
| Stochastic miscontrol prob | `environment.stochastic_miscontrol_prob` | 0.05 | full default 유지 | yaml friendly key → `miscontrol_p_low` 변환 |
| Periodic slip 주기 | `environment.periodic_slip_period` | 4 | adaptation/correction hard case ablation에서만 변경 | `enable_periodic_slip=true`일 때만 작동 |
| Periodic slip 활성 | `environment.enable_periodic_slip` | true | full default 유지 | adaptation/correction 분리 검증 핵심 |
| Invisible field 활성 | `environment.enable_invisible_fields` | true | full default 유지 | false면 모든 field effect 무력화 — ablation only |
| Event-triggered shift 활성 | `environment.enable_event_triggered_shift` | true | full default 유지 | false면 abrupt shift 발생 안 함 — ablation only |
| Field coupling 종류 | `environment.field_coupling_type` | sparse_family_limited | metadata-only label | 의미적 변경 없이 이름만 |
| Task permutation 모드 | `environment.task_permutation_mode` | split_aware | split-aware: train/OOD disjoint pool. random: 단순 random (ablation only) | generator-level 정책 |
| Target band 폭 | `environment.target_band_width` | 0.02 | full default 유지 | task별 target band의 half-width |
| Behavior policy | `generation.behavior_policy` | random_biased | full default 유지. random_uniform은 ablation only | task_probe 추가는 P1 후보 |

### 7.2 핵심 명시

- **`local_obs_size = 5`가 메인 세팅이다.** 7×7 main 고정 아님.
- **`local_obs_size = 3`은 hard visibility ablation** — partial observability 압력 극단 상승.
- **`local_obs_size = 7`은 easy visibility ablation** — hidden state belief 압력 약화.
- **`episode_max_steps = 200`은 smoke용** (CLI override). 학습용 full dataset은 600 이상 권장.
- **smoke `num_train=50`과 학습용 `num_train=5000`은 다름**. smoke는 environment + generator + validator + inspector + stats가 end-to-end로 정상 작동하는지의 sanity check 용도.
- **OOD split은 반드시 별도 생성/검증해야 함**. 8개 split을 한 번에 생성하는 single command가 표준 (`scripts/generate_dataset.py`가 자동 분리).

---

## 8. 학습용 full dataset 권장 시작값

### 8.1 권장 config (실제 full generation은 사용자가 명시적으로 실행할 때만 한다)

| 항목 | 권장 시작값 | 근거 |
|---|---|---|
| `num_train` | 5000 | RG4F_Environment_Plan §9 default. 4 task family × 5 task complexity × ~250 episode/cell 추정 |
| `num_valid` | 500 | 학습 중 model selection + hyperparameter tuning |
| `num_test` (test_id) | 500 | in-distribution generalization |
| `num_ood_per_type` | 500 | OOD 5종 각각 — 통계 안정성 |
| `episode_max_steps` | 600 | yaml default. random_biased로 task room 진입 + 다단계 task progression 가능 |
| `local_obs_size` | 5 | 메인 세팅 (PART0/Plan §3.1) |
| `local_obs_ablation_values` | `[3, 5, 7]` | ablation 후보 — config validation에 사용 |
| `behavior_policy` | random_biased (1차) → 학습 후 진단 결과 task_probe 추가 검토 (2차) | ENV_FIX_INSTRUCTIONS Issue 3 |
| `seed` | 42 (또는 실험 명세에 따라 변경) | 모든 split의 master seed |
| OOD split 정책 | 모두 yaml default 유지 | train_pool=12, ood_pool=12, ×2.0 multipliers |

### 8.2 명령 예시 (사용자가 명시 실행 시)

```powershell
python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\rg4f --num-train 5000 --num-valid 500 --num-test 500 --num-ood-per-type 500 --max-steps 600 --overwrite
```

예상 소요시간 (CPU 단일 프로세스): **60~150분** (8 splits × episode 수 × 600 step × ~수ms per step). 환경에 따라 변동.

### 8.3 학습용 dataset 생성 후 반드시 실행

```powershell
# 1. strict validation
python scripts\validate_dataset.py --root data\rg4f --strict --max-episodes-per-split 100 --json-report data\rg4f\validation_report.json

# 2. determinism check (선택)
python scripts\validate_dataset.py --root data\rg4f --check-determinism --config configs\dataset_default.yaml --max-episodes-per-split 3

# 3. 통계
python scripts\plot_dataset_stats.py --root data\rg4f --out outputs\rg4f_stats --max-episodes-per-split 200
```

본 6세션 안에서는 학습용 full dataset 생성을 수행하지 않는다 (PART0 §3 / 사용자 요구사항 §1: "장시간 실행 금지"). 사용자가 명시적으로 실행할 때만 진행.

---

## 9. 문제 발생 시 확인 순서

### 9.1 import error (가장 흔함)

| 증상 | 원인 | 조치 |
|---|---|---|
| `ModuleNotFoundError: No module named 'falsifiable_regime_world_model'` | `.venv` 활성화 안 됨 / sys.path에 프로젝트 루트 미포함 | `.\.venv\Scripts\Activate.ps1` 실행. script들은 `Path(__file__).resolve().parents[1]`을 sys.path에 자동 추가. |
| `ModuleNotFoundError: No module named 'numpy'` | `.venv`가 망가졌거나 dependency 미설치 | `pip install -r requirements.txt` (단 본 6세션에서는 requirements.txt 변경 금지) |
| `ImportError: cannot import name 'XYZ' from 'falsifiable_regime_world_model.rg4f'` | 패키지 구조 변경 또는 부분 수정 후 import 캐시 꼬임 | `Get-ChildItem -Recurse __pycache__ \| Remove-Item -Recurse -Force` 후 재실행 |

### 9.2 .venv가 아닌 python 사용

| 증상 | 원인 | 조치 |
|---|---|---|
| `where.exe python` 첫 줄이 `.venv` 밖 | global Python 우선 | `python` 대신 `.\.venv\Scripts\python.exe` 절대 경로 호출 또는 PowerShell 세션 재진입 후 `Activate.ps1` 재실행 |

### 9.3 overwrite error

| 증상 | 원인 | 조치 |
|---|---|---|
| `[ERROR] output_root <path> already exists. Use --overwrite or set project.overwrite=true.` | 기존 출력 디렉토리 존재 | `--overwrite` 추가 또는 `data\smoke` 폴더 삭제 |

### 9.4 validation FAIL

| 증상 | 원인 | 조치 |
|---|---|---|
| `numeric.no_nan_inf` FAIL | 환경 코드의 division by zero / overflow | `env.py`의 `_compute_movement_cooldown` 등 numerical safety 검토 |
| `shape.local_grid_channels` FAIL | `LOCAL_CHANNELS` enum 변경 vs npz 비호환 | yaml + types.py + observation.py 일관성 검토 |
| `sparse_coupling.le2` FAIL | field가 3개 이상 state dim에 coupling | `RG4FConfig.field_coupling_max_dims=2` 강제 / `types.FIELD_COUPLED_STATES` 검토 |
| `split_specific.room_perm.disjoint_from_train` FAIL | train_pool과 ood_pool이 우연히 동일 permutation 포함 | `_build_permutation_pools`의 `ood_use_disjoint=true` 확인. `manifest.json`의 `train_pool` / `ood_pool` 직접 비교 |

### 9.5 determinism FAIL

| 증상 | 원인 | 조치 |
|---|---|---|
| `determinism.equal_output` FAIL | 환경 코드에 비결정적 randomness | `env.py`/`fields.py`/`tasks.py`/`observation.py`/`map_generator.py`에서 `np.random` global 사용 / `random.random()` global 사용 / `time.time()` 검색. 모두 `rng: np.random.Generator` 인자로 받아야 함 |

### 9.6 Unicode/encoding issue (Windows cp949)

| 증상 | 원인 | 조치 |
|---|---|---|
| `UnicodeEncodeError: 'cp949' codec can't encode character` | em-dash, 화살표, 한글 등이 cp949로 인코딩 불가 | Session 5에서 `inspect_episode.py`의 em-dash → ASCII hyphen + `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` 안전망 추가 완료. 다른 script에서 발생 시 동일 패턴 적용 |

### 9.7 npz schema mismatch

| 증상 | 원인 | 조치 |
|---|---|---|
| `npz.required_keys_present` FAIL with missing keys | dataset_io.py의 `REQUIRED_NPZ_KEYS_FLAT` 변경 또는 serialization.py 변경 시 schema 불일치 | 두 파일을 single source of truth로 동기화. validate가 더 엄격하므로 dataset_io.py가 master |

### 9.8 OOD invariant fail

| 증상 | 원인 | 조치 |
|---|---|---|
| `split_specific.factor_recomb.families_in_ood_pool` FAIL | family filter retry 8회 실패 | `RG4FConfig.num_fields_max` 확인. 너무 작으면 family filter 후 빈 fields가 자주 발생 |
| `split_specific.field_placement.relocate_flag` FAIL | episode meta에 `relocate_fields_room_center` 누락 | generator의 `_run_one_episode`가 relocate 이후 meta에 기록하는지 확인 |
| `split_specific.obs_shift.channel_perm_valid` FAIL | obs_perm이 length=10 permutation이 아님 | generator의 `_build_split_plans` 검토 (`np.random.permutation(C)`) |

### 9.9 local_obs_size mismatch

| 증상 | 원인 | 조치 |
|---|---|---|
| `shape.local_obs_size_matches_expected` WARN | npz의 local_grid 크기가 manifest의 expected와 다름 | yaml + RG4FConfig.local_obs_size + npz `(T, H, W, 10)` 일관성 검토. ablation dataset과 main dataset을 한 디렉토리에 섞으면 발생 가능 |

---

## 10. 빠른 reference

### 10.1 자주 쓰는 명령 (한 줄 요약)

```powershell
# 1. smoke 재생성 (~7초)
python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\smoke --num-train 50 --num-valid 20 --num-test 20 --num-ood-per-type 20 --max-steps 200 --overwrite

# 2. strict validation (~6초)
python scripts\validate_dataset.py --root data\smoke --strict --max-episodes-per-split 50 --json-report data\smoke\validation_report.json

# 3. determinism (~6초)
python scripts\validate_dataset.py --root data\smoke --check-determinism --config configs\dataset_default.yaml --max-episodes-per-split 3

# 4. inspect train + OOD (~3초)
python scripts\inspect_episode.py --root data\smoke --split train --index 0 --num-steps 5 --show-grid --show-info
python scripts\inspect_episode.py --root data\smoke --split ood_room_perm --index 0 --num-steps 5 --show-grid --show-task --show-fields

# 5. stats (~5초)
python scripts\plot_dataset_stats.py --root data\smoke --out outputs\smoke_stats --max-episodes-per-split 50

# 6. dry-run (config 검증만, IO 없음)
python scripts\generate_dataset.py --config configs\dataset_default.yaml --dry-run
```

### 10.2 monitoring file size (참고)

| 항목 | smoke (190 episodes) | full (8000 episodes 추정) |
|---|---|---|
| `data\smoke` 전체 | ~15 MB | ~5~10 GB |
| 한 episode npz | ~18 KB (200 step) | ~55 KB (600 step) |
| 한 episode meta.json | ~60 KB (debug_trace 포함) | ~180 KB |
| 한 episode total | ~78 KB | ~235 KB |

`metadata.save_debug_trace=false`로 두면 episode_meta.json이 수 KB로 줄지만 step-level inspect 시 trace를 잃게 된다.
