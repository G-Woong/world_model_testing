# 05_SELF_EVOLVING_LOOP.md

Self-Evolving 운영 루프 프로토콜  
작성일: 2026-05-15  
작성자: Main Claude (Phase 2)  
근거: `docs/orchestration/01_PERMISSION_SCOPE_AUDIT.md` R3/R7, `docs/orchestration/PHASE1_GATE_REPORT.md` NC-6

---

## 1. Self-evolving Definition

**Self-evolving의 대상은 "운영 프로토콜"이다. settings 파일이 아니다.**

개선 가능 대상:
```text
- Main Claude 운영 rules (docs/orchestration/03~08 문서)
- Codex task schema (04_CODEX_FEEDBACK_LOOP_PROTOCOL.md §3)
- Agent report contract (08_AGENT_OUTPUT_CONTRACTS.md)
- session report 구조
- recurring failure taxonomy (§6)
- DECISIONS_REQUIRED 형식
```

개선 불가 대상 (직접 수정 절대 금지):

---

## 2. Forbidden Direct Modifications

아래 파일/디렉터리는 self-evolving 루프에서 **직접 수정 절대 금지**. 모든 변경은 human approval branch에서만.

```text
.claude/settings.json
.claude/settings.local.json
.claude/agents/
.claude/hooks/
.claude/skills/
.claude/commands/
.mcp.json
CLAUDE.md
paper_context_ref/
scripts/run_codex_task.ps1
.agent_tasks/codex_prompt_template.md
outputs/phase_gates/
```

이 목록은 `codex_orchestration_rules.md` §"Codex 절대 수정 금지 경로"의 super-set이다.

---

## 3. 9-Step Self-Evolution Procedure

```text
Step 1. ISSUE DETECTED
        - recurring failure 감지 (§6 taxonomy 참조)
        - 사용자 feedback 수신
        - Agent Team report에서 패턴 발견
        - CRITICAL/WARNING gate 반복 발동

Step 2. EVIDENCE COLLECTED
        - 관련 파일 경로 + 라인 번호
        - 관련 log artifact
        - 재현 조건 명시

Step 3. IMPROVEMENT CANDIDATE GENERATED
        - 구체적 변경 내용 (what + where)
        - 기대 효과 (expected_benefit)
        - 관련 프로토콜 문서 (03~08 중 어느 것)

Step 4. RISK ASSESSED
        - 변경이 FRCG-WM scientific contract에 영향을 주는가?
        - 변경이 다른 프로토콜 문서와 모순되는가?
        - rollback 방법이 명확한가?

Step 5. HUMAN APPROVAL REQUESTED
        - DECISIONS_REQUIRED 섹션으로 사용자에게 전달 (08_AGENT_OUTPUT_CONTRACTS.md §7)
        - settings/hook/agent/MCP 변경 포함 시: 별도 human approval gate (03 §6)

Step 6. IMPLEMENTATION BRANCH PLANNED
        - 변경 대상이 protocol 문서라면: orchestration/redesign 또는 신규 branch에서만
        - 변경 대상이 settings/hooks라면: 별도 permission-change branch (Phase 3+ 전용)

Step 7. POST-CHANGE VALIDATION PLAN DEFINED
        - 어떤 테스트/smoke-run으로 변경이 올바른지 확인할 것인가?
        - 어떤 CRITICAL/WARNING gate를 재실행해볼 것인가?

Step 8. ROLLBACK PLAN DEFINED
        - 어떻게 이전 상태로 되돌릴 것인가? (git revert / 파일 복원)
        - rollback이 다른 작업에 미치는 영향?

Step 9. ADOPTED / REJECTED LOG
        - 결과를 self-evolution log에 기록 (§4 schema)
        - ADOPTED: index.md 갱신
        - REJECTED: 이유 및 재검토 조건 기록
```

---

## 4. Self-evolution Log Schema

경로: `docs/orchestration/self_evolution/YYYY-MM/session_<id>.md`

```yaml
evolution_id: <SEV_YYYY-MM_NNN>
date: <ISO 8601>
trigger: <RECURRING_FAILURE | USER_FEEDBACK | AGENT_REPORT | GATE_PATTERN | CODEX_SCOPE_VIOLATION>
observed_failure: <무엇이 반복 실패했는가>
evidence:
  - path: <파일 경로>
    line: <라인 번호>
    description: <해당 증거 설명>
affected_component: <03 | 04 | 05 | 06 | 07 | 08 | settings (requires human approval)>
proposed_improvement: <구체적 변경 내용>
expected_benefit: <기대 효과>
risk: <HIGH | MED | LOW>
required_approval: <HUMAN | AUTO>
adoption_status: <ADOPTED | REJECTED | PENDING>
adopted_in_branch: <적용된 branch (없으면 none)>
rollback_method: <되돌리는 방법>
next_review_date: <YYYY-MM-DD>
notes: <기타 메모>
```

---

## 5. Index 파일

경로: `docs/orchestration/self_evolution/index.md`

형식:
```markdown
# Self-Evolution Index

| evolution_id | date | trigger | component | status | summary |
|---|---|---|---|---|---|
| SEV_2026-05_001 | 2026-05-15 | ... | ... | PENDING | ... |
```

새 evolution log 생성 시마다 index.md를 갱신한다.

---

## 6. Recurring Failure Taxonomy

| 유형 | 예시 | 우선 대응 |
|---|---|---|
| **Main Claude 판단 오류** | context bundle을 잘못 라우팅함 / phase 판정 오류 | 03 §3 Task Intake Flow 보완 |
| **Codex 반복 실패** | 동일 forbidden_paths 반복 위반 / test 반복 실패 | 04 §10 Scope Violation 패턴 기록 + TASK schema 강화 |
| **Agent report 품질 저하** | 해결책 없는 비판 / citation 미검증 | 08 §11 contract 강화 |
| **사용자 feedback 누락** | DECISIONS_REQUIRED 응답 없음 / NC 항목 carry-forward 반복 | 03 §4 Decision Log 갱신 + PHASE_GATE에 미결 항목 명시 |
| **Gate 반복 발동** | CRITICAL GATE가 같은 원인으로 3회+ 발동 | 해당 모듈의 STOP_CONDITION 강화 |

---

## 7. Session-end Report와 Self-evolution 연결

모든 session-end report (08_AGENT_OUTPUT_CONTRACTS.md §5)는 다음 섹션을 포함한다:

```markdown
## Self-Evolution Candidates

| 관찰된 패턴 | 영향 컴포넌트 | 제안 개선안 | 우선순위 |
|---|---|---|---|
| ...        | ...          | ...        | HIGH/MED/LOW |
```

이 섹션에 기록된 항목은 다음 세션 시작 시 9-step procedure로 진행 여부를 판단한다.

---

## 8. DECISIONS_REQUIRED 섹션 형식

session 내에 사용자 결정이 필요한 항목이 발생하면 아래 형식으로 정리한다.

```markdown
## DECISIONS_REQUIRED

다음 항목에 대해 사용자 결정이 필요합니다.

| ID | 항목 | 옵션 A | 옵션 B | 권장 | 배경 |
|---|---|---|---|---|---|
| DEC_001 | ... | ... | ... | A | ... |
```

사용자가 결정하지 않은 항목은 작업을 중단하거나 default 옵션으로 진행하지 않는다.  
단, 사용자가 "default로 진행"을 명시한 경우에는 권장 옵션을 선택하고 Decision Log에 기록한다.

---

## 9. Skill(update-config) 처리 (R3 대응)

**현재 상태**: `settings.local.json`에 `Skill(update-config)` allow 등록됨 (R3 HIGH).

**Phase 3 처리 계획**:
- 옵션 A: `Skill(update-config)` allow 제거 → settings 자가 수정 통로 완전 차단
- 옵션 B: `explicit-approval-only` 조건 추가 → 사용자 명시 승인 시에만 허용 + audit log 의무화

**Phase 2에서의 조치**: 본 문서에 "self-evolving은 proposal-only" 원칙을 명문화.  
실제 settings 변경은 Phase 3 R1/R2/R3 처리 PR에서 human approval 후 실행.

---

## 10. Monthly Review Cadence

매월 첫 번째 세션 시작 시:

```text
1. docs/orchestration/self_evolution/index.md 확인
2. PENDING 항목 중 ADOPTED 또는 REJECTED 미결정 항목 검토
3. 지난 month 동안 반복된 failure pattern 확인
4. 해당 월 DECISIONS_REQUIRED 미결 항목 확인
5. 필요 시 새 self-evolution log 생성
```
