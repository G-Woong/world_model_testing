# Phase R8 — Algorithm Variants (ASAP, I3G, IVI)

## Goal
Implement ASAP, I3G, IVI algorithms. All share Stage 1 base WM. Compare against CIRCA.

## Steps

1. **ASAP**: Add interventional ASV computation on top-k groups; distill to α
2. **I3G**: Add iVAE factored prior + ICP invariance penalty; SPCI calibration
3. **IVI**: Add influence function (gradient norm) as first-pass ranker; randomized knockout validation

## Gate Criteria
- [ ] All 3 algorithms train without divergence
- [ ] Shared Stage 1 weights confirmed identical (SHA256 match)
- [ ] 4-algorithm comparison results on PickCube ID+OOD available

## Codex Delegation
Yes — 3 separate algorithm training variants → TASK_R8_ALGORITHM_VARIANTS.md
