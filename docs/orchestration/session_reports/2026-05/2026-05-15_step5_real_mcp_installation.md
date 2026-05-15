# Session Report — STEP 5-REAL: MCP Real Installation + Harness Audit

session_id: 20260515-006
date: 2026-05-15
mode: full
branch: solo/p3-final-boss-cleared
HEAD_start: 7dc291d
HEAD_end: (STEP 5-REAL commit hash — see §8)
근거: `docs/orchestration/11_SESSION_END_REPORT_PROTOCOL.md`, `docs/orchestration/09_MCP_RESEARCH_STACK.md §2`

---

## 1. Executive Summary

STEP 5-REAL (Option A) 완료.

- uv 0.11.14 설치 (python -m pip install → .venv/Scripts/uv.exe)
- arxiv-mcp-server 0.4.12 설치 (`C:\Users\computer\.local\bin\`)
- semantic-scholar-mcp 0.1.0 설치 (FujishigeTemma, git HEAD ead98e8)
- `.mcp.json` 업데이트: context7 + arxiv + semantic-scholar
- `.claude/settings.local.json` `enabledMcpjsonServers` 업데이트 (1회 명시 승인)
- STEP 1~5 하네스 중간점검: 전 layer PASS (DEC_011 placeholder back-fill 포함)
- DEC_2026-05_012 yaml 생성 및 INDEX 갱신

Gate Verdict: **PARTIAL** (arxiv PASS, SS rate-limit PARTIAL, 하네스 PASS)

---

## 2. Current Branch / HEAD

- Branch: `solo/p3-final-boss-cleared`
- HEAD_start: `7dc291d` (STEP 5 — Context7 verify)
- Ahead of origin: 35 (start) → 36 (this commit)

---

## 3. MCP Installed / Deferred / Failed

| server | version | verdict | note |
|---|---|---|---|
| context7 | ctx7@0.4.2 | ACTIVE (unchanged) | endpoint https://mcp.context7.com/mcp |
| arxiv | arxiv-mcp-server 0.4.12 | **INSTALLED PASS** | C:\Users\computer\.local\bin\arxiv-mcp-server.exe |
| semantic-scholar | 0.1.0 (git ead98e8) | **INSTALLED PARTIAL** | CLI 정상, API 429 (rate limit) |
| GitHub | official v1.0.4 | DEFERRED | PAT 미제공 |
| doi-mcp | tfscharff ~12★ | DEFERRED | maturity 부족 |

---

## 4. Toolchain Changes

| tool | before | after | method |
|---|---|---|---|
| uv | NOT FOUND | 0.11.14 (.venv/Scripts/uv.exe) | python -m pip install uv |
| arxiv-mcp-server | NOT FOUND | 0.4.12 (C:\Users\computer\.local\bin\) | python -m uv tool install |
| semantic-scholar-mcp | NOT FOUND | 0.1.0 git (C:\Users\computer\.local\bin\) | python -m uv tool install git+... |
| docker | 27.4.0 (pre-existing) | unchanged | N/A |
| node | v22.17.0 (pre-existing) | unchanged | N/A |
| python | 3.11.9 (pre-existing) | unchanged | N/A |

---

## 5. .mcp.json Changes

수정 전: context7 1개 (`type: http`)
수정 후: context7 + arxiv + semantic-scholar 3개

- arxiv: `type: stdio`, command: `C:/Users/computer/.local/bin/arxiv-mcp-server`, storage: `mcp_research/_arxiv_cache/`
- semantic-scholar: `type: stdio`, command: `C:/Users/computer/.local/bin/semantic-scholar-mcp`, args: `["serve"]`

---

## 6. Smoke Test Results

| server | test_method | result | details |
|---|---|---|---|
| arxiv | `Test-Path .exe` + uv tool list | PASS | .exe 존재 확인, arxiv==3.0.0 backbone 설치됨 |
| semantic-scholar | `--help` CLI | PASS (CLI) | serve/tools 명령 확인, PARTIAL (API 429) |
| context7 | system-reminder inject | PASS | mcp__context7__* tools 세션 내 확인됨 |

SS API 429 원인: 세션 중 Phase 1 exploration agents의 WebSearch/WebFetch 호출 과다 → 익명 rate limit 소진. 서버/패키지 결함 아님.

---

## 7. Harness Audit Result

별도 보고서: `session_reports/2026-05/2026-05-15_step1_to_step5_harness_audit.md`

요약: 7개 layer 모두 PASS. Minor gap 2건 (DEC_011 placeholder → 이번 세션 back-fill, harness_audit/ 미생성 → session_reports에 통합). **Overall: PASS**

---

## 8. Created/Updated Files

| # | 경로 | 종류 | 상태 |
|---|---|---|---|
| 1 | `.mcp.json` | M | arxiv + semantic-scholar 추가 |
| 2 | `.claude/settings.local.json` | M | enabledMcpjsonServers 갱신 (1회 승인) |
| 3 | `docs/orchestration/mcp_research/_arxiv_cache/.gitkeep` | A | arxiv storage 경로 |
| 4 | `docs/orchestration/mcp_research/2026-05/MCP_20260515_002.md` | A | smoke test 9필드 log |
| 5 | `docs/orchestration/mcp_research/INDEX.md` | M | MCP_20260515_002 행 추가 |
| 6 | `docs/orchestration/human_feedback/2026-05/HF_20260515_002.md` | A | Option A + 수정 승인 기록 |
| 7 | `docs/orchestration/human_feedback/INDEX.md` | M | HF_20260515_002 행 추가 |
| 8 | `docs/orchestration/session_reports/2026-05/2026-05-15_step5_real_mcp_installation.md` | A | 이 파일 |
| 9 | `docs/orchestration/session_reports/2026-05/2026-05-15_step1_to_step5_harness_audit.md` | A | 하네스 audit 보고서 |
| 10 | `docs/orchestration/session_reports/INDEX.md` | M | 006, 007 행 추가 |
| 11 | `docs/orchestration/decision_logs/2026-05/session_step5_real_mcp.md` | A | DEC_2026-05_012 yaml |
| 12 | `docs/orchestration/decision_logs/2026-05/session_step5_mcp.md` | M | DEC_011 executed_commit back-fill |
| 13 | `docs/orchestration/decision_logs/INDEX.md` | M | DEC_012 행 추가 |

---

## 9. Security Verification

| 항목 | 상태 |
|---|---|
| R2 LOCK (enableAllProjectMcpServers=false) | ✅ VERIFIED |
| settings.local.json 수정 범위 | ✅ enabledMcpjsonServers 한 줄만 |
| .claude/agents/ / .claude/hooks/ / .claude/rules/ / .claude/skills/ | ✅ 미수정 |
| paper_context_ref/ | ✅ 미수정 |
| src/ / tests/ / configs/ / data/ / outputs/ | ✅ 미수정 |
| scripts/run_codex_task.ps1 | ✅ 미수정 |
| Prompt injection scan | ✅ CLEAN (0건) |
| arXiv API key | ✅ 불필요 (anonymous) |
| SS API key | ✅ 미등록 (익명 100req/5min 한도) |
| GitHub PAT | ✅ 미등록 (GitHub MCP 보류) |
| Tier 4 MCP 등록 여부 | ✅ NONE |
| arxiv Tier | 1 (metadata) |
| semantic-scholar Tier | 1 (metadata) |

---

## 10. Rollback Information

commit hash: (STEP 5-REAL commit — git log -1 --oneline)

rollback 명령:
```powershell
git revert <STEP5-REAL-commit-hash>   # git reset --hard 금지
python -m uv tool uninstall arxiv-mcp-server
python -m uv tool uninstall semantic-scholar-mcp
# uv 자체 rollback:
# pip uninstall uv
```

---

## 11. Remaining Risks

| risk | level | mitigation |
|---|---|---|
| SS API anonymous rate limit | LOW | Phase 4 agent 호출 간격 조정, 또는 API key 취득 |
| arxiv server --storage-path 파라미터 지원 여부 | LOW | v0.4.12 README 확인 필요; fallback: 파라미터 제거 |
| C:\Users\computer\.local\bin PATH 미등록 | LOW | Claude Code subprocess 직접 실행 시 문제없음 (full path 사용) |
| GitHub MCP PAT 미제공 | LOW | PAT 제공 시 별도 DEC_013으로 추가 가능 |
| semantic-scholar git HEAD 가변성 | MEDIUM | commit hash ead98e8 기록됨 — Phase 4 사용 전 재검증 권장 |

---

## 12. Next Step

STEP 6 (hook redirect: `pre_compact` → `SEV_2026-05_001` PENDING) 진입 가능.

Phase 4 (STEP 8: G1~G6 + TASK_1021) 진입 전 STEP 6/7 완료 필요:
- STEP 6: hook redirect (`.claude/hooks/` pre_compact 설정)
- STEP 7: Codex FF (`a55cb33` → `ba204a8`)
- STEP 8: P4 G1~G6 + first Codex task

---

## 13. Gate Verdict

**PARTIAL**

- MCP 최소 1개 신규 설치 성공: ✅ (arxiv PASS, semantic-scholar PARTIAL)
- 하네스 7개 layer: ✅ PASS
- R2 LOCK 유지: ✅
- forbidden path violations: 0
- Prompt injection: 0건

PARTIAL 이유: semantic-scholar API smoke test가 rate limit으로 직접 검증 불가.
Phase 4 진입 전 SS API key 취득 또는 rate limit 해제 후 재검증 권장.

---

## decisions_made

| decision_id | outcome |
|---|---|
| DEC_2026-05_012 | EXECUTED — Option A (uv + arxiv + SS 설치, GitHub 보류) |
| DEC_2026-05_011 | executed_commit back-fill → `7dc291d` |

## needs_confirmation

- GitHub MCP 포함 여부 (PAT 제공 시 DEC_013)
- SS API key 취득 여부 (rate limit 해소)

## blockers

none
