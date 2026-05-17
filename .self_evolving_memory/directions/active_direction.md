# Active Direction

Last updated: 2026-05-17
Branch: `memory-redesign-2026-05-16`

## Current Focus

**Lifecycle Automation v2 — Phase 1 Foundation** (이번 turn)

- `scripts/lifecycle_audit_v2.py` dry-run 분류 엔진 구현 완료
- `.self_evolving_memory/` skeleton 생성 완료
- `outputs/lifecycle/` + `.lifecycle_trash/` reservation 완료
- hook/settings 변경 없음, 파일 이동 없음

## Open Blockers

### B-1: C3 LR Claim Falsification (HIGH PRIORITY — P3 gate)

- **Issue**: `planning_rate=0.0` — P3 eval에서 planning calls zero
- **Gate sentinel**: `outputs/phase_gates/P3_EVAL.BLOCKED_planning_calls_zero.md`
- **Claim**: C3은 wrong-control-grammar falsification이 recovery 향상을 유발함을 주장
- **Required before P4**: falsification signal 확인 또는 claim 수정
- **Status**: 이번 turn은 lifecycle Phase 1 우선; C3 remediation은 다음 turn

### B-2: Lifecycle Phase E — stop hook integration (MEDIUM, 별도 승인 필요)

- **Requires**: `stop_lifecycle_automation.ps1` 신규 생성 + `settings.json` hook entry 추가
- **Requires**: 명시적 사용자 승인 (fragile invariant 변경)
- **Not in Phase 1 scope**

## Completed This Turn

- [x] `.gitignore` lifecycle reservation entries 추가
- [x] `scripts/lifecycle_audit_v2.py` 생성 (dry-run only, no subprocess, no destructive API)
- [x] `tests/test_lifecycle_audit_v2.py` 생성 (10 contract tests)
- [x] `outputs/lifecycle/.gitkeep` 생성
- [x] `.lifecycle_trash/.gitkeep` 생성
- [x] `.self_evolving_memory/` skeleton 생성

## Next After This Turn

1. Run verification plan (pytest + dry-run audit)
2. Address C3 falsification blocker (P3 remediation plan)
3. Lifecycle Phase E: stop hook integration (별도 PLAN turn 필요)
