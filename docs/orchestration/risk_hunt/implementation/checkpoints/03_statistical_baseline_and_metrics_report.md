# Checkpoint-3 — Statistical Baseline + Sequential Metrics Report

**Date**: 2026-05-19  
**Tasks**: TASK_LFD_001 (CUSUM/SPRT) + TASK_LFD_007 (metric harness)  
**Branch**: `memory-redesign-2026-05-16`

---

## 1. 구현 완료 항목

### TASK_LFD_001 — Statistical Baselines

| 컴포넌트 | 파일 | 상태 |
|---|---|---|
| `CUSUMDetector` (Page 1954) | `src/frcgw/evaluation/baseline_detectors.py` | ✅ |
| `SPRTDetector` (Wald 1945) | 동일 | ✅ |
| `compute_effect_llr()` | 동일 | ✅ |
| `run_cusum_on_episode()`, `run_sprt_on_episode()` | 동일 | ✅ |
| `detection_delay()`, `false_alarm_rate_per_step()` | `metrics.py` | ✅ |
| `run_length_posterior_ece()` | 동일 | ✅ |
| `regime_shift_f1_sequential()` | 동일 | ✅ |
| `split_episodes_by_grammar_ood()` (SPLIT-003) | 동일 | ✅ |

### TASK_LFD_007 — Metric Harness

| 컴포넌트 | 파일 | 상태 |
|---|---|---|
| `DetectorEvalResult` 스키마 | `src/frcgw/evaluation/metric_schema.py` | ✅ |
| `auroc_wrong_hypothesis()` | `metrics.py` | ✅ |
| `auprc_wrong_hypothesis()` | 동일 | ✅ |
| `recovery_delay_correlation()` | 동일 | ✅ |
| `aggregate_episode_metrics()` | 동일 | ✅ |

---

## 2. 테스트 결과

```
tests/test_sequential_detectors.py: 11 passed
tests/test_odc_split.py:             4 passed
tests/test_detection_metric_schema.py: 13 passed
─────────────────────────────────────────────
total: 28 passed
```

---

## 3. v0_5 Small Eval — CUSUM Baseline (n=20 switch episodes)

| 메트릭 | 값 |
|---|---|
| `n_switch_episodes` | 20 |
| `mean_detection_delay` | **7.0 steps** |
| `false_alarm_rate_per_step` | **0.000** |
| `regime_shift_f1` | **0.000** |
| `auroc_wrong_hypothesis` | 1.000 (시뮬레이션 완벽 분리) |
| `auprc_wrong_hypothesis` | 1.000 |

### 핵심 발견

**CUSUM(h=4.0, k=0.5)은 10-step episode에서 매우 느리다.**

수학적 분석:
- LLR=1.0(mismatch) 시 S_pos 0.5/step 증가 → alarm까지 8 steps
- switch_step ∈ [2, max_steps-2] = [2, 8]
- switch 이후 남은 steps = max_steps - switch_step
- switch_step > 3이면 남은 steps < 7 → alarm 불발
- E[switch_step] ≈ 5 → 대부분 에피소드에서 alarm 미달

**결론**: `regime_shift_f1 = 0.0` — CUSUM은 10-step text env에서 alarm을 거의 내지 못함.
이 baseline이 LFD의 비교 대상이다. LFD는 accumulated h_t를 통해 더 빠르게 탐지해야 함.

---

## 4. 아키텍처 메모

- `aggregate_episode_metrics()`: dict 기반 인터페이스 (episode 당 switch_step, first_alarm, alarm_steps, stable_steps, wrong_prob_scores, true_wrong_hypothesis 필요)
- `DetectorEvalResult.to_json()`: JSON 직렬화 가능
- `split_episodes_by_grammar_ood()`: SPLIT-003 equivalent — filter_accordion, nested_scroll → OOD

---

## 5. 남은 갭 (TASK_LFD_005 진입 전)

| 갭 | 설명 | 해결 단계 |
|---|---|---|
| LFD 실제 학습 없음 | wrong_prob_learned 시뮬레이션 입력 사용 | TASK_LFD_005 loss 구현 후 |
| h_t 누적 효과 미검증 | FalsificationDetectorHead 학습 전 | TASK_LFD_005 |
| CUSUM vs LFD 비교 | LFD 학습 결과 없음 | PHASE 9 end-to-end |
| detection_delay=7 의미 | 실제 max_steps와 episode 길이 의존 | longer episodes로 재확인 필요 |
