# Agent A — Data Quality Gatekeeper Report (PushCube-v1)

**상태**: PENDING — Stage 3 PushCube full collection 완료 후 populate  
**Phase**: R2 data pipeline → R3 진입 전  
**트리거**: Stage 4 Agent A (plans/fglc-step-vectorized-iverson.md §G.1)  
**담당**: data-quality-gatekeeper  
**입력**: PushCube-v1 5 HDF5 + validators.py EpisodeRejectReason 10종  

---

## 검사 항목

| Gate | 기준 | 결과 | 판정 |
|---|---|---|---|
| NaN/Inf 없음 (H1) | 0 위반 | PENDING | — |
| constant-state 차단 (H2) | 0 episode | PENDING | — |
| zero-action 차단 (H3) | 0 episode | PENDING | — |
| no-movement 차단 (H4) | state_delta_norm > 1e-3 | PENDING | — |
| done/truncated consistency (H5) | 마지막 step만 done=True | PENDING | — |
| shape consistency (H6) | 모든 ep 동일 D_x, D_a | PENDING | — |
| trajectory hash duplicate (H7) | intra=0, inter=0 | PENDING | — |
| episode length (H12) | 모든 ep len=50 | PENDING | — |
| success rate (H13) | < 30% (random policy) | PENDING | — |
| reject reason 기록 (H14) | 10종 분포 manifest 기록 | PENDING | — |

## 통계 요약

- n_accepted: PENDING
- n_rejected: PENDING
- reject_rate: PENDING
- rejection_counts: PENDING

## 판정

**PENDING** — Stage 3 완료 후 채워질 것.

최종 판정 기준:
- PASS: accept ≥ 99%
- PATCH_REQUIRED: accept 95~99%
- FAIL: accept < 95%
