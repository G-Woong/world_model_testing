---
evolution_id: SEV_2026-05_001
date: 2026-05-15
trigger: AGENT_REPORT
---

## OBSERVED_FAILURE

`pre_compact_phase_handoff.ps1` hook이 `plans/PHASE_PROGRESS.md`에 자동 append한다.
이로 인해:
1. `plans/`가 사용자 작성 plan + hook auto-append가 혼재됨
2. 공식 source-of-truth가 `docs/orchestration/session_reports/`로 이관됐으나 hook이 여전히 구 경로에 쓴다
3. `plans/PHASE_PROGRESS.md`가 repo tracking 대상이 아닌 경우 hook 결과가 git history에서 누락될 수 있음

## EVIDENCE

| path | line | description |
|---|---|---|
| `docs/orchestration/PHASE2_GATE_REPORT.md` | §8.1 R7 | R7 MED: PreCompact hook이 plans/PHASE_PROGRESS.md에 자동 append |
| `docs/orchestration/01_PERMISSION_SCOPE_AUDIT.md` | R7 항목 | hook auto-append side-effect |

## AFFECTED_COMPONENT

settings (hook) — `.claude/hooks/pre_compact_phase_handoff.ps1` 수정 필요. requires human approval.

## PROPOSED_IMPROVEMENT

`pre_compact_phase_handoff.ps1`의 출력 경로를:

```
before: plans/PHASE_PROGRESS.md  (append)
after:  docs/orchestration/session_reports/YYYY-MM/<session_id>_precompact.md  (new file per session)
```

으로 변경.

이때 YYYY-MM은 실행 시점 날짜에서 추출, session_id는 타임스탬프 기반.

## EXPECTED_BENEFIT

- `plans/`는 사용자 작성 plan 전용으로 정화됨
- PreCompact 자동 append는 session_reports/와 일관된 위치에 저장됨
- 월별 디렉터리 구조로 추적 가능

## RISK

MED — 기존 `plans/PHASE_PROGRESS.md`를 참조하는 다른 워크플로가 있을 수 있음.
hook 변경 후 일정 기간 dual-write (구 경로 + 새 경로) 고려.

## REQUIRED_APPROVAL

HUMAN — `.claude/hooks/` 수정은 Phase 3 §4.2 절대 수정 금지 목록에 포함됨.
이 proposal은 Phase 3에서 승인 요청만 하며, 실제 수정은 Phase 4에서 별도 atomic step.

## ADOPTION_STATUS

PENDING

## ADOPTED_IN_BRANCH

none

## ROLLBACK_METHOD

```
git revert <hook-redirect-commit>
# 또는
# .claude/hooks/pre_compact_phase_handoff.ps1의 출력 경로 라인을 원복:
# $outputPath = "plans/PHASE_PROGRESS.md"
```

## NEXT_REVIEW_DATE

Phase 4 시작 시

## NOTES

Phase 3에서는 proposal만 작성. 적용은 사용자가 Q6=B를 선택하면 Phase 4에서 진행.
현재 상태: Q6=A (proposal만, Phase 3 보류) — 이 파일이 proposal artifact.
