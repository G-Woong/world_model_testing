TASK_NAME: step8_longhorizon_configs
TASK_NUMBER: 1090

Files changed:
- configs/train_text_v0_4_long.yaml
- configs/train_text_v0_4_long_stage2.yaml
- configs/lr_eval_real_v0_4_long.yaml
- src/frcgw/training/monitoring.py
- tests/test_step8_long_horizon_training_config.py
- .agent_tasks/codex_done/TASK_1090_step8_longhorizon_configs_RESULT.md

Notes:
- src/frcgw/training/train_text.py already contained the required torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0) call between loss.backward() and optimizer.step(); left unchanged to avoid non-required churn.

Tests run:
- .venv\Scripts\python.exe -m pytest tests/test_step8_long_horizon_training_config.py -q
  - PASS: 4 passed
- $env:PYTHONPATH='src'; $env:PYTHONUTF8='1'; .venv\Scripts\python.exe -m pytest tests/test_step5_pretraining_checkpoint.py tests/test_train_text_smoke.py -q
  - PASS: 7 passed, 6 skipped
- $env:PYTHONPATH='src'; $env:PYTHONUTF8='1'; .venv\Scripts\python.exe -m pytest tests/ -q --ignore=tests/test_step8_c3_trace_integrity.py --ignore=tests/test_step8_v0_4_dataset.py
  - FAIL: 25 failures remain in out-of-scope/protected areas.
- git diff --check
  - PASS

Pass/fail summary:
- New Step 8 long-horizon config tests pass.
- Existing nearby monitoring/training smoke tests pass.
- The required broad suite is not green in this worktree, but the observed failures are outside this task's allowed edit set.

Blockers:
- tests/test_archive_sweep_v2.py and tests/test_lifecycle_phase2_hooks.py require missing .claude hook/settings files; .claude/ is forbidden for this task.
- tests/test_step3_dataset_backfill.py and tests/test_step3_ood_split.py require missing data/frcgw_text/v0_2 artifacts; data/ is forbidden for this task.
- tests/test_ablation_runner.py expects exactly 16 ablation IDs, but the current registry includes extra existing IDs.
- tests/test_text_data_collection.py expects P2 counterfactuals to be empty, while current generation emits counterfactual records.
