# 03_LATENT_DECOMPOSITION

## Source
- main.md §3 (latent decomposition, grouped tokens)
- deep-research-report.md §iVAE·nonlinear ICA·disentanglement (R-4)

## Claim

Latent space must be grouped into K functional subspaces rather than a single unstructured vector.
This is NOT a claim of semantic ground-truth disentanglement (Locatello impossibility), but a
claim that **functional grouping + group-level correction** is more stable than scalar-level correction,
and that group assignments are consistent across seeds under controlled OOD variation.

## Mathematical Formalization

```
z_t = [z_t^1, ..., z_t^K] ∈ R^{K×d}  [K=6, d=32; total latent = 192]

Recommended functional groups (NOT ground-truth semantic labels):
  z^1 ∈ R^32  # robot proprioception/motion subspace
  z^2 ∈ R^32  # object pose/velocity subspace
  z^3 ∈ R^16  # contact/interaction subspace
  z^4 ∈ R^16  # action-gain/effect subspace
  z^5 ∈ R^16  # context/hidden-regime subspace
  z^6 ∈ R^16  # reward/goal/task-value subspace

Attention over groups: α_t ∈ R^K (not scalar-dimension α ∈ R^{K*d})
→ Prevents permutation sensitivity, improves interpretability of correction mask

iVAE-inspired auxiliary: p(z|u) = Π_k p(z^k|u) where u = task/domain context
→ Enables identifiability of group assignments under context variation (R-11/I3G)
```

**Locatello critique**: Without auxiliary signals or explicit inductive bias,
group factorization is fundamentally unidentifiable. FGLC claims:
(1) functional consistency across seeds under same OOD type (empirical check)
(2) group lasso / per-group dynamics head creates implicit separability bias
(3) For I3G algorithm: explicit iVAE prior enforces identifiability

## Connection Map
- Upstream: M-4 (encoder produces z_t), R-4 (iVAE/identifiability)
- Downstream: M-6 (dynamics per group), M-9 (attention over K groups), M-10 (correction per group)
- Algorithm link: R-11 (I3G uses iVAE + ICP for identifiable groups)

## Checkpoints

- C1 Math validity: CONDITIONAL — Locatello impossibility applies to unsupervised case.
  Claims must be restricted to "functional consistency" not "ground-truth disentanglement."
  iVAE claim is valid ONLY for I3G algorithm variant with task context u.
- C2 Novelty: PENDING — HiP-RSSM uses context-conditioned latent parameters; differentiation
  needed (K-group functional grouping vs. parameter inference)
- C3 Reviewer attack: HIGH RISK — Attack 3 from reviewer-2-attack-agent:
  "K=6 grouping is arbitrary." Defense: functional not semantic claim; cross-seed consistency.
  Verification: 5-seed Spearman > 0.7 for per-OOD attention vectors
- C4 Feasibility: PASS — K=6, d=32 gives 192-dim latent; comparable to TD-MPC2 default.
  MLP encoder feasible on A100 for state-only ManiSkill.
- C5 Claim-metric: CONDITIONAL — K ablation (K=3,6,12) required to validate K=6 choice.
  Also: cross-seed consistency metric for group stability.
- C6 Impl risk: LOW — Group splitting is a reshape operation; no special architecture needed.
- C7 Experiment design: Required: K ablation sweep + collapsed-K=1 ablation (see 20_ABLATIONS.md)
- C8 Failure interp: Latent group collapse (all groups learn same representation) detected by
  cosine similarity between group representations; mitigation: per-group dynamics head.
- C9 Related work: Locatello et al. (2019) PMLR; iVAE Khemakhem et al. (2020) — PENDING ≥2 sources
- C10 Context routing: Source = main.md §3. Consumers: 04_BASE_WORLD_MODEL.md, 06_CAUSAL_ATTENTION.md

## Open Questions
- What is the right K? Too small: can't represent diverse shift types. Too large: attention too sparse.
- Do we need explicit group-separation loss or is per-group dynamics head sufficient?
- For RGB-D extension: should visual tokens be their own group or merged with existing groups?
