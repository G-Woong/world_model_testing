# 08_ACTION_VALUE_RELEVANCE

## Source
- main.md §10 (action/value relevance)
- deep-research-report.md §Robust control·DRO·value-aware loss (R-8)

## Claim

Correction attention must be guided by **action/value relevance**, not just prediction error.
A world model can have high prediction error in irrelevant latent dimensions without affecting
planning. Conversely, small mismatch in action-relevant subspaces can collapse return.
L_value and cause_score alignment ensure correction is value-aware.

## Mathematical Formalization

```
Value/reward heads:
  r̂_t = Rθ(flatten(z_t), a_t, h_t)
  Q̂_t = Qθ(flatten(z_t), a_t, h_t)

Action relevance per group k:
  (a) Value sensitivity:  A_k = |V(z̃_t^{(k)}) - V(z_t)|
  (b) Policy KL divergence: P_k = D_KL(π(·|z̃_t^{(k)}) || π(·|z_t))

Cause score (pseudo-target for attention):
  cause_score_k = standardized_mismatch_k × action_relevance_k × temporal_consistency_k

Attention alignment loss:
  L_attn_align = KL(stopgrad(normalize(cause_score)) || α_t)
  NOTE: cause_score is a pseudo-target, not ground truth

Value consistency loss (n-step TD):
  G_t = r_t + γ r_{t+1} + ... + γ^n V(z_{t+n})
  L_value = ||V(z̃_t) - G_t||²
```

**Why value-aware?** Without L_value, correction maximizes prediction accuracy at
the cost of planning performance. A model that predicts "friction = 1.0" when true
friction = 0.5 will show high prediction NLL — but this may not change the optimal
action for certain task+state combinations. L_value forces correction to matter for control.

## Connection Map
- Upstream: M-7 (mismatch score), M-9 (α_t), M-10 (correction δ_t)
- Downstream: M-13..M-15 (nec/suf/contrast), M-16 (total loss)
- Algorithm: R-8 (robust control value-aware loss), R-9 (CIRCA -ξ·ΔQ_robust term)

## Checkpoints

- C1 Math validity: CONDITIONAL — cause_score is a pseudo-target (not ground truth).
  The claim that cause_score = mismatch × action_relevance × temporal_consistency is an
  empirically motivated formula, not derivable from first principles.
- C2 Novelty: CONDITIONAL — Value-aware world model correction has precedent (TD-MPC2).
  Novel combination: value-guided attention selection + group-level correction.
- C3 Reviewer attack: MEDIUM — "Why not just maximize return directly without the WM?"
  Answer: WM enables multi-step planning under shift; direct policy gradient doesn't generalize to OOD.
- C4 Feasibility: PASS — Q-sensitivity computation is a forward pass; KL divergence is standard.
- C5 Claim-metric: Required: show L_value ablation (no-value) degrades return but not NLL.
  This demonstrates value-aware selection adds something beyond pure prediction correction.
- C6 Impl risk: LOW — standard TD loss; Q-head is a small MLP.
- C7 Experiment design: Required ablation: no-value (L_value = 0).
  Hypothesis: without L_value, prediction NLL improves but return degrades.
- C8 Failure interp: If no-value ablation matches FGLC on return: value-aware correction
  doesn't add above pure prediction correction. Implication: reduce claim to "prediction recovery."
- C9 Related work: TD-MPC2 (value-aware latent planning), DRO literature — PENDING ≥2 sources
- C10 Context routing: Source = main.md §10. Downstream: 09_NECESSITY_SUFFICIENCY.md, 10_LOSS_DESIGN.md
