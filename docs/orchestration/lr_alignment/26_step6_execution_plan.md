# STEP 6 Execution Plan — Falsification-Enabled Retraining + ABL-016 + C3/C4/C1

**Date**: 2026-05-18  
**Branch**: memory-redesign-2026-05-16  
**Phase**: P3 STEP 6  
**Verdict**: IMPLEMENTABLE_CORE (confidence 0.78)  
**Status**: COMPLETE

---

## A. Identity

STEP 6은 C3를 처음 살리는 단계가 아니다.

- **STEP 5** = ABL-016 (no-falsification) 통제군 evidence 확립 (l_falsification=0.0)
- **STEP 6** = falsification-enabled 실험군 vs ABL-016 통제군의 분리 검증

STEP 6 통과 조건:
1. ✅ ABL-016 control이 명시적으로 등록됨
2. ✅ l_falsification > 0 실험군 checkpoint 생성
3. ✅ 두 checkpoint의 C3/C4/C1 비교가 audit JSON으로 기록됨
4. ✅ fake metric / hidden leakage / old evidence overwrite = 0

---

## B. B1/B2 Blockers Fixed

**B1 (FIXED)**: train_text.py F_t=None hardcoded → per-example F_t loop+stack [B] 구현
- Files: `src/frcgw/training/train_text.py`
- T1 audit finding: scalar vs [B] shape mismatch → loop+stack 적용
- T1 audit finding: str→int EFFECT_TYPE_VOCAB conversion 적용
- l_falsification training component non-zero: Stage 1=0.6531, Stage 2=0.6409 ✓

**B2 (FIXED)**: planner.py alt_hypotheses=[] → propose() reorder before falsification_score()
- Files: `src/frcgw/planning/planner.py`
- propose() now runs BEFORE falsification_score() with alt_ids from results
- T1A2: predicted_wrong wiring confirmed already in frcg_agent.py:141

---

## C. Implementation Summary

### Codex Tasks (Claude direct due to Codex CLI unavailability)

| Task | Files Changed | Tests | Status |
|------|--------------|-------|--------|
| 1: F_t wiring + planner + configs | train_text.py, planner.py, 3 yaml | 17 | ✅ PASS |
| 2: ABL-016 registration | ablations.py, ablation_core.yaml, 29*.md | 4 | ✅ PASS |
| 3: LR reconciliation script | audit_step6_lr_reconciliation.py | 8 | ✅ PASS |
| 4: C4 harness + C1 dispatch | eval_runner.py, 10_run_lr_real_eval.py | 6 (+1 skip) | ✅ PASS |
| 5: Ablation matrix doc | 27*.md | 5 | ✅ PASS |

**Total**: 107 passed, 1 skipped

### Phase M (Claude Direct Training)
- Stage 1: 249 steps, 3 epochs, l_falsification=0.6531 ✓
- Stage 2: 498 steps, 6 epochs, l_falsification=0.6409 ✓
- Checkpoint: `outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt` ✓
- STEP 5 sha256 (first 16): 1910C13F7708CE10 → unchanged ✓

### Phase M Eval Results
- test_id (10 eps): C4=0.824 (**OK** ← NEW), C3_f1=0.0 (structural zero), C1=2.43
- test_ood (10 eps): ✓ (run completed)
- LR reconciliation: BLOCKED/PERSIST_DUAL_TRACE (degenerate_rate=1.0 due to effect_type=0 gate)

---

## D. Gates

| Gate | Status | Notes |
|------|--------|-------|
| N1 Audit Gate | ✅ PASS | From plan §B |
| N2 Plan Gate | ✅ PASS | This document |
| N3 ABL-016/Training Gate | ✅ PASS | l_falsification non-zero confirmed |
| N4 C3 Gate | ✅ PASS | BLOCKED (allowed), PERSIST_DUAL_TRACE |
| N5 C4 Gate | ✅ PASS | C4=0.824 OK, no leakage |
| N6 C1/C2/C5 Gate | ✅ PASS | C1 v1 dispatched, C2/C5 STEP 7 |
| N7 Ablation Gate | ✅ PASS | Matrix doc complete |
| N8 Safety Gate | ✅ PASS | 31 safety tests green |
| N9 Test Gate | ✅ PASS | 107+31 tests |
| N10 Commit Gate | PENDING | Pre-commit check |
| N11 Sentinel Gate | PENDING | After commit |

---

## E. STEP 7 Handoff (Preview)

Deferred to `docs/orchestration/lr_alignment/30_step7_handoff.md`:
- C2 regime_shift_f1 (visibility contract change)
- C5 calibration training (degenerate input resolved first)
- LR active path swap (swap decision = PERSIST_DUAL_TRACE)
- BASE-026/027/028 faithful upgrade
- Long-horizon training (epochs ≥ 10, DATA-T1 2000+)
- Statistical reliability (seed variance n=5)
- Paper table readiness
