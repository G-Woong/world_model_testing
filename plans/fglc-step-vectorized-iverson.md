# Step 11-D7 — ManiSkill PickCube-v1 state-only 실제 데이터 수집 PLAN

> **Status**: PLAN ONLY — 수집 미실행. `outputs/phase_gates/R3.passed` 생성 금지.
> **Branch**: `memory-redesign-2026-05-16`
> **Date**: 2026-05-23

---

## Context

Step 11 D0~D6은 모두 PASS — ManiSkill 의존성, PickCube-v1 state-only probe(`D_x=42, D_a=8`), OOD mass/friction API 확인, `collector.py / collect_maniskill.py / validators.py(9 reject reason) / manifest.py / stats.py / build_split.py / dataloader maniskill 분기 / R3 runner maniskill branch` 모두 구현·테스트 완료, **279 tests passed** (`docs/STEP11_RESULT_REPORT.md:18-47`).

D7만 PENDING. D7의 목적은 단순한 "episode 수집 성공"이 아니라, **FGLC novelty(`wrong-dynamics-hypothesis persistence → falsification → latent correction → planning recovery`)를 검증할 수 있는 고품질 ID/OOD 데이터**를 episode-level garbage gate, split-level integrity gate, OOD severity gate, novelty relevance gate 4중 검증으로 확보하는 것이다.

본 PLAN은 사용자 결정 3건을 반영한다:
1. **수집 단계 전략**: Probe → Pilot 180ep → Scaled 450ep (3단계 strict)
2. **friction severity**: 코드 default `joint_friction=5.0` 유지 + quality_report에 SSoT 단위 분리 명시
3. **GAP 처리**: PLAN과 함께 collector 패치 Codex task 1건 **선행**(D7 수집은 패치 후)

---

## A. 현재 구현 상태 요약

| 항목 | 상태 | 근거 |
|---|---|---|
| `D_x=42, D_a=8` 확정 | PASS | `src/fglc/data/maniskill_schema.py:3`, `configs/fglc/smoke_maniskill_pickcube.yaml:8-9` |
| Validator 9 reject reason | PASS | `src/fglc/data/validators.py:20-29` (ALL_STATE_STATIC, ALL_ACTION_ZERO, NO_TRANSITION, REWARD_FLAT, EPISODE_TOO_SHORT, EPISODE_SHORT, NO_DONE_SIGNAL, DONE_FLOOD, NUMERICAL_INVALID) |
| Collector / save_episodes_h5 | PASS | `src/fglc/data/collector.py:21-228`, gzip4 압축, eval_only attrs 별도 |
| Manifest/stats/quality_report | PASS | `src/fglc/data/manifest.py:128-209` (`build_dataset_stats`, `verify_split_integrity`, `verify_ood_severity`) |
| Dataset/DataLoader 분기 | PASS | `src/fglc/data/maniskill_dataset.py:67-69`, `src/fglc/data/dataloader.py:108-124` |
| `collect_maniskill.py` 5 split CLI | PASS | `scripts/fglc/collect_maniskill.py:34-91` (`train_id, val_id, test_id, ood_mass_low, ood_friction_low`) |
| `build_split.py` | PASS | `scripts/fglc/build_split.py:44-186` (manifest/dataset_stats/quality_report/split_config 4종 산출) |
| `r3_smoke.py` 1-iter 가능 | PASS (mock fixture) | `tests/test_fglc_r3_runner_maniskill.py:20-177` |
| 12 forbidden field 차단 | PASS | `src/fglc/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS`, `tests/test_fglc_forbidden_field_sync.py` |
| `.gitignore` raw HDF5 차단 | PASS | `.gitignore:30,36-42` (`data/*` + `*.h5/*.hdf5`) |
| **GAP** `--probe/--pilot/--scaled` 명시 플래그 | **MISSING** | `collect_maniskill.py:79-91` — `--no-save`만 존재 |
| **GAP** quarantine/temp 분리 경로 | **MISSING** | reject episode가 카운트만 누적 |
| **GAP** trajectory hash duplicate 검사 | **MISSING** | `tests/test_fglc_split_integrity.py`에 검사 없음, seed-pool disjoint만 검증 |
| **GAP** DATA_TOO_SMALL 직접 episode-count trigger | **MISSING** | `diagnose.py:38-48`는 `id_nll>0.5 AND stagnant_epochs>=10`에 종속 |
| **GAP** `eval_ci95_over_effect_size`가 CANONICAL_METRIC_KEYS 미포함 | **MISSING** | `diagnose.py:10-31` vs `:117-123` 불일치 |

---

## B. 실제 수집 목표

| 목표 | 수치 / 조건 |
|---|---|
| 5-split 데이터셋 확보 | `train_id / val_id / test_id / ood_mass_low(mass=1.5) / ood_friction_low(joint_friction=5.0)` |
| Pilot 단계 episode budget | 180ep (train 100 + val 20 + test 20 + ood_mass 20 + ood_friction 20) |
| Scaled 단계 episode budget | 450ep (train 250 + val 50 + test 50 + ood_mass 50 + ood_friction 50) |
| L-확장 트리거 | r3_smoke에서 `DATA_TOO_SMALL` 또는 `EVAL_NOISE_HIGH` 발화 시 900ep |
| 4축 quality gate | (1) episode-level garbage, (2) split integrity, (3) OOD severity, (4) novelty relevance — 모두 PASS 또는 CONDITIONAL_PASS |
| R3 smoke 1-iter ledger | `outputs/repair/smoke_maniskill_pickcube/iter_1/metrics.json` 생성, ID NLL ≤ 0.5 nat, OOD-ID gap ≥ 0.05 nat (4060 완화) |
| `R2.passed` / `R3.passed` | **둘 다 미생성** — 본 D7은 R3 smoke까지만, gate sentinel은 별도 round |

---

## C. 자원 계산 및 episode 수 확장안

### bytes/transition 추정 (D_x=42, D_a=8 기준)

```
state    float32 (T, 42)  → 42 × 4 = 168 B/step
action   float32 (T,  8)  →  8 × 4 =  32 B/step
reward   float32 (T,)     →           4 B/step
done     bool    (T,)     →           1 B/step
raw subtotal             ≈ 205 B/transition
gzip4 compression (~25-35%) ≈ 55-70 B/transition (적용)
```

eval_only metadata는 attrs로 별도(episode당 ~12 키 × ~16 B ≈ 192 B), HDF5 group overhead ~500 B/episode.

### avg T 추정 (probe로 실측 예정)

ManiSkill `PickCube-v1`의 `max_episode_steps=50`이 default. Success early termination 가능. **probe Stage 0에서 mean_episode_len을 실측**하고, 보수 추정 `T_avg=70` (실패 episode 포함 시 50 cap 초과 가능성 고려).

### bytes/episode

```
T=70 × 205 B raw     ≈ 14.4 KB/ep raw
                     ≈   4.3 KB/ep gzip4
+ attrs/overhead     ≈ 700 B/ep
                     ≈ 5.0 KB/ep total (gzip4)
```

### 데이터셋 크기 예측

| Option | Total ep | Raw size | Compressed size |
|---|---|---|---|
| Pilot S | 180 | 2.6 MB | 0.9 MB |
| Scaled M | 450 | 6.5 MB | 2.3 MB |
| Scaled L | 900 | 12.9 MB | 4.6 MB |

→ **디스크 부담 무시 가능**(< 5 MB). 8 GB VRAM과도 무관.

### 수집 wall-clock 예측

ManiSkill `PickCube-v1` state-only CPU 추정 ~30~50ms/step:
- 70 steps × 40ms = **2.8 s/ep**
- 180 ep ≈ **8.4분**, 450 ep ≈ **21분**, 900 ep ≈ **42분**

→ collector `--max-wall-minutes 20.0` default(`collect_maniskill.py:90`)로 split별 30~50ep 묶음 안전. Pilot/Scaled 전체는 `--max-wall-minutes 45` 또는 split별 호출로 분산.

### 학습 시간 예측 (4060 8GB)

`docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md:42-78` 기준 `K=6, d=32, h_dim=128, T=8, batch=16`, R3 smoke `per-iter ≤30분, max-iter=5` → 합 ≤2.5h.

### VRAM 예측

`docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md:54-62`: `batch(16) × T(8) × K(6) × d(32) ≈ 100 KB/sample`, **~200 MB total** (8 GB의 ~3%).

### 결론

- Pilot 180 → Scaled 450이 자원적으로 무리 없음.
- L=900 확장도 디스크/시간/VRAM 모두 여유. 발화 트리거만 확보되면 즉시 가능.

---

## D. split별 수집량 후보 (Pilot 180 / Scaled 450 확정, L=900 옵션)

| Split | Pilot (확정) | Scaled (확정) | L (옵션) |
|---|---|---|---|
| `train_id` (seed 42-91) | 100 | 250 | 500 |
| `val_id` (seed 200-209) | 20 | 50 | 100 |
| `test_id` (seed 300-309) | 20 | 50 | 100 |
| `ood_mass_low` (seed 500-509, mass=1.5) | 20 | 50 | 100 |
| `ood_friction_low` (seed 600-609, joint_friction=5.0) | 20 | 50 | 100 |
| **Total** | **180** | **450** | **900** |

> Seed pool은 `collect_maniskill.py:34-75 SPLIT_DEFAULTS`에서 split마다 분리됨 (`train_id [42,92), val_id [200,210), test_id [300,310), ood_mass_low [500,510), ood_friction_low [600,610)`). Pilot 100ep는 train_id pool `[42,92)`의 50 seed를 retry해 100ep까지 채움(`max_retry=3`). Scaled 250ep는 pool 확장 필요 — Codex 패치 A에 `seed_pool` 확장 옵션 포함.

---

## E. OOD axis / severity 설계

| Axis | 값 | 단위 | SSoT 정합성 | 비고 |
|---|---|---|---|---|
| mass | 1.5 | object_mass 배수 | OK (`docs/idea/18_DATA_BENCHMARKS.md:44`, mass ∈ {0.5, 1.5, 2.0}) | sweep은 R4+로 미룸 |
| friction | 5.0 | joint dry friction | **단위 분리 명시 필요** — SSoT(`:44`)는 μ_kinetic ∈ {0.3, 0.7, 1.5}. 코드는 joint API. `quality_report.json`에 `friction_api: joint_dry_friction, ssot_unit: mu_kinetic, mapping: DEFERRED` 기록 | 4060 probe(2026-05-23)에서 L2 diff ~0.042/step 확인 |
| latency | DEFERRED | step delay | R4+ 단계 | `04_PHASE_R3 gate`에 미요구 |
| noise | DEFERRED | obs σ | R4+ (standardized mismatch/calibration용 2차) | conformal calibration에서 검토 |
| action_gain | DEFERRED | gain factor | R4+ | — |

**근거**: `docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md:35-42`가 R3 gate에서 mass/friction만 요구. latency/noise/gain은 R4+ (falsification gate) 단계 데이터로 분리.

---

## F. Episode-level garbage 차단 gate (수집 중 강제)

`validate_episode()` (`src/fglc/data/validators.py:32-89`)가 매 episode마다 호출되어 9 reject reason 중 하나라도 발화하면 저장 금지. Pilot/Scaled에서 추가로 다음 layer 강제:

1. **NaN/Inf**: `NUMERICAL_INVALID` 자동 차단 (`validators.py:60-64`).
2. **no_done_signal**: `dones[-1]=True` 강제(`collector.py:148-149`) + `NO_DONE_SIGNAL`(`validators.py:84-85`).
3. **constant_state**: `ALL_STATE_STATIC` (`std.max() < 1e-4`, `:67-68`).
4. **zero_action**: `ALL_ACTION_ZERO` (`abs().max() < 1e-3`, `:71-72`).
5. **abnormal_length**: `EPISODE_TOO_SHORT (T<2)` + `EPISODE_SHORT (T<10)` (`:51-56`).
6. **NO_TRANSITION** (mean state-diff norm < 1e-4, `:74-77`).
7. **REWARD_FLAT** (`std(rewards) < 1e-6`, `:80-81`).
8. **DONE_FLOOD** (`all(dones[:-1])`, `:88-89`).
9. **duplicate trajectory**: 신규 — Codex 패치 A에서 `hash(state.tobytes())` 기반 검사 추가 → `EPISODE_DUPLICATE` reject reason 확장.
10. **success rate sanity**: split별 success rate가 train_id에서 ≥30% (Pilot), ≥40% (Scaled)이 아니면 quality_report에 `WARN_LOW_SUCCESS` 기록 (CONDITIONAL_PASS).

`CollectionStats.rejection_counts` (`collector.py:36-42`) 누적 후 `quality_report.json`에 reject reason 분포 그대로 직렬화.

---

## G. Split-level integrity gate (수집 후 강제)

1. **Seed pool disjoint**: `verify_split_integrity()` (`manifest.py:178-196`) — 이미 PASS 기대.
2. **Trajectory hash duplicate**: Codex 패치 A에서 추가. `build_split.py` 안에서 episode별 `state.tobytes()` SHA1 해시 모아 split-내 중복 0, split-간 중복 0 검증.
3. **Regime contamination**: ood_mass / ood_friction split의 eval_only attrs `regime_id`가 ID split과 disjoint한 정수 집합인지 검증. (코드 추가: build_split.py post-check)
4. **D_x/D_a invariance**: 모든 split의 `dataset_stats.json::D_x==42, D_a==8` 검증 (`tests/test_fglc_split_integrity.py:106-149`).
5. **Forbidden field audit**: `_HorizonDataset` (`dataloader.py:25-34`) 와 `assert_no_forbidden_fields` (`maniskill_dataset.py:61`) 가 12 forbidden 필드 부재 확인 — `tests/test_fglc_forbidden_field_sync.py` green 유지.

---

## H. OOD severity / novelty relevance gate

### OOD severity (`verify_ood_severity`, `manifest.py:199-209`)

- **임계**: `delta_min=0.01` on `state_delta_norm_mean` (split간 절대 차).
- **PASS**: `|train_id.state_delta_norm_mean - ood.state_delta_norm_mean| ≥ 0.01` AND `≤ 0.5` (간단 sanity).
- **OOD_TOO_EASY**: gap < 0.01 → `diagnose.py:51-61` AUROC<0.7과 연계, repair `OOD_TOO_EASY_shift_strength_2x`(`candidates.py:117-126`) 발화.
- **OOD_TOO_HARD**: gap > 0.5 또는 R3 smoke에서 `ood_id_nll_diff > 2.0` → `candidates.py:141-170` (mass 1.5→1.3, friction 5.0→3.0, expand_coverage→200).

### Novelty relevance (수동 + Agent D)

다음 6개 질문에 모두 응답 가능해야 함:
1. mass/friction shift가 단순 noise가 아닌 **physical dynamics hypothesis shift**인가?
2. base WM 1-step prediction이 ID에서는 적합, OOD에서는 mismatch가 누적되는가?
3. falsification gate(`β_t`)가 residual 차이를 감지할 가능성이 보이는가?
4. latent correction(`δ_t^k`)이 필요한 group-wise 구조 차이가 관찰되는가?
5. mass/friction shift가 action/value에 영향을 주는가(success rate 변동, episode length 변동)?
6. wrong-dynamics-hypothesis persistence 구간이 multi-step에 걸쳐 존재하는가? (`04_BASE_WORLD_MODEL.md:46-49` 근거)

---

## I. 팀 에이전트 구성과 산출물

각 agent는 **수집 전 plan review + 수집 후 실측 review** 2회 보고. 각 보고서에 PASS/FAIL/CONDITIONAL_PASS 명시.

| Agent | 역할 | 보고 경로 (사용자 명세 + 프로젝트 컨벤션) | PASS 조건 |
|---|---|---|---|
| **A. data-quality-gatekeeper** | episode 단위 garbage 차단, 9 reject reason 분포 분석 | `reports/data_quality_agent_report.md` + `docs/orchestration/agent_reports/2026-05/data_quality_d7_R0.md` | train_id accept rate ≥70%, reject 사유 모두 설명 가능 |
| **B. split-leakage-auditor** | seed overlap / hash duplicate / regime contamination | `reports/split_leakage_agent_report.md` + `docs/orchestration/agent_reports/2026-05/split_leakage_d7_R0.md` | seed overlap=0, hash duplicate=0, regime contamination=0 |
| **C. ood-severity-critic** | OOD severity gap 측정, OOD_TOO_EASY / TOO_HARD 발화 판정 | `reports/ood_severity_agent_report.md` + `docs/orchestration/agent_reports/2026-05/ood_severity_d7_R0.md` | gap ∈ [0.01, 0.5] (state_delta_norm), 또는 repair candidate 명시 |
| **D. novelty-relevance-critic** | FGLC novelty 관련 6개 질문 답변 | `reports/novelty_relevance_agent_report.md` + `docs/orchestration/agent_reports/2026-05/novelty_relevance_d7_R0.md` | PASS / CONDITIONAL_PASS / FAIL 판정 + 근거 |
| **E. training-readiness-auditor** | R3 runner 실제 데이터 1-iter forward + 1 epoch tiny train | `reports/training_readiness_agent_report.md` + `docs/orchestration/agent_reports/2026-05/training_readiness_d7_R0.md` | `outputs/repair/.../iter_1/metrics.json`, `ledger.jsonl`, `iter_1/` artifact 생성 확인 |
| **F. resource-budget-auditor** | bytes/disk/time/VRAM 추정, 180/450/900 비교 | `reports/resource_budget_agent_report.md` + `docs/orchestration/agent_reports/2026-05/resource_budget_d7_R0.md` | recommended episode count + OOM fallback 순서 명시 |

> Agent 호출 시점:
> - **Pre-collection** (Probe 직후): A·B·F (계획 검증)
> - **Post-Pilot 180** (수집 후): A·B·C·D·E·F (실측)
> - **Post-Scaled 450** (수집 후): A·B·C·D·E·F (실측) + area-chair-synthesis-agent 1회 통합

---

## J. 수집 전/중/후 체크포인트

### J.1 수집 전 (Pre-flight)

1. `git status` → 의도치 않은 staged 변경 없음 확인
2. `pytest -q tests/test_fglc_no_garbage_data.py tests/test_fglc_split_integrity.py tests/test_fglc_ood_severity.py tests/test_fglc_r3_runner_maniskill.py tests/test_fglc_forbidden_field_sync.py` → 5개 핵심 데이터 테스트 green
3. `data/fglc/PickCube-v1/raw/`가 `.gitignore`로 차단되는지 재확인 (`.gitignore:30,36-42`)
4. temp/probe/quarantine/final 디렉터리 분리 — **Codex 패치 A 적용 후** 가능:
   - `data/fglc/PickCube-v1/_probe/` (--no-save 기준)
   - `data/fglc/PickCube-v1/_quarantine/` (reject 격리)
   - `data/fglc/PickCube-v1/raw/` (final HDF5)
5. seed list 생성: SPLIT_DEFAULTS(`collect_maniskill.py:34-75`) 그대로 사용, Scaled는 pool 확장.
6. PickCube-v1 reset/step probe(`--no-save --n-episodes 3`) 확인 — D6에서 이미 PASS, 재현용 1회 더 권장.
7. OOD mass/friction API 적용 확인: `ood_mass_low`에서 `set_object_mass(1.5)`, `ood_friction_low`에서 `set_joint_friction(5.0)` 호출 로그 확인.
8. 디스크 예산 확인: `data/fglc/`에 ≥ 50 MB 여유.
9. dry-run 수집 1ep: `python scripts/fglc/collect_maniskill.py --split train_id --n-episodes 1 --no-save --verbose`.

### J.2 수집 중 (per-split)

- `validate_episode()` 매 episode 호출.
- reject → `_quarantine/<split>/<seed>_<reason>.h5`로 격리 저장 (Codex 패치 A로 추가).
- `CollectionStats.rejection_counts`를 실시간 stdout (`--verbose`).
- split별 `accepted, rejected, transitions, wall_clock` 출력.
- `--max-wall-minutes 20.0` 초과 시 abort, partial save 차단.
- `done`/`truncated` consistency 자동 검증 (`collector.py:148-149`).

### J.3 수집 후 (build/audit)

1. `python scripts/fglc/build_split.py --data-root data/fglc/PickCube-v1/raw --output-dir data/fglc/PickCube-v1` 실행.
2. 산출물 4종 생성 확인:
   - `data/fglc/PickCube-v1/manifest.json`
   - `data/fglc/PickCube-v1/dataset_stats.json`
   - `data/fglc/PickCube-v1/quality_report.json`
   - `data/fglc/PickCube-v1/split_config.yaml`
3. `verify_split_integrity()` PASS (seed disjoint).
4. **Trajectory hash audit**(패치 A 후 build_split 내장 또는 별도 스크립트) duplicate=0.
5. `verify_ood_severity()` PASS / CONDITIONAL_PASS / FAIL.
6. Agent A·B·C·D·E·F 보고.
7. raw HDF5 git staged 없음 확인 (`git status -s data/fglc/PickCube-v1/raw/` → 빈 출력).
8. `manifest.json / dataset_stats.json / quality_report.json / split_config.yaml`만 staging 가능 검토 (사용자 승인 후 commit).

---

## K. 저장 / manifest / report 구조

```
data/fglc/PickCube-v1/
├── _probe/                          (gitignore, --no-save 흔적 없음)
├── _quarantine/                     (gitignore, reject 격리, 패치 A 후)
│   ├── train_id/
│   │   └── seed42_ALL_STATE_STATIC.h5
│   └── ...
├── raw/                             (gitignore, *.h5)
│   ├── train_id.h5
│   ├── val_id.h5
│   ├── test_id.h5
│   ├── ood_mass_low.h5
│   └── ood_friction_low.h5
├── manifest.json                    (negation, commit 가능)
├── dataset_stats.json               (negation, commit 가능)
├── quality_report.json              (negation, commit 가능)
└── split_config.yaml                (negation, commit 가능)

reports/                             (신규, gitignore 미지정 — PLAN에 추가 권장)
├── data_quality_agent_report.md
├── split_leakage_agent_report.md
├── ood_severity_agent_report.md
├── novelty_relevance_agent_report.md
├── training_readiness_agent_report.md
└── resource_budget_agent_report.md

docs/orchestration/agent_reports/2026-05/
├── data_quality_d7_R0.md
├── split_leakage_d7_R0.md
├── ood_severity_d7_R0.md
├── novelty_relevance_d7_R0.md
├── training_readiness_d7_R0.md
├── resource_budget_d7_R0.md
└── synthesis/
    └── d7_collection_synthesis_R0.md   (area-chair-synthesis-agent)
```

**quality_report.json 신규 필드**:
- `friction_api: "joint_dry_friction"`
- `friction_ssot_unit: "mu_kinetic"`
- `friction_ssot_value_used: 5.0`
- `friction_mapping: "DEFERRED — see docs/idea/18_DATA_BENCHMARKS.md:44"`

---

## L. R3 smoke와 repair loop 연결

```powershell
& ".venv\Scripts\python.exe" scripts\fglc\r3_smoke.py `
  --phase R3 --config configs\fglc\smoke_maniskill_pickcube.yaml `
  --seed 42 --descriptor smoke_maniskill_pickcube `
  --max-iter 1 --max-wall-clock-minutes 60 `
  --output-root outputs\repair
```

기록 확인:
- `outputs/repair/smoke_maniskill_pickcube/iter_1/metrics.json` 키: `id_nll, ood_mass_nll, ood_friction_nll, val_nll, ood_auroc, attention_entropy, corrected_nll_gain, planner_return_gain, stagnant_epochs, train_nll` (`scripts/fglc/r3_smoke.py:14-22`, `src/fglc/repair/diagnose.py:10-31`).
- `outputs/repair/smoke_maniskill_pickcube/ledger.jsonl` 행 1개 이상.

`diagnose.py` 발화 매핑:
- `id_nll > 0.5 AND stagnant_epochs >= 10` → `DATA_TOO_SMALL` → `DATA_TOO_SMALL_episode_x2 (num_episodes=200)` (`candidates.py:37-46`)
- `ood_auroc < 0.7` → `OOD_TOO_EASY` → `OOD_TOO_EASY_shift_strength_2x (ood_shift_scale=2.0)` (`candidates.py:117-126`)
- `ood_id_nll_diff > 2.0` → `OOD_TOO_HARD` → mass 1.5→1.3 / friction 5.0→3.0 / expand_coverage→200 (`candidates.py:141-170`)
- `eval_ci95_over_effect_size > 1.0` → `EVAL_NOISE_HIGH` (**주의**: 이 메트릭이 `CANONICAL_METRIC_KEYS`에 없음 — 패치 A에 추가 또는 패치 B로 후속 처리)

실패는 결론이 아니라 다음 repair candidate로 전환:
- DATA_TOO_SMALL → Scaled 450 또는 L 900으로 확장
- OOD_TOO_EASY → friction을 mass 단위로 통일(SSoT) 또는 shift_scale 2x
- OOD_TOO_HARD → severity 완화 (1.3, 3.0)
- EVAL_NOISE_HIGH → multi-seed (seed 42, 43, 44) 평균화

---

## M. Codex 패치 A (선행) — collector / build_split 최소 보강

> 사용자 결정 3에 따라 **D7 수집 전에** 1건의 Codex task를 선행. `scripts/run_codex_task.ps1`로 위임. T3 audit 필수.

### TASK_11D7A_COLLECTOR_PATCH.md (`.agent_tasks/codex_queue/`)

```
TASK_NAME: 11D7A_COLLECTOR_PATCH
BACKGROUND:
  Step 11-D7 실제 수집 전 collector/build_split에 quarantine, trajectory hash duplicate
  검사, mode 분기를 추가한다. 기존 9 reject reason과 SPLIT_DEFAULTS는 보존.

GOAL:
  (1) collect_maniskill.py에 --mode {probe,pilot,scaled} 명시 플래그 추가
      (--no-save와 호환). --quarantine-dir 옵션 추가.
  (2) collector.py에 reject episode를 quarantine 경로로 격리 저장하는 기능 추가
      (HDF5 파일명: <seed>_<reason>.h5). default off.
  (3) validators.py에 EPISODE_DUPLICATE reject reason 추가 (state.tobytes() SHA1 기준,
      split 내 중복 차단).
  (4) build_split.py에 trajectory hash duplicate audit 추가 (split-내, split-간 모두).
      quality_report.json에 hash_duplicate_count, hash_collision_pairs 기록.
  (5) build_split.py가 quality_report.json에 friction_api / friction_ssot_unit /
      friction_ssot_value_used / friction_mapping 4 필드 기록.
  (6) diagnose.py CANONICAL_METRIC_KEYS에 eval_ci95_over_effect_size 추가.

FILES_ALLOWED:
  - scripts/fglc/collect_maniskill.py
  - scripts/fglc/build_split.py
  - src/fglc/data/collector.py
  - src/fglc/data/validators.py
  - src/fglc/data/manifest.py
  - src/fglc/repair/diagnose.py
  - tests/test_fglc_no_garbage_data.py
  - tests/test_fglc_split_integrity.py

FILES_FORBIDDEN:
  - src/fglc/schemas/visibility.py
  - docs/idea/*
  - docs/ROADMAP/*
  - .claude/*
  - CLAUDE.md
  - .mcp.json
  - data/*
  - outputs/*

REQUIRED_IMPLEMENTATION:
  (위 6개 항목 그대로)

REQUIRED_TESTS:
  - tests/test_fglc_no_garbage_data.py에 EPISODE_DUPLICATE 케이스 추가 (10번째 reason)
  - tests/test_fglc_split_integrity.py에 trajectory hash duplicate 검사 케이스 추가
  - 279 + 신규 ≥ 281 tests passed

ACCEPTANCE_CRITERIA:
  - pytest -q tests/ 전체 PASS
  - collect_maniskill.py --help 출력에 --mode/--quarantine-dir 등장
  - quality_report.json에 friction_api 4 필드 + hash_duplicate_count 등장

COMMIT_MESSAGE:
  feat(d7): collector quarantine + trajectory hash + friction unit annotation
            (Step 11-D7-A precursor)

STOP_CONDITION:
  허용된 파일 외 어떤 파일도 수정 금지. tests 전부 PASS 미달성 시 abort.

RELATED_AGENT_REPORT_IDS:
  - docs/orchestration/agent_reports/2026-05/impl_risk_11d7a_R0.md
```

T3 audit는 `implementation-risk-critic` + `fglc-code-reviewer`로 수행 후 `/codex-result-audit`. PASS 시에만 accept commit.

---

## N. 실행 명령 후보 (Codex 패치 A 적용 후)

### Stage 0 — Probe (각 split 3~5ep, --no-save)

```powershell
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split train_id        --n-episodes 5 --no-save --verbose
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split val_id          --n-episodes 3 --no-save --verbose
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split test_id         --n-episodes 3 --no-save --verbose
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split ood_mass_low     --ood-mass 1.5     --n-episodes 5 --no-save --verbose
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split ood_friction_low --ood-friction 5.0 --n-episodes 5 --no-save --verbose
```

**Probe Stage 0 gate**: shape 검증(D_x=42, D_a=8), `dones[-1]==True`, success 1건 이상, mass/friction 적용 로그. Agent A·B·F 사전 보고. **FAIL 시 Pilot 진입 금지**.

### Stage 1 — Pilot 180ep

```powershell
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split train_id         --n-episodes 100
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split val_id           --n-episodes 20
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split test_id          --n-episodes 20
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split ood_mass_low      --ood-mass 1.5     --n-episodes 20
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split ood_friction_low  --ood-friction 5.0 --n-episodes 20

& ".venv\Scripts\python.exe" scripts\fglc\build_split.py --data-root data\fglc\PickCube-v1\raw --output-dir data\fglc\PickCube-v1
```

**Pilot Stage 1 gate**: Agent A·B·C·D·E·F 실측 보고. PASS 또는 CONDITIONAL_PASS 시 Scaled. FAIL 시 repair candidate 적용 후 재수집.

### Stage 2 — Scaled 450ep (Pilot 데이터 retention + 추가 수집)

> Pilot 180 데이터는 폐기하지 않고 Scaled 450에 흡수. 즉 추가로 수집할 양은 270ep.

```powershell
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split train_id         --n-episodes 150  # Pilot 100 + 추가 150 = 250
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split val_id           --n-episodes 30   # 20+30 = 50
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split test_id          --n-episodes 30   # 20+30 = 50
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split ood_mass_low      --ood-mass 1.5     --n-episodes 30  # 20+30 = 50
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split ood_friction_low  --ood-friction 5.0 --n-episodes 30  # 20+30 = 50

& ".venv\Scripts\python.exe" scripts\fglc\build_split.py --data-root data\fglc\PickCube-v1\raw --output-dir data\fglc\PickCube-v1
```

> **주의**: collect_maniskill.py가 기존 HDF5에 append 가능한지 사전 확인 필요. 불가하면 Stage 2는 누계 수치(250/50/50/50/50)로 fresh 재수집. Codex 패치 A의 STOP_CONDITION에 append 모드 검토 추가 권장.

### Stage 3 — L=900 (조건부, DATA_TOO_SMALL 또는 EVAL_NOISE_HIGH 발화 시)

```powershell
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split train_id         --n-episodes 250
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split val_id           --n-episodes 50
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split test_id          --n-episodes 50
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split ood_mass_low      --ood-mass 1.5     --n-episodes 50
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split ood_friction_low  --ood-friction 5.0 --n-episodes 50
```

### R3 smoke (Pilot 후, Scaled 후 각 1회)

```powershell
& ".venv\Scripts\python.exe" scripts\fglc\r3_smoke.py `
  --phase R3 --config configs\fglc\smoke_maniskill_pickcube.yaml `
  --seed 42 --descriptor smoke_maniskill_pickcube `
  --max-iter 1 --max-wall-clock-minutes 60 `
  --output-root outputs\repair
```

---

## O. PASS / PATCH_REQUIRED / BLOCKED 판정 기준

### COLLECTION_PLAN_PASS

다음을 모두 충족:
- [ ] Codex 패치 A merge + T3 audit PASS
- [ ] 279 + 신규 ≥ 281 tests passed
- [ ] Probe Stage 0에서 5 split 모두 shape / done / OOD 적용 OK
- [ ] Agent A·B·F 사전 보고에서 disk/time/seed-pool/forbidden audit PASS
- [ ] Pilot 180ep 4 quality gate(garbage / integrity / severity / novelty) 모두 PASS 또는 CONDITIONAL_PASS
- [ ] R3 smoke 1-iter `metrics.json` + `ledger.jsonl` + `iter_1/` artifact 생성
- [ ] Scaled 450ep 4 quality gate 모두 PASS 또는 CONDITIONAL_PASS
- [ ] area-chair-synthesis-agent 통합 보고 PASS

### COLLECTION_PATCH_REQUIRED

다음 중 하나라도 발생:
- Probe에서 mass/friction effect 약함 → severity 조정 (mass→2.0 또는 friction→3.0 검토)
- Pilot에서 OOD_TOO_EASY 발화 → `OOD_TOO_EASY_shift_strength_2x` 적용
- Pilot에서 OOD_TOO_HARD 발화 → `severity_down_mass / severity_down_friction` 적용
- Pilot에서 train_id reject rate > 30% → validator 임계 재조정 사용자 승인 필요
- Scaled에서 EVAL_NOISE_HIGH → multi-seed average 추가
- `eval_ci95_over_effect_size` CANONICAL_METRIC_KEYS 등록 누락 → 패치 B

### COLLECTION_BLOCKED

다음 중 하나라도 발생:
- Probe에서 ManiSkill `PickCube-v1` reset/step 실패 → R1 dependency 재검증
- OOD mass/friction API가 episode마다 적용되지 않음 → collector wrapper 재구현 필요
- raw HDF5가 git staged 됨 → 즉시 `.gitignore` 점검 + `git rm --cached`
- forbidden field가 dataloader에 노출됨 → 즉시 중단, `visibility.py` 점검
- split seed pool overlap 감지 → SPLIT_DEFAULTS 재설계
- Novelty relevance agent FAIL → mass/friction shift가 domain randomization 수준일 가능성, R3 진행 금지
- Codex 패치 A T3 audit FAIL → merge abort, PLAN 재설계

---

## P. 사용자 승인 필요 항목 (수집 진행 전 명시 동의 필요)

1. **Codex 패치 A 위임 시작**: TASK_11D7A_COLLECTOR_PATCH 파일 작성 + `run_codex_task.ps1 -Mode run` 실행 승인.
2. **Probe Stage 0 실행**: 5 split 16~21ep no-save 수집 실행 승인.
3. **Pilot Stage 1 실행** (Probe PASS 후): 180ep 5-split 수집 + build_split + 6 agent 보고 실행 승인.
4. **Scaled Stage 2 실행** (Pilot PASS 후): 추가 270ep 또는 fresh 450ep 수집 실행 승인. (append 가능 여부 사전 확인 결과에 따라)
5. **L 900 확장** (DATA_TOO_SMALL 또는 EVAL_NOISE_HIGH 발화 시): 추가 450ep 수집 실행 승인.
6. **manifest.json / dataset_stats.json / quality_report.json / split_config.yaml만 commit**: raw HDF5 미포함 검증 후 commit 승인.
7. **R3.passed 미생성 확정**: D7 PLAN 종료 시점에도 R3 phase gate sentinel 절대 생성하지 않음을 사용자 재확인.

---

## Verification Plan

### End-to-end smoke verification (코드 수정 시)

```powershell
# 1. 핵심 데이터 테스트
& ".venv\Scripts\python.exe" -m pytest -q `
  tests\test_fglc_no_garbage_data.py `
  tests\test_fglc_split_integrity.py `
  tests\test_fglc_ood_severity.py `
  tests\test_fglc_r3_runner_maniskill.py `
  tests\test_fglc_forbidden_field_sync.py

# 2. Probe (--no-save)
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split train_id --n-episodes 3 --no-save --verbose

# 3. Pilot 1 split sanity (실제 저장 1ep만)
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split train_id --n-episodes 1 --output data\fglc\PickCube-v1\raw\_sanity_train_id.h5

# 4. build_split
& ".venv\Scripts\python.exe" scripts\fglc\build_split.py --data-root data\fglc\PickCube-v1\raw --output-dir data\fglc\PickCube-v1

# 5. R3 smoke 1-iter
& ".venv\Scripts\python.exe" scripts\fglc\r3_smoke.py --phase R3 --config configs\fglc\smoke_maniskill_pickcube.yaml --seed 42 --descriptor smoke_maniskill_pickcube --max-iter 1 --max-wall-clock-minutes 30 --output-root outputs\repair

# 6. gitignore 검증
git status -s data\fglc\PickCube-v1\raw\   # 빈 출력이어야 함
git status -s outputs\repair\               # 빈 출력이어야 함 (.gitkeep 제외)

# 7. forbidden field
& ".venv\Scripts\python.exe" -m pytest -q tests\test_fglc_forbidden_field_sync.py
```

### Critical files (수정 대상 — 패치 A에서만)

- `scripts/fglc/collect_maniskill.py`
- `scripts/fglc/build_split.py`
- `src/fglc/data/collector.py`
- `src/fglc/data/validators.py`
- `src/fglc/data/manifest.py`
- `src/fglc/repair/diagnose.py`
- `tests/test_fglc_no_garbage_data.py`
- `tests/test_fglc_split_integrity.py`

### Reused existing utilities (재사용 권장)

- `validate_episode()` — `src/fglc/data/validators.py:32-89` (9 reject reason)
- `build_dataset_stats()` — `src/fglc/data/manifest.py:128-167`
- `verify_split_integrity()` — `src/fglc/data/manifest.py:178-196`
- `verify_ood_severity()` — `src/fglc/data/manifest.py:199-209`
- `CollectionStats` — `src/fglc/data/collector.py:36-42`
- `_make_maniskill_datasets()` — `src/fglc/data/dataloader.py:108-124`
- `FORBIDDEN_AGENT_FIELDS` runtime guard — `src/fglc/schemas/visibility.py`
- `EpisodeRejectReason` enum — `src/fglc/data/validators.py:20-29`
- `R3SmokeRunner` / `run_repair_loop` — `scripts/fglc/r3_smoke.py:87`

### Absolute do-not

- ❌ `outputs/phase_gates/R3.passed` 생성 금지
- ❌ `outputs/phase_gates/R2.passed` 생성 금지
- ❌ raw HDF5 (`data/fglc/PickCube-v1/raw/*.h5`) git staging 금지
- ❌ `src/fglc/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS` 수정 금지
- ❌ `docs/idea/*` / `docs/ROADMAP/*` 수정 금지 (`-AllowDocsIdea` / `-AllowDocsRoadmap` 없이)
- ❌ TD-MPC2 / DreamerV3 / HiP-RSSM / PLSM / ReDRAW / AdaWM 등 R10 baseline 사전 구현 금지
- ❌ RGB-D / DROID / BridgeData 확장 금지
- ❌ 90ep만으로 R3 gate 충족 주장 금지
- ❌ negative result(예: ID NLL 안 떨어짐) 발생 시 숨김 금지 — repair candidate로 전환

---

## Open UNKNOWNs (BLOCKER 후보)

1. **mean_episode_len 실측**: Probe Stage 0에서 측정 후 본 PLAN의 자원 계산 보정.
2. **collect_maniskill.py append 가능 여부**: Stage 2에서 기존 raw HDF5에 추가 가능한지, 아니면 fresh 재수집인지. 패치 A에서 결정.
3. **`eval_ci95_over_effect_size` 실제 R3 metrics에 등장 여부**: `diagnose.py:10-31` CANONICAL_METRIC_KEYS에 없어 발화 누락 가능 — 패치 A에서 추가.
4. **R3SmokeRunner ledger.jsonl schema**: `scripts/fglc/r3_smoke.py:87`이 `run_repair_loop`로 위임 — `src/fglc/repair/orchestrator.py` 추가 조사 필요. PLAN 진행에 차단 요인은 아님.
5. **PickCube-v1 success rate (mass=1.0)**: train_id에서 ≥30% (Pilot 기준) 충족 여부 미확인 — Probe Stage 0 측정 후 결론.
6. **friction=5.0 → joint dry friction 물리 효과**: probe(2026-05-23)에서 L2 diff ~0.042/step 보고됨(`docs/STEP11_RESULT_REPORT.md:93`) — Pilot에서 state_delta_norm gap 재측정.
