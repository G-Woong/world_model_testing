# FGLC Next-Stage Four-Axis Dataset Execution Plan

> **Status**: EXECUTION PLAN — 코드/데이터/configs/tests/data artifacts/phase-gate sentinel 변경 금지. 새 수집 금지. R3 smoke 금지. `outputs/phase_gates/R3.passed` 생성 금지. axis별 성공/실패 사전 단정 금지.
> **Branch**: `memory-redesign-2026-05-16`
> **Date**: 2026-05-24 (post commit `6f48d67` — DESIGN plan 산출 후 후속)
> **Predecessor**: `docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md` (DESIGN, commit `6f48d67`)
> **Synthesis**: `reports/four_axis_dataset_design_synthesis.md` (Agent I CONDITIONAL_ACCEPT × 5조건)
> **User Decisions (PLAN-time 확정)**:
> - **Axis 순서**: gain → latency → noise 조건부 (이전 단계 PASS 시에만 다음 axis 진입)
> - **Noise metric**: framework만 정의 (AUROC/Σ-calibration/FPR 항목 명시, 구체 threshold는 R3 smoke 단계 결정)
> - **Repair cause/candidate 신규**: 제안만 기록, 실제 추가는 axis failure 발생 시 case-by-case 사용자 승인

---

## §A — 현재 상태 요약

### A.1 DESIGN commit `6f48d67` 결과

직전 작업으로 확정된 설계 산출물:
- `docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md` (1124줄) — 4 axis 설계 골격, tier 점수, FGLC claim 매핑
- `reports/four_axis_dataset_design_synthesis.md` (467줄) — Agent A~I 9명 심사

**Agent I 최종 판정: CONDITIONAL_ACCEPT**, 5개 조건:
1. TASK_2050 (action_gain `_apply_ood` 구현, ~50 LOC) 완료
2. action_gain Pilot OOD severity PASS (state_delta_norm gap > 0.01)
3. R3 smoke (friction + action_gain) NLL finite + ood NLL > id NLL
4. mass FAIL × 2 task negative result 투명 공시
5. friction µ_kinetic ↔ joint_dry_friction DEFERRED status 유지

### A.2 Explore agent 실측 상태 (2026-05-24 기준)

| 항목 | 상태 |
|---|---|
| `_apply_ood()` (collector.py:66-89) | mass + joint_friction만 처리, gain/latency/noise 무처리 |
| eval_meta (collector.py:187-191) | 4축 `true_*` 모두 기록, 단 `ood_params.get(..., default)` fall-through로 1.0/0/0.0 |
| REGIME_ID (maniskill_schema.py) | ood_latency:30 stub만, ood_gain/ood_noise 없음 |
| TASK_OOD_PARAMS | PickCube/PushCube × {train,val,test,ood_mass_low,ood_friction_low}만 |
| FORBIDDEN_AGENT_FIELDS | 12개, 4축 `true_*` 모두 포함 — 추가 변경 불필요 |
| Test inventory | 24 `test_fglc_*.py`, gain/latency/noise 전용 test 0개 |
| `taxonomy.py` FailureCauseId | 20개, axis-specific (gain/latency/noise) cause 없음 |
| `diagnose.py` fire 함수 | 9개, axis-specific dispatcher 없음 |
| `candidates.py` RepairCandidate | 29개, policy-change family 없음 |
| `configs/fglc/` | 3 yaml, gain/latency/noise 전용 config 없음 |
| Phase gates | R0/R1/R2 PASS, R3 absent |

### A.3 기존 on-disk 데이터 인벤토리

```
data/fglc/PickCube-v1/
  raw/train_id.h5         250ep  D_x=42, D_a=8, ep_len≈50  gap_friction=0.138 PASS
  raw/val_id.h5            50ep
  raw/test_id.h5           50ep
  raw/ood_mass_low.h5      50ep  gap=0.0038 BLOCKED
  raw/ood_friction_low.h5  50ep  gap=0.138 PASS
  manifest.json            seed_pool [42~650), git_sha=3c1806ed, ManiSkill 3.0.1
  dataset_stats.json       D_x=42, D_a=8
  quality_report.json      Ckpt4=FAIL(ood_sev mass), friction_mapping=DEFERRED

data/fglc/PushCube-v1/
  raw/train_id.h5         500ep  D_x=35, D_a=8, ep_len≈50  gap_friction=0.124 PASS
  raw/val_id.h5           100ep
  raw/test_id.h5          100ep
  raw/ood_mass_low.h5     100ep  gap=0.008 BLOCKED
  raw/ood_friction_low.h5 100ep  gap=0.124 PASS
  manifest.json            seed_pool [1042~1999)
```

**총 기존 데이터**: PickCube 450ep + PushCube 900ep = 1350ep (friction/mass 포함)

### A.4 핵심 구현 격차

| 격차 | 위치 | 추가 LOC | BACKBONE 등급 |
|---|---|---|---|
| action_gain `_apply_ood` 분기 | collector.py L73-89 직후 | ~10 | 등급 3 (코드, 수정 가능) |
| latency FIFO buffer + commanded/executed | collector.py episode loop | ~25 | 등급 3 |
| noise injection + RNG seed | collector.py `_flat_obs` 직후 | ~8 | 등급 3 |
| TASK_OOD_PARAMS 3 axis 확장 | maniskill_schema.py | ~10 | 등급 3 |
| REGIME_ID 2개 추가 (gain/noise) | maniskill_schema.py | ~5 | 등급 3 |
| config yaml 3 axis × 2 task | configs/fglc/ | ~6 파일 | 등급 3 |
| 신규 test 9~12개 | tests/ | ~300 | 등급 3 |
| repair taxonomy 4 cause (제안) | taxonomy.py | ~20 | **등급 1 (사용자 승인 필요)** |
| repair candidate policy-change family | candidates.py | ~40 | **등급 1** |

**총 구현 격차**: ~105 LOC (코드) + ~300 LOC (test) + 6 config files

---

## §B — 다음 단계 목표

### B.1 최우선 목표 (action_gain)

1. friction 기존 데이터 (PickCube 450ep + PushCube 900ep) 재활용 확인
2. action_gain TASK_2050 구현 (~50 LOC, Codex 위임 권장)
3. action_gain probe 50ep × {gain=0.7, gain=1.3} × 2 task
4. action_gain Pilot 350ep × 2 task → 30 gate 통과
5. action_gain Scaled 1300ep × 2 task → R3 smoke 두 번째 axis 등록
6. R3 smoke: friction + action_gain → NLL finite + ood_nll > id_nll

### B.2 조건부 확장 순서

```
action_gain Scaled PASS
  → latency TASK_2053 구현 (~40 LOC)
    → latency Pilot PASS
      → noise TASK_2054 구현 (~15 LOC)
        → noise Pilot + specificity metric PASS
```

각 단계는 이전 단계 **Pilot 이상 PASS** 시에만 진입. Probe 단계 FAIL은 repair loop 후 재probe.

### B.3 noise의 특별 지위

noise는 dynamics OOD가 **아니다**. noise axis의 목적은:
- FGLC β-gate가 observation noise를 dynamics shift로 오인하지 않음을 검증 (specificity)
- state_delta_norm gap ≈ 0 이 **의도된 결과** (dynamics 변화 없음)
- 검증 metric: AUROC < 0.65 (falsification AUROC), Σ calibration check, β-gate false positive rate

### B.4 mass의 분리

mass는 본 R3 주력에서 제외한다. 이유: contact_rate=0%에서 F=ma 물리 경로 차단 (PickCube gap=0.0038, PushCube gap=0.008 < delta_min=0.01). mass는 별도 contact-rich policy repair track으로 보존 — scripted/expert policy를 통한 contact_rate 향상이 선행 조건.

### B.5 R5/R6 Stage 3 gate 목표

`docs/idea/12_TRAINING_STAGES.md` Stage 3 gate: **최소 2개 OOD 축**에서 TD-MPC2 baseline 초과.
- 최소 구성: friction(기존) + action_gain → 2 axes
- 권장 구성: + latency → 3 axes
- robust 구성: + noise specificity → 4 axes (FGLC의 4개 독립 시나리오 완전 커버)

---

## §C — friction/action_gain/latency/noise 역할 정리

### C.1 friction (기존 PASS — 재활용)

**FGLC claim 연결**:
```
τ_eff = τ_motor - 5.0 × sign(qvel)   [매 step, 접촉 무관]
qvel 변화 → z_t의 velocity group 오류 → ρ_t 편차 → β_t 발화
```

**현재 상태**:
- PickCube gap=0.138 PASS (delta_min=0.01의 13.8×), PushCube gap=0.124 PASS
- 30 gate 중 H1-H21 PASS (Ckpt4 FAIL은 mass에 의한 것, friction 개별은 PASS)
- quality_report.json: `friction_mapping=DEFERRED` (µ_kinetic ↔ joint_dry_friction 단위 매핑 미해결)

**EXECUTION 행동**: 재수집 불필요. R3 smoke 첫 번째 axis로 등록.

**위험**: µ_kinetic 단위 매핑 DEFERRED → reviewer "unrealistic setting" 공격 가능. 논문 Appendix에 `joint_dry_friction=5.0 N·m/rad`과 µ_kinetic 간 변환 공식 문서화로 선제 방어.

**신규 LOC**: 0 (단, µ_kinetic mapping ledger 작성 시 ~20 LOC + 신규 수집 필요)

**repair 경로**: friction gap 재측정 후 < 0.01이면 `OOD_TOO_EASY` → `OOD_TOO_EASY_shift_strength_2x`

---

### C.2 action_gain (PRIMARY — 다음 EXECUTION 최우선)

**FGLC claim 연결**:
```
a_executed = gain × a_commanded         [step 전 변환]
state_{t+1} = f(state_t, a_executed)   [환경 dynamics]
μ_t = f_θ(z_t, a_commanded, h_t)       [WM은 a_commanded 기반 예측]
ρ_t = Σ_t^{-1/2}(z_{t+1} - μ_t)       [systematic mismatch]
```
이것이 FGLC "wrong-dynamics-hypothesis persistence"의 가장 직접적인 예시.

**구현 필요**:
- `collector.py` L89 직후에 action_gain 분기 (~10 LOC):
  ```python
  if "action_gain" in ood_params:
      gain = float(ood_params["action_gain"])
      a = np.clip(a * gain, env.action_space.low, env.action_space.high)
  ```
  **주의**: clipping은 `env.step(a)` **전** 적용 (clipping 후 적용 = saturation 자연 발생, high-gain=1.3 시 신호 약화 가능)
- `maniskill_schema.py` TASK_OOD_PARAMS에 `ood_gain_low` / `ood_gain_high` entry 추가
- REGIME_ID에 `ood_gain_low:40` 추가
- config 2개: `smoke_maniskill_pickcube_gain.yaml`, `smoke_maniskill_pushcube_gain.yaml`
- test: `tests/test_fglc_action_gain_collector.py` (신규)

**gain 후보**:
- gain=0.7 (PRIMARY — low-gain, saturation 없음, 명확한 systematic mismatch)
- gain=1.3 (SECONDARY — high-gain, ManiSkill env.step 내부 clipping 영향 확인 필요)

**probe success criteria**:
- state_delta_norm gap > 0.005 (probe 단계 lenient), > 0.01 (Pilot)
- KS p < 0.1 (probe), < 0.05 (Pilot)
- OOD param 적용 evidence: `eval_meta["true_action_gain"]` ≠ 1.0

**failure → repair**:
- gap < 0.005 → `OOD_AXIS_GAIN_UNCOVERED` (신규 cause, 사용자 승인 후 추가) → gain=0.7→0.5
- clipping saturation → gain 범위 재설계 (0.6, 1.2)

---

### C.3 latency (SECONDARY — action_gain Scaled PASS 후 진입)

**FGLC claim 연결**:
```
a_executed_t = a_commanded_{t-d}        [d-step delay]
μ_t = f_θ(z_t, a_commanded_t, h_t)     [WM은 현재 action 기반 예측]
실제: d-step 이전 action 적용 → z_{t+1} ≠ μ_t
→ phase error 누적: episode 후반부 mismatch 증가
→ temporal latent group의 d-step shifted pattern
```

**구현 필요**:
- `collector.py` episode loop에 `deque(maxlen=d)` FIFO buffer 추가 (~25 LOC)
- **reset 정책**: zero-fill 권장 (episode 시작 시 d개 zero action push → causality clean)
- **commanded/executed 분리**:
  - `episodes[i]["action"]` = executed_action (실제 적용, inference path)
  - `eval_metas[i]["commanded_actions"]` = commanded list (eval-only, 선택적)
- `true_latency`는 collector.py L189 그대로 eval_only에만 유지

**delay 후보**: d=3 (PRIMARY), d=5, d=8 (SECONDARY)

**probe success criteria**:
- state_delta_norm gap > 0.01 (d=5 이상에서 기대값 ≈ 0.05~0.15)
- episode 후반부 gap > 전반부 gap (누적 phase error 관측)

**UNKNOWN**: latency buffer가 `_apply_ood` 내부에 있으면 안 됨 (action flow 변경이지 state 변경이 아님). 별도 episode loop 수준에서 구현 필요.

---

### C.4 noise (SECONDARY/CALIBRATION — latency Pilot PASS 후 진입)

**FGLC claim 연결**:
```
obs_noisy = _flat_obs(obs) + N(0, σ²I)   [observation noise injection]
dynamics: state_{t+1} = f(state_t, a_t)  [변화 없음]
목적: Σ_t calibration이 올바르면 β_t가 noise를 dynamics shift로 오인하지 않음
검증: β_t false positive rate (ID data에 noise 주입 → β_t 발화율 < 0.05)
```

**구현 필요**:
- `collector.py` `_flat_obs` 직후 noise injection (~8 LOC):
  ```python
  if "noise_sigma" in ood_params:
      sigma = float(ood_params["noise_sigma"])
      rng = np.random.default_rng(seed)
      flat_obs = flat_obs + rng.normal(0, sigma, flat_obs.shape).astype(np.float32)
  ```
- σ upper bound guard: σ > 0.15 → warning, σ > 0.2 → BLOCKED (probe만 허용)
- per-episode deterministic RNG: `np.random.default_rng(seed)` → reproducibility

**검증 기준 (별도 metric)**:
- state_delta_norm gap: 기대값 ≈ 0 (dynamics 변화 없음) → delta_min 기준 **미적용**
- AUROC < 0.65: β-gate가 noise를 dynamics shift로 오인하지 않음 (의도된 낮은 값)
- Σ calibration: Σ̂_t / Σ_true ratio → 1.0 근처 (올바른 calibration)
- β-gate false positive rate < 0.05 (σ=0.1 기준)

**sigma 후보**: σ=0.05 (conservative), σ=0.1 (PRIMARY), σ=0.2 (severe, probe 단계만)

**noise는 FAIL이 아닌 SPECIFICITY TEST**: AUROC < 0.65가 올바른 결과이며, ≥ 0.70이면 β-gate oversensitivity → `OBS_NOISE_SIGMA_MISMATCH` (신규 cause) → Σ recalibration.

---

## §D — 자원 계산 기반 수집량 계획

### D.1 단위 계산

| Task | D_x | D_a | ep_len | bytes/transition | KB/episode |
|---|---|---|---|---|---|
| PickCube-v1 | 42 | 8 | 50 | (42+8+1+1)×4 = 208 B | ≈11.5 KB |
| PushCube-v1 | 35 | 8 | 50 | (35+8+1+1)×4 = 180 B | ≈10.0 KB |

### D.2 Stage × Axis × Task 수집량 매트릭스

| Stage | ep/split (5 splits) | total ep | PickCube disk | PushCube disk | wall clock |
|---|---|---|---|---|---|
| Probe | 10×5 = 50 | 50 | 0.6 MB | 0.5 MB | 1~2분 |
| Pilot | 50/100/100/50/50 | 350 | 4.0 MB | 3.5 MB | 5~10분 |
| Scaled | 100/500/500/100/100 | 1300 | 15 MB | 13 MB | 15~30분 |
| Robust | 200/1000/1000/200/200 | 2600 | 30 MB | 26 MB | 30~60분 |

**3 axis × 2 task × Scaled** = 6 수집:
- 총 에피소드: 6 × 1300 = 7800 ep
- 총 디스크: ~168 MB (기존 ~6 MB 포함 총 ~174 MB)
- 총 수집 시간: ~3 hour (병렬 불가, 순차 axis별)

### D.3 단계별 최소/권장/robust 구성

| 구성 | 내용 | 신규 ep | 신규 disk | 시간 |
|---|---|---|---|---|
| 최소 (R3-readiness) | friction 재활용 + action_gain Pilot × 2 task | 700ep | ~8 MB | 20분 |
| 권장 (R3 + R4) | + action_gain Scaled × 2 task | 2600ep | ~30 MB | 1.5 hour |
| 추천 (R5/R6 기준) | + latency Pilot × 2 task | 3300ep | ~38 MB | 2.5 hour |
| 논문급 (R9 ablation) | + latency Scaled + noise Pilot × 2 task | 6500ep | ~80 MB | 4 hour |
| robust (다중 seed) | 전체 × 2 seed | 13000ep | ~160 MB | 8 hour |

### D.4 VRAM 안전성 분석 (RTX 4060 8GB)

| 구성 | VRAM 추정 | 안전 여부 |
|---|---|---|
| R3 base WM (batch=16, T=16, K=8, d=32, h=256) | ~400 MB | ✅ 20× 여유 |
| R4 falsification gate 추가 | ~600 MB | ✅ 13× 여유 |
| R5 causal attention (sparse, K heads) | ~800 MB | ✅ 10× 여유 |
| R7 MPPI rollout (n=512) | ~2 GB | ✅ 4× 여유 |
| R9 ablation grid (4 seed × 11 family) | ~6 GB | ⚠ 한계 근접 → sequential seed |
| R11 RGB-D 확장 (T=64, 추후) | ~6 GB+ | ⚠ 별도 검토 필요 |

**rule**: batch × T × K × d × 4 bytes (float32) 곱이 250M float32(≈1 GB) 초과 시 OOM 위험. 사전 `torch.cuda.memory_summary()` 확인.

---

## §E — 단계별 수집 절차

### Stage 0 — Preflight (코드 변경 없음, ~1~2 hour)

**목적**: EXECUTION 진입 전 환경 및 격차 최종 점검

**체크리스트**:
- [ ] DESIGN commit `6f48d67` 무수정 확인: `git diff HEAD~1 -- docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md`
- [ ] friction 기존 데이터 재사용 가능성: quality_report.json Ckpt 0~3 PASS 재확인
- [ ] mass FAIL evidence 확인: gap=0.0038/0.008 < delta_min=0.01, negative result 공시 준비
- [ ] action_gain 구현 위치 확인: collector.py L89 직후, `_apply_ood()` 종료 직전
- [ ] latency buffer 정책 결정: zero-fill 권장 (사용자 D-3 확인)
- [ ] noise injection 위치: `_flat_obs()` 직후 (L50-57 기반 확장)
- [ ] FORBIDDEN_AGENT_FIELDS 12개 ↔ 3 axis 추가 후 leakage 검토: `true_action_gain, true_latency, true_noise_sigma` 이미 포함 → 변경 불필요
- [ ] quality_report.json `friction_mapping=DEFERRED` 유지 결정
- [ ] phase gate 상태: `outputs/phase_gates/R0.passed`, `R1.passed`, `R2.passed` 존재 / `R3.passed` 부재

**산출**: §A 현황표 검증 완료 + 사용자 결정 D-1~D-7 정리 자료

---

### Stage 1 — Probe (axis별 50ep, quarantine)

**목적**: 구현 직후 최소 가능성 확인 (shape, OOD param 적용, gap > 0.005)

**방법**: `scripts/fglc/collect_maniskill.py --quarantine` (본 수집은 data/fglc/ 외부에 임시 저장)

**axis별 probe 파라미터**:
- friction: SKIP (기존 데이터 재사용)
- action_gain: 50ep × {gain=0.7, gain=1.3} × 2 task
- latency: 50ep × {d=3, d=5, d=8} × 2 task
- noise: 50ep × {σ=0.05, σ=0.1, σ=0.2} × 2 task

**probe 성공 조건** (axis별):
- [ ] shape consistency: D_x / D_a 일치
- [ ] reward scalar 정상
- [ ] done/truncated valid
- [ ] state_delta_norm gap > 0.005 (lenient, Pilot에서 0.01 강화)
- [ ] OOD param 적용 evidence: `eval_meta["true_*"]` ≠ default (1.0/0/0.0)
- [ ] AttributeError 없음 (ManiSkill API 호환)
- [ ] forbidden field guard 통과 (금지 12개 미포함)

**실패 분기**:
- gap < 0.005 → `diagnose.py` 호출 → axis-specific cause → repair candidate → 재probe
- AttributeError → ManiSkill API mismatch → **BLOCKED** + version 재확인
- forbidden field detected → **즉시 abort** (leakage 규칙)
- noise σ=0.2에서 dynamics learning destruction sign → σ 상한 0.15로 하향

---

### Stage 2 — Pilot (axis별 350ep = 50+100+100+50+50 per 5 splits)

**목적**: 30개 quality gate 전체 통과 + OOD severity PASS

**성공 조건** (§F 30 gate 모두):
- 특히 H22 (ood_sev): gain/latency는 gap > 0.01, noise는 AUROC < 0.65
- H6 accept_rate > 99%
- H14-H16 split leakage 0건
- H27-H28 forbidden field 0건

**실패 분기**:
- H22 FAIL (gain/latency) → `OOD_AXIS_*_UNCOVERED` (신규 cause) → severity 증가 → repair loop
- H22 FAIL (noise, AUROC ≥ 0.70) → `OBS_NOISE_SIGMA_MISMATCH` → Σ recalibration
- H6 FAIL → `DATA_TOO_SMALL` or `IMPLEMENTATION_BUG_SUSPECTED` → reject reason 분석
- H14-H16 FAIL → `DATA_BAD_SPLIT` → seed pool 재생성

---

### Stage 3 — Scaled (axis별 1300ep = 100+500+500+100+100)

**목적**: Pilot gate 재PASS + per-dim Cohen's d > 0.3 + KS p < 0.01 + R3 smoke 진입 조건 충족

**추가 조건 (Pilot 대비 강화)**:
- per-dim Cohen's d > 0.3인 dim 수: friction qvel 9-17 기준 ≥ 5 dims
- KS p < 0.01 (Pilot의 p < 0.05 강화)
- CI95 < 50% of mean gap

**R3 smoke 진입 조건**:
- [ ] friction Scaled OK (기존 재확인) + action_gain Scaled PASS
- [ ] `scripts/fglc/r3_smoke.py --dry-run`: shape mismatch 없음
- [ ] 1-epoch smoke: NLL finite + ood_nll > id_nll (friction + action_gain)
- [ ] metrics.json artifact 생성
- [ ] repair_loop ledger jsonl ≥ 1줄

---

### Stage 4 — Robust (axis별 2600ep = 200+1000+1000+200+200, multi-seed)

**목적**: 논문급 재현성 + multi-seed 일관성 검증

**조건**:
- 2 seed 독립 Scaled 수집 → gap 차이 < 20%
- multi-seed 결합 후 KS p < 0.001
- novelty reviewer attack 시뮬레이션 통과 (Agent G 호출)

**본 PLAN 범위**: Stage 4는 R5/R6 진입 후 결정. 본 PLAN은 Stage 3까지가 primary target.

---

## §F — 품질 gate checklist (25개 + DESIGN §G 30개 매핑)

| # | Gate | DESIGN H# | 측정 방법 |
|---|---|---|---|
| 1 | schema consistency | H1 | validators reject reason `SCHEMA_MISMATCH` 0건 |
| 2 | state/action dim consistency | H1 | D_x/D_a == observed |
| 3 | dtype numeric (float32/int32) | H2 | np.isfinite 전수 통과 |
| 4 | reward scalar 정상 | H3 | reward ∈ (-inf, +inf), no NaN |
| 5 | done/truncated valid | H4 | bool dtype, 마지막 step True |
| 6 | accept rate > 99% | H6 | n_accepted / (n_accepted + n_rejected) |
| 7 | episode 최소 길이 > 10 | H7 | validators min_episode_len 통과 |
| 8 | hash 중복 0건 | H8 | seen_state_hashes 중복 검사 |
| 9 | 관측 값 범위 정상 | H9 | 각 dim mean ∈ [-10, 10], std > 0 |
| 10 | action 범위 [-1,1] 준수 | H10 | env.action_space 범위 내 |
| 11 | forbidden field 미포함 (inference) | H11 | FORBIDDEN_AGENT_FIELDS 0건 |
| 12 | eval_meta 분리 확인 | H12 | episodes 내 true_* 0건 |
| 13 | seed pool 범위 disjoint | H13 | train/val/test/ood* seed 비중복 |
| 14 | split leakage 0건 | H14 | trajectory hash cross-split 비중복 |
| 15 | regime_id leakage 0건 | H15 | episodes 내 regime_id 0건 |
| 16 | ood_type leakage 0건 | H16 | episodes 내 ood_type 0건 |
| 17 | manifest git_sha 기록 | H17 | manifest.json git_sha 존재 |
| 18 | manifest seed_pool 명시 | H18 | manifest.json seed_pool 리스트 존재 |
| 19 | collection wall_clock 기록 | H19 | stats.wall_clock_seconds 존재 |
| 20 | OOD param 적용 evidence | H20 | eval_meta true_* ≠ default |
| 21 | repair ledger 기록 | H21 | outputs/repair/loop_*.jsonl 19 key 충족 |
| 22 | OOD severity (axis별 기준) | H22 | gain/latency: gap > 0.01; noise: AUROC < 0.65 |
| 23 | 신규 axis test green | H23 | test_fglc_*_collector.py PASS |
| 24 | r3_smoke --dry-run OK | H24 | shape mismatch 없음 |
| 25 | 1-epoch smoke NLL finite | H25 | metrics.json NLL < ∞ |

**DESIGN §G H26-H30** (추가):

| # | Gate | 측정 |
|---|---|---|
| 26 | CI95 < 50% of mean gap | multi-seed bootstrap |
| 27 | forbidden field sync test | test_fglc_forbidden_field_sync.py green |
| 28 | split integrity test | test_fglc_split_integrity.py green |
| 29 | ood_severity test | test_fglc_ood_severity.py green |
| 30 | r3_runner test | test_fglc_r3_runner_maniskill.py green |

---

## §G — axis별 특수 checkpoint

### G.1 friction 특수 checkpoint

**µ_kinetic ↔ joint_dry_friction 매핑 (DEFERRED 유지)**:
- SSoT (`18_DATA_BENCHMARKS.md`): µ_kinetic ∈ {0.3, 0.7, 1.5}
- 코드: `j.set_friction(5.0)` (단위: N·m/rad × joint angle)
- 물리적 관계: µ_kinetic과 joint_dry_friction은 다른 모델. 완전 동일시 불가.
- DEFERRED 이유: R4 falsification gate 단계에서 qvel signal 강도만 중요, 단위 정확성은 논문 Appendix에서 해결
- ledger에 `friction_mapping=DEFERRED` 계속 유지, 논문 시 "Implementation Details" 섹션에 명시

**qvel dim 분석**:
- PickCube D_x=42에서 qvel dims 9-17이 friction에 민감 (7 DOF Panda + gripper)
- per-dim Cohen's d > 0.3인 dim 수 ≥ 5 기대

### G.2 action_gain 특수 checkpoint

**clipping 위치 결정** (중요):
- **권장 패턴**: `a = np.clip(a * gain, env.action_space.low, env.action_space.high)` → env.step(a)
- **이유**: env.step 내부에서 추가 clip이 발생할 수 있으므로, 외부 clip 후 적용하면 effective gain이 명확
- gain=1.3 + env.action_space = [-1,1]: saturation 발생 → effective gain 감소 → paper에 saturation 분석 포함 필요
- gain=0.7: saturation 없음 → 명확한 systematic mismatch → PRIMARY

**`true_action_gain` 기록**:
- collector.py L191: `"true_action_gain": float(config.ood_params.get("action_gain", 1.0))` → eval_only 유지 (변경 불필요)

**신규 validator 추가 권장** (Codex 위임):
- action_std 감소 검증: `a_std_id ≈ 0.577`, `a_std_gain07 ≈ 0.404` (random policy + gain=0.7)
- 이 validator는 TASK_2050 내 `test_fglc_action_gain_collector.py`에 포함

### G.3 latency 특수 checkpoint

**FIFO buffer 구현 위치**: `_apply_ood()` 외부, episode loop 수준. `_apply_ood`는 env.reset() 후 state-level 설정만.

**zero-fill reset 정책**:
```python
# episode 시작 전
buffer = deque([np.zeros(D_a, dtype=np.float32)] * delay, maxlen=delay)
# episode loop 내
buffer.append(a_commanded)
a_executed = buffer[0]  # popleft equivalent
```
이유: zero-fill → episode 시작 d step 동안 zero action 실행 → causality clean, phase error 명확

**commanded/executed 분리**:
- `episodes[i]["action"]` = `a_executed` (inference path가 보는 action)
- `eval_metas[i]` 내 `"commanded_actions"` 리스트 (선택적, eval-only)
- `true_latency`는 L189 그대로 유지

**누적 phase error 관측**:
- episode 전반부 (step 0~24) gap vs 후반부 (step 25~49) gap 비교
- latency=5 시 후반부 gap > 전반부 gap이 기대 패턴

### G.4 noise 특수 checkpoint

**injection 위치**: `_flat_obs(obs)` 반환값에 직접 적용
```python
flat = _flat_obs(obs)
if "noise_sigma" in ood_params:
    rng = np.random.default_rng(episode_seed)
    flat = flat + rng.normal(0, ood_params["noise_sigma"], flat.shape).astype(np.float32)
states.append(flat)
```

**per-episode deterministic RNG**: seed = collection seed로 결정 → `episode_seed = seed + step_idx` 또는 `seed` 직접 사용

**σ upper bound guard 구현**:
```python
if ood_params.get("noise_sigma", 0.0) > 0.2:
    raise ValueError("noise_sigma > 0.2 blocked: dynamics learning destruction risk")
elif ood_params.get("noise_sigma", 0.0) > 0.15:
    warnings.warn("noise_sigma > 0.15: proceed with caution")
```

**specificity metric framework** (threshold는 R3 smoke 단계에서 결정):
- AUROC(β_t 발화, OOD label): 기대값 < 0.65
- Σ̂_t / Σ_true ratio: R4 gate 후 측정 가능
- β-gate false positive rate (ID+noise): 기대값 < 0.05

---

## §H — Team agent 검증 계획

### H.1 Agent × Stage × Axis 호출 매트릭스

| Agent | Stage 0 | Stage 1 (probe) | Stage 2 (pilot) | Stage 3 (scaled) | Stage 4 (robust) | R3 smoke |
|---|---|---|---|---|---|---|
| A (axis-impl) | ✅ pre-TASK_2050 | — | — | — | — | — |
| B (data-quality) | — | ✅ post-probe | ✅ post-pilot | ✅ post-scaled | ✅ post-robust | — |
| C (split-leakage) | — | — | ✅ post-pilot | ✅ post-scaled | ✅ post-robust | — |
| D (ood-severity) | — | ✅ post-probe | ✅ post-pilot | ✅ post-scaled | ✅ post-robust | — |
| E (dynamics-forensics) | — | ✅ post-probe | ✅ if D fails | ✅ if D fails | — | — |
| F (claim-metric) | — | — | ✅ post-pilot | ✅ post-scaled | — | ✅ post-smoke |
| G (novelty) | — | — | — | ✅ post-scaled | ✅ post-robust | — |
| H (resource) | ✅ pre-Stage 3 | — | — | ✅ pre-Stage 4 | — | — |
| I (synthesis) | ✅ post-Stage 0 | ✅ post-Stage 1 | ✅ post-Stage 2 | ✅ post-Stage 3 | ✅ post-Stage 4 | ✅ post-smoke |

### H.2 호출 명령

```powershell
# Stage 0/1/2 개별 gate (compact mode)
/agent-team-review compact

# Stage 3/4 + R3 smoke 종합 (deep mode, T4 트리거)
/agent-team-review deep

# axis별 PASS/FAIL 결정 직전 (Agent I 주재)
/war-room
```

### H.3 산출 경로

- 개별 report: `docs/orchestration/agent_reports/2026-05/<agent>_<axis>_<stage>_R1.md`
- synthesis: `docs/orchestration/agent_reports/synthesis/2026-05/four_axis_<axis>_<stage>_R1.md`

---

## §I — repair loop 및 재탐색/재수집 전략

### I.1 16단계 repair loop

```
1.  metric 수집: Stage 1/2/3 post-collection metrics 기록
2.  diagnose.py 입력: scripts/fglc/repair_loop.py diagnose --metrics <path>
3.  FailureCauseId 매핑: 20개 기존 + 신규 4개 제안(사용자 승인 후)
4.  candidates.py 후보 생성: 29개 기존 + policy-change family 제안
5.  ranker.py 우선순위: cost_minutes × risk / expected_signal 기반
6.  수집 조건/config 수정: 사용자 승인 필요 if config/schema 변경
7.  재수집: probe → pilot → scaled 회귀 (axis별 STOP: max 3 iter)
8.  compare.py before/after: gap_before vs gap_after
9.  ledger 19 REQUIRED_KEYS 기록: timestamp, iter, diagnosed_cause 등
10. ledger JSONL append: outputs/repair/loop_<axis>_<YYYY-MM-DD>.jsonl
11. agent team re-review: Agent B/D/I 재호출
12. PASS → 다음 stage 진입
13. FAIL → step 1 회귀 (max 3 iter 내)
14. INCONCLUSIVE → USER_ESCALATION (ledger next_action 기록)
15. R3 smoke 진입 조건 충족 시 r3_smoke.py 실행
16. commit: raw HDF5 제외, ledger jsonl 보존, sentinel 미생성
```

### I.2 axis × failure cause × repair candidate 매핑

| 시나리오 | 기존 FailureCauseId | 신규 cause (제안) | 기존 candidate | 신규 candidate (제안) |
|---|---|---|---|---|
| friction gap < 0.01 | `OOD_TOO_EASY` | — | `OOD_TOO_EASY_shift_strength_2x` | µ_kinetic 매핑 추가 |
| action_gain gap < 0.005 (probe) | — | `OOD_AXIS_GAIN_UNCOVERED` | — | `OOD_AXIS_GAIN_severity_up` (gain=0.7→0.5) |
| action_gain gap < 0.01 (pilot) | — | `OOD_AXIS_GAIN_UNCOVERED` | — | gain=0.5 재수집 |
| latency gap < 0.01 | — | `OOD_AXIS_LATENCY_UNCOVERED` | — | `OOD_AXIS_LATENCY_delay_up` (d=8→12) |
| noise AUROC ≥ 0.70 (oversensitivity) | `EVAL_NOISE_HIGH`와 혼재 위험 | `OBS_NOISE_SIGMA_MISMATCH` | `EVAL_NOISE_HIGH_more_seeds` | Σ_recalibration |
| 모든 axis random policy invariant | `OOD_TOO_HARD` (mass용) | `OOD_INVISIBLE_TO_RANDOM_POLICY` | `OOD_TOO_HARD_severity_down_mass` | scripted/expert policy |
| validators reject > 5% | `DATA_TOO_SMALL` | — | `DATA_TOO_SMALL_episode_x2` | — |
| R3 NLL = inf | `IMPLEMENTATION_BUG_SUSPECTED` | — | `IMPLEMENTATION_BUG_manual_blocker` | — |

> **신규 cause/candidate 4개는 BACKBONE 등급 1 (사용자 승인 필요)**. 본 PLAN에서는 제안만 기록.
> 실제 추가 시: taxonomy.py FailureCauseId enum 확장 + candidates.py CANDIDATE_TABLE 확장 + test 재실행.

### I.3 repair loop STOP 조건

- `--max-iter=3`: 3회 후 USER_ESCALATION
- `--max-consecutive-inconclusive=2`: 2회 연속 inconclusive → stop
- `--max-wall-clock-minutes=60`: stage별 60분 한도
- `target_reached`: gap > 0.01 + KS p < 0.05 + 30 gate PASS
- `hook_blocked`: pre-commit hook 또는 forbidden field guard → USER_ESCALATION

---

## §J — TASK 분해안

### TASK 2049 — Preflight Audit (Claude 직접)

```text
TASK_NAME: TASK_2049_PREFLIGHT_AUDIT
BACKGROUND: DESIGN commit 6f48d67 후 EXECUTION 진입 직전. friction 재사용 가능성 + 3 axis 구현 격차 + ManiSkill 3.0.1 version 재확인.
GOAL: Stage 0 checklist 9개 통과 + 사용자 결정 D-1~D-7 정리
FILES_ALLOWED: docs/NEXT_STAGE_FOUR_AXIS_DATA_COLLECTION_EXECUTION_PLAN.md (편집), reports/next_stage_four_axis_agent_synthesis.md (편집)
FILES_FORBIDDEN: src/, scripts/, configs/, data/, outputs/, docs/idea/, .claude/, tests/
REQUIRED_IMPLEMENTATION: read-only audit + MD 작성
REQUIRED_TESTS: git status로 다른 파일 수정 없음 확인
ACCEPTANCE_CRITERIA: Stage 0 9개 체크 모두 통과 + D-1~D-7 정리 완료
COMMIT_MESSAGE: docs(data): next-stage four-axis execution plan §A preflight
STOP_CONDITION: ManiSkill API 신규 격차 발견 시 BLOCKED 기록 후 사용자 escalation
```

### TASK 2050 — action_gain Implementation (Codex 위임 권장)

```text
TASK_NAME: TASK_2050_ACTION_GAIN_IMPL
BACKGROUND: collector.py:89 _apply_ood 직후 action_gain 분기 추가 + maniskill_schema.py TASK_OOD_PARAMS 확장 + config + integration test
GOAL: action_gain OOD parameter가 collect_episodes()에서 실제 적용되도록 ~50 LOC 추가
FILES_ALLOWED: src/fglc/data/collector.py, src/fglc/data/maniskill_schema.py, configs/fglc/smoke_maniskill_pickcube_gain.yaml (신규), configs/fglc/smoke_maniskill_pushcube_gain.yaml (신규), tests/test_fglc_action_gain_collector.py (신규)
FILES_FORBIDDEN: src/fglc/schemas/visibility.py, docs/idea/, .claude/, src/fglc/repair/
REQUIRED_IMPLEMENTATION:
  - collector.py: episode loop 내 a = clip(a * gain, ...) 적용 ~10 LOC
  - maniskill_schema.py: TASK_OOD_PARAMS에 ood_gain_low/high entry + REGIME_ID ood_gain_low:40
  - config 2개: gain=0.7 (low), gain=1.3 (high)
  - test: gain 적용 evidence + true_action_gain eval_only 검증 + forbidden field guard
REQUIRED_TESTS: test_fglc_action_gain_collector.py + test_fglc_forbidden_field_sync.py PASS
ACCEPTANCE_CRITERIA: 1-ep smoke gain 적용 확인 + eval_meta true_action_gain ≠ 1.0 + forbidden field 0건
COMMIT_MESSAGE: feat(collector): action_gain OOD parameter support
STOP_CONDITION: clipping 위치 불명 시 BLOCKED (env.step 전 vs 내부 결정 필요)
RELATED_AGENT_REPORT_IDS: T3 implementation-risk-critic (post-Codex merge 전 필수)
```

### TASK 2051 — action_gain Probe Execution

```text
TASK_NAME: TASK_2051_GAIN_PROBE
BACKGROUND: TASK_2050 완료 후 50ep × {gain=0.7, gain=1.3} × 2 task probe
GOAL: probe 결과로 Pilot 진입 PASS/FAIL 결정
FILES_ALLOWED: data/fglc/PickCube-v1/probe/, data/fglc/PushCube-v1/probe/ (quarantine), docs/orchestration/agent_reports/2026-05/
FILES_FORBIDDEN: src/, configs/, outputs/phase_gates/
REQUIRED_IMPLEMENTATION: collect_maniskill.py --split ood_gain_low --quarantine
REQUIRED_TESTS: gate H1-H8, H20, H22 (gap > 0.005) 통과
ACCEPTANCE_CRITERIA: gap > 0.005 + KS p < 0.1 + OOD param 적용 evidence
COMMIT_MESSAGE: data(probe): action_gain probe collection PickCube/PushCube
STOP_CONDITION: gap < 0.005 → repair loop 진입 (gain 확대 0.7→0.5)
```

### TASK 2052 — action_gain Pilot/Scaled

```text
TASK_NAME: TASK_2052_GAIN_PILOT_SCALED
BACKGROUND: probe PASS 후 Pilot(350ep × 2 task) + Scaled(1300ep × 2 task)
GOAL: action_gain Scaled PASS → R3 smoke 두 번째 axis 등록 가능
FILES_ALLOWED: data/fglc/PickCube-v1/pilot/, data/fglc/PushCube-v1/pilot/, data/fglc/*/manifest.json (gain split 추가)
FILES_FORBIDDEN: outputs/phase_gates/R3.passed (절대 생성 금지)
REQUIRED_IMPLEMENTATION: Pilot → 30 gate → Scaled → 30 gate (Cohen's d > 0.3)
REQUIRED_TESTS: test_fglc_split_integrity.py + test_fglc_ood_severity.py
ACCEPTANCE_CRITERIA: gap > 0.01 + KS p < 0.05 + 30 gate PASS
COMMIT_MESSAGE: data(scaled): action_gain pilot+scaled PickCube/PushCube
STOP_CONDITION: Pilot FAIL → repair loop → gain 확대 → re-probe
```

### TASK 2053 — latency Implementation/Probe (action_gain PASS 후 진입)

```text
TASK_NAME: TASK_2053_LATENCY_IMPL_PROBE
BACKGROUND: action_gain Scaled PASS → latency 진입. FIFO buffer + commanded/executed 분리 + zero-fill reset.
GOAL: FIFO buffer 구현(~40 LOC) + probe → pilot 진입 가능성 확인
FILES_ALLOWED: src/fglc/data/collector.py, src/fglc/data/maniskill_schema.py, configs/, tests/test_fglc_latency_collector.py (신규)
FILES_FORBIDDEN: src/fglc/schemas/visibility.py
REQUIRED_IMPLEMENTATION: deque FIFO + zero-fill reset + commanded/executed 이중 기록
REQUIRED_TESTS: latency 적용 evidence + true_latency eval_only + commanded ≠ executed
ACCEPTANCE_CRITERIA: 1-ep smoke + 50ep probe gap > 0.005 + phase error 관측
COMMIT_MESSAGE: feat(collector): action_latency OOD parameter support
STOP_CONDITION: zero-fill vs first-action-repeat 미결정 시 사용자 D-3 결정 요청
```

### TASK 2054 — noise Implementation/Probe (latency Pilot PASS 후 진입)

```text
TASK_NAME: TASK_2054_NOISE_IMPL_PROBE
BACKGROUND: noise는 dynamics OOD가 아닌 specificity test. AUROC < 0.65 / Σ calibration metric 별도.
GOAL: ~15 LOC 추가 + noise probe + specificity metric framework 정의
FILES_ALLOWED: src/fglc/data/collector.py, configs/, tests/test_fglc_noise_collector.py (신규)
FILES_FORBIDDEN: 동일 (visibility.py 변경 불필요)
REQUIRED_IMPLEMENTATION: _flat_obs 직후 noise injection + RNG seed + σ upper bound guard
REQUIRED_TESTS: noise σ 적용 evidence + same-seed reproducibility 검증
ACCEPTANCE_CRITERIA: 1-ep smoke + specificity metric framework 정의 (실측은 R3 smoke 단계)
COMMIT_MESSAGE: feat(collector): observation_noise OOD parameter support
STOP_CONDITION: σ > 0.15에서 dynamics destruction sign → upper bound 0.1로 하향
```

### TASK 2055 — R3 Integration (action_gain PASS 후)

```text
TASK_NAME: TASK_2055_R3_INTEGRATION
BACKGROUND: friction + action_gain (+ latency + noise) → r3_smoke.py → metrics.json → repair ledger
GOAL: R3 smoke 두 번째 axis 등록 후 1-epoch smoke 실행
FILES_ALLOWED: scripts/fglc/r3_smoke.py (최소 편집), outputs/metrics/, outputs/repair/loop_*.jsonl
FILES_FORBIDDEN: outputs/phase_gates/R3.passed (절대 생성 금지 — 사용자 승인 필수)
REQUIRED_IMPLEMENTATION: dataloader 다중 axis 지원 확인 + 1-batch forward + 1-epoch smoke
REQUIRED_TESTS: test_fglc_r3_runner_maniskill.py 재실행
ACCEPTANCE_CRITERIA: NLL finite + ood_nll > id_nll (axis별) + metrics.json 생성
COMMIT_MESSAGE: feat(r3): four-axis smoke integration (friction + action_gain)
STOP_CONDITION: R3 smoke FAIL → repair loop (axis-specific cause)
```

### TASK 2056 — Execution Finalize

```text
TASK_NAME: TASK_2056_EXECUTION_FINALIZE
BACKGROUND: TASK 2049~2055 결과 정리 + 사용자 결정 D-1~D-7 최종 정리 + R3 진입 사용자 승인 요청
GOAL: §K PASS/PATCH/BLOCKED 기준 + §L 사용자 결정 + §M atomic checklist + §N 다음 단계 작성
FILES_ALLOWED: docs/NEXT_STAGE_FOUR_AXIS_DATA_COLLECTION_EXECUTION_PLAN.md (편집), reports/next_stage_four_axis_agent_synthesis.md (편집)
FILES_FORBIDDEN: outputs/phase_gates/R3.passed (생성 금지)
REQUIRED_IMPLEMENTATION: 모든 stage 결과 종합 + commit 단위 정리 (TASK별 1 commit)
REQUIRED_TESTS: full pytest -q 회귀 확인
ACCEPTANCE_CRITERIA: 8 TASK 완료 + Agent I 최종 판정 + 사용자 승인 대기
COMMIT_MESSAGE: docs(data): next-stage four-axis execution plan finalize
STOP_CONDITION: 사용자 승인 미응답 시 PLAN 완료 + 대기
```

### Gatekeeper 6조건 (모든 TASK 공통)

1. verify mode 종료 코드 0
2. `git diff --cached` 수동 review — 의도치 않은 변경 없음
3. 금지 경로 미수정 확인 (`.claude/`, `docs/idea/`, `src/fglc/schemas/`)
4. RESULT.md 존재 확인
5. REQUIRED_TESTS 통과 재확인
6. T3 (implementation-risk-critic) PASS — MD-only TASK는 T5 권장

---

## §K — PASS/PATCH_REQUIRED/BLOCKED 기준

### K.1 본 PLAN 자체 판정

**PLAN_PASS**:
- §A~§N 14 섹션 완성
- 4 axis 카드 (friction/gain/latency/noise) 각각 claim/LOC/criteria/failure 기술
- 25개 quality gate + DESIGN §G 30개 매핑 완성
- 16단계 repair loop + axis × cause × candidate 매핑 완성
- TASK 2049~2056 10헤더 명세 완성
- atomic checklist + BLOCKED/UNKNOWN 명시
- verification plan 4 step 완성
- D-1~D-7 사용자 결정 정리

**PATCH_REQUIRED**: ManiSkill API 추가 격차 발견 (action clipping 위치 불명 등)
**PLAN_BLOCKED**: FORBIDDEN_AGENT_FIELDS guard 격차 / forbidden field leakage 발견

### K.2 axis별 R3 진입 조건

| Axis | R3 진입 조건 | 사용자 승인 필요 |
|---|---|---|
| friction | 기존 PASS (gap 0.138/0.124) | ❌ 자동 |
| action_gain | Stage 2 Pilot PASS (gap > 0.01, KS p < 0.05) | ⚠ R3.passed 생성 시 |
| latency | Stage 2 Pilot PASS | ⚠ 동일 |
| noise | Stage 2 Pilot PASS + AUROC < 0.65 | ⚠ 동일 |

### K.3 R3 smoke PASS 조건 (전체)

- 데이터: friction + 최소 1 추가 axis (action_gain 우선) Scaled 완료
- 모델: 1-batch forward shape OK + 1-epoch smoke NLL finite
- 검증: ood_nll > id_nll per-axis + metrics.json 생성
- repair: repair_loop ledger jsonl ≥ 1줄 (axis별)

### K.4 stage별 판정 기준 요약

| Stage | PASS 기준 | PATCH 조건 | BLOCKED 조건 |
|---|---|---|---|
| Stage 0 | 9개 체크 완료 | ManiSkill 격차 발견 | forbidden field leakage |
| Stage 1 | gap > 0.005 + H1-H8 + H20 | gap 0.001~0.005 (lenient repair) | gap ≈ 0 (axis 무효) |
| Stage 2 | gap > 0.01 + 30 gate | H22 FAIL (repair 가능) | leakage 발견 |
| Stage 3 | + Cohen's d > 0.3 + KS p < 0.01 | CI95 > 50% | NLL = inf |

---

## §L — 사용자 승인 필요 항목

### L.1 D-1: 다음 EXECUTION 진입 axis

- **(a) action_gain (gain=0.7 primary) [권장]** — 구현 난이도 최저, FGLC claim 연결 직접
- (b) latency 먼저 — control-temporal 통합 우선 시
- (c) noise 먼저 — specificity test 조기 검증 시
- (d) friction 재수집 — µ_kinetic 매핑 해결 우선 시

### L.2 D-2: 첫 TASK 위임 대상

- **(a) Codex (~50 LOC, multi-file) [권장]** — TASK_2050 3파일 동시 수정, Codex 위임 트리거 조건 충족
- (b) Claude 직접 (소규모 검토 비용 절감)
- (c) Codex worktree 병렬

### L.3 D-3: latency reset 정책

- **(a) zero-fill (causality clean) [권장]** — d-step gap 명확, phase error 자연 발생
- (b) first-action-repeat (instantaneous startup)
- (c) random init (worst-case stress)

### L.4 D-4: noise σ upper bound

- **(a) σ_max = 0.15 (conservative) [권장]** — dynamics learning 안전 + specificity 검증 가능
- (b) σ_max = 0.2 (SSoT 18_DATA_BENCHMARKS 그대로)
- (c) σ_max = 0.1 (very conservative, Σ calibration 관찰 범위 좁음)

### L.5 D-5: BACKBONE 등급 1 변경 사전 승인

- **(a) case-by-case [권장]** — axis FAIL 발생 시 해당 cause만 추가
- (b) taxonomy.py 4 신규 cause 모두 사전 승인
- (c) candidates.py policy-change family 모두 사전 승인

### L.6 D-6: mass repair track 병렬?

- **(a) 4 axis 완료 후 contact-rich policy track [권장]** — 현재 R3 주력과 분리
- (b) 3 axis 병렬로 LiftCube probe (mass-sensitive task 후보)
- (c) mass DEFERRED 확정 (논문 limitation 처리)

### L.7 D-7: R3.passed 생성 권한

- **(a) action_gain Scaled PASS + R3 smoke OK 시 사용자 명령 [권장]**
  `scripts/run_codex_task.ps1` 또는 `/fglc-phase-check --pass R3`
- (b) Claude가 조건 충족 시 자동 → **NOT RECOMMENDED** (BACKBONE 등급 2 위반)
- (c) 추가 사용자 review 후 생성

---

## §M — Atomic Checklist

```
[ ] 탐색: 30개 reference 확인 + Phase 1 Explore 결과 read
[ ] 계획: §A~§N 14 섹션 작성 완료
[ ] 검증: test_fglc_split_integrity.py + test_fglc_no_garbage_data.py +
          test_fglc_ood_severity.py + test_fglc_r3_runner_maniskill.py +
          test_fglc_forbidden_field_sync.py 회귀 green (본 PLAN 단계)
[ ] 테스트 계획: 신규 axis별 test (test_fglc_action_gain/latency/noise_collector.py) 계획 정의
[ ] 재설계: TASK 2049~2056 10헤더 작성 완료
[ ] 수집 계획: probe → pilot → scaled axis별 명시 (action_gain 우선)
[ ] R3 smoke 금지: 본 PLAN MD 작성 단계에서 r3_smoke.py 실행 금지
[ ] repair loop: axis × cause × candidate 매핑 완성 (§I.2)
[ ] commit 정책: raw HDF5 제외, outputs/repair *.jsonl 대용량 제외, phase gate sentinel 제외
[ ] R3.passed 금지: /fglc-phase-check --pass R3 사용자 승인 필수 (본 PLAN 단계 아님)
[ ] forbidden field 12개 보존: 4 axis 추가 후 leakage 0건 검증 plan 완성
[ ] mass repair track 분리: DESIGN §E.2 P3/P4/P7 참조 보존
[ ] negative result 공시: mass FAIL × 2 task (gap 0.0038/0.008), noise AUROC < 0.65 의도적
[ ] friction µ_kinetic DEFERRED: 논문 Appendix 처리 계획 명시
[ ] noise specificity metric: AUROC, false positive rate, Σ calibration 별도 정의 완성
[ ] D-1~D-7 사용자 결정 항목 명시
```

**절대 금지 항목** (PLAN 내 어느 단계에서도):

```
❌ action_gain/latency/noise 성공 사전 단정
❌ friction-only로 전체 주장 완전 검증 단정
❌ delta_min=0.01 또는 KS p=0.05 threshold 완화
❌ 기존 데이터 사후 변형
❌ negative result (mass FAIL × 2 task) 숨김
❌ raw HDF5 commit
❌ outputs/phase_gates/R3.passed 생성 (사용자 승인 없이)
❌ docs/idea/18_DATA_BENCHMARKS.md / 19_BASELINES.md / 20_ABLATIONS.md 무단 수정
❌ 문제 발견에서 종료 — 반드시 원인 분해 + 해결 후보 + 재검증 + 적용 조건
❌ Codex 위임 없이 ~105 LOC 구현을 본 PLAN 단계에서 직접 실행
❌ noise axis의 낮은 gap을 FAIL 처리 (specificity로 분리)
```

---

## §N — 다음 execute 단계 최소 작업

**D-1=(a) 선택 시 (action_gain 우선, 권장안):**

```
Step 1. 사용자 D-1~D-7 결정 확인 (특히 D-2 Codex 위임 여부)

Step 2. TASK_2050 파일 작성 (Claude 담당)
  경로: .agent_tasks/codex_queue/TASK_2050_ACTION_GAIN_IMPL.md
  10헤더 완성 + ACCEPTANCE_CRITERIA + STOP_CONDITION

Step 3. Codex 위임 (D-2=(a) 선택 시)
  명령: scripts/run_codex_task.ps1 -Mode run -TaskName 2050
        -TaskFile .agent_tasks/codex_queue/TASK_2050_ACTION_GAIN_IMPL.md
        -BypassSandbox
  예상 소요: 30~60분

Step 4. verify (Claude 담당)
  git diff --cached --stat
  금지 경로 미수정 확인
  test_fglc_action_gain_collector.py (신규) + test_fglc_forbidden_field_sync.py PASS
  RESULT.md 존재 확인

Step 5. T3 implementation-risk-critic 호출
  /codex-result-audit
  report 경로: docs/orchestration/agent_reports/2026-05/impl_risk_TASK_2050_R1.md

Step 6. Gatekeeper 6조건 통과 시 accept commit
  통과 못하면: git merge --abort → repair → 재시도

Step 7. TASK_2051 (probe) 진입
```

**예상 산출물 (TASK_2050 완료 후)**:
- `src/fglc/data/collector.py` — ~10 LOC 추가 (action_gain 분기)
- `src/fglc/data/maniskill_schema.py` — ~10 LOC 추가 (TASK_OOD_PARAMS, REGIME_ID)
- `configs/fglc/smoke_maniskill_pickcube_gain.yaml` (신규)
- `configs/fglc/smoke_maniskill_pushcube_gain.yaml` (신규)
- `tests/test_fglc_action_gain_collector.py` (신규, ~20 LOC)
- 1 commit: `feat(collector): action_gain OOD parameter support`

---

## Open UNKNOWNs

| # | UNKNOWN | 해결 방법 | 우선순위 |
|---|---|---|---|
| U-1 | ManiSkill 3.0.1 action clipping 위치 (env.step 전 vs 내부) | 1-step probe 또는 ManiSkill source 확인 | HIGH (TASK_2050 전) |
| U-2 | latency reset 정책 (사용자 D-3) | 사용자 결정 | HIGH |
| U-3 | noise σ 상한 (사용자 D-4) | 사용자 결정 | MEDIUM |
| U-4 | taxonomy.py 4 신규 cause 사용자 승인 (D-5) | 사용자 결정 | MEDIUM |
| U-5 | PickCube on-disk 250ep ↔ smoke config 50ep 격차 | Stage 0 audit | MEDIUM |
| U-6 | quality_report.json Ckpt 4 FAIL vs STEP11 RESULT Ckpt 4 PASS 충돌 | Stage 0 재확인 | MEDIUM |
| U-7 | TASK_SPLIT_DEFAULTS 정확한 위치 (maniskill_schema.py grep miss) | Stage 0 직접 확인 | LOW |
| U-8 | LiftCube-v1 actor 이름 (mass repair track 후보) | D-6 결정 후 probe | LOW |
| U-9 | PickCube/PushCube seed pool 정확한 끝값 | manifest.json 직접 읽기 | LOW |
| U-10 | 2025/2026 논문 중 action-gain shift를 explicitly 다루는 논문 존재 여부 | MCP arxiv + semantic-scholar (G agent 재호출) | MEDIUM |

---

## Verification Plan

```powershell
# 1. 산출물 생성 확인
Test-Path "C:\Users\computer\Desktop\ICLR_WM_claude-code\docs\NEXT_STAGE_FOUR_AXIS_DATA_COLLECTION_EXECUTION_PLAN.md"
Test-Path "C:\Users\computer\Desktop\ICLR_WM_claude-code\reports\next_stage_four_axis_agent_synthesis.md"

# 2. 참조 파일 무결성 (수정 없음)
git status --short docs/idea/
git status --short data/fglc/
git status --short src/fglc/
git status --short scripts/fglc/
git status --short configs/fglc/
git status --short tests/

# 3. phase gate 보호
Test-Path "C:\Users\computer\Desktop\ICLR_WM_claude-code\outputs\phase_gates\R0.passed"  # True
Test-Path "C:\Users\computer\Desktop\ICLR_WM_claude-code\outputs\phase_gates\R1.passed"  # True
Test-Path "C:\Users\computer\Desktop\ICLR_WM_claude-code\outputs\phase_gates\R2.passed"  # True
Test-Path "C:\Users\computer\Desktop\ICLR_WM_claude-code\outputs\phase_gates\R3.passed"  # False (금지)

# 4. 기존 테스트 회귀 (코드 변경 없음이므로 현재 green 상태 재확인)
& "C:\Users\computer\Desktop\ICLR_WM_claude-code\.venv\Scripts\python.exe" -m pytest -q `
    tests\test_fglc_split_integrity.py `
    tests\test_fglc_no_garbage_data.py `
    tests\test_fglc_ood_severity.py `
    tests\test_fglc_forbidden_field_sync.py `
    tests\test_fglc_repair_taxonomy.py `
    tests\test_fglc_repair_diagnose.py `
    tests\test_fglc_repair_candidates.py `
    tests\test_fglc_r3_runner_maniskill.py
```

---

## Final Rule

본 PLAN의 목표는 3 axis 구현 자체가 아니다.

**목표**: friction(재활용) + action_gain(신규 PRIMARY) → latency → noise(specificity) 의 EXECUTION 순서, STOP 조건, repair loop 진입 트리거, R3 smoke 연결을 단일 MD로 정리하여 사용자가 D-1~D-7 결정 + Codex 위임 + 단계적 검증이 가능하게 하는 것.

```
read correct context (30 references + Phase 1 Explore 결과)
preserve scientific contract (FGLC 4축 metric + SSoT 5 axes + forbidden 12개 + delta_min=0.01)
implement smallest valid step (2 MD 작성, 코드 변경 없음)
test before scaling (verification plan 4 step)
report blockers honestly (mass FAIL × 2 task, friction-only 한계, taxonomy 격차, noise specificity framing)
```

---

*참조 DESIGN: `docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md` (commit `6f48d67`)*
*참조 SYNTHESIS: `reports/four_axis_dataset_design_synthesis.md`*
*다음 단계 EXECUTION: TASK_2049 → D-1~D-7 사용자 결정 → TASK_2050 Codex 위임*
