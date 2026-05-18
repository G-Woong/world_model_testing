# Loop-01 Report: RH-CORE-01 — Proxy OFF Ablation (TASK_1131/1134)

작성일: 2026-05-18
담당: Main Claude (STEP 10 Phase 2 Loop Execution)

---

## 목적

C3 F1=0.539가 `no_state_change→effect_type=3` proxy 없이도 유지되는가?

TASK_1131 Fix-B 적용 완료:
- line 122 `_obs_effect_type_id` 게이팅
- line 124 `_observed_failed` 게이팅 (both lines gated for full proxy decoupling)

---

## 구현 완료 사항

| 파일 | 변경 내용 | 상태 |
|---|---|---|
| `src/frcgw/planning/decision_gate.py` | `GateConfig.use_no_state_change_proxy: bool = True` 추가 | ✓ |
| `src/frcgw/planning/planner.py` | line 122, 124 모두 proxy 게이팅 | ✓ |
| `configs/lr_eval_step10_proxy_ablation.yaml` | proxy-on vs proxy-off eval config | ✓ |
| `scripts/risk_hunt/run_proxy_ablation_eval.py` | 비교 eval 실행기 | ✓ |
| `tests/test_step10_proxy_ablation.py` | 4 tests pass | ✓ |

---

## 테스트 결과

```
tests/test_step10_proxy_ablation.py: 4 passed
tests/test_forbidden_field_mirror_sync.py: 3 passed (GREEN)
tests/test_step9_regime_shift_f1.py: 6 passed (no regression)
Total: 13 passed
```

---

## Decision Gate

**PENDING**: eval 실행 필요 (TASK_1134 scaffold 완료, 실제 eval은 `pretrain_v0_4_long/checkpoint_best.pt` 필요)

```
configs/lr_eval_step10_proxy_ablation.yaml:
  - FRCG-LR-proxy-on (use_no_state_change_proxy=True)
  - FRCG-LR-proxy-off (use_no_state_change_proxy=False)
metrics: falsification_precision_recall, threshold_free_c3_auroc
split: test_id, seeds=[0]
```

| 조건 | KEEP | REJECT |
|---|---|---|
| proxy-off AUROC > 0.55 | learned signal exists → C3 claim alive | - |
| proxy-off AUROC ≈ 0.5 | - | C3 is purely proxy artifact → claim 격하 |

**실행 명령**: `python scripts/risk_hunt/run_proxy_ablation_eval.py`

---

## Blockers

- Eval 실행 전: `outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt` 존재 확인 필요
- ABL-040 regression: test_step9_regime_shift_f1.py GREEN (no proxy regression confirmed)

---

## 결론

Loop-01 scaffold COMPLETE. Fix-B 정확히 적용됨 (line 122+124 모두 게이팅).
Eval 실행 후 KEEP/REJECT verdict 결정 가능.
