# scripts/turn_cleanup.ps1 — "턴별정리" repo-wide cleanup orchestrator
# Sequence: audit → cache cleanup → trash → archive sweep → tests
# Usage: pwsh scripts/turn_cleanup.ps1
# Policy: docs/orchestration/14_REPORT_LIFECYCLE_POLICY.md §3.5
#         docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md §Phase G

$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$pyExe = Join-Path $projectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $pyExe)) { $pyExe = "python" }

Write-Host "== Turn cleanup (repo-wide) ==" -ForegroundColor Cyan

& $pyExe (Join-Path $projectDir "scripts\lifecycle_audit_v2.py") --dry-run --scope repo --json `
    | Out-File (Join-Path $projectDir "outputs\lifecycle\turn_cleanup_audit.json") -Encoding utf8

& $pyExe (Join-Path $projectDir "scripts\lifecycle_trash_v2.py") cleanup-cache --apply --allow-dirty --confirm-cache-cleanup

& $pyExe (Join-Path $projectDir "scripts\lifecycle_trash_v2.py") trash --scope repo --apply --confirm-controlled-trash

& $pyExe (Join-Path $projectDir "scripts\archive_sweep_v2.py") sweep --scope repo --apply --confirm-auto-archive

& $pyExe -m pytest -q `
    tests/test_lifecycle_audit_v2.py `
    tests/test_archive_sweep_v2.py `
    tests/test_lifecycle_phase2_hooks.py `
    tests/test_lifecycle_phase3_trash.py `
    tests/test_lifecycle_phase3_restore.py `
    tests/test_lifecycle_phase3_promote.py

Write-Host "== Turn cleanup complete ==" -ForegroundColor Green
