# 23_step5_execution_plan.md — STEP 5 Execution Plan (Permanent Record)

작성일: 2026-05-18
branch: `memory-redesign-2026-05-16` @ `bea9b9c`
선행 sentinel: `outputs/phase_gates/P3_STEP4_EVIDENCE_INTEGRITY.passed` ✓

---

## §1. Purpose

이 문서는 STEP 5 구현 계획의 영구 기록이다.
STEP 4에서 `valid_trained_eval=false`(random-init), C1 BLOCKED, C4 metric 부재,
C3 LR divergence, C5 degenerate artifact 등을 이관받아 해결하는 단계다.

---

## §2. Verdict (IMPLEMENTABLE_CORE, confidence 0.78)

### GREEN (READY_TO_PATCH)
- Pretraining checkpoint (Codex Task 1): v0_3 config + 기존 entrypoint
- valid_trained_eval=True 전환: ckpt path 제공
- C1 namespace mapping (Codex Task 3): 8-entry static dict
- C5 DEGENERATE 임계 강화 (Codex Task 5): `unique<=2` 조건 추가
- ABL-011/015/040 registry wiring (Codex Task 6)

### YELLOW (NEEDS_NEW_FUNCTION)
- C4 MET-WM-001 `alternative_rollout_fidelity` (Codex Task 2)
- LR reconciliation audit script (Codex Task 4)

### YELLOW (CONTRACT-ONLY for STEP 5)
- BASE-026/027/028 documentation (Claude direct doc, T8)
- C2 regime_shift_f1 → STEP 6 이관
- Full LR scorer active path 교체 → STEP 6 이관
- Calibration training → STEP 6 이관 (STEP 5: status flag 강화만)

### RED (STEP 6 이관)
- Long-horizon training
- Production-ready WAC/CUWM/WebWorld baseline
- Full 14 critical ablation 실행

---

## §3. Claim-to-Task Mapping

| Claim | Metric | STEP 5 Task | Status 목표 |
|---|---|---|---|
| C1 wrong-grammar persistence | MET-PERSIST-001 `compute_wrong_grammar_persistence_v1` | T3 namespace + T1 ckpt | BLOCKED → preliminary OK |
| C3 LR falsification divergence | F_t planner vs lr_scorer | T1 ckpt + T4 reconciliation | dual_trace 유지, C3 preliminary |
| C4 rollout fidelity | MET-WM-001 `alternative_rollout_fidelity` | T2 metric 신규 구현 | BLOCKED → OK or BLOCKED_no_counterfactuals |
| C5 calibration | `falsification_calibration` + ECE | T5 DEGENERATE 임계 강화 | DEGENERATE_OR_UNTRAINED or OK |
| ABL-011 no-action-effect-log | falsification_precision_recall_f1 | T6 registry wiring | dispatch test PASS |
| ABL-015 no-control-grammar-loss | regime_shift_f1 | T6 registry wiring | dispatch test PASS |
| ABL-040 leakage sanity probe | task_success_rate | T6 registry wiring (positive control) | leakage_auditor catches |

---

## §4. Task Breakdown

### T1 — Pretraining Checkpoint (v0_3) — Codex Task 1 + Claude direct
- **Files**: `configs/train_text_v0_3.yaml`, `configs/train_text_v0_3_stage2.yaml`,
  `src/frcgw/training/monitoring.py`, `tests/test_step5_pretraining_checkpoint.py`
- **Staged**: Stage 1 (max_steps=200, epochs=3) → gate check → Stage 2 (max_steps=500, epochs=5)
- **Claude direct**: actual training execution + checkpoint copy + trained eval config creation
- **Abort condition**: NaN/Inf in loss, loss non-decreasing, gradient norm > 100 (5 consecutive steps)

### T2 — C4 MET-WM-001 `alternative_rollout_fidelity` — Codex Task 2
- **Files**: `src/frcgw/evaluation/metrics.py`, `src/frcgw/evaluation/eval_runner.py`,
  `scripts/10_run_lr_real_eval.py` (BLOCKED marker → actual call 교체),
  `tests/test_step5_rollout_fidelity.py`
- **Definition**: step-level fidelity = `1.0 - min(1.0, abs(predicted_top1_delta - actual_delta))`
- **Safety**: counterfactual 없으면 None 반환 (0.0 fake 금지); oracle_best_action public input 노출 금지

### T3 — C1 Namespace Alignment — Codex Task 3
- **Files**: `src/frcgw/evaluation/frcg_agent.py`, `tests/test_step5_namespace_alignment.py`
- **Mapping**: 8-entry static dict (ControlGrammar enum order) → `_last_selected_hypothesis_id`
- **Fallback**: unknown idx → `f"grammar_{idx}"` 유지 + warning

### T4 — LR Reconciliation Audit — Codex Task 4
- **Files**: `scripts/audit_step5_lr_reconciliation.py` (신규),
  `src/frcgw/evaluation/eval_runner.py` (degenerate counter bug fix),
  `tests/test_step5_lr_reconciliation.py`
- **Active path 변경 금지** (STEP 6 이관)
- **Decision rule**: `mean_abs_diff < 0.1 AND both degenerate < 0.1` → CONVERGED; else DIVERGENCE_PERSISTS

### T5 — C5 DEGENERATE 임계 강화 — Codex Task 5
- **Files**: `scripts/10_run_lr_real_eval.py` (`_compute_c5_status`),
  `tests/test_step5_calibration.py`
- **New condition**: `unique_wrong_prob_count <= 2` OR `variance < 1e-6` OR `mean_f_t < 1e-6` → DEGENERATE
- **Calibration training**: STEP 6 이관

### T6 — ABL-011/015/040 Registry Wiring — Codex Task 6
- **Files**: `src/frcgw/evaluation/ablations.py`, `tests/test_step5_critical_ablations.py`
- **ABL-011**: `no_action_effect_log` — action-effect log 없이 falsification grounding 제거
- **ABL-015**: `no_control_grammar_loss` — L_control_grammar 학습 손실 제거
- **ABL-040**: `leakage_sanity_probe` — oracle 주입으로 metric discriminability 확인 (positive control)

### T7 — Trained Smoke Eval — Claude direct
- configs/lr_eval_real_v0_3_trained.yaml 생성 + test_id (5 ep) + test_ood (5 ep) 실행

### T8 — BASE-026/027/028 Reviewer-Response Doc — Claude direct
- `docs/orchestration/lr_alignment/24_step5_direct_threat_baseline_report.md`
- "preliminary comparison with heuristic approximations" wording 강제
- Forbidden: "outperforms WAC/CUWM/WebWorld", "direct-threat baselines defeated"

### T9 — Documentation — Claude direct
- This file (23_step5_execution_plan.md) ✓
- Append to 22_step5_handoff.md (§7 status update)
- 25_step6_handoff.md (신규)

### T10 — Red-team Review — Codex Task 7
- Read-only review of all STEP 5 diff

---

## §5. Out of Scope (STEP 6)

1. C2 `regime_shift_f1` metric 함수
2. Full LR scorer active path 교체 (frcg_agent.py → lr_scorer.py 통합)
3. Long-horizon training (epochs ≥ 10)
4. WAC/CUWM/WebWorld 충실 재구현 (BASE-026/027/028 고도화)
5. Full 14 critical ablation 실행 (ABL-011/015/040 외 11개)
6. Calibration training (temperature scaling)
7. h_exec_id emission policy
8. Compute-matched comparison (BASE-015 vs FRCG-LR)
9. Statistical reliability (seed variance, n=5 seeds)

---

## §6. Phase Gate

Sentinel: `outputs/phase_gates/P3_STEP5_TRAINED_EVIDENCE_READY.passed`

### 최종 통과 조건
- [ ] all Codex tasks exit 0 + T3 impl-risk-critic PASS each
- [ ] `valid_trained_eval == true` in trained smoke manifest
- [ ] C4 either OK or explicit BLOCKED reason (not bare 0.0)
- [ ] C5 status DEGENERATE_OR_UNTRAINED (trained: OK 가능) — no random-init OK
- [ ] C1 persistence_v1 status field 존재
- [ ] ABL-011/015/040 dispatch test PASS
- [ ] STEP 4 outputs unmodified
- [ ] 32 신규 tests + 82 STEP4 regression + base regression all green

---

## §7. Cross-references

- `docs/orchestration/lr_alignment/22_step5_handoff.md` — task origin
- `docs/orchestration/lr_alignment/24_step5_direct_threat_baseline_report.md` — BASE-026/027/028 (T8)
- `docs/orchestration/lr_alignment/25_step6_handoff.md` — STEP 6 이관 목록
- `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7,§8` — baseline/ablation SSoT
