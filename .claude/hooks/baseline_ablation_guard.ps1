# FRCG-WM: PreToolUse Edit/Write — baseline/ablation drop warning
# WARN (not BLOCK) when a known baseline/ablation name appears deleted in the new content.
# BLOCK does not apply because rename is a legitimate operation — user must confirm.

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
if ($toolName -notin @("Edit", "Write")) { exit 0 }

$fp = [string]$data.tool_input.file_path
if (-not $fp) { exit 0 }

# Only scan evaluation/ablation files
$isTarget = ($fp -match "evaluation[/\\]baselines\.py" -or
             $fp -match "evaluation[/\\]ablations\.py" -or
             $fp -match "configs[/\\]ablation.*\.yaml" -or
             $fp -match "evaluation[/\\]eval_runner\.py")

if (-not $isTarget) { exit 0 }

# Must-not-disappear baselines
$baselines = @(
    "frozen.base", "verifier.only", "next.state.wm.only", "uncertainty.gated",
    "always.plan", "random.alternative", "compute.matched", "oracle.regime",
    "oracle.control.grammar", "oracle.alternative"
)

# Must-not-disappear ablations
$ablations = @(
    "no.control.grammar", "merged.regime", "collapsed.latent",
    "no.falsification", "uncertainty.instead", "no.alternative.hypothesis",
    "random.alternative", "no.rollout", "no.rewrite",
    "no.progress", "no.compute.gate"
)

# Get old_string (what is being removed)
$oldStr = ""
if ($data.tool_input.old_string) {
    $oldStr = [string]$data.tool_input.old_string
}

if (-not $oldStr) { exit 0 }

$newStr = ""
if ($data.tool_input.new_string) {
    $newStr = [string]$data.tool_input.new_string
}

$warnings = @()

foreach ($b in $baselines) {
    if ($oldStr -match $b) {
        # Check if new content still has similar pattern (rename case)
        $normalizedB = $b -replace "\.", "[^a-zA-Z0-9]?"
        if (-not ($newStr -match $normalizedB)) {
            $warnings += "baseline: $b"
        }
    }
}

foreach ($a in $ablations) {
    if ($oldStr -match $a) {
        $normalizedA = $a -replace "\.", "[^a-zA-Z0-9]?"
        if (-not ($newStr -match $normalizedA)) {
            $warnings += "ablation: $a"
        }
    }
}

if ($warnings.Count -gt 0) {
    Write-Output "[FRCG-WM WARN] Possible baseline/ablation removal detected in: $fp"
    foreach ($w in $warnings) {
        Write-Output "  -> Suspected removal: $w"
    }
    Write-Output "  -> If renaming: confirm new name preserves scientific identity."
    Write-Output "  -> If removing: the corresponding claim CANNOT be made without this baseline/ablation."
    Write-Output "  -> See 10_EVALUATION_BASELINE_ABLATION.md §7~§8 must-not-disappear list."
}

exit 0
