# Mass OOD Repair Options 분석 보고서

**보고일**: 2026-05-24  
**역할**: OOD-axis-repair-planner (Agent 4)  
**트리거**: T2 (실험설계 변경 전)  
**소스**: Agent 1~3 결과, G.1~G.5 forensic 데이터  

---

## Forensic 데이터 확정 사실

```
Root cause: B1 (Data artifact) + B4 (Env artifact) 복합
- contact_rate = 0.0% (tcp_dist ~1m, random policy)
- object_pose_delta_norm gap = 0.000136 (near-zero, 구분 불가)
- state_delta_norm gap = +0.004 (FAIL, threshold=0.01)
- dim24 Cohen's d = 1.034 but abs delta = 4e-6 (수치적 artifact)
- friction 작동 이유: joint friction → robot velocity에 접촉 독립적 영향
- mass 미작동 이유: mass → object dynamics, 접촉 없으면 효과 없음
- reward_max: train=0.4036 vs mass=0.1641 (gap=0.24, but n=50 소표본)
- reward_mean: 사실상 동일 (Δ=0.0006, KS p=0.107)
```

---

## 7개 후보 평가 표

| 후보 | 실효성 | SSoT 영향 | 구현 시간 | reviewer-defensibility | risk score | 판정 |
|---|---|---|---|---|---|---|
| E.1 severity metric 보강 (composite) | **낮음** (contact=0%에서 object metric도 near-zero) | 없음 | 2~3시간 | 0.50 | 0.55 | 보류 |
| E.2 mass secondary tier 격하 | **높음** | 없음 | 0시간 | 0.70 | 0.30 | **추천 1** |
| E.3 severity metric 교체 | **낮음** (dim32 gap=0.0001) | 없음 | 2~3시간 | 0.50 | 0.55 | 비추천 |
| E.4 PushCube-v1 task variant | **높음** | 없음 (18_DATA:54 허용) | 1~2시간 probe | 0.80 | 0.20 | **추천 2** |
| E.5 scripted reaching policy | 중간 | 없음 | 3~5시간 | 0.40 | 0.60 | 비추천 |
| E.6 composite reward/state/object | **낮음** (reward_max 통계 취약) | 없음 | 1~2시간 | 0.35 | 0.65 | 비추천 |
| E.7 friction-only R3 + mass BLOCKED | **높음** | 없음 | 0시간 | 0.75 | 0.25 | **추천 1** |

---

## E.1, E.3, E.6의 Forensic 데이터 기반 실효성 상세 평가

### E.1: object_pose_delta_norm composite 보강

**핵심 수치 (G.2)**:
```
train_id:      object_pose_delta_norm = 0.020535 ± 0.001356
ood_mass_low:  object_pose_delta_norm = 0.020671 ± 0.001516
gap = +0.000136  (threshold 0.02 기준의 0.7%)
```

**판정**: contact_rate=0%에서 큐브가 정적이므로 object pose delta도 near-zero.  
E.1이 전제하는 "global L2가 object signal을 희석시켰다"는 가설은 부분적으로 맞지만,  
object-only metric도 gap=0.000136으로 구분 불가.  
**현재 데이터에서 E.1 실효성 없음.**

### E.3: object_z_delta 교체

**핵심 수치 (G.1 dim32)**:
```
train_id dim32 (obj z-related): 0.009679
ood_mass_low dim32:              0.009780
gap = +0.000101  (near-zero)
```

**판정**: dominant cause가 B1+B4이므로 metric 교체로 해결 불가.  
dim32 gap=0.0001이 이를 직접 증명함.  
**현재 데이터에서 E.3 실효성 없음.**

### E.6: reward_max_gap composite

**핵심 수치 (G.4)**:
```
reward_max: train=0.4036, mass=0.1641, gap=0.2395
reward_mean: train=0.0504, mass=0.0510 (사실상 동일)
KS test (reward): p=0.1077 (NOT significant)
```

**reward_max 문제점**:
1. n=50 소표본의 단일 extreme value → 분산 매우 큼
2. reward_mean은 사실상 동일 → reward_max gap은 train_id의 lucky episode 1개를 반영
3. "mass OOD에서 best-case performance 낮다"가 "dynamics hypothesis shift"와 직접 연결 안 됨
4. selective metric 선택 → p-hacking 의심

**판정**: reviewer-defensibility=0.35, ICLR 수준에서 너무 낮음. 비추천.

---

## 최종 추천 우선순위

### 추천 1 (즉시 적용): E.7 + E.2 — friction-only R3 + mass BLOCKED ledger

**실행 조건**: 코드 변경 없음, 재수집 없음, SSoT 위반 없음

**논리적 근거**:
- friction axis는 joint-level friction이 state dynamics에 명확한 shift 생성 (gap=0.138, 13.8x threshold)
- mass axis는 contact-dependent physics 요구, random policy에서 contact=0%
- FGLC C1~C4는 friction/latency/noise로 완전히 입증 가능
- 19_BASELINES.md의 oracle-mass baseline은 R10에서 PushCube 등에서 사용 가능

**BLOCKED ledger 기록 형식**:
```
outputs/repair/mass_axis_BLOCKED_2026-05-24.md:
  Reason: contact_rate=0% (tcp_dist=0.999m, random policy)
  Root cause: B1 (Data) + B4 (Env)
  state_delta_norm gap = +0.004 (threshold=0.01 미달)
  object_pose_delta_norm gap = +0.000136 (near-zero)
  Next step: E.4 (PushCube-v1 probe) or F.1 (mass=3.0, BACKBONE 승인 필요)
```

### 추천 2 (병렬 탐색, 1~2시간): E.4 — PushCube-v1 probe

**실행 조건**: PushCube-v1 환경 확인, probe 10~20ep (--no-save), gap 측정

**논리적 근거**:
- PushCube는 cube pushing이 task 정의상 필수 → contact rate 구조적으로 높음
- mass=1.5에서 push force, velocity, trajectory가 달라짐 → state_delta_norm gap 예상
- 18_DATA_BENCHMARKS.md:54에서 PushCube 허용
- gap ≥ 0.01이면 full 재수집, C5 "5개 axis" 주장 완전 복원

**probe 명령 (read-only, --no-save)**:
```powershell
# 탐색용, 저장 안 함
.venv\Scripts\python.exe scripts\fglc\collect_maniskill.py \
  --task PushCube-v1 --split ood_mass_low --ood-mass 1.5 \
  --n-episodes 20 --no-save --verbose
```

### 추천 3 (보류, E.1 재평가): object_pose_delta_norm composite

**조건**: PushCube-v1 probe 후 contact rate 증가 확인 시  
현재는 contact=0%로 실효성 없음. PushCube에서 contact rate가 올라가면 object metric이 의미를 가질 수 있음.  
→ E.4 결과에 따라 재평가.

---

## 비추천 4~7

### E.3: 비추천
dominant cause가 B2(metric)가 아닌 B1+B4(data/env). dim32 gap=0.0001이 이를 증명.

### E.5: 비추천 (이 단계에서는)
1. cherry-picking 의심: mass만 scripted policy로 수집 → 다른 axis와 비대칭
2. collector.py 수정 + 전체 재수집 = 5~7시간 작업, 다른 모든 axis도 영향받음
3. R4+ 단계에서 task performance 평가 시 도입 검토가 적절

### E.6: 비추천
reward_max_gap 통계적 유의성 없음 (KS p=0.107). reviewer-defensibility=0.35.

### F.1 (mass=3.0): 보류 (사용자 BACKBONE 승인 필요)
- contact_rate=0%에서 mass=3.0도 동일한 문제 발생 가능성 높음
- 18_DATA_BENCHMARKS.md:44 변경 필요 → BACKBONE_CHANGE 형식 필수
- E.4 (PushCube probe) 실패 시 최후 수단으로만 검토

### F.2 (mass axis 영구 폐기): 절대 비추천
- oracle-mass baseline 무의미해짐
- "physical parameter OOD" 주장 약화
- 먼저 E.4 probe로 가능성 확인이 선행되어야 함

---

## "Negative Result as Honest Reporting" 전략

논문 Experiments 섹션 권장 서술:

```
OOD-friction 축은 joint-level friction이 robot proprioceptive observation에
직접 반영되어 state_delta 분포에서 측정 가능한 shift를 생성합니다
(gap = 0.138, 13.8x threshold).

OOD-mass 축은 cube mass가 contact-dependent한 dynamics에만 영향을 주기 때문에,
random exploration policy 하에서는 state-level에서 severity를 측정하기 어렵습니다
(gap = 0.004, contact_rate = 0%). 이는 mass shift의 falsification 효과가
contact 빈도에 의존적임을 시사하며, PushCube-v1에서 추가 검증이 필요합니다.
```

이 서술의 장점:
1. selective reporting 아님 (mass FAIL을 명시적으로 기록)
2. p-hacking 아님 (metric을 바꿔 PASS를 만들지 않음)
3. friction/latency/noise positive result가 있으면 mass 한 축의 약점이 전체를 무효화하지 않음
4. PushCube future work로 연결
