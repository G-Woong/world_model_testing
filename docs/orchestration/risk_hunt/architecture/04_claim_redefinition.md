# STEP 10 Claim Redefinition

date: 2026-05-18
gate: O-CLAIM
source: 01_global_risk_register.md, 00_current_state_truth_table.md
status: COMPLETE

---

## 1. Threshold Demotion Rationale

### 기존 약한 claim (격하)
> "F_t가 threshold를 넘으면 wrong hypothesis를 감지한다."

**격하 이유**:
- tau_f=0.0은 inference-time decision rule이며 learned mechanism이 아님 (RH-CORE-01)
- calibration 없는 single threshold는 distribution shift에 fragile (RH-THR-02)
- no_state_change→type3 proxy는 learned falsification이 아닌 heuristic (RH-THR-01)
- threshold tuning은 p-hacking 위험 (RH-LEAK-02)

**격하 결과**:
- Threshold-based falsification detector = **보조 검출기 (auxiliary detector)**
- 단독으로 main claim에 사용 불가
- "threshold-based detector"로 명시적 레이블링 필요

---

## 2. Three Strengthened Claims

### Claim-A: Evidence-Integrating Falsification + Decision-Relevant Compute (CORE)

**Statement**:
> FRCG-WM agent accumulates multi-step prediction mismatch, action outcome inconsistency, and regime belief instability into a falsification state that selectively reallocates planning compute when the current dynamics hypothesis becomes decision-relevantly unreliable.

**한국어**:
> 단순 점수 문턱값이 아니라 누적 예측 실패 / 행동 결과 불일치 / regime belief 흔들림 / 정책 실패 패턴을 통합해서 현재 가설이 의사결정 위험 수준으로 틀렸는지 판단하고, 그때 planning compute를 재배치한다.

**기존 C1~C6 매핑**:
| 기존 claim | 신 claim 매핑 |
|---|---|
| C3 falsification detection | Primary — falsification state (learned) |
| C6 compute-rational planning | Primary — compute reallocation |
| C1 persistence | Secondary — wrong hypothesis tracking duration |
| C5 calibration | Secondary — ECE of falsification state |

**Required metrics**:
- Primary: threshold-free AUROC/AUPRC on wrong_prob
- Primary: evidence accumulation quality (window-AUROC, window=10)
- Primary: progress_per_compute (fair compute matched)
- Secondary: wrong-hypothesis recovery delay
- Secondary: ECE after calibration

**Required baselines**:
- threshold-only detector (tau_f sweep, no accumulation)
- uncertainty-gated planner (BASE: ABL-023)
- always-plan no-gate (ABL-036, faithful version TASK_1132)

**Required ablations**:
- ABL: no evidence accumulation (instant detection only, Loss #1 absent)
- ABL: no falsification gate (ABL-022)
- ABL: no compute gate (ABL-036)
- ABL-015: no grammar loss (control)

**Falsification condition**:
- Threshold-based C3 F1 < 0.3 AND AUROC < 0.6 → Claim-A weak → report honestly
- AUROC > 0.6 AND ppc ratio > 2× (fair matched) → Claim-A alive

---

### Claim-B: Regime Change-Point Detection + Alternative Hypothesis Adoption (REGIME)

**Statement**:
> FRCG-WM agent maintains a belief over interaction regimes and detects change-points in regime transitions, enabling timely adoption of alternative control-grammar hypotheses when the current regime shifts.

**한국어**:
> FRCG-WM 에이전트는 interaction regime에 대한 belief를 유지하고, regime 전환 시점을 change-point로 탐지하여 현재 regime이 바뀔 때 대안적 control-grammar 가설로 적시에 전환한다.

**기존 C1~C6 매핑**:
| 기존 claim | 신 claim 매핑 |
|---|---|
| C2 regime_shift_f1 | Primary — regime change-point detection |
| C1 persistence | Secondary — transition delay measurement |

**Required metrics**:
- Primary: regime_shift_f1 (v0_5 multi-regime data 필요)
- Primary: wrong-hypothesis recovery delay (regime shift 이후)
- Secondary: alternative hypothesis adoption rate

**Required baselines**:
- ABL-001 (l_regime=0.0): regime latent collapse → C2 collapse 기대
- Classical change-point detection (CUSUM, BOCPD) as simple baseline

**Required ablations**:
- ABL-001 (no_regime): C2 collapse 확인 (TASK_1127)
- ABL-003 (merged_regime_grammar): C2 + Claim-A collapse 확인 (TASK_1128)

**Data requirement**: v0_5 multi-regime generator (TASK_1130) 필수

**Falsification condition**:
- v0_5에서 regime_shift_f1 < 0.1 → Claim-B 제거
- ABL-001 no collapse → disentanglement 근거 없음 → Claim-B 약화

---

### Claim-C: Foresight-Conditioned Action Switch Under Wrong-Grammar Persistence (FORESIGHT)

**Statement**:
> FRCG-WM agent uses world model rollout to evaluate alternative hypothesis quality and switches to a rewritten action when the falsification state indicates that continuing under the current grammar would yield suboptimal outcomes.

**한국어**:
> FRCG-WM 에이전트는 world model rollout을 통해 대안 가설의 품질을 평가하고, falsification state가 현재 grammar 하에서 최적이 아닌 결과를 예측할 때 rewrite된 행동으로 전환한다.

**기존 C1~C6 매핑**:
| 기존 claim | 신 claim 매핑 |
|---|---|
| C3 + C6 combined | Primary — foresight-to-policy link |
| Novelty | Primary — falsification-guided planning novelty |

**Required metrics**:
- Primary: rollout-to-action causal influence (action divergence rate: rollout on vs off)
- Primary: action switch rate after falsification (post-falsification planning activation rate)
- Secondary: policy outcome improvement after foresight (v0_5 harder tasks에서)

**Required baselines**:
- no-rollout ablation (ABL-011): foresight 없을 때 성능
- always-plan (ABL-036 faithful): rollout이 항상 있을 때

**Required ablations**:
- ABL-011: no rollout (foresight 제거)
- ABL-024: no alternative hypothesis
- ABL-022: no falsification gate

**Falsification condition**:
- rollout divergence rate < 5% → foresight cosmetic → Claim-C 제거
- action switch rate < 2% → planning gate가 효과 없음 → Claim-C 약화

---

## 3. Claim Mapping Summary

| Strengthened Claim | Primary metric | Secondary metric | Forbidden metric | Gate condition |
|---|---|---|---|---|
| Claim-A (evidence-integrating falsification) | AUROC/AUPRC, ppc (fair) | ECE, recovery delay | task_success | AUROC > 0.6 AND ppc ratio > 2× |
| Claim-B (regime change-point) | regime_shift_f1 (v0_5) | adoption rate | task_success | regime_shift_f1 > 0.3 on v0_5 |
| Claim-C (foresight-conditioned action) | rollout divergence rate, action switch rate | policy outcome | task_success, raw tsr diff | divergence rate > 10% |

---

## 4. Old C1~C6 → New Claim Status

| Old | New Status | New Mapping | Paper wording |
|---|---|---|---|
| C1 persistence | CONDITIONAL | Claim-A secondary + Claim-B secondary | "wrong-hypothesis persistence delay (v0_5 required)" |
| C2 regime_shift_f1 | CONDITIONAL | Claim-B primary | "regime change-point detection (requires v0_5 data)" |
| C3 falsification detection | REDESIGNED | Claim-A primary (AUROC + accumulation) + Claim-C | "falsification state AUROC=X.XX, ppc=Y.Y× (fair matched)" |
| C4 task_success | DEMOTED | FORBIDDEN as primary metric | — |
| C5 calibration ECE | CONDITIONAL | Claim-A secondary | "calibration ECE=X.XXX (requires calibration training)" |
| C6 ppc advantage | REDESIGNED | Claim-A primary (fair matched) | "ppc ratio Z.Z× (fair compute matched, wall-clock)" |

---

## 5. Threshold Demotion Declaration

**공식 선언**:

Threshold-based falsification (tau_f=0.0 decision boundary on wrong_prob) is hereby demoted from **primary mechanism** to **auxiliary detector**.

Rationale:
1. tau_f is an inference-time rule, not a learned component.
2. Performance depends critically on no_state_change→type3 proxy heuristic.
3. Without evidence accumulation, threshold-based detection is instantaneous and fragile.

New role:
- Threshold-based detector = "simple baseline" for comparison against learned evidence-integrating state.
- In paper: "As a simple detector baseline, threshold-based F_t achieves F1=0.539/0.587. The learned evidence-integrating state (Claim-A) further achieves AUROC=X.XX."

---

## 6. Gate O-CLAIM Status

| 조건 | 상태 |
|---|---|
| 3개 strengthened claim 명시 | ✓ (A: Evidence-Integrating, B: Regime Change-Point, C: Foresight-Conditioned) |
| 각 claim testable | ✓ (metric/baseline/ablation 정의됨) |
| threshold demoted from main mechanism | ✓ |
| 기존 C1~C6와 매핑 표 작성 | ✓ |

**Gate O-CLAIM: PASS**
