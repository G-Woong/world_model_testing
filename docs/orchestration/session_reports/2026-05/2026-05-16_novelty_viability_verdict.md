# Novelty Viability Verdict
**Date**: 2026-05-16
**Session**: War Room R1

---

## VERDICT: C (AT RISK)

7개 deep critic + area-chair synthesis 종합 결과.

---

## Claim Survivability

| Claim | Verdict | Blocking Issue |
|---|---|---|
| C1 wrong-grammar persistence | AT_RISK | h_exec trace missing; planning_calls=0 |
| C2 regime/grammar separation | AT_RISK | Locatello impossibility; ABL-001 missing; crossed split absent |
| C3 falsification mechanism | CONDITIONAL | LR theory vs BCE implementation gap |
| C4 alternative grammar rollout | AT_RISK | MET-WM-001/ALT-001 missing; rollout_steps=0 |
| C5 grammar-conditioned rewrite | CONDITIONAL | Best claim mathematically; ABL-017 missing |
| C6 compute gate | AT_RISK | CATTS (2602.12276) directly threatens novelty |

---

## FATAL_FLAW Items

1. P4 GUI env = 14-line stub (paper framed as Web/GUI)
2. P3_EVAL.passed invalid (planning_calls=0, mechanism undemonstrated)
3. h_exec trace not populated
4. BASE-026/027/028 0% (WAC/CUWM/WebWorld direct threats)

---

## Surviving Novelty (4 items)

1. Wrong-grammar persistence as measurable failure mode (≠ action failure, ≠ verification failure)
2. Likelihood ratio falsification ≠ binary verification (if BCE gap resolved)
3. Grammar-conditioned alternative hypothesis rollout (≠ generic next-state WM)
4. Grammar-conditioned intent-to-action rewrite (≠ generic feedback correction)

---

## New Threats (3 discovered, 2-source confirmed)

| Paper | arXiv | Threat | Action |
|---|---|---|---|
| CATTS | 2602.12276 | Uncertainty compute gate (threatens C6) | Add to threat map + compute-matched experiment |
| VLAA-GUI | 2604.21375 | Loop breaker + mode switch (threatens C1/C3) | Add to threat map + BASE-loop-heuristic |
| WebUncertainty | 2604.17821 | Dual-level uncertainty (threatens C6) | Add to threat map |

---

## Next 3 Tasks (Immediate)

**TASK_A**: Fix `scripts/run_codex_task.ps1` paths (USER APPROVAL REQUIRED first)
- Change `NeurIPS2026_claude-code` → `ICLR_WM_claude-code`
- Change `NeurIPS2026_codex` → `ICLR_WM_codex`
- Re-run: `pytest -q` (smoke test after change)

**TASK_B**: After harness fix — execute TASK_1021_A (GUI env data integrity scaffold)
- TASK file already written and updated with impl_risk fixes
- FILES_FORBIDDEN now includes visibility.py, step_schema.py, etc.

**TASK_C**: Decide P3_EVAL.passed validity and re-train model
- Option 1: Extend training to 1k+ steps, verify F_t exceeds tau_f
- Option 2: Lower gate threshold for smoke test purposes
- Prerequisite for any mechanism claim
