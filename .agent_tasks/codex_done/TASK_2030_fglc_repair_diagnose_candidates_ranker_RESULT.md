# Codex Task Report ??TASK_2030 fglc_repair_diagnose_candidates_ranker
## Summary
Implemented the Step 7 repair diagnosis, candidate generation, and candidate ranking modules. Added focused unit tests covering the required diagnosis rules, phase filtering, candidate table behavior, ranking validation, and diagnose-to-rank round trip.
## Files Changed
- src/fglc/repair/diagnose.py
- src/fglc/repair/candidates.py
- src/fglc/repair/ranker.py
- tests/test_fglc_repair_diagnose.py
- tests/test_fglc_repair_candidates.py
- tests/test_fglc_repair_ranker.py
- .agent_tasks/codex_done/TASK_2030_fglc_repair_diagnose_candidates_ranker_RESULT.md
## Commands Run
- Get-Content -Raw AGENTS.md
- Get-Content -Raw .agent_tasks/codex_queue/TASK_2030_fglc_repair_diagnose_candidates_ranker.md
- git status --short
- Get-ChildItem src\fglc\repair; Get-ChildItem tests -Filter test_fglc_repair_*
- Get-Content -Raw src\fglc\repair\taxonomy.py
- Select-String -Path docs\EXPERIMENT_REPAIR_LOOP_PLAN.md -Pattern 'D\.2|D\.3|D\.1|## D|### D' -Context 0,80
- Checked all FILES_ALLOWED paths for existing contents
- Test-Path tests\test_fglc_forbidden_field_sync.py
- rg "diagnose\(|candidates_for\(|rank\(" src tests
- .venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_diagnose.py tests\test_fglc_repair_candidates.py tests\test_fglc_repair_ranker.py
- .venv\Scripts\python.exe -m pytest -q tests\test_fglc_forbidden_field_sync.py
- $env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests\test_fglc_forbidden_field_sync.py
- rg "src\.fglc|repair\.compare|repair\.ledger|repair.__init__|fglc\.schemas|outputs/|data/|configs/" src\fglc\repair\diagnose.py src\fglc\repair\candidates.py src\fglc\repair\ranker.py tests\test_fglc_repair_diagnose.py tests\test_fglc_repair_candidates.py tests\test_fglc_repair_ranker.py
## Tests Run (pass/fail)
- PASS: .venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_diagnose.py tests\test_fglc_repair_candidates.py tests\test_fglc_repair_ranker.py (24 passed)
- FAIL then PASS with import path: .venv\Scripts\python.exe -m pytest -q tests\test_fglc_forbidden_field_sync.py initially failed with ModuleNotFoundError: No module named 'fglc'; rerun with PYTHONPATH=src passed (18 passed, 14 skipped).
## Evidence (log paths, metric values)
- Required focused tests: 24 passed.
- Forbidden-field guard with PYTHONPATH=src: 18 passed, 14 skipped.
- Restricted import/path scan: no matches.
- No files written under outputs/, data/, configs/, or docs/.
## Risks / Open Questions
- The standalone forbidden-field sync test requires PYTHONPATH=src in this environment; this was not changed because its file is outside FILES_ALLOWED.
- Candidate costs, risks, and expected signals are heuristic values as specified by the task.
## Patch Review Notes for Claude Code
- diagnose.py implements exactly seven _fire_* helpers for D.2 rows and filters by applicable phases from taxonomy.py.
- candidates.py hard-codes D.3 cause-to-candidate mappings and deduplicates repeated causes while preserving input order.
- ranker.py validates candidate fields, sorts lexicographically by cost, risk, negative expected signal, and id, then assigns normalized scores.
- No changes were made to __init__.py, taxonomy.py, compare.py, ledger.py, schemas, docs, configs, outputs, data, or scripts.
## Accept/Reject Recommendation
ACCEPT
