# 08_AGENT_OUTPUT_CONTRACTS.md

Agent Output 표준 계약서  
작성일: 2026-05-15  
작성자: Main Claude (Phase 2)  
근거: `docs/orchestration/06_AGENT_TEAM_BLUEPRINT.md`, `docs/orchestration/07_RESEARCH_CRITIC_AGENTS.md`, `.claude/rules/codex_orchestration_rules.md`

---

## 1. Standard Agent Report Template

모든 agent report는 아래 frontmatter + 본문 구조를 따른다.

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

**비판만 하고 끝나는 report는 실패 처리.** 모든 RISK 항목에 resolution + verification 필수.

---

## 2. Main Claude Synthesis Report Template

Deep mode 완료 후 Main Claude가 작성.

```markdown
---
synthesis_id: <synthesis_YYYYMMDD_NNN>
topic: <주제>
agents_called:
  - agent: <agent 이름>
    report_path: <report 경로>
    verdict: <PASS | FAIL | NEEDS_REVISION>
timestamp: <ISO 8601>
---

## COMMON_RISKS
<여러 agent가 공통으로 제기한 위험 (우선순위 순)>

## CONFLICTING_OPINIONS
| issue | agent_A | agent_B | main_claude_resolution |
|---|---|---|---|

## FINAL_ACTION_ITEMS
| priority | action | type | target |
|---|---|---|---|
| HIGH | ... | CODEX_TASK | ... |
| MED | ... | HUMAN_APPROVAL | ... |
| LOW | ... | HOLD | ... |

## PHASE_GATE_IMPACT
<이 synthesis 결과가 Phase gate 판정에 영향을 주는가? YES/NO + 근거>

## UNKNOWN_ITEMS
<아직 해소되지 않은 UNKNOWN 항목>
```

---

## 3. Codex Task Handoff Template

Main Claude가 Codex에게 전달하는 TASK 파일. `04_CODEX_FEEDBACK_LOOP_PROTOCOL.md §3` 15 필드 기반.

```yaml
# .agent_tasks/codex_queue/TASK_XXXX_<short-name>.md

TASK_NAME: TASK_XXXX_<short-name>
TASK_ID: TASK_XXXX
BACKGROUND: |
  <작업 배경 및 연구 맥락>
  <근거 MD: paper_context_ref/XX_*.md>
GOAL: |
  <달성해야 할 구체적 목표>
FILES_ALLOWED:
  - src/frcgw/...
  - tests/...
  - configs/...
FILES_FORBIDDEN:
  - .claude/
  - CLAUDE.md
  - .mcp.json
  - paper_context_ref/
  - docs/orchestration/
  - outputs/phase_gates/
  - scripts/run_codex_task.ps1
RELATED_AGENT_REPORT_IDS:
  - docs/orchestration/agent_reports/YYYY-MM/<agent>_<topic>_<id>.md
CONTEXT_DOCS:
  - paper_context_ref/XX_*.md
REQUIRED_IMPLEMENTATION: |
  - 구현 요구사항 1
  - 구현 요구사항 2
NON_GOALS: |
  - 이번 task에서 하지 않는 것
IMPLEMENTATION_CONSTRAINTS: |
  - 금지 패턴: (예: forbidden field 목록)
  - 금지 필드: true_regime, true_control_grammar, ...
REQUIRED_TESTS:
  - tests/test_<module>.py::test_<case>
ACCEPTANCE_CRITERIA: |
  - 기준 1
  - 기준 2
COMMIT_MESSAGE: |
  feat(<scope>): <설명>
REQUIRED_OUTPUT_REPORT: docs/orchestration/codex_reports/TASK_XXXX.md
SANDBOX_MODE: default  # bypass 필요 시 이유 명시 후 human approval
MAX_REJECT_COUNT: 2
ESCALATION_CONDITION: |
  3회 reject 또는 forbidden_paths 위반
STOP_CONDITION: |
  - forbidden_paths 수정 시
  - forbidden inference field가 model input에 등장 시
  - REQUIRED_TESTS 통과 불가능한 구조적 blocker 발견 시
SOURCE_BRANCH: orchestration/redesign
CODEX_BRANCH: codex/TASK_XXXX_<short-name>
```

---

## 4. Rejection Decision Template

Main Claude가 Codex 결과를 reject할 때 사용.

```markdown
---
rejection_id: REJ_TASK_XXXX_NNN
task_id: TASK_XXXX
timestamp: <ISO 8601>
max_retries_remaining: <2 | 1 | 0>
---

## BLOCKING_REASONS
1. <이유 1 (파일 경로 + 라인 번호 포함)>
2. <이유 2>

## REQUIRED_FIXES
1. <수정 요구사항 1>
2. <수정 요구사항 2>

## FILES_ALLOWED_FOR_FIX
- <이번 fix에서만 허용하는 파일>

## EVIDENCE
<근거 diff 발췌 또는 파일 경로>

## RE_REVIEW_CRITERIA
- [ ] <다음 RESULT.md에서 확인할 항목 1>
- [ ] <다음 RESULT.md에서 확인할 항목 2>

## HUMAN_ESCALATION_CONDITION
<언제 human review로 넘길지>
```

---

## 5. Session-end Report Template

### 5A. Compact Session-end Report

```markdown
---
session_id: <식별자>
date: <ISO 8601>
branch: <현재 branch>
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
<없으면 "none". 있으면 §7 형식>

## SELF_EVOLUTION_CANDIDATES
<없으면 "none". 있으면 관찰된 패턴 + 제안 개선안>

## NEXT_SESSION_START_WITH
<다음 세션 첫 작업>
```

### 5B. Full Session-end Report

Compact report의 모든 섹션 포함 + 아래 추가:

```markdown
## PHASE_STATUS
<현재 Phase / gate sentinel / blockers>

## CODEX_STATUS
<TASK ID / branch / 마지막 commit / 다음 fast-forward 필요 여부>

## AGENT_REPORTS_GENERATED
<이번 세션에서 생성된 agent report 경로 목록>

## DECISION_LOG_ENTRIES
<이번 세션의 Decision Log 항목 목록 (04 §4 schema 요약)>

## NC_STATUS_UPDATE
<NC-1~NC-7 현재 상태>

## RISK_FLAGS_UPDATE
<R1~R14 현재 상태 변경사항>
```

---

## 6. Self-evolution Log Template

`docs/orchestration/self_evolution/YYYY-MM/session_<id>.md`에 저장.

```markdown
---
evolution_id: SEV_YYYY-MM_NNN
date: <ISO 8601>
trigger: <RECURRING_FAILURE | USER_FEEDBACK | AGENT_REPORT | GATE_PATTERN | SCOPE_VIOLATION>
---

## OBSERVED_FAILURE
<무엇이 반복 실패했는가>

## EVIDENCE
| path | line | description |
|---|---|---|

## AFFECTED_COMPONENT
<03 | 04 | 05 | 06 | 07 | 08 | settings (requires human approval)>

## PROPOSED_IMPROVEMENT
<구체적 변경 내용 (what + where)>

## EXPECTED_BENEFIT
<기대 효과>

## RISK
<HIGH | MED | LOW>

## REQUIRED_APPROVAL
<HUMAN | AUTO>

## ADOPTION_STATUS
<ADOPTED | REJECTED | PENDING>

## ADOPTED_IN_BRANCH
<적용된 branch (없으면 none)>

## ROLLBACK_METHOD
<되돌리는 방법>

## NEXT_REVIEW_DATE
<YYYY-MM-DD>

## NOTES
<기타>
```

---

## 7. DECISIONS_REQUIRED Template

사용자 결정이 필요한 항목이 있을 때 사용.

```markdown
## DECISIONS_REQUIRED

다음 항목에 대해 결정이 필요합니다. 결정되지 않은 항목은 작업을 계속하지 않습니다.

| ID | 항목 | 옵션 A | 옵션 B | 권장 | 배경 |
|---|---|---|---|---|---|
| DEC_001 | <항목> | <A> | <B> | <A 또는 B> | <배경 한 줄> |

결정 후 응답 형식: "DEC_001: A" 또는 "DEC_001: B" 또는 "DEC_001: <custom>"
```

---

## 8. Evidence / Citation / Source 요구사항

| 항목 유형 | 요구사항 |
|---|---|
| 코드 근거 | 파일 경로 + 라인 번호 |
| 논문 claim | arXiv URL 또는 DOI + 섹션 |
| 실험 결과 | outputs/ artifact 경로 + metric 값 |
| 외부 논문 citation | 최소 2개 출처 교차검증 |
| UNKNOWN | `UNKNOWN (route: paper_context_ref/XX_*.md)` 형식으로 명시 |

placeholder metric / manually typed result / fake number 사용 금지.

---

## 9. Uncertainty 표시 규칙

| 키워드 | 사용 조건 |
|---|---|
| `UNKNOWN` | 정의/근거가 없어서 판단 불가 — 해당 paper_context_ref MD로 라우팅 |
| `TBD` | 정의는 있으나 실험/구현이 없어서 판단 보류 |
| `NEEDS_CONFIRMATION` | 사용자 결정이 필요한 항목 — DECISIONS_REQUIRED 섹션으로 이동 |

이 키워드를 숨기거나 무시하지 않는다.  
UNKNOWN/TBD/NEEDS_CONFIRMATION을 final claim으로 승격하지 않는다.

---

## 10. 비판만 하고 끝나는 Report 금지 규칙

모든 RISK/공격 항목에는 반드시:
1. **해결책** (resolution): 구체적으로 어떻게 고칠 수 있는가
2. **검증법** (verification): 해결됐다는 것을 어떻게 확인하는가

이 두 항목 없이 비판만 나열하면 해당 report는 **실패 처리**된다.  
Main Claude는 실패 처리된 report를 Codex task로 변환하지 않고 agent에게 재작성을 요청한다.

---

## 11. 비판 + 해결책 + 검증법 3종 필수

```text
비판(RISK): 무엇이 문제인가
해결책(resolution): 어떻게 고치는가 (구체적 action)
검증법(verification): 어떻게 확인하는가 (테스트/실험/grep 기준)
```

3종 중 하나라도 없으면 report 미완성으로 처리.
