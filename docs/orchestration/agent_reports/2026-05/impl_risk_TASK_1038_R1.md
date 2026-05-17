# impl_risk_TASK_1038_R1.md

**Agent**: implementation-risk-critic
**Task**: TASK_1038_step4_evidence_timestamp (B0)
**Date**: 2026-05-17
**Mode**: T3 pre-audit

## Verdict: ACCEPT_READY

## Scope Compliance
- allowed_files_only: YES (collector.py + test file only)
- forbidden_paths_clean: YES
- violations: none

## Semantic Correctness
- evidence_ts = next((i for i, step in enumerate(steps) if step.evaluation_labels.true_wrong_hypothesis), None)
- Matches eval_runner.py:255 SSoT exactly
- Invariants: evidence_ts <= hyp_update_ts and evidence_ts <= recovery_ts — both hold by episode structure definition

## Regression Risk: LOW
- _backfill_episode_timestamps 변경은 additive (hyp_update_ts, recovery_ts 로직 unchanged)
- test_step3_dataset_backfill.py (12) 회귀 위험 없음
- _build_evaluation_labels(L209-227) 미수정 명시됨

## Test Coverage: ADEQUATE
- 8 tests cover: first-wrong-step semantic, None path, leakage guard (3), invariants (2), bug-before-fix comparison
- Optional gap: step-0 edge case (LOW, non-blocking)

## Post-Execution Verification (Main Claude)
1. verify exit code = 0
2. git diff --cached --name-only → exactly 2 files
3. RESULT.md exists
4. pytest tests/test_step4_evidence_timestamp.py → 8/8 PASSED
5. pytest tests/test_step3_dataset_backfill.py → all PASSED
6. pytest tests/test_forbidden_field_mirror_sync.py → PASSED
7. v0_1/v0_2 mtime unchanged
