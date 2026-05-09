---
description: >
  `/plugin install`, `/plugin marketplace add`, `claude mcp add` 같은 발화나 명령 시도가
  발생하면 설치 직전에 실행한다. 외부 plugin/MCP의 source/permission/hook/MCP/network/secret/
  Windows risk를 10-item checklist로 audit한다. 결과는 plans/PLUGIN_AUDIT_REPORT.md에 기록된다.
---

# frcgw-plugin-audit

Source MDs: `plans/P1_5_PLUGIN_SKILL_AGENT_HOOK_PIPELINE_PLAN.md` §2~§3;
`code.claude.com/docs/en/plugins`.

## 10-Item Audit Checklist

1. **Official status**: vendor(Anthropic/GitHub/Microsoft/Upstash) or community-marketplace or unknown?
2. **Source repo**: URL + last commit date + ⭐ count.
3. **Issue tracker scan**: Windows compatibility / hook 충돌 / security 항목 exists?
4. **Plugin manifest structure**: `.claude-plugin/plugin.json` + bundled dirs
   (skills/ agents/ hooks/ .mcp.json/ .lsp.json/ monitors/ bin/ settings.json).
5. **Hook conflict check**: bundled hooks의 event/matcher가 우리 `settings.json` PreToolUse/PostToolUse/Stop/UserPromptSubmit/SubagentStop/PreCompact 와 충돌 가능성.
6. **Bundled MCP**: network endpoint, auth mode, secret 요구사항.
7. **File write scope**: 어떤 경로에 write하는가.
8. **Install scope**: project vs user. PAT/token 필요 시 무조건 user scope 권고.
9. **Uninstall path**: rollback 절차 명시.
10. **Result**: 위 9개 항목 전부 green이면 install-later PROMOTE; 1개라도 unknown/red이면 audit-only 또는 reject.

## Known Decisions (갱신 금지)

| Plugin | Verdict | Reason |
|---|---|---|
| superpowers (obra) | AUDIT_ONLY | SessionStart hook 동봉, Private Journal MCP 동봉 — 충돌 위험 audit 미완 |
| github MCP | REJECT | PAT 필수, gh CLI passthrough 미지원, project-scope 정책 위반 |
| Playwright MCP | INSTALL_LATER (P4) | P4 synthetic GUI MVE 도달 시 재평가 |
| code-review (third-party) | REJECT | 존재 미검증, built-in /review로 대체 |
| code-simplifier | REJECT | 존재 미검증, built-in /simplify로 대체 |
| skill-creator | REJECT | 공식 repo 부재 |
| claude-md-management | REJECT | plugin 존재 안 함, built-in /init 사용 |
| Context7 | KEEP | 이미 connected |

## Required Output

```
Candidate: <name>
Source: <URL>
Checklist: 1-10 결과 테이블
Verdict: install-now / install-later / audit-only / reject
Reason: <text>
PLUGIN_AUDIT_REPORT.md updated: YES/NO
```

## Stop Condition

"install-now"가 아닌 한, install 명령 실행 금지.
PAT/API-key가 project 파일에 저장되는 구조이면 무조건 REJECT.
