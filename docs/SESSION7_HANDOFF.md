# SESSION 7 — Handoff Document

> Session 7은 RG-4F 환경의 NeurIPS 2026 메인트랙 실험을 위한 RSSM/Dreamer-style world model의 아키텍처 / config / forward & loss API contract / variant 학습 정책을 닫았다. **training loop / dataset loader / planner / evaluator는 본 세션에서 일절 작성하지 않았다.**

본 문서는 Session 8 (loader / event-window sampler), Session 9 (training loop), Session 11+ (planner)가 본 세션의 산출물을 깨지 않고 이어 받기 위해 알아야 할 모든 사실을 닫는다.

---

## 1. 생성/수정 파일 목록

| 경로 | 종류 | 내용 |
| --- | --- | --- |
| `configs/wm_debug.yaml` | 신규 | RSSM **debug capacity**. shape sanity / 8GB GPU / overfit check 전용. `paper_main: false`. |
| `configs/wm_medium.yaml` | 신규 | RSSM **paper main capacity**. 동일 backbone capacity로 모든 baseline / ablation을 비교한다. `paper_main: true`. |
| `falsifiable_regime_world_model/wm/__init__.py` | 신규 | wm 패키지 public API. |
| `falsifiable_regime_world_model/wm/config.py` | 신규 | `WMConfig` 및 하위 dataclass (yaml 매핑, variant apply). |
| `falsifiable_regime_world_model/wm/modules.py` | 신규 | encoder / decoder / action embedding / MLP utility. |
| `falsifiable_regime_world_model/wm/rssm.py` | 신규 | RSSM core (deterministic h + stochastic z + prior + posterior + observe/imagine sequence). |
| `falsifiable_regime_world_model/wm/heads.py` | 신규 | prediction head 묶음 + `RSSMWorldModel` top-level. |
| `falsifiable_regime_world_model/wm/losses.py` | 신규 | loss component 함수 + `compute_total_loss` + KL Dreamer-style. |
| `falsifiable_regime_world_model/wm/README.md` | 신규 | wm 패키지 사용법 / API contract / variant 표. |
| `scripts/check_wm_shapes.py` | 신규 | synthetic-only shape sanity script (no dataset / no training). |
| `docs/WM_ARCHITECTURE_DESIGN.md` | 신규 | 본 backbone의 설계/contract 종합 문서. |
| `docs/SESSION7_HANDOFF.md` | 신규 | 본 문서. |

미수정 (보존 0줄):

- `falsifiable_regime_world_model/rg4f/**`
- `scripts/{generate_dataset,validate_dataset,inspect_episode,plot_dataset_stats,_p1_check_family_disjoint}.py`
- `configs/dataset_default.yaml`
- `ref/PART0_IMPLEMENTATION_STRATEGY.md`, `ref/PART1_PROBLEM_FRAMING.md`, `ref/PART2_ALGORITHM.md`, `ref/PART3_EXPERIMENT_DESIGN.md`
- `data/**`, `outputs/**`
- `requirements.txt`

---

## 2. config 파일 설명

### 2.1 `configs/wm_debug.yaml`

| 영역 | key | 값 | 의미 |
| --- | --- | --- | --- |
| meta | `name`, `scale`, `paper_main` | `wm_debug`, `debug`, `false` | **논문 main 결과로 인용 금지**. shape sanity / overfit check 전용. |
| observation | `local_grid_size/channels`, `scalar_dim`, `event_vocab`, `action_vocab` | 5/10/14/13/16 | dataset npz schema 1:1 (변경 금지). |
| encoder | `cnn_channels`, `feature_dim` | (32,64), 256 | 작은 capacity. |
| rssm | `deter_dim`, `stoch_dim`, `hidden_dim` | 256, 64, 256 | feature_dim(h+z) = 320. |
| heads | (모두) | 9개 head + (off) action_relevance_proxy | obs/reward/done/state/regime/cp/reveal/shift/mismatch. |
| loss | `cp_use_focal` | false | debug는 BCE+pos_weight만. |
| trainer | `chunk_len`/`batch_size`/`precision` | 64/8/fp32 | Session 9가 채움. |
| variants | full / no_regime / no_change_point / no_reveal / no_state_aux | 5개 | head/loss를 끄는 방식. |

### 2.2 `configs/wm_medium.yaml`

| 영역 | key | 값 | 의미 |
| --- | --- | --- | --- |
| meta | `name`, `scale`, `paper_main` | `wm_medium`, `medium`, `true` | **논문 main 결과는 이 config 위에서 학습된 checkpoint로만 보고**. |
| encoder | `cnn_channels`, `feature_dim` | (64,128), 512 | medium capacity. |
| rssm | `deter_dim`, `stoch_dim`, `hidden_dim` | 512, 128, 512 | feature_dim(h+z) = 640. |
| loss | `cp_use_focal` | true | main은 focal+BCE. |
| trainer | `chunk_len`/`batch_size`/`precision` | 128/32/bf16 | Session 9가 실제 사용. |
| variants | (debug와 동일 5개) | | |

### 2.3 large 후보 (이번 세션 미생성, 문서에만 설계)

`deter_dim=1024 / stoch_dim=256 / cnn_channels=[128,256] / feature_dim=1024 / batch_size=16`. capacity sensitivity / reviewer defense 용 (Session 9 이후 별도 yaml).

---

## 3. model module 설명

### 3.1 `falsifiable_regime_world_model/wm/modules.py`

- `ObservationEncoder(obs_cfg, enc_cfg)`: local_grid CNN + scalar MLP + event embedding → `(B, T, feature_dim)` feature.
- `ObservationDecoder(feature_dim, obs_cfg, hidden_dim)`: `features → (local_pred, scalar_pred)` reconstruction.
- `ActionEmbedding(action_vocab, embed_dim)`: action_raw / action_effective 공통 embedding.
- `make_mlp(in, hidden, out)`, `concat_features(h, z)` 유틸.

### 3.2 `falsifiable_regime_world_model/wm/rssm.py`

- `RSSMState`: `h, z, prior_mean/std, post_mean/std` 컨테이너 (`detach()` 메서드 포함).
- `RSSMCore`: `h_t = GRUCell(input_proj([z_{t-1}, action_emb_{t-1}]), h_{t-1})`.
- `TransitionPrior`: `h → (μ_p, σ_p)` over z_t.
- `RepresentationPosterior`: `[h, e_t] → (μ_q, σ_q)` over z_t.
- `RSSM`:
  - `posterior_step(prev_state, prev_action_emb, feature_t) -> RSSMState`.
  - `prior_step(prev_state, prev_action_emb) -> RSSMState`.
  - `observe_sequence(features, action_embeds, initial_state)`: 학습용 BPTT.
  - `imagine_sequence(action_embeds, initial_state)`: planner stub. Session 11에서 alternative-regime conditioning 추가 예정.

### 3.3 `falsifiable_regime_world_model/wm/heads.py`

- `ScalarHead`, `BinaryLogitHead`, `CategoricalLogitHead`, `RegressionHead` (단순 MLP head).
- `WMHeads`: ON head만 nn.Module로 만든다. `forward(features) -> dict`.
- `RSSMWorldModel(cfg)`:
  - `forward(batch, initial_state=None)`: encoder + RSSM observe + heads.
  - `predict_heads(h, z)`: encoder/RSSM 호출 없이 head만 평가 (planner용).
  - `imagine(action_seq_raw, initial_state)`: prior-only rollout + heads (Session 11에서 확장).
  - `initial_state(B, device)`.

### 3.4 `falsifiable_regime_world_model/wm/losses.py`

- 개별 loss: `mse_loss`, `bce_with_logits_loss` (pos_weight + focal), `categorical_ce_loss`, `kl_divergence_diag_normal`, `kl_loss_dreamer` (free nats + KL balancing).
- `compute_total_loss(forward_out, target, cfg.loss, sample_weight=None) -> WMLossOutput(total, components, diagnostics)`.

---

## 4. forward output key contract

(WM_ARCHITECTURE_DESIGN §10.1 참조; 여기서는 표만 다시 명시)

| key | shape | dtype | 비고 |
| --- | --- | --- | --- |
| `h` | (B, T, deter_dim) | float32 | RSSM deterministic state |
| `z` | (B, T, stoch_dim) | float32 | RSSM stochastic latent (posterior sample) |
| `prior_mean`, `prior_std` | (B, T, stoch_dim) | float32 | p(z_t \| h_t) |
| `post_mean`, `post_std` | (B, T, stoch_dim) | float32 | q(z_t \| h_t, e_t) |
| `obs_local_pred` | (B, T, 5, 5, 10) | float32 | head ON일 때만 |
| `obs_scalar_pred` | (B, T, 14) | float32 | head ON일 때만 |
| `reward_pred` | (B, T) | float32 | |
| `done_logit` | (B, T) | float32 | BCE-with-logits 그대로 |
| `state_pred` | (B, T, 5) | float32 | |
| `regime_logits` | (B, T, 5) | float32 | CE 그대로 (5 control modes) |
| `change_point_logit` | (B, T) | float32 | BCE-with-logits |
| `reveal_logit` | (B, T) | float32 | BCE-with-logits |
| `shift_logit` | (B, T) | float32 | BCE-with-logits |
| `raw_eff_mismatch_logit` | (B, T) | float32 | BCE-with-logits |
| `action_rel_proxy_pred` | (B, T) | float32 | optional, 기본 off |

---

## 5. loss input/output contract

### 5.1 input

```python
forward_out = RSSMWorldModel.forward(batch)
target = {
  "obs_local_target":  Tensor[B, T, 5, 5, 10] float32,
  "obs_scalar_target": Tensor[B, T, 14]       float32,
  "reward":            Tensor[B, T]           float32,
  "done":              Tensor[B, T]           float32 or bool,
  "true_state":        Tensor[B, T, 5]        float32,
  "true_regime_control_mode": Tensor[B, T]    long (0..4),
  "change_point":      Tensor[B, T]           float32 or bool,
  "reveal_event":      Tensor[B, T]           float32 or bool,
  "shift_event":       Tensor[B, T]           float32 or bool,
  "raw_eff_mismatch":  Tensor[B, T]           float32 or bool,
}
sample_weight = Optional[Tensor[B, T]] float   # padding mask + event-window oversampling weight
loss_out = compute_total_loss(forward_out, target, cfg.loss, sample_weight=sample_weight)
```

### 5.2 output (`WMLossOutput`)

```python
loss_out.total           # scalar tensor (학습 backprop)
loss_out.components      # dict[str, scalar tensor] — 각 component 분해 (logging용)
loss_out.diagnostics     # dict[str, scalar tensor] — 부수 metric (예: kl_raw_mean)
```

---

## 6. metadata exclusion rule

본 backbone은 **다음 키를 입력으로 받지 않으며, 학습 target으로도 사용하지 않는다.** Session 8 loader는 이를 hard guard로 강제해야 한다.

| 카테고리 | 키 |
| --- | --- |
| collector metadata | `collector_metadata`, `collector_mode`, `task_order_str`, `task_order_planned`, `task_attempt_ticks`, `task_timeout`, `task_retry_count`, `task_budgets`, `privilege_level`, `b_use_label_oracle` |
| episode meta (privilege) | `permutation`, `permutation_id`, `forced_permutation` (raw), `field_info_static` (input으로 금지; coupling shape 정보를 학습 input에 노출시킴) |
| task parameter (oracle) | `target_band_center`, `tau_i`, `stele_positive_k`, `piece_weight_j` (raw value) |
| evaluation-only ground truth | `true_regime_*` (target은 가능, **input은 금지**), `change_point` (target은 가능, **input은 금지**), `reveal_event`/`shift_event` (target은 가능, **input은 금지**) |

> 단, `target_band_center`, `target_band_active` 등 일부 키는 환경 obs에 노출되도록 설계된 *cue*가 아니라 ground-truth metadata이므로 **모델 input/target 모두 금지**다. 환경의 cue layer는 obs scalar / local_grid에 이미 약하게 노출되므로 별도 입력이 필요 없다.

---

## 7. training variant 목록

(WM_ARCHITECTURE_DESIGN §9.1)

| variant | head ON/OFF | loss ON/OFF | 학습 새 checkpoint? | 비고 |
| --- | --- | --- | :-: | --- |
| `full_model` | regime ✅, cp ✅, reveal ✅, shift ✅, state ✅ | 모두 ON | ✅ | 메인 모델 |
| `no_regime` | regime ❌ | λ_regime=0 | ✅ | PART3 §3.23.1 |
| `no_change_point` | cp ❌ | λ_cp=0 | ✅ | PART3 §3.23.2 |
| `no_reveal` (optional) | reveal ❌ | λ_reveal=0 | ✅ (선택) | |
| `no_state_aux` (optional) | state ❌ | λ_state=0 | ✅ (선택) | |

> **다음은 학습 variant가 아니라 evaluation-time planner swap** — checkpoint 새로 만들지 않음:
> Reactive / Fixed-k / Always-plan / Uncertainty gate / Novelty gate / Event-only gate / Adaptive lookahead / Sparse imagination / no action relevance / risk-only gate / no adaptation-correction distinction.

---

## 8. Session 8 — Loader / Event-Window Sampler TODO

### 8.1 핵심 책임

| TODO | 내용 |
| --- | --- |
| RG-4F dataset npz → batch dict 변환 | `falsifiable_regime_world_model.rg4f.dataset_io`의 `iter_episodes` / `load_episode`를 사용. |
| chunk extraction | `chunk_len = cfg.trainer.chunk_len`, `batch_size = cfg.trainer.batch_size`. |
| `action_prev_raw` alignment | episode 시작 step의 prev action은 0(=Action.W) 또는 별도 `<BOS>` token (vocab=16에 17번째 추가하지 않는 게 좋음; 0으로 채우고 `sample_weight[:, 0]=0` 또는 작게). |
| target 변환 | npz의 `dones`/`truncateds`를 OR하여 `done`. `actions_raw != actions_effective`를 `raw_eff_mismatch`. 나머지는 직접 mapping. |
| obs_*_target 정의 | 두 옵션: (a) 현재 obs와 동일 (auto-encoding) or (b) `next_observations_*` (next-step prediction). DreamerV3는 (b)에 가까움. Session 8가 결정. |
| padding mask | episode 끝이 chunk_len에 못 미치면 0으로 pad + sample_weight=0. |
| **event-window sampling** | change_point=1 또는 shift=1 step의 ±k window를 oversample. `k=5` 권장. 두 방식: (i) 해당 chunk의 sample_weight에 ×N, (ii) chunk 시작 위치를 event 주변에 sampling. (i)가 단순. |
| stage mix | random_2000 vs success_curriculum_v5_2000을 (1.0, 0.0) → (0.5, 0.5) → (0.3, 0.7)로 stage 진행에 따라 blend. |
| split guard | `train`, `valid` 외 split을 yield하면 즉시 raise. test_id/OOD를 학습 input으로 절대 흘리지 않는다. |
| metadata guard | `episode_meta.collector_metadata` 등 §6 금지 키는 batch dict에 포함되지 않도록 unit test. |
| 결정성 | `master_seed` 동일 시 동일 batch 순서. |

### 8.2 sampler 권장 hyperparameter

| hyperparameter | 권장 시작값 | 비고 |
| --- | --- | --- |
| `event_window_k` | 5 | change_point/shift 주변 ±5 step |
| `event_oversample_factor` | 5 | 기본 1.0 + event window에는 ×5 weight |
| `chunk_overlap_jitter` | True | chunk 시작 위치를 random offset |
| stage 1 블렌딩 비율 | random_2000:success_v5 = 100:0 | dynamics warmup |
| stage 2 비율 | 50:50 | reveal/interaction 혼합 |
| stage 3 비율 | 30:70 | reward/value/regime 강화 |

> 위 hyperparameter는 Session 8에서 ablation으로 검증한다.

---

## 9. Session 9 — Training Loop TODO

### 9.1 핵심 책임

| TODO | 내용 |
| --- | --- |
| optimizer | AdamW (DreamerV3 표준 또는 RAdam). `lr=3e-4` 권장 시작값. |
| lr scheduler | linear warmup ~1k step → constant 또는 cosine. |
| precision | yaml `trainer.precision` (`bf16` for medium). `torch.autocast` 사용. |
| grad clipping | `cfg.trainer.grad_clip` (default 100.0). |
| variant dispatch | `cfg.apply_variant(name)`로 5 variant 학습 schedule. |
| logging | `WMLossOutput.components` + `diagnostics` step별 기록. |
| valid evaluation | epoch 단위 valid total loss + per-component + change_point F1 + reward MSE. |
| early stop | valid total loss + change_point F1 plateau. |
| checkpoint | `(variant, seed, stage)` × 매 N step. |
| seed | 학습 단계 seed≥3, 최종 paper number seed≥10. |
| **train/valid only** | hard guard: split이 test_id/ood_*이면 학습 loop이 raise. |

### 9.2 학습 단계 (stage)

(WM_ARCHITECTURE_DESIGN §2.4와 일치)

| Stage | dataset 비율 | 비고 |
| --- | --- | --- |
| 1 — dynamics warmup | random_2000 100% | feature_dim 학습 안정화 |
| 2 — mixed | random_2000 50% + success_v5 50% | reveal/interaction 도입 |
| 3 — value/action-relevance emphasis | random_2000 30% + success_v5 70% | reward/regime/change_point 강화 |

---

## 10. Self-Audit

| Check | Status | Evidence |
| --- | :-: | --- |
| ref/PART0~3를 읽고 architecture novelty가 아님을 반영했는가 | PASS | `docs/WM_ARCHITECTURE_DESIGN.md` §1, `wm/README.md` §2, configs의 `paper_main` 플래그, variant 정책이 “head/loss만 끄고 capacity 동일”. |
| random_2000 / success_v5_2000 역할을 분리했는가 | PASS | `WM_ARCHITECTURE_DESIGN.md` §2.1–2.4 표 + 본 handoff §9.2. |
| train/valid만 학습에 쓰도록 명시했는가 | PASS | `WM_ARCHITECTURE_DESIGN.md` §2.3, 본 handoff §8 split guard, §9 train/valid only. |
| test_id/OOD 학습 금지를 명시했는가 | PASS | 본 handoff §8 / §9, `WM_ARCHITECTURE_DESIGN.md` §2.3. |
| collector metadata 금지 입력을 명시했는가 | PASS | 본 handoff §6 metadata exclusion 표, `WM_ARCHITECTURE_DESIGN.md` §3 / §13, `wm/README.md` §4. |
| weak-oracle collector가 model input이 아님을 명시했는가 | PASS | 본 handoff §6, `WM_ARCHITECTURE_DESIGN.md` §13. |
| RSSM/Dreamer-style backbone을 설계했는가 | PASS | `wm/rssm.py`의 `RSSMCore`/`TransitionPrior`/`RepresentationPosterior`, KL Dreamer-style + free nats + balancing in `wm/losses.py`. |
| hidden_dim=256을 debug용으로만 두었는가 | PASS | `configs/wm_debug.yaml: paper_main: false`, `meta.scale: debug`, README/문서에 명시. |
| main medium config를 만들었는가 | PASS | `configs/wm_medium.yaml: paper_main: true`, `deter_dim=512 / stoch_dim=128 / feature_dim=512 / batch=32 / chunk=128 / bf16`. |
| reward/done/state/regime/change/reveal/shift heads를 포함했는가 | PASS | `wm/heads.WMHeads`에 모두 포함. shape smoke에서 모두 OK. |
| change-point imbalance 대응을 loss/sampler 설계에 반영했는가 | PASS | `LossConfig.cp_pos_weight=50`, `cp_use_focal` 옵션, `λ_change_point=5.0`, sampler event-window는 Session 8 TODO §8.1로 명시. |
| no-regime / no-change-point ablation 학습 variant를 정의했는가 | PASS | `WMConfig.apply_variant("no_regime")` / `("no_change_point")` 검증; shape smoke에서 `no_regime` PASS. |
| planner/baseline/evaluator를 구현하지 않았는가 | PASS | imagine은 stub만 (prior-only). planner allocator/falsification/action relevance 코드 0줄. |
| training loop를 구현하지 않았는가 | PASS | optimizer.step / loss.backward는 `scripts/check_wm_shapes.py`의 sanity backward 1회만. dataset loader / replay / training script 0줄. |
| import 또는 synthetic shape smoke가 통과했는가 | PASS | `python -c "from falsifiable_regime_world_model.wm import RSSMWorldModel, WMConfig; print('wm import ok')"` ✅. `python scripts/check_wm_shapes.py --config configs/wm_debug.yaml` PASS (params 2.72M). `--config configs/wm_medium.yaml` PASS (10.70M). `--variant no_regime` PASS (2.57M). |
| docs/WM_ARCHITECTURE_DESIGN.md를 작성했는가 | PASS | 총 18절, ~13kB. PART0/1/2/3 정합 + dataset 사실 반영 + handoff. |
| docs/SESSION7_HANDOFF.md를 작성했는가 | PASS | 본 문서. |

**17 항목 모두 PASS.**

---

## 11. Smoke 명령 재현 절차 (사용자가 직접 실행)

```powershell
# import test
.\.venv\Scripts\python.exe -c "from falsifiable_regime_world_model.wm import RSSMWorldModel, WMConfig; print('wm import ok')"

# debug capacity shape smoke
.\.venv\Scripts\python.exe scripts\check_wm_shapes.py --config configs\wm_debug.yaml --batch 2 --time 8 --device cpu

# medium capacity shape smoke
.\.venv\Scripts\python.exe scripts\check_wm_shapes.py --config configs\wm_medium.yaml --batch 2 --time 8 --device cpu

# variant: no_regime smoke
.\.venv\Scripts\python.exe scripts\check_wm_shapes.py --config configs\wm_debug.yaml --batch 2 --time 8 --variant no_regime --device cpu

# (옵션) GPU 사용
.\.venv\Scripts\python.exe scripts\check_wm_shapes.py --config configs\wm_medium.yaml --batch 4 --time 16 --device cuda
```

각 명령은 forward output key/shape, 모든 component loss scalar, backward grad finite 여부, imagine API stub 출력 shape을 모두 통과해야 한다.

---

## 12. 다음 세션 진입점

1. **Session 8 — dataset loader + event-window sampler.** 본 handoff §8 TODO를 그대로 이행. forward batch dict / target dict / sample_weight를 만든다. `train`/`valid` 외 split는 절대 yield 금지. collector metadata 차단 unit test.
2. **Session 9 — training loop.** optimizer / scheduler / variant dispatch / checkpoint / logging. 5 variant × seed≥3 학습 schedule.
3. **Session 11+ — planner.** `RSSMWorldModel.imagine` 위에 alternative-regime conditioning, current-vs-alternative rollout 비교, falsification score, action relevance, compute reallocation.
