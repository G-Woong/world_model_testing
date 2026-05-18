TASK_NAME: step8_full_eval_harness
SANDBOX_MODE: bypass

BACKGROUND:
FRCG-WM STEP 8. Need a full evaluation report harness that: (a) aggregates 11 inference-time ablations + ABL-025 + ABL-026 (newly added based on agent audit) + direct baselines + FRCG-LR across n=5 seeds × test_id + test_ood, (b) isolates ABL-040 in positive_control bucket, (c) verifies ABL-040 injection propagates to metric output (injection validation test). The harness does NOT execute training — it aggregates from per-seed eval runs.

STEP 8 team agent audit (exp_design_step8_v04_ablation_R1) identified that ABL-025 (random-alternative) and ABL-026 (no-rollout) have NO runners in STEP 7 or STEP 8 plans, violating CLAUDE.md requirement that "random-alternative" and "no-rollout" families must have ≥1 runner each.

GOAL:
1. Create scripts/run_step8_full_eval_report.py that aggregates eval outputs and computes n=5 stats.
2. Verify ABL-025 (random_alternative) and ABL-026 (no_rollout) are in ABLATION_REGISTRY — add them if missing.
3. Verify ABL-040 positive control injection test: add a test that `LeakageSanityProbeAblation` produces different `selected_hypothesis_id` flow than base agent.
4. Create tests/test_step8_full_eval_report.py.

FILES_ALLOWED:
- scripts/run_step8_full_eval_report.py (NEW)
- src/frcgw/evaluation/ablations.py (Edit: add ABL-025, ABL-026 if missing; add ABL-040 injection validation)
- tests/test_step8_full_eval_report.py (NEW)
- .agent_tasks/codex_done/TASK_1081_step8_full_eval_harness_RESULT.md

FILES_FORBIDDEN:
- src/frcgw/schemas/visibility.py
- src/frcgw/schemas/step_schema.py
- outputs/**
- data/**
- paper_context_ref/**
- .claude/**
- scripts/run_codex_task.ps1
- *.pt

REQUIRED_IMPLEMENTATION:
scripts/run_step8_full_eval_report.py:
- Args: --config (yaml), --agents (list of agent IDs), --out-dir (output dir), --seeds (list of ints), --splits (list)
- Does NOT execute training. Reads existing eval output JSONs from out_dir or sub-dirs.
- For each (agent_id, seed, split), reads metrics from eval run dirs: outputs/runs/p3_lr_real_eval_step8_ablations/<agent_id>_seed<S>_<split>/metrics.json
- Computes mean ± std across 5 seeds for: task_success_rate, falsification_precision, falsification_recall, ood_shift_f1, progress_per_compute, false_planning_call_rate
- ABL-040 must be in a separate "positive_control" section in output summary.json — NEVER averaged with other ablations
- Output: outputs/runs/p3_lr_real_eval_step8_full_report/summary.json with schema:
  {
    "agents": {agent_id: {"mean": {...}, "std": {...}, "n_seeds": 5, "splits": {...}}},
    "positive_control": {abl040_results},
    "metadata": {config, timestamp, commit}
  }
- Write also: outputs/runs/p3_lr_real_eval_step8_full_report/summary_human.md (text table)

src/frcgw/evaluation/ablations.py additions (if ABL-025 or ABL-026 missing):
ABL-025 (RandomAlternativeHypothesisAblation):
- description: "Random alternative hypothesis selection — selects h_alt at random instead of using falsification signal"
- tdd_ref: ABL-025, inference_time: True, expected_collapse: {falsification_precision: "decrease", recovery_delay: "increase"}
- Implementation: override _select_best_alternative() to use random.choice(alt_hypotheses)

ABL-026 (NoShortRolloutAblation):
- description: "Skip short rollout — do not roll out alternative hypothesis before committing to rewrite"
- tdd_ref: ABL-026, inference_time: True, expected_collapse: {alternative_rollout_fidelity: "decrease"}
- Implementation: override _should_rollout() to always return False

ABL-040 injection validation (add to existing LeakageSanityProbeAblation or a new test):
- The injection `self._agent._last_selected_hypothesis_id = eval_labels["true_control_grammar"]` must affect the metric output
- Add class attribute `_injection_applied_count: int = 0` to track injection events
- In act(), after injection, log one warning per injection and increment counter
- External callers can check _injection_applied_count > 0 to verify injection happened

tests/test_step8_full_eval_report.py:
- test_summary_json_schema: create mock eval output dirs + metrics.json files, run aggregation, verify summary.json has correct schema
- test_abl040_isolated: verify that when ABL-040 is in agents list, it appears ONLY in positive_control section and NOT in agents section
- test_injection_applied: create a mock LeakageSanityProbeAblation instance, call act() with eval_labels containing true_control_grammar, verify _injection_applied_count > 0
- All 3 tests must pass

REQUIRED_TESTS:
- tests/test_step8_full_eval_report.py: all 3 tests green
- existing: python -m pytest tests/test_step8_faithful_ablations.py tests/test_forbidden_field_mirror_sync.py -q (if TASK_1082 already merged)

ACCEPTANCE_CRITERIA:
1. scripts/run_step8_full_eval_report.py exists and handles missing eval dirs gracefully (returns partial summary with count_missing)
2. ABL-025 and ABL-026 appear in ABLATION_REGISTRY (or are imported/accessible from ablations.py)
3. ABL-040 positive_control isolation verified by test
4. ABL-040 injection_applied_count test passes
5. summary.json schema: "agents", "positive_control", "metadata" sections present

COMMIT_MESSAGE:
feat(step8/task4): full eval aggregation harness + ABL-025/026 + ABL-040 validation

STOP_CONDITION:
Stop if: ABL-025/ABL-026 implementation requires re-training (BLOCKED — they must be inference-time only). Report as blocker.

RELATED_AGENT_REPORT_IDS: exp_design_step8_v04_ablation_R1, claim_metric_step8_alignment_R1
