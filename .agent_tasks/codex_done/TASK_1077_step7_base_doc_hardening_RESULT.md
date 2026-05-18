# TASK 1077: step7_base_doc_hardening Result

## Files Changed

- `src/frcgw/evaluation/baselines.py`
- `tests/test_step7_direct_threat_approximation_declared.py`
- `docs/orchestration/lr_alignment/34_step7_direct_threat_baseline_status.md`
- `.agent_tasks/codex_done/TASK_1077_step7_base_doc_hardening_RESULT.md`

## Tests Run

- `.\\.venv\\Scripts\\python.exe -m pytest tests/test_step7_direct_threat_approximation_declared.py -q`
  - FAIL: collection failed because `frcgw` was not on the import path.
- `$env:PYTHONPATH='src'; .\\.venv\\Scripts\\python.exe -m pytest tests/test_step7_direct_threat_approximation_declared.py -q`
  - PASS: 7 passed.
- `git diff -- src/frcgw/schemas`
  - PASS: empty diff.
- `rg -n "defeats WAC|outperforms CUWM|superior to WebWorld" src tests`
  - PASS: no matches in source or tests.
- `git diff --check`
  - PASS: no whitespace errors.

## Pass/Fail Summary

Final targeted test run passed with `PYTHONPATH=src` using the existing `.venv`.
Scope checks passed: no schema changes, no forbidden claim wording in source/tests,
and BASE-028 was left unchanged.

## Blockers

None.
