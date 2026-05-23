# Mass OOD Dynamics Forensics 분석 보고서

**보고일**: 2026-05-24  
**역할**: dynamics-forensics-agent (Agent 2)  
**트리거**: T4 — failure-interpretation-critic 역할  
**소스 데이터**: G.1~G.5 분석 결과, raw HDF5 3 split  

---

## 1. 물리 메커니즘 분석: friction vs mass의 dynamics 영향 경로 차이

### joint friction (ood_friction_low)의 영향 경로

`joint_dry_friction=5.0`은 로봇 관절 자체의 **내부 마찰**을 증가시킨다.  
이것은 contact friction(큐브-바닥 간 마찰)이 아니다.

```
τ_effective = τ_motor - 5.0 * sign(qvel)   [Coulomb friction]
qvel_{t+1} = qvel_t + M^{-1} * τ_effective * dt
```

관절 마찰은 **모든 time step, 모든 관절 속도 범위, 접촉 여부와 무관하게** 작용한다.

실측 확인 (G.1):
```
dims 13-15 (qvel):
  train_id:       [0.403, 0.409, 0.406]
  ood_friction:   [0.318, 0.338, 0.278]
  절대 차이:      [-0.085, -0.071, -0.128]  → 20~32% 감소
```

### object mass (ood_mass_low)의 영향 경로

mass=1.5 kg는 큐브의 관성 질량 변경. 물리 경로:
```
F_contact → a_object = F_contact / mass_object
```

이 경로가 작동하려면 **F_contact > 0**, 즉 접촉이 필요.

실측 확인 (G.3):
```
contact_rate = 0.0000 (모든 split)
mean_tcp_dist = 0.999m  (EEF에서 큐브까지 ~1m)
```

**접촉이 없다. mass의 물리 경로가 완전히 차단된다.**

큐브는 테이블 위에 정적으로 놓여 있고, 테이블 반력이 중력을 완전히 상쇄한다.  
결과: mass 변화가 관측 가능한 trajectory에 영향을 주지 않는다.

---

## 2. Per-dim Signal 표: mass-sensitive vs friction-sensitive 차원 식별

| 차원 범위 | 의미 | mass-sensitive? | friction-sensitive? | 관찰 (G.1) |
|---|---|---|---|---|
| dims 0-8 | agent/qpos (관절 위치) | NO (< 0.01 차이) | MARGINAL | qpos는 누적값, 변화 작음 |
| dims 9-17 | agent/qvel (관절 속도) | NO (max diff 0.007) | **YES** (max diff 0.128) | joint friction이 직접 영향 |
| dims 18-28 | agent/extra (tcp_pose, gripper) | NO (~0.0001) | NO | 미세 변화 |
| dims 29-35 | obj_pose (큐브 7-dim pose) | NO (~0.001) | NO | 접촉 없음 → 정적 |
| dims 36-38 | tcp_to_object | NO (~0.013) | NO | EEF 큐브 근처 미이동 |
| dims 39-41 | object_to_goal | NO (~0.010) | NO | 큐브 움직임 없음 |

### dim24 d=1.034 해석 (G.5)

dim24(agent/extra group, dims 18-28)에서 Cohen's d = 1.034이지만 abs delta ≈ 4e-6.  
Cohen's d = Δμ / pooled_σ에서 pooled_σ ≈ 4e-6 (극소 분산).  
해당 차원의 값이 항상 near-zero → 분산이 극히 작아 수치 표준화 시 d가 커 보이는 현상.  
**수치적 artifact. 물리적 mass 신호가 아님.**

---

## 3. contact_rate=0%의 함의

**중력 분석**: 큐브(1.5 kg)는 테이블 위에 정적으로 놓여 있음.  
중력(mg = 1.5×9.81 = 14.7 N)은 테이블 반력으로 완전히 상쇄됨.  
큐브는 움직이지 않음.

**관성 경로 분석**: `F = ma`에서 F=0이면 a=0이고 mass는 irrelevant.

**결론**: contact_rate=0% 상황에서 mass 변화는 **관측 가능한 trajectory에 물리적으로 효과가 없다.**  
ood_mass_low는 train_id와 동일한 dynamics를 생성하는 것이 정확한 물리적 예측이다.

---

## 4. "mass OOD는 약하다" vs "metric이 약하다" 가설 평가

**가설 A: "mass OOD 자체가 약하다" (물리적 주장)** → **옳다**

- contact_rate=0%에서 mass=1.5는 어떤 metric으로 측정해도 ID와 구분 불가
- reward_mean 차이: Δ=0.0006 (통계적으로 무의미, KS p=0.108)
- 큐브가 아예 움직이지 않는 환경에서 큐브의 질량은 무관
- state_delta_norm gap 방향도 불안정 (+0.004, 역전됨)

**가설 B: "metric(state_delta_norm)이 mass를 포착 못 한다"** → **부분적으로 옳음 (secondary)**

- state_delta_norm은 qvel-dominated norm. object signal 희석 가능
- 그러나 현재 상황에서 **object pose 자체가 변하지 않는다** (abs delta < 0.001)
- metric 문제 이전에 물리 신호 자체가 없다
- B2는 secondary 원인, primary는 물리 신호 부재(B1)

---

## 5. 가설 B1 / B2 / B4 Dominant Cause 판정

### B1 (Data artifact): contact_rate=0%, random policy

**지지 증거**:
- contact_rate = 0.0000 (직접 측정)
- tcp_dist = 0.999m (1미터 거리)
- qvel, obj_pose 모든 차원에서 mass 차이 near-zero
- reward_mean 차이 Δ=0.0006 (통계적 무의미)

### B4 (Env artifact): PickCube-v1 + random policy = mass-insensitive

**지지 증거**:
- PickCube-v1 목표: 큐브를 집어 목표 위치로 이동
- random policy는 성공률 0% → 큐브를 접촉하지 못함
- mass가 관련되는 task phase(pick, lift, carry)가 전혀 실행되지 않음
- B4는 B1의 원인: random policy(B4) → contact 없음(B1) → mass 효과 없음

### 최종 판정

**dominant cause: B1 (Data) + B4 (Env) — 동일 인과 체인의 두 레벨**

```
B4: PickCube-v1 + random policy → cube 접촉 동작 발생 안 함
    ↓
B1: contact_rate = 0%, tcp_dist = 0.999m
    ↓
mass의 물리 경로(F=ma on object)가 차단됨
    ↓
mass=1.5 vs mass=0.064의 관측 trajectory가 사실상 동일
    ↓
gap = +0.004 (< threshold 0.01) → FAIL
```

**B2 (Metric artifact)는 tertiary 요인.**  
물리 신호가 존재한다면 qvel-dominance 개선이 필요하지만,  
현재는 신호 자체가 없으므로 metric 개선이 FAIL을 해결하지 못한다.

---

## 6. Negative Result 공시 (숨기지 않음)

1. **mass OOD는 현재 데이터 수집 설정에서 실질적으로 의미 없다.**  
   450ep 수집했지만 ood_mass_low split은 train_id와 구별되지 않는 dynamics를 담고 있다.

2. **Pilot 90ep PASS (gap=0.0148)는 소표본 variance였다.**  
   n=50으로 증가 시 gap=0.004로 드러남. 소표본에서 우연히 통과한 것이었다.

3. **RC-2 (reward_mean_diff로 metric 변경)도 근본 해결이 아니다.**  
   reward_mean 차이 Δ=0.001, KS p=0.107 → 미유의.

4. **RC-3 (gate 완화)은 novelty 신뢰성을 훼손한다.**  
   gap=0.004인 mass OOD를 "충분한 difficulty"라 주장하면 FGLC 핵심 claim 약화.

5. **유일하게 유효한 수리책**:  
   - mass를 훨씬 크게 (3.0+ kg, 단 SSoT 변경 필요) 또는  
   - **contact이 발생하는 task (PushCube-v1)** + 현재 mass 범위 유지  
   - 또는 expert/scripted policy로 수집 방법 변경 (reviewer-defensibility 주의)

---

## 7. FGLC Claim에 대한 함의

mass OOD가 ID와 동일한 dynamics를 생성한다는 것은:
- mass axis에서 wrong-dynamics-hypothesis가 발생하지 않음
- falsification gate β_t가 발화할 근거가 없음
- mass 관련 correction이 필요하지 않음

**mass OOD axis는 현재 데이터 설정에서 FGLC 핵심 claim 검증에 기여하지 못한다.**  
friction axis (gap=0.138, joint velocity에 명확한 signal)는 검증에 기여한다.

mass effect를 검증하려면 반드시 다음 중 하나가 필요:
- (a) EEF가 실제로 큐브를 집는 scripted/expert policy로 수집
- (b) robot arm 자체의 링크 질량 변화 (random policy에서도 qvel에 영향)
- (c) mass가 훨씬 크거나, 접촉력이 발생하는 환경 (PushCube-v1 등)
