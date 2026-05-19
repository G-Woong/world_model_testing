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

## Eval 실행 (2026-05-19)

- 명령: `.venv/Scripts/python.exe scripts/risk_hunt/run_proxy_ablation_eval.py --max-episodes 50`
- 데이터: test_id 50 episodes (284 steps total per agent)
- checkpoint: `outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt`
- 산출물: `outputs/risk_hunt/experiments/loop01_proxy_ablation/test_id/`
  - `metrics.json`
  - `per_step/FRCG-LR-{proxy-on,proxy-off}_seed0.jsonl`
  - `proxy_ablation_summary.json`

---

## 핵심 결과 표

| Metric | FRCG-LR proxy-ON | FRCG-LR proxy-OFF |
|---|---|---|
| C3 falsification F1 | **0.5806** | **0.0000** |
| C3 precision | 0.4932 | 0.0000 |
| C3 recall | 0.7059 | 0.0000 |
| C6 progress_per_compute | 0.1926 | 0.1926 |
| Mean planner F_t | +0.0984 | **-0.4636** |
| Steps with F_t > τ_f | 146 / 284 | **0 / 284** |
| Max planner F_t | 2.774 | **0.000** |
| Steps with observed=no_state_change | 149 / 284 | 149 / 284 (동일 입력) |
| Predicted-wrong count | 146 | 0 |

C5 status (양쪽 동일): `BLOCKED_DEGENERATE_PREDICTOR` (mean_wrong_prob=0.473, variance=0.047).

---

## 해석

1. 같은 episodes·같은 observed_effect_type 분포에서 proxy OFF는 F_t 신호를 **단 한 step도** 임계 위로 올리지 못한다. 학습된 falsification signal이 존재하지 않는다.
2. proxy ON에서 모든 positive 예측(146건)이 `observed_effect_type == "no_state_change"` 휴리스틱과 일대일 대응한다.
3. C6 PPC는 양쪽 동일 — proxy는 planning gate 자체를 변경하지 않고 falsification label에만 영향. ABL-036 비교(Loop-06)는 별개 신호.
4. STEP 9 C3 F1=0.539/0.587 회복은 **순전히 `no_state_change → effect_type=3` proxy artifact**다.

---

## Decision Gate

**판정: REJECT** (no learned C3 signal)

| 조건 | 결과 |
|---|---|
| proxy-off F1 > 0 AND AUROC > 0.55 | FAIL — F1=0, predicted_wrong_count=0 |
| proxy-off F1 > 0 but < 0.2 | FAIL |
| proxy-off F1 = 0 AND AUROC ≈ 0.5 | **MATCH** → C3 = proxy artifact |

`threshold_free_c3_auroc`는 metrics.json output에 표시되지 않았다 (config로 등록됐지만 _build_metrics_with_blocked_markers가 미반영). 단 predicted_wrong_count=0, F_t≤0 이라는 사실만으로 ROC가 무의미함을 확인할 수 있다. 별도 follow-up: `threshold_free_c3_auroc` 계산 회로가 새 metric을 노출하도록 보강 필요.

---

## Claim 영향

- C3 (falsification precision/recall claim): **DEAD as currently formulated**
- STEP 9에서 회복으로 보고된 0.539/0.587 수치는 proxy 의존이므로 학습 신호 주장으로는 사용 불가
- 가능한 후속 처리:
  1. C3를 "휴리스틱 + model" 결합 systemic detector로 재정의 (proxy를 명시적 component로 selling)
  2. 학습된 falsification head를 **다시** 설계 (현재 F_t scorer는 no_state_change 이외 정보를 활용하지 못함)
  3. C3 claim 자체 격하 후 alternative claim으로 대체

---

## Blockers

- `threshold_free_c3_auroc` metric이 output에 노출되지 않음 → eval_runner._build_metrics_with_blocked_markers에서 별도 입출력 단계 누락 (P1 follow-up Codex task 후보).
- proxy OFF 시 학습된 falsification signal 부재 — model 재학습 또는 head 재설계 필요. STEP 11 또는 v0.5 후속.

---

## 결론

**Loop-01 verdict = REJECT.**
STEP 9 C3 회복은 학습 신호가 아니라 `no_state_change` 휴리스틱 의존이라는 명백한 negative result.
이는 paper claim에 직접적인 영향. C3 claim 재구성 또는 격하 필수.
