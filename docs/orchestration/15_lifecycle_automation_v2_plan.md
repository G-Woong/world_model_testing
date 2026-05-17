# 15_lifecycle_automation_v2_plan.md

## Purpose

Stop turn / auto-commit hook 흐름에 lifecycle automation을 연결하는 설계도.

생성일: 2026-05-17  
Branch: memory-redesign-2026-05-16  
Status: ACTIVE_POLICY  
Phase: pre-implementation (설계만, 코드 수정 0)  
Archive_after: Phase G 완료 후 → `plans/archive/2026-06/`

---

## §1. Current Hook Audit

### Stop chain (현재)

```
stop_summary_guard.ps1       → 요약 검사 / stderr WARN
stop_auto_commit.ps1         → chore(turn): auto-commit <UTC>
stop_codex_sync_telemetry.ps1 → Codex 워킹트리 sync log
```

### fragile 8개 path (stop_auto_commit.ps1 보호 대상)

```
.claude/settings.json
CLAUDE.md
.mcp.json
scripts/run_codex_task.ps1
.agent_tasks/codex_prompt_template.md
src/frcgw/schemas/visibility.py
paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
```

### Gap (보호 안 됨)

```
src/frcgw/training/**        ← science commit이 cleanup과 섞일 위험
src/frcgw/models/**
configs/*.yaml
tests/**
outputs/runs/*/metrics.json
```

### Lifecycle hook 상태

`.lifecycle_trash/` → NOT_FOUND  
lifecycle automation hook → NOT_FOUND  
자동 cleanup 메커니즘 → 없음

---

## §2. Desired Event Pipeline

```
Claude turn ends
  → Stop event fires
  → stop_summary_guard.ps1            (existing)
  → stop_lifecycle_automation.ps1     (NEW, dry-run default)
      ├─ changed-files snapshot         (git status --porcelain)
      ├─ lifecycle classifier           (auto-safe / manual-only / protected / disposable)
      ├─ trash/quarantine staging manifest  (Phase A/B: 실제 이동 없음)
      └─ outputs/lifecycle/latest_session_audit.md 기록
  → stop_auto_commit.ps1              (existing, extended fragile list)
  → stop_codex_sync_telemetry.ps1     (existing)
```

---

## §3. Trash/Quarantine 구조

```
.lifecycle_trash/
  YYYY-MM/
    run_<UTC-ts>/
      manifest.json        (sha256, original_path, reason, classifier_version)
      manifest.md          (human-readable)
      files/
        <sanitized_path>   (이동된 실제 파일)
      restore.ps1          (자동 생성, 1-click 복구)
      delete_after_review.ps1  (사용자가 직접 실행)
```

원칙:
- 삭제가 아닌 이동 (원본 경로 기록)
- sha256 기록 (integrity 검증 가능)
- restore 스크립트 자동 생성 (롤백 1-click)
- manifest 없이 이동 금지
- hash 없이 이동 금지
- dry-run default (사용자가 `--apply` 명시해야 실제 이동)

---

## §4. Auto Classification Rules

### auto-safe (자동 trash 허용)

```
임시 plan draft         → PLAN-DRAFT-* 패턴, status=DRAFT 메타
superseded handoff      → 같은 날 동일 artifact_type 중 최신만 active
stale cleanup_audit     → outputs/cleanup_audit_temp.json, orphan staging
__pycache__             → Python 캐시
.pytest_cache           → pytest 캐시
intermediate logs       → outputs/logs/tmp_*, *.log.tmp
```

### protected (절대 이동 금지)

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
docs/orchestration/00_*.md .. 14_*.md .. 15_*.md .. 19_*.md
plans/PHASE_PROGRESS.md
CLAUDE.md
CLAUDE.local.md
.claude/settings.json
.claude/settings.local.json
.mcp.json
.agent_tasks/codex_prompt_template.md
.self_evolving_memory/
```

### manual-only (사용자 승인 필요)

```
session_reports/**
decision_logs/**
.agent_tasks/codex_done/**
docs/orchestration/PHASE*_GATE_REPORT.md
negative evidence reports     (삭제 절대 금지, archive만 가능)
unknown *.md
```

---

## §5. Hook Integration Phases

| Phase | 동작 | 기본값 |
|---|---|---|
| A | dry-run report only (outputs/lifecycle/*.md 작성) | default |
| B | cache auto-clean + trash candidate report (no move) | 추천 첫 단계 |
| C | safe artifacts auto-trash + 별도 lifecycle commit | B 안정화 후 |

추천: **B**부터 시작, 2주 운영 후 C.

---

## §6. Auto-Commit Interaction

lifecycle 이동은 반드시 `stop_auto_commit.ps1`의 chore(turn)과 **분리된 commit**으로 생성:

```
chore(lifecycle): quarantine superseded artifacts <UTC>
```

`stop_auto_commit.ps1` fragile list에 추가할 경로 (Phase G):
```
.lifecycle_trash/**
outputs/lifecycle/**
.self_evolving_memory/**
```

이 3개를 fragile list에 추가하면 lifecycle hook이 자기 commit 책임을 가진다.
`stop_auto_commit.ps1`은 위 3개를 skip하고, lifecycle commit script가 별도 처리.

---

## §7. Required Scripts (사양만, 구현은 Phase B~G)

| 스크립트 | 역할 | 구현 Phase |
|---|---|---|
| `scripts/lifecycle_audit_v2.py` | changed-files manifest → classification JSON | B |
| `scripts/lifecycle_trash_v2.py` | classification + approval flag → trash manifest | G |
| `scripts/lifecycle_restore_v2.ps1` | trash manifest 기반 복구 | G |
| `.claude/hooks/stop_lifecycle_automation.ps1` | Stop chain 2번째 위치 | E |

---

## §8. Safety Gates

- default dry-run (사용자 `--apply` 명시 없으면 실제 이동 없음)
- protected globs hard block (매칭 시 skip, error 아닌 warn)
- max files per run: 50개
- max total bytes per run: 50 MB
- source code 이동 금지 (`src/**`)
- phase gate 이동 금지 (`outputs/phase_gates/**`)
- paper_context_ref 이동 금지
- restore script 없으면 이동 금지
- manifest 없으면 이동 금지
- hash 없으면 이동 금지
- auto-commit 분리 (lifecycle commit ≠ science commit)

---

## §9. Cross-reference

- `docs/orchestration/14_REPORT_LIFECYCLE_POLICY.md` — 기존 lifecycle policy SSoT
- `docs/orchestration/18_orchestration_slimming_and_trash_policy_plan.md` — orchestration 슬림화
- `docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md` — master plan
- `.claude/rules/behavioral_coding_rules.md §5` — fragile file invariants
