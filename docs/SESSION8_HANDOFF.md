# SESSION 8 — Handoff Document

> Session 8은 RG-4F `train`/`valid` dataloader, event-window chunk sampler, sample_weight boost, random_2000 + success_curriculum_v5_2000 stage-mix, 그리고 `RSSMWorldModel.forward(batch["inputs"])`까지 그대로 흐를 수 있는 batch dict contract를 닫았다. **training loop / optimizer / planner / evaluator는 본 세션에서 일절 작성하지 않았다.**

본 문서는 Session 9 (training loop), Session 11+ (planner)가 본 세션의 산출물을 깨지 않고 이어 받기 위해 알아야 할 모든 사실을 닫는다.

---

## 1. 생성/수정 파일 목록

| 경로 | 종류 | 내용 |
| --- | --- | --- |
| `falsifiable_regime_world_model/wm/data_config.py` | 신규 | `WMDataConfig` + 하위 dataclass + ALLOWED/FORBIDDEN split & key |
| `falsifiable_regime_world_model/wm/sampling.py` | 신규 | `EventIndex`, `EventWindowSampler`, `compute_sample_weight` |
| `falsifiable_regime_world_model/wm/data.py` | 신규 | `SourceIndex`, `RG4FChunkIterableDataset`, `MixtureChunkIterableDataset`, `build_chunk_dataset` |
| `falsifiable_regime_world_model/wm/collate.py` | 신규 | `collate_chunks` (inputs/targets/sample_weight/valid_mask/meta dict) |
| `falsifiable_regime_world_model/wm/__init__.py` | 수정 | 위 신규 심볼들을 public API에 노출 |
| `configs/wm_data_stage1.yaml` | 신규 | random_2000 100% (warmup) |
| `configs/wm_data_stage2.yaml` | 신규 | 50:50 mixed |
| `configs/wm_data_stage3.yaml` | 신규 | 30:70 (success emphasis) |
| `scripts/check_wm_dataloader.py` | 신규 | smoke + safety + (옵션) forward + bad-split injection |
| `docs/WM_DATALOADER_DESIGN.md` | 신규 | 본 dataloader의 설계/contract 종합 |
| `docs/SESSION8_HANDOFF.md` | 신규 | 본 문서 |

미수정 (보존 0줄):

- `ref/PART0~3`
- `data/**`, `outputs/**`
- `scripts/{generate_dataset,validate_dataset,inspect_episode,plot_dataset_stats,_p1_check_family_disjoint}.py`
- `falsifiable_regime_world_model/rg4f/**`
- `configs/dataset_default.yaml`, `configs/wm_debug.yaml`, `configs/wm_medium.yaml`
- `falsifiable_regime_world_model/wm/{config,modules,rssm,heads,losses,README.md}.py` (Session 7 산출물 그대로)
- `requirements.txt`

---

## 2. data config 3개 설명

| Stage | yaml | random_2000 | success_v5_2000 | 비고 |
| --- | --- | ---: | ---: | --- |
| 1 | `wm_data_stage1.yaml` | 1.0 | 0.0 | dynamics warmup. event_window/sample_weight default. |
| 2 | `wm_data_stage2.yaml` | 0.5 | 0.5 | mixed. seed 4321로 분리. |
| 3 | `wm_data_stage3.yaml` | 0.3 | 0.7 | value emphasis. `success_prob=0.20`, `success_boost=3.0`로 강화. |

세 yaml 모두:
- `train.chunk_len = 64`, `batch_size = 8` (Session 9가 medium에서 override 권장).
- `train.chunks_per_epoch = 4096`, `valid.chunks_per_epoch = 512`.
- `event_window.window_radius = 16`, `sample_weight.boost_radius = 8`, `weight_cap = 10.0`.
- `target.obs_recon_mode = next_step` (DreamerV3 표준).

---

## 3. loader class / API 설명

### 3.1 `WMDataConfig` (data_config.py)

```python
cfg = WMDataConfig.from_yaml("configs/wm_data_stage2.yaml")
cfg.validate()                         # source root / manifest 존재 검증
cfg.normalized_weights("train")        # → [0.5, 0.5]
```

- `sources: List[DatasetSourceConfig]` — name, root, train_weight, valid_weight.
- `train: SplitConfig`, `valid: SplitConfig` — chunk_len / batch_size / chunks_per_epoch / seed / num_workers.
- `event_window: EventWindowConfig` — type별 prob + window_radius + raw_eff_mismatch_subsample_max.
- `sample_weight: SampleWeightConfig` — base_weight + boost_factor + boost_radius + weight_cap.
- `target: TargetConfig` — `obs_recon_mode = next_step | same_step`.

split guard:
- `validate(extra_split_names=[...])`에 `test_id`/`ood_*`가 있으면 즉시 `ValueError`.
- `normalized_weights(split)`이 ALLOWED 외 split을 받으면 즉시 `ValueError`.

### 3.2 `SourceIndex` (data.py)

```python
src = SourceIndex(cfg.sources[0])         # train/valid index.jsonl만 로드
entries = src.entries("train")            # List[IndexEntry]; "test_id"는 ValueError
arrays = src.load_episode_arrays("train", idx)   # npz dict (meta.json은 무시)
```

### 3.3 `RG4FChunkIterableDataset` / `MixtureChunkIterableDataset`

```python
sources = build_source_indices(cfg)
ds = build_chunk_dataset(cfg, "train", epoch=0, sources=sources)
loader = DataLoader(ds, batch_size=8, num_workers=0, collate_fn=collate_chunks)
batch = next(iter(loader))
```

- IterableDataset 기반 — 매 epoch에서 `chunks_per_epoch`개 yield, worker별 분배.
- `set_epoch(epoch)`으로 결정성 mixing.
- mixture weight categorical로 source 선택, source 내부에서 episode uniform 선택, episode 내부에서 chunk_start는 `EventWindowSampler`로 결정.

---

## 4. batch dict 구조

```python
batch = {
    "inputs": {                                           # → RSSMWorldModel.forward
        "local_grid":      FloatTensor[B, T, 5, 5, 10],
        "scalar":          FloatTensor[B, T, 14],
        "event_token":     LongTensor[B, T],
        "action_raw":      LongTensor[B, T],
        "action_prev_raw": LongTensor[B, T],     # right-shift; t=0=0
    },
    "targets": {                                          # → compute_total_loss
        "obs_local_target":          FloatTensor[B, T, 5, 5, 10],
        "obs_scalar_target":         FloatTensor[B, T, 14],
        "reward":                    FloatTensor[B, T],
        "done":                      FloatTensor[B, T],   # dones | truncateds
        "true_state":                FloatTensor[B, T, 5],
        "true_regime_control_mode":  LongTensor[B, T],    # 0..4
        "change_point":              FloatTensor[B, T],
        "reveal_event":              FloatTensor[B, T],
        "shift_event":               FloatTensor[B, T],
        "raw_eff_mismatch":          FloatTensor[B, T],
    },
    "sample_weight": FloatTensor[B, T],                   # → compute_total_loss(sample_weight=...)
    "valid_mask":    FloatTensor[B, T],                   # 1=valid, 0=padding
    "meta": {                                             # debug only — model에 입력 금지
        "source_id":    LongTensor[B],
        "source_name":  List[str],
        "split":        List[str],
        "episode_id":   List[str],
        "chunk_start":  LongTensor[B],
        "sampler_type": List[str],
        "valid_len":    LongTensor[B],
    },
}
```

> Session 9 training step:
> ```python
> forward_out = model(batch["inputs"])
> loss_out   = compute_total_loss(forward_out, batch["targets"], cfg.loss,
>                                 sample_weight=batch["sample_weight"])
> ```

---

## 5. target dict 상세

| key | npz origin | 변환 |
| --- | --- | --- |
| `obs_local_target` | `next_observations_local_grid` (mode `next_step`) 또는 `observations_local_grid` (mode `same_step`) | float32 그대로 |
| `obs_scalar_target` | 동상 | float32 |
| `reward` | `rewards` | float32 |
| `done` | `dones | truncateds` | bool→float32 |
| `true_state` | `true_state` | float32 |
| `true_regime_control_mode` | `true_regime_control_mode` | int32→long |
| `change_point` | `change_point` | bool→float32 |
| `reveal_event` | `reveal_event` | bool→float32 |
| `shift_event` | `shift_event` | bool→float32 |
| `raw_eff_mismatch` | `(actions_raw != actions_effective)` | float32 0/1 |

> `true_regime_mobility_mode`, `true_regime_miscontrol_p`, `true_regime_periodic_slip`은 현재 target에서 제외 (Session 7의 model이 control_mode 1-factor만 supervised). Session 9 또는 multi-factor 확장 시 추가 가능.

---

## 6. sample_weight / event-window sampling 설명

### 6.1 chunk_start sampling (`EventWindowSampler`)

매 chunk마다 type을 categorical로 1개 선택:
```
P(change_point)=0.25, P(shift)=0.20, P(reveal)=0.15, P(success)=0.10, P(uniform)=0.30
```
(stage3은 success_prob=0.20)

해당 type의 event index가 episode에 있으면 그 주변 ±`window_radius=16` jitter로 chunk_start sampling. 없으면 uniform fallback (debug 출력에 `uniform_fallback_<type>`로 기록).

### 6.2 sample_weight boost (`compute_sample_weight`)

chunk가 결정된 뒤, 각 tick의 sample_weight를 계산:

```
weights = zeros(chunk_len)
weights[:valid_len] = base_weight (1.0)
for each event in {change_point, shift, reveal, done(success), raw_eff_mismatch}:
    for pos in episode 안 event index ∩ [chunk_start - radius, chunk_start + valid_len + radius):
        weights[local-radius : local+radius+1] *= boost
weights = clip(weights, 0, weight_cap=10.0)
weights[valid_len:] = 0      # padding 강제 0
```

stage1/2 default:
- change_point boost = 5.0
- shift boost = 5.0
- reveal boost = 2.0
- success(=done) boost = 2.0
- raw_eff_mismatch boost = 1.5
- weight_cap = 10.0

stage3는 `success_boost=3.0`. 두 event가 같은 tick에 겹치면 multiplicative (cap 10).

**sample_weight는 `compute_total_loss`의 `sample_weight=` 인자 (Session 7 §5.1)에 그대로 전달된다.** 모든 component loss(MSE/BCE/CE/KL)가 동일한 weight를 사용한다.

---

## 7. split leakage guard 설명

§3 of `docs/WM_DATALOADER_DESIGN.md` 표 그대로.

검증된 항목 (smoke + negative test):
- `WMDataConfig.from_yaml`이 `splits:` 키에 forbidden split이 있으면 `ValueError`
- `WMDataConfig.validate(extra_split_names=["test_id"])` → `ValueError`
- `build_chunk_dataset(cfg, "test_id")` → `ValueError`
- `SourceIndex.entries("test_id")` → `ValueError`
- `SourceIndex.__init__`이 OOD index.jsonl을 아예 메모리에 안 올림
- `collate_chunks`가 `inputs` dict에 `FORBIDDEN_INPUT_KEYS` 중 하나라도 있으면 `RuntimeError`
- `load_episode(..., load_meta=False)` 강제 → collector_metadata가 메모리 진입 차단

---

## 8. smoke test 결과

### 8.1 import / shape check

```bash
python -c "from falsifiable_regime_world_model.wm import WMDataConfig, build_chunk_dataset, collate_chunks; print('wm-data import ok')"
# → wm-data import ok
```

### 8.2 stage1 smoke (3 batches train + 3 batches valid)

```text
[train] batch 0..2: B=8 T=64
        source_dist: random_2000=100%, success_v5_2000=0%   (config 그대로)
        events per batch: change_point 0~4, reveal 0~61, shift 0~4, mismatch 92~112
        sample_weight: min=1.0, mean=1.27~3.74, max=10.0 (cap에 도달; cp/shift 동시 발생 시)
        boost_check: PASS (mean_sw_at_cp=10.00 — change_point가 있는 batch에서)
[valid] 동일하게 PASS.

→ source ratio (24 chunks): random_2000 100% / success_v5 0% (expected 1.0/0.0)
```

### 8.3 stage2 smoke (2 batches × train+valid)

```text
[train] batch 0: src={'random_2000': 6, 'success_v5_2000': 2}, mean_sw_at_cp=10.0 PASS
[train] batch 1: src={'random_2000': 3, 'success_v5_2000': 5}, no_cp_in_batch
[valid] batch 0/1: src 5:3/5:3
→ source ratio (16 chunks): random 0.56 vs expected 0.50 (편차 ±6%; 표본 작음)
```

### 8.4 stage3 smoke (2 batches × train+valid)

```text
[train] batch 0: src={'success_v5_2000': 5, 'random_2000': 3}, mean_sw_at_cp=10.0 PASS
[train] batch 1: src={'success_v5_2000': 8}, mean_sw_at_cp=10.0 PASS
→ source ratio (16 chunks): random 0.19 vs expected 0.30 (편차 ±11%; 작은 표본 noise)
   chunks_per_epoch=4096일 때 수렴.
```

### 8.5 model forward smoke

```bash
python scripts/check_wm_dataloader.py \
  --data-config configs/wm_data_stage2.yaml \
  --wm-config configs/wm_debug.yaml --num-batches 1 --device cpu
```

```text
[fwd] device=cpu
[fwd] forward_keys=['change_point_logit', 'done_logit', 'h', 'obs_local_pred', 'obs_scalar_pred',
                    'post_mean', 'post_std', 'prior_mean', 'prior_std',
                    'raw_eff_mismatch_logit', 'regime_logits', 'reveal_logit',
                    'reward_pred', 'shift_logit', 'state_pred', 'z']
[fwd] h_shape=(8, 64, 256)  z_shape=(8, 64, 64)  reward_pred_shape=(8, 64)
```

→ wm_debug capacity (deter=256, stoch=64)와 정확히 일치. 모든 head output 정상.

### 8.6 negative (bad-split injection) test

```bash
python scripts/check_wm_dataloader.py --data-config configs/wm_data_stage1.yaml \
  --inject-bad-split test_id --expect-fail
```

```text
[NEG] PASS: WMDataConfig.validate raised ValueError as expected.
        message: Split leakage detected: test_id/OOD splits must not be used
                 for training loaders. Got: 'test_id'. Allowed: ('train', 'valid')
```

---

## 9. Known limitations

1. **chunk_len=64 통일.** medium training에서 chunk_len=128을 쓰려면 stage*.yaml의 `train.chunk_len`을 override해야 한다. medium 전용 stage yaml 추가는 Session 9의 책임.
2. **`num_workers=0` default.** Windows 안전성 우선. Linux GPU 환경에서는 4~8로 늘리고 worker별 결정성 검증 권장.
3. **mixture weight 작은 표본 편차.** chunks_per_epoch=4096이면 수렴. smoke 시 16~24 chunks 표본은 ±15% 편차 정상.
4. **success boost와 done boost가 동일.** truncated가 많은 random_2000에서는 success_boost가 task-success가 아닌 truncated tick에도 적용. 정확한 task-success boost는 Session 9에서 `completion_reward > 0` 또는 `completed_tasks` 증가 기준으로 분리 가능.
5. **`true_regime_mobility_mode` / `miscontrol_p` / `periodic_slip`은 target에서 제외.** Session 7 model이 control_mode 1-factor만 supervised. multi-factor regime supervision 확장은 model + dataloader 둘 다 수정 필요.
6. **field_info_static, target_band_*, agent_position 등은 미사용.** oracle 차단 원칙. 추후 cue layer에 노출되도록 환경이 이미 obs scalar에 약하게 흘려보내고 있음.
7. **action_relevance_proxy target 미생성.** Session 13의 rollout 기반 action relevance가 actual; 본 dataloader는 supervised proxy를 만들지 않는다.
8. **`debug_trace`는 meta.json에만 있음.** dataloader가 meta.json을 로드하지 않으므로 debug_trace는 학습에 진입하지 않는다 (PART0 §3 정합).

---

## 10. Session 9 — Training Loop TODO

| 책임 | 핵심 |
| --- | --- |
| optimizer / scheduler | AdamW (lr 3e-4 권장), warmup 1k step + constant 또는 cosine |
| precision | medium은 `bf16` (`torch.autocast`); debug는 fp32 |
| grad_clip | `cfg.trainer.grad_clip` (default 100.0) |
| variant dispatch | `WMConfig.apply_variant("full_model" | "no_regime" | "no_change_point" | ...)` × seed≥3 |
| **stage 전환** | epoch N마다 `WMDataConfig.from_yaml("wm_data_stage{1,2,3}.yaml")`로 갈아끼우기. `build_chunk_dataset` 새로 호출. `set_epoch`으로 RNG seed mix |
| **batch → forward → loss 연결** | `out = model(batch["inputs"])` → `loss = compute_total_loss(out, batch["targets"], cfg.loss, sample_weight=batch["sample_weight"])` → `loss.total.backward()` |
| valid loop | `valid` split loader로 매 epoch end에 forward + loss components 기록 |
| logging | `WMLossOutput.components` + `meta.source_name`/`sampler_type` distribution을 step별 로그 |
| checkpoint | `(stage, variant, seed) × N step`마다 |
| dataset stage schedule | 권장: total step의 30% stage1 → 30% stage2 → 40% stage3. Session 9에서 ablation. |
| chunk_len override | medium 학습 시 stage yaml의 `train.chunk_len=128` (또는 medium 전용 stage yaml 신설) |
| **train/valid only 강제** | training script에서 `cfg.validate(extra_split_names=["train", "valid"])`로 명시적 호출 (이미 dataloader가 차단하지만 다중 방어) |
| metric | step loss, valid total/components, change_point F1, reward MSE, regime accuracy, raw_eff_mismatch accuracy |

---

## 11. Self-Audit

| Check | Status | Evidence |
| --- | :-: | --- |
| random_2000 / success_v5_2000 train/valid loader 구현 | PASS | `data.py` `MixtureChunkIterableDataset` + `build_chunk_dataset`. stage1/2/3 yaml 모두 `train` + `valid` 양쪽에서 batch 정상 yield. |
| test_id/OOD가 학습 loader에서 차단 | PASS | smoke negative test (`--inject-bad-split test_id --expect-fail`)에서 `ValueError: Split leakage detected: test_id/OOD splits must not be used for training loaders.` 발생. `data_config`/`data`/`build_chunk_dataset` 다중 방어선. |
| forbidden metadata가 model input에서 제외 | PASS | `collate.py` `_assert_no_forbidden_keys`가 inputs dict의 모든 key를 `FORBIDDEN_INPUT_KEYS`(43개)와 비교. smoke의 모든 batch에서 leak 없음. `load_episode(..., load_meta=False)`로 collector_metadata 자체가 메모리 진입 차단. |
| local_grid/scalar/action/reward/done/state/regime/change/reveal/shift target 준비 | PASS | smoke 출력의 `events={'change_point': ..., 'reveal': ..., 'shift': ..., 'done': ..., 'raw_eff_mismatch': ...}` + targets shape/dtype assert 모두 통과. |
| chunk_len windowing 구현 | PASS | `data.py`의 `_slice_episode` + `_pad_to_len`. smoke에서 모든 batch shape (B=8, T=64) 일관. |
| padding mask / sample_weight | PASS | `valid_mask=1` (valid_mask_mean=1.000으로 epi 길이≥chunk_len인 정상 case 확인). `sample_weight[valid_len:] = 0` 강제. smoke의 `sample_weight.min=1.0` (base_weight) 준수. |
| event-window sampling 구현 | PASS | smoke의 sampler_types 분포: change_point/shift/reveal/success/uniform_fallback_* 모두 등장. stage3에서 success_prob=0.2로 `success` type이 등장 (`'success': 1`). |
| change_point/shift/reveal sample_weight boost | PASS | smoke 모든 stage에서 change_point가 있는 batch의 `mean_sw_at_cp=10.0` (cap에 도달; cp_boost=5.0 × shift_boost=5.0 가 같은 tick에 겹쳐 multiplicative). max=10.0이 정확히 cap. |
| stage1/2/3 mix config 작성 | PASS | `configs/wm_data_stage1.yaml` (1.0:0.0), `wm_data_stage2.yaml` (0.5:0.5), `wm_data_stage3.yaml` (0.3:0.7). 본 문서 §2 표. |
| dataloader smoke가 stage1/2/3에서 PASS | PASS | 본 문서 §8.2~§8.4. 세 yaml 모두 train+valid에서 batch sampling/sample_weight/event 분포/forbidden guard 통과. |
| bad split injection이 정확히 ValueError | PASS | 본 문서 §8.6. `[NEG] PASS: ... ValueError as expected.` |
| training loop 미구현 | PASS | optimizer.step / loss.backward 코드 0줄. `check_wm_dataloader.py`의 forward smoke는 `model.eval()` + `torch.no_grad()`로 명시. |
| planner / evaluator 미구현 | PASS | imagine 호출 없음. RSSMWorldModel.predict_heads 호출 없음. baseline 코드 없음. |
| docs/WM_DATALOADER_DESIGN.md 작성 | PASS | 14절, ~20kB. |
| docs/SESSION8_HANDOFF.md 작성 | PASS | 본 문서. |

**15개 항목 모두 PASS.**

---

## 12. Smoke 명령 재현 절차

```powershell
# import
.\.venv\Scripts\python.exe -c "from falsifiable_regime_world_model.wm import WMDataConfig, build_chunk_dataset, collate_chunks; print('wm-data import ok')"

# stage1 smoke
.\.venv\Scripts\python.exe scripts\check_wm_dataloader.py --data-config configs\wm_data_stage1.yaml --num-batches 3

# stage2 smoke
.\.venv\Scripts\python.exe scripts\check_wm_dataloader.py --data-config configs\wm_data_stage2.yaml --num-batches 2

# stage3 smoke
.\.venv\Scripts\python.exe scripts\check_wm_dataloader.py --data-config configs\wm_data_stage3.yaml --num-batches 2

# (옵션) model forward 결합 smoke
.\.venv\Scripts\python.exe scripts\check_wm_dataloader.py --data-config configs\wm_data_stage2.yaml --wm-config configs\wm_debug.yaml --num-batches 1 --device cpu

# 부정 테스트: forbidden split inject
.\.venv\Scripts\python.exe scripts\check_wm_dataloader.py --data-config configs\wm_data_stage1.yaml --inject-bad-split test_id --expect-fail
```

각 명령이 위 §8 결과와 일치하는지 확인.
