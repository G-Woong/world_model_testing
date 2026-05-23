# Full Session-end Report Template

근거: `docs/orchestration/08_AGENT_OUTPUT_CONTRACTS.md §5B`

Compact report의 모든 섹션 포함 + 아래 추가 섹션.
Full mode 사용 조건: Phase gate 결정 / Codex merge / agent deep mode / NC 변동 / R 상태 변경

---

```markdown
---
session_id: <YYYYMMDD-NNN>
date: <ISO 8601>
branch: <현재 branch>
mode: full
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

## PHASE_STATUS
<현재 Phase / gate sentinel / blockers>

## CODEX_STATUS
<TASK ID / branch / 마지막 commit / 다음 fast-forward 필요 여부>

## AGENT_REPORTS_GENERATED
<이번 세션에서 생성된 agent report 경로 목록>
<없으면 "none">

## DECISION_LOG_ENTRIES
<이번 세션의 Decision Log 항목 목록 (03 §4 schema 요약)>
<없으면 "none">

## NC_STATUS_UPDATE
<NC-1~NC-7 현재 상태>

| NC # | 항목 | 이전 상태 | 현재 상태 | 변경 사유 |
|---|---|---|---|---|
| NC-1 | ... | OPEN | OPEN | carry-forward |

## RISK_FLAGS_UPDATE
<R1~R14 현재 상태 변경사항>
<없으면 "none">
```
