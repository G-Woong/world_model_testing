TASK_NAME: TASK_1053_step5_lr_reconciliation
SANDBOX_MODE: bypass

BACKGROUND:
STEP 4 found a LR divergence: planner F_t (from text_frcg_plan) vs lr_scorer F_t showed
mean_abs_diff=1.5, both constant (random-init artifact). The STEP 4 comparison script
is scripts/audit_step4_lr_comparison.py and outputs outputs/audits/step4_lr_comparison.json.

STEP 5 goal: create a new audit script for the TRAINED checkpoint comparison, fix the
degenerate_f_t_count rollup bug in eval_runner.py, and write 5 tests.

Active path change is FORBIDDEN in STEP 5 (dual trace policy; STEP 6 iit).

GOAL:
1. Create scripts/audit_step5_lr_reconciliation.py (new file)
2. Fix degenerate_f_t_count counter bug in src/frcgw/evaluation/eval_runner.py
3. Write tests/test_step5_lr_reconciliation.py (5 tests)

FILES_ALLOWED:
- scripts/audit_step5_lr_reconciliation.py (NEW)
- src/frcgw/evaluation/eval_runner.py (degenerate counter fix ONLY — minimal change)
- tests/test_step5_lr_reconciliation.py

FILES_FORBIDDEN:
- outputs/**
- data/**
- paper_context_ref/**
- src/frcgw/schemas/**
- src/frcgw/evaluation/frcg_agent.py (active F_t path — DO NOT CHANGE)
- src/frcgw/falsification/lr_scorer.py (read-only)
- .claude/**
- scripts/run_codex_task.ps1
- outputs/audits/step4_lr_comparison.json (DO NOT OVERWRITE)

REQUIRED_IMPLEMENTATION:

1. scripts/audit_step5_lr_reconciliation.py:
   - argparse: --dataset (default: data/frcgw_text/v0_3/test_id.jsonl),
     --ckpt-path (default: outputs/checkpoints/pretrain_v0_3/checkpoint.pt),
     --out (default: outputs/audits/step5_lr_reconciliation.json),
     --max-episodes (default: 5)
   - If ckpt_path does not exist: write {"status": "CKPT_NOT_FOUND", "mean_abs_diff_trained": null, ...}
   - If ckpt_path exists: load trained TextFRCGModelAgent, run first max-episodes episodes,
     collect F_t_planner per step (from plan_meta or last_F_t)
   - Collect F_t_lr_scorer: import lr_scorer.py, compute separately on same observations
   - Compare: mean_abs_diff_trained, degenerate_planner_rate_trained (F_t == 0.0 fraction),
     degenerate_lr_rate_trained
   - Decision rule in output:
     if mean_abs_diff < 0.1 AND both rates < 0.1: interpretation = "CONVERGED_AFTER_TRAINING"
     else: interpretation = "DIVERGENCE_PERSISTS"
   - Output JSON: {status, mean_abs_diff_trained, degenerate_planner_rate_trained,
     degenerate_lr_rate_trained, interpretation, step4_comparison_path, n_episodes, timestamp}
   - MUST NOT overwrite outputs/audits/step4_lr_comparison.json
   - MUST write to outputs/audits/step5_lr_reconciliation.json (different file)
   - If dataset not found: write {"status": "DATASET_NOT_FOUND", ...}

2. src/frcgw/evaluation/eval_runner.py — degenerate_f_t_count bug fix:
   - Find where degenerate_f_t_count is computed per episode
   - Bug: F_t==0.0 steps are not being counted correctly (always returns 0)
   - Fix: ensure each step where F_t==0.0 (or last_F_t==0.0) is counted
   - ONLY fix this counter logic — do not change any other code

3. tests/test_step5_lr_reconciliation.py (5 tests):
   - test_audit_json_written_on_ckpt_not_found(): run script with nonexistent ckpt → JSON written with status="CKPT_NOT_FOUND"
   - test_dual_trace_policy(): audit script outputs both F_t_planner and F_t_lr_scorer fields (dual trace preserved)
   - test_degenerate_counter_fix(): synthetic episodes where all F_t=0.0 → degenerate_f_t_count > 0
   - test_c3_claim_blocked_on_divergence(): if interpretation=="DIVERGENCE_PERSISTS", C3 claim must be marked preliminary (test asserts interpretation string)
   - test_no_step4_overwrite(): after running, outputs/audits/step4_lr_comparison.json unchanged (or doesn't exist — skip if not present)

REQUIRED_TESTS:
pytest tests/test_step5_lr_reconciliation.py -q
Expected: 5 passed

ACCEPTANCE_CRITERIA:
- 5 tests pass
- scripts/audit_step5_lr_reconciliation.py handles missing ckpt/dataset gracefully
- eval_runner.py degenerate_f_t_count counts F_t==0.0 steps correctly
- step4_lr_comparison.json is NEVER overwritten
- Active F_t path in frcg_agent.py UNCHANGED

COMMIT_MESSAGE:
feat(step5/task4): LR reconciliation audit script + degenerate counter fix

STOP_CONDITION:
Stop if: (1) lr_scorer.py import fails (report BLOCKED — do not implement workaround),
(2) cannot locate degenerate_f_t_count logic in eval_runner.py (report BLOCKED)
