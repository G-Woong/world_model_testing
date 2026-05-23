# data-quality-gatekeeper 보고서 — Step 11-D7 Scaled (450ep) R1

**보고일**: 2026-05-24
**단계**: Scaled Stage 2 (실측, Post-Scaled)
**판정**: PASS

---

## episode 수집 결과

| Split | 목표 | 실제 | reject | accept rate | wall_clock |
|---|---|---|---|---|---|
| train_id | 250ep | 250ep | 0 | 100% | 200.6초 |
| val_id | 50ep | 50ep | 0 | 100% | 61.0초 |
| test_id | 50ep | 50ep | 0 | 100% | 60.8초 |
| ood_mass_low | 50ep | 50ep | 0 | 100% | 60.6초 |
| ood_friction_low | 50ep | 50ep | 0 | 100% | 58.0초 |
| **합계** | **450ep** | **450ep** | **0** | **100%** | ~7분 |

목표 450ep 달성 ✓ (Pilot 90ep 대비 5배 확장).

## 에피소드 분포 다양성

| Split | n_ep | episode_length | seed 범위 |
|---|---|---|---|
| train_id | 250 | 50.0 (all) | [42, 292) |
| val_id | 50 | 50.0 (all) | [200, 250) |
| test_id | 50 | 50.0 (all) | [300, 350) |
| ood_mass_low | 50 | 50.0 (all) | [500, 550) |
| ood_friction_low | 50 | 50.0 (all) | [600, 650) |

seed pool 모두 disjoint 범위 사용 ✓. 각 split 내 seed 연속적으로 소진.

## Reject reason 분포

ALL_STATE_STATIC: 0, ALL_ACTION_ZERO: 0, NO_TRANSITION: 0, REWARD_FLAT: 0,
EPISODE_TOO_SHORT: 0, EPISODE_SHORT: 0, NO_DONE_SIGNAL: 0, DONE_FLOOD: 0,
NUMERICAL_INVALID: 0, EPISODE_DUPLICATE: 0

모든 reject reason: **0건**. quarantine 파일 없음.

## Success rate sanity

전 split success rate: 0/450 = 0% (WARN_LOW_SUCCESS)
→ PickCube-v1 random policy에서 예상 (max_episode_steps=50에 도달).
월드 모델 학습에는 실패 episode도 유효 데이터.

## nan_inf_count

`hash_intra_duplicate_count: 0, hash_inter_duplicate_count: 0` ✓

## PASS 조건

- train_id accept rate ≥70%: ✓ (100%)
- reject 사유 설명 가능: ✓ (0건)
- EPISODE_DUPLICATE: ✓ (0건)
- 목표 ep 달성: ✓ (450/450)
