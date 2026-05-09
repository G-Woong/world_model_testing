# FRCG-WM: UserPromptSubmit phase/task router hint
# Fires on every user prompt. Light-weight keyword scan — warn only, never blocks.

$inputRaw = ""
try {
    if ([Console]::IsInputRedirected) { $inputRaw = [Console]::In.ReadToEnd() }
} catch { }

$data = $null
if ($inputRaw -and $inputRaw.Trim()) {
    try { $data = $inputRaw | ConvertFrom-Json } catch { }
}
if (-not $data) { exit 0 }

$prompt = [string]$data.prompt
if (-not $prompt) { exit 0 }

# Phase keywords → routing hint
if ($prompt -match "\bP[0-8]\b|phase\s*[0-8]|start\s+phase|end\s+phase|next\s+phase") {
    Write-Output "[FRCG-WM] Phase keyword detected."
    Write-Output "  -> Read paper_context_ref/00_CONTEXT_INDEX.md §5 for the correct phase gate and MD bundle."
    Write-Output "  -> Use /frcgw-phase-check to verify gate status before proceeding."
}

# Data/schema keywords
if ($prompt -match "schema|dataloader|collat|collector|leakage|visibility|hidden label|counterfactual") {
    Write-Output "[FRCG-WM] Data/schema keyword detected."
    Write-Output "  -> Read 06_DATA_SCHEMA_AND_LABELING.md §4 visibility contract before editing."
    Write-Output "  -> Run tests/test_visibility_contract.py + test_leakage_auditor.py after changes."
}

# Baseline/ablation keywords
if ($prompt -match "baseline|ablation|verifier.only|no.control.grammar|no.falsification|always.plan") {
    Write-Output "[FRCG-WM] Baseline/ablation keyword detected."
    Write-Output "  -> Read 10_EVALUATION_BASELINE_ABLATION.md §7~§8 must-not-disappear list."
}

# Plugin keywords
if ($prompt -match "plugin|mcp\s+add|marketplace|superpowers|playwright|github mcp") {
    Write-Output "[FRCG-WM] Plugin/MCP keyword detected."
    Write-Output "  -> Run /frcgw-plugin-audit BEFORE any install."
    Write-Output "  -> Current policy: 0 external plugins installed. See plans/PLUGIN_AUDIT_REPORT.md."
}

exit 0
