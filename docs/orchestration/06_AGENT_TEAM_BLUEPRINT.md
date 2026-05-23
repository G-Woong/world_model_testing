# 06_AGENT_TEAM_BLUEPRINT.md

Agent Team 운영 Blueprint  
작성일: 2026-05-15  
작성자: Main Claude (Phase 2)  
근거: `docs/orchestration/01_PERMISSION_SCOPE_AUDIT.md` §8, `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md`, `paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md`

---

## 1. Purpose

Agent Team은 ICLR 2026 수준 연구 운영을 위한 **사전 비판 위원회**이다.

- Reviewer #2 관점: 논문을 가장 공격적으로 비판하는 리뷰어 시각
- Area Chair 관점: reviewer 의견 충돌을 정리하고 최종 acceptability를 판단
- 모든 비판은 해결책 + 검증법을 반드시 동반

주요 목적:
- Main Claude 및 Codex 결과물의 독립적 검증
- FRCG-WM scientific contract(baseline/ablation/용어/leakage) 보존 감시
- 외부 위협(WebWorld/CUWM/WAC/VeriGUI) 대비 novelty 방어
- 수학적 정의/가정/loss/identifiability 검증

---

## 2. Read-only Principle (4중 금지)

Agent Team의 어떤 agent도 아래 행동을 하지 않는다.

```text
금지 1: 코드 직접 편집 (Edit/Write 사용 불가)
금지 2: git commit / merge / push
금지 3: settings / hooks / agents / skills / MCP 수정
금지 4: Codex task 직접 생성 또는 할당
```

Agent Team은 **md report만 작성**한다.  
report → Main Claude → 검증/synthesis → Codex task 변환.

---

## 3. Fixed Triggers (T1~T6)

아래 이벤트 발생 시 Main Claude는 Agent Team 호출을 **기본으로 검토**한다.

| 트리거 | 이벤트 | 권장 모드 | 권장 agent |
|---|---|---|---|
| T1 | 핵심 claim 변경 전 | deep | mathematical-validity-critic + novelty-threat-scout + claim-metric-alignment-auditor |
| T2 | 실험설계 변경 전 | deep | experiment-design-expander + feasibility-and-cost-auditor + failure-interpretation-critic |
| T3 | 주요 Codex merge 전 | compact | implementation-risk-critic + frcgw-code-reviewer |
| T4 | 결과 해석 전 | deep | failure-interpretation-critic + area-chair-synthesis-agent + claim-metric-alignment-auditor |
| T5 | 논문 섹션 수정 전 | deep | reviewer-2-attack-agent + novelty-threat-scout + related-work-mcp-scout |
| T6 | reviewer-risk / novelty-risk 감지 시 | compact → deep 전환 | reviewer-2-attack-agent |

---

## 4. Claude Discretionary Trigger

고정 트리거 외에도 Main Claude 재량으로 비교적 자유롭게 호출 가능.

권장 호출 상황 (예시):
```text
- Codex 구현 시작 전 scope 확인 (compact, implementation-risk-critic)
- 실험 설정 파일 검토 (compact, feasibility-and-cost-auditor)
- 논문 related work 작성 중 새 threat 발견 (novelty-threat-scout)
- ablation 결과 해석 불확실 시 (failure-interpretation-critic)
```

---

## 5. Compact Mode

| 항목 | 내용 |
|---|---|
| agent 수 | 1~2개 |
| 사용 시점 | merge 전 quick risk scan, 단일 claim 확인, scope 검토 |
| report 깊이 | 1페이지 요약 (핵심 위험 + 해결책 + 검증법) |
| 소요 토큰 | 보통 |

Compact mode에서도 비판 + 해결책 + 검증법 3종은 필수.

---

## 6. Deep Mode

| 항목 | 내용 |
|---|---|
| agent 수 | 3~5개 병렬 |
| 사용 시점 | 핵심 claim/실험설계 변경, 주요 결과 해석, 논문 수정 |
| report 깊이 | 다층 synthesis (개별 agent report + Main Claude synthesis) |
| 소요 토큰 | 높음 |

Deep mode에서는 Main Claude가 synthesis report 별도 작성 (§9 참조).

---

## 7. Report 경로 (C-1 해결)

```text
개별 agent report:
  docs/orchestration/agent_reports/YYYY-MM/<agent_name>_<topic>_<id>.md

synthesis report:
  docs/orchestration/agent_reports/synthesis/YYYY-MM/<topic>_<id>.md
```

경로 명명 규칙:
```text
<agent_name>: mathematical-validity-critic, experiment-design-expander, ... (07 §각 항목 참조)
<topic>: 작업 대상 요약 (예: p4-env-schema, claim-falsification-gate)
<id>: 날짜 기반 또는 task_id 연동 (예: 20260515-001, TASK_1021)
```

---

## 8. outputs/review_reports/와의 관계

현재 `outputs/review_reports/`는 Phase 1 cleanup 분류에서 **REVIEW_LATER** 상태.

처리 방침:
- 즉시 삭제 금지 — Phase 4+ cleanup phase에서 결정
- 향후 신규 agent report는 모두 `docs/orchestration/agent_reports/`에 작성
- `outputs/review_reports/`의 기존 내용은 아카이브 후보로 유지

---

## 9. Main Claude Synthesis Report

Deep mode 완료 후 Main Claude가 작성하는 통합 보고서.

경로: `docs/orchestration/agent_reports/synthesis/YYYY-MM/<topic>_<id>.md`

포함 내용:
```text
1. 호출된 agent 목록 및 각 report 경로
2. 공통적으로 제기된 위험 (우선순위 순)
3. 상충하는 의견 및 Main Claude의 판단
4. 최종 action items (Codex task 변환 대상 / human approval 필요 항목 / 보류 항목)
5. Phase gate 영향 여부
```

---

## 10. Agent → Main Claude → Codex Task 변환 절차

```text
1. Agent report 수신
2. Main Claude가 report 검증:
   - 비판 + 해결책 + 검증법 3종 포함 여부 확인
   - citation 2개 이상 출처 확인
   - forbidden field / forbidden path 언급 시 문맥 확인
3. 통과 시: synthesis report 작성 (deep mode) 또는 직접 action items 도출 (compact mode)
4. action items 중 구현이 필요한 항목 → Codex TASK 파일 생성 (04 §3 schema)
5. 구현 불필요하고 human approval 필요한 항목 → DECISIONS_REQUIRED 섹션으로 사용자 전달
```

---

## 11. Reviewer #2 + AC Critic 강도 기준

Agent Team은 아래 기준으로 비판 강도를 설정한다.

| 강도 | 적용 상황 | 예시 |
|---|---|---|
| **Level 3 (가장 공격적)** | claim이 acceptance-level evidence 없이 제출될 위험 | "falsification mechanism이 simple anomaly detection과 구분되지 않는다" |
| **Level 2 (표준)** | baseline/ablation 보완 필요 | "no-control-grammar ablation이 효과 없으면 핵심 claim 무효화" |
| **Level 1 (점검)** | 구현/인프라 risk | "eval_runner에 forbidden field가 입력으로 들어갈 위험 있음" |

모든 level에서 **해결책 없이 비판만 하면 report 실패 처리.**

---

## 12. 비용/토큰 관리

| 선택 기준 | compact | deep |
|---|---|---|
| 의사결정에 미치는 영향 | 낮음~중간 | 높음 (claim / 실험설계 / 논문 수정) |
| 긴급도 | 높음 (merge 직전) | 낮음 (계획 단계) |
| 작업 불확실성 | 낮음 | 높음 |

Deep mode는 T1/T2/T4/T5 fixed trigger에 한해 기본 사용. T3/T6는 compact로 시작 후 필요 시 deep 전환.

---

## 13. Citation Cross-check

외부 논문 인용 시 규칙:

```text
- 최소 2개 출처 교차 검증 (예: arXiv + Semantic Scholar + 직접 PDF)
- 인용 내용이 "비판을 강화"하는 방향과 "방어"하는 방향 양쪽 포함
- related-work-mcp-scout agent가 담당 (07 §9 참조)
- 인용 URL/DOI를 report frontmatter에 기록
- 2025/2026년 신규 논문 위협 여부 주기적 확인
```
