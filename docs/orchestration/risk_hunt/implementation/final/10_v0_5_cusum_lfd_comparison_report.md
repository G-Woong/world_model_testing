# Phase 9 v0_5 Oracle-Free: CUSUM/SPRT vs LFD Comparison Report

```yaml
report_id: phase9_v0_5_cusum_lfd_oracle_free_001
date: 2026-05-19
phase: 9
verdict: LFD_PARTIALLY_BEATS_CUSUM_NEEDS_CALIBRATION
revised_verdict_recommendation: LFD_AUROC_ADVANTAGE_UNCONFIRMED_ORIGIN_NOT_DEPLOYABLE_AS_GATE
script: scripts/phase9_v0_5_cusum_lfd_eval.py
artifacts:
  - outputs/risk_hunt/implementation/evals/v0_5_oracle_free_dataset_audit.json
  - outputs/risk_hunt/implementation/evals/cusum_sprt_v0_5_oracle_free_metrics.json
  - outputs/risk_hunt/implementation/evals/lfd_v0_5_oracle_free_metrics.json
  - outputs/risk_hunt/implementation/evals/comparison_v0_5_oracle_free.json
critics_run:
  - mathematical-validity-critic: NEEDS_REVISION
  - reviewer-2-attack-agent: HIGH_RISK
  - frcgw-data-leakage-auditor: PASS
  - failure-interpretation-critic: WEAKENED
  - novelty-threat-scout: NOVELTY_AT_RISK
```

---

## 1. 실험 조건

| 항목 | 값 |
|---|---|
| 실행 모드 | ORACLE-FREE (collect_episode() 사용, oracle simulation 없음) |
| N_collect | 250 v0_5 에피소드 |
| N_train / N_eval | 200 / 50 (index 기반 분할) |
| N_seeds (LFD) | 3 |
| Grammar pairs | search_form ↔ required_dropdown (2개 pair만) |
| Max steps | 12 |
| Switch step | mean=6.0, min=2, max=10 |
| CUSUM k | 0.3, h sweep {0.5, 1.0, 2.0, 3.0, 4.0} |
| SPRT A | primary=3.0, fallback=2.0, B=0.1 |
| LFD epochs | 15, lr=5e-4, alarm_threshold=0.5 (고정) |
| Proxy OFF | alarm_threshold 사전 고정, 결과 후 튜닝 없음 |

### 이전 Phase 9 (oracle-probe)와의 차이

Phase 9 기존 eval (`scripts/phase9_lfd_eval.py`)은 `SYNTHETIC_ORACLE_PROBE` 모드였다.
`collect_episode()`가 v0_5 switch를 처리하지 못하던 시기에 oracle 시뮬레이션으로 effect stream을 생성하였다.

이 두 평가의 수치는 **직접 비교 불가**:
- Oracle-probe: CUSUM AUROC=0.913, LFD AUROC=0.947 (N=250 mixed, oracle-simulated)
- Oracle-free: CUSUM AUROC=0.692, LFD AUROC=0.842 (N=50 all-switch, genuine effects)

이 보고서의 모든 수치는 **oracle-free** 기준이다.

---

## 2. Dataset Audit 결과

| 항목 | 값 | 판정 |
|---|---|---|
| n_episodes | 250 | — |
| n_switch_episodes | 250 (100%) | 주의: n_stable=0 |
| post_switch_wrong_rate | 14.73% | PASS (>0, <100%) |
| pre_switch_wrong_rate | 37.66% | 참조값 |
| shared_action_success_count | 33 | PASS (>0) |
| vocabulary_mismatch_count | 465 | 참조값 |
| leakage_clean | True | **PASS** |
| integrity_all_pass | True | **PASS** |

**주의**: n_stable_episodes=0. 전체 eval set이 switch episode로만 구성된다.
이는 FAR 계산의 "negative class" 정의를 pre-switch steps으로만 제한하며,
pre-switch wrong_rate=37.66%가 이미 오염된 negative class를 만든다.
(mathematical-validity-critic CRITICAL finding)

**Data Leakage Audit: PASS**
- `regime_switch_t`: eval metric 계산에만 사용, model forward에 미전달 ✓
- `true_wrong_hypothesis`: loss supervision signal / eval ground truth (EVALUATION_ONLY) ✓
- `effect_type`: PublicEffect의 public 필드, oracle leakage 아님 ✓

---

## 3. Eval Set (N=50) 비교표

| Metric | CUSUM (h=2.0) | SPRT (A=3.0) | LFD seed0 | LFD mean±std (3 seeds) |
|---|---|---|---|---|
| **AUROC** | 0.692 | 0.692 | 0.841 | **0.842 ± 0.003** |
| **AUPRC** | 0.479 | 0.479 | 0.704 | **0.707 ± 0.012** |
| **regime_shift_F1** | **0.237** | **0.237** | 0.178 | 0.178 ± 0.000 |
| detection_delay (mean) | 0.231 | 0.192 | 0.000 | 0.000 ± 0.000 |
| FAR/step | **0.086** | **0.086** | 0.548 | 0.382 ± 0.127 |
| run_length_concentration | N/A | N/A | 0.854 | — |
| fair_ppc_ratio (vs CUSUM) | 1.0 | — | 0.000 | — |

### CUSUM threshold sweep (all 250 episodes)

| h | detection_delay | FAR | F1 | AUROC |
|---|---|---|---|---|
| 0.5 | 0.000 | 0.138 | 0.152 | 0.706 |
| 1.0 | 0.063 | 0.104 | 0.216 | 0.706 |
| **2.0** | **0.264** | **0.080** | **0.297** | **0.706** |
| 3.0 | 1.605 | 0.052 | 0.260 | 0.706 |
| 4.0 | 2.521 | 0.046 | 0.136 | 0.706 |

### SPRT A sweep (eval set N=50)

| A | alarms (/ 50) | FAR | F1 |
|---|---|---|---|
| 2.0 | 34 | 0.113 | 0.167 |
| **3.0** | **26** | **0.086** | **0.237** |

---

## 4. LFD 학습 상세

| Seed | final_loss | wrong_prob_mean | wrong_prob_std | FAR | F1 | AUROC |
|---|---|---|---|---|---|---|
| 0 | 1.536 | 0.477 | 0.414 | 0.548 | 0.178 | 0.841 |
| 1 | 1.532 | 0.309 | 0.357 | 0.359 | 0.178 | 0.839 |
| 2 | 1.532 | 0.240 | 0.335 | 0.239 | 0.178 | 0.845 |

**train_loss 관찰**:
- 3 seed 모두 1.48~1.65에서 시작하여 1.53 수준에서 진동 (15 epochs 내 단조 감소 없음)
- log(2)=0.693보다 훨씬 높음
- **중요**: loss는 `L_seq_falsification + L_run_length_posterior` 합산. 단순 binary BCE random baseline
  (=log(2))과 직접 비교 불가. 각 항 분리 측정이 필요 (mathematical-validity-critic RECOMMENDATION)

**wrong_prob_mean의 seed간 분산**: 0.477 → 0.309 → 0.240 (범위 0.237)
이것은 AUROC seed stability (std=0.003)와 상반된다. calibration 측면에서
세 모델이 다른 출력 scale을 가지면서 ranking order는 비슷하다는 의미다.

---

## 5. 핵심 판단

### Verdict

**기록된 verdict**: `LFD_PARTIALLY_BEATS_CUSUM_NEEDS_CALIBRATION`

**failure-interpretation-critic 권고 (합의)**: 더 보수적인 표현이 필요하다.

> "학습 실패 (loss 비감소) 상태에서 'calibration이 필요한 후보'라 표현하는 것은
> 학습 자체가 성공했다는 가정을 내포한다. 이 가정이 성립하지 않는다."

**권고 revised verdict**:
`LFD_AUROC_ADVANTAGE_UNCONFIRMED_ORIGIN_NOT_DEPLOYABLE_AS_GATE`

**판정 근거**:

| 조건 | 결과 | 판정 |
|---|---|---|
| LFD AUROC > CUSUM AUROC (+0.15) | True | PARTIALLY BEATS |
| AUROC 우위가 학습 기여인지 feature 아티팩트인지 불명 | UNCONFIRMED | UNCONFIRMED ORIGIN |
| LFD F1 < CUSUM F1 (-0.059) | True | CUSUM 우위 |
| LFD FAR (38%) vs CUSUM (8.6%) | 4.4배 차이 | NOT DEPLOYABLE |
| detection_delay = 0.000 (alarm bias) | True | NOT FAST DETECTION |
| LFD train_loss 비감소 | True | LEARNING FAILURE |

### 세부 판단 — metric별

**AUROC (0.842 vs 0.692, delta=+0.150)**:
- ranking 능력은 CUSUM 대비 실질적 우위
- **단**: episode-level bootstrap CI 없이는 paper claim으로 쓸 수 없음 (mathematical-validity-critic CRITICAL)
- **단**: random-weight LFD probe 없이는 AUROC 우위가 학습 결과인지 확인 불가 (failure-interpretation-critic FAIL-016)
- CUSUM과 SPRT가 동일한 AUROC=0.6916 (소수점 13자리)를 공유 — 독립성 확인 필요

**AUPRC (0.707 vs 0.479, delta=+0.228)**:
- threshold 최적화 여지가 존재함을 시사
- 그러나 n_positive (switch episodes)=50, n_negative (stable)=0인 불균형이 AUPRC를 왜곡

**F1 (0.178 vs 0.237, delta=-0.059)**:
- threshold=0.5에서 threshold-based detection 성능은 CUSUM 열세
- tolerance=2 sensitivity sweep 미보고 (reviewer 공격 취약)
- F1 std=0.000 (3 seeds) → model collapse 신호일 수 있음

**detection_delay (0.000 vs 0.231)**:
- LFD delay=0은 **alarm bias**이며, 빠른 탐지가 아니다
- FAR=38%와 함께 해석하면: 대부분의 step에서 alarm을 발동하기 때문에 delay가 0이다
- paper에서 "detection_delay=0 = 빠른 탐지"라는 표현을 절대 쓰면 안 된다

**FAR (38.2% vs 8.6%)**:
- 4.4배 차이
- FAR std=0.127 (seed 간 23.9% ~ 54.8%) — 불안정
- n_stable_episodes=0으로 negative class 정의가 오염된 pre-switch steps에만 의존
- 운영 환경에서 38% FAR은 매 2~3 step마다 wrong-hypothesis alarm → planning trigger → compute 낭비

**fair_ppc**:
- LFD ppc_ratio ~0.00002 (training amortized over N_eval=50)
- mathematical-validity-critic: fair_ppc 정의 무효 (progress proxy 자의적, amortization 방식 부당)
- paper claim으로 사용 불가

---

## 6. Critic Agent 요약

### 6.1 frcgw-data-leakage-auditor

```
verdict: PASS
```

- `regime_switch_t`, `true_wrong_hypothesis`, `detection_delay_gt`: inference input에 미노출 ✓
- `effect_type` from `PublicEffect`: public 필드, oracle leakage 아님 ✓
- 잔여 WARN:
  - `BatchTargets.regime_switch_step` 필드명이 `FORBIDDEN_AGENT_FIELDS`의 `regime_switch_t`와 달라
    유지보수 위험 (runtime leakage 아님)
  - `_make_batch_targets()`의 hardcoded placeholder strings (loss 항별 학습 목적 오염 위험)

### 6.2 failure-interpretation-critic

```
overall_claim_status: WEAKENED
fail_triggered: FAIL-016, FAIL-018
```

**FAIL-016**: LFD AUROC 우위가 학습 결과인지 feature 구조 아티팩트인지 불명확
- train_loss 15 epochs 내내 ~1.53 (감소 없음)
- AUROC=0.84가 나오는 이유: (a) feature encoding이 grammar-switch signal을 직접 포함할 수 있음,
  (b) eval set 100% switch episodes → recall-driven AUROC 인플레이션,
  (c) uncalibrated classifier는 ranking은 하지만 calibration은 안 함
- **필수 실험**: random-weight LFD probe (학습 전 AUROC vs 학습 후 AUROC)

**FAIL-018**: v0_5 결과가 real Web/GUI로 일반화 불가 (범주적 차이)
- 2 grammar pairs, perfect discrete effects, 12 steps, 14.73% post-switch wrong rate
- 실제 환경: 수십 grammar, noisy DOM/screenshot, 수백 steps, partial observability
- "LFD shows promise in oracle-free conditions" 표현 사용 불가 (caveat 없이)

### 6.3 reviewer-2-attack-agent

```
overall_rejection_risk: HIGH
verdict: HIGH_RISK
```

| 공격 | 강도 | 방어 상태 |
|---|---|---|
| "CUSUM이면 충분" (F1+FAR) | MAJOR | calibration 후 F1 재측정 필요 |
| "toy v0_5 — 2개 grammar만" | **FATAL** | v0_6 이상 실험 없으면 방어 불가 |
| "GRU+BOCPD ablation 없음" | MAJOR | rule-based counter baseline 필요 |
| "N=50 통계적 유의성 없음" | MAJOR | bootstrap CI 필요 |
| "train_loss > log(2) = 학습 실패" | MAJOR | loss 항 분리 보고 필요 |
| "detection_delay=0 = alarm bias" | MAJOR | alarm bias 표현으로 수정 필요 |

**P0 즉각 조치**: "fast detection" 표현 제거, alarm bias 명시

### 6.4 mathematical-validity-critic

```
verdict: NEEDS_REVISION
```

| 위험도 | 항목 | 조치 |
|---|---|---|
| CRITICAL | AUROC CI 없음 — episode 상관 미반영 | bootstrap CI (episode 단위) 필수 |
| CRITICAL | detection_delay=0 = alarm bias — "빠른 탐지" 표현 금지 | alarm bias로 수정 |
| HIGH | CUSUM=SPRT 동일 AUROC (소수점 13자리) | score stream 독립성 확인 |
| HIGH | FAR reference class 오염 (n_stable=0) | stable episodes 추가 |
| HIGH | fair_ppc 무효 (progress proxy, amortization 부당) | multiple proxy로 대체 |
| HIGH | train_loss random baseline 불명확 | 항별 분리 + dummy classifier |
| HIGH | F1 tolerance sensitivity 미보고 | tolerance={0,1,2,3} sweep 필요 |
| MEDIUM | oracle-probe vs oracle-free 수치 혼용 위험 | 두 조건 명확 분리 |

### 6.5 novelty-threat-scout

```
verdict: NOVELTY_AT_RISK
```

| 위협 논문 | 중복도 | defense 강도 | 조치 |
|---|---|---|---|
| **R-BOCPD** (2304.00232, CoLLAs 2023) | OVERLAP (run_length_head ≅ BOCPD posterior) | MODERATE | related work 명시적 differentiation 필수 |
| **NN-CUSUM** (2210.17312, ICASSP 2023) | PARTIAL_OVERLAP (cusum_head, CUSUM 대비 비교) | **WEAK** | NN-CUSUM baseline 추가 필수 |
| **E-valuator** (2512.03109, 2025) | PARTIAL (sequential hypothesis testing + agent failure) | MODERATE | related work 추가 필요 |
| WebWorld / CUWM | PARTIAL | STRONG | 현 differentiation 유지 가능 |
| WAC / VeriGUI | PARTIAL | MODERATE | verifier-only baseline 비교 필요 |

**즉각 조치**:
1. NN-CUSUM (2210.17312) baseline을 eval에 추가 — 없으면 "약한 baseline 비교" 공격 불가피
2. R-BOCPD (2304.00232) related work differentiation 추가
3. E-valuator (2512.03109) related work에 추가 (2025년 신규)
4. "CUSUM-based" / "changepoint detector" 표현 → "grammar-conditioned falsification estimator"

---

## 7. 결론 — 보존 가능한 claim vs 제거/수정 필요 claim

### 보존 가능 (조건부)

| Claim | 조건 |
|---|---|
| LFD AUROC > CUSUM AUROC on oracle-free v0_5 (+0.15) | episode-level bootstrap CI 확인 후 |
| LFD AUPRC > CUSUM AUPRC (+0.23) | 동일 조건 |
| LFD alarm_threshold=0.5에서 FAR이 과다 (calibration 필요) | 무조건 보존 |
| run_length_posterior_concentration=0.854 (집중) | BOCPD 구조가 posterior 집중에 기여함을 보여줌 |
| CUSUM h=2.0이 oracle-free v0_5에서 가장 높은 F1 (0.297) | sweep 결과로 보존 |

### 제거 / 수정 필요

| Claim | 이유 |
|---|---|
| "LFD is faster to detect switches (delay=0)" | alarm bias — 제거 |
| "LFD beats CUSUM" (단순 표현) | F1 열세, FAR 과다 — "AUROC에서 우위"로 범위 한정 |
| "LFD learns to detect wrong hypotheses" | train_loss 비감소, random-weight probe 미수행 — "learns"를 조건부로 수정 |
| fair_ppc로 CUSUM 대비 LFD 비교 | 정의 무효 — 제거 또는 다른 proxy로 대체 |
| 결과의 일반화 가능성 (>2 grammar pairs) | FAIL-018 — 반드시 scope limitation 명시 |

### 절대 삭제 금지 (negative results)

- train_loss=1.53 비감소 (15 epochs, 3 seeds)
- FAR=38.2% (seed 간 range 23.9%~54.8%)
- F1=0.178 < CUSUM F1=0.237
- detection_delay=0.000 (alarm bias)
- 이 결과들은 보고서/논문에 반드시 포함되어야 한다

---

## 8. 필수 후속 실험 (Priority 순)

### P0 (즉각 — 코드 수정 없이 가능)

1. **Paper 표현 수정**: "fast detection" → "alarm bias at threshold=0.5"
2. **Verdict 수정**: `comparison_v0_5_oracle_free.json`의 verdict string 수정

### P1 (다음 Codex 태스크)

1. **episode-level bootstrap CI for AUROC**
   - 50 episodes를 unit으로 1000회 resampling
   - delta AUROC 95% CI 계산
   - CI lower bound > 0이면 AUROC 우위 주장 허용

2. **random-weight LFD probe**
   - 학습 없는 LFD (초기화 직후) AUROC 측정
   - gap = trained AUROC - random AUROC < 0.05이면 AUROC 우위는 feature 아티팩트

3. **alarm_threshold sweep**
   - threshold ∈ {0.1, 0.2, ..., 0.9}에서 FAR/F1/precision/recall
   - FAR-matched threshold (FAR=8.6%)에서의 F1 vs CUSUM F1

4. **rule-based mismatch counter baseline**
   - "no_state_change or delayed_effect이면 wrong=1" 규칙 기반 AUROC
   - LFD AUROC와 비교 → architecture contribution 검증

5. **loss decomposition**
   - L_seq_falsification vs L_run_length_posterior 분리 logging
   - dummy classifier (p=0.5 constant) loss 측정

6. **F1 tolerance sensitivity**
   - tolerance ∈ {0, 1, 2, 3}에서 F1 재계산

7. **stable episodes 추가**
   - eval set에 25~50% stable episodes 포함 (switch/stable balanced)
   - FAR 재측정 (negative class 정제)

### P2 (신규 Phase 또는 Phase 9 연장)

1. **multi-grammar v0_6 환경**
   - k=4~6 grammar pairs
   - LFD vs CUSUM vs NN-CUSUM 비교
   - FATAL attack (Attack 2) 방어를 위한 필수 실험

2. **NN-CUSUM (2210.17312) baseline 구현**
   - same oracle-free dataset에서 비교
   - novelty defense를 위한 필수 baseline

### P3 (논문 framing)

1. LFD를 "discrete alarm detector"가 아닌 "wrong-hypothesis probability scorer"로 reposition
2. R-BOCPD, NN-CUSUM, E-valuator differentiation text 추가
3. verifier-only baseline vs LFD 비교 명시

---

## 9. Blockers

| Blocker | 심각도 | 해소 조건 |
|---|---|---|
| AUROC delta CI 미확인 | HIGH | episode-level bootstrap CI lower bound > 0 |
| random-weight probe 미수행 | HIGH | probe AUROC vs trained AUROC gap > 0.05 |
| 2-grammar pair 한계 (FATAL attack) | **FATAL** | v0_6+ 실험 또는 claim scope 한정 명시 |
| NN-CUSUM baseline 없음 | HIGH | NN-CUSUM baseline AUROC 추가 |
| n_stable_episodes = 0 | HIGH | balanced eval set 재실험 |
| F1 tolerance sensitivity 미보고 | MEDIUM | tolerance={0,1,2,3} sweep |
| fair_ppc 정의 무효 | MEDIUM | multiple proxy 대체 또는 제거 |

---

## 10. 파일 참조

```
scripts/phase9_v0_5_cusum_lfd_eval.py         — 이번 task 신규 스크립트
scripts/phase9_lfd_eval.py                     — 이전 oracle-probe 비교 원본 (직접 비교 불가)

outputs/.../v0_5_oracle_free_dataset_audit.json
outputs/.../cusum_sprt_v0_5_oracle_free_metrics.json
outputs/.../lfd_v0_5_oracle_free_metrics.json
outputs/.../comparison_v0_5_oracle_free.json

paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md  — FALS-03
paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md — §7-§8
paper_context_ref/01_RELATED_WORK_THREAT_MAP.md     — R-BOCPD/NN-CUSUM/E-valuator 추가 필요
```

---

*이 보고서는 5개 Critic Agent (mathematical-validity-critic, reviewer-2-attack-agent,
frcgw-data-leakage-auditor, failure-interpretation-critic, novelty-threat-scout)의
parallel review를 Main Claude가 합성한 결과다.
음의 결과(negative results)는 삭제되지 않았다.*
