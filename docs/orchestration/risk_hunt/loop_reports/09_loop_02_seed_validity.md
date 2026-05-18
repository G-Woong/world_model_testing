# Loop-02 Report: RH-STAT-01 — 5 Training Seeds (TASK_1129)

작성일: 2026-05-18
담당: Main Claude (STEP 10 Phase 2 Loop Execution)

---

## 목적

std=0.000 deterministic 문제 해결 → true across-seed variance 확보
5개 독립 학습 seed로 CI 작성 가능성 확인

---

## 구현 완료 사항

| 파일 | 변경 내용 | 상태 |
|---|---|---|
| `scripts/risk_hunt/run_multiseed_training.py` | seeds=[42,123,456,789,999] launcher | ✓ |
| `configs/lr_eval_step10_multiseed.yaml` | 5 FRCG-LR checkpoint eval config | ✓ |
| `tests/test_step10_multiseed.py` | 4 tests pass (dry-run 포함) | ✓ |

---

## 테스트 결과

```
tests/test_step10_multiseed.py: 4 passed
  - test_multiseed_script_exists: PASS
  - test_multiseed_eval_config_exists: PASS
  - test_multiseed_eval_config_has_5_seeds: PASS
  - test_multiseed_script_dry_run: PASS
tests/test_forbidden_field_mirror_sync.py: 3 passed (GREEN)
```

---

## Decision Gate

**PENDING**: 5× retrain 실행 필요 (예상 ~50분)

**실행 절차**:
```
python scripts/risk_hunt/run_multiseed_training.py
  → seed 42: outputs/checkpoints/pretrain_v0_4_seed42/checkpoint_best.pt
  → seed 123: outputs/checkpoints/pretrain_v0_4_seed123/checkpoint_best.pt
  → seed 456: outputs/checkpoints/pretrain_v0_4_seed456/checkpoint_best.pt
  → seed 789: outputs/checkpoints/pretrain_v0_4_seed789/checkpoint_best.pt
  → seed 999: outputs/checkpoints/pretrain_v0_4_seed999/checkpoint_best.pt

python scripts/10_run_lr_real_eval.py --config configs/lr_eval_step10_multiseed.yaml
```

| 조건 | KEEP | REJECT/MODIFY |
|---|---|---|
| std(F1) > 0.01 across seeds | true variance 있음, CI 작성 가능 | - |
| std < 0.01 but > 0.001 | 약한 variance → bootstrapping 보강 | MODIFY |
| std ≈ 0 | architecture invariance → 명시 보고 | REJECT (statistical claim 불가) |

---

## Blockers

- `configs/train_text_v0_4_long.yaml`에 `--seed` 및 `--checkpoint-dir` CLI 인수 지원 확인 필요
  → `scripts/02_train_text_smoke.py`가 이 인수를 처리하는지 확인 필요
- 예상 시간: 10분 × 5 = ~50분

---

## 결론

Loop-02 scaffold COMPLETE. 5-seed launcher 준비됨.
Retrain 실행 후 std 측정 → CI 작성 여부 결정.
