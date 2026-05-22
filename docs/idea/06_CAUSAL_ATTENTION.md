# 06_CAUSAL_ATTENTION

## Source
- main.md §7 (custom attention design)
- deep-research-report.md §R-0 (attention critique), §R-3 (Shapley/ASV), §R-9 (CIRCA)

## Claim

The correction attention α_t is an **intervention-policy** (NOT a causal attributor).
High α_t^k means "intervening on group k actually changes planning utility" — validated by
randomized intervention experiments (τ_g utility effect estimation), not just attention visualization.
This is operationally distinguishable from standard softmax attention.

**Terminology decision**: Per reviewer-2-attack-agent Attack 1, the term "causal attention"
must either be renamed to "intervention-policy attention" OR backed by the full τ_g randomized
intervention experiment (CIRCA-style). The paper must choose one of these paths.

## Mathematical Formalization

```
Correction attention query:
  context_t = [flatten(ρ_t), flatten(σ_t), a_embed, h_t, value_signal, history_embed]
  
Group token keys:
  group_token_k = concat(z_t^k, ρ_t^k, σ_t^k)
  K_k = W_K @ group_token_k
  
Query:
  q = W_Q @ context_t

Raw attention weights:
  ẽ_k = q · K_k / sqrt(d)
  
Sparse attention (recommended progression):
  Phase 1: α_k = softmax(ẽ) + L_entropy penalty
  Phase 2: entmax/sparsemax(ẽ)  [exact zeros for non-selected groups]
  Phase 3: top-k Gumbel mask  [hard selection]

Intervention-policy formulation (CIRCA-style, for validity defense):
  m_t^k ~ Bernoulli(α_t^k)   [during training: randomized gate]
  τ̂_g = E[U_t|do(m^k=1)] - E[U_t|do(m^k=0)]  [estimated via IPW or DR]
  L_alignment = ||α - Normalize(τ̂_+)||²   [align attention with positive utility effects]
```

## Attention-as-Explanation Critique (Jain & Wallace 2019)

Standard attention fails three causal criteria (Grimsley et al.):
1. Different attention distributions → same prediction (not unique)
2. Removing high-attention tokens → small effect (not necessary)
3. No surgical intervention defined

FGLC response: α_t is NOT explaining predictions, it is selecting a correction intervention.
The L_nec loss validates necessity. The L_suf loss validates sufficiency. The τ_g estimation
validates that high-α groups have positive interventional utility. Together, these constitute
an operationally validated intervention policy, not just attention.

## Connection Map
- Upstream: M-7 (ρ_t input), M-8 (β_t gates the attention), R-0 (attention critique), R-3 (Shapley)
- Downstream: M-10 (correction uses α_t), M-13..M-15 (nec/suf/contrast use α_t)
- Algorithm: R-9 (CIRCA adds τ_g estimation), R-10 (ASAP adds ASV estimation)

## Checkpoints

- C1 Math validity: CONDITIONAL — Attention formulation is valid but "causal" label is
  mathematically unjustified without τ_g randomized intervention experiment.
  Required: either rename or add CIRCA-style τ_g training. See math-validity-critic report.
- C2 Novelty: CONDITIONAL — Sparse attention for correction is not novel alone.
  The intervention-policy framing + L_nec/L_suf + τ_g alignment is the differentiator.
  Check: no prior work combining all three in a world model context.
- C3 Reviewer attack: HIGH — Attack 1 (causal attention critique) is the highest-risk attack.
  Defense requires τ_g experiment or terminology change. See reviewer2_attack_fglc_R1.md.
- C4 Feasibility: CONDITIONAL — entmax/sparsemax available as libraries; top-k Gumbel needs
  custom implementation. τ_g estimation adds ~20% training overhead. Feasible.
- C5 Claim-metric: Attention claim validated by: (1) necessity test (AUROC on group selection),
  (2) sufficiency test, (3) τ_g significance (p<0.05 per group), (4) Jain-Wallace adversarial test.
- C6 Impl risk: MEDIUM — entmax library dependency; Gumbel-softmax gradient stability.
- C7 Experiment design: Required: ABL-no-attention (uniform α=1/K). Must show FGLC > uniform-α
  on return/recovery with effect size > 0.3σ.
- C8 Failure interp: If ABL-no-attention matches FGLC: attention module adds nothing.
  Implication: claim reduces to "gated residual correction" without group selection.
- C9 Related work: Jain & Wallace (2019), Wiegreffe & Pinter (2019), entmax (Peters et al.) — PENDING
- C10 Context routing: Source = main.md §7, deep-research-report.md §R-0,R-3.
  Downstream: 07_CORRECTION_MECHANISM.md, 13_ALGORITHM_CIRCA.md
