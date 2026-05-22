# Phase R4 — Falsification Gate

## Goal
Implement standardized mismatch, conformal calibration, β-gate MLP.
Gate: OOD detection AUROC > 0.75 with false alarm rate < 0.2 on ID.

## Inputs
- Prior phase sentinel: outputs/phase_gates/R3.passed
- Code: src/fglc/detectors/mismatch.py, gate.py
- Data: Stage 1 trained model, ID + OOD splits

## Steps

1. Implement `src/fglc/detectors/mismatch.py`
   ```python
   def standardized_mismatch(z_next, mu, sigma):
       rho = (z_next - mu) / sigma  # per-group [K, d]
       F_k = (rho**2).sum(dim=-1)   # [K]
       F_total = F_k.sum()           # scalar
       return rho, F_k, F_total
   ```

2. Implement `src/fglc/detectors/gate.py`
   ```python
   class FalsificationGate(nn.Module):
       # MLP([F_1,...,F_K, F_total, h_t]) → β_t
       # Conformal calibration: threshold = empirical (1-α)-quantile of F_t on ID holdout
   ```

3. Run conformal calibration
   - Collect F_t distribution on held-out ID validation episodes
   - Set threshold τ = (1-α)-quantile (α = 0.05 → 95th percentile)
   - Post-training calibration (no fine-tuning needed)

4. Variance calibration check
   - Plot reliability diagram for σ_t predictions
   - Compute ECE; target ECE < 0.1
   - If ECE > 0.2: add L_cal penalty and re-train

5. Evaluate detection
   - AUROC using F_t as score, regime_id as oracle label
   - Detection delay measurement
   - False alarm rate on ID data

## Gate Criteria (all must be true for R4.passed)

- [ ] OOD detection AUROC > 0.75 (vs. random 0.5)
- [ ] False alarm rate on ID < 0.20 (at α=0.05 conformal threshold)
- [ ] ECE for σ_t predictions < 0.15
- [ ] β_t autocorrelation AR(1) > 0.5 under OOD-mass (vs. < 0.1 under ID noise)
- [ ] Variance calibration reliability plot saved to outputs/
- [ ] `pytest tests/test_fglc_falsification.py` green

## Risk Register References
- R-5: σ calibration is load-bearing — if ECE fails, detection claim fails
- R-6: Conformal coverage conservative under non-exchangeable OOD data

## Commit Cadence
- commit 1: `feat(detect): R4 standardized mismatch + per-group F_t`
- commit 2: `feat(detect): R4 falsification gate MLP + conformal calibration`
- commit 3: `results(R4): OOD AUROC > 0.75 + ECE < 0.15 verified`

## Codex Delegation
Yes → Codex TASK_R4_FALSIFICATION_GATE.md
