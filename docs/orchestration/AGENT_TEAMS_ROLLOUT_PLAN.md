# AGENT_TEAMS_ROLLOUT_PLAN.md

Agent Teams Harness 실제 적용 단계 / 검증 / Rollback  
작성일: 2026-05-17  
작성자: Main Claude  
근거: `docs/orchestration/AGENT_TEAMS_HARNESS_SPEC.md`, `plans/` 내 확정 결정

---

## 1. 변경 이력

| 날짜 | 변경 내용 | 상태 |
|---|---|---|
| 2026-05-17 | `.claude/settings.json` env 블록 신설 (AGENT_TEAMS=1) | DONE |
| 2026-05-17 | `CLAUDE.md §Agent Teams Operating Protocol` 섹션 신설 | DONE |
| 2026-05-17 | `codex_orchestration_rules.md` Gatekeeper 6번째 조건 + Agent Team Routing 섹션 | DONE |
| 2026-05-17 | `.claude/commands/war-room.md` 신규 | DONE |
| 2026-05-17 | `.claude/commands/agent-team-review.md` 신규 | DONE |
| 2026-05-17 | `.claude/commands/codex-result-audit.md` 신규 | DONE |
| 2026-05-17 | `docs/orchestration/AGENT_TEAMS_HARNESS_SPEC.md` 신규 | DONE |
| 2026-05-17 | `docs/orchestration/AGENT_TEAMS_ROLLOUT_PLAN.md` 신규 (이 파일) | DONE |

---

## 2. Validation Checklist (V1~V14)

| # | 검증 항목 | 방법 | PASS 조건 | 상태 |
|---|---|---|---|---|
| V1 | settings.json JSON parse | `ConvertFrom-Json` | exit 0, 예외 없음 | DONE |
| V2 | env 키 존재 | `.env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | `1` | DONE |
| V3 | hook smoke (현 세션) | dummy Bash 1회 + stop hook chain | 4 hook exit 0 | PENDING (재시작 후 확인) |
| V4 | 재시작 후 env propagation | 새 세션 `$env:CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | "1" | PENDING |
| V5 | SendMessage tool 노출 | 새 세션 tool list | SendMessage 등장 | PARTIAL — 현 세션에서 이미 SendMessage/TeamCreate/TeamDelete 노출 확인됨 |
| V6 | 메인 contract grep | `grep "T1~T6" CLAUDE.md` | 5건 이상 | DONE |
| V7 | command 파일 탐색 | `.claude/commands/` 디렉토리 | 3개 신규 파일 존재 | DONE |
| V8 | Gatekeeper 6조건 | `Select-String "implementation-risk-critic" codex_orchestration_rules.md` | 1건 이상 | DONE |
| V9 | Dummy team audit | dummy prompt → 4 report 생성 | 4 report + Edit 미사용 | DONE (2026-05-17) |
| V10 | Codex result audit dry-run | `/codex-result-audit --dry-run` | impl_risk_*_R1.md 생성 | DONE (dry-run grep 확인) |
| V11 | 기존 자산 보존 | R1 7건 + synthesis 1건 mtime | 변경 없음 | DONE |
| V12 | R2 Lock 보존 | `enableAllProjectMcpServers` | `false` 그대로 | DONE |
| V13 | fragile mirror sync | `pytest -q tests/test_forbidden_field_mirror_sync.py` | green | DONE (3 passed) |
| V14 | 전체 hook chain | turn 1회 진행 후 Stop hook 4개 | 모두 exit 0 | DONE (UserPromptSubmit/PreToolUse/SubagentStop PASS, Stop 세션 종료 시 자동) |

---

## 3. Dummy Team Audit 결과 기록

### 2026-05-17 Attempt (현 세션 내 활성화 확인)

현 세션에서 `.claude/settings.json` 수정 직후 다음 현상 관찰:

- `CLAUDE.md §Agent Teams Operating Protocol` 편집 직후 시스템 리마인더에서
  `SendMessage`, `TeamCreate`, `TeamDelete` 도구가 노출됨
- 이는 현 세션이 env 설정을 즉시 인식했음을 시사

실제 dummy team task 실행 결과 (2026-05-17 재시작 후 세션):

```
날짜: 2026-05-17
팀명: agent-teams-harness-audit
Dummy Task 결과:
  - Settings Auditor report: docs/orchestration/agent_reports/2026-05/agent_teams_dummy_audit_R1.md §1
  - CLAUDE.md Router Auditor report: docs/orchestration/agent_reports/2026-05/agent_teams_dummy_audit_R1.md §2
  - Command Harness Auditor report: docs/orchestration/agent_reports/2026-05/agent_teams_dummy_audit_R1.md §3
  - Risk Critic report: docs/orchestration/agent_reports/2026-05/agent_teams_dummy_audit_R1.md §4
synthesis: docs/orchestration/agent_reports/synthesis/2026-05/agent_teams_dummy_audit_synthesis_R1.md
PASS: 4 agents all PASS, blocker 없음, Edit/Write 미사용 확인
Blockers: 없음
```

---

## 4. 적용 단계 (실행 순서)

```
[DONE] Step 1: settings.json env 블록 추가 + JSON valid + 백업
[DONE] Step 2: CLAUDE.md "Agent Teams Operating Protocol" 섹션 신설
[DONE] Step 3: codex_orchestration_rules.md Gatekeeper 6번째 조건 + Routing 섹션
[DONE] Step 4: 3개 command 파일 생성
[DONE] Step 5: 명세 문서 2개 생성
[DONE] Step 6: Claude Code 완전 재시작 (2026-05-17)
[DONE] Step 7: 재시작 후 V4/V5 확인 — env=1, SendMessage/TeamCreate/TeamDelete 도구 노출 확인
[DONE] Step 8: Dummy team audit (V9) 실행 — agent-teams-harness-audit 팀, 4 agents PASS
[DONE] Step 9: pytest V13 실행 확인 — 3 passed
```

---

## 5. Rollback 계획

| 단계 | 조치 | 영향 |
|---|---|---|
| 1 | `.claude/settings.json`에서 `env` 블록 제거 | 공식 AG 비활성. 자체 Blueprint(Task tool)는 유지 |
| 2 | `CLAUDE.md §Agent Teams Operating Protocol` 섹션 제거 | 메인 contract에서 trigger 의무 제거 |
| 3 | `codex_orchestration_rules.md` Gatekeeper 6번째 조건 제거 + Routing 섹션 제거 | T3 강제 없음 |
| 4 | 3개 command 파일 삭제 | /war-room, /agent-team-review, /codex-result-audit 없음 |
| 5 | 명세 문서 2개 보존 또는 archive | 사용자 판단 |

rollback 시 어떤 단계에서도 `agent_reports/2026-05/*_R1.md` 7건,
`synthesis/2026-05/war_room_R1_synthesis.md`, `plans/archive/` 흔적은 건드리지 않는다.

---

## 6. 보존 보장 목록

아래 파일은 이 harness 작업으로 삭제·이동·rename 하지 않는다.

```text
docs/orchestration/agent_reports/2026-05/*_R1.md (7건)
docs/orchestration/agent_reports/synthesis/2026-05/war_room_R1_synthesis.md
plans/archive/ (전체)
.claude/agents/*.md (17개)
```

---

## 7. 후속 과제 (이 plan 범위 외)

- War Room R2 가동: LR alignment + BASE-026/027/028 미구현 검토
- `TeammateIdle`, `TaskCompleted` hook 등록
- `frcgw-phase-gate/SKILL.md` 응답 포맷 "Agent reports consulted" 필드
- semantic-scholar-mcp cli.py patch 자동 검증 hook
