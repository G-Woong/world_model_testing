# Agent C — OOD Severity Critic Report (PushCube-v1)

**상태**: PENDING — Stage 3 PushCube full collection 완료 후 populate  
**Phase**: R2 data pipeline → R3 진입 전  
**트리거**: Stage 4 Agent C (plans/fglc-step-vectorized-iverson.md §G.3)  
**담당**: ood-severity-critic + claim-metric-alignment-auditor  
**입력**: PushCube-v1 5 HDF5 + dataset_stats.json  

---

## Mass OOD Severity (Primary, H15)

| Metric | Value | Threshold | 판정 |
|---|---|---|---|
| state_delta_norm gap | PENDING | > 0.01 | — |
| KS test p | PENDING | < 0.05 | — |
| Cohen's d | PENDING | > 0.3 | — |
| 95% CI lower bound | PENDING | > 0 | — |

### Probe 참조 (n=50)

| Metric | Probe (n=50) | Full 예측 (n=100) |
|---|---|---|
| gap | 0.017756 | 안정적 기대 |
| KS p | 0.0217 | < 0.05 기대 |
| t-test p | 0.0600 (borderline) | < 0.05 기대 (n↑) |

## Friction OOD Severity (Secondary)

| Metric | Value | 판정 |
|---|---|---|
| state_delta_norm gap | PENDING | — |
| KS test p | PENDING | — |

## PickCube Contrast

| Task | OOD axis | gap | KS p | 판정 |
|---|---|---|---|---|
| PickCube-v1 | friction | 0.1380 | (확인) | PASS |
| PickCube-v1 | **mass** | 0.0038 | (확인) | **FAIL** |
| PushCube-v1 | mass | PENDING | PENDING | — |
| PushCube-v1 | friction | PENDING | PENDING | — |

## 판정

**PENDING** — Stage 3 완료 후 채워질 것.

최종 판정 기준 (H15):
- PASS: gap > 0.01 AND KS p < 0.05 AND Cohen's d > 0.3
- PATCH_REQUIRED: metric 추가 권고
- FAIL: 재수집 또는 task 재고 → repair loop entry
