# Phase R12 — DROID/BridgeData Validation

## Goal
Transfer FGLC to real robot data (DROID RLDS, BridgeData V2).
Validate generalization beyond sim physics.

## Steps

1. DROID: convert RLDS format to FGLC training format (proprio + action, no regime_id available)
2. BridgeData V2: institution split as OOD (different labs = distribution shift)
3. Evaluate: return/recovery on available subsets (no oracle regime label → use control metrics only)

## Key Difference from Sim
- No regime_id → cannot compute detection AUROC or mask precision/recall
- Evaluation limited to: prediction NLL, return, success rate, recovery time
- OOD must be defined by data source (DROID collectors, BridgeData institutions)

## Gate Criteria
- [ ] FGLC trained on DROID (subset ≥ 500 trajectories) and evaluated
- [ ] NLL improvement on held-out institution vs. base WM
- [ ] Return improvement on BridgeData V2 institution OOD split

## Risk Register
- R-4 (ROADMAP/19): DROID dataset access requires application (~100GB)
- R-5: Real robot noise may overwhelm correction signal; ECE may be worse than sim
