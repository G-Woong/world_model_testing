# FRCG-WM: PostToolUse Edit/Write/NotebookEdit — targeted test recommendation
# Warns only. Does NOT auto-run tests (too slow per edit). Recommends specific testcases.

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

# File → target test mapping
$mappings = @(
    @{
        Pattern = "src[/\\]frcgw[/\\]schemas[/\\]"
        Tests   = "tests/test_visibility_contract.py tests/test_episode_schema.py tests/test_counterfactual_exclusion.py"
    },
    @{
        Pattern = "src[/\\]frcgw[/\\]data[/\\]leakage_auditor\.py"
        Tests   = "tests/test_leakage_auditor.py"
    },
    @{
        Pattern = "src[/\\]frcgw[/\\]data[/\\]"
        Tests   = "tests/test_leakage_auditor.py"
    },
    @{
        Pattern = "src[/\\]frcgw[/\\]text_env[/\\]"
        Tests   = "tests/test_text_env.py  (create if P2 started)"
    },
    @{
        Pattern = "src[/\\]frcgw[/\\]planning[/\\]falsification\.py"
        Tests   = "tests/test_falsification.py  (P3+)"
    },
    @{
        Pattern = "src[/\\]frcgw[/\\]planning[/\\]decision_gate\.py"
        Tests   = "tests/test_decision_gate.py  (P3+)"
    },
    @{
        Pattern = "src[/\\]frcgw[/\\]evaluation[/\\]"
        Tests   = "tests/test_metrics.py tests/test_eval_runner.py  (P3+)"
    },
    @{
        Pattern = "configs[/\\].+\.yaml$"
        Tests   = "tests/test_config_validation.py  (if exists)"
    }
)

$matched = $false
foreach ($m in $mappings) {
    if ($fp -match $m.Pattern) {
        Write-Output "[FRCG-WM POST] Modified: $fp"
        Write-Output "  -> Recommended targeted tests: $($m.Tests)"
        Write-Output "  -> Run: pytest $($m.Tests) -v --tb=short"
        $matched = $true
    }
}

exit 0
