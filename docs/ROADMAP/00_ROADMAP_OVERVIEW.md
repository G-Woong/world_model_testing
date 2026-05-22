# ROADMAP OVERVIEW — FGLC (R0..R16)

## Project Goal

FGLC (Falsification-Guided Latent Correction for World Model Planning) — ICLR submission.
Target: demonstrate that falsification-guided latent correction outperforms TD-MPC2/DreamerV3/
HiP-RSSM on ManiSkill manipulation tasks under controlled physical OOD shift.

## Milestone Summary

| Phase | Goal | Duration (A100) | Gate sentinel |
|---|---|---|---|
| R0 | Contract reset (DONE) | 0 | R0.passed |
| R1 | Infrastructure: ManiSkill + src/fglc skeleton | 1 day | R1.passed |
| R2 | Data pipeline: state-only ID+OOD dataset | 2 days | R2.passed |
| R3 | Base world model: Stage 1 training converged | 3 days | R3.passed |
| R4 | Falsification gate: calibrated β_t, OOD detection AUROC > 0.75 | 2 days | R4.passed |
| R5 | CIRCA: corrected NLL < uncorrected NLL on OOD | 3 days | R5.passed |
| R6 | Correction module: necessity+sufficiency tests pass | 2 days | R6.passed |
| R7 | Planner: closed-loop FGLC > TD-MPC2 on ≥1 OOD condition | 4 days | R7.passed |
| R8 | Algorithm variants: ASAP, I3G, IVI implemented + compared | 4 days | R8.passed |
| R9 | Ablation grid: all 11 families + results | 3 days | R9.passed |
| R10 | Baselines: TD-MPC2, DreamerV3, HiP-RSSM + compute-matched | 5 days | R10.passed |
| R11 | RGB-D extension: same ablation/baseline grid | 4 days | R11.passed |
| R12 | DROID/BridgeData validation | 5 days | R12.passed |
| R13 | Necessity/sufficiency deep eval: sim oracle | 2 days | R13.passed |
| R14 | Paper framing + drafting | 7 days | R14.passed |
| R15 | Reviewer-attack defense + supplementary | 3 days | R15.passed |
| R16 | Final report + reproducibility package | 2 days | R16.passed |

**Total estimated A100 compute**: ~55 days (state-only Phase 1: ~25 days)
**Critical path**: R3 → R4 → R5 → R7 → R10 (baseline comparison required for main claim)

## Commit Cadence Policy

One commit per completed phase gate (per `docs/ROADMAP/18_COMMIT_AND_GIT_STRATEGY.md`).
Branch: `memory-redesign-2026-05-16` until R14 gate passes; then create PR to main.
Sentinel convention: `outputs/phase_gates/R<N>.passed`.

## Success Criteria

**Minimum viable paper**:
1. R3 passed: base WM converged on ID (NLL < 0.1 nat)
2. R4 passed: OOD detection AUROC > 0.75 (vs. 0.5 random)
3. R7 passed: FGLC > TD-MPC2 return on ≥2 OOD conditions (p < 0.05)
4. R9 passed: ABL-01 (no-correction) < FGLC on OOD (problem existence)
5. R10 passed: FGLC > HiP-RSSM on OOD return (closest competitor)
6. R14 passed: paper section drafts complete

**Full paper (ICLR target)**:
All 17 gates passed + war-room synthesis PASS + reviewer-2 defense complete.

## Phase Gate Sentinel Convention

```
outputs/phase_gates/R0.passed  ← created by this pivot (A.1..A.5 complete)
outputs/phase_gates/R1.passed  ← after infrastructure verified
...
outputs/phase_gates/R16.passed ← final report complete
```

Phase gates are ZERO-BYTE marker files created via `/fglc-phase-check --pass R<N>`.
