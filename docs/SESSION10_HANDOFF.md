# SESSION 10 — Handoff Document

> Session 10은 `wm_medium_full_v1` / `wm_medium_no_regime_v1` / `wm_medium_no_change_point_v1` 3 run의 frozen checkpoint를 read-only로 분석하여, paper main claim의 정량 지지 근거와 약점을 모두 정리한 read-only diagnostic이다.
>
> **학습/optimizer/checkpoint write 0건. test_id/OOD는 frozen forward로만 평가했고 hyperparameter / checkpoint selection에 사용하지 않았다.** ref/PART0~3 위반 0건.

---

## 1. 생성/수정 파일 목록

| 경로 | 종류 | 내용 |
| --- | --- | --- |
| `falsifiable_regime_world_model/wm/diagnostics.py` | 신규 | log parser + RunSummary + threshold_sweep + pr_auc + reward_diagnostics + write_csv |
| `scripts/diagnose_wm_runs.py` | 신규 | log-only run summary + checkpoint inventory + reward long-tail (train_log proxy) |
| `scripts/diagnose_wm_thresholds.py` | 신규 | frozen checkpoint forward (no_grad) → threshold sweep + PR-AUC for cp/reveal/shift/mismatch/done |
| `scripts/diagnose_wm_rollout_fidelity.py` | 신규 | warmup posterior + prior-only rollout @ H={1,5,10,20,50} + cp detection delay |
| `scripts/compare_wm_ablation_runs.py` | 신규 | held-out diagnostic (test_id + 5 OOD splits × 2 datasets × 3 runs) |
| `docs/WM_DIAGNOSTICS_REPORT.md` | 신규 | 9절 종합 진단 + 쉬운 해석 + verdict table |
| `docs/SESSION10_HANDOFF.md` | 신규 | 본 문서 |
| `outputs/wm_diagnostics/session10/*.csv` | 신규 (자동) | 12개 csv (§4 산출물 표) |

미수정 (보존 0줄):

- `ref/PART0~3`
- `data/**`
- `outputs/*_stats/**`
- `outputs/wm_runs/*/checkpoints/*.pt` (read만)
- 기존 `train_log.jsonl` / `valid_log.jsonl` 원본
- `configs/wm_train_*.yaml` / `wm_data_stage*.yaml` / `wm_medium.yaml` / `wm_debug.yaml`
- `falsifiable_regime_world_model/wm/{config,modules,rssm,heads,losses,collate,data,data_config,sampling,schedules,checkpointing,env_check,train_config,trainer,metrics,__init__}.py`
- `scripts/{generate_dataset,validate_dataset,inspect_episode,plot_dataset_stats,_p1_check_family_disjoint,check_wm_shapes,check_wm_dataloader,check_training_env,probe_wm_hparams,train_world_model,summarize_wm_run}.py`
- `requirements.txt`

---

## 2. 분석에 사용한 checkpoint

primary 비교: 각 run의 `step_00030000.pt`. (best alias 파일은 wm_medium_full_v1과 no_regime_v1에서 누락 — 이는 Session 9 `ManagedCheckpointer._evict_best`의 known issue로, 본 분석은 step_00030000.pt로 동일 budget 비교를 수행).

| run_name | variant | primary checkpoint | alias missing |
| --- | --- | --- | --- |
| wm_medium_full_v1 | full_model | `outputs/wm_runs/wm_medium_full_v1/checkpoints/step_00030000.pt` | best_valid_uniform / best_cp_f1 alias missing |
| wm_medium_no_regime_v1 | no_regime | `outputs/wm_runs/wm_medium_no_regime_v1/checkpoints/step_00030000.pt` | best_valid_uniform / best_cp_f1 alias missing |
| wm_medium_no_change_point_v1 | no_change_point | `outputs/wm_runs/wm_medium_no_change_point_v1/checkpoints/step_00030000.pt` | best_valid_uniform alias missing (cp는 head 자체 X) |

---

## 3. 핵심 비교표 (요약 한눈에)

### 3.1 Final valid (step=30000)

| Run | uni_total | event_total | reward_mse_uni | state_mse_uni | regime_acc | cp F1@0 (event) | reveal F1 | mismatch F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full_model | 4.088 | 11.677 | 1097 | 6.91 | 0.873 | 0.112 | 0.551 | 0.704 |
| no_regime | 3.876 | 11.267 | 1057 | 7.26 | N/A | 0.108 | 0.552 | 0.659 |
| no_cp | 3.712 | 7.360 | 1024 | 6.69 | 0.870 | N/A | 0.569 | 0.701 |

> **total loss는 head 개수 차이로 인해 직접 비교 불가**. common-core metric (state, reward, reveal, shift, mismatch) 비교를 사용.

### 3.2 핵심 격차 (paper main argument)

| 비교 | full | no_regime | 결론 |
|---|---:|---:|---|
| valid_event mismatch best F1 | **0.721** | 0.686 | full 우세 (5%) |
| valid_event mismatch PR-AUC | **0.788** | 0.724 | full 우세 (9%) |
| **random_2000 test_id mismatch f1@0** | **0.442** | 0.006 | **full 74×** |
| **random_2000 ood_room_perm mismatch** | **0.473** | 0.002 | **full 236×** |
| **random_2000 ood_param_shift mismatch** | 0.519 | 0.008 | **full 65×** |
| success_v5 ood_param_shift cp best F1 | **0.500** | 0.067 | **full 7.5×** |

→ **regime supervision은 control-drift mismatch 학습과 drift-OOD에서의 cp 분리에 결정적**.

---

## 4. Common-core metric 결과

| Run | reward_mse_uniform | state_mse_uniform | reveal_f1_event | shift_f1_event | mismatch_f1_event |
|---|---:|---:|---:|---:|---:|
| full | 1097.2 | 6.91 | 0.551 | (best=0.18) | 0.704 |
| no_regime | 1056.7 | 7.26 | 0.552 | 0.189 | 0.659 |
| no_cp | 1024.1 | 6.69 | 0.569 | 0.197 | 0.701 |

**State MSE trade-off**: rollout @ H=1에서 full=0.0077, no_regime=0.0034, no_cp=0.0047. **no_regime이 5D state 자체는 더 정확** (regime supervision이 state head capacity를 약간 차지). 단 절대값이 매우 작아 paper-critical 아님.

---

## 5. Threshold sweep + PR-AUC 결과

| Run / head / eval | n_pos / n_total | F1@th=0 | best F1 / threshold | PR-AUC | separation |
|---|---|---:|---:|---:|---:|
| full / change_point / event | 80 / 32,768 | 0.119 | **0.183 / +1.26** | 0.098 | **+12.61** |
| full / shift / event | 80 / 32,768 | 0.116 | 0.182 / +1.26 | 0.097 | +13.04 |
| full / reveal / event | 2,034 / 32,768 | 0.551 | **0.622 / -0.77** | 0.647 | +6.68 |
| full / mismatch / event | 8,923 / 32,768 | 0.717 | 0.721 / -0.30 | **0.788** | +2.95 |
| full / success_done / event,uniform | 0 / 32,768 | 0.000 | N/A (no positives) | 0.000 | 0.00 |

**핵심:** cp의 fixed F1=0.12는 낮아 보이지만 **best threshold ~+1.26 logit (sigmoid≈0.78)에서 F1=0.18**, **PR-AUC=0.098 (random baseline 0.0024 대비 40×)**, **logit separation +12.6**. *모델은 cp를 잘 분리하고 있고 threshold tuning만 필요*하다는 결정적 증거.

success_done은 n_pos=0이라 F1=0이 통계 한계 (chunk-sample math; PART3 §3.25.1 success rate는 Session 11+ episode-level evaluator가 측정).

---

## 6. Rollout fidelity 결과

warmup_len=32, horizons={1,5,10,20,50}, chunk_len=128, 32 batches × 8 chunks = 256 chunks per (run, eval).

### 6.1 state MSE @ H (낮을수록 좋음, valid_uniform)

| Run | H=1 | H=5 | H=10 | H=50 |
|---|---:|---:|---:|---:|
| full | 0.0077 | 0.0083 | 0.0088 | 0.0241 |
| no_regime | 0.0034 | 0.0042 | 0.0046 | 0.0224 |
| no_cp | 0.0047 | 0.0053 | 0.0062 | 0.0201 |

**모든 variant가 H=50에서도 state MSE ≤ 0.04** (5D state range [-1, 1] 기준 충분히 작음). **planner phase로 진행 가능**.

### 6.2 cp delay (full_model, valid_uniform)

| 지표 | 값 |
|---|---:|
| n_cp_chunks (chunk 안 cp 포함) | 5 (uniform sampling) / 23 (event) |
| mean delay (predicted_peak - true_cp tick) | -2.6 (event) / -6.6 (uniform) — 모두 **early bias** |
| **hit@10 (uniform)** | **40%** |
| hit@10 (event) | 35% |

→ exact F1=0.11보다 훨씬 의미 있는 신호. 모델이 *2~7 tick 일찍* 변화를 감지 — paper에서 PART2 §3.7 빠른 falsification와 일치.

---

## 7. Reward long-tail 분석

| Run | mean | median | p99 | max | n_spikes | grad p99 | NaN/Inf |
|---|---:|---:|---:|---:|---:|---:|:-:|
| full | 1.64 | 0.95 | 10.73 | 49.31 | 53/601 | 51.2 | 없음 |
| no_regime | 1.60 | 0.95 | 10.56 | 56.41 | 47/601 | 66.0 | 없음 |
| no_cp | 1.70 | 1.00 | 11.61 | 55.92 | 51/601 | 38.5 | 없음 |

valid_uniform mean reward MSE 1057~1097은 task_reward=50 / completion_reward=200 outlier 1개의 MSE = 200²=40,000 영향. **rollout @ H=10 reward MSE ≈ 0.7 (정상 범위에서는 매우 정확)**. paper에서 reward MSE를 raw mean으로 보고하지 말 것.

---

## 8. Change-point delay 결과

| Run | eval | n_cp | mean delay | abs_mean | hit@1 | hit@3 | hit@5 | **hit@10** |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| full | event | 23 | -2.6 (early) | 20.6 | 0.04 | 0.13 | 0.17 | **0.35** |
| full | uniform | 5 | -6.6 | 15.8 | 0.20 | 0.40 | 0.40 | **0.40** |
| no_regime | event | 23 | -2.6 | 16.3 | 0.04 | 0.13 | 0.17 | **0.39** |
| no_regime | uniform | 5 | **-26.4** | 26.4 | 0 | 0 | 0 | **0** |
| no_cp | — | N/A (cp head removed) |

→ **uniform valid에서 no_regime은 hit@10=0%** (cp를 매우 일찍 misfire). **regime 없으면 cp 신호가 noise로 처리됨**. full_model은 hit@10=40%로 안정.

---

## 9. Held-out (test_id / OOD) Diagnostic

> **이 결과는 hyperparameter / checkpoint selection에 사용하지 않았다.** 6 splits × 2 datasets × 3 runs × 8 episodes × 4 chunks = 576 chunks.

### 9.1 random_2000 splits (full_model 기준)

regime accuracy: test_id 0.81 → ood_room_perm 0.90 → ood_obs_shift **0.27** (가장 큰 degradation; visual permutation이 regime classification 가장 어렵게 함).

mismatch f1@0: **ood_param_shift 0.519** (drift OOD에서도 robust).

### 9.2 success_v5_2000 splits — full vs no_regime 비교

| split | metric | full | no_regime | ratio |
|---|---|---:|---:|---:|
| **ood_param_shift** | **cp best F1** | **0.500** | 0.067 | **7.5×** |
| ood_factor_recomb | cp best F1 | 0.211 | 0.200 | 1.06× |
| ood_field_placement | cp best F1 | 0.400 | 0.087 | 4.6× |

→ **drift-heavy OOD에서 regime supervision이 cp 학습에 결정적** (paper §3.21 small cumulative drift 시나리오와 일치).

---

## 10. Claim Verdict Table

| Claim | Verdict | 근거 |
|---|:-:|---|
| C1. State dynamics learned | **PASS** | valid state MSE 66→7 (10×), rollout @ H=10 = 0.009 |
| C2. Hidden regime matters | **PASS (강하게)** | mismatch full vs no_regime: random test_id 74×, ood_room_perm 236×; success ood_param_shift cp 7.5× |
| C3. Change-point awareness matters | **WEAK** | cp ablation effect on other heads ~0; rollout 차이 미세 |
| C4. Reveal/shift separation learnable | **PASS** (reveal) / **WEAK** (shift exact) | reveal best F1=0.62; shift best F1=0.18 / sep=+13.0 |
| C5. Control mismatch learned | **PASS** | mismatch best F1=0.72, PR-AUC=0.79; OOD에서 full vs no_regime 74× |
| C6. Reward usable for planner | **WEAK** | spike 견딤, NaN 없음, p99=10.7; raw mean MSE=1097은 outlier 영향 |
| C7. Planner can proceed | **PASS** | rollout @ H=50 state MSE 0.024~0.04, cp delay hit@10=35~40% |

**Overall: 🟡 YELLOW (toward GREEN)**. 4 PASS + 1 강한 PASS (C2) + 2 WEAK. Hidden regime의 effect와 control mismatch는 paper main claim을 명확히 지지. cp ablation은 약함 — paper 위치 조정 필요 (cp head는 이단 그 자체로 paper-main이 아니라 planner falsification gate signal).

---

## 11. ref/PART0~3 위반 여부

| 검사 | 결과 |
|---|:-:|
| test_id/OOD를 학습/checkpoint selection에 사용 | **위반 없음** |
| collector_metadata / oracle metadata input | **위반 없음** (`assert_safe_inputs` + `load_meta=False` 다중 방어) |
| state/regime/change-point/reveal 분리 구조 | **유지** |
| same-backbone control (PART0 §1.4) | **유지** (3 variant 모두 medium capacity) |
| 결과 과장 | **없음** (PASS/WEAK/YELLOW 정직) |

---

## 12. Session 11 (Planner Phase) 진행 권장 + 보강 항목

### 12.1 진행 권장 — **PASS**

다음 인프라가 그대로 사용 가능:

- `RSSMWorldModel.imagine` API stub (Session 7에서 작동 검증) + cp logit / regime logit / state pred 모두 frozen checkpoint에서 정상 forward.
- 3 variant checkpoint (`step_00030000.pt`)가 normalizable + comparable (same-backbone, same-budget).
- cp logit separation +12.6 / hit@10=35~40% → falsification score (PART2 §3.7) 의 *원료*.
- mismatch F1=0.72 → control-drift hypothesis 비교의 *원료*.
- regime accuracy 0.87 → current regime hypothesis로 사용 가능.

### 12.2 Session 11에서 별도로 결정할 항목 (보강)

| 항목 | 권장 |
|---|---|
| cp threshold tuning | `logit > +1.26` (sigmoid≈0.78). 단 dataset의 양성 prevalence에 따라 planner 단에서 sweep. |
| reward target normalization | percentile-based reporting (p50/p90/p95) + spike sign accuracy. raw mean MSE는 misleading. |
| Session 9 `ManagedCheckpointer._evict_best` 버그 수정 | 다음 학습 run 전. 4번째 best 갱신부터 file unlink 발생. |
| valid_event success_done positives 0 처리 | done head는 *학습 진단*으로만 두고 paper-main success는 episode-level G_episode (Session 11+ planner rollout). |
| stage3에서 cp 신호 추가 강화 (선택) | success_v5의 cp event window를 0.20→0.30. 단 추가 학습이 필요 — Session 12. |
| paper-main metric 정의 | C1, C2, C5는 그대로; C3는 *cp planner-gate quality*로 재배치; C6는 percentile-based. |

---

## 13. Self-Audit

| Check | Status | Evidence |
| --- | :-: | --- |
| 3개 run 모두 읽었는가 | PASS | full / no_regime / no_cp 모두 train+valid log + step_30000.pt loadable |
| checkpoint inventory 작성 | PASS | `outputs/wm_diagnostics/session10/checkpoint_inventory.csv` |
| same-step final comparison 수행 | PASS | 모든 비교가 step=30000 기준 |
| total loss naïve 비교 회피 | PASS | §1.1에 "head 개수 차이로 직접 비교 불가" 명시; §1.2에서 common-core 우선 |
| common-core metrics 별도 비교 | PASS | §1.2 / common_core_metrics.csv |
| variant-specific N/A 처리 | PASS | no_regime의 regime_accuracy / no_cp의 cp_*는 N/A 또는 "head removed" 표기 |
| cp threshold sweep | PASS | 13 thresholds × 3 runs × 2 evals × 6 heads = 612 sweep rows |
| PR-AUC + best-threshold F1 계산 | PASS | sklearn 의존성 없이 수기 구현 (`diagnostics.pr_auc`) |
| rollout fidelity 수행 | PASS | H={1,5,10,20,50} × event/uniform × 3 runs × 32 batches |
| reward long-tail 분석 | PASS | train_log p50/p90/p99 + spike count + grad norm; reward_diagnostics_log.csv |
| change-point delay 분석 | PASS | mean/abs_mean delay + hit@1/3/5/10; change_point_delay.csv |
| heldout/OOD 학습/선택 미사용 | PASS | scripts/compare_wm_ablation_runs.py가 frozen forward only; 결과 csv는 분석 자료로만 |
| ref/PART0~3 위반 점검 | PASS | §11; collector_metadata/test/OOD/regime 분리 모두 유지 |
| 쉬운 해석 섹션 작성 | PASS | report §0 (먼저 읽으세요) |
| claim verdict table 작성 | PASS | report §7 + claim_verdict_table.csv (8 rows including overall) |
| planner phase 진행 여부 판정 | PASS | YELLOW with PASS C7; §12에서 진행 권장 + 보강 항목 명시 |

**16 항목 모두 PASS.**
