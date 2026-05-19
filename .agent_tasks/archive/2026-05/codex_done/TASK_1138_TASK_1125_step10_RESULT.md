TASK_NAME: TASK_1125_step10_fair_ppc
TASK_NUMBER: 1138

Files changed:
- src/frcgw/evaluation/metrics.py
- src/frcgw/evaluation/eval_runner.py
- src/frcgw/evaluation/frcg_agent.py
- tests/test_step10_fair_ppc.py
- .agent_tasks/codex_done/TASK_1138_TASK_1125_step10_RESULT.md

Tests run:
- `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests/test_step10_fair_ppc.py` -> PASS, 4 passed.
- `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests/test_step9_regime_shift_f1.py` -> PASS, 6 passed.
- `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests/test_forbidden_field_mirror_sync.py` -> PASS, 2 passed, 1 skipped.
- `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests/test_step10_fair_ppc.py tests/test_step9_regime_shift_f1.py tests/test_forbidden_field_mirror_sync.py` -> PASS, 12 passed, 1 skipped.
- `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests/test_eval_runner.py` -> PASS, 7 passed.
- `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests/test_frcg_agent.py` -> PASS, 11 passed, 1 warning.
- `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests/test_step10_threshold_free.py` -> PASS, 9 passed.

Pass/fail summary:
- Required tests pass with `PYTHONPATH=src`.
- A preliminary invocation without `PYTHONPATH=src` failed during collection because `frcgw` was not importable from the src-layout checkout.

Blockers:
- None.
