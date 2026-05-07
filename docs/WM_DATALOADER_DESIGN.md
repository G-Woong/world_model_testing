# WM Dataloader Design — RG-4F train/valid loader + Event-Window Sampler

> **Session 8 산출물.** 본 문서는 `data/rg4f_random_2000`과 `data/rg4f_success_curriculum_v5_2000`의 **train / valid** episode를 RSSM/Dreamer-style world model 학습에 안전하게 공급하기 위한 dataloader / event-window sampler / sample_weight boost / stage-mix 정책을 닫는다.
>
> Session 8은 학습 루프를 만들지 않는다. optimizer / loss.backward / checkpoint / planner / evaluator 코드 없음 (Session 9+).

---

## 1. Session 8의 목적

| 책임 | 본 문서가 닫는 위치 |
| --- | --- |
| RG-4F npz episode → batch dict 변환 | §6, §10 |
| chunk windowing + padding mask | §6 |
| event-window chunk sampling (change-point/shift/reveal/done/uniform) | §7 |
| tick-level sample_weight boost (loss 가중치) | §8 |
| random_2000 + success_v5_2000 stage-mix | §9 |
| split-leak guard (test_id/OOD 차단) | §3, §4 |
| forbidden-input guard (collector_metadata 등 모델 input에 누수 차단) | §5 |

---

## 2. 데이터 root

| dataset root | 역할 | behavior policy | 학습 split |
| --- | --- | --- | --- |
| `data/rg4f_random_2000` | broad dynamics / 실패 / 방황 / control-drift / cooldown / field drift | `random_biased` | `train` 5000ep, `valid` 500ep |
| `data/rg4f_success_curriculum_v5_2000` | rare success / near-success / reward / value / action-relevance 보강 | `task_success_curriculum` (weak-oracle) | `train` 5000ep, `valid` 500ep |

> `outputs/*_stats`는 통계 확인용이며 학습 input이 아니다 (PART0 §3 §6).

각 episode는 길이 ≤ 2000 tick. 모든 npz는 동일한 schema(§10 표)를 따른다. `episode_meta.json`은 collector_metadata 등을 담지만 **학습 dataloader는 meta.json을 절대 로드하지 않는다** (`load_meta=False`로 강제).

---

## 3. train/valid만 사용하는 이유

본 dataloader가 yield 가능한 split은 다음 두 개로 한정된다:

```python
ALLOWED_TRAIN_SPLITS = ("train", "valid")
```

`test_id` / `ood_*` 6개 split은 모델 학습에 노출되면 PART3 §3.24의 OOD evaluation이 무효가 된다 (test 누수). 따라서 다음을 hard guard로 강제한다:

- `WMDataConfig.validate(extra_split_names=[...])`: forbidden split이 들어오면 `ValueError`.
- `WMDataConfig.normalized_weights(split)`: `split ∉ ALLOWED_TRAIN_SPLITS`이면 즉시 `ValueError`.
- `RG4FChunkIterableDataset.__init__(split=...)`: 같음.
- `MixtureChunkIterableDataset` → `build_chunk_dataset(cfg, split)`: 같음.
- `SourceIndex.entries(split)`: 같음.

negative test:
```bash
python scripts/check_wm_dataloader.py \
  --data-config configs/wm_data_stage1.yaml \
  --inject-bad-split test_id --expect-fail
# → [NEG] PASS: WMDataConfig.validate raised ValueError as expected.
```

---

## 4. test/OOD 누수 금지 정책

| 위협 | 방어 |
| --- | --- |
| yaml에 `splits: [test_id, ...]` | `WMDataConfig.from_yaml`이 `splits` 키에 forbidden split이 있으면 `ValueError`. |
| 코드에서 `build_chunk_dataset(cfg, "test_id")` | `RG4FChunkIterableDataset.__init__` + `SourceIndex.entries`가 모두 `ValueError`. |
| `SourceIndex`가 OOD index를 메모리에 올림 | `SourceIndex.__init__`은 `ALLOWED_TRAIN_SPLITS`만 순회하므로 OOD index.jsonl을 아예 로드하지 않음. |
| dataloader iter 중 OOD episode가 yield됨 | `build_chunk_dataset`가 만드는 `SourceIndex.entries(split)`이 `train/valid`에 한정되어 OOD가 도달 불가능. |

---

## 5. input / target / forbidden metadata 표

### 5.1 모델 입력 (`batch["inputs"]`) — 허용

| 키 | shape | dtype | 설명 |
| --- | --- | --- | --- |
| `local_grid` | (B, T, 5, 5, 10) | float32 | obs CNN 입력 |
| `scalar` | (B, T, 14) | float32 | obs MLP 입력 |
| `event_token` | (B, T) | long | event vocab=13 |
| `action_raw` | (B, T) | long | env step에 들어간 raw action (vocab=16) |
| `action_prev_raw` | (B, T) | long | `action_raw`를 한 step 우측 shift, t=0=0 |

### 5.2 학습 target (`batch["targets"]`) — 허용

| 키 | shape | dtype | 정의 |
| --- | --- | --- | --- |
| `obs_local_target` | (B, T, 5, 5, 10) | float32 | `next_observations_local_grid` (mode `next_step`) 또는 `observations_local_grid` (mode `same_step`) |
| `obs_scalar_target` | (B, T, 14) | float32 | 동상 |
| `reward` | (B, T) | float32 | env reward (task+cost decomposed) |
| `done` | (B, T) | float32 | `(dones \| truncateds).float()` |
| `true_state` | (B, T, 5) | float32 | 5D 상태벡터 ground truth |
| `true_regime_control_mode` | (B, T) | long | 0..4 (IDENTITY/CW/LR/UD/REV) |
| `change_point` | (B, T) | float32 | 0/1 |
| `reveal_event` | (B, T) | float32 | 0/1 |
| `shift_event` | (B, T) | float32 | 0/1 |
| `raw_eff_mismatch` | (B, T) | float32 | `(action_raw != action_effective).float()` (loader가 계산) |

### 5.3 부수 (`batch["sample_weight"]`, `batch["valid_mask"]`, `batch["meta"]`) — 모델 입력에 들어가서는 안 됨

| 키 | shape | dtype | 설명 |
| --- | --- | --- | --- |
| `sample_weight` | (B, T) | float32 | `compute_total_loss`의 `sample_weight` 인자에 직접 사용 |
| `valid_mask` | (B, T) | float32 | 1=valid, 0=padding (sample_weight과 별도) |
| `meta.source_id` | (B,) | long | 0-based source index (debug용) |
| `meta.source_name` | List[str] | str | 'random_2000' / 'success_v5_2000' |
| `meta.split` | List[str] | str | 'train' / 'valid' |
| `meta.episode_id` | List[str] | str | index.jsonl의 episode_id |
| `meta.chunk_start` | (B,) | long | episode 안 chunk 시작 위치 |
| `meta.sampler_type` | List[str] | str | event-window sampler가 사용한 type |
| `meta.valid_len` | (B,) | long | padding 전 실제 tick 수 |

### 5.4 절대 금지 (model input에 들어가면 FAIL)

```python
FORBIDDEN_INPUT_KEYS = (
    # collector / privilege metadata
    "collector_metadata", "collector_mode",
    "task_order_str", "task_order_planned",
    "task_attempt_ticks", "task_timeout", "task_retry_count", "task_budgets",
    "privilege_level", "b_use_label_oracle",
    # task oracle parameters
    "target_band_center", "target_band_half_width", "target_band_kind",
    "target_band_state_dim", "target_band_active",
    "tau_i", "stele_positive_k", "piece_weight_j",
    # episode-level static metadata
    "forced_permutation", "permutation", "permutation_id",
    "field_info_static", "field_info_mu", "field_info_sigma",
    # ground-truth latent (target은 가능, input은 금지)
    "true_regime", "true_regime_control_mode", "true_regime_mobility_mode",
    "true_regime_miscontrol_p", "true_regime_periodic_slip",
    "change_point", "reveal_event", "shift_event", "reveal_or_shift",
    "true_state",
)
```

`collate_chunks`가 `inputs` dict를 만들 때 위 키가 하나라도 들어 있으면 `RuntimeError`로 즉시 raise (`_assert_no_forbidden_keys`).

> 또한 dataloader는 `episode_meta.json`을 **로드하지 않으므로** collector_metadata 자체가 메모리에 올라오지 않는다 (schema 단계 차단).

---

## 6. Chunk windowing 방식

각 episode는 길이 ≤ 2000. 한 번에 모델에 주입할 수 없으므로 **chunk_len 단위로 자른다.**

### 6.1 알고리즘

1. `MixtureChunkIterableDataset.__iter__`이 worker별 categorical sampling으로 source(=dataset root)를 1개 선택.
2. 해당 source의 `entries(split)` (= train/valid index.jsonl entries)에서 episode 1개를 uniform 선택.
3. `load_episode(root, entry, load_meta=False)`로 npz arrays만 로드 (meta 차단).
4. `EventWindowSampler.sample_chunk_start(ev_index, chunk_len, rng)`로 chunk_start 결정.
5. `valid_len = min(chunk_len, T - chunk_start)`. valid_len < chunk_len이면 0-padding.
6. `_slice_episode`로 화이트리스트 키만 slice + pad → numpy dict.
7. `compute_sample_weight`로 (chunk_len,) sample_weight 생성.
8. `EpisodeChunk`로 wrap → `MixtureChunkIterableDataset`이 yield.

### 6.2 padding 정책

- `valid_len < chunk_len`인 경우 chunk의 `[valid_len:chunk_len]` 위치를 **0으로 padding**.
- `valid_mask[valid_len:] = 0`.
- `sample_weight[valid_len:] = 0` (강제, base_weight=0이 아니어도).

### 6.3 deterministic eval

`SplitConfig.seed`를 변경하지 않으면 동일한 batch sequence가 재현된다. `set_epoch(epoch)`을 호출하여 epoch마다 다른 seed를 가질 수 있다 (RNG mixing).

---

## 7. Event-window chunk sampling

change_point는 tick-level positive rate ~0.05% 수준으로 매우 희소하다. uniform chunk sampling만 쓰면 한 epoch 내내 change_point=1 step을 거의 보지 못한다. 따라서 **chunk start를 event 주변에 가두는** event-window sampling을 둔다.

### 7.1 type categorical

매 chunk마다 다음 5개 중 1개를 weight로 sampling:

| type | yaml key | 의미 |
| --- | --- | --- |
| `change_point` | `change_point_prob` | change_point=1 tick 주변에서 chunk_start 결정 |
| `shift` | `shift_prob` | shift_event=1 tick 주변 |
| `reveal` | `reveal_prob` | reveal_event=1 tick 주변 |
| `success` | `success_prob` | dones=1 tick 주변 |
| `uniform` | `uniform_prob` | episode 전체 uniform |

해당 type의 event index가 episode에 0개이면 자동으로 `uniform_fallback_<type>`으로 추적되어 분포 통계로 노출된다 (debug).

### 7.2 chunk_start 위치

event_pos가 결정되면 chunk_start는 다음 범위에서 sampling:

```
low  = max(0, event_pos - chunk_len + 1 - radius)
high = min(max_start, event_pos + radius)
start ~ Uniform(low, high)  (inclusive)
```

→ chunk 안에 event가 무조건 포함되도록 만들고, ±`window_radius`만큼 jitter를 준다.

### 7.3 raw_eff_mismatch 처리

`raw_eff_mismatch`는 (action_raw != action_effective)로 episode당 수백 개씩 나오므로 **chunk-start sampler에는 사용하지 않는다** (sample_weight boost에서만 subsample을 거쳐 사용). yaml `event_window.raw_eff_mismatch_subsample_max`로 한 episode당 최대 N개만 sampling된다.

---

## 8. sample_weight boost 정책

chunk가 결정된 뒤, chunk 안 각 tick에 대해 sample_weight를 계산한다. 이 weight는 `compute_total_loss(..., sample_weight=batch["sample_weight"])`에 그대로 전달된다.

### 8.1 알고리즘

```text
weights = zeros(chunk_len)
weights[:valid_len] = base_weight       # 기본 1.0
for each event in {change_point, shift, reveal, success, raw_eff_mismatch}:
    for pos in event positions ∈ [chunk_start - radius, chunk_start + valid_len + radius):
        local = pos - chunk_start
        weights[clip(local-radius, 0, valid_len) : clip(local+radius+1, 0, valid_len)]
            *= boost_factor
weights = clip(weights, 0, weight_cap)
weights[valid_len:] = 0
```

- 같은 위치에 여러 event가 겹치면 **multiplicatively** 곱해진다 (예: change_point ∩ shift → 5×5=25 → cap 10).
- padding tick은 항상 0.
- `weight_cap=10.0`으로 무한 곱셈 방지.

### 8.2 yaml default (stage1/2)

```yaml
sample_weight:
  enabled: true
  base_weight: 1.0
  boost_radius: 8
  change_point_boost: 5.0
  shift_boost: 5.0
  reveal_boost: 2.0
  success_boost: 2.0
  raw_eff_mismatch_boost: 1.5
  weight_cap: 10.0
```

stage3은 `success_boost: 3.0`으로 강화하여 done 직전 trajectory의 reward/done/regime supervision 가중치를 더 키운다.

---

## 9. stage-mix 정책

| Stage | random_2000 | success_v5_2000 | 목적 |
| --- | ---: | ---: | --- |
| **1** (`wm_data_stage1.yaml`) | 1.0 | 0.0 | dynamics warmup. control-drift / mobility cooldown / field drift broad coverage |
| **2** (`wm_data_stage2.yaml`) | 0.5 | 0.5 | mixed WM training. reveal / interaction / near-success 도입 |
| **3** (`wm_data_stage3.yaml`) | 0.3 | 0.7 | value / action-relevance emphasis. reward / done / regime / change_point 강화 (`success_boost=3.0`) |

`MixtureChunkIterableDataset.__iter__`이 매 chunk마다 source_id를 categorical sampling. 따라서 single batch 내에 두 source가 섞여 있을 수 있다 (stage2/3).

stage 전환은 Session 9의 training loop가 `WMDataConfig.from_yaml(...)`을 stage별로 다시 부르고 `build_chunk_dataset`을 새로 만들어서 처리한다.

---

## 10. dtype / shape contract

### 10.1 npz schema (rg4f generator가 만드는 파일; 변경 금지)

| key | shape | dtype | 본 dataloader 사용 |
| --- | --- | --- | :-: |
| `observations_local_grid` | (T, 5, 5, 10) | float32 | inputs |
| `observations_scalar` | (T, 14) | float32 | inputs |
| `observations_event_token` | (T,) | int32 | inputs (long으로 cast) |
| `actions_raw` | (T,) | int32 | inputs (long) |
| `actions_effective` | (T,) | int32 | targets에서 mismatch 계산용; inputs에는 안 들어감 |
| `next_observations_local_grid` | (T, 5, 5, 10) | float32 | obs_local_target (mode=next_step) |
| `next_observations_scalar` | (T, 14) | float32 | obs_scalar_target (mode=next_step) |
| `next_observations_event_token` | (T,) | int32 | (현재 미사용; 필요 시 Session 9에서 추가 head로) |
| `rewards` | (T,) | float32 | targets.reward |
| `dones` | (T,) | bool | done 계산 |
| `truncateds` | (T,) | bool | done 계산 |
| `true_state` | (T, 5) | float32 | targets.true_state |
| `true_regime_control_mode` | (T,) | int32 | targets.regime (long) |
| `change_point`, `reveal_event`, `shift_event` | (T,) | bool | targets (float) |
| `tick_cost`, `latency_cost`, ...`reset_flag` | (T,) | varies | (현재 미사용; reward에 이미 합산됨) |
| `target_band_*`, `field_info_*` | varies | varies | **input/target 모두 미사용** (oracle 차단) |
| `task_id`, `room_id`, `event_token` | (T,) | int32 | event_token만 input. task_id/room_id는 input/target에서 제외 |
| `agent_position` | (T, 2) | int32 | 미사용 |

### 10.2 batch tensor contract

§5.1 / §5.2 / §5.3 표 그대로. dtype은 `collate.py`의 `_INPUT_DTYPES`/`_TARGET_DTYPES`에서 강제 cast + assert.

### 10.3 channel order

`local_grid`는 `(B, T, H, W, C)` (channel-last) 그대로 collate한다. `ObservationEncoder`가 내부에서 `(B*T, C, H, W)`로 permute하므로 dataloader 단에서 변환하지 않는다.

---

## 11. `check_wm_dataloader` 사용법

```powershell
# stage1: random_2000 100% (warmup)
.\.venv\Scripts\python.exe scripts\check_wm_dataloader.py `
  --data-config configs\wm_data_stage1.yaml --num-batches 3

# stage2: 50/50 (mixed)
.\.venv\Scripts\python.exe scripts\check_wm_dataloader.py `
  --data-config configs\wm_data_stage2.yaml --num-batches 2

# stage3: 30/70 (value emphasis)
.\.venv\Scripts\python.exe scripts\check_wm_dataloader.py `
  --data-config configs\wm_data_stage3.yaml --num-batches 2

# 추가: model forward smoke (RSSMWorldModel.forward 1회만; no training)
.\.venv\Scripts\python.exe scripts\check_wm_dataloader.py `
  --data-config configs\wm_data_stage2.yaml `
  --wm-config configs\wm_debug.yaml --num-batches 1 --device cpu

# 부정 테스트: forbidden split inject
.\.venv\Scripts\python.exe scripts\check_wm_dataloader.py `
  --data-config configs\wm_data_stage1.yaml `
  --inject-bad-split test_id --expect-fail
```

각 호출에서 자동 검증되는 항목:

1. forbidden key가 `batch["inputs"]`에 없음
2. `meta.split` 안에 forbidden split 없음
3. shape contract 모두 일치
4. dtype contract 모두 일치
5. `action_prev_raw[:, 0] == 0` (right-shift)
6. `raw_eff_mismatch ∈ {0, 1}`
7. padding 위치 sample_weight = 0
8. change_point가 있는 batch에서 sample_weight boost가 적용됨 (mean_sw_at_cp > 1.0)
9. source 분포가 yaml weight와 추세적으로 일치 (16 chunks 표본에서는 ±15% 편차 정상)
10. (옵션) RSSMWorldModel.forward 한 번 통과 → forward output key가 모두 존재

---

## 12. Session 9 — Training Loop에 넘길 사항

| 책임 | 본 dataloader가 이미 해 둠 | Session 9가 추가로 해야 할 것 |
| --- | --- | --- |
| batch dict 구조 | inputs/targets/sample_weight/valid_mask/meta 분리 완료 | `loss_out = compute_total_loss(forward_out, targets, cfg.loss, sample_weight=...)`로 직접 연결 |
| dataset stage mix | 3 yaml 작성 완료 | training loop에서 stage 전환 시 새 `WMDataConfig` 로드 + `build_chunk_dataset` 새로 생성 |
| epoch 결정성 | `set_epoch(epoch)` 메서드 노출 | optimizer step 카운트 → epoch 매핑 |
| forbidden key guard | collate에서 hard 검증 | training script에 unit test로 추가 (`assert FORBIDDEN_INPUT_KEYS not in batch["inputs"]`) |
| split guard | yaml/code 모두 hard 차단 | training script에서 직접 `inject` 시도 안 함 |
| compute_total_loss alignment | sample_weight (B,T) float32 그대로 전달 가능 | KL term의 free_nats / kl_balance는 cfg.loss를 그대로 사용 |
| chunk_len mismatch (debug=64 vs medium=128) | yaml에 명시. 단 본 stage*.yaml은 `chunk_len=64`로 통일됨 | medium 학습 시 stage*.yaml에서 chunk_len=128로 override 또는 별도 yaml 추가 |
| GPU multi-worker | `num_workers=0` (Windows 안전) | Linux GPU 환경에서 `num_workers=4`로 늘리고 worker별 결정성 검증 |
| dataset 사이즈 vs chunks_per_epoch | 5000 train ep × ~30~50 chunks/ep = ~150k 학습용 chunk pool | yaml chunks_per_epoch을 8192 ~ 16384로 키워도 무방 |

> **본 dataloader의 chunk_len은 모두 64다.** Session 9의 medium training에서는 chunk_len=128을 쓰고 싶으면 stage yaml의 `train.chunk_len`만 128로 override한다 (모델 forward는 chunk_len에 무관).

---

## 13. Known limitations

1. **chunk_len이 stage*.yaml에 64로 고정.** medium config의 `trainer.chunk_len=128`과 차이가 있다. Session 9가 stage yaml override 또는 medium 전용 stage yaml을 만들어 처리.
2. **`num_workers=0` default.** Windows 안정성 우선. Linux 환경에서는 worker별 file descriptor leak이 없는지 확인 후 4~8로 증가 권장.
3. **mixture weight 표본 크기.** 한 batch당 8 chunks이므로 단일 batch에서 0.5:0.5가 정확히 4:4가 아닐 수 있다 (smoke 결과 8 chunk 기준 6:2~5:3 편차). chunks_per_epoch=4096일 때 수렴.
4. **`event_token`은 episode-level event token만 사용한다.** info["debug"]의 step-level interaction/cooldown_blocked 등은 npz의 numeric column으로 들어가지 않으므로 모델은 obs token으로만 학습한다 (이건 PART2 §3.14.2 contract와 일치).
5. **success_boost와 done_boost를 분리하지 않았다.** 현재 done = (terminated || truncated)이므로 truncated가 많은 random_2000에서는 success_boost가 truncated tick에도 적용된다. 정확한 task-success boost가 필요하면 Session 9에서 `completion_reward > 0` 또는 `completed_tasks > prev`로 보정 가능.
6. **action_relevance_proxy** 학습에 필요한 supervised proxy target은 본 dataloader가 제공하지 않는다 (model config에서도 default off; PART2 §3.8의 actual action relevance는 Session 13).
7. **field_info / target_band cue를 모델이 obs scalar로만 보게 되어 있다.** dataloader 단에서 별도로 target/feature로 노출시키지 않는다 (oracle 차단 원칙).

---

## 14. forbidden key & split guard 요약

| 위치 | 동작 |
| --- | --- |
| `WMDataConfig.from_yaml`, `WMDataConfig.validate` | yaml `splits:` 또는 `extra_split_names`에 forbidden split이 있으면 `ValueError` |
| `WMDataConfig.normalized_weights(split)` | split이 ALLOWED 외면 `ValueError` |
| `SourceIndex.entries(split)` | 같음 |
| `SourceIndex.__init__` | ALLOWED 외 split의 index.jsonl을 메모리에 로드하지 않음 |
| `RG4FChunkIterableDataset.__init__` | split 검증, forbidden시 즉시 raise |
| `build_chunk_dataset(cfg, split)` | 같음 |
| `collate_chunks` | inputs dict에 `FORBIDDEN_INPUT_KEYS` 중 하나라도 있으면 `RuntimeError` |
| `load_episode(..., load_meta=False)` | meta.json을 로드하지 않으므로 collector_metadata가 메모리 진입 자체 차단 |

> 다중 방어선이며, 어느 한 곳을 우회하더라도 collate 단에서 마지막으로 잡힌다.
