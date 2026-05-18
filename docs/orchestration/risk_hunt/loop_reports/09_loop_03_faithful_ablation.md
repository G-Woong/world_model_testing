# Loop-03 Report: RH-FAI-01 — ABL-001/003 Faithful Retrain (TASK_1127/1128)

작성일: 2026-05-18
담당: Main Claude (STEP 10 Phase 2 Loop Execution)

---

## 목적

Regime latent 제거(ABL-001) / 병합(ABL-003) 시 C2/C3 collapse 확인 → separability claim 근거

Fix-A 적용 완료:
- ABL-001 eval config: `outputs/checkpoints/abl001_no_regime/checkpoint_best.pt` (수정됨)
- ABL-003 eval config: `outputs/checkpoints/abl003_merged_regime_grammar/checkpoint_best.pt` (수정됨)

---

## 구현 완료 사항

| 파일 | 변경 내용 | 상태 |
|---|---|---|
| `scripts/risk_hunt/run_abl001_retrain.py` | ABL-001 retrain + eval launcher | ✓ |
| `configs/lr_eval_step10_abl001.yaml` | abl001_no_regime/ checkpoint, regime_shift_f1 metric | ✓ |
| `tests/test_step10_abl001_retrain.py` | 4 tests pass | ✓ |
| `scripts/risk_hunt/run_abl003_retrain.py` | ABL-003 retrain + eval launcher | ✓ |
| `configs/lr_eval_step10_abl003.yaml` | abl003_merged_regime_grammar/ checkpoint, C2+C3 metrics | ✓ |
| `tests/test_step10_abl003_retrain.py` | 4 tests pass | ✓ |

---

## 테스트 결과

```
tests/test_step10_abl001_retrain.py: 4 passed
tests/test_step10_abl003_retrain.py: 4 passed
tests/test_forbidden_field_mirror_sync.py: 3 passed (GREEN)
```

---

## Decision Gate

**PENDING**: 실제 retrain 및 eval 실행 필요

**ABL-001 (l_regime=0.0) 실행 절차**:
```
python scripts/risk_hunt/run_abl001_retrain.py
  └─ python scripts/02_train_text_smoke.py --config configs/train_text_v0_4_abl001.yaml
  └─ python scripts/10_run_lr_real_eval.py --config configs/lr_eval_step10_abl001.yaml
```

**ABL-003 (merged_regime_grammar) 실행 절차**:
```
python scripts/risk_hunt/run_abl003_retrain.py
```

**주의**: `warm_start_checkpoint: outputs/checkpoints/pretrain_v0_4_long_stageA/checkpoint_best.pt`
→ stageA checkpoint 없으면 `pretrain_v0_4_long/checkpoint_best.pt`로 대체 필요

| 조건 | KEEP | REJECT |
|---|---|---|
| ABL-001: regime_shift_f1 collapse(≈0.0), C3 F1 유지(>0.3) | regime latent → C2 전용 | - |
| ABL-003: C2+C3 동시 collapse | disentanglement claim 근거 | - |
| no collapse (C3 유지 under ABL-001) | - | regime loss → C3에도 필수 → claim 수정 |

---

## Blockers

- train config의 warm_start checkpoint 경로 확인 필요 (`pretrain_v0_4_long_stageA/`)
- 예상 retrain 시간: ~30분 × 2 = ~1시간
- eval 시간: ~20분 × 2

---

## 결론

Loop-03 scaffold COMPLETE. Fix-A 정확히 적용됨 (올바른 checkpoint 경로).
Retrain 실행 후 KEEP/REJECT verdict 결정 가능.
