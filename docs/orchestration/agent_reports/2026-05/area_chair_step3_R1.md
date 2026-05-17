# Area-Chair Synthesis: STEP 3 Final Assessment

**Date**: 2026-05-17
**Verdict**: MAJOR_REVISION (infrastructure advance, zero claim advance)

## What STEP 3 Achieves (Permitted Wording)

- "C1/C3 metric infrastructure is now populated with non-null values from a random-init smoke run."
- "LR-based predicted_wrong (F_t > tau_f) replaces confidence proxy; tau_f propagation verified."
- "Preliminary ECE=0.025 is a calibration reference point from random-init run, not a calibration claim."

## Forbidden Wording (Scientific Contract Violation)

- "FRCG-WM detects wrong control-grammar hypotheses" (F1=0.0 at random init)
- "The LR falsification scorer is calibrated" (ECE from 3-episode random-init is an artifact)
- "C3_delay=3.0 shows recovery is faster" (no baseline comparison)
- "C1 is now computable" without PARTIALLY_COMPUTABLE qualifier

## TOP 3 Risks to Acceptability

1. **FATAL**: F1=0.0 with no pre-trained checkpoint — C3 claim collapses
2. **CRITICAL**: C1 start anchor (evidence_timestamp) missing — MET-PERSIST-001 uncomputable
3. **HIGH**: No baseline comparison — metrics have no comparative anchor

## What STEP 4+ Must Resolve

1. Pre-trained checkpoint (F1=0.0 is only expected from random init)
2. evidence_timestamp backfill (C1 start anchor)
3. Counterfactual rollout (C4)
4. BASE-006 comparison (C3)
5. ABL-017 reverse direction (C5)
6. planning_calls > 0 (P3 gate validity)
