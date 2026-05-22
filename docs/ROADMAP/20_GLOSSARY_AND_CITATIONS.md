# Glossary and Citations

## Term SSoT (Terms Must Be Preserved)

These terms are defined here. Do not rename in any code, doc, or paper section.

| Term | Definition |
|---|---|
| falsification gate | Calibrated sigmoid MLP β_t detecting when predictive distribution is statistically inconsistent with observations |
| standardized mismatch | ρ_t = Σ_t^{-1/2}(z_{t+1}-μ_t); per-group normalized residual under base WM |
| latent group | One of K functional latent subspaces z^k ∈ R^d; not ground-truth semantic factors |
| intervention-policy attention | α_t; group-level sparse attention validated as correction intervention policy (not causal attributor) |
| sparse correction | μ̃_t^k = μ_t^k + β_t α_t^k δ_t^k; correction applied only to selected groups |
| necessity | L_nec: removing selected mask worsens performance |
| sufficiency | L_suf: selected mask alone achieves near-full-correction performance |
| counterfactual rollout | Rollout under alternative physical parameters to validate correction choice |
| robust MPC | MPPI/CEM planning under corrected dynamics with distributional robustness |
| decision-relevant compute | Planning only when action/value changes justify compute cost |
| action-relevance | Correction selection guided by Q-sensitivity / value improvement, not NLL alone |
| wrong-dynamics-hypothesis persistence | Duration that wrong physical dynamics remain undetected and uncorrected |

## Citation Ledger (≥2-source rule)

All citations require ≥2 confirmed source URLs before inclusion.
Status: PENDING MCP cross-check. See docs/orchestration/mcp_research/INDEX.md.

| Reference | arXiv | Semantic Scholar | Status |
|---|---|---|---|
| TD-MPC2 (Hansen 2024) | 2310.16828 | TBD | PENDING |
| DreamerV3 (Hafner 2023) | 2301.04104 | TBD | PENDING |
| HiP-RSSM (Achterhold 2022) | 2206.14697 | TBD | PENDING |
| PLSM (Tomar 2024) | 2401.17835 | TBD | PENDING |
| Jain & Wallace 2019 | arXiv | TBD | PENDING |
| Wiegreffe & Pinter 2019 | arXiv | TBD | PENDING |
| Khemakhem 2020 iVAE | 1907.04809 | TBD | PENDING |
| Locatello 2019 | PMLR v97 | TBD | PENDING |
| Peters 2016 ICP | arXiv | TBD | PENDING |
| Arjovsky 2019 IRM | arXiv | TBD | PENDING |
| Angelopoulos 2022 CRC | arXiv | TBD | PENDING |
| Koh & Liang 2017 | 1703.04730 | TBD | PENDING |
| Frye 2020 ASV | arXiv | TBD | PENDING |
| ManiSkill v3 | 2410.00425 | TBD | PENDING |
| DROID (Khazatsky 2024) | 2403.12945 | TBD | PENDING |
| BridgeData V2 (Walke 2023) | 2308.12952 | TBD | PENDING |

Note: This ledger is populated from the MCP cross-check in Phase C/D (22_NOVELTY_AND_THREATS.md).
