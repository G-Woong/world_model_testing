# PLUGIN_AUDIT_REPORT.md

Pipeline F (FRCG-PLUGIN-AUDIT-LOOP) 산출물.
plugin/MCP 설치 전 심사 결과를 기록한다.

---

## Audit Policy

- Install 전 `/frcgw-plugin-audit <name>` 명령 또는 `frcgw-plugin-security-auditor` subagent 실행 필수.
- PAT/token을 project 파일에 저장하는 구조 → 무조건 REJECT.
- hook 동봉 plugin → 우리 settings.json 충돌 확인 후만 install-later PROMOTE.
- Source: `plans/P1_5_PLUGIN_SKILL_AGENT_HOOK_PIPELINE_PLAN.md` §2~§3, §6.

---

## Entries

### superpowers (obra/superpowers-marketplace)
- audited: 2026-05-08
- source: github.com/obra/superpowers-marketplace
- stars: 940
- official status: community-marketplace
- bundled: 20+ skills (core), Elements of Style, Developing-for-Claude-Code, Private Journal MCP, SessionStart hook
- hook conflict: SessionStart context injection conflicts potentially with our `pre_tool_guard.ps1` daily-sentinel mechanism
- MCP: Private Journal MCP (network yes, secret unknown)
- secret risk: unknown (Private Journal MCP auth not fully documented)
- Windows compatibility: no known issues reported in README
- install scope: user recommended
- audit items: 1-Official=community ✓, 2-Source=known ✓, 3-Issues=11 open (topics unknown) ?, 4-Manifest=full bundle ?, 5-Hook=SessionStart conflict ?, 6-MCP=Private Journal MCP ?, 7-File write=unknown ?, 8-Scope=user ✓, 9-Uninstall=unknown ?, 10=NOT ALL GREEN
- **verdict: AUDIT_ONLY**
- reason: SessionStart hook and Private Journal MCP require deeper audit before install. 10-item checklist not fully green. Re-audit if specific skills (testing/debugging) are needed at P3.

---

### github MCP (github/github-mcp-server)
- audited: 2026-05-08
- source: github.com/github/github-mcp-server v1.0.3 (2026-04-24)
- official status: official-vendor (GitHub Inc.)
- bundled: GitHub API full (repos, issues, PRs, discussions, code, search)
- secret risk: GITHUB_PERSONAL_ACCESS_TOKEN required; no gh CLI passthrough; PAT must live in env
- Windows: Docker required for local; or npm binary
- scope: user scope possible but PAT in OS env still required
- **verdict: REJECT** *(superseded — see re-audit 2026-05-17 below)*
- reason: Project policy forbids PAT in project files. No gh CLI passthrough support. All GitHub operations covered by `gh` CLI via Bash.

### github MCP (github/github-mcp-server) — 재심사 2026-05-17

- re-audited: 2026-05-17
- source: github.com/github/github-mcp-server (same binary, ghcr.io/github/github-mcp-server)
- previous verdict: **REJECT** (2026-05-08)
- **new verdict: ACCEPTED**
- current `.mcp.json` config:
  - transport: `docker run -i --rm` (ephemeral, no persistent container)
  - PAT: `--env-file C:/Users/computer/Desktop/ICLR_WM_claude-code/.env` — `.env` is gitignored (`.gitignore` line 1 + line 73); PAT NOT in project files
  - `GITHUB_READ_ONLY=1` env flag enforced
  - `GITHUB_LOCKDOWN_MODE=1` env flag enforced
  - `GITHUB_TOOLSETS=repos,issues,pull_requests` — toolset restricted (no admin, discussions, code, search)
- 10-item checklist (re-evaluation):
  - 1-Official=official-vendor (GitHub Inc.) ✓
  - 2-Source=ghcr.io/github/github-mcp-server (official GitHub registry) ✓
  - 3-Issues=none blocking ✓
  - 4-Manifest=toolset-restricted (repos/issues/pull_requests only) ✓
  - 5-Hook=none (stdio Docker MCP, no hooks bundled) ✓
  - 6-MCP=GitHub API HTTPS only ✓
  - 7-File-write=none (read-only mode enforced) ✓
  - 8-Scope=project (enabledMcpjsonServers 명시 승인, settings.local.json) ✓
  - 9-Uninstall=remove docker entry from .mcp.json ✓
  - 10-ALL-GREEN ✓
- transport verification: 3-agent diagnosis (2026-05-17) confirmed:
  - Docker image pulled ✓, PAT scope=public_repo ✓, stdio handshake → `server session connected` ✓
  - `docker ps` empty = `--rm` normal behavior (not a crash) ✓
  - Claude Code "deferred schema load" misidentified as death — tool works when ToolSearch schema fetched
- R2 Lock: `enableAllProjectMcpServers: false` preserved in `.claude/settings.local.json` ✓
- change from REJECT: PAT now in `.env` (untracked), READ_ONLY+LOCKDOWN flags in place, toolset restricted
- remaining risk: Docker dependency (requires Docker Desktop running); `.env` must not be committed
- reason: 10-item checklist ALL GREEN. PAT isolated in gitignored `.env`. Lockdown+read-only flags reduce write surface. Official GitHub vendor image. Transport confirmed working.

---

---

### Playwright MCP (microsoft/playwright-mcp)
- audited: 2026-05-08
- source: github.com/microsoft/playwright-mcp v0.0.75 (2026-05-07)
- stars: 32,200
- official status: official-vendor (Microsoft)
- bundled: browser automation MCP
- network: yes (browser launch + site access)
- file write: yes (trace files)
- secret: none
- Windows: cross-platform via npm; "not a security boundary" warning
- install command: `claude mcp add playwright npx @playwright/mcp@latest`
- install scope: project MCP (user-scope also possible)
- **verdict: INSTALL_LATER @ P4**
- reason: Required for synthetic GUI MVE (P4). Not needed until P4. Re-audit at P4 arrival with updated docs.

---

### code-review (third-party plugin name)
- audited: 2026-05-08
- **verdict: REJECT**
- reason: No third-party plugin with this name verified in official marketplace. Built-in `/review` + `/security-review` skills already available and cover all code review needs.

---

### code-simplifier
- audited: 2026-05-08
- **verdict: REJECT**
- reason: Not found as an official or community marketplace plugin. Built-in `/simplify` skill already available.

---

### skill-creator
- audited: 2026-05-08
- **verdict: REJECT**
- reason: Not found in official Anthropic skills repo (github.com/anthropics/skills). Replace with project-local `.claude/commands/` custom skills.

---

### claude-md-management
- audited: 2026-05-08
- **verdict: REJECT**
- reason: No plugin with this name exists. Built-in `/init` handles CLAUDE.md scaffolding.

---

### Context7 (upstash/context7)
- audited: P0 (pre-existing)
- source: mcp.context7.com/mcp (HTTP)
- **verdict: KEEP**
- reason: Already configured in `.mcp.json` and `.claude/settings.local.json`. `claude mcp list` shows ✓ Connected. No additional plugin needed.

---

### semantic-scholar-mcp (FujishigeTemma)

- audited: 2026-05-16
- source: github.com/FujishigeTemma/semantic-scholar-mcp (commit ead98e8)
- version: 0.1.0
- official status: community (not official Semantic Scholar vendor)
- installed: `uv tool install git+https://github.com/FujishigeTemma/semantic-scholar-mcp` → `C:\Users\computer\.local\bin\semantic-scholar-mcp`
- network: yes (api.semanticscholar.org HTTPS)
- file write: no (stdio MCP, no local file I/O)
- secret: `SEMANTIC_SCHOLAR_API_KEY` — env-injected via `.mcp.json` env 블록 (`.gitignore` 라인 108에서 `.mcp.json` untracked → git 노출 없음)
- hook conflict: none (stdio MCP, no hooks)
- rate-limit: **caller-enforced 1 RPS** (도구 내부 retry/back-off 없음 — `.claude/rules/mcp_rate_limit_rules.md` 정책 준수)
- Windows compatibility: uv-managed python 환경, 확인 완료
- 10-item checklist:
  - 1-Official=community ✓
  - 2-Source=known (FujishigeTemma, git commit ead98e8) ✓
  - 3-Issues=minor (FujishigeTemma는 소규모 repo) ✓
  - 4-Manifest=slim (serve/stdio 전용) ✓
  - 5-Hook=none ✓
  - 6-MCP=SemanticScholar API only ✓
  - 7-File-write=none ✓
  - 8-Scope=project (enabledMcpjsonServers 명시 승인) ✓
  - 9-Uninstall=`uv tool uninstall semantic-scholar-mcp` ✓
  - 10-ALL-GREEN ✓
- smoke test: 3a auth check PASS, 3b HTTP 200 PASS, 3c rate-limit 2-call PASS (interval=2.078s, 429=0)
- **verdict: ACCEPTED**
- reason: 10-item checklist ALL GREEN. secret은 env-injected로 git 비노출. network은 HTTPS only. rate-limit는 caller-side 정책으로 강제. 인증 호출 검증 완료 (MCP_20260516_004 PASS).
- **[2026-05-16 패치노트]** cli.py 패치 적용 (session 20260516-010):
  - 원인 RC-001: Windows cp949 UnicodeEncodeError (✓ 문자) → .mcp.json PYTHONUTF8=1+PYTHONIOENCODING=utf-8 추가로 해결
  - 원인 RC-002: banner 14개 click.echo가 stdout 출력 → MCP stdio 규약 위반 → err=True 추가로 stderr redirect
  - stdio 4a 검증: stdout JSON-only, stderr banner, UnicodeEncodeError 없음 PASS
  - MCP stdio 연결: HTTPS-only PARTIAL → full-MCP PASS (DEC_012 addendum_002)
- **[upgrade guard]** `uv tool upgrade semantic-scholar-mcp` 실행 시 cli.py 패치 덮어쓰여짐 주의.
  - 재적용 runbook: `docs/orchestration/session_reports/2026-05/2026-05-16_semantic_scholar_mcp_connection_fix.md` § Patch reapplication runbook
  - 패치 검증: `Select-String -Pattern 'err=True' cli.py | Measure-Object` → 14건 기대

---

## Pending Re-Audits

| Candidate | Trigger Condition |
|---|---|
| superpowers | P3 도달 or specific debugging need identified |
| Playwright MCP | P4 synthetic GUI MVE phase starts |
