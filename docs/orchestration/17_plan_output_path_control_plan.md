# 17_plan_output_path_control_plan.md

## Purpose

plan md 생성 경로를 `plans/` 또는 사용자가 지정한 경로로 고정하는 설계도.

생성일: 2026-05-17  
Branch: memory-redesign-2026-05-16  
Status: ACTIVE_POLICY  
Phase: pre-implementation (설계만, 코드 수정 0)  
Archive_after: Phase D 완료 후 → `plans/archive/2026-06/`

---

## §1. Current Plan Output Audit

### 현재 plan md가 존재하는 위치 (5+곳)

| 위치 | 파일 수 | 설명 |
|---|---|---|
| `C:\Users\computer\.claude\plans\` | 17개 | 글로벌 harness 자동 생성 |
| `plans/` | 13개 | 프로젝트 active phase plan |
| `docs/orchestration/` | 4개 (plan suffix) | `02_option_b_design_plan.md` 등 |
| `docs/orchestration/lr_alignment/` | 00~17 | 연구 alignment plan |
| `outputs/cleanup_audit/<ts>/` | 1개 | `final_cleanup_plan.md` |
| `.agent_tasks/codex_*/` | N개 | `TASK_*.md` (TASK 파일) |

### 어떤 settings/hook도 plan path를 enforce하지 않음

현재 상태: plan md를 어디에 생성해도 차단 메커니즘 없음.

---

## §2. Desired Rule (경로 분리 원칙)

| 파일 유형 | 올바른 경로 | 예시 |
|---|---|---|
| 실행 plan | `plans/` | `plans/P3_eval_run7.md` |
| 정책/report/decision/evidence | `docs/orchestration/` | `docs/orchestration/15_*.md` |
| scientific SSoT | `paper_context_ref/` | `paper_context_ref/10_*.md` |
| run artifact | `outputs/` | `outputs/runs/p3_lr_eval/` |
| 완료된 plan | `plans/archive/YYYY-MM/` | `plans/archive/2026-05/P2_done.md` |
| harness 자동 plan | `~/.claude/plans/` | 그대로 유지 (글로벌) |
| Codex TASK 파일 | `.agent_tasks/codex_queue/` | `TASK_001_*.md` |

규칙: 프로젝트 영구 plan은 `plans/`로 이관 의무.  
harness 자동 plan은 `~/.claude/plans/` 그대로 (글로벌, 변경 불가).

---

## §3. Enforcement Options

### A. CLAUDE.md `## Plan Output Path` 섹션 추가

- 비용: 5~10줄 CLAUDE.md 추가
- 효과: Claude 동작 지침
- 한계: hook 없음 → 위반 시 차단 안 됨

### B. `.claude/settings.json` 수정

- UNKNOWN: 현재 schema에 plan-path 항목 없음
- 시도 가능하나 schema 확장 필요
- fragile file → 사용자 승인 필수

### C. `.claude/commands/`에 plan template 추가

- `frcgw-plan-new.md` command 추가
- 신규 plan 생성 시 `plans/PXX_*.md` 자동 생성 템플릿
- 비용: 새 command 파일 1개

### D. `.claude/hooks/pre_tool_guard.ps1`에 plan path 검사 추가

- Write tool 대해: file_path가 `*.md`이고 "plan" 키워드 포함이면
- path가 `plans/`, `docs/orchestration/`, `~/.claude/plans/` 중 하나인지 확인
- 아니면 stderr WARN (block 아닌 warn, 작업 중단 없음)

### E. `stop_lifecycle_automation.ps1`에 misplaced plan md 감지

- Stop hook에서 plan-like md를 detected → manifest에 등록
- 다음 sweep에서 trash 후보로 표시

---

## §4. 추천 조합: A + D + E

| Layer | 역할 | 구현 |
|---|---|---|
| CLAUDE.md A | 규칙 명문화 | Phase A |
| pre_tool_guard.ps1 D | PreToolUse 검사 (WARN) | Phase D |
| stop_lifecycle_automation.ps1 E | Stop hook 감지 | Phase E |

3-layer 방어: 정책 명시 → 생성 시점 경고 → 생성 후 감지.

---

## §5. Proposed Patch Plan (다음 구현 턴)

이번 턴 **실제 수정 0**. 다음 구현 Phase에서 적용할 exact diff 사양:

### CLAUDE.md 추가 섹션 (Phase A)

```markdown
## Plan Output Path Rule

- 실행 plan md → `plans/PXX_<name>.md`
- 정책/report/evidence → `docs/orchestration/`
- 완료된 plan → `plans/archive/YYYY-MM/`
- harness 자동 plan → `~/.claude/plans/` (글로벌, 변경 불가)
- Codex TASK → `.agent_tasks/codex_queue/TASK_*.md`
- 위 경로 이외의 plan md 생성은 pre_tool_guard.ps1 WARN 발생.
```

### pre_tool_guard.ps1 추가 로직 (Phase D)

```powershell
# plan path check (WARN only, no block)
if ($tool -eq "Write" -and $filePath -match "\.md$" -and $filePath -match "plan") {
    $allowed = @("plans/", "docs/orchestration/", ".claude/plans/", ".agent_tasks/")
    $isAllowed = $false
    foreach ($prefix in $allowed) {
        if ($filePath -replace "\\","/" -match [regex]::Escape($prefix)) {
            $isAllowed = $true; break
        }
    }
    if (-not $isAllowed) {
        Write-Error "[WARN] plan md를 비표준 경로에 생성 중: $filePath"
        Write-Error "[WARN] 허용 경로: plans/, docs/orchestration/"
        # exit 0 (warn only, 작업 계속)
    }
}
```

### .claude/commands/frcgw-plan-new.md (Phase D, 신규 command)

```markdown
# /frcgw-plan-new

신규 실행 plan md를 `plans/` 아래 올바른 경로에 생성한다.

Usage: /frcgw-plan-new <phase> <name>
Example: /frcgw-plan-new P3 eval_run7

생성 경로: plans/P<phase>_<name>.md
frontmatter 자동 추가: status, phase, created, archive_after
```

### 수정 금지

`.claude/settings.json` — fragile file, plan path enforcement는 hook 레이어에서.

---

## §6. Validation

| 검증 항목 | 방법 |
|---|---|
| pre_tool_guard WARN 동작 | 비표준 경로에 plan-xxx.md Write 시도 → stderr WARN 확인 |
| lifecycle 감지 | Stop event 후 outputs/lifecycle/latest_session_audit.md에 misplaced plan 등록 |
| archive-ready 판단 | plan md YAML frontmatter: `status: COMPLETED`, `archive_after: 2026-06-01` |

---

## §7. Plan Lifecycle Metadata (YAML frontmatter)

plan md에 아래 frontmatter를 추가하면 lifecycle automation이 자동 분류:

```yaml
---
status: ACTIVE | COMPLETED | SUPERSEDED
phase: P3
created: 2026-05-17
archive_after: 2026-06-01
owner: claude | user
---
```

`status: COMPLETED` + `archive_after < today` → archive-ready 자동 분류.

---

## §8. Cross-reference

- `docs/orchestration/14_REPORT_LIFECYCLE_POLICY.md` — §2 SSoT 표에 plan path 규칙 행 추가 예정 (Phase A)
- `docs/orchestration/15_lifecycle_automation_v2_plan.md` — lifecycle classifier
- `docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md` — master plan
- `CLAUDE.md §Behavioral Coding Rules` — 수정 전 Goal/Change/Test 서술 의무
