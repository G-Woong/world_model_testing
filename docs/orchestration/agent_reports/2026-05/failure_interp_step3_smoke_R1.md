# T4 Failure-Interpretation-Critic: STEP 3 Smoke Run

**Date**: 2026-05-17
**Artifact**: `outputs/runs/p3_lr_real_eval_step3_smoke/metrics.json`
**Run**: ckpt_path=null, random_init_ok=False, N=3 episodes

## Findings

| Metric | Verdict | FAIL | Claim Impact |
|---|---|---|---|
| C3_falsification_f1=0.0 | EXPECTED (random init, no signal) | None | PRESERVES — prior f1=0.583 from p3_lr_real_eval_smoke is live evidence |
| C5_calibration_ece=0.025 | ARTIFACT (degenerate F_t=0.0 constant) | FAIL-018 inverse risk | REQUIRES_MODIFICATION — label artifact in evidence card |
| C1_persistence=3.0 | EXPECTED (episode-length floor, all agents same) | None | PRESERVES at CONDITIONAL_ALIVE |
| BLOCKED→COMPUTABLE | No hidden negatives | None | One disclosure gap: add valid_trained_eval=false |

## Required Actions

1. C5 evidence card: add counter_evidence for ECE=0.025 artifact
2. C3 evidence card: distinguish STEP 3 zero from pre-backfill f1=0.583
3. Metrics runner: add `valid_trained_eval: false` when hard_checks_all_pass=False
4. STEP 4: evidence_timestamp backfill + pre-trained checkpoint before any C1 claim

## overall_claim_status: PRESERVED (with disclosure corrections)
