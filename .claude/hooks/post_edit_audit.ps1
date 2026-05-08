# FRCG-WM: PostToolUse audit reminder
# Runs after Edit, Write, NotebookEdit.
# Always exits 0 (non-blocking, informational only).

$inputRaw = ""
try {
    if ([Console]::IsInputRedirected) { $inputRaw = [Console]::In.ReadToEnd() }
} catch { }

$data = $null
if ($inputRaw -and $inputRaw.Trim()) {
    try { $data = $inputRaw | ConvertFrom-Json } catch { }
}
if (-not $data) { exit 0 }

$fp = [string]$data.tool_input.file_path
if (-not $fp) { exit 0 }

# --- Python files ---
if ($fp -match "\.py$") {
    Write-Output "[FRCG-WM POST] Python modified: $fp"

    # Leakage-sensitive modules
    if ($fp -match "(schemas|dataset_loader|collat|data\.py|fields\.py)") {
        Write-Output "  -> LEAKAGE RISK: run tests/test_visibility_contract.py + tests/test_counterfactual_exclusion.py"
    }
    # Evaluation module
    if ($fp -match "(eval|evaluation)[/\\]") {
        Write-Output "  -> BASELINE RISK: confirm no-control-grammar, no-falsification, verifier-only ablations intact."
    }
    # Planner module
    if ($fp -match "planner[/\\]") {
        Write-Output "  -> PLANNING: ensure falsification gate and uncertainty gate are separate and not collapsed."
    }
}

# --- Config files ---
if ($fp -match "configs[/\\][^/\\]+\.yaml$") {
    Write-Output "[FRCG-WM POST] Config modified: $fp"
    Write-Output "  -> Run tests/test_config_validation.py if it exists."
}

# --- Research context MDs ---
if ($fp -match "paper_context_ref[/\\].+\.md$") {
    Write-Output "[FRCG-WM POST] Research context MD modified: $fp"
    Write-Output "  -> Update 00_CONTEXT_INDEX.md (section 3 Memory Map) if file added/renamed."
    Write-Output "  -> Never silently change scientific definitions (regime, control grammar, falsification, etc.)."
}

# --- Schema / data source ---
if ($fp -match "(frcgw|frcgwm)[/\\](schemas|data|rg4f)[/\\]") {
    Write-Output "[FRCG-WM POST] Schema/data file modified: $fp"
    Write-Output "  -> LEAKAGE RISK: re-run full leakage audit."
}

# --- Settings / MCP config ---
if ($fp -match "(settings\.json|\.mcp\.json)$") {
    Write-Output "[FRCG-WM POST] Claude/MCP config modified: $fp"
    Write-Output "  -> Verify no secrets (PAT, API key, token) were written to this file."
    Write-Output "  -> Run: Select-String -Path $fp -Pattern 'ghp_|github_pat_|sk-|TOKEN'"
}

exit 0
