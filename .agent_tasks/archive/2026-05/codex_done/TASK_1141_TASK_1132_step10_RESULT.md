TASK_NAME: TASK_1132_step10_abl036_real_no_gate
TASK_NUMBER: 1141

Files changed:
- src/frcgw/evaluation/ablations.py
- src/frcgw/evaluation/eval_runner.py
- configs/lr_eval_step10_fair_compute.yaml
- tests/test_step10_fair_compute.py
- .agent_tasks/codex_done/TASK_1141_TASK_1132_step10_RESULT.md

Tests run:
- .venv\Scripts\python.exe -m pytest -q tests\test_step10_fair_compute.py
- $env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests\test_step10_fair_compute.py
- $env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests\test_step9_regime_shift_f1.py
- $env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests\test_forbidden_field_mirror_sync.py

Pass/fail summary:
- Initial no-PYTHONPATH run failed during collection because frcgw was not importable from the venv.
- tests/test_step10_fair_compute.py: PASS (4 passed) after adding test-local src path setup; also PASS without PYTHONPATH afterward.
- tests/test_step9_regime_shift_f1.py: PASS (6 passed).
- tests/test_forbidden_field_mirror_sync.py: PASS (2 passed, 1 skipped).
- Wrapper sanity check: PASS.

Blockers:
- None.
