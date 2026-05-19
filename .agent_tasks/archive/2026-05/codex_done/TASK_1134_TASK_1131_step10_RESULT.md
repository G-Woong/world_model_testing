TASK_NAME: TASK_1131_step10_no_state_change_decoupling
TASK_NUMBER: 1134

Files changed:
- configs/lr_eval_step10_proxy_ablation.yaml
- scripts/risk_hunt/run_proxy_ablation_eval.py
- src/frcgw/planning/decision_gate.py
- src/frcgw/planning/planner.py
- tests/test_step10_proxy_ablation.py

Tests run:
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_step10_proxy_ablation.py`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_forbidden_field_mirror_sync.py`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_step9_regime_shift_f1.py`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_step10_proxy_ablation.py tests/test_forbidden_field_mirror_sync.py tests/test_step9_regime_shift_f1.py`
- `.\.venv\Scripts\python.exe scripts\risk_hunt\run_proxy_ablation_eval.py --dry-run`

Pass/fail summary:
- tests/test_step10_proxy_ablation.py: PASS, 4 passed.
- tests/test_forbidden_field_mirror_sync.py: PASS, 2 passed, 1 skipped.
- tests/test_step9_regime_shift_f1.py: PASS, 6 passed.
- Combined required pytest run: PASS, 12 passed, 1 skipped.
- Proxy ablation runner dry-run: PASS, dispatch shows proxy-on=True and proxy-off=False.
- Initial pytest collection without `PYTHONPATH=src` failed with `ModuleNotFoundError: frcgw`; rerun with `PYTHONPATH=src` passed.

Blockers:
- None.
