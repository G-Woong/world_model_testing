# P3 Final Evaluation & P4 GUI MVE Plan

> 실행 단계 복사본 (원본: Plan Mode 출력).
> branch: solo/p3-final-boss-cleared, 복사일: 2026-05-13

---

## Context

현재 `solo/p3-final-boss-cleared` branch는 commit `cd6d3a3 feat(p3): P3 gate PASS - tiny text FRCG model complete`에서 **P3 implementation gate** PASS sentinel (`outputs/phase_gates/P3.passed`)을 발행했다. `pytest -q`는 174 tests green. Codex worktree에서 C1~C7 sub-task 7개가 완료되어 `src/frcgw/{models,objectives,planning,training}` 구현이 끝났다.

그러나 이 PASS는 **"tiny FRCG text model code + smoke train"** 수준의 implementation gate일 뿐이다. `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md:478~483`이 정의하는 **CC-P3 evaluation gates (G1~G5)** — verifier-only/uncertainty-gated 비교, no-control-grammar/no-falsification ablation 검증 — 은 한 건도 실행되지 않았다.

- `src/frcgw/evaluation/__init__.py:6` — `__all__: list[str] = []`, "implementation deferred to P3/P6"
- `scripts/03_eval_text_smoke.py` — `raise NotImplementedError("CC-P3: implementation deferred")`
- `scripts/08_run_core_ablations.py` — `raise NotImplementedError("CC-P6: implementation deferred")`
- `configs/eval_text.yaml`, `configs/ablation_core.yaml` — 모든 값 `null` (P0 skeleton). `ablation_core.yaml`은 12 ablation 이름만 list로 보유.

따라서 본 계획은 **P3 마무리 = Step 7 evaluation/ablation 실행**을 먼저 정의하고, 그 gate가 정성적으로 PASS할 때에만 **P4 synthetic GUI MVE**로 진입하도록 분기 구조를 설계한다. P3 evaluation이 FAIL이면 P4가 아니라 `plans/P3_EVAL_FAILURE_DEBUG_PLAN.md` 작성으로 분기한다.

부가적 결정 사항:
- **PASS 기준은 정성적(qualitative)** — 04.md:500~510의 후보 수치(≥25% failed-repetition 감소, ≥15% recovery delay 감소, ≥10% progress/compute)는 보고서에 기록만 하고 hard gate로 쓰지 않는다 (MD가 "후보값, 최종 주장 아님" 명시).
- **Codex harness 우선 수정** — Sonnet이 P3 eval Codex 위임 직전에 `scripts/run_codex_task.ps1` line 60의 `$CLAUDE_BRANCH = 'feat/p1-schema-visibility'` 하드코딩을 `-ClaudeBranch` 파라미터로 받도록 바꾸고, untracked `TASK_C2~C7_*.md` 6개 stale 사본을 archive 한다.

---

## 1. Read Context

### Always-first
- `CLAUDE.md`
- `paper_context_ref/00_CONTEXT_INDEX.md` §5 (phase gate)
- `.claude/rules/codex_orchestration_rules.md`
- `.claude/rules/research_context_rules.md`

### P3 evaluation bundle
- `paper_context_ref/03_CORE_CONCEPT_TAXONOMY.md`
- `paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md` (§splits, §scenarios, §gates)
- `paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md`
- `paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md` (L_falsification, L_calibration)
- `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md` (decision-gate variants, baseline defs)
- `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md` (§7 BASE-001~028, §8 ABL-001~042, §metrics)
- `paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md` (compute budget, episode counts, seeds)
- `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md` §10 CC-P3 (lines 460~485)
- `paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md` §P3 acceptance
- `paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md` §evaluation (lines 974~1058)

### P4 GUI MVE bundle (P3 PASS 후에만)
- `paper_context_ref/05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` (ACT-001~015, GRAM-001~021, EVT-001~010)
- `paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md` §4 visibility contract
- `paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md` (CA-001~010 coverage)
- `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md` §11 CC-P4

---

## 2. Current Repository / Worktree Inspection

실행 시점 기준 상태:
- Branch: `solo/p3-final-boss-cleared`
- P2.passed: ✓, P3.passed: ✓
- Codex worktree: `C:/Users/computer/Desktop/NeurIPS2026_codex` at `codex-work`
- Stale TASK_C{2..7}_*.md 6개 → archive됨
- outputs/runs/: 없음 (eval runner가 fresh checkpoint 생성 예정)

---

## 3. P3 Implementation Completion Check

확인 완료된 사실:

| 항목 | 상태 |
|---|---|
| `src/frcgw/models/{encoders,latent_heads,text_frcg_model,world_model_heads}.py` | present, source MD docstring 인용 OK |
| `src/frcgw/objectives/{losses,rewards}.py` | present, L-MAIN-001~006 + L-AUX-001~005 인용 |
| `src/frcgw/planning/{falsification,alternative_proposer,decision_gate,rewrite,planner}.py` | present, FALS-02/PROP-03/G_hybrid/RW-02/RW-06/§12 인용 |
| `src/frcgw/training/{train_text,monitoring}.py` | present |
| `tests/test_{text_frcg_model,falsification,decision_gate,rewrite,train_text_smoke,losses}.py` | 모두 PASS |
| `pytest -q` | 174 passed, 0 failed |
| `data/frcgw_text/v0_1/manifest.json` | 200 episodes (train 132 / valid 35 / test_id 33), coverage/leakage gate PASS |
| `plans/P3_GATE_REPORT.md` | C1~C7 PASS sentinel 발행됨 (단, implementation gate임) |
| `paper_context_ref/` | unmodified |

결론: **implementation gate PASS는 진짜**. 그러나 evaluation gate는 §4부터 새로 만든다.

---

## 4. P3 Evaluation / Ablation Scope

Step 7 = `CC-P3 evaluation` (paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §10).

### 구현 대상 (TDD 15.md:974~1058 인용)

| 파일 | 책임 |
|---|---|
| `src/frcgw/evaluation/metrics.py` | 10 metric 함수 (15.md:976~991) |
| `src/frcgw/evaluation/baselines.py` | 11 baseline agent class (15.md:993~1009) |
| `src/frcgw/evaluation/ablations.py` | 12 ablation ID + model masking interface (15.md:1011~1029) |
| `src/frcgw/evaluation/compute_budget.py` | `ComputeBudgetLog` dataclass (15.md:1032~1042) |
| `src/frcgw/evaluation/eval_runner.py` | `EvaluationRunner.run(model_or_agent, dataset, config)` (15.md:1044~1058) |
| `configs/eval_text.yaml` | seed: [0,1,2,3,4], splits: text_id/text_ood_grammar/text_noisy, metrics: 10개, compute_budget: matched |
| `configs/ablation_core.yaml` | 기존 12 ablation ID + 효과 가설 expected_collapse |
| `scripts/03_eval_text_smoke.py` | text_id baseline 비교 + report writer |
| `scripts/08_run_core_ablations.py` | CRITICAL ablation 12개 sweep + report writer |
| `tests/test_metrics.py` | metric 단위 테스트 |
| `tests/test_baselines.py` | 각 baseline agent forward + compute log |
| `tests/test_eval_runner.py` | runner integration + hidden label assertion |
| `tests/test_ablation_runner.py` | ablation masking + expected_collapse 방향성 |
| `tests/test_compute_budget.py` | budget log invariants |
| `plans/P3_EVAL_GATE_REPORT.md` | metric_summary + ablation_summary + failure_cases + compute_budget |
| `outputs/phase_gates/P3_EVAL.passed` | sentinel (정성적 PASS 시) |

### 금지 사항 (P3 eval 단계에서)
- VLM/GUI 코드 작성 금지 (P4 영역)
- 새 dataset shard 생성 금지 (기존 `data/frcgw_text/v0_1/` 재사용)
- placeholder metric을 report에 쓰지 마라 (14.md:138 SYS-REQ-009)
- hidden label / counterfactual / oracle 필드를 eval batch input에 포함시키지 마라
- `paper_context_ref/` 수정 금지

---

## 5. P3 Evaluation Algorithm and Metrics

### 5.1 Metric 정의 (10.md 인용)

| Metric | 정의 | source |
|---|---|---|
| task_success_rate | `#success / #episodes` | 10.md:151 |
| normalized_return | `(return - task_min)/(oracle_or_task_max - task_min)` | 10.md:152 |
| wrong_control_grammar_persistence | `t(correct_grammar_switch) - t(first_falsifying_evidence)` per episode → mean | 10.md:155 |
| failed_action_repetition_rate | `repeated same intent+invalid mapping / failure opportunities` | 10.md:157 |
| recovery_delay | `t(progress_delta>0) - t(falsifying_evidence)` per episode → mean | 10.md:160 |
| falsification_precision_recall | `TP_wrong_current` 기반 PR | 10.md:167~168 |
| falsification_calibration | ECE (10 bins, predicted vs empirical wrong prob) | 10.md:169 |
| progress_per_compute | `sum(progress_delta) / (planning_calls + rollout_steps)` | 10.md:178 |
| false_planning_call_rate | `#plans_without_action_or_progress_change / total_plans` | 10.md:179 |
| action_switch_delay | `t(rewrite) - t(evidence)` | 10.md:159 |

### 5.2 Compute-matched 정의

`compute_budget.ComputeBudgetLog`:
```python
@dataclass(frozen=True)
class ComputeBudgetLog:
    planning_calls: int
    rollout_steps: int
    candidate_actions_scored: int
    top_k_alternatives: int
    wall_clock_seconds: float
```

### 5.3 Splits
`text_id` (main), `text_ood_grammar`, `text_noisy` — 04.md:266, 511. text_ood_task는 P3 단계에서 optional.

### 5.4 Seeds
`seeds: [0, 1, 2, 3, 4]` — 10.md:628.

---

## 6. P3 Baselines and Ablations

### 6.1 필수 Baseline (must-not-disappear)

1. **FrozenBaseAgent** — BASE-001
2. **ReactiveAgent** — BASE-002
3. **RetryAfterFailureAgent** — BASE-003
4. **VerifierOnlyAgent** — BASE-005 **← CC-P3-G1 비교 대상**
5. **NextStateWMOnlyAgent** — BASE-009
6. **AlwaysPlanAgent** — BASE-010
7. **UncertaintyGatedAgent** — BASE-012 **← CC-P3-G2 비교 대상**
8. **RandomAlternativePlannerAgent** — BASE-014
9. **OracleRegimeAgent** / **OracleControlGrammarAgent** — BASE-016/017 (upper bound)

### 6.2 필수 Ablation CRITICAL

| ablation_id | expected_collapse |
|---|---|
| no_control_grammar (ABL-002, CRITICAL) | persistence ↑, OOD grammar ↓ **← CC-P3-G3** |
| merged_regime_control_grammar (ABL-003, CRITICAL) | OOD recombination ↓ |
| collapsed_latent (ABL-006, CRITICAL) | mechanism metrics ↓ |
| no_falsification (ABL-016, CRITICAL) | falsification PR ↓ **← CC-P3-G4** |
| uncertainty_instead_of_falsification (ABL-023, CRITICAL) | false_planning ↑ |
| no_alternative_hypothesis (ABL-024, CRITICAL) | recovery ↓ |
| random_alternative (ABL-025) | recovery ↓ |
| no_rollout (ABL-026) | switch usefulness ↓ |
| no_rewrite (ABL-035, CRITICAL) | failed repetition ↑ |
| always_plan_no_gate (ABL-034, CRITICAL) | progress_per_compute ↓ |
| no_progress_reward (ABL-013/019) | progress error ↑ |
| no_compute_gate (ABL-033, CRITICAL) | false_planning ↑ |

---

## 7. P3 Closed-Loop Evaluation Workflow

```
[1] evaluation contract 확정 (§4~§6)
[2] harness 사전 수정 (run_codex_task.ps1 + stale TASK 정리)
[3] Codex: E1~E5 구현 (TASK_1007~1011)
[4] frcgw-test-runner: targeted tests 실행
[5] frcgw-data-leakage-auditor: eval batch input 검증
[6] scripts/03_eval_text_smoke.py + scripts/08_run_core_ablations.py 실행
[7] frcgw-experiment-evaluator: CC-P3-G1~G4 판정
[8] frcgw-code-reviewer: baseline/ablation 누락 점검
[9] pytest -q 전체, P2/P3 regression 0건
[10] plans/P3_EVAL_GATE_REPORT.md 작성
[11] 정성적 PASS 판정:
    - PASS → P3_EVAL.passed + commit
    - FAIL → P3_EVAL_FAILURE_DEBUG_PLAN.md, P4 금지
```

---

## 8. P3 Codex Delegation Plan

### 8.1 Codex 위임 5 task (TASK_1007~1011)

| TASK | 파일 |
|---|---|
| TASK_1007_E1_eval_metrics | metrics.py, compute_budget.py, tests/test_metrics.py, tests/test_compute_budget.py |
| TASK_1008_E2_baselines | baselines.py, tests/test_baselines.py |
| TASK_1009_E3_eval_runner | eval_runner.py, configs/eval_text.yaml, scripts/03_eval_text_smoke.py, tests/test_eval_runner.py |
| TASK_1010_E4_ablations | ablations.py, configs/ablation_core.yaml, scripts/08_run_core_ablations.py, tests/test_ablation_runner.py |
| TASK_1011_E5_eval_report | src/frcgw/evaluation/reporter.py (신규), tests/test_reporter.py |

### 8.2 FILES_FORBIDDEN 공통

```
paper_context_ref/
.claude/
.mcp.json
.venv/
data/
outputs/
secrets/
.env*
scripts/run_codex_task.ps1
src/frcgw/gui_env/
src/frcgw/logging/
src/frcgw/models/
src/frcgw/objectives/
src/frcgw/planning/
src/frcgw/training/
```

---

## 9. P3 Gate Criteria

### 9.1 PASS 기준 (정성적)

| Gate | 조건 |
|---|---|
| pytest | `pytest -q` 174+ passed, regression 0 |
| Leakage | FORBIDDEN_AGENT_KEYS 검증 통과, hidden/counterfactual/oracle 0건 |
| Compute log | 모든 baseline/ablation에 ComputeBudgetLog 생성 |
| CC-P3-G1 | `mean(recovery_delay) FRCG < VerifierOnly` (text_id, 5 seeds) |
| CC-P3-G2 | `mean(progress_per_compute) FRCG > UncertaintyGated` (text_id, 5 seeds) |
| CC-P3-G3 | `mean(persistence) no_control_grammar > FRCG full` (text_ood_grammar) |
| CC-P3-G4 | `mean(recovery_delay) no_falsification > FRCG full` AND `mean(falsification_recall) no_falsification < FRCG full` |
| Report | `plans/P3_EVAL_GATE_REPORT.md`가 실제 `outputs/runs/p3_*/metrics.json` 인용 |
| paper_context_ref | unmodified |

**수치 thresholds는 report에 기록만 — PASS 판정에 미사용.**

---

## 10. P4 Entry Criteria

다음이 **모두** 충족될 때에만 P4 진입:

- `outputs/phase_gates/P2.passed` exists
- `outputs/phase_gates/P3.passed` exists
- `outputs/phase_gates/P3_EVAL.passed` exists
- `plans/P3_EVAL_GATE_REPORT.md` exists (real metrics)
- G3 또는 G4 중 최소 하나 PASS
- G1 + G2 중 최소 하나 PASS
- hidden leakage: 0건
- `paper_context_ref/` unmodified

---

## 11. P4 Synthetic GUI MVE Scope

목표: 100 episode dry-run, DOM + screenshot_ref + a11y tree + action-effect log, leakage/replay/coverage gate 통과. VLM training은 P5 영역.

### 11.1 구현 대상

| 파일 | 책임 |
|---|---|
| `src/frcgw/gui_env/task_spec.py` | TaskSpec |
| `src/frcgw/gui_env/template_generator.py` | UITemplateGenerator |
| `src/frcgw/gui_env/regime_grammar_engine.py` | GRAM-001~021 |
| `src/frcgw/gui_env/event_scheduler.py` | EVT-001~010 |
| `src/frcgw/gui_env/browser_executor.py` | synthetic backend |
| `src/frcgw/gui_env/action_space.py` | ACT-001~015 |
| `src/frcgw/gui_env/collector.py` | episode collection |
| `src/frcgw/logging/action_effect_logger.py` | effect logging |
| `src/frcgw/logging/counterfactual_logger.py` | counterfactual sim (eval-only) |
| `src/frcgw/logging/replay_validator.py` | deterministic replay |

### 11.2 Task Family 10개
search form, product/list filtering, modal confirmation, nested scroll, pagination/infinite scroll, disabled submit/form validation, permission/consent gate, async loading/stale DOM, settings toggle, multi-step wizard.

---

## 12. P4 Gate Criteria

| Gate | 조건 |
|---|---|
| G1 deterministic replay | 100 episode 전수 일치 |
| G2 visibility/leakage audit | FORBIDDEN_AGENT_KEYS ⊄ agent_observation |
| G3 coverage audit | §12.3 thresholds 전부 충족 |
| G4 timestamp alignment | DOM/screenshot/a11y/action-effect 시간축 일치 |
| G5 counterfactual valid + excluded | top-k 생성 but inference batch 미포함 |
| G6 dry-run scale | 100 episode |
| pytest | full PASS, P1/P2/P3/P3_EVAL regression 0건 |

---

## 13. Commit Policy

### P3 eval PASS 후
```
feat(p3-eval): implement text model evaluation and core ablations
```

### P4 PASS 후
```
feat(p4): implement synthetic GUI MVE data collection dry-run
```

### 금지
- `data/` shard commit 금지 (manifest만)
- `outputs/runs/` commit 금지 (sentinel + 요약 report만)
- model checkpoint commit 금지
- `paper_context_ref/` add 금지
- `git push` 금지 (별도 user 승인)
- `--no-verify` 금지

---

## 14. Blockers (실행 시점 기준)

- [x] `scripts/run_codex_task.ps1` line 60 하드코딩 → 수정 완료
- [x] `.agent_tasks/codex_queue/TASK_C2~C7_*.md` 6개 stale → archive 완료
- [ ] TASK_1007~1011 Codex 위임 → E1~E5 구현 필요
- [ ] P3 eval scripts 실행 필요
- [ ] P3 evaluation gate 판정 필요
