# 04_CODEX_FEEDBACK_LOOP_PROTOCOL.md

Codex 피드백 루프 프로토콜  
작성일: 2026-05-15  
작성자: Main Claude (Phase 2)  
근거: `.claude/rules/codex_orchestration_rules.md`, `docs/orchestration/PHASE1_GATE_REPORT.md`, `docs/orchestration/01_PERMISSION_SCOPE_AUDIT.md`

---

## 1. Codex Role Definition

**Codex는 task-scoped 구현자이다.** 설계, 리뷰, 승인, reject, phase gate 판단은 하지 않는다.

| 허용 | 금지 |
|---|---|
| FILES_ALLOWED에 명시된 파일 Edit/Write | forbidden_paths 수정 |
| 지정 tests 실행 (`pytest tests/...`) | git force push |
| `codex-work` 또는 `codex/TASK_XXXX` branch에 commit | settings / hooks / agents / MCP 수정 |
| RESULT.md 작성 | Phase gate sentinel 생성/삭제 |
| — | Main Claude / Agent Team 없이 독자 판단 |
| — | Agent Team과 직접 연결 |

---

## 2. Codex Worktree 운영 원칙

- **Worktree 경로**: `C:\Users\computer\Desktop\ICLR_WM_codex` (기존 유지)
- **현재 branch**: `codex-work` (HEAD: `a55cb33`)
- **향후 전환 계획**: task별 `codex/TASK_XXXX_short-name` branch로 단계적 전환
  - 전환 시점: Phase 3 첫 Codex task 할당 시 (human approval 후)
  - 전환 방법: `git -C <codex_worktree> checkout -b codex/TASK_XXXX_short-name`
  - 전환 전 fast-forward gate 필수 (03_MAIN_CLAUDE_ORCHESTRATION_PROTOCOL.md §10)
- **2-commit lag (현재)**: Main HEAD `ba204a8` vs Codex HEAD `a55cb33` — 다음 task 전 fast-forward 필수

---

## 3. Codex Task Schema (15 필드)

기존 `codex_orchestration_rules.md` 10개 헤더와 하위 호환. 5개 확장 필드 추가.

```yaml
# ─── 기존 10개 헤더 (하위 호환) ───
TASK_NAME: <식별자 (예: TASK_1021_p4-env-scaffold)>
BACKGROUND: <작업 배경 및 연구 맥락 (paper_context_ref MD 인용 포함)>
GOAL: <달성해야 할 구체적 목표>
FILES_ALLOWED: <수정/생성 허용 파일 목록 (절대 경로 또는 glob)>
FILES_FORBIDDEN: <수정 금지 파일 목록>
REQUIRED_IMPLEMENTATION: <구현 요구사항 목록>
REQUIRED_TESTS: <작성/통과해야 할 테스트 목록>
ACCEPTANCE_CRITERIA: <PASS 판정 기준>
COMMIT_MESSAGE: <commit message 형식>
STOP_CONDITION: <즉시 중단해야 할 조건>

# ─── Phase 2 확장 5개 필드 ───
TASK_ID: <고유 ID (예: TASK_1021)>
SOURCE_BRANCH: <기준 branch (예: orchestration/redesign 또는 solo/p3-final-boss-cleared)>
CODEX_BRANCH: <Codex 작업 branch (예: codex/TASK_1021_short-name 또는 codex-work)>
RELATED_AGENT_REPORT_IDS: <Agent report 파일 경로 목록 (없으면 none)>
SANDBOX_MODE: <default | bypass>  # bypass는 TASK 파일 명시 시만 허용 (R4 해결)
```

**추가 필드** (TASK 파일에 포함 권장):

```yaml
CONTEXT_DOCS: <참조할 paper_context_ref MD 목록>
NON_GOALS: <이번 task에서 하지 않는 것>
IMPLEMENTATION_CONSTRAINTS: <금지 패턴, 금지 필드, 스타일 제약>
REQUIRED_OUTPUT_REPORT: <docs/orchestration/codex_reports/TASK_XXXX.md>
MAX_REJECT_COUNT: <default 2>
ESCALATION_CONDITION: <3회 reject 또는 forbidden_paths 위반>
```

---

## 4. allowed_files / forbidden_paths 표

### 4.1 Codex 절대 수정 금지 경로 (`codex_orchestration_rules.md` 기반 + Phase 2 확장)

```text
.claude/
CLAUDE.md
.mcp.json
.venv/
data/
outputs/
secrets/
.env* (모든 .env 접두어 파일)
scripts/run_codex_task.ps1
paper_context_ref/
docs/orchestration/          ← Phase 2 추가: 오케스트레이션 문서는 Main Claude 전용
plans/PHASE_PROGRESS.md      ← Phase 2 추가: hook side-effect 파일, Codex 수정 금지
outputs/phase_gates/         ← Phase 2 추가: phase sentinel은 Main Claude만
```

### 4.2 allowed_files 작성 원칙

```text
- 항상 구체적 파일 목록 또는 최소 범위 glob 사용
- "src/**" 같은 광범위 glob은 금지
- 신규 파일 생성이 필요한 경우 경로 명시
- 테스트 파일은 tests/ 아래 구체 경로 지정
```

---

## 5. SANDBOX_MODE 정책 (R4 해결)

| 모드 | 조건 | 허용 동작 |
|---|---|---|
| `default` | TASK 파일에 `SANDBOX_MODE: default` 또는 미지정 | sandbox 활성화 (worktree lock 문제 발생 시 사용자 보고) |
| `bypass` | TASK 파일에 `SANDBOX_MODE: bypass` 명시 | `-BypassSandbox` 허용 (Windows worktree 환경 한정) |

**규칙**: Main Claude는 `SANDBOX_MODE: bypass`를 TASK 파일에 작성하기 전 사용자에게 이유를 명시한다.  
`scripts/run_codex_task.ps1` 실행 시 `SANDBOX_MODE: bypass`가 없으면 `-BypassSandbox` 플래그를 자동 추가하지 않는다.

---

## 6. related_agent_report_ids 연결 방식

```text
1. Agent Team이 report를 docs/orchestration/agent_reports/YYYY-MM/<agent>_<topic>_<id>.md에 작성
2. Main Claude가 report 검증 (08_AGENT_OUTPUT_CONTRACTS.md §1 체크)
3. Main Claude가 synthesis report 작성 (docs/orchestration/agent_reports/synthesis/)
4. 검증된 agent report ID를 TASK 파일 RELATED_AGENT_REPORT_IDS에 기록
5. Codex는 해당 파일을 Read하여 구현 방향 참고 가능 (직접 수정 금지)
```

---

## 7. Codex Result Report Schema

경로: `docs/orchestration/codex_reports/TASK_XXXX.md` (또는 `.agent_tasks/codex_done/TASK_<N>_<NAME>_RESULT.md`)

```yaml
task_id: <TASK_XXXX>
branch: <codex branch>
commit_hash: <HEAD commit>
files_changed: <수정된 파일 목록>
allowed_files_compliance: <PASS | FAIL>  # FAIL이면 어떤 파일이 침범됐는지 명시
tests_run: <실행된 테스트 목록>
test_results: <PASS | FAIL (실패 시 오류 내용)>
rejection_id_handled: <처리된 rejection_id 목록 (없으면 none)>
rejection_response_table: |
  | rejection_id | blocking_reason | fix_applied | verification |
  |---|---|---|---|
  | ...         | ...             | ...         | ...          |
diff_summary: <주요 변경 사항 요약 (3~5줄)>
risk_notes: <발견된 위험이나 불확실성>
ready_for_claude_review: <YES | NO>
```

---

## 8. Claude Reject Decision Schema

rejection_id 생성 규칙: `REJ_<TASK_ID>_<순번>` (예: `REJ_TASK_1021_001`)

```yaml
rejection_id: <REJ_TASK_XXXX_NNN>
task_id: <TASK_XXXX>
blocking_reasons:
  - <구체적 이유 1 (파일 경로 + 라인 번호 포함)>
  - <구체적 이유 2>
required_fixes:
  - <수정 요구사항 1>
  - <수정 요구사항 2>
files_allowed_for_fix: <이번 fix에서 수정 허용 파일 (최소 범위)>
evidence: <근거 파일 또는 diff 발췌>
re_review_criteria: <다음 RESULT.md에서 확인해야 할 항목>
max_retries_remaining: <2 | 1 | 0 (0이면 human escalation)>
human_escalation_condition: <언제 human review로 넘길지>
```

---

## 9. Retry Loop

```text
1회 reject  → max_retries_remaining: 1, Codex 재시도
2회 reject  → max_retries_remaining: 0, Codex 마지막 시도
3회째 FAIL  → 자동 human review escalation
              RESULT.md에 누적 rejection_id 전체 기록
              Main Claude가 사용자에게 escalation report 제출
```

**누적 rejection_id 기록 위치**: RESULT.md의 `rejection_id_handled` 필드에 이전 rejection_id 포함.

---

## 10. Codex Scope Violation Handling

Codex가 forbidden_paths를 수정한 경우:

```text
Step 1. git diff --cached --name-only 확인
Step 2. 금지 경로 감지 → 즉시 REJECT 분류
Step 3. rejection_id 생성 (REJ_<TASK>_SCOPE_VIOLATION_NNN)
Step 4. git merge --abort 또는 git checkout -- <forbidden_file>
Step 5. docs/orchestration/self_evolution/ 에 scope violation 패턴 기록
Step 6. 반복 시 TASK 파일 STOP_CONDITION 강화
```

---

## 11. Fast-forward Checklist

다음 Codex task 시작 전 반드시 수행:

```text
[  ] Main HEAD 확인: git log --oneline -3
[  ] Codex HEAD 확인: git -C <codex_worktree> log --oneline -3
[  ] 뒤진 commit 수 확인: git log codex_HEAD...main_HEAD --oneline
[  ] 빠진 commit 중 forbidden_paths 변경 없음 확인
[  ] fast-forward 결과 dry-run: git -C <codex_worktree> merge --ff-only --no-commit <main_HEAD>
[  ] 결과 DECISIONS_REQUIRED에 기록 → 사용자 승인 요청
[  ] 승인 후: git -C <codex_worktree> merge --ff-only <main_HEAD>
```

---

## 12. Codex ↔ Agent Team 직접 연결 금지

**Codex는 Agent Team report를 직접 받거나 응답하지 않는다.**  
**Agent Team은 Codex task를 직접 생성하거나 할당하지 않는다.**

모든 흐름은 반드시 Main Claude를 경유한다:
```text
Agent Team → report → Main Claude 검증/synthesis → Codex task 변환 → Codex
```

---

## 13. Exit Code 표 (`codex_orchestration_rules.md` §"하네스 출구 코드 참조" 인용)

| 코드 | 의미 |
|---|---|
| 0 | 성공 |
| 10 | precondition 실패 (dirty worktree, lock, divergence, ff-only 실패) |
| 20 | TASK 파일 schema 위반 |
| 30 | Codex 실행 실패 또는 timeout |
| 40 | Codex commit 누락, 금지 경로 위반, RESULT.md 누락 |
| 50 | merge conflict |

exit code 0이 아닌 경우 Main Claude가 원인 분석 후 사용자에게 보고. 자동 재시도 금지.
