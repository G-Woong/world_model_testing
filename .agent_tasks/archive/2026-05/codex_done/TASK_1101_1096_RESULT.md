# TASK_1101_1096 Result

Files changed:
- `src/frcgw/schemas/step_schema.py`: added `EvaluationLabels.true_regime`.
- `src/frcgw/text_env/collector.py`: emits `true_regime` from `TextState._hidden_regime`.
- `src/frcgw/evaluation/metrics.py`: added `regime_shift_f1`.
- `src/frcgw/evaluation/eval_runner.py`: registered `regime_shift_f1`.
- `scripts/backfill_v0_4_true_regime.py`: added v0_4 JSONL backfill utility.
- `tests/test_step9_regime_shift_f1.py`: added six focused unit tests.

Tests run:
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_step9_regime_shift_f1.py tests/test_forbidden_field_mirror_sync.py tests/test_visibility_contract.py tests/test_eval_runner_timestamps.py`
  - PASS: 32 passed, 1 skipped.
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe scripts\backfill_v0_4_true_regime.py .agent_tasks\codex_tmp_backfill_1101`
  - PASS on temporary fixture: updated 1, already_set 1.

Pass/fail summary:
- Required targeted tests passed.
- Backfill script smoke test passed on a temporary fixture.
- Initial pytest invocation without `PYTHONPATH=src` failed during collection with `ModuleNotFoundError: frcgw`; the venv rerun above is the passing targeted test run.

Blockers:
- None. The backfill script was not run against `data/frcgw_text/v0_4` because this task's hard constraints forbid modifying `data/`.
