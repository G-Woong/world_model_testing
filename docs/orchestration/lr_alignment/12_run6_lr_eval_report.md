# Run 6A: LR Evaluation Report

**Date**: 2026-05-16
**Phase**: CC-P3 (pilot/core eval scope)
**Run**: 6A — Evaluation script + metrics collection
**Scope**: NOT paper-accept-level evidence. Pilot evaluation from smoke runs.

---

## 1. 실행 환경

| 항목 | 값 |
|---|---|
| config | configs/lr_eval_core.yaml |
| script | scripts/09_run_lr_eval.py |
| run_mode | full_eval_preflight_metrics |
| data shard | data/frcgw_text/v0_1/test_id.jsonl (found) |
| smoke source | outputs/runs/p3_lr_smoke/metrics.json |
| ablation source | outputs/runs/p3_ablations/ablation_results.json |
| metrics output | outputs/runs/p3_lr_eval/metrics.json |
| manifest output | outputs/runs/p3_lr_eval/manifest.json |

---

## 2. Hard Check 결과

| Check | 조건 | 결과 |
|---|---|---|
| planning_calls_gt_0 | planning_calls > 0 | PASS (1) |
| h_exec_null_rate_lt_1 | h_exec_null_rate < 1.0 | PASS (0.0) |
| f_t_variance_gt_0 | F_t_variance > 0 | PASS (1.26) |
| hidden_leakage_count_eq_0 | leakage == 0 | PASS (0) |
| degenerate_rate_lt_0_5 | degenerate_rate < 0.5 | PASS (0.20) |
| abl_022_result_exists | ABL-022 results exist | PASS |
| fake_metric_count_eq_0 | no fabricated values | PASS (0) |

**hard_checks_all_pass: true**

---

## 3. C3 핵심 비교 결과

| 비교 | FRCG-FULL | 비교 대상 | Delta |
|---|---|---|---|
| falsification_f1 vs ABL-022 (no gate) | 0.403 | 0.000 | +0.403 |
| falsification_f1 vs ABL-023 (uncertainty) | 0.403 | 0.000 | +0.403 |
| F_t_variance | 1.26 | — | — |
| F_t_degenerate_rate | 0.20 | — | — |
| calibration_ece | 0.244 | — | — |

LR scorer distinguishable from both ABL-022 and ABL-023 on falsification_f1.
BCE/sigmoid not in main path — confirmed by lr_scorer.py code review.

---

## 4. C6 Gate Efficiency

| 비교 | FRCG-FULL | ABL-034 (always_plan) | Delta |
|---|---|---|---|
| progress_per_compute | 0.229 | 0.114 | +0.115 (~2x) |
| false_planning_call_rate | 0.0 | 0.0 | 0.0 |

Gate improves compute efficiency ~2x over always-plan baseline in pilot.

---

## 5. C5 Unexpected Finding (ABL-017)

| 비교 | FRCG-FULL failed_rep | ABL-017 failed_rep | Delta |
|---|---|---|---|
| no_intent_action_mapping vs FRCG-FULL | 0.500 | 0.089 | -0.411 (OPPOSITE DIRECTION) |

**ABL-017 shows unexpected direction**: removing intent-action mapping reduces failure repetition instead of increasing it. This is a negative result that must not be hidden.

Likely explanation: synthetic data proxy artifact. `failed_action_repetition_rate` in smoke run may not reflect real grammar failure episodes. Requires investigation with real evaluation data.

---

## 6. C1/C4 Blockers

| Claim | Metric | Status | Reason |
|---|---|---|---|
| C1 MET-PERSIST-001 | wrong_grammar_persistence_v1 | BLOCKED | eval_labels.evidence_timestamp not populated |
| C4 MET-WM-001 | rollout_fidelity | BLOCKED | rollout_steps=0 |
| C4 MET-ALT-001 | alternative_adoption_rate | BLOCKED | rollout_steps=0 |
| C6 compute_matched_delta | BASE-015 delta | null | BASE-015 not in ablation_results |

---

## 7. 직접 위협 baseline 비교 현황

| Baseline | 상태 |
|---|---|
| BASE-026 WACStyleConsequenceCorrectionAgent | 미실행 (not in ablation_results) |
| BASE-027 CUWMStyleCandidateSimulationAgent | 미실행 (not in ablation_results) |
| BASE-028 WebWorldStyleSearchAgent | 미실행 (not in ablation_results) |
| BASE-006 VerifierRecoveryAgent | 미실행 (not in ablation_results) |
| BASE-012-CATTS CATTSStyleUncertaintyGateAgent | 미실행 (not in ablation_results) |

Direct-threat baseline artifacts: 부재. Run 7 후보 항목.

---

## 8. 결론

- hard checks: 전부 PASS
- C3: CONDITIONAL_ALIVE (ABL-022/023 delta 존재, 직접 위협 비교 부재)
- Run 6B 판정으로 진행

**scope_note**: pilot/core eval — NOT paper-accept-level evidence.
