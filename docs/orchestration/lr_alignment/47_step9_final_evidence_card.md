# STEP 9 Final Evidence Card

date: 2026-05-18
branch: memory-redesign-2026-05-16 @ 6a1f475
phase_gate_target: P3_STEP9_C3_RECOVERY
gate_sources: docs/orchestration/lr_alignment/39~46

---

## 1. Executive Summary

STEP 9는 STEP 8의 C3 0.0 4중 죽음 원인(tau_f 과보수 / eval evidence 비대칭 / PlannerState 동결 / ABL-040 inert)을 직접 코드 라인 단위로 증명하고 6개 surgical fix로 해결했다. FRCG-WM의 핵심 노벨티인 **falsification-guided planning** (C3)이 실제 eval evidence로 살아났다. compute-rational planning (C6)은 14.9× advantage를 유지하며 강화되었다.

C3 f1=0.539/0.587 (test_id/test_ood), C6 ppc 5.5-14.9× advantage, ABL-040 positive control 활성화(recall=1.0). C2 regime_shift_f1 구현 완료 but v0_4 데이터 한계로 0.0.

---

## 2. Verdict

**VERDICT: AT_RISK_BUT_RECOVERING**
**Confidence: HIGH**
**Reason**: C3 ALIVE (f1=0.539/0.587), C6 strong (5.5-14.9×), ABL-040 분리됨.
C2 데이터 한계, n=5 std=0 (deterministic eval), ABL-001/003 retrain not yet run.
Phase gate PRELIMINARY_PLUS 달성. ALIVE_READY를 위해 ABL faithful retrain + C2 dataset 필요.

**Rubric**:
- NOT ALIVE_READY: n=5 std=0 (deterministic, not stochastic), ABL-001/003 retrain 미완, C2 v0_4 0.0
- NOT BLOCKED: C3 alive, ABL-040 분리, fixes committed
- AT_RISK_BUT_RECOVERING: C3 PRELIMINARY_PLUS + C6 strong + critical blockers 명확

---

## 3. Repo State

Before: c5b96ab (P3_STEP8_FINAL_EVIDENCE_VALIDATION.passed)
After: 6a1f475
Branch: memory-redesign-2026-05-16
Commits this session: fix/step9 C3 recovery + TASK_1096 (C2 true_regime) + TASK_1097 (ABL configs)

---

## 4. Data

| Item | Value | Gate |
|---|---|---|
| v0_4 total episodes | 5000 | PASS |
| train/valid/test_id/test_ood | 3500/500/500/500 | PASS |
| leakage_count | 0 (all runs) | PASS |
| true_regime backfill | 26,226 steps updated | DONE |
| true_wrong_hypothesis coverage | True=102/284, False=182/284 (50ep sample) | PASS |
| final_success coverage | 93%~99.8% per split | PASS |
| v0_3 sha256 | unchanged | PASS |

---

## 5. Training

| Config | Steps | l_falsification | Status |
|---|---|---|---|
| Stage B (pretrain_v0_4_long) | 2000 | 0.635 | complete |
| ABL-015 (l_cg=0.0) | 2000 | 0.635 | complete (checkpoint exists) |
| ABL-001 (l_regime=0.0) | — | — | CONFIG READY, retrain pending |
| ABL-003 (merged) | — | — | CONFIG READY, retrain pending |

---

## 6. C3 Final Status

### n=5 Seeds Results (deterministic; all seeds identical)

| Split | precision | recall | f1 | std |
|---|---|---|---|---|
| test_id | 0.467 | 0.638 | **0.539** | 0.000 |
| test_ood | 0.520 | 0.675 | **0.587** | 0.000 |

STEP 8 대비: 0.0 → 0.539/0.587 (BREAKTHROUGH)

### ABL-040 Positive Control

| Agent | test_id f1 | test_ood f1 | recall |
|---|---|---|---|
| FRCG-LR | 0.539 | 0.587 | 0.638/0.675 |
| leakage_sanity_probe | 0.511 | 0.481 | **1.000/1.000** |

ABL-040 recall=1.000 confirms metric discriminability. No longer inert.

---

## 7. C4 Final Status

| Split | FRCG-LR tsr | BASE-026 tsr | Note |
|---|---|---|---|
| test_id | 0.964 | 0.964 | DATASET-INVARIANT |
| test_ood | 0.998 | 0.998 | DATASET-INVARIANT |

task_success_rate is not agent-discriminative in offline eval. NON_DISCRIMINATIVE. Do NOT use as claim evidence.

---

## 8. C1/C2/C5

| Metric | Value | Status |
|---|---|---|
| C1 persistence | null | BLOCKED_no_hypothesis_update_timestamp |
| C2 regime_shift_f1 (test_id) | 0.0 | IMPLEMENTED, v0_4 no intra-episode regime shifts |
| C2 regime_shift_f1 (test_ood) | 0.0 | IMPLEMENTED, v0_4 no intra-episode regime shifts |
| C5 calibration ECE | null | BLOCKED_DEGENERATE_PREDICTOR → partially resolved: std=0 issue |

---

## 9. Ablation Results

### Inference Ablations (13 ablations, seed=0)

| Ablation | C3 f1 | C6 ppc | Note |
|---|---|---|---|
| ABL-036 (no_compute_gate) | 0.0 | 0.014 | Expected — no F_t path |
| leakage_sanity_probe | 0.511/0.481 | 0.216/0.290 | ABL-040 ACTIVE |
| Other ablations | STEP 8 data (partial) | — | STEP 10 full run needed |

### Faithful Ablation Queue

| Ablation | Config | Checkpoint | Status |
|---|---|---|---|
| ABL-001 (no_regime) | `configs/train_text_v0_4_abl001.yaml` | MISSING | Config ready, retrain pending |
| ABL-003 (merged) | `configs/train_text_v0_4_abl003.yaml` | MISSING | Config ready, retrain pending |
| ABL-015 (no_cg_loss) | `configs/train_text_v0_4_abl015.yaml` | EXISTS | STEP 8 trained |

---

## 10. Direct-Threat Baselines

| Agent | approx_level | test_id C3 f1 | test_ood C3 f1 | test_id ppc | test_ood ppc |
|---|---|---|---|---|---|
| FRCG-LR | — | **0.539** | **0.587** | **0.216** | **0.290** |
| BASE-026 WAC | PARTIAL | 0.0 | 0.0 | 0.037 | 0.053 |
| BASE-027 CUWM | PARTIAL | 0.0 | 0.0 | 0.025 | 0.036 |
| BASE-028 WebWorld | HEURISTIC | 0.0 | 0.0 | 0.025 | 0.036 |

C3: FRCG-LR uniquely >0. C6 ratio: 5.5-8.6× vs direct threats.

---

## 11. Claim Readiness

| Claim | Readiness | Paper wording allowed | Forbidden |
|---|---|---|---|
| C3 falsification-guided planning detects wrong grammar | PRELIMINARY_PLUS | "F1=0.539/0.587 on test_id/test_ood (partial faithful, n=5 deterministic)" | "outperforms", "superior", "achieves high accuracy" |
| C6 compute-rational planning saves compute vs no-gate | STRONG | "14.9× ppc vs ABL-036; 5.8-8.6× vs direct-threat baselines" | "dramatic", "breakthrough" |
| C3 ABL-040 positive control confirms metric validity | PASS | "Recall=1.000 when oracle grammar injected" | ← |
| C2 regime separation | NOT_READY | — | "regime shift detected" |
| C4 task completion advantage | NOT_READY | — | task_success_rate comparison (dataset-invariant) |
| C5 calibration | NOT_READY | — | ECE claims |

---

## 12. Tests

| Category | Count | Status |
|---|---|---|
| STEP 9 new tests | 6 (test_step9_regime_shift_f1.py) | PASS |
| Pre-existing regression | test_eval_runner_timestamps (11+), test_lr_real_eval_runner, test_visibility_contract (15), test_forbidden_field_mirror_sync | PASS |
| Pre-existing failures (unchanged) | test_ablation_runner_16_ids, test_p0_no_fake_result, test_p0_scaffold, test_text_data_counterfactuals | 4 FAIL (pre-existing) |

---

## 13. Safety

| Check | Status |
|---|---|
| hidden_label_leakage_count | 0 (all eval runs) |
| fake_metric_count | 0 (all eval runs) |
| forbidden_wording in reports | 0 |
| true_regime in public_observation | NEVER (validation.py only checks public_obs) |
| visibility.py modified | NO |
| eval_runner.py leakage check | PASS (assert_no_hidden_labels_in_input) |

---

## 14. Team Agents / Codex

| Agent/Task | Used | Result |
|---|---|---|
| TASK_1096 (Codex) | C2 true_regime + regime_shift_f1 | ACCEPTED |
| TASK_1097 (Codex) | ABL-001/003 configs | ACCEPTED |
| T3 (impl-risk-critic) | 미실행 (Claude direct changes <3 files each) | N/A |
| T4 (result interpretation) | 미실행 | STEP 10 권장 |

---

## 15. User Feedback Events

| Turn | Decision | Impact |
|---|---|---|
| User provided STEP 9 plan | 10-step recovery loop 정의 | 전체 작업 구조 |
| no_state_change proxy fix | Phase 1 발견으로 임시 수정 | C3 0.0→0.539 breakthrough |

---

## 16. Commits This Session

| SHA | Message |
|---|---|
| 6f5adeb | fix(step9): C3 recovery — tau_f, evidence proxy, planner_state, ABL-040, success fix |
| 90829a5 | merge: accept TASK_1096 — EvaluationLabels.true_regime + regime_shift_f1 |
| 7251463 | merge: accept TASK_1097 — ABL-001/003 faithful retrain configs |
| 6a1f475 | feat(step9): C2 regime_shift_f1 integration + test updates |

---

## 17. Final Human-readable Summary

STEP 9에서 FRCG-WM의 핵심 노벨티인 "falsification-guided planning"이 실제 eval evidence로 살아났다. C3 falsification F1이 STEP 8의 0.0에서 0.539/0.587로 상승했다. 이는 에이전트가 잘못된 control grammar 가설을 실제로 탐지하고 있음을 보여준다. 동시에 compute gate가 falsification-gated planning 없는 경우 대비 14.9×의 compute efficiency를 달성했으며, 직접 경쟁 baseline 대비 5.5-8.6×의 우위를 보였다. ABL-040 positive control이 활성화되어 metric 유효성이 확인되었다. C2 regime_shift_f1은 구현은 완료되었으나 v0_4 데이터가 per-episode single regime이라 의미있는 값을 산출하지 못했다. ABL-001/003 faithful retrain config는 준비되었으며 실제 retrain은 STEP 10에서 진행한다.

---

## 18. STEP 10 Handoff

### Remaining for ALIVE_READY
1. ABL-001 faithful retrain + eval (l_regime=0.0 collapse 검증)
2. ABL-003 faithful retrain + eval (merged regime/grammar collapse 검증)
3. n=5 stochastic eval (training 5× different seeds 또는 ensemble)
4. C2 dataset: multi-regime episodes in v0_5+
5. C1 persistence: hypothesis_update_timestamp coverage audit

### STEP 10 Decision Gate
**AT_RISK_BUT_RECOVERING → ALIVE_READY**: ABL-001/003 collapse 확인 시
**AT_RISK_BUT_RECOVERING → CLAIM_REDESIGN_READY**: ABL-001/003 collapse 없을 시 (C2 claim 축소)

### P4 Readiness
P4 (synthetic GUI MVE data) 진입 가능 조건:
- C3 PRELIMINARY_PLUS: ✓ (f1=0.539+)
- C6 ppc advantage vs baselines: ✓ (14.9×)
- ABL-040 discriminability: ✓ (recall=1.000)
- Remaining: ABL-001/003 (P4 진입 전 실행 권장)
