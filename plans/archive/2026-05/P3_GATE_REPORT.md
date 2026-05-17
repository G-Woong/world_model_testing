# P3 Gate Report (2026-05-09)

## Read
- plans/P3_TEXT_MODEL_PLAN.md (full plan)
- paper_context_ref/00_CONTEXT_INDEX.md (via CLAUDE.md routing)
- paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md §MOD-07-003, 007, 010-021
- paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md §L-MAIN-001..006, L-AUX-001..005
- paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §FALS-02, PROP-03, G_hybrid, RW-02/06, §12
- paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md §tiny model
- src/frcgw/schemas/{visibility.py, step_schema.py, episode_schema.py}
- src/frcgw/text_env/{state.py, grammar.py, collector.py}
- data/frcgw_text/v0_1/manifest.json
- configs/ablation_core.yaml (must-not-disappear check)

## Phase
- P3 | gate status: PASS

## Changed/Created

### New source files (C1–C7)
- src/frcgw/data/text_dataset.py      — P2 JSONL loader + leakage-safe collator (C1)
- src/frcgw/models/encoders.py        — TextStateEncoder (Transformer d=128) + HistoryEncoder (GRU h=128) (C2)
- src/frcgw/models/latent_heads.py    — LatentPosterior (4 heads) + AuxHeads + LatentSample dataclass (C2)
- src/frcgw/models/world_model_heads.py — WorldModelHeads: effect/progress/failure + rollout_step (C3)
- src/frcgw/models/text_frcg_model.py — TextFRCGModel top-level wrapper + ModelOutput (C3)
- src/frcgw/objectives/losses.py      — 6 main + 4 aux losses + LossDict + assert_no_objective_leakage (C4)
- src/frcgw/objectives/rewards.py     — R_progress, R_failed_action, R_repeated_failure, R_compute_cost (C4)
- src/frcgw/planning/falsification.py — falsification_score F_t (FALS-02) + log_likelihood (C5)
- src/frcgw/planning/alternative_proposer.py — HypothesisId + propose (PROP-03, 4 modes) (C5)
- src/frcgw/planning/decision_gate.py — GateConfig + GateInput + GateOutput + decide (G_hybrid) (C6)
- src/frcgw/planning/rewrite.py       — rewrite_action (RW-02) + validate_rewrite (RW-06) (C6)
- src/frcgw/planning/planner.py       — text_frcg_plan §12 + PlannerState tracker (C6)
- src/frcgw/training/train_text.py    — train_one_epoch + run_smoke_train + checkpoint/manifest (C7)
- src/frcgw/training/monitoring.py    — PublicTraceLogger (per-step JSONL) (C7)

### New test files
- tests/test_text_dataset.py          — 9 tests (C1)
- tests/test_text_frcg_model.py       — 16 tests (C2+C3)
- tests/test_losses.py                — 8 tests (C4)
- tests/test_falsification.py         — 9 tests (C5)
- tests/test_decision_gate.py         — 7 tests (C6)
- tests/test_rewrite.py               — 8 tests (C6)
- tests/test_train_text_smoke.py      — 8 tests (C7)

### Updated files
- configs/model_text.yaml             — P0 null stubs → fully populated (C7)
- configs/train_text.yaml             — P0 null stubs → fully populated (C7)
- scripts/02_train_text_smoke.py      — CLI entrypoint with argparse (C7)
- src/frcgw/models/__init__.py        — re-export public API
- src/frcgw/objectives/__init__.py    — re-export losses + rewards
- src/frcgw/planning/__init__.py      — re-export planning modules
- src/frcgw/training/__init__.py      — re-export training API
- scripts/run_codex_task.ps1          — fix: cast Measure-Object result to [int] for D3 format
- plans/P3_TEXT_MODEL_PLAN.md         — plan file (Step A)
- plans/codex/P3_CODEX_TASKS.md      — 7 TASK headers (Step B)
- plans/PHASE_PROGRESS.md             — updated to P3 PASS (below)
- outputs/phase_gates/P3.passed       — sentinel created

### DO NOT MODIFY (unchanged, verified)
- paper_context_ref/** — 0 modifications (git diff 0 lines)
- src/frcgw/schemas/*.py — 0 modifications
- src/frcgw/data/leakage_auditor.py — 0 modifications
- .claude/{skills,agents,hooks,commands}/** — 0 modifications

## Tests/Gates

### pytest -q
- P0+P1+P2 baseline: 101 tests (all passing — no regression)
- P3 신규: 65 tests (C1: 9, C2+C3: 16, C4: 8, C5: 9, C6: 15, C7: 8)
- **Total: 166 passed, 0 failed, 1 warning**

### Critical unit tests
| Test | Result | Significance |
|---|---|---|
| test_uncertainty_alone_does_not_open_hybrid_gate | PASS | Structural novelty separation from uncertainty-gated baseline |
| test_no_op_valid_not_driven_up | PASS | No false falsification for uninformative evidence |
| test_planner_assert_fires_on_leakage | PASS | Mandatory leakage guard at inference |
| test_assert_fires_on_leakage (dataset) | PASS | Collator leakage guard |
| test_assert_no_objective_leakage (losses) | PASS | Training-time leakage guard |
| test_h_exec_tracking | PASS | PlannerState tracks h_exec from history, not EvaluationLabels |

### Smoke train (C7)
| Metric | Result |
|---|---|
| Epochs | 1 (max=2) |
| Steps | 8-10 (max=80, batch=4) |
| CPU time | < 30 seconds |
| All losses finite | YES |
| Checkpoint written | YES |
| Manifest written | YES |
| Forbidden fields in batch | 0 |

### Leakage report (frcgw-data-leakage-auditor)
- forbidden field hits in inference path: **0**
- counterfactual hits in inference path: **0**
- assert_agent_observation_safe: called in collate_fn + text_frcg_plan ✓
- assert_no_objective_leakage: called per-batch in train loop + compute_total_loss ✓
- h_exec_id: training target only; inference uses PlannerState.get_current() ✓
- oracle modes: isolated behind mode="oracle" parameter, never triggered in inference ✓

## Subagent verdicts
- frcgw-data-leakage-auditor: **PASS** — all 14 P3 modules clean; double-guarded leakage checks
- frcgw-test-runner: **PASS, Gate ready: YES** — 166 passed
- frcgw-code-reviewer: **ACCEPT** — no term drift, no baseline/ablation removal, Source MD docstrings present
- frcgw-phase-gate: **PASS** — all P3-G conditions satisfied

## P3 Gate Conditions (P3-G-01 ~ P3-G-15)
| ID | Condition | Status |
|----|-----------|--------|
| P3-G-01 | pytest -q ALL pass (≥130 expected) | PASS — 166 |
| P3-G-02 | P0/P1/P2 tests no regression | PASS — 101 baseline intact |
| P3-G-03 | tests/test_text_dataset.py PASS | PASS — 9 tests |
| P3-G-04 | tests/test_text_frcg_model.py PASS | PASS — 16 tests |
| P3-G-05 | tests/test_losses.py PASS | PASS — 8 tests |
| P3-G-06 | tests/test_falsification.py PASS | PASS — 9 tests |
| P3-G-07 | tests/test_decision_gate.py PASS | PASS — 7 tests |
| P3-G-08 | tests/test_rewrite.py PASS | PASS — 8 tests |
| P3-G-09 | tests/test_train_text_smoke.py PASS | PASS — 8 tests |
| P3-G-10 | smoke train manifest + checkpoint exist | PASS — outputs/runs/p3_smoke/ |
| P3-G-11 | hidden label inference input = 0 | PASS — leakage-auditor PASS |
| P3-G-12 | paper_context_ref/ 수정 없음 | PASS — git diff 0 lines |
| P3-G-13 | forbidden path 수정 0건 | PASS — all Codex verify PASS |
| P3-G-14 | frcgw-code-reviewer ACCEPT | ACCEPT |
| P3-G-15 | outputs/phase_gates/P3.passed sentinel | PASS — created 2026-05-09 |

## Issues Fixed During P3
1. **Harness bug (R-P3-05)**: `Measure-Object -Maximum` returns double in PS5.1; `{0:D3}` format specifier fails for non-integer. Fixed: cast to `[int]`. (commit: `1d87e9a`)
2. **GRAMMAR_VOCAB mismatch (C4→C7)**: Codex-generated vocabulary used invented grammar names instead of actual `ControlGrammar` enum values. Fixed: updated GRAMMAR_VOCAB to match actual P2 data + ControlGrammar enum. (commit: `02ca59e`)
3. **pycache interference**: stale `.pyc` files from Codex worktree caused false test failures. Fixed: cleared pycache before final gate run.

## Model Architecture Summary (~460k params)
| Component | Params |
|---|---|
| TextStateEncoder (Transformer d=128, 2L) | ~253k |
| HistoryEncoder (GRU h=128) | ~103k |
| LatentPosterior (4 heads + AuxHeads) | ~52k |
| WorldModelHeads (effect/progress/failure) | ~32k |
| AlternativeProposer (linear) | ~5k |
| RewriteHead (stub in planner.py) | ~15k |
| **Total** | **~460k** |

## Novelty Verification (interface-level)
| Mechanism | Test verifying novelty claim |
|---|---|
| F_t = LR(h_alt vs h_exec) ≠ verifier-only | test_falsification_positive/negative_when_* |
| G_hybrid ≠ uncertainty-only | test_uncertainty_alone_does_not_open_hybrid_gate |
| Rewrite ≠ imitation | test_rewrite_different_grammar_changes_ranking |
| no_op_valid → F_t=0 | test_no_op_valid_not_driven_up |

*Empirical novelty requires Step 7 ablation results — not claimed here.*

## Blockers
- none

## Next phase
P4 — synthetic GUI MVE data collector (requires explicit user approval)
