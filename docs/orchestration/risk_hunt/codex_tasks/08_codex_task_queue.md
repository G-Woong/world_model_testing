# STEP 10 Codex Task Queue

date: 2026-05-18
gate: O-CODEX
source: 09_test_first_loop_protocol.md

---

## Task Queue Status

| Task ID | Topic | Status | Loop | Gate |
|---|---|---|---|---|
| TASK_1110_step10_scaffold | Directory scaffold + test | ✓ DONE (Claude direct) | STEP 0 | O-CURRENT |
| TASK_1111_step10_current_state_audit | Audit script + JSON | ✓ DONE (Claude direct) | STEP 0 | O-CURRENT |
| TASK_1112_step10_risk_register_validator | Schema validator + test | ✓ DONE (Claude direct) | STEP 1 | O-RISK |
| TASK_1113_step10_lit_scout_harness | Literature scout MCP harness | PENDING | STEP 2 | O-LIT |
| TASK_1114_step10_lit_idea_extractor | Idea bank JSON extractor | PENDING | STEP 2 | O-LIT |
| TASK_1115_step10_v0_5_design_audit | v0_5 schema design audit | PENDING | STEP 3 | O-DATA |
| TASK_1116_step10_openx_schema_audit | Open X-Embodiment schema fit | PENDING | STEP 3 | O-DATA |
| TASK_1117_step10_arch_b_skeleton | Arch B: evidence-integrating skeleton | PENDING | STEP 5 | O-ARCH |
| TASK_1118_step10_arch_i_skeleton | Arch I: foresight-to-policy adapter | PENDING | STEP 5 | O-ARCH |
| TASK_1119_step10_arch_f_skeleton | Arch F: value-of-computation gate | PENDING | STEP 5 | O-ARCH |
| TASK_1120_step10_loss_evidence_accum | Loss #1: sequence evidence accumulation | PENDING | STEP 6 | O-LOSS |
| TASK_1121_step10_loss_calibration_aware | Loss #7: calibration-aware + focal | PENDING | STEP 6 | O-LOSS |
| TASK_1122_step10_loss_clt_falsification | Loss #14 (WH-1): CLT-based falsification | PENDING | STEP 6 | O-LOSS |
| TASK_1123_step10_threshold_free_c3 | Metric #2: AUROC/AUPRC + window-AUROC | PENDING | STEP 7 | O-EVAL |
| TASK_1124_step10_foresight_causal | Metric #10: rollout causal influence logger | PENDING | STEP 7 | O-EVAL |
| TASK_1125_step10_fair_ppc | Metric #7: fair ppc wall-clock denominator | PENDING | STEP 7 | O-EVAL |
| TASK_1126_step10_eval_config_align | Add regime_shift_f1 to main eval config | PENDING | STEP 7 | O-EVAL |
| TASK_1127_step10_abl001_retrain | ABL-001 faithful retrain executor | PENDING | Loop-03 | O-LOOP |
| TASK_1128_step10_abl003_retrain | ABL-003 faithful retrain executor | PENDING | Loop-03 | O-LOOP |
| TASK_1129_step10_n5_multiseed | 5 different training seed checkpoints | PENDING | Loop-02 | O-LOOP |
| TASK_1130_step10_v0_5_generator | Multi-regime synthetic generator | PENDING | Loop-05 | O-LOOP |
| TASK_1131_step10_no_state_change_decoupling | Proxy ablation (RH-CORE-01 검증) | PENDING | Loop-01 | O-LOOP |
| TASK_1132_step10_abl036_real_no_gate | always_plan FRCG model agent (faithful ABL-036) | PENDING | Loop-06 | O-LOOP |
| TASK_1133_step10_base028_faithful | BASE-028 WebWorld faithful search | PENDING | STEP 9 | O-LOOP |
| TASK_1134_step10_codex_queue_cleanup | Stale TASK_1098~1109 cleanup | PENDING | Admin | — |
| TASK_1135_step10_dataset_decision_gate | Dataset verdict manifest builder | PENDING | STEP 10 | O-DATA-FINAL |
| TASK_1136_step10_phase_gate_sentinel | Phase gate sentinel + PHASE_PROGRESS update | PENDING | STEP 11 | O-FINAL |

---

## Execution Order (Next Session)

### Immediate (Loop execution):

**Loop-01 (RH-CORE-01)** — First and most critical:
```
1. Write TASK_1131 (no_state_change proxy ablation eval script)
2. Run: scripts/run_codex_task.ps1 -Mode run -TaskName TASK_1131 -BypassSandbox
3. Verify + accept
4. Run eval: python scripts/10_run_lr_real_eval.py --config configs/lr_eval_step9_c3_recovery.yaml --proxy-off
5. Compare: proxy ON F1=0.539 vs proxy OFF F1=?
6. Decision: KEEP/MODIFY/REJECT
7. Write loop_report: docs/orchestration/risk_hunt/loop_reports/09_loop_01_core01_proxy.md
```

**Loop-02 (RH-STAT-01)** — n=5 multiseed:
```
1. Write TASK_1129 (5 training seeds)
2. Run: scripts/run_codex_task.ps1 -Mode run -TaskName TASK_1129 -BypassSandbox
3. Verify + accept (WARNING: long training job)
4. Run eval on each seed checkpoint
5. Compute CI: mean ± 1.96*std across 5 seeds
6. Decision: KEEP if std > 0.01
7. Write loop_report
```

**Loop-03 (RH-FAI-01)** — ABL-001/003:
```
1. TASK_1127: ABL-001 faithful retrain (l_regime=0.0)
2. TASK_1128: ABL-003 faithful retrain (merged)
3. Run evals with step9_c3_recovery config
4. Check: ABL-001 → regime_shift_f1 collapse? C3 maintained?
5. Check: ABL-003 → C2 + C3 simultaneous collapse?
6. Decision: KEEP if expected collapse confirmed
7. Write loop_reports
```

### After Loop-01,02,03 complete: run TASK_1123, 1124, 1125, 1126 for O-EVAL.

---

## Gate O-CODEX Status

**Status**: PASS (protocol defined, queue structured)

All tasks have:
- 10-field schema
- SANDBOX_MODE: bypass
- No research judgment clause in STOP_CONDITION
- forbidden path list explicit
