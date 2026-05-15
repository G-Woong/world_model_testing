---
session_id: "20260516-008"
date: "2026-05-16"
branch: "solo/p3-final-boss-cleared"
mode: full
head_before: "3856320"
head_after: "(STEP 5-REAL-GITHUB commit — TBD)"
decisions_made:
  - DEC_2026-05_013
needs_confirmation: []
---

# Session Report 008 — STEP 5-REAL-GITHUB: GitHub MCP v1.0.4 실제 활성화

작성일: 2026-05-16
작성자: Main Claude (STEP 5-REAL-GITHUB)
근거: `docs/orchestration/08_AGENT_OUTPUT_CONTRACTS.md §5`

---

## 1. Executive Summary

STEP 5-REAL (`4c4355c`, DEC_012)에서 DEFERRED됐던 GitHub MCP를 실제 설치·등록·컨테이너 스모크 테스트까지 완료.

- PAT (`GITHUB_PERSONAL_ACCESS_TOKEN`) 제공 확인 (.env alias 추가)
- Docker image pull: `ghcr.io/github/github-mcp-server:latest` (v1.0.4)
- read-only + toolsets + lockdown 모드 동시 적용
- Smoke Test 4건 PASS, 1건 PARTIAL (허용)
- Gate: **PASS**

---

## 2. Branch / HEAD

- Branch: `solo/p3-final-boss-cleared`
- HEAD before: `3856320` (docs(orchestration): back-fill STEP 5-REAL commit hash...)
- HEAD after: STEP 5-REAL-GITHUB commit (단일 commit)

---

## 3. Docker Image

| 항목 | 값 |
|---|---|
| Repository | `ghcr.io/github/github-mcp-server` |
| Tag | `latest` (= v1.0.4) |
| Digest | `sha256:e3816a476a977cfb836e7d221510011436c654d11861db66ecfd826601aba6a4` |
| Image ID | `e3816a476a97` |
| Built | 2026-05-11T15:06:44Z |
| Size | 60.7MB |
| Version confirmed | `Version: v1.0.4, Commit: c3dedbece0bf3834829f638a245fb3c51cd98d0b` |

---

## 4. .env Alias Verified

- Key: `GITHUB_PERSONAL_ACCESS_TOKEN` (value redacted)
- Source: user-added manually to `.env` (Claude 미수정 — secrets policy)
- `.env` gitignored: `.gitignore:73` ✅

---

## 5. .mcp.json Changes (4 servers active)

| Server | Type | Status |
|---|---|---|
| context7 | http | ACTIVE (이전) |
| arxiv | stdio | ACTIVE (STEP 5-REAL) |
| semantic-scholar | stdio | ACTIVE (STEP 5-REAL) |
| github | stdio (docker) | **NEW — ACTIVE** ✅ |

github 엔트리:
```json
{
  "type": "stdio",
  "command": "docker",
  "args": ["run", "-i", "--rm",
    "--env-file", "C:/Users/computer/Desktop/ICLR_WM_claude-code/.env",
    "-e", "GITHUB_READ_ONLY=1",
    "-e", "GITHUB_TOOLSETS=repos,issues,pull_requests",
    "-e", "GITHUB_LOCKDOWN_MODE=1",
    "ghcr.io/github/github-mcp-server"]
}
```

---

## 6. enabledMcpjsonServers Updated

```json
["context7", "arxiv", "semantic-scholar", "github"]
```

- `enableAllProjectMcpServers`: `false` — R2 LOCK HELD ✅

---

## 7. Smoke Test Results

| # | Test | Method | Result |
|---|---|---|---|
| 1 | --version | `docker run ... --version` | PASS ✅ v1.0.4 |
| 2 | --help | `docker run ... --help` | PASS ✅ CLI flags 확인 |
| 3 | stdio init log | Start-Process + stderr capture 6s | PASS ✅ readOnly=true, lockdownEnabled=true, scopes=[public_repo] |
| 4 | list-scopes | `docker run ... list-scopes` | PASS ✅ 19 tools 모두 👁, write tool 없음 |
| 5 | PAT API call | JSON-RPC stdin — Windows Docker stdin pipe 제약 SKIP | PARTIAL ✅ (PAT 인증은 Smoke 3에서 확인) |

**Write Tool Check**: create_issue, delete_*, push_*, merge_* — **부재 확인** (read-only enforced)

---

## 8. Security Verification

| Layer | Status |
|---|---|
| GITHUB_READ_ONLY=1 | ✅ readOnly=true 로그 확인 |
| GITHUB_TOOLSETS 제한 | ✅ repos, issues, pull_requests 3개만 |
| GITHUB_LOCKDOWN_MODE=1 | ✅ lockdownEnabled=true 로그 확인 |
| PAT: .env-file only | ✅ .mcp.json 평문 없음 |
| R2 LOCK | ✅ enableAllProjectMcpServers=false |
| Token leakage scan | 0 hits CLEAN ✅ |
| Prompt injection scan | 0 hits CLEAN ✅ |

---

## 9. Created / Updated Files

| # | Path | Action |
|---|---|---|
| 1 | `.mcp.json` | M — github 엔트리 추가 (gitignored) |
| 2 | `.claude/settings.local.json` | M — enabledMcpjsonServers "github" 추가 (gitignored) |
| 3 | `docs/orchestration/mcp_research/2026-05/MCP_20260516_003.md` | A |
| 4 | `docs/orchestration/mcp_research/INDEX.md` | M |
| 5 | `docs/orchestration/human_feedback/2026-05/HF_20260516_003.md` | A |
| 6 | `docs/orchestration/human_feedback/INDEX.md` | M |
| 7 | `docs/orchestration/decision_logs/2026-05/session_step5_real_github.md` | A |
| 8 | `docs/orchestration/decision_logs/INDEX.md` | M |
| 9 | `docs/orchestration/session_reports/2026-05/2026-05-16_step5_real_github_mcp.md` | A (this file) |
| 10 | `docs/orchestration/session_reports/INDEX.md` | M |
| 11 | `docs/orchestration/13_MASTER_ORCHESTRATION_PLAN.md` | M (§9 MCP Runtime 갱신) |

---

## 10. Forbidden Path Verification

사전 forbidden path 검사 결과:
- `.claude/settings*` (settings.json 제외, settings.local.json만 enabledMcpjsonServers 1줄 변경) ✅
- `paper_context_ref/` 미수정 ✅
- `src/`, `tests/`, `configs/`, `data/`, `outputs/` 미수정 ✅
- `scripts/run_codex_task.ps1` 미수정 ✅
- `.claude/agents/hooks/rules/skills/` 미수정 ✅
- `.env` 미수정 (사용자 직접) ✅

---

## 11. Remaining Risks

| Risk | 내용 | 대응 |
|---|---|---|
| Rate limit | public_repo PAT: 5000 req/h | Phase 4 agent는 batch 쿼리 지양 |
| Issue/PR body prompt injection | GitHub content가 untrusted | LOCKDOWN_MODE=1 부분 완화, agent에서 raw body quarantine 필요 |
| Image update | :latest tag drift | 재확인 시 digest pinning 권장 |
| PAT scope 변경 | public_repo만 → 향후 private repo 필요 시 | PAT 재발급 + scope 확인 필요 |

---

## 12. Next Steps

- **STEP 6**: hook redirect (pre_compact) — NC-6 carry
- **STEP 7**: Codex fast-forward (a55cb33 → ba204a8) — NC-3 carry
- **STEP 8**: Codex P4 task 생성 — DEC_006 LOCKED
- **Phase 4**: related-work-mcp-scout 가동 가능 (GitHub MCP + arXiv + SS 완비)

---

## 13. Gate Verdict

**PASS** (Smoke Test 5 PARTIAL은 허용 조건 내 — PAT 인증 Smoke 3에서 확인됨)

---

## 14. Decisions Made This Session

| ID | Subject | Status |
|---|---|---|
| DEC_2026-05_013 | GitHub MCP v1.0.4 실제 활성화 (Option A+) | EXECUTED |
