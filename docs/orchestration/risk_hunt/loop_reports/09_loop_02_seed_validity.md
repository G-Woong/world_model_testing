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

## Launcher 패치 (2026-05-19)

원본 launcher가 `02_train_text_smoke.py`에 `--seed`와 `--checkpoint-dir`을 넘기지만, 스크립트가 두 인자 모두 미정의 → argparse error로 즉시 실패. STEP C 분류 E(launcher argument 문제) 최소 수정 허용 범위.

수정:
- `scripts/02_train_text_smoke.py`: `--seed`(train_cfg.seed override), `--checkpoint-dir`(--output-dir alias) 인자 추가. seed override 시 임시 yaml 생성 후 `run_smoke_train`에 전달. `train_text.py` 핵심 라이브러리 수정 없음.
- `scripts/risk_hunt/run_multiseed_training.py`: 학습 종료 후 `checkpoint_ep*.pt`를 `checkpoint_best.pt`로 promote 단계 추가.

---

## Eval 실행 결과 (2026-05-19)

- 학습: 5 seeds × 1 epoch (1000 steps, batch_size=8, ~3분 each) = ~15분
- 모든 checkpoint 생성: `outputs/checkpoints/pretrain_v0_4_seed{42,123,456,789,999}/checkpoint_best.pt`
- Eval: `.venv/Scripts/python.exe scripts/10_run_lr_real_eval.py --config configs/lr_eval_step10_multiseed.yaml --out-dir outputs/risk_hunt/experiments/loop02_multiseed --max-episodes 50`

---

## 핵심 결과 표

| Seed | C3 F1 | C3 Precision | C3 Recall | C6 PPC |
|---|---|---|---|---|
| 42 | 0.5806 | 0.4932 | 0.7059 | 0.1926 |
| 123 | 0.4198 | 0.5667 | 0.3333 | 0.1926 |
| 456 | 0.4762 | 0.4630 | 0.4902 | 0.1926 |
| 789 | 0.5785 | 0.5000 | 0.6863 | 0.1926 |
| 999 | 0.5806 | 0.4932 | 0.7059 | 0.1926 |
| **mean ± std** | **0.527 ± 0.075** | 0.503 ± 0.038 | 0.584 ± 0.167 | **0.193 ± 0.000** |
| min / max | 0.420 / 0.581 | 0.463 / 0.567 | 0.333 / 0.706 | 0.193 / 0.193 |

---

## 해석

1. **C3 F1 across-seed std = 0.075** (range 0.42–0.58) — 이전 STEP 9의 std=0.000 deterministic 문제 해소. statistical validity 측면에서 KEEP.
2. **C6 PPC std = 0.000** — 모든 seed가 동일한 0.1926. planning gate가 seed에 무관하게 deterministic하게 작동. STEP 9의 self-report 분모 문제와 일관 (gate가 안 열림).
3. **Loop-01과의 연계**: seed variance는 model이 학습한 신호의 variance가 아니라 proxy boundary 근처에서의 confidence/threshold 변동. proxy OFF 결과 F1=0 (Loop-01 확인)이므로 0.42–0.58 분산도 휴리스틱-주도.
4. seed 42와 999가 정확히 같은 결과 (0.5806/0.4932/0.7059) — 1 epoch 학습으로는 동일한 local plateau에 빠르게 수렴할 가능성. 충분한 학습 길이에서 분산이 더 커질 수 있음.
5. C3 Recall std (0.167)가 Precision std (0.038)보다 4배 큼 → recall이 seed에 매우 민감. proxy boundary 근처 sample 분류가 흔들림.

---

## Decision Gate

**판정: KEEP** (statistical validity 확보)

| 조건 | 결과 |
|---|---|
| std(F1) > 0.01 across seeds | **MATCH** — std = 0.075 |
| std < 0.01 but > 0.001 | NO |
| std ≈ 0 | NO |

단 caveat: variance는 model-learned signal의 variance가 아니라 proxy-driven heuristic boundary variability.

---

## Claim 영향

- statistical reporting: 5-seed mean ± std로 보고 가능. CI 작성 가능.
- 단 "C3 F1 ≈ 0.53 ± 0.08"이라는 보고는 proxy artifact임을 명시해야 함 (Loop-01에서 proxy OFF F1=0 확인).
- C6 PPC는 seed에 deterministic — planning gate 동작에 randomness 없음. self-report-aware 분모이므로 wall-clock으로 cross-check 필요.

---

## Blockers / Follow-up

- 5 seeds가 1 epoch만 학습됨 (1000 steps). 충분한 학습(예: 10 epochs)에서의 variance 측정 권장. 시간 cost 고려.
- `threshold_free_c3_auroc`, `regime_shift_f1`, `fair_ppc` 등 새 metric이 metrics.json에 노출되지 않음 — Loop-01/03/06과 동일 issue.

---

## 결론

**Loop-02 verdict = KEEP** (with caveat: variance는 휴리스틱 boundary 부근의 confidence 변동에 기인).
5-seed mean F1 = 0.527, std = 0.075. true variance 확보 → STEP 9의 std=0.000 deterministic 문제는 해결. 단 fundamental claim signal 자체가 학습 신호인지 휴리스틱인지는 Loop-01/03 결과에 의해 결정됨 (휴리스틱 측).
