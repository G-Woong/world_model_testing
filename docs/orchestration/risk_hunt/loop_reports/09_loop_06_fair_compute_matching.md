# Loop-06 Report: RH-EVAL-02 — Fair Compute Matching (TASK_1125/1132)

작성일: 2026-05-18
담당: Main Claude (STEP 10 Phase 2 Loop Execution)

---

## 목적

C6 14.9× advantage가 fair compute 조건에서도 유지되는가?
Wall-clock denominator + RealNoGateAblation(faithful ABL-036b) 도입

---

## 구현 완료 사항

| 파일 | 변경 내용 | 상태 |
|---|---|---|
| `src/frcgw/evaluation/frcg_agent.py` | `time.perf_counter()` wall-clock 기록 | ✓ |
| `src/frcgw/evaluation/metrics.py` | `fair_ppc()` compute_logs 리스트 처리 | ✓ |
| `src/frcgw/evaluation/ablations.py` | `RealNoGateAblation` (ABL-036b) 추가 | ✓ |
| `src/frcgw/evaluation/eval_runner.py` | RealNoGateAblation 등록 | ✓ |
| `configs/lr_eval_step10_fair_compute.yaml` | FRCG-LR vs ABL-036b vs ABL-036 heuristic | ✓ |
| `tests/test_step10_fair_ppc.py` | 4 tests pass | ✓ |
| `tests/test_step10_fair_compute.py` | 4 tests pass | ✓ |

---

## RealNoGateAblation 설계

```python
class RealNoGateAblation(AblatedAgent):
    ablation_id = "real_no_gate"  # ABL-036b
    always_plan = True
    # TextFRCGModelAgent wrapping with gate_mode="always_plan"
    # planning_calls=1 per step guaranteed
    # full FRCG model forward (not heuristic bypass)
```

기존 `NoComputeGateAblation` (heuristic bypass, no model forward)과의 차이:
- ABL-036b: FRCG model forward O, gate=always → fair wall-clock denominator
- ABL-036: heuristic bypass → biased self-report denominator

---

## 테스트 결과

```
tests/test_step10_fair_ppc.py: 4 passed
tests/test_step10_fair_compute.py: 4 passed
  - test_real_no_gate_ablation_class_exists: PASS
  - test_real_no_gate_ablation_id: PASS
  - test_fair_compute_eval_config_exists: PASS
  - test_fair_compute_config_has_fair_ppc: PASS
tests/test_step9_regime_shift_f1.py: 6 passed (no regression)
tests/test_forbidden_field_mirror_sync.py: 3 passed (GREEN)
```

---

## Decision Gate

**PENDING**: eval 실행 필요

**실행 절차**:
```
python scripts/10_run_lr_real_eval.py --config configs/lr_eval_step10_fair_compute.yaml
```

결과에서 `fair_ppc_ratio = ppc_wall(FRCG-LR) / ppc_wall(ABL-036b)` 계산

| 조건 | KEEP | MODIFY | REJECT |
|---|---|---|---|
| fair_ppc ratio > 2.0 | C6 claim alive | - | - |
| 1.5-2.0× | - | moderate advantage, 보고 | - |
| < 1.5× | - | - | self-report bias 지배 → C6 격하 |

---

## 예상 결과

현재 14.9× (self-report 기반)는 bias가 포함됨.
Fair wall-clock 기준:
- FRCG-LR: 실제 text_frcg_plan() 시간 (rollout + model forward)
- ABL-036b: model forward (always_plan, 더 짧음)
- Fair ratio = FRCG-LR progress / wall_clock vs ABL-036b progress / wall_clock

---

## Blockers

- `outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt` 존재 필요

---

## 결론

Loop-06 scaffold COMPLETE. Fair compute infrastructure 완성.
- wall-clock 기록: frcg_agent.py ✓
- RealNoGateAblation: ablations.py ✓
- eval config: lr_eval_step10_fair_compute.yaml ✓
Eval 실행 후 C6 advantage 검증 가능.
