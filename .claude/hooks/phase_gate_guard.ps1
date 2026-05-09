# FRCG-WM: PreToolUse Bash — phase gate sentinel guard
# Blocks main training/data generation scripts if previous phase gate sentinel is absent.
# Exit 1 = BLOCK. Exit 0 = allow.

$inputRaw = ""
try {
    if ([Console]::IsInputRedirected) { $inputRaw = [Console]::In.ReadToEnd() }
} catch { }

$data = $null
if ($inputRaw -and $inputRaw.Trim()) {
    try { $data = $inputRaw | ConvertFrom-Json } catch { }
}
if (-not $data) { exit 0 }

$toolName = [string]$data.tool_name
if ($toolName -ne "Bash") { exit 0 }

$cmd = [string]$data.tool_input.command
if (-not $cmd) { exit 0 }

# Map: script pattern → required sentinel
$gates = @(
    @{ Pattern = "scripts[/\\]01_generate_text_data\.py";   Sentinel = "P1"; RequiredPhase = "P0" },
    @{ Pattern = "scripts[/\\]02_train_text_smoke\.py";     Sentinel = "P2"; RequiredPhase = "P2" },
    @{ Pattern = "scripts[/\\]03_eval_text_smoke\.py";      Sentinel = "P2"; RequiredPhase = "P2" },
    @{ Pattern = "scripts[/\\]04_generate_gui_mve_data\.py"; Sentinel = "P3"; RequiredPhase = "P3" },
    @{ Pattern = "scripts[/\\]05_validate_dataset\.py";     Sentinel = "P4"; RequiredPhase = "P4" },
    @{ Pattern = "scripts[/\\]06_train_vlm_mve\.py";        Sentinel = "P4"; RequiredPhase = "P4" },
    @{ Pattern = "scripts[/\\]07_eval_vlm_mve\.py";         Sentinel = "P5"; RequiredPhase = "P5" },
    @{ Pattern = "scripts[/\\]08_run_core_ablations\.py";   Sentinel = "P6"; RequiredPhase = "P6" },
    @{ Pattern = "scripts[/\\]09_generate_reports\.py";     Sentinel = "P7"; RequiredPhase = "P7" }
)

foreach ($g in $gates) {
    if ($cmd -match $g.Pattern) {
        $sentinelPath = "outputs/phase_gates/$($g.Sentinel).passed"
        if (-not (Test-Path $sentinelPath)) {
            Write-Output "[FRCG-WM BLOCK] Phase gate sentinel missing: $sentinelPath"
            Write-Output "  -> Phase $($g.RequiredPhase) gate must PASS before running this script."
            Write-Output "  -> Run /frcgw-phase-check to review gate status."
            Write-Output "  -> To override intentionally: /frcgw-phase-check --override <reason>"
            exit 1
        }
    }
}

exit 0
