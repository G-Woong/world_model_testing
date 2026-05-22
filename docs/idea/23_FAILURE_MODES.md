# 23_FAILURE_MODES

## Source
- main.md §23 (failure patterns to avoid)
- docs/orchestration/agent_reports/synthesis/2026-05/reviewer2_attack_fglc_R1.md

## 5 Core Failure Modes (from main.md)

### Failure 1: Correction Module Too Strong
**Pattern**: Base WM learns nothing; correction module absorbs all dynamics.

**Detection**: Stage 1 NLL doesn't decrease without correction; Stage 2 correction size > δ_max;
β_t fires on ID data > 20% of timesteps.

**Mitigation**:
- Staged training (freeze base in Stage 2)
- δ_max clamp (δ_max = 0.1 initially, increase only if Stage 1 converges)
- L_corr_size penalty
- β_t gate (correction only when falsification detected)

### Failure 2: Attention = Shortcut (Not Selective)
**Pattern**: α_t always selects same 1-2 groups regardless of OOD type.

**Detection**: Attention entropy very low across all OOD conditions; ABL-04 (random mask) ≈ FGLC.

**Mitigation**:
- L_entropy penalty (prevents always-selecting)
- Verify per-OOD-type attention distribution differs
- Necessity test: removing same group should hurt in DIFFERENT OOD conditions

### Failure 3: σ Inflation (Variance Collapse Escape)
**Pattern**: Model learns large σ_t to make all mismatch appear "within uncertainty."

**Detection**: ECE plot for σ shows overconfidence; OOD AUROC → 0.5; σ_t >> data std.

**Mitigation**:
- L_cal = mean(log σ_t)² penalty
- σ clamp: σ_min=1e-3, σ_max=3.0
- Monitor σ_t during training; STOP if σ_t > 2× data std

### Failure 4: Latent Group Collapse (Groups Learn Same Representation)
**Pattern**: All K groups encode similar features; group interaction doesn't distinguish groups.

**Detection**: Cosine similarity between group representations > 0.9; ABL-08 (K=1) ≈ FGLC.

**Mitigation**:
- Per-group dynamics head (forces groups to predict different aspects)
- Group-separation regularization (optional: L_2,1 sparse group lasso)
- K sensitivity ablation to find right K

### Failure 5: Prediction Improves But Control Doesn't
**Pattern**: Corrected NLL improves but return/recovery unchanged.

**Detection**: Stage 2 shows corrected NLL < uncorrected NLL but closed-loop return ≈ TD-MPC2 baseline.

**Mitigation**:
- L_value (value-aware correction)
- L_attn_align (cause_score alignment)
- Increase planning horizon H_corr (short-horizon hold may be too short)
- Check that MPPI samples corrected dynamics (not just base dynamics)

## Reviewer-2 Additional Failure Modes

### Failure 6: Causal Attention Label Causes Sustained Reviewer Skepticism
**Pattern**: Paper uses "causal attention" but cannot pass Jain-Wallace manipulation test.

**Mitigation**: Rename to "intervention-policy attention" OR run τ_g randomized intervention
experiment (CIRCA algorithm required for this defense).

### Failure 7: K=6 Groups Are Seed-Dependent
**Pattern**: Cross-seed Spearman < 0.7 for per-OOD attention vectors.

**Mitigation**: Run 5-seed experiment; if < 0.7, reduce K or add explicit group-separation loss.

### Failure 8: Compute-Matched Baseline Matches FGLC
**Pattern**: BASE-COMP-04 (compute-matched random realloc) ≈ FGLC return.

**Mitigation**: This is a HARD reduction. Reduce claim to "FGLC achieves same performance with
fewer correction evaluations" (efficiency claim). Cannot claim "correction improves planning."

## Connection Map
- Sources: main.md §23, reviewer2_attack_fglc_R1.md
- Downstream: 24_OPEN_QUESTIONS.md, 26_CROSSCHECK_SUMMARY.md
