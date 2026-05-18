# PHASE_PROGRESS.md

Pipeline A (FRCG-PHASE-GATE-LOOP) 산출물.
phase gate 진행 상황을 기록한다.

sentinel 위치: `outputs/phase_gates/<phase>.passed`
gate 명령: `/frcgw-phase-check`

---

## Phase Status

| Phase | Status | Date | Notes |
|---|---|---|---|
| P0 | PASS | 2026-05-08 | docs/scaffold complete — commit `290eb43` |
| P1 | PASS | 2026-05-08 | schema/visibility guards complete — commit `b5e4777`, 53 tests pass |
| P1.5 | PASS | 2026-05-08 | harness complete — 7 skills/7 agents/11 hooks/3 commands, sentinel P1.5.passed created |
| P2 | PASS | 2026-05-08 | text-only data generator complete — 101 tests pass, coverage all thresholds met, leakage PASS, sentinel P2.passed created |
| P3 | PASS | 2026-05-09 | tiny text FRCG model complete — 166 tests pass (65 new), leakage PASS, F_t/gate/rewrite/planner all implemented, sentinel P3.passed created |
| P3_LR_REAL_EVAL | PASS | 2026-05-17 | Real episode-level eval runner (STEP 2) — 14 tests pass, fake_metric_count=0, forbidden_source_assertion=none_read, 66 BLOCKED markers all null. random_init_ok=False (advisory, P3 pre-training normal). sentinel P3_LR_REAL_EVAL.passed created |
| P3_STEP3_DATASET_BACKFILL | PASS | 2026-05-17 | Dataset v0.2 label backfill + LR wire-up (STEP 3) — 48 tests pass (1 skipped ABL-023 marker), 4 fields 0→>0 coverage, fake_metric_count=0, C1/C3/C5 status=OK, tau_f=0.5 non-null, predicted_wrong distribution changed. T4: C5 ECE=0.025 is degenerate-predictor artifact; C1 PARTIALLY_COMPUTABLE (evidence_timestamp missing). sentinel P3_STEP3_DATASET_BACKFILL.passed created |
| P3_STEP4_EVIDENCE_INTEGRITY | PASS | 2026-05-17 | Evidence Integrity Repair + Counterfactual Rollout + LR Disclosure (STEP 4) — 82 tests pass (37 new: B0×8 + B1×13 + B2×4 + B3×5 + B4×3 + B5×4; 45 regression). B0: evidence_timestamp semantic fix (first-wrong-step, not self-index). B1: counterfactual_rollout.py active (v0_3 counterfactual coverage 100%). B2: LR comparison report (major_divergence mean_abs_diff=1.5 → STEP 5). B3: valid_trained_eval disclosure field. B4: selected_hypothesis_id per_step non-null 100%. B5: C5_calibration_status. v0_3 dataset PASS. Task 5 red-team PASS 7/7. Area-chair SENTINEL_WARN 3조건 충족. T4 claims: FC-04 MET-WM-001 deferred STEP 5, FC-01 v1 BLOCKED (namespace), all valid_trained_eval=False. sentinel P3_STEP4_EVIDENCE_INTEGRITY.passed created |
| P3_STEP5_TRAINED_EVIDENCE_READY | PASS | 2026-05-18 | STEP 5 complete — 86 tests pass (32 new STEP5 + 54 regression). Pretrained ckpt (loss 1.96→0.0081). C1 namespace fix (grammar_idx→grammar_name). C4 MET-WM-001 metric (BLOCKED_no_model_rollout_prediction — honest). C5 OR logic fix + DEGENERATE_OR_UNTRAINED status. ABL-011/015/040 registry wired. LR reconciliation (DIVERGENCE_PERSISTS — l_falsification=0.0 → STEP 6 retrain). T4 critical: current ckpt = ABL-010 condition. valid_trained_eval=True. sentinel created. |
| P4 | PENDING | — | synthetic GUI MVE collector |
| P5 | PENDING | — | frozen VLM MVE model |
| P6 | PENDING | — | core baselines/ablations compute-matched |
| P7 | PENDING | — | paper-main planning (after P6 gates pass) |
| P8 | PENDING | — | report generation from real logs only |

---

## P1.5 Gate Criteria

- [x] 7 skill files created under `.claude/skills/`
- [x] 7 agent files created under `.claude/agents/`
- [x] 11 hook scripts present under `.claude/hooks/`
- [x] 3 commands created under `.claude/commands/`
- [x] `.claude/settings.json` updated with hook events
- [x] `pytest -q` = 53 passed (baseline unchanged)
- [x] harness sanity verified — P2 plan §2.2 criteria met
- [x] `plans/PLUGIN_AUDIT_REPORT.md` initialized
- [x] `outputs/phase_gates/`, `outputs/test_reports/`, `outputs/review_reports/`, `outputs/eval_reports/` directories created
- [x] `outputs/phase_gates/P1.passed` sentinel created
- [x] `outputs/phase_gates/P1.5.passed` sentinel created

---

## P2 Gate Criteria (pre-condition before starting)

- P1.5 sentinel: `outputs/phase_gates/P1.5.passed` (or equivalent)
- Required reads: `04_TEXT_ONLY_SMOKE_TESTBED.md`, `06_DATA_SCHEMA_AND_LABELING.md`, `12_DATA_COLLECTION_METHODOLOGY_v1.md`
- Required gate: coverage audit pass (failure/recovery/reveal/shift/wrong-grammar coverage thresholds)
- Required gate: no hidden label leakage in text generator
- Required gate: `pytest -q` all pass

---

## Compaction Handoff Log

(pre_compact_phase_handoff.ps1가 자동 append)
- 2026-05-16T03:07:46Z | branch: memory-redesign-2026-05-16 | passed_gates: P1.5, P1, P2, P3, P3_EVAL | SoT: docs/orchestration/session_reports/2026-05/2026-05-16_precompact_handoff.md
- 2026-05-16T14:37:59Z | branch: memory-redesign-2026-05-16 | passed_gates: P1.5, P1, P2, P3, P3_EVAL | SoT: docs/orchestration/session_reports/2026-05/2026-05-16_precompact_handoff.md
- 2026-05-16T15:37:34Z | branch: memory-redesign-2026-05-16 | passed_gates: P1.5, P1, P2, P3, P3_EVAL | SoT: docs/orchestration/session_reports/2026-05/2026-05-16_precompact_handoff.md
- 2026-05-16T20:05:44Z | branch: memory-redesign-2026-05-16 | passed_gates: P1.5, P1, P2, P3, P3_EVAL | SoT: docs/orchestration/session_reports/2026-05/2026-05-16_precompact_handoff.md
- 2026-05-16T21:41:09Z | branch: memory-redesign-2026-05-16 | passed_gates: P1.5, P1, P2, P3, P3_EVAL | SoT: docs/orchestration/session_reports/2026-05/2026-05-16_precompact_handoff.md
- 2026-05-16T22:56:05Z | branch: memory-redesign-2026-05-16 | passed_gates: P1.5, P1, P2, P3, P3_EVAL | SoT: docs/orchestration/session_reports/2026-05/2026-05-16_precompact_handoff.md
- 2026-05-17T12:53:52Z | branch: memory-redesign-2026-05-16 | passed_gates: P1.5, P1, P2, P3, P3_EVAL, P3_LR_EVAL | SoT: docs/orchestration/session_reports/2026-05/2026-05-17_precompact_handoff.md
- 2026-05-17T17:00:19Z | branch: memory-redesign-2026-05-16 | passed_gates: P1.5, P1, P2, P3, P3_EVAL, P3_LR_EVAL | SoT: docs/orchestration/session_reports/2026-05/2026-05-17_precompact_handoff.md
- 2026-05-17T21:29:21Z | branch: memory-redesign-2026-05-16 | passed_gates: P1.5, P1, P2, P3, P3_EVAL, P3_LR_EVAL, P3_LR_REAL_EVAL | SoT: docs/orchestration/session_reports/2026-05/2026-05-17_precompact_handoff.md
- 2026-05-17T22:47:17Z | branch: memory-redesign-2026-05-16 | passed_gates: P1.5, P1, P2, P3, P3_EVAL, P3_LR_EVAL, P3_LR_REAL_EVAL, P3_STEP3_DATASET_BACKFILL | SoT: docs/orchestration/session_reports/2026-05/2026-05-17_precompact_handoff.md
- 2026-05-18T11:14:31Z | branch: memory-redesign-2026-05-16 | passed_gates: P1.5, P1, P2, P3, P3_EVAL, P3_LR_EVAL, P3_LR_REAL_EVAL, P3_STEP3_DATASET_BACKFILL, P3_STEP4_EVIDENCE_INTEGRITY | SoT: docs/orchestration/session_reports/2026-05/2026-05-18_precompact_handoff.md
