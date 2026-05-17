# 14_REPORT_LIFECYCLE_POLICY.md

**작성일**: 2026-05-16  
**Phase**: P5 orchestration cleanup  
**근거**: `02_CLEANUP_CANDIDATES.md`, `11_SESSION_END_REPORT_PROTOCOL.md`,  
`CLAUDE.md` §Behavioral Coding Rules (destructive → dry-run → 승인)

---

## §1. Purpose

FRCG-WM 리포지토리에는 세션 작업 중 생성된 임시 리포트 파일이 기하급수적으로 누적된다.  
이 정책은 SSoT(진실의 단일 출처)와 Temporary(임시 산출물)를 명확히 분리하고,  
임시 파일의 수명주기(archive 조건, 절차, 금지 조건)를 명문화한다.

**핵심 원칙**:
- delete 금지, archive-first
- ARCHIVE_READY 클래스 중 rule-based 조건을 만족하는 파일은 **자동 git mv** (Phase 5 이후)
- MANUAL_ONLY / UNKNOWN: dry-run 출력 + human 승인 후 별도 라운드에서만 실행
- scientific contract(forbidden field, baseline, evaluation) 완화 0

---

## §2. SSoT vs Temporary 분류표

### §2.1 SSoT (절대 archive/delete 금지)

| 경로 패턴 | 설명 |
|---|---|
| `paper_context_ref/*.md` (16개) | 논문 scientific contract |
| `docs/orchestration/00_..13_*.md` (14개) | 오케스트레이션 정책 파일 |
| `docs/orchestration/**/_TEMPLATE*.md` | 세션 리포트/결정 로그 템플릿 |
| `docs/orchestration/**/INDEX.md` | 각 서브디렉토리 인덱스 |
| `outputs/phase_gates/*.passed` | Phase gate sentinel (zero-byte marker) |
| `CLAUDE.md`, `CLAUDE.local.md` | 프로젝트/머신 지침 |
| `src/`, `tests/`, `configs/`, `scripts/` | 구현 코드 |
| `pyproject.toml`, `.claude/settings.json` | 프로젝트 설정 |

### §2.2 Temporary (archive 후보)

| 경로 패턴 | 카테고리 |
|---|---|
| `plans/P*_PLAN.md` | PLAN |
| `plans/P*_GATE_REPORT.md` | GATE_REPORT |
| `plans/PHASE_PROGRESS.md` | PROGRESS (special: NEVER — pre_compact hook active) |
| `plans/P*_PROGRESS_*.md` | PROGRESS |
| `plans/PLUGIN_AUDIT_REPORT.md` | PLAN |
| `plans/codex/*.md` | PLAN |
| `docs/orchestration/PHASE*_GATE_REPORT.md` | GATE_REPORT |
| `docs/orchestration/session_reports/YYYY-MM/*.md` | SESSION |
| `docs/orchestration/decision_logs/YYYY-MM/session_*.md` | DECISION |
| `.agent_tasks/codex_done/*_RESULT.md` | RESULT |

> **Special case**: `plans/PHASE_PROGRESS.md`는 pre_compact hook가 active append를 수행하므로
> ssot_absorbed=NEVER로 처리. archive/delete 절대 금지.

---

## §3.5 Auto-archive rule set (Phase 5 — rule-based)

다음 5개 규칙을 만족하는 파일은 `stop_lifecycle_automation.ps1` 턴 종료 hook에서
`archive_sweep_v2.py`가 자동으로 `git mv`한다. 복구 가능한 이동이다 (`restore_command` 포함).

| Rule | Path pattern | 조건 | Destination |
|---|---|---|---|
| A | `plans/P\d+.*\.md` (not PHASE_PROGRESS) | `outputs/phase_gates/P{N}.passed` 존재 | `plans/archive/YYYY-MM/` |
| B | `docs/orchestration/PHASE\w+_GATE_REPORT\.md` | 항상 (historical, immutable) | `docs/orchestration/archive/YYYY-MM/` |
| C | `.agent_tasks/codex_done/TASK_\d+.*_RESULT\.md` | 항상 (completed task records) | `.agent_tasks/archive/YYYY-MM/codex_done/` |
| D | `.agent_tasks/codex_archive/**/*.md` | 항상 (already named archive) | `.agent_tasks/archive/YYYY-MM/p3_impl/` |
| E | `docs/orchestration/session_reports/YYYY-MM/*_precompact_handoff.md` | 같은 폴더에 더 최신 precompact_handoff 존재 | `docs/orchestration/archive/YYYY-MM/session_reports/` |

**보호 예외** (어떤 규칙에서도 ARCHIVE_READY 금지):
- `paper_context_ref/**`, `src/frcgw/**`, `tests/**`, `evidence_cards/**`
- `outputs/phase_gates/**`, `outputs/runs/**`, `data/**`
- `claim_status.json`, `ablation_results.json`
- `plans/PHASE_PROGRESS.md`, `CLAUDE.md`, `.claude/**`, `.self_evolving_memory/**`

**Implementation**: `scripts/archive_sweep_v2.py` (MAX_FILES=50, MAX_BYTES=5MB)
**Self-evolving status**: manifest field `self_evolving_summary_status` + DEC-003

---

## §3. Archive 5조건 (모두 충족 필수)

임시 파일을 archive 대상으로 판정하려면 다음 **5개 조건을 모두** 충족해야 한다.

| ID | 조건 |
|---|---|
| C1 | 내용이 active SSoT(paper_context_ref, 00..13 정책, sentinel)에 흡수됨 |
| C2 | blocker/decision이 후속 session report 또는 decision log에 이관됨 |
| C3 | data manifest 또는 phase gate sentinel에 결과가 반영됨 |
| C4 | 미해결 leakage/schema/baseline/evaluation 결정 없음 |
| C5 | 본 정책 §3 archive 사유 한 줄이 archive 이동 PR에 명시됨 |

---

## §4. Archive-First 원칙

- **delete 금지**: 임시 파일은 삭제하지 않는다.
- **archive 경로**:
  - `plans/archive/YYYY-MM/` (plans 임시 파일)
  - `docs/orchestration/archive/YYYY-MM/` (docs 임시 파일)
  - `.agent_tasks/codex_done/` 내 RESULT.md는 현재 위치 유지 (별도 archive 불필요)
- archive 이동 후 `INDEX.md` 갱신 의무.

---

## §5. 디렉토리 레이아웃

```
docs/orchestration/
  archive/                <- .gitkeep 존재, 실제 파일 이동 전까지 비어 있음
    YYYY-MM/              <- 이동 시 월별 서브디렉토리 생성
  session_reports/
  decision_logs/
  mcp_research/

plans/
  archive/                <- .gitkeep 존재
    YYYY-MM/
```

`.gitkeep` 파일은 zero-byte marker로 git에 트래킹된다.  
실제 archive 이동 시 `YYYY-MM/` 서브디렉토리를 만들고 파일을 이동한다.

---

## §6. Dry-run 절차

```powershell
# 기본 dry-run (전체)
.\.venv\Scripts\python.exe scripts\audit_stale_reports.py

# JSON 출력 (human review)
.\.venv\Scripts\python.exe scripts\audit_stale_reports.py --json

# 카테고리 필터
.\.venv\Scripts\python.exe scripts\audit_stale_reports.py --category PLAN

# --apply 플래그: 정책상 미지원 (exit code 2 반환)
```

`--apply` 플래그: Phase 5 이후 `archive_sweep_v2.py --apply --confirm-auto-archive`로 rule-based 자동 실행.
`scripts/audit_stale_reports.py`의 `--apply`는 계속 미구현 (MANUAL_ONLY 대상 파일은 별도 라운드).

---

## §7. 절대 archive/delete 금지 조건

다음 중 하나라도 해당하면 해당 파일의 archive/delete를 즉시 중단한다.

| 금지 조건 | 이유 |
|---|---|
| active phase gate sentinel의 source report | sentinel이 살아 있는 동안 report도 살아 있어야 함 |
| 현재 phase의 `*_PLAN.md` (`PHASE_PROGRESS.md` 확인) | 진행 중인 phase의 plan은 active |
| `_TEMPLATE*`, `INDEX.md` | SSoT §2.1 |
| `paper_context_ref/` 내 모든 파일 | SSoT §2.1 |
| `outputs/phase_gates/*.passed` | phase gate sentinel은 영구 보존 |
| `DECISIONS_REQUIRED` 섹션이 열린 session report | 미해결 결정 포함 |
| `plans/PHASE_PROGRESS.md` | pre_compact hook active append |

---

## §8. Milestone 후 정리 루틴

새 phase gate sentinel 추가 후:

1. `scripts\audit_stale_reports.py --json` 실행
2. `per_category` 및 `ssot_absorbed` 값 검토
3. archive 후보 각각에 대해 §3 5조건 수동 검증
4. 통과 파일만 Move-Item 명령 준비 (PR로 제출)
5. SEV(Session End Validation) 포함

---

## §9. Cross-reference

| 파일 | 역할 |
|---|---|
| `docs/orchestration/02_CLEANUP_CANDIDATES.md` | 분류 규칙 원본 (복제 금지, 참조만) |
| `docs/orchestration/11_SESSION_END_REPORT_PROTOCOL.md` | session report 경로 + 5종 리포트 규약 |
| `docs/orchestration/13_MASTER_ORCHESTRATION_PLAN.md` | phase progression sentinel 매핑 출처 |
| `scripts/audit_stale_reports.py` | dry-run audit 실행 스크립트 |
| `outputs/phase_gates/*.passed` | dynamic glob (하드코딩 금지) |
