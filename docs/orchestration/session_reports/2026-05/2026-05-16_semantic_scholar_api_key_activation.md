# Session Report — 2026-05-16: Semantic Scholar API 키 활성화

session_id: 20260516-009
date: 2026-05-16
branch: solo/p3-final-boss-cleared
mode: full
근거: `docs/orchestration/08_AGENT_OUTPUT_CONTRACTS.md §5`

---

## 목표

DEC_2026-05_012 Gate PARTIAL(HTTP 429) → PASS 갱신.  
Semantic Scholar API 키를 MCP 서버가 실제로 읽도록 주입하고, 인증 호출 검증, caller-side 1 RPS 정책 명문화.

---

## 세션 흐름

### Phase 1 — 탐색 (이전 세션, plan mode)

| 발견 사항 | 의미 |
|---|---|
| `SEMANTIC_SCHOLAR_API_KEY` 단 1개 환경변수 표면 (`cli.py:45,122`) | `.env` 자동로드 없음 → `.mcp.json` env 블록 주입 필요 |
| `requests.get(..., timeout=30)` 단순 호출, 비-200 에러 TextContent 반환 (`server.py:397,428,467,500`) | retry/back-off 없음 → caller-side 정책 필요 |
| `python-dotenv` — transitive dep만 있고 패키지에서 임포트 없음 | `.env`만으로는 MCP 서버가 키를 못 읽음 |
| `.mcp.json`은 `.gitignore` 라인 108에서 untracked | inline 키 주입해도 git 노출 없음 |

### Phase 2 — 구현 (이번 세션)

1. **`.mcp.json` 수정** (line 20): `SEMANTIC_SCHOLAR_API_KEY` 빈 값 → 실제 키 주입
2. **`.claude/rules/mcp_rate_limit_rules.md` 신규 생성**: 1 RPS 정책, sequential 강제, 429 stop condition, budget logging 경로
3. **검증**:
   - JSON 파싱 OK
   - 3a auth: `x-api-key` 헤더 전송 확인
   - 3b data fetch: HTTP 200, 5 results
   - 3c rate-limit: 2 calls, interval=2.078s ≥ 1.0s, 429=0

---

## 결정 사항

| 결정 | 근거 |
|---|---|
| `.mcp.json` env 블록 inline 주입 (vs dotenv shim) | dotenv 없이 동작하는 가장 단순한 wiring, git 비노출 |
| caller-side 1 RPS rule 파일 (`mcp_rate_limit_rules.md`) | 도구 자체 수정 없이 정책 강제 가능한 최소 개입 |
| MCP 자체 retry 패치 PR 제출 안 함 | upstream 변경은 별도 결정 필요 (out of scope) |

---

## 검증 결과 요약

| 항목 | 결과 |
|---|---|
| JSON 파싱 | OK |
| key length | 44 chars |
| 3a auth header | x-api-key set ✓ |
| 3b HTTP status | 200 |
| 3b result count | 5 |
| 3b first paper | [2025] WebEvolver: Enhancing Web Agent Self-Improvement with Coevolving World Model |
| 3c call 1 status | 200 |
| 3c call 2 status | 200 |
| 3c interval | 2.078s ≥ 1.0s |
| 3c 429 count | 0 |
| **Verdict** | **PASS** |

---

## 변경 파일

| 파일 | 작업 |
|---|---|
| `.mcp.json` | env.SEMANTIC_SCHOLAR_API_KEY 주입 |
| `.claude/rules/mcp_rate_limit_rules.md` | 신규 생성 (1 RPS 정책) |
| `docs/orchestration/mcp_research/2026-05/MCP_20260516_004.md` | 신규 생성 (smoke test 결과, PASS) |
| `docs/orchestration/mcp_research/_call_log/semantic_scholar_2026-05-16.tsv` | 신규 생성 (3 rows) |
| `docs/orchestration/mcp_research/INDEX.md` | MCP_20260516_004 row 추가 |
| `docs/orchestration/decision_logs/2026-05/session_step5_real_mcp.md` | DEC_012 addendum (PARTIAL→PASS) |
| `plans/PLUGIN_AUDIT_REPORT.md` | semantic-scholar-mcp ACCEPTED 엔트리 추가 |
| `docs/orchestration/session_reports/INDEX.md` | 본 세션 row 추가 |

---

## 잔존 위험

| 위험 | 현황 |
|---|---|
| upstream retry 없음 | caller-side 1 RPS 정책으로 완화. 429 발생 시 즉시 중단 조건 명문화 |
| API 키 `.mcp.json` inline | `.gitignore` 라인 108 untracked → git 비노출. backup은 `.env` 유지 |
| 세션 reload 전 MCP 툴 미반영 | 다음 세션 시작 시 `mcp__semantic-scholar__*` 툴 노출 예상 |

---

## Blockers

none

---

## Cross-links

- DEC_012 addendum: `decision_logs/2026-05/session_step5_real_mcp.md`
- MCP query log: `mcp_research/2026-05/MCP_20260516_004.md`
- Rate-limit policy: `.claude/rules/mcp_rate_limit_rules.md`
- Plugin audit: `plans/PLUGIN_AUDIT_REPORT.md` (semantic-scholar-mcp ACCEPTED)
- Call log: `mcp_research/_call_log/semantic_scholar_2026-05-16.tsv`
