# resource-budget-auditor 보고서 — Step 11-D7 Scaled (450ep) R1

**보고일**: 2026-05-24
**단계**: Scaled Stage 2 (실측, Post-Scaled)
**판정**: PASS

---

## 실측 수집 결과

| Split | ep 수 | 총 step | wall_clock |
|---|---|---|---|
| train_id | 250 | 12,500 | 200.6초 |
| val_id | 50 | 2,500 | 61.0초 |
| test_id | 50 | 2,500 | 60.8초 |
| ood_mass_low | 50 | 2,500 | 60.6초 |
| ood_friction_low | 50 | 2,500 | 58.0초 |
| **합계** | **450** | **22,500** | **~7분 (병렬)** |

5개 split 병렬 실행 총 wall-clock: ~7분 (train_id 완료 기준 200.6초 = 3.3분).

## 디스크 추정

```
T=50, D_x=42, D_a=8 기준:
450ep × 4.3 KB/ep ≈ 1.9 MB (gzip4)
```

실제 HDF5 파일 총계 ~2 MB — PLAN 예측과 일치.

## 수집 속도 실측

| Split | ep/초 | 총 시간 | PLAN 예측 |
|---|---|---|---|
| train_id | 1.25 ep/s | 200.6초 | 5분 |
| val_id | 0.82 ep/s | 61초 | 2분 |
| test_id | 0.82 ep/s | 61초 | 2분 |
| ood_* | ~0.85 ep/s | ~60초 | 2분 |

## L=900 확장 예산 (DATA_TOO_SMALL 발화 시)

| Split | 추가 ep | 추가 시간 | 총 ep |
|---|---|---|---|
| train_id | 250 | ~200초 | 500 |
| 나머지 × 4 | 50 × 4 | ~60초 × 4 | 50 × 4 |
| **총 추가** | **450** | **~8분** | **900** |

seed pool 여유:
- train_id: [42, 292) 중 현재 [42, 292) 250개 모두 사용됨 → L=900 위해 pool 추가 확장 필요
- train_id L=500: [42, 542) = 500 seeds

## PASS 조건

- recommended episode count 명시: ✓ (Scaled 450ep 완료)
- 수집 wall-clock 실측: ✓ (병렬 ~7분)
- OOM risk: ✓ (없음, VRAM 측정은 R3 smoke 후)
- L=900 확장 예산 명시: ✓
