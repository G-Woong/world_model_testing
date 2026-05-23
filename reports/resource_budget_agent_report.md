# resource-budget-auditor 보고서 — Step 11-D7 Pilot (90ep)

**보고일**: 2026-05-23
**단계**: Pilot Stage 1 (실측, Post-Pilot)
**판정**: PASS

---

## 실측 디스크 / 시간 / VRAM

### 수집 실측

| Split | ep 수 | episode_length_mean | 총 step |
|---|---|---|---|
| train_id | 50 | 50.0 | 2,500 |
| val_id | 10 | 50.0 | 500 |
| test_id | 10 | 50.0 | 500 |
| ood_mass_low | 10 | 50.0 | 500 |
| ood_friction_low | 10 | 50.0 | 500 |
| **합계** | **90** | 50.0 | **4,500** |

> episode_length_mean=50: max_episode_steps=50에 random policy가 모두 도달. PLAN의 T_avg=70 추정보다 실제는 정확히 50.

### 디스크 추정 (실측 T=50 기준)

```
state:  float32 (50, 42) →  8.4 KB/ep raw
action: float32 (50,  8) →  1.6 KB/ep raw
reward: float32 (50,)    →  0.2 KB/ep raw
done:   bool    (50,)    →  0.05 KB/ep raw
raw total: ≈ 10.2 KB/ep  (PLAN 예측 14.4 KB vs 실측: T=50 < T=70)
gzip4 (~35%): ≈ 3.6 KB/ep
+ attrs/overhead: ~700 B/ep
≈ 4.3 KB/ep (gzip4 포함)
```

| 단계 | 목표 ep | 예측 크기 | 비고 |
|---|---|---|---|
| Pilot (실측) | 90 | ~0.4 MB | ✓ |
| Scaled | 450 | ~1.9 MB | 여유 |
| L=900 | 900 | ~3.9 MB | 여유 |

### VRAM 실측 (R3 smoke)

- `train_vram_peak_mib`: **33.25 MiB** (8 GB의 **0.4%**)
- batch(16) × T(8) × K(6) × d(32): 모델 정상 작동 확인.
- OOM risk: 없음. Scaled 450ep에서도 동일 batch/horizon 유지 가능.

### 학습 시간 실측

- 5 epoch / 50ep: **0.036분 (2.2초)**
- 50 epoch 추정: ~22초
- 100 epoch 추정: ~44초

→ `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md:42-78` 예측 "≤30분/iter"보다 실제 훨씬 빠름 (90ep 소규모 데이터 한계).

### 수집 wall-clock (추정)

- PLAN 예측: T=70 → 2.8s/ep → 180ep ≈ 8.4분
- 실측 T=50 → 2.0s/ep → 90ep ≈ 3분 (실제는 더 빨랐을 것)

## Seed pool 한계 분석

| Split | 현재 pool | 최대 ep | 목표(Scaled) | 부족분 |
|---|---|---|---|---|
| train_id | [42, 92) = 50 seeds | 50 ep | 250 ep | **200 ep 부족** |
| val_id | [200, 210) = 10 seeds | 10 ep | 50 ep | **40 ep 부족** |
| test_id | [300, 310) = 10 seeds | 10 ep | 50 ep | **40 ep 부족** |
| ood_mass_low | [500, 510) = 10 seeds | 10 ep | 50 ep | **40 ep 부족** |
| ood_friction_low | [600, 610) = 10 seeds | 10 ep | 50 ep | **40 ep 부족** |

**핵심 BLOCKER**: Scaled 450ep 달성 위해 seed pool 확장 필수.

권장 확장안:
- `train_id`: [42, 292) = 250 seeds → max 250 ep ✓
- `val_id`: [200, 250) = 50 seeds → max 50 ep ✓
- `test_id`: [300, 350) = 50 seeds → max 50 ep ✓
- `ood_mass_low`: [500, 550) = 50 seeds → max 50 ep ✓
- `ood_friction_low`: [600, 650) = 50 seeds → max 50 ep ✓

또는 `collect_maniskill.py SPLIT_DEFAULTS`에서 `max_retry` 활용 (동일 seed 다른 random policy init → 중복 hash 체크로 필터링).

## OOM fallback 순서 (필요 시)

1. batch_size: 16 → 8 (절반)
2. train_horizon: 8 → 4 (절반)
3. K: 6 → 4 (group 축소)
4. d: 32 → 16 (latent dim 축소)
5. h_dim: 128 → 64

현재 VRAM 33 MiB 사용 → OOM까지 8192/33 ≈ 248× 여유. **OOM fallback 불필요**.

## PASS 조건

- recommended episode count 명시: ✓ (Scaled 450ep)
- OOM fallback 순서 명시: ✓ (불필요하나 명시)
- seed pool 확장 필요성 명시: ✓
- disk/time/VRAM 실측 vs 예측 비교: ✓
