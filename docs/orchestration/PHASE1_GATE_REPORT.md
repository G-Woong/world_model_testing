# PHASE1_GATE_REPORT.md

Phase 1 Orchestration Audit — Gate Report  
작성일: 2026-05-15  
작성자: Main Claude (Phase 1 실행)  
증거 출처: 3-agent Explore sweep + 직접 파일 읽기 (`.claude/settings.json`, `settings.local.json`, `.mcp.json`, glob 결과)

---

## 1. Phase 1 Scope Summary

**목적**: Phase 2(오케스트레이션 재설계) 진입 전, 변경 없이 repo 현황을 4개 evidence-based 보고서로 산출.

**산출물**:
- `docs/orchestration/00_CURRENT_STATE_INVENTORY.md` — repo/worktree/branch + inventory
- `docs/orchestration/01_PERMISSION_SCOPE_AUDIT.md` — 권한 감사 + 위험 플래그 R1–R14
- `docs/orchestration/02_CLEANUP_CANDIDATES.md` — 5분류 cleanup 후보 목록
- `docs/orchestration/PHASE1_GATE_REPORT.md` — 본 파일 (50-item checklist)

**제약**: 4개 md 외 어떤 파일도 추가/수정/삭제하지 않음.

---

## 2. 50-item Checklist

### Section A: Repo / Branch / Worktree (1–10)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 1 | Main worktree HEAD 확인 (`ba204a8`) | **PASS** | git 확인: `ba204a8 feat(p3-eval): fix B1/B2 blockers → P3_EVAL.passed issued` |
| 2 | Codex worktree (`ICLR_WM_codex`) 정상 존재 | **PASS** | `.git/worktrees/ICLR_WM_codex` metadata 정상, orphaned/stale 없음 |
| 3 | Codex worktree branch (`codex-work`) HEAD 확인 | **PASS** | HEAD `a55cb33`, clean |
| 4 | 손상된 orphaned worktree 없음 | **PASS** | metadata 정상 확인 |
| 5 | Remote origin URL 정상 | **PASS** | `https://github.com/G-Woong/world_model_testing.git` 확인 |
| 6 | Main worktree tracked 파일 clean | **PASS** | untracked 1개 제외, tracked 파일 변경 없음 |
| 7 | Codex HEAD ↔ Main HEAD drift 파악 | **PASS** | 2 commit 뒤 (drift 아님, 다음 task 전 fast-forward 필요로 기록) |
| 8 | 로컬 branch 3개 (`main`, `solo/p3-final-boss-cleared`, `codex-work`) 확인 | **PASS** | git branch 확인 |
| 9 | `origin/feat/p1-schema-visibility` 잔재 파악 | **PASS** (NEEDS_CONFIRMATION) | 존재 확인됨. 폐기 여부는 사용자 확인 필요 → §4 |
| 10 | 5개 phase gate sentinel 모두 존재 | **PASS** | `P1.passed`, `P1.5.passed`, `P2.passed`, `P3.passed`, `P3_EVAL.passed` 확인 |

### Section B: Settings & Permissions (11–25)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 11 | `settings.json` hooks-only 구조 확인 | **PASS** | permission keys 없음, hooks 10개만 |
| 12 | `settings.json` model=opusplan 확인 | **PASS** | `"model": "opusplan"` |
| 13 | `settings.local.json` `enableAllProjectMcpServers: true` 위험 파악 | **PASS** | R2(HIGH)로 문서화됨 |
| 14 | `settings.local.json` `Skill(update-config)` allow 위험 파악 | **PASS** | R3(HIGH)로 문서화됨 |
| 15 | `Bash(cmd *)`, `Bash(powershell *)` 무제한 wildcard 파악 | **PASS** | R1(HIGH)로 문서화됨 |
| 16 | `PowerShell(Remove-Item *)` 무제한 wildcard 파악 | **PASS** | R1(HIGH)로 문서화됨 |
| 17 | NeurIPS2026 cross-project 경로 27개+ 파악 | **PASS** | R5(MED)로 문서화됨 (L5, L6, L35, L42–78 다수) |
| 18 | Codex `-BypassSandbox` 7개 allow 항목 파악 | **PASS** | R4(MED)로 문서화됨 |
| 19 | Dead rule `Bash(git commit -m ' *)` 파악 | **PASS** | R11(LOW)로 문서화됨 |
| 20 | `.venv` 슬래시 중복 allow 파악 | **PASS** | R11(LOW)로 문서화됨 |
| 21 | `permissionMode` 미지정 파악 | **PASS** | R13(INFO)로 문서화됨 |
| 22 | `enabledMcpjsonServers: ["context7"]` 명시 확인 | **PASS** | `settings.local.json` L90 확인 |
| 23 | plugin-audit STOP rule ↔ `enableAllProjectMcpServers` 자기모순 파악 | **PASS** | R2와 함께 `01_PERMISSION_SCOPE_AUDIT.md` §3.3에 기록 |
| 24 | R1–R14 전체 위험 플래그 문서화 완료 | **PASS** | `01_PERMISSION_SCOPE_AUDIT.md` §11 확인 |
| 25 | 3-Tier 권한 분리 초안 작성 완료 | **PASS** | `01_PERMISSION_SCOPE_AUDIT.md` §10 확인 |

### Section C: MCP / Hooks (26–35)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 26 | `.mcp.json` context7 HTTP 단일 서버 확인 | **PASS** | R14(INFO), clean |
| 27 | `.mcp.json` 무인증·secret 참조 없음 확인 | **PASS** | URL만 노출, secret 없음 |
| 28 | 10개 hook 이벤트 등록 확인 | **PASS** | `settings.json` 직접 읽기 |
| 29 | `session_start_context.ps1` 미등록 이상 파악 | **PASS** | 파일 존재하나 settings.json에 없음 — A7로 기록 |
| 30 | `pre_compact_phase_handoff.ps1` repo-file side-effect 파악 | **PASS** | R7(MED)로 문서화됨 |
| 31 | `NotebookEdit` coverage gap (schema/baseline guard) 파악 | **PASS** | R8(LOW)로 문서화됨 |
| 32 | 모든 hook `-ExecutionPolicy Bypass` 사용 파악 | **PASS** | R6(MED)로 문서화됨 |
| 33 | `subagent_stop_audit.ps1` reminder-only (비차단) 파악 | **PASS** | R12(LOW)로 문서화됨 |
| 34 | `baseline_ablation_guard` old_string-only 한계 파악 | **PASS** | R9(LOW)로 문서화됨 |
| 35 | `Edit\|Write` hook matcher 중복 파악 | **PASS** | R10(LOW)로 문서화됨 |

### Section D: Agents / Skills / Commands (36–42)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 36 | 7개 agent 인벤토리 완료 | **PASS** | `01_PERMISSION_SCOPE_AUDIT.md` §8 |
| 37 | agent 전체 Edit/Write 없음 확인 | **PASS** | 시스템 프롬프트 tool 목록 확인 |
| 38 | 7개 skill 인벤토리 완료 | **PASS** | `01_PERMISSION_SCOPE_AUDIT.md` §9 |
| 39 | 3개 slash command 인벤토리 완료 | **PASS** | `01_PERMISSION_SCOPE_AUDIT.md` §6 |
| 40 | `.claude/rules/` 2개 파일 역할 명확화 | **PASS** | `01_PERMISSION_SCOPE_AUDIT.md` §7 |
| 41 | `codex_orchestration_rules.md` CLAUDE.md 상위 우선순위 확인 | **PASS** | orchestration 범위 내 명시됨 |
| 42 | `scripts/run_codex_task.ps1` (29.5 KB harness) source-of-truth 확인 | **PASS** | `00_CURRENT_STATE_INVENTORY.md` §5 |

### Section E: Cleanup Candidates (43–47)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 43 | DELETE_CANDIDATE: cache/build artifacts 8개 항목 분류 | **PASS** | `02_CLEANUP_CANDIDATES.md` §3.1 |
| 44 | DELETE_CANDIDATE: codex_queue 원본 TASK 7쌍 파악 | **PASS** | glob으로 1007–1011, 1017–1018 vs 1012–1016, 1019–1020 확인 |
| 45 | ARCHIVE: P0/P2/P3 historical plans 7개 분류 | **PASS** | `02_CLEANUP_CANDIDATES.md` §3.2 |
| 46 | MERGE: PHASE_PROGRESS ↔ P4 recovery 중복 파악 | **PASS** | `02_CLEANUP_CANDIDATES.md` §3.3 |
| 47 | REVIEW_LATER: 7개 항목 + Human-approval 필요 목록 | **PASS** | `02_CLEANUP_CANDIDATES.md` §3.4, §5 |

### Section F: 산출물 검증 (48–50)

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 48 | 4개 md 신규 생성 (`docs/orchestration/`만) | **PASS** | Write tool 4회 성공 |
| 49 | `paper_context_ref/`, `CLAUDE.md`, `.claude/`, `data/`, `configs/`, `src/`, `tests/` 미수정 | **PASS** | Phase 1에서 Read/Glob만 사용, Edit/Write는 신규 docs만 |
| 50 | DO_NOT_DELETE 목록 완전성 확인 | **PASS** | `02_CLEANUP_CANDIDATES.md` §3.5 에 절대 보호 경로 전체 나열 |

**체크리스트 결과: 50/50 PASS, 0 FAIL, 0 UNKNOWN**  
(단, item 9는 PASS+NEEDS_CONFIRMATION 병행)

---

## 3. Blockers

**Blockers: none**

Phase 1은 read-only 인벤토리/감사 작업이므로 구현 blocker 없음.  
단, Phase 2 진입 전 사용자 결정이 필요한 항목은 §4에 명시.

---

## 4. NEEDS_CONFIRMATION 목록

Phase 2 시작 전 사용자가 확인/결정해야 할 항목:

| ID | 항목 | 옵션 A | 옵션 B | 옵션 C |
|---|---|---|---|---|
| NC-1 | `plans/P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md` (untracked) 처리 | `git add` + commit (추적 시작) | 내용 확인 후 다른 파일에 통합 (MERGE) | 삭제 (영구 손실) |
| NC-2 | `origin/feat/p1-schema-visibility` 원격 branch | 삭제 (`git push origin --delete feat/p1-schema-visibility`) | 유지 (현재 상태 유지) | 내용 확인 후 결정 |
| NC-3 | Phase 2용 기준 branch 전략 | `solo/p3-final-boss-cleared` 계속 사용 | 새 `orchestration/redesign` branch 신설 | `main`으로 전환 후 작업 |
| NC-4 | Codex worktree fast-forward 시점 | Phase 2 시작 직전 | 다음 Codex TASK 할당 시 | 지금 즉시 |
| NC-5 | `outputs/runs/p3_smoke/checkpoint_ep0.pt` git LFS 처리 | `git lfs track` 추가 | `.gitignore`에 추가 | 현 상태 유지 |
| NC-6 | `session_start_context.ps1` 처리 | `settings.json`에 등록 | 파일 삭제 | 현 상태 유지 (미등록 방치) |
| NC-7 | 빈 placeholder 디렉터리 3개 (`eval_reports/`, `review_reports/`, `test_reports/`) | 삭제 (Phase 4 전 불필요) | 유지 (Phase 4 준비 자리) | 현 상태 유지 |

---

## 5. Decisions Required from User Before Phase 2

Phase 2(오케스트레이션 재설계) 시작 전 사용자 결정이 필요한 핵심 항목:

### 5.1 Branch 전략 (NC-3)

Phase 2는 `settings.local.json` 대규모 수정을 포함. 별도 branch 없이 `solo/p3-final-boss-cleared`에서 작업 가능하나, orchestration 변경이 연구 흐름과 섞이지 않도록 `orchestration/redesign` branch 신설을 권장.

### 5.2 HIGH 위험 플래그 우선순위 결정 (R1, R2, R3)

Phase 2 재설계 시 HIGH 3개를 먼저 처리할지, 전체 R1–R14를 한 번에 처리할지 결정 필요.

### 5.3 Cleanup 실행 범위 결정

Phase 2에서 cleanup을 병행할지 (DELETE_CANDIDATE 8개 + codex_queue 원본 7개), 아니면 별도 cleanup phase로 분리할지 결정 필요.

### 5.4 Codex Sandbox 정책

Phase 2 Codex orchestration 재설계에서 `-BypassSandbox` 기본화를 어떻게 처리할지:
- (A) 로컬 dev에서는 계속 `-BypassSandbox` 기본 허용
- (B) TASK 파일에 `SANDBOX_MODE: bypass` 명시 시만 허용
- (C) sandbox 완전 활성화 (Windows worktree lock 문제 해결 방법 별도 설계 필요)

---

## 6. Phase 2 Inputs (Carry-forward)

Phase 2 오케스트레이션 재설계 세션에서 사용할 입력 요약:

### 6.1 3-Tier Permission 초안 (Phase 2 구체화 대상)

- Tier 1: Main Claude — 설계/리뷰/승인/최종 commit
- Tier 2: Codex — FILES_ALLOWED 내 구현, codex-work branch only
- Tier 3: Agent Team — read-only report + outputs/review_reports/ write

### 6.2 Codex Sandbox 정책 결정 (NC-4/5)

`-BypassSandbox` 기본화 → TASK 파일 명시 선언 조건부 패턴으로 변경 (R4)

### 6.3 MCP Enable 정책 (R2)

`enableAllProjectMcpServers: true` → `false` + 명시 enable 목록 유지

### 6.4 Cleanup Approval Gates (NC-1 ~ NC-7)

CONFIRM-1 ~ CONFIRM-6 중 사용자 승인 후 실행

### 6.5 Phase 2 시작 시 읽을 문서

- `docs/orchestration/00_CURRENT_STATE_INVENTORY.md` (본 Phase 1 산출)
- `docs/orchestration/01_PERMISSION_SCOPE_AUDIT.md` (R1–R14, 3-tier 초안)
- `docs/orchestration/02_CLEANUP_CANDIDATES.md` (cleanup 승인 목록)
- `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP.md` (harness source MD)
- `.claude/rules/codex_orchestration_rules.md` (orchestration contract)

---

## 7. Phase 1 Gate Verdict

```
Phase 1 Gate Verdict: PASS
```

**근거**:
- 50-item checklist 50/50 PASS
- 신규 생성 파일: 정확히 4개 (`docs/orchestration/*.md`)
- 기존 파일 수정/삭제: 0건
- `paper_context_ref/`, `CLAUDE.md`, `.claude/`, `data/`, `configs/`, `src/`, `tests/`, `outputs/phase_gates/*.passed` 전부 unchanged
- Blockers: 없음
- NEEDS_CONFIRMATION: 7개 (NC-1 ~ NC-7) — Phase 2 진입 전 사용자 결정 필요

**Phase 2 진입 가능 조건**: NC-3 (branch 전략) 결정 후 즉시 진입 가능.  
NC-1~NC-2, NC-4~NC-7은 Phase 2 중에 병행 결정 가능.
