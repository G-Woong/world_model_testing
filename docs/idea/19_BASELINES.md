# 19_BASELINES — Must-Not-Disappear Baseline Enumeration

## Source
- main.md §22.5 (ablation list), deep-research-report.md §벤치마크
- CLAUDE.md §Baselines That Must Not Disappear

## This file IS the normative baseline SSoT. Do not maintain duplicates elsewhere.

## Required Baselines

Every category MUST have at least one runner in the evaluation suite.

### Category A: World Model Baselines

| ID | Name | Description | Expected result |
|---|---|---|---|
| BASE-WM-01 | TD-MPC2 | Reference decoder-free latent WM (Hansen 2024) | Strong ID; degrades OOD |
| BASE-WM-02 | DreamerV3 | RSSM-based WM (Hafner 2023) | Strong on partial-obs tasks |
| BASE-WM-03 | HiP-RSSM | Context-conditioned RSSM (Achterhold 2022) | Strong with regime context |
| BASE-WM-04 | PLSM | Action-effect systematic WM (Tomar 2024) | Action-relevance comparison |

### Category B: Adaptation Baselines

| ID | Name | Description | Expected result |
|---|---|---|---|
| BASE-ADAPT-01 | ReDRAW | Residual latent correction (sim-to-real) | Similar mechanism, no causal attention |
| BASE-ADAPT-02 | AdaWM | Mismatch-driven adaptation | Closest competitor to FGLC |

### Category C: Ablative Baselines

| ID | Name | Description | Expected result |
|---|---|---|---|
| BASE-ABL-01 | Next-state-WM-only | FGLC base WM, no correction module | FGLC Stage 1; lower bound |
| BASE-ABL-02 | Always-correct WM | β_t = 1 always (no falsification gate) | Upper bound for correction; tests gate necessity |
| BASE-ABL-03 | Verifier-only (CUSUM) | CUSUM detector, no correction | Detection without planning benefit |
| BASE-ABL-04 | Verifier-only (SPRT) | SPRT detector, no correction | Optimal detection-delay tradeoff |
| BASE-ABL-05 | Verifier-only (BOCPD) | BOCPD change-point detector, no correction | Bayesian detection; no planning |

### Category D: Compute/Planning Baselines

| ID | Name | Description | Expected result |
|---|---|---|---|
| BASE-COMP-01 | Uncertainty-gated planner | Plan more when σ_t high (no falsification) | Compute efficiency comparison |
| BASE-COMP-02 | Random correction mask | Random k groups corrected (not attention-guided) | Tests attention contribution |
| BASE-COMP-03 | No-correction baseline | Base WM, no correction capacity at all | True lower bound |
| BASE-COMP-04 | Compute-matched random realloc | Same # planning rollouts as FGLC, randomly allocated | Critical: Attack 5 defense |

### Category E: Oracle Upper Bounds

| ID | Name | Description | Expected result |
|---|---|---|---|
| BASE-ORACLE-01 | Oracle-mass | Planner given true mass at inference | Perfect OOD-mass correction |
| BASE-ORACLE-02 | Oracle-friction | Planner given true friction | Perfect OOD-friction correction |
| BASE-ORACLE-03 | Oracle-latency | Planner given true action delay | Perfect OOD-latency correction |
| BASE-ORACLE-04 | Oracle-noise | Planner given true noise σ | Perfect OOD-noise correction |

## Baseline Removal Policy

If any baseline is removed, the corresponding claim CANNOT be made:
- Remove TD-MPC2 → cannot claim "outperforms TD-MPC2"
- Remove Compute-matched → cannot claim "return-per-compute improvement"
- Remove Oracle → cannot claim "approaches oracle performance"
- Remove Verifier-only → cannot claim "correction adds beyond detection"

## Connection Map
- This file is referenced by: CLAUDE.md, behavioral_coding_rules.md §5, baseline_ablation_guard.ps1
- Downstream: 21_METRICS.md (eval each baseline), docs/ROADMAP/11_PHASE_R10_BASELINES.md
