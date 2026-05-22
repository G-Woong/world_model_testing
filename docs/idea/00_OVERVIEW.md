# 00_OVERVIEW — FGLC Idea Navigation Map

## One-Sentence Problem Fix

When a latent world model's predictive distribution is statistically inconsistent with actual
observation transitions (**falsification event**), standard models silently persist the wrong
dynamics hypothesis. FGLC detects falsification, identifies *which* grouped latent subspace
drives the planning failure via **causalized attention**, and applies **sparse residual
correction** only to that subspace, validated by necessity/sufficiency/counterfactual rollout.

## Core Equation Set

```
pθ(z_{t+1}|z_t,a_t,h_t) = N(μ_t, Σ_t)                   [base dynamics prior]
ρ_t = Σ_t^{-1/2}(z_{t+1} − μ_t)                          [standardized mismatch]
F_t^k = ||ρ_t^k||₂²,  F_t = Σ_k F_t^k                    [falsification scores]
β_t = sigmoid(MLP([F_1,...,F_K, F_t, h_t]))               [calibrated gate]
α_t = SparseAttention(ρ_t, z_t, a_t, h_t, ∇_z Q)         [group-level, value-aware]
δ_t^k = tanh(MLP([z_t^k, ρ_t^k, a_t, h_t])) · δ_max      [bounded correction]
μ̃_t^k = μ_t^k + β_t · α_t^k · δ_t^k                     [corrected dynamics]
```

## 44 Atomic Units — M↔R Cross-Validation Matrix

### main.md units (M-0..M-25)

| ID | Unit | Key claim | Linked R-units |
|---|---|---|---|
| M-0 | One-sentence problem fix | 4 sub-problems (detect/localize/correct/validate) | R-0, R-18 |
| M-1 | Base WM choice (TD-MPC2 vs Dreamer) | TD-MPC2 decoder-free hybrid recommended | R-11 |
| M-2 | Input data structure | ManiSkill state_dict, T=16~32 train horizon | R-13 |
| M-3 | Latent decomposition | K=6 groups, d=32; functional not semantic | R-4 |
| M-4 | Encoder | MLP D_x→256→K*d, LayerNorm, SiLU | R-4 |
| M-5 | Belief memory h_t | GRU on flatten(z)+a+r | R-11 |
| M-6 | Base dynamics prior | N(μ,diag(σ²)); group interaction transformer | R-4 |
| M-7 | Standardized mismatch | ρ_t = (z-μ)/σ; χ²/conformal calibration | R-7 |
| M-8 | Falsification gate β_t | sigmoid(MLP), calibrated; variance clamp | R-6 |
| M-9 | Causal attention α_t | group-level, sparse; entmax/sparsemax/top-k | R-0, R-3, R-4 |
| M-10 | Correction location | transition-adapter recommended: μ̃=μ+βαδ | R-1, R-9 |
| M-11 | Correction module Gψ | tanh bounding δ_max; correction-size penalty | R-2 |
| M-12 | Action/value relevance | Q-sensitivity, KL on policy, cause_score align | R-8 |
| M-13 | Necessity loss | L_nec = max(0, m - (L_without - L_with)) | R-1, R-3 |
| M-14 | Sufficiency loss | L_suf = |L_selected - L_full| | R-1, R-3 |
| M-15 | Random-mask contrast | L_rand = max(0, m - (L_random - L_selected)) | R-1, R-3 |
| M-16 | Total loss (10-term) | L_total = L_base + λ1..λ10 terms | — |
| M-17 | Training stages | Stage 1 base / Stage 2 freeze+correction / Stage 3 planner | — |
| M-18 | Planner MPPI/CEM | corrected rollout; H_corr=3~5 hold | R-15..R-17 |
| M-19 | Data split | ID + OOD-mass/friction/latency/noise/mixed | R-13 |
| M-20 | Modality progression | state-only → +RGB → RGB-D → DROID/Bridge | R-13 |
| M-21 | 7 inductive biases | grouped/sparse/bounded/temporal/action/nec-suf/OOD | — |
| M-22 | HiP-RSSM/PLSM differentiation | parameter inference vs sparse falsification-correction | R-11 |
| M-23 | Architecture spec | K=6,d=32,h=256,T=16,H_plan=5-15,δ_max=0.25 | — |
| M-24 | Training loop pseudocode | Stage-1,Stage-2,open-loop rollout | — |
| M-25 | Theory consolidation | F_t,β_t,α_t,μ̃_t invariants; min-objective | — |

### deep-research-report.md units (R-0..R-18)

| ID | Unit | Key insight | Linked M-units |
|---|---|---|---|
| R-0 | Attention-as-explanation critique | Jain&Wallace/Grimsley: surgical intervention needed | M-9 |
| R-1 | SCM/do-intervention/mediator | Gate m^(g) Bernoulli; τ_g interventional effect | M-10,13,14,15 |
| R-2 | Influence functions | Hessian-vector product; local sensitivity | M-11 |
| R-3 | Shapley/ASV | Interventional v(S); causal-order respect | M-9,13,14,15 |
| R-4 | iVAE/nonlinear ICA | Khemakhem: identifiable under auxiliary u | M-3,4,6,9 |
| R-5 | ICP/IRM/anchor regression | Invariance prior; IRM practical failures | M-22 |
| R-6 | Conformal prediction/CRC | Finite-sample coverage; online conformal | M-8 |
| R-7 | CUSUM/SPRT/BOCPD | Sequential change detection; classical baselines | M-7 |
| R-8 | Robust control/DRO | Value-aware loss; Wasserstein ambiguity | M-12 |
| R-9 | CIRCA algorithm | Bernoulli gate + conformal + α-distill + robust MPC | M-10 |
| R-10 | ASAP algorithm | Top-k + MC interventional ASV + α-distill | M-9 |
| R-11 | I3G algorithm | iVAE + ICP/anchor + SPCI gate + sparse group gates | M-5,22 |
| R-12 | IVI algorithm | Influence-rank + knockout + sparse α-distill | M-11 |
| R-13 | Datasets | ManiSkill/robosuite/DROID/BridgeData V2 | M-2,19,20 |
| R-14 | 4-axis metrics | Prediction/detection/attribution/behavior | M-22 |
| R-15 | Causal graph | encoder→pred→mismatch→trigger→gate→corrected→planner | M-18 |
| R-16 | Training pipeline | base→identifiable→randomized→ASV→distill→calibrate→plan | M-17 |
| R-17 | Inference decision flow | calibrated gate→top-k→effect-eval→value-check→robust MPC | M-18 |
| R-18 | Open questions | latent surgery realism / conformal-causal gap / action relevance | M-0 |

## Navigation Guide

For implementation tasks, read units in this order:
1. This file (navigation)
2. `01_PROBLEM_FORMULATION.md` (start here)
3. `04_BASE_WORLD_MODEL.md` → `02_FALSIFICATION_THEORY.md` → `06_CAUSAL_ATTENTION.md` → `07_CORRECTION_MECHANISM.md`
4. `13_ALGORITHM_CIRCA.md` (primary algorithm)
5. `19_BASELINES.md` + `20_ABLATIONS.md` + `21_METRICS.md` (evaluation)

For paper framing: `22_NOVELTY_AND_THREATS.md` → `25_PAPER_TITLE_CONTRIBUTIONS.md`
For checkpoints summary: `26_CROSSCHECK_SUMMARY.md`

## Checkpoint Status (session 2026-05-22)

Cluster 1 (M-0, R-0, R-18): Agent team T1 review — IN PROGRESS
Cluster 2 (M-1..M-6, R-4): PENDING
Cluster 3 (M-7, M-8, R-6, R-7): Agent team T1 review — IN PROGRESS
Cluster 4 (M-9..M-11, R-1..R-3, R-9..R-12): PENDING
Cluster 5 (M-12..M-15): PENDING
Cluster 6 (M-16..M-18, M-23..M-25, R-15..R-17): PENDING
Cluster 7 (M-19..M-22, R-5, R-8, R-13, R-14): PENDING

Note: All docs/idea/ files scaffold content from main.md + deep-research-report.md.
Full C1..C10 checkpoint verdicts require per-cluster agent team execution.
