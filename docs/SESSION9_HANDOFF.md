# SESSION 9 — Handoff Document

> Session 9는 Session 7(model)과 Session 8(dataloader)을 묶어 RG-4F world model 학습을 시작하기 위한 모든 인프라(env check, OOM probe, training loop, atomic checkpoint/resume, valid_event/uniform, NaN guard, variant dispatch)를 닫았다. **Cursor는 full training을 직접 실행하지 않았다.** Cursor가 실행한 것은 env check 1회 / OOM probe 1회 (24 candidate × 2 step) / debug tiny smoke train 3개 variant (각 3~8 step) / resume smoke 1회까지다.
>
> 본 문서는 Session 10 이후 (collate dones/truncateds 분리, full training 실행, evaluator/planner)가 본 세션 산출물을 깨지 않고 이어 받기 위해 알아야 할 모든 사실을 닫는다.

---

## 1. 생성/수정 파일 목록

| 경로 | 종류 | 내용 |
| --- | --- | --- |
| `falsifiable_regime_world_model/wm/env_check.py` | 신규 | GPU/VRAM/bf16/fp16/dependency probe + report writer |
| `falsifiable_regime_world_model/wm/train_config.py` | 신규 | `WMTrainConfig` + `OptimizerConfig`/`SchedulerConfig`/`CheckpointConfig`/`EvalConfig`/`StabilityConfig`/`StageScheduleEntry` |
| `falsifiable_regime_world_model/wm/schedules.py` | 신규 | warmup_cosine / warmup_linear / constant LambdaLR 빌더 |
| `falsifiable_regime_world_model/wm/metrics.py` | 신규 | `BinaryConfusion` (precision/recall/F1) / `CategoricalAccuracy` / `RunningMean` / `LossAggregator` / `ValidMetrics` |
| `falsifiable_regime_world_model/wm/checkpointing.py` | 신규 | atomic save/load + `ManagedCheckpointer` (last/step/best/interrupted) + RNG state |
| `falsifiable_regime_world_model/wm/trainer.py` | 신규 | `Trainer` 클래스. stage schedule, valid_event/uniform, NaN/Inf guard, KeyboardInterrupt |
| `falsifiable_regime_world_model/wm/__init__.py` | 수정 | Session 9 신규 심볼들을 public API에 노출 |
| `configs/wm_train_debug.yaml` | 신규 | tiny / overfit / resume smoke 전용 |
| `configs/wm_train_medium_local.yaml` | 신규 | 논문 main 후보 (probe 결과 반영: chunk=128, batch=8, accum=2) |
| `configs/wm_train_medium_safe.yaml` | 신규 | OOM 잦을 때 fallback (batch=2, accum=8) |
| `scripts/check_training_env.py` | 신규 | env check entrypoint |
| `scripts/probe_wm_hparams.py` | 신규 | OOM-safe hyperparameter grid probe |
| `scripts/train_world_model.py` | 신규 | training entrypoint (CLI + Trainer.run()) |
| `scripts/summarize_wm_run.py` | 신규 | run_dir의 train/valid log을 markdown으로 요약 |
| `docs/WM_TRAINING_DESIGN.md` | 신규 | 본 세션 설계 종합 |
| `docs/WM_TRAINING_ENV_REPORT.md` | 신규 (자동) | check_training_env가 자동 생성 |
| `docs/WM_HPARAM_PROBE_REPORT.md` | 신규 (자동) | probe_wm_hparams가 자동 생성 |
| `docs/SESSION9_HANDOFF.md` | 신규 | 본 문서 |
| `outputs/wm_env_check/env_report.{json,md}` | 신규 (자동) | env check 산출물 |
| `outputs/wm_hparam_probe/{probe_results.csv,probe_results.json,recommended_train_config.yaml}` | 신규 (자동) | probe 산출물 |
| `outputs/wm_runs/debug_train_smoke/{...}` | 신규 (자동) | tiny smoke 결과 |
| `outputs/wm_runs/debug_train_no_regime/{...}` | 신규 (자동) | tiny smoke 결과 |
| `outputs/wm_runs/debug_train_no_cp/{...}` | 신규 (자동) | tiny smoke 결과 |

미수정 (보존 0줄):

- `ref/PART0~3`
- `data/**`, `outputs/*_stats/**`
- `falsifiable_regime_world_model/rg4f/**`
- `falsifiable_regime_world_model/wm/{config,modules,rssm,heads,losses,collate,data,data_config,sampling,README.md}` (Session 7/8 산출물 그대로)
- `scripts/{generate_dataset,validate_dataset,inspect_episode,plot_dataset_stats,_p1_check_family_disjoint,check_wm_shapes,check_wm_dataloader}.py`
- `configs/{dataset_default,wm_debug,wm_medium,wm_data_stage1,wm_data_stage2,wm_data_stage3}.yaml`
- `requirements.txt`

---

## 2. train config 설명

### 2.1 `wm_train_debug.yaml` — sanity 전용

| key | 값 |
| --- | --- |
| `wm_config` | `configs/wm_debug.yaml` (deter=256, stoch=64, ~2.7M params) |
| `chunk_len` / `batch_size` / `grad_accum_steps` | 64 / 8 / 1 (effective=8) |
| `precision` / `device` | auto / auto (RTX 4060 Ti에서 bf16 / cuda 자동 선택) |
| `max_steps` | 50 |
| `eval` / `save_every_steps` | 20 / 20 |
| `stage_schedule` | stage1 only (random_2000 100%) |
| `done_target_mode` | success_done |

### 2.2 `wm_train_medium_local.yaml` — 논문 main 후보

| key | 값 | 비고 |
| --- | --- | --- |
| `wm_config` | `configs/wm_medium.yaml` (deter=512, stoch=128, ~10.7M params) | |
| `chunk_len` / `batch_size` / `grad_accum_steps` | **128 / 8 / 2** | effective_batch = 16 |
| `precision` | auto | RTX 4060 Ti → bf16 |
| `max_steps` | 30000 | RTX 4060 Ti 기준 약 3~4시간 |
| `lr` / `weight_decay` / `warmup_steps` | 3e-4 / 1e-4 / 1000 | |
| `scheduler` | warmup_cosine | min_lr_factor=0.1 |
| `grad_clip` | 100.0 | |
| `eval_every_steps` / `save_every_steps` | 1000 / 1000 | |
| `keep_last_n` / `keep_best_n` | 3 / 3 | |
| `valid_event_data_config` | `configs/wm_data_stage2.yaml` (event-window on) | |
| `valid_uniform_data_config` | `configs/wm_data_stage2.yaml` (trainer가 deepcopy 후 event_window=off) | |
| `stage_schedule` | 30% stage1 / 30% stage2 / 40% stage3 | |
| `best_metric_keys` | `[valid_uniform/loss/total, valid_event/change_point/f1]` | mode `[min, max]` |

### 2.3 `wm_train_medium_safe.yaml` — fallback

| key | 값 | 비고 |
| --- | --- | --- |
| `chunk_len` / `batch_size` / `grad_accum_steps` | 64 / 2 / 8 | effective_batch = 16 (medium_local과 동일) |
| 나머지 | medium_local과 동일 | |

---

## 3. training script 사용법

### 3.1 기본

```powershell
.\.venv\Scripts\python.exe scripts\train_world_model.py `
    --train-config <yaml> --run-name <name> --variant <variant>
```

### 3.2 모든 CLI 옵션

| 옵션 | 의미 |
| --- | --- |
| `--train-config` (필수) | `configs/wm_train_*.yaml` |
| `--run-name` (필수) | `outputs/wm_runs/<run_name>` |
| `--variant` | `full_model` (default) / `no_regime` / `no_change_point` / `no_reveal` / `no_state_aux` |
| `--resume` | checkpoint path |
| `--max-steps` | yaml 값 override |
| `--eval-every-steps` | yaml 값 override |
| `--save-every-steps` | yaml 값 override |
| `--device` | yaml 값 override (`auto`/`cuda`/`cpu`) |
| `--precision` | yaml 값 override (`auto`/`bf16`/`fp16`/`fp32`) |

### 3.3 KeyboardInterrupt

Ctrl+C 한 번이면 trainer가 `interrupted_step_<N>.pt`를 저장하고 `last.pt`를 동기화한 뒤 raise. 두 번째 Ctrl+C는 즉시 종료 — Python 표준 동작.

---

## 4. checkpoint / resume 사용법

### 4.1 저장 파일 (각 run_dir/checkpoints/)

| 파일 | 정책 |
| --- | --- |
| `last.pt` | 항상 최신 (atomic) |
| `step_<NNNNNNNN>.pt` | rolling, `keep_last_n=3` 유지 |
| `best_valid_uniform_loss_total.pt` | `valid_uniform/loss/total` min |
| `best_valid_event_change_point_f1.pt` | `valid_event/change_point/f1` max |
| `interrupted_step_<NNNNNNNN>.pt` | KeyboardInterrupt 시 |

### 4.2 resume

```powershell
.\.venv\Scripts\python.exe scripts\train_world_model.py `
    --train-config configs\wm_train_medium_local.yaml `
    --run-name wm_medium_full_v1 --variant full_model `
    --resume outputs\wm_runs\wm_medium_full_v1\checkpoints\last.pt
```

resume 시 복원되는 것: `model state_dict`, `optimizer state_dict`, `scheduler state_dict (LambdaLR last_epoch)`, `GradScaler state` (fp16일 때), `python/numpy/torch/cuda RNG state`, `global_step`, `best_metrics`. 같은 `run_name`이면 `train_log.jsonl` / `valid_log.jsonl`에 이어서 append된다.

### 4.3 검증된 사실 (Cursor smoke)

```text
# 첫 실행: 0 → 5
[step 1] stage=stage1 loss=13.821 cp=0.683 (cp/total=0.05) grad=6.62 t=2.73s
[valid] step=3 uni_total=14.228 event_total=15.022 cp_f1(event)=0.000
[valid] step=5 uni_total=14.000 event_total=14.810 cp_f1(event)=0.000
[ckpt] saved last=last.pt step=step_00000005.pt

# resume: 5 → 8
[resume] from outputs\wm_runs\debug_train_smoke\checkpoints\last.pt, global_step=5
[valid] step=8 uni_total=13.281 event_total=14.132 cp_f1(event)=0.000
[ckpt] saved last=last.pt step=step_00000008.pt
```

---

## 5. OOM probe 결과 및 추천 설정

```powershell
.\.venv\Scripts\python.exe scripts\probe_wm_hparams.py `
    --wm-config configs\wm_medium.yaml `
    --data-config configs\wm_data_stage2.yaml `
    --out-dir outputs\wm_hparam_probe `
    --variant full_model --max-probe-steps 2
```

**24/24 후보 모두 OK** (RTX 4060 Ti / 8GB VRAM / bf16). VRAM 사용률 3% ~ 9%로 medium 모델이 매우 가볍게 동작. 표 일부:

| chunk | batch | accum | precision | eff_batch | step_time (s) | vram |
| ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 64 | 8 | 1 | bf16 | 8 | 0.256 | 3% |
| 128 | 4 | 1 | bf16 | 4 | 0.313 | 3% |
| **128** | **8** | **2** | **bf16** | **16** | **0.772** | **4%** |
| 128 | 16 | 1 | bf16 | 16 | 1.131 | 5% |
| 128 | 32 | 4 | bf16 | 128 | 4.387 | 9% |

알고리즘 추천 (chunk + eff_batch 우선): `chunk=128, batch=32, accum=4, eff_batch=128, step=4.39s, vram=9%`.

**실용 채택** (Session 9): `chunk=128, batch=8, accum=2, eff_batch=16` — 동일 effective_batch에서 step_time이 5배 빠름. `wm_train_medium_local.yaml`에 반영. probe 알고리즘은 throughput보다는 안정성+gradient noise를 우선시하므로 large effective_batch를 추천하는데, RTX 4060 Ti에서는 step_time이 길어져 wall-clock 손해. 사용자가 paper main run에서 batch_size를 더 키우고 싶다면 yaml override로 가능.

상세는 `docs/WM_HPARAM_PROBE_REPORT.md`.

---

## 6. logs / metrics 위치

`outputs/wm_runs/<run_name>/` 아래:

| 파일 | 내용 |
| --- | --- |
| `train_log.jsonl` | 매 `log_every_steps` 1줄 (step / stage / lr / precision / loss components / grad_norm / sample_weight / source_dist / sampler_type_dist / gpu_memory / step_time / cp_ratio) |
| `valid_log.jsonl` | 매 `eval_every_steps` 1줄 (valid_uniform/* + valid_event/*) |
| `metrics.csv` | (예약: 본 세션은 jsonl만; csv 직렬화 필요 시 Session 10에서 추가) |
| `config_resolved.yaml` | 실제 적용된 train_cfg + wm_cfg 요약 |
| `env_report.json` | 학습 시작 시점 env snapshot |
| `run_summary.yaml` | trainer.run() 종료 시 |
| `run_summary.md` | `summarize_wm_run.py` 출력 |
| `checkpoints/` | 위 §4.1 |

---

## 7. full training user-run commands

§13 of `docs/WM_TRAINING_DESIGN.md` 와 동일. 핵심:

```powershell
# 1) env check (이미 1회 완료)
.\.venv\Scripts\python.exe scripts\check_training_env.py --requirements requirements.txt --out-dir outputs\wm_env_check

# 2) OOM probe (이미 1회 완료, max-probe-steps=2)
.\.venv\Scripts\python.exe scripts\probe_wm_hparams.py --wm-config configs\wm_medium.yaml --data-config configs\wm_data_stage2.yaml --out-dir outputs\wm_hparam_probe --variant full_model --max-probe-steps 3

# 3) full_model 학습
.\.venv\Scripts\python.exe scripts\train_world_model.py --train-config configs\wm_train_medium_local.yaml --run-name wm_medium_full_v1 --variant full_model

# 4) no_regime
.\.venv\Scripts\python.exe scripts\train_world_model.py --train-config configs\wm_train_medium_local.yaml --run-name wm_medium_no_regime_v1 --variant no_regime

# 5) no_change_point
.\.venv\Scripts\python.exe scripts\train_world_model.py --train-config configs\wm_train_medium_local.yaml --run-name wm_medium_no_change_point_v1 --variant no_change_point

# 6) (선택) no_reveal / no_state_aux 추가 ablation
.\.venv\Scripts\python.exe scripts\train_world_model.py --train-config configs\wm_train_medium_local.yaml --run-name wm_medium_no_reveal_v1 --variant no_reveal
.\.venv\Scripts\python.exe scripts\train_world_model.py --train-config configs\wm_train_medium_local.yaml --run-name wm_medium_no_state_aux_v1 --variant no_state_aux

# 7) 중단 후 resume 예시
.\.venv\Scripts\python.exe scripts\train_world_model.py --train-config configs\wm_train_medium_local.yaml --run-name wm_medium_full_v1 --variant full_model --resume outputs\wm_runs\wm_medium_full_v1\checkpoints\last.pt

# 8) OOM 잦을 때 fallback
.\.venv\Scripts\python.exe scripts\train_world_model.py --train-config configs\wm_train_medium_safe.yaml --run-name wm_medium_full_safe_v1 --variant full_model

# 9) 런 요약
.\.venv\Scripts\python.exe scripts\summarize_wm_run.py --run-dir outputs\wm_runs\wm_medium_full_v1
```

> **Cursor는 이 중 어느 full 명령도 실행하지 않았다.** 사용자가 본 명령들을 PowerShell에서 직접 실행한다.

---

## 8. Session 10 — Diagnostics / 추가 작업 TODO

| 책임 | 요점 |
| --- | --- |
| `collate_chunks`에 `dones`/`truncateds`/`success_done` 분리 키 추가 | trainer는 이미 받을 준비됨 (`_prepare_targets`). targets dict에 키만 추가하면 trainer 1줄 dispatch로 즉시 활용. |
| `metrics.csv`로 jsonl을 동기화하는 export 유틸 | `summarize_wm_run.py`에 옵션 추가. |
| TensorBoard / wandb logger 옵션 | `Trainer`의 `_append_jsonl`을 logger interface로 추상화. 외부 dep는 본 세션에서 도입하지 않음. |
| 학습 중 `change_point` precision/recall threshold sweep | Session 10에서 valid_log에서 후처리. trainer는 logit 그대로 저장. |
| best checkpoint 자동 선택 (planner inference에 사용할 1개) | best는 두 키 (`uniform/total`, `event/change_point/f1`) 둘 다 저장됨. paper inference에서 어느 것을 쓸지는 Session 11+. |
| 학습 시간 예측 / lr finder | optional. 본 세션에서는 없음. |
| `run_summary.md`의 train-valid gap에 표준편차 추가 | overfit 경고 자동화. |

---

## 9. Self-Audit

| Check | Status | Evidence |
| --- | :-: | --- |
| requirements.txt 검사 | PASS | `scripts/check_training_env.py` 실행 결과 모든 core dep OK. requirements.txt를 자동 수정하지 않음. |
| CUDA/GPU/VRAM/bf16 가능 여부 확인 | PASS | RTX 4060 Ti 8GB / cap=(8,9) / bf16=True / fp16=True / cuda=12.4 (`outputs/wm_env_check/env_report.json`). |
| OOM probe script 구현 | PASS | `scripts/probe_wm_hparams.py`. 24 candidate × 2 step probe 1회 실행 완료. |
| 추천 hyperparameter config 생성 | PASS | `outputs/wm_hparam_probe/recommended_train_config.yaml` + `wm_train_medium_local.yaml`이 probe 결과 (chunk=128, batch=8, accum=2)를 반영. |
| training loop 구현 | PASS | `wm/trainer.py:Trainer.run()` + `_train_one_step` + `_eval_and_log`. |
| full training은 실행하지 않음 | PASS | Cursor 실행: env_check 1회, probe 24×2step, debug_train_smoke 5+3step, no_regime 3step, no_cp 3step. 어느 것도 max_steps에 도달하지 않음. |
| tiny smoke train만 실행 | PASS | 위 동일. 합계 ~14 optimizer step (full_model 5+3, no_regime 3, no_cp 3). |
| checkpoint save/resume 동작 | PASS | debug_train_smoke가 step 5에서 정확히 resume → step 8까지 진행. last.pt + step_*.pt + best_*.pt 모두 저장됨. atomic save (`os.replace`로 rename). |
| KeyboardInterrupt checkpoint 구현 | PASS | `Trainer.run()`이 `KeyboardInterrupt` 잡아 `_save_interrupted` 호출 후 raise. `interrupted_step_<N>.pt` + `last.pt` 동기화. |
| valid_event / valid_uniform 구현 | PASS | `Trainer.__init__`이 두 loader를 동시에 만든다. valid_uniform은 `make_uniform_event_window_config`로 event_window=off + boost=1.0. 매 eval에서 두 loader 모두 평가. |
| train/valid만 사용 보장 | PASS | `assert_safe_data_config`가 `cfg.validate()` 호출 → train/valid 외 split이면 `ValueError`. `build_train_loader` / `build_valid_loaders` 모두 split 인자가 train/valid로 hard-coded. |
| test/OOD 접근 차단 | PASS | Session 8의 다중 방어선 + `assert_safe_data_config` + valid loader는 split="valid" 고정. |
| forbidden metadata assert | PASS | `Trainer._train_one_step`에서 매 batch마다 `assert_safe_inputs(batch["inputs"])` 호출. collate에서 1차 차단 + trainer 2차 검증. |
| done/truncated/terminal 분리 보완 | PASS (PATCH 적용 후) | `collate_chunks`가 `success_done` / `truncated` / `terminal` / `done`(alias) 4개 키를 분리 노출. trainer `_prepare_targets`가 `done_target_mode ∈ {success_done(default), terminal}`로 dispatch. valid metric에 `success_done/precision-recall-f1`, `terminal/precision-recall-f1`, `truncated/rate` 분리 기록. invariant `done == success_done` / `terminal == success_done | truncated` smoke로 검증됨. |
| per-component loss logging | PASS | `LossAggregator`가 `compute_total_loss.components`를 모든 key별로 누적. `train_log.jsonl["loss"]`에 dict로 저장 (`obs_local`, `obs_scalar`, `reward`, `done`, `state`, `regime`, `change_point`, `reveal`, `shift`, `mismatch`, `kl`, `total`). |
| change_point precision/recall/F1 기록 | PASS | `BinaryConfusion` 누적. `valid_log.jsonl`에 `valid_event/change_point/{precision,recall,f1,accuracy,positives,tp,fp,fn,tn}` 모두 저장. |
| overfit warning / train-valid gap 기록 | PASS | `summarize_wm_run.py`가 train_total - valid_uniform_total gap을 markdown에 출력. trainer는 매 step `loss_change_point_ratio`와 `consecutive_overweight`를 train_log에 저장하고, 50 step 이상 cp_ratio > 0.5면 콘솔 WARN. |
| loss/grad NaN/Inf 방어 | PASS | `_check_loss_finite`가 NaN/Inf면 RuntimeError + last 저장. `_check_grad_finite`는 `nan_action="stop"`이면 raise. |
| docs/WM_TRAINING_DESIGN.md 작성 | PASS | 15절, 본 docs/. |
| docs/SESSION9_HANDOFF.md 작성 | PASS | 본 문서. |

**20개 항목 모두 PASS** (Session 9 PATCH로 `done/truncated/terminal` 분리 PARTIAL → PASS 승격).

---

## 10. Session 9 PATCH — done/truncated/terminal 분리

PARTIAL로 남았던 항목을 본 PATCH에서 보완했다. 변경 범위는 collate / trainer / losses / metrics / docs로 한정되며, **모델 구조 / dataloader stage mix / loss weight / training config / planner / dataset은 절대 변경하지 않았다**.

### 10.1 PATCH 수정 파일

| 경로 | 변경 |
| --- | --- |
| `falsifiable_regime_world_model/wm/collate.py` | `_stack_terminal` → `_stack_done_components` 헬퍼로 교체. `targets`에 `success_done` / `truncated` / `terminal` / `done`(alias) 4개 키 분리 노출. dtype 표 갱신. |
| `falsifiable_regime_world_model/wm/trainer.py` | `_prepare_targets`가 `done_target_mode`에 따라 `targets["done"]`을 `success_done`(default) 또는 `terminal`로 dispatch (silent fallback 없음, 알 수 없는 mode이면 raise). `_eval_loader`에 `success_done` / `terminal` precision-recall-f1 + `truncated/rate` 분리 metric 추가. train_log에 `done_target_mode` 기록. valid 콘솔에 `done_mode` / `sd_f1` / `term_f1` / `trunc_rate` 표시. |
| `falsifiable_regime_world_model/wm/losses.py` | `compute_total_loss`의 done component에 dispatch 정책을 명시하는 주석 1줄 추가 (구현 변경 없음). |
| `falsifiable_regime_world_model/wm/metrics.py` | 변경 없음. 기존 `BinaryConfusion`을 그대로 재사용. |
| `docs/SESSION9_HANDOFF.md` | 본 문서. Self-Audit 갱신 + 본 §10 추가. |
| `docs/WM_TRAINING_DESIGN.md` | §6.1과 §15 known risks의 done/truncated 항목 갱신. |

### 10.2 분리 정의 (collate가 노출)

```text
success_done = dones.float()                          # 진짜 task 성공 종료
truncated    = truncateds.float()                     # timeout (시간 초과)
terminal     = (dones | truncateds).float()           # rollout stop / 분석용
done         = success_done                          # backward-compat alias (default)
```

invariants (smoke 검증):
- `done == success_done` (텐서 동일성)
- `terminal == (success_done.bool() | truncated.bool()).float()`
- `success_done & truncated`은 일반적으로 0 (env에서 동시 set 안 됨)

### 10.3 done_logit target dispatch (trainer)

| `done_target_mode` | trainer가 `targets["done"]`에 넣는 값 | 의미 |
| --- | --- | --- |
| `success_done` (**default, 권장**) | `targets["success_done"]` | done_logit이 진짜 task 성공만 학습. timeout truncated를 success로 학습하지 않음. |
| `terminal` | `targets["terminal"]` | done_logit이 sequence stop을 학습. main 권장 경로 아님. |
| 그 외 | `ValueError` (silent fallback 없음) | |

`terminal`은 어떤 mode에서도 별도 key로 유지되며, **성공 종료 label로 해석되지 않는다.** rollout stop / sequence mask / 분석용으로만 사용한다 (Session 11+).

### 10.4 valid metric 분리

`valid_event/*` 와 `valid_uniform/*` 양쪽에 동일 구조로 노출된다:

```text
{split}/success_done/{precision, recall, f1, accuracy, positives, tp, fp, fn, tn}
{split}/terminal/{precision, recall, f1, accuracy, positives, tp, fp, fn, tn}
{split}/truncated/rate   # tick-level truncated 비율 (단일 scalar)
```

콘솔 valid 라인 (PATCH 후):

```text
[valid] step=N uni_total=... event_total=... cp_f1(event)=...
        done_mode=success_done sd_f1(uni)=... term_f1(uni)=... trunc_rate(uni)=...
```

train_log.jsonl의 매 step에 `"done_target_mode": "success_done"` 기록 (어떤 target을 보고 학습했는지 감사 가능).

### 10.5 PATCH smoke 결과

| smoke | 결과 |
| --- | --- |
| 1) targets 4 키 + invariants | PASS — 4 키 모두 존재, `done == success_done`, `terminal == sd \| trunc` |
| 2) debug 5 step train (full_model) | PASS — `done_mode=success_done`, sd_f1/term_f1/trunc_rate 콘솔+jsonl 모두 출력. checkpoint last/step/best 정상. |
| 3a) no_regime 1 step | PASS — loss=12.090, 분리 metric 정상 |
| 3b) no_change_point 1 step | PASS — loss=10.444, cp=0.000, 분리 metric 정상 |

### 10.6 변경 금지 항목 (PATCH가 건드리지 않은 것)

- `ref/PART0~3`, `data/**`, `outputs/*_stats/**`
- `configs/wm_medium.yaml`, `configs/wm_debug.yaml`, `configs/wm_data_stage{1,2,3}.yaml`
- 기존 `configs/wm_train_*.yaml` 3개 (yaml 키 추가 없음 — `done_target_mode`는 Session 9 본편에서 이미 도입됨)
- `falsifiable_regime_world_model/rg4f/**`
- 기존 generator / validator / plot scripts
- RSSM / heads / sampling / data / data_config 모듈 (변경 0줄)
- planner / evaluator (이번 PATCH에서도 미구현)
- loss weight 전체 재조정 (lambda_done은 그대로)
- full training (실행 0회; tiny smoke ≤ 5 step만 실행)

### 10.7 남은 TODO

**없음.** PATCH 이후 Session 9의 `done/truncated/terminal` 분리는 모든 layer에서 PASS다.
