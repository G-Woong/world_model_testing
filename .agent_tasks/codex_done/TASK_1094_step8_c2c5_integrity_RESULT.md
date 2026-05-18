TASK_NAME: step8_c2c5_integrity
TASK_NUMBER: 1094

Files changed:
- src/frcgw/evaluation/metrics.py
- src/frcgw/evaluation/calibration.py
- tests/test_step8_regime_shift_f1.py
- tests/test_step8_calibration.py
- .agent_tasks/codex_done/TASK_1094_step8_c2c5_integrity_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_step8_regime_shift_f1.py tests/test_step8_calibration.py tests/test_visibility_contract.py tests/test_forbidden_field_mirror_sync.py -q
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_step8_regime_shift_f1.py tests/test_step8_calibration.py tests/test_visibility_contract.py tests/test_forbidden_field_mirror_sync.py -q

Pass/fail summary:
- First run failed during collection because frcgw was not on the import path.
- Rerun with PYTHONPATH=src passed: 25 passed, 1 skipped.

Blockers:
- None.
