#Requires -Version 5.1
<#
.SYNOPSIS
    Claude→Codex orchestration harness for FRCG-WM.

.DESCRIPTION
    Modes:
      init          Create .agent_tasks/ dirs, prompt template, update .gitignore
      assign        Validate TASK file, record BASE_SHA, git commit in Claude worktree
      dispatch      Divergence check, ff-only sync, codex exec via stdin pipe
      verify        Forbidden path check, RESULT.md check (BASE_SHA-anchored)
      prepare-merge git merge --no-commit --no-ff codex-work → Claude review
      run           assign → dispatch → verify → prepare-merge sequentially

    Exit codes:
      0   success
      10  precondition failure (dirty worktree, lock exists, divergence, ff-only failed)
      20  TASK file schema violation
      30  codex exec failure or timeout
      40  Codex commit missing, forbidden path violated, or RESULT.md missing
      50  merge conflict

    Source MD: paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP.md
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('init','assign','dispatch','verify','prepare-merge','run')]
    [string]$Mode,

    [string]$TaskName        = '',
    [string]$TaskFile        = '',
    [int]   $TaskNumber      = -1,
    [switch]$AllowPaperContextRef,
    [string]$CodexModel      = 'gpt-5.5',
    [string]$CodexSandbox    = 'workspace-write',
    [int]   $TimeoutMinutes  = 60,
    [switch]$DryRun,
    # Use only in local dev/smoke-test: bypasses all sandbox restrictions so
    # Codex can write to git worktree metadata outside $CODEX_ROOT.
    [switch]$BypassSandbox,
    # Override the Claude-side branch Codex should merge into.
    # Falls back to $env:FRCGW_CLAUDE_BRANCH, then 'solo/p3-final-boss-cleared'.
    [string]$ClaudeBranch    = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
$CLAUDE_ROOT    = 'C:\Users\computer\Desktop\ICLR_WM_claude-code'
$CODEX_ROOT     = 'C:\Users\computer\Desktop\ICLR_WM_codex'
$AGENT_TASKS    = Join-Path $CLAUDE_ROOT '.agent_tasks'
$QUEUE_DIR      = Join-Path $AGENT_TASKS  'codex_queue'
$DONE_DIR       = Join-Path $AGENT_TASKS  'codex_done'
$LOGS_DIR       = Join-Path $AGENT_TASKS  'codex_logs'
$LOCK_FILE      = Join-Path $AGENT_TASKS  '.lock'
$TEMPLATE_FILE  = Join-Path $AGENT_TASKS  'codex_prompt_template.md'
$GITIGNORE_FILE = Join-Path $CLAUDE_ROOT  '.gitignore'

if (-not $ClaudeBranch) {
    $ClaudeBranch = if ($env:FRCGW_CLAUDE_BRANCH) { $env:FRCGW_CLAUDE_BRANCH } else { 'memory-redesign-2026-05-16' }
}
$CLAUDE_BRANCH  = $ClaudeBranch
$CODEX_BRANCH   = 'codex-work'

# Resolve codex runner: on Windows npm installs codex as .cmd/.ps1 which
# Start-Process cannot handle; resolve to node + codex.js directly.
$_codexCmd = Get-Command 'codex' -ErrorAction SilentlyContinue
if ($_codexCmd -and $_codexCmd.Source -match '\.ps1$|\.cmd$|\.sh$') {
    # Unwrap: find the actual JS entry point from the npm shim's sibling node_modules
    $_codexJs = Join-Path (Split-Path $_codexCmd.Source) 'node_modules\@openai\codex\bin\codex.js'
    if (Test-Path $_codexJs) {
        $CODEX_EXE  = (Get-Command 'node' -ErrorAction Stop).Source
        $CODEX_ARGV_PREFIX = @($_codexJs)
    } else {
        # Fall back to cmd.exe wrapper
        $CODEX_EXE  = $env:COMSPEC
        $CODEX_ARGV_PREFIX = @('/c', $_codexCmd.Source)
    }
} elseif ($_codexCmd) {
    $CODEX_EXE  = $_codexCmd.Source
    $CODEX_ARGV_PREFIX = @()
} else {
    Write-Fail "codex not found in PATH — install @openai/codex globally"
    exit 10
}

$REQUIRED_HEADERS = @(
    'TASK_NAME:',
    'BACKGROUND:',
    'GOAL:',
    'FILES_ALLOWED:',
    'FILES_FORBIDDEN:',
    'REQUIRED_IMPLEMENTATION:',
    'REQUIRED_TESTS:',
    'ACCEPTANCE_CRITERIA:',
    'COMMIT_MESSAGE:',
    'STOP_CONDITION:'
)

$FORBIDDEN_PATTERNS = @(
    '^\.claude/',
    '^CLAUDE\.md$',
    '^\.mcp\.json$',
    '^\.venv/',
    '^data/',
    '^outputs/',
    '^secrets/',
    '^\.env',
    '^scripts/run_codex_task\.ps1$'
)
if (-not $AllowPaperContextRef) {
    $FORBIDDEN_PATTERNS += '^paper_context_ref/'
}

# Script-level context shared between modes when running in 'run' pipeline
$script:Ctx = @{}

# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────
function Write-Step { param([string]$Msg) Write-Host "[HARNESS] $Msg" -ForegroundColor Cyan }
function Write-Warn  { param([string]$Msg) Write-Host "[WARN]    $Msg" -ForegroundColor Yellow }
function Write-Fail  { param([string]$Msg) Write-Host "[FAIL]    $Msg" -ForegroundColor Red }

function Get-NextTaskNumber {
    $existing = Get-ChildItem $QUEUE_DIR -Filter 'TASK_*.md' -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -match '^TASK_\d+_' }
    if (-not $existing) { return 1 }
    $numbers = $existing | ForEach-Object {
        if ($_.Name -match '^TASK_(\d+)_') { [int]$Matches[1] } else { 0 }
    }
    return [int](($numbers | Measure-Object -Maximum).Maximum) + 1
}

function Get-QueueMdPath   { param([int]$N, [string]$Name) Join-Path $QUEUE_DIR ("TASK_{0:D3}_{1}.md"         -f $N, $Name) }
function Get-QueueMetaPath { param([int]$N, [string]$Name) Join-Path $QUEUE_DIR ("TASK_{0:D3}_{1}.meta.json" -f $N, $Name) }
function Get-ResultPath    { param([int]$N, [string]$Name) Join-Path $DONE_DIR  ("TASK_{0:D3}_{1}_RESULT.md" -f $N, $Name) }
# RESULT.md lives in the Codex worktree until prepare-merge brings it into Claude worktree
function Get-CodexResultPath { param([int]$N, [string]$Name)
    $codexDone = Join-Path $CODEX_ROOT '.agent_tasks\codex_done'
    Join-Path $codexDone ("TASK_{0:D3}_{1}_RESULT.md" -f $N, $Name)
}

function Resolve-Ctx {
    # Return task context: first from script-level cache, then from meta file.
    if ($script:Ctx.Count -gt 0) { return $script:Ctx }

    if (-not $TaskName) { Write-Fail "-TaskName is required for this mode"; exit 10 }

    $filter = if ($TaskNumber -ge 0) {
        "TASK_$("{0:D3}" -f $TaskNumber)_${TaskName}.meta.json"
    } else {
        "TASK_*_${TaskName}.meta.json"
    }
    $metas = Get-ChildItem $QUEUE_DIR -Filter $filter -ErrorAction SilentlyContinue
    if (-not $metas) {
        Write-Fail "No meta file matching '$filter' in $QUEUE_DIR"
        exit 10
    }
    $metaPath = ($metas | Sort-Object Name | Select-Object -Last 1).FullName
    $m = Get-Content $metaPath -Raw | ConvertFrom-Json
    return @{
        Number   = [int]$m.task_number
        Name     = [string]$m.task_name
        BaseSha  = [string]$m.base_sha
        MetaPath = $metaPath
    }
}

function Test-ForbiddenPaths {
    # Use three-dot diff (merge-base..CODEX_BRANCH) so we only check what Codex
    # added on top of the Claude branch — Claude's own commits are excluded.
    Push-Location $CODEX_ROOT
    try {
        $changed = git diff --name-only "${CLAUDE_BRANCH}...${CODEX_BRANCH}"
        if ($LASTEXITCODE -ne 0) { throw "git diff --name-only failed (exit $LASTEXITCODE)" }
    } finally {
        Pop-Location
    }
    $files = ($changed -join "`n") -split "`n" |
             ForEach-Object { $_.Trim() } |
             Where-Object   { $_ -ne '' }
    $violations = @()
    foreach ($file in $files) {
        foreach ($pat in $FORBIDDEN_PATTERNS) {
            if ($file -match $pat) { $violations += $file; break }
        }
    }
    return $violations
}

# ─────────────────────────────────────────────────────────────────────────────
# MODE: init
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-Init {
    Write-Step "Mode: init"

    if (Test-Path $LOCK_FILE) {
        Write-Fail "Lock file exists: $LOCK_FILE — remove manually if stale"
        exit 10
    }

    if ($DryRun) {
        Write-Host "[DRY] mkdir $QUEUE_DIR"
        Write-Host "[DRY] mkdir $DONE_DIR"
        Write-Host "[DRY] mkdir $LOGS_DIR"
        Write-Host "[DRY] create $TEMPLATE_FILE"
        Write-Host "[DRY] update $GITIGNORE_FILE  (+codex_logs/, +.lock)"
        return
    }

    foreach ($d in @($QUEUE_DIR, $DONE_DIR, $LOGS_DIR)) {
        if (-not (Test-Path $d)) {
            New-Item -ItemType Directory -Path $d -Force | Out-Null
            Write-Step "Created dir: $d"
        }
    }

    # .gitkeep for tracked dirs (codex_queue + codex_done are NOT ignored)
    foreach ($d in @($QUEUE_DIR, $DONE_DIR)) {
        $k = Join-Path $d '.gitkeep'
        if (-not (Test-Path $k)) { New-Item -ItemType File -Path $k -Force | Out-Null }
    }

    if (-not (Test-Path $TEMPLATE_FILE)) {
        $tpl = @'
You are the implementation agent for the FRCG-WM repo at
C:\Users\computer\Desktop\ICLR_WM_codex (worktree branch: codex-work).

Your task is fully specified in: {{TASK_FILE}}
Task name: {{TASK_NAME}}
Task number: {{TASK_NUMBER}}

Hard constraints:
- Work only inside C:\Users\computer\Desktop\ICLR_WM_codex.
- Do not modify: .claude/, CLAUDE.md, .mcp.json, .venv/, data/, outputs/,
  secrets/, .env*, paper_context_ref/, scripts/run_codex_task.ps1.
- Use the existing Python venv at .venv. Use `python -m pip`, not bare pip.
- Run the targeted tests listed in REQUIRED_TESTS of the task file.
- Commit ALL completed changes to branch codex-work.
- Do not push. Do not amend. Do not rebase.
- After committing, write a short summary to
  .agent_tasks/codex_done/TASK_{{TASK_NUMBER}}_{{TASK_NAME}}_RESULT.md
  including: files changed, tests run, pass/fail summary, blockers.
- Use the COMMIT_MESSAGE field of the task file verbatim as the commit message.
- Stop after the commit completes. Do not continue to additional work.
'@
        Set-Content -Path $TEMPLATE_FILE -Value $tpl -Encoding utf8
        Write-Step "Created template: $TEMPLATE_FILE"
    } else {
        Write-Step "Template already exists: $TEMPLATE_FILE"
    }

    # Update .gitignore — only codex_logs/ and .lock are ignored; queue/ and done/ stay tracked
    $gi = Get-Content $GITIGNORE_FILE -Raw -ErrorAction SilentlyContinue
    if ($gi -notmatch '\.agent_tasks/codex_logs/') {
        $block = @"


# =========================
# Agent task harness
# =========================
.agent_tasks/codex_logs/
.agent_tasks/.lock
"@
        Add-Content -Path $GITIGNORE_FILE -Value $block -Encoding utf8
        Write-Step "Updated .gitignore (+codex_logs/, +.lock)"
    } else {
        Write-Step ".gitignore already has harness entries"
    }

    Write-Step "init complete."
}

# ─────────────────────────────────────────────────────────────────────────────
# MODE: assign
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-Assign {
    if (-not $TaskFile) { Write-Fail "-TaskFile is required for assign mode"; exit 20 }
    if (-not $TaskName)  { Write-Fail "-TaskName is required for assign mode";  exit 20 }
    if (-not (Test-Path $TaskFile)) { Write-Fail "TaskFile not found: $TaskFile"; exit 20 }

    Write-Step "Mode: assign | task=$TaskName | file=$TaskFile"

    # Validate required headers
    $content = Get-Content $TaskFile -Raw
    $missing = $REQUIRED_HEADERS | Where-Object { $content -notmatch [regex]::Escape($_) }
    if ($missing) {
        Write-Fail "TASK file missing required headers:`n  $($missing -join "`n  ")"
        exit 20
    }
    Write-Step "TASK schema: OK"

    $num = if ($TaskNumber -ge 0) { $TaskNumber } else { Get-NextTaskNumber }
    Write-Step "Task number: $num"

    # Record BASE_SHA — snapshot of Claude HEAD at assign time
    $baseSha = (git -C $CLAUDE_ROOT rev-parse HEAD) -join ''
    if ($LASTEXITCODE -ne 0) { Write-Fail "git rev-parse HEAD failed"; exit 10 }
    $baseSha = $baseSha.Trim()
    Write-Step "BASE_SHA: $baseSha"

    $destMd   = Get-QueueMdPath   $num $TaskName
    $destMeta = Get-QueueMetaPath $num $TaskName

    if ($DryRun) {
        Write-Host "[DRY] copy $TaskFile → $destMd"
        Write-Host "[DRY] write meta → $destMeta  (base_sha=$baseSha)"
        Write-Host "[DRY] git add + commit in $CLAUDE_ROOT"
        $script:Ctx = @{ Number=$num; Name=$TaskName; BaseSha=$baseSha; MetaPath=$destMeta }
        return
    }

    Copy-Item $TaskFile $destMd -Force
    Write-Step "Copied TASK file → $destMd"

    $meta = [ordered]@{
        task_number = $num
        task_name   = $TaskName
        task_file   = ($destMd -replace [regex]::Escape($CLAUDE_ROOT + '\'), '') -replace '\\', '/'
        base_sha    = $baseSha
        assigned_at = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')
        assigned_by = 'claude'
    }
    $meta | ConvertTo-Json | Set-Content -Path $destMeta -Encoding utf8
    Write-Step "Meta written: $destMeta"

    Push-Location $CLAUDE_ROOT
    try {
        git add $destMd $destMeta
        if ($LASTEXITCODE -ne 0) { throw "git add failed" }
        $msg = "task: assign TASK_{0:D3}_{1} to codex" -f $num, $TaskName
        git commit -m $msg
        if ($LASTEXITCODE -ne 0) { throw "git commit failed" }
    } finally {
        Pop-Location
    }

    $script:Ctx = @{ Number=$num; Name=$TaskName; BaseSha=$baseSha; MetaPath=$destMeta }
    Write-Step ("assign complete: TASK_{0:D3}_{1}" -f $num, $TaskName)
}

# ─────────────────────────────────────────────────────────────────────────────
# MODE: dispatch
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-Dispatch {
    $ctx     = Resolve-Ctx
    $num     = $ctx.Number
    $name    = $ctx.Name
    $baseSha = $ctx.BaseSha
    Write-Step "Mode: dispatch | task=$name | num=$num | base=$baseSha"

    # [Pre-check 1] Lock
    if (Test-Path $LOCK_FILE) {
        Write-Fail "Lock file exists: $LOCK_FILE — another dispatch may be running. Remove manually if stale."
        exit 10
    }

    # [Pre-check 2] Divergence check — reject if unaccepted Codex commits exist
    $diverged = git -C $CODEX_ROOT log "${CLAUDE_BRANCH}..${CODEX_BRANCH}" --oneline
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "git log divergence check failed (exit $LASTEXITCODE)"
        exit 10
    }
    $divergedStr = ($diverged -join "`n").Trim()
    if ($divergedStr -ne '') {
        Write-Fail "Unaccepted Codex commits exist on ${CODEX_BRANCH}:"
        Write-Host $divergedStr
        Write-Fail "Run verify + prepare-merge first to accept or abort pending Codex work."
        exit 10
    }
    Write-Step "Divergence check: clean"

    # [Codex worktree sync] ff-only preferred; abort if fast-forward impossible
    if ($DryRun) {
        Write-Host "[DRY] git merge --ff-only $CLAUDE_BRANCH  (in $CODEX_ROOT)"
    } else {
        Push-Location $CODEX_ROOT
        try {
            git merge --ff-only $CLAUDE_BRANCH
            if ($LASTEXITCODE -ne 0) {
                Write-Fail "Cannot fast-forward codex-work onto $CLAUDE_BRANCH. Resolve divergence manually."
                exit 10
            }
        } finally {
            Pop-Location
        }
        Write-Step "Codex worktree synced (--ff-only)"
    }

    # Build prompt via template substitution
    if (-not (Test-Path $TEMPLATE_FILE)) {
        Write-Fail "Prompt template missing: $TEMPLATE_FILE — run 'init' first"
        exit 10
    }

    # ─── SANDBOX_MODE consistency check (04 §5, R4) ───
    # Parse SANDBOX_MODE from TASK file (default: 'default' if missing — backward compat with P3 tasks).
    # If -BypassSandbox is passed, TASK file must declare SANDBOX_MODE: bypass.
    $taskMdPath = Get-QueueMdPath $num $name
    if (-not (Test-Path $taskMdPath)) {
        Write-Fail "TASK file missing for SANDBOX_MODE check: $taskMdPath"
        exit 10
    }
    $taskMdContent = Get-Content $taskMdPath -Raw
    $sandboxModeMatch = [regex]::Match($taskMdContent, '(?im)^SANDBOX_MODE:\s*(default|bypass)\b')
    $taskSandboxMode = if ($sandboxModeMatch.Success) { $sandboxModeMatch.Groups[1].Value.ToLower() } else { 'default' }
    Write-Step "TASK SANDBOX_MODE: $taskSandboxMode (from $taskMdPath)"

    if ($BypassSandbox -and $taskSandboxMode -ne 'bypass') {
        Write-Fail "TASK file declares SANDBOX_MODE: $taskSandboxMode but -BypassSandbox was passed."
        Write-Fail "Set SANDBOX_MODE: bypass in TASK file, or remove -BypassSandbox switch."
        Write-Fail "Reference: docs/orchestration/04_CODEX_FEEDBACK_LOOP_PROTOCOL.md §5"
        exit 20
    }
    if (-not $BypassSandbox -and $taskSandboxMode -eq 'bypass') {
        Write-Warn "TASK file declares SANDBOX_MODE: bypass but -BypassSandbox switch not passed."
        Write-Warn "Falling back to sandbox mode (workspace-write). To enable bypass, re-run with -BypassSandbox."
    }

    $taskFileRel = ".agent_tasks/codex_queue/TASK_{0:D3}_{1}.md" -f $num, $name
    $prompt = (Get-Content $TEMPLATE_FILE -Raw) `
        -replace '\{\{TASK_FILE\}\}',   $taskFileRel `
        -replace '\{\{TASK_NAME\}\}',   $name `
        -replace '\{\{TASK_NUMBER\}\}', ("{0:D3}" -f $num)

    # Artifact paths
    $ts        = Get-Date -Format 'yyyyMMdd_HHmmss'
    $runId     = "RUN_${ts}_TASK_$("{0:D3}" -f $num)"
    $logPrefix = Join-Path $LOGS_DIR $runId
    $jsonlLog  = "${logPrefix}.jsonl"
    $errLog    = "${logPrefix}.err.log"
    $lastMsg   = "${logPrefix}_lastmsg.txt"
    $sumFile   = "${logPrefix}.summary.json"

    # Write prompt to temp file — passed via stdin to avoid PS5.1 arg quoting issues
    $promptFile = [System.IO.Path]::GetTempFileName()
    Set-Content -Path $promptFile -Value $prompt -Encoding utf8

    # Git worktrees store index/HEAD under the parent repo's .git/worktrees/<name>/.
    # The codex sandbox only allows writes to CODEX_ROOT; git commits from a worktree
    # also need write access to this metadata dir.
    $codexWorktreeMeta = Join-Path $CLAUDE_ROOT ".git\worktrees\$(Split-Path $CODEX_ROOT -Leaf)"

    if ($BypassSandbox) {
        Write-Warn "-BypassSandbox: using --dangerously-bypass-approvals-and-sandbox (dev/smoke-test only)"
        $codexArgs = @(
            'exec',
            '-C', $CODEX_ROOT,
            '--dangerously-bypass-approvals-and-sandbox',
            '-m', $CodexModel,
            '--json',
            '-o', $lastMsg,
            '-'
        )
    } else {
        $codexArgs = @(
            'exec',
            '-C', $CODEX_ROOT,
            '-s', $CodexSandbox,
            '--add-dir', $codexWorktreeMeta,
            '-m', $CodexModel,
            '--json',
            '-o', $lastMsg,
            '-'                # read prompt from stdin
        )
    }

    if ($DryRun) {
        Write-Host "[DRY] $CODEX_EXE $($CODEX_ARGV_PREFIX -join ' ') $($codexArgs -join ' ')"
        Write-Host "[DRY] stdin from temp file (prompt length=$($prompt.Length) chars)"
        Write-Host "[DRY] stdout → $jsonlLog"
        Write-Host "[DRY] stderr → $errLog"
        Remove-Item $promptFile -ErrorAction SilentlyContinue
        return
    }

    if (-not (Test-Path $LOGS_DIR)) { New-Item -ItemType Directory -Path $LOGS_DIR -Force | Out-Null }

    # Acquire lock
    New-Item -ItemType File -Path $LOCK_FILE -Force | Out-Null
    Write-Step "Lock acquired: $LOCK_FILE"

    # Combine argv: node_modules path prefix + codex subcommand args
    $fullArgs = $CODEX_ARGV_PREFIX + $codexArgs

    $startTime = Get-Date
    $codexExit = -1
    $proc      = $null
    try {
        $proc = Start-Process -FilePath $CODEX_EXE `
            -ArgumentList $fullArgs `
            -RedirectStandardInput  $promptFile `
            -RedirectStandardOutput $jsonlLog `
            -RedirectStandardError  $errLog `
            -NoNewWindow -PassThru

        Write-Step "codex exec started (PID $($proc.Id)), timeout=${TimeoutMinutes}min"

        $proc | Wait-Process -Timeout ($TimeoutMinutes * 60) -ErrorAction SilentlyContinue

        if (-not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Fail "codex exec timed out after ${TimeoutMinutes} minutes"
            $codexExit = -1
        } else {
            $codexExit = $proc.ExitCode
            if ($codexExit -ne 0) {
                Write-Fail "codex exec failed (exit $codexExit). See: $errLog"
            } else {
                Write-Step "codex exec completed (exit 0)"
            }
        }
    } finally {
        Remove-Item $LOCK_FILE    -ErrorAction SilentlyContinue
        Remove-Item $promptFile   -ErrorAction SilentlyContinue
        Write-Step "Lock released"
    }

    $endTime  = Get-Date
    $codexSha = (git -C $CODEX_ROOT rev-parse HEAD) -join ''
    if ($LASTEXITCODE -ne 0) { $codexSha = 'UNKNOWN' }
    $codexSha = $codexSha.Trim()

    $summary = [ordered]@{
        run_id               = $runId
        task_number          = $num
        task_name            = $name
        base_sha             = $baseSha
        started_at           = $startTime.ToString('yyyy-MM-ddTHH:mm:ssZ')
        ended_at             = $endTime.ToString('yyyy-MM-ddTHH:mm:ssZ')
        codex_exit_code      = $codexExit
        codex_commit_sha     = $codexSha
        files_changed        = @()
        forbidden_violations = @()
        status               = if ($codexExit -eq 0) { 'dispatch_ok' } else { 'dispatch_failed' }
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -Path $sumFile -Encoding utf8
    Write-Step "Summary written: $sumFile"

    if ($codexExit -ne 0) { exit 30 }

    Write-Step "dispatch complete. JSONL log: $jsonlLog"
}

# ─────────────────────────────────────────────────────────────────────────────
# MODE: verify
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-Verify {
    $ctx     = Resolve-Ctx
    $num     = $ctx.Number
    $name    = $ctx.Name
    $baseSha = $ctx.BaseSha
    Write-Step "Mode: verify | task=$name | num=$num | base=$baseSha"

    if ($DryRun) {
        Write-Host "[DRY] git log ${baseSha}..${CODEX_BRANCH}  (check new commits)"
        Write-Host "[DRY] git status --porcelain  (check clean worktree)"
        Write-Host "[DRY] Test-ForbiddenPaths -BaseSha $baseSha"
        $resultPath = Get-ResultPath $num $name
        Write-Host "[DRY] Test-Path $resultPath  (check RESULT.md)"
        Write-Step "verify PASSED (dry-run)."
        return
    }

    # [1] Codex commits must exist since BASE_SHA
    $newCommits = git -C $CODEX_ROOT log "${baseSha}..${CODEX_BRANCH}" --oneline
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "git log failed (exit $LASTEXITCODE)"
        exit 40
    }
    $newCommitsStr = ($newCommits -join "`n").Trim()
    if ($newCommitsStr -eq '') {
        Write-Fail "No Codex commits found since BASE_SHA ($baseSha). Codex did not commit."
        exit 40
    }
    Write-Step "Codex commits since BASE_SHA:"
    Write-Host $newCommitsStr

    # [2] Codex working tree must be clean
    $status = git -C $CODEX_ROOT status --porcelain
    if ($LASTEXITCODE -ne 0) { Write-Fail "git status failed (exit $LASTEXITCODE)"; exit 40 }
    $statusStr = ($status -join "`n").Trim()
    if ($statusStr -ne '') {
        Write-Fail "Codex worktree has uncommitted changes:`n$statusStr"
        exit 40
    }
    Write-Step "Working tree: clean"

    # [3] Forbidden path check (BASE_SHA-anchored)
    # Wrap in @() so that empty return from Test-ForbiddenPaths stays an array in PS5.1
    $violations = @(Test-ForbiddenPaths -BaseSha $baseSha)
    if ($violations.Count -gt 0) {
        Write-Fail "Forbidden paths modified by Codex:"
        $violations | ForEach-Object { Write-Fail "  $_" }
        exit 40
    }
    Write-Step "Forbidden paths: clean"

    # [4] RESULT.md must exist in Codex worktree (prepare-merge brings it to Claude worktree later)
    $resultPath = Get-CodexResultPath $num $name
    if (-not (Test-Path $resultPath)) {
        Write-Fail "RESULT.md not found in codex worktree: $resultPath"
        exit 40
    }
    Write-Step "RESULT.md: found at $resultPath"

    # [5] Push trace — best-effort warning only (not a blocking condition)
    $pushed = git -C $CODEX_ROOT log "origin/${CODEX_BRANCH}..${CODEX_BRANCH}" --oneline
    if ($LASTEXITCODE -eq 0) {
        $pushedStr = ($pushed -join "`n").Trim()
        if ($pushedStr -eq '') {
            Write-Warn "Push trace: codex-work appears fully pushed to origin. Policy reminder: do not push from Codex worktree."
        }
    }
    # Non-zero exit (origin doesn't exist or fetch hasn't run) → silently skip

    # Update summary.json with files_changed and verified status
    $sumFiles = Get-ChildItem $LOGS_DIR -Filter "*$("{0:D3}" -f $num)*.summary.json" `
                    -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime | Select-Object -Last 1
    if ($sumFiles) {
        $s = Get-Content $sumFiles.FullName -Raw | ConvertFrom-Json
        $changedRaw = git -C $CODEX_ROOT diff --name-only "${baseSha}..${CODEX_BRANCH}"
        $changedList = if ($changedRaw) {
            [string[]]( ($changedRaw -join "`n") -split "`n" |
                        ForEach-Object { $_.Trim() } |
                        Where-Object   { $_ -ne '' } )
        } else { @() }

        $updated = [ordered]@{
            run_id               = $s.run_id
            task_number          = $s.task_number
            task_name            = $s.task_name
            base_sha             = $s.base_sha
            started_at           = $s.started_at
            ended_at             = $s.ended_at
            codex_exit_code      = $s.codex_exit_code
            codex_commit_sha     = $s.codex_commit_sha
            files_changed        = $changedList
            forbidden_violations = @()
            status               = 'verified'
        }
        $updated | ConvertTo-Json -Depth 5 | Set-Content -Path $sumFiles.FullName -Encoding utf8
        Write-Step "Summary updated: $($sumFiles.FullName)"
    }

    Write-Step "verify PASSED."
}

# ─────────────────────────────────────────────────────────────────────────────
# MODE: prepare-merge
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-PrepareMerge {
    Write-Step "Mode: prepare-merge"

    if ($DryRun) {
        Write-Host "[DRY] git merge --no-commit --no-ff $CODEX_BRANCH  (in $CLAUDE_ROOT)"
        Write-Host "[DRY] git diff --cached --stat"
        Write-Host "[DRY] git diff --cached --name-only"
        return
    }

    Push-Location $CLAUDE_ROOT
    try {
        git merge --no-commit --no-ff $CODEX_BRANCH
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Merge failed or conflict (exit $LASTEXITCODE)"
            Write-Host "Resolve manually or run: git merge --abort" -ForegroundColor Yellow
            exit 50
        }
    } finally {
        Pop-Location
    }

    Write-Step "Merge staged (NOT committed). Review before accepting."
    Write-Host ""
    Write-Host "=== git diff --cached --stat ===" -ForegroundColor Green
    git -C $CLAUDE_ROOT diff --cached --stat
    Write-Host ""
    Write-Host "=== git diff --cached --name-only ===" -ForegroundColor Green
    git -C $CLAUDE_ROOT diff --cached --name-only
    Write-Host ""
    Write-Step "Next steps for Claude agent:"
    Write-Host "  Accept : git commit -m 'merge: accept codex-work into feat/p1-schema-visibility'"
    Write-Host "  Abort  : git merge --abort"
}

# ─────────────────────────────────────────────────────────────────────────────
# MODE: run  (full pipeline: assign → dispatch → verify → prepare-merge)
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-Run {
    Write-Step "Mode: run (assign -> dispatch -> verify -> prepare-merge)"
    Invoke-Assign
    Invoke-Dispatch
    Invoke-Verify
    Invoke-PrepareMerge
    Write-Step "run pipeline complete."
}

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
switch ($Mode) {
    'init'          { Invoke-Init }
    'assign'        { Invoke-Assign }
    'dispatch'      { Invoke-Dispatch }
    'verify'        { Invoke-Verify }
    'prepare-merge' { Invoke-PrepareMerge }
    'run'           { Invoke-Run }
}
