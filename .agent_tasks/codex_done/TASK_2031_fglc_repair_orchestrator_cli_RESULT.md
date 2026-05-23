# Codex Task Report ??TASK_2031 fglc_repair_orchestrator_cli
## Summary
Implemented the Step 8 dry-run repair orchestrator, CLI mock control plane, smoke config, output marker, exports, and focused tests for the five stop conditions plus CLI behavior.
## Files Changed
- src/fglc/repair/orchestrator.py
- scripts/fglc/repair_loop.py
- configs/fglc/smoke_4060.yaml
- outputs/repair/.gitkeep
- tests/test_fglc_repair_orchestrator.py
- tests/test_fglc_repair_loop_cli.py
- src/fglc/repair/__init__.py
- .gitignore
- .agent_tasks/codex_done/TASK_2031_fglc_repair_orchestrator_cli_RESULT.md
## Commands Run
- Get-Content -Raw AGENTS.md
- Get-Content -Raw .agent_tasks\codex_queue\TASK_2031_fglc_repair_orchestrator_cli.md
- git status --short
- Get-Content -Raw docs\EXPERIMENT_REPAIR_LOOP_PLAN.md
- Get-Content -Raw src\fglc\repair\taxonomy.py
- Get-Content -Raw src\fglc\repair\compare.py
- Get-Content -Raw src\fglc\repair\ledger.py
- Get-Content -Raw src\fglc\repair\diagnose.py
- Get-Content -Raw src\fglc\repair\candidates.py
- Get-Content -Raw src\fglc\repair\ranker.py
- Read all FILES_ALLOWED paths that existed before editing
- New-Item -ItemType Directory -Force scripts\fglc, configs\fglc, outputs\repair
- New-Item -ItemType File -Force outputs\repair\.gitkeep
- .venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_orchestrator.py tests\test_fglc_repair_loop_cli.py
- .venv\Scripts\python.exe -m pytest -q tests\test_fglc_forbidden_field_sync.py
- $env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests\test_fglc_forbidden_field_sync.py
- .venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); sys.path.insert(0, '.'); import fglc.repair.orchestrator; import scripts.fglc.repair_loop; assert 'torch' not in sys.modules; assert 'maniskill' not in sys.modules; assert 'numpy' not in sys.modules"
- git status --short --untracked-files=all
- git diff -- src\fglc\repair\orchestrator.py scripts\fglc\repair_loop.py src\fglc\repair\__init__.py .gitignore tests\test_fglc_repair_orchestrator.py tests\test_fglc_repair_loop_cli.py configs\fglc\smoke_4060.yaml
## Tests Run (pass/fail)
- PASS: .venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_orchestrator.py tests\test_fglc_repair_loop_cli.py
- PASS: $env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests\test_fglc_forbidden_field_sync.py
- PASS: import guard confirmed torch, maniskill, and numpy were not imported by orchestrator.py or repair_loop.py.
- NOTE: Bare forbidden-field guard invocation failed before PYTHONPATH was set because that legacy test does not add src to sys.path; the contract passed with PYTHONPATH=src and no forbidden-field leakage was detected.
## Evidence (log paths, metric values)
- Required repair tests: 12 passed.
- Forbidden-field sync guard with PYTHONPATH=src: 18 passed, 14 skipped.
- Stop conditions covered by tests: hook_blocked, target_reached, wall_clock, consecutive_inconclusive, max_iter.
- Ledger validation: orchestrator tests validate emitted ledger lines with validate_ledger_line().
## Risks / Open Questions
- scripts/fglc/repair_loop.py uses argparse because the TASK explicitly requires argparse parser behavior and SystemExit(2) handling.
- outputs/repair/.gitkeep must be force-added because the existing outputs/* ignore rule hides the directory; .gitignore was changed only by appending the requested negation line.
## Patch Review Notes for Claude Code
- Existing repair modules taxonomy.py, compare.py, ledger.py, diagnose.py, candidates.py, and ranker.py were read for signatures but not modified.
- run_repair_loop creates cfg.output_root before ledger writes and initializes metrics_before from baseline metrics before the main loop.
- CLI mock scenarios use deterministic closure constants and do not call training code.
## Accept/Reject Recommendation
Accept.
