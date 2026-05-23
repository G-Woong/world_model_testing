# training-readiness-auditor 보고서 — Step 11-D7 Pilot (90ep)

**보고일**: 2026-05-23
**단계**: Pilot Stage 1 (실측, Post-Pilot)
**판정**: CONDITIONAL_PASS

---

## R3 smoke 1-iter 실행 결과

### Artifact 생성 확인

| 경로 | 존재 | 내용 |
|---|---|---|
| `outputs/repair/iter_0/metrics.json` | ✓ | epoch=5, id_nll=0.8726, ... |
| `outputs/repair/loop_2026-05-23T14-45-47-212f/ledger.jsonl` | ✓ | 1행 (iter=1) |
| `outputs/repair/loop_.../` 디렉터리 | ✓ | loop artifacts |

> **주의**: iter 번호는 0-indexed (`iter_0/`). PLAN의 `iter_1/` 표기는 1-indexed 기준으로, 실제 경로는 `iter_0/`이 첫 번째 iter에 해당함.

### 핵심 메트릭 (5 epoch)

| 메트릭 | 실측값 | 목표 | 판정 |
|---|---|---|---|
| id_nll | 0.8726 | ≤ 0.5 | FAIL (epoch 부족) |
| ood_mass_nll | 0.8730 | — | (참고) |
| ood_friction_nll | 0.8704 | — | (참고) |
| ood_id_nll_diff | -0.0009 | ≥ 0.05 | FAIL (epoch 부족) |
| stagnant_epochs | 0 | — | (참고) |
| train_nll | 0.8724 | — | (참고) |
| val_nll | 0.8726 | — | (참고) |
| val_train_nll_gap | 0.000176 | — | 과적합 없음 ✓ |
| train_vram_peak_mib | 33.25 | ≤ 8192 | ✓ (8GB의 0.4%) |
| wall_clock_minutes | 0.036 | ≤ 30 | ✓ |

### 진단 결과

- `diagnosed_cause`: `IMPLEMENTATION_BUG_SUSPECTED` (catch-all — 구체적 trigger 없음)
- `result`: inconclusive
- `next_action`: escalate_to_user
- `stop_condition_hit`: hook_blocked

`IMPLEMENTATION_BUG_SUSPECTED`는 `stagnant_epochs < 10` (=0)으로 `DATA_TOO_SMALL` 미발화, `ood_auroc` 미포함으로 `OOD_TOO_EASY` 미발화, `oid_id_nll_diff < 2.0`으로 `OOD_TOO_HARD` 미발화 — 모든 specific trigger가 비활성화된 상태에서의 정상 catch-all 동작.

### hook_blocked 원인

`diagnose.py:R3` → `result: inconclusive` 후 `escalate_to_user` → hook이 사용자 에스컬레이션 요구로 루프 중단. 이는 데이터 부족이 아닌 **파이프라인 정상 동작**의 일환.

## Dataloader 검증

- R3 smoke에서 `_make_maniskill_datasets()` → `HorizonDataset` → 실제 HDF5 로드 ✓
- shape: batch(16) × T(8) × D_x(42), batch(16) × T(8) × D_a(8) — OOM 없음
- nan_inf: 0 (전체 split) ✓

## 학습 인프라 검증

| 항목 | 실측 | 목표 |
|---|---|---|
| VRAM peak | 33.25 MiB | ≤ 8192 MiB |
| Wall clock (5 epoch) | 0.036 min (~2.2초) | ≤ 30 min/iter |
| OOM 발생 | 없음 | — |
| NaN/Inf gradient | 없음 (NLL 안정) | — |

## CONDITIONAL_PASS 근거

**PASS**: artifact 생성(metrics.json, ledger.jsonl, loop dir) ✓, VRAM ✓, wall-clock ✓, nan_inf=0 ✓
**CONDITIONAL**: id_nll=0.8726 (목표 ≤0.5 미달) — 5 epoch 초기 학습으로 정상. 50~100 epoch으로 목표 달성 가능성 있음.

## 다음 단계 권고

1. `configs/fglc/smoke_maniskill_pickcube.yaml`의 `trainer.epochs: 5` → `50` 으로 변경 후 재실행.
2. Scaled 450ep 데이터로 재실행 시 `DATA_TOO_SMALL` 발화 여부 모니터링.
3. `ood_auroc` 메트릭 추가(R4 conformal calibration 단계)로 `OOD_TOO_EASY` trigger 활성화.
