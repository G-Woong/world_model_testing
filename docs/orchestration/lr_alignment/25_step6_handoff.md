# 25_step6_handoff.md — STEP 6 Handoff Document

작성일: 2026-05-18
선행: STEP 5 `P3_STEP5_TRAINED_EVIDENCE_READY.passed` (예정)
branch: `memory-redesign-2026-05-16`

---

## §1. Purpose

이 문서는 STEP 5 완료 후 STEP 6에서 수행해야 할 작업을 기록한다.
STEP 5의 "STEP 6 이관" 항목들의 공식 추적 기록이다.

---

## §1a. CRITICAL Finding from STEP 5 T4 Agent Review

**l_falsification=0.0 in Stage 1/2 training** → 현재 pretrained checkpoint는 사실상 **no-falsification 조건 (ABL-010)**.

| 항목 | 발견 | 요구 조치 |
|---|---|---|
| F_t_planner | 모든 step에서 0.0 (degenerate_planner_rate=1.0) | l_falsification > 0 재학습 |
| C3 falsification F1 | 0.0 (모든 agent 동일) | 현재 run을 ABL-010 data로 등록 |
| C5 calibration | DEGENERATE_PREDICTOR (trained model에서도) | 재학습 + calibration training |
| C4 rollout fidelity | BLOCKED_no_model_rollout_prediction | eval runner harness fix |
| CLAIM-EVAL-003 | BLOCKED_EVIDENCE_INSUFFICIENT | l_falsification > 0 재학습 후 재측정 |

**STEP 6 FIRST ACTION**: Enable `l_falsification > 0` in training config + relabel current checkpoint as ABL-010.

---

## §2. STEP 6 Task 목록

### §2.0 l_falsification > 0 재학습 (CRITICAL — STEP 6 first priority)

**Task**: l_falsification weight를 0이 아닌 값으로 설정한 새 학습 config + 실행
- Stage 1/2 훈련에서 `l_falsification: 0.0` → `l_falsification: 1.0` (또는 0.5) 변경
- 현재 checkpoint를 ABL-010 (no-falsification) data로 기록/등록
- 새 checkpoint에서 F_t_planner non-trivial 확인 필수
- **Priority**: CRITICAL (모든 FRCG-LR falsification claim의 전제조건)

### §2.1 Full LR Scorer Active Path 교체 (HIGH)

**Task**: `frcg_agent.py` act()가 `lr_scorer.py`를 호출하도록 통합
- 현재: planner F_t만 사용 (dual trace policy)
- STEP 5 reconciliation audit 결과에 따라 결정
- 결정 조건: `mean_abs_diff < 0.1 AND degenerate_rate < 0.1` → full wiring
- **Files**: `src/frcgw/evaluation/frcg_agent.py`, `src/frcgw/falsification/lr_scorer.py`
- **Priority**: HIGH (C3 claim 최종 해소 전제조건)

### §2.2 C2 `regime_shift_f1` Metric 함수 (HIGH)

**Task**: `metrics.py`에 `regime_shift_f1()` (MET-REG-001) 신규 작성
- OOD-vs-ID aggregator in eval_runner.py
- ABL-001 (no_regime) 검증에 필수
- **Files**: `src/frcgw/evaluation/metrics.py`, `src/frcgw/evaluation/eval_runner.py`
- **Priority**: HIGH (C2 claim 전제조건)

### §2.3 Calibration Training (MEDIUM)

**Task**: temperature scaling / isotonic regression calibration
- `src/frcgw/evaluation/calibration.py` 신규 작성
- C5_calibration_status → "OK" (DEGENERATE 해소)
- **Files**: `src/frcgw/evaluation/calibration.py` (신규), `configs/calibration.yaml`
- **Priority**: MEDIUM (C5 claim 해소)

### §2.4 Long-horizon Training (HIGH)

**Task**: epochs ≥ 10, real dataset scale
- DATA-T1 (2,000-10,000 episodes) 달성 후 진행
- `l_falsification` weight 활성화 (현재 0.0)
- **Files**: training configs, 신규 dataset 생성
- **Priority**: HIGH (모든 metric 신뢰도 전제조건)

### §2.5 Direct-Threat Baseline 고도화 (HIGH)

**Task**: BASE-026/027/028 알고리즘 충실 재구현
- WAC: grammar posterior 통합, consequence model 학습
- CUWM: latent state model 학습, posterior 통합
- WebWorld: search tree 확장, reward model 학습
- **Priority**: HIGH (reviewer attack defense 필수; STEP 5는 heuristic approximation만)
- **참조**: `docs/orchestration/lr_alignment/24_step5_direct_threat_baseline_report.md §5`

### §2.6 Full 14 Critical Ablation 실행 (HIGH)

**Task**: ABL-011/015/040 외 11개 CRITICAL ablation 실행
- ABL-001 (no_regime) — C2 claim
- ABL-003 (merged_regime_control_grammar) — C1/C2
- ABL-006 (collapsed_latent) — C3
- ABL-016 (no_falsification) — C3
- ABL-022 (no_falsification_score_gate) — C1/C3
- ABL-023 (uncertainty_instead_of_falsification) — C3
- ABL-024 (no_alternative_hypothesis) — C4
- ABL-033 (no_compute_gate) — compute efficiency
- ABL-034 (always_plan_no_gate) — compute efficiency
- ABL-035 (no_rewrite) — C5
- ABL-036 (no_counterfactual_target) — C4
- **Priority**: HIGH (모든 core claim 검증 필수)

### §2.7 h_exec_id Emission Policy 최종 결정 (LOW)

**Task**: `h_exec_id` (hypothesis execution ID) — agent-derived vs generator gap 결정
- 현재: 모든 step에서 None
- Options: (a) emit agent-derived, (b) leave None + document, (c) generator-derived
- **Priority**: LOW

### §2.8 Compute-Matched Comparison (MEDIUM)

**Task**: BASE-015 vs FRCG-LR same compute budget 비교
- `ComputeMatchedRandomAgent` (BASE-015) 대비 FRCG-LR의 progress_per_compute
- **Files**: eval config + report
- **Priority**: MEDIUM

### §2.9 Statistical Reliability (MEDIUM)

**Task**: seed variance (n=5 seeds), confidence intervals
- STEP 5는 smoke (seed=0 only)
- **Priority**: MEDIUM

### §2.10 Paper Table Readiness (HIGH)

**Task**: 모든 claim에 대응하는 metric + ablation이 green → paper table 생성
- 전제조건: §2.1~§2.6 완료
- **Priority**: HIGH (P7 진입 조건)

---

## §3. Prerequisite Checklist

STEP 6 시작 전 반드시 확인:
- [ ] `outputs/phase_gates/P3_STEP5_TRAINED_EVIDENCE_READY.passed` 존재
- [ ] trained checkpoint (`outputs/checkpoints/pretrain_v0_3/checkpoint.pt`) 존재
- [ ] C1 persistence_v1 status "OK" (trained model)
- [ ] C4 alternative_rollout_fidelity 정의 확정 (BLOCKED or OK)
- [ ] LR reconciliation audit JSON 존재 + interpretation 확인
- [ ] DATA-T1 dataset 생성 계획 (2000+ episodes)

---

## §4. Agent Team Triggers (STEP 6)

| Task | Trigger | Agents |
|---|---|---|
| §2.1 LR active path | T1 (claim 변경) | mathematical-validity-critic + claim-metric-alignment |
| §2.2 C2 metric | T1 | claim-metric-alignment-auditor |
| §2.4 Long-horizon training | T2 (실험설계) | experiment-design-expander + feasibility-and-cost-auditor |
| §2.5 Baseline 고도화 | T5 (논문 섹션) | reviewer-2-attack-agent + novelty-threat-scout |
| §2.10 Paper table | T4 (결과 해석) | failure-interpretation-critic + area-chair-synthesis |

---

## §5. Cross-references

- `docs/orchestration/lr_alignment/23_step5_execution_plan.md` — STEP 5 계획
- `docs/orchestration/lr_alignment/24_step5_direct_threat_baseline_report.md` — BASE-026/027/028
- `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7,§8` — baseline/ablation SSoT
- `paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md §5,§8` — data/compute budget
