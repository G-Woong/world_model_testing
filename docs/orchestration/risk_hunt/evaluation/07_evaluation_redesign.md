# STEP 10 Evaluation Redesign

date: 2026-05-18
gate: O-EVAL
source: 04_claim_redefinition.md, 01_global_risk_register.md
status: COMPLETE

---

## 18 Metrics × 8 Field Matrix

### Metric #1 — Learned Falsification F1

| Field | Value |
|---|---|
| What it measures | threshold-based (wrong_prob > 0.5) binary detector F1 against true_wrong_hypothesis |
| Why task_success insufficient | task_success=0.964 dataset-invariant. F1 discriminates between agents (0.539 vs 0.0). |
| Required data | eval_labels.true_wrong_hypothesis, agent.last_wrong_prob |
| Implementation path | src/frcgw/evaluation/metrics.py: falsification_precision_recall() (EXISTS) |
| Leakage risk | LOW — true_wrong_hypothesis in eval_labels (audit-only), not PublicObservation |
| Fake metric risk | MEDIUM — threshold-based, not calibrated. threshold=0.5 is fixed. |
| Baseline comparison | ABL-036: 0.0 (no F_t path). ABL-040: 0.511/0.481 (oracle). |
| Success threshold | F1 > 0.3 on test_id AND test_ood (currently 0.539/0.587) |

---

### Metric #2 — Threshold-Free AUROC/AUPRC

| Field | Value |
|---|---|
| What it measures | Area Under ROC/PR curve for wrong_prob as a continuous detector of wrong hypotheses |
| Why task_success insufficient | threshold selection sensitivity → AUROC is threshold-free |
| Required data | eval_labels.true_wrong_hypothesis, agent.last_wrong_prob per-step |
| Implementation path | metrics.py: threshold_free_c3_auroc() — NEEDS IMPLEMENTATION (TASK_1123) |
| Leakage risk | LOW — same as Metric #1 |
| Fake metric risk | LOW — AUROC is threshold-free, less susceptible to threshold selection |
| Baseline comparison | Random detector: AUROC=0.5. threshold-only: AUROC≈0.55-0.65 expected. |
| Success threshold | AUROC > 0.65 (moderate), > 0.7 (good) |

---

### Metric #3 — Evidence Accumulation Quality (Window-AUROC)

| Field | Value |
|---|---|
| What it measures | AUROC of sliding-window accumulated evidence vs per-step evidence. window=10 default. |
| Why task_success insufficient | per-step AUROC doesn't capture sequence accumulation quality |
| Required data | F_t sequence per-episode, true_wrong_hypothesis |
| Implementation path | metrics.py: evidence_accumulation_quality(episodes, window=10) — NEEDS IMPLEMENTATION (TASK_1123) |
| Leakage risk | LOW |
| Fake metric risk | MEDIUM — window size is a hyperparameter |
| Baseline comparison | per-step AUROC (Metric #2) |
| Success threshold | window-AUROC > per-step AUROC + 0.05 → accumulation beneficial |

---

### Metric #4 — Wrong-Hypothesis Recovery Delay

| Field | Value |
|---|---|
| What it measures | Steps from first falsification event to first correct hypothesis adoption |
| Why task_success insufficient | recovery delay is causal, not outcome metric |
| Required data | hypothesis_update_timestamp (C1 infrastructure needed) |
| Implementation path | metrics.py: wrong_hypothesis_recovery_delay() — BLOCKED (C1 timestamp missing) |
| Leakage risk | MEDIUM — requires hypothesis_update_timestamp in eval_labels |
| Fake metric risk | MEDIUM — requires correct hypothesis tracking |
| Baseline comparison | no-falsification ablation: delayed/infinite recovery |
| Success threshold | mean recovery delay < 3 steps after falsification |

---

### Metric #5 — Action Switch Rate After Falsification

| Field | Value |
|---|---|
| What it measures | Fraction of post-falsification steps where rewrite_action changes the action vs baseline |
| Why task_success insufficient | action switch rate is behavioral, not outcome |
| Required data | plan_meta.planned, rewrite_result vs base_action |
| Implementation path | eval_runner.py: planning_events tracking (partial) |
| Leakage risk | LOW — all from public observation |
| Fake metric risk | LOW — directly measurable from agent trace |
| Baseline comparison | no-falsification ablation: switch rate ≈ 0 |
| Success threshold | switch rate > 5% on post-falsification steps |

---

### Metric #6 — Planning Compute Reallocation Accuracy

| Field | Value |
|---|---|
| What it measures | Are planning calls concentrated on wrong-grammar episodes (where planning is beneficial)? |
| Why task_success insufficient | even if task succeeds, planning may be misallocated |
| Required data | planning_calls per-step, true_wrong_hypothesis |
| Implementation path | eval_runner.py: compute_log per episode |
| Leakage risk | LOW |
| Fake metric risk | MEDIUM — requires definition of "beneficial planning" |
| Baseline comparison | ABL-036: all steps planned equally |
| Success threshold | planning_calls/episode higher in wrong-grammar episodes than correct |

---

### Metric #7 — Progress Per Compute (Fair Compute Matched)

| Field | Value |
|---|---|
| What it measures | progress_delta / actual_compute_units. compute_units = wall-clock time OR FLOPs (not self-report) |
| Why task_success insufficient | task_success doesn't account for compute cost |
| Required data | total_progress (episode), actual compute units (wall-clock) |
| Implementation path | eval_runner.py: wall-clock logging (TASK_1125) |
| Leakage risk | LOW |
| Fake metric risk | HIGH CURRENTLY — uses self-report denominator. MUST be fixed before C6 claim. |
| Baseline comparison | ABL-036 faithful (TASK_1132): must use same wall-clock denominator |
| Success threshold | ppc ratio FRCG-LR/ABL-036 > 2× (fair matched, currently 14.9× self-report) |

---

### Metric #8 — Compute-Matched Return

| Field | Value |
|---|---|
| What it measures | total_return / compute_budget under matched constraint |
| Why task_success insufficient | return per compute budget is the relevant quantity |
| Required data | total_return, compute_budget fixed at N |
| Implementation path | eval_runner.py: compute budget cap (EXISTS: planning_calls_cap=5, rollout_steps_cap=10) |
| Leakage risk | LOW |
| Fake metric risk | LOW if compute cap is fixed |
| Baseline comparison | always-plan at same compute cap |
| Success threshold | FRCG-LR compute-matched return > ABL-036 at same compute budget |

---

### Metric #9 — Alternative Hypothesis Adoption Rate

| Field | Value |
|---|---|
| What it measures | Fraction of planning events where h_star ≠ current_hypothesis (actual adoption) |
| Why task_success insufficient | adoption rate measures mechanism utilization |
| Required data | plan_meta.h_star, current hypothesis_id |
| Implementation path | eval_runner.py: planning_events (partial), planner_state |
| Leakage risk | LOW |
| Fake metric risk | LOW — directly measurable |
| Baseline comparison | no-alternative-hypothesis ablation (ABL-024): adoption_rate=0 |
| Success threshold | adoption rate > 10% of planning events |

---

### Metric #10 — Rollout-to-Action Causal Influence (Intervention Test)

| Field | Value |
|---|---|
| What it measures | Action divergence rate: same obs, rollout ON vs rollout OFF. P(action changes | rollout present) |
| Why task_success insufficient | causal influence is mechanism validation, not outcome |
| Required data | agent.act(obs) twice: once with rollout, once without (intervention) |
| Implementation path | eval_runner.py: rollout intervention logger (TASK_1124) |
| Leakage risk | LOW |
| Fake metric risk | LOW — objective comparison |
| Baseline comparison | no-rollout ablation (ABL-011) |
| Success threshold | divergence rate > 10% (moderate claim), > 30% (strong claim) |

---

### Metric #11 — Regime Shift F1

| Field | Value |
|---|---|
| What it measures | F1 for intra-episode regime shift detection (v0_5 only) |
| Why task_success insufficient | regime shift detection is C2 claim |
| Required data | true_regime per-step (v0_5), agent regime belief |
| Implementation path | metrics.py: regime_shift_f1() (EXISTS) |
| Leakage risk | MEDIUM — true_regime is inference-forbidden; must be in eval_labels only |
| Fake metric risk | MEDIUM — 0.0 on v0_4 (data limitation) |
| Baseline comparison | ABL-001 (no_regime): regime_shift_f1 collapse expected |
| Success threshold | > 0.3 on v0_5 test |

---

### Metric #12 — Long-Horizon Degradation Curve

| Field | Value |
|---|---|
| What it measures | F1 / ppc as function of episode length. C3/C6 degrade with longer horizon? |
| Why task_success insufficient | degradation curve shows robustness to long-horizon |
| Required data | episode length metadata, C3 F1 / ppc per episode length bucket |
| Implementation path | eval_runner.py: episode length stratification |
| Leakage risk | LOW |
| Fake metric risk | LOW — stratified analysis |
| Baseline comparison | ABL-036: no gate → faster degradation expected |
| Success threshold | C3 F1 doesn't halve within 10-step episodes (v0_5) |

---

### Metric #13 — Calibration ECE

| Field | Value |
|---|---|
| What it measures | Expected Calibration Error of wrong_prob vs actual wrong_hypothesis rate |
| Why task_success insufficient | calibration is about probability quality |
| Required data | wrong_prob, true_wrong_hypothesis |
| Implementation path | metrics.py: calibration_ece() (EXISTS, DEGENERATE currently) |
| Leakage risk | LOW |
| Fake metric risk | MEDIUM — std=0 causes degenerate ECE |
| Baseline comparison | RANDOM predictor: ECE≈0.32 (wrong_rate). perfect calibration: ECE=0. |
| Success threshold | ECE < 0.025 (C5 gate) after calibration training |

---

### Metric #14 — Counterfactual Action Divergence

| Field | Value |
|---|---|
| What it measures | Divergence between FRCG-LR action and counterfactual action (what would have been taken under correct grammar) |
| Why task_success insufficient | counterfactual divergence is direct evidence of falsification-guided correction |
| Required data | counterfactual rollout records |
| Implementation path | eval_runner.py: counterfactuals field (EXISTS in step_results) |
| Leakage risk | MEDIUM — counterfactual labels must not enter inference |
| Fake metric risk | LOW — compare actual vs counterfactual |
| Baseline comparison | no-falsification ablation: counterfactual divergence ≈ 0 |
| Success threshold | counterfactual divergence > 0.2 on wrong-grammar episodes |

---

### Metric #15 — Policy Outcome Improvement After Foresight

| Field | Value |
|---|---|
| What it measures | Progress delta improvement in planned vs unplanned steps |
| Why task_success insufficient | outcome improvement is action quality, not binary success |
| Required data | progress_delta per-step, planned flag |
| Implementation path | eval_runner.py: progress_delta + plan_meta.planned (PARTIAL) |
| Leakage risk | LOW |
| Fake metric risk | MEDIUM — confounded by episode difficulty |
| Baseline comparison | ABL-011 (no rollout): planned vs unplanned delta comparison |
| Success threshold | mean progress_delta(planned) > mean progress_delta(unplanned) × 1.2 |

---

### Metric #16 — Rollout Usefulness Score

| Field | Value |
|---|---|
| What it measures | Fraction of rollouts that actually improve action selection (measured by action switch) |
| Why task_success insufficient | rollout utility is intermediate mechanism metric |
| Required data | rollout results, action comparison |
| Implementation path | eval_runner.py: planning_events (PARTIAL) |
| Leakage risk | LOW |
| Fake metric risk | MEDIUM — "useful rollout" definition circular |
| Baseline comparison | ABL-036 always-plan: baseline for "how often is planning wasted" |
| Success threshold | useful_rollout_fraction > 0.3 (30% of rollouts change action) |

---

### Metric #17 — Latent Intervention Consistency

| Field | Value |
|---|---|
| What it measures | Does intervening on z_regime change regime_shift_f1? Does z_grammar intervention change C3 F1? |
| Why task_success insufficient | latent causality measurement |
| Required data | model intervention capability |
| Implementation path | diagnostic scripts (P2 scope) |
| Leakage risk | LOW |
| Fake metric risk | LOW — causal intervention is direct |
| Baseline comparison | random intervention baseline |
| Success threshold | regime intervention → regime_shift_f1 changes > 0.1 |

---

### Metric #18 — OOD Surprise Spike Quality (Robotics Logs)

| Field | Value |
|---|---|
| What it measures | F_t spike rate on OXE robot failure trajectories vs success trajectories |
| Why task_success insufficient | OOD passive validation metric |
| Required data | OXE/RT-X trajectories with failure labels |
| Implementation path | scripts/risk_hunt/audit_openx_schema.py (TASK_1116) |
| Leakage risk | HIGH if OXE failure labels enter inference |
| Fake metric risk | MEDIUM — must not use failure labels in inference |
| Baseline comparison | random spike detector |
| Success threshold | spike_rate(failure) > spike_rate(success) × 2 |

---

## Claim-Metric 1:1 Mapping Table

| Strengthened Claim | Primary metric | Secondary metric | Forbidden metric | Task |
|---|---|---|---|---|
| Claim-A (evidence-integrating falsification) | #2 AUROC, #7 ppc(fair) | #1 F1, #3 window-AUROC, #13 ECE | task_success | TASK_1123, TASK_1125 |
| Claim-B (regime change-point) | #11 regime_shift_f1(v0_5), #4 recovery delay | #6 compute reallocation | task_success | TASK_1130 |
| Claim-C (foresight-conditioned action) | #10 rollout causal influence, #5 switch rate | #15 policy outcome, #16 rollout usefulness | task_success, raw tsr diff | TASK_1124 |

### task_success Declaration as FORBIDDEN PRIMARY METRIC

task_success is formally declared as a **FORBIDDEN primary evidence metric** for all claims.

Reason: dataset-invariant in offline eval (0.964/0.998 for all agents).

Allowed use:
- Sanity check only ("agent achieves task success of 0.X%")
- Context information ("difficulty level")

Forbidden use:
- "FRCG-LR outperforms X by Y% on task success"
- "task success proves C3/C6 advantage"

---

## Implementation Roadmap

| Priority | Metric | TASK | Gate |
|---|---|---|---|
| P0 | #2 AUROC + #3 window-AUROC | TASK_1123 | O-EVAL |
| P0 | #10 rollout causal influence | TASK_1124 | O-EVAL |
| P0 | #7 ppc (fair, wall-clock) | TASK_1125 | O-EVAL |
| P0 | eval config alignment (regime_shift_f1 to main config) | TASK_1126 | O-EVAL |
| P1 | #11 regime_shift_f1 v0_5 | TASK_1130 (prerequisite v0_5) | O-LOOP |
| P1 | #4 recovery delay | C1 timestamp infrastructure | O-LOOP |
| P2 | #18 OOD robotics | TASK_1116 | P6 |

---

## Gate O-EVAL Status

| 조건 | 상태 |
|---|---|
| 18 metric × 8 field 완성 | ✓ |
| claim-metric 1:1 매핑 표 | ✓ |
| task_success forbidden metric 선언 | ✓ |
| threshold-free C3 AUROC 구현 Codex task | ✓ (TASK_1123) |
| fair compute matched ppc Codex task | ✓ (TASK_1125) |

**Gate O-EVAL: PASS** (Codex task 실행 후 구현 완료 필요)
