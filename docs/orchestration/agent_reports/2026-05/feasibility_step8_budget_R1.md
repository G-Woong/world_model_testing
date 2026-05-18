# feasibility-and-cost-auditor Report: STEP 8 Time/Compute Budget

**report_id**: feasibility_step8_budget_R1
**date**: 2026-05-18
**trigger**: T2 (실험설계 변경 전)
**verdict**: FEASIBLE (with 3 action items)

---

## Summary

STEP 8 is fully executable on local Windows CPU with MODEL-T0 (~460k params). No GPU required. Total estimated wall-clock: 1.1-5.7 hours best-to-worst.

## Wall-Clock Estimates

| Task | Best Case | Worst Case |
|---|---|---|
| (a) v0_4 dataset generation (5000 ep) | 5 min | 45 min |
| (b) Stage A training (1000 steps recommended) | 1 min | 5 min |
| (c) Stage B training (2000 steps) | 2 min | 8 min |
| (d) ABL-015 retrain (2000 steps) | 2 min | 8 min |
| (e) 30 eval runs (n=5 seeds) | 15 min | 90 min |
| (f) 11 inference ablations | 30 min | 150 min |
| (g) Regression test suite | 2 min | 10 min |
| (h) BASE-026/027 faithful eval | 10 min | 30 min |
| **TOTAL** | **~67 min** | **~346 min (~5.8h)** |

Empirical rate basis: training logs show 0.054-0.106 s/step (CPU, batch_size=8). v0_3: 135 train episodes, 250 total.

## Risk Flags

| Item | Severity | Flag |
|---|---|---|
| NaN recovery (lr × 0.5) | MED-WARN | Insufficient if NaN from F_t forward pass; gradient clipping needed |
| Stage A 500 steps (original) | MED-WARN | Only 1.1 epochs over v0_4; extend to 1000 steps |
| v0_4 counterfactual rollout cost | LOW | Measure first 200 ep before committing to 5000 |
| All others | LOW | No escalation needed |

## 3 Required Action Items (Before STEP 8 Execution)

### ACTION 1 (REQUIRED): Gradient clipping in train_one_epoch()
Add `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)` between `.backward()` and `.step()` in `src/frcgw/training/train_text.py`. The LR × 0.5 retry alone is insufficient if NaN originates from large logit magnitudes in falsification_score().

Target file: `src/frcgw/training/train_text.py`
Change: 1 line + test assertion that grad_norm never exceeds 2.0 in smoke test

### ACTION 2 (RECOMMENDED): Extend Stage A to 1000 steps
Change `max_steps: 500` to `max_steps: 1000` in Stage A config. At v0_4 (3500 train ep), 500 steps = 1.1 epochs; 1000 steps = 2.28 epochs, sufficient for F_t convergence signal. Wall-clock cost: +30-90 seconds.

### ACTION 3 (ADVISORY): Early-stop hook at Stage B step 1000
If valid `l_falsification < 0.60` at step 1000, extend `max_steps` to 3000. Monitor via training_log.jsonl.

## Q&A

**Q2: Is lr × 0.5 / 1-retry sufficient for NaN?** No. Gradient clipping at max_norm=1.0 is required.

**Q3: Stage A 500 steps sufficient for F_t variance?** No. 1.1 epochs is insufficient. Extend to 1000 steps.

**Q4: n=5 seed parallelization?** Use sequential seeds within eval runner (current design). No Windows parallelism needed.

**Q5: Overfitting risk at 2000 steps / 3500 episodes?** Low. Model is 460k params. Underfitting from too-few unique-episode passes is higher risk than overfitting.

## Empirical Timing Evidence
- `outputs/runs/p3_train_v0_3_stage1/training_log.jsonl`: 200 steps in 21.2s = 0.106 s/step
- `outputs/runs/p3_train_v0_3_falsification_stage2/training_log.jsonl`: 498 steps in 27s = 0.054 s/step
- `data/frcgw_text/v0_3/manifest.json`: 250 total episodes confirmed
