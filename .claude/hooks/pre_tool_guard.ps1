# FRCG-WM: PreToolUse guard
# Runs for Bash, Edit, Write, NotebookEdit tool calls.
# Critical blocks: exit 1 (tool is blocked).
# Warnings: exit 0 with message (tool runs but user is alerted).

# --- Session start: run once per day via date sentinel ---
$sentinelDir = "$env:TEMP\frcgwm"
$today       = Get-Date -Format "yyyy-MM-dd"
$sentinel    = "$sentinelDir\session_${today}.lock"
if (-not (Test-Path $sentinelDir)) {
    New-Item -ItemType Directory -Path $sentinelDir -Force | Out-Null
}
if (-not (Test-Path $sentinel)) {
    $sessionScript = Join-Path $PSScriptRoot "session_start_context.ps1"
    if (Test-Path $sessionScript) { & $sessionScript }
    New-Item -Path $sentinel -ItemType File -Force | Out-Null
}

# --- Read stdin JSON ---
$inputRaw = ""
try {
    if ([Console]::IsInputRedirected) { $inputRaw = [Console]::In.ReadToEnd() }
} catch { }

$data = $null
if ($inputRaw -and $inputRaw.Trim()) {
    try { $data = $inputRaw | ConvertFrom-Json } catch { }
}
if (-not $data) { exit 0 }

$toolName  = [string]$data.tool_name
$toolInput = $data.tool_input

# ============================================================
# CRITICAL BLOCKS — exit 1 (tool is not executed)
# ============================================================

if ($toolName -eq "Bash") {
    $cmd = [string]$toolInput.command

    # Block: git push --force
    if ($cmd -match "git\s+push\s+.*(--force|-f)\b") {
        Write-Output "[FRCG-WM BLOCK] git push --force is forbidden."
        Write-Output "  Reason: force-push can overwrite shared history. Use a PR."
        exit 1
    }

    # Block: delete paper_context_ref
    if ($cmd -match "(Remove-Item|rm\b|rmdir|del\b).*paper_context_ref") {
        Write-Output "[FRCG-WM BLOCK] Deleting paper_context_ref/ is forbidden."
        Write-Output "  Reason: these files are the research contract."
        exit 1
    }

    # Block: delete .git
    if ($cmd -match "(Remove-Item|rm\b|rmdir|del\b).*[/\\]\.git\b") {
        Write-Output "[FRCG-WM BLOCK] Deleting .git is forbidden."
        exit 1
    }

    # Block: print .env content
    if ($cmd -match "(cat|type|Get-Content)\s+.*\.env\b") {
        Write-Output "[FRCG-WM BLOCK] Printing .env is forbidden. Never expose secrets in output."
        exit 1
    }

    # Block: raw PAT/token patterns in command text
    if ($cmd -match "ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]+|ghs_[A-Za-z0-9]+") {
        Write-Output "[FRCG-WM BLOCK] Possible PAT/token detected in command. Aborting to prevent secret leakage."
        exit 1
    }

    # ============================================================
    # WARNINGS — exit 0 (tool runs, but user is alerted)
    # ============================================================

    if ($cmd -match "git\s+reset\s+--hard") {
        Write-Output "[FRCG-WM WARN] git reset --hard detected. Confirm explicit user approval exists."
    }

    if ($cmd -match "(train_world_model|generate_dataset|train\.py)") {
        Write-Output "[FRCG-WM WARN] Training/data generation command. Verify all phase gates passed before running."
    }
}

# --- Edit / Write: warn on sensitive file classes ---
if ($toolName -in @("Edit", "Write", "NotebookEdit")) {
    $fp = [string]$toolInput.file_path

    if ($fp -match "configs[/\\][^/\\]+\.yaml$") {
        Write-Output "[FRCG-WM WARN] Config file: $fp — run test_config_validation.py after changes."
    }
    if ($fp -match "paper_context_ref[/\\].+\.md$") {
        Write-Output "[FRCG-WM WARN] Research context MD: $fp — update 00_CONTEXT_INDEX.md if structure changed."
    }
    if ($fp -match "(schemas|dataset_loader|collat)[/\\]") {
        Write-Output "[FRCG-WM WARN] Schema/dataloader: $fp — re-run hidden-label leakage tests."
    }
    if ($fp -match "evaluation[/\\]") {
        Write-Output "[FRCG-WM WARN] Evaluation file: $fp — verify all required baselines/ablations remain intact."
    }
}

exit 0
