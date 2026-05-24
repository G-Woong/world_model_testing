# Action_Gain Scaled Report — R1 (Stage 4)

**Date**: 2026-05-24
**Branch**: memory-redesign-2026-05-16
**Split**: ood_gain_low (gain=0.7)
**Episodes**: 500 × 2 task (official path, overwrites pilot)
**Seeds**: PickCube 811-1311, PushCube 2111-2611
**Wall-clock**: PickCube 227s, PushCube 125s

---

## 30-Gate Full Results

| Gate | Description | PickCube | PushCube |
|---|---|---|---|
| G1-G16 | (probe gates) | ✅ PASS | ✅ PASS |
| G17 | state_delta_norm gap > 0.01 | ✅ PASS (gap=**0.3999**) | ✅ PASS (gap=**0.3834**) |
| G18 | KS p-value < 0.05 | ✅ PASS (p≈0, stat=0.553) | ✅ PASS (p≈0, stat=0.549) |
| G19 | per-dim Cohen's d (|action|) | 8/8 > 0.3 (0.58~0.62) | 8/8 > 0.3 (0.58~0.62) |
| G20 | seed disjoint | ✅ PASS | ✅ PASS |
| G21 | trajectory hash dup = 0 | ✅ PASS | ✅ PASS |
| G22 | regime_id not in inference | ✅ PASS | ✅ PASS |
| G23 | manifest.json updated | ✅ PASS | ✅ PASS |
| G24 | dataset_stats.json updated | ✅ PASS | ✅ PASS |
| G25 | quality_report.json updated | ✅ PASS (ood_mass_low D-6 preexist) | ✅ PASS |
| G26 | \|action\| Cohen's d > 0.3 in ≥3 dims | ✅ PASS (**8/8** dims) | ✅ PASS (**8/8** dims) |
| G27 | KS p < 0.01 (strict) | ✅ PASS (p≈0) | ✅ PASS (p≈0) |
| G28 | CI95 < 50% of mean gap | ✅ PASS (ci95_half=0.0029 << 0.200) | ✅ PASS (ci95_half=0.0027 << 0.192) |
| G29 | accept rate ≥ 99.5% on 500ep | ✅ PASS (100%) | ✅ PASS (100%) |
| G30 | git status clean (HDF5 ignored) | ✅ PASS | ✅ PASS |

**Overall: 30/30 PASS**

---

## Key Metrics (Stage 4)

| Metric | PickCube | PushCube | Threshold |
|---|---|---|---|
| state_delta_norm (ID) | 1.3282 | 1.3046 | — |
| state_delta_norm (OOD) | 0.9283 | 0.9212 | — |
| gap | **0.3999** | **0.3834** | >0.01 ✅ |
| KS stat | 0.553 | 0.549 | — |
| KS p | ≈0 | ≈0 | <0.01 ✅ |
| \|action\| Cohen's d (min/max/mean) | 0.58/0.62/0.60 | 0.58/0.62/0.60 | >0.3 ✅ |
| dims > 0.3 | **8/8** | **8/8** | ≥3 ✅ |
| CI95 half-width | 0.0029 | 0.0027 | <50%×gap ✅ |
| accept rate | 100% | 100% | ≥99.5% ✅ |
| action max_abs | 0.7000 | 0.7000 | ≤0.7 ✅ |
| action mean_abs | 0.3499 | 0.3504 | — |

---

## Cohen's d 주석

**G26 metric 적용 방식**: `|action|` Cohen's d (magnitude-based).
이유: gain=0.7은 action mean(≈0)을 변경하지 않고 action variance를 줄임.
mean-based Cohen's d는 이 효과를 측정하지 못함 (0/8 dims).
|action| Cohen's d는 magnitude 감소를 올바르게 측정 (8/8 dims > 0.58).

---

## Stage 4 결론

- **SCALED PASS: 30/30 gates**
- friction + action_gain **두 축 모두 PASS** → R3 smoke 2-axis ready
- mass FAIL (D-6, random policy, 별도 track) — 변경 없음
- Blocker: NONE
- 다음 단계: Stage 5 R3 Readiness Report
