# STEP 10 Architecture Candidate Matrix

date: 2026-05-18
gate: O-ARCH
source: 04_claim_redefinition.md, 01_global_risk_register.md
status: COMPLETE

---

## Architecture Candidates (10개 × 11 field)

### A. Current FRCG-LR Fixed

| Field | Value |
|---|---|
| What it changes | 없음 — 현재 상태 유지 |
| RH-IDs addressed | None (baseline) |
| Expected benefit | 현재 C3 F1=0.539/0.587, C6 14.9× baseline |
| Required code change | 없음 |
| Required dataset field | 없음 |
| Required loss | BCE (현재) |
| Required metric | threshold-based F1, ppc |
| Minimal viable test | 현재 eval config 재실행 |
| Failure condition | C3 F1 regression 발생 시 |
| Novelty contribution | baseline |
| Implementation priority | P0 (reference baseline) |

---

### B. Evidence-Integrating Falsification Recurrent State (RNN/GRU/Transformer)

| Field | Value |
|---|---|
| What it changes | falsification_score()를 instantaneous scalar에서 recurrent state로 변환. 연속 스텝의 prediction mismatch, action outcome, regime belief instability를 통합. |
| RH-IDs addressed | RH-CORE-01 (threshold/proxy artifact), RH-THR-01 (short-circuit dependency), RH-THR-03 (temporal inconsistency), RH-LOSS-01 (BCE 한계), RH-ARC-03 (long-horizon) |
| Expected benefit | F_t가 단발 score가 아닌 evidence-integrating state → AUROC 개선, temporal consistency 개선 |
| Required code change | src/frcgw/falsification/ 신규 EvidenceIntegratingFalsifier 클래스. falsification_score() wrapper 교체. |
| Required dataset field | 없음 (공개 observation에서 계산) |
| Required loss | sequence evidence accumulation loss (Loss #1) |
| Required metric | AUROC/AUPRC (threshold-free), evidence accumulation quality (window-AUROC) |
| Minimal viable test | unit test: EvidenceIntegratingFalsifier(history=10).forward(obs_seq) → F_t 시계열. AUROC vs baseline A. |
| Failure condition | AUROC < baseline A → recurrent state가 instantaneous보다 나쁨 |
| Novelty contribution | evidence-integrating falsification state (sequential hypothesis testing) |
| Implementation priority | **P0** |

---

### C. Regime Belief State + Change-Point Head

| Field | Value |
|---|---|
| What it changes | z_regime head에서 explicit change-point posterior 산출. P(change | history) 학습. |
| RH-IDs addressed | RH-DUP-01 (v0_4 no regime shift), RH-REG-02 (no change-point head), RH-REG-03 (OOD meaningless) |
| Expected benefit | regime_shift_f1 > 0 on v0_5 multi-regime data |
| Required code change | world_model_heads.py에 change_point_head 추가. metrics.py regime_shift_f1 연결. |
| Required dataset field | v0_5 multi-regime (intra-episode shift) 필수 |
| Required loss | Regime transition/change-point loss (Loss #3) |
| Required metric | regime_shift_f1 (v0_5 only) |
| Minimal viable test | v0_5 100-episode smoke → regime_shift_f1 > 0.1 |
| Failure condition | regime_shift_f1 = 0.0 on v0_5 → change-point head ineffective |
| Novelty contribution | explicit regime belief tracking in web agent |
| Implementation priority | P1 (v0_5 data 준비 후) |

---

### D. Task-Relevant Latent Without Reconstruction Objective

| Field | Value |
|---|---|
| What it changes | reconstruction head 제거. task-relevant prediction loss만 유지. |
| RH-IDs addressed | RH-LAT-03 (reconstruction vs task-relevant) |
| Expected benefit | latent representation이 task 결과에 relevant한 정보만 encoding |
| Required code change | world_model_heads.py reconstruction head 제거 또는 비활성화 |
| Required dataset field | 없음 |
| Required loss | task-relevant prediction loss만 (effect, progress, failure) |
| Required metric | task-relevant latent probe accuracy |
| Minimal viable test | reconstruction head ablation → F_t quality 비교 |
| Failure condition | reconstruction 제거 후 F_t variance < baseline → reconstruction이 regularizer 역할 |
| Novelty contribution | JEPA-style task-relevant latent |
| Implementation priority | P1 |

---

### E. JEPA-Style Latent Consistency Objective

| Field | Value |
|---|---|
| What it changes | 미래 latent prediction 일관성 loss 추가. encoder의 "same episode = similar latent" constraint. |
| RH-IDs addressed | RH-LAT-03 (reconstruction bias), RH-LOSS-01 (BCE only) |
| Expected benefit | latent continuity → temporal falsification signal 안정화 |
| Required code change | 신규 latent_consistency_loss() in losses.py |
| Required dataset field | 없음 |
| Required loss | Reconstruction-free latent alignment loss (Loss #13) |
| Required metric | latent consistency (consecutive step embedding similarity) |
| Minimal viable test | JEPA loss on → consecutive latent cosine similarity > 0.8 |
| Failure condition | latent consistency < 0.5 → JEPA objective ineffective |
| Novelty contribution | JEPA-inspired web agent latent |
| Implementation priority | P1 |

---

### F. Value-of-Computation Gated Planner

| Field | Value |
|---|---|
| What it changes | fixed k=3 rollout을 동적 k로 대체. compute budget이 decision quality에 marginal benefit이 있을 때만 rollout 확장. |
| RH-IDs addressed | RH-FORE-03 (k fixed), RH-PCG-02 (rollout-policy link weak), RH-LONG-02 (adaptive depth), RH-EVAL-02 (fair compute) |
| Expected benefit | compute 효율 증가 + ABL-036 faithful replacement (진짜 no-gate ablation) |
| Required code change | planner.py: adaptive k gate. ComputeBudgetLog: actual wall-clock 기록. |
| Required dataset field | 없음 |
| Required loss | Value-of-computation loss (Loss #4) |
| Required metric | ppc (fair compute matched), rollout usefulness score |
| Minimal viable test | adaptive k=1 vs k=3 ppc 비교. ABL-036 faithful (FRCG model forward 강제) ppc 비교. |
| Failure condition | adaptive k < fixed k=1 ppc → compute adaptation ineffective |
| Novelty contribution | value-of-computation adaptive planning depth |
| Implementation priority | **P0** |

---

### G. Policy-Conditioned Rollout Evaluator

| Field | Value |
|---|---|
| What it changes | rollout quality를 policy outcome과 연결하는 evaluator module 추가. rollout이 action을 실제로 바꾸는지 측정. |
| RH-IDs addressed | RH-FORE-01 (foresight-policy gap), RH-PCG-02 (prediction-control gap) |
| Expected benefit | foresight-to-policy causal influence 측정 가능. Claim-C 직접 지원. |
| Required code change | 신규 PolicyConditionedRolloutEvaluator. frcg_agent.py action comparison hook. |
| Required dataset field | 없음 |
| Required loss | Rollout usefulness loss (Loss #11) |
| Required metric | rollout-to-action causal influence (action divergence rate) |
| Minimal viable test | rollout on vs off → action divergence rate > 5% |
| Failure condition | divergence rate < 5% → rollout cosmetic |
| Novelty contribution | rollout utility measurement in planning |
| Implementation priority | P1 |

---

### H. Alternative Hypothesis Scorer (Margin-Based)

| Field | Value |
|---|---|
| What it changes | alt hypothesis 선택을 value 비교에서 margin-based score로 개선. evidence-conditional alt scoring. |
| RH-IDs addressed | RH-FORE-04 (evidence-blind alt selection), RH-LAT-01 (grammar probe accuracy) |
| Expected benefit | evidence-aware alt selection → false positive 감소 |
| Required code change | propose() mode="evidence_aware" 추가. falsification.py evidence-conditioned alt scoring. |
| Required dataset field | 없음 |
| Required loss | Alternative hypothesis scorer margin loss |
| Required metric | alt hypothesis adoption rate, false positive rate |
| Minimal viable test | evidence-aware vs evidence-blind → precision/recall tradeoff |
| Failure condition | evidence-aware precision < evidence-blind → evidence condition harmful |
| Novelty contribution | evidence-conditioned alternative hypothesis selection |
| Implementation priority | P1 |

---

### I. Foresight-to-Policy Adapter

| Field | Value |
|---|---|
| What it changes | rollout 예측 결과를 policy에 직접 conditioning하는 adapter 추가. world model representation이 action selection에 직접 영향. |
| RH-IDs addressed | RH-FORE-01 (foresight-policy gap), RH-ARC-01 (no foresight adapter), RH-CORE-02 (lr_scorer 미연결) |
| Expected benefit | foresight-to-policy causal link 강화. rollout-off vs rollout-on divergence rate 증가. |
| Required code change | 신규 ForesightPolicyAdapter. text_frcg_plan에 rollout representation conditioning 추가. |
| Required dataset field | 없음 |
| Required loss | Policy outcome inconsistency loss (Loss #5) |
| Required metric | action divergence rate (rollout on vs off), policy outcome improvement |
| Minimal viable test | adapter on vs off → action divergence rate 비교 |
| Failure condition | divergence rate 개선 < 5% → adapter ineffective |
| Novelty contribution | foresight-conditioned policy adapter |
| Implementation priority | **P0** |

---

### J. Long-Horizon Adaptive Lookahead Controller

| Field | Value |
|---|---|
| What it changes | episode 길이에 따라 rollout depth k를 적응적으로 조정. 긴 에피소드에서는 더 깊은 lookahead. |
| RH-IDs addressed | RH-LONG-01 (short episode only), RH-LONG-02 (fixed k) |
| Expected benefit | long-horizon task에서 C6 ppc advantage 유지 |
| Required code change | planner.py: episode-length aware k adjustment |
| Required dataset field | v0_5 longer episodes 필요 |
| Required loss | 없음 (heuristic k adjustment) |
| Required metric | C6 ppc vs episode length curve |
| Minimal viable test | k=adaptive vs k=3 on v0_5 longer episodes |
| Failure condition | ppc degrades with longer episodes regardless of k |
| Novelty contribution | adaptive long-horizon planning |
| Implementation priority | P2 (v0_5 first) |

---

## P0 Selection (3개) + 근거

### P0-1: Architecture B — Evidence-Integrating Falsification Recurrent State

**근거**:
- CRITICAL risk RH-CORE-01 직접 해결 (threshold/proxy artifact → learned mechanism)
- Claim-A의 핵심 ("evidence-integrating falsification state") 직접 구현
- minimal test: unit test만으로 baseline A 대비 AUROC 비교 가능
- no dataset change needed
- Loss #1 (sequence evidence accumulation)과 직접 결합

**Expected deliverable**: `src/frcgw/falsification/evidence_integrating.py` skeleton + unit test

---

### P0-2: Architecture I — Foresight-to-Policy Adapter

**근거**:
- CRITICAL risk RH-FORE-01 직접 해결 (foresight-policy causal gap)
- Claim-C의 핵심 ("foresight-conditioned action switch") 직접 지원
- RH-ARC-01, RH-CORE-02 부분 해결
- minimal test: rollout on/off divergence rate 측정 (new logging hook)

**Expected deliverable**: foresight causal influence logger + intervention test hook

---

### P0-3: Architecture F — Value-of-Computation Gated Planner

**근거**:
- HIGH risk RH-EVAL-02 직접 해결 (C6 fair compute matching)
- RH-FORE-03 (fixed k), RH-LONG-02 (adaptive depth) 해결
- ABL-036 faithful implementation (TASK_1132) 의존
- minimal test: fair ppc 비교 (wall-clock denominator)
- TASK_1125, TASK_1132와 직접 연결

**Expected deliverable**: adaptive k planner + wall-clock logger + fair ppc metric

---

## Gate O-ARCH Status

| 조건 | 상태 |
|---|---|
| 10 후보 × 11 field 완성 | ✓ |
| 3 P0 선정 | ✓ (B, I, F) |
| 각 P0의 minimal viable test 정의 | ✓ |
| 각 P0의 codex task 연결 | ✓ (TASK_1117, TASK_1118, TASK_1119) |

**Gate O-ARCH: PASS**
