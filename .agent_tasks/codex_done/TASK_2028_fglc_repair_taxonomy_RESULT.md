# Codex Task Report ??TASK_2028 fglc_repair_taxonomy
## Summary
BLOCKED: Implemented the requested repair taxonomy files and tests, but did not commit because the exact required test launcher `.venv\Scripts\pytest.exe` exits with code 1 and no stdout/stderr before running tests. The same tests pass through `.venv\Scripts\python.exe -m pytest`, indicating a broken venv pytest launcher outside FILES_ALLOWED.
## Files Changed
- `src/fglc/repair/__init__.py` added
- `src/fglc/repair/taxonomy.py` added
- `tests/test_fglc_repair_taxonomy.py` added
- `.agent_tasks/codex_done/TASK_2028_fglc_repair_taxonomy_RESULT.md` added
## Commands Run
- `Get-Content -Raw AGENTS.md`
- `Get-Content -Raw .agent_tasks\codex_queue\TASK_2028_fglc_repair_taxonomy.md`
- `git status --short`
- `Get-Content -Raw docs\idea\FGLC_FAILURE_TAXONOMY.md`
- `Get-Content -Raw docs\EXPERIMENT_REPAIR_LOOP_PLAN.md`
- checked all FILES_ALLOWED target source/test files before edit; all were missing
- checked existence of source markdown reference paths under `docs/`
- `rg "repair|FailureCause|applicable_phases_for|FGLC_FAILURE_TAXONOMY" -n src tests docs -g '!docs/idea/FGLC_FAILURE_TAXONOMY.md' -g '!docs/EXPERIMENT_REPAIR_LOOP_PLAN.md'`
- `Test-Path tests\test_fglc_forbidden_field_sync.py`
- `New-Item -ItemType Directory -Force src\fglc\repair`
- `.venv\Scripts\pytest.exe -q tests\test_fglc_repair_taxonomy.py`
- `.venv\Scripts\pytest.exe -q tests\test_fglc_forbidden_field_sync.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_taxonomy.py`
- `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests\test_fglc_forbidden_field_sync.py`
- checked `.venv\Scripts\pytest.exe` metadata and reran via PowerShell, `cmd /c`, and `System.Diagnostics.ProcessStartInfo`
## Tests Run (pass/fail)
- FAIL: `.venv\Scripts\pytest.exe -q tests\test_fglc_repair_taxonomy.py` exited 1 with no stdout/stderr.
- FAIL: `.venv\Scripts\pytest.exe -q tests\test_fglc_forbidden_field_sync.py` exited 1 with no stdout/stderr.
- PASS: `.venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_taxonomy.py` -> `8 passed`.
- PASS: `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests\test_fglc_forbidden_field_sync.py` -> `18 passed, 14 skipped`.
## Evidence (log paths, metric values)
- No log files were generated.
- Direct launcher evidence: `.venv\Scripts\pytest.exe` exists, size `108373`, pytest import via `.venv\Scripts\python.exe` reports version `9.0.3`; `System.Diagnostics.ProcessStartInfo` captured `EXIT=1`, `STDOUT=[]`, `STDERR=[]`.
- Taxonomy test evidence: `.venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_taxonomy.py` returned `........ [100%]`.
- Forbidden-field sync evidence: `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -q tests\test_fglc_forbidden_field_sync.py` returned `..................ssssssssssssss [100%]`.
## Risks / Open Questions
- Required test command uses `.venv\Scripts\pytest.exe`, but that launcher appears broken independently of this patch. `.venv/` is explicitly forbidden to modify, so I could not repair or reinstall the launcher.
- The existing repo is a `src/` layout and is not installed into this venv. The new taxonomy test inserts `src` into `sys.path` locally because editing shared pytest config or installing the package was outside scope.
## Patch Review Notes for Claude Code
- `FailureCauseId` contains exactly 20 `str, Enum` members from the SSoT.
- `CAUSE_METADATA` covers all 20 causes, keeps `IMPLEMENTATION_BUG_SUSPECTED.source_md_refs == ()`, and all other refs point to existing docs paths.
- `DETECTION_THRESHOLDS` uses only `float` values from the SSoT numeric thresholds, with `{}` for `IMPLEMENTATION_BUG_SUSPECTED`.
- `applicable_phases_for()` derives active causes from `CAUSE_METADATA`.
## Accept/Reject Recommendation
Reject for now due to blocked required-test launcher. The code patch itself passes equivalent venv module-based pytest checks, but I did not commit because the exact required pytest executable command failed and `.venv` is outside FILES_ALLOWED.
