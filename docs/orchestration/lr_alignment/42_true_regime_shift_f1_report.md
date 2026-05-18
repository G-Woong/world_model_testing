# STEP 9 C2 Label Contract Recovery Report

date: 2026-05-18
source: 41_c3_fix_evidence.md
gate: Gate O-C2
status: PARTIAL — implementation complete, data limitation identified

---

## 1. What Was Done

### Schema Change (TASK_1096 via Codex)
- `src/frcgw/schemas/step_schema.py`: `EvaluationLabels.true_regime: str | None = None` 추가
- `src/frcgw/text_env/collector.py`: `_build_evaluation_labels`에서 `true_regime=pre_state._hidden_regime` emit
- `src/frcgw/evaluation/metrics.py`: `regime_shift_f1()` 함수 신설 (MET-OOD-003 faithful)
- `src/frcgw/evaluation/eval_runner.py`: `regime_shift_f1` METRIC_FUNCTIONS에 추가
- `scripts/backfill_v0_4_true_regime.py`: v0_4 JSONL 백필 (26,226 steps 업데이트)
- `tests/test_step9_regime_shift_f1.py`: 6개 단위 테스트 (모두 PASS)

### R2 Lock 준수
- `visibility.py` 미수정 ✓
- `test_forbidden_field_mirror_sync.py` GREEN ✓
- `test_visibility_contract.py` GREEN ✓
- `true_regime`이 `public_observation`이나 inference input에 유입 없음 ✓

---

## 2. C2 regime_shift_f1 Evaluation Results

| Agent | test_id | test_ood | n |
|---|---|---|---|
| FRCG-LR | 0.0 | 0.0 | 5 seeds |
| ABL-036 | 0.0 | 0.0 | 5 seeds |
| leakage_sanity_probe | 0.0 | 0.0 | 5 seeds |

---

## 3. Root Cause: v0_4 Dataset Design

v0_4 에피소드 구조 분석:
- **test_id (200 episodes 샘플)**: regime_shift_episodes=0, no_shift=200
- **test_ood (200 episodes 샘플)**: regime_shift_episodes=0, no_shift=200
- 에피소드당 하나의 고정 regime (검색형, 드롭다운형, 모달형 등)

`regime_shift_f1`의 정의: `is_shift = len(set(step_regimes)) > 1`. 모든 에피소드가 단일 regime이므로 `is_shift=False` → shift episodes=0 → true_positives=0 → f1=0.0.

**이는 구현 버그가 아니라 데이터셋 설계 한계다.**

v0_4는 per-episode 단일 grammar/regime 설계 (P3 smoke test 목적).
실제 "regime shift" 에피소드는 v0_5+ (multi-regime within episode) 이후에 가능.

---

## 4. C2 구현 완료 vs 데이터 공백

| 항목 | 상태 |
|---|---|
| EvaluationLabels.true_regime 스키마 | ✓ 완료 |
| collector true_regime emit | ✓ 완료 |
| v0_4 JSONL true_regime 백필 | ✓ 완료 (26,226 steps) |
| regime_shift_f1 함수 | ✓ 완료 |
| METRIC_FUNCTIONS 등록 | ✓ 완료 |
| 테스트 (6개) | ✓ PASS |
| v0_4 데이터에서 의미있는 C2 값 | ✗ 데이터 없음 (intra-episode regime shift 없음) |

---

## 5. Gate O-C2 Status

| 조건 | 상태 |
|---|---|
| regime_shift_f1 양수 + PROXY 아님 | ✗ 0.0 (데이터 한계) |
| OOD 100 episodes에서 계산 가능 | ✗ OOD에도 shift 없음 |
| leakage_count = 0 유지 | ✓ |

**Gate O-C2: FAIL** — 구현은 완료되었으나 v0_4 데이터에서 의미있는 값 없음.

**대안**: 다음 phase에서 C2 측정을 위한 multi-regime episode 데이터셋 필요.

---

## 6. C1 Persistence Status

`correct_hypothesis_id`는 이미 v0_4 evaluation_labels에 있음 (STEP 8 확인).
그러나 `hypothesis_update_timestamp` coverage = 0 → C1 BLOCKED.

collector에서 `_backfill_episode_timestamps`가 hypothesis_update_timestamp를 채우는 로직 존재:
```python
if was_wrong and tw is False and hypothesis_update_timestamp is None:
    hypothesis_update_timestamp = idx
```
이는 `true_wrong_hypothesis` transition(True→False)을 기반으로 하는데, v0_4에서 이 transition이 충분히 발생하는지 확인 필요.

**다음**: C1 persistence 계산 가능 여부 audit → `evidence_timestamp_coverage` 확인.

---

## 7. Next Actions

1. v0_5 dataset에서 multi-regime episodes 포함하여 C2 의미있는 값 측정 가능
2. C1 persistence: hypothesis_update_timestamp coverage audit 실행
3. STEP 7 Direct-Threat Baselines: BASE-026/027 faithful eval 실행 예정
