# FRCG-WM: PreCompact — phase handoff to PHASE_PROGRESS.md
# Appends current phase status to plans/PHASE_PROGRESS.md before context compaction.

$timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")

# Read current phase from sentinel files
$sentinelDir = "outputs/phase_gates"
$passedPhases = @()
if (Test-Path $sentinelDir) {
    Get-ChildItem "$sentinelDir/*.passed" -ErrorAction SilentlyContinue | ForEach-Object {
        $passedPhases += $_.BaseName
    }
}

$progressPath = "plans/PHASE_PROGRESS.md"
if (-not (Test-Path $progressPath)) {
    Write-Output "[FRCG-WM] plans/PHASE_PROGRESS.md not found — skipping handoff."
    exit 0
}

$entry = @"

---
compaction_handoff: $timestamp
passed_gates: $($passedPhases -join ', ')
note: Context compaction triggered. Verify phase status from sentinel files and this log on resume.
"@

try {
    Add-Content -Path $progressPath -Value $entry
    Write-Output "[FRCG-WM] Phase handoff written to plans/PHASE_PROGRESS.md at $timestamp"
    Write-Output "  Passed gates: $($passedPhases -join ', ')"
} catch {
    Write-Output "[FRCG-WM WARN] Could not write to plans/PHASE_PROGRESS.md: $_"
}

exit 0
