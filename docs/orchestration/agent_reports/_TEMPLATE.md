# Agent Report Template (Standard)

근거: `docs/orchestration/08_AGENT_OUTPUT_CONTRACTS.md §1`

---

```markdown
---
agent: <agent 이름 (07 §1~10 중 하나)>
topic: <검토 주제>
report_id: <agent_name_topic_YYYYMMDD_NNN>
triggered_by: <T1~T6 | DISCRETIONARY>
session_id: <세션 식별자>
input_docs:
  - <입력 문서 경로 1>
  - <입력 문서 경로 2>
timestamp: <ISO 8601>
---

## CLAIM
<검토된 claim 또는 검토 대상 요약>

## RISK
<발견된 위험 목록 (severity: HIGH/MED/LOW, 해결책 없는 비판 금지)>

| severity | risk | evidence | resolution | verification |
|---|---|---|---|---|
| HIGH | ... | ... | ... | ... |

## EVIDENCE
<근거 자료 (파일 경로 + 라인 번호, citation URL/DOI)>

## RECOMMENDATION
<구체적 권고 행동 목록>

## ACTIONABLE_CODE_DIRECTION
<코드/실험 변경이 필요한 경우 Main Claude가 Codex task로 변환할 수 있는 구체적 방향>
(코드 직접 작성 금지 — 방향성과 제약만 기술)

## VERIFICATION_PLAN
<어떤 테스트/실험/check로 권고 사항이 반영됐는지 확인할 수 있는가>

## VERDICT
<PASS | FAIL | NEEDS_REVISION | ESCALATE>

## UNKNOWN_ITEMS
<UNKNOWN / TBD / NEEDS_CONFIRMATION 항목 목록 (숨김 금지)>
```

---

**비판만 하고 끝나는 report는 실패 처리.** 모든 RISK 항목에 resolution + verification 필수.
