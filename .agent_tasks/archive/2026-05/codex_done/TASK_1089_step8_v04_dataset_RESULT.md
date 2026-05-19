TASK_NAME: step8_v04_dataset
TASK_NUMBER: 1089

Files changed:
- configs/dataset_v0_4.yaml
- scripts/generate_v0_4_dataset.py
- scripts/audit_step8_dataset_coverage.py
- tests/test_step8_v0_4_dataset.py
- .agent_tasks/codex_done/TASK_1089_step8_v04_dataset_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_step8_v0_4_dataset.py -q
- .\.venv\Scripts\python.exe -m py_compile scripts/generate_v0_4_dataset.py scripts/audit_step8_dataset_coverage.py
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_step8_v0_4_dataset.py -q
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_forbidden_field_mirror_sync.py tests/test_leakage_auditor.py -q
- .\.venv\Scripts\python.exe scripts/generate_v0_4_dataset.py --config configs/dataset_v0_4.yaml --out-root .agent_tasks/codex_tmp/TASK_1089_dry_run --target-episodes 5

Pass/fail summary:
- New Step 8 v0.4 tests: PASS (3 passed).
- Script compile check: PASS.
- Existing forbidden-field mirror and leakage auditor tests: PASS with PYTHONPATH=src (13 passed, 1 skipped).
- Generator dry-run: PASS. The 5-episode dry run emitted OOD_COVERAGE_GATE_PARTIAL in the manifest, as expected because 5 episodes cannot satisfy >=30 blocker_removed and delayed_effect gates.

Blockers:
- None.
- Note: this worktree requires PYTHONPATH=src for direct pytest runs unless the package is installed in editable mode.
