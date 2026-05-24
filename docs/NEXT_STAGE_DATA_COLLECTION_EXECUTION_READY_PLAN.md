# FGLC Next-Stage Data Collection — EXECUTION-READY Plan

> **Status**: EXECUTION-READY — action_gain 구현·수집·검증 절차 정의 완료. 실제 코드 변경·데이터 수집·R3 smoke·`outputs/phase_gates/R3.passed` 생성은 사용자 D-1~D-9 승인 후에만 진행.
> **Branch**: `memory-redesign-2026-05-16`
> **Date**: 2026-05-24
> **Commit ref**: `4fc3565` (4-axis 종합 EXECUTION plan) → 본 문서는 그 후속 단계.
> **이전 문서**: `docs/NEXT_STAGE_FOUR_AXIS_DATA_COLLECTION_EXECUTION_PLAN.md` (4-axis 종합),
> `reports/next_stage_four_axis_agent_synthesis.md` (Agent I CONDITIONAL_ACCEPT 8조건)

---

## §A 현재 상태 요약

### A.1 Commit 이력

| Commit | 내용 |
|---|---|
| `4fc3565` | docs(data): next-stage four-axis dataset execution plan + agent synthesis |
| `6f48d67` | docs(data): four-axis dataset construction plan + agent synthesis |
| `7fe0a02` | docs(data): review interaction axes and dataset strategy for FGLC claims |
| `6f21885` | feat(collector): PushCube-v1 task-aware support + Q1-Q6 plan artifacts |

### A.2 코드/데이터/configs/tests 실측

| 영역 | 항목 | 실측 |
|---|---|---|
| `collector.py` | `_apply_ood()` L66-89 | mass + joint_friction만 처리. env-side 파라미터 전용 — **action_gain은 env에 set 불가** |
| `collector.py` | episode loop | L148 `a = env.action_space.sample()` → L149 `env.step(a)`. **action_gain 곱셈+clip 삽입 위치** |
| `collector.py` | `_flat_obs()` L46-57 | obs dict → flat np.ndarray. noise injection 후보 위치 |
| `collector.py` | eval_metas L187-191 | `true_action_gain` 슬롯 이미 존재 (L191) |
| `maniskill_schema.py` | TASK_OOD_PARAMS L115-130 | `train_id, val_id, test_id, ood_mass_low, ood_friction_low`만. **ood_gain_low / ood_noise_low 부재** |
| `maniskill_schema.py` | REGIME_ID L103-110 | `ood_latency:30` stub 존재(명명 비표준). ood_gain / ood_noise **부재** |
| `maniskill_schema.py` | TASK_SPLIT_DEFAULTS | **코드에 미존재** (계획 문서 가공물) |
| `maniskill_schema.py` | EvalOnlyTransition | `true_action_gain` L56 포함 확인 |
| ManiSkill 3.x | action clipping | sapien_env.py L1042-1044 자동 clip 확인. **외부 pre-clip 권장** |
| PickCube data | friction gap | **0.1380 PASS** (ID 1.3220 / OOD 1.1840, 50ep, seeds 600-609) |
| PickCube data | mass gap | 0.0038 **FAIL** (random policy 한계) |
| PushCube data | friction gap | **0.1236 PASS** (100ep, seeds 600-609) |
| PushCube data | mass gap | 0.0080 **FAIL** |
| quality_report | friction_mapping | **DEFERRED** (µ_kinetic ↔ joint_dry_friction 단위 불일치, 18_DATA_BENCHMARKS.md:44) |
| quality_report | Ckpt 상태 | 0,1,2,3,7,8 PASS / **4 FAIL** (mass ood_sev) / 5,6,9 SKIP |
| seed pool | PickCube 실측 | train 42-91, val 200-209, test 300-309, ood_mass 500-509, ood_friction 600-609 |
| seed pool | PushCube 실측 | train 42-91 (500ep), val/test/ood_* 100ep each, 동일 prefix 규칙 |
| configs | 현황 | `smoke_4060.yaml`, `smoke_maniskill_pickcube.yaml`, `smoke_maniskill_pushcube.yaml`. **gain/latency/noise 부재** |
| configs | PushCube yaml | seed_pool dict (L32-37) + ood_severity block (L65-69) 존재 |
| configs | PickCube yaml | seed_pool, ood_severity block **부재** → 신규 axis 추가 전 보강 필요 (U-N1) |
| `taxonomy.py` | FailureCauseId | **20개**. gain/latency/noise/invisible 전용 cause **부재** |
| `candidates.py` | CANDIDATE_TABLE | **29개**. policy-change family / axis-specific **부재** |
| Phase gates | sentinels | R0, R1, R2 **PASS** / R3 **부재** (올바름) |

### A.3 해결된 UNKNOWN (이전 plan 대비)

- ✅ U-A1: ManiSkill clipping → sapien_env.py L1042-1044 자동 clip 확인, 외부 pre-clip 권장
- ✅ U-C1: seed pool 정확 범위 → 위 표 그대로
- ✅ TASK_SPLIT_DEFAULTS → 코드 미존재 확인, 계획 문서 가공물로 정리

### A.4 잔존 UNKNOWN (Stage 0/1에서 해결 예정)

| ID | 내용 | 해결 예정 단계 |
|---|---|---|
| U-N1 | PickCube yaml에 seed_pool block 없음 | D-8 결정 + Stage 0 |
| U-N2 | REGIME_ID `ood_latency:30` 명명 비표준 | D-9 결정 + Stage 1 |
| U-N3 | PickCube train_id manifest=250ep vs smoke yaml=50ep 격차 | 사용자 확인 |
| U-N4 | quality_report Ckpt 4 FAIL vs STEP11_RESULT Ckpt 4 PASS 충돌 | 사용자 확인 |
| U-N5 | ManiSkill 정확한 버전 핀 (requirements.txt 확인) | Stage 0 |
| U-N6 | PickCube/PushCube ood split seed 끝값 manifest ↔ dataset_stats 정합성 | Stage 0 |
| U-N7 | np.clip 후 dtype float64 cast 여부 | TASK_2050 test |
| U-N8 | PickCube ID baseline action_std (gain=1.0) — gain=0.7 비교 baseline | Probe Stage 2 |
| U-N9 | 2025/2026 신규 4-axis OOD baseline 논문 유무 | Stage 4 또는 R14 |
| U-N10 | friction_mapping DEFERRED 해결 시점 | R12 단계 |

---

## §B 다음 단계 목표

### B.1 단일 핵심 목표

> **friction 기존 데이터(PASS)를 R3 smoke 1번 axis로 재사용하면서, action_gain을 신뢰 가능한 2번째 axis로 만들기 위한 Stage 0→Stage 5 EXECUTION-READY 절차를 단일 PLAN으로 정렬한다. latency/noise는 action_gain Pilot/Scaled PASS 후에만 조건부 진입한다.**

### B.2 목표 달성 경로

```
Stage 0: friction 재검증 + preflight audit (read-only)
Stage 1: action_gain 구현 (TASK_2050, Codex 위임)
Stage 2: action_gain Probe (50ep × 2 task, quarantine)
Stage 3: action_gain Pilot (100ep ood_gain_low × 2 task)
Stage 4: action_gain Scaled (500ep ood_gain_low × 2 task)
Stage 5: R3 smoke 2-axis (friction + action_gain)

조건부 확장:
  action_gain Pilot PASS → latency 진입 (TASK_2053)
  latency Pilot PASS    → noise 진입 (TASK_2054)
  mass track            → 별도 contact-rich policy repair (D-6)
```

### B.3 R5/R6 Stage 3 gate 관계

- `docs/idea/12_TRAINING_STAGES.md` Stage 3: TD-MPC2 baseline 초과를 **≥2 OOD axis**에서 입증 필요
- 현재 PASS 가능 axis = {friction} 1개 → friction만으로 R5/R6 Stage 3 gate 불가
- 목표: {friction + action_gain} → 2축 달성 → Stage 3 gate 충족

### B.4 절대 금지 (본 단계 포함 전체)

- R3.passed 자동 생성 금지 — D-7 사용자 명령 `/fglc-phase-check --pass R3` 후에만
- raw HDF5 commit 금지
- axis 사전 성공 단정 금지 (action_gain PASS 단정 금지)
- negative result 숨김 금지 (mass FAIL, friction DEFERRED, noise specificity ≈ 0)
- delta_min=0.01 / KS p-value threshold 완화 금지

---

## §C action_gain 우선 이유

### C.1 R5/R6 Stage 3 gate 요구

`docs/idea/12_TRAINING_STAGES.md` Stage 3는 TD-MPC2 baseline 초과를 ≥2 OOD axis에서 입증하도록 요구한다. 현재 friction 1축만 PASS 상태이므로 단일 axis 학습만으로는 reviewer attack에 취약하다. mass는 random policy에서 두 task 모두 FAIL(PickCube 0.0038, PushCube 0.0080)이므로 다음 유력 후보는 제어 side의 action_gain 또는 latency다.

### C.2 contact-independent 작동

mass와 달리 action_gain은 `a_executed = clip(a × gain, low, high)`로 모든 joint motor 단계에 직접 작용한다. random policy에서도 action distribution shift가 reward/state trajectory로 전파된다. 이는 contact rate에 독립적이며, PickCube/PushCube 두 task 모두에서 dynamics shift를 기대할 수 있다.

- gain=0.7: action magnitude 약 30% 감소 → joint velocity / end-effector displacement 감소
- gain=1.3: action magnitude 약 30% 증가 → clipping saturation 위험 (secondary 검증 후 폐기 가능)
- **random policy에서 mass OOD FAIL의 근본 원인(contact 부재)이 action_gain에는 해당 없음**

### C.3 novelty framing 강화

HiP-RSSM / PLSM 등 직접 위협 논문들은 mass/friction OOD에 집중하는 경향이 있다. action_gain OOD axis를 추가하면 FGLC의 **control-relevance claim**을 직접 노출하는 axis가 생긴다. causal attention이 action-relevant latent group에 α_t 가중치를 부여하는 behavior가 action_gain 변화에서 더 선명하게 나타날 수 있다.

---

## §D friction 재사용 조건

### D.1 재검증 필요 항목

| 조건 | 확인 사항 | 현재 값 |
|---|---|---|
| gap threshold | state_delta_norm gap > 0.01 | PickCube 0.1380 ✅ / PushCube 0.1236 ✅ |
| KS p-value | p < 0.05 | PASS (manifest 기록) |
| seed disjoint | ood_friction seeds ∩ train seeds = ∅ | 600-609 ∩ 42-91 = ∅ ✅ |
| forbidden field | FORBIDDEN_AGENT_FIELDS count = 0 | 0 ✅ |
| duplicates | trajectory hash collision = 0 | 0 ✅ |

### D.2 friction_mapping DEFERRED 명시적 방어

논문 Appendix / Implementation Detail에 다음 문장을 준비한다:

> "We use ManiSkill's `joint_dry_friction=5.0` as a controlled friction OOD knob. The exact mapping to Coulomb µ_kinetic is deferred (see 18_DATA_BENCHMARKS.md §44) and does not affect FGLC's falsification claim — what matters is the demonstrable, validator-verified dynamics shift (PickCube gap=0.138 / PushCube gap=0.124)."

### D.3 Ckpt 4 FAIL 범위 명확화

- quality_report Ckpt 4 FAIL: **mass OOD severity** 항목 (gap=0.004/0.008)
- friction OOD 항목(Ckpt 0~3)은 PASS — friction 재사용에 직접 영향 없음
- U-N4(Ckpt 4 FAIL vs STEP11_RESULT PASS 충돌)는 사용자 확인 대기

### D.4 friction 재수집 트리거 조건

재수집이 필요한 경우:
- (a) µ_kinetic 매핑이 reviewer에 의해 accept blocking 수준으로 차단된 경우
- (b) Stage 0 audit에서 seed pool 정합성 격차 발견 시 (U-N6)

그 외에는 **재수집 불필요**. 이미 PASS된 friction data를 R3 smoke 첫 번째 axis로 직접 등록한다.

### D.5 R3 dataloader 등록 요건

- R3 smoke 시 friction split을 첫 axis로 등록: `dataloader.py`에서 split_id=`ood_friction_low` 처리 가능 여부 확인
- 1-batch forward: shape (B, T, D_x), (B, T, D_a) 정합성 확인
- dtype: float32 일관성

---

## §E action_gain 구현/수집/검증 계획

### E.1 구현 명세 (Stage 1, TASK_2050)

#### collector.py 변경 (L148-149 사이)

```python
# 현재 (L148-149):
a = env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(a)

# 변경 후:
a = env.action_space.sample()
gain = float(config.ood_params.get("action_gain", 1.0))
if gain != 1.0:
    a = np.clip(
        a * gain,
        env.action_space.low,
        env.action_space.high
    ).astype(np.float32)
obs, reward, terminated, truncated, info = env.step(a)
```

**설계 결정**:
- `np.clip` + dtype cast를 env.step 전에 수행 (외부 pre-clip) — sapien_env.py 자동 clip과 분리하여 정보 손실 방지
- gain=1.0 (ID) 분기 시 기존 코드와 동일 경로 유지
- `import np` 이미 존재 확인 필요

#### maniskill_schema.py 변경 (~10 LOC)

```python
# REGIME_ID (L103-110)에 추가:
"ood_gain_low": 40,

# TASK_OOD_PARAMS (L115-130) PickCube 항목에 추가:
"PickCube-v1": {
    "train_id":       {"action_gain": 1.0},
    "val_id":         {"action_gain": 1.0},
    "test_id":        {"action_gain": 1.0},
    "ood_mass_low":   {"mass": 0.5},
    "ood_friction_low": {"joint_dry_friction": 5.0},
    "ood_gain_low":   {"action_gain": 0.7},   # 신규
},
# PushCube도 동일
```

#### configs/fglc 신규 (2개)

`configs/fglc/smoke_maniskill_pickcube_gain.yaml`:
```yaml
# extends: smoke_maniskill_pickcube.yaml
task_name: PickCube-v1
ood_axis: action_gain
ood_gain_value: 0.7
seed_pool:
  train:         {start: 42,  count: 50}
  val:           {start: 200, count: 10}
  test:          {start: 300, count: 10}
  ood_gain_low:  {start: 700, count: 10}
ood_severity:
  ood_gain_low:  {action_gain: 0.7}
```

`configs/fglc/smoke_maniskill_pushcube_gain.yaml`: 동일 구조, seed_pool 동일 prefix

#### tests 신규 (1개)

`tests/test_fglc_action_gain_collector.py` 핵심 assertion:
1. 1-ep collect with gain=0.7 → `np.abs(actions).mean() < id_baseline × 0.85` (action magnitude 감소)
2. `eval_metas["true_action_gain"] == 0.7`
3. FORBIDDEN_AGENT_FIELDS 중 inference input 노출 = 0건
4. dtype: actions.dtype == float32
5. reproducibility: same seed → same action sequence (대표 10 step)

**LOC 총합**: collector.py +3, schema +10, config 2개 ×~15, test ~80 ≈ 총 **120 LOC**

### E.2 Codex 위임 분기 (D-2)

D-2=(a) Codex 위임 권장 이유:
- 동시 수정 파일 ≥ 3 (`collector.py`, `maniskill_schema.py`, configs 2개, test 1개)
- 테스트 작성 + 구현 동반 → `codex_orchestration_rules.md` §Codex 호출 트리거 (a),(b) 충족

TASK 파일 경로: `.agent_tasks/codex_queue/TASK_2050_ACTION_GAIN_IMPL.md`

실행 명령:
```powershell
scripts/run_codex_task.ps1 -Mode run `
  -TaskName 2050 `
  -TaskFile .agent_tasks/codex_queue/TASK_2050_ACTION_GAIN_IMPL.md `
  -BypassSandbox
```

T3 implementation-risk-critic: post-Codex, pre-accept commit 필수 (Gatekeeper 6조건 #6)

### E.3 Probe (Stage 2, TASK_2051)

**목적**: action_gain axis 진입 가능 여부 조기 판단

```
gain=0.7 primary  × 2 task = 50ep × 2 = 100ep (quarantine 경로)
gain=1.3 secondary × PickCube 50ep (clipping saturation 확인용)
```

**성공 조건 (probe-lenient)**:
| Gate | 기준 |
|---|---|
| shape consistency | D_x=42(PickCube)/35(PushCube), D_a=8 |
| NaN/Inf | 0건 |
| done/truncated | 정상 bool |
| forbidden field | 0건 |
| true_action_gain | == 0.7 ✅ |
| action 분포 shift | `|a|_mean` ID 대비 ≥10% 감소 |
| **state_delta_norm gap** | **> 0.005** (probe lenient, Pilot에서 0.01) |
| KS p-value | < 0.1 (probe lenient) |

**실패 분기**:
- gap < 0.005 → `diagnose.py` → `OOD_AXIS_GAIN_UNCOVERED` (신규 cause, D-5 승인) → gain 0.7 → 0.5 severity-up
- clipping saturation (gain=1.3 시 `|a| ≈ clip` 빈도 > 50%) → gain=1.3 폐기, low side만 유지

### E.4 Pilot (Stage 3, TASK_2052 전반)

```
gain=0.7 × {ood_gain_low: 100ep} × 2 task = 200ep 신규
ID 분할(train 250ep)은 기존 데이터 재사용
```

**성공 조건 (30 gate §I 전체)**:
| Gate | 기준 |
|---|---|
| gap | > 0.01 |
| KS p-value | < 0.05 |
| Cohen's d | > 0.3 (qvel/action dims subset) |
| seed disjoint | ∅ |
| trajectory hash duplicate | 0 |
| forbidden field | 0 |
| quality_report + manifest + dataset_stats | 존재 + 기존 manifest append |

Agent B/C/D/F review (compact) → PASS 시 Scaled 진입

### E.5 Scaled (Stage 4, TASK_2052 후반)

```
gain=0.7 × ood_gain_low 500ep × 2 task = 1000ep 신규
누적: probe 50 + pilot 100 + scaled 500 = 650ep/task ood_gain_low
```

**추가 성공 조건**:
| Gate | 기준 |
|---|---|
| per-dim Cohen's d > 0.3 | action dims 8개 중 ≥3 개 |
| KS p-value | < 0.01 |
| CI95 | < 50% of mean gap |

Agent B/C/D/F/G/H review (compact + war-room 선택) → R3 readiness

### E.6 Stop Conditions

**axis 진입 STOP**:
- `env.action_space.low/high` shape mismatch → BLOCKED
- action dtype float64 (cast 격차) → BLOCKED
- `np.clip` 후 dtype 변경 → schema reject → BLOCKED

**수집 STOP**:
- 3회 연속 inconclusive (`--max-consecutive-inconclusive=2` + 1 escape)
- wall-clock > 60 min per stage
- target_reached: gap > 0.01 + 30 gate PASS

---

## §F latency/noise 조건부 확장 계획

### F.1 진입 조건 (엄격한 순서 준수)

```
latency 진입: action_gain Pilot PASS (gap > 0.01)
noise 진입:   latency Pilot PASS
```

### F.2 latency 구현 명세 (TASK_2053, 조건부)

collector.py episode 시작 시:
```python
from collections import deque
delay = int(config.ood_params.get("action_latency", 0))
buffer = deque([np.zeros(D_a, dtype=np.float32)] * delay, maxlen=delay) if delay > 0 else None
```

episode loop L148 직후:
```python
a_commanded = env.action_space.sample()
if buffer is not None:
    buffer.append(a_commanded)
    a = buffer[0]   # FIFO: delay 스텝 전 action 실행
else:
    a = a_commanded
```

**설계 결정**:
- reset 정책: **zero-fill** (D-3 권장안) — episode 시작 시 `deque([np.zeros(D_a)]×delay)`
- commanded vs executed 분리: `true_latency` → eval_metas (EvalOnly, inference 불가)
- REGIME_ID `ood_latency:30` → `ood_latency_low:30` 통일 (D-9 결정 필요)

### F.3 noise 구현 명세 (TASK_2054, 조건부)

`_flat_obs(obs)` 직후:
```python
sigma = float(config.ood_params.get("noise_sigma", 0.0))
if sigma > 0.2:
    raise ValueError(f"noise_sigma={sigma} > 0.2 BLOCKED")
if sigma > 0.15:
    warnings.warn(f"noise_sigma={sigma} > 0.15 WARNING")
if sigma > 0:
    rng = np.random.default_rng(seed + episode_idx)  # per-episode 결정적
    flat = flat + rng.normal(0, sigma, flat.shape).astype(np.float32)
```

### F.4 noise specificity metric framework (R4 이후 실측)

noise는 **dynamics OOD axis가 아닌 specificity test axis**. 측정 목적:
- FGLC β-gate가 observation noise를 dynamics shift로 오인하지 않음을 검증

| Metric | 기준 | 의미 |
|---|---|---|
| state_delta_norm gap | ≈ 0 (의도적) | noise는 dynamics 변화 없음 |
| β-gate AUROC | < 0.65 | β-gate가 noise를 dynamics shift로 검출 안 함 |
| β-gate FPR | < 0.05 | 오탐 낮음 (σ calibration 올바름) |
| Σ̂_t / Σ_true ratio | ∈ [0.8, 1.2] | 분산 추정 calibration |

---

## §G 자원 계산 기반 수집량 계획

### G.1 bytes/transition (실측 근거)

| Task | D_x | D_a | bytes/transition | bytes/ep (len=50) |
|---|---|---|---|---|
| PickCube-v1 | 42 | 8 | ≈ 230 B | ≈ 11.5 KB |
| PushCube-v1 | 35 | 8 | ≈ 200 B | ≈ 10 KB |

계산: (D_x + D_a + scalar×4) × float32(4 B) ≈ (42+8+4)×4 = 216B (PickCube)

### G.2 Stage × Axis × Task 매트릭스

**action_gain 단독 (gain=0.7)**:

| Stage | 신규 ood ep/task | 총 신규 ep | PickCube disk | PushCube disk | 예상 wall clock |
|---|---|---|---|---|---|
| Probe (S2) | 50 | 100 | 0.6 MB | 0.5 MB | 2~5 min |
| Pilot (S3) | 100 | 200 | 1.2 MB | 1.0 MB | 5~10 min |
| Scaled (S4) | 500 | 1000 | 6 MB | 5 MB | 20~40 min |
| Robust (+2 seed) | 2000 | 4000 | 24 MB | 20 MB | 1~2 hour |

**action_gain Scaled 누적 (Probe+Pilot+Scaled)**: 2 task × 650ep ≈ **16 MB / ~1 hour**

**3-axis 확장 시나리오** (action_gain + latency + noise Scaled):
- 3 axis × 2 task × Scaled (650ep) ≈ **50 MB / ~3 hour**

**4-axis Robust**:
- 4 axis × 2 task × Robust (2000ep) ≈ **200 MB / ~12 hour**

### G.3 R3 training VRAM 예상

| Config | VRAM 예상 | 판정 |
|---|---|---|
| batch=16, T=16, K=8, d=32, h=256 | ~1 GB | ✅ RTX 4060 8GB 여유 |
| batch=32, T=32, K=16, d=64, h=512 | ~3 GB | ✅ |
| batch=64, T=64, K=32, d=128, h=512 | ~7.5 GB | ⚠ OOM 위험 |

1-epoch smoke (650ep ood + 250ep ID 재사용) ≈ **5~10 min on RTX 4060**

### G.4 DATA_TOO_SMALL 확장 trigger

- Pilot ood ep < 100 + KS p > 0.05 → episode ×2 재수집
- Scaled CI95 > 60% mean → episode ×2 재수집
- Robust: 1 seed → 2 seed 추가 + ID 비교

---

## §H 팀 에이전트 검증 계획

### H.1 Stage × Agent 매트릭스

| Agent | Role | S0 | S1 impl | S2 probe | S3 pilot | S4 scaled | R3 smoke |
|---|---|---|---|---|---|---|---|
| A axis-impl-auditor | 구현 정합성 | ✅ pre | ✅ post | — | — | — | — |
| B data-quality | 데이터 품질 | — | — | ✅ | ✅ | ✅ | — |
| C split-leakage | split 누수 | — | — | — | ✅ | ✅ | — |
| D ood-severity | OOD severity | — | — | ✅ lenient | ✅ | ✅ | — |
| E dynamics-forensics | dynamics 분석 | — | — | ✅ | ✅ if D fail | — | — |
| F claim-metric | claim-metric 정렬 | — | — | — | ✅ | ✅ | ✅ |
| G novelty-relevance | 노벨티 방어 | — | — | — | — | ✅ | — |
| H resource-budget | 자원 예산 | ✅ pre-S3 | — | — | — | ✅ pre-Robust | — |
| I synthesis chair | 최종 판정 | ✅ post | ✅ post | ✅ post | ✅ post | ✅ post | ✅ post |

### H.2 호출 명령 및 모드

| 상황 | 명령 | 모드 |
|---|---|---|
| Stage 0~2 빠른 gate | `/agent-team-review compact` | compact |
| Stage 3/4 심층 검증 | `/agent-team-review deep` | deep |
| axis PASS/FAIL 직전 최종 | `/war-room` | deep, Agent I 주재 |

### H.3 산출 경로

- 개별: `docs/orchestration/agent_reports/2026-05/<agent>_action_gain_<stage>_R<n>.md`
- synthesis: `docs/orchestration/agent_reports/synthesis/2026-05/action_gain_<stage>_R<n>.md`

---

## §I 품질 gate checklist (30개)

| # | Gate | 측정 방법 | 기준 |
|---|---|---|---|
| 1 | schema consistency | validators.py SCHEMA_MISMATCH | 0건 |
| 2 | state/action dim | D_x/D_a observed | schema와 일치 |
| 3 | dtype | torch.dtype | float32 + int32 |
| 4 | NaN/Inf | torch.isfinite | 0건 |
| 5 | reward scalar | reward.shape | () |
| 6 | done/truncated | bool consistency | 100% |
| 7 | accept rate | rejected/total | ≥ 99% |
| 8 | reject reason table | EpisodeRejectReason histogram | 기록됨 |
| 9 | state_delta distribution | mean/std per split | 비퇴화 |
| 10 | action_norm distribution | mean/std per split | 비퇴화 |
| 11 | reward distribution | mean/std per split | 비퇴화 |
| 12 | ep length distribution | mean ≈ 50 | 일정 |
| 13 | success/failure ratio | reward > threshold | 기록됨 |
| 14 | seed disjoint | set intersection | ∅ |
| 15 | trajectory hash duplicate | hash collision | 0건 |
| 16 | forbidden inference field | FORBIDDEN_AGENT_FIELDS | 0건 |
| 17 | OOD param applied | _apply_ood log + ood_params | 비어있지 않음 |
| 18 | ID/OOD gap (gain) | state_delta_norm gap | > 0.01 (pilot+) |
| 18' | noise specificity | dynamics gap | ≈ 0 (의도적) |
| 19 | KS p-value | scipy.ks_2samp | < 0.05 |
| 20 | per-dim shift | Cohen's d per dim | > 0.3 (≥3 dims) |
| 21 | axis response evidence | qvel/tcp delta vs ID | 비영(non-zero) |
| 22 | R3 dataloader compat | 1-batch forward shape | 일치 |
| 23 | 1-batch forward | model fwd | shape OK |
| 24 | 1-epoch smoke | NLL | finite |
| 25 | metrics.json artifact | 파일 존재 | yes |
| 26 | repair loop ledger | ledger jsonl line | ≥ 1 |
| 27 | quality_report.json | 파일 존재 | yes |
| 28 | manifest.json | 파일 존재 | yes |
| 29 | dataset_stats.json | 파일 존재 | yes |
| 30 | git hygiene | git status | clean (raw HDF5 없음) |

**Probe 적용 subset**: Gate 1~10, 14~17, 21 (총 16개, lenient 기준)
**Pilot 전체**: Gate 1~21 + 26~29 (총 25개)
**Scaled 전체**: Gate 1~30 (30개)

---

## §J repair loop 및 재수집 전략

### J.1 16단계 repair loop

```
1.  metric 수집 (post-collection: gap / KS / Cohen's d / accept rate)
2.  diagnose.py 호출 → FailureCauseId 매핑
3.  axis × cause 매핑 표 참조 (§J.2)
4.  candidates.py 후보 생성 (29개 + 신규 D-5 제안)
5.  ranker.py 우선순위 결정
6.  수집 조건/config 수정 (BACKBONE 변경 시 D-5 사용자 승인)
7.  재수집 (probe 실패 → probe 재시도, pilot 실패 → pilot 재시도)
8.  compare.py before/after metric 비교
9.  ledger.py 19 REQUIRED_KEYS 충족 확인
10. ledger JSONL append (outputs/repair/loop_<task>_<date>.jsonl)
11. Agent B/D/I re-review (compact)
12. PASS → 다음 stage 진입
13. FAIL → step 1 회귀 (max 3 iter)
14. INCONCLUSIVE (max 2 consecutive) → USER_ESCALATION
15. R3 smoke 진입 조건 충족 시 r3_smoke.py (D-7 사용자 승인 후)
16. commit (raw HDF5 / repair *.jsonl 대용량 / sentinel 제외)
```

### J.2 axis × cause × candidate 매핑

| 시나리오 | 현재 cause | 신규 cause (D-5 승인 필요) | 현재 candidate | 신규 candidate (D-5) |
|---|---|---|---|---|
| action_gain gap < 0.005 (probe) | 없음 | `OOD_AXIS_GAIN_UNCOVERED` | 없음 | severity-up (0.7→0.5) |
| action_gain gap < 0.01 (pilot) | `DATA_TOO_SMALL` ✅ | — | episode ×2 ✅ | — |
| action_gain clipping saturation | `OOD_TOO_HARD` | `OOD_AXIS_GAIN_CLIP_SATURATION` | 없음 | severity-down high side (1.3→1.1) |
| latency gap < 0.01 | 없음 | `OOD_AXIS_LATENCY_UNCOVERED` | 없음 | delay-up (3→5→8) |
| noise AUROC ≥ 0.7 | `EVAL_NOISE_HIGH` ⚠ | `OBS_NOISE_SIGMA_MISMATCH` | eval_repeat ⚠ | Σ recalibration |
| validators reject > 5% | `DATA_TOO_SMALL` ✅ / `IMPLEMENTATION_BUG_SUSPECTED` ✅ | — | 동일 ✅ | — |
| R3 NLL = inf | `IMPLEMENTATION_BUG_SUSPECTED` ✅ | — | manual_blocker ✅ | — |

**신규 cause/candidate 추가는 BACKBONE 등급 1 → D-5 사용자 승인 필수**

### J.3 Stop conditions

```
--max-iter=3                    : 3회 후 USER_ESCALATION
--max-consecutive-inconclusive=2: 연속 불명 2회 후 USER_ESCALATION
--max-wall-clock-minutes=60     : stage당 60분 초과 시 정지
target_reached                  : 30 gate PASS
hook_blocked                    : pre-commit / forbidden field guard → USER_ESCALATION
```

### J.4 Negative result 공시 의무

mass FAIL (두 task, random policy 한계), friction DEFERRED (µ_kinetic 매핑), noise specificity gap ≈ 0 (의도적) — 이 세 결과는 **숨기지 않고** 논문 Section 4 / Appendix에 명시한다.

---

## §K TASK 분해안 (TASK_2049~2056)

### TASK_2049 — PREFLIGHT_AUDIT

```
TASK_NAME: TASK_2049_PREFLIGHT_AUDIT
BACKGROUND:
  commit 4fc3565 (4-axis plan) → EXECUTION 진입 직전.
  friction 재사용 증거 재확인 + action_gain 구현 위치 + clipping 정책 + seed pool + yaml 보강 격차.
GOAL:
  §A 현재 상태 최종 확인 + Stage 0 6 check 통과 + D-1~D-9 결정 항목 정리
FILES_ALLOWED:
  docs/NEXT_STAGE_DATA_COLLECTION_EXECUTION_READY_PLAN.md
  reports/next_stage_data_collection_agent_review.md
FILES_FORBIDDEN:
  src/, scripts/, configs/, data/, outputs/, docs/idea/, .claude/, tests/
REQUIRED_IMPLEMENTATION:
  read-only audit + MD 작성 (코드 변경 없음)
REQUIRED_TESTS:
  git status 검증 — 다른 파일 수정 0건
ACCEPTANCE_CRITERIA:
  Stage 0 6 check PASS
  D-1~D-9 결정 항목 표 완성
  U-N1~N10 해결안 또는 deferred 명시
COMMIT_MESSAGE:
  docs(data): execution-ready data collection plan §A preflight
STOP_CONDITION:
  ManiSkill API 신규 격차 발견 시 BLOCKED + 사용자 escalation
```

### TASK_2050 — ACTION_GAIN_IMPL

```
TASK_NAME: TASK_2050_ACTION_GAIN_IMPL
BACKGROUND:
  collector.py L148-149 사이에 np.clip(a*gain, low, high) 삽입.
  maniskill_schema.py TASK_OOD_PARAMS + REGIME_ID 확장.
  gain yaml 2개 신규. test 1개 신규.
GOAL:
  action_gain OOD parameter 적용 (~120 LOC)
FILES_ALLOWED:
  src/fglc/data/collector.py
  src/fglc/data/maniskill_schema.py
  configs/fglc/smoke_maniskill_pickcube_gain.yaml (신규)
  configs/fglc/smoke_maniskill_pushcube_gain.yaml (신규)
  tests/test_fglc_action_gain_collector.py (신규)
FILES_FORBIDDEN:
  src/fglc/schemas/visibility.py
  docs/idea/
  .claude/
  src/fglc/repair/
REQUIRED_IMPLEMENTATION:
  - collector.py L148-149 사이 gain 분기 + np.clip + float32 cast
  - maniskill_schema.py: REGIME_ID에 ood_gain_low:40, TASK_OOD_PARAMS PickCube/PushCube에 ood_gain_low:{"action_gain":0.7}
  - PickCube/PushCube gain yaml (seed_pool 700s 영역)
  - test: 1-ep + true_action_gain==0.7 + forbidden field 0 + dtype float32 + reproducibility
REQUIRED_TESTS:
  pytest -q tests/test_fglc_action_gain_collector.py
  pytest -q tests/test_fglc_forbidden_field_sync.py
ACCEPTANCE_CRITERIA:
  pytest -q tests/test_fglc_action_gain_collector.py PASS
  git diff --cached 수동 검토 통과
  금지 경로 미수정 확인
  RESULT.md 존재
  T3 implementation-risk-critic PASS
COMMIT_MESSAGE:
  feat(collector): action_gain OOD parameter support
STOP_CONDITION:
  clipping 위치 모호 시 BLOCKED
  env.action_space.low/high shape mismatch 시 BLOCKED
RELATED_AGENT_REPORT_IDS:
  impl_risk_TASK_2050_R1.md (T3 post-Codex)
```

### TASK_2051 — GAIN_PROBE

```
TASK_NAME: TASK_2051_GAIN_PROBE
BACKGROUND:
  TASK_2050 완료 후 50ep × {gain=0.7, gain=1.3} × 2 task probe.
  quarantine 경로에 저장 (raw HDF5 commit 금지).
GOAL:
  axis 진입 PASS/FAIL 조기 결정
FILES_ALLOWED:
  data/fglc/PickCube-v1/probe_gain/ (quarantine)
  data/fglc/PushCube-v1/probe_gain/ (quarantine)
  docs/orchestration/agent_reports/2026-05/
FILES_FORBIDDEN:
  src/, configs/, outputs/phase_gates/
REQUIRED_IMPLEMENTATION:
  python scripts/fglc/collect_maniskill.py \
    --config configs/fglc/smoke_maniskill_pickcube_gain.yaml \
    --split ood_gain_low --quarantine
REQUIRED_TESTS:
  Gate 1~10, 14~17, 21 (probe subset 16개) PASS
ACCEPTANCE_CRITERIA:
  state_delta_norm gap > 0.005
  KS p < 0.1
  true_action_gain == 0.7
  forbidden field 0건
  reproducibility (same seed → same action sequence)
COMMIT_MESSAGE:
  data(probe): action_gain probe collection PickCube/PushCube (quarantine)
STOP_CONDITION:
  gap < 0.005 → diagnose.py 호출 → repair loop (gain 0.7→0.5 후보, D-5 승인)
```

### TASK_2052 — GAIN_PILOT_SCALED

```
TASK_NAME: TASK_2052_GAIN_PILOT_SCALED
BACKGROUND:
  probe PASS 후 Pilot 100ep + Scaled 500ep × 2 task.
  기존 ID 데이터 재사용, ood_gain_low split 신규 수집.
GOAL:
  action_gain Scaled PASS → R3 smoke 2-axis readiness
FILES_ALLOWED:
  data/fglc/PickCube-v1/ (split append)
  data/fglc/PushCube-v1/ (split append)
  manifest.json, dataset_stats.json, quality_report.json 갱신
FILES_FORBIDDEN:
  outputs/phase_gates/R3.passed (절대 생성 금지)
REQUIRED_IMPLEMENTATION:
  python scripts/fglc/collect_maniskill.py ... (pilot)
  python scripts/fglc/collect_maniskill.py ... (scaled)
  python scripts/fglc/build_split.py ... (manifest 갱신)
  30 gate per stage
REQUIRED_TESTS:
  test_fglc_split_integrity.py
  test_fglc_ood_severity.py
  test_fglc_forbidden_field_sync.py
ACCEPTANCE_CRITERIA:
  gap > 0.01 + KS p < 0.05 + Cohen's d > 0.3 (≥3 dims)
  30 gate 전체 PASS
  manifest 갱신 + Agent B/C/D/F review PASS
COMMIT_MESSAGE:
  data(scaled): action_gain pilot+scaled PickCube/PushCube
STOP_CONDITION:
  Pilot FAIL → repair loop. 3 iter inconclusive → USER_ESCALATION
```

### TASK_2053 — LATENCY_IMPL_PROBE (조건부)

```
TASK_NAME: TASK_2053_LATENCY_IMPL_PROBE
BACKGROUND:
  action_gain Pilot PASS 후 진입.
  deque FIFO + zero-fill reset + commanded/executed 분리.
GOAL:
  latency OOD parameter ~40 LOC + probe 50ep × {delay=3,5}
FILES_ALLOWED:
  src/fglc/data/collector.py
  src/fglc/data/maniskill_schema.py
  configs/fglc/smoke_maniskill_pickcube_latency.yaml (신규)
  configs/fglc/smoke_maniskill_pushcube_latency.yaml (신규)
  tests/test_fglc_latency_collector.py (신규)
  data/fglc/*/probe_latency/ (quarantine)
FILES_FORBIDDEN:
  src/fglc/schemas/visibility.py
REQUIRED_IMPLEMENTATION:
  deque(maxlen=delay) + zero-fill reset + commanded vs executed + true_latency eval_only
  REGIME_ID ood_latency_low:30 통일 (D-9 결정 후)
REQUIRED_TESTS:
  test_fglc_latency_collector.py + reproducibility
ACCEPTANCE_CRITERIA:
  1-ep smoke + 50ep probe gap > 0.005 + delay 적용 evidence
COMMIT_MESSAGE:
  feat(collector): action_latency OOD parameter support + probe
STOP_CONDITION:
  D-3 reset 정책 미결정 시 BLOCKED
  delay=5에서 gap<0.005 → delay=8 후보 (D-5 신규 cause)
```

### TASK_2054 — NOISE_IMPL_PROBE (조건부)

```
TASK_NAME: TASK_2054_NOISE_IMPL_PROBE
BACKGROUND:
  latency Pilot PASS 후 진입. noise는 specificity test axis.
  AUROC < 0.65 / Σ calibration framework 정의 (실측은 R4).
GOAL:
  noise OOD parameter ~15 LOC + probe 50ep × σ=0.05
FILES_ALLOWED:
  src/fglc/data/collector.py
  configs/fglc/smoke_maniskill_pickcube_noise.yaml (신규)
  configs/fglc/smoke_maniskill_pushcube_noise.yaml (신규)
  tests/test_fglc_noise_collector.py (신규)
FILES_FORBIDDEN:
  동일 (visibility.py)
REQUIRED_IMPLEMENTATION:
  _flat_obs 후 rng.normal 덧셈 + per-episode seed + σ guard (>0.15 WARN, >0.2 BLOCK)
REQUIRED_TESTS:
  noise σ 적용 evidence + reproducibility + true_noise_sigma eval_only
ACCEPTANCE_CRITERIA:
  1-ep smoke + dynamics gap ≈ 0 확인 + specificity metric framework MD 작성
COMMIT_MESSAGE:
  feat(collector): observation_noise OOD parameter support + framework
STOP_CONDITION:
  σ > 0.15에서 dynamics destruction sign → σ_max 하향 (D-4 재확인)
```

### TASK_2055 — R3_SMOKE_INTEGRATION

```
TASK_NAME: TASK_2055_R3_SMOKE_INTEGRATION
BACKGROUND:
  action_gain Scaled PASS 후. friction + action_gain (+ 조건부 latency/noise)
  → r3_smoke.py → metrics.json → ledger.
GOAL:
  R3 smoke 2-axis (friction + action_gain) 1-epoch 완료
FILES_ALLOWED:
  scripts/fglc/r3_smoke.py (최소 편집)
  outputs/metrics/
  outputs/repair/loop_*.jsonl
  docs/orchestration/agent_reports/synthesis/2026-05/
FILES_FORBIDDEN:
  outputs/phase_gates/R3.passed (절대 생성 금지 — D-7 사용자 명령 필수)
REQUIRED_IMPLEMENTATION:
  dataloader 2-axis 지원 확인 + 1-batch forward + 1-epoch smoke + metrics.json
REQUIRED_TESTS:
  test_fglc_r3_runner_maniskill.py PASS
ACCEPTANCE_CRITERIA:
  NLL finite
  ood_nll > id_nll per-axis (friction + action_gain)
  metrics.json 존재
  ledger jsonl ≥ 1
COMMIT_MESSAGE:
  feat(r3): two-axis smoke integration (friction + action_gain)
STOP_CONDITION:
  R3 smoke FAIL → repair loop (axis별 cause). R3.passed 자동 생성 절대 금지
RELATED_AGENT_REPORT_IDS:
  impl_risk_TASK_2055_R1.md
  claim_metric_TASK_2055_R1.md
```

### TASK_2056 — EXECUTION_FINALIZE

```
TASK_NAME: TASK_2056_EXECUTION_FINALIZE
BACKGROUND:
  TASK_2049~2055 결과 통합 + D-1~D-9 결정 정리 + R3 진입 사용자 승인 요청.
  negative result 공시 (mass FAIL, friction DEFERRED).
GOAL:
  §L PASS/PATCH/BLOCKED + §M 사용자 결정 + §N atomic + §O 다음 단계
FILES_ALLOWED:
  docs/NEXT_STAGE_DATA_COLLECTION_EXECUTION_READY_PLAN.md
  reports/next_stage_data_collection_agent_review.md
FILES_FORBIDDEN:
  outputs/phase_gates/R3.passed
REQUIRED_IMPLEMENTATION:
  8 TASK 결과 종합 + commit 단위 정리 (TASK별 1 commit)
REQUIRED_TESTS:
  pytest -q (전체 회귀) + git status clean
ACCEPTANCE_CRITERIA:
  8 TASK 완료 + Agent I 최종 판정 + 사용자 승인 대기
COMMIT_MESSAGE:
  docs(data): execution-ready data collection plan finalize
STOP_CONDITION:
  사용자 승인 미응답 시 plan 완료 + 대기
```

---

## §L PASS/PATCH_REQUIRED/BLOCKED 기준

### L.1 본 plan 자체

| 판정 | 조건 |
|---|---|
| **PLAN_PASS** | §A~§O 15 섹션 + axis 카드 4개 + 30 gate + 16 repair loop + TASK_2049~2056 + D-1~D-9 + atomic checklist + U-N1~N10 처리 + verification plan → 모두 충족 |
| **PATCH_REQUIRED** | yaml seed_pool 보강 절차 미완 / REGIME_ID 명명 결정 미정 |
| **PLAN_BLOCKED** | FORBIDDEN_AGENT_FIELDS 격차 발견 / ManiSkill clipping 패턴 재격차 / docs/idea/18 변경 필수 |

### L.2 axis별 R3 진입 조건

| Axis | R3 진입 조건 | 자동/사용자 |
|---|---|---|
| friction | 이미 PASS (Scaled 재검증만) | Stage 0 재확인 후 자동 |
| action_gain | Stage 4 Scaled PASS (gap>0.01, KS<0.05, 30 gate) | **D-7 사용자 승인** |
| latency | Stage 3 Pilot PASS (action_gain PASS 후 진입) | **D-7** |
| noise | Stage 3 Pilot PASS + AUROC < 0.65 | **D-7** |

### L.3 R3 smoke PASS 전체 조건

- 데이터: friction + action_gain 최소 2축 Scaled 완료
- 모델: 1-batch fwd shape OK + 1-epoch NLL finite
- 검증: ood_nll > id_nll per-axis + metrics.json 존재
- 절차: D-7 사용자 `/fglc-phase-check --pass R3` 명령

---

## §M 사용자 승인 필요 항목 (D-1~D-9)

### D-1: 다음 EXECUTION 진입 axis

- **(a) action_gain (gain=0.7 primary)** [권장 — 본 PLAN 전체가 이 선택 전제]
- (b) latency 먼저
- (c) noise 먼저
- (d) friction 재수집 (µ_kinetic 매핑 해결 우선)

### D-2: TASK_2050 위임 대상

- **(a) Codex 위임** [권장 — 3파일 동시 수정, ~120 LOC]
- (b) Claude 직접
- (c) Codex worktree 병렬

### D-3: latency reset 정책

- **(a) zero-fill** [권장 — episode 시작 시 `deque([np.zeros(D_a)]×delay)`]
- (b) first-action-repeat
- (c) random init

### D-4: noise σ 상한

- **(a) σ_max=0.15** [권장]
- (b) σ_max=0.2 (SSoT 그대로)
- (c) σ_max=0.1 (very conservative)

### D-5: BACKBONE 등급 1 신규 cause/candidate 사전 승인

- (a) taxonomy.py 4 신규 cause 사전 일괄 승인
- (b) candidates.py policy-change family 사전 일괄 승인
- **(c) 모든 BACKBONE 변경은 case-by-case** [권장 — 과학적 계약 정확도 유지]

### D-6: mass repair track

- **(a) 4 axis 완료 후 contact-rich policy track** [권장]
- (b) LiftCube probe 병렬 진행
- (c) mass DEFERRED 확정 + 논문에 명시

### D-7: R3.passed 생성 권한

- **(a) action_gain Scaled PASS + R3 smoke OK 시 사용자 명령 `/fglc-phase-check --pass R3`** [권장]
- (b) Claude 자동 (BACKBONE 위반, 금지)
- (c) 별도 한 번 더 review 후 결정

### D-8 (신규): PickCube yaml seed_pool 보강 commit 단위

- (a) TASK_2049 별도 micro-task commit (read-only 분리)
- **(b) TASK_2050에 포함** [권장 — gain yaml 신규와 함께]
- (c) Stage 0 audit에서 미보강 결정 → 신규 axis는 yaml 외부 인자로

### D-9 (신규): REGIME_ID `ood_latency:30` 명명 통일 시점

- **(a) TASK_2053 latency 구현 시 동시 변경** [권장 — latency axis 첫 사용 시점]
- (b) TASK_2050 action_gain과 함께 일괄 변경
- (c) 명명 유지 (비표준이지만 현재 사용 없음)

---

## §N atomic checklist

```
[ ] 탐색: 30 reference + Phase 1 Explore (2개 병렬) 결과 read 완료
[ ] 계획: §A~§O 15 섹션 작성
[ ] UNKNOWN 처리:
    [ ] U-N1 PickCube yaml seed_pool → D-8 결정 (TASK_2049/2050)
    [ ] U-N2 REGIME_ID 명명 → D-9 결정 (TASK_2050/2053)
    [ ] U-N3 PickCube train_id 격차 → 사용자 확인
    [ ] U-N4 Ckpt 4 FAIL/PASS 충돌 → 사용자 확인 또는 deferred
    [ ] U-N5 ManiSkill 버전 핀 → Stage 0 requirements.txt 재확인
    [ ] U-N6 seed 끝값 정합성 → Stage 0 manifest 비교
    [ ] U-N7 np.clip dtype → TASK_2050 test 검증
    [ ] U-N8 ID baseline action_std → Probe Stage 2
    [ ] U-N9 신규 4-axis OOD 논문 → Stage 4 / R14
    [ ] U-N10 friction_mapping DEFERRED 해결 시점 → R12
[ ] 검증 (Stage 1 이후):
    [ ] test_fglc_split_integrity.py PASS
    [ ] test_fglc_no_garbage_data.py PASS
    [ ] test_fglc_ood_severity.py PASS
    [ ] test_fglc_forbidden_field_sync.py PASS
    [ ] test_fglc_r3_runner_maniskill.py PASS
    [ ] test_fglc_action_gain_collector.py (신규) PASS
[ ] 테스트: validators.py 10 reject reason + 30 gate plan 정의
[ ] 재설계: TASK_2049~2056 10헤더 작성
[ ] 재수집: probe → pilot → scaled axis별 명시 (action_gain 우선)
[ ] R3 smoke 금지: MD 작성 단계에서 r3_smoke.py 실행 금지
[ ] repair loop: axis × cause × candidate 매핑 (§J) 정의
[ ] commit: raw HDF5 / outputs/repair *.jsonl 대용량 / phase gate sentinel 제외
[ ] R3.passed 금지: D-7 사용자 명령 후에만
[ ] forbidden field 12개 보존 + leakage 0건 검증 plan
[ ] mass repair track 분리 보존 (D-6)
[ ] negative result 공시:
    [ ] mass FAIL (두 task, random policy)
    [ ] friction DEFERRED (µ_kinetic 매핑)
    [ ] noise dynamics gap ≈ 0 (의도적 specificity)
[ ] friction µ_kinetic DEFERRED Appendix 방어 문장 포함
[ ] noise specificity metric (AUROC, FPR, Σ ratio) 별도 정의 (R4 이후 실측)
[ ] D-1~D-9 결정 항목 표 작성
```

---

## §O 다음 execute 최소 작업

**D-1=(a) action_gain + D-2=(a) Codex 위임 선택 시 즉시 실행 가능 순서**:

```
Step 1. 사용자 D-1~D-9 응답 확인
        특히: D-2 Codex 위임, D-3 reset, D-4 σ_max, D-5 cause 승인, D-7 R3 권한, D-8 yaml 보강 위치

Step 2. TASK_2049_PREFLIGHT_AUDIT 실행 (Claude 직접, read-only)
        - friction 재사용 evidence 재확인 (gap, seed disjoint, forbidden=0)
        - clipping 외부 pre-clip 정책 확정
        - PickCube yaml seed_pool 보강 plan 확정 (D-8)
        - REGIME_ID 명명 결정 (D-9)
        - U-N5/N6 재확인

Step 3. TASK_2050 파일 작성 (Claude 담당)
        경로: .agent_tasks/codex_queue/TASK_2050_ACTION_GAIN_IMPL.md
        내용: §K TASK_2050 10헤더 그대로

Step 4. Codex 위임 실행 (D-2=(a) 시)
        명령:
          scripts/run_codex_task.ps1 -Mode run `
            -TaskName 2050 `
            -TaskFile .agent_tasks/codex_queue/TASK_2050_ACTION_GAIN_IMPL.md `
            -BypassSandbox
        예상 소요: 30~60 min

Step 5. Gatekeeper 6조건 검증
        - exit 0 확인
        - git diff --cached --stat (변경 파일 ≤ 5개: collector/schema/2yaml/1test)
        - 금지 경로 미수정 (visibility.py / docs/idea/)
        - test_fglc_action_gain_collector.py + test_fglc_forbidden_field_sync.py PASS
        - RESULT.md 존재
        - T3 implementation-risk-critic report PASS

Step 6. accept commit 또는 git merge --abort

Step 7. TASK_2051 probe 진입 (50ep × 2 task quarantine)
        - gain=0.7 primary (PickCube + PushCube)
        - gain=1.3 secondary (PickCube 50ep 클리핑 포화 확인)

Step 8. /agent-team-review compact (Agent D/E 중심, probe 결과)

Step 9. probe PASS → TASK_2052 Pilot 진입
        probe FAIL → §J repair loop (gain severity-up 0.7→0.5, D-5 승인)
```

**예상 산출물** (TASK_2050만):

| 파일 | 변경 | LOC |
|---|---|---|
| `src/fglc/data/collector.py` | L148-149 사이 삽입 | +3 |
| `src/fglc/data/maniskill_schema.py` | REGIME_ID + TASK_OOD_PARAMS | +10 |
| `configs/fglc/smoke_maniskill_pickcube_gain.yaml` | 신규 | ~50 |
| `configs/fglc/smoke_maniskill_pushcube_gain.yaml` | 신규 | ~50 |
| `tests/test_fglc_action_gain_collector.py` | 신규 | ~80 |

Commit: `feat(collector): action_gain OOD parameter support`

---

## Appendix A. Open UNKNOWNs 전체 목록

| ID | 내용 | 해결 단계 |
|---|---|---|
| U-N1 | PickCube yaml seed_pool block 부재 | D-8 결정 |
| U-N2 | REGIME_ID ood_latency:30 명명 비표준 | D-9 결정 |
| U-N3 | PickCube train_id manifest 250ep vs yaml 50ep 격차 | 사용자 확인 |
| U-N4 | quality_report Ckpt 4 FAIL vs STEP11_RESULT PASS 충돌 | 사용자 확인 |
| U-N5 | ManiSkill 정확한 버전 핀 | Stage 0 |
| U-N6 | PickCube/PushCube ood split seed 끝값 manifest↔dataset_stats 정합성 | Stage 0 |
| U-N7 | np.clip 후 dtype float64 cast 여부 | TASK_2050 test |
| U-N8 | PickCube ID baseline action_std (gain=1.0) | Probe Stage 2 |
| U-N9 | 2025/2026 신규 4-axis OOD baseline 논문 | Stage 4 / R14 |
| U-N10 | friction_mapping DEFERRED 해결 시점 | R12 단계 |

## Appendix B. Verification Plan

```powershell
# 1. 산출물 생성 확인
Test-Path "docs\NEXT_STAGE_DATA_COLLECTION_EXECUTION_READY_PLAN.md"   # True 필요
Test-Path "reports\next_stage_data_collection_agent_review.md"         # True 필요

# 2. 참조 파일 무결성 (수정 없음)
git status --short docs/idea/
git status --short data/fglc/
git status --short src/fglc/
git status --short scripts/fglc/
git status --short configs/fglc/
git status --short tests/

# 3. phase gate 보호
Test-Path "outputs\phase_gates\R0.passed"   # True (보존)
Test-Path "outputs\phase_gates\R1.passed"   # True (보존)
Test-Path "outputs\phase_gates\R2.passed"   # True (보존)
Test-Path "outputs\phase_gates\R3.passed"   # False (금지)

# 4. 기존 테스트 회귀 (Stage 1 이후 실행)
& ".venv\Scripts\python.exe" -m pytest -q `
    tests\test_fglc_split_integrity.py `
    tests\test_fglc_no_garbage_data.py `
    tests\test_fglc_ood_severity.py `
    tests\test_fglc_forbidden_field_sync.py `
    tests\test_fglc_r3_runner_maniskill.py
```

## Appendix C. Absolute Do-Not

```
❌ src/fglc/, scripts/fglc/, configs/fglc/, data/fglc/, tests/ 수정 (본 plan 단계)
❌ 새 collection 실행 (probe 포함, --no-save도 본 PLAN 작성 단계 금지)
❌ src/fglc/data/manifest.py::verify_ood_severity threshold 완화
❌ docs/idea/18_DATA_BENCHMARKS.md 무단 수정
❌ src/fglc/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS 무단 수정
❌ outputs/phase_gates/R3.passed 생성
❌ outputs/phase_gates/R0/R1/R2.passed 삭제
❌ raw HDF5 commit
❌ axis 사전 정답 확정 (action_gain PASS 단정 금지)
❌ negative result 숨김
❌ friction-only 완전 검증 단정
❌ delta_min / KS p-value threshold 완화
❌ noise axis 낮은 gap을 FAIL 처리 (specificity로 분리)
❌ mass FAIL 결과 숨김
❌ 문제 발견에서 종료 — 반드시 repair loop 진입
```

---

## Final Rule

```
read correct context (30 references + Phase 1 Explore 결과)
preserve scientific contract (FGLC 4축 metric + SSoT + forbidden 12개 + delta_min=0.01)
implement smallest valid step (2 MD 작성, 코드 변경 없음)
test before scaling (verification plan 4 step)
report blockers honestly (mass FAIL, friction DEFERRED, taxonomy 격차, yaml 보강 격차)
```

**판정**: PLAN_PASS — §A~§O 15 섹션 + TASK_2049~2056 + D-1~D-9 + U-N1~N10 + 30 gate + repair loop 16단계 + atomic checklist + verification plan 모두 충족. 사용자 D-1~D-9 응답 후 TASK_2049 진입 준비 완료.
