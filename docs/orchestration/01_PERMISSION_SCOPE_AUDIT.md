# 01_PERMISSION_SCOPE_AUDIT.md

Phase 1 Orchestration Audit — 권한 범위 감사  
작성일: 2026-05-15  
작성자: Main Claude (read-only sweep, Phase 1)  
증거 출처: `.claude/settings.json`, `.claude/settings.local.json`, `.mcp.json` 직접 읽기 + evidence block C

---

## 1. Audit Scope

감사 대상:
- `.claude/settings.json` (project-shared)
- `.claude/settings.local.json` (user-local)
- `.mcp.json`
- `.claude/hooks/*.ps1` (11개 파일, 10개 등록)
- `.claude/commands/` (3개 slash command)
- `.claude/rules/` (2개 md)
- `.claude/agents/` (7개 md)
- `.claude/skills/` (7개 skill)

감사 원칙: 읽기만 함. 어떤 파일도 수정하지 않음. 발견 사항은 R1–R14로 번호 부여.

---

## 2. settings.json (project-shared)

**파일 경로**: `.claude/settings.json`  
**역할**: 전체 프로젝트 공유 설정. hooks만 정의, permission allow/deny 없음.

### 2.1 설정 키 요약

| 키 | 값 | 비고 |
|---|---|---|
| `showClearContextOnPlanAccept` | `true` | plan accept 시 context clear 제안 표시 |
| `model` | `"opusplan"` | plan mode용 모델 지정 |
| `hooks` | 10개 이벤트 | 아래 §5 참조 |
| `permissions` | **없음** | permission allow/deny 미지정 → settings.local.json에 모두 위임됨 |
| `permissionMode` | **없음** | 미지정 (R13: 기본값이 무엇인지 명시적 확인 필요) |

### 2.2 판정

`settings.json`은 hooks-only 파일로 직접 권한 노출 없음. permissions 키가 없으므로 모든 allow 규칙은 user-local `settings.local.json`에 있음.

---

## 3. settings.local.json (user-local)

**파일 경로**: `.claude/settings.local.json`  
**경고**: 이 파일은 git-tracked 여부 불명. user-local이므로 팀 공유 안 됨. **단일 실패점**.

### 3.1 Wildcard Allow 인벤토리 (전체 86개 항목)

주요 광범 wildcard (제한 없음):

| 패턴 | 위험도 | 비고 |
|---|---|---|
| `Bash(python *)` | HIGH | Python 임의 실행 |
| `Bash(cmd *)` | HIGH | Windows cmd.exe 임의 실행 (shell injection 위험) |
| `Bash(powershell *)` | HIGH | PowerShell 임의 실행 |
| `Bash(git *)` | MED | git 임의 명령 (force push 포함) |
| `Bash(codex *)` | MED | codex 임의 명령 |
| `Bash(codex exec *)` | MED | codex exec 임의 실행 |
| `PowerShell(Remove-Item *)` | HIGH | 임의 경로 삭제 |
| `PowerShell(New-Item *)` | MED | 임의 파일/디렉터리 생성 |
| `PowerShell(git *)` | MED | PowerShell에서 git 임의 명령 |
| `PowerShell(codex *)` | MED | PowerShell에서 codex 임의 명령 |
| `Bash(.venv/Scripts/python.exe *)` | MED | .venv Python 실행 |
| `Bash(.venv\\Scripts\\python.exe *)` | MED | 중복 (슬래시/역슬래시 양쪽) — R11 |

**R1 (HIGH)**: `Bash(cmd *)`, `Bash(powershell *)`, `PowerShell(Remove-Item *)` — root-shell 수준 임의 실행. agent가 오용 시 시스템 파일 삭제·임의 명령 실행 가능.

### 3.2 NeurIPS2026 Cross-Project 경로 Leak (R5)

현재 프로젝트(`ICLR_WM_claude-code`)와 무관한 경로가 allow 목록에 다수 존재:

```
L5:  Bash(Test-Path "C:\\Users\\computer\\Desktop\\NeurIPS2026\\...")
L6:  Bash(Test-Path "C:\\Users\\computer\\Desktop\\NeurIPS2026\\...")
L35: Bash(git -C C:\\Users\\computer\\Desktop\\NeurIPS2026_codex rev-parse HEAD)
L42: PowerShell(cd "C:\\Users\\computer\\Desktop\\NeurIPS2026_claude-code"; ...)
L44: PowerShell(cd "C:\\Users\\computer\\Desktop\\NeurIPS2026_claude-code"; ...)
L46–47: PowerShell(cd ... NeurIPS2026_claude-code; scripts/run_codex_task.ps1 ...)
L52–53: PowerShell(cd ... NeurIPS2026_claude-code; ...)
L58: Bash(Test-Path C:/Users/computer/Desktop/NeurIPS2026_claude-code/...)
L61–63: PowerShell(Set-Location "C:\\...\\NeurIPS2026_claude-code"; ...)
L65–78: PowerShell(Get-ChildItem/Set-Location ... NeurIPS2026_claude-code ...)
```

**R5 (MED)**: 이전 프로젝트 `NeurIPS2026_claude-code` 경로 27개+ 항목이 현 프로젝트 allow 목록에 박혀 있음. ICLR_WM 프로젝트 cwd와 무관하므로 실질적 실행 위험은 낮으나, allow 목록이 오염되어 감사 복잡도 증가. Phase 2에서 일괄 제거 필요.

### 3.3 enableAllProjectMcpServers (R2)

```json
"enableAllProjectMcpServers": true
```

**R2 (HIGH)**: 미래에 `.mcp.json`에 추가되는 모든 MCP 서버가 자동 활성화됨. 현재는 `context7` 1개만 존재하나, 신규 MCP 추가 시 즉시 활성화되는 자가-허가 상태. `frcgw-plugin-audit` STOP rule이 "외부 plugin을 수동 허가하라"고 강제하는데, `enableAllProjectMcpServers: true`는 이 rule과 **자기모순**.

### 3.4 Skill(update-config) Allow (R3)

```json
"Skill(update-config)"
```

**R3 (HIGH)**: agent가 `update-config` skill을 통해 `settings.json` / `settings.local.json`을 자가 수정 가능. audit trail 없이 권한 목록이 바뀔 수 있음. 자가-수정 루프를 허용하는 열린 통로. Phase 2에서 통제 방안 필요.

### 3.5 Codex -BypassSandbox 기본 (R4)

allow 목록에 7개 TASK 실행 항목이 `-BypassSandbox` 포함:

```
TASK_C1..C7 (L71–77): -BypassSandbox
TASK_1007..1011 (L79–83): -BypassSandbox
TASK_1017..1018 (L84–85): -BypassSandbox
```

**R4 (MED)**: 로컬 dev 환경에서 worktree index.lock 제약 우회를 위해 `-BypassSandbox`가 기본화됨. Production sandbox 정책 부재. Phase 2에서 sandbox 명시적 옵션화 필요.

### 3.6 Dead / Duplicate Rules (R10, R11)

| 패턴 | 문제 |
|---|---|
| `Bash(git commit -m ' *)` (L34) | 단일 따옴표 패턴 — HEREDOC/double-quote commit과 매치 안 됨. 실질적으로 dead rule. |
| `Bash(.venv/Scripts/python.exe *)` + `Bash(.venv\\Scripts\\python.exe *)` (L28,L29) | 슬래시/역슬래시 양쪽 중복 등록 |
| `PowerShell(...)` 동일 명령 중복 | NeurIPS2026 cd 기반 동일 harness 명령이 dispatch/verify/prepare-merge 3 mode로 각각 별도 등록 |

**R10 (LOW)**: `Edit|Write` matcher가 `schema_leakage_guard`와 `baseline_ablation_guard` 두 hook에 중복 선언됨 (settings.json L35–51). 동작은 정상이나 유지보수 복잡도 증가.  
**R11 (LOW)**: dead rule + 슬래시 중복이 allow 목록 복잡도를 불필요하게 키움.

---

## 4. .mcp.json (R14)

```json
{
  "mcpServers": {
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

**R14 (INFO)**: `context7` HTTP MCP 1개. 무인증, secret 참조 없음. URL만 노출. `.mcp.json` 자체는 clean.  
단, R2(`enableAllProjectMcpServers: true`)와 조합 시 미래 MCP 자동 허가 위험 존재.

---

## 5. .claude/hooks/ — 11개 파일, 10개 등록

### 5.1 Hook 등록 현황

| Event | Hook 파일 | 등록 여부 | 유형 |
|---|---|---|---|
| `UserPromptSubmit` | `user_prompt_phase_router.ps1` | ✅ 등록 | reminder/routing |
| `PreToolUse(Bash\|Edit\|Write\|NotebookEdit)` | `pre_tool_guard.ps1` | ✅ 등록 | guard |
| `PreToolUse(Bash)` | `phase_gate_guard.ps1` | ✅ 등록 | blocking gate |
| `PreToolUse(Edit\|Write)` | `schema_leakage_guard.ps1` | ✅ 등록 | blocking guard |
| `PreToolUse(Edit\|Write)` | `baseline_ablation_guard.ps1` | ✅ 등록 | blocking guard |
| `PostToolUse(Edit\|Write\|NotebookEdit)` | `post_edit_audit.ps1` | ✅ 등록 | audit |
| `PostToolUse(Edit\|Write\|NotebookEdit)` | `post_edit_targeted_tests.ps1` | ✅ 등록 | test trigger |
| `SubagentStop` | `subagent_stop_audit.ps1` | ✅ 등록 | reminder-only |
| `PreCompact` | `pre_compact_phase_handoff.ps1` | ✅ 등록 | **repo file write** |
| `Stop` | `stop_summary_guard.ps1` | ✅ 등록 | reminder |
| — | `session_start_context.ps1` | ❌ **미등록** | 파일만 존재 |

**10개 등록, 1개 미등록** (session_start_context.ps1).

### 5.2 Blocking vs Warning vs Reminder 분류

| 분류 | 해당 hook |
|---|---|
| **Blocking** (exit 1 시 tool 차단) | `phase_gate_guard.ps1`, `schema_leakage_guard.ps1`, `baseline_ablation_guard.ps1`, `pre_tool_guard.ps1` |
| **Audit / Test Trigger** | `post_edit_audit.ps1`, `post_edit_targeted_tests.ps1` |
| **Reminder / Routing** | `user_prompt_phase_router.ps1`, `stop_summary_guard.ps1`, `subagent_stop_audit.ps1` |
| **Side-effect** (repo file write) | `pre_compact_phase_handoff.ps1` |

모든 hook이 `-ExecutionPolicy Bypass` 옵션 사용 (**R6 MED**).

### 5.3 Side-effect Hook: pre_compact_phase_handoff (R7)

**R7 (MED)**: `pre_compact_phase_handoff.ps1`는 PreCompact 이벤트에서 `plans/PHASE_PROGRESS.md`에 append 작업 수행. PreCompact는 context window 압축 시 자동 호출되므로, AI 세션 내 자동으로 repo 파일이 수정됨. 이 수정은 commit되지 않으면 추적되지 않음.

### 5.4 Coverage Gap: NotebookEdit (R8)

**R8 (LOW)**: `schema_leakage_guard.ps1`과 `baseline_ablation_guard.ps1`의 matcher는 `Edit|Write`뿐. `NotebookEdit`는 제외됨. `.ipynb` 파일 편집 시 leakage/baseline guard를 우회 가능. 현재 `.ipynb` 파일 없어 즉각 위험은 낮으나, P4+ 이후 노트북 도입 시 갭 발생.

### 5.5 Baseline Guard 한계 (R9)

**R9 (LOW)**: `baseline_ablation_guard.ps1`은 old_string 패턴 매칭만 수행 (삭제 감지). 새 코드에 baseline 구현이 누락되는 경우는 감지 불가. semantic coverage는 사람이 직접 리뷰해야 함.

### 5.6 SubagentStop 비차단 (R12)

**R12 (LOW)**: `subagent_stop_audit.ps1`은 SubagentStop 이벤트에서 reminder만 출력. agent 산출물의 실제 차단/승인 불가. Main Claude가 결과를 receive하여 수동 판단해야 함.

---

## 6. .claude/commands/ — 3개 slash command

| 파일 | Command | 역할 |
|---|---|---|
| `read-paper-context.md` | `/read-paper-context` | paper_context_ref/ 라우팅 |
| `frcgw-phase-check.md` | `/frcgw-phase-check` | Phase gate 상태 확인 |
| `frcgw-plugin-audit.md` | `/frcgw-plugin-audit` | plugin 설치 전 보안 감사 |

위험 없음. read-only 명령 3개.

---

## 7. .claude/rules/ — 2개 규칙 파일

| 파일 | 역할 | 우선순위 |
|---|---|---|
| `research_context_rules.md` | Scientific/data contract 강제 | CLAUDE.md 동급 |
| `codex_orchestration_rules.md` | Codex = default 구현자. CLAUDE.md보다 orchestration 상 우선 | CLAUDE.md 상위 (orchestration 범위) |

**모순 없음**: codex_orchestration_rules.md가 CLAUDE.md의 "implementation" 역할을 "설계·리뷰·통합"으로 재정의하고 실 구현을 Codex에 위임한다고 명시.

---

## 8. .claude/agents/ — 7개 agent

| Agent | 도구 | 분류 |
|---|---|---|
| `frcgw-context-router` | Read, Glob, Grep | Pure read-only |
| `frcgw-data-leakage-auditor` | Read, Glob, Grep | Pure read-only |
| `frcgw-code-reviewer` | Read, Glob, Grep | Pure read-only |
| `frcgw-test-runner` | Bash, Read, Glob, Grep | Bash 보유 |
| `frcgw-experiment-evaluator` | Read, Glob, Grep, Bash | Bash 보유 |
| `frcgw-related-work-scout` | Read, Glob, Grep, WebFetch, WebSearch | Web 보유 |
| `frcgw-plugin-security-auditor` | Read, Glob, Grep, WebFetch, WebSearch, Bash | Bash + Web 보유 |

3개 pure read-only, 2개 Bash 보유, 2개 Web 보유 (1개는 Bash+Web 겸).  
모든 agent는 Edit/Write 없음 → 코드 수정 불가. 설계 의도에 적합.

---

## 9. .claude/skills/ — 7개 skill

| Skill | 트리거 조건 |
|---|---|
| `frcgw-code-review` | code review / PR 직전 |
| `frcgw-data-safety` | schema/data/collector 변경 시 |
| `frcgw-experiment-design` | eval config / ablation runner 수정 시 |
| `frcgw-paper-framing` | abstract/intro/related work 작성 시 |
| `frcgw-phase-gate` | phase 시작/종료 시 |
| `frcgw-plugin-audit` | plugin/MCP 설치 시도 시 |
| `frcgw-test-quality` | 코드 변경 후 / pytest 실행 시 |

`update-config` skill이 `settings.local.json` L4에 allow 등록되어 있음 (**R3 참조**).

---

## 10. 3-Tier Permission Separation Draft

Phase 2 재설계를 위한 초안. 현재 상태가 아닌 목표 상태.

### Tier 1: Main Claude (설계, 리뷰, 승인, 최종 commit)

허용:
- Read/Glob/Grep (all paths)
- Edit/Write (docs/, plans/, paper_context_ref/ 제외, .claude/ 제외)
- Bash(git add, git commit, git status, git diff, git log)
- Bash(python .venv/Scripts/python.exe -m pytest ...) — 지정 경로만
- Agent 호출 (read-only agents)
- Plan mode

금지:
- `Bash(cmd *)`, `Bash(powershell *)` 무제한 wildcard
- `PowerShell(Remove-Item *)` 무제한
- `Skill(update-config)` — 자가 수정 통로 차단 (explicit approval만)

### Tier 2: Codex (구현, 테스트 작성, codex-work commit)

허용:
- `FILES_ALLOWED`에 명시된 파일만 Edit/Write
- `.venv/Scripts/python.exe -m pytest` (지정 tests만)
- `git add`, `git commit` (codex-work 브랜치 only)
- `-BypassSandbox` — TASK 파일에 명시적으로 선언된 경우만

금지:
- `.claude/`, `CLAUDE.md`, `.mcp.json`, `paper_context_ref/`, `data/`, `outputs/`, `secrets/`, `.env*`, `scripts/run_codex_task.ps1`
- codex-work 외 브랜치 commit
- settings 파일 수정

### Tier 3: Agent Team (read-only report, 산출물 디렉터리 write만)

허용:
- Read/Glob/Grep (all paths)
- WebFetch/WebSearch (frcgw-related-work-scout, frcgw-plugin-security-auditor)
- Bash(pytest ...) — frcgw-test-runner, frcgw-experiment-evaluator 한정
- `outputs/review_reports/` Write (agent report 저장, 미래)

금지:
- Edit/Write (src/, tests/, configs/ 등)
- git commit / push

---

## 11. Risk Flags R1–R14

| ID | 심각도 | 위치 | 내용 |
|---|---|---|---|
| **R1** | HIGH | `settings.local.json` | `Bash(cmd *)`, `Bash(powershell *)`, `PowerShell(Remove-Item *)` — root-shell 수준 wildcard |
| **R2** | HIGH | `settings.local.json` | `enableAllProjectMcpServers: true` — 미래 MCP 자동 허가, plugin-audit STOP rule과 자기모순 |
| **R3** | HIGH | `settings.local.json` | `Skill(update-config)` allow — agent settings 자가 수정 통로, audit trail 없음 |
| **R4** | MED | `settings.local.json` (TASK 7개) | `-BypassSandbox` 기본화 — Production sandbox 정책 부재 |
| **R5** | MED | `settings.local.json` (27개+ 항목) | NeurIPS2026 cross-project 경로 leak — 현 프로젝트와 무관한 경로가 allow 목록 오염 |
| **R6** | MED | `settings.json` (hooks 10개) | 모든 hook `-ExecutionPolicy Bypass` — PowerShell 실행 정책 우회 |
| **R7** | MED | `pre_compact_phase_handoff.ps1` | PreCompact에서 `plans/PHASE_PROGRESS.md` 자동 append — repo 파일 side-effect |
| **R8** | LOW | `settings.json` (hook matcher) | `schema_leakage_guard`, `baseline_ablation_guard` matcher에 `NotebookEdit` 누락 |
| **R9** | LOW | `baseline_ablation_guard.ps1` | old_string 패턴 감지만 — semantic baseline 누락 감지 불가 |
| **R10** | LOW | `settings.json` | `Edit\|Write` matcher 중복 (schema + baseline guard 양쪽에 동일 matcher) |
| **R11** | LOW | `settings.local.json` | Dead rule `Bash(git commit -m ' *)` + 슬래시 중복 (.venv 경로 양쪽) |
| **R12** | LOW | `subagent_stop_audit.ps1` | SubagentStop은 reminder만 — agent 결과 차단 불가 |
| **R13** | INFO | `settings.json` | `permissionMode` 미지정 — 기본 동작이 무엇인지 명시적 확인 필요 |
| **R14** | INFO | `.mcp.json` | context7 HTTP 1개, 무인증 — 현재는 clean (R2와 조합 주의) |

---

## 12. Phase 2 Redesign Targets (우선순위 순)

1. **[HIGH-1]** `Bash(cmd *)`, `Bash(powershell *)`, `PowerShell(Remove-Item *)` wildcard 제거 → 최소 구체 패턴으로 교체 (R1)
2. **[HIGH-2]** `enableAllProjectMcpServers: true` → `false` 변경, 명시적 enable 목록만 유지 (R2)
3. **[HIGH-3]** `Skill(update-config)` allow 제거 또는 조건부 제어 + audit log 메커니즘 도입 (R3)
4. **[MED-1]** NeurIPS2026 경로 27개+ allow 항목 일괄 제거 (R5)
5. **[MED-2]** Codex `-BypassSandbox` → TASK 파일 명시 선언 시만 허가하는 조건부 패턴으로 변경 (R4)
6. **[MED-3]** `session_start_context.ps1` 등록 여부 결정 (A7)
7. **[LOW-1]** `NotebookEdit` coverage 추가 (schema_leakage_guard, baseline_ablation_guard) (R8)
8. **[LOW-2]** Dead rule + 슬래시 중복 정리 (R11)
9. **[INFO-1]** `permissionMode` 명시 설정 (R13)
