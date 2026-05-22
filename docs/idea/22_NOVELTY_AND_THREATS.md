# 22_NOVELTY_AND_THREATS

## Source
- main.md §18 (HiP-RSSM/PLSM differentiation)
- deep-research-report.md §summary, §CIRCA description

## Direct Threat Table

All threats require ≥2-source cross-check (C9 checkpoint). Citation links PENDING MCP verification.

| Threat | arXiv/DOI | Differentiation | Severity |
|---|---|---|---|
| TD-MPC2 (Hansen 2024) | 2310.16828 | FGLC adds falsification gate + correction; TD-MPC2 has no OOD adaptation mechanism | SOFT (we extend it) |
| DreamerV3 (Hafner 2023) | 2301.04104 | Decoder-based RSSM; FGLC is decoder-free; DreamerV3 has no falsification/correction | SOFT |
| HiP-RSSM (Achterhold 2022) | 2206.14697 | HiP-RSSM: explicit parameter inference → which dynamics family; FGLC: falsification + sparse correction without parameter inference | MEDIUM (closest competitor) |
| PLSM (Tomar 2024) | 2401.17835 | PLSM: makes action effects more systematic at training; FGLC: detects and corrects hypothesis violations at inference | SOFT |
| ReDRAW (residual WM) | TBD | Residual latent correction; FGLC adds causal attention + necessity/sufficiency + value-aware selection | MEDIUM |
| AdaWM (sim-to-real) | TBD | Mismatch-driven adaptation; FGLC adds formal calibration + group-level attribution | MEDIUM |
| CIRCA-adjacent conformal RL | recent | FGLC's conformal gate is one component; CIRCA combines conformal + intervention + robust MPC | SOFT |
| iVAE (Khemakhem 2020) | arxiv 1907.04809 | iVAE is a component of I3G algorithm only; not the primary FGLC contribution | SOFT |

## Core Novelty Claim

FGLC's novelty is the **combination** in the world model correction context:
1. Standardized mismatch as calibrated falsification signal
2. Intervention-validated group-level correction attention (not explanation)
3. Necessity/sufficiency training losses making attention a validated correction policy
4. Four algorithms (CIRCA/ASAP/I3G/IVI) covering different validity/calibration/efficiency tradeoffs

None of these individually are claimed as novel in isolation.
The novel contribution is their integration for latent world model correction under physical OOD shift.

## 2025/2026 Novelty Threat Sweep

Required per plan §D.1: arxiv last-12-months search for:
- "world model correction robotics"
- "latent correction world model"
- "falsification robotics planning"
- "causal attention world model"
- "sparse latent correction"

Status: PENDING MCP search (semantic-scholar + arxiv). See docs/orchestration/mcp_research/INDEX.md.

## Connection Map
- Upstream: 17_ALGORITHM_COMPARISON.md (algorithm differentiation)
- Downstream: 25_PAPER_TITLE_CONTRIBUTIONS.md
- Verification: fglc-related-work-scout agent

## Checkpoints

- C2 Novelty: PENDING — MCP cross-check required for all threat entries above
- C9 Related work: PENDING — ≥2-source rule requires arxiv + semantic-scholar per entry
- All other checkpoints: deferred until C9 MCP verification complete
