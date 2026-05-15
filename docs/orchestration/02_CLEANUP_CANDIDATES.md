# 02_CLEANUP_CANDIDATES.md

Phase 1 Orchestration Audit — Cleanup 후보 분류  
작성일: 2026-05-15  
작성자: Main Claude (read-only sweep, Phase 1)  
증거 출처: evidence block D + 직접 glob 확인  

**CRITICAL**: 이 문서는 분류 보고서다. 아무것도 삭제·이동·수정하지 않는다.  
실제 삭제/이동은 §5 Human-approval 절차를 통해서만 진행한다.

---

## 1. Scope (Report-only, NO deletion)

이 문서는 Phase 2 오케스트레이션 재설계 이전, repo에서 정리가 필요한 파일/디렉터리를 분류하는 보고서다. 분류는 아래 5가지로 나뉜다:

- `DELETE_CANDIDATE`: 삭제해도 연구 손실 없는 자동 생성 파일/폴더
- `ARCHIVE`: 완료된 phase의 historical 문서 — 삭제 대신 `archive/` 이동 검토
- `MERGE`: 중복/분산된 정보 → 하나로 통합 필요
- `REVIEW_LATER`: 사용자 확인 후 판단 필요
- `DO_NOT_DELETE`: 절대 보호 대상

---

## 2. Classification Rules

| 분류 | 기준 |
|---|---|
| DELETE_CANDIDATE | auto-generated, git-tracked 아님, 재생성 가능, 연구 내용 없음 |
| ARCHIVE | 과거 phase 완료 후 더 이상 active하지 않으나 historical 가치 있음 |
| MERGE | 동일 정보가 여러 파일에 분산됨 — 통합이 유지보수에 유리 |
| REVIEW_LATER | 상태 불명, 사용자 의도 확인 필요, 혹은 Phase 2 결정에 달림 |
| DO_NOT_DELETE | 연구 결과, source-of-truth, sentinel, 데이터, 테스트 — 손실 불허 |

---

## 3. Tables

### 3.1 DELETE_CANDIDATE

| 경로 | 근거 | 재생성 방법 |
|---|---|---|
| `.pytest_cache/` | pytest 자동 생성 cache. git-ignored 가능성 높음. 재생성 가능 | `pytest` 재실행 |
| `src/frcgw.egg-info/` | `pip install -e .` 자동 생성 build artifact. 재생성 가능 | `pip install -e .` 재실행 |
| `src/frcgw/**/__pycache__/` | Python 컴파일 cache. 재생성 가능 | Python 실행 시 자동 재생성 |
| `tests/__pycache__/` | 테스트 컴파일 cache. 재생성 가능 | Python 실행 시 자동 재생성 |
| `scripts/__pycache__/` | 스크립트 컴파일 cache. 재생성 가능 | Python 실행 시 자동 재생성 |
| `outputs/eval_reports/` (`.gitkeep`만) | 빈 placeholder, 아직 사용 안 됨. Phase 4 전 불필요 | `mkdir` |
| `outputs/review_reports/` (`.gitkeep`만) | 빈 placeholder, 아직 사용 안 됨 | `mkdir` |
| `outputs/test_reports/` (`.gitkeep`만) | 빈 placeholder, 아직 사용 안 됨 | `mkdir` |

**주의**: `.gitkeep` placeholder는 삭제 전 `.gitignore` 확인 필요. git-tracked이면 삭제 시 빈 디렉터리가 사라져 checkout 시 재생성 안 됨.

**codex_queue 원본 TASK (superseded by 재번호 버전)**:

| 경로 | 근거 | RESULT 존재 여부 |
|---|---|---|
| `.agent_tasks/codex_queue/TASK_1007_E1_eval_metrics.md` | `TASK_1012` (재번호)로 대체, `TASK_1012_..._RESULT.md` 존재 | ❌ 없음 (1007 기준) |
| `.agent_tasks/codex_queue/TASK_1008_E2_baselines.md` | `TASK_1013`으로 대체, RESULT 존재 | ❌ 없음 (1008 기준) |
| `.agent_tasks/codex_queue/TASK_1009_E3_eval_runner.md` | `TASK_1014`로 대체, RESULT 존재 | ❌ 없음 (1009 기준) |
| `.agent_tasks/codex_queue/TASK_1010_E4_ablations.md` | `TASK_1015`로 대체, RESULT 존재 | ❌ 없음 (1010 기준) |
| `.agent_tasks/codex_queue/TASK_1011_E5_eval_report.md` | `TASK_1016`으로 대체, RESULT 존재 | ❌ 없음 (1011 기준) |
| `.agent_tasks/codex_queue/TASK_1017_B1_episode_timestamps.md` | `TASK_1019`로 대체, RESULT 존재 | ❌ 없음 (1017 기준) |
| `.agent_tasks/codex_queue/TASK_1018_B2_frcg_agent_wrapper.md` | `TASK_1020`으로 대체, RESULT 존재 | ❌ 없음 (1018 기준) |

**판정**: 위 7개 원본 TASK는 재번호 버전의 RESULT가 존재하므로 orphaned. 단, 내용이 재번호 버전과 동일한지 diff 확인 후 삭제 권장.

---

### 3.2 ARCHIVE

이미 완료된 phase의 historical 문서. 삭제 대신 `plans/archive/` 또는 `.agent_tasks/codex_archive/` 이동 검토.

| 경로 | 근거 | phase 상태 |
|---|---|---|
| `plans/P0_REPO_SCAFFOLD_PLAN.md` | P0(repo scaffold) 완료. `P1.passed` sentinel 존재 | 완료 |
| `plans/P2_TEXT_ONLY_DATA_PLAN.md` | P2(text-only data) 완료. `P2.passed` sentinel 존재 | 완료 |
| `plans/P3_TEXT_MODEL_PLAN.md` | P3(text model) 완료. `P3.passed` sentinel 존재 | 완료 |
| `plans/P3_EVAL_FAILURE_DEBUG_PLAN.md` | P3 eval 디버그 완료. `P3_EVAL.passed` sentinel 존재 | 완료 |
| `plans/P2_GATE_REPORT.md` | P2 gate report. P2 완료로 historical | 완료 |
| `plans/P3_GATE_REPORT.md` | P3 gate report. P3 완료로 historical | 완료 |
| `plans/P3_EVAL_GATE_REPORT.md` | P3 eval gate report (104 KB). P3_EVAL 완료로 historical | 완료 |
| `.agent_tasks/codex_archive/p3_impl/` (6개) | 이미 archive 위치에 존재 | 완료 (현 위치 유지) |

**주의**: archive 이동은 `git mv`를 사용해야 history 보존. 단순 copy/delete는 금지.

---

### 3.3 MERGE

| 대상 파일들 | 중복 내용 | 제안 |
|---|---|---|
| `plans/PHASE_PROGRESS.md` ↔ `plans/P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md`(untracked) | P4 진행 상태/복구 계획 정보가 양쪽에 존재 | 통합 후 하나만 유지. untracked 파일의 내용을 먼저 확인해야 판단 가능 |
| `plans/P3_FINAL_EVAL_AND_P4_GUI_MVE_PLAN.md` ↔ `plans/P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md` | P4 GUI MVE 계획 정보 중복 가능 | 동일 내용 확인 후 결정 |

**주의**: MERGE 전 양쪽 파일 내용 diff 필수. PreCompact hook이 `PHASE_PROGRESS.md`에 자동 append하므로, merge 후에도 hook 대상 파일 경로를 업데이트해야 함.

---

### 3.4 REVIEW_LATER

| 항목 | 이유 | 필요한 확인 |
|---|---|---|
| `plans/P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md` (untracked) | git에 없음. 내용 중요도 및 add/commit/archive/삭제 여부 판단 필요 | 사용자 확인 필요 |
| `origin/feat/p1-schema-visibility` (원격 branch) | P1 schema/visibility 완료 후 폐기됐는지 불명. 삭제 시 원격 기록 손실 | `git log origin/feat/p1-schema-visibility`로 내용 확인 후 결정 |
| `outputs/runs/p3_smoke/checkpoint_ep0.pt` (18 MB) | git LFS 없이 tracked되어 있는지 불명. LFS 없이 tracked이면 repo 크기 문제 | `git lfs ls-files`로 LFS 등록 여부 확인 필요 |
| `plans/P3_FINAL_EVAL_AND_P4_GUI_MVE_PLAN.md` — `NeurIPS2026` 잔재 | 파일 자체는 유효하나 내부에 이전 프로젝트명 포함 | 해당 텍스트 수정 여부 결정 (content 수정은 trivial) |
| `plans/P0_REPO_SCAFFOLD_PLAN.md` — `NeurIPS2026` 잔재 | 동상 | 동상 |
| `.agent_tasks/codex_prompt_template.md` — `NeurIPS2026` 잔재 | Codex 측 contract 파일. Claude 수정 금지 범주. | Codex에게 수정 위임 또는 사용자 직접 수정 |
| `outputs/eval_reports/`, `outputs/review_reports/`, `outputs/test_reports/` | Phase 4 이후 사용될 placeholder인지, 지금 삭제해도 되는지 불명 | Phase 4 계획 확인 후 결정 |

---

### 3.5 DO_NOT_DELETE (절대 보호)

| 경로 | 이유 |
|---|---|
| `paper_context_ref/` (18개 md 전부) | Scientific source-of-truth. CLAUDE.md First Rule 근거 |
| `CLAUDE.md` | Scientific contract + First Rule |
| `.claude/rules/research_context_rules.md` | Non-negotiable scientific/data rules |
| `.claude/rules/codex_orchestration_rules.md` | Orchestration policy |
| `outputs/phase_gates/P1.passed` | P1 completion sentinel |
| `outputs/phase_gates/P1.5.passed` | P1.5 completion sentinel |
| `outputs/phase_gates/P2.passed` | P2 completion sentinel |
| `outputs/phase_gates/P3.passed` | P3 completion sentinel |
| `outputs/phase_gates/P3_EVAL.passed` | P3_EVAL completion sentinel (가장 최근) |
| `outputs/runs/p3_ablations/` | P3 ablation 실험 원본 결과 |
| `outputs/runs/p3_eval/` | P3 eval 실험 원본 결과 |
| `outputs/runs/p3_smoke/` | P3 smoke 실험 원본 (checkpoint 포함) |
| `data/frcgw_text/v0_1/` | 데이터셋 + audits + manifest |
| `configs/*.yaml` (7개) | 실험·훈련·평가 하이퍼파라미터 원본 |
| `tests/` (27개 파일) | 검증 테스트 전체 |
| `src/frcgw/` (전체) | 구현 코드 + stub 4개 (P4 이후 채워질 자리 포함) |
| `scripts/run_codex_task.ps1` | Codex harness source-of-truth (29.5 KB) |
| `.agent_tasks/codex_done/` (15개 RESULT.md) | 완료 TASK 결과 기록 |
| `.agent_tasks/codex_archive/` | 이미 archive된 P3 구현 TASK 6개 |
| `plans/PHASE_PROGRESS.md` | PreCompact hook 대상. 진행 상황 기록 |
| `.mcp.json` | MCP 서버 설정 |
| `.claude/settings.json` | Project hook 설정 |
| `.claude/agents/` (7개) | Agent 정의 파일 |
| `.claude/skills/` (7개) | Skill 정의 파일 |
| `.claude/commands/` (3개) | Slash command 정의 |
| `.claude/hooks/` (11개 .ps1) | Hook 구현 파일 |

---

## 4. Evidence per Row (One-line)

- `DELETE_CANDIDATE` cache: `git status`로 미확인이면 untracked — `git clean -n`으로 확인 가능.
- `DELETE_CANDIDATE` codex_queue 원본 7개: glob으로 `TASK_1007..1011`, `TASK_1017..1018` 직접 확인; `TASK_1012..1016`, `TASK_1019..1020` RESULT.md glob으로 확인.
- `ARCHIVE` plans/P*: `outputs/phase_gates/*.passed` sentinel 5개 모두 확인.
- `MERGE` PHASE_PROGRESS: PreCompact hook에서 `plans/PHASE_PROGRESS.md` append 직접 확인 (settings.json L87).
- `REVIEW_LATER` untracked: `git status` 스냅샷에서 1개 untracked 확인.
- `REVIEW_LATER` checkpoint: `outputs/runs/p3_smoke/` glob 결과.
- `DO_NOT_DELETE` sentinels: `outputs/phase_gates/` glob에서 5 sentinel + .gitkeep 확인.

---

## 5. Human-approval Required Before Any Real Deletion

다음 항목은 사용자가 명시적으로 승인해야 삭제/이동 가능:

| 우선순위 | 항목 | 확인 필요 이유 |
|---|---|---|
| CONFIRM-1 | `plans/P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md` | untracked이므로 삭제 시 영구 손실. 내용 중요도 사용자만 앎 |
| CONFIRM-2 | `origin/feat/p1-schema-visibility` 원격 branch | 원격 branch 삭제는 협업자가 있으면 영향 |
| CONFIRM-3 | codex_queue 원본 TASK 7개 (1007–1011, 1017–1018) | 재번호 버전과 내용 동일 여부 diff 확인 후 승인 |
| CONFIRM-4 | `plans/P*` archive 이동 | historical plan 손실 가능성 없는지 확인 |
| CONFIRM-5 | 빈 placeholder 3개 디렉터리 삭제 | Phase 4 계획에서 사용 예정인지 확인 |
| CONFIRM-6 | `outputs/runs/p3_smoke/checkpoint_ep0.pt` | git LFS 상태 확인 후 처리 방법 결정 |

---

## 6. Pre-deletion Verification Checklist

실제 삭제 전 다음 항목을 확인한다:

- [ ] `git status` / `git ls-files` — 해당 파일이 git-tracked인지 확인
- [ ] `git log --all -- <path>` — 해당 파일에 연관된 commit history 확인
- [ ] `grep -r <filename> configs/ scripts/ .claude/hooks/` — config/hook에서 해당 경로 참조 여부 확인
- [ ] `grep -r <filename> paper_context_ref/ CLAUDE.md` — 보호 문서에서 참조 여부 확인
- [ ] `git clean -n` — untracked delete candidate 미리보기 (dry-run)
- [ ] Codex worktree 동기화 완료 여부 — 삭제 전 codex-work fast-forward 확인

---

## 7. Rollback Strategy

실수로 삭제 후 복구 방법:

| 케이스 | 복구 방법 |
|---|---|
| git-tracked 파일 삭제 | `git checkout HEAD -- <path>` 또는 `git restore <path>` |
| untracked 파일 삭제 (`plans/P4_...md`) | **복구 불가** — Phase 1에서 손대지 않는 이유 |
| archive 이동 후 원복 | `git mv` 사용했으면 `git mv` 역방향으로 복구 |
| 원격 branch 삭제 | `git push origin <commit-hash>:refs/heads/<branch-name>` (commit 알면) |
| pytest_cache / __pycache__ 삭제 | `pytest` 재실행으로 자동 재생성 |
| egg-info 삭제 | `pip install -e .` 재실행으로 재생성 |
