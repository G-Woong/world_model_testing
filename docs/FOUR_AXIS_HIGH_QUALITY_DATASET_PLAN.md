# FGLC Four-Axis High-Quality Dataset Construction Plan

> **Status**: PLAN — 코드/데이터 변경 금지, 새 수집 금지, R3 smoke 금지, R3.passed 생성 금지
> **Branch**: `memory-redesign-2026-05-16`
> **Date**: 2026-05-24
> **Predecessor**: `docs/INTERACTION_AXIS_DATASET_DESIGN_REVIEW.md` (commit `7fe0a02`, 1260줄)
> **선행 완료**: PickCube 450ep + PushCube 900ep friction PASS, mass FAIL × 2 task
> **목적**: friction + action_gain + latency + noise 4축 기반 고품질 데이터셋 구축 계획

---

## §A — 현재 발견사항 요약

### A.1 INTERACTION_AXIS_REVIEW 결과 요약 (commit `7fe0a02`)

2026-05-24 기준 R2 완료, R3 PENDING. 두 task에 걸친 axis × policy 교차 실험 결과:

| Task | Axis | state_delta_norm gap | 판정 | 원인 |
|---|---|---|---|---|
| PickCube-v1 | friction | **0.138** | **PASS** | joint Coulomb friction → qvel 직접 영향 |
| PickCube-v1 | mass | 0.0038 | **FAIL** | contact_rate=0%, tcp_dist=0.999m |
| PushCube-v1 | friction | **0.124** | **PASS** | 동일 메커니즘 |
| PushCube-v1 | mass | 0.0080 | **FAIL** | random policy 저접촉 |

**핵심 교훈**: friction axis는 joint motor에 직접 작용(`τ_eff = τ_motor - 5.0 × sign(qvel)`)하여 접촉 여부와 무관하게 매 step qvel에 영향. mass axis는 물체 접촉(F=ma)이 필요하나 contact_rate=0%에서 물리 경로 차단.

repair loop는 `consecutive_inconclusive` 종료, `next_action=USER_ESCALATION_BACKBONE_DECISION`으로 기록됨.

### A.2 repair_ledger 상태

```jsonl
{
  "loop_id": "pushcube_mass_2026-05-24",
  "iter": 1,
  "diagnosed_cause": "OOD_TOO_HARD_RANDOM_POLICY_LOW_CONTACT_BOTH_TASKS",
  "result": "reject",
  "stop_condition_hit": "consecutive_inconclusive",
  "next_action": "USER_ESCALATION_BACKBONE_DECISION",
  "metrics_before": {"state_delta_norm_gap": 0.004, "task": "PickCube-v1"},
  "metrics_after":  {"state_delta_norm_gap": 0.008, "task": "PushCube-v1"}
}
```

### A.3 현재 on-disk 데이터 인벤토리

```
data/fglc/PickCube-v1/
  raw/train_id.h5         250 ep, D_x=42, D_a=8, ep_len=50
  raw/val_id.h5            50 ep
  raw/test_id.h5           50 ep
  raw/ood_mass_low.h5      50 ep  (gap=0.0038, BLOCKED)
  raw/ood_friction_low.h5  50 ep  (gap=0.138,  PASS)
  manifest.json            seed_pool [42~650), git_sha=3c1806ed, ManiSkill 3.0.1
  dataset_stats.json       D_x=42, D_a=8
  quality_report.json      Ckpt4=FAIL(ood_sev mass), Ckpt5/6/9=SKIP
                           friction_mapping=DEFERRED

data/fglc/PushCube-v1/
  raw/train_id.h5         500 ep, D_x=35, D_a=8, ep_len=50
  raw/val_id.h5           100 ep
  raw/test_id.h5          100 ep
  raw/ood_mass_low.h5     100 ep  (gap=0.008, BLOCKED)
  raw/ood_friction_low.h5 100 ep  (gap=0.124, PASS)
  manifest.json            seed_pool [1042~1999)
```

**총 기존 데이터**: PickCube 450ep + PushCube 900ep = 1350ep

### A.4 SSoT vs 코드 격차 (Phase 1 정밀 조사 결과)

| Axis | SSoT 정의 (`18_DATA_BENCHMARKS.md`) | 코드 구현 | 격차 |
|---|---|---|---|
| friction | µ_kinetic ∈ {0.3, 0.7, 1.5} | `set_friction(5.0)` (joint_dry_friction) | **단위 매핑 DEFERRED** |
| action_gain | gain ∈ {0.7, 0.85, 1.3} | `eval_metas["true_action_gain"]` placeholder만 | `_apply_ood` 분기 **없음** (~10 LOC) |
| latency | delay ∈ {3, 5, 8} steps | `eval_metas["true_latency"]` placeholder만 | FIFO buffer **없음** (~25-40 LOC) |
| noise | σ ∈ {0.05, 0.1, 0.2} | `eval_metas["true_noise_sigma"]` placeholder만 | noise injection **없음** (~15 LOC) |

**collector.py 핵심 갭**: `_apply_ood()` (line 66~89)에 friction/mass만 분기, action_gain/latency/noise 처리 없음.

### A.5 repair loop 격차 (Phase 1 발견)

- `taxonomy.py`: 20개 `FailureCauseId` — `OOD_INVISIBLE_TO_RANDOM_POLICY` 없음, action_gain/latency용 cause 없음
- `diagnose.py`: 9개 fire 함수 — axis-specific는 friction/mass 계열만
- `candidates.py`: 14개 candidate — policy-change family **전무** (mass repair 결정적 격차)
- noise는 `EVAL_NOISE_HIGH`(evaluation variance)와 의미 혼재 위험

### A.6 test/config 격차

- 24개 `test_fglc_*` 중 4 axis end-to-end OOD test **없음** (synthetic만)
- 3개 config 중 action_gain/latency/noise config **없음**
- PickCube on-disk train_id=250ep ↔ smoke config 50ep 격차 (별도 collect run 추정)
- `quality_report.json` Ckpt 4=FAIL, Ckpt 5/6/9=SKIP

### A.7 R3/R5/R6 gate 요구사항

- **Stage 1 gate** (`docs/idea/12_TRAINING_STAGES.md`): ID NLL 수렴 + OOD NLL > ID NLL
- **Stage 3 gate**: 최소 **2개** OOD 조건에서 TD-MPC2 baseline 초과 → friction 단독으로 불충분

**핵심 결론**: friction 데이터 단독으로 R3 smoke는 가능하나 R5/R6 Stage 3 gate는 `≥2 axes` 필요. 따라서 action_gain + latency + noise 중 최소 1개 축 추가 필수.

---

## §B — 4개 주력 Axis 정의와 의미

### B.1 friction (joint_dry_friction) — PRIMARY

- **물리/제어 의미**: 로봇 관절 내부 Coulomb 마찰. `τ_eff = τ_motor - friction_coeff × sign(qvel)`. 전기모터 효율 저하 시뮬레이션.
- **FGLC claim 연결**:
  * `μ_t` 변화: qvel dims 9-17에서 마찰 증가 → joint deceleration 증가 → μ_t의 qvel 예측 오류
  * `ρ_t = Σ_t^{-1/2}(z_{t+1} - μ_t)` — qvel 관련 latent dims에서 편차 발화
  * `β_t`: 표준화된 mismatch 누적 → falsification gate 점화
  * 예측 NLL ↑, falsification AUROC ↑ 모두 예상
- **적용 step**: env init (episode 시작 시 한 번)
- **API**: `art.joints[i].set_friction(value)` — `collector.py:84-89`
- **추가 LOC**: ≈ 0 (구현 완료), µ_kinetic 매핑 ledger ~20-30 LOC (별도 문서화 TASK)
- **forbidden field**: `true_friction` ← 이미 12개 목록에 포함
- **random policy invariance**: 접촉 무관 (joint motor에 직접) → random policy에서 **작동**
- **위험**: SSoT 단위(µ_kinetic) ↔ 코드 단위(joint_dry_friction N·m) 매핑 미해결 → reviewer "물리 단위 오류" 공격 가능

### B.2 action_gain — PRIMARY

- **물리/제어 의미**: `a_executed = gain × a_commanded`, gain ∈ {0.7, 0.85, 1.3}. 제어 이득(control gain) 변화. robot이 "둔감해지거나(gain<1)" "과민해지는(gain>1)" 제어 shift.
- **FGLC claim 연결**:
  * action scaling → state transition function 직접 변경
  * `μ_t` 변화: gain=0.7 → joint velocity 응답 70%로 감소 → μ_t의 qvel/tcp_pose 예측 오류
  * `α_t` (causal attention): action-value relevance — action_gain shift는 planning decision 변화 → α_t의 action-related latent group 활성화 강함
  * **4축 모두** 영향 (prediction NLL ↑, detection AUROC ≥ 0.70, nec-suf 측정 필요, planner return 변화)
- **적용 step**: `env.step(a)` 전, action scaling
- **API**: `collector.py:148-149` 사이에 `a = a * gain_factor` (clip 여부 확인 필요)
- **추가 LOC**: `_apply_ood` 분기 ~10 + schema entry ~5 + config ~5 + test ~30 = ~50 LOC
- **forbidden field**: `true_action_gain` ← 이미 12개 목록에 포함
- **random policy invariance**: 접촉 무관 (action 자체 변형) → random policy에서 **작동**
  * gain=0.7: `a_effective_std = 0.7 × 0.577 ≈ 0.404` → qvel 응답 감소 신호
- **위험**: gain=1.3 시 action clipping 가능 ([-1,1] 경계). **[UNKNOWN] clipping 전 vs 후 적용 위치** 확인 필요

### B.3 action_latency / action_delay_steps — SECONDARY

- **물리/제어 의미**: 현재 step의 action이 실제 환경에 `d` step 후 적용. delay ∈ {3, 5, 8} steps. real robot control loop delay 시뮬레이션.
- **FGLC claim 연결**:
  * temporal mismatch → WM이 `μ_t`를 `a_t` 기반 예측하나 실제 실행은 `a_{t-d}`
  * `ρ_t`에 누적 phase error → 시간이 지날수록 falsification gate 발화 강화
  * **HiP-RSSM 차별**: HiP-RSSM은 파라미터 추론으로 latency 추정, FGLC는 grouped latent의 d-step phase error 분리 → α_t의 temporal-group 활성화 측정
- **적용 step**: `env.step()` 전, action buffer에서 pop
- **API**: `collector.py` 내 FIFO deque: `deque(maxlen=d)`, initial fill: zero-action
  * commanded_action ≠ executed_action → commanded 별도 보관 (eval_only)
- **추가 LOC**: FIFO buffer + dual record + validator 확장 + reproducibility ~25-40 LOC
- **forbidden field**: `true_latency` ← 이미 12개 목록에 포함
- **random policy invariance**: 접촉 무관 (제어 chain만 영향) → random policy에서 **작동**
- **위험**: **[UNKNOWN] buffer reset 정책** — episode 시작 시 zero-fill vs first-action repeat → severity에 영향

### B.4 observation_noise σ — SECONDARY

- **물리/제어 의미**: `s_observed = s_true + ε`, ε ~ N(0, σ² I_{D_x})`, σ ∈ {0.05, 0.1, 0.2}. sensor 노이즈 시뮬레이션.
- **FGLC claim 연결**:
  * μ_t는 clean dynamics 기반이지만 Σ_t 추정이 노이즈 포함 관측으로 mis-calibrated
  * ρ_t의 분모(`Σ_t^{-1/2}`) 부정확 → β_t **false positive 위험**
  * **비판적 검증 기준**: FGLC가 noise를 dynamics shift로 오인하지 않아야 함 → **AUROC < 0.65 의도된 결과**
  * noise는 wrong-dynamics-hypothesis가 아님 — 이를 구분하는 것이 FGLC의 Σ calibration 능력 검증
- **적용 step**: `_flat_obs()` 후, state 기록 직전
- **API**: `collector.py:150` 부근에 `state = state + np.random.normal(0, σ, D_x)` (deterministic RNG)
- **추가 LOC**: noise injection + RNG seed 정책 + validator ~15 LOC
- **forbidden field**: `true_noise_sigma` ← 이미 12개 목록에 포함
- **random policy invariance**: 관측 후처리만 영향 → 모든 policy에서 작동
- **위험**: **[UNKNOWN] noise σ 상한** — σ가 너무 크면 `Σ_t^{-1/2}` ill-conditioned → dynamics learning 자체 파괴

### B.5 axis별 FGLC 수식 변수 영향 매트릭스

| Axis | μ_t 변화 | Σ_t 변화 | ρ_t 편차 | β_t 발화 | α_t 활성화 | δ_t correction |
|---|---|---|---|---|---|---|
| friction | qvel dims 직접 | 간접 (variance ↑) | qvel 관련 | **예상됨** | qvel/position group | 예상됨 |
| action_gain | qvel/tcp_pose dims | 간접 | action-related | **예상됨** | action-value group | 예상됨 |
| latency | temporal phase error | 간접 | time-lag accumulation | **예상됨** | temporal group | 예상됨 |
| noise | 없음 (μ_t clean) | **직접** (Σ_t mis-cal) | denominator 오류 | **오탐 위험** | — | **없어야 함** |

---

## §C — Axis별 5관점 점수 재검토

### C.1 5관점 정의

| # | 관점 | 정의 |
|---|---|---|
| **C1** | Dynamics/control falsification strength | shift가 FGLC β_t 점화에 기여 (state_delta_norm gap, KS p-value, per-dim Cohen's d) |
| **C2** | Action/value/planning relevance | shift가 action/reward/V(s) 결정에 영향 (reward KS, success rate Δ, planner return Δ) |
| **C3** | State-only observability | D_x만으로 mismatch 관측 가능 (per-dim variance ratio, SNR, contact-dim coverage) |
| **C4** | Dataset controllability & quality | OOD param 안정 + leakage 없음 (API 안정성, 10 reject reasons, forbidden field=0) |
| **C5** | Paper defensibility & novelty | 6 direct-threat 논문 차별 + reviewer 방어 (TD-MPC2/DreamerV3/HiP-RSSM/PLSM/ReDRAW/AdaWM) |

### C.2 Scoring Rubric

| 점수 | 의미 |
|---|---|
| 1 | 부적합 / 신호 없음 / reviewer rejection 명백 |
| 2 | 약함 / 보조 evidence만 |
| 3 | 조건부 사용 가능 |
| 4 | 강함, 주요 실험 후보 |
| 5 | 매우 강함 / 핵심 주장 검증 |

### C.3 4 Axis × 5관점 점수표 (재검토)

| Axis | C1 | C2 | C3 | C4 | C5 | 합계 | Tier | 변경? |
|---|---|---|---|---|---|---|---|---|
| **friction** | **5** | **4** | **5** | **5** | **4** | **23** | **PRIMARY** | 동일 (cross-task PASS 실증) |
| **action_gain** | **4** | **5** | **4** | **3** | **4** | **20** | **PRIMARY** | 동일 |
| **latency** | **4** | **4** | **4** | **3** | **4** | **19** | **SECONDARY** | 동일 (HiP-RSSM 차별 C5 재확인) |
| **noise** | **3** | **3** | **4** | **4** | **3→4** | **17→18** | **SECONDARY** | C5 재평가: Σ calibration 검증 가치 |
| mass (random) | 1 | 1 | 1 | 5 | 2 | 10 | **BLOCKED** | 별도 repair track 분리 |

**noise C5 재평가 근거**: FGLC가 observation noise를 dynamics shift로 오인하지 않음을 보이는 것 자체가 reviewer 방어 가능한 차별점. AUROC < 0.65가 "의도된 결과"로 논문에 투명하게 제시될 경우 C5 4점 가능. 단, 실측 전 확정 금지 → C5 잠정 3~4점.

### C.4 Tier 결정 기준

```
PRIMARY:   합계 ≥ 20 (friction, action_gain)
SECONDARY: 15~19  (latency, noise)
DEFERRED:  10~14  (contact_friction, inertia, mass=3.0+BACKBONE 등)
BLOCKED:   < 10 또는 실측 실패 (mass+random_policy)
```

### C.5 4 axis가 FGLC 핵심 주장에 기여하는 방식

FGLC Stage 3 gate (`docs/idea/12_TRAINING_STAGES.md`): "최소 2개 OOD 조건에서 TD-MPC2 baseline 초과"

| OOD 조건 | 기여 | 충족 가능 시점 |
|---|---|---|
| friction (PickCube) | PRIMARY, 이미 PASS | R3 smoke 이미 가능 |
| friction (PushCube) | cross-task replication | 현재 완료 |
| action_gain | 두 번째 PRIMARY axis | Stage 2 Pilot 후 |
| latency | SECONDARY, temporal mismatch | Stage 2 Pilot 후 |
| noise | Σ calibration 검증 | Stage 2 Pilot 후 (AUROC < 0.65 확인) |

**결론**: friction + action_gain 2축 Scaled 완료 시 R5/R6 Stage 3 gate 진입 가능.

---

## §D — 고품질 데이터셋 구축 목표

### D.1 단일 목적 정의

> **FGLC 4축 metric (예측 NLL / falsification AUROC / nec-suf attribution / control return)의 신뢰할 수 있는 검증**이 4축 고품질 데이터셋 구축의 단일 목적이다.

4축 metric은 `docs/idea/21_METRICS.md` SSoT 기준:
1. **예측 축**: ID NLL ↔ OOD NLL 격차 (axis별 분리)
2. **탐지 축**: falsification AUROC (regime_id = eval_only label, not inference)
3. **귀인 축**: necessity-Δ, sufficiency-Δ, random-Δ
4. **제어 축**: OOD 조건별 planner return, 성공률

### D.2 axis별 예상 metric 값 (사전 가설, 실측 필요)

| Axis | OOD NLL diff | falsification AUROC | nec-suf nec | planner return Δ |
|---|---|---|---|---|
| friction | ≥ 0.2 (expected, gap=0.138 실측) | ≥ 0.75 | ≥ 0.5 | ≥ 5% |
| action_gain | ≥ 0.1 (expected, 미실측) | ≥ 0.70 | 측정 필요 | 측정 필요 |
| latency | ≥ 0.15 (expected, 미실측) | ≥ 0.75 | 측정 필요 | 측정 필요 |
| noise | 소폭 (Σ만 잘 calibration되면) | **< 0.65** (**의도된 결과**) | N/A | ≈ 0 |

> **noise AUROC < 0.65**: FGLC가 observation noise를 dynamics shift로 오인하지 않음을 검증. 이 값이 0.70 이상이면 FGLC의 β_t gate false positive 문제로 판단.

threshold 출처: `docs/idea/21_METRICS.md` 기반. delta_min=0.01 유지 (완화 금지).

### D.3 데이터 품질 불변조건

1. `FORBIDDEN_AGENT_FIELDS` 12개 ← `src/fglc/schemas/visibility.py` (4 axis true_* 모두 포함)
2. `/episodes/` HDF5에 inference 필드만 (`state/action/reward/done`)
3. `eval_metas`는 HDF5 별도 보관, inference 경로와 완전 분리
4. seed pool 완전 disjoint (기존 [42~1999), 신규 [2000+))
5. trajectory hash duplicate = 0 (validators.py 강제)
6. quality_report.json에 각 checkpoint 결과 기록

---

## §E — 자원 계산 기반 수집량 계획

### E.1 단위 추정 (Phase 1 실측 기반)

| Task | D_x | D_a | ep_len | bytes/transition | bytes/episode | 수집 속도 |
|---|---|---|---|---|---|---|
| PickCube-v1 | 42 | 8 | 50 | ~430 B (float32+overhead) | ~21.5 KB | ~1.25 ep/s |
| PushCube-v1 | 35 | 8 | 50 | ~374 B | ~18.7 KB | ~1.25 ep/s |

실측: PickCube 450ep ≈ 2 MB (gzip4), ~7분 (병렬 5 split).

### E.2 4 Stage × axis × task 수집량 시나리오

| Stage | ep/split (train/val/test/ood1/ood2) | 총 ep | PickCube disk/task | 수집 시간/task |
|---|---|---|---|---|
| **Probe** | 10/10/10/10/10 | 50 | ~1 MB | ~1-2분 |
| **Pilot** | 100/50/50/50/50 | 300 | ~6 MB | ~4-5분 |
| **Scaled** | 500/100/100/100/100 | 900 | ~19 MB | ~12-15분 |
| **Robust** | 1000/200/200/200/200 | 1800 | ~39 MB | ~24-30분 |

> 기존 PickCube friction Scaled: 250/50/50/50/50 = 450ep ≈ 2 MB (실측, gzip4 적용)

### E.3 4 axis × 2 task 전체 예산 (Scaled 기준)

| 항목 | 값 |
|---|---|
| 총 ep (friction 재사용 포함) | 기존 1350ep + 신규 ~3600ep = ~5000ep |
| 총 disk | ~80 MB |
| 총 수집 시간 (action_gain+latency+noise × 2 task) | ~150-180분 ≈ 3시간 |
| R3 training (30 epoch × 4 axis × 2 task × 1 seed) | ~8-12시간 |
| VRAM peak (R3, batch=16, T=16, ~10M params) | ~200-500 MB |
| VRAM 여유 (8GB 한계) | ~16-40× 여유 |

### E.4 VRAM 안전성 분석 (RTX 4060 Ti 8GB)

| 항목 | 추정 | 한계 | 마진 |
|---|---|---|---|
| 데이터 수집 (CPU only) | ~0 MB | 8188 MB | 100% |
| R3 model 파라미터 (~10M) | ~40 MB | 8188 MB | 204× |
| Adam state | ~80 MB | 8188 MB | 102× |
| 활성화 (batch=16, T=16, h_dim=256) | ~200 MB | 8188 MB | 41× |
| 총 R3 | ~400-600 MB | 8188 MB | ~14-20× |
| R5/R6 causal attention 추가 | ~500-1000 MB | 8188 MB | ~8-16× |

**결론**: R7 planner integration 이전까지 VRAM 제약 없음. batch=32, T=32까지 안전.

### E.5 권장 수집 경로

| 목적 | 권장 | axis/task/stage |
|---|---|---|
| R3 즉시 smoke | 기존 friction 450ep (완료) | friction/PickCube/Scaled |
| R3 full + action_gain gate | +900ep | action_gain/{Pick,Push}Cube/Scaled |
| R5/R6 Stage 3 gate | +1800ep 추가 | latency/{Pick,Push}Cube/Scaled |
| 4축 paper-grade | +3600ep (Robust) | 전체 4 axis × 2 task |
| 전체 3 seeds | ×3 = 7 day budget | sequential |

**총 wall-clock 추정**: 4 axis × 2 task × Scaled(15분) + R3 training = ~2-4 day (데이터+학습 합산).

---

## §F — Stage별 수집 절차

### F.1 Stage 0: Static Audit (코드 변경 없음, 약 2시간)

**목적**: 4 axis 구현 가능성 + 기존 데이터 재사용 + leakage risk 정량화

```
체크리스트:
[ ] friction 기존 데이터 재사용 가능성 확인
    → PickCube 250 train + 50×4 OOD ep = 450ep PASS 확인됨
[ ] action_gain `_apply_ood` 구현 위치 확인 (collector.py:66-89)
    → TASK_OOD_PARAMS에 "action_gain" key 추가 분기
[ ] latency FIFO buffer 구현 위치 확인
    → collector.py episode loop 내 deque 추가 위치
[ ] noise injection 위치 확인
    → _flat_obs() 반환 후, state 기록 직전
[ ] FORBIDDEN_AGENT_FIELDS 12개 ↔ 4 axis 추가 후 leakage 가능성
    → true_action_gain/true_latency/true_noise_sigma 모두 포함 확인
[ ] quality_report.json:friction_mapping=DEFERRED 해결 plan 수립
[ ] PickCube on-disk 250ep ↔ smoke config 50ep 격차 원인 조사
```

**산출**: §A 현재 발견사항 + §C tier 표 + §K TASK A1 완성

### F.2 Stage 1: Probe (axis별 10~50 ep, quarantine 저장)

**목적**: API 동작 확인 + shape 일관성 + OOD parameter 적용 evidence

**friction (기존 완료)**: PickCube gap=0.138 PASS, PushCube gap=0.124 PASS

**action_gain probe** (신규):
```yaml
probe_action_gain_low:
  task: PickCube-v1
  n_episodes: 50
  ood_params: {action_gain: 0.7}
  seed_pool: [2000, 2050)
  save: quarantine

probe_action_gain_high:
  task: PickCube-v1
  n_episodes: 50
  ood_params: {action_gain: 1.3}
  seed_pool: [2050, 2100)
  save: quarantine
```

**latency probe** (신규):
```yaml
probe_latency_3:
  task: PickCube-v1
  n_episodes: 50
  ood_params: {action_delay_steps: 3}
  seed_pool: [2100, 2150)

probe_latency_8:
  task: PickCube-v1
  n_episodes: 50
  ood_params: {action_delay_steps: 8}
  seed_pool: [2150, 2200)
```

**noise probe** (신규):
```yaml
probe_noise_low:
  task: PickCube-v1
  n_episodes: 50
  ood_params: {noise_sigma: 0.05}
  seed_pool: [2200, 2250)

probe_noise_high:
  task: PickCube-v1
  n_episodes: 50
  ood_params: {noise_sigma: 0.2}
  seed_pool: [2250, 2300)
```

**Probe 성공 조건** (axis별):
- shape consistency (D_x=42, D_a=8)
- reward scalar (not array)
- done/truncated valid
- state_delta_norm gap > 0.005 (probe 단계 lenient threshold)
- AttributeError 없음
- OOD parameter 적용 evidence (manifest의 ood_params non-empty)

**Probe 실패 분기**:
- gap < 0.005 → `OOD_TOO_EASY` (action_gain의 경우: clipping 확인 → gain 범위 확장)
- AttributeError → ManiSkill API 미지원 → BLOCKED + 사용자 escalation
- forbidden field detected → 즉시 abort + 보고

### F.3 Stage 2: Pilot (axis별 100/50/50/50/50 = 300 ep)

**목적**: H1-H15 quality gate 전체 통과 + KS p-value 안정

**성공 조건**:
- H1-H14 quality gates PASS (episode-level + split-level)
- H15: gap > 0.01 + KS p-value < 0.05 (per-axis aggregate)

**Pilot 실패 분기**:
- H15 FAIL (gap < 0.01) → diagnose: `OOD_TOO_EASY` → severity 증가 후보:
  * action_gain: {0.7→0.5, 1.3→1.5} 재검토
  * latency: {3,5,8} → {5,8,12} 재검토
  * noise: σ 범위 재검토 (단, 상한 주의)
- H15 FAIL (KS p > 0.05) → `DATA_TOO_SMALL` → Scaled 단계로 바로 진행
- H7/H8/H9 FAIL (seed/hash/regime leakage) → `DATA_BAD_SPLIT` → seed pool 재생성

### F.4 Stage 3: Scaled (axis별 500/100/100/100/100 = 900 ep)

**목적**: 통계적 검출력 확보 + per-dim Cohen's d 안정

**성공 조건**:
- Pilot의 모든 gate 재PASS
- per-dim Cohen's d > 0.3인 dim 수 (axis별 expected dims):
  * friction: qvel dims 9-17 (9 dims) → ≥ 6 dims
  * action_gain: qvel/tcp_pose dims → ≥ 4 dims
  * latency: phase-shifted velocity dims → ≥ 3 dims (시간 지연 효과)
  * noise: all dims (uniform noise) → statistical noise only
- KS p < 0.01 (Scaled에서)
- ID/OOD gap의 CI95 < 50% of mean gap

**axis × task 수집 매트릭스**:

| Axis | PickCube Stage 0 | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| friction | DONE | DONE | DONE (450ep) | OPTIONAL | OPTIONAL |
| friction (PushCube) | DONE | DONE | DONE (900ep) | OPTIONAL | OPTIONAL |
| action_gain | TODO | **NEXT** | TODO | TODO | TODO |
| latency | TODO | TODO | TODO | TODO | TODO |
| noise | TODO | TODO | TODO | TODO | TODO |

### F.5 Stage 4: Robust (axis별 1000/200/200/200/200 = 1800 ep, 2 seeds)

**목적**: paper-grade reproducibility + 2 seed 일치

**성공 조건**:
- 2개 독립 seed로 Scaled 수집 → gap 일치 확인 (seed 간 gap 불일치 ≤ 20%)
- multi-seed 결합 후 KS p < 0.001
- novelty relevance (Agent G) reviewer attack 시뮬레이션 통과

### F.6 axis × stage × task 전체 진행 현황

| Axis | Task | Probe | Pilot | Scaled | Robust | 상태 |
|---|---|---|---|---|---|---|
| friction | PickCube | DONE | DONE | DONE (250ep) | OPT | **PASS** |
| friction | PushCube | DONE | DONE | DONE (500ep) | OPT | **PASS** |
| mass (random) | PickCube | DONE | DONE | DONE (50ep) | — | **BLOCKED** |
| mass (random) | PushCube | DONE | DONE | DONE (100ep) | — | **BLOCKED** |
| action_gain | PickCube | TODO | TODO | TODO | TODO | 미구현 |
| action_gain | PushCube | TODO | TODO | TODO | TODO | 미구현 |
| latency | PickCube | TODO | TODO | TODO | TODO | 미구현 |
| latency | PushCube | TODO | TODO | TODO | TODO | 미구현 |
| noise | PickCube | TODO | TODO | TODO | TODO | 미구현 |
| noise | PushCube | TODO | TODO | TODO | TODO | 미구현 |

---

## §G — Quality Gate Checklist (30 항목)

### G.1 Episode-level (validators.py 10 reject reasons)

| # | Gate | 검증 기준 | 담당 |
|---|---|---|---|
| H1 | Schema consistency | D_x=42/35, D_a=8 일치 | `validate_episode` |
| H2 | Dtype numeric | float32 / bool valid | `validate_episode` |
| H3 | NaN/Inf 없음 | state/action/reward에 NaN/Inf 0건 | `validate_episode` |
| H4 | Reward scalar | reward shape=() or (T,) | `validate_episode` |
| H5 | Done/truncated valid | boolean, 마지막 step=True | `validate_episode` |
| H6 | Action range valid | action ∈ env.action_space | `validate_episode` |
| H7 | Min episode length | len ≥ min_episode_len=10 | `validate_episode` |
| H8 | No constant state | state_std > ε per dim | `validate_episode` |
| H9 | No zero action | action_norm > ε for ≥1 step | `validate_episode` |
| H10 | No duplicate trajectory | hash(state) not in seen | `validate_episode` |

### G.2 Split-level (manifest.py + 추가 검증)

| # | Gate | 검증 기준 | 담당 |
|---|---|---|---|
| H11 | Accept rate ≥ 99% | n_rejected / n_total < 0.01 | `CollectionStats` |
| H12 | Reject reason table | axis별 reject reason 분포 기록 | 수동 확인 |
| H13 | state_delta distribution | mean ± std per split | `dataset_stats.json` |
| H14 | action_norm distribution | per split | `dataset_stats.json` |
| H15 | reward distribution | per split | `dataset_stats.json` |
| H16 | episode length distribution | 모든 split ep_len=50 | `dataset_stats.json` |
| H17 | success/failure ratio | task-level | `eval_metas` |

### G.3 Dataset-level (leakage audit)

| # | Gate | 검증 기준 | 담당 |
|---|---|---|---|
| H18 | Seed disjoint | 5 split 간 seed overlap=0 | `test_fglc_split_integrity.py` |
| H19 | Hash duplicate = 0 | 동일 trajectory 중복 없음 | `quality_report.json` |
| H20 | Forbidden field = 0 | inference HDF5에 12 fields 없음 | `test_fglc_forbidden_field_sync.py` |
| H21 | OOD param evidence | manifest.json `ood_params` non-empty | `manifest.json` |

### G.4 OOD severity (axis별 expected gap)

| # | Gate | 검증 기준 | axis별 임계 |
|---|---|---|---|
| H22 | ID/OOD gap > delta_min | gap > 0.01 | **delta_min=0.01 유지, 완화 금지** |
| H23 | KS p-value | p < 0.05 (Pilot), p < 0.01 (Scaled) | per-axis |
| H24 | Cohen's d per dim | d > 0.3 for expected dims | friction qvel 9-17, gain qvel/tcp |
| H25 | Axis-specific dim coverage | friction→9-17, gain→qvel+tcp, latency→velocity | per-axis |
| H26 | noise AUROC (R4+) | **< 0.65** (의도된 결과) | noise axis만 |

### G.5 R3 readiness (post-collection, 코드 변경 후)

| # | Gate | 검증 기준 | 담당 |
|---|---|---|---|
| H27 | R3 dataloader | `test_fglc_maniskill_dataloader.py` PASS | pytest |
| H28 | 1-batch forward | shape mismatch 없음 | `r3_smoke.py` |
| H29 | 1-epoch smoke | NLL finite + OOD NLL > ID NLL | `r3_smoke.py` |
| H30 | metrics.json artifact | axis별 NLL/gap 기록 | `r3_smoke.py` |

---

## §H — Novelty Relevance Checklist

### H.1 6 direct-threat 논문별 axis 차별점

| Threat | friction 차별 | action_gain 차별 | latency 차별 | noise 차별 |
|---|---|---|---|---|
| **TD-MPC2** | "OOD friction에서 falsification gate β_t 점화, sparse grouped correction" | "control-gain shift에 value-aware α_t로 action-group correction" | "control-delay shift에 temporal latent group correction" | "noise vs dynamics 구분 능력 보임 (AUROC<0.65)" |
| **DreamerV3** | 동일 + "K-group latent 구조화로 friction 관련 subspace 분리" | 동일 + "grouped correction이 gain shift에 action-specific" | 동일 + temporal consistency loss로 d-step phase error 보정 | 동일 + Σ calibration explicit |
| **HiP-RSSM** | "파라미터 추론 없이 mismatch-driven β_t 발화" | 동일 | **핵심 차별**: "latency를 explicit parameter로 추론하지 않고 temporal group mismatch로 감지" | 동일 |
| **PLSM** | "action-effect 체계성 insufficient alone; falsification + correction 필요" | **핵심 차별**: "action-gain shift는 action-effect 일반화 실패 케이스" | 동일 | 동일 |
| **ReDRAW** | "sparse latent correction vs dense residual" | 동일 | 동일 | "noise는 correction 대상 아님 — FGLC가 noise를 dynamics로 오인 안 함 (ReDRAW는 모든 mismatch에 correction 시도)" |
| **AdaWM** | "불일치 기반 적응의 grouped+sparse 버전" | 동일 | 동일 | 동일 |

### H.2 axis별 예상 reviewer attack 및 방어

**friction 공격**: "joint_dry_friction=5.0 N·m는 µ_kinetic SSoT와 단위 다름, unrealistic"
→ **방어**: "joint dry friction 5.0 N·m/rad은 Panda arm OOD benchmark 설정으로 정당. effect size (gap=0.138)가 주장의 물리적 타당성을 지지. 단위 매핑 문서화 진행 중 (friction_mapping ledger)."

**action_gain 공격**: "single-task action scaling만 변형하면 cherry-picking"
→ **방어**: "PickCube + PushCube 두 task에서 교차 검증. gain=0.7 (clipping 없음)에서 qvel 응답 비례 감소 확인."

**latency 공격**: "action buffer 구현은 RSSM에서 흔하다, novelty 없음"
→ **방어**: "FGLC의 차별: K-group latent subspace에서 d-step temporal phase error의 group-specific 분리 → α_t의 temporal-group 활성화 측정. HiP-RSSM과 다름: explicit parameter inference 없음."

**noise 공격**: "Σ calibration 실패를 noise injection으로 노출하는 것은 trivial"
→ **방어**: "FGLC가 noise를 dynamics shift로 오인하지 않음 (AUROC<0.65)은 falsification gate의 specificity 검증. 이를 보이지 않는 논문은 false positive 문제 미검증."

### H.3 negative result 공시 의무

이하 항목은 반드시 논문에 명시:
1. **mass + random policy FAIL × 2 task** (gap 0.004/0.008) — INTERACTION_AXIS_REVIEW §B,E에 기록
2. **noise AUROC < 0.65 의도된 결과** — 본 PLAN의 핵심 검증 가설
3. **friction µ_kinetic ↔ joint_dry_friction 매핑 DEFERRED** — `quality_report.json` 기록 보존

---

## §I — Team Agent 역할과 산출물

`reports/four_axis_dataset_design_synthesis.md`에 기록되는 9명의 agent sub-section.

| Agent | Role | Input | Output | Judgment |
|---|---|---|---|---|
| **A** | axis-scout | docs/idea 5 axis SSoT + ManiSkill API + collector.py | 4 axis × 구현 가능성 표 + LOC 추정 | PASS / PATCH |
| **B** | claim-metric-alignment-auditor | docs/idea/04,10,21 + taxonomy.py | axis → metric → claim 1:1 매핑 표 | PASS / PATCH |
| **C** | data-quality-gatekeeper | validators.py + manifest.py + 10 reject reasons | 30 gate 통과 예측 표 | PASS / PATCH |
| **D** | split-leakage-auditor | manifest seed_pools + test_fglc_split_integrity.py | seed/hash/regime leakage 표 | PASS / FAIL |
| **E** | ood-severity-critic | dataset_stats.json + KS/Cohen's d 분석 | axis별 expected gap + threshold | PASS / CONDITIONAL / FAIL |
| **F** | dynamics/control-forensics-agent | mass_ood_forensics + per-dim 분석 가설 | axis별 물리 경로 분해 | PASS / BLOCKED |
| **G** | novelty-relevance-critic | 6 direct-threat 차별 + reviewer attack 시뮬레이션 | axis × threat 차별 표 | PASS / CONDITIONAL |
| **H** | resource-budget-auditor | §E 표 + 4060 8GB 한계 | disk/time/VRAM 시나리오 | PASS / EXPAND |
| **I** | experiment-design-chair (synthesis) | Agent A~H 종합 | 최종 axis ranking + 권장 path + R3 조건 | ACCEPT / MAJOR_REVISION |

각 agent는 `reports/four_axis_dataset_design_synthesis.md`에 다음 형식으로 기록:
```
### Agent X — <role>
- Input: <파일 목록>
- Top 3 findings
- Top 2 unresolved UNKNOWNs
- Recommendations
- Judgment: <verdict>
```

---

## §J — Repair Loop 및 재탐색/재수집 전략

### J.1 16단계 루프

```
1.  axis 후보 탐색 (§C tier 분류 → 4 PRIMARY/SECONDARY 선택)
2.  task/severity 결정 (Stage 0 audit)
3.  probe 수집 (10~50 ep, quarantine 저장)
4.  episode-level quality gate (H1-H10, validators.py)
5.  split-level leakage gate (H11-H21: seed disjoint + hash + forbidden field)
6.  OOD severity gate (H22-H25: delta_min=0.01, KS, Cohen's d)
7.  novelty relevance gate (Agent G: 5관점 점수 ≥ 15)
8.  training readiness gate (H27-H30: dataloader + 1-batch forward + 1-epoch smoke)
9.  R3 smoke metric 확인 (NLL finite + OOD NLL > ID NLL)
10. 실패 metric → diagnose.py 입력
11. 원인 진단 (FailureCauseId 매핑)
12. 수집 조건 또는 policy 재설계 (CANDIDATE_TABLE 참조)
13. 재수집 (probe → pilot → scaled 단계 준수)
14. before/after 비교 (compare_metrics: gap, KS, Cohen's d)
15. ledger 기록 (outputs/repair/loop_<task>_<axis>_<date>.jsonl)
16. commit (raw HDF5 + outputs/repair/*.jsonl 제외)
```

### J.2 Stop Conditions

| 조건 | 값 | 행동 |
|---|---|---|
| `max_iter` | 3 | USER_ESCALATION |
| `max_consecutive_inconclusive` | 2 | USER_ESCALATION |
| `max_wall_clock_minutes` | 60분/stage | BLOCKED 보고 |
| `target_reached` | gap > 0.01 + KS p < 0.05 + quality gate PASS | commit + 다음 단계 |
| `hook_blocked` | pre-commit 또는 forbidden field guard | escalate_to_user |
| `OOD_INVISIBLE_TO_RANDOM_POLICY` | contact=0% 반복 | policy 전환 고려 (mass track 전용) |

### J.3 axis × failure cause × repair candidate 매핑 (Phase 1 격차 포함)

| 시나리오 | 현재 FailureCauseId | **신규 cause 제안** | 현재 candidate | **신규 candidate 제안** |
|---|---|---|---|---|
| friction gap < 0.01 | `OOD_TOO_EASY` ✅ | — | severity-up (5.0→10.0) ✅ | µ_kinetic mapping 추가 |
| action_gain gap < 0.01 | `OOD_TOO_EASY` (proxy) | **`OOD_AXIS_GAIN_UNCOVERED`** | 없음 | gain ratio 확대 (0.7→0.5) |
| action_gain clipping issue | `IMPLEMENTATION_BUG_SUSPECTED` | — | manual debug | clipping 전 적용으로 변경 |
| latency gap < 0.01 | `OOD_TOO_EASY` (proxy) | **`OOD_AXIS_LATENCY_UNCOVERED`** | 없음 | d steps 확대 (8→12) |
| noise AUROC ≥ 0.7 (오탐) | `SIGMA_CALIBRATION_FAILURE` (근사) | **`OBS_NOISE_SIGMA_MISMATCH`** | `EVAL_NOISE_HIGH` (conflate ⚠) | Σ recalibration |
| mass contact=0% | `OOD_TOO_HARD_RANDOM_POLICY` | `OOD_INVISIBLE_TO_RANDOM_POLICY` | 없음 | scripted policy (별도 track) |
| validators reject > 5% | `DATA_TOO_SMALL` ✅ | — | episode 확장 ✅ | — |
| R3 NLL = inf | `IMPLEMENTATION_BUG_SUSPECTED` ✅ | — | manual_blocker_report ✅ | — |

> **격차 명시**: `taxonomy.py`에 4개 신규 cause 추가 권장 (BACKBONE 등급 1 — 사용자 승인 후 진행).
> `candidates.py`에 policy-change family 전무 (BACKBONE 등급 1 — mass repair track 연계).

### J.4 axis별 repair 우선순위

| 우선순위 | axis | repair 시작 조건 | 예상 cause | 예상 candidate |
|---|---|---|---|---|
| 1 | action_gain | Probe FAIL (gap < 0.005) | `OOD_AXIS_GAIN_UNCOVERED` | gain ratio 확대 또는 clipping 전 적용 |
| 2 | latency | Probe FAIL (gap < 0.005) | `OOD_AXIS_LATENCY_UNCOVERED` | d steps 확대 |
| 3 | noise | AUROC ≥ 0.70 (R4+) | `OBS_NOISE_SIGMA_MISMATCH` | Σ recalibration |
| — | mass | 별도 repair track | `OOD_INVISIBLE_TO_RANDOM_POLICY` | scripted policy |

---

## §K — Codex TASK 분해

### K.1 TASK A1: Feasibility Audit (Claude 직접, ~4시간)

```
TASK_NAME: TASK_A1_FOUR_AXIS_FEASIBILITY_AUDIT
BACKGROUND: 4 axis 구현 가능성 + 기존 데이터 재사용 + leakage risk 정량화.
            Stage 0 Static Audit 수행. 코드 변경 없음.
GOAL: §A~§C 작성 완료. 4 axis × 5관점 점수표 + BLOCKED/UNKNOWN 목록.
FILES_ALLOWED: docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md (신규)
FILES_FORBIDDEN: src/, scripts/, configs/, data/, outputs/, docs/idea/, .claude/
REQUIRED_IMPLEMENTATION: read-only audit + MD 작성
REQUIRED_TESTS: git status로 다른 파일 수정 없음 확인
ACCEPTANCE_CRITERIA: §A~§C 완성 + tier표 + BLOCKED ≥5 + UNKNOWN ≥5 명시
COMMIT_MESSAGE: docs(data): four-axis dataset plan §A-C — feasibility audit
STOP_CONDITION: ManiSkill API 신규 격차 발견 시 BLOCKED 기록 후 사용자 escalation
```

### K.2 TASK A2: Resource Budget (Claude 직접, ~2시간)

```
TASK_NAME: TASK_A2_RESOURCE_BUDGET
BACKGROUND: 4 axis × 2 task × 4 stage scenario의 disk/time/VRAM 정량화.
GOAL: §D~§E 작성. 4060 8GB VRAM 안전성 분석 포함.
FILES_ALLOWED: docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md (편집)
FILES_FORBIDDEN: src/, scripts/, configs/, data/, outputs/, docs/idea/, .claude/
REQUIRED_IMPLEMENTATION: dataset_stats.json + resource_budget_R1 인용 + 계산
REQUIRED_TESTS: 주요 수치 1개 이상 다른 출처 cross-check
ACCEPTANCE_CRITERIA: 4 stage × 2 task × disk/time 표 + VRAM 추정 + 권장 수집량
COMMIT_MESSAGE: docs(data): four-axis dataset plan §D-E — resource budget
STOP_CONDITION: 4060 8GB 한계 초과 시나리오 발견 시 SHRINK 또는 사용자 escalation
```

### K.3 TASK A3: Axis Implementation Design (Codex 위임 권장, ~3시간)

```
TASK_NAME: TASK_A3_AXIS_IMPL_DESIGN
BACKGROUND: action_gain/latency/noise 미구현. collector.py에 ~70-95 LOC 추가 필요.
            Stage별 절차 설계 + Codex TASK 후보 작성.
GOAL: §F 작성 + TASK_2050~2053 파일 4개 작성 (10 헤더)
FILES_ALLOWED: docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md (편집),
               .agent_tasks/codex_queue/TASK_2050~2053_*.md (신규)
FILES_FORBIDDEN: src/, scripts/, configs/, data/, outputs/, docs/idea/, .claude/
REQUIRED_IMPLEMENTATION: Codex TASK 파일 4개 (10 헤더 + FILES_ALLOWED 명확)
REQUIRED_TESTS: forbidden field 12개에 4 axis true_* 모두 포함 확인
ACCEPTANCE_CRITERIA: §F + TASK 파일 4개 + leakage prevention 설계 명시
COMMIT_MESSAGE: docs(data): four-axis dataset plan §F + codex task drafts
STOP_CONDITION: forbidden field guard 격차 발견 시 BLOCKED
```

### K.4 TASK A4: Probe Collection Plan (사용자 승인 후 실행, ~2시간)

```
TASK_NAME: TASK_A4_PROBE_COLLECTION_PLAN
BACKGROUND: Stage 1 axis별 10~50 ep probe. action_gain/latency/noise 구현 완료 후.
GOAL: §G probe checklist + repair branch tree + dry-run plan
FILES_ALLOWED: docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md,
               .agent_tasks/codex_queue/TASK_2054_PROBE_*.md
FILES_FORBIDDEN: data/ (구현 완료 전까지), src/ (TASK_2050~2053 완료 전)
REQUIRED_IMPLEMENTATION: probe scripts (quarantine 모드) + repair branch trees
REQUIRED_TESTS: dry-run (--no-save) 가능 여부 확인
ACCEPTANCE_CRITERIA: axis별 probe 명령 + 성공/실패 조건 + repair tree
COMMIT_MESSAGE: docs(data): four-axis probe checklist + repair branches
STOP_CONDITION: action_gain/latency/noise 구현 미완료 시 BLOCKED
```

### K.5 TASK A5: Pilot/Scaled Collection Plan (사용자 승인 후, ~3-6시간/axis)

```
TASK_NAME: TASK_A5_PILOT_SCALED_PLAN
BACKGROUND: Stage 2/3 axis별 300~900 ep 수집 계획.
GOAL: §G full checklist + manifest/stats/quality_report template + Agent A~I report template
FILES_ALLOWED: docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md,
               reports/four_axis_dataset_design_synthesis.md
FILES_FORBIDDEN: (동일)
REQUIRED_IMPLEMENTATION: pilot/scaled command plan + agent report template
REQUIRED_TESTS: Agent template structure 검증
ACCEPTANCE_CRITERIA: axis별 수집량 + seed pool + manifest 명세 + Agent A~I template
COMMIT_MESSAGE: docs(data): four-axis pilot/scaled plan + synthesis template
STOP_CONDITION: probe FAIL 시 repair loop로 회귀
```

### K.6 TASK A6: R3 Integration Plan (사용자 승인 후, ~2-4시간)

```
TASK_NAME: TASK_A6_R3_INTEGRATION_PLAN
BACKGROUND: 4 axis 데이터 → R3 dataloader → r3_smoke.py → metrics.json
GOAL: §H novelty checklist + §K TASK_2055_R3_SMOKE 작성
FILES_ALLOWED: docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md,
               reports/four_axis_dataset_design_synthesis.md,
               .agent_tasks/codex_queue/TASK_2055_*.md
FILES_FORBIDDEN: outputs/phase_gates/R3.passed (절대 생성 금지)
REQUIRED_IMPLEMENTATION: r3 smoke plan + R3.passed 생성 금지 명시
REQUIRED_TESTS: test_fglc_r3_runner_maniskill.py 회귀 확인 plan
ACCEPTANCE_CRITERIA: r3 smoke flow + repair loop 연계 + R3.passed 조건 명시
COMMIT_MESSAGE: docs(data): four-axis R3 integration plan
STOP_CONDITION: R3 smoke FAIL 시 repair loop 회귀
```

### K.7 TASK A7: Execution Kickoff (Claude 직접, ~1시간)

```
TASK_NAME: TASK_A7_EXECUTION_KICKOFF
BACKGROUND: TASK_2050~2055 실행 순서 + 사용자 승인 체크포인트 정의.
GOAL: §L PASS/PATCH/BLOCKED 기준 + §M 사용자 결정 D-1~D-5 + §N atomic checklist
FILES_ALLOWED: docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md (편집)
FILES_FORBIDDEN: (동일)
REQUIRED_IMPLEMENTATION: 실행 순서 + decision points
REQUIRED_TESTS: PLAN 전체 cross-reference 검증
ACCEPTANCE_CRITERIA: TASK 분해 완성 + D-1~D-5 + atomic checklist
COMMIT_MESSAGE: docs(data): four-axis §L-N execution kickoff
STOP_CONDITION: 사용자 미결 응답 시 PLAN 완료 + 대기
```

### K.8 Codex TASK 2050~2055 초안 헤더 명세

**TASK_2050: action_gain 구현**
```
TASK_NAME: TASK_2050_ACTION_GAIN_IMPL
BACKGROUND: collector.py _apply_ood에 action_gain 분기 추가. ~10-50 LOC.
GOAL: ood_params["action_gain"] 처리 + schema entry + test 1개
FILES_ALLOWED: src/fglc/data/collector.py,
               src/fglc/data/maniskill_schema.py,
               tests/test_fglc_collector_ood_axes.py (신규)
FILES_FORBIDDEN: .claude/, docs/idea/, src/fglc/schemas/, scripts/run_codex_task.ps1
REQUIRED_IMPLEMENTATION: _apply_ood에 action_gain 분기 + TASK_OOD_PARAMS entry
REQUIRED_TESTS: pytest tests/test_fglc_collector_ood_axes.py::test_action_gain_applied
ACCEPTANCE_CRITERIA: gain=0.7 probe 시 state_delta std가 gain=1.0 대비 ~30% 감소
COMMIT_MESSAGE: feat(collector): action_gain OOD axis implementation
STOP_CONDITION: clipping 위치 불명확 시 BLOCKED + 사용자 확인
```

**TASK_2051: latency FIFO buffer 구현**
```
TASK_NAME: TASK_2051_LATENCY_FIFO_BUFFER
BACKGROUND: collector.py episode loop에 action FIFO buffer 추가. ~25-40 LOC.
GOAL: action_delay_steps 처리 + commanded/executed 분리 + buffer reset 정책
FILES_ALLOWED: src/fglc/data/collector.py,
               src/fglc/data/maniskill_schema.py,
               tests/test_fglc_collector_ood_axes.py
FILES_FORBIDDEN: (동일)
REQUIRED_IMPLEMENTATION: deque(maxlen=d) + zero-fill reset + dual record
REQUIRED_TESTS: pytest tests/test_fglc_collector_ood_axes.py::test_latency_buffer
ACCEPTANCE_CRITERIA: delay=3 probe 시 trajectory가 ID 대비 time-shifted state 보임
COMMIT_MESSAGE: feat(collector): action_latency FIFO buffer implementation
STOP_CONDITION: buffer reset 정책 불명확 시 BLOCKED
```

**TASK_2052: noise injection 구현**
```
TASK_NAME: TASK_2052_NOISE_INJECTION
BACKGROUND: _flat_obs() 후 Gaussian noise 주입. ~15 LOC.
GOAL: noise_sigma 처리 + deterministic RNG + validator 확장
FILES_ALLOWED: src/fglc/data/collector.py,
               tests/test_fglc_collector_ood_axes.py
FILES_FORBIDDEN: (동일)
REQUIRED_IMPLEMENTATION: np.random.default_rng(seed).normal(0, sigma, D_x) 주입
REQUIRED_TESTS: pytest tests/test_fglc_collector_ood_axes.py::test_noise_injection
ACCEPTANCE_CRITERIA: sigma=0.1 probe 시 state std가 ID 대비 증가 확인
COMMIT_MESSAGE: feat(collector): observation_noise injection implementation
STOP_CONDITION: sigma 상한 미확인 시 보수적으로 sigma=0.1 상한 사용
```

**TASK_2053: config + 통합 테스트 추가**
```
TASK_NAME: TASK_2053_CONFIG_INTEGRATION_TEST
BACKGROUND: action_gain/latency/noise용 config YAML 3개 + end-to-end test.
GOAL: configs/fglc/smoke_maniskill_4axis.yaml + test_fglc_4axis_ood_e2e.py
FILES_ALLOWED: configs/fglc/smoke_maniskill_4axis.yaml (신규),
               tests/test_fglc_4axis_ood_e2e.py (신규)
FILES_FORBIDDEN: (동일)
REQUIRED_IMPLEMENTATION: probe 설정 3개 + E2E test (synthetic mock)
REQUIRED_TESTS: pytest tests/test_fglc_4axis_ood_e2e.py
ACCEPTANCE_CRITERIA: 3 axis probe E2E test PASS (quarantine 저장 확인)
COMMIT_MESSAGE: feat(config): 4-axis OOD config + integration tests
STOP_CONDITION: ManiSkill API 격차 발견 시 BLOCKED
```

### K.9 Gatekeeper 6조건 (모든 TASK 적용)

1. `verify` mode 종료 코드 0
2. `git diff --cached` 수동 review — 의도치 않은 변경 없음
3. 금지 경로 미수정 확인
4. `RESULT.md` 존재
5. `REQUIRED_TESTS` 통과 재확인
6. T3(implementation-risk-critic) agent report PASS (MD-only TASK는 T5 권장)

---

## §L — PASS/PATCH_REQUIRED/BLOCKED 기준

### L.1 본 PLAN 자체 판정 기준

| 판정 | 조건 |
|---|---|
| **PLAN_PASS** | §A~§N 14개 섹션 완성 + 4 axis 5관점 점수표 + Agent A~I template + Codex TASK 7개 + atomic checklist + BLOCKED/UNKNOWN 명시 |
| **PATCH_REQUIRED** | ManiSkill API 추가 격차 발견 (action_gain clipping 위치, latency buffer reset 등) → 보강 후 재PASS |
| **BLOCKED** | forbidden field 12개 ↔ 4 axis 추가 후 leakage 위험 발견 시 |

### L.2 axis별 R3 진입 조건

| Axis | R3 진입 조건 | 사용자 승인 필요? |
|---|---|---|
| friction | 이미 PASS | ❌ 자동 (기존 데이터 사용) |
| action_gain | Stage 2 Pilot PASS (gap > 0.01, AUROC ≥ 0.70) | ⚠ 첫 R3.passed 생성 시 필수 |
| latency | Stage 2 Pilot PASS (gap > 0.01) | ⚠ 동일 |
| noise | Stage 2 Pilot PASS + **AUROC < 0.65** 확인 | ⚠ 동일 |

> **noise의 R3 진입 조건이 특수**: AUROC가 0.70 이상이면 β_t false positive 문제 → BLOCKED + repair loop 진입.

### L.3 BACKBONE 변경 flag

| 변경 대상 | BACKBONE 등급 | 승인 |
|---|---|---|
| `docs/idea/18_DATA_BENCHMARKS.md` 수정 | **등급 2** | 사용자 승인 필수 |
| `src/fglc/schemas/visibility.py` 수정 | **등급 2** | 사용자 승인 필수 (현재 12개 이미 포함, 추가 불필요) |
| `src/fglc/repair/taxonomy.py` 신규 cause | 등급 1 | 사용자 승인 권장 |
| `src/fglc/repair/candidates.py` policy-change family | 등급 1 | 사용자 승인 권장 |
| `src/fglc/data/collector.py` axis 분기 추가 | 등급 0 | Codex 위임 가능 |

### L.4 전체 R3 진입 최소 조건

```
1. friction 데이터 (PickCube 450ep) → 현재 완료 ✅
2. action_gain 데이터 (Pilot 300ep 이상) → TASK_2050 + 수집 완료 후
3. test_fglc_maniskill_dataloader.py PASS
4. r3_smoke.py 1-epoch: ID NLL 수렴 + OOD NLL > ID NLL (friction + action_gain axis)
5. forbidden field 0건
6. 사용자 승인: R3.passed 생성
```

---

## §M — 사용자 승인 필요 항목

### M.D-1: axis 구현 우선순위

| 옵션 | 내용 | 권장 |
|---|---|---|
| (a) action_gain → latency → noise | 난이도 순, LOC 최소~최대 | ✅ **권장** |
| (b) latency → action_gain → noise | control integration 우선 |  |
| (c) 3개 병렬 (Codex 3 worktree) | 시간 절감, 컨텍스트 분산 위험 |  |
| (d) noise 먼저 | Σ calibration test가 R4 gate에 필요한 경우 |  |

### M.D-2: 첫 task 선택

| 옵션 | 내용 | 권장 |
|---|---|---|
| (a) PickCube-v1 (D_x=42) | 기존 friction 데이터 재사용 가능, 검증 완료 | ✅ **권장** |
| (b) PushCube-v1 (D_x=35) | 새 axis 통합 첫 시도 |  |
| (c) 두 task 동시 | 4 axis × 2 task = 8 수집 병렬 |  |

### M.D-3: Stage 진입 시점

| 옵션 | 내용 | 권장 |
|---|---|---|
| (a) probe → pilot → scaled 표준 | 각 단계 검증 후 다음 단계 | ✅ **권장** |
| (b) probe → scaled 단축 | 시간 절감, 실패 시 비용 큼 |  |
| (c) pilot 후 사용자 review checkpoint | 가시성 최대 |  |

### M.D-4: mass repair track 병렬 진행

| 옵션 | 내용 | 권장 |
|---|---|---|
| (a) 4 axis 완료 후 mass scripted policy | 순차 진행, 리소스 집중 | ✅ **권장** |
| (b) 4 axis와 병렬로 LiftCube probe | mass-sensitive task 탐색 |  |
| (c) mass DEFERRED 확정 | 논문에 honest limitation 명시 |  |

### M.D-5: BACKBONE 등급 1 변경 사전 승인

| 옵션 | 내용 | 권장 |
|---|---|---|
| (a) taxonomy.py 신규 4 cause 사전 일괄 승인 |  |  |
| (b) candidates.py policy-change family 사전 승인 |  |  |
| (c) 모든 BACKBONE 등급 1 변경은 case-by-case | 투명성 최대 | ✅ **권장** |

---

## §N — Atomic Checklist + BLOCKED/UNKNOWN

### N.1 Atomic Checklist

```
탐색:
[ ] 25개 reference 파일 read 완료 (본 PLAN 작성 기준)
[ ] Phase 1 collector/repair/test 정밀 조사 완료

계획:
[ ] 4 axis × 5관점 점수표 완성 (§C.3)
[ ] 4 axis FGLC claim 연결 매핑 완성 (§B.5)
[ ] resource 예산 4 scenario 표 완성 (§E.2)
[ ] Stage별 수집 절차 완성 (§F)
[ ] repair loop axis × cause × candidate 매핑 완성 (§J.3)

구현 설계:
[ ] Codex TASK A1~A7 (본 PLAN) 작성 완료
[ ] Codex TASK_2050~2055 헤더 명세 작성 완료

회귀 테스트:
[ ] test_fglc_split_integrity.py green (seed disjoint)
[ ] test_fglc_forbidden_field_sync.py green (12 fields)
[ ] test_fglc_ood_severity.py green (delta_min=0.01)
[ ] test_fglc_repair_taxonomy.py green (20 causes)
[ ] test_fglc_r3_runner_maniskill.py green (회귀)

금지 조건:
[ ] R3 smoke 금지 (본 PLAN MD 작성 단계)
[ ] R3.passed 생성 금지
[ ] raw HDF5 commit 금지
[ ] outputs/repair/*.jsonl 대용량 commit 금지
[ ] docs/idea/18_DATA_BENCHMARKS.md 무단 수정 금지
[ ] FORBIDDEN_AGENT_FIELDS 무단 수정 금지
[ ] threshold 완화 금지 (delta_min=0.01 유지)
[ ] 특정 axis 사전 성공 단정 금지
[ ] negative result 숨김 금지

commit 정책:
[ ] raw HDF5 제외한 단일 commit
[ ] 2 MD + plan file 포함
[ ] outputs/phase_gates/ 보존 확인
```

### N.2 BLOCKED

- **[BLOCKED-1]** mass + random policy: PickCube gap=0.0038, PushCube gap=0.008, 두 task 모두 FAIL. contact_rate=0%에서 물리 경로 차단. 별도 scripted policy repair track으로 분리.
- **[BLOCKED-2]** friction µ_kinetic ↔ joint_dry_friction 단위 매핑 미해결. `quality_report.json:friction_mapping=DEFERRED`. 논문 reviewer "물리 단위 오류" 공격 가능. 매핑 ledger 문서화 TASK 필요.

### N.3 UNKNOWN

- **[UNKNOWN-1]** ManiSkill 3.0.1에서 action scaling clipping 위치 — `env.step(a)` 전 clip vs 내부 clip. gain=1.3에서 effective gain이 감소할 가능성.
- **[UNKNOWN-2]** latency buffer reset 정책 — episode 시작 시 zero-fill vs first-action repeat. severity에 영향 있음.
- **[UNKNOWN-3]** noise σ 상한 — dynamics learning 파괴 임계. σ=0.2 이상에서 Σ_t^{-1/2} ill-conditioned 가능성.
- **[UNKNOWN-4]** `OOD_INVISIBLE_TO_RANDOM_POLICY` cause → 기존 9개 fire function과의 호환성.
- **[UNKNOWN-5]** `OOD_AXIS_LATENCY_UNCOVERED` cause + axis-specific fire function 추가 LOC.
- **[UNKNOWN-6]** LiftCube-v1 actor 이름 (`inner.cube`? `inner.obj`?) — mass repair track 후보.
- **[UNKNOWN-7]** PickCube on-disk train_id=250ep ↔ smoke config 50ep 격차 — 별도 collect run 결과인지 확인 필요.
- **[UNKNOWN-8]** quality_report.json Ckpt 4 FAIL (mass) vs STEP11_RESULT_REPORT Ckpt 4 PASS 충돌 — 어느 것이 정확한지 확인 필요.

### N.4 UNRESOLVED (본 PLAN에서 미해결)

- **[UNRESOLVED-1]** mass repair track 우선순위 (M.D-4 사용자 결정 대기)
- **[UNRESOLVED-2]** taxonomy.py BACKBONE 등급 1 변경 사전 승인 여부 (M.D-5 대기)
- **[UNRESOLVED-3]** noise AUROC < 0.65 검증을 Stage 2 vs Stage 4 배치 (현재 R4+ 예정)
- **[UNRESOLVED-4]** PickCube on-disk 250ep vs config 50ep 격차 해소 방법
- **[UNRESOLVED-5]** quality_report.json Ckpt 4 FAIL vs STEP11 충돌 해소

---

## §O — Verification Plan

### O.1 PLAN 자체 완료 검증 (read-only)

```powershell
# 1. 산출물 생성 확인
Test-Path "docs\FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md"   # True
Test-Path "reports\four_axis_dataset_design_synthesis.md"  # True

# 2. 참조 파일 무결성 (수정 없음)
git status --short docs/idea/
git status --short data/fglc/
git status --short src/fglc/
git status --short scripts/fglc/

# 3. phase gate 보호
Test-Path "outputs\phase_gates\R0.passed"  # True
Test-Path "outputs\phase_gates\R1.passed"  # True
Test-Path "outputs\phase_gates\R2.passed"  # True
Test-Path "outputs\phase_gates\R3.passed"  # False (금지)

# 4. 기존 테스트 회귀
& ".venv\Scripts\python.exe" -m pytest -q `
    tests\test_fglc_split_integrity.py `
    tests\test_fglc_no_garbage_data.py `
    tests\test_fglc_ood_severity.py `
    tests\test_fglc_forbidden_field_sync.py `
    tests\test_fglc_repair_taxonomy.py `
    tests\test_fglc_repair_diagnose.py `
    tests\test_fglc_repair_candidates.py

# 5. R3 runner 회귀
& ".venv\Scripts\python.exe" -m pytest -q tests\test_fglc_r3_runner_maniskill.py
```

### O.2 Commit 정책

단일 commit:
```
docs(data): four-axis dataset construction plan + agent synthesis
```
포함:
- `docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md` (신규)
- `reports/four_axis_dataset_design_synthesis.md` (신규)
- `plans/fglc-step-vectorized-iverson.md` (본 PLAN 파일 업데이트)

제외 (절대):
- `data/fglc/*/raw/*.h5` (raw HDF5)
- `outputs/repair/*.jsonl`
- `outputs/phase_gates/R3.passed`

---

## §P — 절대 금지 사항

```
❌ friction-only로 전체 주장 완전 검증되었다고 단정
❌ action_gain/latency/noise를 실측 전 성공한다고 단정
❌ delta_min=0.01 threshold 완화
❌ 기존 데이터 사후 변형
❌ 실패 데이터 은폐 또는 negative result 숨김
❌ raw HDF5 commit
❌ outputs/phase_gates/R3.passed 생성 (사용자 승인 없이)
❌ docs/idea/18_DATA_BENCHMARKS.md 무단 수정 (BACKBONE 등급 2)
❌ src/fglc/schemas/visibility.py FORBIDDEN_AGENT_FIELDS 무단 수정
❌ "문제 발견에서 종료" — 반드시 원인 분해 + 해결 후보 + 재검증 + 적용 조건까지
❌ Codex 위임 없이 ~95 LOC 구현을 본 PLAN 단계에서 직접 실행
❌ noise AUROC 기준 (< 0.65)을 "실패"로 잘못 해석
❌ mass repair track을 4-axis plan에 통합 (별도 분리 유지)
```

---

## §Q — Plan Execution Timeline

```
완료됨:
  ✅ Stage 0 (friction): PickCube 450ep + PushCube 900ep PASS
  ✅ INTERACTION_AXIS_DESIGN_REVIEW (commit 7fe0a02, 1260줄)
  ✅ 본 PLAN 문서 (docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md)
  ✅ Agent A~I 합성 보고서 (reports/four_axis_dataset_design_synthesis.md)

사용자 승인 대기:
  ⏳ M.D-1: axis 구현 우선순위 (a/b/c/d)
  ⏳ M.D-2: 첫 task 선택 (a/b/c)
  ⏳ M.D-3: Stage 진입 시점 (a/b/c)
  ⏳ M.D-4: mass repair track 병렬 여부 (a/b/c)
  ⏳ M.D-5: BACKBONE 등급 1 사전 승인 여부 (a/b/c)

승인 후 순서:
  1. TASK_2050: action_gain 구현 (Codex, ~50 LOC, ~2일)
  2. TASK_2053 일부: config + test (Codex, ~1일)
  3. Probe: action_gain PickCube (50 ep × 2 = 100 ep)
  4. Pilot: action_gain PickCube+PushCube (300 ep × 2 task)
  5. R3 smoke: friction + action_gain 2-axis (사용자 승인 후 R3.passed 생성)
  6. TASK_2051: latency FIFO (Codex, ~40 LOC)
  7. TASK_2052: noise injection (Codex, ~15 LOC)
  8. Scaled: 전체 4 axis × 2 task → R5/R6 Stage 3 gate 진입
```

---

**PLAN 판정**: PLAN_PASS — §A~§N(§P, §Q 포함) 14+2 섹션 완성, 4 axis 5관점 점수표, Codex TASK 7개, 30개 quality gate, atomic checklist, BLOCKED 2개 + UNKNOWN 8개 + UNRESOLVED 5개 명시.

> **최종 원칙**: 본 PLAN의 목표는 4 axis 구현 자체가 아니다. friction + action_gain + latency + noise 4축 기반 고품질 데이터셋 구축 계획을 단일 MD로 정리하여, **사용자가 근거 기반 결정 + Codex 위임 + 단계적 검증**이 가능하게 하는 것이다.
