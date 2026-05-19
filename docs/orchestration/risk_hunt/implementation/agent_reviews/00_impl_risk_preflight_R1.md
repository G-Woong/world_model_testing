# Agent Report: implementation-risk-critic — PHASE 0 Preflight

**Date**: 2026-05-19  
**Agent**: implementation-risk-critic  
**Topic**: LFD implementation plan pre-check  
**Verdict**: `NEEDS_FIX before Codex TASK authoring`

---

## Gatekeeper 5-Condition Pre-Check

### Condition 1 — Scope / FILES_ALLOWED
**WARN** — PHASE 4 `HistoryEncoder.forward` 반환 타입 변경 시 caller 연쇄 파괴 위험. 모든 caller를 FILES_ALLOWED에 열거해야 함.

### Condition 2 — Dependency Graph
**PASS** — 순서 논리적으로 올바름. PHASE 4 → TextFRCGModel 링크 명시 필요.

### Condition 3 — Test Coverage
**FAIL** — persistent h_t, BOCPD posterior, CUSUM/SPRT 테스트 전무.

### Condition 4 — visibility.py Risks
**WARN** — PHASE 6 visibility.py 변경 시 fragile-file 승인 게이트 TASK STOP_CONDITION에 명시 필수.

### Condition 5 — Top 3 CRITICAL Risks
**FAIL** — 3개 CRITICAL 블로커:

**CRITICAL-1**: `HistoryEncoder.forward` 반환 타입 변경 시 모든 caller 연쇄 파괴.  
**CRITICAL-2**: `falsification.py:66-67` `{0,6}` short-circuit이 BOCPD head 입력의 65%+ 차단.  
**CRITICAL-3**: per-step regime switch → BatchTargets + L_regime cascade 미매핑.
