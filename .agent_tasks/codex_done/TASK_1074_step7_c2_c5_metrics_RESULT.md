TASK_NAME: step7_c2_c5_metrics
TASK_NUMBER: 1074

## Files Changed

- src/frcgw/evaluation/metrics.py
- src/frcgw/evaluation/eval_runner.py
- tests/test_step7_ood_shift_f1.py
- tests/test_step7_c5_calibration_stub.py
- docs/orchestration/lr_alignment/31_step7_c2_metric_decision.md
- .agent_tasks/codex_done/TASK_1074_step7_c2_c5_metrics_RESULT.md

## Tests Run

- PASS: `$env:PYTHONPATH='src'; .\.venv\Scripts\python -m pytest tests\test_step7_ood_shift_f1.py -q`
- PASS: `$env:PYTHONPATH='src'; .\.venv\Scripts\python -m pytest tests\test_step7_c5_calibration_stub.py -q`
- PASS: `$env:PYTHONPATH='src'; .\.venv\Scripts\python -m pytest tests\test_forbidden_field_mirror_sync.py -q`

## Pass/Fail Summary

- Required ood_shift_f1 tests: 6 passed.
- Required C5 calibration tests: 3 passed.
- Stop-condition forbidden-field mirror check: 2 passed, 1 skipped.
- Schema diff check: empty.

## Blockers

- None.
- Note: running the required pytest commands without `PYTHONPATH=src` fails in this
  local venv because its editable `frcgw` install points at
  `C:\Users\computer\Desktop\NeurIPS2026_codex`. The venv was not modified.
