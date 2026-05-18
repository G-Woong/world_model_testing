TASK_NAME: TASK_1056_step5_redteam_review
SANDBOX_MODE: bypass

BACKGROUND:
STEP 5 is complete. All Codex tasks (1-6) have been accepted and merged.
This is a read-only red-team review of all STEP 5 changes.

STEP 5 changes summary:
- Task 1: configs/train_text_v0_3.yaml, train_text_v0_3_stage2.yaml + monitoring.py functions
- Task 2: metrics.py alternative_rollout_fidelity() + eval_runner.py METRIC_FUNCTIONS + scripts/10_run_lr_real_eval.py BLOCKED→actual
- Task 3: frcg_agent.py _GRAMMAR_IDX_TO_NAME + _last_selected_hypothesis_id fix
- Task 4: scripts/audit_step5_lr_reconciliation.py + eval_runner.py degenerate_f_t_count fix
- Task 5: scripts/10_run_lr_real_eval.py C5 OR logic + DEGENERATE_OR_UNTRAINED status
- Task 6: ablations.py ABL-011/015/040 registry wiring

GOAL:
Read-only review of STEP 5 diff for:
1. Hidden label leakage (oracle fields in inference input)
2. Fake metrics (claiming results without actual computation)
3. Checkpoint misuse (valid_trained_eval=True without actual checkpoint)
4. LR overclaim (C3 claim stronger than "PRELIMINARY")
5. C4 fake rollout (metric using oracle delta instead of model's own prediction)
6. C5 fake calibration (degenerate predictor marked OK)
7. Old evidence overwrite (STEP 4 outputs modified)
8. Namespace leakage (grammar_{idx} still in any inference-sensitive path)
9. ABL fake (registry entry with no behavioral change)

FILES_ALLOWED: (read-only — do not modify any files)
FILES_FORBIDDEN: ALL writes forbidden. This is READ-ONLY.

REQUIRED_IMPLEMENTATION:
Read and audit the following files:
- src/frcgw/evaluation/metrics.py (alternative_rollout_fidelity function)
- src/frcgw/evaluation/frcg_agent.py (_GRAMMAR_IDX_TO_NAME usage)
- src/frcgw/evaluation/eval_runner.py (degenerate_f_t_count, METRIC_FUNCTIONS)
- src/frcgw/evaluation/ablations.py (ABL-011/015/040 wrappers)
- scripts/10_run_lr_real_eval.py (C5 OR logic, BLOCKED markers)
- scripts/audit_step5_lr_reconciliation.py (LR audit script)
- configs/train_text_v0_3.yaml (l_falsification=0.0 confirmed)
- outputs/runs/p3_lr_real_eval_step5_trained_smoke/manifest.json (valid_trained_eval)
- outputs/audits/step5_lr_reconciliation.json (DIVERGENCE_PERSISTS)

For each of the 9 review criteria, report: CLEAN or VIOLATION + specifics.

Write report to: .agent_tasks/codex_done/TASK_1056_step5_redteam_review_RESULT.md

REQUIRED_TESTS:
(none — read-only review)

ACCEPTANCE_CRITERIA:
Report exists. All 9 criteria explicitly addressed.

COMMIT_MESSAGE:
review(step5/task7): STEP 5 red-team review PASS

STOP_CONDITION:
Stop only if file read permissions are denied. Never stop for "not enough findings."
