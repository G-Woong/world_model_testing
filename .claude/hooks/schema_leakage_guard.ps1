# FRCG-WM: PreToolUse Edit/Write — schema leakage context guard
# BLOCK: forbidden fields in agent observation / build_agent_observation / dataloader return context.
# WARN: forbidden field token appears but not in a dangerous context.

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

# Only scan leakage-sensitive paths
$sensitivePatterns = @(
    "src[/\\]frcgw[/\\]schemas[/\\]",
    "src[/\\]frcgw[/\\]data[/\\]",
    "src[/\\]frcgw[/\\]text_env[/\\]collector\.py",
    "src[/\\]frcgw[/\\]gui_env[/\\]collector\.py",
    "src[/\\]frcgw[/\\]logging[/\\]"
)

$isSensitive = $false
foreach ($p in $sensitivePatterns) {
    if ($fp -match $p) { $isSensitive = $true; break }
}
if (-not $isSensitive) { exit 0 }

# Forbidden field tokens
$forbiddenTokens = @(
    "true_regime", "true_control_grammar", "true_change_point",
    "true_reveal_vs_shift", "true_wrong_hypothesis",
    "counterfactual_action_effects", "counterfactual_progress_delta",
    "counterfactual_failure_risk", "counterfactual_best_alternative",
    "oracle_regime_action", "oracle_grammar_action", "oracle_best_action",
    "split_id", "ood_type", "template_id", "policy_id"
)

# Dangerous context patterns (BLOCK conditions)
$dangerousContextPatterns = @(
    "build_agent_observation",
    "AGENT_OBSERVATION.*=.*true_",
    "agent_input.*update.*true_",
    "agent_obs\[",
    "return.*obs.*true_",
    "__getitem__.*true_",
    "collate_fn.*true_",
    "forward\(.*true_"
)

$newStr = ""
if ($data.tool_input.new_string) {
    $newStr = [string]$data.tool_input.new_string
} elseif ($data.tool_input.content) {
    $newStr = [string]$data.tool_input.content
}

if (-not $newStr) { exit 0 }

$foundTokens = @()
foreach ($token in $forbiddenTokens) {
    if ($newStr -match $token) { $foundTokens += $token }
}

if ($foundTokens.Count -eq 0) { exit 0 }

# Check dangerous context
$isDangerous = $false
foreach ($ctx in $dangerousContextPatterns) {
    if ($newStr -match $ctx) { $isDangerous = $true; break }
}

if ($isDangerous) {
    Write-Output "[FRCG-WM BLOCK] Forbidden field in agent observation / dataloader context detected."
    Write-Output "  File: $fp"
    Write-Output "  Fields: $($foundTokens -join ', ')"
    Write-Output "  -> These fields must NOT enter build_agent_observation, __getitem__, collate_fn, or forward input."
    Write-Output "  -> Use build_agent_observation() to strip hidden labels before returning obs."
    Write-Output "  -> Run tests/test_visibility_contract.py + test_leakage_auditor.py after fix."
    exit 1
}

# Soft warning for non-dangerous occurrence (definition/comment context)
Write-Output "[FRCG-WM WARN] Forbidden field token in sensitive file: $fp"
Write-Output "  Fields: $($foundTokens -join ', ')"
Write-Output "  -> Verify these fields stay in TRAINING_SUPERVISION/EVALUATION_ONLY/COUNTERFACTUAL_ONLY buckets."
Write-Output "  -> NOT blocked (definition context) — but re-run leakage tests after this change."
exit 0
