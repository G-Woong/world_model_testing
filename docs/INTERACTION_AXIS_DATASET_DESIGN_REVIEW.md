# FGLC Interaction Axis Selection & High-Quality Dataset Design Review

> **작성일**: 2026-05-24 (post-PushCube mass FAIL, USER_ESCALATION 후)
> **Branch**: `memory-redesign-2026-05-16`
> **Phase**: R2 완료 → R3 진입 전 (R0/R1/R2 PASS, R3 PENDING)
> **상태**: REVIEW ONLY — 코드/데이터 변경 금지, 새 수집 금지, R3 smoke 금지, R3.passed 생성 금지
> **선행 작업**: PickCube 450ep + PushCube 900ep 수집 완료. 두 task 모두 mass OOD FAIL.
> **목적**: interaction axis × task × policy 3차원 설계 공간에서 FGLC 핵심 주장 검증 가능 조합을 메타 수준에서 재선택.

---

## §A — Executive Summary

### A.1 현재 상황 요약

2026-05-24 기준, R2 데이터 파이프라인 단계에서 두 task 모두에 걸쳐 **mass OOD axis가 random policy 조건에서 완전히 실패**했다. friction OOD는 두 task 모두에서 강하게 PASS되었다.

| Task | Axis | state_delta_norm gap | 판정 | 원인 |
|---|---|---|---|---|
| PickCube-v1 | friction | **0.138** | **PASS** | joint friction → qvel 직접 영향, 접촉 독립적 |
| PickCube-v1 | mass | 0.0038 | **FAIL** | contact_rate=0%, tcp_dist=0.999m |
| PushCube-v1 | friction | **0.124** | **PASS** | 동일 메커니즘 |
| PushCube-v1 | mass | 0.0080 | **FAIL** | random policy 저접촉 + obs_mode mismatch |

repair loop는 `consecutive_inconclusive` 종료, `next_action=USER_ESCALATION_BACKBONE_DECISION`으로 기록됨 (`outputs/repair/loop_pushcube_2026-05-24.jsonl`).

### A.2 핵심 문제 재정의

이는 단순한 "mass 파라미터 값" 문제가 아니다. **interaction axis × task × policy 3차원 설계 공간**에서 FGLC 핵심 주장(falsification gate β_t + sparse correction)을 검증할 수 있는 물리적 dynamics shift를 만들어야 한다.

- **friction axis**: 구현 완료, 두 task 모두 PASS — 즉시 R3 진입 가능한 PRIMARY axis
- **mass axis**: random policy에서 구조적으로 실패 — policy 전환 또는 task 재설계 없이는 BLOCKED
- **latency/noise/action_gain**: SSoT에 정의됨, 코드 구현 없음 (placeholder만)
- **R5/R6 요구**: Stage 3 gate가 "최소 2개 OOD 조건"에서 baseline 초과를 요구 (`docs/idea/12_TRAINING_STAGES.md`)

### A.3 권장 방향 3개 후보

- **Option 1 (friction-first)**: 즉시 friction 단독으로 R3 진행 + mass repair 병렬 트랙
- **Option 2 (contact-rich mass)**: scripted/expert policy로 mass 재수집 후 2-axis R3
- **Option 3 (multi-axis 확장)**: action_gain/latency/noise axis 구현 추가

사전 확정하지 않음 — §K에서 risk matrix 기반 비교 후 사용자 결정 위임.

---

## §B — Current Evidence Audit

### B.1 실측 evidence 목록

**PickCube-v1 (450ep, seed [42~650)):**

| Metric | train_id | ood_friction_low | ood_mass_low | 판정 |
|---|---|---|---|---|
| n_episodes | 250 | 50 | 50 | — |
| state_delta_norm_mean | 1.322009 | 1.183966 | 1.325756 | — |
| friction gap | — | **0.138043** | — | **PASS** |
| mass gap | — | — | 0.003747 | **FAIL** |
| contact_rate | 0.0% | 0.0% | 0.0% | (모두 동일) |
| reward_mean | 0.0504 | 0.0502 | 0.0510 | (유의미한 차이 없음) |
| D_x / D_a | 42 / 8 | 42 / 8 | 42 / 8 | — |

**PushCube-v1 (900ep, seed [1042~1999)):**

| Metric | train_id | ood_friction_low | ood_mass_low | 판정 |
|---|---|---|---|---|
| n_episodes | 500 | 100 | 100 | — |
| state_delta_norm_mean | 1.314 (추정) | 1.190 (추정) | 1.322 (추정) | — |
| friction gap | — | **0.124** | — | **PASS** |
| mass gap | — | — | 0.008 | **FAIL** (< 0.01) |
| D_x / D_a | 35 / 8 | 35 / 8 | 35 / 8 | — |

### B.2 repair ledger 요약

```jsonl
{
  "loop_id": "pushcube_mass_2026-05-24",
  "iter": 1,
  "diagnosed_cause": "OOD_TOO_HARD_RANDOM_POLICY_LOW_CONTACT_BOTH_TASKS",
  "result": "reject",
  "stop_condition_hit": "consecutive_inconclusive",
  "next_action": "USER_ESCALATION_BACKBONE_DECISION",
  "metrics_before": {"state_delta_norm_gap": 0.004, "task": "PickCube-v1"},
  "metrics_after":  {"state_delta_norm_gap": 0.008, "task": "PushCube-v1", "friction_gap": 0.124}
}
```

### B.3 evidence usability 분류

| 데이터 | 용도 | 신뢰도 |
|---|---|---|
| PickCube friction OOD (gap=0.138) | R3 학습 데이터 — PRIMARY | HIGH |
| PushCube friction OOD (gap=0.124) | cross-task friction evidence — SECONDARY | HIGH |
| PickCube mass OOD (gap=0.0038) | Negative result 보고용 — BLOCKED for training | HIGH (BLOCKED) |
| PushCube mass OOD (gap=0.008) | Negative result 보고용 — BLOCKED for training | HIGH (BLOCKED) |

### B.4 16개 metric 후보 평가 (mass axis)

Agent 1 (metric-validity-critic) 결론: **16개 metric 중 어떤 것도 현재 데이터에서 mass OOD를 신뢰할 수 있게 구분 못함.**

- state_delta_norm gap=+0.0038: 물리 신호 없음 (contact_rate=0%)
- object_pose_delta_norm gap=+0.000136: near-zero
- reward_mean Δ=+0.000581: KS p=0.108 (not significant)
- dim24 Cohen's d=1.034: 수치적 artifact (abs delta ~4e-6)
- **결론**: metric 교체로 해결 불가 — 물리 신호 자체가 없다

### B.5 질량 측정 불가 근본 물리 원인

```
B4: PickCube/PushCube + random policy → cube 접촉 동작 발생 안 함
    ↓
B1: contact_rate = 0%, tcp_dist = 0.999m (PickCube 실측)
    ↓
mass의 물리 경로(F=ma on object)가 차단됨
    ↓
mass=1.5 vs mass=0.064의 관측 trajectory가 사실상 동일
    ↓
gap = +0.004 (PickCube) / +0.008 (PushCube) < threshold 0.01 → FAIL
```

반면 friction은 `τ_effective = τ_motor - 5.0 × sign(qvel)`로 매 step 접촉 없이 작용 → qvel dims 9-17에서 20~32% std 변화 → gap=0.138.

---

## §C — Evaluation Criteria

### C.1 5관점 정의

| # | 관점 | 정의 | 측정 기준 |
|---|---|---|---|
| **C1** | Dynamics falsification strength | ID vs OOD에서 world model dynamics hypothesis가 깨지는 강도 | state_delta_norm gap, KS p-value, per-dim Cohen's d, predicted vs observed mismatch |
| **C2** | Action/value relevance | shift가 action/reward/success/planning decision에 미치는 영향 | reward distribution shift, success rate drop, planning Q-value variation |
| **C3** | Observability under state-only data | state vector만으로 residual/mismatch 관측 가능성 | per-dim variance, SNR, contact-related dims (qvel 13-15 등) |
| **C4** | Dataset controllability & quality | OOD parameter 안정 조작 + garbage/leakage 없는 수집 가능성 | ManiSkill API 안정성, validators.py 10 reject reasons 통과율, manifest 재현성 |
| **C5** | Paper defensibility & novelty relevance | 국제학회 리뷰어 관점 "의미 있는 dynamics shift"로 방어 가능 | 6 direct-threat 논문(TD-MPC2/DreamerV3/HiP-RSSM/PLSM/ReDRAW/AdaWM) 차별점 유지 |

### C.2 Scoring Rubric (1~5)

| 점수 | 의미 | Trigger |
|---|---|---|
| 1 | 거의 부적합 | gap < 0.005 OR API 미구현 OR reviewer rejection 명백 |
| 2 | 약함, 보조 evidence만 | gap 0.005~0.01 OR 구현 가능하나 unit 매핑 미해결 |
| 3 | 조건부 사용 가능 | gap 0.01~0.05 OR policy 변경 필요 OR threshold 경계 |
| 4 | 강함, 주요 실험 후보 | gap 0.05~0.15 OR 구현 완료 + PASS |
| 5 | 매우 강함 | gap > 0.15 OR cross-task replicated PASS OR direct-threat 차별 명확 |

### C.3 왜 이 5관점인가

- **C1-C2-C3**: FGLC 핵심 수식(falsification gate β_t + sparse correction α_t)이 작동할 물리적/통계적 기반
- **C4**: forbidden field leakage 없는 데이터 수집 운영 안전성
- **C5**: ICLR 수준 reviewer defensibility — TD-MPC2, DreamerV3, HiP-RSSM, PLSM, ReDRAW, AdaWM와의 차별점 유지

5개 모두 통과(합계 ≥ 20)해야 axis가 **PRIMARY tier**로 진입한다.

---

## §D — Interaction Axis Candidate Survey

### D.0 Cross-axis Comparison Matrix

| # | Axis | C1 | C2 | C3 | C4 | C5 | Total | Tier |
|---|---|---|---|---|---|---|---|---|
| 1 | joint_dry_friction | **5** | **4** | **5** | **5** | **4** | **23** | **PRIMARY** |
| 2 | action_gain | 4 | **5** | 4 | 3 | 4 | 20 | **PRIMARY** |
| 3 | action_latency | 4 | 4 | 4 | 3 | 4 | 19 | SECONDARY |
| 4 | observation_noise | 3 | 3 | 3 | 4 | 4 | 17 | SECONDARY |
| 5 | object_mass (random policy) | 1 | 1 | 1 | 5 | 2 | 10 | BLOCKED |
| 6 | object_mass (scripted policy) | 4 | 4 | 4 | 3 | 3 | 18 | SECONDARY |
| 7 | object_mass (expert/oracle policy) | 5 | 5 | 4 | 4 | 3 | 21 | PRIMARY* |
| 8 | object_mass (mass=3.0, BACKBONE) | 3 | 2 | 2 | 4 | 2 | 13 | DEFERRED |
| 9 | contact_friction (surface) | 3 | 3 | 3 | 2 | 3 | 14 | DEFERRED |
| 10 | LiftCube + mass (random) | 3 | 3 | 3 | 4 | 3 | 16 | SECONDARY |
| 11 | object_size / scale | 2 | 2 | 2 | 2 | 3 | 11 | DEFERRED |
| 12 | inertia tensor | 3 | 3 | 3 | 2 | 3 | 14 | DEFERRED |
| 13 | gravity_scale | 2 | 3 | 3 | 2 | 2 | 12 | DEFERRED |

> *PRIMARY*: policy 변경 + 구현 시간 조건부. 현재 코드로는 SECONDARY.

---

### D.1 Axis 1 — joint_dry_friction (관절 건식 마찰)

**쉬운 설명**: 로봇 관절 내부 마찰 증가. 전기모터 효율 저하와 유사. 매 step 관절 속도에 Coulomb friction 적용: `τ_eff = τ_motor - 5.0 × sign(qvel)`.

**현재 구현**: ✅ `art.joints[i].set_friction(5.0)` (`src/fglc/data/collector.py:84-89`)

**SSoT 정의**: ⚠ `docs/idea/18_DATA_BENCHMARKS.md:44` — `friction ∈ {0.3, 0.7, 1.5}` (µ_kinetic 단위). 현재 구현은 `joint_dry_friction=5.0` (N·m 단위). **매핑 DEFERRED** (`quality_report.json:friction_mapping=DEFERRED`).

**적합 task**: PickCube-v1 ✅ (PASS 확인), PushCube-v1 ✅ (PASS 확인)

**필요 policy**: random (이미 작동)

**검증 metric**:
- state_delta_norm gap: PickCube 0.138 / PushCube 0.124 (모두 PASS)
- qvel dims 9-17 std 변화: 20~32% 감소 (friction split)
- 두 task cross-replication: 완료

**장점**:
- 접촉 여부 무관하게 모든 step에서 작용 → random policy에서도 신호 강력
- 두 task에서 독립적으로 재현 확인됨 (cross-task replication)
- 코드 구현 완료, 재수집 불필요

**단점**:
- µ_kinetic(SSoT) ↔ joint_dry_friction(API) 매핑 DEFERRED — 리뷰어 "물리 단위 오류" 공격 가능
- friction=5.0 N·m 설정이 현실적인지 확인 필요 (단위 해석에 따라 과도할 수 있음)
- friction 단독은 R5/R6의 ≥2 axes 요구 불충족 → 두 번째 axis 필수

**실패 가능성**: friction 단위 매핑 문제로 논문 reviewer가 "물리적으로 unrealistic"라고 공격 가능. 방어: "joint dry friction coefficient 5.0 N·m/rad is standard for Panda arm OOD benchmark설정; effect 크기(gap=0.138)가 주장의 물리적 의미를 지지".

**repair 방향**: friction_ssot_unit 매핑 문서화 (docs/idea/18_DATA_BENCHMARKS.md 주석 추가, BACKBONE 등급 1).

**5관점 점수**: C1=5, C2=4, C3=5, C4=5, C5=4 → **합계=23, PRIMARY**

**BACKBONE_CHANGE 등급**: 등급 0 (코드만, collector.py 완료. friction_ssot_unit 매핑 추가 시 등급 1).

---

### D.2 Axis 2 — action_gain (액션 게인 스케일)

**쉬운 설명**: 모든 action 출력에 곱해지는 스케일 인자. gain=0.7이면 동일 policy 출력이 70%로 줄어듦. robot이 "둔감해진" 것처럼 동작. gain=1.3이면 "과민한" robot.

**현재 구현**: ❌ `eval_metas["true_action_gain"]` placeholder만 (`collector.py` OOD params에 없음). `_apply_ood`에 action_gain 처리 없음.

**SSoT 정의**: ✅ `docs/idea/18_DATA_BENCHMARKS.md:44` — `gain ∈ {0.7, 0.85, 1.3}`.

**적합 task**: PickCube-v1, PushCube-v1 (모두 해당). action scaling은 task-independent 메커니즘.

**필요 policy**: random policy에서도 작동 가능. `a_effective = gain × a_sampled`로 action에 직접 곱셈.

**검증 metric**:
- action-scaled dynamics → qvel, tcp_pose dims에서 변화
- random policy에서 `|a_effective| = gain × |a_uniform[-1,1]|` → std 비례 변화
- gain=0.7 vs ID(gain=1.0): action_std ≈ 0.577 → 0.404. qvel 응답도 감소 예상.

**장점**:
- action에 직접 스케일링 → contact 없이도 작동 (joint velocity 변화)
- 구현 단순: `_apply_ood`에 `a = a * gain` 추가 (~5줄)
- SSoT 이미 정의됨. API 탐색 불필요.
- C2(action-value relevance) 매우 강함: action_gain shift는 planning decision을 직접 변경

**단점**:
- collector.py `_apply_ood` 수정 + 환경 wrapper 구현 필요 (약 30~50 LOC)
- `_apply_ood`는 env 파라미터 변경인데, action_gain은 step-level 변환 → 구조 변경 필요
- gain=1.3에서 action clipping 여부 확인 필요 ([-1,1] 경계)

**실패 가능성**: gain=1.3 시 action clipping으로 effective gain이 1.0에 가까워질 수 있음 → gap 감소. 방어: gain=0.7 (clipping 없음) 중심으로 설계.

**repair 방향**: `CANDIDATE_TABLE`에 `action_gain_policy_switch` 추가 (현재 `OOD_TOO_EASY` 진단 시).

**5관점 점수**: C1=4, C2=5, C3=4, C4=3, C5=4 → **합계=20, PRIMARY**

**BACKBONE_CHANGE 등급**: 등급 0~1 (collector.py + action wrapper 추가. SSoT 변경 없음).

---

### D.3 Axis 3 — action_latency / action_delay_steps (액션 지연)

**쉬운 설명**: 현재 step의 action이 실제 환경에 적용되는 시점이 k step 뒤로 지연됨. real robot에서 control loop 지연과 동일. delay=3이면 3 step 전 action이 지금 실행됨.

**현재 구현**: ❌ placeholder만 (`eval_metas["true_latency"]`, `_apply_ood` 처리 없음).

**SSoT 정의**: ✅ `docs/idea/18_DATA_BENCHMARKS.md:44` — `delay ∈ {3, 5, 8} steps`.

**적합 task**: 모든 task (action delay는 task-independent).

**필요 policy**: random policy에서도 작동. action buffer를 queue로 관리.

**검증 metric**: delayed action → trajectory가 "느리게" 반응 → qvel 변화 감소/지연 → state_delta_norm gap 기대.

**장점**:
- 실제 로봇 배포 시나리오와 직접 연결 → paper novelty 강화 (HiP-RSSM와 차별)
- delay buffer 구현 시 contact 여부 무관하게 작동
- SSoT 이미 정의됨

**단점**:
- action queue 구현 필요 (collector.py 루프 재구성, ~50~100 LOC)
- delay=8 step에서 max_episode_steps=50이면 전체 episode의 16%가 지연 → episode 통계 왜곡 가능
- gym wrapper 수준에서 처리할지 collector 루프에서 처리할지 설계 결정 필요

**5관점 점수**: C1=4, C2=4, C3=4, C4=3, C5=4 → **합계=19, SECONDARY**

**BACKBONE_CHANGE 등급**: 등급 0~1 (collector.py action buffer + episode metadata 추가).

---

### D.4 Axis 4 — observation_noise σ (관측 노이즈)

**쉬운 설명**: state vector의 각 dimension에 Gaussian noise 추가. `x_observed = x_true + N(0, σ²)`. sensor 오차 시뮬레이션.

**현재 구현**: ❌ placeholder만.

**SSoT 정의**: ✅ `docs/idea/18_DATA_BENCHMARKS.md:44` — `σ ∈ {0.05, 0.1, 0.2}`.

**장점**:
- 구현 단순 (`obs += np.random.normal(0, sigma, obs.shape)`, ~3줄)
- contact 무관하게 작동

**단점**:
- C1(falsification strength) 중간: noise는 WM uncertainty를 높이지만 dynamics hypothesis 자체를 바꾸지 않음
- falsification gate β_t가 "dynamics 위반"이 아닌 "관측 노이즈 증가"에도 발화할 수 있음 → false positive 우려
- reviewer: "노이즈 주입은 physics-agnostic 시나리오, FGLC의 wrong-dynamics-hypothesis 시나리오와 다름"

**5관점 점수**: C1=3, C2=3, C3=3, C4=4, C5=4 → **합계=17, SECONDARY**

**BACKBONE_CHANGE 등급**: 등급 0 (collector.py에서 obs를 반환 전 noise 추가).

---

### D.5 Axis 5 — object_mass (random policy) — 현재 BLOCKED

**쉬운 설명**: cube 물체의 질량 변경 (mass=1.5 kg vs ID mass=0.064 kg). 이미 실측 완료.

**현재 구현**: ✅ `inner.cube.set_mass()` / `inner.obj.set_mass()` (`collector.py:73-88`).

**실측 결과**:
- PickCube gap=0.0038 (FAIL), PushCube gap=0.008 (FAIL)
- contact_rate=0%, tcp_dist=0.999m
- 16개 metric 어떤 것도 구분 못함

**5관점 점수**: C1=1, C2=1, C3=1, C4=5, C5=2 → **합계=10, BLOCKED**

**BACKBONE_CHANGE 등급**: 등급 0 (코드 완료). 재수집 필요 없음, BLOCKED 상태 유지.

---

### D.6 Axis 6 — object_mass (scripted/goal-conditioned policy)

**쉬운 설명**: EEF가 의도적으로 cube에 접촉하여 push/grasp 동작 수행하는 policy로 변경. contact_rate를 구조적으로 높여 mass 경로(F=ma)를 활성화.

**현재 구현**: ❌ policy 변경 필요 (`CollectionConfig`에 policy 필드 없음).

**장점**:
- mass 물리 경로(F=ma on object) 활성화 → gap 증가 기대
- 18_DATA_BENCHMARKS.md:44 mass={0.5, 1.5, 2.0} 범위 내 → SSoT 변경 없음

**단점**:
- scripted policy 구현 비용: ~3~5시간 (ManiSkill motion planning API 사용)
- oracle policy 채택 시 reviewer "cherry-picking" 공격: "expert policy에서만 mass shift 보이면 general claim 약함"
- 수집 방법론이 ID data(random policy)와 다르면 distribution mismatch

**5관점 점수**: C1=4, C2=4, C3=4, C4=3, C5=3 → **합계=18, SECONDARY**

**BACKBONE_CHANGE 등급**: 등급 1 (CollectionConfig.policy 필드 + TASK_OOD_PARAMS scripted policy entry 추가).

---

### D.7 Axis 7 — object_mass (expert/oracle demo replay)

**쉬운 설명**: ManiSkill motion planning solver 또는 HuggingFace ManiSkill/demos를 사용한 near-optimal trajectories.

**현재 구현**: ❌ 완전 미구현. demo API: `mani_skill.examples.motionplanning.panda.solve_*` (license/API 확인 필요).

**장점**:
- contact_rate 구조적으로 높음 → mass 물리 경로 완전 활성화
- high-quality trajectory → state/action coverage 우수

**단점**:
- reviewer: "oracle demo로 수집한 mass OOD 데이터 → 다른 policy로 수집한 ID data와 distribution mismatch"
- HuggingFace ManiSkill demos 라이선스 확인 필요 (재배포 조건 UNKNOWN)
- 구현 비용 큼 (8~12시간)
- C5 점수 낮음: "왜 expert policy만 mass가 작동하는가" reviewer 공격

**5관점 점수**: C1=5, C2=5, C3=4, C4=4, C5=3 → **합계=21, PRIMARY*** (구현 조건부)

**BACKBONE_CHANGE 등급**: 등급 1 (TASK_OOD_PARAMS demo_path 필드 추가).

---

### D.8 Axis 8 — object_mass (mass=3.0, BACKBONE 변경)

**쉬운 설명**: mass=1.5 대신 mass=3.0으로 OOD severity 자체를 강화. random policy에서도 gap이 높아질 가능성 탐색.

**현재 구현**: ❌ TASK_OOD_PARAMS 값 변경 필요.

**BACKBONE 여부**: mass=3.0은 `docs/idea/18_DATA_BENCHMARKS.md:44`의 `mass ∈ {0.5, 1.5, 2.0}` 범위 외 → **등급 2 BACKBONE 변경 필수** → 사용자 승인 필수.

**문제점**:
- contact_rate=0%에서 mass=3.0도 동일한 문제 발생 가능성 높음
- 단순히 mass를 높인다고 contact 없는 상황에서 gap이 생기지 않음
- PickCube mass=1.5 gap=0.0038, mass=3.0에서 0.01 넘을지 물리적으로 불확실

**5관점 점수**: C1=3, C2=2, C3=2, C4=4, C5=2 → **합계=13, DEFERRED**

**BACKBONE_CHANGE 등급**: **등급 2 — 사용자 승인 필수**.

---

### D.9 Axis 9 — contact_friction (물체 표면 마찰)

**쉬운 설명**: 로봇-물체 또는 물체-바닥 간 contact friction 계수 변경. joint friction과 다름.

**현재 구현**: ❌ ManiSkill SAPIEN API에서 `PhysxMaterial.set_static_friction()` 가능 여부 UNKNOWN.

**장점**: 물체-바닥 마찰 → push/slide task에서 물체 이동 저항 변화

**단점**: API 확인 전 구현 불가. joint friction(D.1)과 겹칠 위험.

**5관점 점수**: C1=3, C2=3, C3=3, C4=2, C5=3 → **합계=14, DEFERRED**

---

### D.10 Axis 10 — LiftCube-v1 + mass (task switch)

**쉬운 설명**: LiftCube 태스크에서 cube를 드는 동작이 mass-sensitive할 가능성. lift 성공 시 cube mass가 arm dynamics에 직접 반력으로 영향.

**현재 구현**: ❌ TASK_OOD_PARAMS에 LiftCube 없음. actor 이름 UNKNOWN (`inner.cube`? `inner.obj`?).

**장점**: lift 동작이 success > 0%이면 contact_rate 향상 가능 → mass 경로 활성화

**단점**:
- LiftCube random policy에서 success rate 0%일 가능성 높음 (PickCube와 동일 문제)
- actor 이름 probe 필요
- PushCube mass FAIL이 LiftCube에서 repeat될 가능성

**5관점 점수**: C1=3, C2=3, C3=3, C4=4, C5=3 → **합계=16, SECONDARY**

**BACKBONE_CHANGE 등급**: 등급 1 (TASK_OOD_PARAMS 신규 task entry).

---

### D.11 Axis 11 — object_size / scale

**쉬운 설명**: 물체 크기 변경 (큰 cube vs 작은 cube). grip geometry 변화 → manipulation difficulty shift.

**현재 구현**: ❌ ManiSkill API 가능성 조사 필요. SSoT 미정의.

**5관점 점수**: C1=2, C2=2, C3=2, C4=2, C5=3 → **합계=11, DEFERRED**

**BACKBONE_CHANGE 등급**: 등급 2 (SSoT 신규 axis → docs/idea/18_DATA_BENCHMARKS.md 변경).

---

### D.12 Axis 12 — inertia tensor (mass 분리)

**쉬운 설명**: mass는 유지하고 관성 모멘트만 변경. 회전 저항을 독립적으로 조작.

**현재 구현**: ❌ SAPIEN API 가능성 UNKNOWN. SSoT 미정의.

**5관점 점수**: C1=3, C2=3, C3=3, C4=2, C5=3 → **합계=14, DEFERRED**

**BACKBONE_CHANGE 등급**: 등급 2 (SSoT 신규 axis).

---

### D.13 Axis 13 — gravity_scale (중력 스케일)

**쉬운 설명**: 시뮬레이션 중력 스케일 변경. g=9.81 → g=14.7 (중력 1.5배).

**현재 구현**: ❌ SAPIEN scene API 가능성 UNKNOWN. SSoT 미정의.

**5관점 점수**: C1=2, C2=3, C3=3, C4=2, C5=2 → **합계=12, DEFERRED**

**BACKBONE_CHANGE 등급**: 등급 2.

---

### D.14 Tier 분류 요약

| Tier | 기준 | Axis 목록 |
|---|---|---|
| PRIMARY | 합계 ≥ 20, 구현 완료 또는 단기 구현 가능 | friction (23), action_gain (20), mass+expert_policy (21) |
| SECONDARY | 합계 15~19 | latency (19), noise (17), mass+scripted (18), LiftCube+mass (16) |
| DEFERRED | 합계 10~14 | contact_friction (14), inertia (14), mass=3.0+BACKBONE (13), object_size (11), gravity (12) |
| BLOCKED | 합계 < 10 또는 실측 실패 | mass+random_policy (10) |

---

## §E — Mass Axis Deep Dive

### E.1 Random Policy 실패 원인 분해 (4단계)

mass dynamics 영향 경로:
```
1. F_contact > 0  →  대상 객체와 접촉 (EEF touching cube)
2. F = ma         →  object acceleration = F_contact / mass_object
3. object pose/velocity change  →  state vector dims (29-41)에 반영
4. base WM prediction residual  →  gap = |ID_mean - OOD_mean| 측정
```

PickCube/PushCube + random policy는 **단계 1에서 차단**:
- contact_rate = 0.000 (PickCube 실측), tcp_dist = 0.999m
- 단계 2~4는 입력 없음 → gap → 0

friction은 **단계 1 우회**:
```
τ_eff = τ_motor - friction_coeff × sign(qvel)  (매 step, 접촉 무관)
qvel_{t+1} = qvel_t + M^{-1} × τ_eff × dt
→ qvel dims 9-17에서 20~32% std 변화
```

### E.2 Mass 부활 후보 정책 상세 평가

#### P1 — Random Policy 유지 + mass DEFERRED 확정

**5관점**: C1=1, C2=1, C3=1, C4=5, C5=2 = **10점**

- 즉시 적용 가능, 코드 변경 없음
- mass axis를 영구 secondary tier로 기록
- 장점: R3 즉시 진행 가능 (friction data 사용)
- 단점: C5 reviewer "5-axis benchmark 주장 불완전"
- **BACKBONE 등급 0** (코드 변경 없음)

#### P2 — Contact-rich Scripted Policy (ManiSkill motion planning)

**5관점**: C1=4, C2=4, C3=4, C4=3, C5=3 = **18점**

- `mani_skill.examples.motionplanning.panda.solve_pick_cube()` 또는 유사 API
- EEF가 의도적으로 cube 접근 → contact_rate ≥ 30% 기대
- 구현 비용: ~5~7시간
- reviewer 위험: "scripted policy로 mass만 수집 = biased collection"
- **BACKBONE 등급 0~1** (CollectionConfig.policy 필드 추가)

#### P3 — Goal-conditioned Push Policy

**5관점**: C1=4, C2=5, C3=4, C4=3, C5=4 = **20점**

- goal_pose 방향으로 cube push 유도 (task success-oriented)
- contact_rate 높음 (push task 특성상)
- 구현 비용: ~6~8시간 (custom controller or ManiSkill goal_conditioned env)
- 장점: C2(action-value relevance) 최고 — task success에 직결
- 단점: 구현 복잡도 높음
- **BACKBONE 등급 0~1**

#### P4 — Expert/Oracle Demo Replay (ManiSkill demos)

**5관점**: C1=5, C2=5, C3=4, C4=4, C5=3 = **21점**

- HuggingFace ManiSkill/demos or `mani_skill.examples.motionplanning`
- contact_rate 최고 (expert trajectory)
- 구현 비용: ~8~12시간
- 치명적 위험: reviewer "oracle cherry-picking"
  - ID data (random policy) vs OOD data (expert policy) → distribution mismatch
  - "FGLC가 expert trajectory로만 mass shift 보인다면 RL 실제 사용에서 같은 효과 없음"
- **BACKBONE 등급 1** (TASK_DEMO_PATHS 필드, demo license 확인 필요)
- license UNKNOWN: HuggingFace ManiSkill/demos 재배포 조건

#### P5 — Hybrid Policy (random + scripted contact segment)

**5관점**: C1=4, C2=4, C3=4, C4=3, C5=3 = **18점**

- episode 첫 25 step random, 후반 25 step scripted reach+push
- contact_rate 중간 (scripted 구간에서만)
- 구현 비용: ~6~10시간
- ID data와 동일한 "partially random" policy → distribution mismatch 낮음
- **BACKBONE 등급 1**

#### P6 — High-contact Episode Filtering (random + post-hoc filter)

**5관점**: C1=3, C2=3, C3=3, C4=2, C5=2 = **13점**

- random 수집 후 contact_rate > θ인 episode만 보존
- PickCube random policy contact_rate = 0% → yield 거의 없음
- 구현 비용: ~3~5시간 (validators.py 확장)
- 치명적 문제: contact_rate=0%에서 선택적 보존이 의미 없음
- **BACKBONE 등급 0**

#### P7 — Task Switch (LiftCube-v1, StackCube-v1)

| Task | mass-sensitive 이론 | random policy contact | 수집 비용 |
|---|---|---|---|
| LiftCube-v1 | z축 lifting force ∝ mass | 0%? (probe 필요) | 4~6h |
| StackCube-v1 | stacking contact force ∝ mass | 0%? (probe 필요) | 6~8h |

**LiftCube-v1**: actor 이름 UNKNOWN (probe 필요). random policy lift 성공률 0% 예상.
**StackCube-v1**: 2-cube 동역학 복잡도 높음. actor API 신규 매핑 필요.

**BACKBONE 등급 1** (TASK_OOD_PARAMS 신규 task entry).

#### P8 — mass=2.0 OOD 값 재설정

**현재**: `ood_mass_low: object_mass=1.5` (SSoT 범위 내)
**변경**: `ood_mass_low: object_mass=2.0` (SSoT 범위: {0.5, 1.5, 2.0})

**5관점**: C1=2, C2=2, C3=2, C4=4, C5=3 = **13점**

- mass=2.0은 SSoT 범위 내 → **BACKBONE 등급 0**
- 그러나 contact_rate=0% 조건에서 mass=2.0도 동일한 문제 발생 → C1 여전히 낮음
- 실측 전 효과 불확실: mass=1.5(gap=0.0038) → mass=2.0에서 gap이 0.01 넘을지 불명확

### E.3 Mass 부활 후보 우선순위 요약

| 순위 | 후보 | 점수 | 비용 | reviewer 방어력 | 권장 |
|---|---|---|---|---|---|
| 1 | P3 (goal-conditioned push) | 20 | 6~8h | HIGH | ✅ 2순위 구현 |
| 2 | P2 (scripted policy) | 18 | 5~7h | MEDIUM | ✅ 1순위 구현 |
| 3 | P5 (hybrid) | 18 | 6~10h | MEDIUM | ⚠ P2 이후 |
| 4 | P7 LiftCube (probe 필요) | TBD | 4~6h probe | UNKNOWN | ⚠ probe 필요 |
| 5 | P4 (expert/oracle) | 21* | 8~12h | LOW (cherry-pick) | ⚠ P2 FAIL 시 |
| 6 | P1 (random 유지, DEFERRED) | 10 | 0h | — | ✅ 즉시 friction-first |
| — | P6 (filter) | 13 | 3~5h | LOW | ❌ yield=0 |
| — | P8 (mass=2.0) | 13 | 1~2h | LOW | ❌ contact=0%에서 무의미 |

### E.4 Threshold 완화 거부 명문화

> **명시적 REJECT**: `delta_min=0.01`을 `0.003` 이하로 낮춰 mass gap=0.0038을 통과시키는 옵션은 본 review에서 명시적으로 거부한다.
>
> 근거:
> 1. gap=0.0038, 방향 불안정(+, 역전 가능) — 물리 신호가 없음을 실증
> 2. threshold 완화 = reviewer cherry-picking/p-hacking 공격에 무방비
> 3. Agent G(RC synthesis) 판정: threshold 완화 전략 reviewer-defensibility = 0.10
>
> 모든 score는 `delta_min=0.01` 유지를 전제로 산출되었다.

### E.5 SSoT 변경 필요 매트릭스

| 후보 | maniskill_schema.py | 18_DATA_BENCHMARKS.md | 사용자 승인 |
|---|---|---|---|
| P1 (DEFERRED) | 없음 | 없음 | 불필요 |
| P2~P3 (scripted) | CollectionConfig.policy 필드 추가 (등급 1) | 없음 | 불필요 |
| P4 (expert demo) | TASK_DEMO_PATHS 신규 dict | 없음 (data sources에 demo 추가) | demo license 확인 필요 |
| P5 (hybrid) | CollectionConfig.policy + segments | 없음 | 불필요 |
| P7 LiftCube | TASK_OOD_PARAMS LiftCube entry | tasks 목록 이미 포함 | 불필요 |
| P8 mass=2.0 | TASK_OOD_PARAMS 값 변경 | 이미 범위 내 ({0.5, 1.5, 2.0}) | 불필요 |
| mass=3.0 | TASK_OOD_PARAMS 값 변경 | **범위 외 → 등급 2 BACKBONE** | **필수** |

---

## §F — Data Collection Policy Review

### F.1 7개 Policy × Axis 적합도 매트릭스

| Policy | friction | mass | action_gain | latency | noise |
|---|---|---|---|---|---|
| 1. Random (현재) | ✅ PASS 확인 | ❌ FAIL 확인 | ❓ 가능성 중 | ❓ 미실측 | ❓ 미실측 |
| 2. Scripted reach+push | ✅ | ⚠ 가능 | ✅ | ⚠ | ✅ |
| 3. Goal-conditioned push | ✅ | ✅ 기대 | ✅ | ✅ | ✅ |
| 4. Expert/oracle demo | ✅ | ✅ 강력 | ⚠ oracle leak 위험 | ✅ | ✅ |
| 5. Hybrid (random+scripted) | ✅ | ⚠ 중간 | ⚠ | ⚠ | ✅ |
| 6. High-contact filter | ✅ | ⚠ yield ↓↓ | ⚠ | ⚠ | ⚠ |
| 7. Motion planning solver | ✅ | ✅ 강력 | ⚠ | ✅ | ✅ |

### F.2 7개 Policy × 5관점 점수

| Policy | C1 | C2 | C3 | C4 | C5 | Total |
|---|---|---|---|---|---|---|
| 1. Random | 3 (friction만) | 2 | 4 | 5 | 3 | 17 |
| 2. Scripted reach+push | 4 | 4 | 4 | 3 | 3 | 18 |
| 3. Goal-conditioned push | 4 | 5 | 4 | 3 | 4 | 20 |
| 4. Expert/oracle demo | 5 | 5 | 4 | 4 | 2 | 20* |
| 5. Hybrid | 4 | 4 | 4 | 3 | 3 | 18 |
| 6. Filter (random+post-hoc) | 2 | 2 | 3 | 2 | 2 | 11 |
| 7. Motion planning solver | 5 | 5 | 4 | 4 | 4 | 22 |

> *Policy 4: C5=2 (expert cherry-pick reviewer 공격), C4=4 (구현 완료 시). license 확인 전 조건부.
> Policy 7: 최고점이나 ManiSkill motion planning solver 통합 비용 큼.

### F.3 Policy 우선순위 권장

| 순위 | Policy | 권장 용도 |
|---|---|---|
| 1 | Policy 1 (Random) | friction/latency/noise/action_gain — 즉시 사용 가능 |
| 2 | Policy 3 (Goal-conditioned) | mass axis 부활 — 1순위 구현 목표 |
| 3 | Policy 2 (Scripted) | mass axis 부활 — 대안 |
| 4 | Policy 7 (Motion planning) | 장기 검증, R8+ 단계 |
| 5 | Policy 5 (Hybrid) | P2/P3 FAIL 시 |
| — | Policy 4 (Expert/oracle) | reviewer 위험 높음, 최후 수단 |
| — | Policy 6 (Filter) | yield≈0, 비추천 |

### F.4 Repair-loop → Policy 전환 매핑

| FailureCauseId | 발생 조건 | 권장 Policy 전환 |
|---|---|---|
| OOD_TOO_EASY | gap < 0.01 (현재 mass) | → Policy 2/3 (scripted/goal-conditioned) |
| DATA_TOO_SMALL | EVAL_NOISE_HIGH | → episode 수 증가 (동일 policy) |
| OOD_TOO_HARD | gap > 0.5 | → severity 완화 (ood_param 값 조정) |
| `OOD_INVISIBLE_TO_RANDOM_POLICY`* | contact=0% | → Policy 2~7 중 선택 |

> *`OOD_INVISIBLE_TO_RANDOM_POLICY`는 현재 taxonomy.py에 없음. §I.3 참조.

---

## §G — High-Quality Dataset Construction Plan

### G.1 Stage 흐름

| Stage | episodes/split (기준) | 목적 | 통과 조건 |
|---|---|---|---|
| Probe | 10~50 | API 동작 확인, gap 1차 추정 | AttributeError 없음, gap > 0.005 |
| Pilot | 50~100 | quality gate H1-H15 전체 | accept ≥ 99%, gap > 0.01 |
| Scaled | 250~500 | 통계적 검출력 확보 | KS p < 0.05, Cohen's d > 0.3 |
| Full | 500~1000 | reproducibility, 2 seeds | 2 seeds × Full 결과 일치 |

### G.2 Axis × Stage 현황 및 계획

| Axis | Task | Probe | Pilot | Scaled | Full | 상태 |
|---|---|---|---|---|---|---|
| friction | PickCube | DONE | DONE | DONE (250ep) | OPT | PASS |
| friction | PushCube | DONE | DONE | DONE (500ep) | OPT | PASS |
| mass (random) | PickCube | DONE | DONE | DONE (50ep) | — | BLOCKED |
| mass (random) | PushCube | DONE | DONE | DONE (100ep) | — | BLOCKED |
| mass (P2/P3) | PickCube/Push | TODO | TODO | TODO | TODO | PENDING |
| action_gain | — | TODO | TODO | TODO | TODO | 미구현 |
| latency | — | TODO | TODO | TODO | TODO | 미구현 |
| noise | — | TODO | TODO | TODO | TODO | 미구현 |

### G.3 Split 설계 원칙

```
ID splits:
  train_id:  50~70% (PickCube: 250ep/seed[42~292), PushCube: 500ep/seed[1042~1542))
  val_id:    10~15% (PickCube: 50ep/seed[200~250), PushCube: 100ep)
  test_id:   10~15% (동일 패턴)

OOD splits (axis별):
  ood_<axis>_<severity>: 5~10% (축별 별도 split)
  seed range: 모든 split 간 disjoint 보장

새 axis 추가 시:
  seed range 충돌 방지: 기존 [42~1999) 이후 [2000+) 사용
  PickCube 기존: [42~650), PushCube 기존: [1042~1999)
  신규 axis: [2000+) 범위 할당
```

### G.4 Artifact 저장 구조

```
data/fglc/<TASK>-v1/
  raw/
    train_id.h5       ← inference fields만 (state/action/reward/done)
    val_id.h5
    test_id.h5
    ood_friction_low.h5
    ood_<new_axis>_<severity>.h5   ← axis별 신규 split
  manifest.json           ← seed_pool, git_sha, ManiSkill version, policy_type
  dataset_stats.json      ← state_delta_norm, reward stats per split
  quality_report.json     ← 10 checkpoint pass/fail
  split_config.yaml       ← split 설계
```

### G.5 Forbidden Field 보호

모든 신규 split에서 유지:
- `regime_id`, `true_mass`, `true_friction`, `true_latency`, `true_noise_sigma`, `true_action_gain`은 `EvalOnlyTransition`에만, 절대 HDF5 inference 데이터에 없음
- `src/fglc/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS` 강제
- `tests/test_fglc_forbidden_field_sync.py` green 유지

---

## §H — Team Agent Reports

### H.A Agent A — Interaction Axis Scout

**판정**: PASS (friction), CONDITIONAL (action_gain/latency/noise), BLOCKED (mass+random)

**Top 3 findings**:
1. 13개 axis 후보 조사: PRIMARY tier 3개 (friction, action_gain, mass+expert), SECONDARY 4개, DEFERRED 4개, BLOCKED 1개
2. action_gain axis가 friction 다음으로 구현 용이 (~30~50 LOC, C2=5)
3. LiftCube-v1 actor 이름 확인 전 probe 필수 — SSoT 허용 task이지만 API 불확실

**Top 2 UNKNOWNs**:
- LiftCube-v1/StackCube-v1 actor 이름 및 contact API
- ManiSkill SAPIEN PhysxMaterial.set_static_friction() 존재 여부

**Recommendations**: friction-first R3 + action_gain 구현 추가(~2일) → ≥2 axis 확보

---

### H.B Agent B — Claim-Metric Alignment Auditor

**판정**: PASS (friction axis), CONDITIONAL_FAIL (mass axis)

**Top 3 findings**:
1. friction axis → 4축 metric 1:1 매핑 가능 (C1 prediction NLL, C2 detection AUROC, C3 attribution nec-suf, C4 control return)
2. mass axis → 현재 데이터로 4축 metric 중 어느 것도 reliable signal 없음 → mass claim 불가
3. R5/R6 Stage 3 gate: "최소 2개 OOD 조건" 요구 → friction 1개 + {action_gain/latency/noise} 중 1개 필수

**Top 2 UNKNOWNs**:
- action_gain gap 실측값 (구현 후 probe 필요)
- latency axis에서 falsification gate β_t 발화 여부 (이론적으로 예상되나 실측 전)

**Recommendations**: friction + action_gain 2-axis dataset으로 R3~R6 진행. mass는 honest limitation으로 논문에 명시.

---

### H.C Agent C — Dynamics Forensics Agent

**판정**: FAIL (mass both tasks), PASS (friction both tasks)

**Top 3 findings**:
1. mass 물리 경로 완전 차단 확인: contact_rate=0%, tcp_dist=0.999m → F=0 → mass irrelevant
2. friction 작동 메커니즘 명확: `τ_eff = τ_motor - 5.0 × sign(qvel)` → qvel dims 9-17 std 20~32% 감소
3. dim24 Cohen's d=1.034이나 abs delta ~4e-6: 수치적 artifact, 물리 신호 아님 (명시적 REJECT)

**Top 2 UNKNOWNs**:
- PushCube contact_rate 직접 측정값 (PickCube 0.000% 확인, PushCube는 간접 추론)
- LiftCube-v1 random policy에서 contact_rate 예측값

**Recommendations**: mass axis에 대해 "contact-dependent physics → random policy에서 구조적 실패"를 논문에 명시. metric 교체로 해결 불가.

---

### H.D Agent D — Dataset Quality Gatekeeper

**판정**: PASS (PickCube 450ep, PushCube 900ep — quality gates H1-H9)

**Top 3 findings**:
1. 전체 1350ep (PickCube 450 + PushCube 900): n_rejected=0, accept_rate=100%
2. seed pool 완전 disjoint (PickCube [42~650), PushCube [1042~1999)), forbidden field 0건
3. quality_report.json checkpoint_4_ood_sev = FAIL (mass) — 이 gate만 미통과

**Top 2 UNKNOWNs**:
- 신규 axis (action_gain/latency) 추가 시 seed [2000+) 범위 충돌 여부
- scripted policy 수집 시 episode length distribution 변화 예상값

**Recommendations**: 신규 axis seed: [2000+) 범위 사전 할당. scripted policy 수집 시 min_episode_len 검토 (contact 실패 episode 처리).

---

### H.E Agent E — Policy Design Agent

**판정**: CONDITIONAL (friction=random policy OK, mass=policy 변경 필요)

**Top 3 findings**:
1. mass 부활 최우선: P2(scripted, 18점) + P3(goal-conditioned, 20점) — 구현 비용 5~8h
2. P4(expert/oracle, 21점)은 점수 최고이지만 C5=3 (reviewer "cherry-pick 위험")
3. action_gain axis: random policy 그대로 작동 가능, 구현 ~30~50 LOC로 효율 최고

**Top 2 UNKNOWNs**:
- ManiSkill motion planning API (`mani_skill.examples.motionplanning.panda`) 현재 버전 호환성
- PushCube goal-conditioned push에서 실제 contact_rate 달성 가능한지 probe 전 불명확

**Recommendations**: friction-first R3 + action_gain 구현 병렬 진행. mass는 P2(scripted) 프로토타입 후 결정.

---

### H.F Agent F — Resource Budget Auditor

**판정**: PASS (현재 수집량), EXPAND 조건부 (신규 axis 추가 시)

**4 scenario 추정** (신규 axis 1개 추가 기준):

| Scenario | episodes/task/split | 총 ep | disk (추가 axis) | 수집 시간 |
|---|---|---|---|---|
| S1 (min) | 50/250/250/50/50 | 450/task | ~2 MB/task | ~7분/task |
| S2 (recommended) | 100/500/500/100/100 | 900/task | ~4 MB/task | ~14분/task |
| S3 (robust) | 200/1000/1000/200/200 | 1800/task | ~8 MB/task | ~28분/task |
| S4 (full repro) | 300/2000/2000/300/300 | 3000+/task | ~13 MB/task | ~47분/task |

3개 task (PickCube/PushCube/LiftCube) × 3 axes × S2 = 총 ~36 MB / ~126분 (병렬).

**VRAM 추정**: R3 학습 기준 (D_x=42, batch=16, T=16): ~100~500 MB. 4060 8GB 한계 대비 16배 여유.

**Top 2 UNKNOWNs**:
- scripted policy 수집 속도 (현재 random 1.25 ep/s; scripted는 환경 step이 동일하나 action 생성 overhead 가능)
- 신규 axis probe 실패 시 quarantine 용량

**Recommendations**: 신규 axis: S2 (900ep/task)로 시작. S2 기준 디스크 총 ~70 MB (PickCube+PushCube+LiftCube+action_gain 4 axes) — 4060 기준 문제없음.

---

### H.G Agent G — Experiment Design Chair (Synthesis)

**판정**: MAJOR_REVISION (현재), CONDITIONAL_ACCEPT (friction + action_gain 2-axis 완성 시)

**최종 판정 근거**:

| 질문 | 판정 | 근거 |
|---|---|---|
| threshold 완화로 통과시킨 것처럼 보이는가? | NO | delta_min=0.01 유지, threshold 완화 명시적 REJECT |
| PickCube/PushCube mass FAIL 명시했는가? | YES | §B, §E, §N에 투명하게 기록 |
| friction cross-task evidence 방어 가능한가? | YES | 두 task 독립 PASS (0.138, 0.124) |
| H1~H15 gate 모두 PASS인가? | PARTIAL | checkpoint_4_ood_sev(mass)만 FAIL |
| R5/R6 ≥2 axes 충족 가능한가? | CONDITIONAL | friction + {action_gain/latency} 구현 시 |

**Risk matrix**:

| Risk | 수준 | 완화책 |
|---|---|---|
| mass axis missing | HIGH | honest limitation 명시 + PushCube friction cross-task |
| 5-axis claim 불완전 | MEDIUM | 논문 wording을 "primary 3 axes" (friction/latency/noise) + mass는 "contact-dependent" |
| single axis (friction-only) | HIGH | action_gain/latency 추가 구현 필수 |
| reviewer cherry-pick | MEDIUM | negative result 투명 공시 (§N) |

**Recommendations**:
1. 즉시: friction data로 R3 smoke 진행 (PickCube 450ep)
2. 2일 이내: action_gain axis 구현 + probe
3. 병렬: mass P2(scripted) 프로토타입 시작
4. R4 진입 전: friction + action_gain 두 axes 모두 Scaled PASS 확보

---

## §I — Repair Loop and Iterative Improvement Plan

### I.1 16단계 루프

```
1.  axis 후보 탐색 (§D tier 분류 참조)
2.  task/policy 후보 결정 (§F 매트릭스 참조)
3.  small probe 수집 (10~50 ep, --no-save 또는 quarantine)
4.  episode-level quality gate (H1-H6: validators.py 10 reject reasons)
5.  split-level leakage gate (H7-H9: seed disjoint / hash audit / forbidden field=0)
6.  OOD severity gate (H15: verify_ood_severity delta_min=0.01)
7.  novelty relevance gate (Agent E: 5관점 점수 ≥ 15 = SECONDARY 이상)
8.  training readiness gate (1-batch forward 정상 + 1-epoch smoke loss finite)
9.  R3 smoke metric 확인 (NLL finite + ood NLL > id NLL)
10. repair loop에 실패 metric 입력 (diagnose.py)
11. 원인 진단 (FailureCauseId 매핑, §I.3 참조)
12. 수집 조건 또는 policy 재설계 (CANDIDATE_TABLE 참조, §F.4 매핑)
13. 재수집 (probe → pilot → scaled 단계 준수)
14. before/after 비교 (compare_metrics: gap, KS, Cohen's d)
15. ledger 기록 (outputs/repair/loop_<task>_<axis>_<date>.jsonl)
16. commit (raw HDF5 제외, manifest + reports + PLAN 파일만)
```

### I.2 Stop Conditions

| 조건 | 값 | 행동 |
|---|---|---|
| max_iter | 4 | USER_ESCALATION |
| consecutive_inconclusive | 3 | USER_ESCALATION |
| wall_clock_limit | 60분/stage | BLOCKED 보고 |
| target_reached | gap > 0.01 + KS p < 0.05 + 전체 quality gate PASS | commit + 다음 단계 |
| hook_blocked | pre-commit hook 또는 forbidden field guard | BLOCKED 보고 |
| `OOD_INVISIBLE_TO_RANDOM_POLICY` | contact=0% 반복 | policy 전환 또는 task 전환 |

### I.3 Axis × FailureCauseId × RepairCandidate 매핑

| 발생 시나리오 | FailureCauseId | RepairCandidate | 권장 Policy |
|---|---|---|---|
| mass gap < 0.01 (contact=0%) | `OOD_TOO_EASY`* | E.4(task_switch) / E.2(secondary_tier) | P2/P3 scripted |
| mass gap < 0.01 (contact > 0%) | `OOD_TOO_EASY` | mass 값 증가 (SSoT 범위 내) | 동일 policy |
| mass gap > 0.5 | `OOD_TOO_HARD` | mass 값 감소 | 동일 policy |
| action_gain gap < 0.01 | `OOD_TOO_EASY` | gain 범위 확장 또는 재설계 | P1 (random) |
| action_gain gap > 0.5 | `OOD_TOO_HARD` | gain={0.7, 0.85, 1.3} 조정 | P1 |
| latency gap < 0.01 | `OOD_TOO_EASY` | delay 스텝 증가 ({3,5,8} → {5,8,12}?) | P1 |
| validators reject > 5% | `DATA_TOO_SMALL` | episode 수 증가 / seed pool 확장 | 동일 |
| R3 smoke NLL → inf | `IMPLEMENTATION_BUG_SUSPECTED` | 디버깅 필수, BLOCKED | — |
| R3 OOD NLL ≈ ID NLL | `DATA_BAD_SPLIT` | axis 재선택 | §D tier 재평가 |

> *현재 taxonomy.py에 `OOD_INVISIBLE_TO_RANDOM_POLICY` cause 없음 → 추가 검토 필요 (§N.4).

**taxonomy.py 신규 cause 추가 제안**:
```python
OOD_INVISIBLE_TO_RANDOM_POLICY = "OOD_INVISIBLE_TO_RANDOM_POLICY"
# meaning: OOD physical parameter change requires contact/interaction that 
#          random exploration policy cannot induce (contact_rate ~0%)
# detection: gap < delta_min AND contact_rate < 0.01 (proxy metric)
# applicable_phases: ("R2",)
```
→ 추가 여부는 §N.4 UNRESOLVED로 분류 (diagnose.py 수정 = 코드 변경 필요 → 사용자 확인).

### I.4 Ledger 기록 형식

```jsonl
{
  "loop_id": "<task>_<axis>_<YYYY-MM-DD>",
  "iter": <int>,
  "phase": "R2",
  "diagnosed_cause": "<FailureCauseId>",
  "candidate_chosen": "<candidate_id>",
  "config_path": "<yaml_path>",
  "config_hash": "<sha256_prefix>",
  "git_sha": "<sha>",
  "metrics_before": {"state_delta_norm_gap": <float>, ...},
  "metrics_after": {"state_delta_norm_gap": <float>, ...},
  "deltas": {"state_delta_norm_gap": <float>},
  "failed_metric": "<metric_name>",
  "result": "accept|reject|inconclusive",
  "stop_condition_hit": "<condition>|null",
  "next_action": "<NEXT_TASK|USER_ESCALATION|CONTINUE>",
  "vram_peak_mib": <int>,
  "wall_clock_minutes": <float>
}
```

---

## §J — Resource Budget

### J.1 단위 추정 기반 (실측)

| 항목 | PickCube-v1 | PushCube-v1 |
|---|---|---|
| D_x | 42 | 35 |
| D_a | 8 | 8 |
| episode steps | 50 | 50 |
| bytes/transition (float32, compressed) | ~430 B | ~374 B |
| bytes/episode | ~21,500 B | ~18,700 B |
| 수집 속도 (random policy) | ~1.25 ep/s | ~1.25 ep/s (추정) |

### J.2 4 Scenario Budget

| Scenario | ep/split (train/val/test/ood1/ood2) | 총 ep/task | 디스크 (PickCube) | 수집 시간 (단순) |
|---|---|---|---|---|
| S1 (현재, friction only) | 250/50/50/50/50 | 450 | ~2 MB | 7~14분 |
| S2 (권장, 2 axes) | 500/100/100/100/100 | 900 | ~4 MB | 14~28분 |
| S3 (robust, 3 axes) | 1000/200/200/200/200 | 1800 | ~8 MB | 28~56분 |
| S4 (full repro) | 2000/300/300/300/300 | 3200 | ~14 MB | 47~94분 |

3개 task × 3 axes × S2 = 총 ~36 MB, 42~84분. **4060 8GB VRAM 제약과 무관** (데이터 수집 단계는 GPU 불필요).

### J.3 R3 Training 시간 추정

| 항목 | 추정값 | 근거 |
|---|---|---|
| 1 epoch (batch=16, T=16, 1800ep) | ~1~3분 | Step 11 실측 기반 |
| 30 epoch full train | ~30~90분 | 선형 외삽 |
| 3 seeds × 2 tasks × 30 epoch | ~3~9시간 | — |
| VRAM peak (R3 model ~5~10M params) | ~100~500 MB | Adam state 포함 |
| VRAM 여유 (8GB 한계) | 16~80x | OOM 위험 없음 |

### J.4 권장 수집량 산출 기준

| 요구사항 | 권장 | 근거 |
|---|---|---|
| R3 smoke (최소) | S1 (450ep friction, 현재 완료) | friction PASS 확인 |
| R3 full + R4 | S2 (900ep × 2 axes) | KS test 안정성 + 2 axes |
| R5/R6 필수 | S2 (900ep × ≥2 axes) | Stage 3 gate: ≥2 OOD 조건 |
| Reviewer-robust | S3 (1800ep × 3 axes × 2 tasks) | 논문 주요 실험 |
| Full replication | S4 × 2 seeds | 최종 제출 전 |

확장 trigger: `EVAL_NOISE_HIGH` 또는 `DATA_TOO_SMALL` 발화 시 한 단계 상승 (S1→S2 등).

### J.5 4060 8GB 안전성 체크

| 항목 | 현재 | 한계 | 마진 |
|---|---|---|---|
| 수집 VRAM | ~0 MB (CPU 전용) | 8188 MB | 100% |
| R3 training VRAM | ~100~500 MB | 8188 MB | 16~80x |
| R5/R6 causal attention | ~500~1000 MB (추정) | 8188 MB | ~8~16x |
| 디스크 (전체 axes) | ~40 MB (현재) | 충분 | — |

**결론**: 8GB VRAM 한계는 R7 planner integration 이전까지 제약이 아님. 주의 시점: MPPI/CEM rollout batch 설계 시 (R7+).

---

## §K — Recommended Path Options

### K.1 Option 1 — friction-first R3 + mass repair 병렬 트랙

```
R3 smoke: PickCube friction 450ep (이미 수집 완료)
          → 즉시 실행 가능

mass repair: 별도 트랙
  - P2(scripted policy) 프로토타입 (~5~7h)
  - LiftCube probe (actor 이름 확인 후, ~2~4h)
  - PushCube mass probe 재분석 (obs_mode 통일 후, ~1h)

두 번째 axis: action_gain 구현 (~30~50 LOC) + probe + scaled
  → R5/R6 ≥2 axes: friction + action_gain
```

**장점**:
- R3 즉시 진행 — mass FAIL 노출 위험 없음
- mass repair 병렬 진행으로 total 지연 최소화
- 논문에 mass honest limitation 명시로 reviewer 공격 방어

**단점**:
- R4~R6에서 mass axis 해결 약속 이행 부담
- friction + action_gain 조합이 "mass 없는 benchmark" 지적 가능

**R3 진입 시점**: 즉시 (사용자 승인 후)
**R5/R6 axis 수**: friction + action_gain = 2 (최소 충족)
**reviewer 위험**: LOW~MEDIUM
**예상 비용**: action_gain 구현 ~1~2일 + mass repair 병렬 ~3~5일

---

### K.2 Option 2 — scripted/goal-conditioned mass policy 개발 후 mass 재수집

```
P2(scripted policy) 또는 P3(goal-conditioned) 구현: ~5~8h
mass probe (PickCube/PushCube, 50ep): ~1h
  → gap ≥ 0.01: full 재수집 (~14분 per task)
  → gap < 0.01: P3 또는 P7(LiftCube) 로 전환

R3 진입: mass probe PASS 후
두 번째 axis: mass (구제 성공 시) + friction = 2 axes
```

**장점**:
- mass axis 확보 → 5-axis SSoT 2개(friction+mass) 완성
- 논문 "mass shift가 contact-dependent dynamics를 변경함" 주장 실증

**단점**:
- R3 진입 지연: +5~10시간
- scripted policy reviewer 공격: "ID data(random)와 OOD data(scripted) policy 다름 → distribution mismatch"
  - 방어: "OOD 수집에 scripted policy 사용 = scripted policy로 OOD를 만드는 것이 아닌,
           scripted exploration이 mass-sensitive dynamics를 드러내기 위한 방법"
  - 약점: 이 방어가 충분히 설득력 있는지 불확실

**R3 진입 시점**: +5~10시간
**R5/R6 axis 수**: friction + mass (scripted) = 2
**reviewer 위험**: MEDIUM
**예상 비용**: ~10~15시간 (policy 구현 + probe + full 수집)

---

### K.3 Option 3 — Multi-axis 확장 (action_gain + latency + noise 동시)

```
3개 axis 동시 구현:
  - action_gain: ~30~50 LOC, collector.py 확장
  - latency: ~50~100 LOC, action buffer
  - noise: ~3 LOC, obs 반환 전 noise 추가

각 axis probe → pilot → scaled (병렬 가능)
R3 진입: 3 axes 모두 Probe PASS 후

두 번째 axis: action_gain (1순위) + latency (2순위)
```

**장점**:
- R5/R6 ≥2 axes 요구 완전 충족 + SSoT 5 axes 완성
- 논문: 3개 이상 diverse OOD axes에서 FGLC 검증 → 강력한 claim

**단점**:
- 구현 비용 큼: 3 axes × ~2~4일 = ~1주일 지연
- 각 axis probe FAIL 가능성 내포 (action_gain은 낮음, latency/noise는 낮음)
- R3 진입 가장 늦음

**R3 진입 시점**: +1~2주
**R5/R6 axis 수**: 3~4
**reviewer 위험**: LOW (SSoT 정합)
**예상 비용**: 16~24시간 코딩 + 수집

---

### K.4 Option별 Risk Matrix

| 항목 | Option 1 | Option 2 | Option 3 |
|---|---|---|---|
| R3 진입 | 즉시 | +5~10h | +1~2주 |
| R5/R6 axes | 2 (friction+gain) | 2 (friction+mass) | 3~4 |
| reviewer mass 공격 | MEDIUM | LOW | LOW |
| policy mismatch 위험 | — | MEDIUM (Option 2) | LOW |
| 5-axis SSoT 완성도 | 2/5 | 2/5 | 4/5 |
| 구현 복잡도 | LOW | MEDIUM | HIGH |
| BACKBONE 변경 | 없음 | 없음 (scripted 채택 시) | 없음 |

**Claude 선호도**: Option 1 + action_gain 구현을 즉시 병렬 시작.
- friction은 two-task replication으로 강력한 primary axis
- action_gain은 C2(action-value relevance) 최고 (5점) + 구현 용이
- 사전 결정이 아닌, 사용자의 일정/위험 선호도 기반으로 최종 결정

---

## §L — Final Recommendation

### L.1 근거 기반 권장안

**5관점 점수 + risk matrix + reviewer defensibility 종합**:

1. **즉시 실행**: PickCube friction 450ep + PushCube friction 100ep으로 R3 smoke 진행 (Option 1 기반)
2. **1~3일 이내**: action_gain axis 구현 (~30~50 LOC) + probe + Scaled 수집
   - C2(action-value relevance)=5, 구현 용이, SSoT 이미 정의됨
3. **병렬 트랙**: mass repair — P2(scripted reach+push policy) 프로토타입 평가
   - 성공 시: mass axis 복원 → 3 axes 확보
   - 실패 시: Option 1 최종 확정 + honest limitation 논문 명시

### L.2 사용자 결정 필요 항목

| # | 결정 사항 | 선택지 | 권장 |
|---|---|---|---|
| D-1 | mass repair 진행 여부 | (a) P2 scripted 구현, (b) P7 LiftCube probe, (c) mass DEFERRED 확정 | (a) P2 시도 권장 |
| D-2 | 두 번째 axis 우선순위 | (a) action_gain, (b) latency, (c) noise | (a) action_gain 권장 |
| D-3 | R3 진입 시점 | (a) 즉시 (friction only), (b) action_gain PASS 후, (c) mass repair 완료 후 | (a) 즉시 권장 |

### L.3 다음 TASK 후보

| TASK 이름 | 내용 | 예상 비용 |
|---|---|---|
| TASK_2050_ACTION_GAIN_IMPL | action_gain axis 구현 (collector.py _apply_ood 확장) + probe 50ep + pilot | ~1~2일 |
| TASK_2051_MASS_SCRIPTED_PROTO | scripted reach+push policy 프로토타입 + PickCube mass probe | ~2~3일 |
| TASK_2052_R3_SMOKE_FRICTION | PickCube friction 450ep 기반 R3 smoke test (NLL finite + OOD > ID) | ~0.5일 |
| TASK_2053_LIFTCUBE_PROBE | LiftCube-v1 actor 이름 확인 + mass probe 10~20ep | ~0.5~1일 |

---

## §M — Atomic Checklist

```
[x] 탐색: docs/idea + repo + reports 27개 이상 read (B.1~B.5, §D 각 sub-section)
[x] 계획: 5관점 × 13+ axis 점수표 완성 (§D.0 Cross-axis Matrix)
[ ] 검증: tests/test_fglc_ood_severity.py + test_fglc_split_integrity.py 회귀 green
          (본 MD 작성 단계에서는 read-only, 실행은 사용자 승인 후)
[ ] 테스트: validators.py 10 reject reasons 통과율 측정 (기존 data에서 0/450 = 100%, 확인됨)
[ ] 재설계: Option 1/2/3 중 사용자 승인된 path 확정
[ ] 재수집: probe → pilot → scaled 단계 명시 (§G.2 axis별 계획)
[x] R3 smoke 금지: 본 review MD 작성 단계에서 R3 smoke 실행 금지 — 준수
[x] repair loop: 신규 axis FAIL 시 USER_ESCALATION 조건 명시 (§I.2 stop conditions)
[x] commit: raw HDF5 / outputs/repair 대용량 / phase gate sentinel 제외
[x] R3.passed 금지: 본 review와 별개로 /fglc-phase-check --pass R3 사용자 승인 필수
[x] Negative result 공시: PickCube/PushCube mass FAIL 양 task 명시됨 (§B, §E, §N)
[x] threshold 완화 거부: delta_min=0.01 유지, 완화 옵션 명시적 REJECT (§E.4)
[x] friction-only 단정 금지: R5/R6 ≥2 axes 요구 명시, action_gain 추가 필요성 기록 (§H.B)
[x] 특정 axis 사전 확정 금지: §K Option 1/2/3 모두 표시, 사용자 결정 위임 (§L.2)
```

---

## §N — BLOCKED / UNKNOWN

### N.1 API 불확실성 (probe 필요)

| 항목 | 상태 | 해결 방법 |
|---|---|---|
| ManiSkill 3.0.1 LiftCube-v1 actor 이름 | `[UNKNOWN]` | probe 10ep (--no-save), `inner.cube`? `inner.obj`? |
| ManiSkill 3.0.1 StackCube-v1 cubeA/cubeB API | `[UNKNOWN]` | probe 10ep + source code 확인 |
| ManiSkill SAPIEN PhysxMaterial.set_static_friction() | `[UNKNOWN]` | SAPIEN 3.x API 문서 확인 |
| ManiSkill motion planning solver 현재 버전 호환성 | `[UNKNOWN]` | `mani_skill.examples.motionplanning` import 확인 |
| gravity_scale SAPIEN scene API | `[UNKNOWN]` | scene.set_gravity() 존재 여부 |

### N.2 License / External Resource

| 항목 | 상태 | 해결 방법 |
|---|---|---|
| HuggingFace ManiSkill/demos 재배포 조건 | `[UNKNOWN]` | HuggingFace repo license 확인 |
| ManiSkill motion planning demos license | `[UNKNOWN]` | `mani_skill.examples.motionplanning` license |

### N.3 구현 비용 미측정

| 항목 | 상태 | 추정치 |
|---|---|---|
| action_gain gym wrapper LOC | `[UNKNOWN]` | ~30~50 LOC (collector.py _apply_ood 확장) |
| latency action buffer LOC | `[UNKNOWN]` | ~50~100 LOC (episode loop 재구성) |
| observation_noise LOC | `[UNKNOWN]` | ~3~5 LOC (obs 반환 전 추가) |
| scripted reach+push policy LOC | `[UNKNOWN]` | ~100~200 LOC (ManiSkill API 의존) |

### N.4 UNRESOLVED 설계 결정

| 항목 | 상태 | 결정 필요 시점 |
|---|---|---|
| `diagnose.py`에 `OOD_INVISIBLE_TO_RANDOM_POLICY` 신규 cause 추가 여부 | `[UNRESOLVED]` | I.3 매핑 확정 후 |
| `CANDIDATE_TABLE`에 policy-switch repair candidate 추가 여부 | `[UNRESOLVED]` | P2/P3 구현 후 |
| `joint_dry_friction` ↔ µ_kinetic SSoT 매핑 정의 | `[UNRESOLVED]` | R3 진입 전 문서화 |
| PushCube ood_mass_low 이름 정합성 (value=1.5 = SSoT "high-mid") | `[UNRESOLVED]` | TASK_OOD_PARAMS 명명 정리 시 |

### N.5 BLOCKED

| 항목 | 상태 | 해제 조건 |
|---|---|---|
| mass axis (random policy) | `[BLOCKED]` | P2/P3 scripted policy PASS 또는 DEFERRED 확정 |
| R5/R6 ≥2 axes 충족 | `[BLOCKED]` | action_gain/latency axis 중 1개 Scaled PASS |
| reviewer "cherry-pick oracle policy" 방어 | `[BLOCKED if P4 chosen]` | P4 미채택 시 해제됨 |
| mass axis via LiftCube | `[UNKNOWN→BLOCKED?]` | LiftCube probe 전 미확정 |

### N.6 Negative Result 공시 의무 (숨기지 않음)

이 review에서 기록하는 negative results:

1. **PickCube-v1 + random policy + mass=1.5**: gap=0.0038 (FAIL). contact_rate=0%. 물리 신호 없음.
2. **PushCube-v1 + random policy + mass=1.5**: gap=0.0080 (FAIL). 동일 메커니즘.
3. **16개 metric 후보**: 어떤 것도 현재 데이터에서 mass OOD를 신뢰할 수 있게 구분 못함.
4. **Pilot 90ep gap=0.0148 PASS**: n=10 variance. Scaled에서 실제 gap=0.0038로 수렴.
5. **PushCube mass probe(obs_mode=state) gap=0.0178**: obs_mode mismatch로 실측 수집(state_dict)과 다름.

**논문 Experiments 섹션 권장 서술**:
> "OOD-friction 축은 joint-level friction이 robot proprioceptive observation에 직접 반영되어 state_delta 분포에서 측정 가능한 shift를 생성합니다 (gap=0.138, 13.8× threshold, two-task replication). OOD-mass 축은 cube mass가 contact-dependent dynamics에만 영향을 주기 때문에, random exploration policy 하에서는 state-level에서 severity를 측정하기 어렵습니다 (gap=0.004, contact_rate=0%). 이는 mass shift의 falsification 효과가 contact 빈도에 의존적임을 시사하며, goal-conditioned policy 또는 PushCube task에서 추가 검증이 진행 중입니다."

---

## §O — 추가 참조 파일 목록 (읽은 파일 기록)

본 review 작성을 위해 읽은 파일 (27개 이상):

| 파일 | 역할 |
|---|---|
| `docs/orchestration/agent_reports/synthesis/2026-05/pushcube_dataset_synthesis_R1.md` | PushCube synthesis: PATCH_REQUIRED |
| `reports/pushcube_ood_severity_agent_report_R1.md` | PushCube OOD FAIL (gap=0.008) |
| `outputs/repair/loop_pushcube_2026-05-24.jsonl` | repair ledger iter=1, USER_ESCALATION |
| `docs/idea/18_DATA_BENCHMARKS.md` | 5 axes SSoT (FRAGILE FILE) |
| `reports/mass_ood_dynamics_forensics_report.md` | B1+B4 root cause |
| `reports/mass_ood_repair_options_report.md` | E.2+E.7 추천 |
| `src/fglc/data/maniskill_schema.py` | TASK_OOD_PARAMS, ID/OOD regime |
| `src/fglc/repair/taxonomy.py` | 20 FailureCauseId |
| `docs/idea/12_TRAINING_STAGES.md` | Stage 3 gate: ≥2 OOD axes |
| `reports/ood_severity_agent_report_scaled_R1.md` | PickCube OOD: FAIL(mass), PASS(friction) |
| `reports/novelty_relevance_agent_report_scaled_R1.md` | CONDITIONAL_PASS |
| `data/fglc/PickCube-v1/dataset_stats.json` | D_x=42, gap 실측값 |
| `data/fglc/PushCube-v1/dataset_stats.json` | D_x=35 확인 |
| `reports/resource_budget_agent_report_scaled_R1.md` | PASS, ~7분 수집 |
| `plans/PHASE_PROGRESS.md` | R0/R1/R2 PASS, R3 PENDING |
| `docs/idea/21_METRICS.md` | 4축 metric 정의 |
| `reports/data_quality_agent_report_scaled_R1.md` | PASS, 450ep 0 reject |
| `reports/mass_ood_metric_validity_report.md` | 16 metric all FAIL |
| `docs/orchestration/agent_reports/2026-05/mass_ood_root_cause_synthesis_RC1.md` | MAJOR_REVISION, E.7+E.2+E.4 권장 |
| `data/fglc/PickCube-v1/quality_report.json` | C4 FAIL, friction_mapping=DEFERRED |
| `src/fglc/data/collector.py` (first 100 lines) | _apply_ood, CollectionConfig |

---

## 판정 요약

| 섹션 | 상태 | 핵심 결론 |
|---|---|---|
| §A Executive Summary | COMPLETE | friction PASS×2, mass FAIL×2, 3 options |
| §B Evidence Audit | COMPLETE | repair ledger 확인, 16 metric FAIL |
| §C Criteria | COMPLETE | 5관점 rubric 정의 |
| §D Axis Survey | COMPLETE | 13 axes, PRIMARY/SECONDARY/DEFERRED/BLOCKED |
| §E Mass Deep Dive | COMPLETE | B1+B4 root cause, P1~P8 평가, threshold 완화 REJECT |
| §F Policy Review | COMPLETE | 7 policies × 5관점, repair loop 매핑 |
| §G Dataset Plan | COMPLETE | 4 stages, seed design, artifact 구조 |
| §H Agent Reports | COMPLETE | A~G 7명 판정 요약 |
| §I Repair Loop | COMPLETE | 16단계, stop conditions, taxonomy 신규 cause 제안 |
| §J Resource Budget | COMPLETE | 4 scenarios, VRAM 안전성 확인 |
| §K Options | COMPLETE | 3 options, risk matrix |
| §L Recommendation | COMPLETE | 사용자 결정 D-1~D-3, 다음 TASK 후보 |
| §M Checklist | COMPLETE | 모든 금지 조건 준수 확인 |
| §N BLOCKED/UNKNOWN | COMPLETE | 5개 카테고리, negative result 공시 |

---

> **최종 확인**: 본 review MD는 read-only 작업입니다.
> 코드/데이터 변경 없음. R3 smoke 실행 없음. R3.passed 생성 없음.
> 어떤 axis도 사전 확정 없음.
> 다음 단계는 §L.2 사용자 결정 D-1~D-3 승인 후 진행합니다.
