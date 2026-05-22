# 01_PROBLEM_FORMULATION

## Source
- main.md §0 — one-sentence problem fix, 4 sub-problems
- deep-research-report.md §요약, §무엇이 attention을 explanation에서 intervention으로 바꾸는가

## Claim

Current latent world models suffer from **wrong-dynamics-hypothesis persistence**: when
physical parameters shift (mass/friction/latency/noise/action-gain), the model continues
generating predictions from the wrong dynamics distribution, and planning degrades silently.

FGLC addresses four coupled sub-problems:
1. **Is the current world model wrong?** → Standardized mismatch + falsification gate
2. **Which part of the latent space is wrong?** → Causalized group-level attention
3. **How much correction is needed?** → Bounded sparse residual correction module
4. **Does correction actually help planning?** → Value/return improvement validation

## Mathematical Formalization

```
Define: z_t = [z_t^1,...,z_t^K] ∈ R^{K×d}  [K=6 grouped latent tokens]
        pθ(z_{t+1}|z_t,a_t,h_t) = N(μ_t, diag(σ_t²))  [base dynamics prior]
        ρ_t = Σ_t^{-1/2}(z_{t+1} - μ_t)  [standardized mismatch]

Falsification event: ||ρ_t||² exceeds calibrated ID-distribution threshold
Goal: find sparse α_t ∈ Δ^K (attention over K groups) and δ_t^k (correction)
      such that μ̃_t = μ_t + β_t Σ_k α_t^k δ_t^k maximizes value improvement
      subject to ||α||_0 ≤ k (sparsity) and ||δ^k|| ≤ δ_max (boundedness)
```

**Critical distinction from attention-as-explanation**: Standard attention (Jain & Wallace 2019)
cannot be claimed as causal. FGLC attention α_t is a **correction gate policy** — it specifies
which latent groups to intervene on. Causality is validated via necessity/sufficiency/counterfactual
losses, not just the attention weights themselves (Grimsley et al.: surgical intervention required).

## Connection Map
- Upstream: docs/main/main.md §0 (source)
- Downstream: M-7 (mismatch), M-8 (β gate), M-9 (attention), M-10..M-11 (correction)
- Algorithm: R-9 (CIRCA), R-1 (SCM/do-intervention)

## Checkpoints

- C1 Math validity: **CONDITIONAL** — Attention-causality conflation risk. The dynamics
  interaction block (self-attention in §4.3) and the correction attention are distinct modules.
  The problem description must clearly separate (a) mismatch score locates group (F_t^k ranking)
  from (b) correction gate applies residual. "Causalized attention" label requires operational
  definition: it is a correction gate policy, not a causal attribution mechanism.
  agent_report: see mathematical-validity-critic result 2026-05-22
- C2 Novelty: PENDING (cluster review required — see 22_NOVELTY_AND_THREATS.md)
- C3 Reviewer attack: PENDING (reviewer-2-attack-agent in progress)
- C4 Feasibility: CONDITIONAL — ManiSkill state-only Phase 1 feasible on single A100;
  modality extension (RGB-D, DROID) requires Phase 2+. State-only baseline sufficient for
  first submission claim.
- C5 Claim-metric alignment: CONDITIONAL — 4 sub-problems each map to a metric axis
  (prediction NLL / detection AUROC / attention necessity-sufficiency / return recovery).
  All 4 must be measured together; NLL alone is insufficient claim evidence.
- C6 Impl risk: PENDING
- C7 Experiment design: PENDING
- C8 Failure interp: Two key failure modes documented in 23_FAILURE_MODES.md:
  (a) correction module too strong → base WM doesn't learn; (b) attention = shortcut.
- C9 Related work: PENDING (MCP cross-check required)
- C10 Context routing: Source = main.md §0, deep-research-report.md §요약.
  Downstream consumers: 02_FALSIFICATION_THEORY.md, 06_CAUSAL_ATTENTION.md,
  07_CORRECTION_MECHANISM.md, 09_NECESSITY_SUFFICIENCY.md.

## Open Questions
- R-18: Does latent surgery stay on the valid representation manifold?
- R-18: Can conformal coverage be maintained for causal claims simultaneously?
- R-18: What is the minimum correction size that produces action-relevant change?
