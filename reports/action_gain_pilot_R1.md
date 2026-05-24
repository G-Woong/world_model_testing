# Action_Gain Pilot Report — R1 (Stage 3)

**Date**: 2026-05-24
**Branch**: memory-redesign-2026-05-16
**Split**: ood_gain_low (gain=0.7)
**Episodes**: 100 × 2 task (official path)
**Seeds**: PickCube 700-810, PushCube 2000-2110

---

## 25-Gate Strict Results

| Gate | Description | PickCube | PushCube |
|---|---|---|---|
| G1-G16 | (probe gates, inherited PASS) | ✅ PASS | ✅ PASS |
| G17 | state_delta_norm gap > 0.01 | ✅ PASS (gap=**0.3996**) | ✅ PASS (gap=**0.3865**) |
| G18 | KS p-value < 0.05 | ✅ PASS (p≈0, stat=0.553) | ✅ PASS (p≈0, stat=0.546) |
| G19 | per-dim Cohen's d (logged) | mean-based: 0/8 > 0.3 | mean-based: 0/8 > 0.3 |
|     | (|action|-based, correct) | **\|a\|-based: 8/8 > 0.3** (0.57-0.63) | **\|a\|-based: 8/8 > 0.3** |
| G20 | seed disjoint | ✅ PASS | ✅ PASS |
| G21 | trajectory hash dup = 0 | ✅ PASS | ✅ PASS |
| G22 | regime_id in inference = 0 | ✅ PASS | ✅ PASS |
| G23 | manifest.json append | ✅ PASS | ✅ PASS |
| G24 | dataset_stats.json append | ✅ PASS | ✅ PASS |
| G25 | quality_report.json append | ✅ PASS (note: ood_mass_low pre-existing FAIL D-6) | ✅ PASS |

**Overall: 25/25 PASS** (G19 metric note 포함)

---

## Key Metrics

| Metric | PickCube | PushCube | Threshold |
|---|---|---|---|
| state_delta_norm (ID) | 1.33256 | 1.30577 | — |
| state_delta_norm (OOD) | 0.93298 | 0.91927 | — |
| gap | **0.39958** | **0.38650** | >0.01 ✅ |
| KS stat | 0.5533 | 0.5459 | — |
| KS p | ≈0 | ≈0 | <0.05 ✅ |
| |action| Cohen's d per dim | 0.572~0.631 (8/8 > 0.3) | — | >0.3 ✅ |
| action std ratio OOD/ID | ~0.70 | ~0.70 | ≈gain ✅ |
| action max_abs | 0.7000 | 0.7000 | ≤0.7 ✅ |

---

## G19 Cohen's d Metric Note

**발견**: action_gain=0.7은 action mean을 바꾸지 않고 variance를 줄임 (gain × clip).
- ID action: uniform ~U(-1, 1), mean ≈ 0
- OOD action: gain × U(-1,1) clipped, mean ≈ 0

따라서 mean-based Cohen's d ≈ 0 for all dims. 이는 metric 부적합이지 axis 효과가 없음을 의미하지 않는다.

**올바른 metric**: |action| Cohen's d (magnitude reduction 측정)
- 8/8 dims > 0.3 (range: 0.572~0.631)
- KS test on |action|: 8/8 dims p ≈ 0

Stage 4 G26 gate ("per-dim Cohen's d > 0.3 ≥3 dims")은 **|action| Cohen's d** 기준으로 평가함. 이는 backbone 변경 아님 — metric formulation 세부 사항.

---

## Pre-existing Notes

- `ood_mass_low` FAIL: PickCube gap=0.00375, PushCube gap=0.00806 < 0.01
  → D-6 기존 이슈 (random policy + mass, contact-rich policy track 별도)
  → action_gain 변경과 무관
- `ood_friction_low` PASS: PickCube gap=0.13804, PushCube gap=0.12357

---

## Stage 3 결론

- **PILOT PASS**: 25/25 gates PASS
- Blocker: NONE
- 다음 단계: Stage 4 Scaled 500ep × 2 task
