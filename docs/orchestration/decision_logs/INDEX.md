# Decision Logs Index

작성일: 2026-05-15
근거: `docs/orchestration/03_MAIN_CLAUDE_ORCHESTRATION_PROTOCOL.md §4` + `docs/orchestration/12_HUMAN_FEEDBACK_AND_EVOLUTION_PROTOCOL.md §3`

모든 주요 결정(HUMAN_APPROVAL_REQUEST / PHASE_GATE / SELF_EVOLUTION_PROPOSE)은 이 INDEX를 통해 추적한다.
세부 yaml 블록은 각 월별 파일에 저장된다.

---

| decision_id | date | session | type | subject | selected | status | execution_step |
|---|---|---|---|---|---|---|---|
| DEC_2026-05_001 | 2026-05-15 | 20260515-001 | HUMAN_APPROVAL_REQUEST | orchestration/redesign merge | A | EXECUTED | STEP 2 |
| DEC_2026-05_002 | 2026-05-15 | 20260515-001 | HUMAN_APPROVAL_REQUEST | cleanup 방식 (NC-1 우선 + atomic PR) | B | LOCKED | STEP 9 |
| DEC_2026-05_003 | 2026-05-15 | 20260515-001 | HUMAN_APPROVAL_REQUEST | Codex fast-forward 시점 | A | LOCKED | STEP 7 |
| DEC_2026-05_004 | 2026-05-15 | 20260515-001 | HUMAN_APPROVAL_REQUEST | MCP scaffold 생성 | A | EXECUTED | STEP 3 |
| DEC_2026-05_005 | 2026-05-15 | 20260515-001 | HUMAN_APPROVAL_REQUEST | atomic PR 시작 지점 | B | EXECUTED | STEP 4 |
| DEC_2026-05_006 | 2026-05-15 | 20260515-001 | HUMAN_APPROVAL_REQUEST | P4 첫 task 전 G1~G6 검토 | C | LOCKED | STEP 8 |
| DEC_2026-05_011 | 2026-05-15 | 20260515-005 | HUMAN_APPROVAL_REQUEST | STEP 5 MCP 등록 범위 (신규 설치 여부) | B | EXECUTED | STEP 5 |
| DEC_2026-05_012 | 2026-05-15 | 20260515-006 | HUMAN_APPROVAL_REQUEST | STEP 5-REAL MCP 실제 설치 범위 (uv+arXiv+SS+하네스 audit) | A | EXECUTED | STEP 5-REAL |
| DEC_2026-05_013 | 2026-05-16 | 20260516-008 | HUMAN_APPROVAL_REQUEST | GitHub MCP v1.0.4 실제 활성화 (Option A+ — Docker, read-only+lockdown) | A+ | EXECUTED | STEP 5-REAL-GITHUB |
| DEC_2026-05_014 | 2026-05-16 | 20260516-011 | SELF_EVOLUTION_PROPOSE | pre_compact hook redirect (Option A dual-write, SEV_2026-05_001 ADOPTION) | A | EXECUTED | STEP 6 |
| DEC_2026-05_003 | 2026-05-16 | 20260516-012 | HUMAN_APPROVAL_REQUEST | Codex fast-forward 실행 (Q1-A+Q2-A, ff-only 5e77f1b, exit 0) | A | EXECUTED | STEP 7 |

---

## 파일 명명

`docs/orchestration/decision_logs/YYYY-MM/session_<id>.md`

## 규칙

- 모든 HUMAN_APPROVAL_REQUEST는 사용자 응답 후 outcome 갱신
- LOCKED 상태 = 다음 세션이 다시 사용자에게 묻지 않음 (실행 승인은 별도)
- 각 실행은 해당 STEP의 PLAN→승인→APPLY 사이클에서 별도 처리
