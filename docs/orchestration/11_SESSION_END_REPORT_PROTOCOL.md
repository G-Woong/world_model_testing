# 11_SESSION_END_REPORT_PROTOCOL.md

세션 종료 보고서 프로토콜  
작성일: 2026-05-15  
작성자: Main Claude (Phase 3B)  
근거: `docs/orchestration/08_AGENT_OUTPUT_CONTRACTS.md §5`, `docs/orchestration/03_MAIN_CLAUDE_ORCHESTRATION_PROTOCOL.md §4/6`, `docs/orchestration/session_reports/INDEX.md`

---

## 1. 목적

세션/중요 turn 종료 시 상태·변경·위험·다음 결정을 누적하는 공식 체계.

```text
context loss 방지      → 다음 세션 bootstrapping 시 즉시 재개 가능
human feedback loop   → DECISIONS_REQUIRED 항목 사용자에게 전달
self-evolution 수집   → SEV 후보 기록 및 05_SELF_EVOLVING_LOOP 연결
Codex 동기화          → TASK ID / branch / commit 상태 추적
Agent/MCP 동기화      → report ID / MCP call ID 추적
phase gate 추적       → 현재 Phase / gate sentinel / blocker 명시
```

---

## 2. 공식 경로

```text
INDEX:
  docs/orchestration/session_reports/INDEX.md
  (이미 존재 — 본 문서가 schema를 확정하고 column 정의를 보강)

세션 파일:
  docs/orchestration/session_reports/YYYY-MM/YYYY-MM-DD_<session_id>.md

예시:
  docs/orchestration/session_reports/2026-05/2026-05-15_phase3b_complete.md
```

---

## 3. `PHASE_PROGRESS.md`와의 관계

```text
plans/PHASE_PROGRESS.md
  = hook auto-append legacy log
  = pre_compact_phase_handoff.ps1 출력 대상 (현재 경로)
  = 빠르게 쌓이는 비구조화 로그 (운영 source-of-truth 아님)

docs/orchestration/session_reports/
  = 공식 source-of-truth
  = Main Claude가 작성하는 구조화된 기록
  = DECISIONS_REQUIRED / SEV / phase gate 포함
```

**SEV_2026-05_001 연결**:
- `self_evolution/2026-05/SEV_2026-05_001_precompact_redirect.md` (PENDING)
- pre_compact hook의 출력 경로를 `session_reports/`로 redirect하는 제안
- 본 문서는 proposal 등재에 그침 — 실 적용은 Phase 4 human approval 후 별도 atomic PR
- 적용 전까지: `PHASE_PROGRESS.md` 계속 사용, `session_reports/`에도 병렬 기록

---

## 4. Report 종류 5개

| 종류 | 기반 템플릿 | 사용 시점 |
|---|---|---|
| compact report | `_TEMPLATE_compact.md` | 일반 세션 종료, blockers 0, decisions ≤ 2 |
| full report | `_TEMPLATE_full.md` | §5 트리거 중 1개 이상 해당 시 |
| phase transition report | full 의 specialization | branch 변경, Phase gate 판정 시 |
| codex review report | full 의 specialization | Codex accept/reject 직후 |
| agent synthesis link report | compact 의 specialization | Agent Team deep mode 호출 후 |

기존 템플릿 파일 위치:
- `docs/orchestration/session_reports/_TEMPLATE_compact.md`
- `docs/orchestration/session_reports/_TEMPLATE_full.md`

---

## 5. Full Report 필수 조건 (8 트리거)

다음 중 하나라도 해당하면 compact가 아닌 full report를 작성한다.

```text
트리거 1: branch 변경 (신규 생성, 전환, merge)
트리거 2: settings / hook / agent / MCP 변경 (any)
트리거 3: Codex task 생성 또는 accept/reject
트리거 4: Agent Team deep mode 호출
트리거 5: 실험설계 변경 (eval config, ablation 추가/제거)
트리거 6: 논문 claim 변경 (major claim text 수정)
트리거 7: phase gate 판정 (PASS / FAIL / PARTIAL)
트리거 8: cleanup 실행 전후 (archive/delete/move)
```

**CRITICAL gate**: phase 전환 전 full report 없으면 진행 불가.  
**CRITICAL gate**: cleanup 전 full report 없으면 진행 불가.  
**WARNING**: 중요 변경 전 full report 없으면 경고.

---

## 6. Report Template — 필수 18 필드

```markdown
---
session_id: <YYYYMMDD_NNN 또는 phase명_단계>
date_time: <ISO 8601, 예: 2026-05-15T14:30:00+09:00>
branch: <현재 branch>
HEAD: <HEAD commit hash>
current_phase: <Phase 3B | Phase 4 | ...>
---

## files_changed
<수정된 파일 목록 (경로 + 한 줄 설명)>

## docs_created
<신규 생성된 문서 목록>

## codex_status
<TASK ID / branch / 마지막 commit hash / 다음 fast-forward 필요 여부>
예: TASK_1021 미착수 | codex-work a55cb33 | ff 필요 (2 commits lag)

## agent_reports
<이번 세션 생성된 agent report 경로 목록 (없으면 none)>

## mcp_calls
<이번 세션 MCP 호출 ID 목록 (없으면 none)>

## decisions_made
<이번 세션에서 확정된 결정 목록 (DEC_NNN 형식)>
예: DEC_2026-05_001: orchestration/redesign 유지 결정

## risks_discovered
<새로 발견된 risk (R-NNN 또는 신규 명칭)>

## blockers
<진행 불가 blocker (없으면 none)>

## needs_confirmation
<사용자 결정 필요 항목 목록 (NC-NNN 형식)>
예: NC-1 plans/P4_PROGRESS_RECOVERY.md 처리 방법

## self_evolution_candidates
<SEV 후보 (없으면 none)>
예: SEV 후보: pre_compact redirect — SEV_2026-05_001과 연계

## next_recommended_step
<다음 세션 첫 번째 권장 행동 (1줄)>

## verdict
<PASS | PARTIAL | BLOCKED>
PASS: 모든 목표 달성, blocker 없음
PARTIAL: 일부 목표 달성, carry-forward 존재
BLOCKED: 핵심 blocker 해소 필요

## related_reports
<연결된 다른 report ID/경로>
```

---

## 7. INDEX.md 구조 보강

`docs/orchestration/session_reports/INDEX.md`에 아래 column 정의를 추가한다.

```markdown
| session_id | date | phase | summary | branch | linked_reports | next_action |
|---|---|---|---|---|---|---|
```

| column | 정의 |
|---|---|
| session_id | 세션 파일명과 동일 (YYYYMMDD_NNN) |
| date | ISO 8601 date |
| phase | 현재 Phase (Phase 3B / Phase 4 등) |
| summary | 1줄 작업 요약 |
| branch | HEAD branch 이름 |
| linked_reports | 관련 agent report / codex report ID (쉼표 구분) |
| next_action | 다음 세션 첫 action (1줄) |

---

## 8. 작성 책임

```text
작성 가능: Main Claude만
작성 불가: Agent Team 직접 작성 금지 (agent report와 구분)
           Codex 직접 작성 금지

Codex report 연결 방법:
  codex_reports/TASK_XXXX.md → session report codex_status 필드에 경로 기재
  Main Claude가 수동으로 연결

Agent report 연결 방법:
  agent_reports/YYYY-MM/<agent>_<topic>_<id>.md → session report agent_reports 필드
  Main Claude가 검증 후 연결
```

---

## 9. Gate 정책 요약

| 조건 | 등급 | 결과 |
|---|---|---|
| phase 전환 전 full report 없음 | CRITICAL | 진행 불가 |
| cleanup 전 full report 없음 | CRITICAL | 진행 불가 |
| Codex accept/reject 후 report 없음 | WARNING | 경고, 다음 세션 보완 |
| Agent deep mode 후 synthesis 없음 | WARNING | 경고, synthesis 작성 요청 |
| merge 전 compact 또는 full 없음 | WARNING | 경고, 즉시 작성 후 진행 |

---

## 10. Phase 4 적용 계획

```text
1. session report INDEX 운영 시작
   - Phase 3B 완료 세션 1건 생성:
     session_reports/2026-05/2026-05-15_phase3b_complete.md

2. 기존 PHASE_PROGRESS.md 연결
   - 레거시 요약 → 위 session 파일에 summary로 포함
   - PHASE_PROGRESS.md 자체는 삭제하지 않음 (NC-1 REVIEW_LATER)

3. hook redirect 실 적용
   - SEV_2026-05_001 human approval 이후 별도 atomic PR
   - 적용 전까지 PHASE_PROGRESS.md와 session_reports/ 병렬 유지

4. codex_reports/ 연결
   - P4 첫 Codex task 완료 후 TASK_XXXX 결과 → session report 반영

5. mcp_calls 필드 운영
   - Phase 4에서 arXiv MCP 활성화 후 query_id 기록 시작
```
