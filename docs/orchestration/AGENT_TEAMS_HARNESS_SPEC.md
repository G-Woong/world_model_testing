# AGENT_TEAMS_HARNESS_SPEC.md

Agent Teams Harness 전체 명세  
작성일: 2026-05-17  
작성자: Main Claude  
근거: `docs/orchestration/06_AGENT_TEAM_BLUEPRINT.md`, `07_RESEARCH_CRITIC_AGENTS.md`,
`13_MASTER_ORCHESTRATION_PLAN.md §8`, `CLAUDE.md §Agent Teams Operating Protocol`

---

## 1. 개요

이 문서는 FRCG-WM 프로젝트의 Agent Teams Harness 전체 명세를 담는다.

- **공식 활성화**: `.claude/settings.json env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- **자체 Blueprint**: `docs/orchestration/06_AGENT_TEAM_BLUEPRINT.md` (Task tool 기반 fallback 포함)
- **17개 sub-agent**: `.claude/agents/` (7개 frcgw-* + 10개 critic agent)
- **3개 호출 명령**: `/war-room`, `/agent-team-review`, `/codex-result-audit`

새 세션은 이 파일 1개만 읽으면 전체 구조를 파악할 수 있어야 한다.

---

## 2. 활성화 조건

| 조건 | 파일 | 상태 |
|---|---|---|
| 공식 env flag | `.claude/settings.json` `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | `1` 설정 완료 |
| Blueprint SSoT | `docs/orchestration/06_AGENT_TEAM_BLUEPRINT.md` | 13개 §, T1~T6 trigger 정의 |
| Critic agent 정의 | `.claude/agents/*.md` (17개) | frontmatter T1~T6 trigger 명시 |
| 메인 contract 등재 | `CLAUDE.md §Agent Teams Operating Protocol` | trigger 표 + 4중 금지 + 경로 |
| Codex routing 강제 | `.claude/rules/codex_orchestration_rules.md §Gatekeeper` | 6번째 조건 T3 |

**재시작 필수**: 세션 종료 후 새 Claude Code 세션에서 `SendMessage` / `TeamCreate` 도구가 tool list에 등장하면 공식 활성화 확인.

---

## 3. Fixed Triggers (T1~T6)

상세: `docs/orchestration/06_AGENT_TEAM_BLUEPRINT.md §3`

| Trigger | 이벤트 | 모드 | 권장 agent |
|---|---|---|---|
| T1 | 핵심 claim 변경 전 | deep | mathematical-validity-critic + novelty-threat-scout + claim-metric-alignment-auditor |
| T2 | 실험설계 변경 전 | deep | experiment-design-expander + feasibility-and-cost-auditor + failure-interpretation-critic |
| T3 | 주요 Codex merge 전 | compact | implementation-risk-critic + frcgw-code-reviewer |
| T4 | 결과 해석 전 | deep | failure-interpretation-critic + area-chair-synthesis-agent + claim-metric-alignment-auditor |
| T5 | 논문 섹션 수정 전 | deep | reviewer-2-attack-agent + novelty-threat-scout + related-work-mcp-scout |
| T6 | reviewer-risk / novelty-risk 감지 | compact→deep | reviewer-2-attack-agent |

---

## 4. 팀 구성 및 역할

| 역할 | 담당 agent | 산출물 | 권한 |
|---|---|---|---|
| Main Orchestrator | Main Claude 본인 | synthesis report, action items, Codex TASK 변환 | read/edit (fragile file은 사용자 승인 필수) |
| Research Scout | novelty-threat-scout + related-work-mcp-scout + frcgw-related-work-scout | 관련 논문, 위협, 인용 후보 (2 출처 cross-check) | read-only + WebFetch/WebSearch/arXiv/SS MCP |
| Code Auditor | frcgw-code-reviewer + frcgw-data-leakage-auditor | diff 분석, leakage 위험 | read-only |
| Test Analyst | frcgw-test-runner + frcgw-experiment-evaluator | pytest 결과, metric validity | Bash(pytest) + read |
| Risk Critic | reviewer-2-attack-agent + implementation-risk-critic + mathematical-validity-critic | severity별 risk table | read-only |
| Codex Liaison | implementation-risk-critic (T3 특화) + frcgw-code-reviewer | Codex diff 분석, merge 가능성 판정 | read-only |
| Synthesis Writer | area-chair-synthesis-agent | reviewer 충돌 정리, 최종 acceptability 판단 | read-only md report만 |

---

## 5. 권한 모델

### Main Orchestrator

- Read/Search: 무제한
- Edit/Write: 가능. fragile file 5종은 사용자 승인 + 테스트 재실행 필수
  - `src/frcgw/schemas/visibility.py`
  - `paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md`
  - `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md`
  - `.claude/settings.json`
  - `scripts/run_codex_task.ps1`
- git push, destructive delete, archive 이동: **금지**
- Codex worktree merge: Gatekeeper 6조건 모두 PASS 후에만

### Teammate (4중 금지)

```
금지 1: 코드 직접 편집 (Edit/Write 사용 불가)
금지 2: git commit / merge / push
금지 3: settings / hooks / agents / skills / MCP 수정
금지 4: Codex task 직접 생성 또는 할당
```

위반 시: SubagentStop hook이 WARN 발신. Main Claude가 수동 차단.

---

## 6. Report 경로 및 포맷

```text
개별 agent report:
  docs/orchestration/agent_reports/YYYY-MM/<agent_name>_<topic>_<id>.md

synthesis report (deep mode):
  docs/orchestration/agent_reports/synthesis/YYYY-MM/<topic>_<id>.md

T3 audit report:
  docs/orchestration/agent_reports/YYYY-MM/impl_risk_<TASK>_R<n>.md
```

모든 report 필수 포함: **비판 + 해결책 + 검증법 3종**. 미포함 시 report 실패 처리.

---

## 7. Codex ↔ Agent Team Routing 원칙

- Codex ↔ Agent Team 직접 연결 **금지**
- 모든 비판은 Main Claude 경유 필수
- Codex TASK 생성 권한은 Main Claude만 보유 (agent에게 위임 금지)
- T3 trigger: 주요 Codex merge 전 impl-risk-critic 호출 → `/codex-result-audit` 실행

근거: `docs/orchestration/04_CODEX_FEEDBACK_LOOP_PROTOCOL.md §12`

---

## 8. 호출 명령

| 명령 | 용도 | 모드 |
|---|---|---|
| `/war-room` | Deep mode 전체 비판 위원회 (7 critic) | deep |
| `/agent-team-review` | Compact/deep 선택형 다용도 review | compact(default)/deep |
| `/codex-result-audit` | Codex merge 전 T3 audit (Gatekeeper 6조건) | compact |

---

## 9. Failure Modes 및 대응

| 실패 유형 | 증상 | 대응 |
|---|---|---|
| 공식 Agent Teams 비활성 | SendMessage 도구 미등장 | 플랜 자격 확인 → fallback: Task tool 기반 Blueprint |
| Report 품질 미달 | 해결책 없이 비판만 있음 | Main Claude가 해결책 추가 요청 (실패 처리) |
| Citation 부족 | 외부 논문 인용 1건 이하 | 2개 이상 출처 교차검증 요청 |
| SS 429 error | Semantic Scholar rate limit | 즉시 중단 + 60초 cool-down + 1회 재시도 |
| T3 FAIL | Gatekeeper 6번째 조건 미충족 | `git merge --abort` + blocker 목록 출력 |
| Teammate 금지 위반 | SubagentStop WARN | Main Claude 수동 차단 + report 무효화 |

---

## 10. Validation Checklist (V1~V14)

계획 문서에서 정의된 14개 검증 항목 참조: `docs/orchestration/AGENT_TEAMS_ROLLOUT_PLAN.md §Validation`

핵심 항목:
- V1/V2: settings.json JSON valid + env 키 = "1"
- V5: SendMessage tool 노출 (재시작 후)
- V6: CLAUDE.md에 "T1~T6" 등재 5건 이상
- V7: 3개 command 파일 존재
- V8: codex_orchestration_rules.md에 impl-risk-critic 언급
- V9: Dummy team audit 4 report 생성 + 어떤 teammate도 Edit 미사용
- V11: R1 흔적 7건 + synthesis 1건 mtime 변경 없음
- V12: R2 Lock(enableAllProjectMcpServers=false) 보존
- V13: pytest test_forbidden_field_mirror_sync green

---

## 11. 후속 작업 (이 harness 범위 외)

- `TeammateIdle`, `TaskCompleted` hook 등록 (D4 LIKELY 영향 LOW)
- `frcgw-phase-gate/SKILL.md` 응답 포맷에 "Agent reports consulted" 필드 (B3)
- War Room R2 가동 (LR alignment + BASE-026/027/028 미구현 검토)
- `outputs/review_reports/` REVIEW_LATER 정리 (Phase 4+ cleanup)
