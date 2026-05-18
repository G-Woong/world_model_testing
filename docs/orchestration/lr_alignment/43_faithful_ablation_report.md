# STEP 9 Faithful Ablation Report

date: 2026-05-18
gate: Gate O-ABL
status: CONFIG_READY_RETRAIN_PENDING

---

## 1. ABL-015 (no_control_grammar_loss)

- Config: `configs/train_text_v0_4_abl015.yaml` (STEP 8 작성)
- Checkpoint: `outputs/checkpoints/abl015_no_control_grammar_loss/checkpoint_best.pt` (EXISTS)
- Status: STEP 8에서 faithful retrain 완료
- ABL-015 vs Stage B l_control_grammar differentiation: 2.075 vs 0.055 (training-time signal confirmed)
- Eval: STEP 8 했으나 이 eval의 STEP 9 fix (tau_f=0.0, evidence proxy) 미적용 → STEP 10에서 재실행 권장

---

## 2. ABL-001 (no_regime)

- Config: `configs/train_text_v0_4_abl001.yaml` (TASK_1097, STEP 9 작성)
- Checkpoint: MISSING (retrain pending)
- Expected collapse: `regime_shift_f1` decrease + `C2_regime_split` decrease
- Status: **CONFIG_READY, RETRAIN_PENDING**

---

## 3. ABL-003 (merged_regime_control_grammar)

- Config: `configs/train_text_v0_4_abl003.yaml` (TASK_1097, STEP 9 작성)
- Checkpoint: MISSING (retrain pending)
- Expected collapse: C2 `regime_shift_f1` + C3 `falsification_f1` 동시 collapse
- Status: **CONFIG_READY, RETRAIN_PENDING**

---

## 4. Gate O-ABL Status

| 조건 | 상태 |
|---|---|
| ABL-001 faithful retrain checkpoint 존재 | ✗ PENDING |
| ABL-003 faithful retrain checkpoint 존재 | ✗ PENDING |
| ABL-015 checkpoint 존재 | ✓ |
| collapse 분석 완료 | ✗ PENDING (ABL-001/003) |

**Gate O-ABL: FAIL (CONFIG READY, RETRAIN PENDING)**
STEP 7 진행 차단 → STEP 9에서 Direct-Threat baseline 실행으로 우회.
ABL-001/003 retrain은 STEP 10 최우선 사항.
