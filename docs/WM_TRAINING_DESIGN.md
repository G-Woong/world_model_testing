# WM Training Design — RG-4F World Model Training Loop (Session 9)

> **Session 9 산출물.** Session 7에서 만든 RSSM/Dreamer-style world model과 Session 8의 dataloader를 연결하는 training loop, OOM-safe hyperparameter probe, atomic checkpoint/resume, 그리고 valid_event/valid_uniform 두 가지 일반화 모니터링까지 닫는다.
>
> **본 문서의 가장 중요한 정책: Cursor는 full training을 실행하지 않았다.** Cursor는 environment check, OOM probe, tiny smoke train (≤ 8 step), checkpoint/resume smoke까지만 수행했다. `full_model` / `no_regime` / `no_change_point` 본 학습은 §13의 명령어를 사용자가 PowerShell에서 직접 실행한다.

---

## 1. Session 9의 목적

| 책임 | 본 문서가 닫는 위치 |
| --- | --- |
| requirements / GPU / VRAM / bf16 / fp16 환경 점검 | §2, §3 |
| OOM-safe hyperparameter probe (batch / chunk / accum / precision) | §4, §5 |
| training loop (forward → loss → backward → step + log) | §6 |
| stage schedule (random_2000 → 50:50 → 30:70) | §7 |
| valid_event / valid_uniform 두 평가 path | §8 |
| atomic checkpoint / resume / best / interrupted | §9 |
| overfit / generalization / sample_weight 과강조 모니터링 | §10, §11 |
| variant 학습 (full_model / no_regime / no_change_point / no_reveal / no_state_aux) | §12 |
| 사용자 직접 실행 명령 | §13 |
| 출력물 저장 위치 | §14 |
| known risks / fallback | §15 |

---

## 2. requirements / env check 결과

```
python scripts\check_training_env.py --requirements requirements.txt --out-dir outputs\wm_env_check
```

`scripts/check_training_env.py`가 ``outputs/wm_env_check/env_report.{json,md}``와 ``docs/WM_TRAINING_ENV_REPORT.md``에 저장한다. 실측 결과 (Cursor가 본 세션에서 실행):

| 항목 | 값 |
| --- | --- |
| python | 3.11.9 |
| torch | 2.6.0+cu124 |
| GPU | NVIDIA GeForce RTX 4060 Ti, capability (8,9), VRAM 8.0 GB |
| bf16 supported | **True** |
| fp16 (AMP) supported | **True** |
| recommended_precision (auto) | **bf16** |
| recommended_device | **cuda** |
| core deps | torch / numpy / yaml / tqdm / pandas / matplotlib 모두 OK |
| optional deps | tensorboard, wandb 미설치 (학습에 필수 아님) |

> requirements.txt는 본 세션이 자동 수정하지 않았다. 필요 시 사용자가 직접 `pip install <missing>`. 누락된 핵심 dep 0개.

---

## 3. GPU / VRAM 감지 결과

`falsifiable_regime_world_model.wm.env_check.probe_gpu()`이 ``GPUStatus`` dataclass를 반환한다.

| 항목 | 값 |
| --- | --- |
| device_count | 1 |
| device_name | NVIDIA GeForce RTX 4060 Ti |
| capability | (8, 9) — Ada Lovelace |
| total VRAM | 8.0 GB |
| bf16 | True (Ada는 bf16 native) |
| fp16 AMP | True |
| CUDA runtime | 12.4 |

**해석**: capability 8.9 + 8GB VRAM. medium 모델(deter=512, stoch=128, ~10.7M param)은 충분히 GPU에 들어가지만, large 후보(deter=1024)는 VRAM 부족 가능성이 있다.

> `pick_precision(gpu, "auto")` 기본 동작: `bf16 ✓ → bf16`.

---

## 4. OOM probe 설계

`scripts/probe_wm_hparams.py`는 ``WMConfig`` (default `wm_medium.yaml`) + `WMDataConfig` (default `wm_data_stage2.yaml`)를 받아 다음 24개 후보를 1~3 step씩 forward+backward 시도한다:

```
chunk_len ∈ {64, 128}
batch_size ∈ {4, 8, 16, 32}
grad_accum_steps ∈ {1, 2, 4}
precision = pick_precision(gpu, "auto")
```

각 후보:
1. data loader / model / AdamW / (fp16면 GradScaler) 새로 생성.
2. ``--max-probe-steps`` 만큼 ``loss.backward() / clip_grad_norm_(100) / optimizer.step()``.
3. 각 step에서 loss/grad finite 여부, peak VRAM 추적.
4. ``torch.cuda.empty_cache()`` + ``gc.collect()``로 다음 후보 진입.

OOM 처리:
- ``torch.cuda.OutOfMemoryError`` / ``RuntimeError("out of memory")`` 모두 잡아 후보 실패로 기록.
- 다음 후보로 즉시 진행.

추천 알고리즘 (`pick_recommended`):
1. success ∧ loss/grad finite ∧ vram_ratio < 0.90 인 후보만 feasible.
2. (없으면 vram_ratio < 0.95까지 완화)
3. **chunk_len 큰 쪽 우선** (128 > 64) — temporal context 보존이 backbone supervision에 유리.
4. **effective_batch 큰 쪽 우선** — gradient noise 줄임.
5. step_time 짧은 쪽, vram_ratio 낮은 쪽.

### 4.1 실측 OOM probe 결과 (Cursor 실행)

```
python scripts\probe_wm_hparams.py --wm-config configs\wm_medium.yaml \
    --data-config configs\wm_data_stage2.yaml --out-dir outputs\wm_hparam_probe \
    --variant full_model --max-probe-steps 2
```

24/24 후보 **모두 OK** (VRAM 3% ~ 9%로 매우 여유). 추천:

```
chunk_len:        128
batch_size:       32
grad_accum_steps: 4
precision:        bf16
effective_batch:  128
step_time_sec:    4.39
vram_ratio:       9%
```

> 추천 알고리즘은 effective_batch와 chunk_len을 우선시하므로 step_time이 큰 후보를 고른다. **실용적 선택**: 동일한 effective_batch=16을 더 빠르게 만드는 ``chunk=128 batch=8 accum=2`` (step_time 0.77s, vram 4%)이 시간 효율이 더 좋다. 이를 ``configs/wm_train_medium_local.yaml`` 기본값으로 채택했다.

상세는 `docs/WM_HPARAM_PROBE_REPORT.md` (probe가 자동 생성).

---

## 5. recommended hyperparameter 선택

| config | chunk_len | batch_size | grad_accum_steps | effective_batch | precision | 용도 |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `wm_train_debug.yaml` | 64 | 8 | 1 | 8 | auto | sanity / overfit / resume smoke |
| `wm_train_medium_local.yaml` | **128** | **8** | **2** | **16** | auto | 본 paper main 후보 |
| `wm_train_medium_safe.yaml` | 64 | 2 | 8 | 16 | auto | OOM 잦을 때 fallback (effective batch 동일) |

> 본 yaml들은 probe가 만든 ``recommended_train_config.yaml``과 paper-friendly trade-off를 결합한 결과다. 사용자가 probe 결과를 본 후 `wm_train_medium_local.yaml`을 직접 override 가능.

---

## 6. Training loop 구조

`falsifiable_regime_world_model.wm.trainer.Trainer.run()`이 main loop. 흐름:

```
while global_step < max_steps:
    # 1. stage 결정 (global_step / max_steps 비율 기반)
    stage = train_cfg.stage_for_step(global_step)
    batch = next(stages[stage.name].iterator)

    # 2. forbidden key guard (collate에서 1차, trainer에서 2차)
    assert_safe_inputs(batch["inputs"])

    # 3. forward + loss
    inputs  = batch["inputs"]  → device
    targets = batch["targets"] → device  + done_target_mode 적용
    sw      = batch["sample_weight"] → device

    with autocast(precision):
        out = model(inputs)
        loss_out = compute_total_loss(out, targets, cfg.loss, sample_weight=sw)

    # 4. backward + grad accum
    (loss / accum).backward()      # accum 회 반복

    # 5. NaN/Inf check + grad_clip
    grad_norm = clip_grad_norm_(model.parameters(), cfg.stability.grad_clip)
    if not finite(grad_norm): raise / save_step

    # 6. optimizer + scheduler step
    if scaler: scaler.step(optimizer); scaler.update()
    else: optimizer.step()
    scheduler.step()

    # 7. log + 주기적 평가 + 주기적 checkpoint
    if step % log_every: append jsonl
    if step % eval_every: _eval_and_log()       # valid_event + valid_uniform
    if step % save_every: _save_step()          # last + step_<N> (rolling)
```

KeyboardInterrupt → ``_save_interrupted()`` 후 raise. NaN/Inf grad → ``_save_step()`` 후 RuntimeError.

### 6.1 done / truncated / terminal 분리 (PART2 reward decomp; Session 9 PATCH 적용)

`collate_chunks`가 다음 4개 키를 분리 노출한다:

| 키 | 정의 | 사용 |
| --- | --- | --- |
| `success_done` | `dones.float()` | 진짜 task 성공 종료. **default done_logit target.** |
| `truncated` | `truncateds.float()` | timeout. valid metric에서 `truncated/rate` 분석용. |
| `terminal` | `(dones \| truncateds).float()` | rollout stop / sequence mask / 분석용. **성공 라벨로 해석 금지.** |
| `done` | = `success_done` (alias) | backward compatibility. trainer가 mode에 따라 `success_done` 또는 `terminal`로 dispatch. |

Trainer `_prepare_targets`가 `WMTrainConfig.done_target_mode`에 따라 `targets["done"]`을 다음으로 dispatch:

- `done_target_mode = "success_done"` (**default, 권장**): `targets["done"] := targets["success_done"]`. world model의 `done_logit`이 진짜 task 성공만 학습한다 (timeout truncated를 success로 오해 학습하지 않게).
- `done_target_mode = "terminal"`: `targets["done"] := targets["terminal"]`. done_logit을 sequence stop 신호로 학습. 메인 권장 경로 아님.
- 그 외: `ValueError` (silent fallback 없음).

invariants (smoke로 검증):
- `done == success_done` (텐서 동일성, default 모드)
- `terminal == (success_done.bool() | truncated.bool()).float()`
- `success_done & truncated`는 일반적으로 0 (env가 동시 set 안 함)

valid metric 분리 (`valid_event/*` 와 `valid_uniform/*` 양쪽에 동일):

```text
{split}/success_done/{precision, recall, f1, accuracy, positives, tp, fp, fn, tn}
{split}/terminal/{precision, recall, f1, accuracy, positives, tp, fp, fn, tn}
{split}/truncated/rate   # tick-level truncated 비율
```

`train_log.jsonl`의 매 step에 `"done_target_mode": "..."` 기록 → 어떤 target을 학습했는지 감사 가능.

---

## 7. Stage schedule

`WMTrainConfig.stage_schedule`은 `List[StageScheduleEntry]`. 각 entry:

```
StageScheduleEntry(name, data_config, end_fraction)
# end_fraction은 누적 비율: global_step / max_steps <= end_fraction이면 이 stage.
```

`wm_train_medium_local.yaml` 기본값:
```yaml
stage_schedule:
  - {name: stage1, data_config: configs/wm_data_stage1.yaml, end_fraction: 0.30}  # 30%
  - {name: stage2, data_config: configs/wm_data_stage2.yaml, end_fraction: 0.60}  # 30%
  - {name: stage3, data_config: configs/wm_data_stage3.yaml, end_fraction: 1.00}  # 40%
```

Trainer는 stage entry별로 `RG4FChunkIterableDataset` + `DataLoader`를 사전 생성해 두고, step마다 어느 stage에서 batch를 뽑을지만 결정한다. stage 전환 비용 없음.

`train_log.jsonl`에 매 step `stage`, `stage_data_config`, `source_dist`, `sampler_type_dist`가 기록되어 stage 전환과 mixture ratio 추세 모두 감사 가능.

---

## 8. valid_event / valid_uniform 구조

매 `eval_every_steps`마다 `Trainer._eval_and_log`가 두 종류의 평가를 수행한다:

| 이름 | 데이터 | event_window 사용? | sample_weight boost | 역할 |
| --- | --- | :-: | :-: | --- |
| **valid_event** | `eval.valid_event_data_config` (default `wm_data_stage2.yaml`)의 `valid` split | ✅ on | ✅ (loader 그대로) | change_point/shift/reveal 감지 성능 — event 주변에서 정밀도 |
| **valid_uniform** | `eval.valid_uniform_data_config`의 `valid` split, **trainer가 deepcopy 후 event_window.enabled=False + boost factor 1.0** | ❌ uniform | ❌ (모두 1.0) | 전체 분포 dynamics / reward / state 일반화 — train 분포와 diverge되었는지 확인 |

두 loader 모두 `valid` split만 사용한다. Session 8의 hard guard가 train/valid 외 split을 차단한다 (다중 방어).

valid 출력 (한 step 단위로 jsonl):

```
valid_uniform/loss/total
valid_uniform/loss/{obs_local, obs_scalar, reward, done, state, regime, change_point, reveal, shift, mismatch, kl}
valid_uniform/reward/mse
valid_uniform/state/mse
valid_uniform/regime/accuracy
valid_uniform/change_point/{precision, recall, f1, accuracy, positives, tp, fp, fn, tn}
valid_uniform/shift/...
valid_uniform/reveal/...
valid_uniform/raw_eff_mismatch/...

valid_event/...    (동일 구조)
```

> **change_point는 tick-level positive ~0.05% 수준이라 accuracy를 보고하면 안 된다.** F1 / precision / recall 모두 함께 기록한다 (PART3 §3.25.7).

---

## 9. Checkpoint / Resume 구조

`falsifiable_regime_world_model.wm.checkpointing.ManagedCheckpointer`가 다음 정책으로 저장:

| 파일 | 저장 시점 | 정책 |
| --- | --- | --- |
| `last.pt` | 매 `save_every_steps` + 평가 후 | 항상 최신, atomic rename |
| `step_{N:08d}.pt` | 매 `save_every_steps` | rolling, `keep_last_n` 개 유지 |
| `best_valid_uniform_loss_total.pt` | 매 평가 후 | `keep_best_n` 개 유지, mode=`min` |
| `best_valid_event_change_point_f1.pt` | 매 평가 후 | `keep_best_n` 개 유지, mode=`max` |
| `interrupted_step_{N:08d}.pt` | KeyboardInterrupt | `last.pt`도 함께 동기화 |

저장 atomicity:
- `path.suffix + ".tmp"`로 먼저 `torch.save` 후 `os.replace(target)` (Windows 호환).
- 같은 파일 시스템에서 atomic rename 보장.

저장 내용:
```
{
  "model": state_dict (CPU tensor),
  "optimizer": state_dict,
  "scheduler": LambdaLR.state_dict(),
  "scaler": GradScaler.state_dict() | None,
  "wm_config": dict (variant 적용 후),
  "train_config": dict,
  "variant": str,
  "global_step": int,
  "best_metrics": dict (지금까지 본 최고 metric들),
  "rng": {python, numpy, torch, cuda},   # capture/restore_rng_state
  "env_summary": {torch, python, platform, cuda},
  "git_commit": None,                     # 향후 확장
  "schema_version": 1,
}
```

Resume:
```
python scripts\train_world_model.py \
    --train-config configs\wm_train_medium_local.yaml \
    --run-name wm_medium_full_v1 \
    --variant full_model \
    --resume outputs\wm_runs\wm_medium_full_v1\checkpoints\last.pt
```

`Trainer._resume_from`이 model/optimizer/scheduler/scaler/RNG/global_step/best_metrics를 모두 복원한다.

> **검증 결과** (§14): debug_train_smoke가 step 5에서 정확히 resume되어 step 8까지 계속 학습됨.

---

## 10. Overfit / generalization 모니터링

| 위협 | 모니터 |
| --- | --- |
| train loss는 줄어드는데 valid_uniform이 악화 | `valid_uniform/loss/total` 트렌드 + `train-valid gap` (run_summary.md) |
| valid_event만 좋아지고 valid_uniform이 나빠짐 | event-window oversampling 과적합. `valid_uniform/...` 모두 함께 추적. |
| change_point F1만 좋아지고 reward / state 악화 | loss weight 과도. `loss_change_point / total_loss` ratio 모니터 (§11). |
| early stop | `early_stop_patience_evals > 0`이면 best가 N evals 동안 갱신 안 되면 stop (default 0=비활성). |

best checkpoint 정책:
- `valid_uniform/loss/total`이 가장 작을 때 → `best_valid_uniform_loss_total.pt`
- `valid_event/change_point/f1`이 가장 클 때 → `best_valid_event_change_point_f1.pt`

> 두 best 중 어느 것을 paper inference에 쓸지는 Session 11+의 planner evaluation에서 결정 (cp F1이 좋아도 mass-loss가 나쁘면 reward prediction quality가 떨어짐).

regularization:
- `weight_decay = 1e-4` (AdamW)
- `grad_clip = 100.0` (`StabilityConfig.grad_clip`)
- KL `free_nats=1.0`, `kl_balance=0.8` (Session 7 `LossConfig`).
- `warmup_steps=1000`, cosine decay to 0.1× lr (Session 7 §9의 medium hyperparameter와 일치).
- dropout은 backbone에 두지 않았다 (Dreamer 계열은 일반적으로 미사용).

---

## 11. Loss 안정성 / sample_weight 과강조 모니터링

다음 지표가 매 step `train_log.jsonl`에 기록된다:

```
loss.{obs_local, obs_scalar, reward, done, state, regime, change_point, reveal, shift, mismatch, kl, total}
loss_change_point_ratio = loss.change_point / loss.total
sample_weight.mean / sample_weight.max
grad_norm
gpu_memory_allocated / gpu_memory_reserved
step_time_sec
consecutive_overweight
```

자동 가드:
- `consecutive_overweight`: `cp_ratio > 0.5`인 step이 연속 N step 이상이면 `[WARN] change_point loss has dominated >50%...` 콘솔 출력. (default N=50)
- 계산된 `loss.total`이 NaN/Inf면 step에서 `RuntimeError` raise + last checkpoint 저장.
- `grad_norm`이 NaN/Inf면 `nan_action="stop"`이면 raise / `"skip"`이면 zero_grad 후 skip.
- GPU OOM은 자동 복구하지 않는다. fallback: `wm_train_medium_safe.yaml` 사용 권장 메시지.

`compute_total_loss`의 KL component는 free_nats clamp이 들어가 있어 0 아래로 떨어지지 않는다. 다만 sample_weight × λ 누적이 `loss.change_point`를 과잉으로 키울 수 있어 §10의 비율 모니터로 검출.

---

## 12. Variant 학습 전략

| variant | head ON/OFF (Session 7 `apply_variant`) | 학습 새 ckpt? |
| --- | --- | :-: |
| `full_model` | regime ✅, cp ✅, reveal ✅, shift ✅, state ✅ | ✅ |
| `no_regime` | regime ❌ | ✅ |
| `no_change_point` | cp ❌ | ✅ |
| `no_reveal` (optional) | reveal ❌ | ✅ |
| `no_state_aux` (optional) | state ❌ | ✅ |

`scripts/train_world_model.py --variant <name>`. `WMConfig.apply_variant(name)`이 head/loss를 끄고 RSSM backbone capacity는 동일 유지 (PART0 §1.4 same-capacity 원칙).

> Reactive / Fixed-k / Always-plan / Uncertainty gate / Novelty gate / Event-only / Adaptive lookahead / no-action-relevance 등 PART3 §3.22 baseline은 학습 variant가 아니다 — 동일 checkpoint 위에서 Session 11~13이 evaluation-time에 swap한다.

검증 (§14): Cursor가 본 세션에서 `full_model` / `no_regime` / `no_change_point` 세 variant 모두 3 step씩 tiny smoke train PASS (step 1 loss는 각 12~14, no_change_point에서 loss.change_point가 정확히 0).

---

## 13. 사용자가 직접 실행할 명령어

> **Cursor는 본 명령들을 full로 실행하지 않는다.** 사용자가 PowerShell에서 직접 실행한다.

### 13.1 환경 확인 (이미 Cursor가 한 번 실행함)

```powershell
.\.venv\Scripts\python.exe scripts\check_training_env.py `
    --requirements requirements.txt --out-dir outputs\wm_env_check
```

### 13.2 OOM / 하이퍼파라미터 probe (이미 Cursor가 1차 실행함)

```powershell
.\.venv\Scripts\python.exe scripts\probe_wm_hparams.py `
    --wm-config configs\wm_medium.yaml `
    --data-config configs\wm_data_stage2.yaml `
    --out-dir outputs\wm_hparam_probe `
    --variant full_model --max-probe-steps 3
```

### 13.3 debug tiny train smoke (이미 Cursor가 5 step / 3 step 실행함)

```powershell
.\.venv\Scripts\python.exe scripts\train_world_model.py `
    --train-config configs\wm_train_debug.yaml `
    --run-name debug_full_smoke --variant full_model --max-steps 50
```

### 13.4 medium full_model 학습 (full)

```powershell
.\.venv\Scripts\python.exe scripts\train_world_model.py `
    --train-config configs\wm_train_medium_local.yaml `
    --run-name wm_medium_full_v1 --variant full_model
```

### 13.5 no_regime 학습

```powershell
.\.venv\Scripts\python.exe scripts\train_world_model.py `
    --train-config configs\wm_train_medium_local.yaml `
    --run-name wm_medium_no_regime_v1 --variant no_regime
```

### 13.6 no_change_point 학습

```powershell
.\.venv\Scripts\python.exe scripts\train_world_model.py `
    --train-config configs\wm_train_medium_local.yaml `
    --run-name wm_medium_no_change_point_v1 --variant no_change_point
```

### 13.7 resume 예시

```powershell
.\.venv\Scripts\python.exe scripts\train_world_model.py `
    --train-config configs\wm_train_medium_local.yaml `
    --run-name wm_medium_full_v1 --variant full_model `
    --resume outputs\wm_runs\wm_medium_full_v1\checkpoints\last.pt
```

### 13.8 run 요약

```powershell
.\.venv\Scripts\python.exe scripts\summarize_wm_run.py `
    --run-dir outputs\wm_runs\wm_medium_full_v1
```

### 13.9 OOM 발생 시 fallback

```powershell
.\.venv\Scripts\python.exe scripts\train_world_model.py `
    --train-config configs\wm_train_medium_safe.yaml `
    --run-name wm_medium_full_safe_v1 --variant full_model
```

---

## 14. 출력물 저장 위치

| 경로 | 내용 |
| --- | --- |
| `outputs/wm_env_check/env_report.{json,md}` | env_check 결과 |
| `outputs/wm_hparam_probe/probe_results.{csv,json}` | OOM probe per-candidate 결과 |
| `outputs/wm_hparam_probe/recommended_train_config.yaml` | probe 알고리즘이 추천한 config |
| `docs/WM_HPARAM_PROBE_REPORT.md` | probe markdown 요약 |
| `outputs/wm_runs/<run_name>/train_log.jsonl` | 매 log_every_steps train metric |
| `outputs/wm_runs/<run_name>/valid_log.jsonl` | 매 eval_every_steps valid metric (event + uniform) |
| `outputs/wm_runs/<run_name>/config_resolved.yaml` | 실제 적용된 train_config + wm_config 요약 |
| `outputs/wm_runs/<run_name>/env_report.json` | 학습 시작 시점 env snapshot |
| `outputs/wm_runs/<run_name>/run_summary.yaml` | 학습 종료 시 요약 |
| `outputs/wm_runs/<run_name>/run_summary.md` | `summarize_wm_run.py` 출력 |
| `outputs/wm_runs/<run_name>/checkpoints/{last,step_*,best_*,interrupted_*}.pt` | checkpoint 파일들 |
| `docs/WM_TRAINING_ENV_REPORT.md` | env_check가 docs로 복사한 markdown |

---

## 15. Known risks and fallback

1. **Sample-weight cap이 멀티 event 겹침에서 빨리 도달.** Session 8에서 cp×shift 동시 step의 sample_weight=10 cap. 학습 안정 후 cap을 낮추거나 boost를 multiplicative→additive로 바꿀 수 있다. Session 10에서 평가 후 결정.
2. **(완료)** `done_target_mode="success_done"`이 Session 9 PATCH로 완전히 동작한다. `collate_chunks`가 `success_done` / `truncated` / `terminal` / `done`(alias) 4개 키를 모두 분리 노출하며, `Trainer._prepare_targets`가 mode dispatch한다. valid metric도 `success_done` / `terminal` precision-recall-f1과 `truncated/rate`를 분리 기록한다.
3. **Linux 환경에서 `num_workers > 0`은 미검증.** Windows 안전성 우선. 사용자가 Linux로 옮기면 `num_workers=4` 정도로 변경 가능.
4. **OOM 발생 시 즉시 fallback yaml로.** `wm_train_medium_safe.yaml` (batch=2, accum=8) 사용. 추가 OOM이면 `chunk_len=64`로 추가 축소.
5. **Loss NaN/Inf 발생 시 자동 복구 없음.** `nan_action="stop"`이 default. 사용자가 `"skip"`으로 변경하면 grad NaN인 step만 zero_grad + skip하지만, world model 학습에서 NaN은 보통 lr 또는 loss weight 문제이므로 stop이 안전.
6. **TensorBoard / wandb 미설치.** 본 trainer는 jsonl + csv-friendly 구조로 metric을 저장한다 (외부 의존성 0). 필요 시 `pip install tensorboard wandb` 후 별도 logger 추가 (Session 10+).
7. **early_stopping default off (`patience_evals=0`).** 의도적 — 학습 초기에는 valid가 noisy하다. 사용자가 학습 후 안정 구간에서 5~10으로 켜는 것을 권장.
8. **medium 학습은 ~30k step** (yaml default `max_steps=30000`). RTX 4060 Ti에서 1 step ~0.4s 가정 시 약 3~4시간. 학습이 끝까지 도달하지 못해도 매 1k step마다 last.pt + best_*.pt가 저장되므로 resume으로 안전하게 이어 학습 가능.
