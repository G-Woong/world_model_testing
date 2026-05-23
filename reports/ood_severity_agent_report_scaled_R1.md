# ood-severity-critic 보고서 — Step 11-D7 Scaled (450ep) R1

**보고일**: 2026-05-24
**단계**: Scaled Stage 2 (실측, Post-Scaled)
**판정**: FAIL (ood_mass_low gate 미통과)

---

## OOD severity 측정 (state_delta_norm_mean 기준)

| Split | n_ep | state_delta_norm_mean | train_id 대비 gap | gate [0.01, 0.5] | 판정 |
|---|---|---|---|---|---|
| train_id (기준) | 250 | 1.322009 | — | — | 기준 |
| val_id | 50 | 1.308479 | 0.013530 | (참고) | — |
| test_id | 50 | 1.325398 | 0.003389 | (참고) | — |
| **ood_mass_low** (mass=1.5) | 50 | **1.325756** | **+0.003747** | **< 0.01** | **FAIL** |
| ood_friction_low (friction=5.0) | 50 | 1.183966 | 0.138043 | ✓ | **PASS** |

## FAIL 분석

### 원인

`ood_mass_low`의 state_delta_norm_mean이 train_id(1.322009)보다 오히려 **소폭 높음**(1.325756). gap=+0.00375로 임계 0.01 미달.

**근본 원인**: mass=1.5 (default 1.0의 1.5배)는 `state_delta_norm` metric으로 측정 시 ID와 통계적으로 구분되지 않음.
- Pilot(10ep)에서 gap=0.0148은 소표본(n=10) variance였음 — 실제 효과가 아님.
- Scaled(50ep)에서 수렴하면서 실제 gap=0.0038로 드러남.
- Random policy에서 mass 1.5배 증가는 step-wise state delta norm에 측정 가능한 방향성 편향을 주지 않음 (torque-free random action 특성).

### OOD_TOO_EASY 발화

`verify_ood_severity()` → `OOD_TOO_EASY` 조건 충족 (gap < delta_min=0.01).

---

## Repair Candidate 목록

### RC-1: mass 강도 증가 (추천)

```
id: OOD_TOO_EASY_mass_2x
patch: {"object_mass": 3.0}  # 1.5 → 3.0 (3× default)
cost_minutes: 20
risk: 0.3
rationale: mass=1.5는 state_delta_norm gap 0.004. mass=3.0에서 gap≥0.01 가능성 있음.
           단, 너무 극단적이면 OOD_TOO_HARD(gap>0.5) 발화 위험.
```

**중간값 후보**: mass=2.0 또는 mass=2.5 probe 1~5ep로 gap 예비 측정 권장.

### RC-2: OOD severity metric 변경

```
id: OOD_SEVERITY_METRIC_REWARD_DIFF
patch: {"severity_metric": "reward_mean_diff"}
cost_minutes: 0  # 코드 변경, 재수집 불필요
risk: 0.4
rationale: reward_mean diff가 더 mass-sensitive할 수 있음.
           train_id reward_mean=0.046 vs ood_mass_low=0.061 → diff=0.015 ≥ 0.01.
           하지만 reward metric으로 severity를 정의하면 SSoT 변경 필요.
```

**주의**: metric 변경은 manifest.py::verify_ood_severity() + 19_BASELINES.md 동기화 필요.

### RC-3: gate 임계 완화 (axis별 분리)

```
id: OOD_GATE_MASS_THRESHOLD_RELAX
patch: {"delta_min_mass": 0.003}  # mass axis에 한해 0.01 → 0.003
cost_minutes: 0
risk: 0.6
rationale: mass 물리 효과가 state_delta_norm으로 잘 포착되지 않음을 인정.
           gap=0.0038 > 0.003이면 PASS.
           단, gap=+0.0038(방향이 양수)이라 mass 증가가 state_delta를 오히려
           미세하게 증가시키는 방향. 물리적 의미 불분명.
```

**주의**: FGLC novelty 검증에서 mass shift가 dynamics hypothesis shift임을 요구.
gap이 0.003이라도 방향 불확실(±)하면 학습에서 mass-OOD 신호가 약함.

---

## 분포 다양성 리포트 (state_delta_norm 분포 이외 지표)

| 지표 | train_id | ood_mass_low | 차이 |
|---|---|---|---|
| reward_mean | 0.046 (Pilot 기준) | ~0.061 (Pilot) | Δ+0.015 |
| state_delta_norm_mean | 1.322009 | 1.325756 | +0.003747 |
| state_delta_norm_p50 | 1.317310 | 1.324460 | +0.007 |
| state_delta_norm_p95 | 1.835648 | 1.809392 | -0.026 |

> reward 차이가 mass shift의 유일한 양적 신호일 수 있음.

---

## 현재 PASS/FAIL 판정 요약 (Scaled 450ep)

| Agent | 판정 | 비고 |
|---|---|---|
| A (data-quality) | PASS | 450ep, 0 reject |
| B (split-leakage) | PASS (예상) | seed disjoint, hash audit 통과 예상 |
| **C (ood-severity)** | **FAIL** | ood_mass_low gap=0.00375 < 0.01 |
| D (novelty-relevance) | PENDING | mass OOD 신뢰성 문제 발생으로 재평가 필요 |
| E (training-readiness) | PENDING | R3 smoke 금지 (C FAIL로) |
| F (resource-budget) | PASS (예상) | 450ep, VRAM 문제 없음 |

## 판정 결론

**Agent C FAIL → R3 smoke 금지.**

사용자 결정 필요 사항:
1. RC-1: mass 3.0으로 ood_mass_low 재수집 (probe 5ep → gap 확인 → 재수집)
2. RC-2: severity metric을 reward_mean_diff로 변경 (SSoT 영향 있음)
3. RC-3: gate 임계 mass axis 한해 0.003으로 완화 (novelty 신뢰성 저하)
4. mass OOD axis 자체를 포기하고 friction만으로 OOD 검증 진행

**추천**: RC-1 (mass 3.0 probe) → gap 실측 후 결정.
