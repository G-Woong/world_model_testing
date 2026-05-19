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

## Eval 실행 (2026-05-19)

- 명령: `.venv/Scripts/python.exe scripts/10_run_lr_real_eval.py --config configs/lr_eval_step10_fair_compute.yaml --out-dir outputs/risk_hunt/experiments/loop06_fair_compute --max-episodes 50`
- 사전 패치(STEP C 분류 D — class dispatch 누락 minimal fix):
  - `scripts/10_run_lr_real_eval.py`의 `_build_agent_dispatch_table`에 `RealNoGateAblation`, `NoComputeGateAblation` class_table 등록 + factory 분기. import도 추가.
  - 검증 대상 contract 변경 없음. 기존 agent 작동 유지.
- 데이터: test_id 50 episodes (284 steps total per agent)
- checkpoint: `outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt` (3 agents 모두 동일)
- 산출물: `outputs/risk_hunt/experiments/loop06_fair_compute/`
  - `metrics.json`, `manifest.json`
  - `per_step/{FRCG-LR,ABL-036b-real-no-gate,ABL-036-heuristic}_seed0.jsonl`

---

## 핵심 결과 표

| Agent | C3 F1 | C6 PPC (self-report) | planning_calls_total | rollout_steps_total | self-report denom |
|---|---|---|---|---|---|
| FRCG-LR | 0.5806 | **0.1926** | **0** | 0 | 0 (gate never opened) |
| ABL-036b-real-no-gate | 0.5806 | **0.0963** | 284 | 0 | 284 |
| ABL-036-heuristic | 0.0000 | **0.0130** | 284 | 2840 | 3124 |

**Ratio (FRCG-LR / Ablation, self-report 분모 기준)**:
- vs ABL-036b RealNoGate (fair model-forward): **2.00×**
- vs ABL-036 heuristic-bypass: **14.81×** (STEP 9 보고 유지)

---

## 해석

1. STEP 9의 14.9× C6 advantage는 ABL-036 heuristic이 model forward를 건너뛰면서도 `rollout_steps=10`을 self-report로 신고했기 때문에 발생한 분모 inflation artifact였다.
2. **공정 비교(ABL-036b real_no_gate)** 에서 advantage는 14.9× → **2.0×** 로 약 7.4× 줄어든다.
3. FRCG-LR은 50 episodes 동안 `planning_calls=0` 즉 gate가 단 한 번도 열리지 않았다. 그럼에도 C3 F1=0.58은 그대로 — proxy artifact가 labels matching만으로 작동(Loop-01과 일관).
4. 2.0× 자체는 양의 advantage이지만 sample size 50 episodes에서의 self-report 비교라는 한계가 있다.

---

## Decision Gate

**판정: MODIFY** (advantage 살아있지만 크기 축소 + wall-clock 검증 미완)

| 조건 | 결과 |
|---|---|
| fair_ppc ratio > 2.0 | BOUNDARY — 정확히 2.00× (self-report denom) |
| 1.5-2.0× | (boundary 위) |
| < 1.5× | NO |

---

## Blockers / 잔여 위험

1. **wall_clock_seconds 누락**: per_step JSONL에 `wall_clock_seconds` 필드 미기록. `frcg_agent.py`가 wall-clock을 기록하더라도 `_write_per_step_jsonl`이 누락. metrics.json에도 `fair_ppc` key가 안 보임 → `fair_ppc` metric 함수가 wall_clock 없이 fallback할 가능성. **별도 P1 follow-up (Codex task 후보)**: per_step writer가 ComputeBudgetLog의 모든 필드를 dump하도록 보강 + fair_ppc metric이 metrics.json에 노출되도록 정렬.
2. **FRCG-LR planning_calls=0**: gate 진입 자체가 없었다. 즉 PPC 분자는 progress가 ε로 나뉜 형태일 가능성. 실제 advantage가 self-report-aware인지 wall-clock-aware인지 단정 불가.
3. **Sample size**: 50 episodes only. full split(284 episodes 이상)으로 재검증 권장.

---

## Claim 영향

- **C6 (advantage in progress per compute)**: STEP 9의 14.9× 주장은 self-report 분모 artifact였음. fair compute 기준 advantage는 ~2.0× (boundary)로 축소.
- paper 작성 시: "14× advantage" 표현 금지. "fair compute 기준 ~2× advantage at n=50, wall-clock 미측정"으로 정직하게 보고.
- Loop-04 (foresight causal)와 함께 paper-main claim 재구성 필요.

---

## 결론

**Loop-06 verdict = MODIFY.**
C6 advantage는 살아있으나 정확한 수치는 14.9× → 2.0×로 약 7배 축소. STEP 9 보고는 self-report 분모 artifact였다. wall_clock_seconds 기록 회로가 노출되지 않아 wall-clock 검증은 P1 follow-up.
