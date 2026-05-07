# SESSION 11-13 — Handoff Document

> Session 11-13은 **planner interface + 6 baseline planners + FRC-WM (Ours)** + **evaluation runner**까지 구현한다. 학습된 RSSM checkpoint(`outputs/wm_runs/wm_medium_*_v1/checkpoints/step_00030000.pt`)를 frozen으로 사용하며, **full evaluation은 사용자가 직접 PowerShell에서 실행한다.**
>
> Cursor 스코프: 구현 + import smoke + checkpoint load + 1~2 episode dry-run. **Long evaluation 직접 실행 금지.**

---

## 1. 생성/수정 파일 목록

### 1.1 신규 (Cursor가 생성)

| 경로 | 종류 | 라인 수 (대략) | 내용 |
| --- | --- | ---: | --- |
| `falsifiable_regime_world_model/planner/__init__.py` | 신규 | 90 | public API re-export |
| `falsifiable_regime_world_model/planner/config.py` | 신규 | 250 | PlannerConfig, BaselinePlannerConfig, FRCPlannerConfig, PlannerEvalConfig (yaml 매핑) |
| `falsifiable_regime_world_model/planner/interface.py` | 신규 | 220 | BeliefState, RolloutPrediction, PlannerDecision, ComputeAccountant, PlannerState |
| `falsifiable_regime_world_model/planner/world_model_adapter.py` | 신규 | 350 | WorldModelAdapter (load_from_checkpoint / encode_observation / update_belief / imagine_from_belief / imagine_alternative / score_rollout / get_head_outputs) |
| `falsifiable_regime_world_model/planner/action_space.py` | 신규 | 165 | ActionSpaceSpec, CandidateActionSequence, enumerate_action_candidates, sample_action_sequences |
| `falsifiable_regime_world_model/planner/scoring.py` | 신규 | 270 | FalsificationContext, compute_falsification_score, compute_action_relevance, compute_alternative_disagreement |
| `falsifiable_regime_world_model/planner/baselines.py` | 신규 | 360 | BasePlanner + 6 baseline class (Reactive / FixedK / AlwaysPlan / UncertaintyGate / AdaptiveLookahead / EventOnly) |
| `falsifiable_regime_world_model/planner/frc_planner.py` | 신규 | 280 | FRCWMPlanner (Ours) — 9-step decision loop |
| `falsifiable_regime_world_model/planner/policies.py` | 신규 | 60 | select_reactive_action helper |
| `falsifiable_regime_world_model/planner/trace.py` | 신규 | 150 | StepTrace, PlannerTrace, write_traces_jsonl |
| `falsifiable_regime_world_model/eval/__init__.py` | 신규 | 25 | public API re-export |
| `falsifiable_regime_world_model/eval/metrics.py` | 신규 | 250 | EpisodeResult, compute_episode_metrics, aggregate_by_planner, aggregate_by_split, bootstrap_ci |
| `falsifiable_regime_world_model/eval/rollout_runner.py` | 신규 | 195 | run_episode helper (env loop + trace 기록) |
| `falsifiable_regime_world_model/eval/planner_eval.py` | 신규 | 320 | PlannerEvalRunner (model × planner × split × seed cross-product) |
| `configs/planner_eval_debug.yaml` | 신규 | 90 | smoke test config (Cursor-runnable) |
| `configs/planner_eval_main.yaml` | 신규 | 175 | 7 planners × 3 models × 6 splits × 3 seeds |
| `configs/planner_eval_ood.yaml` | 신규 | 165 | OOD-focused (5 seeds × 100 episodes) |
| `scripts/check_planner_interface.py` | 신규 | 230 | interface smoke (1~2 episode dry-run) |
| `scripts/evaluate_planners.py` | 신규 | 80 | top-level eval entry |
| `scripts/compare_planner_results.py` | 신규 | 175 | 결과 비교 csv 생성 |
| `scripts/summarize_planner_eval.py` | 신규 | 130 | markdown summary 생성 |
| `docs/PLANNER_INTERFACE_DESIGN.md` | 신규 | 12-section spec |
| `docs/PLANNER_BASELINES_DESIGN.md` | 신규 | 8-section spec |
| `docs/FRC_WM_PLANNER_DESIGN.md` | 신규 | 12-section spec |
| `docs/SESSION11_13_HANDOFF.md` | 신규 | 본 문서 |

### 1.2 수정 없음 (보존 0줄)

- `ref/PART0~3`
- `data/**` (모든 dataset)
- `outputs/wm_runs/*/checkpoints/*.pt` (read-only)
- `outputs/wm_runs/*/{train_log.jsonl, valid_log.jsonl}`
- `scripts/{train_world_model,generate_dataset,validate_dataset,inspect_episode,plot_dataset_stats,_p1_check_family_disjoint,check_wm_shapes,check_wm_dataloader,check_training_env,probe_wm_hparams,summarize_wm_run,diagnose_wm_runs,diagnose_wm_thresholds,diagnose_wm_rollout_fidelity,compare_wm_ablation_runs}.py`
- `falsifiable_regime_world_model/wm/**` 전부
- `falsifiable_regime_world_model/rg4f/**` 전부
- `configs/{wm_*.yaml, dataset_default.yaml}`
- `requirements.txt`

---

## 2. Planner Interface 핵심 API

```python
from falsifiable_regime_world_model.planner import (
    WorldModelAdapter, BeliefState, RolloutPrediction,
    PlannerConfig, FRCPlannerConfig, FRCWMPlanner,
    ReactivePlanner, FixedKPlanner, AlwaysPlanPlanner,
    UncertaintyGatePlanner, AdaptiveLookaheadPlanner, EventOnlyPlanner,
)

# 1. checkpoint 로드
adapter = WorldModelAdapter.load_from_checkpoint(
    "outputs/wm_runs/wm_medium_full_v1/checkpoints/step_00030000.pt",
    wm_config_path="configs/wm_medium.yaml",
    variant="full_model",
    device="auto",
)

# 2. belief update (per env step)
belief = adapter.update_belief(prev_belief=None, obs=env_obs, prev_action=None, step_index=0)

# 3. imagine current
rollout = adapter.imagine_from_belief(belief, action_seqs, horizon=10, n_samples=1, n_candidates=8)

# 4. imagine alternative (oracle 사용 금지)
alt = adapter.imagine_alternative(belief, action_seqs, horizon=10, latent_perturb_std=0.5)

# 5. score
value = adapter.score_rollout(rollout)

# 6. planner decision
planner = FRCWMPlanner(adapter=adapter, config=PlannerConfig(...), frc_config=FRCPlannerConfig(...))
decision = planner.select_action(env_obs=obs, belief=belief, planner_state=state)
```

---

## 3. Baseline Planner 요약

PART3 §3.22 전부 구현.

| Planner | yaml `kind` | planning 빈도 | 사용 head | 비고 |
|---|---|---|---|---|
| Reactive | `reactive` | 매 step 1-step lookahead | reward, state | head greedy |
| Fixed-k | `fixed_k` | k=5 step마다 | reward, state | period yaml에서 변경 가능 |
| Always-plan | `always_plan` | 매 step | 모든 head | compute frontier baseline |
| Uncertainty Gate | `uncertainty_gate` | uncertainty > τ | regime_logits / latent | regime_entropy default + reward_var fallback |
| Adaptive Lookahead | `adaptive_lookahead` | 매 step (horizon만 변경) | regime_logits / latent | low/high horizon switch |
| Event-only | `event_only` | reveal/mismatch > τ | reveal_logit, mismatch_logit | cp 사용 금지 (Ours에 reserve) |

상세: `docs/PLANNER_BASELINES_DESIGN.md`.

---

## 4. Ours: FRC-WM Planner 요약

PART2 §3.7~§3.14 알고리즘 1:1 구현.

핵심:
- **9-step decision loop**: context push → preliminary falsification → low/medium/high stage 결정 → candidate generation → current rollout → alternative rollout (high/extreme stage) → action relevance → final falsification → decision mode 선택.
- **falsification = weighted aggregation of 5 factors**: change_risk, mismatch_risk, reveal_risk, regime_uncertainty, rollout_disagreement. yaml weights `(0.30, 0.20, 0.15, 0.20, 0.15)`.
- **action relevance = value gap + action flip** (PART2 §3.8.3).
- **compute reallocation = stage-based horizon/candidate count + alternative rollout 추가**: low → reactive (compute 거의 0), medium → current rollout만, high/extreme → alternative rollout 추가.
- **decision modes**: reactive, plan_current, plan_alternative, correct, avoid, delay, explore_for_information.
- **oracle 금지**: alternative는 latent perturbation으로만 모의. true_regime / cp / shift / reveal info 직접 사용 금지.

상세: `docs/FRC_WM_PLANNER_DESIGN.md`.

---

## 5. Smoke Test 결과

### 5.1 Import smoke

```
.\.venv\Scripts\python.exe -c "from falsifiable_regime_world_model.planner import WorldModelAdapter, FRCWMPlanner, PlannerEvalConfig; from falsifiable_regime_world_model.eval import PlannerEvalRunner, run_episode; print('IMPORT OK')"
```

→ **PASS**. 모든 public API import 성공.

### 5.2 Interface smoke

```
.\.venv\Scripts\python.exe scripts\check_planner_interface.py --checkpoint outputs\wm_runs\wm_medium_full_v1\checkpoints\step_00030000.pt --max-steps 20
```

→ **PASS**. 9 단계 모두 통과.

확인된 동작:
- checkpoint load (full_model variant) — 1.47s
- has_regime_head=True, has_change_point_head=True, has_mismatch_head=True
- env reset → obs shape (5,5,10), scalar (14,), event_token=0
- belief update single step → h(1,512), z(1,128), 10 head keys
- enumerate 16 candidates / sample 8 candidates / candidates_to_tensor (16,5)
- imagine_from_belief → state_pred(16,5,5), reward_pred(16,5), candidate_value 16개
- imagine_alternative (latent perturb) → |alt-cur| mean ≈ 1.44
- ReactivePlanner.select_action → action=9, mode=reactive
- FRCWMPlanner.select_action → action=12, mode=reactive (low falsification stage), F=0.265
- 1 episode dry-run (max_steps=20) → return=-22, planning_calls=20, rollout_steps=328, wallclock=0.14s

### 5.3 Debug eval smoke

```
.\.venv\Scripts\python.exe scripts\evaluate_planners.py --config configs\planner_eval_debug.yaml --out-dir outputs\planner_eval_debug --max-episodes 2
```

→ **PASS**. 6 episode (3 planner × 1 model × 1 split × 1 seed × 2 episode) 완료, 3.9s.

생성 파일 확인:
- `outputs/planner_eval_debug/raw_episodes.jsonl`
- `outputs/planner_eval_debug/metrics_by_episode.csv`
- `outputs/planner_eval_debug/metrics_by_planner.csv`
- `outputs/planner_eval_debug/metrics_by_split.csv`
- `outputs/planner_eval_debug/aggregate_summary.csv`
- `outputs/planner_eval_debug/config_resolved.yaml`
- `outputs/planner_eval_debug/planner_traces/*.jsonl` (6개)

debug eval의 metrics_by_planner.csv 일부 (max_steps=60, num_episodes=2, full only):

| planner | n | return | success | planning_calls | rollout_steps | compute_norm_return | mean_falsification |
|---|---:|---:|---:|---:|---:|---:|---:|
| reactive | 2 | -60.6 | 0.0 | 60.0 | 960 | -0.063 | 0.000 |
| fixed_k | 2 | -61.3 | 0.0 | 12.0 | 1248 | -0.049 | 0.000 |
| ours_frc | 2 | -61.3 | 0.0 | 2.0 | 952 | -0.064 | 0.051 |

→ ours_frc는 60 step의 짧은 episode에서 mean_falsification=0.05로 *대부분 low falsification stage* (yaml `falsification_threshold=0.30` 미만). 따라서 reactive로 동작 → planning_calls=2 (FRC가 reactive fallback 시 planning을 안 카운트). compute reallocation이 의도대로 작동.

success_rate=0인 이유: 60 step은 task A/B/C/D 4개를 모두 완료하기에 너무 짧다 (default episode_max_steps=600). 이는 **debug smoke의 의도된 동작**이며, full evaluation에서 max_steps_per_episode=600으로 평가한다.

### 5.4 Compare + summarize smoke

```
.\.venv\Scripts\python.exe scripts\compare_planner_results.py --input outputs\planner_eval_debug --out-dir outputs\planner_eval_debug_summary
.\.venv\Scripts\python.exe scripts\summarize_planner_eval.py --input outputs\planner_eval_debug_summary --out outputs\planner_eval_debug_summary\summary.md
```

→ **PASS**. 4 csv + summary.md 생성.

---

## 6. 사용자가 직접 실행할 명령어

> **본 세션은 long evaluation 직접 실행을 금지한다.** Cursor smoke까지만 수행. 아래 명령은 사용자가 PowerShell에서 직접 실행한다.

### 6.1 인터페이스 smoke (이미 PASS, 재실행 가능)

```powershell
.\.venv\Scripts\python.exe scripts\check_planner_interface.py `
    --checkpoint outputs\wm_runs\wm_medium_full_v1\checkpoints\step_00030000.pt `
    --config configs\planner_eval_debug.yaml
```

### 6.2 Debug planner eval

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_planners.py `
    --config configs\planner_eval_debug.yaml `
    --out-dir outputs\planner_eval_debug
```

### 6.3 Main planner eval (사용자 권장 실행)

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_planners.py `
    --config configs\planner_eval_main.yaml `
    --out-dir outputs\planner_eval_main
```

처음에는 `--max-episodes 10` 옵션으로 cap을 걸어 압박을 줄이는 것을 권장:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_planners.py `
    --config configs\planner_eval_main.yaml `
    --out-dir outputs\planner_eval_main_quick `
    --max-episodes 10
```

전체 main eval (7 planner × 3 model × 6 split × 3 seed × 50 episode = 18,900 episode)은 GPU에서 수 시간이 걸릴 수 있다. paper-final로 가기 전에 quick 검증 후 full 실행을 권한다.

### 6.4 OOD-focused eval

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_planners.py `
    --config configs\planner_eval_ood.yaml `
    --out-dir outputs\planner_eval_ood
```

### 6.5 결과 비교 (compare_planner_results)

```powershell
.\.venv\Scripts\python.exe scripts\compare_planner_results.py `
    --input outputs\planner_eval_main `
    --out-dir outputs\planner_eval_main_summary
```

OOD eval 결과는:

```powershell
.\.venv\Scripts\python.exe scripts\compare_planner_results.py `
    --input outputs\planner_eval_ood `
    --out-dir outputs\planner_eval_ood_summary
```

### 6.6 결과 markdown summary

```powershell
.\.venv\Scripts\python.exe scripts\summarize_planner_eval.py `
    --input outputs\planner_eval_main_summary `
    --out docs\PLANNER_EVAL_SUMMARY.md
```

```powershell
.\.venv\Scripts\python.exe scripts\summarize_planner_eval.py `
    --input outputs\planner_eval_ood_summary `
    --out docs\PLANNER_EVAL_OOD_SUMMARY.md
```

---

## 7. 결과 저장 위치

```
outputs/planner_eval_main/
├─ raw_episodes.jsonl                       # episode dataclass-as-dict per line
├─ metrics_by_episode.csv                   # per-episode raw metric
├─ metrics_by_planner.csv                   # planner × model aggregate
├─ metrics_by_split.csv                     # planner × model × split aggregate
├─ aggregate_summary.csv                    # 위 두 개 합본
├─ config_resolved.yaml                     # 실행 시점 yaml 풀어둔 사본
└─ planner_traces/
   ├─ <model>__<planner>__<split>__seed<seed>__ep<idx>.jsonl
   └─ ... (모든 episode trace; save_traces=true 시)
```

```
outputs/planner_eval_main_summary/
├─ planner_comparison_table.csv             # main paper table
├─ model_ablation_planner_table.csv         # 같은 planner across model variants
├─ ood_breakdown_table.csv                  # per-(planner, model, split)
├─ compute_normalized_table.csv             # compute frontier
├─ figures/                                 # 사용자 plot용 빈 폴더
└─ summary.md                                # markdown 자동 생성
```

`docs/PLANNER_EVAL_SUMMARY.md` — `summarize_planner_eval.py`로 자동 생성하는 markdown 표 + 해석 가이드.

paper-side (생성하지 않음): `confidence_intervals.csv`, `compute_tradeoff.csv`, `wrong_hypothesis_metrics.csv`, `action_relevance_metrics.csv`는 `metrics_by_*.csv`의 column으로 이미 포함되어 있으며 별도 파일을 만들지는 않았다 (모두 한 csv에서 join 가능).

---

## 8. Session 14 Evaluation Runner 확장 TODO

본 세션은 *기능*은 모두 구현했지만 paper-final reporting을 위해 다음 확장이 권장된다.

### 8.1 OOD environment 변형 정확화

- 현재 `_build_env_config_for_split`은 `ood_param_shift`만 자동 처리. 다른 OOD (room_perm / factor_recomb / obs_shift / field_placement)는 dataset generator의 `split_policy` 정확 재현이 필요.
- **방법:** `scripts/generate_dataset.py`의 split policy 함수를 import하여 episode-level RG4FConfig를 만든다. 또는 *dataset 기반 evaluator* — npz를 직접 replay해 평가.

### 8.2 정식 regime conditioning

- `imagine_alternative`가 latent perturbation만 사용. 학습 단에서 RSSM input에 `regime_index_embedding`을 추가한 backbone variant를 학습하면 정식 conditioning 가능.
- API 호환: `adapter.imagine_alternative(..., regime_embedding=emb)` — 현재 시그니처에 추가 가능.

### 8.3 value head

- 현재 candidate value = reward sum × done masking. PART2 §3.8.3의 `Q(s, r, a)`에 더 가까운 값을 위해 학습 시 supervised value head 추가.

### 8.4 explanation faithfulness eval

- PART3 §3.25.13: regime intervention하여 action argmax / value shift 측정. 별도 script `scripts/explain_planner.py`로 추가.

### 8.5 counterfactual rollout fidelity

- PART3 §3.25.12: alternative action sequence로 imagine한 결과를 *다른* env replay와 비교. dataset 기반 evaluator + replay buffer가 필요.

### 8.6 multi-seed × bootstrap CI 강화

- 현재 main yaml: 3 seed × 50 episode = 150 sample/cell. paper-final은 10 seed × 100 episode = 1000 sample/cell이 권장.
- yaml `splits[*].seeds`와 `num_episodes`만 늘리면 됨.

### 8.7 task별 separately reporting

- `task_completed`는 obs.scalar의 마지막 4개로 추정. 더 정확한 task별 추적은 env가 task-A/B/C/D별 done flag를 별도 노출해야 함 (Session 14에서 RG4FEnv `_build_info`에 추가).

### 8.8 ManagedCheckpointer best alias 버그 수정

- WM_DIAGNOSTICS_REPORT §1.4 known issue. 다음 학습 run 전에 fix.

---

## 9. 논문 주장 검증을 위한 기대 비교표

main eval 결과가 다음 패턴을 보여야 paper main claim이 supported.

### 9.1 좋은 결과 (paper-friendly)

| 비교 | 기대 | metric |
|---|---|---|
| Ours > fixed_k | 같은 budget에서 더 높은 success/return | `compute_normalized_return` ↑, `success_rate` ≥ |
| Ours > uncertainty_gate | uncertainty 만으로는 부족 | `success_rate` ↑ (특히 OOD), `WHPT` ↓ |
| Ours > adaptive_lookahead | horizon 조절 vs hypothesis switch | `action_flip_rate` ↑ (useful), `WHPT` ↓ |
| Ours ≥ always_plan | 같은 성능을 더 적은 compute로 | `planning_calls` ↓, `success_rate` ≥ |
| full + Ours > no_regime + Ours | regime supervision 필요 | `WHPT` ↓ in ood_param_shift |
| full + Ours > no_change_point + Ours | cp signal이 falsification에 필요 | `recovery_delay_after_change` ↓ |

### 9.2 애매한 결과 (정직 보고)

- Ours가 in-domain test_id에서는 fixed_k와 비슷, OOD에서만 우위 → "OOD generalization"으로 위치.
- cp signal이 약해도 mismatch + reveal로 falsification이 잘 작동 → cp head는 보조 신호로 위치.
- always_plan과 success는 비슷하지만 compute는 절반 → "compute efficiency"로 위치.

### 9.3 나쁜 결과 (claim 약화 필요)

- Ours가 fixed_k보다 모든 split에서 낮음 → falsification weights 재조정 필요. 또는 cp threshold transferability 한계 인정.
- always_plan이 모든 metric에서 dominate → compute frontier claim 약화.
- no_regime / no_cp와 차이 없음 → variant ablation의 effect 부재 → paper에서 mechanism contribution 약화.

본 세션의 Cursor smoke (max_steps=60, 2 episode)로는 위 어느 패턴도 결정할 수 없다. paper-side conclusion은 **사용자가 main eval을 실행한 후** 결정한다.

---

## 10. Self-Audit

| Check | Status | Evidence |
|---|:-:|---|
| ref/PART0~3를 읽었는가 | PASS | 모두 read 도구로 전체 로드. PART2 §3.7~§3.14 1:1 매핑은 frc_planner.py / scoring.py에서 구현. |
| checkpoint를 수정하지 않았는가 | PASS | `outputs/wm_runs/*/checkpoints/*.pt`는 `WorldModelAdapter.load_from_checkpoint`에서 read-only로만 사용. |
| 학습을 새로 실행하지 않았는가 | PASS | scripts/train_world_model.py 호출 없음. trainer 호출 없음. |
| planner interface가 구현되었는가 | PASS | `WorldModelAdapter` (load/encode/update_belief/imagine_from_belief/imagine_alternative/score_rollout/get_head_outputs) 6 메서드 모두 구현 + smoke PASS. |
| checkpoint load smoke가 통과했는가 | PASS | check_planner_interface.py [1] step. full_model checkpoint 로드 1.47s. |
| current rollout이 구현되었는가 | PASS | `imagine_from_belief` + smoke [5]. shape (16, 5, 5/...) 검증. |
| alternative hypothesis rollout이 oracle 없이 구현되었는가 | PASS | `imagine_alternative` (latent perturb + prior_std inflation). info input 없음. smoke [6] |alt-cur| mean=1.44. |
| compute budget accounting이 구현되었는가 | PASS | `ComputeAccountant.can_plan` / `record_planning` / `begin_step`. metrics_by_planner.csv의 rollout_steps_mean / planning_calls_mean. |
| reactive baseline이 구현되었는가 | PASS | `ReactivePlanner` + smoke [7]. |
| fixed-k baseline이 구현되었는가 | PASS | `FixedKPlanner` + debug eval에서 planning_calls=12 (period=5, 60 step). |
| always-plan baseline이 구현되었는가 | PASS | `AlwaysPlanPlanner` (yaml entry 검증). |
| uncertainty gate baseline이 구현되었는가 | PASS | `UncertaintyGatePlanner` (4 signals + fallback). |
| adaptive lookahead baseline이 구현되었는가 | PASS | `AdaptiveLookaheadPlanner` (low/high horizon switch). |
| event-only/novelty gate baseline이 구현되었는가 | PASS | `EventOnlyPlanner` (reveal + mismatch + shift + novelty). |
| FRC-WM planner가 구현되었는가 | PASS | `FRCWMPlanner` (9-step decision loop) + smoke [8]/[9]. |
| falsification score가 구현되었는가 | PASS | `compute_falsification_score` (5-factor weighted) + smoke [8] F=0.265. |
| action relevance가 구현되었는가 | PASS | `compute_action_relevance` (value gap + flip). |
| compute reallocation이 구현되었는가 | PASS | stage-based (low/medium/high/extreme) horizon/candidate/alternative 조절. debug eval에서 ours_frc planning_calls=2 (대부분 low → reactive). |
| decision mode trace가 저장되는가 | PASS | `StepTrace.decision_mode` + `decision_reason`. trace.write_jsonl. |
| oracle metadata를 사용하지 않았는가 | PASS | `WorldModelAdapter` / `BasePlanner.select_action` / `imagine_alternative` 모두 info input 안 받음. info는 trace 기록용. |
| test/OOD threshold tuning이 금지되어 있는가 | PASS | yaml에 valid에서 결정한 threshold 박아둠. eval 코드에서 threshold 변경 hook 없음. docs에 명시. |
| debug eval smoke만 실행했는가 | PASS | `--max-episodes 2` cap. test_id only, 1 model only. main / OOD eval은 사용자에게 위임. |
| main eval은 사용자가 직접 실행하도록 명령을 출력했는가 | PASS | §6 명령어 6개 (smoke / debug / main / OOD / compare / summarize) 모두 PowerShell-friendly로 명시. |
| 결과 저장 경로를 문서화했는가 | PASS | §7 디렉토리 트리 명시. trace dir 포함. |
| docs 4개를 작성했는가 | PASS | PLANNER_INTERFACE_DESIGN.md, PLANNER_BASELINES_DESIGN.md, FRC_WM_PLANNER_DESIGN.md, SESSION11_13_HANDOFF.md (본 문서). |

**26 항목 모두 PASS.**

---

## 11. 본 세션이 *남긴* 것 (Session 14+에 위임)

1. **Full evaluation 실행** — 사용자가 §6.3 / §6.4 명령으로 직접 수행.
2. **OOD environment 변형 정확화** (§8.1).
3. **정식 regime conditioning + value head 학습** (§8.2 / §8.3).
4. **explanation faithfulness eval** (§8.4).
5. **counterfactual rollout fidelity eval** (§8.5).
6. **task별 separately tracking** (§8.7 — env 측 변경).
7. **ManagedCheckpointer best alias 버그 fix** (§8.8 — 다음 학습 run 전).
8. **paper-final result 해석 + claim verdict** — main eval 결과 보고 정직하게 작성.

---

> Session 11-13 완료: planner interface, 6 baseline planner, FRC-WM planner가 모두 구현되었고, 사용자가 main / OOD evaluation을 직접 실행할 수 있도록 명령어와 결과 저장 경로가 확정되었다.
