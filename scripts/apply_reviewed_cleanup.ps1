# ============================================================
# apply_reviewed_cleanup.ps1
# FRCG-WM Cleanup Execution Script — 10-Guard Safety System
#
# 사용법:
#   # Dry-run (기본값 — 실제 실행 안 됨)
#   .\scripts\apply_reviewed_cleanup.ps1 -CsvPath outputs\cleanup_audit\<TS>\human_decision_template.csv
#
#   # 실제 실행 (두 플래그 동시 필요)
#   .\scripts\apply_reviewed_cleanup.ps1 `
#     -CsvPath outputs\cleanup_audit\<TS>\human_decision_template.csv `
#     -DryRun:$false `
#     -ConfirmApprovedCleanup
#
# Source plan: docs/orchestration/lr_alignment/17_step1_5_lifecycle_cleanup_design.md
# ============================================================

param(
    [Parameter(Mandatory = $true)]
    [string]$CsvPath,

    # Guard #9: DryRun defaults to $true — must explicitly pass -DryRun:$false to execute
    [bool]$DryRun = $true,

    # Guard #10: second flag required alongside -DryRun:$false
    [switch]$ConfirmApprovedCleanup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ------------------------------------------------------------------
# Guard #1: Input file must exist
# ------------------------------------------------------------------
if (-not (Test-Path $CsvPath)) {
    Write-Error "[GUARD-1 FAIL] CSV 파일이 존재하지 않습니다: $CsvPath"
    exit 1
}

# ------------------------------------------------------------------
# Guard #10: Both flags required for actual execution
# ------------------------------------------------------------------
if (-not $DryRun -and -not $ConfirmApprovedCleanup) {
    Write-Error "[GUARD-10 FAIL] 실제 실행에는 -DryRun:`$false AND -ConfirmApprovedCleanup 두 플래그가 모두 필요합니다."
    exit 1
}

Write-Host ""
if ($DryRun) {
    Write-Host "=== apply_reviewed_cleanup.ps1 [DRY-RUN MODE] ==="
} else {
    Write-Host "=== apply_reviewed_cleanup.ps1 [LIVE EXECUTION MODE] ==="
    Write-Host "    경고: 실제 파일 변경이 발생합니다."
}
Write-Host "    CSV: $CsvPath"
Write-Host ""

# ------------------------------------------------------------------
# Guard #7: Protected path segments — immediate exit if matched
# ------------------------------------------------------------------
$PROTECTED_PATHS = @(
    "paper_context_ref",
    "src/frcgw",
    "tests",
    "configs",
    "outputs/phase_gates",
    "plans/PHASE_PROGRESS.md",
    "outputs/runs/p3_lr_eval",
    "outputs/runs/p3_ablations",
    "outputs/runs/p3_lr_smoke",
    "data/frcgw_text/v0_1",
    "evidence_cards",
    "12_run6_lr_eval_report.md",
    "13_claim_survivability_decision_report.md",
    "CLAUDE.md",
    "CLAUDE.local.md",
    ".claude",
    ".mcp.json"
)

# scripts/__pycache__ is allowed despite scripts/ being partially protected
$PROTECTED_PATH_EXCEPTIONS = @(
    "scripts/__pycache__"
)

function Test-ProtectedPath {
    param([string]$path)
    foreach ($exc in $PROTECTED_PATH_EXCEPTIONS) {
        if ($path -like "*$exc*") { return $false }
    }
    foreach ($guard in $PROTECTED_PATHS) {
        if ($path -like "*$guard*") { return $true }
    }
    return $false
}

# ------------------------------------------------------------------
# Load CSV
# ------------------------------------------------------------------
$rows = Import-Csv -Path $CsvPath

$archiveCount = 0
$deleteCacheCount = 0
$skipCount = 0
$errorCount = 0

# ------------------------------------------------------------------
# Guard #8: Preview ALL commands before execution
# ------------------------------------------------------------------
Write-Host "--- Command Preview (all APPROVED=YES rows) ---"
$approvedRows = $rows | Where-Object { $_.APPROVED -eq "YES" }
if ($approvedRows.Count -eq 0) {
    Write-Host "  APPROVED=YES 행이 없습니다. 종료."
    Write-Host ""
    Write-Host "=== 완료 (변경 0건) ==="
    exit 0
}

foreach ($row in $approvedRows) {
    $path = $row.path.Trim()
    $action = $row.recommended_action.Trim()
    $decision = $row.decision.Trim()
    Write-Host "  [APPROVED] $path"
    Write-Host "    action=$action, decision=$decision"
}
Write-Host ""

# ------------------------------------------------------------------
# Guard #4/5/6: Only ARCHIVE_LATER + APPROVE_ARCHIVE or DELETE_CACHE + APPROVE_DELETE_CACHE are executable
# DO_NOT_TOUCH / KEEP / MANUAL_REVIEW_ONLY → skip
# ------------------------------------------------------------------

foreach ($row in $approvedRows) {
    $path = $row.path.Trim()
    $action = $row.recommended_action.Trim()
    $decision = $row.decision.Trim()

    # Guard #6: DO_NOT_TOUCH / KEEP / MANUAL_REVIEW_ONLY → always skip
    if ($action -in @("DO_NOT_TOUCH", "KEEP", "MANUAL_REVIEW_ONLY")) {
        if ($action -eq "DO_NOT_TOUCH") {
            Write-Host "[SKIP-DO_NOT_TOUCH] $path — 절대 보호. 건너뜀."
        } else {
            Write-Host "[SKIP-$action] $path — action 허용 안 됨. 건너뜀."
        }
        $skipCount++
        continue
    }

    # Guard #7: Protected path check
    if (Test-ProtectedPath -path $path) {
        Write-Error "[GUARD-7 FAIL] 보호 경로 감지: $path — 즉시 중단"
        exit 1
    }

    # ARCHIVE_LATER + APPROVE_ARCHIVE
    if ($action -eq "ARCHIVE_LATER" -and $decision -eq "APPROVE_ARCHIVE") {
        $archiveTarget = "plans/archive/2026-05/" + (Split-Path $path -Leaf)

        # Guard #3: git mv only
        if ($DryRun) {
            Write-Host "[DRY-RUN] git mv `"$path`" `"$archiveTarget`""
        } else {
            Write-Host "[EXECUTE] git mv `"$path`" `"$archiveTarget`""
            if (-not (Test-Path "plans/archive/2026-05")) {
                New-Item -ItemType Directory -Path "plans/archive/2026-05" -Force | Out-Null
                Write-Host "[INFO] archive 디렉터리 생성: plans/archive/2026-05/"
            }
            if (Test-Path $path) {
                git mv $path $archiveTarget
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "[ERROR] git mv 실패: $path"
                    $errorCount++
                } else {
                    Write-Host "[OK] archived: $path -> $archiveTarget"
                    $archiveCount++
                }
            } else {
                Write-Host "[WARN] 파일 없음 (이미 이동됨?): $path"
            }
        }
        continue
    }

    # DELETE_CACHE + APPROVE_DELETE_CACHE
    if ($action -eq "DELETE_CACHE" -and $decision -eq "APPROVE_DELETE_CACHE") {
        # Guard #4: Remove-Item only for cache
        if ($DryRun) {
            if ($path -like "*/**/*") {
                # glob pattern path
                Write-Host "[DRY-RUN] Get-ChildItem recursive -WhatIf: $path"
            } else {
                Write-Host "[DRY-RUN] Remove-Item -WhatIf: $path"
                if (Test-Path $path) {
                    Remove-Item -Recurse -Force $path -WhatIf
                } else {
                    Write-Host "  -> 이미 없음"
                }
            }
        } else {
            if ($path -match "src/frcgw/\*\*/") {
                # src/frcgw/**/__pycache__/ pattern
                Write-Host "[EXECUTE] src/frcgw/**/__pycache__/ 재귀 삭제"
                $dirs = Get-ChildItem "src/frcgw" -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
                foreach ($d in $dirs) {
                    Remove-Item -Recurse -Force $d.FullName
                    Write-Host "[OK] deleted: $($d.FullName)"
                    $deleteCacheCount++
                }
            } else {
                if (Test-Path $path) {
                    Remove-Item -Recurse -Force $path
                    Write-Host "[OK] deleted: $path"
                    $deleteCacheCount++
                } else {
                    Write-Host "[SKIP] 이미 없음: $path"
                }
            }
        }
        continue
    }

    # DELETE_STAGING_COPY + APPROVE_DELETE_STAGING_COPY
    if ($action -eq "DELETE_STAGING_COPY" -and $decision -eq "APPROVE_DELETE_STAGING_COPY") {
        if ($DryRun) {
            Write-Host "[DRY-RUN] Remove-Item -WhatIf (staging copy): $path"
        } else {
            if (Test-Path $path) {
                Remove-Item -Recurse -Force $path
                Write-Host "[OK] deleted staging copy: $path"
                $deleteCacheCount++
            } else {
                Write-Host "[SKIP] 이미 없음: $path"
            }
        }
        continue
    }

    # Unknown action/decision combination
    Write-Host "[SKIP-UNKNOWN] action=$action, decision=$decision — 인식 불가. 건너뜀."
    $skipCount++
}

Write-Host ""
Write-Host "--- Summary ---"
Write-Host "  ARCHIVE (git mv): $archiveCount"
Write-Host "  DELETE_CACHE:      $deleteCacheCount"
Write-Host "  SKIPPED:           $skipCount"
Write-Host "  ERRORS:            $errorCount"

# Guard #11 (bonus): git status after execution
if (-not $DryRun -and $archiveCount -gt 0) {
    Write-Host ""
    Write-Host "--- git status (변경 확인) ---"
    git status --short
}

Write-Host ""
if ($DryRun) {
    Write-Host "=== DRY-RUN 완료 (실제 변경 0건) ==="
    Write-Host "    실제 실행하려면: -DryRun:`$false -ConfirmApprovedCleanup"
} else {
    Write-Host "=== LIVE 실행 완료 ==="
    if ($errorCount -gt 0) {
        Write-Host "    ERROR $errorCount 건 발생. 위 로그를 확인하십시오."
        exit 1
    }
}
