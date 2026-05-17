# STEP 3 Dataset Label Backfill Plan
# 19_step3_dataset_backfill_plan.md

작성일: 2026-05-17
branch: `memory-redesign-2026-05-16` @ `1c6d511`
선행: STEP 2 `P3_LR_REAL_EVAL.passed` (66 BLOCKED markers, fake_metric_count=0)

---

## §1. Purpose

이 계약서는 STEP 3의 **Dataset v0.2 Label Backfill + LR Wire-up** 구현 계약을 정의한다.

STEP 2 real eval runner는 `test_id.jsonl`을 직접 순회하지만 6개 metric이 모두
BLOCKED 상태다. STEP 3은 이 BLOCKED 상태의 근본 원인을 제거하여
C1/C3/C5 metric을 COMPUTABLE 상태로 전환한다.

C4 counterfactual 및 full lr_scorer wiring은 STEP 4로 명확히 이관한다.

---

## §2. Root Cause Analysis

| ID | 파일 | 위치 | 근본 원인 |
|---|---|---|---|
| RC-1 | `src/frcgw/text_env/collector.py` | L220-226 | `hypothesis_update_timestamp`, `recovery_timestamp`, `h_exec_id`, `ood_type` 모두 None 하드코딩 |
| RC-2 | `data/frcgw_text/v0_1/` | jsonl rows | `action.selected_hypothesis_id` / `action.selected_hypothesis_confidence` 필드 key 자체 없음 (v0_1 생성 이전 schema) |
| RC-3 | `src/frcgw/text_env/collector.py` | L349 | `counterfactuals=[]` 하드코딩; C4 rollout 로직 미구현 |
| RC-4 | dataset | — | `test_ood.jsonl` 파일 부재; OOD spec generator path 없음 |
| RC-5 | `src/frcgw/evaluation/frcg_agent.py` | L95-96 | `predicted_wrong = (max P(grammar) < confidence_threshold)` — confidence proxy; `last_F_t`를 `plan_meta.F_t`로 설정하지만 `predicted_wrong`이 이를 사용하지 않음 |
| RC-6 | `scripts/10_run_lr_real_eval.py` | L304 | `"tau_f": None` 하드코딩 |

---

## §3. STEP 3 Unblock 대상

| Metric | Claim | RC 제거 | 예상 결과 | 주의 |
|---|---|---|---|---|
| `wrong_grammar_persistence` | C1 | RC-1 (`hypothesis_update_timestamp`) | PARTIALLY_COMPUTABLE | switch endpoint only; start anchor (evidence_timestamp) + correct_hypothesis_id 미완성 → "infrastructure" wording만 허용 |
| `recovery_delay` | C3 | RC-1 (`recovery_timestamp`) | BLOCKED → COMPUTABLE | BASE-006/CATTS 비교 없음 → pass condition 미달 |
| `falsification_calibration` (ECE) | **C3** (NOT C5) | RC-2 (`selected_hypothesis_confidence`) | BLOCKED → COMPUTABLE (preliminary, uncalibrated) | ECE는 MET-CAL-001 → CLAIM-EVAL-003(C3) 소속; C5는 action-interface rewrite |
| `falsification_precision_recall` (F1) | C3 | RC-5 + RC-6 (F_t > tau_f) | BLOCKED → COMPUTABLE | BASE-006 비교 여전히 없음 → C3 pass condition 미달 |
| C4 WM metric | C4 | RC-3 (counterfactuals) | → STEP 4 handoff | — |
| OOD generalization | — | RC-4 (`test_ood.jsonl`) | partial: `ood_type` tag added | — |
| C5 (action-interface rewrite) | C5 | — | NOT a STEP 3 target | ABL-017 역방향 결과 미해소; MET-REWRITE-001 = STEP 5+ |

> **Claim wording 제한**: STEP 3 종료 후 C1/C3/C5에 대해 "proven" / "demonstrated" 사용 금지.
> 허용: "infrastructure populated", "metric now computable", "preliminary evidence"

---

## §4. Scope

### In Scope (STEP 3)
1. **Dataset v0.2 regeneration** — `data/frcgw_text/v0_2/{train,valid,test_id,test_ood}.jsonl` + `manifest.json` + `audits/`
2. **Collector label backfill** — `src/frcgw/text_env/collector.py` L220-226 + L349 인근:
   - `hypothesis_update_timestamp` ← first step where `valid_hypothesis_switch=True`
   - `recovery_timestamp` ← first step where action_type == recovery_action_id AND progress_delta>0 AND prior step had true_wrong_hypothesis=True
   - `ood_type` ← spec.ood_type (id split이면 None, ood split이면 "grammar_shift")
3. **TextEpisodeSpec.ood_type field** — `src/frcgw/text_env/state.py` (ood_type: str | None = None 추가)
4. **OOD spec generator** — held-out grammar family로 `test_ood.jsonl` 생성; `configs/dataset_v0_2.yaml` ood section
5. **LR wire-up (1-line + tau_f propagation)** — `frcg_agent.py:95-96` + `10_run_lr_real_eval.py:304`
6. **Coverage audit script** — `scripts/audit_step3_dataset_coverage.py`
7. **Tests** — 31개 신규 (Tasks 1+2+3)
8. **계약 문서** — 이 파일 + `20_step4_handoff.md`

### Out of Scope (STEP 4 이관)
- `counterfactuals=[]` non-empty (collector.py L349)
- `counterfactual_action_effects` field wiring
- `src/frcgw/falsification/lr_scorer.py` full wiring
- `eval_runner.py`, `metrics.py` 수정
- `src/frcgw/schemas/visibility.py` (fragile)
- `paper_context_ref/**` (fragile)

---

## §5. Backfill Design

### §5.1 collector.py 패치

`collect_episode()` 함수 끝에 episode-level post-pass 추가:

```python
def _backfill_episode_timestamps(
    steps: list[StepRecord],
    ood_type: str | None,
) -> list[StepRecord]:
    """Episode-level post-pass: backfill hypothesis_update_timestamp + recovery_timestamp + ood_type."""
    import dataclasses

    # hypothesis_update_timestamp: first step where valid_hypothesis_switch=True
    hyp_update_ts = None
    for i, step in enumerate(steps):
        if step.training_labels.valid_hypothesis_switch:
            hyp_update_ts = i
            break

    # recovery_timestamp: first step where action_type == recovery_action_id
    # AND progress_delta > 0 AND prior step had true_wrong_hypothesis=True
    recovery_ts = None
    for i, step in enumerate(steps):
        if i == 0:
            continue
        prior_wrong = steps[i - 1].evaluation_labels.true_wrong_hypothesis
        tl = step.training_labels
        if (
            prior_wrong
            and step.action.action_type == tl.recovery_action_id
            and tl.progress_delta > 0
        ):
            recovery_ts = i
            break

    patched = []
    for step in steps:
        new_eval = dataclasses.replace(
            step.evaluation_labels,
            hypothesis_update_timestamp=hyp_update_ts,
            recovery_timestamp=recovery_ts,
            ood_type=ood_type,
        )
        patched.append(dataclasses.replace(step, evaluation_labels=new_eval))
    return patched
```

Call site 추가 (`collect_episode` return 직전, episode validation 이전):
```python
steps = _backfill_episode_timestamps(steps, getattr(spec, 'ood_type', None))
```

단, episode-level `validate_visibility_contract(episode)` 호출 전에 수행하여
backfill된 값이 visibility 검증을 통과하도록 한다.

### §5.2 TextEpisodeSpec.ood_type field

`src/frcgw/text_env/state.py`의 `TextEpisodeSpec`에 필드 추가:
```python
ood_type: str | None = None  # None for id split, "grammar_shift" for ood split
```

### §5.3 OOD Spec Generator (Codex Task 2)

`configs/dataset_v0_2.yaml`에 `ood_grammar_families: ["filter_accordion", "nested_scroll"]` 추가.

이 2개 family는 `test_ood.jsonl`에만 사용 (train/valid/test_id에서 제외).
`test_ood.jsonl` 생성 시 `spec.ood_type = "grammar_shift"` 설정.

`EpisodeSpecGenerator`는 `ood_grammar_families`를 파라미터로 받아
OOD 전용 spec을 생성하는 `generate_ood()` 메서드 추가.

### §5.4 Leakage 방지

- `ood_type`은 `EvaluationLabels`에만 저장; `PublicObservation`에 lift 금지
- `hypothesis_update_timestamp`, `recovery_timestamp`도 `EvaluationLabels`에만
- `validate_visibility_contract()` 기존 로직으로 강제됨
- 신규 테스트 `test_step3_no_label_leakage.py`에서 명시 검증

---

## §6. C1/C3 Label Dependency Table (C5 rewrite는 STEP 5+ 대상)

| Metric | Claim | Required Label | Dataset Field | STEP 3 Action | 주의 |
|---|---|---|---|---|---|
| `wrong_grammar_persistence` | C1 | hypothesis_update_timestamp | `eval_labels.hypothesis_update_timestamp` | collector backfill | switch endpoint만; start anchor(evidence_timestamp) 미완성 → PARTIALLY_COMPUTABLE |
| `recovery_delay` | C3 | recovery_timestamp | `eval_labels.recovery_timestamp` | collector backfill | — |
| `falsification_precision_recall` | C3 | predicted_wrong, true_wrong_hypothesis | `predicted_wrong` (agent) + `eval_labels.true_wrong_hypothesis` | LR wire-up (frcg_agent.py) | — |
| `falsification_calibration` (ECE) | **C3** (MET-CAL-001) | selected_hypothesis_confidence, true_wrong_hypothesis | `action.selected_hypothesis_confidence` | v0_2 regeneration | ECE → C3 (NOT C5). C5 = action-interface rewrite |
| C4 WM metrics | C4 | counterfactual_action_effects | `counterfactuals` | STEP 4 handoff | — |
| C5 action-interface rewrite | C5 | rewrite_success, ABL-017 comparison | — | NOT a STEP 3 target | ABL-017 역방향 결과 미해소 |

---

## §7. LR Wire-up Design

### §7.1 frcg_agent.py:95-107 패치

기존:
```python
self._last_wrong_prob = 1.0 - max_grammar_prob
self._last_predicted_wrong = max_grammar_prob < self._confidence_threshold
action, plan_meta = text_frcg_plan(...)
self._last_F_t = float(plan_meta.F_t)
```

후 (plan_meta.F_t lift 후 predicted_wrong 결정):
```python
action, plan_meta = text_frcg_plan(...)
self._last_F_t = float(plan_meta.F_t)
tau_f = float(self.gate_config.tau_f)
self._last_tau_f = tau_f
self._last_predicted_wrong = self._last_F_t > tau_f
self._last_wrong_prob = float(_sigmoid(self._last_F_t - tau_f))
```

`_sigmoid` 헬퍼 (overflow clamp ±50):
```python
import math
def _sigmoid(x: float) -> float:
    x = max(-50.0, min(50.0, x))
    return 1.0 / (1.0 + math.exp(-x))
```

### §7.2 10_run_lr_real_eval.py:304 패치

`_TracingAgent.act()` 내부에서 `getattr(self._agent, "_last_tau_f", None)`을 trace에 lift:
```python
trace["tau_f"] = getattr(self._agent, "_last_tau_f", None)
```

`_attach_trace_records` line 304:
```python
"tau_f": record.get("tau_f"),
```

---

## §8. Test Plan Summary

| Task | Tests | Count |
|---|---|---|
| Task 1 (Coverage audit) | test_step3_dataset_coverage_audit.py | 5 |
| Task 2 (Dataset backfill) | test_step3_dataset_backfill.py | 12 |
| Task 2 (Leakage) | test_step3_no_label_leakage.py | 5 |
| Task 2 (OOD split) | test_step3_ood_split.py | 3 |
| Task 3 (LR wire-up) | test_step3_lr_trace_contract.py | 6 |
| Regression | test_lr_real_eval_runner.py | 14 (no change required) |
| **Total new** | — | **31** |

---

## §9. Gate Criteria

### Smoke Gate (PHASE F)
- [ ] before/after coverage audit JSON 존재
- [ ] after report에서 ≥3개 필드 coverage 0→>0
  - `hypothesis_update_timestamp`, `selected_hypothesis_confidence`, `ood_type` or `recovery_timestamp`
- [ ] targeted pytest green (31 신규 + ≥14 회귀)
- [ ] smoke run exit 0
- [ ] manifest `forbidden_source_assertion == "none_read"`
- [ ] manifest `source_artifacts_used == ["data/frcgw_text/v0_2/test_id.jsonl"]`
- [ ] metrics `fake_metric_count == 0`
- [ ] 모든 BLOCKED metric `value is None`
- [ ] `predicted_wrong` 분포가 placeholder saturate(all true)와 다름
- [ ] `tau_f` non-null in per_step

### Sentinel Gate (I7)
- [ ] `outputs/phase_gates/P3_STEP3_DATASET_BACKFILL.passed` 생성
- [ ] `plans/PHASE_PROGRESS.md`에 row 추가

---

## §10. Dataset v0.2 Configuration

`configs/dataset_v0_2.yaml`:
- `dataset_version: "0.2"`
- `num_episodes: 200` (ID split) + 50 OOD episodes
- id grammar families: search_form, required_dropdown, modal_blocker, pagination_vs_infinite, loading_delayed, permission_gate (6개)
- ood grammar families: filter_accordion, nested_scroll (2개)
- Splits: train 0.70, valid 0.15, test_id 0.15 (ID only); test_ood separate
- `output_dir: data/frcgw_text/v0_2`

---

## §11. Hidden Label Leakage Rules

### 절대 금지 (leakage 즉시 중단)
1. `ood_type`이 `PublicObservation.instruction`에 포함되는 것
2. `hypothesis_update_timestamp`가 `history_public`에 포함되는 것
3. `recovery_timestamp`가 candidate action params에 포함되는 것
4. `true_wrong_hypothesis`가 `PublicObservation` 어디에도 나타나는 것

### 검증 메커니즘
- `validate_visibility_contract(episode)` — 기존 강제 (collector.py L398-400)
- `tests/test_step3_no_label_leakage.py` — 5개 명시 검증
- `tests/test_forbidden_field_mirror_sync.py` — sync 보장

### EvaluationLabels 한정 필드
다음 필드는 `EvaluationLabels`에만 존재하며 다른 어떤 스키마 클래스에도 복사되지 않는다:
- `hypothesis_update_timestamp`
- `recovery_timestamp`
- `ood_type`
- `true_wrong_hypothesis`
- `correct_hypothesis_id`

---

## §12. Risks

| Risk | Mitigation |
|---|---|
| OOD spec generator 복잡성 | PHASE F Gate: `ood_type` 또는 `recovery_timestamp` 중 하나 충족이면 PASS |
| v0_1 collector 패치 회귀 | `test_original_v0_1_dataset_not_overwritten` 강제; v0_1 unmodified |
| LR wire-up 회귀 | PHASE F 전체 pytest 회귀 |
| wrong_prob saturation | `_sigmoid` ±50 clamp |
| counterfactual BLOCKED 영구화 | STEP 4 handoff 문서화 + 일정 |
| C5 ECE 비신뢰 | "preliminary calibration evidence; STEP 5+에서 calibration training" 명시 |

---

## §13. Pre-existing Dirty Files (수정 금지)

STEP 3 전체에서 다음 5개 파일은 수정 금지:
- `.gitignore`
- `.self_evolving_memory/hooks/hook_execution_log.md`
- `docs/orchestration/AGENT_TEAMS_ROLLOUT_PLAN.md`
- `docs/orchestration/session_reports/2026-05/2026-05-17_precompact_handoff.md`
- `plans/PHASE_PROGRESS.md`

---

## §17. STEP 4 Handoff Blockers

다음 항목은 STEP 3에서 해소 불가능한 구조적 blocker로서 STEP 4로 이관:

| Blocker | 근거 |
|---|---|
| `counterfactuals=[]` non-empty | collector.py L349; `src/frcgw/text_env/counterfactual_rollout.py` 신규 구현 필요 |
| `CounterfactualRecord.counterfactual_effect_type` paper token 불일치 | paper §4와 schema 명칭 정리 필요 |
| `falsification/lr_scorer.py` full wiring | `LikelihoodRatioFalsificationScorer` signature + evidence pipeline 변경 |
| calibration head 학습 | C5 ECE는 preliminary only; temperature scaling은 STEP 5 |
| `random_init_ok=False` | pre-training checkpoint 필요 |

상세: `docs/orchestration/lr_alignment/20_step4_handoff.md`
