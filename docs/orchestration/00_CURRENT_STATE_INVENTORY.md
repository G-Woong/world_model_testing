# 00_CURRENT_STATE_INVENTORY.md

Phase 1 Orchestration Audit — 현재 상태 인벤토리  
작성일: 2026-05-15  
작성자: Main Claude (read-only sweep, Phase 1)  
증거 출처: 3-agent Explore sweep (evidence block A/B, 2026-05-15) + 직접 파일 읽기

---

## 1. Scope & Method

- **목적**: 오케스트레이션 재설계(Phase 2) 전, repo 현황을 변경 없이 기록
- **방법**: git 상태 확인, 파일 glob/read, settings.json/local.json 직접 읽기
- **제약**: 이 문서는 read-only 산출물. 어떤 파일도 수정/삭제/이동하지 않음

---

## 2. Repo / Branch / Worktree State

### 2.1 Main Worktree

| 항목 | 값 |
|---|---|
| Root | `C:/Users/computer/Desktop/ICLR_WM_claude-code` |
| Branch | `solo/p3-final-boss-cleared` |
| HEAD | `ba204a8` (feat(p3-eval): fix B1/B2 blockers → P3_EVAL.passed issued) |
| Tracked status | clean |
| Untracked | `plans/P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md` (1개) |
| Remote | `origin = https://github.com/G-Woong/world_model_testing.git` |

### 2.2 Codex Worktree

| 항목 | 값 |
|---|---|
| Path | `C:/Users/computer/Desktop/ICLR_WM_codex` |
| Branch | `codex-work` |
| HEAD | `a55cb33` (feat(p3-eval-b2): TextFRCGModelAgent wrapper for FRCG-FULL evaluation) |
| Status | clean |
| `.git/worktrees/` metadata | 정상, orphaned/stale 없음 |
| Main HEAD 대비 | 2 commit 뒤 (merge `3b178fa` + fix `ba204a8` 미반영) |

**주의**: Codex HEAD가 Main HEAD보다 2 commit 뒤에 있음. 다음 task 시작 전 fast-forward 필요 (drift는 아니지만 사전 동기화 권장).

### 2.3 Remote & Branch Graph

로컬 브랜치:
- `main`
- `solo/p3-final-boss-cleared` (현재)
- `codex-work`

원격 잔재:
- `origin/feat/p1-schema-visibility` — **NEEDS_CONFIRMATION**: P1 완료 후 폐기됐는지 확인 필요

### 2.4 NEEDS_CONFIRMATION 항목

| 항목 | 이유 |
|---|---|
| `plans/P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md` (untracked) | git add/commit 여부 미결. Phase 1에서 손대지 않음 — `02_CLEANUP_CANDIDATES.md` REVIEW_LATER 분류 |
| `origin/feat/p1-schema-visibility` | P1 schema/visibility gate 후 폐기 여부 불명. 삭제 전 사용자 확인 필요 |
| `solo/p3-final-boss-cleared` 유지 여부 | Phase 2에서 orchestration 기준 branch 신설 여부 결정 필요 |

---

## 3. Top-level Inventory

| Path | 유형 | 크기/수량 | 비고 |
|---|---|---|---|
| `CLAUDE.md` | docs | 4.2 KB | First-rule + scientific rules + execution order. 절대 보호 |
| `README.md` | docs | 2.0 KB | 프로젝트 개요 |
| `.claude/` | config | 하위 7개 서브디렉터리 | settings.json / settings.local.json / agents/ / commands/ / hooks/ / rules/ / skills/ |
| `.mcp.json` | config | 115 B | context7 단일 HTTP MCP, 무인증 |
| `.agent_tasks/` | workflow | 총 170+ 파일 | codex_queue(22) + codex_done(15 RESULT) + codex_archive/p3_impl(6) + codex_logs(66) + codex_prompt_template.md |
| `.venv/` | env | 거대 | .gitignore 제외. 내용 미열람 |
| `configs/` | config | 7 YAML | ablation_core, data_collection_text, data_collection_viz, eval_text, model_text, text_smoke, train_text |
| `data/frcgw_text/v0_1/` | data | jsonl 3종 + metadata | train/valid/test_id + manifest.json + audits/ + metadata. 절대 보호 |
| `docs/` | docs | 신규: orchestration/ | orchestration/ 이전엔 사실상 비어있음 (README 1개만 1979 B) |
| `outputs/` | output | phase_gates 5+1 + runs + 빈 3개 | phase_gates/: P1, P1.5, P2, P3, P3_EVAL.passed + .gitkeep |
| `paper_context_ref/` | source-of-truth | 18개 md | 총 ~1 MB. **절대 DELETE 후보 금지** |
| `plans/` | docs | 12개 md | P0/P2/P3 historical + gate reports + PHASE_PROGRESS + P4 recovery |
| `scripts/` | code | 11개 | `00..09_*.py` 10개 + `run_codex_task.ps1` (29.5 KB harness) |
| `src/frcgw/` | code | 13개 subpackage | 4개(gui_env, logging, reporting, utils)는 `__init__.py`만 있는 stub |
| `tests/` | tests | 27개 파일 | 절대 보호 |
| `src/frcgw.egg-info/` | build | auto-generated | cleanup 후보 |
| `.pytest_cache/` | cache | auto-generated | cleanup 후보 |

---

## 4. Source-of-truth Map

### 4.1 paper_context_ref/ (18 docs, 절대 보호)

| 파일 | 역할 |
|---|---|
| `00_CONTEXT_INDEX.md` | First-rule: 모든 작업 전 읽는 라우터 |
| `00_MASTER_REFERENCE.md` | Core thesis/ref ledger |
| `01_RELATED_WORK_THREAT_MAP.md` | Related work threats |
| `02_PROBLEM_NOVELTY_FALSIFICATION.md` | Problem/novelty/falsification |
| `03_CORE_CONCEPT_TAXONOMY.md` | Concepts/taxonomy |
| `04_TEXT_ONLY_SMOKE_TESTBED.md` | Text-only smoke test |
| `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` | Synthetic Web/GUI env |
| `06_DATA_SCHEMA_AND_LABELING.md` | Schema/leakage/labels |
| `07_LATENT_ARCHITECTURE_DESIGN.md` | Architecture |
| `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | Loss/reward/objective |
| `09_PLANNING_THEORY_ALGORITHM.md` | Planning/theory |
| `10_EVALUATION_BASELINE_ABLATION.md` | Evaluation/baseline/ablation |
| `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md` | Scale/budget |
| `12_DATA_COLLECTION_METHODOLOGY.md` | Data collection |
| `13_CLAUDE_CODE_EXECUTION_ROADMAP.md` | Claude execution roadmap |
| `14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md` | TRD requirements |
| `15_TDD_TECHNICAL_DESIGN_DOCUMENT.md` | TDD design |
| `FINAL_RESEARCH_BLUEPRINT.md` | Final blueprint |

### 4.2 CLAUDE.md + .claude/rules/

| 파일 | 역할 | 우선순위 |
|---|---|---|
| `CLAUDE.md` | First rule + scientific contract | Base |
| `.claude/rules/research_context_rules.md` | Scientific/data non-negotiables | CLAUDE.md와 동급 |
| `.claude/rules/codex_orchestration_rules.md` | Codex = default 구현자, orchestration 정책 | CLAUDE.md보다 구체적이어서 orchestration 상 우선 |

### 4.3 outputs/phase_gates/ (5 sentinels)

| Sentinel | 의미 |
|---|---|
| `P1.passed` | Phase 1 (docs/scaffold) 완료 |
| `P1.5.passed` | Phase 1.5 (plugin/skill/agent/hook pipeline) 완료 |
| `P2.passed` | Phase 2 (schema/visibility) 완료 |
| `P3.passed` | Phase 3 (text-only model/training) 완료 |
| `P3_EVAL.passed` | Phase 3 Eval gate 완료 (가장 최근) |

### 4.4 configs/ + data/frcgw_text/v0_1/

- `configs/` 7 YAML: 실험·훈련·평가 하이퍼파라미터 원본. 절대 보호.
- `data/frcgw_text/v0_1/`: train/valid/test_id jsonl + manifest.json + audits/. 절대 보호.

---

## 5. Code & Test Surface

### src/frcgw/ — 13개 subpackage

| Subpackage | 상태 | 비고 |
|---|---|---|
| `schemas/` | 구현됨 | visibility/forbidden field 정의 포함 |
| `text_env/` | 구현됨 | P2/P3 data collection 완료 |
| `data/` | 구현됨 | dataloader, collator |
| `models/` | 구현됨 | P3 text model |
| `objectives/` | 구현됨 | P3 loss/objective |
| `planning/` | 구현됨 | P3 gate/rewrite planner |
| `training/` | 구현됨 | P3 train loop |
| `evaluation/` | 구현됨 | P3 eval runner + metrics |
| `gui_env/` | **STUB** | `__init__.py`만, P4 이후 채워질 자리 |
| `logging/` | **STUB** | `__init__.py`만, P4 이후 채워질 자리 |
| `reporting/` | **STUB** | `__init__.py`만, P4 이후 채워질 자리 |
| `utils/` | **STUB** | `__init__.py`만, P4 이후 채워질 자리 |

### scripts/ — 11개

- `00_setup_environment.py` ~ `09_generate_eval_report.py`: phase별 실행 스크립트
- `run_codex_task.ps1`: Codex 오케스트레이션 harness (29.5 KB, source-of-truth)

### tests/ — 27개 파일

절대 보호. Phase 2에서 coverage 변경 없음.

---

## 6. Stub vs Implemented

P4 이후 채워질 stub 4개 패키지 (`gui_env`, `logging`, `reporting`, `utils`)는 의도적 placeholder. 삭제 금지.

---

## 7. Outputs & Run Artifacts

| Path | 내용 | 보호 여부 |
|---|---|---|
| `outputs/phase_gates/` | 5 sentinel + .gitkeep | **절대 보호** |
| `outputs/runs/p3_ablations/` | P3 ablation 결과 | **절대 보호** |
| `outputs/runs/p3_eval/` | P3 eval 결과 | **절대 보호** |
| `outputs/runs/p3_smoke/` | P3 smoke 결과 (checkpoint_ep0.pt 18 MB 포함) | **절대 보호** (LFS 여부 REVIEW_LATER) |
| `outputs/eval_reports/` | `.gitkeep`만 | cleanup 후보 (empty placeholder) |
| `outputs/review_reports/` | `.gitkeep`만 | cleanup 후보 (empty placeholder) |
| `outputs/test_reports/` | `.gitkeep`만 | cleanup 후보 (empty placeholder) |

---

## 8. Anomalies & Risk Items

| ID | 위치 | 내용 | 심각도 |
|---|---|---|---|
| A1 | `.agent_tasks/codex_queue/` | 7쌍 중복 TASK 파일: `TASK_1007..1011`, `TASK_1017..1018` (원본) vs `TASK_1012..1016`, `TASK_1019..1020` (재번호 버전, RESULT 존재) | MED |
| A2 | `.claude/settings.local.json` | `NeurIPS2026_claude-code`·`NeurIPS2026_codex`·`NeurIPS2026` 경로 다수 (현재 프로젝트와 무관) | MED |
| A3 | `.claude/settings.local.json` | `enableAllProjectMcpServers: true` (미래 MCP 자동 허가) | HIGH |
| A4 | `.claude/settings.local.json` | `Skill(update-config)` allow (agent 자가 수정 통로) | HIGH |
| A5 | `.claude/settings.local.json` | `Bash(cmd *)`, `Bash(powershell *)` 무제한 wildcard | HIGH |
| A6 | `.agent_tasks/codex_queue/` | 원본 TASK 1007-1011, 1017-1018 — RESULT가 재번호 버전(1012-1016, 1019-1020)에만 존재. 원본은 orphaned | MED |
| A7 | `.claude/hooks/` | `session_start_context.ps1` 파일 존재하나 `settings.json`에 미등록 | LOW |
| A8 | `outputs/runs/p3_smoke/` | `checkpoint_ep0.pt` 18 MB binary — git LFS 사용 여부 불명 | REVIEW_LATER |
| A9 | `plans/` | `plans/P3_FINAL_EVAL_AND_P4_GUI_MVE_PLAN.md`, `plans/P0_REPO_SCAFFOLD_PLAN.md` 등에 `NeurIPS2026` 잔재 | LOW |

---

## 9. Open Questions for Phase 2

1. **Branch 전략**: `solo/p3-final-boss-cleared`를 계속 쓸지, Phase 2용 orchestration 기준 branch를 새로 만들지 결정 필요.
2. **Codex HEAD 동기화**: 다음 task 시작 전 `codex-work`를 fast-forward할 절차 확립 필요.
3. **`origin/feat/p1-schema-visibility`**: 원격 branch 삭제 여부 — 사용자 확인 필요.
4. **`plans/P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md`**: untracked 파일 처리 — add/commit/archive/삭제 중 선택 필요.
5. **`outputs/runs/p3_smoke/checkpoint_ep0.pt`**: git LFS 설정 여부 또는 .gitignore 추가 여부 결정 필요.
6. **빈 placeholder 디렉터리** (`eval_reports/`, `review_reports/`, `test_reports/`): Phase 4에서 쓰일 자리인지 지금 정리할지 결정 필요.
7. **`session_start_context.ps1`**: settings.json에 등록할지, 파일 제거할지 결정 필요.
