# Decision Log Template

근거: `docs/orchestration/03_MAIN_CLAUDE_ORCHESTRATION_PROTOCOL.md §4`

---

```yaml
turn_id: <N>
timestamp: <ISO 8601>
decision_type: >
  TASK_ASSIGN | AGENT_CALL | ACCEPT | REJECT | ESCALATE |
  HUMAN_APPROVAL_REQUEST | PHASE_GATE | SELF_EVOLUTION_PROPOSE
subject: <대상 (파일명/TASK_ID/agent명/gate명)>
evidence:
  - <근거 1 (파일 경로 + 라인 번호 또는 artifact)>
  - <근거 2>
risk: HIGH | MED | LOW | INFO
reasoning: <한 줄 판단 근거>
approval: AUTO | HUMAN_REQUIRED | HUMAN_APPROVED | HUMAN_DENIED
outcome: <결과 (실행됨/보류됨/거부됨)>
```

## 사용 방법

- 모든 주요 결정은 1개 항목으로 기록
- `docs/orchestration/decision_logs/YYYY-MM/session_<id>.md`에 저장
- HUMAN_REQUIRED 항목은 사용자 응답 후 outcome 갱신
