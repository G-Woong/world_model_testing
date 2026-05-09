# FRCG-WM: SubagentStop — subagent responsibility audit
# Diagnostic only (Stop events cannot block). Warns if read-only subagents made writes.

$inputRaw = ""
try {
    if ([Console]::IsInputRedirected) { $inputRaw = [Console]::In.ReadToEnd() }
} catch { }

$data = $null
if ($inputRaw -and $inputRaw.Trim()) {
    try { $data = $inputRaw | ConvertFrom-Json } catch { }
}
if (-not $data) { exit 0 }

# Read-only subagents that must not produce edits
$readOnlyAgents = @(
    "frcgw-data-leakage-auditor",
    "frcgw-code-reviewer",
    "frcgw-context-router",
    "frcgw-related-work-scout",
    "frcgw-plugin-security-auditor"
)

$agentName = ""
if ($data.agent_name) { $agentName = [string]$data.agent_name }
if (-not $agentName -and $data.subagent_name) { $agentName = [string]$data.subagent_name }

# Check if result mentions file edits
$resultText = ""
if ($data.result) { $resultText = [string]$data.result }

$editKeywords = @("Edit\(", "Write\(", "NotebookEdit\(", "file_path.*modified", "created successfully")

$hasEdits = $false
foreach ($kw in $editKeywords) {
    if ($resultText -match $kw) { $hasEdits = $true; break }
}

if ($agentName -and ($readOnlyAgents -contains $agentName) -and $hasEdits) {
    Write-Output "[FRCG-WM WARN] Read-only subagent '$agentName' appears to have made file edits."
    Write-Output "  -> $agentName is configured as read-only (no Edit/Write)."
    Write-Output "  -> Review the subagent result and verify no unintended modifications occurred."
}

if ($agentName) {
    Write-Output "[FRCG-WM] Subagent '$agentName' completed."
}

exit 0
