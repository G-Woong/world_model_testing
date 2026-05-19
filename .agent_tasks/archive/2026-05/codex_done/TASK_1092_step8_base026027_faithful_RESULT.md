# TASK_1092_step8_base026027_faithful Result

## Files changed

- `src/frcgw/evaluation/baselines.py`
- `tests/test_step8_direct_threat_baselines.py`
- `scripts/audit_step8_direct_threat_baselines.py`
- `docs/orchestration/lr_alignment/39_step8_direct_baseline_faithfulness.md`
- `.agent_tasks/codex_done/TASK_1092_step8_base026027_faithful_RESULT.md`

## Tests run

- `PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests/test_step8_direct_threat_baselines.py -q`
- `PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests/test_forbidden_field_mirror_sync.py tests/test_leakage_auditor.py -q`

## Pass/fail summary

- Step 8 direct-threat baseline tests: PASS, 4 passed.
- Existing leakage guard tests: PASS, 13 passed and 1 skipped.
- A first run without `PYTHONPATH=src` failed during import collection because `frcgw` was not on the module path in this shell; the required venv test reruns above passed.

## Blockers

- None.
