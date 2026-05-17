# Real Episode-Level Eval Runner Contract
# STEP 2 Contract — `18_real_eval_runner_contract.md`

작성일: 2026-05-17  
branch: `memory-redesign-2026-05-16`  
선행: Run 6 P3_LR_EVAL preflight audit (PHASE A), STEP 1 reliability audit  
관련: `docs/orchestration/lr_alignment/14_run7_step_structure_blueprint.md`

---

## §1. Purpose

이 계약서는 STEP 2의 **Real Episode-Level Eval Runner** 구현 계약을 정의한다.

Run 6의 `P3_LR_EVAL.passed`는 preflight 통합 결과(smoke 집계)다.
이 runner는 `data/frcgw_text/v0_1/test_id.jsonl`을 step-by-step 순회하여
등록된 agent의 `act()`를 실제 호출하고, 누락 label에는 fake 0이 아닌
BLOCKED marker를 정직하게 기록한다.

---

## §2. Scope

### In Scope (STEP 2)

| 파일 | 역할 |
|---|---|
| `scripts/10_run_lr_real_eval.py` | Real runner entrypoint |
| `configs/lr_eval_real.yaml` | Real eval config (FRCG-LR alias 포함) |
| `tests/test_lr_real_eval_runner.py` | 14개 단위 테스트 |

### §3. Out of Scope (STEP 3+ 이관)

다음은 STEP 2 범위 밖이다. `scripts/10_run_lr_real_eval.py` 및 TASK FILES_FORBIDDEN에 명시된다.

- `src/frcgw/falsification/lr_scorer.py` ↔ `src/frcgw/evaluation/frcg_agent.py` wire-up
- Dataset label 백필:
  - `hypothesis_update_timestamp` (현재 0/1002 present)
  - `recovery_timestamp` (현재 0/1002 present)
  - `selected_hypothesis_confidence` (현재 0/1002 present)
  - `counterfactual_action_effects` (현재 sparse/absent)
  - `test_ood.jsonl` split 생성
- `src/frcgw/evaluation/baselines.py` registry 리팩토링
- `scripts/09_run_lr_eval.py`, `configs/lr_eval_core.yaml`, `eval_runner.py`, `metrics.py`, `frcg_agent.py` 수정 금지
- Pre-existing dirty 6개 파일 수정 금지:
  - `.gitignore`, `.self_evolving_memory/hooks/hook_execution_log.md`
  - `docs/orchestration/AGENT_TEAMS_ROLLOUT_PLAN.md`
  - `docs/orchestration/session_reports/2026-05/2026-05-17_precompact_handoff.md`
  - `plans/PHASE_PROGRESS.md`, `scripts/run_codex_task.ps1`

---

## §4. Architecture

```
configs/lr_eval_real.yaml
   │
   ▼
scripts/10_run_lr_real_eval.py::main()
   │
   ├── load YAML → config dict
   ├── _install_forbidden_source_guard()       # 3-layer monkeypatch
   ├── dataset_path = data/frcgw_text/v0_1/test_id.jsonl
   ├── _build_agent_dispatch_table(config):
   │      ├── FRCG-FULL / FRCG-LR → TextFRCGModelAgent(ckpt_path=…)  [alias]
   │      ├── ABL-017 → apply_ablation(TextFRCGModelAgent(), ABLATION_REGISTRY["no_intent_action_mapping"])
   │      ├── ABL-022 → apply_ablation(TextFRCGModelAgent(), ABLATION_REGISTRY["no_falsification_score_gate"])
   │      ├── ABL-023 → apply_ablation(TextFRCGModelAgent(), ABLATION_REGISTRY["uncertainty_instead_of_falsification"])
   │      ├── BASE-006 → VerifierRecoveryAgent()
   │      ├── BASE-012-CATTS → CATTSStyleUncertaintyGateAgent()
   │      ├── BASE-015 → ComputeMatchedRandomAgent()
   │      ├── BASE-026 → WACStyleConsequenceCorrectionAgent()
   │      ├── BASE-027 → CUWMStyleCandidateSimulationAgent()
   │      ├── BASE-028 → WebWorldStyleSearchAgent()
   │      └── BASE-003+008-VLAA → VLAALoopHeuristicAgent()
   │
   ├── preflight_dry_obs_check(dispatch_table)  # forbidden field 부재 확인
   │
   ├── runner = EvaluationRunner(_minimal_metric_config(config))
   │
   ├── for seed in seeds:
   │     for agent_id, factory in dispatch_table.items():
   │         agent = factory(); agent.reset()
   │         result = runner.run(agent, dataset_path, split, seed)
   │         write_per_step_jsonl(result, out_dir/per_step/{agent_id}_seed{seed}.jsonl)
   │         write_per_episode_jsonl(result, out_dir/per_episode/{agent_id}_seed{seed}.jsonl)
   │
   ├── metrics_payload = _build_metrics_with_blocked_markers(all_results, dataset_audit)
   └── write metrics.json + manifest.json → outputs/runs/p3_lr_real_eval/
```

### Reuse 목록 (수정 금지 파일에서 import만)

| 모듈 | 재사용 대상 |
|---|---|
| `src/frcgw/evaluation/eval_runner.py` | `EvaluationRunner.run()` — episode loop + leakage assert |
| `src/frcgw/evaluation/metrics.py` | `METRIC_FUNCTIONS`, `assert_no_hidden_labels_in_input` |
| `src/frcgw/evaluation/baselines.py` | 9개 baseline class (registry 미생성, 직접 import) |
| `src/frcgw/evaluation/ablations.py` | `ABLATION_REGISTRY` + `apply_ablation` |
| `src/frcgw/evaluation/frcg_agent.py` | `TextFRCGModelAgent` (FRCG-LR alias 대상) |
| `src/frcgw/schemas/visibility.py` | `FORBIDDEN_AGENT_FIELDS` (leakage guard) |

---

## §5. predicted_wrong Placeholder Contract

**STEP 2 결정**: `lr_scorer.py` wire-up 미포함. 기존 `frcg_agent.py` path 사용.

- `TextFRCGModelAgent.act()`가 `self._last_predicted_wrong = max_grammar_prob < self._confidence_threshold` 설정.
- `EvaluationRunner.run()`이 `agent.last_predicted_wrong` (line 107-110), `agent.last_wrong_prob` (line 111-114) 읽음.
- `F_t` 필드는 trace용으로 `agent.last_F_t`를 per_step에 기록하되, **predicted_wrong은 F_t에서 유도하지 않음**.
- **명시적 계약**: predicted_wrong = `(1 - max P(grammar)) > (1 - confidence_threshold)` — placeholder.
  `F_t > tau_f` mechanism은 STEP 3 `lr_scorer` wire-up에서 도입.

---

## §6. per_step.jsonl 스키마

```
run_id, agent_id, agent_type, episode_id, step_id, step_index, split,
action_id, action_type, selected_hypothesis_id|null, selected_hypothesis_confidence|null,
f_t:float|null, tau_f:float|null, predicted_wrong:bool, wrong_prob:float,
planning_calls:int, rollout_steps:int, observed_effect_type:str,
true_wrong_hypothesis_available:bool, leakage_guard_passed:bool, error:str|null
```

---

## §7. per_episode.jsonl 스키마

```
run_id, agent_id, episode_id, split,
num_steps, planning_calls_total, rollout_steps_total,
falsification_tp, falsification_fp, falsification_fn,
degenerate_f_t_count, h_exec_null_count,
blocked_metrics:[str], errors:[str]
```

---

## §8. metrics.json 스키마 (BLOCKED-aware)

```json
{
  "run_mode": "real_episode_eval",
  "agents": {
    "FRCG-FULL": {
      "seeds": [0, 1, 2],
      "C1_falsification_f1":     {"value": 0.36,  "status": "OK"},
      "C1_persistence":          {"value": null,  "status": "BLOCKED_no_hypothesis_update_timestamp"},
      "C3_recovery_delay":       {"value": null,  "status": "BLOCKED_no_recovery_timestamp"},
      "C5_calibration_ece":      {"value": null,  "status": "BLOCKED_no_confidence_label"},
      "task_success_rate":       {"value": 0.13,  "status": "OK"},
      "progress_per_compute":    {"value": 0.07,  "status": "OK"}
    },
    "ABL-022": { "..." : "..." }
  },
  "deltas": {
    "FRCG-FULL_vs_ABL-022_falsification_f1":  {"value": 0.36, "status": "OK"},
    "FRCG-FULL_vs_BASE-015_progress_per_compute": {"value": 0.07, "status": "OK"}
  },
  "blocked_metric_count": 9,
  "fake_metric_count": 0,
  "hard_checks_all_pass": true
}
```

**규칙**: 모든 numeric metric은 `{value, status}` wrapper. 누락 label에 `0.0` bare 금지. 14번 테스트로 강제.

---

## §9. manifest.json 스키마

```json
{
  "run_mode": "real_episode_eval",
  "run_id": "p3_lr_real_eval_<UTC>",
  "created_at": "...", "git_sha": "...", "branch": "memory-redesign-2026-05-16",
  "config_path": "configs/lr_eval_real.yaml",
  "dataset_path": "data/frcgw_text/v0_1/test_id.jsonl",
  "split": "test_id", "seed": [0, 1, 2],
  "runner": "scripts/10_run_lr_real_eval.py",
  "source_artifacts_used":  ["data/frcgw_text/v0_1/test_id.jsonl"],
  "forbidden_source_artifacts": [
    "outputs/runs/p3_lr_smoke/metrics.json",
    "outputs/runs/p3_ablations/ablation_results.json",
    "outputs/runs/p3_lr_eval/metrics.json"
  ],
  "forbidden_source_assertion": "none_read",
  "per_step_path": "outputs/runs/p3_lr_real_eval/per_step/",
  "per_episode_path": "outputs/runs/p3_lr_real_eval/per_episode/",
  "metrics_path": "outputs/runs/p3_lr_real_eval/metrics.json",
  "agents": ["FRCG-LR", "ABL-017", "ABL-022", "ABL-023", "BASE-006",
             "BASE-012-CATTS", "BASE-015", "BASE-026", "BASE-027", "BASE-028",
             "BASE-003+008-VLAA"],
  "id_aliases": {"FRCG-LR": "FRCG-FULL"},
  "random_init_ok": false,
  "scope_note": "Real episode-level eval. BLOCKED metrics honestly report missing labels."
}
```

**random_init_ok**: checkpoint 미지정 시 `false`. hard_checks_all_pass를 `false`로 만든다.

---

## §10. Leakage Prevention

1. **PublicObservation only**: `EvaluationRunner.run()` line 99가 `step["public_observation"]`을 읽고 `assert_no_hidden_labels_in_input()` 호출. runner는 PublicObservation을 직접 생성하지 않음.
2. **eval_labels 분리**: non-oracle agent에는 `agent.act(obs)` (eval_labels 미전달). Oracle agent는 dispatch table에서 제외.
3. **Pre-flight dry observation**: dispatch table 빌드 직후 각 agent에 dummy obs 한 번 호출하여 forbidden field 부재 확인.
4. **Forbidden-source guard** (`_install_forbidden_source_guard()`): `builtins.open` + `pathlib.Path.read_text` + `pathlib.Path.open` 3-layer wrapping. 3개 forbidden path 중 하나라도 접근 시 `RuntimeError`. main() 진입 시 install, exit 시 restore.
5. **Counterfactuals**: dataset의 `counterfactuals` field는 `_build_public_observation()`에서 읽지 않음 (기존 코드 검증됨).

---

## §11. BLOCKED Metric Policy

`_build_metrics_with_blocked_markers()` 함수 규칙:

| 누락 label | 영향 metric | BLOCKED status |
|---|---|---|
| `hypothesis_update_timestamp` (0/1002) | C1_persistence, wrong_grammar_persistence | `BLOCKED_no_hypothesis_update_timestamp` |
| `recovery_timestamp` (0/1002) | C3_recovery_delay | `BLOCKED_no_recovery_timestamp` |
| `selected_hypothesis_confidence` (0/1002) | C5_calibration_ece | `BLOCKED_no_confidence_label` |
| `counterfactuals` 빈 list | CF metrics | `BLOCKED_no_counterfactual_samples` |
| `test_ood.jsonl` 없음 | C2 regime-split | `BLOCKED_no_ood_split` |

**bare 0.0 금지**: BLOCKED metric에 bare numeric value 기록 절대 금지.  
`metrics.fake_metric_count` 필드로 강제. 0이 아니면 hard check fail.

---

## §12. FRCG-LR / FRCG-FULL Alias

- `FRCG-LR`와 `FRCG-FULL`은 동일 class (`TextFRCGModelAgent`, `baseline_id="FRCG-FULL"`).
- `id_aliases: {"FRCG-LR": "FRCG-FULL"}` manifest에 명시.
- dispatch table에서는 `"FRCG-FULL"` key 사용. 외부 ID `"FRCG-LR"`는 config에서 alias로 해석.

---

## §13. Forbidden Source Artifacts (3개 고정)

다음 3개 경로는 `_install_forbidden_source_guard()`가 접근 차단한다.
manifest에 `forbidden_source_artifacts`로 열거되고 `forbidden_source_assertion: "none_read"` 검증.

```
outputs/runs/p3_lr_smoke/metrics.json
outputs/runs/p3_ablations/ablation_results.json
outputs/runs/p3_lr_eval/metrics.json
```

이 경로들은 preflight 집계 결과다. real runner는 이를 절대 읽지 않는다.

---

## §14. Claim-OK vs BLOCKED 요약

| Claim | 현재 가능성 | STEP 2 결과 |
|---|---|---|
| C1 binary (falsification F1) | OK | 실측값 기록 |
| C1 persistence | BLOCKED | null + status |
| C3 recovery_delay | BLOCKED | null + status |
| C3 vs ABL-022 delta_f1 | OK | 실측 delta |
| C3 vs ABL-023 delta_f1 | OK | 실측 delta |
| C4 rollout fidelity | BLOCKED | null + status |
| C5 rewrite proxy (1-failed_rep) | OK | 실측값 기록 |
| C5 calibration ECE | BLOCKED | null + status |
| C5 switch_delay | BLOCKED | null + status |
| C6 progress_per_compute | OK | 실측값 기록 |
| C6 false_planning_call_rate | OK | 실측값 기록 |
| C2 regime-split F1 | BLOCKED | null + status |

---

## §15. Hard-Fail Triggers

다음 중 하나라도 발생하면 STEP 2 BLOCKED:

- 14 test 중 하나라도 red
- `fake_metric_count > 0`
- `forbidden_source_assertion != "none_read"`
- `hidden_leakage_count > 0`
- BLOCKED metric에 bare numeric value (non-null)
- `random_init_ok = false` → `hard_checks_all_pass = false`

---

## §16. Test Plan — 14 tests

`tests/test_lr_real_eval_runner.py`:

1. `test_loads_config_without_error` — YAML 로드 에러 없음
2. `test_dispatch_table_contains_all_required_agent_ids` — 11개 agent_id 전부 존재
3. `test_frcg_full_and_frcg_lr_alias_resolve_to_same_class` — 동일 class
4. `test_runner_calls_agent_act_at_least_once` — stub agent call counter
5. `test_runner_passes_public_observation_only` — eval_labels non-oracle에 미전달
6. `test_runner_does_not_read_p3_lr_smoke` — monkeypatch builtins.open + Path.read_text
7. `test_runner_does_not_read_p3_ablations` — 동일
8. `test_runner_does_not_read_p3_lr_eval_metrics` — 동일
9. `test_predicted_wrong_equals_agent_last_predicted_wrong` — stub agent True/False 순환
10. `test_predicted_wrong_threshold_documented_in_contract` — contract MD §5 grep
11. `test_missing_recovery_timestamp_marks_C3_blocked` — synthetic episode
12. `test_missing_confidence_marks_C5_calibration_blocked_not_fake` — value=null, fake_count=0
13. `test_manifest_records_source_artifacts_used` — 정확히 test_id.jsonl만
14. `test_manifest_forbidden_source_artifacts_assertion_is_none_read` — "none_read"

Fixture: `tests/test_eval_runner.py`의 `_episode()` helper를 차용하여 eval_label field를 선택적으로 비워 BLOCKED path 검증.

---

## §17. STEP 3 Handoff — 데이터셋 재생성 필요 label

STEP 3 진입 전에 반드시 해결해야 하는 label 백필:

| 누락 field | 현재 coverage | STEP 3 action |
|---|---|---|
| `hypothesis_update_timestamp` | 0/1002 | generator 추가 후 데이터 재생성 |
| `recovery_timestamp` | 0/1002 | generator 추가 후 데이터 재생성 |
| `selected_hypothesis_confidence` | 0/1002 | `frcg_agent.py` + dataset backfill 필요 |
| `counterfactual_action_effects` | sparse | counterfactual generator 구현 |
| `test_ood.jsonl` | 없음 | OOD split 생성 (ood_type=grammar_shift) |

이 label들이 없는 한 C1_persistence, C3_recovery, C4_rollout, C5_ECE, C2_regime_split는 영구 BLOCKED.  
STEP 3 plan은 이 테이블을 blocker로 참조해야 한다.

---

## §18. Codex TASK 계약

### FILES_ALLOWED
```
scripts/10_run_lr_real_eval.py
configs/lr_eval_real.yaml
tests/test_lr_real_eval_runner.py
```

### FILES_FORBIDDEN (representative list)
```
.claude/**, CLAUDE.md, .mcp.json, .venv/**, data/**, outputs/**, secrets/**, .env*
scripts/run_codex_task.ps1
paper_context_ref/**
src/frcgw/evaluation/eval_runner.py
src/frcgw/evaluation/metrics.py
src/frcgw/evaluation/baselines.py
src/frcgw/evaluation/ablations.py
src/frcgw/evaluation/frcg_agent.py
src/frcgw/falsification/lr_scorer.py
scripts/09_run_lr_eval.py
configs/lr_eval_core.yaml
(pre-existing dirty 6개 파일)
```

### ACCEPTANCE_CRITERIA
- 14 tests green
- smoke run (--max-episodes 3) 성공, exit 0
- `manifest.forbidden_source_assertion == "none_read"`
- `metrics.fake_metric_count == 0`
- 모든 BLOCKED metric의 `value is None`

---

## §19. Phase Gate

신규 sentinel: `outputs/phase_gates/P3_LR_REAL_EVAL.passed` (zero-byte)

기존 `P3_LR_EVAL.passed`는 historical record로 보존.

PHASE F 끝 조건:
- `fake_metric_count == 0` + `hard_checks_all_pass == true` + `forbidden_source_assertion == "none_read"` 충족 시 sentinel 작성.
- `/frcgw-phase-check --pass P3_LR_REAL_EVAL` 호출 후 공식 기록.

---

*Source MDs: `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md`, `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP.md`, `docs/orchestration/lr_alignment/14_run7_step_structure_blueprint.md`*
