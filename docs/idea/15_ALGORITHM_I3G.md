# 15_ALGORITHM_I3G — Identifiable Invariant Intervention Gates

## Source
- deep-research-report.md §I3G (R-11), §iVAE/nonlinear ICA (R-4), §ICP/IRM/anchor (R-5)

## Priority: 2

## Claim

I3G makes latent groups identifiable and invariant by combining iVAE-style context-conditioned
priors with ICP/anchor regression invariance penalties. This provides the strongest theoretical
guarantee for *which* group corresponds to *which* type of physical shift, at the cost of
requiring auxiliary context variable u_t (task ID or domain ID).

## Mathematical Formalization

```
Context-conditioned prior (iVAE-inspired):
  p_θ(z_t | u_t) = Π_k p_θ(z_t^k | u_t)   [auxiliary var u_t: task/domain/time context]

I3G Total Loss:
  L = L_wm
    + λ_id   L_iVAE        [identifiability: ELBO with factored prior]
    + λ_inv  L_ICP_anchor  [invariance: residuals consistent across environments]
    + λ_s    ||m||_{2,1}   [sparse group gates]

iVAE Loss:
  L_iVAE = ELBO(z_t | x_t, u_t) with p_θ(z_t^k | u_t) = ExpFam(λ_k(u_t))

Invariance Loss (ICP/anchor variant):
  L_ICP = Σ_env_e Var_e[residual(z_t^k; causal_S)] - E[residual^2(z_t^k; causal_S)]
  (penalizes variance of residuals across environments)

I3G Training:
  1. Learn context-conditioned latent model z_t with auxiliary u_t
  2. Apply invariant penalty across environments (different OOD conditions as environments)
  3. Learn sparse group gates only over invariant/identifiable groups
  4. Calibrate sequential residual detector (SPCI or CUSUM)

I3G Inference:
  1. Detect mismatch with calibrated gate
  2. Prefer updating context/hidden-parameter groups before state groups (causal priority)
  3. Plan with corrected context-conditioned model
```

## When I3G Wins (vs. CIRCA)

I3G has the strongest interpretability: when mass shifts, z^context (identifiable by u_t) 
activates consistently across seeds. In sim where ground-truth physical factors are known,
I3G should have highest mask precision/recall vs. changed factor.

Expected superiority: sim evaluation where ground-truth causal factor known + good u_t.
Expected weakness: real robot where u_t is unavailable or noisy.

## Connection Map
- Upstream: R-4 (iVAE), R-5 (ICP/anchor), R-11 (SPCI), M-3 (latent decomposition)
- Algorithm peers: 13_ALGORITHM_CIRCA.md, 14_ALGORITHM_ASAP.md, 16_ALGORITHM_IVI.md
- Downstream: 17_ALGORITHM_COMPARISON.md

## Checkpoints

- C1 Math validity: CONDITIONAL — iVAE identifiability requires auxiliary variable u_t with
  sufficient variation. In ManiSkill, u_t = task condition (mass/friction value) would provide
  this — BUT using mass/friction label as u_t at training time contradicts "no regime label at
  inference" policy. Conflict: iVAE needs regime context at training, not inference.
  Resolution: u_t = time-of-episode index (weak auxiliary) or task-type (PickCube vs PushCube).
  This weakens identifiability guarantee but may still improve group consistency.
- C2 Novelty: CONDITIONAL — iVAE + ICP + sparse gates combination is not standard.
  Closest: HiP-RSSM (context-RSSM); differentiation: FGLC uses sparse correction gates.
- C3 Reviewer attack: HIGH — "Requires regime labels at training (u_t = mass/friction)."
  This violates the no-oracle-label principle. Defense: u_t = task type (not physical params),
  which is observable. Requires clarification in paper.
- C4 Feasibility: CONDITIONAL — iVAE ELBO with factored prior adds complexity. ICP across
  OOD conditions requires multi-environment batching. ~3× more complex than CIRCA.
- C5 Claim-metric: Sim ground-truth: mask precision/recall vs. changed factor (mass shift →
  z^context activated; friction shift → z^contact activated). I3G should be best here.
- C6 Impl risk: HIGH — iVAE factored prior + ICP multi-env training needs careful batching.
- C7 Experiment design: Sim evaluation with ground-truth factor oracle. Compare I3G attention
  activation vs. changed physical parameter. Precision/recall per group per OOD type.
- C8 Failure interp: If I3G doesn't have better mask precision than CIRCA: identifiability
  assumptions not satisfied by available auxiliary signals. Reduce I3G to ablation.
- C9 Related work: Khemakhem et al. (2020) iVAE; Peters et al. (2016) ICP — PENDING ≥2 sources
- C10 Context routing: Source = deep-research-report.md §I3G. Downstream: 17_ALGORITHM_COMPARISON.md
