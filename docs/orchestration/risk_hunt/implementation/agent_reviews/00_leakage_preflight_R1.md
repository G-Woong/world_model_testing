# Agent Report: frcgw-data-leakage-auditor — PHASE 0 Preflight

**Date**: 2026-05-19  
**Agent**: frcgw-data-leakage-auditor  
**Topic**: LFD planned changes leakage pre-audit  
**Verdict**: `PASS with 2 CRITICAL pre-conditions`

---

## 신규 필드 leakage 위험

| 필드 | 판정 | 이유 |
|---|---|---|
| `regime_switch_t` (PHASE 2) | CRITICAL | ground-truth switch timing = true_change_point급. FORBIDDEN_AGENT_FIELDS 추가 + 사용자 승인 필수 |
| `detection_delay_gt` (PHASE 6) | CRITICAL | regime_switch_t 파생 = oracle timing. 동일 조건 |
| `wrong_prob_learned` | SAFE | 모델 출력, ground truth 아님 |
| `run_length_posterior` | SAFE | 모델 출력, ground truth 아님 |
| `cusum_stat_t` | SAFE | 통계적 집계, ground truth 아님 |
| `detector_*` EvaluationLabels | SAFE (EVALUATION_ONLY) | 평가 전용 |

## 사전 조건

PHASE 2 구현 전 사용자 승인 후 `visibility.py` 수정:
```python
# 추가:
"regime_switch_t",
"detection_delay_gt",
```
mirror 의무: `.claude/hooks/schema_leakage_guard.ps1 $forbiddenTokens` + sync test GREEN.
