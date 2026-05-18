# STEP 10 Current State Truth Table

date: 2026-05-18
branch: memory-redesign-2026-05-16 @ 3b56ce7 (P3_STEP9_C3_RECOVERY PASS)
gate: O-CURRENT
source_files:
  - docs/orchestration/lr_alignment/37_step8_final_evidence_card.md
  - docs/orchestration/lr_alignment/39_step9_current_state_audit.md
  - docs/orchestration/lr_alignment/40_c3_root_cause_report.md
  - docs/orchestration/lr_alignment/41_c3_fix_evidence.md
  - docs/orchestration/lr_alignment/42_true_regime_shift_f1_report.md
  - docs/orchestration/lr_alignment/47_step9_final_evidence_card.md
  - docs/orchestration/lr_alignment/48_next_phase_plan.md
  - plans/PHASE_PROGRESS.md
  - data/frcgw_text/v0_4/manifest.json
  - configs/lr_eval_real_v0_4_long.yaml
  - configs/lr_eval_step9_c3_recovery.yaml
  - src/frcgw/evaluation/frcg_agent.py:60-160
  - src/frcgw/planning/planner.py:100-200
  - src/frcgw/planning/falsification.py:60-80
  - src/frcgw/evaluation/eval_runner.py:100-180
  - src/frcgw/evaluation/ablations.py:80-90,400-425

---

## 1. FRCG-WM Overall Verdict

| Field | Value |
|---|---|
| Current STEP 9 verdict | AT_RISK_BUT_RECOVERING |
| Confidence | HIGH |
| Branch/SHA | memory-redesign-2026-05-16 @ 3b56ce7 |
| Last passing sentinel | outputs/phase_gates/P3_STEP9_C3_RECOVERY.passed |
| STEP 10 target verdict | ALIVE_REDESIGNED or HYBRID_PIVOT_RECOMMENDED |

---

## 2. Claim Status (STEP 9 종료 시점)

| Claim | Status | Value | Source (file:line) |
|---|---|---|---|
| C1 persistence | BLOCKED_no_hypothesis_update_timestamp | null | collector.py backfill logic uncovered, coverage audit missing |
| C2 regime_shift_f1 | IMPLEMENTED_DATA_LIMITED | 0.0 (test_id/test_ood n=5) | 42_true_regime_shift_f1_report.md §3 |
| C3 falsification f1 | PRELIMINARY_PLUS | 0.539/0.587 (test_id/test_ood, n=5 deterministic) | 47_step9_final_evidence_card.md §6 |
| C4 task_success | NON_DISCRIMINATIVE | 0.964/0.998 dataset-invariant | eval_runner.py:169 |
| C5 calibration ECE | BLOCKED_DEGENERATE | null | blocked on C3 std=0 |
| C6 ppc | PRELIMINARY_STRONG | 14.9× vs ABL-036, 5.5-8.6× vs direct threats | 47_step9_final_evidence_card.md §10 |

---

## 3. C3 Falsification — Mechanism Breakdown

### 3.1 Six Fixes Applied (STEP 9)

| Fix | File:Line | Change | Effect |
|---|---|---|---|
| fix-1a | frcg_agent.py:74 | `GateConfig(tau_f=0.5)` → `GateConfig(tau_f=0.0)` | predicted_wrong gate 개방 |
| fix-1b | frcg_agent.py:138-142 | `predicted_wrong = wrong_prob > 0.5` 순서 재배치 | sigmoid 공간 일관화 |
| fix-2a | planner.py:115-126 | `no_state_change` → effect_type=3 proxy | falsification short-circuit 우회 |
| fix-2b | planner.py:~190 | `planner_state.update(step_idx+1, h_star.combined_id)` | h_exec_id 동적 갱신 |
| fix-3a | eval_runner.py:117-124 | ABL-040 탐지 후 eval_labels+training_labels 전달 | ABL-040 positive control 활성화 |
| fix-3b | ablations.py:417-420 | `_last_F_t=10.0, _last_wrong_prob=1.0, _last_predicted_wrong=True` forced | ABL-040 discriminability 확보 |
| success fix | eval_runner.py:169 | `success = bool(episode.get("final_success", False))` | C4 ceiling 제거 |

### 3.2 C3 회복이 진짜인지 검증 방법 (4개)

| 방법 | 실험 설계 | 예상 결과 (진짜면) | 예상 결과 (artifact면) |
|---|---|---|---|
| (a) tau_f sweep | tau_f=[0.0,0.1,0.2,0.3,0.5] — proxy on | threshold 높을수록 F1 단조 감소 | 0.0에서만 F1>0, 나머지 0.0 |
| (b) no_state_change proxy 제거 | proxy OFF (no_state_change→type=0 환원) | F1 부분 감소 but >0 유지 | F1 0.0으로 완전 회귀 |
| (c) ABL-040 disabled | ABL-040 injection off | FRCG-LR F1 변화없음 | FRCG-LR F1도 0.0 |
| (d) threshold-free AUROC/AUPRC | roc_auc_score/average_precision on wrong_prob | AUROC>0.6 (일관) | AUROC≈0.5 (불일관) |

**판정 기준**: (b)에서 F1이 0.0으로 회귀하면 `proxy artifact` → claim 격하 필요. (d)에서 AUROC>0.6이면 신호 존재.

### 3.3 핵심 취약점

| 취약점 | 파일:라인 | 설명 |
|---|---|---|
| tau_f=0.0 의존 | frcg_agent.py:74, decision_gate.py:14 | default=0.0 일치는 정상이나, 학습된 signal이 아닌 문턱값 조정에 의한 게이트 개방 |
| no_state_change→type3 proxy | planner.py:120-126 | v0_4 데이터 65%+ 스텝이 no_state_change → 해당 proxy 없으면 falsification.py:66-67 short-circuit이 대부분 걸림 |
| falsification.py:66-67 short-circuit | falsification.py:66-67 | `if evidence.observed_effect_type in {0, 6}: return zeros` — type=0(no_state_change 원래 값)에서 F_t=0 강제 |
| text path lr_scorer 미연결 | frcg_agent.py 전체, gui_env/lr_integration.py | `lr_scorer.py`는 GUI path에만 사용. text path trace의 `lr_scorer_F_t == planner_F_t`는 lr_scorer 미사용 증거 |

---

## 4. C6 Compute Efficiency — 진짜인지 검증 방법 (3개)

| 방법 | 설명 | 현재 값 | 검증 필요 이유 |
|---|---|---|---|
| (a) fair compute matching | wall-clock 또는 FLOPs denominator로 ppc 재계산 | self-report denominator (planning_calls + rollout_steps + candidate_actions_scored) | eval_runner.py:141 total_progress = dataset-invariant; denominator = agent self-report → 14.9× gap이 self-report 차이만으로 설명 가능 |
| (b) ABL-036 진짜 always_plan | FRCG 모델 forward 강제 + no gate ablation | NoComputeGateAblation.act() = _best_public_candidate(obs) (FRCG 모델 미호출) | 현재 ABL-036은 heuristic bypass → fair ablation 아님 |
| (c) candidate_actions_scored=1 hard match | candidate_actions_scored=1로 통일 후 ppc 재비교 | FRCG-LR: len(candidates) when planned, 1 when not. ABL-036: 1 | hard match에서 advantage 유지 여부 |

**판정 기준**: (b)에서 FRCG 모델 forward를 강제한 ABL-036 대비 ppc ratio < 2× 면 C6 약화.

---

## 5. C2 regime_shift_f1 — 왜 0.0인가

| 항목 | 값 |
|---|---|
| 구현 완료 여부 | ✓ (metrics.py `regime_shift_f1()`, step_schema.py EvaluationLabels.true_regime, collector.py emit) |
| v0_4 백필 완료 | ✓ 26,226 steps |
| test_id regime_shift 에피소드 수 | 0 (200 샘플 확인) |
| test_ood regime_shift 에피소드 수 | 0 (200 샘플 확인) |
| 근본 원인 | v0_4 generator: 에피소드당 단일 regime 고정 (`_hidden_regime`). intra-episode regime shift 없음 |
| 해결책 | v0_5 multi-regime generator (intra-episode shift 포함) |

---

## 6. ABL-001/003 — 왜 retrain이 필요한가

| ABL | Config (ready) | Checkpoint | 기대 결과 | Claim 근거 |
|---|---|---|---|---|
| ABL-001 (l_regime=0.0) | configs/train_text_v0_4_abl001.yaml | MISSING | regime_shift_f1 collapse, C3 유지 | C2 separability claim |
| ABL-003 (merged regime+grammar) | configs/train_text_v0_4_abl003.yaml | MISSING | C2 + C3 동시 collapse | C3 disentanglement claim |

**판정 기준**: 기대 collapse 확인되면 claim alive. collapse 없으면 separability 근거 부재 → claim 축소.

---

## 7. n=5 std=0.000 — 왜 치명적인가

| 항목 | 값 |
|---|---|
| 현재 n=5 eval 방식 | 동일 checkpoint + 동일 dataset + seeds=[0,1,2,3,4] → deterministic model → 5회 모두 동일 결과 |
| C3 f1 std | 0.000 (test_id), 0.000 (test_ood) |
| 정보 내용 | 5회 측정이 정보적으로 1회와 동일 |
| CI 작성 가능 여부 | 불가 (std=0 → CI=[0.539, 0.539]) |
| reviewer attack 위험도 | CRITICAL — "n=5 std=0이면 단일 측정이다" |
| 해결책 A | 5개 다른 training seed로 모델 재학습 (권장) |
| 해결책 B | episode subsampling pseudo-variance (약함) |

---

## 8. pretrain_v0_4_long/manifest.json — MISSING

| 항목 | 상태 |
|---|---|
| checkpoint 존재 | ✓ (checkpoint_best.pt 사용 중) |
| manifest.json | MISSING |
| 영향 | training metadata (steps, loss curve, seed, config hash) 인용 불가 |
| 우선순위 | MEDIUM — checkpoint provenance gap이나 eval 실행에는 지장 없음 |

---

## 9. lr_eval_real_v0_4_long.yaml — regime_shift_f1 누락

| Config | metrics 목록 | regime_shift_f1 있음? |
|---|---|---|
| configs/lr_eval_real_v0_4_long.yaml | task_success_rate, falsification_precision_recall, ood_shift_f1, progress_per_compute, false_planning_call_rate | **ABSENT** |
| configs/lr_eval_step9_c3_recovery.yaml | + regime_shift_f1 추가됨 | **PRESENT** |

**문제**: main eval config와 recovery eval config 사이 metric 불일치. main eval에서 regime_shift_f1이 측정되지 않음.

---

## 10. codex_queue stale 작업 목록

현재 `.agent_tasks/codex_queue/` 에 누적된 완료 미이동 파일들이 있음.  
TASK_1134_step10_codex_queue_cleanup으로 정리 예정.

---

## 11. ABL-040 현황

| 항목 | 값 |
|---|---|
| STEP 8 상태 | INERT (FRCG-LR과 bit-identical) |
| STEP 9 fix 후 상태 | ACTIVE (recall=1.000/1.000 test_id/test_ood) |
| FRCG-LR C3 f1 | 0.539/0.587 |
| ABL-040 (leakage_sanity_probe) C3 f1 | 0.511/0.481 |
| 분리 확인 | ✓ (recall 1.000 vs 0.638/0.675) |
| 퇴보 시 | 즉시 중단 (STEP 10 invariant) |

**위험**: ABL-040 fix-3b가 `_last_F_t=10.0, _last_predicted_wrong=True`를 직접 write → oracle 활용이 정직한지, metric 우회인지 검증 필요 (RH-LEAK-01).

---

## 12. 5번 eval 실행 경로 (STEP 9 기준)

| 경로 | 용도 | 실행 여부 |
|---|---|---|
| outputs/runs/p3_lr_real_eval_step9_c3_recovery/ | C3 smoke (100 ep, seed=0) | ✓ |
| outputs/runs/p3_lr_real_eval_step9_c3_full/ | C3 full (500 ep, seeds=[0,1,2,3,4]) | ✓ |
| outputs/runs/p3_lr_real_eval_step9_c2_regime_shift_f1/ | C2 verification (seeds=[0..4]) | ✓ |
| outputs/runs/p3_lr_real_eval_step9_c6_advantage/ | C6 direct threat comparison | ✓ |
| configs/lr_eval_real_v0_4_long.yaml eval | STEP 8 full long-horizon | ✓ (no regime_shift_f1) |

---

## 13. Gate O-CURRENT Status

| 조건 | 상태 |
|---|---|
| 00_current_state_truth_table.md 작성 완료 | ✓ |
| C3 4개 검증 방법 정리 | ✓ |
| C6 3개 검증 방법 정리 | ✓ |
| C2 데이터 한계 설명 | ✓ |
| ABL-001/003 retrain 필요 근거 | ✓ |
| n=5 std=0 치명성 | ✓ |
| pretrain_v0_4_long manifest MISSING | ✓ |
| lr_eval_real_v0_4_long.yaml metric 불일치 | ✓ |
| text path lr_scorer 미연결 | ✓ |

**Gate O-CURRENT: PASS**
