# training-readiness-auditor — Step 11-D7 Pilot R0

**판정**: CONDITIONAL_PASS  
**보고일**: 2026-05-23  
**전체 보고서**: `reports/training_readiness_agent_report.md`

## R3 smoke 1-iter 결과

| 항목 | 실측 | 목표 | 판정 |
|---|---|---|---|
| iter_0/metrics.json 생성 | ✓ | 필수 | ✓ |
| ledger.jsonl 생성 | ✓ | 필수 | ✓ |
| id_nll | 0.8726 | ≤ 0.5 | FAIL (epoch 부족) |
| ood_id_nll_diff | -0.0009 | ≥ 0.05 | FAIL (epoch 부족) |
| vram_peak_mib | 33.25 | ≤ 8192 | ✓ (0.4%) |
| wall_clock_minutes | 0.036 | ≤ 30 | ✓ |
| nan_inf | 0 | 0 | ✓ |

## 진단

- `IMPLEMENTATION_BUG_SUSPECTED` (catch-all): stagnant_epochs=0으로 구체 trigger 미발화 정상
- `stop_condition_hit: hook_blocked`: 파이프라인 정상 동작
- NLL 미달: 5 epoch 초기 학습 한계 (50~100 epoch 권장)

## CONDITIONAL_PASS 근거

Artifact 생성, VRAM, wall-clock 모두 통과.  
id_nll 목표 미달은 epoch 수 부족으로 해석 — Scaled 데이터 + 50 epoch으로 재실행 필요.
