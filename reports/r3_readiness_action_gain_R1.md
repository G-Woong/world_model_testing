# R3 Readiness Report: friction + action_gain 2-axis

**Date**: 2026-05-24
**Branch**: memory-redesign-2026-05-16
**Stage**: Stage 5 (D-7: sentinel NOT generated, 사용자 결정 필요)
**Author**: Claude (main session)

---

## 1. 2-Axis PASS 요약

| Axis | Split | PickCube gap | PushCube gap | KS p | \|a\| Cohen's d | Status |
|---|---|---|---|---|---|---|
| friction | ood_friction_low | 0.13804 | 0.12357 | <0.01 | N/A (state-based) | ✅ PASS |
| action_gain | ood_gain_low | **0.3999** | **0.3834** | ≈0 | 8/8 dims >0.3 | ✅ PASS |
| **2-axis** | — | — | — | — | — | **✅ BOTH PASS** |

R3 smoke 2-axis readiness: **READY**

---

## 2. friction axis 재검증 결과

| Task | ood_friction_low gap | Threshold |
|---|---|---|
| PickCube-v1 | 0.13804 | >0.01 ✅ |
| PushCube-v1 | 0.12357 | >0.01 ✅ |

(from build_split.py OOD severity check, 2026-05-24 rebuild)

---

## 3. action_gain axis Stage 4 결과

| 메트릭 | PickCube | PushCube | 기준 | 결과 |
|---|---|---|---|---|
| state_delta_norm gap | 0.3999 | 0.3834 | >0.01 | ✅ |
| KS p-value | ≈0 | ≈0 | <0.01 | ✅ |
| \|action\| Cohen's d dims>0.3 | 8/8 | 8/8 | ≥3 | ✅ |
| CI95 half-width | 0.0029 | 0.0027 | <50%×gap | ✅ |
| accept rate | 100% | 100% | ≥99.5% | ✅ |
| n_episodes | 500 | 500 | 충분 | ✅ |

---

## 4. mass FAIL 명시 (negative result)

**mass axis (ood_mass_low)**: FAIL for both tasks.

| Task | ood_mass_low gap | Threshold | Cause |
|---|---|---|---|
| PickCube-v1 | 0.00375 | >0.01 | ❌ FAIL |
| PushCube-v1 | 0.00806 | >0.01 | ❌ FAIL |

**원인**: random policy는 object mass 변화를 충분히 탐색하지 못함.
contact-rich interaction이 없는 random trajectories에서 mass OOD 신호가 미미함.

**처리**: D-6 결정 (사용자 2026-05-24) — 4-axis 완료 후 contact-rich policy track으로 별도 처리.
이 negative result는 R3 진입을 차단하지 않음 (mass는 R3 smoke 2-axis 대상 외).

---

## 5. friction µ_kinetic DEFERRED 방어

**주석**: ood_friction_low는 joint dry friction (Panda robot joints)을 변경하며,
ManiSkill의 `joint_friction` API를 통해 적용됨. object-ground contact의
µ_kinetic은 변경하지 않음. 이 구분은 appendix에서 명시:

> "friction axis는 robot joint dry friction (관절 마찰)을 변경하며,
>  object-surface contact friction과는 다름. contact friction 변경은
>  별도 API 필요 (contact material 변경). R3 scope는 joint friction에 한정."

---

## 6. 잔존 UNKNOWN

| UNKNOWN | 상태 | 처리 |
|---|---|---|
| U-N3 (train_id manifest 250ep vs yaml 50ep) | 영향 없음 (ood_gain_low 별도 split) | 명시적 blocker 아님 |
| U-N4 (Ckpt 4 FAIL vs STEP11 Ckpt 4 PASS 충돌) | mass axis에 관련, D-6 별도 | Stage 5 report 명시 완료 |

---

## 7. Cohen's d Metric 해석 조정

action_gain axis에서 G26 gate는 **`|action|` Cohen's d**를 사용.
이유: gain × clip은 action mean(≈0)이 아닌 action variance를 변경함.
mean-based Cohen's d로는 effect를 측정할 수 없음.

이는 BACKBONE metric 정의 변경 아님:
- BACKBONE § 4축 metric 정의: "제어 return" — 변경 없음
- G26은 데이터 품질 gate (실험설계 세부사항)이지 논문 핵심 claim metric 아님

---

## 8. R3 진입 권고

**권고**: R3 진입 가능

**근거**:
1. friction + action_gain 2-axis PASS (state_delta gap, KS, Cohen's d 모두 충족)
2. 500ep × 2 task × 2 axis = 1000ep OOD 데이터 준비 완료
3. 코드 변경 (7파일): tests PASS (forbidden field, split integrity 회귀 없음)
4. negative result (mass FAIL) 명시 완료 — 숨기지 않음

**R3 진입을 위해 사용자가 해야 할 것**:
```
/fglc-phase-check --pass R3
```
이 명령 없이 R3.passed sentinel은 생성되지 않음 (D-7 준수).

---

## 9. 사용자 결정 요청 항목

1. **R3 진입 승인**: `/fglc-phase-check --pass R3` 실행 여부
2. **U-N3 처리**: train_id manifest ep count 불일치 (250ep 수집 vs yaml 50ep 참조) — 무시 또는 yaml 동기화
3. **mass repair track 시작 시점** (D-6): 4-axis 후 contact-rich policy 도입 시점 결정
4. **latency/noise axis 진입** (D-3/D-4): R4 이후 진입 결정

---

## 10. Stage 0~5 완주 확인

| Stage | 상태 | Commit |
|---|---|---|
| Stage 0 | ✅ PASS | 21b6513 |
| Stage 1 | ✅ PASS (7 files, tests green) | f10936c |
| Stage 2 | ✅ PASS (16/16 lenient gates) | 92024b0 |
| Stage 3 | ✅ PASS (25/25 strict gates) | 92024b0 |
| Stage 4 | ✅ PASS (30/30 full gates) | cf45f07 |
| Stage 5 | ✅ REPORT 작성 (sentinel 미생성) | 현재 |

**EXECUTION_PASS**: Stage 0~5 완주, 30 gates Stage 4 PASS, R3 readiness report 작성, sentinel 미생성 (사용자 결정 대기).
