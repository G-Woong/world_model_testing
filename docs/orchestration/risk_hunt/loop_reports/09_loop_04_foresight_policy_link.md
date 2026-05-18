# Loop-04 Report: RH-FORE-01 — Foresight Causal Influence (TASK_1124)

작성일: 2026-05-18
담당: Main Claude (STEP 10 Phase 2 Loop Execution)

---

## 목적

World model rollout이 policy action을 실제로 바꾸는가? (Claim-C 검증)
`divergence_rate = E[action_changed_by_rollout]`가 Claim-C의 실험 근거

---

## 구현 완료 사항

| 파일 | 변경 내용 | 상태 |
|---|---|---|
| `src/frcgw/evaluation/frcg_agent.py` | `last_action_changed_by_rollout` 속성 + rollout_off 비교 | ✓ |
| `src/frcgw/evaluation/eval_runner.py` | step_result에 `action_changed_by_rollout` 기록 | ✓ |
| `scripts/risk_hunt/compute_foresight_causal.py` | divergence_rate 집계 스크립트 | ✓ |
| `tests/test_step10_foresight_causal.py` | 4 tests pass | ✓ |

---

## 구현 방법

`act()` 내부에서:
1. `rollout_off_gate_config = replace(gate_config, gate_mode="never_plan")` 생성
2. `rollout_off_planner_state = deepcopy(self._planner_state)` (state 변조 방지)
3. `rollout_off_action = text_frcg_plan(..., rollout_off_gate_config)` 호출
4. `action_changed_by_rollout = (action.action_id != rollout_off_action.action_id)` 비교

**Leakage 검토**: public_observation만 사용, hidden label 미사용 ✓

---

## 테스트 결과

```
tests/test_step10_foresight_causal.py: 4 passed
  - test_foresight_causal_script_exists: PASS
  - test_action_changed_attr_default: PASS
  - test_eval_runner_records_field: PASS
  - test_compute_foresight_causal_empty_dir: PASS
tests/test_step9_regime_shift_f1.py: 6 passed (no regression)
tests/test_forbidden_field_mirror_sync.py: 3 passed (GREEN)
```

---

## Decision Gate

**PENDING**: eval 실행 필요

**실행 절차**:
```
python scripts/10_run_lr_real_eval.py --config configs/lr_eval_step9_c3_recovery.yaml
python scripts/risk_hunt/compute_foresight_causal.py --result-dir outputs/risk_hunt/experiments/
```

| 조건 | KEEP | MODIFY | REJECT |
|---|---|---|---|
| divergence_rate > 10% | Claim-C alive | - | - |
| 5-10% | - | foresight-to-policy adapter (Arch I) 추가 | - |
| < 5% | - | - | foresight cosmetic → Claim-C 제거 |

---

## Blockers

- eval config에 `action_changed_by_rollout` 기록 활성화 확인 필요
- `outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt` 존재 필요

---

## 결론

Loop-04 scaffold COMPLETE. divergence_rate logger 구현 완료 (leakage 없음).
Eval 실행 후 Claim-C alive/dead verdict 결정 가능.
