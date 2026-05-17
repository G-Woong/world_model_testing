# 16_self_evolving_memory_architecture_plan.md

## Purpose

반복 에러 차단 + 단일 폴더 self-evolving memory 설계.

생성일: 2026-05-17  
Branch: memory-redesign-2026-05-16  
Status: ACTIVE_POLICY  
Phase: pre-implementation (설계만, 코드 수정 0)  
Archive_after: Phase C 완료 후 → `plans/archive/2026-06/`

---

## §1. Current Self-Evolving Audit

### SSoT 문서

`docs/orchestration/05_SELF_EVOLVING_LOOP.md` — canonical  
§1: "self-evolving은 운영 프로토콜 대상. settings 파일이 아니다."

### 현재 데이터 위치 (4분산)

```
docs/orchestration/self_evolution/2026-05/     ← 진화 사이클 로그
docs/orchestration/decision_logs/2026-05/      ← 결정 기록
docs/orchestration/human_feedback/2026-05/     ← 피드백
docs/orchestration/session_reports/2026-05/    ← 세션 보고서
```

### Gap

- error/decision/idea/lesson 통합 store 없음
- hook 중 memory update 하는 것 없음
- `pre_compact_phase_handoff.ps1`만 `session_reports/`에 dual-write
- error_memory / recurring_error / do_not_repeat 패턴 grep → **0건**
- `.self_evolving_memory/` → **NOT_FOUND**

---

## §2. Problem Statement

1. 동일 에러 재발 감지 메커니즘 없음
2. 사용자가 4폴더를 모두 봐야 함 (session_reports + decision_logs + human_feedback + self_evolution)
3. decision과 superseded plan이 분리되지 않음
4. 방향성 아이디에이션이 active plan과 섞임
5. negative evidence와 superseded report 구별 불가

---

## §3. Desired Single Folder Structure

```
.self_evolving_memory/
  README.md                    ← 사용자 진입점 (이것만 보면 됨)
  index.yaml                   ← machine-readable master pointer
  errors/
    error_memory.yaml          ← canonical store (append-only)
    recurring_errors.md        ← occurrence_count >= 2 highlight
    resolved_errors.md
  decisions/
    decision_memory.yaml       ← canonical store (append-only)
    superseded_decisions.md
  patterns/
    successful_patterns.md
    anti_patterns.md
  directions/
    active_direction.md        ← 사용자가 승인한 현재 방향
    rejected_directions.md     ← 거부된 방향 (이유 포함)
    parking_lot.md             ← 나중에 재검토할 아이디어
  hooks/
    hook_failures.md           ← hook 실패 기록
    hook_execution_log.md
  run_summaries/
    YYYY-MM/
      run_<UTC>.md
```

---

## §4. Error Memory Schema (YAML)

```yaml
- error_id: ERR-2026-05-001
  first_seen: 2026-05-17T04:23:56Z
  last_seen: 2026-05-17T04:49:10Z
  occurrence_count: 2
  error_signature: "<sha256 of normalized stack>"
  stack_trace_excerpt: |
    File "src/frcgw/...", line N, in ...
    ...
  root_cause: "..."
  fix_applied: "<commit hash or PR link>"
  verification_command: "pytest -q tests/test_xxx.py"
  regression_test: "tests/test_xxx.py::test_yyy"
  related_files:
    - src/frcgw/...
  owner: claude | codex | user
  status: OPEN | RESOLVED | WATCH
  do_not_repeat_rule: "..."
  escalation_rule: "occurrence_count >= 2 → BLOCKER"
```

### Error Memory 운영 규칙

- occurrence_count ≥ 2 → BLOCKER 표시, stop event에서 재발 경고
- regression test 없이 status: RESOLVED 금지
- fix_applied 없이 status: RESOLVED 금지
- error_signature: normalized stack sha256 (파일 경로/라인 번호 제거 후 해시)

---

## §5. Direction / Idea Memory Schema (YAML)

```yaml
- idea_id: IDEA-2026-05-014
  source: war_room_R1_synthesis | user_prompt | codex_result
  hypothesis: "..."
  claim_relation: C1 | C2 | C3 | C4 | C5 | C6
  status: ACTIVE | PARKED | REJECTED | SUPERSEDED
  evidence:
    - docs/orchestration/lr_alignment/...
  why_rejected: "..."
  revisit_condition: "...if seen again or if claim changes"
  related_docs:
    - docs/orchestration/...
```

---

## §6. Hook Integration

`stop_lifecycle_automation.ps1` 또는 별도 `stop_self_evolving_update.ps1`가 stop event에서:

| 이벤트 | 업데이트 대상 |
|---|---|
| 이번 턴 에러 발생 | `errors/error_memory.yaml` append |
| hook stderr capture | `hooks/hook_failures.md` append |
| 에러 재발 감지 | `errors/recurring_errors.md` highlight + BLOCKER 경고 |
| 에러 해결 | status: RESOLVED, regression_test 필드 확인 |
| 새 decision | `decisions/decision_memory.yaml` append |
| superseded plan | `directions/rejected_directions.md` 요약 기록 |
| 새 active direction | `directions/active_direction.md` 덮어쓰기 (이전 → rejected) |
| 턴 완료 | `run_summaries/YYYY-MM/run_<UTC>.md` 작성 |
| repeated error | `stop_summary_guard.ps1`과 통합 경고 |

---

## §7. User Management Model

사용자가 직접 볼 파일 2개만:
```
.self_evolving_memory/README.md
.self_evolving_memory/index.yaml
```

사용자 수동 조작 4항목:
1. `directions/active_direction.md` 승인 또는 수정
2. `directions/rejected_directions.md` 복구 (parking_lot으로 이동)
3. `errors/recurring_errors.md` BLOCKER escalation 승인
4. memory pruning 승인 (연 1회 정도)

---

## §8. Integration with Lifecycle Trash

- `.self_evolving_memory/` 자체는 **자동 trash 금지** (protected glob)
- superseded idea/report 원문은:
  1. `directions/rejected_directions.md`에 요약 기록
  2. 원문이 lifecycle trash 후보가 될 수 있음 (manual-only 분류)
- negative evidence는 **삭제 절대 금지**, archive만 허용
- decision_logs, human_feedback 원문: manual-only → 사용자 승인 후 archive

---

## §9. .gitignore 갱신 권고

`.self_evolving_memory/` commit 정책:

| 경로 | commit 여부 | 이유 |
|---|---|---|
| `index.yaml` | YES | master pointer, 다른 기기에서 상태 파악 |
| `README.md` | YES | 사용자 진입점 |
| `errors/recurring_errors.md` | YES | BLOCKER 정보 공유 |
| `directions/active_direction.md` | YES | 현재 방향 공유 |
| `run_summaries/**` | NO (.gitignore) | 로컬 machine state |
| `hooks/hook_execution_log.md` | NO (.gitignore) | 로컬 trace |
| `errors/error_memory.yaml` | SELECTIVE | occurrence_count >= 2만 commit 추천 |

`.gitignore` 추가 예정 라인 (Phase A):
```
# Self-evolving memory (machine state)
.self_evolving_memory/run_summaries/
.self_evolving_memory/hooks/hook_execution_log.md
# .self_evolving_memory/index.yaml 은 whitelist 유지
```

---

## §10. Cross-reference

- `docs/orchestration/05_SELF_EVOLVING_LOOP.md` — 기존 self-evolving SSoT
- `docs/orchestration/15_lifecycle_automation_v2_plan.md` — lifecycle automation
- `docs/orchestration/19_LIFECYCLE_AUTOMATION_V2_MASTER_PLAN.md` — master plan
