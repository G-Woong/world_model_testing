# data-quality-gatekeeper 보고서 — Step 11-D7 Pilot (90ep)

**보고일**: 2026-05-23
**단계**: Pilot Stage 1 (실측, Post-Pilot)
**판정**: PASS

---

## episode 수집 결과

| Split | 목표 | 실제 | reject | accept rate |
|---|---|---|---|---|
| train_id | 100ep | 50ep | 0 | 100% |
| val_id | 20ep | 10ep | 0 | 100% |
| test_id | 20ep | 10ep | 0 | 100% |
| ood_mass_low | 20ep | 10ep | 0 | 100% |
| ood_friction_low | 20ep | 10ep | 0 | 100% |
| **합계** | **180ep** | **90ep** | **0** | **100%** |

## 목표 대비 shortfall

seed pool 한계로 계획 180ep 대비 **90ep(50%)** 수집. 원인:
- train_id pool: range(42, 92) = 50 seeds → max 50ep
- val/test/ood pools: 각 10 seeds → max 10ep
- Scaled 단계에서 pool 확장(train_id → range(42, 192) 등) 필요

## Reject reason 분포

ALL_STATE_STATIC: 0, ALL_ACTION_ZERO: 0, NO_TRANSITION: 0, REWARD_FLAT: 0,
EPISODE_TOO_SHORT: 0, EPISODE_SHORT: 0, NO_DONE_SIGNAL: 0, DONE_FLOOD: 0,
NUMERICAL_INVALID: 0, EPISODE_DUPLICATE: 0

모든 reject reason: **0건**. PickCube-v1 random policy가 clean episodes를 생산.

## Success rate sanity

train_id success rate: 0/50 = 0% (WARN_LOW_SUCCESS < 30% Pilot 기준)
→ PickCube-v1 random policy에서 0% 예상됨. 월드 모델 학습에는 실패 episode도 유효.

## nan_inf_count

전체 split: 0 (PASS)

## PASS 조건

- train_id accept rate ≥ 70%: ✓ (100%)
- reject 사유 설명 가능: ✓ (0건, seed pool 소진)
- EPISODE_DUPLICATE: ✓ (0건)
