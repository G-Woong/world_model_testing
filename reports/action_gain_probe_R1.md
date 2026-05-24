# Action_Gain Probe Report — R1 (Stage 2)

**Date**: 2026-05-24
**Branch**: memory-redesign-2026-05-16
**Split**: ood_gain_low (gain=0.7)
**Episodes**: 50 × 2 task (quarantine, NOT committed)
**Seeds**: PickCube 700-760, PushCube 2000-2060

---

## 16-Gate Lenient Results

| Gate | Description | PickCube | PushCube |
|---|---|---|---|
| G1 | Schema consistency | ✅ PASS (50ep loaded) | ✅ PASS (50ep loaded) |
| G2 | D_x/D_a dims | ✅ PASS (42/8) | ✅ PASS (35/8) |
| G3 | dtype float32 | ✅ PASS | ✅ PASS |
| G4 | NaN/Inf count | ✅ PASS (0) | ✅ PASS (0) |
| G5 | Reward scalar | ✅ PASS | ✅ PASS |
| G6 | Done consistency | ✅ PASS | ✅ PASS |
| G7 | Accept rate ≥99% | ✅ PASS (100%) | ✅ PASS (100%) |
| G8 | Reject reason logged | ✅ PASS (none) | ✅ PASS (none) |
| G9 | State_delta non-degenerate | ✅ PASS (0.9301) | ✅ PASS (0.9222) |
| G10 | Action_norm non-degenerate | ✅ PASS (0.3516) | ✅ PASS (0.3509) |
| G11 | true_action_gain == 0.7 | ✅ PASS | ✅ PASS |
| G12 | Forbidden field in inference | ✅ PASS (0) | ✅ PASS (0) |
| G13 | Reproducibility (same seed) | ✅ PASS (clip bound invariant) | ✅ PASS |
| G14 | Clip range [low, high] | ✅ PASS (min=-0.70 max=0.70) | ✅ PASS (min=-0.70 max=0.70) |
| G15 | Action norm reduced (≤ID×0.95) | ✅ PASS (ratio=0.702) | ✅ PASS (ratio=0.701) |
| G16 | State_delta_norm gap >0.005 | ✅ PASS (gap=**0.3984**) | ✅ PASS (gap=**0.3795**) |

**Overall: 16/16 PASS** → Stage 3 Pilot 진입 조건 충족

---

## Key Metrics

| Metric | PickCube | PushCube | Threshold |
|---|---|---|---|
| state_delta_norm (ID) | 1.3284 | 1.3017 | — |
| state_delta_norm (OOD) | 0.9301 | 0.9222 | — |
| gap | **0.3984** | **0.3795** | >0.005 (lenient) |
| action_mean_abs (ID) | 0.5010 | 0.5002 | — |
| action_mean_abs (OOD) | 0.3516 | 0.3509 | — |
| gain ratio | 0.702 | 0.701 | ≈0.7 ✅ |
| clip max | 0.7000 | 0.7000 | ≤0.7 ✅ |

---

## Stage 2 결론

- **PROBE PASS**: 16/16 gates, gap >> 0.005
- gap이 friction (gap≈0.13) 보다 훨씬 크다. action_gain axis가 state_delta에 강한 영향을 미침.
- 이유: gain=0.7이 action magnitude 30% 감소 → robot 이동량 감소 → state 변화량 감소.
- Blocker: NONE
- 다음 단계: Stage 3 Pilot 100ep × 2 task
