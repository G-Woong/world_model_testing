# FGLC — Idea Documentation (TOC)

This file is a table-of-contents pointer. The actual idea content is in `docs/idea/`.

## Navigation

Start here: `docs/idea/00_OVERVIEW.md`

## All Idea Units (27 files)

| File | Content |
|---|---|
| 00_OVERVIEW.md | Navigation map, 44-unit M↔R matrix, checkpoint status |
| 01_PROBLEM_FORMULATION.md | 4 sub-problems, intervention-policy framing |
| 02_FALSIFICATION_THEORY.md | Standardized mismatch, β gate, conformal vs CUSUM |
| 03_LATENT_DECOMPOSITION.md | K=6 grouped tokens, iVAE identifiability |
| 04_BASE_WORLD_MODEL.md | TD-MPC2 base, encoder, GRU belief, dynamics transformer |
| 05_BELIEF_MEMORY.md | GRU h_t, HiP-RSSM comparison |
| 06_CAUSAL_ATTENTION.md | Intervention-policy α_t, sparse softmax/entmax |
| 07_CORRECTION_MECHANISM.md | Transition adapter μ̃=μ+βαδ, tanh bounding |
| 08_ACTION_VALUE_RELEVANCE.md | Q-sensitivity, value consistency loss |
| 09_NECESSITY_SUFFICIENCY.md | L_nec, L_suf, L_rand training losses |
| 10_LOSS_DESIGN.md | 10-term total loss, staged λ schedule |
| 11_PLANNING_THEORY.md | MPPI/CEM corrected rollout, robust MPC, H_corr=3~5 |
| 12_TRAINING_STAGES.md | Stage 1-4 training protocol, freeze strategy |
| 13_ALGORITHM_CIRCA.md | CIRCA: Bernoulli gate + conformal + τ_g distill + robust MPC |
| 14_ALGORITHM_ASAP.md | ASAP: top-k + MC interventional ASV + α-distill |
| 15_ALGORITHM_I3G.md | I3G: iVAE + ICP/anchor + SPCI + sparse group gates |
| 16_ALGORITHM_IVI.md | IVI: influence-rank + randomized knockout + sparse α |
| 17_ALGORITHM_COMPARISON.md | 4-algorithm cross-table: validity/calibration/cost/wins |
| 18_DATA_BENCHMARKS.md | ManiSkill OOD splits, data rules (FRAGILE) |
| 19_BASELINES.md | Must-not-disappear baselines (FRAGILE SSoT) |
| 20_ABLATIONS.md | 11 ablation families (FRAGILE SSoT) |
| 21_METRICS.md | 4-axis metric suite |
| 22_NOVELTY_AND_THREATS.md | Direct threats table, 2025/2026 sweep (PENDING MCP) |
| 23_FAILURE_MODES.md | 8 failure modes with mitigations |
| 24_OPEN_QUESTIONS.md | 6 unresolved questions |
| 25_PAPER_TITLE_CONTRIBUTIONS.md | Title, contributions, abstract draft |
| 26_CROSSCHECK_SUMMARY.md | C1..C10 checkpoint matrix summary |

Checkpoint status: Clusters 1+3 reviewed (2026-05-22). Clusters 2,4,5,6,7 + MCP pending.
