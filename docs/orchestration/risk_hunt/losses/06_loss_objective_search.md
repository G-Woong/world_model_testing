# STEP 10 Loss Objective Search

date: 2026-05-18
gate: O-LOSS
source: 04_claim_redefinition.md, 01_global_risk_register.md
status: COMPLETE

---

## Loss Candidates (13 + 3 Wild = 16개)

### Loss #1 — Sequence Evidence Accumulation Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_accum = BCE(f_accum(h_1,...,h_t), y_t). h_t = hidden state of GRU over evidence history. 누적 evidence sequence가 wrong hypothesis에 대한 posterior를 올바르게 업데이트하도록 학습. |
| Required labels | true_wrong_hypothesis (per-step binary) |
| Required model outputs | EvidenceIntegratingFalsifier hidden state h_t |
| Risk addressed | RH-CORE-01, RH-THR-03, RH-LOSS-01, RH-ARC-03 |
| Why novel or useful | BCE는 instantaneous. 이 loss는 sequence-level evidence accumulation을 강제. |
| Why it may fail | GRU over short episodes (4-5 steps) → vanishing gradient. evidence sequence too short for meaningful accumulation. |
| Minimal test | EvidenceIntegratingFalsifier(history=10) on Stage B ckpt fine-tune → AUROC vs plain BCE |
| Codex implementation task | TASK_1120_step10_loss_evidence_accum |
| Priority | **P0** |

---

### Loss #2 — Contrastive Wrong-Hypothesis Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_contrast = max(0, margin - F_wrong + F_correct). wrong grammar episode에서 F_t_wrong > F_t_correct + margin를 강제. |
| Required labels | true_wrong_hypothesis, true_control_grammar (inference-forbidden! → eval path only) |
| Required model outputs | F_t per hypothesis |
| Risk addressed | RH-CORE-01, RH-LAT-01 |
| Why novel or useful | F_t가 wrong grammar에서 높고 correct grammar에서 낮도록 명시적 margin 강제. |
| Why it may fail | true_control_grammar는 inference-forbidden → training에서만 사용 가능. inference path에서 사용 불가. |
| Minimal test | contrastive loss fine-tune → F1 precision improvement vs BCE |
| Codex implementation task | N/A (P1, leakage check 필수) |
| Priority | P1 |

---

### Loss #3 — Regime Transition/Change-Point Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_regime_transition = BCE(P(change_t), is_shift_t). change-point head가 regime shift를 탐지하도록 학습. |
| Required labels | regime shift binary (v0_5에서만 가능) |
| Required model outputs | change_point_head output |
| Risk addressed | RH-REG-02, RH-DUP-01 |
| Why novel or useful | explicit regime change-point detection → C2 claim 활성화 |
| Why it may fail | v0_5 데이터 없으면 학습 불가. shift event rare → class imbalance. |
| Minimal test | v0_5 100-episode smoke → regime_shift_f1 > 0.1 |
| Codex implementation task | TASK_1130_step10_v0_5_generator (prerequisite) |
| Priority | P1 (v0_5 first) |

---

### Loss #4 — Value-of-Computation Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_voc = E[(V_planned - V_unplanned)^2 · I(plan_benefit > 0)]. planning이 value를 실제로 높일 때만 compute 투자를 보상. |
| Required labels | progress_delta (per-step) |
| Required model outputs | value head V(h, hypothesis_id) |
| Risk addressed | RH-FORE-03, RH-PCG-02, RH-LONG-02 |
| Why novel or useful | decision-relevant compute gate의 핵심. planning compute가 marginal benefit이 있을 때만 투자. |
| Why it may fail | V_planned - V_unplanned가 noisy → gradient signal 약함. |
| Minimal test | VoC loss fine-tune → planning gate threshold adaptation |
| Codex implementation task | TASK_1119_step10_arch_f_skeleton (partial) |
| Priority | P1 |

---

### Loss #5 — Policy Outcome Inconsistency Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_policy = ||action_with_foresight - action_without_foresight||_2. foresight가 실제로 action을 바꿀 때 loss가 낮아지도록. |
| Required labels | 없음 (self-supervised: rollout on vs off action comparison) |
| Required model outputs | action logits/embedding |
| Risk addressed | RH-FORE-01, RH-ARC-01 |
| Why novel or useful | foresight-to-policy causal link를 loss로 직접 강제. |
| Why it may fail | rollout이 action을 바꾸지 않으면 loss=0 → no gradient |
| Minimal test | foresight adapter + policy inconsistency loss → action divergence rate > 5% |
| Codex implementation task | TASK_1118_step10_arch_i_skeleton (partial) |
| Priority | P1 |

---

### Loss #6 — Action-Conditioned Prediction Mismatch Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_mismatch = ||predicted_effect(a, h) - actual_effect(a)||_2 when grammar_mismatch=True. wrong grammar 하에서의 action 결과 예측 오류를 추가로 페널티. |
| Required labels | effect_type (per-step), true_control_grammar (training only) |
| Required model outputs | world_model_heads effect prediction |
| Risk addressed | RH-THR-01, RH-CORE-01 |
| Why novel or useful | grammar mismatch 상황에서의 예측 오류를 falsification signal로 명시적 활용 |
| Why it may fail | true_control_grammar는 training-only → inference에서 mismatch detection이 어려워짐 |
| Minimal test | mismatch loss on → prediction accuracy on wrong-grammar episodes |
| Codex implementation task | N/A (P1) |
| Priority | P1 |

---

### Loss #7 — Calibration-Aware Falsification Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_calib = BCE + lambda * ECE_smooth(wrong_prob, y_wrong). predicted probability가 실제 precision과 일치하도록 smooth ECE 페널티 추가. |
| Required labels | true_wrong_hypothesis |
| Required model outputs | wrong_prob (sigmoid(F_t)) |
| Risk addressed | RH-THR-02, RH-CORE-01 |
| Why novel or useful | threshold-free claim을 위해 calibration이 필수. calibrated probability → threshold selection이 arbitrary하지 않음. |
| Why it may fail | smooth ECE computation overhead. N이 작으면 ECE 추정 noisy. |
| Minimal test | calibration loss → ECE < 0.025 (target from C5 gate) |
| Codex implementation task | TASK_1121_step10_loss_calibration_aware |
| Priority | **P0** |

---

### Loss #8 — Focal Loss for Rare Falsification Events

| Field | Value |
|---|---|
| Mathematical intuition | L_focal = -(1-p_t)^gamma * log(p_t). gamma=2가 default. rare positive (wrong hypothesis) 샘플에 더 높은 loss weight. |
| Required labels | true_wrong_hypothesis |
| Required model outputs | wrong_prob |
| Risk addressed | RH-LOSS-02 |
| Why novel or useful | class imbalance 해결: 627/(627+1352) ≈ 32% positive rate에서 precision 개선 가능 |
| Why it may fail | gamma tuning sensitivity. v0_4 imbalance가 32%로 mild → focal 효과 제한적. |
| Minimal test | focal(gamma=2) vs BCE → precision comparison on positive class |
| Codex implementation task | TASK_1121_step10_loss_calibration_aware (partial) |
| Priority | P1 |

---

### Loss #9 — Temporal Consistency Loss for F_t

| Field | Value |
|---|---|
| Mathematical intuition | L_temporal = ||F_t - F_{t-1}||^2 * (1 - y_shift). regime shift 없는 상황에서 F_t가 급변하지 않도록 temporal smoothness 강제. |
| Required labels | regime shift (v0_5) or per-step stability flag |
| Required model outputs | F_t sequence |
| Risk addressed | RH-THR-03 |
| Why novel or useful | F_t temporal consistency → "falsification state" claim 강화 (instantaneous score 아님) |
| Why it may fail | too strong smoothing → F_t misses real falsification events. lambda tuning critical. |
| Minimal test | temporal consistency loss → F_t consecutive step variance < 0.1 (within-episode) |
| Codex implementation task | TASK_1120_step10_loss_evidence_accum (partial) |
| Priority | P1 |

---

### Loss #10 — Decision-Relevance Weighted Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_dr = BCE(F_t, y_wrong) * w_decision where w_decision = abs(V_alt - V_current). decision-relevant 상황 (alt hypothesis가 significantly better)에서 falsification loss에 더 높은 weight. |
| Required labels | true_wrong_hypothesis |
| Required model outputs | F_t, value function V |
| Risk addressed | RH-PCG-01, RH-PCG-02 |
| Why novel or useful | falsification signal이 decision-relevant 상황에서 더 정확하도록 training. |
| Why it may fail | value function 품질에 의존. V이 noisy하면 weight도 noisy. |
| Minimal test | decision-relevance weighted → improvement in C6 ppc vs unweighted |
| Codex implementation task | N/A (P2) |
| Priority | P2 |

---

### Loss #11 — Rollout Usefulness Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_rollout = BCE(useful_rollout, I(action_changed_by_rollout)). rollout이 actual action selection을 바꿀 때를 예측하는 meta-loss. |
| Required labels | 없음 (self-supervised: action_changed = action_with_rollout ≠ action_without_rollout) |
| Required model outputs | rollout prediction quality |
| Risk addressed | RH-FORE-01, RH-PCG-02 |
| Why novel or useful | "useful rollout" prediction → VoC gate의 better proxy. |
| Why it may fail | action_changed label은 offline replay에서 counterfactual 필요. |
| Minimal test | rollout usefulness score vs actual action divergence rate correlation |
| Codex implementation task | TASK_1124_step10_foresight_causal (partial) |
| Priority | P1 |

---

### Loss #12 — Latent Control Sufficiency Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_sufficiency = ||z - T(a, r)||^2 where T is a target encoder update-free copy. latent z가 control action a와 reward r을 예측하기에 sufficient하도록. |
| Required labels | progress_delta (as reward proxy) |
| Required model outputs | z_grammar, z_regime, z_state |
| Risk addressed | RH-PCG-01, RH-LAT-02, RH-LAT-03 |
| Why novel or useful | prediction-control gap 해결: latent가 control performance와 직접 연결. |
| Why it may fail | T update-free copy → training instability (similar to BYOL collapse). |
| Minimal test | sufficiency loss → z probe accuracy on downstream action prediction |
| Codex implementation task | N/A (P2) |
| Priority | P2 |

---

### Loss #13 — Reconstruction-Free Latent Alignment Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_align = ||z_t - sg(z_{t+1})||^2 / (||z_t|| * ||sg(z_{t+1})||). JEPA-style: consecutive latent이 cosine-aligned. no reconstruction needed. |
| Required labels | 없음 (self-supervised temporal consistency) |
| Required model outputs | z_state sequence |
| Risk addressed | RH-LAT-03, RH-LOSS-01 |
| Why novel or useful | JEPA/I-JEPA inspiration: reconstruction-free latent alignment → task-relevant representation. |
| Why it may fail | collapse risk (z_t → same vector). need non-collapse regularizer. |
| Minimal test | JEPA loss on → latent cosine similarity consecutive steps > 0.7, no collapse |
| Codex implementation task | N/A (P1) |
| Priority | P1 |

---

## Wild Hypothesis Losses (3개)

### Loss #14 (WH-1) — CLT-Based Falsification Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_clt = max(0, |z_score(error_window)| - margin)^2. sliding window n=50 prediction error의 z-score가 |z|>2.0이면 high loss. N(0,σ²) 가정 하에서 distribution shift 탐지를 loss로 학습. |
| Required labels | prediction_error (per-step, self-computed) |
| Required model outputs | predicted effect vs actual effect |
| Risk addressed | RH-CORE-01, RH-THR-02 |
| Why novel or useful | learnable threshold 없이 statistical falsification. CLT로 threshold-free → calibration 자동. |
| Why it may fail | i.i.d. 가정 위반 (temporal correlation). n=50 requires 50-step episodes (v0_4는 4-5 steps). |
| Minimal test | CLT detector on v0_5 longer episodes (50-step) → AUROC vs plain BCE |
| Codex implementation task | TASK_1122_step10_loss_clt_falsification |
| Priority | **P0** (wild hypothesis test, TASK_1122) |

**Wild Hypothesis WH-1 details**:
- sliding window size n ∈ {20, 50, 100}
- z_score = (mean_error - mu_0) / (sigma_0 / sqrt(n))
- mu_0, sigma_0 = running statistics from episode history
- falsification condition: |z_score| > 2.0 (95% CI)
- expected benefit: distribution-free threshold; adapts to episode statistics automatically

---

### Loss #15 (WH-2) — HMM Regime Belief Forward-Backward Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_hmm = -log P(O|lambda) where lambda = (A, B, pi) are HMM transition/emission/prior matrices. forward-backward algorithm gradient for regime sequence. |
| Required labels | regime sequence (v0_5 only) |
| Required model outputs | z_regime as emission |
| Risk addressed | RH-REG-02, RH-DUP-01 |
| Why novel or useful | Markov regime belief → change-point detection with explicit prior. generative model approach. |
| Why it may fail | Markov assumption. HMM training instability. requires v0_5 regime sequence labels. |
| Minimal test | HMM forward-backward on v0_5 → regime_shift_f1 vs naive regime BCE |
| Codex implementation task | N/A (optional WH-2) |
| Priority | P2 (optional) |

---

### Loss #16 (WH-3) — Tripartite Consistency Loss

| Field | Value |
|---|---|
| Mathematical intuition | L_tripartite = ||W(s,a) - pi(s) - F(s,a)||^2. world model W + policy pi + falsification monitor F 3-way consistency loss. unstable fixed point → wrong hypothesis signal. |
| Required labels | 없음 (self-supervised tripartite) |
| Required model outputs | world model, policy, falsification outputs |
| Risk addressed | RH-FORE-01, RH-PCG-01, RH-PCG-02 |
| Why novel or useful | three-body dynamics analogy — instability in W-pi-F interaction = wrong hypothesis. |
| Why it may fail | abstract concept — difficult to make into concrete training signal. convergence unclear. |
| Minimal test | L_tripartite on → action divergence rate measurement (indirect) |
| Codex implementation task | N/A (optional WH-3, P2) |
| Priority | P2 (optional) |

---

## P0 Selection (3개)

### P0-1: Loss #1 — Sequence Evidence Accumulation

**근거**:
- RH-CORE-01 (threshold/proxy artifact) 직접 해결 — instantaneous BCE에서 sequence accumulation으로
- Architecture B (Evidence-Integrating)와 직접 결합
- minimal test: Stage B ckpt fine-tune → AUROC comparison

**TASK**: TASK_1120_step10_loss_evidence_accum

---

### P0-2: Loss #7 — Calibration-Aware Falsification

**근거**:
- RH-THR-02 (single threshold uncalibrated) 직접 해결
- C5 calibration ECE < 0.025 gate 달성 경로
- minimal test: ECE measurement after isotonic regression

**TASK**: TASK_1121_step10_loss_calibration_aware

---

### P0-3: Loss #14 (WH-1) — CLT-Based Falsification

**근거**:
- Wild hypothesis WH-1 정식 검증 (Loop-WH-1)
- threshold-free claim을 statistical 방식으로 지원
- minimal test: AUROC > 0.7 on longer episodes

**TASK**: TASK_1122_step10_loss_clt_falsification

---

## Decision Criteria

- KEEP: 각 P0 loss가 BCE (baseline) 대비 primary metric > 5% improvement
- MODIFY: 0-5% improvement → hypothesis 보강 후 재시도
- REJECT: ≤0% improvement → BCE가 sufficient → loss 격하

---

## Gate O-LOSS Status

| 조건 | 상태 |
|---|---|
| 13+3 후보 × 9 field 완성 | ✓ (16 losses) |
| 3 P0 선정 | ✓ (Loss #1, #7, #14) |
| 각 P0의 minimal test = Stage B baseline 대비 | ✓ |
| 각 P0의 Codex task 연결 | ✓ (TASK_1120, 1121, 1122) |

**Gate O-LOSS: PASS**
