# Session Reports Index

작성일: 2026-05-15
근거: `docs/orchestration/08_AGENT_OUTPUT_CONTRACTS.md §5`

세션 종료 시 Main Claude가 작성하는 공식 source-of-truth.
`plans/PHASE_PROGRESS.md`는 hook auto-append legacy — 이 디렉터리가 공식 기록.

---

| session_id | date | branch | mode | summary | report_path | blocker_count |
|---|---|---|---|---|---|---|
| (초기값) | 2026-05-15 | orchestration/redesign | full | Phase 3 orchestration protocol runtime adoption | (이 파일) | 0 |
| 20260515-001 | 2026-05-15 | orchestration/redesign | full | Phase 3B→4 boundary: STEP 1 Decision Lock-in (DEC_001~006 LOCKED) | session_reports/2026-05/2026-05-15_step1_decision_lockin.md | 0 |

---

## 규칙

- Compact mode: 일반 세션 끝, blockers 0, decisions ≤ 2
- Full mode: Phase gate 결정 / Codex merge / agent deep mode / NC 변동 / R 상태 변경

## 파일 명명

`docs/orchestration/session_reports/YYYY-MM/<session_id>.md`
