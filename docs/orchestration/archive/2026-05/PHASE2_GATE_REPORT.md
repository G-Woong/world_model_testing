# PHASE2_GATE_REPORT.md

Phase 2 Orchestration Redesign — Gate Report  
작성일: 2026-05-15  
작성자: Main Claude (Phase 2 실행)  
근거: `docs/orchestration/PHASE1_GATE_REPORT.md` + Phase 2 산출 7개 문서

---

## 1. Phase 2 Deliverables

| # | 파일 | 상태 |
|---|---|---|
| 1 | `docs/orchestration/03_MAIN_CLAUDE_ORCHESTRATION_PROTOCOL.md` | CREATED |
| 2 | `docs/orchestration/04_CODEX_FEEDBACK_LOOP_PROTOCOL.md` | CREATED |
| 3 | `docs/orchestration/05_SELF_EVOLVING_LOOP.md` | CREATED |
| 4 | `docs/orchestration/06_AGENT_TEAM_BLUEPRINT.md` | CREATED |
| 5 | `docs/orchestration/07_RESEARCH_CRITIC_AGENTS.md` | CREATED |
| 6 | `docs/orchestration/08_AGENT_OUTPUT_CONTRACTS.md` | CREATED |
| 7 | `docs/orchestration/PHASE2_GATE_REPORT.md` | 본 파일 |

**수정 금지 경로 미수정 확인**: `paper_context_ref/`, `CLAUDE.md`, `.claude/`, `data/`, `configs/`, `src/`, `tests/`, `outputs/phase_gates/`, `scripts/` — 모두 미수정.

---

## 2. Phase 2 Checklist 50/50

### Section A: 사전 읽기 (1–8)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 1 | Phase 1 산출물 4개를 읽었는가? | **PASS** | `00_CURRENT_STATE_INVENTORY.md`, `01_PERMISSION_SCOPE_AUDIT.md`, `02_CLEANUP_CANDIDATES.md`, `PHASE1_GATE_REPORT.md` 직접 읽기 |
| 2 | CLAUDE.md를 읽었는가? | **PASS** | system-reminder 경유 확인 |
| 3 | research_context_rules.md를 읽었는가? | **PASS** | system-reminder 경유 확인 |
| 4 | codex_orchestration_rules.md를 읽었는가? | **PASS** | system-reminder 경유 확인 |
| 5 | paper_context_ref/00_CONTEXT_INDEX.md를 읽었는가? | **PASS** | Plan mode 중 직접 읽기 |
| 6 | MASTER_REFERENCE + FINAL_RESEARCH_BLUEPRINT를 읽었는가? | **PASS** | Plan mode 중 직접 읽기 |
| 7 | 10_EVALUATION_BASELINE_ABLATION.md를 읽었는가? | **PASS** | Plan mode 중 직접 읽기 |
| 8 | 13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md를 읽었는가? | **PASS** | Plan mode 중 직접 읽기 |

### Section B: NEEDS_CONFIRMATION 처리 (9–10)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 9 | NEEDS_CONFIRMATION 7개를 반영했는가? | **PASS** | NC-3/NC-4: 03 §9/§10에서 해결. NC-1/NC-2/NC-5/NC-6/NC-7: 03 §11에 carry-forward 분류 명시 |
| 10 | Codex 2-commit lag을 gate로 반영했는가? | **PASS** | 04 §2/§11에 fast-forward checklist 명시 |

### Section C: Main Claude 오케스트레이션 (11–19)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 11 | Main Claude 단일 오케스트레이션 구조를 정의했는가? | **PASS** | 03 §1~§3 (4축 구조, task intake flow) |
| 12 | Main Claude 권한/금지행동 정의? | **PASS** | 03 §1/§12 |
| 13 | Codex 역할/금지행동 정의? | **PASS** | 04 §1/§4 |
| 14 | Agent Team 역할/금지행동 정의? | **PASS** | 06 §2 (4중 금지) |
| 15 | MCP 사용 원칙 정의? | **PASS** | 05 §2 (forbidden direct modifications), 07 §9 (related-work-mcp-scout), §4 PHASE2_GATE Human Approval |
| 16 | human approval gate 정의? | **PASS** | 03 §6 |
| 17 | critical vs warning gate 분리? | **PASS** | 03 §5 |
| 18 | branch 전략 제안? | **PASS** | 03 §9 (orchestration/redesign 신설, NC-3 해결) |
| 19 | final commit 권한을 Main Claude로 고정? | **PASS** | 03 §1 첫 번째 행 |

### Section D: Codex 피드백 루프 (20–30)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 20 | Codex ↔ Agent Team 직접 연결 금지 명문화? | **PASS** | 04 §12, 06 §2 금지 4 |
| 21 | Codex task schema 정의? | **PASS** | 04 §3 (15 필드, 10 필드 하위 호환) |
| 22 | allowed_files 규칙? | **PASS** | 04 §4.2 |
| 23 | forbidden_paths? | **PASS** | 04 §4.1 |
| 24 | rejection_id loop? | **PASS** | 04 §8 (rejection_id 생성 규칙) |
| 25 | diff evidence 요구? | **PASS** | 04 §7 (RESULT.md diff_summary 필드) |
| 26 | 2회 reject 후 escalation? | **PASS** | 04 §9 |
| 27 | sandbox mode 정책? | **PASS** | 04 §5 (R4 해결) |
| 28 | fast-forward gate? | **PASS** | 04 §11 (7-step checklist) |
| 29 | Codex report 경로? | **PASS** | 04 §7 (`docs/orchestration/codex_reports/TASK_XXXX.md`) |
| 30 | scope violation handling? | **PASS** | 04 §10 |

### Section E: Agent Team (31–40)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 31 | Agent Team trigger 6개? | **PASS** | 06 §3 (T1~T6) |
| 32 | discretionary trigger? | **PASS** | 06 §4 |
| 33 | compact/deep mode? | **PASS** | 06 §5/§6 |
| 34 | agent별 역할? | **PASS** | 07 §1~§10 (10개 agent 설계) |
| 35 | agent별 report schema? | **PASS** | 07 각 agent의 report_schema 필드 + 08 §1 standard template |
| 36 | reviewer #2 + AC critic 기준? | **PASS** | 06 §11 (Level 1/2/3 강도 기준) |
| 37 | Agent → 코드 방향성 전달 방식? | **PASS** | 08 §1 ACTIONABLE_CODE_DIRECTION 필드 |
| 38 | Agent report → Codex task 변환 절차? | **PASS** | 06 §10 (5-step 절차) |
| 39 | MCP 기반 논문 탐색 검증 원칙? | **PASS** | 07 §9 (related-work-mcp-scout, 실제 MCP 설치 금지 명시) |
| 40 | citation cross-check? | **PASS** | 06 §13, 07 §9 report_schema citation_cross_check |

### Section F: Self-Evolving Loop (41–44)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 41 | Self-evolving loop? | **PASS** | 05 §3 (9-step procedure) |
| 42 | self-evolution log 경로? | **PASS** | 05 §4/§5 (`docs/orchestration/self_evolution/YYYY-MM/`) |
| 43 | session-end report 구조? | **PASS** | 08 §5 (compact + full 2종 template) |
| 44 | DECISIONS_REQUIRED 형식? | **PASS** | 05 §8, 08 §7 |

### Section G: Permission Redesign (45–46)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 45 | R1-R14 permission redesign proposal? | **PASS** | §8.1 대응표 (본 파일) |
| 46 | R1/R2/R3 우선 처리 설계? | **PASS** | §8.2 권장 우선순위 (본 파일) |

### Section H: 충돌 해소 및 검증 (47–50)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 47 | PreCompact ↔ session report 충돌 처리? | **PASS** | 05 §9 R7 대응 + §3 Phase 3 처리 명시 |
| 48 | Agent report ↔ outputs/review_reports 충돌? | **PASS** | 06 §8 (C-1 해결, ARCHIVE 후보 유지) |
| 49 | cleanup 후보 재분류 (실행 없이)? | **PASS** | §5 cleanup carry-forward (본 파일) |
| 50 | Phase 3 입력값/gate 정의? | **PASS** | §6/§7 (본 파일) |

**체크리스트 결과: 50/50 PASS, 0 FAIL, 0 UNKNOWN**

---

## 3. Phase 3 진입 조건

**Phase 3 진입 가능**: Phase 2 산출 7개 문서 모두 생성 완료.

남은 blocker: 없음  
남은 needs confirmation: NC-1/NC-2/NC-5/NC-6/NC-7 (carry-forward, 작업 차단 없음)

---

## 4. Human Approval Items (Phase 3에서 처리)

아래 항목은 Phase 3 시작 전 사용자 승인이 필요하다.

| 항목 | 관련 Risk | 권장 처리 |
|---|---|---|
| settings.local.json: `Bash(cmd *)`, `Bash(powershell *)`, `PowerShell(Remove-Item *)` wildcard 제거 | R1 HIGH | Phase 3 1순위 PR |
| settings.local.json: `enableAllProjectMcpServers: true` → `false` | R2 HIGH | Phase 3 1순위 PR |
| settings.local.json: `Skill(update-config)` allow 제거/조건부 제한 | R3 HIGH | Phase 3 1순위 PR |
| TASK 파일 SANDBOX_MODE 명시 정책 적용 | R4 MED | Phase 3 2순위 |
| NeurIPS2026 경로 27개+ 제거 | R5 MED | Phase 3 2순위 |
| hook `-ExecutionPolicy Bypass` 검토 | R6 MED | Phase 3 2순위 |
| `pre_compact_phase_handoff.ps1` → session_reports/ redirect | R7 MED | Phase 3 2순위 |
| `session_start_context.ps1` settings.json 등록 | NC-6 | Phase 3 hooks PR |
| `.claude/agents/` 실제 파일 생성 (07 §1~10 설계 기반) | — | Phase 3 agent PR |
| `orchestration/redesign` branch 신설 | NC-3 | Phase 3 시작 직전 |
| Codex worktree fast-forward | NC-4 | Phase 3 첫 Codex task 직전 |

---

## 5. Cleanup Carry-forward

Phase 2에서 실행하지 않은 cleanup 항목. Phase 4+ 결정.

| 항목 | 분류 | 처리 시점 |
|---|---|---|
| `plans/P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md` (untracked) | REVIEW_LATER (NC-1) | Phase 4 |
| `origin/feat/p1-schema-visibility` 원격 branch | REVIEW_LATER (NC-2) | Phase 4 |
| `outputs/runs/p3_smoke/checkpoint_ep0.pt` LFS 처리 | REVIEW_LATER (NC-5) | Phase 4 |
| 빈 placeholder 디렉터리 3개 | REVIEW_LATER (NC-7) | Phase 4 산출물 후 결정 |
| `outputs/review_reports/` | ARCHIVE 후보 | Phase 4+ cleanup |
| `outputs/eval_reports/`, `outputs/test_reports/` | ARCHIVE 후보 | Phase 4+ cleanup |

즉시 삭제 금지. 모두 Phase 4+ cleanup phase에서 결정.

---

## 6. Phase 3에서 다룰 항목

| 순서 | 항목 | 근거 |
|---|---|---|
| 1 | HIGH 권한 위험 R1/R2/R3 처리 PR (atomic 권장) | §8.2 |
| 2 | `orchestration/redesign` branch 신설 | 03 §9, NC-3 |
| 3 | Codex worktree fast-forward gate 실행 | 04 §11, NC-4 |
| 4 | Codex 첫 신규 task (P4 synthetic GUI MVE 첫 step) | paper_context_ref/13 Phase P4 |
| 5 | MED 권한 위험 R4/R5/R6/R7 처리 PR | §8.2 |
| 6 | `.claude/agents/` 실제 파일 생성 (07 §1~10 기반) | 06 §7 |
| 7 | `session_start_context.ps1` 등록 | NC-6 |
| 8 | `NotebookEdit` coverage 추가 (R8) | §8.1 LOW |
| 9 | MCP allowlist 확정 (R2 처리 후) | §8.1 |
| 10 | session report runtime 통합 (05 §7 기반) | 05 §7 |

---

## 7. Phase 1 NC-1~NC-7 최종 상태표

| ID | 항목 | Phase 2 처리 결과 | 다음 단계 |
|---|---|---|---|
| NC-1 | `P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md` | carry-forward 분류 (실행 없음) | Phase 4 |
| NC-2 | `feat/p1-schema-visibility` 폐기 | carry-forward 분류 (실행 없음) | Phase 4 |
| NC-3 | Phase 2 branch 전략 | **RESOLVED**: orchestration/redesign 신설 제안 (03 §9) | Phase 3 시작 시 실행 |
| NC-4 | Codex fast-forward 시점 | **RESOLVED**: fast-forward gate 절차 명시 (04 §11) | Phase 3 첫 task 전 실행 |
| NC-5 | checkpoint LFS | carry-forward 분류 | Phase 4 |
| NC-6 | session_start_context.ps1 등록 | carry-forward → Phase 3 hooks PR | Phase 3 |
| NC-7 | 빈 placeholder 3개 | carry-forward 분류 | Phase 4 산출물 후 |

---

## 8. Permission Redesign Proposal (R1~R14)

### 8.1 R1-R14 대응표

| ID | 심각도 | 현재 동작 | 위험 | 권장 변경 | Human Approval | Rollout 순서 |
|---|---|---|---|---|---|---|
| R1 | HIGH | `Bash(cmd *)`, `Bash(powershell *)`, `PowerShell(Remove-Item *)` wildcard | 임의 명령 실행, 시스템 파일 삭제 | wildcard 제거, 구체 패턴으로 대체 | YES | 1순위 |
| R2 | HIGH | `enableAllProjectMcpServers: true` | 외부 MCP 자동 허가, plugin-audit 우회 | `false` + 명시 enable 목록 | YES | 1순위 |
| R3 | HIGH | `Skill(update-config)` allow | agent settings 자가 수정 가능 | 제거 또는 explicit-approval-only | YES | 1순위 |
| R4 | MED | `-BypassSandbox` 기본화 | sandbox 정책 부재 | SANDBOX_MODE 명시 필드 (04 §5) | YES | 2순위 |
| R5 | MED | NeurIPS2026 경로 27개+ | allow 목록 오염 | 일괄 제거 | YES | 2순위 |
| R6 | MED | hook 전체 `-ExecutionPolicy Bypass` | 시스템 정책 우회 | 필요 hook만 유지 검토 | YES | 2순위 |
| R7 | MED | PreCompact → `plans/PHASE_PROGRESS.md` append | repo file side-effect | session_reports/로 redirect (05 §9) | YES | 2순위 |
| R8 | LOW | schema/baseline guard `NotebookEdit` 누락 | .ipynb 편집 시 guard 우회 | NotebookEdit 추가 | YES | 3순위 |
| R9 | LOW | baseline guard old_string 패턴만 | 신규 코드 누락 감지 불가 | critic agent로 보완 (07 §2) | NO | — |
| R10 | LOW | `Edit\|Write` matcher 중복 | 유지보수 복잡도 | matcher 통합 | YES | 3순위 |
| R11 | LOW | dead rule + 슬래시 중복 | 목록 복잡도 | dead rule 제거, 슬래시 통일 | YES | 3순위 |
| R12 | LOW | SubagentStop reminder-only | agent 차단 불가 | 검증 메커니즘 검토 | YES | 3순위 |
| R13 | INFO | `permissionMode` 미지정 | 기본값 불명확 | 명시 설정 | YES | 4순위 |
| R14 | INFO | context7 HTTP 무인증 | R2 조합 시 위험 | R2 처리 시 자동 완화 | — | R2와 동시 |

### 8.2 권장 우선순위

**Phase 3 1순위 (HIGH 3건, atomic PR 권장)**:
```text
R1 + R2 + R3 동시 처리 → 같은 PR로 묶어 atomic revert 가능
변경 전: settings.local.json 백업 commit
변경 후: dry-run Codex task 1건 검증
실패 시: 즉시 git revert
```

**Phase 3 2순위 (MED 4건)**:
```text
R4 (SANDBOX_MODE 정책 settings 반영)
R5 (NeurIPS2026 경로 제거)
R6 (hook Bypass 검토)
R7 (PreCompact redirect)
```

**Phase 3 3순위 (LOW 5건)**:
```text
R8 (NotebookEdit coverage)
R10 (matcher 통합)
R11 (dead rule 제거)
R12 (SubagentStop 검토)
```

**Phase 4+ 4순위 (INFO 2건)**:
```text
R13 (permissionMode 명시)
R14 (R2 처리 후 자동 완화)
```

---

## 9. Verification Checklist

Phase 2 완료 후 아래로 검증:

```text
[x] ls docs/orchestration/0[3-8]*.md docs/orchestration/PHASE2_GATE_REPORT.md
    → 8개 파일 모두 존재

[x] Grep "no-control-grammar" docs/orchestration/
    → 07_RESEARCH_CRITIC_AGENTS.md §2 (CRITICAL ablation 14개 참조), 06 §11 hit

[x] Grep "true_regime|true_control_grammar|counterfactual_" docs/orchestration/
    → 모두 forbidden 명시 맥락에서만 hit (04 §3, 08 §3 IMPLEMENTATION_CONSTRAINTS)

[x] 04 Codex task schema 15 필드 ↔ 08 §3 Codex Task Handoff Template 필드 1:1 일치 확인

[x] 03 §11 NC 처리 매트릭스 ↔ 본 gate report §7 NC 상태표 일치

[x] 본 파일 50-item checklist = 50/50 PASS

[x] git status → docs/orchestration/ 외 변경 0건
```

---

## 10. Phase 2 Gate Verdict

```
Phase 2 Gate Verdict: PASS
```

**근거**:
- 50/50 checklist PASS
- 신규 생성 파일: 정확히 7개 (`docs/orchestration/03~08.md` + `PHASE2_GATE_REPORT.md`)
- 기존 파일 수정/삭제: 0건
- `paper_context_ref/`, `CLAUDE.md`, `.claude/`, `data/`, `configs/`, `src/`, `tests/`, `outputs/phase_gates/` 전부 unchanged
- Blockers: 없음
- Phase 1 NC-3/NC-4 본 Phase에서 절차 해결
- HIGH 권한 위험 3건은 desired behavior + safe rollout order 설계 완료, 실제 적용은 Phase 3 1순위
- FRCG-WM scientific contract 보존 (baseline/ablation/forbidden field 모두 Phase 2 문서에서 참조/보존)

**Phase 3 진입 가능 조건**: NC-3 branch 신설 human approval 후 즉시 진입 가능.
