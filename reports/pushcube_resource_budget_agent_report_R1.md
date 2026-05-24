# Agent G — Resource Budget Auditor Report (PushCube-v1)

**상태**: PARTIAL (사전 추정 완료, 실측 대기)  
**Phase**: R2 data pipeline → Stage 3 진입 전  
**트리거**: Stage 4 Agent G (plans/fglc-step-vectorized-iverson.md §G.7)  
**담당**: feasibility-and-cost-auditor  

---

## 사전 추정 (pushcube_audit_R1.md §4 기반)

### Disk 추정 (D_x=38 가정)

| 시나리오 | PushCube ep | disk | PickCube 합계 | 판정 |
|---|---|---|---|---|
| S1 | 450 | ~8.4 MB | ~18.1 MB | 가능 |
| **S2 (권장)** | **900** | **~16.8 MB** | **~26.5 MB** | **가능** |
| S3 | 900 + PickCube 900 | ~36.2 MB | ~36.2 MB | 가능 |
| S4 | 1800 | ~33.5 MB | ~43.2 MB | 가능 |

디스크 가용: 290,298 MB → 모든 시나리오 4000× 여유.

### 수집 시간 추정

| 시나리오 | PushCube | PickCube 추가 | 총 추가 |
|---|---|---|---|
| S2 | ~14분 | 0 | ~14분 |

### VRAM 추정

- 모델: 150~300 MB (8188 MiB의 < 4%)
- OOM 위험: 없음

## 실측값 (Stage 3 완료 후)

| 항목 | 추정 | 실측 |
|---|---|---|
| PushCube 900ep 수집 wallclock | ~14분 | PENDING |
| disk 실사용량 (5 HDF5) | ~16.8 MB | PENDING |
| 1-epoch smoke VRAM peak | < 300 MB | PENDING |
| D_x 실제값 | 38~42 (추정) | PENDING |

## 판정

**PARTIAL** → PENDING (Stage 3 완료 후 실측값으로 업데이트).

최종 판정 기준:
- PASS: 실측이 추정과 2배 이내, VRAM < 6 GB
- EXPAND: 현 수집량으로 KS 통계 불안정
- SHRINK: 과잉 (해당 없을 것)
