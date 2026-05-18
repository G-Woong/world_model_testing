# STEP 10 Test-First Loop Protocol

date: 2026-05-18
gate: O-CODEX
source: 01_global_risk_register.md, 04_claim_redefinition.md

---

## 11-Step Loop Protocol

```
LOOP iteration N (for each CRITICAL/HIGH risk):

  1. Pick risk from register (priority = severity × paper-impact)
     - Pick from 01_global_risk_register.md, Status=OPEN
     - Prefer CRITICAL first, then HIGH

  2. Extract idea from literature/architecture/loss/eval bank
     - 05_architecture_candidate_matrix.md P0 candidates
     - 06_loss_objective_search.md P0 candidates
     - 07_evaluation_redesign.md P0 metrics

  3. Convert idea to testable hypothesis:
     - Observable metric (e.g., AUROC, action divergence rate)
     - Expected effect size (e.g., AUROC > 0.65)
     - Null hypothesis (no effect: AUROC ≈ 0.5)
     - Falsification condition (when to REJECT)

  4. Define minimal test (smallest valid eval/train run):
     - eval: n=100 episode smoke run
     - train: Stage B fine-tune, ≤200 steps
     - prefer: test against existing Stage B checkpoint first

  5. Write Codex task (10-field schema)
     - All 10 required fields (see schema below)
     - RELATED_AGENT_REPORT_IDS if T3 needed
     - No research judgment clause (mandatory)

  6. Run Codex via scripts/run_codex_task.ps1 -Mode run -BypassSandbox
     - Confirm SANDBOX_MODE: bypass in task file
     - Monitor for forbidden path violations

  7. Claude verification (6 conditions must ALL pass):
     a. verify exit 0
     b. git diff --cached --stat 수동 review — 의도치 않은 변경 없음
     c. RESULT.md 존재 확인 (.agent_tasks/codex_done/TASK_N_NAME_RESULT.md)
     d. REQUIRED_TESTS pytest 재실행
     e. T3 impl-risk-critic agent report PASS
     f. forbidden path 미수정 확인

  8. Claude runs test/eval
     - python scripts/10_run_lr_real_eval.py --config configs/...
     - or: pytest -q tests/test_step10_<topic>.py

  9. Compare against baseline (prior checkpoint or Stage B)
     - Stage B checkpoint: outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt
     - Metric delta: new - baseline

  10. Decision:
      KEEP    : metric improvement > 5% AND no leakage AND novelty preserved
      MODIFY  : 0-5% improvement → refine hypothesis and re-loop (max 2 iterations)
      REJECT  : ≤0% improvement OR leakage OR regression in other claims
      BLOCKED : cannot test due to dependency → document blocker with evidence

  11. Write loop_report (docs/orchestration/risk_hunt/loop_reports/09_loop_{N}_{topic}.md)
      11 fields (see below)
```

---

## Codex Task 10-Field Schema

All Codex tasks MUST have these 10 fields:

```
1. TASK_NAME:          TASK_<N>_step10_<topic>
2. SANDBOX_MODE:       bypass  ← REQUIRED for -BypassSandbox
3. BACKGROUND:         context (1-3 sentences)
4. GOAL:               what to build (numbered list)
5. FILES_ALLOWED:      whitelist (explicit paths)
6. FILES_FORBIDDEN:    .claude/, CLAUDE.md, .mcp.json, .venv/, data/, outputs/phase_gates/,
                       outputs/checkpoints/, outputs/runs/, secrets/, .env,
                       scripts/run_codex_task.ps1, paper_context_ref/,
                       src/frcgw/schemas/visibility.py (+ additional forbidden per task)
7. REQUIRED_IMPLEMENTATION: pseudo-code or signature level spec
8. REQUIRED_TESTS:     pytest path + expected pass count
9. ACCEPTANCE_CRITERIA: pytest GREEN + JSON schema valid + no forbidden path
10. COMMIT_MESSAGE:    feat/fix(step10): ...
11. STOP_CONDITION:    abort triggers

Optional field (T3 trigger):
RELATED_AGENT_REPORT_IDS:  docs/orchestration/agent_reports/YYYY-MM/impl_risk_<TASK>_R<n>.md
```

**Mandatory no-research-judgment clause** (all tasks must include in STOP_CONDITION):
```
Codex must not modify claim wording, metric definition, baseline list, or ablation list.
Codex must not edit docs/orchestration/lr_alignment/*.md or paper_context_ref/*.md.
If task ambiguity arises, emit BLOCKED status in RESULT.md, do not guess.
```

---

## Loop Report 11-Field Schema

```
File: docs/orchestration/risk_hunt/loop_reports/09_loop_{N}_{topic}.md

Field 1: Risk addressed (RH-ID from 01_global_risk_register.md)
Field 2: Idea tested (architecture/loss/eval candidate ID)
Field 3: Literature inspiration (source IDs from 02_literature_threat_and_idea_bank.md)
Field 4: Implementation summary (Codex task IDs + accepted/rejected)
Field 5: Dataset used (v0_4 test_id/test_ood/smoke + episode count)
Field 6: Metric used (from 07_evaluation_redesign.md Metric #N)
Field 7: Result (number with seed or CI: e.g., AUROC=0.72±0.03, n=5)
Field 8: Failure analysis (if REJECT/MODIFY: root cause analysis)
Field 9: Decision (KEEP / MODIFY / REJECT / BLOCKED_WITH_EVIDENCE)
Field 10: Next action (follow-up if MODIFY, or gate update if KEEP)
Field 11: Commit SHA (final accepted commit for this loop)
```

---

## Decision Criteria (Quantitative)

| Decision | Condition |
|---|---|
| KEEP | primary metric > 5% improvement vs baseline AND no leakage AND no regression in other claims |
| MODIFY | 0-5% improvement OR partial improvement → refine hypothesis, max 2 iterations total |
| REJECT | ≤0% improvement OR leakage detected OR regression > 2% in another claim |
| BLOCKED_WITH_EVIDENCE | test cannot be executed: data missing, environment unsupported, dependency unresolved |

**Regression definition**:
- C3 F1 regression: new_F1 < baseline_F1 - 0.02
- C6 ppc regression: new_ppc < baseline_ppc × 0.9

---

## Loop Priority Queue (STEP 9)

| Loop | Risk | Priority | Codex Task | Gate |
|---|---|---|---|---|
| Loop-01 | RH-CORE-01 (threshold/proxy) | 1 | TASK_1131 | proxy OFF → F1 measurement |
| Loop-02 | RH-STAT-01 (n=5 multiseed) | 2 | TASK_1129 | std > 0.01 on training seeds |
| Loop-03 | RH-FAI-01 (ABL-001/003) | 3 | TASK_1127, TASK_1128 | expected collapse |
| Loop-04 | RH-FORE-01 (foresight-policy) | 4 | TASK_1124, TASK_1118 | divergence rate > 5% |
| Loop-05 | RH-DUP-01 (v0_5) | 5 | TASK_1130 | regime_shift_f1 > 0 |
| Loop-06 | RH-EVAL-02 (fair compute) | 6 | TASK_1125, TASK_1132 | fair ppc ratio > 2× |
| Loop-07 | RH-THR-02 (calibration) | 7 | TASK_1121 | ECE < 0.025 |
| Loop-WH-1 | RH-CORE-01 (CLT) | 8 (wild) | TASK_1122 | AUROC > 0.7 |

Minimum 3 loops must be completed before Gate O-LOOP.

---

## Safety Invariants (Every Loop)

1. `tests/test_forbidden_field_mirror_sync.py` GREEN after every code change
2. `tests/test_visibility_contract.py` GREEN after every schema change
3. `hidden_label_leakage_count = 0` in every eval run
4. `fake_metric_count = 0` in every eval run
5. `forbidden_wording_count = 0` in every loop report
6. ABL-040 recall=1.000 check in regression suite

---

## Gate O-CODEX Status

| 조건 | 상태 |
|---|---|
| 11-step loop protocol 명문화 | ✓ |
| 10-field Codex task schema 명시 | ✓ |
| loop report 11-field 명시 | ✓ |
| decision criteria 양적 기준 | ✓ |
| loop priority queue 8개 | ✓ |
| safety invariants 명시 | ✓ |

**Gate O-CODEX: PASS**
