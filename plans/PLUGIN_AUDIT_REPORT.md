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
- **verdict: REJECT**
- reason: Project policy forbids PAT in project files. No gh CLI passthrough support. All GitHub operations covered by `gh` CLI via Bash.

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

## Pending Re-Audits

| Candidate | Trigger Condition |
|---|---|
| superpowers | P3 도달 or specific debugging need identified |
| Playwright MCP | P4 synthetic GUI MVE phase starts |
