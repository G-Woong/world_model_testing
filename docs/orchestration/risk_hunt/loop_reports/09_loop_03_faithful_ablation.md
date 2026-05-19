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

## Launcher 패치 (2026-05-19)

원본 `run_abl001_retrain.py` / `run_abl003_retrain.py`는 `02_train_text_smoke.py`에 `--output-dir`을 넘기지 않아 default `outputs/runs/p3_smoke`로 덮어쓰여졌고, `train_text.py`가 `checkpoint_best.pt`를 만들지 않기 때문에 eval config 경로와 불일치했다.

STEP C 분류 A(path/config/checkpoint 누락)에 해당 — 최소 수정 허용:
- launcher에 `--output-dir outputs/runs/p3_train_v0_4_abl00X` 명시
- 학습 후 `checkpoint_ep*.pt` 마지막 파일을 `outputs/checkpoints/abl00X_*/checkpoint_best.pt`로 promote
- eval은 `--out-dir outputs/risk_hunt/experiments/loop03_abl00X_retrain` 명시

원본 train config의 `warm_start_checkpoint`는 train_text.py 코드에서 미사용 cosmetic 필드이므로 stageA 부재가 학습을 막지 않음을 확인. 학습은 from-scratch에서 1 epoch (2000 steps batch_size=8)로 진행.

---

## Eval 실행 결과 (2026-05-19)

- 명령: `.venv/Scripts/python.exe scripts/risk_hunt/run_abl001_retrain.py` 및 `run_abl003_retrain.py`
- 데이터: test_id+test_ood split 자동 reroute로 인해 reference C6 측정도 100 episodes에서 갱신됨
- 산출물:
  - `outputs/checkpoints/abl001_no_regime/checkpoint_best.pt` (promoted)
  - `outputs/checkpoints/abl003_merged_regime_grammar/checkpoint_best.pt` (promoted)
  - `outputs/risk_hunt/experiments/loop03_abl001_retrain/metrics.json`
  - `outputs/risk_hunt/experiments/loop03_abl003_retrain/metrics.json`

---

## 핵심 결과 표

| Variant | C3 F1 | C3 Prec | C3 Rec | C6 PPC (self-report) | C2 regime_split |
|---|---|---|---|---|---|
| FRCG-LR reference (full loss) | **0.5391** | 0.4669 | 0.6377 | 0.2160 | **0.0** |
| ABL-001 no-regime (l_regime=0) | **0.5575** | 0.4953 | 0.6377 | 0.2160 | **0.0** |
| ABL-003 merged regime/grammar | **0.5391** | 0.4669 | 0.6377 | 0.2160 | **0.0** |

(ABL-003은 reference와 정확히 일치 — 동일 episodes의 동일 outputs 추정)

---

## 해석

1. **regime_shift_f1 (C2) 양쪽 모두 0.0**. ABL-001/003만 collapse한 게 아니라 **reference도 동일하게 0**. 즉 reference 자체가 regime separability를 학습하지 못함. ablation으로 시그널 차이를 만드는 게 불가능.
2. **C3 F1**: ABL-001(0.558) ≥ reference(0.539). l_regime을 빼도 C3가 동등 또는 약간 더 좋음. "regime latent이 C3에 기여한다"는 가설 falsified.
3. **ABL-003 = reference 수치 일치**: merged 구조 학습 1 epoch이 reference와 식별 불가능한 결과를 냄. 두 가지 가능성: (a) eval-only forward pass에서 차이를 만들지 못함, (b) 학습 시간이 너무 짧아 reference도 같은 stuck point에 있음.
4. **C6 PPC 모두 동일 (0.2160)**: planning gate 동작이 차이 없음. ABL이 의미 있는 baseline 차이를 만들지 못함.
5. Loop-01에서 확인된 proxy 의존이 그대로 모든 variant에 영향 — C3 F1의 변화는 모두 proxy 휴리스틱 동작 차이일 뿐.

---

## Decision Gate

**판정: REJECT**

| 조건 | 결과 |
|---|---|
| ABL-001 C2 collapse + C3 유지 | FAIL — reference도 C2=0, 즉 baseline contrast 자체가 없음 |
| ABL-003 C2+C3 동시 collapse | FAIL — 수치 reference와 동일 |
| no collapse (C3 유지 under ABL-001) | **MATCH** — regime loss는 C3에 기여하지 않음 |

separability claim의 근거가 무너졌다. 단 **caveat**: reference 자체가 학습이 충분하지 않아 C2=0인 상태이므로, 이는 "regime latent이 의미 없다"보다는 "현재 학습 setup에서 regime separability가 일어나지 않는다"는 더 약한 결론으로 해석되어야 한다.

---

## Claim 영향

- separability claim ("FRCG-WM이 regime과 control grammar를 분리 학습한다") **현재 학습 setup에서는 falsified**
- v0.5 데이터/loss/learning rate 조정으로 regime separability를 확보하기 전에는 이 claim 사용 불가
- ABL-001/003 결과는 paper에서 negative evidence로만 보고 가능

---

## Blockers / Follow-up

- **identifiability ABL-003 = reference**: 학습 길이가 너무 짧다 (1 epoch). full retrain (10 epochs) 후 재검증 권장. 단 이게 reference와 차이를 낼 가능성도 낮음 (proxy artifact가 지배).
- **stage A checkpoint 부재**: warm_start_checkpoint가 미사용 cosmetic이므로 학습에는 영향 없지만, training config의 의도와 어긋남. v0.5에서 stage A → stage B 파이프라인을 실제로 굳혀야 함.
- **threshold_free_c3_auroc 미노출**: Loop-01과 동일 issue.

---

## 결론

**Loop-03 verdict = REJECT (with caveat).**
ABL-001/003이 reference와 의미 있는 차이를 만들지 못한다. 그 이유가 (a) regime latent이 의미 없음 또는 (b) reference 자체가 regime을 학습하지 못함인지는 v0.5 후속에서 구분되어야 한다. 어쨌든 현 시점에서 separability claim은 paper claim으로 사용 불가능.
