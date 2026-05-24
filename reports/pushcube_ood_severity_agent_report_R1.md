# Agent C — OOD Severity Critic Report (PushCube-v1)

**상태**: PENDING — Stage 3 PushCube full collection 완료 후 populate  
**Phase**: R2 data pipeline → R3 진입 전  
**트리거**: Stage 4 Agent C (plans/fglc-step-vectorized-iverson.md §G.3)  
**담당**: ood-severity-critic + claim-metric-alignment-auditor  
**입력**: PushCube-v1 5 HDF5 + dataset_stats.json  

---

## Mass OOD Severity (Primary, H15) — 실측 결과

| Metric | Value (obs_mode=state_dict, n=100) | Threshold | 판정 |
|---|---|---|---|
| train_id state_delta_norm_mean | 1.3144 | — | — |
| ood_mass_low state_delta_norm_mean | 1.3224 | — | — |
| **gap (abs)** | **0.0080** | > 0.01 | **FAIL** |
| probe gap (obs_mode=state, n=50) | 0.0178 | — | 주의: obs_mode 차이로 실측과 다름 |

### 진단

**Root cause**: probe (obs_mode="state")와 collector (obs_mode="state_dict") 간 obs_mode 불일치.  
두 모드에서 state_delta_norm_mean이 다름 (probe: 1.091, state_dict: 1.314).  
**실질적 원인**: random policy → 낮은 contact rate → mass shift가 state dynamics에 반영 안 됨.  
PickCube (0.0038) 와 동일한 패턴. **두 task 모두 random policy에서 mass OOD FAIL.**

## Friction OOD Severity (Secondary) — 실측 결과

| Metric | Value | Threshold | 판정 |
|---|---|---|---|
| ood_friction_low gap | **0.1236** | > 0.01 | **PASS** |

## Task × OOD axis 대조표

| Task | OOD axis | gap (state_dict) | 판정 |
|---|---|---|---|
| PickCube-v1 | **friction** | **0.1380** | **PASS** |
| PickCube-v1 | mass | 0.0038 | FAIL |
| PushCube-v1 | **friction** | **0.1236** | **PASS** |
| PushCube-v1 | mass | 0.0080 | **FAIL** |

**결론**: friction OOD는 두 task에서 모두 PASS. mass OOD는 두 task에서 모두 FAIL (random policy 한계).

## 판정

**FAIL** — mass OOD gap=0.008 < threshold 0.01. 사용자 escalation 필요 (PLAN §N.2).

repair loop 기록: `outputs/repair/loop_pushcube_2026-05-24.jsonl` (iter=1, result=reject, stop_condition=consecutive_inconclusive)

가용 데이터:
- PushCube friction OOD (gap=0.124): PASS — cross-task friction evidence로 활용 가능
- PushCube mass OOD (gap=0.008): FAIL — mass axis claim 불가
