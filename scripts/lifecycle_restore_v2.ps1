# scripts/lifecycle_restore_v2.ps1 — Manifest-based file restore from .lifecycle_trash/
#
# Usage (dry-run, default — no -Apply flag):
#   .\scripts\lifecycle_restore_v2.ps1 -Manifest .lifecycle_trash\2026-05\run_...\manifest.json
#
# Usage (actual restore, dual-flag required):
#   .\scripts\lifecycle_restore_v2.ps1 -Manifest <path> -Apply -ConfirmRestore
#
# Policy: docs/orchestration/15_lifecycle_automation_v2_plan.md §5
# Mirrors apply_reviewed_cleanup.ps1 10-Guard pattern (L29-30 StrictMode, L43-46 dual-flag).

param(
    [Parameter(Mandatory = $true)]
    [string]$Manifest,

    # Guard #9: absent = dry-run (default); present = live mode
    [switch]$Apply,

    # Guard #10: second flag required alongside -Apply for actual restore
    [switch]$ConfirmRestore,

    # Allow overwrite of file already present at original_path
    [switch]$ForceRestore,

    # Override repo root (for tests/isolated environments; default: auto-detect from script path)
    [string]$RepoRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Guard #1: Manifest must exist
if (-not (Test-Path $Manifest)) {
    Write-Error "[GUARD-1 FAIL] Manifest not found: $Manifest"
    exit 1
}

# Guard #10: Dual-flag requirement for actual restore
if ($Apply -and -not $ConfirmRestore) {
    Write-Error "[GUARD-10 FAIL] Actual restore requires BOTH -Apply AND -ConfirmRestore."
    exit 1
}

$manifestPath = (Resolve-Path $Manifest).Path
$manifestText = Get-Content $manifestPath -Raw -Encoding utf8
$manifestObj  = $manifestText | ConvertFrom-Json

# Guard #3: Schema version
$schemaVer = $manifestObj.manifest_schema_version
if ($schemaVer -ne "1.0.0") {
    Write-Error "[GUARD-3 FAIL] Unsupported manifest_schema_version: $schemaVer"
    exit 1
}

# Repo root: use override if provided, else two levels up from script (scripts/ -> repo/)
if ($RepoRoot) {
    $repoRoot = (Resolve-Path $RepoRoot).Path
} else {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot  = (Resolve-Path (Join-Path $scriptDir "..")).Path
}

$isDryRun = -not $Apply

Write-Host ""
if ($isDryRun) {
    Write-Host "=== lifecycle_restore_v2.ps1 [DRY-RUN MODE] ==="
    Write-Host "    Pass -Apply -ConfirmRestore to actually restore."
} else {
    Write-Host "=== lifecycle_restore_v2.ps1 [LIVE RESTORE MODE] ==="
    Write-Host "    Warning: files will be moved from .lifecycle_trash/ to original locations."
}
Write-Host "    Manifest : $manifestPath"
Write-Host "    run_id   : $($manifestObj.run_id)"
Write-Host "    files    : $($manifestObj.files.Count)"
Write-Host ""

function Get-FileSha256 {
    param([string]$FilePath)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($FilePath)
    try {
        $bytes = $sha256.ComputeHash($stream)
        return ([BitConverter]::ToString($bytes) -replace '-', '').ToLower()
    } finally {
        $stream.Close()
        $sha256.Dispose()
    }
}

$restored = 0
$skipped  = 0
$errors   = 0

foreach ($file in $manifestObj.files) {
    $trashRel    = $file.trash_path -replace '/', '\'
    $originalRel = $file.original_path -replace '/', '\'
    $trashAbs    = Join-Path $repoRoot $trashRel
    $originalAbs = Join-Path $repoRoot $originalRel

    Write-Host "  -> $($file.original_path)"

    # Guard #4: trash_path must exist
    if (-not (Test-Path $trashAbs)) {
        Write-Host "     [SKIP] trash file not found: $trashAbs"
        $skipped++
        continue
    }

    # Guard #5: sha256 integrity check (must match sha256_after stored in manifest)
    $sha256Actual = Get-FileSha256 -FilePath $trashAbs
    if ($sha256Actual -ne $file.sha256_after) {
        Write-Host "     [ERROR] sha256 mismatch: expected=$($file.sha256_after) actual=$sha256Actual"
        $errors++
        continue
    }

    # Guard #6: original_path must be inside repo root
    $originalResolved = [System.IO.Path]::GetFullPath($originalAbs)
    if (-not $originalResolved.StartsWith($repoRoot)) {
        Write-Host "     [ERROR] original_path outside repo root: $($file.original_path)"
        $errors++
        continue
    }

    # Guard #7: overwrite protection (skip unless -ForceRestore)
    if (Test-Path $originalAbs) {
        if (-not $ForceRestore) {
            Write-Host "     [SKIP] file already at original_path (use -ForceRestore to overwrite)"
            $skipped++
            continue
        }
        Write-Host "     [WARN] -ForceRestore: overwriting existing file at $originalAbs"
    }

    if ($isDryRun) {
        Write-Host "     [DRY-RUN] would restore: $trashAbs -> $originalAbs"
        $restored++
        continue
    }

    # Guard #8: create parent dir if needed, then move
    $parentDir = Split-Path -Parent $originalAbs
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }
    Move-Item -Path $trashAbs -Destination $originalAbs -Force

    # Guard #8b: verify sha256_before after restore
    $sha256Post = Get-FileSha256 -FilePath $originalAbs
    if ($sha256Post -ne $file.sha256_before) {
        Write-Host "     [ERROR] post-restore sha256 mismatch — file may be corrupt"
        $errors++
    } else {
        Write-Host "     [OK] restored: $($file.original_path)"
        $restored++
    }
}

Write-Host ""
Write-Host "--- Summary ---"
Write-Host "  Restored : $restored"
Write-Host "  Skipped  : $skipped"
Write-Host "  Errors   : $errors"
Write-Host ""
if ($isDryRun) {
    Write-Host "=== DRY-RUN complete (0 files actually moved) ==="
} else {
    Write-Host "=== LIVE RESTORE complete ==="
}

if ($errors -gt 0) {
    exit 1
}
exit 0
