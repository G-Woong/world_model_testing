# Step 11 PLAN — ManiSkill state-only 고품질 데이터 파이프라인

> Status: PLAN ONLY (코드 수정 / 데이터 수집 / 학습 실행 / phase gate sentinel 생성 금지)
> 작성일: 2026-05-23
> 선행: Step 10 완료 (synthetic toy R3 smoke PASS, R0/R1/R2.passed 존재).
> 사용자 결정 (이 PLAN에 명시적으로 반영됨):
> - 데이터 경로 = 2단계 (synthetic → ManiSkill 순차). Step 11은 ManiSkill 실데이터 단계.
> - 이 단계에서 **R3.passed sentinel 생성 금지**. R3 정식 gate는 별도 phase-check.
> - garbage data 0 허용: 수집 전/중/후 10개 checkpoint 통과 강제.
> - 실패는 종료가 아니라 `diagnose → repair candidate → retest` 흐름의 입력.

---

## Context

Step 10에서 `synthetic toy → encoder/belief/dynamics → trainer → evaluator → R3SmokeRunner → run_repair_loop → ledger` 흐름은 검증됐다 (185 tests passed, `docs/STEP10_RESULT_REPORT.md`). 그러나 synthetic toy의 `mass=2.0` / `friction=0.5` OOD는 `ood_id_nll_diff = 0.0065`로 측정됐다 — 이는 `OOD_TOO_EASY` 임계값(0.05) 미달이며 **falsification gate 학습 신호로 부적합**하다. FGLC의 핵심 주장(wrong-dynamics-hypothesis falsification, standardized mismatch, sparse correction)을 실제로 검증하려면 ManiSkill state-only ID/OOD trajectory가 필수다.

본 단계의 목적은 **R3.passed sentinel 생성이 아니라**, FGLC novelty 검증에 사용 가능한 수준의 ManiSkill state-only 데이터 계약·수집·검증·정제·저장 체계를 만드는 것이다. R3.passed 생성은 (a) 본 단계의 high-quality smoke 데이터셋 위에서 base WM이 4060 smoke gate(ID NLL ≤ 0.5 nat, OOD−ID gap ≥ 0.05 nat)를 통과한 후 별도 phase-check로 닫는다.

---

## A. 현재 repo 상태 감사

### A.1 phase sentinel 상태 (`outputs/phase_gates/`)
- `R0.passed` (2026-05-22 15:59)
- `R1.passed` (2026-05-23 18:59)
- `R2.passed` (2026-05-23 19:17 — synthetic mini-closure 기준; ManiSkill 실데이터 R2 통과는 별도 검토 필요)
- `R3.passed` **부재** — 본 단계에서도 생성 금지

### A.2 src/fglc/ 코드 상태
| 영역 | 파일 | ManiSkill 적합성 |
|---|---|---|
| `schemas/` | `visibility.py` (12 FORBIDDEN_AGENT_FIELDS) | OK — SSoT 유지 |
| `data/` | `state_only_dataset.py` (SyntheticToyDataset만), `dataloader.py` (synthetic만 분기) | **NOT OK** — ManiSkill 분기 추가 필요 |
| `models/` | encoder.py, belief.py, dynamics.py, heads.py (K=6, d=32, h_dim=128) | OK — task별 D_x/D_a 변경 가능성 점검 필요 |
| `training/` | trainer_r3.py (Stage 1 loss) | OK — collator 일반화만 필요 |
| `evaluation/` | metrics.py (CANONICAL_METRIC_KEYS 17개) | OK — `ood_mass_nll`/`ood_friction_nll` 있음 |
| `runners/` | r3_runner.py (RepairRunner Protocol 구현) | OK — dataset.type 분기 인지 가능 |
| `repair/` | taxonomy.py (20 cause), diagnose.py, candidates.py, orchestrator.py, ledger.py | OK — 단 OOD_TOO_HARD / EVAL_NOISE_HIGH **후보 부재** (§J.D6에서 보강) |

### A.3 scripts/fglc/
- `repair_loop.py` (mock + real runner 분기)
- `r3_smoke.py` (synthetic 진입점)
- **부재**: `collect_maniskill.py`, `validate_dataset.py`, `build_split.py` — 본 단계에서 신규 생성 대상

### A.4 configs/fglc/
- `smoke_4060.yaml` 현 schema: `dataset.type: synthetic_toy` + `D_x=8, D_a=4, episode_len=64, ood_mass_scale=2.0, ood_friction_scale=0.5` — **synthetic 전용**.
- ManiSkill용 분기 필요: `dataset.type: maniskill_state_only`, `task: PickCube-v1`, `ood_axis: {mass,friction,...}`, `n_episode_*`, storage path, manifest path.

### A.5 tests/
- 현재 185 passed (Step 10 결과). dataset 6 + WM 8 + trainer 6 + r3_runner 6 = 26개가 synthetic 전제.
- **부재**: `test_fglc_maniskill_collector.py`, `test_fglc_split_integrity.py`, `test_fglc_ood_severity.py`, `test_fglc_no_garbage.py` — 본 단계에서 신규 추가.

### A.6 의존성 상태
- `requirements.txt` 154 핀에서 `gymnasium==1.2.3`만 존재. **`mani-skill` / `sapien` / `h5py` / `hydra-core` / `omegaconf` 모두 미핀** → BLOCKED.
- `pyproject.toml` core dependencies에 `h5py>=3.9`, `hydra-core>=1.3`, `omegaconf>=2.3` 명시되어 있으나 venv 실제 설치 상태 UNKNOWN.
- `[maniskill]` extras: `mani-skill>=3.0.0b18`, `sapien>=3.0.0` — 미설치.
- **Windows + ManiSkill 호환성 UNKNOWN** — ManiSkill v3는 SAPIEN 기반이며, SAPIEN의 Windows 지원은 공식 문서 재확인 필요.

### A.7 outputs / data 저장 상태
- `data/` 디렉터리 자체가 `.gitignore`로 차단 (`data/*`, `!data/README.md`).
- `data/README.md` 부재 → 신규 생성 후보(manifest 인덱스 역할).
- `outputs/*`도 동일 패턴.
- `*.npz` / `*.npy` / `*.pkl` / `*.pickle` / `*.jsonl` 차단. **`*.h5` / `*.hdf5` 명시 차단 패턴 없음** → 명시 추가 권고 (Codex TASK 비범위, manual edit).
- HDF5 large file을 commit하지 못하도록 `data/fglc/*.h5` ignore 검증 필요.

### A.8 forbidden field SSoT
- `src/fglc/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS` 12개: `regime_id, true_mass, true_friction, true_latency, true_noise_sigma, true_action_gain, oracle_action, counterfactual_reward, split_id, ood_type, seed, template_id`.
- 본 단계 collector는 **반드시 위 필드를 모델 입력 dict에서 제거**한 후 batch를 반환해야 한다. raw 저장 시에는 평가 전용 partition으로 분리.

---

## B. Step 목표 재정의

본 단계 = **R2 ManiSkill 데이터 계약 단계**.

| 구분 | 본 단계 (Step 11) | DEFERRED (별도 phase) |
|---|---|---|
| ManiSkill state-only collector probe | ✅ 포함 | — |
| transition / episode / split / manifest schema 정의 | ✅ 포함 | — |
| ID + OOD-mass + OOD-friction 소규모 수집 | ✅ 포함 (smoke 규모) | OOD-latency/noise/gain/mixed = DEFERRED |
| 10개 quality checkpoint 통과 | ✅ 포함 | — |
| dataloader ManiSkill 분기 추가 | ✅ 포함 | — |
| R3 base WM 1 batch forward 검증 | ✅ 포함 | full 학습 = DEFERRED |
| repair loop metric artifact 연결 | ✅ 포함 (smoke 1-iter dry) | full repair loop = DEFERRED |
| `R3.passed` sentinel 생성 | ❌ 금지 | 별도 phase-check |
| 정식 R3 gate 통과 (ID NLL < 0.1 nat) | ❌ 범위 밖 | DEFERRED |
| RGB-D / DROID / BridgeData / baseline grid | ❌ 범위 밖 | DEFERRED |
| 다른 task (PushCube/LiftCube) 동시 수집 | ❌ 범위 밖 | DEFERRED (사용자 결정 §K1 후) |

### 본 단계의 완료 = "다음 단계로 진입 가능한 데이터 계약이 검증됨"

다음 단계 진입의 정의:
1. ManiSkill state-only collector가 Windows + 4060 환경에서 안정적으로 동작한다.
2. ID + 2개 OOD(mass/friction) split이 garbage 0건으로 저장됐다.
3. base WM이 해당 dataloader로 1 epoch smoke 학습 가능하다.
4. metric artifact가 `id_nll`, `ood_mass_nll`, `ood_friction_nll`, `ood_id_nll_diff`를 정상 생성한다.
5. `ood_id_nll_diff`가 `OOD_TOO_EASY` 임계값(0.05) 초과, `OOD_TOO_HARD` 임계값(2.0) 미만의 의미 있는 분포로 측정된다.

---

## C. 데이터 계약 (Contract Schemas)

### C.1 Transition schema (`src/fglc/schemas/`)
모델 입력용 (FORBIDDEN 필드 제거 후):
```python
inference_transition = {
    "state":  Tensor[D_x],  # 로봇 qpos + object_pose + goal (state_dict concat)
    "action": Tensor[D_a],  # delta EEF + gripper
    "reward": float,
    "done":   bool,
}
```

평가 전용 partition (모델 입력 절대 금지):
```python
eval_only_transition = {
    "regime_id":    int,   # OOD 분할 식별자
    "ood_type":     str,   # "id" | "ood_mass" | "ood_friction"
    "true_mass":    float,
    "true_friction": float,
    "true_latency": int,
    "true_noise_sigma": float,
    "true_action_gain": float,
    "episode_id":   int,
    "step_idx":     int,
    "split":        str,   # "train_id" | "val_id" | "test_id" | "ood_*"
    "task_id":      str,   # "PickCube-v1"
    "seed":         int,
    "template_id":  str,
    "success":      bool,  # episode 종료 시 success flag (optional)
}
```

`assert_no_forbidden_fields(inference_transition)`는 매 batch 통과 강제.

### C.2 Episode schema
```python
episode = {
    "transitions": list[inference_transition],   # length = episode_len
    "eval_only": list[eval_only_transition],     # length = episode_len, parallel index
    "metadata": {
        "task_id": "PickCube-v1",
        "episode_id": int,
        "seed": int,
        "split": str,
        "regime_id": int,
        "ood_type": str,
        "ood_params": dict,  # e.g., {"object_mass": 1.5}
        "length": int,
        "terminated_reason": str,  # "success" | "max_steps" | "timeout" | "invalid"
        "success": bool,
        "config_hash": str,
        "git_sha": str,
        "maniskill_version": str,
    },
}
```

### C.3 Split schema (`split_config.yaml`)
```yaml
task: PickCube-v1
maniskill_version: <pinned>
git_sha: <pinned>
seed_pool:
  train_id: [42, 43, ..., 91]      # 50 seeds
  val_id:   [200, 201, ..., 209]   # 10 seeds
  test_id:  [300, 301, ..., 309]   # 10 seeds
  ood_mass_low:     [500, ..., 509]   # 10 seeds, object_mass=1.5
  ood_friction_low: [600, ..., 609]   # 10 seeds, friction=0.7
  # DEFERRED: ood_mass_high, ood_friction_high, latency/noise/gain/mixed
overlap_check: hash_set_disjoint
ood_params:
  ood_mass_low: { object_mass: 1.5 }
  ood_friction_low: { friction: 0.7 }
```

### C.4 Manifest schema (`manifest.json`)
```json
{
  "manifest_version": "v1",
  "task_id": "PickCube-v1",
  "maniskill_version": "<resolved>",
  "git_sha": "<sha>",
  "config_hash": "<hash>",
  "created_at": "<ISO>",
  "splits": {
    "train_id": {
      "n_episodes": 50,
      "n_transitions": <int>,
      "episode_ids": [...],
      "seed_pool": [42, ..., 91],
      "storage": "data/fglc/PickCube-v1/train_id.h5",
      "hash": "<sha256_of_h5>"
    },
    "val_id": {...},
    "test_id": {...},
    "ood_mass_low": {..., "ood_params": {"object_mass": 1.5}},
    "ood_friction_low": {..., "ood_params": {"friction": 0.7}}
  },
  "rejected_episodes": [
    {"episode_id": 17, "seed": 59, "split": "train_id", "reason": "all_state_static", "stage": "checkpoint_2"}
  ],
  "collector_command": "<verbatim>",
  "validation_command": "<verbatim>",
  "quality_report_path": "data/fglc/PickCube-v1/quality_report.json"
}
```

### C.5 Stats schema (`dataset_stats.json`)
각 split별로:
- `state_mean`, `state_std` (vector)
- `action_mean`, `action_std`
- `state_delta_norm_mean`, `..._p50`, `..._p95`
- `action_delta_response_mean`, `..._p95`
- `reward_mean`, `reward_std`, `reward_min`, `reward_max`
- `episode_length_mean`, `..._min`, `..._max`, `..._stdev`
- `done_per_episode_count_mean`
- `success_rate`
- `nan_inf_count` (must be 0)
- `D_x`, `D_a` (must be constant within split)

### C.6 Quality report schema (`quality_report.json`)
```json
{
  "checkpoint_0_dependency": "PASS",
  "checkpoint_1_schema":     "PASS",
  "checkpoint_2_dynamics":   "PASS",
  "checkpoint_3_split":      "PASS",
  "checkpoint_4_ood_sev":    "PASS",
  "checkpoint_5_learnability":"PASS",
  "checkpoint_6_repair_metric":"PASS",
  "checkpoint_7_storage":    "PASS",
  "checkpoint_8_reproducibility":"PASS",
  "checkpoint_9_novelty":    "PASS",
  "rejections_by_reason": {"all_state_static": 1, "duplicate_hash": 0},
  "warnings": []
}
```

---

## D. ID/OOD split 설계 (smoke 규모)

### D.1 우선 task
- **PickCube-v1**만 우선 (사용자 결정 §K1).
- PushCube / LiftCube = DEFERRED.

### D.2 split 별 episode 수 (4060 smoke 예산)
| split | seed pool | n_episodes | n_transitions (est. ep_len ~80) |
|---|---|---|---|
| train_id        | 50 seeds | 50 | ~4,000 |
| val_id          | 10 seeds | 10 | ~800 |
| test_id         | 10 seeds | 10 | ~800 |
| ood_mass_low    | 10 seeds | 10 | ~800 (`object_mass=1.5`) |
| ood_friction_low| 10 seeds | 10 | ~800 (`friction=0.7`) |
| **합계** | 90 | 90 | ~7,200 |

근거: `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md` L29 "200 smoke / 500 standard"를 4060 + Windows + ManiSkill 첫 진입에 맞춰 **첫 probe는 90 ep로 축소**. 검증 통과 후 episode 수 증가는 `DATA_TOO_SMALL` repair candidate(`patch={"num_episodes": 200}`) 흐름을 따른다.

### D.3 OOD 축 선택
사용자 결정 §K4에 따름. PLAN default 권장:
- **선택**: `ood_mass_low` (object_mass=1.5), `ood_friction_low` (friction=0.7).
- 근거: `docs/idea/18_DATA_BENCHMARKS.md` L43-44, ManiSkill PickCube에서 가장 직접적으로 dynamics에 영향, novelty 검증 신호 가장 큼.
- **DEFERRED**: `ood_latency`, `ood_noise`, `ood_action_gain`, `ood_mixed`, mass=0.5/2.0 / friction=0.3/1.5 (severity 변화는 OOD_TOO_EASY/HARD repair candidate가 발화될 때 도입).

### D.4 severity 등급
- low: mass=1.5, friction=0.7 (이번 수집).
- medium: mass=2.0, friction=0.5 (다음 round, repair candidate가 발화 시 자동).
- high: mass=0.5 / 2.5+, friction=0.3 (DEFERRED).

severity 변경은 split을 신규 추가하는 방식이며 기존 split 데이터를 덮어쓰지 않는다.

### D.5 split leakage 방지 규칙
- `seed_pool` 6 set 모두 set-disjoint (집합 교집합 0 검증).
- episode trajectory hash (state sequence sha256) 중복 검증 — split 내·간 모두.
- 같은 (task, seed, ood_params) tuple이 두 split에 등장 금지.
- `regime_id`는 split별 고정 정수 (train_id=0, val_id=1, test_id=2, ood_mass_low=10, ood_friction_low=20).
- ID split episode가 OOD parameter로 reset되거나, OOD split episode가 ID parameter로 reset되면 **즉시 reject + log**.

---

## E. 수집 전 checkpoint (Phase A — Collector Audit)

### Checkpoint 0. Dependency gate
검증 명령 (PLAN — execute 단계에서 실제 실행):
```powershell
.\.venv\Scripts\python.exe -c "import mani_skill; print(mani_skill.__version__)"
.\.venv\Scripts\python.exe -c "import sapien; print(sapien.__version__)"
.\.venv\Scripts\python.exe -c "import h5py; print(h5py.__version__)"
.\.venv\Scripts\python.exe -c "import gymnasium; print(gymnasium.__version__)"
```

기대:
- mani-skill ≥ 3.0.0b18
- sapien ≥ 3.0.0
- h5py ≥ 3.9
- gymnasium 1.2.3 (이미 핀됨)

**실패 시 처리**: BLOCKED(§L)로 분류. `requirements.txt` 핀 추가 PR을 별도 호출(사용자 승인 후). 핀 추가 전까지 본 단계 진행 불가.

### Checkpoint 1a. Task availability probe
```python
import gymnasium as gym
import mani_skill.envs  # 등록 트리거
env = gym.make("PickCube-v1", obs_mode="state_dict")
obs, info = env.reset(seed=42)
# 확인: obs는 dict인가, robot_qpos/object_pose/goal 키가 있는가
```

검증: PickCube-v1이 등록되고 state_dict obs가 반환되는가.

### Checkpoint 1b. State/Action shape probe
```python
print(env.observation_space)   # dict, leaf shape 고정 여부
print(env.action_space.shape)  # D_a 고정
flat_state = flatten(obs)      # concat로 1D 벡터화 — D_x 결정
print(flat_state.shape)
```

검증: 모든 step에서 `flat_state.shape` 일정. 미일정 시 reject.

### Checkpoint 1c. Step/reward/done probe
```python
for _ in range(10):
    a = env.action_space.sample()
    obs, r, term, trunc, info = env.step(a)
print(r, term, trunc, info.get("success"))
```

검증: r은 float scalar, term/trunc는 bool, info에 success가 있는지 확인 (있으면 manifest에 기록).

### Checkpoint 1d. Seed reproducibility probe
같은 seed로 두 번 reset + 동일 action sequence → 동일 state sequence 검증.
검증: 모든 t에서 `state_run1[t] == state_run2[t]` (numerical tolerance).

**중요**: ManiSkill 일부 환경은 SAPIEN 내부 GPU/CPU 결정성이 깨질 수 있음. seed 재현성이 불완전하면 manifest에 `reproducibility: "approximate"`로 기록 + warning.

### Checkpoint 1e. OOD parameter API probe
ManiSkill에서 `object_mass` / `friction`을 변경하는 정확한 API는 **UNKNOWN**. 다음 후보를 순차 시도:
1. `gym.make(..., reconfig_kwargs={"object_mass": 1.5})` (v3 reconfig path)
2. `env.unwrapped.set_physical_param(...)` (있다면)
3. `env._objs[...].set_mass(1.5)` (SAPIEN 직접 호출)
4. ManiSkill `domain_randomization` config
5. `env.reset(options={"object_mass": 1.5})`

검증:
- 적어도 1개 API가 동작하여 OOD parameter가 실제 dynamics에 반영되는가.
- 같은 action sequence에서 ID와 OOD state trajectory의 L2 norm 차이가 ε 이상.

실패 시: `OOD_API_UNKNOWN` BLOCKED(§L). synthetic fallback도 제시(`SyntheticToyDataset`에 friction=0.5 — Step 10 결과 OOD_TOO_EASY).

---

## F. 수집 중 checkpoint (Phase B/C — Probe + Smoke Collection)

### F.1 Phase B — Tiny probe (5 episodes 미저장)
- `n_episodes_probe = 5` (train_id seed [42..46])
- **저장 금지** (임시 메모리 또는 `tmp/` 외부)
- 검증:
  - schema 안정성 (모든 episode가 동일 D_x, D_a, 동일 obs key 구조)
  - step success rate, episode 길이 분포
  - state/action에 NaN/Inf 없음
- fail 시 정식 수집 진입 차단.

### F.2 Phase C — Smoke 수집 진입 조건
Phase B PASS + 사용자 §K5/§K6 답변(storage format/location) 받은 후에만 진입.

### F.3 Per-episode 실시간 검증 (수집 중 인라인)
각 episode가 끝나면 즉시 다음 검사 → fail 시 **저장 큐에 넣지 않음**(quarantine):

| 검사 | 기준 | reject reason |
|---|---|---|
| 모든 state ≈ 동일 | `np.std(states, axis=0).max() < 1e-4` | `all_state_static` |
| action ≈ 0 | `np.abs(actions).max() < 1e-3` | `all_action_zero` |
| `next_state - state ≈ 0` | `np.linalg.norm(diff).mean() < 1e-4` | `no_transition` |
| reward 분포 zero variance | `np.std(rewards) < 1e-6` | `reward_flat` |
| episode length = 1 | `len < 2` | `episode_too_short` |
| episode length 비정상 짧음 | `len < min_episode_len (default 10)` | `episode_short` |
| done 발생 안 함 | `not any(done)` | `no_done_signal` |
| done 매 step | `all(done[:-1])` | `done_flood` |
| NaN/Inf 검출 | `np.isnan + np.isinf any` | `numerical_invalid` |

reject 시 manifest `rejected_episodes` 배열에 추가 + 해당 split의 episode 수를 채우기 위해 다음 seed로 재시도 (재시도 한도 default = 3).

### F.4 Collection budget cap (per-split)
- 한 split의 episode 수집이 wall-clock 20분 초과 시 abort.
- 누적 reject > accepted * 0.5 시 abort + BLOCKED 보고 (collector 자체 문제 시사).

### F.5 Online stats (수집 중 streaming)
각 split의 stats(§C.5)는 Welford streaming 알고리즘으로 episode 추가마다 갱신. 메모리 누적 trajectory 보관은 4060 RAM 한계 대비 위험.

---

## G. 수집 후 checkpoint (Phase D — Validation)

### Checkpoint 1. Schema gate
각 transition에 §C.1 inference 필드 4개 + §C.1 eval-only 필드가 분리 저장됐는가. inference에 FORBIDDEN 12개가 0건인가 (`assert_no_forbidden_fields` per-batch).

### Checkpoint 2. Dynamics sanity gate (전체 split별 통계)
이미 per-episode reject가 통과해도, split 단위에서 다음 재검증:
- 전체 state matrix의 rank가 D_x 근접 (rank deficiency = synthetic-like garbage)
- action 분포가 action_space와 매칭
- reward 분포의 매 quantile이 reasonable
- episode length distribution mean/std (4060 smoke에서 너무 짧으면 학습 신호 부족)

### Checkpoint 3. Split integrity gate
- seed_pool 6 set 교집합 = ∅ 검증
- episode trajectory hash uniqueness (split 내·간)
- `regime_id` 별 split 매칭 일관성
- ID split에 OOD params가 적용된 episode 0건
- OOD split에 ID params (mass=1.0 / friction=1.0)가 적용된 episode 0건

### Checkpoint 4. OOD severity gate
ID와 OOD 비교 metric:
- `state_delta_norm_mean(OOD) - state_delta_norm_mean(ID)` 절대값 > δ_min (default 0.01)
- `reward_mean(OOD) - reward_mean(ID)` 절대값 > δ_reward_min
- `episode_length_mean(OOD) - episode_length_mean(ID)` 절대값 > δ_len_min
- success_rate(OOD) ≠ success_rate(ID) (significant difference Bayesian test)

추가: **simple one-step linear baseline 학습** 후 `OOD_NLL - ID_NLL`을 측정 → §J D6 단계에서 검증 metric으로 활용.

fail 시 `OOD_TOO_EASY` 또는 `DATA_BAD_SPLIT` cause-id로 자동 변환.

### Checkpoint 5. Learnability gate
- `make_dataloaders(config)`가 train_id/val_id/test_id/ood_mass_low/ood_friction_low 5개 loader를 정상 반환
- batch shape `[B=16, T=8, D_x, D_a]` 일관성
- 1 batch forward through Encoder + BeliefMemory + GroupedDynamics + RewardHead + ValueHead → loss scalar 정상 (NaN/Inf 0)
- 1 epoch train (≤2분, train_id 50 ep × episode_len 80 ÷ batch 16 × horizon 8 ≈ 30 batch) 후 train_loss 감소

### Checkpoint 6. Repair-loop integration gate
1 epoch 학습 후 evaluator로 다음 metric을 모두 산출 가능:
- `id_nll` (val_id NLL)
- `train_nll`, `val_nll`, `val_train_nll_gap`
- `stagnant_epochs` (epoch ≤ 1이면 0)
- `kstep_nll_slope` (k=1..8)
- `ood_mass_nll`, `ood_friction_nll`, `ood_id_nll_diff`

`R3SmokeRunner(... patch=None ...)` → `RunnerOutput`이 위 키 모두 포함하는지 검증. `run_repair_loop` → `outputs/repair/{loop_id}/ledger.jsonl` 1줄 REQUIRED_KEYS 19개.

### Checkpoint 7. Storage gate
- 저장 경로 `data/fglc/PickCube-v1/<split>.h5`가 `.gitignore` `data/*` 패턴에 차단되는가 (`git status` clean 확인).
- HDF5 파일 크기 합 < 500 MB (smoke 첫 round 기대값).
- `manifest.json`, `dataset_stats.json`, `quality_report.json`, `split_config.yaml`만 commit 후보 — `data/fglc/PickCube-v1/manifest.json`을 `data/README.md`처럼 negation 패턴으로 commit 허용 검토(사용자 §K6).
- `*.h5` / `*.hdf5` 추가 ignore 패턴 명시 권고 (commit 사고 방지).

### Checkpoint 8. Reproducibility gate
manifest에 다음 모두 기록됨:
- `git_sha`
- `config_hash` (split_config.yaml + collector command + ManiSkill version의 sha256)
- task_id, maniskill_version, sapien_version, python_version, torch_version
- seed_pool 6 split
- collector command verbatim
- validation command verbatim
- rejection counts by reason

검증: 동일 `git_sha` + 동일 `config_hash`로 재실행 시 `manifest.json`이 (rejection 비결정성 제외) 동일 trajectory hash를 생성.

### Checkpoint 9. Novelty relevance gate
정성 + 정량 평가:
- ID와 OOD의 simple baseline 1-step NLL 차이가 측정 가능한가
- mismatch가 value head 출력(MC return prediction)에 영향을 주는가 (action-relevance proxy)
- 단순 noise (state에 σ 추가) vs 실제 dynamics 변화(mass·friction)를 구분 가능한가
- standardized residual `ρ_t = Σ_t^{-1/2}(z_{t+1}-μ_t)`의 ID vs OOD 분포 차이 (R4 falsification gate 학습 신호 측정)

이 checkpoint는 **본 단계에서 measurement만 수행하고 pass/fail 결정은 사용자에게 보고**. fail 시 OOD severity 상향 또는 다른 OOD axis 도입 권고.

### Checkpoint 10. Stop / Repair rule (실패 → repair 흐름)

각 checkpoint 실패는 종료가 아니라 cause-id로 변환:

| Checkpoint fail | cause-id | 처리 |
|---|---|---|
| Ckpt 0 (dependency) | (BLOCKED, repair 흐름 밖) | 사용자에게 설치 승인 요청 |
| Ckpt 1 (schema) | `IMPLEMENTATION_BUG_SUSPECTED` | collector schema probe 재실행 |
| Ckpt 2 (dynamics sanity) | `IMPLEMENTATION_BUG_SUSPECTED` 또는 `DATA_TOO_SMALL` | reject 한도 확인 → episode 수 증가 candidate |
| Ckpt 3 (split integrity) | `DATA_BAD_SPLIT` | `patch={"regenerate_split": True}` candidate 발화 |
| Ckpt 4 (OOD severity, gap < 0.05) | `OOD_TOO_EASY` | `patch={"ood_shift_scale": 2.0}` candidate (mass 1.5→2.0, friction 0.7→0.5) |
| Ckpt 4 (OOD severity, gap > 2.0 nat) | `OOD_TOO_HARD` | **신규 candidate 필요** — §J.D6에서 추가 |
| Ckpt 5 (learnability) | `IMPLEMENTATION_BUG_SUSPECTED` | dataloader/collator 재검증 |
| Ckpt 6 (repair metric) | `IMPLEMENTATION_BUG_SUSPECTED` | evaluate_model 확장 |
| Ckpt 7 (storage) | (BLOCKED) | .gitignore 추가 |
| Ckpt 8 (reproducibility) | `EVAL_NOISE_HIGH` 후보 또는 (BLOCKED) | seed 재현성 운영 정책 합의 |
| Ckpt 9 (novelty) | `OOD_TOO_EASY` / `DATA_BAD_SPLIT` | OOD axis 변경 / severity 상향 |

→ 모든 fail은 `outputs/repair/{loop_id}/ledger.jsonl` 라인으로 기록되고, `run_repair_loop`의 한 iter로 진입.

---

## H. 정제 및 저장 계획

### H.1 raw vs processed 분리
- **raw HDF5**: `data/fglc/PickCube-v1/raw/<split>.h5` — collector 직출력. inference + eval-only 모두 포함. **git 외부**.
- **processed cache** (선택): `data/fglc/PickCube-v1/proc/<split>.h5` — dataloader가 빠르게 읽는 인덱스 + 평탄화된 state 벡터. raw에서 결정적으로 재생성 가능.
- 본 단계 smoke에서는 **raw만 저장**(processed는 trainer 진입 시 in-memory).

### H.2 저장 포맷
- **권장**: HDF5 (`h5py` 사용, gzip level 4).
- 근거: episode → group, transition → dataset, attrs로 metadata. random access + 부분 로딩 효율.
- 대안: jsonl (작은 episode 한정) — 본 단계에서는 jsonl 부적합 (episode 수십 ep × episode_len 80 × D_x 30+ = 큰 텍스트).
- **결정**: 사용자 §K5 답변 받은 후 확정. PLAN default = HDF5.

### H.3 파일 명명 규약
```
data/fglc/PickCube-v1/raw/<split>_<git_sha[:7]>_<config_hash[:7]>.h5
```
예: `data/fglc/PickCube-v1/raw/train_id_a1b2c3d_f4e5d6c.h5`

manifest는 split별 파일 path를 명시.

### H.4 rejected episode 기록
별도 디렉터리 `data/fglc/PickCube-v1/quarantine/` (git 외부). 각 reject episode는 `<split>_<seed>_<reason>.json` 형식으로 메타데이터만 저장 (trajectory 자체는 디스크 낭비 방지로 저장 안 함, summary만).

### H.5 commit 대상
- `data/fglc/PickCube-v1/manifest.json` — 사용자 §K6 결정 후 commit 또는 ignore.
- `data/fglc/PickCube-v1/dataset_stats.json`
- `data/fglc/PickCube-v1/quality_report.json`
- `data/fglc/PickCube-v1/split_config.yaml`
- raw .h5 파일 = **commit 절대 금지**.

### H.6 .gitignore 보강 권고 (PLAN — manual edit, Codex 위임 ✗)
```
*.h5
*.hdf5
!data/fglc/**/manifest.json
!data/fglc/**/dataset_stats.json
!data/fglc/**/quality_report.json
!data/fglc/**/split_config.yaml
```

---

## I. 테스트 계획

### I.1 기존 185 tests 회귀 0 (precondition)
모든 sub-step의 merge 전 `pytest tests/ -q` 통과 필수.

### I.2 신규 unit/integration tests

| 파일 | 범위 |
|---|---|
| `tests/test_fglc_maniskill_dep_probe.py` | Dependency import 통과 (Ckpt 0). pytest mark skip if `mani-skill` 미설치 — 본 단계 진입 후 unskip. |
| `tests/test_fglc_maniskill_collector_probe.py` | 3 episode probe 가능. shape/seed reproducibility/OOD param API. |
| `tests/test_fglc_state_only_schema.py` | inference dict에 FORBIDDEN 0건, eval-only dict 분리. |
| `tests/test_fglc_split_integrity.py` | seed_pool 6 set 교집합 = ∅, hash 중복 0. |
| `tests/test_fglc_ood_severity.py` | mass=1.5 / friction=0.7에서 state_delta gap > δ_min. |
| `tests/test_fglc_no_garbage_data.py` | Ckpt 2 dynamics sanity 9 reject reason 합성 dataset에서 모두 reject 동작 확인. |
| `tests/test_fglc_maniskill_dataloader.py` | `make_dataloaders(config={..., dataset.type: maniskill_state_only})`가 5 split 반환. |
| `tests/test_fglc_r3_runner_maniskill.py` | R3SmokeRunner가 ManiSkill dataset에서 1 batch forward 가능 (model build smoke). |
| `tests/test_fglc_repair_metric_artifact.py` | metrics.json에 `id_nll`, `ood_mass_nll`, `ood_friction_nll`, `ood_id_nll_diff` 모두 존재. |

### I.3 회귀 보호
- `test_fglc_forbidden_field_sync.py` 통과 유지.
- 기존 26개 synthetic 관련 테스트 모두 통과 (`make_dataloaders`가 `dataset.type` 분기 후 synthetic 경로 회귀 0).
- repair 9 tests 통과 유지 (`taxonomy.py` enum / `candidates.py` table 변경 시 회귀 점검).

### I.4 CPU/GPU 분기
- ManiSkill collector는 default CPU 기반 SAPIEN renderer. GPU 가속 시 SAPIEN GPU plugin 필요(UNKNOWN, §L).
- 본 단계 smoke는 CPU 기반 collection 가정. R3 trainer만 GPU 사용.
- pytest는 CPU-only 환경에서도 통과 보장 (collector probe는 `@pytest.mark.skipif(not torch.cuda.is_available())` 대신 ManiSkill 설치 유무로 skip).

---

## J. Codex TASK 분해안

한 번에 위임하지 말 것. 다음 7 TASK로 분해, 각 TASK 사이 Claude의 **T3 implementation-risk-critic agent** 호출 + Gatekeeper 6 조건 검증.

### TASK D0 (Claude 직접, Codex 위임 ✗)
- 산출: `docs/STEP11A_DEPENDENCY_AUDIT.md` — 의존성 import 결과, ManiSkill task 등록 확인, OOD API 후보 결정.
- 산출: 사용자 §K1~§K6 답변 수집 + `docs/STEP11A_USER_DECISIONS.md` 기록.
- 산출: `.gitignore`에 `*.h5` 추가 + manifest negation 추가 (PLAN — manual edit).

### TASK D1 — ManiSkill task / OOD API probe script (Codex 위임)
```
FILES_ALLOWED:
  scripts/fglc/probe_maniskill.py
  tests/test_fglc_maniskill_dep_probe.py
FILES_FORBIDDEN:
  src/fglc/schemas/
  docs/idea/
  docs/ROADMAP/
  configs/fglc/smoke_4060.yaml      # D3에서만 수정
  scripts/run_codex_task.ps1
  .claude/, CLAUDE.md
ACCEPTANCE:
  - probe_maniskill.py가 PickCube-v1 등록/reset/step/obs_space 출력
  - OOD param API 후보 5개를 순차 시도, 동작하는 1개 채택, manifest 후보 파일 생성
  - 5 episode tiny probe 결과 stats를 stdout JSON으로 출력
  - test_fglc_maniskill_dep_probe.py 통과 (mani-skill 미설치 시 skip 자동)
```

### TASK D2 — Transition / Episode / Split / Manifest schema (Codex 위임)
```
FILES_ALLOWED:
  src/fglc/data/maniskill_schema.py    # Pydantic-like dataclass 또는 TypedDict
  src/fglc/data/validators.py          # 9 reject reason 검증 함수
  tests/test_fglc_state_only_schema.py
  tests/test_fglc_no_garbage_data.py
FILES_FORBIDDEN:
  src/fglc/schemas/visibility.py       # SSoT 불변
ACCEPTANCE:
  - inference dict + eval-only dict 분리 클래스
  - 9개 reject reason 함수 (all_state_static, all_action_zero, no_transition, reward_flat, episode_too_short, episode_short, no_done_signal, done_flood, numerical_invalid)
  - 합성 garbage dataset에서 9개 reason 모두 정확히 reject
```

### TASK D3 — Config schema 확장 + dataloader 분기 + state-only 일반화 (Codex 위임)
```
FILES_ALLOWED:
  configs/fglc/smoke_4060.yaml
  src/fglc/data/dataloader.py
  src/fglc/data/maniskill_dataset.py   # 신규
  tests/test_fglc_maniskill_dataloader.py
FILES_FORBIDDEN:
  src/fglc/data/state_only_dataset.py  # synthetic 회귀 보호: 기존 SyntheticToyDataset 시그니처 변경 금지
ACCEPTANCE:
  - smoke_4060.yaml에 dataset.type 분기 (synthetic_toy | maniskill_state_only)
  - dataloader.py가 dataset.type으로 SyntheticToyDataset / ManiSkillStateOnlyDataset 분기
  - ManiSkillStateOnlyDataset이 HDF5 path를 받아 lazy load
  - 기존 26 synthetic tests 회귀 0
  - 신규 dataloader test 통과
```

### TASK D4 — Collector script + per-episode validator (Codex 위임)
```
FILES_ALLOWED:
  scripts/fglc/collect_maniskill.py
  src/fglc/data/collector.py
  tests/test_fglc_maniskill_collector_probe.py
ACCEPTANCE:
  - --task PickCube-v1 --split <name> --seed-pool <ints> --ood-params <json> --output <h5>
  - per-episode 9 validator 통과한 것만 저장
  - rejected episode는 manifest에 reason 기록
  - probe 모드(--n-episodes 5 --no-save)에서 stdout JSON stats 출력
  - tiny probe 5 ep 테스트 통과 (mani-skill skip 가능)
```

### TASK D5 — Split builder + manifest/stats/quality_report writer (Codex 위임)
```
FILES_ALLOWED:
  scripts/fglc/build_split.py
  src/fglc/data/manifest.py
  src/fglc/data/stats.py
  tests/test_fglc_split_integrity.py
  tests/test_fglc_ood_severity.py
ACCEPTANCE:
  - 5 split 수집 후 manifest.json + dataset_stats.json + quality_report.json + split_config.yaml 생성
  - split integrity: seed_pool 6 set 교집합 = ∅, trajectory hash 중복 0
  - OOD severity: ID vs OOD state_delta gap > δ_min 검증
```

### TASK D6 — Repair candidate 보강 + R3 metric artifact 연결 (Codex 위임)
```
FILES_ALLOWED:
  src/fglc/repair/candidates.py
  src/fglc/repair/diagnose.py            # OOD_TOO_HARD / EVAL_NOISE_HIGH fire rule 추가
  src/fglc/evaluation/metrics.py         # ManiSkill metric 분기
  src/fglc/runners/r3_runner.py          # dataset.type 분기 활용
  tests/test_fglc_repair_metric_artifact.py
  tests/test_fglc_r3_runner_maniskill.py
ACCEPTANCE:
  - CANDIDATE_TABLE에 OOD_TOO_HARD 후보 추가: severity_down (mass 1.5→1.3, friction 0.7→0.85), expand_coverage (n_episodes ×2)
  - CANDIDATE_TABLE에 EVAL_NOISE_HIGH 후보 추가: more_seeds, longer_episode
  - diagnose.py에 OOD_TOO_HARD fire rule: ood_id_nll_diff > 2.0
  - r3_runner가 ManiSkill dataset에서도 정상 동작
  - 회귀: 기존 9 repair tests, 26 synthetic tests, 6 r3_runner integration tests 통과
```

### TASK D7 (사용자 승인 필요, Codex 위임 후 Claude verify)
실제 smoke 수집 실행:
```
.\.venv\Scripts\python.exe scripts\fglc\collect_maniskill.py `
  --task PickCube-v1 --split train_id ...
.\.venv\Scripts\python.exe scripts\fglc\collect_maniskill.py `
  --task PickCube-v1 --split val_id ...
... (5 splits 모두)
.\.venv\Scripts\python.exe scripts\fglc\build_split.py ...
.\.venv\Scripts\python.exe scripts\fglc\r3_smoke.py --phase R3 --config configs\fglc\smoke_4060.yaml --max-iter 1 --seed 42 --descriptor smoke_maniskill_pickcube
```
산출: `docs/STEP11_RESULT_REPORT.md` — 10 checkpoint 통과 여부 + repair loop iter_0 ledger 라인 + 다음 단계 권고 (R3 정식 gate 진입 가능성).

---

## K. 실제 실행 전 필요한 사용자 확인 (10항목)

execute 진입 전 다음을 사용자에게 명시적으로 받는다. PLAN default 권장값 포함.

### K1. ManiSkill 설치 진행 여부 + task 선택
- 옵션 A (권장): mani-skill 3.0.0b18 + sapien 3.0.0 설치 진행, PickCube-v1만 사용
- 옵션 B: 설치 보류, synthetic OOD 강화로 우회 (severity 변경, e.g., mass=3.0)
- 옵션 C: 다른 task (PushCube-v1 또는 LiftCube-v1)부터 시작

### K2. ManiSkill 의존성 핀 추가 PR 승인 여부
- `requirements.txt`에 `mani-skill==3.0.0b18`, `sapien==3.0.0`, `h5py==3.x.x` 추가 PR
- 사용자 명시 승인 필요 (취약 파일 dependency-related, `.claude/rules/behavioral_coding_rules.md §5`)

### K3. CPU vs GPU 수집
- 권장: CPU 수집 (SAPIEN renderer 기본). 학습만 GPU.
- GPU 수집은 SAPIEN GPU plugin 설치 + 검증 추가 부담 → DEFERRED 권장.

### K4. OOD axis 우선순위
- 권장 (smoke): mass=1.5, friction=0.7만 (severity low).
- 옵션 A: 위 + latency=3 step 추가.
- 옵션 B: 위 + noise_sigma=0.1 추가.
- 다른 axis는 DEFERRED.

### K5. Storage format
- 권장: HDF5 (h5py gzip4).
- 대안: jsonl (smoke 작은 규모) 또는 npz.
- 결정에 따라 D3/D4 TASK 구현 분기.

### K6. Storage location + commit 정책
- 권장: `data/fglc/PickCube-v1/raw/*.h5` = git 외부, `manifest.json` + `dataset_stats.json` + `quality_report.json` = commit.
- 대안: 모두 git 외부 (사용자 머신 로컬만).

### K7. Episode 예산 (4060 smoke 첫 round)
- 권장: train 50 + val 10 + test 10 + ood_mass 10 + ood_friction 10 = 90 ep.
- 대안 A: 절반 (45 ep).
- 대안 B: 권장의 2배 (180 ep) — `DATA_TOO_SMALL` 발화 시 자동 진입.

### K8. R3 real smoke 진입 시점
- 옵션 A (권장): 10 checkpoint 모두 PASS 후에만 r3_smoke.py 진입.
- 옵션 B: Ckpt 5(learnability)까지 PASS 시 진입, Ckpt 6 이후는 r3_smoke 결과로 검증.

### K9. OOD_TOO_HARD / EVAL_NOISE_HIGH repair candidate 보강 승인
- §J D6에서 신규 추가 — 사용자 승인 필요 (`docs/idea/FGLC_FAILURE_TAXONOMY.md` 정합성 확인).

### K10. Linux/WSL fallback 진입 조건
- 권장: Windows 네이티브에서 mani-skill+sapien 설치 성공 시 진행.
- 실패 시: WSL2 (Ubuntu 22.04) fallback — 추가 환경 설정 비용 사용자 합의 필요.

---

## L. BLOCKED / UNKNOWN

### BLOCKED (해결 책임 = Step 11 sub-task)
- `requirements.txt`에 `mani-skill`, `sapien`, `h5py`, `hydra-core`, `omegaconf` 미핀 → §K2 사용자 승인 후 추가.
- ManiSkill Windows 호환성 검증 0건 → §J D1에서 import probe + reset/step probe로 해소.
- OOD parameter 조작 API 5개 후보 중 동작 확인 0건 → §J D1 probe에서 해소.
- `*.h5` ignore 패턴 부재 → §J D0에서 manual edit.
- `data/fglc/` 디렉터리 자체 부재 → §J D5에서 생성.
- `CANDIDATE_TABLE`에 `OOD_TOO_HARD` 후보 부재 → §J D6에서 추가.
- `CANDIDATE_TABLE`에 `EVAL_NOISE_HIGH` 후보 부재 → §J D6에서 추가.
- `diagnose.py`에 `OOD_TOO_HARD` fire rule 부재 (taxonomy 임계값 2.0은 정의됐으나 발화 함수 없음) → §J D6.

### UNKNOWN (실측 또는 사용자 결정 후 확정)
- `D_x` 정확한 값 (PickCube state_dict concat 결과) — §J D1 probe로 확정.
- `D_a` 정확한 값 — §J D1 probe로 확정.
- `episode_len` 분포 (PickCube max_steps default UNKNOWN) — §J D1.
- ManiSkill v3 seed 결정성 수준 — §J D1 reproducibility probe.
- ManiSkill OOD param API의 정확한 시그니처 — §J D1.
- `h5py` Windows 호환성 (NTFS path UNICODE 문제 가능성) — §J D5.
- `train_id` 50 episode가 `OOD_TOO_EASY` 임계값(0.05) 초과 신호를 만들기에 충분한가 — §J D7 실측 후 결정.
- SAPIEN GPU plugin Windows 지원 (현재 권장 = CPU 수집이므로 본 단계 범위 밖).
- `ood_mass=1.5` / `ood_friction=0.7`이 PickCube에서 실제로 의미 있는 dynamics 변화인지 — §J D7 실측 후 결정.
- 본 단계 데이터로 R4 falsification gate 학습 신호가 충분한지 (`ρ_t` 분포 차이) — 본 단계 범위 밖, R4 phase에서 검증.

---

## M. Step 완료 기준

본 단계는 **R3.passed 생성과 무관**. 다음 9개 모두 충족 시 완료.

1. **Phase A.0 dependency PASS** — mani-skill, sapien, h5py import 성공 + 버전 manifest 기록.
2. **Phase A.1 task probe PASS** — PickCube-v1 등록 + state_dict obs reset/step 안정.
3. **Phase A.OOD probe PASS** — OOD param API 1개 이상 동작 확인.
4. **Phase B tiny probe PASS** — 5 episode 수집(저장 ✗), schema/shape/seed 검증 통과.
5. **Phase C smoke 수집 PASS** — 5 split 90 episode 수집, reject episode reason 모두 manifest 기록.
6. **Phase D validation PASS** — 10 checkpoint 통과 (특히 Ckpt 3 split integrity, Ckpt 4 OOD severity gap > 0.05, Ckpt 5 learnability, Ckpt 6 repair metric artifact).
7. **`data/fglc/PickCube-v1/manifest.json` 생성** — 9 필수 메타 모두 기록.
8. **R3 base WM 1 batch forward 성공** — `make_dataloaders` ManiSkill 분기 + Encoder/Belief/Dynamics smoke.
9. **`docs/STEP11_RESULT_REPORT.md` 작성** — 10 checkpoint pass/fail + repair loop iter_0 ledger 라인 + 다음 단계 권고 (R3 정식 gate 진입 가능성, OOD severity 조정 필요 여부).

추가 검증:
- 기존 185 tests 회귀 0 (`pytest tests/ -q` PASS).
- 신규 9개 test 모두 PASS.
- `git status` clean (raw .h5 미커밋, manifest만 staged).

**비완료 조건 (Step 11 종료 금지)**:
- `R3.passed` 생성됨.
- raw HDF5가 git에 staged됨.
- 10 checkpoint 중 1개라도 fail 상태 (repair candidate 진입 없이 종료).
- 사용자 §K9 승인 없이 `CANDIDATE_TABLE` 변경됨.
- garbage episode가 reject 없이 저장됨.

---

## N. 절대 하지 말 것 (사용자 명시 금지)

- garbage 데이터를 "일단 저장하고 학습"하지 않는다.
- validation 없이 학습 진입하지 않는다.
- split leakage 검증을 생략하지 않는다.
- OOD가 ID와 같은지 확인 없이 다음 단계 진입하지 않는다.
- 너무 쉬운 OOD를 "novelty 검증 데이터"라고 주장하지 않는다.
- 너무 어려운 OOD 실패를 "모델 문제"로 단정하지 않는다.
- `R3.passed`를 임의 생성하지 않는다.
- 대용량 raw data를 git에 commit하지 않는다.
- RGB-D / DROID / BridgeData / baseline grid로 확장하지 않는다.
- ManiSkill OOD API를 추측해서 그대로 collector에 박지 않는다 (반드시 §J D1 probe로 확정 후).
- `src/fglc/schemas/visibility.py` 수정 금지 (`.claude/rules/behavioral_coding_rules.md §5` Fragile File).
- `docs/idea/`, `docs/ROADMAP/` 임의 수정 금지.
- smoke 실패를 최종 결론으로 사용하지 않는다 — 항상 repair loop 입력으로 변환.
- FGLC 핵심 주장(falsification / standardized mismatch / causal attention) 성패 판단 금지 (본 단계는 데이터 계약 단계, R4 이후 검증).

---

## O. Execute 진입 시 수행할 최소 작업 순서

ExitPlanMode 후 사용자 승인되면 다음 순서로 진행 (각 단계에 T3 implementation-risk-critic agent 호출 + Gatekeeper 6 조건):

### Order 1 — TASK D0 (Claude 직접)
1. 사용자 §K1~§K10 답변 수집 → `docs/STEP11A_USER_DECISIONS.md` 작성.
2. dependency import probe (Ckpt 0) 직접 실행 → `docs/STEP11A_DEPENDENCY_AUDIT.md` 작성.
3. (선택) `.gitignore`에 `*.h5` 추가 + manifest negation 추가.
4. `requirements.txt` 핀 추가 PR (사용자 §K2 승인 후).

### Order 2 — TASK D1 (Codex 위임)
5. `.agent_tasks/codex_queue/TASK_D1_maniskill_probe.md` 작성.
6. `scripts/run_codex_task.ps1 -Mode run -TaskName TASK_D1 -BypassSandbox` 실행.
7. T3 audit + fglc-code-reviewer agent 호출, PASS 확인.
8. probe 결과로 `D_x`, `D_a`, episode_len, OOD API 채택 결정.

### Order 3 — TASK D2 (Codex 위임)
9. schema + 9 validator 구현.
10. 합성 garbage dataset에서 9 reject reason 검증.

### Order 4 — TASK D3 (Codex 위임)
11. dataloader.py 분기 + ManiSkillStateOnlyDataset.
12. 기존 26 synthetic tests 회귀 0 확인.

### Order 5 — TASK D4 (Codex 위임)
13. collector.py + collect_maniskill.py.
14. 5 episode tiny probe 통과.

### Order 6 — TASK D5 (Codex 위임)
15. build_split.py + manifest writer.
16. split integrity + OOD severity 검증.

### Order 7 — TASK D6 (Codex 위임)
17. CANDIDATE_TABLE에 OOD_TOO_HARD / EVAL_NOISE_HIGH 추가.
18. diagnose.py에 OOD_TOO_HARD fire rule 추가.
19. r3_runner ManiSkill 분기.

### Order 8 — TASK D7 (사용자 승인 후 Claude verify)
20. 실제 5 split 수집 실행.
21. 10 checkpoint validation 실행.
22. r3_smoke.py 1-iter 실행 (`--config configs/fglc/smoke_4060.yaml --descriptor smoke_maniskill_pickcube`).
23. `docs/STEP11_RESULT_REPORT.md` 작성.

---

## P. 검증 (Verification)

본 PLAN이 실제로 실행 가능한지 확인할 명령:

### P.1 현재 185 tests 재확인 (precondition)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q
```
기대: `185 passed`.

### P.2 의존성 import 가능 여부 (BLOCKED 해소 시점)
```powershell
.\.venv\Scripts\python.exe -c "import mani_skill, sapien, h5py, gymnasium; print('OK', mani_skill.__version__, sapien.__version__, h5py.__version__, gymnasium.__version__)"
```

### P.3 TASK D1 probe 결과 검증
```powershell
.\.venv\Scripts\python.exe scripts\fglc\probe_maniskill.py --task PickCube-v1 --n-probe 5 --output-json -
```
기대: stdout JSON에 `D_x`, `D_a`, `episode_len_dist`, `ood_api_resolved` 키.

### P.4 schema 분기 회귀 검증
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_fglc_dataset_state_only.py tests/test_fglc_trainer_r3_smoke.py tests/test_fglc_r3_runner_integration.py -q
```
기대: 18 passed (synthetic 회귀 0).

### P.5 5 split 수집 후 manifest 검증
```powershell
.\.venv\Scripts\python.exe -c "import json; m = json.load(open('data/fglc/PickCube-v1/manifest.json')); print(set(m['splits'].keys()))"
```
기대: `{'train_id', 'val_id', 'test_id', 'ood_mass_low', 'ood_friction_low'}`.

### P.6 r3_smoke 1-iter ManiSkill 실행
```powershell
.\.venv\Scripts\python.exe scripts\fglc\r3_smoke.py `
  --phase R3 --config configs\fglc\smoke_4060.yaml `
  --seed 42 --descriptor smoke_maniskill_pickcube `
  --max-iter 1 --max-wall-clock-minutes 60 `
  --output-root outputs\repair
```
기대: `outputs/repair/loop_*/ledger.jsonl` 1줄, `phase="R3"`, `metrics_after`에 `id_nll`, `ood_mass_nll`, `ood_friction_nll`, `ood_id_nll_diff` 모두 존재.

### P.7 OOD severity 측정 확인
```powershell
.\.venv\Scripts\python.exe -c "import json; r = json.load(open('data/fglc/PickCube-v1/quality_report.json')); print(r['checkpoint_4_ood_sev'])"
```
기대: `PASS`. fail 시 manifest의 OOD severity gap 수치 확인 후 §K4 사용자 결정으로 진입.

---

## Q. 핵심 파일 reference

### PLAN 입력으로 직접 인용된 파일
- `CLAUDE.md` (Invariant Preservation, Fragile Files, Codex Orchestration)
- `.claude/rules/behavioral_coding_rules.md §5` (Fragile File Invariants)
- `.claude/rules/codex_orchestration_rules.md` (TASK 10 헤더, Gatekeeper 6 조건)
- `docs/ROADMAP/00_ROADMAP_OVERVIEW.md` (R0~R16 위치)
- `docs/ROADMAP/03_PHASE_R2_DATA_PIPELINE.md` (OOD_CONFIGS L22-29, gate L40-42)
- `docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md` (정식 gate L35-42)
- `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md` (smoke 예산 L29-34, gate threshold L82-96, OOM fallback L122-130)
- `docs/idea/18_DATA_BENCHMARKS.md` (transition schema L15-35, OOD axes L41-49, 데이터 규칙 L62-69)
- `docs/idea/FGLC_FAILURE_TAXONOMY.md` (20 cause-id, threshold)
- `docs/idea/04_BASE_WORLD_MODEL.md`, `docs/idea/10_LOSS_DESIGN.md`, `docs/idea/12_TRAINING_STAGES.md`, `docs/idea/21_METRICS.md`
- `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` (D.1, D.3, D.5)
- `docs/EXPERIMENT_LEDGER_SCHEMA.md` (REQUIRED_KEYS 19)
- `docs/STEP10_RESULT_REPORT.md` (synthetic OOD_TOO_EASY 결과 = 0.0065)
- `src/fglc/schemas/visibility.py:18-31` (FORBIDDEN_AGENT_FIELDS 12)
- `src/fglc/data/dataloader.py:34-91` (`make_dataloaders` synthetic만 분기, ManiSkill 추가 필요)
- `src/fglc/data/state_only_dataset.py` (SyntheticToyDataset, 회귀 보호 대상)
- `src/fglc/repair/taxonomy.py:12-34` (FailureCauseId 20개), `:202-235` (DETECTION_THRESHOLDS)
- `src/fglc/repair/diagnose.py:10-31` (CANONICAL_METRIC_KEYS 17 + ARTIFACT_KEYS 3), `:119-140` (diagnose fn — OOD_TOO_HARD fire 부재)
- `src/fglc/repair/candidates.py:36-46` (DATA_TOO_SMALL), `:116-138` (OOD_TOO_EASY / DATA_BAD_SPLIT — OOD_TOO_HARD/EVAL_NOISE_HIGH 부재)
- `src/fglc/repair/orchestrator.py:67-87` (RunnerOutput + RepairRunner Protocol)
- `src/fglc/runners/r3_runner.py:50-144` (R3SmokeRunner)
- `scripts/fglc/repair_loop.py`, `scripts/fglc/r3_smoke.py`
- `configs/fglc/smoke_4060.yaml` (synthetic 전용 schema, ManiSkill 분기 필요)
- `pyproject.toml:11-28` (core deps + maniskill/rl/causal/rlds extras)
- `requirements.txt:35` (gymnasium==1.2.3 만 핀; mani-skill/sapien/h5py 미핀)
- `.gitignore:30-34` (data/* 차단), `:98-99` (phase_gates negation), `:140` (`!outputs/repair/.gitkeep`)
- `plans/PHASE_PROGRESS.md` (R0/R1/R2 PASS, R3 PENDING)

### 본 PLAN이 생성될 파일 (execute 후)
- `docs/STEP11A_DEPENDENCY_AUDIT.md`
- `docs/STEP11A_USER_DECISIONS.md`
- `docs/STEP11_RESULT_REPORT.md`
- `data/fglc/PickCube-v1/manifest.json` + `dataset_stats.json` + `quality_report.json` + `split_config.yaml`
- `src/fglc/data/maniskill_schema.py`, `validators.py`, `maniskill_dataset.py`, `collector.py`, `manifest.py`, `stats.py`
- `scripts/fglc/probe_maniskill.py`, `collect_maniskill.py`, `build_split.py`
- 9개 tests/test_fglc_*.py
