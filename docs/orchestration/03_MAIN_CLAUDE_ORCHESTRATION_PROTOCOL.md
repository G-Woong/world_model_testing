# 03_MAIN_CLAUDE_ORCHESTRATION_PROTOCOL.md

Main Claude 단일 오케스트레이션 프로토콜  
작성일: 2026-05-15  
작성자: Main Claude (Phase 2)  
근거: `docs/orchestration/PHASE1_GATE_REPORT.md`, `.claude/rules/codex_orchestration_rules.md`, `paper_context_ref/00_CONTEXT_INDEX.md`

---

## 1. Scope & Authority

**Main Claude는 이 프로젝트의 유일한 최종 오케스트레이터이다.**

| 권한 | 담당 |
|---|---|
| git commit / merge / push 최종 판단 | **Main Claude만** |
| Codex task 생성 / accept / reject / escalation | **Main Claude만** |
| Agent Team 호출 / synthesis / 결과 → Codex 변환 | **Main Claude만** |
| settings / hooks / agents / MCP 변경 승인 요청 | **Main Claude만** (변경은 human approval 필수) |
| Phase gate PASS / FAIL 판정 | **Main Claude만** |
| self-evolution proposal 생성 | **Main Claude만** (적용은 human approval 필수) |

Codex와 Agent Team은 Main Claude를 **경유하지 않고 서로 직접 연결되지 않는다.**

---

## 2. Required Source-of-Truth Read Order

FRCG-WM 관련 작업을 시작할 때 아래 순서로 읽는다.

```text
1. CLAUDE.md                              (절대 과학·데이터 규칙)
2. .claude/rules/research_context_rules.md  (용어·baseline·ablation 보존)
3. .claude/rules/codex_orchestration_rules.md  (Codex 위임 default)
4. paper_context_ref/00_CONTEXT_INDEX.md   (Phase Router + Context Bundle)
5. 작업 유형에 맞는 Context Bundle MD     (00_CONTEXT_INDEX.md §3 참조)
```

절대 규칙이 있는 파일(1~3번)을 읽지 않은 채 구현/설계/리뷰를 시작하지 않는다.

---

## 3. Task Intake Flow

```text
사용자 요청 수신
      ↓
(A) Phase 판정
    현재 실행 단계 확인 (P0~P8, paper_context_ref/00_CONTEXT_INDEX.md §2)
    Phase gate sentinel 존재 여부 확인 (outputs/phase_gates/*.passed)
      ↓
(B) Context Bundle 라우팅
    작업 유형 → 해당 MD 선택 (paper_context_ref/00_CONTEXT_INDEX.md §3)
      ↓
(C) 위임 판단
    직접 처리 케이스인가? (§7 참조)
    → YES: Main Claude가 직접 처리
    → NO:  Codex 위임 (§7 Codex 위임 매트릭스)
      ↓
(D) Agent Team 호출 필요 판단
    Fixed trigger T1~T6 해당하는가? (06_AGENT_TEAM_BLUEPRINT.md §3)
    → YES: Agent Team 호출 (compact 또는 deep mode)
    → NO:  discretionary 판단
      ↓
(E) 실행
    Codex task: 04_CODEX_FEEDBACK_LOOP_PROTOCOL.md §3 schema
    Agent Team: 06_AGENT_TEAM_BLUEPRINT.md §7 report 경로
      ↓
(F) 결과 수신 및 검증
    Codex: Gatekeeper 5조건 (codex_orchestration_rules.md §"Gatekeeper 정책")
    Agent: synthesis + 비판/해결책/검증법 3종 확인 (08_AGENT_OUTPUT_CONTRACTS.md §1)
      ↓
(G) Decision Log 기록 (§4 schema)
      ↓
(H) 사용자 출력 + human approval gate (필요 시)
```

---

## 4. Decision Log Schema

모든 주요 결정은 아래 schema로 기록한다. 저장 경로: `docs/orchestration/decision_logs/YYYY-MM/session_<id>.md`

```yaml
turn_id: <세션 내 순번>
timestamp: <ISO 8601>
decision_type: <TASK_ASSIGN | AGENT_CALL | ACCEPT | REJECT | ESCALATE | HUMAN_APPROVAL_REQUEST | PHASE_GATE | SELF_EVOLUTION_PROPOSE>
subject: <결정 대상 (task_id / agent_name / file / gate_name)>
evidence:
  - <근거 파일 또는 artifact>
risk: <HIGH | MED | LOW | INFO>
reasoning: <한 줄 근거>
approval: <AUTO | HUMAN_REQUIRED | HUMAN_APPROVED | HUMAN_DENIED>
outcome: <결과 한 줄>
```

---

## 5. Critical Gate vs Warning Gate 분류표

| 분류 | 조건 | 처리 |
|---|---|---|
| **CRITICAL GATE** | hidden label leakage 감지 | 즉시 중단, 사용자 보고, 해당 shard 무효화 |
| **CRITICAL GATE** | counterfactual leakage 감지 | 즉시 중단, 사용자 보고 |
| **CRITICAL GATE** | no-control-grammar ablation 무효 (non-effect) | 구현 중단, claim 검토 |
| **CRITICAL GATE** | no-falsification ablation 무효 | 구현 중단, claim 검토 |
| **CRITICAL GATE** | Codex가 forbidden_paths 수정 | 즉시 reject, self-evolution log 기록 |
| **CRITICAL GATE** | Phase gate sentinel 미존재 시 다음 Phase 시작 | 사용자 확인 없이 진행 불가 |
| **WARNING GATE** | Codex 2회 reject (동일 task) | 3회째 human escalation |
| **WARNING GATE** | Agent report에 해결책 없음 | report 실패 처리, 재호출 |
| **WARNING GATE** | R1/R2/R3 권한 위험 파일 수정 시도 | human approval 필수 |
| **WARNING GATE** | NeurIPS2026 경로 접근 시도 | 확인 후 차단 |

---

## 6. Human Approval Gate

아래 작업 유형은 **사용자 명시 승인 없이 실행하지 않는다.**

```text
- settings.json / settings.local.json 변경
- .mcp.json 변경
- .claude/hooks/ 파일 생성/수정/삭제
- .claude/agents/ 파일 생성/수정/삭제
- .claude/skills/ 파일 생성/수정/삭제
- CLAUDE.md 변경
- paper_context_ref/ 변경
- outputs/phase_gates/*.passed 생성/삭제
- git force push
- git reset --hard (tracked files)
- cleanup phase (DELETE 항목 실행)
- 새 MCP 서버 등록
- Codex worktree fast-forward
```

승인 요청 형식: `DECISIONS_REQUIRED` 섹션 (08_AGENT_OUTPUT_CONTRACTS.md §7 참조).

---

## 7. Codex 위임 결정 매트릭스

`codex_orchestration_rules.md` §"Codex 호출 트리거" 기반. 아래 중 **하나라도** 해당하면 Codex 위임을 default로 검토.

| 조건 | 예시 |
|---|---|
| (a) 3개 이상 파일 동시 수정 | 새 모듈 추가 + 테스트 + config |
| (b) 테스트 작성 + 구현 동반 | pytest 신규 케이스 + 구현 함수 |
| (c) 복잡 리팩터링 | 함수/클래스/모듈 재구조화 |
| (d) 데이터/평가/알고리즘 파이프라인 구현 | eval_runner, data_generator |
| (e) 버그 원인 분석 + 코드 수정 | test failure 근본 원인 fix |
| (f) Context 과부하 우려 | 대규모 sweep 후 구현 |

**Main Claude 직접 처리 케이스** (Codex 위임 없음):

```text
- 단일 파일 1~2줄 수정
- .claude/rules/, CLAUDE.md 갱신
- 문서 작성 (docs/, plans/)
- code review / diff 분석
- 이미 verify된 Codex 결과의 accept/abort 결정
- Phase gate 판정
- self-evolution proposal 작성
```

---

## 8. Agent Team 호출 결정 매트릭스

| 모드 | 호출 시점 | agent 수 | 출력 깊이 |
|---|---|---|---|
| **compact** | merge 전 quick risk scan, 단일 claim 확인 | 1~2개 | 1페이지 요약 |
| **deep** | 핵심 claim 변경 / 실험설계 변경 / 주요 결과 해석 | 3~5개 병렬 | 다층 synthesis |

Fixed Trigger 해당 시 호출 (06_AGENT_TEAM_BLUEPRINT.md §3):
- T1: 핵심 claim 변경 전
- T2: 실험설계 변경 전
- T3: 주요 Codex merge 전
- T4: 결과 해석 전
- T5: 논문 섹션 수정 전
- T6: reviewer-risk / novelty-risk 감지 시

Discretionary trigger: Main Claude 재량으로 비교적 자주 호출 가능.

---

## 9. Branch 전략 (NC-3 해결)

| Branch | 용도 | base commit |
|---|---|---|
| `orchestration/redesign` | Phase 2 오케스트레이션 문서 작업 | `ba204a8` (solo/p3-final-boss-cleared) |
| `solo/p3-final-boss-cleared` | 현재 research 작업 기준 | — |
| `codex-work` | Codex 구현 작업 (현재 단일 branch) | `a55cb33` |
| `codex/TASK_XXXX_short-name` | 향후 task별 Codex branch (단계적 전환 — 04 §2 참조) | — |

**주의**: `orchestration/redesign` branch 신설 및 `codex-work` 구조 변경은 human approval 후 실행.

---

## 10. Codex Worktree Fast-forward Gate 절차 (NC-4 해결)

다음 Codex task 시작 전 Main Claude가 수행하는 체크리스트. 실제 fast-forward는 사용자 승인 후만.

```text
Step 1. Main HEAD 확인
        git -C <main_worktree> log --oneline -3

Step 2. Codex HEAD 확인
        git -C <codex_worktree> log --oneline -3

Step 3. diff stat 확인
        git -C <codex_worktree> log HEAD...<main_HEAD> --oneline

Step 4. 빠진 commit 중 forbidden_paths 변경 없음 확인
        git -C <codex_worktree> diff HEAD <main_HEAD> -- .claude/ CLAUDE.md .mcp.json

Step 5. 결과를 DECISIONS_REQUIRED에 기록 → 사용자 fast-forward 승인 요청

Step 6. 사용자 승인 후: git -C <codex_worktree> merge --ff-only <main_HEAD>
```

---

## 11. Phase 1 NEEDS_CONFIRMATION 처리 매트릭스

| ID | 항목 | 처리 단계 | 상태 |
|---|---|---|---|
| NC-1 | `plans/P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md` 처리 | Phase 2 cleanup carry-forward (실행 없이 분류만) | CARRY_FORWARD → Phase 4 |
| NC-2 | `origin/feat/p1-schema-visibility` 폐기 여부 | Phase 4+ cleanup phase | CARRY_FORWARD |
| NC-3 | Phase 2 branch 전략 | **본 문서 §9에서 해결** (`orchestration/redesign` 신설 제안) | RESOLVED_IN_PLAN |
| NC-4 | Codex fast-forward 시점 | **본 문서 §10에서 해결** (절차 명시, 실행은 Phase 3) | RESOLVED_IN_PLAN |
| NC-5 | checkpoint LFS 처리 | Phase 4+ cleanup phase | CARRY_FORWARD |
| NC-6 | `session_start_context.ps1` 등록 | Phase 3 hooks 수정 PR과 함께 | CARRY_FORWARD → Phase 3 |
| NC-7 | 빈 placeholder 디렉터리 3개 | Phase 4 산출물 도착 후 결정 | CARRY_FORWARD |

---

## 12. 금지 행동 목록 (Main Claude조차 못 하는 것)

```text
- human approval 없이 settings.json / settings.local.json 수정
- human approval 없이 CLAUDE.md 수정
- human approval 없이 paper_context_ref/ 수정
- human approval 없이 .mcp.json 수정
- human approval 없이 .claude/agents/ / .claude/hooks/ / .claude/skills/ 수정
- human approval 없이 git force push
- human approval 없이 Phase gate sentinel 삭제
- 실험 결과 수치를 artifact 없이 직접 작성
- hidden label / counterfactual field를 inference input으로 사용하는 코드 작성
- no-control-grammar / no-falsification ablation 코드 삭제 또는 비활성화
- Codex와 Agent Team을 직접 연결
- Agent Team report를 검증 없이 Codex task로 자동 변환
- self-evolution proposal을 human approval 없이 settings에 직접 반영
```

---

## 13. 비상 중단 조건

아래 상황 발생 시 즉시 작업 중단 후 사용자에게 보고:

```text
- CRITICAL GATE 발동 (§5 참조)
- Codex RESULT.md에 rejection 누락
- Agent report에 해결책 없이 비판만 존재
- forbidden inference field가 model input에 등장
- git diff에 paper_context_ref/ 변경 감지
- CLAUDE.md 내 baseline/ablation 삭제 시도 감지
```
