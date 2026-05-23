# Mass OOD Severity Metric 적합성 평가 보고서

**보고일**: 2026-05-24  
**역할**: metric-validity-critic (Agent 1)  
**트리거**: T4 — OOD severity FAIL 결과 해석 전  
**소스 데이터**: dataset_stats.json, raw HDF5 3 split, G.1~G.5 분석 결과  

---

## 핵심 결론

현재 수집된 데이터 (mass=1.5, random policy, contact_rate=0%, 50ep) 기준:  
**16개 metric 후보 중 어떤 것도 mass OOD를 신뢰할 수 있게 구분하지 못한다.**

---

## 측정 수치 (G.2, G.3, G.4, G.5 결과)

| Split | state_delta_norm_mean | object_pose_delta_norm | reward_mean | reward_max | contact_rate |
|---|---|---|---|---|---|
| train_id (250ep) | 1.322009 | 0.020535 | 0.050382 | 0.403577 | 0.0% |
| ood_mass_low (50ep, mass=1.5) | 1.325756 | 0.020671 | 0.050963 | 0.164098 | 0.0% |
| ood_friction_low (50ep, friction=5.0) | 1.183966 | 0.019985 | 0.050189 | 0.132116 | 0.0% |

gap (train_id vs ood_mass_low):
- state_delta_norm: +0.003747 (FAIL, threshold=0.01의 37%)
- object_pose_delta_norm: +0.000136 (near-zero, 불가)
- reward_mean: +0.000581 (KS p=0.1077, NOT significant)
- reward_max: -0.239479 (큰 gap, but 소표본 단일 통계량)

---

## 16개 Metric 후보 Mass-Sensitivity 평가표

| # | Metric | 현재 gap/신호 | 검출력 (n=50) | 물리적 유효성 | 최종 판정 |
|---|---|---|---|---|---|
| 1 | state_delta_norm (현재) | +0.003747 | < 5% | 낮음 (noise floor) | **FAIL** |
| 2 | object_pose_delta_norm (dims 29-35) | +0.000136 | < 1% | 없음 (미접촉) | **FAIL** |
| 3 | object_z_delta (dim 31/32) | ~0.0001 (추정) | < 1% | 없음 (미접촉) | **FAIL** |
| 4 | tcp_to_object_distance_mean (dims 36-38) | +0.0002 | < 1% | 낮음 | **FAIL** |
| 5 | reward_mean | +0.000581 | < 5% (p=0.108) | 낮음 | **FAIL** |
| 6 | reward_max | -0.239479 | 단일 통계량 불안정 | 중간 | **CONDITIONAL** |
| 7 | per-dim Cohen's d composite (dims 29-41) | max d=0.2803 | 소표본 불안정 | 낮음 | **FAIL** |
| 8 | composite severity (multi-metric) | dim24 d=1.034, abs ~4e-6 | 불안정 | 불명확 | **CONDITIONAL** |
| 9 | object_pose_delta_norm per-dim KS | 분포 사실상 동일 | < 1% | 없음 | **FAIL** |
| 10 | qvel-only delta norm (dims 9-17) | mean\|d\|=0.0180 | < 5% | 낮음 | **FAIL** |
| 11 | extra-only delta norm (dims 18-28) | dim24 abs ~4e-6 | 불안정 | 없음 | **BORDERLINE_FAIL** |
| 12 | contact_detection_proxy (tcp_dist < 5cm) | 0% 모두 | 0% | 없음 | **FAIL** |
| 13 | dim24_mean_shift | abs ~4e-6 | 수치 noise 수준 | 없음 | **FAIL** |
| 14 | object_z_position_mean (abs, static) | 정적 (contact 없음) | < 1% | 없음 | **FAIL** |
| 15 | one-step predictor residual | 별도 학습 필요 | UNKNOWN | 이론적 높음 | **UNKNOWN** |
| 16 | normalized per-dim chi-square | n=50 부족 | n=50에서 낮음 | 이론적 중간 | **CONDITIONAL** |

---

## 핵심 결론: 왜 state_delta_norm이 mass OOD를 감지 못하는가

### 원인 1: 물체 미접촉 — mass 효과의 전달 경로 차단
- contact_rate = 0.0000 (측정됨), mean_tcp_dist = 0.999m
- mass는 물체가 접촉될 때 robot dynamics에 반력으로 영향. 접촉 없으면 효과 없음
- PickCube-v1에서 `set_mass(1.5)`는 cube mass만 변경, robot arm mass 불변

### 원인 2: random policy noise floor dominance
- state_delta_norm_mean ≈ 1.32는 주로 qvel 항(dims 9-17, ~0.4) 지배
- mass=1.5가 만드는 동역학 차이는 random action noise에 완전히 매몰됨
- qvel group mean|d| = 0.0180 → 사실상 효과 없음

### 원인 3: n=50에서 gap=0.0038의 통계적 검출력 한계
- 효과 크기 d = 0.0038/0.10 ≈ 0.038
- n=50에서 power < 5%
- 방향도 불안정: train < mass_ood (물리적으로 역전 가능성 = noise 신호)

### dim24 d=1.034 해석
- Cohen's d = Δμ / pooled_σ에서 분모(pooled_σ) ~4e-6인 극소 분산
- 실제 신호 크기 4e-6는 float32 수치 정밀도 이슈 가능성
- 순수 수치 artifact, 물리적 mass 신호 아님

---

## Metric으로 mass OOD를 살릴 수 있는가?

**판정: PATCH_REQUIRED (조건부)**

현재 데이터에서는 불가. 다음 경로 변경 시 가능성 있음:

**경로 1 (우선)**: mass=3.0+ 재수집 후 state_delta_norm 재평가  
**경로 2 (대안)**: PushCube-v1 task variant (contact-dependent mass 효과 직접 포착)

### 구하기 어려운 metric 후보 (추가 조건 필요)
- Candidate M-A: `qvel_delta_norm` (dims 9-17) — robot arm link mass 변경 여부 확인 필요
- Candidate M-B: `reward_p95` (95th percentile) — n=50 소표본 분산 문제, 순환논리 위험

---

## 최종 판정: PATCH_REQUIRED

- threshold 단순 완화 (delta_min 0.01→0.003)는 **last resort, 권장하지 않음**
- gap=0.004, 방향 불안정, 물리 신호 없음 → 완화해도 신뢰성 없음
- 근본 해결 경로: E.7 + E.2 (friction-only R3 진행) + E.4 (PushCube probe)

---

## FGLC 과학적 계약과의 연결

FC-5 (Contribution 5): "5개 OOD 축(mass/friction/latency/noise/action_gain) 평가"가 직접 영향받음.  
mass OOD severity gate FAIL → mass axis에서 falsification AUROC, return 개선 보고 불가.  
**현재 FAIL 상태에서 R3 smoke test 진행 금지.** 해결이 선행되어야 함.
