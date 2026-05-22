# 12_TRAINING_STAGES

## Source
- main.md §13 (training stages), §20 (training loop pseudocode)

## Claim

FGLC must train in 4 sequential stages. End-to-end training from scratch will fail
because the correction module will absorb all base WM gradients before the base WM
learns to produce meaningful predictions.

## Stages

```
Stage 1: Base WM pretraining (ID data only)
  Train: encoder E, GRU h_t, dynamics fθ, reward Rθ, value Vθ
  Freeze: nothing
  Loss: L_base_dynamics + L_reward + L_value + L_calibration
  Gate criterion: ID one-step NLL convergence + OOD NLL increases

Stage 2: Correction module training (ID + OOD data)
  Freeze: encoder E (or very low LR), base dynamics fθ (or low LR)
  Train: β-gate MLP, causal attention Aφ, correction adapter Gψ
  Loss: + L_corrected_dynamics + L_sparse + L_size + L_temporal + L_nec + L_suf + L_rand
  Gate criterion: OOD corrected NLL < uncorrected NLL; correction size < δ_max/2

Stage 3: Planner integration
  Freeze: encoder, dynamics (Stage 1 weights stable)
  Train: planner in closed-loop simulation (MPPI/CEM)
  Loss: return-weighted rollout; value TD updates
  Gate criterion: closed-loop return > TD-MPC2 baseline on at least 2 OOD conditions

Stage 4: Optional online fine-tuning
  Online: adapt correction module to new regime observations
  Loss: Stage 2 losses applied to most-recent trajectory buffer
```

## Why Freeze Base in Stage 2

If base dynamics and correction adapter train simultaneously:
1. Correction module receives gradient signal from BOTH correction losses AND base dynamics
2. Correction module learns to capture base dynamics residuals → base WM learns nothing
3. β_t gate can't distinguish "base WM is wrong due to OOD" from "correction filled the gap"
4. The "base WM = H0 hypothesis, correction = H1" story collapses

By freezing (or severely limiting) base WM LR in Stage 2, correction module can only improve
upon what the base WM produces.

## Connection Map
- Upstream: M-16 (loss design), M-6 (base dynamics architecture)
- Downstream: M-18 (planner in Stage 3), M-24 (pseudocode)
- All implementation phases: R2→R3→R4→R5→R6→R7 in ROADMAP

## Checkpoints

- C1 Math validity: PASS — Staged training is a design decision, not a mathematical claim.
  The argument for freezing is empirically motivated and reasonable.
- C2 Novelty: NOT CLAIMED — Staged training is standard in adapter-based methods.
- C3 Reviewer attack: LOW — "This requires careful staging" is expected. Mitigation: ablation
  showing end-to-end training fails (correction absorbs base WM).
- C4 Feasibility: PASS — Stage 1 ~2h on A100 per task, Stage 2 ~4h, Stage 3 ~6h.
  Total ~12h per task; 3 tasks in 36h. Feasible within 8-week budget.
- C5 Claim-metric: Stage 1 gate: ID NLL convergence + OOD NLL > ID NLL (shows OOD challenge).
  Without this, there's nothing to correct.
- C6 Impl risk: LOW
- C7 Experiment design: Required: show Stage 1 alone fails on OOD (validates problem existence).
  Required: show end-to-end training fails vs. staged training.
- C8 Failure interp: If Stage 1 OOD NLL ≈ ID NLL: OOD shifts don't challenge the base WM.
  This is a fundamental problem existence failure. Would force back to dataset design.
- C9 Related work: N/A (standard practice)
- C10 Context routing: Source = main.md §13,20. Downstream: 13_ALGORITHM_CIRCA.md, docs/ROADMAP/04_PHASE_R3...
