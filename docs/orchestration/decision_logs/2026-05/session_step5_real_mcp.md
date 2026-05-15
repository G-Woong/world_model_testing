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
executed_commit: 4c4355c
executed_session: 20260515-006
```

---

## DEC_2026-05_012 Addendum

```yaml
addendum_id: DEC_2026-05_012_addendum_001
timestamp: 2026-05-16T00:00:00+09:00
subject: Semantic Scholar API 키 활성화 + 1 RPS rate-limit 정책 도입
outcome_update: PARTIAL → PASS
evidence:
  - ".mcp.json env.SEMANTIC_SCHOLAR_API_KEY 주입 완료 (commit: solo/p3-final-boss-cleared HEAD)"
  - "3a auth check: x-api-key 헤더 전송 확인"
  - "3b data fetch: HTTP 200, 5 results, first=[2025] WebEvolver: Enhancing Web Agent Self-Improvement with Coevolving World Model"
  - "3c rate-limit test: 2 calls, interval=2.078s >= 1.0s, 429=0"
  - "rate-limit policy: .claude/rules/mcp_rate_limit_rules.md (1 RPS, sequential only, 429 stop condition)"
  - "call log: docs/orchestration/mcp_research/_call_log/semantic_scholar_2026-05-16.tsv"
  - "MCP query log: MCP_20260516_004.md (supersedes MCP_20260515_002)"
verdict: PASS
executed_at: 2026-05-16T00:00:00+09:00
executed_session: 20260516-009
```

---

## DEC_2026-05_012 Addendum 002

```yaml
addendum_id: DEC_2026-05_012_addendum_002
timestamp: 2026-05-16T00:00:00+09:00
subject: Semantic Scholar MCP stdio 연결 실패 근본 원인 해결 (cp949 crash + banner-on-stdout 규약 위반)
prior_verdict_correction: >
  addendum_001의 PASS 판정은 HTTPS direct API 동작만 검증한 것이었다.
  MCP stdio 핸드셰이크 (Claude Code ↔ semantic-scholar-mcp stdio)는 단 한 번도 성공한 적이 없었다.
  본 addendum_002가 실질적인 MCP stdio PASS를 달성한다.
root_causes_fixed:
  - id: RC-001
    title: Windows cp949 console에서 ✓ 문자 UnicodeEncodeError crash
    location: "cli.py:66  click.echo('✓ Semantic Scholar API key configured')"
    fix: ".mcp.json env 블록에 PYTHONUTF8=1, PYTHONIOENCODING=utf-8 추가"
  - id: RC-002
    title: banner 출력이 stdout으로 전송되어 MCP stdio JSON-RPC 규약 위반
    location: "cli.py lines 63,66,68-70,74-78,81-83,104-106 (14개 click.echo 호출)"
    fix: "모든 14개 click.echo에 err=True 추가 → stderr로 redirect"
files_modified:
  - "C:/Users/computer/Desktop/ICLR_WM_claude-code/.mcp.json (args: serve→serve stdio, env: +PYTHONUTF8+PYTHONIOENCODING)"
  - "C:/Users/computer/AppData/Roaming/uv/tools/semantic-scholar-mcp/Lib/site-packages/semantic_scholar_mcp/cli.py (14개 err=True)"
verification_4a:
  stdout_first_line: JSON-RPC (no banner)
  stderr_has_banner: true
  unicode_error: none
  result: PASS
upgrade_guard: >
  uv tool upgrade semantic-scholar-mcp 실행 시 cli.py 패치가 덮어쓰여진다.
  패치 재적용 runbook: docs/orchestration/session_reports/2026-05/2026-05-16_semantic_scholar_mcp_connection_fix.md
  mcp_rate_limit_rules.md에 reminder 추가됨.
verdict: PASS (HTTPS-only PARTIAL → full-MCP PASS)
executed_at: 2026-05-16T00:00:00+09:00
executed_session: 20260516-010
mcp_query_log: docs/orchestration/mcp_research/2026-05/MCP_20260516_005.md
```

---

## Cross-link

- Session report: `docs/orchestration/session_reports/2026-05/2026-05-15_step5_real_mcp_installation.md`
- Harness audit: `docs/orchestration/session_reports/2026-05/2026-05-15_step1_to_step5_harness_audit.md`
- Human feedback: `docs/orchestration/human_feedback/2026-05/HF_20260515_002.md`
- MCP query log: `docs/orchestration/mcp_research/2026-05/MCP_20260515_002.md`
- Prior decision: `docs/orchestration/decision_logs/2026-05/session_step5_mcp.md` (DEC_011)
- Decision logs INDEX: `docs/orchestration/decision_logs/INDEX.md`
