TASK_NAME: step8_c3_diagnostics

BACKGROUND:
FRCG-WM STEP 8. STEP 7 applied C3 mapping fix: planner.py::_effect_type_id and losses.py::EFFECT_TYPE_VOCAB now both recognize v0_3/v0_4 public strings ("no_state_change", "blocker_removed", "delayed_effect", "state_change", "task_complete"). However, no eval has run yet. STEP 8 requires a C3 root-cause audit script that takes a dataset + checkpoint and produces: (a) per_step F_t variance, (b) predicted_wrong diversity, (c) mapping coverage report, (d) explicit degenerate_reason if F_t variance=0.

Also, scripts/10_run_lr_real_eval.py must emit extended per_step trace fields so the audit can ingest eval outputs.

GOAL:
1. Add per_step trace fields to scripts/10_run_lr_real_eval.py (planner_F_t, lr_scorer_F_t, effect_type, predicted_wrong, wrong_prob, h_exec_id, h_alt_best_id, degenerate_reason) without breaking existing metric pipeline.
2. Create scripts/audit_step8_c3_root_cause.py that ingests a dataset JSONL + eval output directory (or checkpoint directly) and produces outputs/audits/step8_c3_root_cause_audit.json with:
   - planner_F_t_variance, lr_scorer_F_t_variance
   - predicted_wrong_class_counts (true_count, false_count)
   - effect_type_distribution (per string key)
   - mapping_coverage (fraction of episodes with non-short-circuit effect_type_id)
   - degenerate_reason: one of "zero_short_circuit", "mapping_miss", "both_traces_zero", "model_untrained", "non_degenerate"
   - c3_status: "READY_CANDIDATE", "PRELIMINARY_PLUS", "BLOCKED", "PIVOT_REQUIRED"
3. Create tests/test_step8_c3_trace_integrity.py with ≥3 passing tests:
   - test_trace_fields_present: verify per_step trace has all 7 required fields
   - test_degenerate_reason_explicit: audit produces explicit reason when F_t_variance=0
   - test_mapping_coverage_non_zero: audit detects when all episodes short-circuit

FILES_ALLOWED:
- scripts/10_run_lr_real_eval.py
- scripts/audit_step8_c3_root_cause.py (NEW)
- tests/test_step8_c3_trace_integrity.py (NEW)
- .agent_tasks/codex_done/TASK_1078_step8_c3_diagnostics_RESULT.md

FILES_FORBIDDEN:
- src/frcgw/schemas/visibility.py
- src/frcgw/schemas/step_schema.py
- paper_context_ref/**
- .claude/**
- scripts/run_codex_task.ps1
- outputs/**
- data/**
- *.pt

REQUIRED_IMPLEMENTATION:
scripts/10_run_lr_real_eval.py:
- In per-step trace output (wherever EvaluationResult or step_trace is built), add fields:
  planner_F_t: float (from PlanMetadata.F_t if available, else 0.0)
  lr_scorer_F_t: float (from lr_scorer output if available, else 0.0)
  effect_type: str (last effect_summary from public_obs.history_public[-1].effect_summary)
  predicted_wrong: bool | None (from eval labels if present, else None — do NOT use true_wrong_hypothesis at inference)
  wrong_prob: float (from model output wrong_prob if available, else 0.0)
  h_exec_id: int (PlannerState.get_current(step_idx))
  h_alt_best_id: int | None (from PlanMetadata.h_star if available, else None)
  degenerate_reason: str | None (filled by audit script, NOT at eval time)
- These fields MUST be added to per_step trace dict; existing metric computation must NOT change.
- FORBIDDEN: do NOT read true_wrong_hypothesis or any FORBIDDEN_AGENT_KEY into per_step trace.

scripts/audit_step8_c3_root_cause.py:
- Args: --dataset (JSONL path), --checkpoint (optional .pt path or None), --eval-dir (optional dir with per_step trace JSONLs), --out (output JSON path)
- Reads eval per_step trace or runs inference directly
- Computes F_t variance for both planner_F_t and lr_scorer_F_t traces
- Computes predicted_wrong class counts from per-step trace
- Computes effect_type_distribution from per-step trace
- Computes mapping_coverage = fraction of steps where effect_type NOT in {"none", "no_state_change"} (i.e., not short-circuit)
- Assigns degenerate_reason by priority:
  1. If mapping_coverage < 0.05 → "zero_short_circuit"
  2. If both F_t variances < 1e-6 AND mapping_coverage >= 0.05 → "mapping_miss"
  3. If both F_t variances < 1e-6 → "both_traces_zero" (may be "model_untrained")
  4. Else → "non_degenerate"
- Assigns c3_status:
  - "READY_CANDIDATE": max(planner_F_t_variance, lr_scorer_F_t_variance) > 0.01 AND both predicted_wrong classes present
  - "PRELIMINARY_PLUS": max variance > 1e-6 OR one predicted_wrong class present
  - "BLOCKED": degenerate_reason != "non_degenerate" after Stage B training
  - "PIVOT_REQUIRED": left to Claude to set manually after Stage B eval
- Writes JSON to --out path (create parent dirs)
- Audit script must NOT import or use FORBIDDEN_AGENT_KEYS

tests/test_step8_c3_trace_integrity.py:
- 3 focused unit tests using mock data
- No real checkpoint or dataset required
- All tests must pass via: python -m pytest tests/test_step8_c3_trace_integrity.py -q

REQUIRED_TESTS:
- tests/test_step8_c3_trace_integrity.py: all 3 tests green
- existing tests: python -m pytest tests/test_lr_real_eval_runner.py tests/test_forbidden_field_mirror_sync.py -q (must stay green)

ACCEPTANCE_CRITERIA:
1. scripts/audit_step8_c3_root_cause.py exists and can be imported without error
2. per_step trace in 10_run_lr_real_eval.py has all 7 fields (verified by test)
3. Audit produces degenerate_reason explicitly when F_t_variance=0 (verified by test)
4. FORBIDDEN_AGENT_KEYS never appear in per_step trace (verified by leakage guard test)
5. All 3 new tests green
6. Pre-existing tests for eval runner still green

COMMIT_MESSAGE:
feat(step8/task1): C3 trace hardening + root-cause audit script

STOP_CONDITION:
Stop if: (a) cannot add trace fields without breaking EvaluationResult schema, (b) audit script requires true_wrong_hypothesis at inference (LEAKAGE — BLOCKED). Report as blocker.

RELATED_AGENT_REPORT_IDS: math_critic_step8_c3_gradient_R1, claim_metric_step8_alignment_R1
