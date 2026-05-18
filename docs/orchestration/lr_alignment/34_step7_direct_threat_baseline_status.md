# STEP 7 Direct-Threat Baseline Status

date: 2026-05-18
status: DOCUMENTATION_HARDENING_ONLY

## Summary

BASE-026 (WAC), BASE-027 (CUWM), and BASE-028 (WebWorld) are implemented as
heuristic proxies in STEP 7. STEP 7 standardizes the `approximation_level`
declarations and hardens the paper wording forbidden list.

## Approximation Level Declarations

| Baseline | approximation_level | Faithful upgrade |
|---|---|---|
| BASE-026 (WAC) | heuristic last-effect-fail proxy; full WAC deferred | STEP 8 |
| BASE-027 (CUWM) | heuristic longest-action-id proxy; full CUWM deferred | STEP 8 |
| BASE-028 (WebWorld) | heuristic next-state proxy; full WebWorld infeasible | STEP 8/9 |

## Paper Wording: FORBIDDEN (reviewer attack vectors)

- "defeats WAC"
- "outperforms CUWM"
- "superior to WebWorld"
- "compared to WAC baseline" (without approximation_level qualifier)
- "our method vs WAC" (implies faithful WAC comparison)

## Paper Wording: ALLOWED

- "compared against heuristic proxy baselines (approximation_level=heuristic)"
- "BASE-026: WAC-style heuristic proxy (faithful WAC deferred to STEP 8)"
- "BASE-027: CUWM-style heuristic proxy (faithful CUWM deferred to STEP 8)"
- "direct-threat baselines: heuristic approximations only; faithful implementations in STEP 8"

## STEP 8 Roadmap

- BASE-026 faithful: grammar posterior + consequence model (WAC section 3.2)
- BASE-027 faithful: candidate simulation with world model rollout (CUWM section 4)
- BASE-028 faithful: full simulator search (most complex, may require STEP 9)
