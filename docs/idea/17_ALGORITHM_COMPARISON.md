# 17_ALGORITHM_COMPARISON

## Source
- deep-research-report.md §이론 점검을 통과하는 알고리즘 골격, §우선순위

## Claim

The 4 FGLC algorithms (CIRCA, I3G, ASAP, IVI) cover different points in the
interventional validity / statistical calibration / action relevance / compute cost space.
All 4 must be compared on identical benchmarks sharing identical Stage 1 base WM weights.

## 4-Algorithm Cross-Table

| Property | CIRCA | ASAP | I3G | IVI |
|---|---|---|---|---|
| Priority | 1 | 3 | 2 | 4 |
| Intervention validity | Strong (τ_g ATE) | Strong (ASV coalition) | Medium-strong (iVAE+ICP) | Medium (local influence) |
| Statistical calibration | Conformal (finite-sample) | Conformal | SPCI/CUSUM | Calibrated gate |
| Action relevance | Yes (robust MPC -ξΔQ) | Yes (interventional v(S)) | Yes (value-aware planner) | Yes (value-aware loss) |
| Compute cost | Medium | High | Medium-High | Low |
| Expected wins | Detection+recovery | Multi-factor OOD | Sim attribution | Real-time deployment |
| Key weakness | Off-manifold intervention | Too slow for real-time | Needs u_t auxiliary | Large shifts |

## Algorithm Selection Guide

```
Deployment scenario:
  Research understanding + causal attribution → I3G (strongest identifiability)
  High correctness + time budget → ASAP (strongest coalition interactions)
  Primary method (paper claim) → CIRCA (best balance: validity+calibration+action)
  Real-time / low compute → IVI

Benchmarking requirement:
  All 4 algorithms must share IDENTICAL Stage 1 base WM weights
  Stage 2 training: algorithm-specific (CIRCA gets τ_g, ASAP gets ASV, etc.)
  Evaluation: same metric suite (21_METRICS.md §4-axis metrics)
```

## Expected Experimental Results

Based on deep-research-report.md §실험 설계와 벤치마크 §알고리즘별 기대 결과:

| Scenario | Best | 2nd | 3rd | Worst |
|---|---|---|---|---|
| Detection+recovery curves | CIRCA | I3G | IVI | ASAP |
| Interaction-heavy OOD-mixed | ASAP | CIRCA | I3G | IVI |
| Attribution precision (sim oracle) | I3G | CIRCA | ASAP | IVI |
| Compute efficiency (return/compute) | IVI | CIRCA | I3G | ASAP |
| Large shift (2× mass) | CIRCA | I3G | ASAP | IVI |

## Connection Map
- Upstream: 13,14,15,16 (all 4 algorithms)
- Downstream: 19_BASELINES.md, 20_ABLATIONS.md, 21_METRICS.md
- Paper: 25_PAPER_TITLE_CONTRIBUTIONS.md (CIRCA = primary contribution)

## Checkpoints

- C1 Math validity: N/A — This is an expected-results prediction, not a mathematical claim.
- C2 Novelty: CONDITIONAL — The 4-algorithm comparison framework itself is a contribution
  (systematic study of intervention validity / calibration tradeoffs in WM correction).
- C3 Reviewer attack: MEDIUM — "Why not just use ASAP for everything?"
  Defense: ASAP is prohibitively expensive for real-time; CIRCA is the deployable algorithm.
- C4 Feasibility: CONDITIONAL — Running all 4 algorithms on 3 tasks × 5 OOD conditions:
  ~4 algorithm × 3 tasks × 5 OOD = 60 eval runs. Significant compute. Plan: run CIRCA+IVI first,
  add ASAP+I3G if budget allows.
- C5 Claim-metric: All 4 must be evaluated on the same 4-axis metric suite.
- C6 Impl risk: HIGH — 4 separate training procedures on shared base. Version control required.
- C7 Experiment design: Shared Stage 1 → algorithm-specific Stage 2 → identical eval protocol.
- C8 Failure interp: If CIRCA < IVI across all conditions: randomized interventions add overhead
  without benefit. Reduce to IVI + CIRCA (2 algorithm comparison).
- C9 Related work: N/A (comparison section)
- C10 Context routing: Source = deep-research-report.md §우선순위. Consumers: 25_PAPER_TITLE..., 19_BASELINES.md
