TASK_NAME: step6_redteam_review

BACKGROUND:
Codex Tasks 1-5 for STEP 6 have been completed. This task performs a read-only red-team
review of all changes before accept commit.

GOAL:
Read all diffs from Tasks 1-5 and verify correctness, safety, and contract compliance.

FILES_ALLOWED:
- .agent_tasks/codex_done/TASK_1065_step6_ft_wiring_planner_configs_RESULT.md (new — to write)
- .agent_tasks/codex_done/TASK_1070_step6_redteam_review_RESULT.md (new — to write)

FILES_FORBIDDEN: ALL source/config/test files (read-only access only for review)

REQUIRED_IMPLEMENTATION:

Read and review ALL of the following (read-only):

### From Task 1 (TASK_1065):
- src/frcgw/training/train_text.py diff
- src/frcgw/planning/planner.py diff
- configs/train_text_v0_3_falsification.yaml
- configs/train_text_v0_3_falsification_stage2.yaml
- configs/lr_eval_real_v0_3_falsification.yaml
- tests/test_step6_l_falsification_training_config.py
- tests/test_step6_planner_alt_hypothesis_emission.py

### From Task 2 (TASK_1066):
- src/frcgw/evaluation/ablations.py diff (AblationConfig + no_falsification entry)
- configs/ablation_core.yaml diff (ABL-016 entry only)
- docs/orchestration/lr_alignment/29_step6_abl016_control_registration.md
- tests/test_step6_abl016_control_registration.py

### From Task 3 (TASK_1067):
- scripts/audit_step6_lr_reconciliation.py
- tests/test_step6_lr_reconciliation.py

### From Task 4 (TASK_1068):
- src/frcgw/evaluation/eval_runner.py diff
- scripts/10_run_lr_real_eval.py diff
- tests/test_step6_model_rollout_prediction.py
- tests/test_step6_c1_persistence_v1_dispatch.py

### From Task 5 (TASK_1069):
- docs/orchestration/lr_alignment/27_step6_ablation_execution_matrix.md
- tests/test_step6_ablation_execution_matrix.py

## Checklist (verify ALL 15 items):

1. [ ] Hidden label leakage: model_predicted_progress_delta does NOT appear in PublicObservation
2. [ ] F_t wiring: NO torch.no_grad() wrapper around F_t computation in train_text.py (gradient must flow)
3. [ ] F_t shape: L_falsification receives [B]-shaped tensor, not scalar (verify per-example loop exists)
4. [ ] EFFECT_TYPE_VOCAB: true_action_effect_type is mapped through EFFECT_TYPE_VOCAB (not passed as string)
5. [ ] Planner alt-hypothesis: alt_hypotheses is non-empty after propose() call (no regression to [])
6. [ ] ABL-016 control_evidence_ref: does NOT create new files in outputs/ (yaml text only)
7. [ ] STEP 5 configs: configs/train_text_v0_3.yaml and configs/train_text_v0_3_stage2.yaml l_falsification == 0.0 (unmodified)
8. [ ] C4 metric: counterfactual_progress_delta and model_predicted_progress_delta are separate fields (no mis-labeling)
9. [ ] STEP 4/5 artifacts: outputs/audits/step4_*.json and outputs/audits/step5_lr_reconciliation.json not overwritten
10. [ ] C3 claim wording: no "resolved", "proven", "outperforms", "defeated" in any doc or comment
11. [ ] Tests behavior: test assertions verify actual behavior (not just file existence) where applicable
12. [ ] Forbidden path check: paper_context_ref/**, .claude/**, scripts/run_codex_task.ps1, src/frcgw/schemas/visibility.py NOT modified
13. [ ] losses.py DEFAULT_WEIGHTS: unchanged (l_falsification remains 1.0 as before, not newly added)
14. [ ] ABL-040 isolation: leakage_sanity_probe not mixed with performance ablations in matrix doc
15. [ ] NoFalsificationAblation.act() behavior: unchanged (only AblationConfig metadata added)

Write violations as VIOLATION: <description> and non-violations as PASS: <item>.

REQUIRED_TESTS: (none — read-only review)

ACCEPTANCE_CRITERIA:
- RESULT.md contains all 15 checklist items with PASS or VIOLATION
- If any VIOLATION found: mark overall status as BLOCKED, explain fix needed
- If all PASS: mark overall status as ACCEPTED

COMMIT_MESSAGE:
review(step6/task6): red-team review PASS/FAIL for Tasks 1-5

STOP_CONDITION:
Stop if: output doc is missing any of the 15 checklist items.
