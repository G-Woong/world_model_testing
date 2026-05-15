# Human Feedback Log Index

작성일: 2026-05-15
작성자: Main Claude (STEP 3 scaffold)
근거: `docs/orchestration/12_HUMAN_FEEDBACK_AND_EVOLUTION_PROTOCOL.md §7/§10`, `docs/orchestration/03_MAIN_CLAUDE_ORCHESTRATION_PROTOCOL.md §4`

---

## 목적

사용자(PI/reviewer)의 승인·거절·선택 응답을 추적하는 공식 index.

DECISIONS_REQUIRED 해소 내역, cleanup 승인, settings/MCP 변경 승인 등 모든 human feedback을 기록한다.
`decision_logs/`와 상호 보완 — DEC_NNN ID로 연결. (`12_HUMAN_FEEDBACK_AND_EVOLUTION_PROTOCOL.md §7`)

실제 feedback log는 Phase 4 이후 DEC_NNN 발생 시 생성된다.
이 INDEX는 경로 정의 및 schema를 확정하기 위해 STEP 3에서 생성된다.

---

## Storage Path

```text
피드백 파일:
  docs/orchestration/human_feedback/YYYY-MM/HF_YYYY-MM_NNN.md
  (예: HF_2026-06_001.md)

INDEX (이 파일):
  docs/orchestration/human_feedback/INDEX.md
```

---

## Index Table

| feedback_id | date | related_decision_id | topic | user_response | interpreted_action | status | linked_session |
|---|---|---|---|---|---|---|---|
| HF_20260515_001 | 2026-05-15 | DEC_2026-05_011 | STEP 5 MCP 등록 범위 | Option B (신규 설치 0건, Context7 verify only) | .mcp.json 미수정, DEFER 4건 기록 | RESOLVED | 20260515-005 |
| HF_20260515_002 | 2026-05-15 | DEC_2026-05_012 | STEP 5-REAL MCP 실제 설치 범위 (Option A) | Option A (uv + arXiv + SS FujishigeTemma + ctx7 유지, GitHub 보류) + settings.local.json enabledMcpjsonServers 수정 1회 명시 승인 | 3서버 설치, .mcp.json + enabledMcpjsonServers 업데이트, 하네스 audit 수행 | RESOLVED | 20260515-006 |

---

## Cross-link 규칙

- `decision_logs/` : Main Claude side 기록 (결정 과정, 검토 근거) — DEC_NNN ID 공유
- `session_reports/` : 해소된 DEC_NNN → `decisions_made` 필드에, 미해소 → `needs_confirmation` 필드에 기록
- `self_evolution/` : HF_NNN → SEV_NNN (feedback이 self-evolution으로 이어질 경우 cross-link 의무)

---

## Rules

1. **명시 승인 패턴** — "ㅇ", "D", "네", "OK", "A/B/C", "DEC_001: A" 형식만 유효한 승인으로 간주 (`12 §4`)
2. **민감 변경 explicit approval** — cleanup/force-push/MCP 설치/paper_context_ref 수정/settings 변경은 묵시 승인 금지 (`12 §4`)
3. **모호 응답 재질문** — 응답이 불명확하면 auto-default 금지, 재확인 필수 (`12 §4`)
4. **이전 세션 승인 미인계** — 각 세션에서 독립적으로 확인, 이전 세션 승인 재활용 금지 (`12 §4`)
5. **사용자 피드백 임의 해석 금지** — major claim, 연구 방향 변경은 명시 승인만 유효 (`12 §8 금지 3`)

---

## Cross-links

- Human feedback 프로토콜 전문: `docs/orchestration/12_HUMAN_FEEDBACK_AND_EVOLUTION_PROTOCOL.md`
- Decision logs: `docs/orchestration/decision_logs/INDEX.md`
- Self-evolution: `docs/orchestration/self_evolution/index.md`
