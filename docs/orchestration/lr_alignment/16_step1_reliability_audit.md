# 16_step1_reliability_audit.md — STEP 1: Run 6 신뢰성 감사

**작성일**: 2026-05-17  
**Phase**: CC-P3 (pilot/core eval scope)  
**근거**: 코드 직접 trace + `outputs/runs/p3_lr_eval/metrics.json` + `ablation_results.json`  
**범위**: Read-only 코드 감사. 어떤 코드/데이터도 변경하지 않음.

---

## §1. 핵심 판정 요약

> **Run 6 (`scripts/09_run_lr_eval.py`)는 full eval이 아닌 preflight aggregator이다.**

- `metrics.json.run_mode = "preflight_from_smoke"` (line 2)
- `manifest.json.run_mode = "full_eval_preflight_metrics"` (line 2)
- `manifest.json.scope_note = "pilot/core eval scope — NOT paper-accept-level evidence"` (line 19)

어떤 metric도 "논문 accept-level evidence"로 인용할 수 없다.

---

## §2. `scripts/09_run_lr_eval.py` 코드 감사

### §2.1 Preflight 경로 (실제 실행됨)

```python
# line 64-197: _build_consolidated_metrics()
def _build_consolidated_metrics(smoke, ablation_results, config):
    """Build consolidated metrics from smoke runs and ablation results.
    Called when data manifest is missing (preflight mode).
    References outputs from prior runs; does NOT fabricate values.
    """
```

이 함수는:
- `outputs/runs/p3_lr_smoke/metrics.json` (smoke)에서 C1 수치 읽기
- `outputs/runs/p3_ablations/ablation_results.json` (ablation_results)에서 C3/C5/C6 계산
- `EvaluationRunner.run()` **미호출** — 어떤 episode도 실제 실행 안 함

### §2.2 Full data path (현재 no-op)

```python
# line 264-278: Full data path
manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
split = config.get("split", "text_ood_grammar")
shard_path = _find_shard(manifest_data, split)
if shard_path is None:
    print(f"[SKIP] no shard for split={split}")
    return 0

print(f"[INFO] Full eval mode: shard={shard_path}")
# Full eval would run agents here; currently preflight-only
# (agent integration is Phase 5+)
metrics = _build_consolidated_metrics(smoke, ablation_results, config)  # ← 또 aggregator 호출
```

코드 comment: `"currently preflight-only (agent integration is Phase 5+)"` (line 273-274)

→ **Full data path도 내부에서 동일한 aggregator를 호출한다. no-op.**

### §2.3 Split alias — OOD eval 없음

```python
# line 305-313: _find_shard()
def _find_shard(manifest: dict, split: str) -> str | None:
    _ALIAS = {"text_id": "test_id", "text_ood_grammar": "test_id", "text_noisy": "test_id"}
```

`text_ood_grammar`, `text_noisy`가 모두 `test_id`로 alias됨.
→ **OOD split은 실제로 존재하지 않고 test_id에 collapse.**  
→ OOD 성능 주장 불가.

### §2.4 Hidden Leakage Guard — 미호출

`eval_runner.py:100-103`:
```python
assert_no_hidden_labels_in_input(
    public_obs,
    context=f"...",
)
```

이 guard는 `EvaluationRunner.run()` 내부에서만 호출된다.  
`09_run_lr_eval.py`는 `EvaluationRunner.run()`을 호출하지 않으므로 **guard 미실행**.

`metrics.json.hidden_leakage_count = 0`은 smoke passthrough 값 (`smoke.get("hidden_leakage_count", 0)`, line 82).  
→ **실제 leakage 검사 미수행.**

---

## §3. Metric Source Trace

### C1 metrics

| Metric | 값 | 출처 파일 | 출처 라인 | 신뢰도 |
|---|---|---|---|---|
| `planning_calls` | 1 | `p3_lr_smoke/metrics.json` | `smoke.get("planning_calls", 0)` (line 77) | Low — N=1, statistical power 없음 |
| `h_exec_null_rate` | 0.0 | `p3_lr_smoke/metrics.json` | `smoke.get("selected_hypothesis_id_null_rate", None)` (line 78) | Medium — smoke에서 측정, 하지만 h_exec = policy constant proxy |
| `MET_PERSIST_001_status` | `"BLOCKED_no_eval_labels"` | hardcoded in line 155 | N/A | N/A — 측정 불가 상태 |
| `repeated_invalid_mapping_rate` | 0.500 | `ablation_results.json` (FRCG-FULL) | `_mean_metric(frcg_full, "failed_action_repetition_rate")` line 112 | **Low** — deterministic mock (inter-seed variance=0) |
| `recovery_delay` | 2.545 | `ablation_results.json` (FRCG-FULL) | `_mean_metric(frcg_full, "recovery_delay")` line 157 | **Low** — deterministic mock |

### C3 metrics

| Metric | 값 | 출처 파일 | 출처 라인 | 신뢰도 |
|---|---|---|---|---|
| `FRCG_FULL_fals_f1` | 0.4032 | `ablation_results.json` (FRCG-FULL, 5 seeds avg) | `_mean_nested(frcg_full, "falsification_precision_recall", "f1")` line 92 | **Low** — deterministic mock, real model inference 아님 |
| `ABL_022_fals_f1` | 0.0 | `ablation_results.json` (no_falsification_score_gate) | line 93 | **Medium** — 방향 올바름 (gate 제거 → F=0 정상) |
| `ABL_023_fals_f1` | 0.0 | `ablation_results.json` (uncertainty_instead) | line 94 | **Medium** — 방향 올바름 |
| `LR_vs_gate_removal_delta_f1` | +0.4032 | 계산값 | line 100-104 | **Low-Medium** — delta 방향 신뢰, 크기는 mock |
| `F_t_variance` | 1.26 | `p3_lr_smoke/metrics.json` | line 79 | **Medium** — smoke 실제 측정 |
| `F_t_degenerate_rate` | 0.20 | `p3_lr_smoke/metrics.json` | `degenerate_count=5/25` (line 84-85) | **Medium** — 측정됨, 원인 미파악 (ISS-001) |
| `MET_FALS_001_falsification_precision` | 0.338 | `ablation_results.json` | line 96 | **Low** — proxy |
| `MET_FALS_002_falsification_recall` | 0.500 | `ablation_results.json` | line 97 | **Low** — proxy |

### C5 metrics

| Metric | 값 | 출처 | 신뢰도 |
|---|---|---|---|
| `rewrite_success_rate_proxy` | 0.500 | `1.0 - failed_rep` (line 172-174) | **Low** — proxy 명시됨, ABL-017 방향 반전으로 proxy 신뢰도 더 낮음 |
| `action_switch_delay` | 0.0 | `ablation_results.json` FRCG-FULL | **Low** — 차별화 없음 |
| `no_intent_action_mapping_delta_failed_rep` | **-0.4107** | `abl017_failed_rep - frcg_failed_rep` (line 115-118) | **Medium** — 측정 정확, 하지만 방향이 예상 반대 (counter-evidence) |

### C4 / C6 metrics

| Metric | 값 | 신뢰도 |
|---|---|---|
| `MET_WM_001_rollout_fidelity` | `"BLOCKED_no_rollout_log"` | N/A |
| `rollout_steps` | 0 | Confirmed blocked |
| `progress_per_compute` (FRCG-FULL) | 0.2285 | **Low** — deterministic mock |
| `compute_matched_delta_ppc` | `null` | N/A — BASE-015 미실행 |
| `false_planning_call_rate` | 0.0 | Low — N=1 planning call |

---

## §4. Dataset Coverage 분석

### §4.1 Dataset 규모

| 항목 | 값 | 출처 |
|---|---|---|
| 전체 episode 수 | 200 | `data/frcgw_text/v0_1/manifest.json` |
| test_id shard 수 | 33 | `data/frcgw_text/v0_1/test_id.jsonl` |
| episode당 step 수 | 3 | manifest splits 명세 |
| 총 step 수 | 99 | 33 × 3 |

→ **N=33 episodes. 논문 기준 최소 N 미확인. Statistical power 부족.**

### §4.2 필수 필드 존재 여부

`test_id.jsonl` first row 검증 결과:

| 필드 | 존재 여부 | 영향 |
|---|---|---|
| `predicted_wrong` | **ABSENT** | C3 real falsification 측정 불가 |
| `wrong_prob` | **ABSENT** | calibration ECE 실제 측정 불가 |
| `selected_hypothesis_id` | **ABSENT** | h_exec 실제 측정 불가 |
| `evidence_timestamp` | **ABSENT** | MET-PERSIST-001 측정 불가 |
| `correct_hypothesis_id` | **ABSENT** | persistence label 없음 |
| `public_observation` | ✅ PRESENT | 정상 |
| `evaluation_labels` | ✅ PRESENT (구조) | 실제 값은 별도 확인 필요 |
| `training_labels` | ✅ PRESENT (구조) | `progress_delta` 존재 확인 필요 |

### §4.3 Split 분류

| Split | 실제 파일 | 상태 |
|---|---|---|
| `test_id` | `data/frcgw_text/v0_1/test_id.jsonl` (33 eps) | ✅ EXISTS |
| `text_ood_grammar` | **ABSENT** → `test_id`로 alias | OOD eval 불가 |
| `text_noisy` | **ABSENT** → `test_id`로 alias | Noisy eval 불가 |
| `train` | `data/frcgw_text/v0_1/train.jsonl` | ✅ EXISTS (eval 미사용) |

---

## §5. Ablation 신뢰성 분석

### §5.1 Seed variance 0 — Deterministic Mock

```python
# src/frcgw/evaluation/ablations.py:60-65
def _random_public_candidate(obs: PublicObservation, *, salt: str = "") -> CandidateAction:
    seed = f"{salt}|{obs.instruction}|{len(obs.history_public)}|{len(obs.candidate_actions_public)}"
    rng = random.Random(seed)
    return rng.choice(obs.candidate_actions_public)
```

seed는 `obs.instruction + history_length + candidate_count`에서만 파생.  
config의 `seed: [0, 1, 2, 3, 4]`는 wrapper에 전달되지 않음.  
→ **5 seed 모두 동일한 action sequence 선택 → inter-seed variance = 0.**

`ablation_results.json` 80 rows (16 ablations × 5 seeds) 모두 byte-identical per ablation.

### §5.2 Task Success Saturation

```python
# src/frcgw/evaluation/eval_runner.py:122
success = success or total_progress > 0.0
```

OR semantics: `total_progress > 0.0`이면 즉시 success=True.  
`progress_delta > 0`인 step이 하나라도 있으면 `task_success_rate = 1.0`.  
→ **80/80 records = task_success_rate 1.0. Saturated. 차별화 불가.**

### §5.3 ABL-017 OPPOSITE Direction — Counter-Evidence

```python
# src/frcgw/evaluation/ablations.py:267-284
class NoIntentActionMappingAblationAgent(AblatedAgent):
    """ABL-017: Remove training-time intent-to-action mapping loss.
    At inference, manifests as random candidate selection.
    """
    def act(self, obs, eval_labels=None):
        return _random_public_candidate(obs, salt=self.ablation_id), _budget(...)
```

| Agent | failed_action_repetition_rate | 예상 방향 |
|---|---|---|
| FRCG-FULL | 0.500 | — |
| ABL-017 no_intent_action_mapping | 0.089 | FRCG > ABL-017 기대 → **반대** |

Delta = 0.089 - 0.500 = **-0.4107** (FRCG-FULL이 더 높음).

**해석**: random selection이 오히려 failed action repetition을 줄임.  
원인 가설: `_random_public_candidate`의 deterministic seed가 동일 `action_type`을 연속 선택하는 빈도가 FRCG-FULL보다 낮을 수 있음 (proxy artifact).  
→ **C5 claim의 proxy 신뢰도 더 낮아짐. STEP 7에서 root cause 분석 필수.**

### §5.4 Direct-Threat Baseline 0 Row

`ablation_results.json`에서 다음 baseline ID 검색 결과 0 row:

| Baseline | ID | 상태 |
|---|---|---|
| Verifier-Only | BASE-006 | N/A |
| CATTS | BASE-012-CATTS | N/A |
| Compute-Matched Random | BASE-015 | 코드 존재 (`baselines.py:293-320`), 미실행 |
| WAC | BASE-026 | N/A |
| CUWM | BASE-027 | N/A |
| WebWorld | BASE-028 | N/A |

**C3 claim (ABL-022/023 delta)만으로는 직접 위협 방어 불가.**

---

## §6. Trust Level 분류 표

| Metric 그룹 | Trust Level | 이유 |
|---|---|---|
| **C3 delta direction** (ABL-022/023 vs FRCG-FULL) | **Medium** | Gate 제거 → F=0은 메커니즘적으로 올바름. 크기는 mock이지만 방향 신뢰 |
| **F_t variance / degenerate rate** | **Medium** | smoke 실측값. 단, N=25 smoke episodes로 작음 |
| **C1 planning_calls=1** | **Low** | N=1. statistical power 없음. smoke 단일 episode |
| **C1 h_exec null_rate=0.0** | **Low** | h_exec = proxy (policy constant "oracle_best_action_proxy"), 실제 모델 inference 아님 |
| **C3 F1 절댓값** (0.4032) | **Low** | deterministic mock ablation, real model 아님 |
| **C5 rewrite_success_proxy** | **Low** | ABL-017 OPPOSITE direction으로 proxy 신뢰도 추가 하락 |
| **C6 progress_per_compute** | **Low** | deterministic mock, N=1 planning call, BASE-015 absent |
| **C2 regime_shift** | **N/A** | BLOCKED — 측정 자체 없음 |
| **C4 rollout** | **N/A** | BLOCKED — rollout_steps=0 |
| **Direct-threat comparison** | **N/A** | BASE-006/012/015/026/027/028 = 0 row |

### 요약

```
논문 인용 가능: NONE (pilot/core eval scope)
STEP 2+ 이후 인용 후보: C3 delta direction (방향만), F_t variance
STEP 3+ 이후 인용 후보: C1 persistence (MET-PERSIST-001 해소 후)
STEP 5+ 이후 인용 후보: C3 vs BASE-006/012-CATTS, C6 vs BASE-015
STEP 7+ 이후 인용 후보: C5 (ABL-017 방향 해소 후)
```

---

## §7. 하드 체크 결과 재확인

`metrics.json.hard_checks`:

| Check | 값 | 실제 의미 |
|---|---|---|
| `planning_calls_gt_0` | true | ✅ smoke에서 1 planning call 발생 |
| `h_exec_null_rate_lt_1` | true | ✅ h_exec = proxy (null 없음), 실제 모델 아님 |
| `f_t_variance_gt_0` | true | ✅ F_t variance=1.26, 비-degenerate |
| `hidden_leakage_count_eq_0` | true | ⚠️ smoke passthrough 값, real guard 미실행 |
| `degenerate_rate_lt_0_5` | true | ✅ 0.20 < 0.5 |
| `abl_022_result_exists` | true | ✅ ABL-022 행 존재 |
| `fake_metric_count_eq_0` | true | ✅ fabricated 값 없음 (aggregator임을 명시) |
| `hard_checks_all_pass` | true | ⚠️ preflight gate pass이며, 논문 accept 아님 |

---

## §8. STEP 1 PASS 선언

- [x] `09_run_lr_eval.py` 코드 감사 (preflight aggregator 확인, line 64-197, 264-278)
- [x] Full data path가 동일한 aggregator를 호출함 확인 (no-op)
- [x] Hidden leakage guard 미호출 확인 (eval_runner.py:100-103 경로 미진입)
- [x] Metric source trace 완성 (C1/C3/C5/C6 각각)
- [x] Dataset coverage: 33 episodes, predicted_wrong/wrong_prob ABSENT, splits aliased
- [x] Ablation seed variance = 0 (ablations.py:60-65)
- [x] task_success_rate saturation (eval_runner.py:122 OR semantics)
- [x] ABL-017 OPPOSITE direction 분석 + counter-evidence 명시
- [x] Direct-threat baseline 0 row 확인
- [x] Trust Level 분류 표 완성
- [x] 원본 파일 변경 0

**STEP 1: PASS → STEP 1.5로 진입 가능**
