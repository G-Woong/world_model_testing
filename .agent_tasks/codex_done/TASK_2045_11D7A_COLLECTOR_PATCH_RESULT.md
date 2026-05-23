# Codex Task Report ??TASK_2045 11D7A_COLLECTOR_PATCH
## Summary
BLOCKED. Implemented the requested scoped patch locally, but did not commit because `pytest -q tests/` is not green and several failures require changes outside `FILES_ALLOWED` or missing environment dependencies.
## Files Changed
- scripts/fglc/collect_maniskill.py
- scripts/fglc/build_split.py
- src/fglc/data/collector.py
- src/fglc/data/validators.py
- src/fglc/data/manifest.py
- src/fglc/repair/diagnose.py
- tests/test_fglc_no_garbage_data.py
- tests/test_fglc_split_integrity.py
- .agent_tasks/codex_done/TASK_2045_11D7A_COLLECTOR_PATCH_RESULT.md
## Commands Run
- Get-Content -Raw AGENTS.md
- Get-Content -Raw .agent_tasks/codex_queue/TASK_2045_11D7A_COLLECTOR_PATCH.md
- git status --short
- Get-Content -Raw scripts/fglc/collect_maniskill.py
- Get-Content -Raw scripts/fglc/build_split.py
- Get-Content -Raw src/fglc/data/collector.py
- Get-Content -Raw src/fglc/data/validators.py
- Get-Content -Raw src/fglc/data/manifest.py
- Get-Content -Raw src/fglc/repair/diagnose.py
- Get-Content -Raw tests/test_fglc_no_garbage_data.py
- Get-Content -Raw tests/test_fglc_split_integrity.py
- if (Test-Path tests/test_fglc_forbidden_field_sync.py) { 'EXISTS' } else { 'MISSING' }
- rg "validate_episode|collect_episodes|build_quality_report|CANONICAL_METRIC_KEYS|EpisodeRejectReason|quality_report" -n
- rg --files tests | rg "forbidden|garbage|split|diagnose|collector|manifest"
- Get-Content -Raw tests/test_fglc_forbidden_field_sync.py
- .venv/Scripts/python.exe -m pytest -q tests/test_fglc_no_garbage_data.py tests/test_fglc_split_integrity.py tests/test_fglc_forbidden_field_sync.py
- .venv/Scripts/python.exe scripts/fglc/collect_maniskill.py --help
- $env:PYTHONPATH='src'; .venv/Scripts/python.exe -m pytest -q tests/test_fglc_no_garbage_data.py tests/test_fglc_split_integrity.py tests/test_fglc_forbidden_field_sync.py
- $env:PYTHONPATH='src'; .venv/Scripts/python.exe -m pytest -q tests/
- git diff -- scripts/fglc/collect_maniskill.py scripts/fglc/build_split.py src/fglc/data/collector.py src/fglc/data/validators.py src/fglc/data/manifest.py src/fglc/repair/diagnose.py tests/test_fglc_no_garbage_data.py tests/test_fglc_split_integrity.py
- git status --short
## Tests Run (pass/fail)
- FAIL: `.venv/Scripts/python.exe -m pytest -q tests/test_fglc_no_garbage_data.py tests/test_fglc_split_integrity.py tests/test_fglc_forbidden_field_sync.py` failed before collection because `fglc` was not importable without `PYTHONPATH=src`.
- PASS: `PYTHONPATH=src .venv/Scripts/python.exe -m pytest -q tests/test_fglc_no_garbage_data.py tests/test_fglc_split_integrity.py tests/test_fglc_forbidden_field_sync.py` passed: 46 passed, 14 skipped.
- PASS: `.venv/Scripts/python.exe scripts/fglc/collect_maniskill.py --help` showed `--mode {probe,pilot,scaled}` and `--quarantine-dir`.
- FAIL: `PYTHONPATH=src .venv/Scripts/python.exe -m pytest -q tests/` failed.
## Evidence (log paths, metric values)
- Focused tests: 46 passed, 14 skipped.
- Full suite failure classes observed: missing imports for `h5py`, `hydra`, and `omegaconf`; `.claude` hook/settings files absent in this worktree; `tests/test_fglc_repair_metric_artifact.py` expects repair behavior/candidates requiring files outside `FILES_ALLOWED`.
- CLI help includes required flags: `--mode {probe,pilot,scaled}` and `--quarantine-dir QUARANTINE_DIR`.
## Risks / Open Questions
- Full-suite acceptance cannot be met in this worktree without installing missing packages and/or modifying forbidden or non-allowed files such as `.claude/*` and repair candidate/taxonomy modules.
- The implementation remains uncommitted because the task contract forbids committing when required tests fail.
## Patch Review Notes for Claude Code
- `validate_episode()` now supports optional `seen_state_hashes` and adds `EPISODE_DUPLICATE` after the prior nine reject checks.
- `collect_episodes()` accepts optional `quarantine_dir` and writes rejected state/action/reward/done arrays to gzip4 HDF5 best-effort dumps.
- `build_split.py` exposes `audit_trajectory_hashes(split_episodes)` and merges its result into `quality_report`.
- `build_quality_report()` now includes friction unit annotation and default hash-audit fields.
- `CANONICAL_METRIC_KEYS` includes `eval_ci95_over_effect_size`.
## Accept/Reject Recommendation
REJECT / BLOCKED until the full test suite can run green or the task owner narrows the required test gate to the focused tests that are within this task's allowed file scope.
