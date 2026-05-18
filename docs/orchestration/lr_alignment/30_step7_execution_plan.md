# STEP 7 — Execution Plan

date: 2026-05-18
branch: memory-redesign-2026-05-16 @ f488776
verdict: IMPLEMENTABLE_CORE (confidence 0.82)
plan_source: 2026-05-18 session STEP 7 PLAN document

## N1 Audit Gate ✅ COMPLETE

- git_sha=f488776 confirmed
- STEP 6 sentinel + checkpoint inventory
- 4-way C3 reconciliation snapshot
- C3 root cause 5-가설 verdict: H3=CONFIRMED (planner._effect_type_id mapping bug)
- dataset effect_type 분포: 111/185 non-trivial (60%)
- 14 CRITICAL ablation roster confirmed

## Phase C T1 Agents (read-only) ✅ COMPLETE

| Agent | Verdict | Key Finding |
|---|---|---|
| mathematical-validity-critic | FAIL (2 defects) | losses.py EFFECT_TYPE_VOCAB must update atomically; no_effect_flag missing "no_state_change" |
| claim-metric-alignment-auditor | PARTIALLY_ALIGNED | ood_shift_f1 as proxy OK; "MET-OOD-003 STEP 7 proxy" labeling required |
| frcgw-data-leakage-auditor | PASS | PublicEffect fields are public-safe; _accessed_hidden assert is dead no-op |

Critical amendment from T1: task_complete=7 → task_complete=5 (n_effect_types=7, index OOB correction)

## Codex Tasks Status

| Task | Description | Status | Commit |
|---|---|---|---|
| Task 1 | C3 effect_type mapping fix | ✅ MERGED | ae81f32 |
| Task 2 | falsification.py short-circuit | ✅ Option C (direct) | falsification.py comment added |
| Task 3 | C2 ood_shift_f1 + C5 calibration | ✅ MERGED | 5b5f142 |
| Task 4 | C4 expanded validation harness | ✅ MERGED | 0a22336 |
| Task 5 | Full 11 ablation harness | 🔄 IN PROGRESS | pending |
| Task 6 | BASE-026/027/028 doc hardening | ⏳ QUEUED | pending |

## Task 2 Decision Record

**Decision: Option C — keep {0,6} short-circuit unchanged**

Rationale:
- After mapping fix (Task 1), all v0_3 non-trivial types map outside {0,6}:
  - state_change=1, blocker_removed=2, delayed_effect=4, task_complete=5
- no_state_change=0: correctly short-circuits (zero-effect evidence cannot falsify)
- no_op_valid=6: legacy key, not in v0_3 data; semantically valid (deliberate no-op)
- Sanity check: test_step7_falsification_nondegenerate.py — all 5 tests GREEN

Clarifying comment added to falsification.py:64 to document the distinction
(0=unintended no-change vs 6=deliberate no-op valid).

falsification.py modification: 2-line comment only (no logic change).

## F.7 Targeted Regression Status

| Test Suite | Status |
|---|---|
| test_step7_falsification_nondegenerate.py | ✅ 5/5 |
| test_step7_effect_type_mapping_alignment.py | ✅ 16/16 |
| test_step7_lr_scorer_public_proxy.py | ✅ 8/8 |
| test_step7_ood_shift_f1.py | ✅ 6/6 |
| test_step7_c5_calibration_stub.py | ✅ 3/3 |
| test_forbidden_field_mirror_sync.py | ✅ 2/2 (1 skip) |
| test_visibility_contract.py | ✅ 17/17 |
| test_leakage_auditor.py | ✅ PASS |

## Safety Gate (N9) Status

| Check | Status |
|---|---|
| hidden_label_leakage_count | 0 (leakage auditor PASS) |
| fake_metric_count | 0 (all Task RESULT.md confirm) |
| STEP 5/6 artifacts unmodified | ✅ (git diff outputs/runs/p3_lr_real_eval_step{5,6}_* = empty) |
| STEP 5 checkpoint sha256[:16] | ✅ 1910C13F7708CE10 (unmodified) |
| schema_leakage_guard hook drift | STEP 8 deferred |

## Pending (F.3-F.6 evaluation runs)

Evaluation runs require actual data/checkpoint execution. These are deferred
to after all Codex tasks complete.

## STEP 8 Handoff Items

1. v0_4 dataset collection (2000+ episodes)
2. ABL-001/003/015 faithful retrain
3. BASE-026/027/028 faithful implementation
4. LR active path swap (frcg_agent integration)
5. True regime_shift_f1 (visibility contract change required)
6. Long-horizon training (epochs ≥ 10)
7. Statistical reliability (n=5 seeds all metrics)
8. Paper table readiness (P7 entry conditions)
