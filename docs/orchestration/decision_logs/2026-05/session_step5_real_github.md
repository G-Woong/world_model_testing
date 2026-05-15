---
decision_id: DEC_2026-05_013
turn_id: 8
timestamp: "2026-05-16T00:00:00+09:00"
decision_type: HUMAN_APPROVAL_REQUEST
subject: GitHub MCP v1.0.4 실제 활성화 (Option A+)
selected_option: "A+"
status: EXECUTED
execution_step: STEP 5-REAL-GITHUB
---

# DEC_2026-05_013 — GitHub MCP v1.0.4 실제 활성화

작성일: 2026-05-16
작성자: Main Claude (STEP 5-REAL-GITHUB)
근거: `docs/orchestration/10_MCP_SECURITY_POLICY.md §2/§10`, `docs/orchestration/09_MCP_RESEARCH_STACK.md §5`

---

## Decision YAML

```yaml
decision_id: DEC_2026-05_013
turn_id: 8
timestamp: 2026-05-16T00:00:00+09:00
decision_type: HUMAN_APPROVAL_REQUEST
subject: GitHub MCP v1.0.4 실제 활성화 (Option A+)
selected_option: A+   # STEP 5-REAL Option A + GitHub MCP
status: EXECUTED
execution_step: STEP 5-REAL-GITHUB
meaning: >
  ghcr.io/github/github-mcp-server:latest (v1.0.4) Docker image pull.
  .mcp.json에 "github" stdio 엔트리 추가 — docker run -i --rm
  --env-file .env -e GITHUB_READ_ONLY=1
  -e GITHUB_TOOLSETS=repos,issues,pull_requests
  -e GITHUB_LOCKDOWN_MODE=1 ghcr.io/github/github-mcp-server.
  .claude/settings.local.json enabledMcpjsonServers에 "github" 1줄 추가.
  사용자가 .env에 GITHUB_PERSONAL_ACCESS_TOKEN alias 1줄 추가.
  smoke test 5건 수행: --version PASS, --help PASS, init log PASS,
  list-scopes PASS (19 read-only tools, 0 write tools), PAT auth PARTIAL.
risk: LOW-MEDIUM
reasoning: >
  공식 v1.0.4 image, read-only enforced, toolset whitelist 3개,
  lockdown mode 동시 적용. PAT는 .env (gitignored) → docker --env-file로만 주입.
  .mcp.json에 평문 없음. R2 LOCK 유지 (enableAllProjectMcpServers=false).
  Phase 4 related-work-mcp-scout 가동 evidence channel 완비.
approval: HUMAN_APPROVED
approval_evidence: >
  사용자 prompt "Implement the following plan: STEP 5-REAL-GITHUB Plan" 명시 지시.
  .env alias 추가 완료 응답 확인.
```

---

## 실행 결과

| 항목 | 결과 |
|---|---|
| Docker image | `ghcr.io/github/github-mcp-server:latest` pulled ✅ |
| Image digest | `sha256:e3816a476a977cfb836e7d221510011436c654d11861db66ecfd826601aba6a4` |
| Image version | v1.0.4 (2026-05-11 빌드) |
| .mcp.json | github 엔트리 추가 ✅ |
| settings.local.json | enabledMcpjsonServers "github" 추가 ✅ |
| R2 LOCK | enableAllProjectMcpServers=false 유지 ✅ |
| Smoke Test 1 (--version) | PASS ✅ |
| Smoke Test 2 (--help) | PASS ✅ |
| Smoke Test 3 (init log) | PASS ✅ — readOnly=true, lockdownEnabled=true, scopes=[public_repo] |
| Smoke Test 4 (list-scopes) | PASS ✅ — 19 tools 모두 👁, write tool 없음 |
| Smoke Test 5 (PAT API call) | PARTIAL — Windows Docker stdin pipe 제약 SKIP; PAT 인증은 Smoke 3에서 확인 |
| Token leakage scan | 0 hits CLEAN ✅ |
| Prompt injection scan | 0 hits CLEAN ✅ |
| Gate verdict | PASS ✅ |

---

## Security Context

| Security Layer | 적용 상태 |
|---|---|
| GITHUB_READ_ONLY=1 | ✅ (readOnly=true 로그 확인) |
| GITHUB_TOOLSETS=repos,issues,pull_requests | ✅ (tools 목록: 3 toolsets만) |
| GITHUB_LOCKDOWN_MODE=1 | ✅ (lockdownEnabled=true 로그 확인) |
| PAT: .env-file only, no plaintext in .mcp.json | ✅ |
| R2 LOCK (enableAllProjectMcpServers=false) | ✅ |
| Toolset whitelist (no write) | ✅ — list-scopes: 0 📝 tools |

---

## Rollback Info

| 항목 | 방법 |
|---|---|
| .mcp.json rollback | github 엔트리 수동 제거 (.gitignored — git restore 불가) |
| settings.local.json rollback | enabledMcpjsonServers에서 "github" 제거 |
| Image rollback | `docker rmi ghcr.io/github/github-mcp-server` |
| Commit rollback | `git revert <STEP5-REAL-GITHUB commit>` (reset --hard 금지) |

---

## Cross-links

- Human Feedback: `docs/orchestration/human_feedback/2026-05/HF_20260516_003.md`
- MCP Log: `docs/orchestration/mcp_research/2026-05/MCP_20260516_003.md`
- Session Report: `docs/orchestration/session_reports/2026-05/2026-05-16_step5_real_github_mcp.md`
- MCP Security Policy: `docs/orchestration/10_MCP_SECURITY_POLICY.md`
