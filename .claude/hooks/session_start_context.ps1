# FRCG-WM: Session start context check
# Called from pre_tool_guard.ps1 on first tool use per day.
# Checks that required project files exist and outputs research contract reminders.

$cwd = (Get-Location).Path

if ($cwd -notlike "*NeurIPS2026*") {
    Write-Output "[FRCG-WM WARN] CWD does not contain 'NeurIPS2026'. Expected project root. Current: $cwd"
}

$required = @(
    @{ Path = "CLAUDE.md";                                                         Label = "CLAUDE.md" },
    @{ Path = "paper_context_ref\00_CONTEXT_INDEX.md";                             Label = "00_CONTEXT_INDEX" },
    @{ Path = "paper_context_ref\13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md";          Label = "13_EXECUTION_ROADMAP" },
    @{ Path = "paper_context_ref\14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md";    Label = "14_TRD" },
    @{ Path = "paper_context_ref\15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md";          Label = "15_TDD" }
)

$missing = @()
foreach ($item in $required) {
    if (-not (Test-Path $item.Path)) { $missing += $item.Label }
}

if ($missing.Count -gt 0) {
    Write-Output "[FRCG-WM WARN] Missing required files: $($missing -join ', ')"
    Write-Output "  -> Re-create or restore these before continuing."
} else {
    Write-Output "[FRCG-WM] Read CLAUDE.md + paper_context_ref/00_CONTEXT_INDEX.md before task-specific work."
    Write-Output "[FRCG-WM] Do not skip schema/leakage gates or phase order."
    Write-Output "[FRCG-WM] Hidden labels must never enter inference input."
    Write-Output "[FRCG-WM] Forbidden fields: true_regime, true_control_grammar, oracle_*, split_id, seed, ood_type, template_id."
}
