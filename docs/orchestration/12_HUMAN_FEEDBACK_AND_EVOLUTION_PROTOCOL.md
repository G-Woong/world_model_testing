# 12_HUMAN_FEEDBACK_AND_EVOLUTION_PROTOCOL.md

Human Feedback 및 Self-Evolution 연결 프로토콜  
작성일: 2026-05-15  
작성자: Main Claude (Phase 3B)  
근거: `docs/orchestration/05_SELF_EVOLVING_LOOP.md §3/§8`, `docs/orchestration/03_MAIN_CLAUDE_ORCHESTRATION_PROTOCOL.md §4/§6`, `docs/orchestration/08_AGENT_OUTPUT_CONTRACTS.md §7`, `docs/orchestration/11_SESSION_END_REPORT_PROTOCOL.md`

---

## 1. 목적

사용자가 PI/reviewer로서 판단하고, Main Claude가 그 피드백을 self-evolving loop로 흘려보내는 절차를 정의한다.

```text
Main Claude 판단 보정       → 연구 방향 오류 조기 수정
연구 방향 확정              → DECISIONS_REQUIRED 해소
cleanup 승인                → 삭제/아카이브 전 human gate
permission 변경 승인        → settings/hooks/MCP 변경 전 human gate
Agent Team critic 결과 인간 판단 → FATAL_FLAW / REJECT escalation 처리
Codex rejection escalation  → 3회 reject 후 human 결정
paper claim 변경 승인       → major claim 수정 전 human gate
```

---

## 2. Human Feedback 필요 조건 (9 트리거)

다음 중 하나라도 해당하면 사용자 결정/승인이 필요하다.

```text
트리거 1: settings / hook / agent / MCP 변경 요청
트리거 2: cleanup 실행 (delete / archive / move / merge)
트리거 3: paper_context_ref/ 수정
트리거 4: major claim 변경 (핵심 claim 텍스트 수정)
트리거 5: experiment design 변경 (ablation 추가/제거, split 변경)
트리거 6: Codex 3회 reject (04 §9 escalation)
트리거 7: Agent Team FATAL_FLAW / REJECT 판정 (07 §5 escalation_condition)
트리거 8: MCP threat HIGH (10 §1 T-MCP-01~08 중 HIGH 트리거)
트리거 9: phase gate PASS/FAIL 모호 (PARTIAL 판정 또는 blocker 불명확)
```

위 조건 없이 진행하려는 경우 → 즉시 중단 + 사용자 보고.

---

## 3. DECISIONS_REQUIRED 표준 형식

`05_SELF_EVOLVING_LOOP.md §8`을 인용하되 lifecycle 필드를 확장한다.

```markdown
## DECISIONS_REQUIRED

다음 항목에 대해 결정이 필요합니다. 결정되지 않은 항목은 작업을 계속하지 않습니다.

| ID | 항목 | 옵션 A | 옵션 B | 옵션 C | 권장 | 배경 | default_if_no_answer | deadline_or_phase_impact |
|---|---|---|---|---|---|---|---|---|
| DEC_YYYY-MM_NNN | <항목> | <A> | <B> | <C (없으면 —)> | <A/B/C> | <배경 한 줄> | <deadline 없을 시 default> | <Phase 4 진입 전 결정 필요 등> |
```

lifecycle 필드 (DECISIONS_REQUIRED 해소 추적):

```yaml
decision_id: DEC_YYYY-MM_NNN
issue: <무엇을 결정해야 하는가>
context: <결정 배경 (paper_context_ref 또는 문서 경로 인용)>
option_A: <A 설명>
option_B: <B 설명>
option_C: <C 설명 (없으면 none)>
recommended: <A | B | C>
risk: <권장안의 risk>
consequence: <결정에 따른 영향>
default_if_no_answer: <명시적 응답 없을 때 default (단, 민감 변경은 default 없음)>
deadline_or_phase_impact: <결정 안 하면 어떤 Phase 작업이 막히는가>
status: <OPEN | RESOLVED | EXPIRED>
resolution: <결정 내용 (RESOLVED 시)>
resolved_by_session_id: <해소한 세션 ID>
```

---

## 4. 사용자 응답 처리 규칙

```text
명시적 승인 패턴:
  "ㅇ", "D", "네", "권장", "OK", "A", "B", "C" → 권장안 또는 해당 옵션 승인으로 간주
  "DEC_001: A" 형식 → 해당 decision ID에 대한 명확한 응답

불명확한 응답 처리:
  응답이 모호한 경우 → 재질문 (auto-default 금지)
  예: "좋아요" → "DEC_001 항목에 대해 A안을 선택하신 건가요?" 재확인

민감 변경 — 명시 승인 절대 필수 (묵시 승인 금지):
  1. cleanup (파일 삭제/아카이브/이동)
  2. force push / reset --hard / branch 삭제
  3. MCP 설치/활성화
  4. paper_context_ref/ 수정
  5. settings/hooks 변경
  6. Agent Team FATAL_FLAW 후 연구 방향 전환
  7. Codex task 취소 또는 rollback

이전 세션의 승인은 이번 세션에 인계되지 않는다.
각 세션에서 독립적으로 확인한다.
```

---

## 5. Human Feedback → Self-Evolution 반영 절차

`05_SELF_EVOLVING_LOOP.md §3` 9-step procedure와 직접 매핑한다.  
본 문서는 **bridge 역할**만 한다. 9-step 세부 절차는 `05 §3`을 따른다.

```text
Step 1. feedback received (사용자 응답 수신)
        → DECISIONS_REQUIRED 해소 or 새 방향 지시 확인

Step 2. affected protocol identified (영향 받는 운영 프로토콜 확인)
        → docs/orchestration/03~12 중 어느 문서가 영향받는가

Step 3. proposal generated (개선안 작성)
        → 05 §4 schema로 SEV_YYYY-MM_NNN 생성

Step 4. risk assessed (위험 평가)
        → FRCG-WM scientific contract 영향 여부 확인
        → rollback 방법 명확화

Step 5. adoption/rejection recorded
        → ADOPTED: index.md 갱신 + branch 명시
        → REJECTED: 이유 + 재검토 조건 기록

Step 6. index updated
        → self_evolution/index.md 갱신

Step 7. next prompt/task에 반영
        → 다음 세션 시작 시 session report에 SEV 상태 기록
```

---

## 6. Escalation Policy (6 트리거)

다음 상황에서 Main Claude는 작업을 즉시 중단하고 사용자에게 escalation report를 제출한다.

```text
ESC-1: Codex 3회 reject
       → 04 §9 escalation → Human escalation report 제출
       → 사용자 결정: task 수정 / task 폐기 / Main Claude 직접 처리

ESC-2: Agent Team FATAL_FLAW 판정
       → 07 §5 escalation_condition → 논문 방향 재검토 제안
       → 사용자 결정: 연구 방향 수정 / 방어 실험 추가 / 논문 scope 변경

ESC-3: Novelty COMPROMISED (novelty-threat-scout HIGH)
       → 07 §3 escalation → 직접 경쟁 논문 발견 사용자 보고
       → 사용자 결정: claim 차별화 / scope 수정 / 추가 실험

ESC-4: Permission/Security 충돌
       → 10 §1 HIGH threat → 즉시 중단 + 격리
       → 사용자 결정: MCP 비활성화 / revert / 조사 계속

ESC-5: Experimental evidence가 paper claim과 모순
       → failure-interpretation-critic INVALIDATED → 즉시 보고
       → 사용자 결정: claim 수정 / 추가 실험 / 논문 scope 축소

ESC-6: User disagreement with Main Claude recommendation
       → DEC_NNN에서 사용자가 권장안과 다른 옵션 선택
       → Main Claude는 위험 다시 명시 후 사용자 최종 결정 따름
```

---

## 7. Feedback Log 경로

```text
피드백 파일:
  docs/orchestration/human_feedback/YYYY-MM/HF_YYYY-MM_NNN.md
  (Phase 4에 디렉터리 생성 — 이번 turn에 생성 안 함, 경로 정의만)

INDEX:
  docs/orchestration/human_feedback/INDEX.md
  (Phase 4에 생성)
```

`decision_logs/`와의 관계 (03 §4):
```text
decision_logs/ = Main Claude side 기록 (결정 과정, 검토 근거)
human_feedback/ = user input 기록 + DECISIONS_REQUIRED resolution
```
두 디렉터리는 상호 보완적이며 DEC_NNN ID로 연결된다.

`self_evolution/index.md` cross-link 의무:
- HF_YYYY-MM_NNN → SEV_YYYY-MM_NNN (feedback이 self-evolution으로 이어질 경우)
- SEV_YYYY-MM_NNN.md frontmatter에 `triggered_by_hf: HF_YYYY-MM_NNN` 기록

---

## 8. 금지사항

```text
금지 1: 사용자 승인 없이 cleanup (삭제/아카이브/이동) 실행
금지 2: 사용자 승인 없이 settings/hooks/MCP 변경
금지 3: 사용자 피드백을 임의 해석해 major claim 변경
금지 4: 불확실한 내용을 확정으로 기록 (UNKNOWN/TBD/NEEDS_CONFIRMATION 숨김 금지)
금지 5: 이전 세션 승인을 현재 세션 승인으로 재활용
금지 6: 사용자 응답 없이 DECISIONS_REQUIRED default로 진행 (민감 변경에 한함)
금지 7: Agent Team escalation 결과를 사용자 보고 없이 처리
금지 8: Codex 3회 reject를 Main Claude가 단독으로 처리 (human escalation 필수)
```

---

## 9. Human-readable Summary 원칙

매 turn 사용자에게 제시하는 판단 요약은 다음 형식을 따른다.

```text
1줄 현황:     <지금 상태 (Phase, blocker 유무)>
핵심 판단:    <Main Claude의 권장 방향 (1~2줄)>
선택지 3개:   Option A: <설명> / Option B: <설명> / Option C: <설명>
권장안:       <A | B | C> + 이유 1줄
예상 부작용:  <권장안의 주요 위험/비용>
다음 step:    <권장안 선택 시 즉시 실행될 내용>
```

5줄 이내 요약 원칙: 사용자가 맥락 없이 읽어도 판단할 수 있도록 작성한다.

---

## 10. Phase 4 적용 계획

```text
1. human_feedback/ 디렉터리 + INDEX.md scaffold 생성
   - Phase 4 첫 atomic commit (소형)
   - INDEX.md 컬럼: hf_id | date | decision_id | summary | resolution | session_id

2. DECISIONS_REQUIRED lifecycle 운영 시작
   - 본 문서 §3 extended schema 적용
   - 기존 NC-1~NC-7을 DEC_2026-05_NNN으로 마이그레이션

3. session_report와 연결
   - 해소된 DEC_NNN → session report decisions_made 필드에 기록
   - 미해소 DEC_NNN → session report needs_confirmation 필드에 기록

4. self_evolution/index.md와 연결
   - HF_NNN → SEV_NNN cross-link (feedback이 self-evolution으로 이어질 경우)

5. Phase 4 첫 DECISIONS_REQUIRED 항목 (예정):
   - DEC_2026-05_001: orchestration/redesign merge 여부
   - DEC_2026-05_002: cleanup NC-1/NC-2/NC-5/NC-7 처리 방법
   - DEC_2026-05_003: Codex fast-forward (a55cb33 → ba204a8) 실행 시점
   - DEC_2026-05_004: mcp_research/ + human_feedback/ scaffold 생성 승인
```
