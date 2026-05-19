# PHASE 9 End-to-End Evidence Report

**Date**: 2026-05-19  
**Branch**: memory-redesign-2026-05-16  
**Execution mode**: SYNTHETIC ORACLE PROBE  
**Script**: `scripts/phase9_lfd_eval.py`  
**Artifacts**: `outputs/risk_hunt/implementation/evals/`

---

## 1. Executive Verdict

**Final Verdict: `LFD_NOT_BETTER_THAN_CUSUM`**

현재 실험 조건에서 LFD는 CUSUM을 통계적으로 유의미하게 능가하지 못한다.

- AUROC +0.034 (0.947 vs 0.913)은 N=250 에피소드 기준 비유의 (Z=0.83, p≈0.41)
- F1 동일 (LFD 0.632 vs CUSUM 0.635)
- FAR LFD가 6.8× 불리 (0.581 vs 0.086)
- fair_ppc LFD가 5700× 불리
- 핵심 신호 Loop-01 확인 proxy artifact
- 전체 평가가 synthetic oracle probe (실제 collect_episode() 경유 아님)

이 verdict는 LFD의 영구 포기가 아니다. 아래 4가지 전제 조건이 충족되면 재평가 가능:
1. collect_episode() v0_5 switch 처리 구현 (TASK_COLLECTOR_V05_SWITCH)
2. LFD loss plateau 탈출 (15 epochs → train_loss=1.34 stuck, epoch 2 이후 정체)
3. alarm_threshold calibration (0.5 고정 → validation-derived threshold)
4. N ≥ 1000 에피소드로 AUROC CI 확인

---

## 2. 실행 설정

| 항목 | 값 |
|---|---|
| execution_mode | SYNTHETIC_ORACLE_PROBE |
| n_episodes | 250 (200 switch + 50 stable) |
| max_steps | 12 |
| switch_step mean | 6.3 (range 2–10) |
| lfd_epochs | 15 |
| lfd_lr | 5e-4 |
| cusum_h | 2.0 (고정, proxy OFF) |
| cusum_k | 0.3 |
| sprt_A | 5.0 |
| sprt_B | 0.1 |
| n_seeds | 3 |
| alarm_threshold (LFD) | 0.5 (고정, proxy OFF) |
| proxy_off | True |

### 구조적 한계 (명시 필수)

1. **Oracle simulation**: `collect_episode()`가 v0_5 grammar switch를 처리하지 않음. Effect stream이 `simulate_effect_stream(spec.regime_switch_step, noise=0.15)`로 생성됨. 평가 메트릭이 oracle 조건에서 측정됨.
2. **Frozen base encoder**: LFD training에서 base model은 `with torch.no_grad()`로 frozen. LFD head가 effect_scalar와 uninformative synthetic obs에서만 학습.
3. **No pre-trained weights**: `TextFRCGModel(use_lfd_head=True)`가 random init. Phase 9 LFD는 effect_scalar accumulator probe임.

---

## 3. 핵심 결과 테이블

| Metric | CUSUM (h=2.0) | SPRT | LFD (seed0) | LFD (mean±std) |
|---|---|---|---|---|
| mean_detection_delay | 2.356 | 5.872 | 0.070 | 0.288±0.308 |
| false_alarm_rate_per_step | 0.086 | 0.075† | **0.626** | 0.581±0.060 |
| regime_shift_F1 | **0.635** | 0.000‡ | 0.580 | 0.632±0.055 |
| AUROC | 0.913 | 0.913§ | 0.943 | **0.947±0.0035** |
| AUPRC | 0.841 | 0.841§ | 0.921 | — |
| run_length_concentration | N/A | N/A | **0.893** | — |
| fair_ppc_ratio (vs CUSUM) | 1.0 | — | 0.000195 | — |

† SPRT FAR은 break 누락으로 과대계산 가능성 (impl-risk RISK-4)  
‡ SPRT F1=0.000: A=5.0이 12-step 에피소드에서 도달 불가 (ARL≈33.6 > 12)  
§ CUSUM과 SPRT AUROC 동일 (0.913): AUROC 계산 독립성 UNKNOWN

### CUSUM threshold sweep

| h | detection_delay | FAR | regime_shift_F1 |
|---|---|---|---|
| 0.5 | 0.0 | 0.135 | 0.231 |
| 1.0 | 0.729 | 0.131 | 0.569 |
| **2.0** | **2.356** | **0.086** | **0.635** |
| 3.0 | 4.615 | 0.049 | 0.007 |
| 4.0 | 5.609 | 0.034 | 0.000 |

h=2.0이 12-step 에피소드에서 optimal. h≥3.0부터 episode length 한계 (ARL > 12).  
**주의**: h=2.0은 eval set에서 선택됨 → validation-first protocol 미준수 가능성.

---

## 4. Critic별 공격 요약 및 Main Claude 반박/수용

### 4.1 Data Leakage Auditor

**판정**: STRUCTURALLY_LEAKY

**공격**: effect_scalar가 oracle switch_step 파생 → inference input에 oracle 정보 implicit 전달.

**Main Claude 반박/수용**:
- **수용**: Oracle probe 조건 deployment claim 불가. 모든 결과에 "SYNTHETIC_ORACLE_PROBE" 레이블 필수.
- **반박**: runtime FORBIDDEN_AGENT_FIELDS 이름 위반 없음 (assert_agent_observation_safe PASS). true_wrong_hypothesis는 supervision target으로만 사용 (NOT inference input). 구조적 oracle leakage는 스크립트 docstring에 명시 공개됨.
- **행동**: 없음. 이미 disclosed. paper에서 "oracle-stream validation"으로 명시.

---

### 4.2 Implementation Risk Critic

**판정**: NEEDS_FOLLOW_UP

**RISK-4 (HIGH)**: `run_sprt_on_episode()`에 `break` 누락 → SPRT FAR 과대계산.  
**RISK-1 (HIGH)**: collector v0_5 switch 미구현.

**Main Claude 수용**:
- RISK-4: `baseline_detectors.py` line 151에 `break` 추가 필요. **사용자 승인 후 직접 수정** (1줄 수정, CUSUM과 일관성).
- RISK-1: `TASK_COLLECTOR_V05_SWITCH` Codex follow-up task 생성 필요.
- RISK-2/3: 의도적 설계. 문서화만.

---

### 4.3 Reviewer-2 Attack

**판정**: REJECT / Major Revision Required

**FATAL-1 (Oracle contamination)**: 전체 AUROC가 oracle switch_step 기반 시뮬레이션 결과.

**Main Claude**: 수용. 모든 LFD 결과는 oracle probe 조건임. CUSUM이 동일 oracle 조건에서 AUROC 0.913 달성 → oracle이 easy task를 만들고 있다는 반증. **claim 방어 위해 oracle-free collect_episode 구현 필수**.

**FATAL-2 (FAR=0.581)**: 실제 배포 불가 수준.

**Main Claude**: 수용. 그러나 failure-interp critic이 확인: 이것은 calibration 문제이지 모델 붕괴 아님. AUROC=0.947은 discriminative power 실재를 보여줌. 임계값 조정으로 FAR 개선 가능. **paper에서 FAR 단독 보고 금지 → AUROC + threshold sweep curve 동시 제시 필요**.

**FATAL-3 (AUROC delta 비유의)**: N=250에서 Z=0.83, p≈0.41.

**Main Claude**: 수용. +0.034 차이를 claim으로 사용 불가. **N ≥ 1000에서 재측정 필요**.

**FATAL-4 (fair_ppc 0.00019)**: FC-05 허위.

**Main Claude**: 수용. training amortized cost 포함 시 5700× 불리. inference-only는 ~875× 불리. compute efficiency claim을 LFD vs CUSUM 비교에서 제거. 단, Loop-06 2.0× advantage는 다른 실험 (fair compute planning gate)이므로 별도.

**COMPOUNDING (Loop-01/03)**: FC-03(falsification signal DEAD), FC-02(separability 미학습).

**Main Claude**: 수용. Loop-01과 동일 결론. Phase 9 LFD AUROC가 proxy artifact일 가능성 높음.

---

### 4.4 Novelty Scout

**판정**: NOVELTY_AT_RISK

**직접 선행 연구**:
- **R-BOCPD** (arXiv:2304.00232): BOCPD + non-stationary RL 결합 이미 선점
- **NN-CUSUM** (arXiv:2210.17312, AAAI 2024): learned CPD > CUSUM 이론 선점

**Main Claude**:
- **수용**: R-BOCPD, NN-CUSUM을 `paper_context_ref/01_RELATED_WORK_THREAT_MAP.md`에 CONFIRMED_PRIMARY threat으로 추가 필요. **이 업데이트 즉각 실행 (별도 commit)**.
- **보존 가능 claim**: wrong-control-grammar persistence as failure mode (SN-001)는 distinct. grammar-conditioned alternative rollout (SN-004)는 WAC/CUWM과 구분점 있음.
- **약화된 claim**: "BOCPD run-length posterior가 CPD를 개선한다"는 현재 실험으로 지지 불가.

---

### 4.5 Failure Interpretation Critic

**판정**: MODIFIED (not INVALIDATED)

**핵심 발견**:
- FAR=0.581은 calibration 문제 (option c) — AUROC=0.947과 공존 가능 (threshold bias)
- detection_delay=0.07은 pre-switch alarm bias artifact (invalid as "fast detection")
- seed 2 (delay=0.724, FAR=0.496, F1=0.708): optimal threshold에서 LFD > CUSUM F1 가능성

**Main Claude**:
- **수용**: detection_delay를 "빠른 감지" 근거로 사용 불가.
- **보존**: AUROC advantage에서의 discriminative power는 실재.
- **수정 방향**: "LFD achieves lower detection delay at Pareto-equivalent FAR settings" (FAR-delay tradeoff 곡선으로 제시).

---

### 4.6 Statistical Validity Critic

**판정**: FAIL

**핵심 발견**:
- CUSUM과 SPRT의 AUROC가 0.913으로 동일 → AUROC 계산 독립성 UNKNOWN
- train_loss=1.34: multi-task total loss (LFD component 단독 기록 없음) → random보다 나쁘다고 단정 불가하지만 LFD BCE 단독 미확인
- detection_delay CV>1 → 신뢰 구간에 음수 포함 → 측정 자체 무효

**Main Claude**:
- **수용**: CUSUM=SPRT AUROC 현상은 AUROC 계산 코드 검토 필요. **즉각 확인**.
- **수용**: h=2.0 선택이 eval set에서 이루어진 경우 F1=0.635 overfitted 가능성.
- **부분 반박**: train_loss=1.34는 L_seq_falsification + L_run_length_posterior 복합 loss (multi-task). LFD component만의 BCE가 0.693 이하인지 별도 logging 필요.

---

## 5. CUSUM/SPRT AUROC 동일 원인 확인

Statistical critic이 제기한 CUSUM=SPRT AUROC=0.913 현상: 두 detector가 `wrong_prob_scores`로 동일한 `[float(e) for e in effects]` effect stream을 사용하기 때문이다. 실제 aggregate_episode_metrics()가 wrong_prob_scores와 true_wrong_hypothesis를 기반으로 AUROC를 계산하는데, CUSUM과 SPRT 모두 effect stream을 wrong_prob_scores로 사용 → 동일한 AUROC. LFD만 wrong_prob_learned를 사용. 이것은 구현 artifact이며 CUSUM/SPRT의 real AUROC는 별도 measurement 필요.

**결론**: CUSUM/SPRT AUROC=0.913은 effect stream binary signal (0/1)의 AUROC이지 detector statistic의 AUROC가 아님. 실제 CUSUM AUROC는 S_t trace로 측정해야 함. **이것은 LFD AUROC 비교의 기준선이 잘못 설정되었음을 의미**.

---

## 6. 즉각 수정 항목 (Main Claude 판정)

| 항목 | 우선순위 | 변경 | 승인 필요 |
|---|---|---|---|
| SPRT FAR bug fix | HIGH | `baseline_detectors.py:151` `break` 추가 | 사용자 승인 필요 |
| Related work threat map 업데이트 | HIGH | R-BOCPD + NN-CUSUM 추가 | Claude 직접 |
| CUSUM AUROC 재측정 | MEDIUM | S_t trace 기반 AUROC | Codex task |
| LFD component loss 단독 logging | MEDIUM | per-objective loss | Codex task |
| h=2.0 validation-first sweep | MEDIUM | train/val/test split | Codex task |

---

## 7. Codex Follow-up Tasks

| Task ID | 내용 | 우선순위 |
|---|---|---|
| TASK_COLLECTOR_V05_SWITCH | collect_episode()에 v0_5 grammar switch 처리 구현 | CRITICAL |
| TASK_LFD_THRESHOLD_CALIB | alarm_threshold sweep + temperature scaling | HIGH |
| TASK_CUSUM_AUROC_FIX | CUSUM S_t trace 기반 AUROC 재계산 | HIGH |
| TASK_LFD_LOSS_LOGGING | LFD component BCE 단독 logging | HIGH |
| TASK_PHASE9_N1000 | N=1000 에피소드로 AUROC CI 재측정 | HIGH |
| TASK_SPRT_A_SWEEP | A=2.0~3.0 sweep으로 SPRT parameterization 수정 | MEDIUM |
| TASK_PROXY_FREE_AUROC | oracle-free collect_episode 완성 후 proxy-off AUROC | CRITICAL (gate) |

---

## 8. 실행 명령어

```powershell
# PHASE 9 eval 실행
.venv\Scripts\python.exe scripts/phase9_lfd_eval.py

# Leakage + visibility test 재확인
.venv\Scripts\python.exe -m pytest -q tests/test_forbidden_field_mirror_sync.py tests/test_visibility_contract.py tests/test_leakage_auditor.py
```

---

## 9. Negative Result 보존

이 보고서에 기록된 다음 negative results는 삭제 금지이다:

1. LFD FAR=0.581 at threshold=0.5 (production 사용 불가)
2. detection_delay=0.07은 pre-switch alarm bias artifact
3. fair_ppc_ratio=0.000195 (LFD가 CUSUM보다 5700× compute heavy)
4. SPRT F1=0.000 (A=5.0 parameterization failure in 12-step episodes)
5. train_loss plateau epoch 2→15 (no learning progress after epoch 2)
6. 전체 평가가 SYNTHETIC_ORACLE_PROBE (not real grammar-switch trajectories)
7. Loop-01 proxy artifact: LFD signal이 oracle probe에서도 학습됐는지 불확실
8. CUSUM/SPRT AUROC 동일(0.913) — AUROC 기준선 오염 가능성

---

## 10. Reviewer Attack Ledger

| Attack | Severity | Defense 가능 | 해결 방법 |
|---|---|---|---|
| Oracle contamination | FATAL | 부분 (disclosure) | oracle-free collect_episode 필수 |
| FAR=0.581 | FATAL | 부분 (calibration) | threshold sweep + paper에서 AUROC 우선 |
| AUROC delta 비유의 | FATAL | 불가 현 N | N≥1000 재측정 |
| fair_ppc 5700× | FATAL | 불가 | compute claim 제거 |
| FC-03 proxy DEAD | FATAL | 불가 현재 | LFD 재설계 |
| R-BOCPD / NN-CUSUM 선점 | HIGH | 부분 (grammar specificity) | related work 업데이트 |
| 12-step too short | MAJOR | 부분 (SPRT framing) | episode length 확장 |
| No CI | MAJOR | 불가 현재 | bootstrap CI 추가 |

---

## 11. 최종 paper claim 수정안

| Claim | 현재 | 수정 |
|---|---|---|
| FC-03: LFD가 CUSUM보다 fast detection | REMOVE | "LFD는 threshold-free AUROC에서 trend toward advantage (oracle probe, 미유의)" |
| FC-05: compute gate improves PPC | WEAKEN | "계획 호출 빈도 제어; LFD vs CUSUM PPC 비교는 N=1000, oracle-free 후 재평가" |
| detection_delay advantage | MODIFY | "Pareto-equivalent FAR 조건에서 detection delay 감소 경향 (threshold calibration 필요)" |
| AUROC = 0.947 | CONDITIONAL | "oracle-stream probe에서 0.947 ± CI; oracle-free 재측정 필요" |

---

## 12. 다음 단계 (우선순위 순)

1. **[BLOCKED 조건]** TASK_COLLECTOR_V05_SWITCH: 이것 없이는 어떤 eval도 deployment-level claim 불가
2. **[즉각]** SPRT FAR bug fix (사용자 승인 필요)
3. **[즉각]** Related work threat map 업데이트 (R-BOCPD, NN-CUSUM)
4. **[즉각]** CUSUM AUROC 재측정 (S_t trace 기반)
5. **[중기]** N=1000, alarm_threshold sweep, CI 재측정
6. **[중기]** LFD re-training with more epochs + calibration loss

---

*Generated from 6 critic agents: mathematical-validity-critic, reviewer-2-attack-agent, frcgw-data-leakage-auditor, implementation-risk-critic, failure-interpretation-critic, novelty-threat-scout*  
*Artifact: outputs/risk_hunt/implementation/evals/end_to_end_metrics.json*
