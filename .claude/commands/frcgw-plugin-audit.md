# frcgw-plugin-audit

## Purpose

외부 plugin 또는 MCP 서버 설치 전에 Pipeline F(FRCG-PLUGIN-AUDIT-LOOP)를 실행한다.
`frcgw-plugin-security-auditor` subagent를 호출하여 10-item audit checklist를 수행한다.
결과는 `plans/PLUGIN_AUDIT_REPORT.md`에 기록된다.

**반드시 install 전에 실행한다.**

---

## Usage

```text
/frcgw-plugin-audit <plugin-name-or-url>
```

예시:
```text
/frcgw-plugin-audit superpowers
/frcgw-plugin-audit obra/superpowers-marketplace
/frcgw-plugin-audit playwright npx @playwright/mcp@latest
/frcgw-plugin-audit github/github-mcp-server
```

---

## Workflow

1. `plans/P1_5_PLUGIN_SKILL_AGENT_HOOK_PIPELINE_PLAN.md` §2~§3을 읽어 현재 known verdicts 확인.
2. 이미 REJECT 판정된 후보이면 즉시 종료 + 사유 출력.
3. `frcgw-plugin-security-auditor` subagent를 실행하여 10-item checklist 수행.
4. 결과를 `plans/PLUGIN_AUDIT_REPORT.md`에 append.
5. verdict 출력:
   - `install-now`: main agent가 설치 실행 가능.
   - `install-later`: 해당 phase 도달 시 재실행.
   - `audit-only`: 추가 정보 필요.
   - `reject`: 설치 금지.

---

## Known Verdicts (재심 없이 적용)

| Candidate | Verdict |
|---|---|
| github MCP | REJECT |
| code-review (third-party) | REJECT |
| code-simplifier | REJECT |
| skill-creator | REJECT |
| claude-md-management | REJECT |
| Context7 | KEEP (이미 설치) |
| superpowers | AUDIT_ONLY (재심 필요) |
| Playwright MCP | INSTALL_LATER @ P4 |

---

## Required Files

- `plans/PLUGIN_AUDIT_REPORT.md` (audit 결과 append)
- `plans/P1_5_PLUGIN_SKILL_AGENT_HOOK_PIPELINE_PLAN.md` (policy reference)

---

## Stop Conditions

- PAT/API-key가 project 파일에 저장되는 구조이면 무조건 REJECT.
- `enableAllProjectMcpServers=true`를 추가로 설정하는 plugin은 REJECT.
- hook을 동봉하여 우리 PreToolUse/PostToolUse/Stop matcher와 충돌 가능성이 있으면 AUDIT_ONLY 이상.
