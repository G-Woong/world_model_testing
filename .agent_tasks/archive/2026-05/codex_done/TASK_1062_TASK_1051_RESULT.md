TASK_NAME: TASK_1051_step5_c4_rollout_fidelity
TASK_NUMBER: 1062

Files changed:
- src/frcgw/evaluation/metrics.py
- src/frcgw/evaluation/eval_runner.py
- scripts/10_run_lr_real_eval.py
- tests/test_step5_rollout_fidelity.py
- .agent_tasks/codex_done/TASK_1062_TASK_1051_RESULT.md

Tests run:
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_step5_rollout_fidelity.py tests/test_step4_counterfactual_no_leakage.py -q

Pass/fail summary:
- PASS: 10 passed.
- Note: the same pytest target without PYTHONPATH failed at collection because the venv editable install points at C:\Users\computer\Desktop\NeurIPS2026_codex instead of this checkout.

Blockers:
- None.
