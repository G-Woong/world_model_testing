# Self-Evolution Index

작성일: 2026-05-15
근거: `docs/orchestration/05_SELF_EVOLVING_LOOP.md §5`

오케스트레이션 프로토콜의 자가 개선 이력.
각 항목은 `self_evolution/YYYY-MM/SEV_<id>.md`에 상세 기록.

---

| evolution_id | date | trigger | component | status | summary |
|---|---|---|---|---|---|
| SEV_2026-05_001 | 2026-05-15 | AGENT_REPORT | settings (hook) | ADOPTED | pre_compact hook dual-write 전환: session_reports primary + PHASE_PROGRESS legacy pointer (DEC_014, STEP 6, branch: memory-redesign-2026-05-16) |

---

## 규칙

- evolution_id 형식: `SEV_YYYY-MM_NNN`
- PENDING: 제안됨, human approval 대기
- ADOPTED: 적용됨 (branch 명시)
- REJECTED: 기각됨 (사유 명시)

## Self-evolution 9-step procedure

1. ISSUE DETECTED
2. EVIDENCE 수집
3. CANDIDATE 작성 (`_TEMPLATE_log.md` 참조)
4. RISK 평가
5. HUMAN APPROVAL 요청
6. BRANCH 생성
7. VALIDATION
8. ROLLBACK 방법 확인
9. LOG 갱신 (ADOPTED/REJECTED)
