# 18_orchestration_slimming_and_trash_policy_plan.md

## Purpose

`docs/orchestration/` 슬림화 + 자동 lifecycle/trash 정책 편입.

사용자 강조 요구: docs/orchestration/ 자체가 cleanup 대상.  
5개 PLAN 문서 추가로 19→24 파일 증가를 일시적으로 허용하되,  
lifecycle automation v2 Phase F/G 첫 sweep의 **1순위 타겟**이 이 폴더 슬림화여야 한다.

생성일: 2026-05-17  
Branch: memory-redesign-2026-05-16  
Status: ACTIVE_POLICY  
Phase: pre-implementation (설계만, 코드 수정 0)

---

## §1. Current Orchestration Audit

### Top-level 파일 (19개, PLAN 문서 추가 전)

| 번호 | 파일 | 분류 |
|---|---|---|
| 00_CURRENT_STATE_INVENTORY.md | 현황 | ACTIVE_POLICY |
| 01_PERMISSION_SCOPE_AUDIT.md | 감사 | ACTIVE_POLICY |
| 02_CLEANUP_CANDIDATES.md | cleanup | ACTIVE_POLICY |
| 03_MAIN_CLAUDE_ORCHESTRATION_PROTOCOL.md | 프로토콜 | ACTIVE_POLICY |
| 04_CODEX_FEEDBACK_LOOP_PROTOCOL.md | 프로토콜 | ACTIVE_POLICY |
| 05_SELF_EVOLVING_LOOP.md | 정책 | ACTIVE_POLICY |
| 06_AGENT_TEAM_BLUEPRINT.md | 설계 | ACTIVE_POLICY |
| 07_RESEARCH_CRITIC_AGENTS.md | 설계 | ACTIVE_POLICY |
| 08_AGENT_OUTPUT_CONTRACTS.md | contract | ACTIVE_POLICY |
| 09_MCP_RESEARCH_STACK.md | 정책 | ACTIVE_POLICY |
| 10_MCP_SECURITY_POLICY.md | 정책 | ACTIVE_POLICY |
| 11_SESSION_END_REPORT_PROTOCOL.md | 프로토콜 | ACTIVE_POLICY |
| 12_HUMAN_FEEDBACK_AND_EVOLUTION_PROTOCOL.md | 프로토콜 | ACTIVE_POLICY |
| 13_MASTER_ORCHESTRATION_PLAN.md | master plan | ACTIVE_POLICY |
| 14_REPORT_LIFECYCLE_POLICY.md | 정책 SSoT | ACTIVE_POLICY |
| PHASE1_GATE_REPORT.md | gate report | HISTORICAL_REPORT |
| PHASE2_GATE_REPORT.md | gate report | HISTORICAL_REPORT |
| PHASE3_GATE_REPORT.md | gate report | HISTORICAL_REPORT |
| PHASE3B_GATE_REPORT.md | gate report | CURRENT_RUN_REPORT |

### Subdirs

| 디렉토리 | 파일 수 | 비고 |
|---|---|---|
| `agent_reports/2026-05/` | 7 | agent 분석 보고서 |
| `decision_logs/2026-05/` | 6 | 결정 기록 |
| `human_feedback/2026-05/` | 3 | 피드백 |
| `lr_alignment/` | 18 + evidence_cards 6 | P3 lr eval 연구 |
| `mcp_research/2026-05/` | 5 | MCP 연구 |
| `self_evolution/2026-05/` | 1 | 진화 사이클 |
| `session_reports/2026-05/` | 16 | 세션 보고서 |
| `archive/` | 0 | `.gitkeep`만 |
| `codex_reports/` | 0 | `.gitkeep`만 |

---

## §2. Classification Taxonomy (10 카테고리)

| 카테고리 | 정의 | 자동화 허용 |
|---|---|---|
| ACTIVE_POLICY | 00..14 + 15..19 정책 SSoT | 절대 이동 금지 |
| ACTIVE_EVIDENCE | lr_alignment/evidence_cards/, run6 report, claim survivability | 절대 이동 금지 |
| CURRENT_RUN_REPORT | Run 4/5/6 reports (가장 최신) | 절대 이동 금지 |
| HISTORICAL_REPORT | Run 4 이전, PHASE1/2/3 gate | manual-only (archive 가능) |
| SESSION_LOG | session_reports/YYYY-MM/ | manual-only (archive 가능) |
| DECISION_LOG | decision_logs/YYYY-MM/ | manual-only (archive 가능) |
| AGENT_REPORT | agent_reports/YYYY-MM/ | auto-safe 후보 (중복 제거) |
| ARCHIVE_READY | superseded handoff, duplicate | auto-safe (trash/archive) |
| MANUAL_ONLY | negative evidence, gate sentinel source | 삭제 금지, archive만 허용 |
| DO_NOT_TOUCH | paper_context_ref, evidence_cards, phase gate sentinels | 하드 블록 |

---

## §3. Slimming Rules

### 유지 (절대 이동/삭제 금지)

```
docs/orchestration/00_*.md .. 14_*.md    ← 정책 SSoT 전체
docs/orchestration/15_*.md .. 19_*.md   ← 이번 PLAN 문서 (ACTIVE_POLICY)
docs/orchestration/lr_alignment/evidence_cards/**
docs/orchestration/lr_alignment/12_run6_lr_eval_report.md
docs/orchestration/lr_alignment/13_claim_survivability_decision_report.md
docs/orchestration/PHASE3B_GATE_REPORT.md  ← 가장 최신 gate report
```

### archive 후보 (manual-only, 사용자 승인 후)

```
docs/orchestration/PHASE1_GATE_REPORT.md   ← superseded by PHASE3B
docs/orchestration/PHASE2_GATE_REPORT.md   ← superseded by PHASE3B
docs/orchestration/PHASE3_GATE_REPORT.md   ← superseded by PHASE3B
docs/orchestration/session_reports/2026-05/  ← 일부 superseded handoff
docs/orchestration/decision_logs/2026-05/   ← 일부 old decision
```

### auto-safe 후보 (lifecycle automation 자동 처리)

```
docs/orchestration/agent_reports/2026-05/   ← 중복 agent 분석 제거
docs/orchestration/self_evolution/2026-05/  ← .self_evolving_memory/로 이관 후
docs/orchestration/mcp_research/2026-05/    ← 중복 query log 제거
```

### negative evidence (삭제 절대 금지)

- failed attempt report → `.self_evolving_memory/`에 요약 후 original은 archive
- negative ablation result → `MANUAL_ONLY`로 영구 보존
- anti-pattern evidence → `.self_evolving_memory/patterns/anti_patterns.md`에 요약

---

## §4. Integration with Lifecycle Automation

`stop_lifecycle_automation.ps1`이 Stop event에서 orchestration audit 수행:

```
1. 새 report 생성 감지
   → outputs/lifecycle/orchestration_registry.json에 등록
   → artifact_type, created_at, classification 기록

2. 동일 artifact_type 이전 report 감지
   → status: superseded 표시
   → current만 ACTIVE, 이전은 ARCHIVE_READY or MANUAL_ONLY

3. 이동 결정 (dry-run default)
   → archive: plans/archive/ 또는 docs/orchestration/archive/
   → trash: .lifecycle_trash/
   → 삭제: 절대 금지

4. manifest 생성
   → outputs/lifecycle/latest_orchestration_audit.md
   → 사용자 검토 후 apply 결정
```

---

## §5. Output Contract (자동 생성)

lifecycle automation이 매 Stop event 후 생성하는 파일:

| 파일 | 내용 |
|---|---|
| `outputs/lifecycle/latest_orchestration_audit.md` | 전체 분류 결과 |
| `outputs/lifecycle/archive_ready.md` | archive 후보 목록 |
| `outputs/lifecycle/manual_only.md` | 사용자 승인 필요 목록 |
| `outputs/lifecycle/protected_core.md` | 보호된 파일 목록 |
| `outputs/lifecycle/orchestration_registry.json` | machine-readable registry |

---

## §6. User View

사용자가 봐야 하는 파일 4개만:

```
.self_evolving_memory/index.yaml              ← 전체 상태 요약
outputs/lifecycle/latest_orchestration_audit.md  ← 이번 sweep 결과
plans/PHASE_PROGRESS.md                       ← 현재 phase 진행 상황
docs/orchestration/lr_alignment/12_run6_lr_eval_report.md  ← 현재 run report
```

---

## §7. 슬림화 목표 (Phase F/G 첫 sweep 후)

| 항목 | 현재 | 목표 |
|---|---|---|
| top-level .md | 24 (PLAN 추가 후) | 20 이하 (PLAN 문서 포함) |
| session_reports/2026-05/ | 16개 | 5개 (최신 + milestone만) |
| decision_logs/2026-05/ | 6개 | 3개 (active decision만) |
| agent_reports/2026-05/ | 7개 | 3개 (최신 per claim) |

---

## §8. Cross-reference

- `docs/orchestration/14_REPORT_LIFECYCLE_POLICY.md` — 기존 lifecycle policy SSoT
- `docs/orchestration/15_lifecycle_automation_v2_plan.md` — lifecycle automation 설계
- `docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md` — master plan
- `CLAUDE.md §Non-Negotiable Data Rules` — negative evidence 보존 의무
