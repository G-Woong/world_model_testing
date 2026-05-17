# STEP 4 Handoff Document
# 20_step4_handoff.md

작성일: 2026-05-17
branch: `memory-redesign-2026-05-16`
선행: STEP 3 `P3_STEP3_DATASET_BACKFILL.passed`

---

## §1. Purpose

이 문서는 STEP 3에서 해소 불가능한 blocker들의 구현 경로를 STEP 4로 이관한다.

STEP 3 종료 시점에 아래 항목들은 여전히 BLOCKED 상태다.
이 문서는 각 blocker의 구현 방법, 예상 파일, 테스트 계획을 기술한다.

---

## §1.5. T4 Post-Audit Findings (2026-05-17)

T4 agents identified the following issues from the STEP 3 smoke run:

**C5 ECE=0.025 is a DEGENERATE PREDICTOR ARTIFACT** (area-chair + failure-interp consensus):
- F_t=0.0 for all steps (random init) → constant predictor
- ECE=0.025 ≠ calibration evidence; label as artifact in C5 evidence card
- Investigate ECE formula behavior for constant-F_t input before STEP 4

**C1 PARTIALLY_COMPUTABLE** (area-chair):
- `evidence_timestamp` (start anchor for MET-PERSIST-001) is NOT backfilled in STEP 3
- `hypothesis_update_timestamp` only gives the switch endpoint
- persistence = hypothesis_update_ts - evidence_ts is UNCOMPUTABLE until evidence_ts is backfilled
- Add `evidence_timestamp` backfill to STEP 4 B1 scope

**C3 F1=0.0 EXPECTED** (failure-interp):
- Prior run `p3_lr_real_eval_smoke` showed f1=0.583 — PRESERVE this
- STEP 3 zero is from random-init, not a negative result
- evidence card must distinguish the two runs

**Disclosure gap**: metrics.json should carry `"valid_trained_eval": false` when `hard_checks_all_pass=False`

---

## §2. STEP 3 → STEP 4 Handoff Blockers

### B0. evidence_timestamp Backfill (added from T4 finding)

**Newly identified in T4**: `evidence_timestamp` is the start anchor for MET-PERSIST-001.
Without it, `wrong_grammar_persistence = hypothesis_update_timestamp - evidence_timestamp` cannot be computed.

**Implementation**: In `collector.py::_build_evaluation_labels()` or the backfill function:
```python
# evidence_timestamp = first step where is_wrong_grammar_failure() becomes True
evidence_ts = next(
    (i for i, step in enumerate(steps)
     if step.evaluation_labels.true_wrong_hypothesis),
    None
)
```
Then backfill `evaluation_labels.evidence_timestamp = evidence_ts` for all steps in the episode.

**Tests**: `test_step4_evidence_timestamp_backfill.py` (~4 tests)

---

### B1. C4 counterfactual_action_effects Backfill

**현재 상태**: `collector.py:349` `counterfactuals=[]` 하드코딩
**필요 구현**: `src/frcgw/text_env/counterfactual_rollout.py` (신규)

#### 구현 설계

```python
# src/frcgw/text_env/counterfactual_rollout.py
def generate_counterfactuals(
    pre_state: TextState,
    actual_action: ActionRecord,
    engine: GrammarEngine,
    top_k: int = 3,
) -> list[CounterfactualRecord]:
    """For each non-selected candidate action, simulate effect under current grammar.
    
    Returns top_k CounterfactualRecords with:
    - counterfactual_effect_type: what effect this action would have had
    - counterfactual_progress_delta: progress if this action had been taken
    - counterfactual_failure_risk: P(failure) under current grammar
    - is_oracle_best: True if this is the oracle best action
    """
```

#### collector.py patch

`collector.py:349` 변경:
```python
# STEP 3: counterfactuals=[]
# STEP 4: counterfactuals=generate_counterfactuals(state, action_record, engine)
from frcgw.text_env.counterfactual_rollout import generate_counterfactuals
counterfactuals = generate_counterfactuals(state, action_record, engine)
```

#### Schema 정리 필요

`CounterfactualRecord.counterfactual_effect_type` vs paper §4의 `counterfactual_action_effects`:
- paper §4 token: `counterfactual_action_effects` (plural, list of dicts)
- schema token: `counterfactual_effect_type` (singular string per record)
- 정리 방향: `CounterfactualRecord` 유지, `counterfactual_action_effects`는 episode-level aggregate

이 schema 변경은 FRAGILE FILE (`visibility.py`) 연관 → 명시적 사용자 승인 + 테스트 재실행 필요.

#### Tests
- `tests/test_step4_counterfactual_rollout.py` (~10 tests)
- `test_counterfactual_does_not_include_oracle_label`
- `test_counterfactual_effect_type_is_public_safe`
- `test_counterfactual_rollout_is_deterministic_for_seed`
- `test_top_k_counterfactuals_does_not_exceed_candidate_count`

---

### B2. Full lr_scorer Wiring

**현재 상태**: `src/frcgw/falsification/lr_scorer.py::LikelihoodRatioFalsificationScorer` 미연결
**필요 구현**: `frcg_agent.py`에서 `HypothesisCandidate` 리스트 구성 + scorer 호출

#### 구현 설계

```python
# frcg_agent.py 내부 act() 확장
from frcgw.falsification.lr_scorer import LikelihoodRatioFalsificationScorer
from frcgw.falsification.grammar import HypothesisCandidate

scorer = LikelihoodRatioFalsificationScorer()
candidates = [
    HypothesisCandidate(grammar_id=g, log_prob=float(logits[i]))
    for i, g in enumerate(GRAMMAR_IDS)
]
lr_result = scorer.score(candidates, obs)
self._last_F_t = lr_result.F_t  # replaces plan_meta.F_t proxy
```

#### Numerical Equivalence Check

STEP 3의 `plan_meta.F_t` proxy와 STEP 4의 `lr_scorer.F_t` 간 numerical equivalence 또는
차이 정량화 → 보고서 작성.

---

### B3. Calibration Training (C5 진짜 ECE)

**현재 상태**: STEP 3에서 `selected_hypothesis_confidence`는 policy belief로부터 emit됨
**C5 preliminary**: v0.2 데이터의 ECE는 "uncalibrated policy confidence" 수준
**STEP 4 이후**: calibration head 학습 또는 temperature scaling 적용

#### 구현 설계

```python
# Option A: Temperature scaling
# src/frcgw/evaluation/calibration.py
def temperature_scale(logits: torch.Tensor, T: float) -> torch.Tensor:
    return logits / T

# Option B: Isotonic regression
# Use sklearn.isotonic.IsotonicRegression on (wrong_prob, true_wrong_hypothesis) pairs
```

Calibration 결과는 별도 artifacts에 저장:
- `outputs/calibration/temperature_T.json`
- `outputs/calibration/isotonic_regression.pkl`

---

### B4. Pre-training Checkpoint (random_init_ok=False 해소)

**현재 상태**: `configs/lr_eval_real.yaml` → `ckpt_path: null` → `random_init_ok=False` in manifest
**STEP 4 이후**: 최소 short pre-training on `data/frcgw_text/v0_2/train.jsonl`

#### 구현 설계

```bash
python scripts/07_train.py \
  --config configs/train_text_v0_2.yaml \
  --epochs 5 \
  --out-dir outputs/checkpoints/pretrain_v0_2
```

`configs/lr_eval_real_v0_2.yaml`의 `ckpt_path`를 이 checkpoint로 업데이트.
Metric interpretation은 "random-init baseline" 수준임을 명시해야 함.

---

## §3. STEP 4 실행 순서 (preview)

```
1. B2 lr_scorer wiring (dependency: STEP 3 LR wire-up verified)
2. B1 counterfactual_rollout.py + dataset v0_3 (dependency: B2)
3. B4 pre-training (dependency: v0_2 or v0_3 dataset)
4. B3 calibration (dependency: B4 checkpoint)
5. P3_STEP4.passed sentinel
```

---

## §4. Claim Wording Guidance

### C4 (STEP 3 종료 시점)

C4는 STEP 3에서 BLOCKED. 논문 draft에서:
- "counterfactual rollout evidence is deferred to STEP 4"
- C4 관련 claim은 UNKNOWN 또는 "planned" 상태 유지
- fake number 금지

### C5 (STEP 3 종료 시점)

C5 calibration ECE는 STEP 3에서 preliminary:
- "preliminary calibration evidence on v0.2 dataset; uncalibrated policy confidence"
- temperature scaling + calibration head 학습은 STEP 4+
- STEP 3에서 ECE 수치는 "기준점 측정값" 수준으로만 보고

---

## §5. Cross-references

- `docs/orchestration/lr_alignment/19_step3_dataset_backfill_plan.md` — STEP 3 계약
- `paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §4` — 33-field schema SSoT
- `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7,§8` — baseline/ablation SSoT
- `src/frcgw/schemas/step_schema.py::CounterfactualRecord` — schema (수정 시 fragile file 절차)
- `src/frcgw/schemas/visibility.py` — FORBIDDEN_AGENT_FIELDS (수정 시 fragile file 절차)

---

## §6. STEP 4 Execution Status (2026-05-17 append)

**PHASE A audit (2026-05-17)**: handoff 문서와 repo 실태 불일치 발견 후 scope 재정의.
상세 계획: `docs/orchestration/lr_alignment/21_step4_execution_plan.md`

### Scope 재정의 요약

| 구 blocker | 신 분류 | 비고 |
|---|---|---|
| B0 (original: lr_scorer wiring) | **재정의 → evidence_timestamp semantic fix** | IMPLEMENTABLE_CORE |
| B1 (original: counterfactual rollout) | **유지** | 신규 `counterfactual_rollout.py` |
| B2 (original: calibration) | **재정의 → LR comparison report only** | active path 변경 X |
| B3 (new: valid_trained_eval disclosure) | **신규** | manifest 1-field |
| B4 (new: trace writer fix) | **신규** | selected_hypothesis_id null 해소 |
| B5 (new: ECE degeneracy flag) | **신규** | C5_calibration_status |
| B6 (new: v0_3 dataset) | **신규** | B0+B1 반영 |

### PHASE A 핵심 발견

- `evidence_timestamp` = 100% coverage BUT 값이 `pre_state.step_index` (의미 오류)
- eval_runner.py:252 `_compute_episode_timestamps`는 올바른 semantic이지만 dataset-as-source flow에서 미적용
- `correct_hypothesis_id` (grammar name) vs `selected_hypothesis_id` (policy string): namespace 불일치 → STEP 5 handoff
- per_step trace: `selected_hypothesis_id` / `selected_hypothesis_confidence` 100% null
- `LikelihoodRatioFalsificationScorer` = dead code in text path; active F_t = `planning/falsification.py`
- `degenerate_f_t_count` counter bug (runner-level, STEP 5 scope)
- `C4_rollout_fidelity`, `C2_regime_split` metric 함수 미존재 → STEP 5

### Codex Tasks (STEP 4)

- TASK_1038_step4_evidence_timestamp (B0)
- TASK_1039_step4_counterfactual_rollout (B1)
- TASK_1040_step4_lr_comparison (B2)
- TASK_1041_step4_disclosure_trace_ece (B3+B4+B5)
- TASK_1042_step4_redteam_review (Task 5)

### Target Sentinel

`outputs/phase_gates/P3_STEP4_EVIDENCE_INTEGRITY.passed`
