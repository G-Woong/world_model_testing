# Decision Log — Session STEP 5-REAL: MCP Real Installation

근거: `docs/orchestration/03_MAIN_CLAUDE_ORCHESTRATION_PROTOCOL.md §4`, `docs/orchestration/10_MCP_SECURITY_POLICY.md §10 Gate 1`
날짜: 2026-05-15
session_id: 20260515-006
branch: solo/p3-final-boss-cleared
HEAD_start: 7dc291d

---

## DEC_2026-05_012

```yaml
decision_id: DEC_2026-05_012
turn_id: 6
timestamp: 2026-05-15T00:00:00+09:00
decision_type: HUMAN_APPROVAL_REQUEST
subject: STEP 5-REAL MCP 실제 설치 범위 + 하네스 audit 동시 수행
selected_option: A
meaning: >
  uv 0.11.14 설치.
  arxiv-mcp-server 0.4.12 설치 (C:\Users\computer\.local\bin\).
  semantic-scholar-mcp 0.1.0 설치 (FujishigeTemma, git HEAD ead98e8).
  Context7 유지 (변경 없음).
  GitHub MCP 보류 (PAT 미제공).
  doi-mcp 보류 (maturity 부족).
  .mcp.json 업데이트: context7 + arxiv + semantic-scholar.
  .claude/settings.local.json enabledMcpjsonServers 갱신 (1회 명시 승인).
  STEP 1~5 하네스 중간점검 보고서 작성.
execution_step: STEP 5-REAL
status: EXECUTED
requires_additional_approval_before_execution: false
evidence:
  - STEP 5-REAL PLAN (이전 세션 transcript 81f0b5cc)
  - 사용자 "Implement the following plan" 지시 (Option A 선택 명시)
  - Docker 27.4.0 가용 확인됨
  - semantic-scholar 후보 교체: JackKuo666 → FujishigeTemma (더 깨끗한 uv git+ 설치)
  - Phase 1 exploration: Agent 2 하네스 audit, Agent 3 외부 MCP 후보 재확인
  - Prompt injection 1건 발견됨 (WebFetch uv docs 중 fake system-reminder) → quarantine 처리
risk: LOW
reasoning: >
  uv가 .venv pip install로 설치 가능 → 이전 STEP 5 toolchain gap 해소.
  FujishigeTemma semantic-scholar-mcp가 uv tool install git+...으로 설치 가능 → maturity 우려 해소.
  arxiv-mcp-server v0.4.12 community mature (2.7k stars).
  settings.local.json 수정 범위 최소화 (enabledMcpjsonServers 1줄만).
  R2 LOCK 유지 — enableAllProjectMcpServers=false.
  Phase 4 related-work agents (09 §4) 가동을 위한 필수 조건 충족.
approval: HUMAN_APPROVED
outcome: >
  EXECUTED — uv 0.11.14 + arxiv 0.4.12 + semantic-scholar 0.1.0 설치 완료.
  .mcp.json 3서버 등록. enabledMcpjsonServers 갱신.
  Smoke test: arxiv PASS, semantic-scholar PARTIAL (API 429 rate limit).
  하네스 audit: 7 layers PASS (F layer PARTIAL).
  Gate Verdict: PARTIAL.
  GitHub MCP: PAT 미제공으로 DEFERRED.
executed_at: 2026-05-15T00:00:00+09:00
executed_commit: (STEP 5-REAL commit — see session 20260515-006 §8)
executed_session: 20260515-006
```

---

## Cross-link

- Session report: `docs/orchestration/session_reports/2026-05/2026-05-15_step5_real_mcp_installation.md`
- Harness audit: `docs/orchestration/session_reports/2026-05/2026-05-15_step1_to_step5_harness_audit.md`
- Human feedback: `docs/orchestration/human_feedback/2026-05/HF_20260515_002.md`
- MCP query log: `docs/orchestration/mcp_research/2026-05/MCP_20260515_002.md`
- Prior decision: `docs/orchestration/decision_logs/2026-05/session_step5_mcp.md` (DEC_011)
- Decision logs INDEX: `docs/orchestration/decision_logs/INDEX.md`
