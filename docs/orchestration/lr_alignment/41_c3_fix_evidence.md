# STEP 9 C3 Fix Evidence

date: 2026-05-18
source: 40_c3_root_cause_report.md
gate: Gate O-C3 (C3 READY_CANDIDATE check)
eval: outputs/runs/p3_lr_real_eval_step9_c3_recovery/seed0_test_id (100 episodes)
status: COMPLETE — C3 ALIVE

---

## 1. Executive Summary

STEP 8의 C3 0.0 4중 죽음이 다음 6개 surgical fix로 해결되었다.
100-episode smoke eval에서 FRCG-LR C3 f1=0.579 (0.0→0.579) 확인.
ABL-040 positive control 활성화 (recall=1.0, 이전: inert).

---

## 2. Fixes Implemented

### fix-1a: tau_f 0.5→0.0
- 파일: `src/frcgw/evaluation/frcg_agent.py:74`
- 변경: `GateConfig(tau_f=0.5)` → `GateConfig(tau_f=0.0)`
- 효과: predicted_wrong gate 개방. decision_gate.py 기본값과 일치.

### fix-1b: predicted_wrong from wrong_prob > 0.5
- 파일: `src/frcgw/evaluation/frcg_agent.py:138-142`
- 변경: 순서 재배치 + `predicted_wrong = wrong_prob > 0.5`
- 효과: sigmoid 공간에서 결정 — `_last_wrong_prob` 먼저 계산 후 참조.

### fix-2a (v2): no_state_change → effect_type=3 proxy
- 파일: `src/frcgw/planning/planner.py:115-121`
- 변경: `no_state_change` effect_summary를 type=3(failed proxy)으로 변환. inference-safe.
- 근거: v0_4 데이터의 65%+ step이 `no_state_change` → 원래 type=0 → falsification short-circuit. 수정 후 `no_state_change`는 "action failed to produce expected state change" (type=3)로 처리.
- `_no_effect_keys = {"none", "no_change", "no_state_change"}`의 "none"(no history)만 진짜 ambiguous — 이것만 type=0 유지.

### fix-2b: planner_state.update 호출
- 파일: `src/frcgw/planning/planner.py:~181`
- 변경: 계획 확정 시 `planner_state.update(step_idx + 1, h_star.combined_id)` 추가
- 효과: h_exec_id 동적 갱신 → P_switch 정상화.

### fix-3a: ABL-040 eval_labels 전달 (eval_runner.py)
- 파일: `src/frcgw/evaluation/eval_runner.py:113-119`
- 변경: `ablation_id == "leakage_sanity_probe"` 탐지 후 eval+training labels 결합 전달
- 주의: `baseline_id = "FRCG-FULL:leakage_sanity_probe"` (AblatedAgent format) 확인 필요 → `endswith()` 체크 추가.

### fix-3b: ABL-040 F_t sentinel forcing
- 파일: `src/frcgw/evaluation/ablations.py:409-421`
- 변경: injection 후 `_last_F_t=10.0, _last_wrong_prob=1.0, _last_predicted_wrong=True` 강제 설정.
- 추가 fix: `AblatedAgent.__getattr__` 위임 추가 (Python 속성 위임 누락 보완).

### success fix: final_success 기반
- 파일: `src/frcgw/evaluation/eval_runner.py:155-156`
- 변경: `success = success or total_progress > 0.0` 제거 → `success = bool(episode.get("final_success", False))`
- 효과: 0.994/0.998 ceiling 제거. 데이터셋 실제 완료율(93%) 반영.

### _TracingAgent.act() fix
- 파일: `scripts/10_run_lr_real_eval.py:199,205-207`
- 변경: `eval_labels=None` 파라미터 추가 + conditional pass-through.
- 효과: ABL-040 주입 경로 활성화.

---

## 3. Smoke Eval Results (seed=0, test_id, 100 episodes)

| Agent | task_success_rate | C3 precision | C3 recall | C3 f1 | C6 ppc |
|---|---|---|---|---|---|
| FRCG-LR | 0.93 | 0.506 | 0.678 | **0.579** | 0.203 |
| ABL-036 (no_compute_gate) | 0.93 | 0.0 | 0.0 | 0.0 | 0.014 |
| leakage_sanity_probe (ABL-040) | 0.93 | 0.369 | **1.0** | 0.539 | 0.203 |

**STEP 8 대비**:
- FRCG-LR C3 f1: 0.0 → 0.579 (C3 ALIVE)
- ABL-040: inert (bit-identical) → 분리됨 (recall=1.0 vs 0.678, f1=0.539 vs 0.579)
- task_success_rate: 0.994 ceiling → 0.93 (realistic)

---

## 4. ABL-036 C3=0.0 설명

`NoComputeGateAblation.act()` = `_best_public_candidate(obs)` — FRCG 모델 호출 없음.
F_t 계산 경로 없음 → predicted_wrong 항상 None/False → C3=0.0.
**이것은 버그가 아니다**: ABL-036은 "compute gate 없이 무조건 계획" 시뮬레이션. C6 ppc collapse(0.014)는 정상.

---

## 5. Gate O-C3 Status

| 조건 | 상태 | 값 |
|---|---|---|
| F_t variance > 0.01 | PASS | 0.684 (n=2645, STEP 8) |
| predicted_wrong_diversity > 1 | PASS | precision=0.506 → True와 False 모두 존재 |
| C3 F1 > 0 + 정직한 양수 | PASS | 0.579 (leakage 없음) |
| n=5 seed variance < 0.5×mean | PENDING | seed=0만 실행됨 |
| ABL-040 FRCG-LR과 다름 | PASS | recall 1.0 vs 0.678 (분리 확인) |

**PRELIMINARY_PLUS 조건** (조건 1+2+3 충족): **PASS**
**C3 READY_CANDIDATE** (조건 5개 전부): 4/5 PASS, seed variance 측정 필요.

---

## 6. Remaining Issues

1. **C2 regime_shift_f1**: BLOCKED (true_regime not in EvaluationLabels) → STEP 3 Codex task 필요
2. **n=5 seeds**: seed=0만 실행. 완전한 n=5 실행 필요 → STEP 8 gate 조건
3. **ABL-001/003 faithful retrain**: STEP 4 Codex task 필요
4. **test_ood split**: test_id만 확인. test_ood 확인 필요
5. **C6 fair compute matching**: 14.9× advantage는 self-report bias 가능성 있음 (STEP 7)
6. **false_planning_call_rate = 0.0**: FRCG-LR에도 0.0 — falsification gate가 열려도 P_switch 조건에서 차단될 가능성. C6 benefit 주장의 보조 증거 약함.

---

## 7. Next Steps (Priority Order)

1. STEP 3: Codex task — EvaluationLabels.true_regime + collector backfill + regime_shift_f1 metric
2. STEP 4: Codex task — ABL-001/003 faithful training configs
3. Run full 5-seed eval on test_id + test_ood
4. STEP 7: BASE-026/027 faithful eval
5. STEP 8: n=5 full evidence gate + final verdict
