# 24_OPEN_QUESTIONS

## Source
- main.md §마지막 핵심 정리
- deep-research-report.md §R-18 (open questions), §한계와 열린 질문

## Categorized Open Questions

### Q1: Latent Surgery Realism (HIGH PRIORITY)
Does the corrected latent z̃_t = z_t + m ⊙ δ stay on the valid latent manifold?

If correction vectors push z̃ outside the distribution of E(x_t) for any x_t, then:
- The corrected prediction μ̃_t may be in "fantasy" latent space
- The planner may optimize for trajectories that are meaningless under the actual dynamics
- τ_g estimation (CIRCA) may be off-manifold

**Mitigation explored**: Low-rank correction (δ in low-rank subspace of base WM's null space);
retrieval-based correction (nearest valid latent in training set); energy-based constraint.

**Status**: Unresolved. Requires empirical validation: is corrected z̃ still encodable by E?
Check: ||z̃_t - E(D(z̃_t))|| (round-trip check if decoder available) or nearest-neighbor 
distance in training latent distribution.

### Q2: Conformal-Causal Gap (HIGH PRIORITY)
Conformal falsification gives coverage guarantees. Causal attribution (τ_g) gives ATE.
These are separate guarantees that cannot substitute for each other:
- Conformal says: "we report a mismatch with ≤ α false alarm rate"
- τ_g says: "intervening on group k changes utility by τ_g"

These must be maintained as separate, complementary components. Conflating them (e.g., claiming
conformal gate provides causal detection) is a formal error.

**Status**: Design decision needed. Separate conformal gate (for detection) from τ_g estimation
(for group selection). Do NOT claim conformal coverage for the group selection step.

### Q3: Action Relevance Preservation Under Correction
If correction improves prediction accuracy but changes the policy distribution in unexpected ways:
- Corrected planner may select actions that are locally optimal for the corrected dynamics
  but globally suboptimal (planning horizon too short to see long-term effects)
- L_value with n-step TD target (n=5) may not capture long-horizon consequences

**Status**: Requires long-horizon planning experiments (H=20+) to validate.

### Q4: Sparse Attention vs. Soft Attention Under High K
With K=6 and entmax/sparsemax, exactly 1-2 groups receive non-zero attention.
Under OOD-mixed (mass + friction + action-gain simultaneously), 3+ groups should activate.
But sparse attention may suppress the correct multi-group signal.

**Status**: Tension between sparsity (interpretability) and coverage (multi-factor OOD).
ASAP algorithm (Shapley coalition) is designed to handle this. CIRCA τ_g may also estimate
interactions via multi-group intervention sets.

### Q5: Real Robot Applicability
ManiSkill/robosuite: controlled sim with known physics. DROID/BridgeData: real robot data.
In real robot:
- regime_id never available
- ground-truth mass/friction unknown (so mask precision/recall metrics not computable)
- latent correction may amplify real-world sensor noise

**Status**: Real robot evaluation (R12-DROID/BridgeData) will require new metric design:
without ground-truth factors, focus on return/recovery/compute metrics only.

### Q6: 2025/2026 Novelty Threats
Recent papers on "world model correction robotics" need to be checked.
See 22_NOVELTY_AND_THREATS.md for pending MCP search.

## Connection Map
- Sources: deep-research-report.md §한계와 열린 질문 (R-18)
- Downstream: 26_CROSSCHECK_SUMMARY.md (open question tracking)
- Review: reviewer2_attack_fglc_R1.md (Attacks 1,3,4,5 map to Q1,Q4,Q2,Q3 respectively)
