# Compact Session-end Report Template

근거: `docs/orchestration/08_AGENT_OUTPUT_CONTRACTS.md §5A`

---

```markdown
---
session_id: <YYYYMMDD-NNN>
date: <ISO 8601>
branch: <현재 branch>
mode: compact
---

## SUMMARY
<이번 세션에서 한 일 1~3줄>

## CHANGED_CREATED
- <파일/artifact>

## TESTS_GATES
- <실행된 gate / 결과>

## BLOCKERS
<없으면 "none">

## DECISIONS_REQUIRED
<없으면 "none". 있으면 08 §7 형식 표>

| ID | 항목 | 옵션 A | 옵션 B | 권장 | 배경 |
|---|---|---|---|---|---|
| DEC_NNN | ... | ... | ... | A | ... |

## SELF_EVOLUTION_CANDIDATES
<없으면 "none". 있으면 관찰된 패턴 + 제안 개선안>

## NEXT_SESSION_START_WITH
<다음 세션 첫 작업>
```
