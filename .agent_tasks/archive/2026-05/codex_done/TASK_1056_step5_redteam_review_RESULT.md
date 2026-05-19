# TASK_1056 STEP 5 Red-Team Review Result

Review target: STEP 5 changes listed in `.agent_tasks/codex_queue/TASK_1064_TASK_1056.md`.

Required artifacts checked:
- `outputs/runs/p3_lr_real_eval_step5_trained_smoke/manifest.json`: MISSING
- `outputs/audits/step5_lr_reconciliation.json`: MISSING

## Criteria

1. Hidden label leakage: CLEAN
   - `EvaluationRunner.run()` builds `PublicObservation` from `public_observation` / `public_input`, runs `assert_no_hidden_labels_in_input()`, and calls `agent.act(obs)` without `eval_labels` (`src/frcgw/evaluation/eval_runner.py:101-107`).
   - `TextFRCGModelAgent.act()` accepts `eval_labels` only for API compatibility and does not read it (`src/frcgw/evaluation/frcg_agent.py:49-50`, `src/frcgw/evaluation/frcg_agent.py:103`).
   - Metrics and trace writers read evaluation labels after action selection for scoring/audit only.

2. Fake metrics: CLEAN
   - `alternative_rollout_fidelity` is wired in `METRIC_FUNCTIONS` (`src/frcgw/evaluation/eval_runner.py:34-45`).
   - Missing coverage or missing predictions are represented as `BLOCKED_*` / `None`, not as numeric success (`src/frcgw/evaluation/metrics.py:278-344`, `scripts/10_run_lr_real_eval.py:586-618`).
   - C2 regime split and C4 alternative adoption are explicitly blocked rather than claimed (`scripts/10_run_lr_real_eval.py:618-624`).

3. Checkpoint misuse: VIOLATION
   - The required trained-smoke manifest path is absent: `outputs/runs/p3_lr_real_eval_step5_trained_smoke/manifest.json`.
   - Code sets `valid_trained_eval = ckpt_paths_all_provided` (`scripts/10_run_lr_real_eval.py:651`) and the main path preflights by instantiating/loading agents before manifest write, but the required evidence artifact is missing, so `valid_trained_eval` cannot be verified for the Step 5 run.

4. LR overclaim: VIOLATION
   - The required reconciliation artifact is absent: `outputs/audits/step5_lr_reconciliation.json`.
   - The code path is conservative: `DIVERGENCE_PERSISTS` maps to `C3_claim_status: PRELIMINARY` (`scripts/audit_step5_lr_reconciliation.py:51-52`, `scripts/audit_step5_lr_reconciliation.py:213-215`), but the committed worktree lacks the audit JSON that the task required to confirm that state.

5. C4 fake rollout: CLEAN
   - The metric uses `predicted_top1_delta` / model prediction fields for the prediction side and actual `progress_delta` for outcome comparison (`src/frcgw/evaluation/metrics.py:251-267`, `src/frcgw/evaluation/metrics.py:310-318`).
   - If counterfactuals exist without a model rollout prediction, it returns `BLOCKED_no_model_rollout_prediction` instead of using oracle counterfactual deltas as a fake prediction (`src/frcgw/evaluation/metrics.py:329-344`).

6. C5 fake calibration: CLEAN
   - Degenerate wrong-prob traces are marked `DEGENERATE_PREDICTOR` when variance is near zero, unique count is at most two, or mean `F_t` is degenerate (`scripts/10_run_lr_real_eval.py:445-450`).
   - Missing checkpoints downgrade to `DEGENERATE_OR_UNTRAINED` (`scripts/10_run_lr_real_eval.py:521-523`), and both states block `C5_calibration_ece` (`scripts/10_run_lr_real_eval.py:573-576`).

7. Old evidence overwrite: VIOLATION
   - `scripts/10_run_lr_real_eval.py` still writes the C5 audit to the Step 4 filename `step4_ece_degenerate_predictor_audit.json` by default (`scripts/10_run_lr_real_eval.py:49`, `scripts/10_run_lr_real_eval.py:491-497`).
   - `main()` calls that writer unconditionally (`scripts/10_run_lr_real_eval.py:738-740`), so a Step 5 run can overwrite an existing Step 4 audit artifact.
   - The Step 5 LR reconciliation script itself writes to `step5_lr_reconciliation.json` and only references the Step 4 comparison path, so this violation is specific to the C5 audit writer path.

8. Namespace leakage: VIOLATION
   - `_GRAMMAR_IDX_TO_NAME` maps the expected eight grammar ids, but out-of-range model output falls back to `f"grammar_{best_grammar_idx}"` (`src/frcgw/evaluation/frcg_agent.py:122-125`).
   - That value is recorded into inference/evaluation trace fields (`scripts/10_run_lr_real_eval.py:205-208`, `scripts/10_run_lr_real_eval.py:275`, `scripts/10_run_lr_real_eval.py:333`).
   - The regression test explicitly accepts `grammar_99` for unknown indices (`tests/test_step5_namespace_alignment.py:134-135`), so the forbidden namespace can still enter an inference-sensitive trace path under mismatched model output dimensions.

9. ABL fake: VIOLATION
   - ABL-011 and ABL-015 have behavioral effects: ABL-011 removes `effect_summary` from history and ABL-015 selects random public candidates (`src/frcgw/evaluation/ablations.py:326-356`).
   - ABL-040 is registered and its wrapper only changes behavior when `eval_labels["true_control_grammar"]` is passed (`src/frcgw/evaluation/ablations.py:361-376`, `src/frcgw/evaluation/ablations.py:546-578`).
   - The real runner and tracing wrapper call agents without `eval_labels` (`src/frcgw/evaluation/eval_runner.py:107`, `scripts/10_run_lr_real_eval.py:177`, `scripts/10_run_lr_real_eval.py:194`), so ABL-040 has no behavioral change in the real evaluation path despite being registered as a positive-control ablation.

## Additional Notes

- `configs/train_text_v0_3.yaml` and `configs/train_text_v0_3_stage2.yaml` both keep `l_falsification: 0.0` and `l_intent_action_mapping: 0.0` (`configs/train_text_v0_3.yaml:19-20`, `configs/train_text_v0_3_stage2.yaml:19-20`).
- `degenerate_f_t_count` is now counted from per-step `f_t` values (`src/frcgw/evaluation/eval_runner.py:161`, `src/frcgw/evaluation/eval_runner.py:344-350`).

Required tests: none listed in the task file. No tests were run.
