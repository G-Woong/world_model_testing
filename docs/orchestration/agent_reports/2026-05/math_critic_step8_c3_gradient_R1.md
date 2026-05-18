# mathematical-validity-critic Report: STEP 8 C3 Gradient Path Analysis

**report_id**: math_critic_step8_c3_gradient_R1
**date**: 2026-05-18
**trigger**: T2 (실험설계 변경 전)
**verdict**: NEEDS_REVISION

---

## Summary

VOCAB fix (STEP 7) is mathematically correct. Gradient paths for effect type indices 1,2,4,5 are now valid. Two MEDIUM severity issues must be resolved before Stage A training.

## Key Findings

### Q1: VOCAB Fix — Gradient Path (PASS)
After STEP 7 fix, all public strings correctly map:
- `no_state_change` → 0 (short-circuits)
- `state_change` → 1 (gradient flows)
- `blocker_removed` → 2 (gradient flows)
- `delayed_effect` → 4 (gradient flows)
- `task_complete` → 5 (gradient flows)

`losses.py` and `planner.py` now consistent. Before STEP 7, `blocker_removed`, `delayed_effect`, `task_complete` were absent from EFFECT_TYPE_VOCAB → KeyError.

### Q2: Short-Circuit Fraction (WARN)
Short-circuit fires on `{0, 6}`. Index 0 = `no_state_change`. Index 6 (`no_op_valid`) is legacy-only — unreachable via `_PUBLIC_EFFECT_TYPES`. With v0_3 OOD: blocker_removed=0, delayed_effect=0, ~40-70% of steps may short-circuit. v0_4 with OOD coverage is necessary (not sufficient) to reduce this fraction.

### Q3: L_falsification Gradient Density (WARN — CRITICAL RISK)
**CRITICAL**: `compute_total_loss()` accepts `F_t=None` and returns `_zero()` (losses.py:119-120). If the training loop does NOT compute F_t from the world model heads and pass it to `compute_total_loss()`, L_falsification is silently zero regardless of VOCAB fix and l_falsification=1.0 weight setting. **This must be verified in the training script before Stage A runs.**

Stage A (500 steps) is diagnostic only — use for F_t curve monitoring, not C3 verdict.

### Q4: lr_scorer.py Public Proxy (PASS)
`from_public_step()` correctly derives all EvidenceFeatures from public observations only. No hidden labels enter the LR scoring path.

### Q5: 7-Class Identifiability (WARN)
Classes 3 (`failed`) and 6 (`no_op_valid`) are legacy-dead — zero gradient in v0_4. `blocker_removed` (2) and `delayed_effect` (4) at ≥30/5000 = 0.6% frequency is marginal. F_t identifiability is CONDITIONALLY IDENTIFIABLE — requires sufficient (hypothesis_id, effect_type) co-occurrence diversity.

## Risk Table

| Severity | Risk | Action Required |
|---|---|---|
| MEDIUM | L_falsification silently zero if training loop doesn't compute F_t | Verify/fix in Stage A/B training script before run |
| MEDIUM | blocker_removed/delayed_effect class imbalance (0.6%) in v0_4 | Log per-class accuracy in Stage A; consider ≥100 each if compute allows |
| LOW | Classes 3, 6 undertrained | Document as known; no action needed |
| LOW | Short-circuit 40-70% in v0_3 | v0_4 OOD coverage reduces; monitor F_t>0 fraction per batch |

## Action for Codex Tasks

- **Task 3 (training configs)**: TASK file must specify that training script computes `F_t = falsification_score(model, ...)` per batch and passes non-None F_t to compute_total_loss(). Add assertion `assert F_t is not None` when l_falsification>0.
- **Task 1 (C3 diagnostics)**: audit_step8_c3_root_cause.py must measure L_falsification loss curve (non-zero check) and per-class effect_logit accuracy for classes 2,4.

## Files Referenced
- `src/frcgw/objectives/losses.py` lines 44-62, 117-128, 153-191
- `src/frcgw/planning/planner.py` lines 55-75
- `src/frcgw/planning/falsification.py` lines 49-85, 64-67
- `src/frcgw/falsification/lr_scorer.py` lines 89-145
- `src/frcgw/text_env/counterfactual_rollout.py` lines 18-26, 101-103
