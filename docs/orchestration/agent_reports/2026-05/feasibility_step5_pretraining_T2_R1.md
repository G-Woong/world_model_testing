# Feasibility Audit — STEP 5 Pretraining Smoke (T2, compact mode)

**Date**: 2026-05-18
**Branch**: memory-redesign-2026-05-16 @ bea9b9c
**Auditor**: feasibility-and-cost-auditor (T2 pre-STEP5)
**Mode**: compact

---

## Verdict: FEASIBLE (with BORDERLINE item on F_t variance gate)

## Compute Estimate

| Item | Estimate |
|---|---|
| Model size | ~2.1M params (TextFRCGModel default cfg) |
| Stage 1 (200 steps, CPU) | 3–8 min wall-clock |
| Stage 2 (500 steps, CPU) | 8–20 min wall-clock |
| Dataset (train split) | 135 episodes (below DATA-T0 minimum of 500) |

## Key Findings

### HIGH Bottleneck: F_t=None in training loop
`compute_total_loss` receives `F_t=None`; `l_falsification=0.0` in base config.
**The Stage 2 gate `"F_t held-out variance > 1e-4"` CANNOT be evaluated.**
Resolution → DECISIONS_REQUIRED: Weaken Stage 2 gate to `held-out_loss < initial_loss AND all_losses_finite=True`.
F_t variance gate deferred to STEP 6 (after falsification loss is enabled).

### monitoring.py Already Exists
`src/frcgw/training/monitoring.py` exists with `PublicTraceLogger`. Codex must ADD functions, not recreate.
Missing: `check_losses_finite`, `check_grad_norm`, `check_f_t_variance`, `TrainingMonitorState`, `build_monitor_csv_row`.

### Dataset Undersized
135 train episodes — below DATA-T0 minimum (500). Adequate for smoke convergence check, not for mechanism gate.
Label all Stage 1/2 results as "smoke convergence only, not mechanism gate."

### max_steps Acts as Global Cap
200 steps / 17 steps per epoch = ~12 effective passes (not 3 distinct epochs).
Benign for smoke run; update config notes field.

## Stage Gates (Revised)

**Stage 1 (max_steps=200)**: FEASIBLE as-is.
Gate: `all_losses_finite=True AND checkpoint.pt exists`

**Stage 2 (max_steps=500, conditional on Stage 1)**: FEASIBLE for loss convergence.
Gate (WEAKENED): `held-out_loss < initial_loss AND all_losses_finite=True`
(NOT F_t variance — F_t=None in training loop)

## Phase Alignment
Stage 1 and Stage 2 are both P3 text-only. No phase order violation.
Do not set P3.passed on F_t gate alone.
