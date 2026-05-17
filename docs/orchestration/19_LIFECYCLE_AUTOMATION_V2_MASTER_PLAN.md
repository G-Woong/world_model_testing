# 19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md

## Purpose

lifecycle automation v2 4개 설계 문서를 통합한 최종 실행 설계도.

생성일: 2026-05-17  
Branch: memory-redesign-2026-05-16  
Status: ACTIVE_POLICY  
Phase: pre-implementation (설계만, 코드 수정 0)

---

## §1. 현재 문제 요약

| 문제 | 위험도 | 참조 |
|---|---|---|
| auto-commit에 science/cleanup 변경 혼재 위험 | HIGH | 15_§6 |
| plan path 5+위치 산재 (plans/ + docs/ + outputs/ + ~/.claude/plans/ + .agent_tasks/) | MEDIUM | 17_§1 |
| self-evolving memory 단일 store 없음 (4폴더 분산) | MEDIUM | 16_§1 |
| lifecycle hook 없음 (Stop chain에 lifecycle automation 미연결) | HIGH | 15_§1 |
| `P3_EVAL.BLOCKED_planning_calls_zero.md` stale sentinel 공존 | MEDIUM | RISK-A |
| branch 93 commits ahead of main | LOW (local) | RISK-B |
| docs/orchestration/ 24개 파일로 증가 (슬림화 필요) | MEDIUM | 18_§7 |

---

## §2. 자동화 v2 전체 구조

```
1 lifecycle hook          → stop_lifecycle_automation.ps1
1 single memory folder   → .self_evolving_memory/
1 plan path rule          → CLAUDE.md + pre_tool_guard.ps1
1 orchestration registry  → outputs/lifecycle/orchestration_registry.json
```

---

## §3. Hook Pipeline (Stop chain 확장)

### 현재 (3개)

```
stop_summary_guard.ps1
  → stop_auto_commit.ps1
  → stop_codex_sync_telemetry.ps1
```

### 목표 (5개)

```
stop_summary_guard.ps1                    (existing)
  → stop_lifecycle_automation.ps1         (NEW, default dry-run)
      ├─ lifecycle classifier             (auto-safe / protected / manual-only)
      ├─ orchestration audit              (orchestration_registry.json 갱신)
      ├─ self-evolving memory update      (.self_evolving_memory/ 갱신)
      └─ outputs/lifecycle/, .self_evolving_memory/ 에 결과 기록
  → stop_self_evolving_commit.ps1         (NEW, optional)
      └─ lifecycle-scope 변경만 별도 commit
          chore(lifecycle): quarantine superseded artifacts <UTC>
  → stop_auto_commit.ps1                  (existing, extended fragile list)
      └─ fragile list 확장: .lifecycle_trash/**, outputs/lifecycle/**, .self_evolving_memory/**
  → stop_codex_sync_telemetry.ps1         (existing)
```

---

## §4. Self-Evolving Memory 구조

문서 16 §3 참조.

```
.self_evolving_memory/
  README.md          ← 사용자 진입점
  index.yaml         ← machine-readable master pointer
  errors/            ← error_memory.yaml, recurring_errors.md, resolved_errors.md
  decisions/         ← decision_memory.yaml, superseded_decisions.md
  patterns/          ← successful_patterns.md, anti_patterns.md
  directions/        ← active_direction.md, rejected_directions.md, parking_lot.md
  hooks/             ← hook_failures.md, hook_execution_log.md
  run_summaries/     ← YYYY-MM/run_<UTC>.md
```

사용자 view: `README.md` + `index.yaml` 2개만.  
BLOCKER 조건: occurrence_count ≥ 2 in `errors/recurring_errors.md`.

---

## §5. Plan Path Enforcement

문서 17 §3 참조.

```
Layer 1: CLAUDE.md §Plan Output Path Rule    (규칙 명문화)
Layer 2: pre_tool_guard.ps1 WARN             (생성 시점 경고)
Layer 3: stop_lifecycle_automation.ps1 감지  (생성 후 sweep)
```

허용 경로:
```
plans/              ← 실행 plan
docs/orchestration/ ← 정책/report
~/.claude/plans/    ← harness 자동
.agent_tasks/       ← Codex TASK
```

---

## §6. Orchestration Slimming (1순위 sweep 타겟)

문서 18 §2~§5 참조.

Phase F/G 첫 sweep 목표:
```
top-level .md: 24 → 20 이하
session_reports/: 16 → 5
decision_logs/: 6 → 3
agent_reports/: 7 → 3
```

MANUAL_ONLY 보존: negative evidence, gate sentinel source, failed attempt report.  
Archive 후보: PHASE1/2/3_GATE_REPORT.md, old session handoff.

---

## §7. Trash/Quarantine 정책

문서 15 §3~§4 참조.

```
.lifecycle_trash/
  YYYY-MM/
    run_<UTC-ts>/
      manifest.json    (sha256, original_path, reason, classifier_version)
      files/           (이동된 실제 파일)
      restore.ps1      (자동 생성)
      delete_after_review.ps1  (사용자가 직접 실행)
```

원칙: **이동이지 삭제 아님**. restore 1-click. dry-run default.

---

## §8. Protected Paths (통합 마스터 리스트)

아래 경로는 lifecycle automation이 절대 이동/삭제하지 않는다.

```
paper_context_ref/**
src/frcgw/**
tests/**
configs/**
scripts/**
outputs/phase_gates/**
outputs/runs/p3_lr_eval/**
outputs/runs/p3_ablations/**
outputs/runs/p3_lr_smoke/**
docs/orchestration/lr_alignment/evidence_cards/**
docs/orchestration/lr_alignment/12_run6_lr_eval_report.md
docs/orchestration/lr_alignment/13_claim_survivability_decision_report.md
docs/orchestration/00_*.md
docs/orchestration/01_*.md
docs/orchestration/02_*.md
docs/orchestration/03_*.md
docs/orchestration/04_*.md
docs/orchestration/05_*.md
docs/orchestration/06_*.md
docs/orchestration/07_*.md
docs/orchestration/08_*.md
docs/orchestration/09_*.md
docs/orchestration/10_*.md
docs/orchestration/11_*.md
docs/orchestration/12_*.md
docs/orchestration/13_*.md
docs/orchestration/14_*.md
docs/orchestration/15_*.md
docs/orchestration/16_*.md
docs/orchestration/17_*.md
docs/orchestration/18_*.md
docs/orchestration/19_*.md
docs/orchestration/**/_TEMPLATE*.md
docs/orchestration/**/INDEX.md
plans/PHASE_PROGRESS.md
CLAUDE.md
CLAUDE.local.md
.claude/settings.json
.claude/settings.local.json
.mcp.json
.agent_tasks/codex_prompt_template.md
.self_evolving_memory/
```

---

## §9. Next Implementation Phases

각 Phase는 별도 사용자 승인 필요.

| Phase | Goal | Files Modified | Files Created | Approval |
|---|---|---|---|---|
| A | registry/schema 설계 + .gitignore reservation | `.gitignore` (+3 lines) | `.lifecycle_trash/.gitkeep`, `.self_evolving_memory/.gitkeep`, `outputs/lifecycle/.gitkeep`, registry JSON schema doc | YES |
| B | `lifecycle_audit_v2.py` dry-run 구현 | none | `scripts/lifecycle_audit_v2.py` | YES |
| C | `.self_evolving_memory/` 초기 구조 생성 | none | README.md, index.yaml, schema docs | YES |
| D | plan path enforcement hook | `.claude/hooks/pre_tool_guard.ps1` (extend) | `.claude/commands/frcgw-plan-new.md` | YES |
| E | `stop_lifecycle_automation.ps1` dry-run 연결 | `.claude/settings.json` (+1 hook entry) | hook script | YES (CRITICAL — fragile file) |
| F | auto-safe cache cleanup 활성화 | `stop_lifecycle_automation.ps1` (--mode safe) | none | YES |
| G | archive/trash automation 단계적 rollout | `stop_auto_commit.ps1` fragile list 확장 | `scripts/lifecycle_trash_v2.py`, `scripts/lifecycle_restore_v2.ps1` | YES |

---

## §10. 구현 전 사용자 승인 필요 항목 (CRITICAL gate)

| 항목 | Phase | 이유 |
|---|---|---|
| `.gitignore` 수정 | A | 간접적 fragile (commit 영향) |
| `.claude/settings.json` 수정 | E | 직접 fragile (CLAUDE.md §Invariant Preservation) |
| `stop_auto_commit.ps1` fragile list 확장 | G | auto-commit 동작 변경 |
| 첫 actual trash 이동 (apply) | G | 비가역적 파일 이동 시작점 |

---

## §11. Risks (구현 Phase 대비)

| Risk ID | 내용 | 완화 |
|---|---|---|
| RISK-A | `P3_EVAL.BLOCKED_planning_calls_zero.md` stale sentinel | Phase F 첫 sweep candidate 등록 |
| RISK-B | branch 93 commits ahead | Phase E 이전 main 동기화 검토 |
| RISK-C | 5개 .md가 opaque chore(turn) commit에 섞임 | 가능하면 이 5개만 생성하는 단독 턴 |
| RISK-D | 새 PLAN 문서 자체가 다음 sweep에서 superseded 후보 | 18_§2 ACTIVE_POLICY 분류로 보호 |

---

## §12. Verification (구현 Phase 검증)

| 검증 항목 | 방법 |
|---|---|
| Phase A: .gitignore 수정 후 | `git status --short` → .lifecycle_trash/.gitkeep 등 tracked 확인 |
| Phase B: dry-run audit | synthetic dirty tree로 classification JSON 확인 |
| Phase C: memory 구조 | `Get-ChildItem .self_evolving_memory -Recurse` → schema 일치 확인 |
| Phase D: plan path WARN | 비표준 경로 plan-test.md Write 시도 → stderr WARN 확인 |
| Phase E: Stop hook 연결 | Stop event 후 `outputs/lifecycle/latest_session_audit.md` 생성 확인 |
| Phase F: cache cleanup | `.pytest_cache` 삭제 dry-run → manifest 확인 |
| Phase G: restore roundtrip | trash 이동 → restore.ps1 실행 → 원본 경로 복구 확인 |

---

## §13. Cross-reference (4개 하위 설계 문서)

| 문서 | 내용 |
|---|---|
| `docs/orchestration/15_lifecycle_automation_v2_plan.md` | Stop hook pipeline + trash/quarantine 구조 |
| `docs/orchestration/16_self_evolving_memory_architecture_plan.md` | 단일 memory folder + error schema |
| `docs/orchestration/17_plan_output_path_control_plan.md` | plan path 고정 + pre_tool_guard |
| `docs/orchestration/18_orchestration_slimming_and_trash_policy_plan.md` | orchestration 슬림화 타겟 |
| `docs/orchestration/14_REPORT_LIFECYCLE_POLICY.md` | 기존 lifecycle policy SSoT |
| `docs/orchestration/05_SELF_EVOLVING_LOOP.md` | 기존 self-evolving SSoT |
| `.claude/rules/behavioral_coding_rules.md §5` | fragile file invariants |
| `CLAUDE.md §Invariant Preservation` | settings.json 수정 approval gate |
