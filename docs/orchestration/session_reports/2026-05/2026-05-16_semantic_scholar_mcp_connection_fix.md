# Session Report — 20260516-010

session_id: 20260516-010
date: 2026-05-16
branch: solo/p3-final-boss-cleared
mode: full
근거: `docs/orchestration/08_AGENT_OUTPUT_CONTRACTS.md §5`

---

## Summary

Semantic Scholar MCP stdio 연결 실패의 근본 원인 2건을 진단하고 수정했다.

이전 세션(20260516-009)의 DEC_012 PASS 판정은 HTTPS direct API 동작만 검증한 것이었다.
실제 Claude Code ↔ MCP stdio 핸드셰이크는 단 한 번도 성공하지 않았다:
- `/mcp` 명령 결과: `semantic-scholar · ✘ failed`

---

## Read

- `C:\Users\computer\Desktop\ICLR_WM_claude-code\.mcp.json`
- `C:\Users\computer\AppData\Roaming\uv\tools\semantic-scholar-mcp\Lib\site-packages\semantic_scholar_mcp\cli.py`
- `docs/orchestration/decision_logs/2026-05/session_step5_real_mcp.md`
- `docs/orchestration/mcp_research/INDEX.md`
- `plans/PLUGIN_AUDIT_REPORT.md`
- `docs/orchestration/session_reports/INDEX.md`
- `.claude/rules/mcp_rate_limit_rules.md`

---

## Phase

MCP 인프라 유지보수 — Phase 4 진입 전 필수 조건 충족

---

## Root Cause Analysis

### RC-001: Windows cp949 UnicodeEncodeError — 즉시 crash

**파일**: `cli.py:66`

```python
if api_key:
    click.echo("✓ Semantic Scholar API key configured")
```

`✓` (U+2713 CHECK MARK)는 한국어 Windows 기본 codepage cp949로 인코딩 불가.
API 키가 env에 주입된 순간부터 MCP 서버는 stdio 핸드셰이크 직전 즉시 crash.

이전 세션(20260516-009)에서는 API 키가 빈 문자열이라 `if api_key:` 분기에 진입하지 않아 숨겨져 있었다.

**재현 traceback**:
```
UnicodeEncodeError: 'cp949' codec can't encode character '✓' in position 0: illegal multibyte sequence
```

**fix**: `.mcp.json` env 블록에 `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8` 추가.

### RC-002: banner-on-stdout MCP stdio 규약 위반

**파일**: `cli.py` lines 63, 66, 68-70, 74-78, 81-83, 104-106

MCP stdio 규약:
- stdout = JSON-RPC frame 전용
- stderr = 사람용 로그

현재 코드는 14개 `click.echo()` 호출로 배너를 stdout에 출력.
Claude Code MCP client의 JSON parser가 첫 줄에서 비-JSON 텍스트를 만나 연결 실패 처리.

비교: `arxiv-mcp-server`는 stdout에 JSON-RPC만 출력 (stderr 없음).

**fix**: 14개 `click.echo` 호출 모두 `err=True` 추가 → stderr redirect.

---

## Changed / Created

### 수정 파일

| 파일 | 변경 |
|---|---|
| `.mcp.json` | `args: ["serve"] → ["serve","stdio"]`, `env: +PYTHONUTF8=1, +PYTHONIOENCODING=utf-8` |
| `cli.py` (uv tools) | 14개 banner click.echo → `err=True` 추가 |
| `decision_logs/2026-05/session_step5_real_mcp.md` | DEC_012 addendum_002 추가 |
| `mcp_research/INDEX.md` | MCP_20260516_005 row 추가, MCP_20260516_004 note 갱신 |
| `plans/PLUGIN_AUDIT_REPORT.md` | semantic-scholar-mcp 패치노트 + upgrade guard 추가 |
| `session_reports/INDEX.md` | 20260516-010 row 추가 |
| `.claude/rules/mcp_rate_limit_rules.md` | upgrade guard reminder 추가 |

### 생성 파일

| 파일 | 내용 |
|---|---|
| `mcp_research/2026-05/MCP_20260516_005.md` | stdio handshake 검증 결과 + 4a PASS |
| `session_reports/2026-05/2026-05-16_semantic_scholar_mcp_connection_fix.md` | 이 파일 |

---

## Tests / Gates

### 4a — Direct stdio handshake (PASS)

```
환경: PYTHONUTF8=1, PYTHONIOENCODING=utf-8
command: semantic-scholar-mcp.exe serve stdio
input: {"jsonrpc":"2.0","id":1,"method":"initialize",...}
```

| 조건 | 결과 |
|---|---|
| stdout 첫 줄 JSON | PASS |
| stdout에 배너 없음 | PASS |
| stderr에 배너 있음 | PASS |
| UnicodeEncodeError 없음 | PASS |

### JSON 유효성 검증

```powershell
Get-Content .mcp.json | ConvertFrom-Json  # PASS
```

env 블록 3개 키 확인:
- `SEMANTIC_SCHOLAR_API_KEY` ✅
- `PYTHONUTF8` = "1" ✅
- `PYTHONIOENCODING` = "utf-8" ✅

### cli.py 패치 카운트

```powershell
Select-String -Pattern 'err=True' cli.py | Measure-Object  # 14건 ✅
```

### 4b, 4c, 4d (미완료)

4b (`/mcp` 표시 `✔ connected · 4 tools`), 4c (실제 tool 호출), 4d (regression) 는
Claude Code 세션 재시작 후 새 세션에서 확인 필요.

---

## Blockers

none

---

## Patch reapplication runbook

`uv tool upgrade semantic-scholar-mcp` 실행 시 cli.py 패치가 덮어쓰여진다.

### 재적용 절차

**Step 1: 현재 패치 상태 확인**
```powershell
$cliPath = "C:\Users\computer\AppData\Roaming\uv\tools\semantic-scholar-mcp\Lib\site-packages\semantic_scholar_mcp\cli.py"
(Select-String -Path $cliPath -Pattern 'err=True' | Measure-Object).Count
# 기대: 14
```

**Step 2: upgrade 실행**
```powershell
uv tool upgrade semantic-scholar-mcp
```

**Step 3: 재확인**
```powershell
(Select-String -Path $cliPath -Pattern 'err=True' | Measure-Object).Count
# 14가 아니면 Step 4 진행
```

**Step 4: 패치 재적용 (Python 스크립트)**
```python
import re

cli_path = r"C:\Users\computer\AppData\Roaming\uv\tools\semantic-scholar-mcp\Lib\site-packages\semantic_scholar_mcp\cli.py"

with open(cli_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 패치 대상: serve 함수 내 배너 click.echo 호출에만 err=True 추가
# (tools list, search_paper, get_paper 등 다른 echo는 touch 안 함)
# serve() 함수 범위: def serve(...): ... anyio.run(async_main)

# 방법: serve 함수 본문 내 click.echo(... ) → click.echo(..., err=True)
# 단, 이미 err=True가 있는 라인은 skip
lines = content.split('\n')
in_serve = False
serve_banner_lines = {
    'click.echo("Debug mode enabled")',
    'click.echo("✓ Semantic Scholar API key configured")',
    'click.echo("\\nAvailable tools:")',
    'click.echo("  • search_paper - Search for papers using Semantic Scholar")',
    'click.echo("  • get_paper - Get detailed information about a specific paper")',
    'click.echo("  • get_authors - Get authors information for a specific paper")',
    'click.echo("  • get_citation - Get citation information in various formats")',
    'click.echo("\\nStarting Semantic Scholar MCP Server...")',
    'click.echo("Server will communicate via stdio (MCP standard)")',
    'click.echo("Server ready. Waiting for MCP client connection...")',
}

# 가장 안전한 방법: 14개 대상 echo 패턴을 직접 치환
replacements = [
    ('click.echo("Debug mode enabled")', 'click.echo("Debug mode enabled", err=True)'),
    ('click.echo("✓ Semantic Scholar API key configured")', 'click.echo("✓ Semantic Scholar API key configured", err=True)'),
    ('"⚠️  No Semantic Scholar API key found (set SEMANTIC_SCHOLAR_API_KEY environment variable for higher rate limits)"\n        )',
     '"⚠️  No Semantic Scholar API key found (set SEMANTIC_SCHOLAR_API_KEY environment variable for higher rate limits)",\n            err=True,\n        )'),
    ('click.echo("\\nAvailable tools:")', 'click.echo("\\nAvailable tools:", err=True)'),
    ('click.echo("  • search_paper - Search for papers using Semantic Scholar")', 'click.echo("  • search_paper - Search for papers using Semantic Scholar", err=True)'),
    ('click.echo("  • get_paper - Get detailed information about a specific paper")', 'click.echo("  • get_paper - Get detailed information about a specific paper", err=True)'),
    ('click.echo("  • get_authors - Get authors information for a specific paper")', 'click.echo("  • get_authors - Get authors information for a specific paper", err=True)'),
    ('click.echo("  • get_citation - Get citation information in various formats")', 'click.echo("  • get_citation - Get citation information in various formats", err=True)'),
    ('click.echo(f"\\nStarting HTTP server on http://{host}:{port}")', 'click.echo(f"\\nStarting HTTP server on http://{host}:{port}", err=True)'),
    ('click.echo("Available endpoints:")', 'click.echo("Available endpoints:", err=True)'),
    ('click.echo(f"  • HTTP  http://{host}:{port}/mcp - MCP over HTTP endpoint")', 'click.echo(f"  • HTTP  http://{host}:{port}/mcp - MCP over HTTP endpoint", err=True)'),
    ('click.echo("\\nStarting Semantic Scholar MCP Server...")', 'click.echo("\\nStarting Semantic Scholar MCP Server...", err=True)'),
    ('click.echo("Server will communicate via stdio (MCP standard)")', 'click.echo("Server will communicate via stdio (MCP standard)", err=True)'),
    ('click.echo("Server ready. Waiting for MCP client connection...")', 'click.echo("Server ready. Waiting for MCP client connection...", err=True)'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(cli_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("패치 완료")
```

**Step 5: 검증**
```powershell
(Select-String -Path $cliPath -Pattern 'err=True' | Measure-Object).Count
# 기대: 14

# 4a stdio handshake 재검증
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:SEMANTIC_SCHOLAR_API_KEY = "s2k-Jzu7..."
# [plan Step 4a 명령 실행]
```

---

## Cross-link

- Decision log: `docs/orchestration/decision_logs/2026-05/session_step5_real_mcp.md` (DEC_012 addendum_002)
- MCP query log: `docs/orchestration/mcp_research/2026-05/MCP_20260516_005.md`
- Plugin audit: `plans/PLUGIN_AUDIT_REPORT.md` (semantic-scholar-mcp 패치노트)
- Rate limit rule: `.claude/rules/mcp_rate_limit_rules.md` (upgrade guard)
- Prior session (HTTPS-only): `session_reports/2026-05/2026-05-16_semantic_scholar_api_key_activation.md`
