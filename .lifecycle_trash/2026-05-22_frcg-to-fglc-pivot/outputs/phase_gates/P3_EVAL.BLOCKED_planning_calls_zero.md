# P3_EVAL GATE BLOCKED — 2026-05-16

Reason: planning_calls=0 across ALL 5 seeds (outputs/runs/p3_eval/metrics.json).
TextFRCGModelAgent with 80-step trained model never triggers planning gate.
All mechanism metrics identical between FRCG-FULL and all baselines.

Root cause: model weights at near-random-init level. F_t never exceeds tau_f.

Re-evaluation prerequisites:
1. Extend training to >= 1k steps
2. Verify planning_calls > 0 in >= 10pct of episodes
3. Re-run scripts/03_eval_text_smoke.py + scripts/08_run_core_ablations.py
4. Check CC-P3-G1/G3/G4 from ablation_results.json

Do not use P3 results as paper claim evidence until this gate is re-earned.
This file supersedes P3_EVAL.passed per 2026-05-16 war room audit.
