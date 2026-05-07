# ENV_AUDIT_REPORT — RG-4F Environment / Dataset Final Audit

> Session 6 산출물 (1/4). 본 문서는 Session 1~5에서 만들어진 RG-4F 환경/데이터셋
> 생성 파이프라인이 PART0/PART1/PART2/PART3/RG4F_Environment_Plan과 일치하는지를
> 외부 reviewer 시각으로 전수 감사하고, 월드모델 학습 단계로 진입 가능한지를 판정한다.
> 본 감사는 코드의 동적 실행(validate strict, determinism check, inspect)으로 직접
> 검증된 evidence에 기반한다.

---

## 1. Executive Summary

### **최종 판정: CONDITIONAL PASS — 월드모델 학습 단계로 진행 가능.**

근거 요약 (5문장 이내):

1. `validate_dataset.py --strict --max-episodes-per-split 50`가 **PASS=2242 / WARN=0 / FAIL=0 / exit code 0** (Session 6에서 재실행 evidence: `data/smoke/validation_report_session6.json`).
2. determinism check가 **PASS=332 / WARN=0 / FAIL=0**으로 동일 yaml + seed → byte-equal 재현이 보장된다.
3. PART0~3 / RG4F_Environment_Plan의 모든 핵심 설계 (`local_obs_size=5` main + `[3,5,7]` ablation, 중앙홀+4방 cross 토폴로지, 5개 상태값, sparse coupling `|·|≤2`, mobility ↔ control-drift 분리, reveal vs shift 분리 라벨, 8개 split의 OOD invariant, deterministic seeding)가 코드와 dataset에 모두 일관되게 반영되어 있다.
4. 단, 두 개의 “학습 전 인지/보강 필요” 항목이 존재한다 — (a) `change_point = shift_event`는 field mu jump 위주로 정의되어 있고 control_mode mid-episode abrupt remap이 빠져 있으며 (b) random_biased + 200-step에서 task room 진입이 sparse하다. 두 항목 모두 환경 결함이 아니라 “학습용 dataset config + 학습 head 설계”에서 흡수 가능한 boundary issue이다.
5. 따라서 P0 blocker 없음. 본격 학습 단계 진입 가능. 해결 방향은 `ENV_FIX_INSTRUCTIONS.md`와 `RG4F_EXECUTION_GUIDE.md`에 분류되어 있다.

---

## 2. PART0~3 설계 대비 구현 정합성

### 2.1 정합성 표

| 논문 설계 요소 | 구현 위치 | 현재 상태 | 판단 | 근거 |
|---|---|---|---|---|
| Mechanism novelty (architecture novelty 아님) | `falsifiable_regime_world_model/rg4f/*` | 환경/dataset에 model/planner/agent 코드 0줄 | PASS | `Grep "torch"` 0건. world_model/planner 디렉토리 없음. |
| RSSM/GRU-lite controlled backbone main 전제 | (학습 페이즈 책임) | 환경 단계는 backbone-agnostic numeric supervision만 노출 | PASS | npz schema는 `true_state (T,5)`, `true_regime_*`, `change_point`, `reveal_event`, `shift_event` 등 backbone에 무관한 raw signal. |
| 중앙홀 9×9 + 4방 8×8 + 복도 length 3 cross 토폴로지 | `RG4FConfig.hall_size=9 / room_size=8 / corridor_length=3`, `map_generator.build_episode` | 일관 적용 | PASS | manifest `rg4f_config`에 동일 값 기록. inspect 시 agent (18,18)에서 시작 = `(corridor + room + 1) = 14` offset → central hall 중심 = 18. `full_h = 6 + 2·8 + 2·3 + 9 = 37`. |
| `local_obs_size = 5` 메인 | `RG4FConfig.local_obs_size: int = 5` (`config.py` L44) | 일관 적용 | PASS | yaml `local_obs_size: 5` (L54), manifest `rg4f_config.local_obs_size=5`, 모든 npz `observations_local_grid.shape=(T,5,5,10)`. |
| `local_obs_ablation_values = [3,5,7]` | `config.py` L46 + `__post_init__` 강제 | 일관 적용 | PASS | `__post_init__`이 `local_obs_size in {3,5,7}` 필수 강제. 7×7 main 고정 아님. |
| Hidden state ground truth (`true_state`) | `env._build_info()` → `info["true_state"]` (5 dim) → npz `true_state (T,5)` | 일관 적용 | PASS | dict→array 변환은 `serialization.EpisodeBuffer.append()`에서 `(v,m,i,n,d)` 순으로 stack. validate `numeric.true_state_range` PASS. |
| Hidden regime ground truth (`true_regime`) | `env._build_info()` → `info["true_regime"]` → npz `true_regime_control_mode/mobility_mode/miscontrol_p/periodic_slip_active` | 일관 적용 | PASS | factorized regime code (control + mobility + miscontrol + periodic) 모두 numeric 분리 저장. |
| Change-point ground truth | `env.step` line 394 (`change_point = shift_event`) → npz `change_point: bool[T]` | **CONDITIONAL** | reveal supervision은 충분, control_mode mid-episode abrupt remap 누락 | smoke에서 split별 `cp_mean=0.05~0.45`. shift_event 기반이므로 정의가 좁다. ENV_FIX 후보 #1. |
| Reveal vs Shift 분리 라벨 (PART1 §3.5) | `env._build_info`의 `info["reveal_event"]` / `info["shift_event"]` / `info["reveal_or_shift"]` (string enum) → npz `reveal_event/shift_event/reveal_or_shift (int)` | 일관 적용 | PASS | 두 채널이 별도 bool array + int enum {0=none,1=reveal,2=shift}. validate `numeric.reveal_or_shift_enum` PASS. |
| Task A — Weight-order + interaction calibration | `tasks.py` (build_task → TaskA), τ_i sampling `[-0.20, +0.20]` band 0.02 | PASS | `RG4FConfig.task_a_target_range`, `task_a_pickup_di_range` 등 모두 yaml 미명시 default로 적용. |
| Task B — Vision-positive stele + zero-mobility gate | `tasks.py` TaskB, `task_b_num_steles=4` / `task_b_num_positive=2` / `task_b_mobility_gate_half_width=0.02` / `vision_stable_ticks=2` | PASS | config default + `__post_init__` 검증 (`0 < num_positive < num_steles`). |
| Task C — Noise-zero stele + control-drift tracking | `tasks.py` TaskC, `task_c_num_steles_choices=(2,3,4)` / `task_c_initial_d_bins=(-0.70..+0.70)` / `task_c_noise_zero_half_width=0.02` | PASS | 방 진입 시 `on_enter_room`이 initial_d 강제 set. shift_event=True로 change_point에 기록. |
| Task D — Tile drift + zero-i altar + 3-fail forced reset | `tasks.py` TaskD, `task_d_num_tiles=4` / `tile_di_range=(-0.10,+0.10)` / `altar_half_width=0.02` / `fail_reset_threshold=3` | PASS | smoke의 ood_field_placement에서 `failure_max_mean=0.25` 발생 (Task D forced reset). |
| Control-drift 이산 remap (5 modes) | `env._CONTROL_REMAP` (identity/cw/lr/ud/rev) + `_sample_initial_regime` | PASS | inspect ood_room_perm: `control_mode=REV` → `raw=W eff=S`. SMOKE_REPORT §3.2.4. |
| Control-drift 약한 stochastic miscontrol | `env._apply_control_drift`: `if rng.random() < miscontrol_p: slip to neighbor` (90° L/R) | PASS | `miscontrol_p_low=0.05`, `_NEIGHBOR_ACTIONS` table. |
| Control-drift 주기적 slip (adaptation/correction hard) | `env.step` L223: `if step % periodic_K == 0: miscontrol_p = high` | PASS | smoke step 0,4,8,...에서 `miscontrol_p=0.300`, `periodic_slip=True` 확인. |
| Mobility ↔ control-drift 분리 (PART2 §3.10.2) | `env._compute_movement_cooldown` (mobility) ≠ `env._apply_control_drift` (control). info에 `mobility_mode` ≠ `control_mode` 별도 채널 | PASS | 두 함수가 서로 호출하지 않음. 채널 이름이 정확히 분리. |
| Sparse invisible field coupling `|coupled_states| ≤ 2` | `types.FIELD_COUPLED_STATES`, `RG4FConfig.field_coupling_max_dims=2` + `__post_init__` 강제, `fields.evaluate_field_effects` per-family | PASS | validate `sparse_coupling.le2` 모든 episode PASS (smoke 190 episodes). 4 family 모두 `(noise, X)` 2-tuple. |
| Field mean small drift | `fields.apply_small_drift`: `μ ← μ + N(0, σ_η)` | PASS | yaml `drift_strength: 0.01` → `field_mu_drift_sigma`. |
| Event-triggered field shift | `fields.apply_event_shift`: per-event prob에 따라 `μ ← μ ± δ` | PASS | yaml `shift_probability: 0.05` → 모든 `shift_prob_per_*`에 동일 적용. |
| Target band (default utility + local override, PART3 §3.17) | `tasks.BaseTask.get_target_band` + `env._current_target_band` → info `target_band` → npz `target_band_active/state_dim/center/half_width/kind` | PASS | enum kind: none/match_to_band/maximize/threshold/derivative_zero. |
| 8개 Split (train, valid, test_id, OOD 5종) | `scripts/generate_dataset.py._build_split_plans` | PASS | manifest `splits` = 8개. validate `split_coverage.all_present` PASS. |
| ood_room_perm disjoint (train ∩ ood = ∅) | `_build_permutation_pools`: 24개 shuffle 후 K개=train, 나머지=ood, `ood_use_disjoint=true` | PASS | manifest `train_pool ∩ ood_pool = ∅` (12+12). validate `split_specific.room_perm.disjoint_from_train` PASS. |
| ood_factor_recomb (family subset disjoint) | `_run_one_episode`의 `_filter_invisible_fields_by_family(env, [2,3])` + retry up to 8 | PASS | smoke의 ood_factor_recomb family 분포: `{2:10, 3:15}` (yaml `ood_field_families=[2,3]` 정확 강제). |
| ood_param_shift (drift_strength_multiplier=2.0 / shift_prob_multiplier=2.0 / field_radius_multiplier=2.0) | `_build_split_plans` L443 override dict | PASS | 5개 키 override: `field_mu_drift_sigma=0.02 (×2)`, `shift_prob_per_*=0.10 (×2)`, `field_radius_max=12.0 (×2)`. |
| ood_obs_shift (channel permutation, dynamics 동일) | `_apply_obs_channel_permutation(obs, channel_perm)` reset+step both | PASS | smoke `obs_channel_perm=[5,9,7,0,4,3,6,1,2,8]`. validate `channel_perm_valid` + `no_dynamics_change` PASS. |
| ood_field_placement (room interior 중심 placement) | `_maybe_relocate_fields_to_room_centers`: 4방 중심 ± 8-neighborhood traversable cells | PASS | smoke source positions `(30,18), (31,18)` = SOUTH room 중심부. validate `relocate_flag` + `source_in_grid` PASS. |
| npz + index.jsonl + manifest 저장 | `scripts/generate_dataset.py._generate_split` + `np.savez_compressed` | PASS | smoke 190 episodes 모두 `<split>/episodes/*.npz` + `*.meta.json` + `<split>/index.jsonl` + `manifest.json`. |
| Smoke validation strict PASS | `scripts/validate_dataset.py --strict` | PASS | Session 6 재실행: PASS=2242 / WARN=0 / FAIL=0 / exit code 0. determinism PASS=332. |
| `requirements.txt` 미변경 | git diff (변경 없음) | PASS | numpy 2.1.3 / pyyaml 6.0.3 / tqdm 4.67.3 / matplotlib (optional)만 사용. |
| ref/PART0~3 미변경 | git diff (변경 없음) | PASS | 0줄 변경. |

### 2.2 정합성 핵심 결론

- 환경 구현은 **PART0 §3 11개 금지사항** 모두 위반 없음 (Dreamer 코드 부재, magic number 부재, mobility ↔ control-drift 분리, reveal ↔ shift 분리, sparse coupling 강제, room-task permutation episode-level, train↔OOD disjoint).
- dataset schema는 향후 RSSM/GRU-lite 학습용 5-head supervision (state, regime, change-point, observation reconstruction, value)에 모두 충분한 numeric raw signal을 노출한다.
- 단 한 가지 **boundary issue**: `change_point = shift_event` 정의의 좁음 → §3.3, §6에서 분류.

---

## 3. Core Mechanism Support Audit

### 3.1 Hidden state support

- `true_state`는 `(T, 5)` float32 array로 npz에 저장. 순서 = `(vision, mobility, interaction, noise, control_drift)`.
- 매 step의 ground-truth가 그대로 노출되며 obs에는 직접 노출되지 않는다 (PART1 §3.3 contract 준수).
- `state_clip = [-1, +1]` 강제. validate `true_state_range`에서 max|x|<1.05 보장.
- World model의 **state head supervision**(예: regression head from latent z_t to (v,m,i,n,d))에 그대로 사용 가능.
- **부족한 점**: 없다. numeric raw signal로 충분.

### 3.2 Hidden regime support

- `true_regime`은 4개 numeric 채널로 분해 저장:
  - `true_regime_control_mode (T, int32)`: 0=IDENTITY..4=REV
  - `true_regime_mobility_mode (T, int32)`: 0=NORMAL/1=BURDENED/2=PERIODIC
  - `true_regime_miscontrol_p (T, float32)`: 0.05 또는 0.30
  - `true_regime_periodic_slip_active (T, bool)`
- 추가로 `episode_meta.json.field_info_static[*].family`에 invisible field family enum (0..3) 기록 → episode-level regime descriptor에 매핑.
- World model의 **regime head supervision** (factorized regime code: control × mobility × field-family)에 그대로 사용 가능.
- **부족한 점**: 없다. PART3 §3.23.7의 factorized regime code가 모두 분리된 채널로 저장.

### 3.3 Change-point support

- 현재 정의: `change_point = shift_event` (env.py L394). `shift_event=True`인 트리거는 다음 세 곳:
  1. `apply_event_shift`의 field mu abrupt jump (room_entry / checkpoint / stele_activation 시 prob에 따라).
  2. Task C의 `on_enter_room`에서 initial_d 강제 set (mid-episode 첫 진입 시).
  3. Task별 interact 결과 중 일부 (forced reset이나 stele 활성화).
- **부족한 점**: control_mode mid-episode abrupt remap이 change-point에 포함되지 않는다.
  - 현재 control_mode는 `_sample_initial_regime`에서 episode 시작 시 한 번 sampling 후 episode 동안 고정된다.
  - 즉 “episode 중간에 IDENTITY→CW로 갑자기 바뀐다” 시나리오가 데이터에 없다.
  - PART2 §3.10.3은 “abrupt remap shift (identity → cw 등) 가능”을 명시.
  - PART3 §3.21은 “small drift / abrupt shift 동시 처리”를 핵심 hard case로 둔다.
- **수정 vs 보류 판단**: **보류 (Defer)**. 근거:
  - reveal vs shift 분리 라벨이 이미 존재하므로 world model이 두 채널을 별도 head로 학습 가능.
  - shift_event는 field mu jump 위주이지만 episode-level cp_mean이 0이 아니라 각 split별 0.05~0.45로 발생함이 확인됨.
  - control_mode mid-episode remap을 추가하면 PART2 §3.10.3 정합성이 올라가지만, “학습 전 blocker”는 아니다.
  - 학습 단계에서 change-point head supervision이 약하다고 판단되면 그때 추가 가능 (env.py 변경 < 30줄).
- 따라서 `ENV_FIX_INSTRUCTIONS.md`의 P2 (논문 robustness/ablation 단계 수정).

### 3.4 Reveal vs Shift support

- `reveal_event`와 `shift_event`는 **별도 bool array**로 npz에 저장되며 동시에 합산된 `reveal_or_shift` int enum도 저장된다.
- reveal은 task interaction (예: Task A pickup, Task B stele toggle, Task D tile first touch) 시 `info[reveal_event]=True`로 발생.
- shift는 §3.3의 세 트리거에서 발생.
- smoke에서 split별 분포가 다르게 관찰됨 (`reveal_mean`이 train=0.00, test_id=2.70, ood_room_perm=2.85). 즉 reveal과 shift가 학습 가능한 **별도 supervision label**로 분리.
- **부족한 점**: 없다. 두 채널이 완전히 분리되어 있고, 모델이 reveal head + shift head를 별도로 학습 가능.

### 3.5 Falsification support

PART2 §3.7 (current vs alternative hypothesis 비교)에 필요한 evidence가 dataset에 모두 있는가?

- **recent observation-action window**: ✓
  - `observations_local_grid (T, 5, 5, 10)` + `observations_scalar (T, 14)` + `observations_event_token (T,)` + `next_observations_*` 모두 step 단위로 저장.
  - sliding window를 dataset loader에서 (T-W, W) 형태로 만들기 충분.
- **actions_raw vs actions_effective**: ✓
  - npz에 두 array가 별도 저장. control-drift remap 결과를 모델이 직접 관찰 가능.
- **true_regime timeline**: ✓
  - control_mode/mobility_mode/miscontrol_p/periodic_slip가 (T,) 단위 numeric.
  - alternative regime hypothesis 학습 시 각 step에서 “실제 regime”과 “모델 belief”의 divergence 비교 가능.
- **부족한 점**: 없다. PART2 §3.7의 likelihood ratio + change-point posterior 구현에 필요한 ground-truth가 모두 존재.

### 3.6 Action relevance support

PART2 §3.8 (Q/value 학습용 reward/cost decomposition + action flip 분석)에 필요한 데이터:

- **reward decomposition**: ✓ — npz에 6개 component 분리 저장:
  - `tick_cost`, `latency_cost`, `failure_cost`, `reset_cost`, `task_reward`, `completion_reward`.
  - `rewards = sum of components` (signs는 cost = -, reward = +).
- **target_band**: ✓ — `target_band_active/state_dim/center/half_width/kind`. world model의 cost-sensitive value head 학습 가능.
- **failure_count**: ✓ — `failure_count (T, int32)` 누적 저장.
- **reset_flag**: ✓ — `reset_flag (T, bool)`. (Session 3 contract: episode 시작 reset만 True; step 안에서 발생하는 forced reset은 reset_cost > 0 + event_token=FORCED_RESET으로 식별.)
- **action flip 분석**: 가능. `actions_raw[t]`와 `actions_effective[t]`가 분리 저장되어 있고, current vs alternative 모델 hypothesis 하의 `argmax_a Q(s, a)` 비교는 학습 후 분석 가능.
- **부족한 점**: 없다.

---

## 4. OOD Validity Audit

### 4.1 OOD 종합 표

| OOD split | 구현 방식 | 논문적 의미 | 충분성 | 리스크 | 수정 필요 여부 |
|---|---|---|---|---|---|
| `ood_room_perm` | train_pool(12) ∩ ood_pool(12) = ∅, episode마다 ood_pool에서 forced_permutation sampling. `_build_permutation_pools`가 master_seed 기반 deterministic split. | **위치 암기 vs task rule 이해** 분리. agent가 "북쪽 방 = Task A"를 외웠는지 검증. | 충분 | 없음 — 24!/2 = 12 disjoint permutations. validate가 episode-level disjoint도 검증. | 수정 불필요. |
| `ood_factor_recomb` | yaml `train_field_families=[0,1]` (라벨), `ood_field_families=[2,3]` (강제). ood split만 family filter `[2,3]` 강제 + retry 8회. | **factorized regime 일반화**. monolithic regime 모델이 약해야 함. | **부분 충분**. ood split은 `[2,3]`에 강하게 제한되지만 train은 4 family 자유 — 약간의 안티 disjoint. | 학습 시 monolithic regime model이 train family overlap으로 ood에 일부 generalize 가능 → ablation의 sharpness가 약해질 가능성. | 권장 (P1) — yaml에 `train_apply_family_filter` 추가하면 ood_factor_recomb의 disjoint가 더 엄격해진다. 단, 현재도 family={2,3}만 보이도록 강제되므로 학습 전 boundary issue. |
| `ood_param_shift` | 5개 key override × 2.0 (drift/shift/radius) | **scale/intensity 일반화**. | 충분. validate `differs_from_train` PASS. | 너무 강하면 그냥 다른 환경이 되고, 너무 약하면 OOD가 아님. ×2.0은 적정. | 수정 불필요 (학습 후 결과 보고 ×3.0/×1.5 ablation 추가 가능). |
| `ood_obs_shift` | local_grid의 channel index permutation `[5,9,7,0,4,3,6,1,2,8]`. dynamics 변경 없음. | **novelty detector false positive** 검증. | 충분 (단, "tile/sprite 변경"보다는 약한 표현). | reviewer가 "channel permutation은 너무 artificial"이라고 공격할 가능성. | 수정 보류 (P2). novelty FP 검증 목적에 channel permutation은 실제로 충분 — agent의 input distribution은 변하지만 underlying dynamics는 그대로. paper writeup에서 명시하면 방어 가능. |
| `ood_field_placement` | invisible field source를 4방 중심 ± 8-neighborhood traversable cell로 강제 이동. | **hidden field belief의 spatial generalization**. | 충분. train은 free placement, ood는 room-center concentration → 다른 spatial prior. | 만약 train 분포에서 우연히 room-center placement가 자주 발생했다면 disjoint가 약해질 수 있음 — 그러나 train의 free placement는 grid 전체에서 sampling하므로 통계적으로 안전. | 수정 불필요. |

### 4.2 OOD 깊이 판단

- **ood_room_perm은 train permutation과 disjoint인가?** 예. `_build_permutation_pools`가 master_seed 기반 shuffle 후 첫 K=12 = train, 나머지 12 = ood. validate가 episode-level forced_permutation을 train_pool 멤버십으로 검증.
- **ood_factor_recomb가 충분히 강한 OOD인가?** 부분적으로. ood는 `{2,3}`만 강제되지만 train은 `{0,1,2,3}` 전부 sampling 가능 → ood family가 train에서도 보일 수 있다. 단, 이는 reviewer 친화적 설명("train에서는 4 family 자유 노출, ood는 strict subset")이 가능하므로 paper에 명시 시 honest. 더 strict한 disjoint를 원하면 P1 수정.
- **ood_obs_shift가 단순 channel permutation으로 충분한가?** novelty detector FP 검증 목적에는 충분. 단, "visual variant"에 대한 더 풍부한 표현(예: cue 채널 값 분포 변경)은 P2 수정으로 둔다.
- **ood_field_placement가 실제 field prior shift인가?** 예. train은 grid 전역 random, ood는 4방 중심 ± 8-neighborhood. Spatial prior가 명확히 다름.
- **parameter shift가 너무 강하거나 약하지 않은가?** ×2.0은 적정. drift_strength=0.01→0.02, shift_probability=0.05→0.10, field_radius_max=6→12. 학습 후 결과를 보고 ×3.0 / ×1.5 두 단계 추가 ablation 가능.

---

## 5. Data Collection Policy Audit

### 5.1 random_biased policy 적정성

- `_build_action_probs("random_biased")` 분포: movement 55% / E 15% / state-adjust 30% / WAIT 0%.
- 이 분포는 다음을 보장한다:
  - 4-방향 이동이 충분히 발생 → control-drift remap effect 관측 가능.
  - state-adjust action이 30% → 5개 상태값이 episode 동안 변화하여 dynamics learning supervision 강화.
  - E (interact) 15% → invalid context에서도 반복 시도하여 eventual task-room interaction 발생 가능.
  - WAIT 0% → world model dynamics 학습에 무의미한 transition 회피.

### 5.2 200-step smoke의 task room 진입 sparsity

- `data/smoke/`: max_steps=200, train 50 episodes, behavior=random_biased.
- 결과 (SMOKE_REPORT §4.6): train 10000 transitions 중 task=-1 (방 밖)만 등장. ood_factor_recomb (task=1: 79, task=2: 84) 등 일부 split에서만 task=0/1/2 등장.
- 원인: random_biased policy로 200-step 안에 4방 중 하나에 진입하기까지의 expected step 수가 50~100 step 수준. 즉 200-step은 task room 진입 + 다단계 task progression까지 도달하기에 부족.
- **단, 이는 환경 결함이 아니라 smoke dataset 한계**.
- World model의 **state dynamics learning**(state-adjust effect, drift accumulation, control-drift remap, periodic slip, field effect)에는 현재 smoke로도 충분한 supervision이 모인다.
- World model의 **task-conditional dynamics learning** (task_id별로 분기되는 dynamics)을 강하게 학습하려면 더 긴 episode + 더 많은 episode가 필요.

### 5.3 학습용 full dataset의 권장

- `episode_max_steps=600` (yaml `RG4FConfig.episode_max_steps: int = 600` default. smoke는 CLI override로 200으로 줄임.)
- `num_train=5000`, `num_valid=500`, `num_test=500`, `num_ood_per_type=500`.
- 600-step + 5000 episode면 task room 진입이 통계적으로 충분히 발생 (각 episode당 평균 1.5~2회 task room 진입 추정).
- **task_probe policy 추가 여부**: 보류 (P1/Defer). 단순 random_biased가 boundary 가깝게는 작동하므로, 학습 후 task supervision이 약하다고 판단되면 그때 추가하는 것이 ROI 측면에서 합리적.

---

## 6. Known Limitations Reassessment

Session 4/5에서 식별된 6가지 limitation을 재평가한다.

| 항목 | 논문 주장에 치명적? | 학습 전 수정? | Session 6에서 수정? | 학습/실험 단계로 넘김? |
|---|---|---|---|---|
| **train family filter 부재** (Session 4 §6.1, SMOKE §5.6) | 약간 있음. ood_factor_recomb의 disjoint가 reviewer 친화적이지 않음. | 권장 (P1) | 수정 보류 (논문 writeup honest 명시로 방어 가능) | 학습 단계에서 결정 |
| **channel permutation의 의미 한계** (Session 4 §6.2) | 약함. novelty FP 검증 목적은 달성. | 보류 (P2) | 수정 안 함 | 논문 writeup에서 명시 |
| **change_point = shift_event 정의 한계** (Session 4 §6.3) | 약함. control_mode mid-episode remap이 빠짐. 단 reveal/shift 분리 라벨 존재. | 권장 (P2) | 수정 안 함 | 학습 후 change-point head supervision이 약하면 그때 추가 (env.py 30줄 미만 수정) |
| **object dtype field 한계** (Session 4 §6.4) | 없음 (의도적 안전장치) | 불필요 | 수정 안 함 | N/A |
| **ASCII rendering 한계** (Session 4 §6.5) | 없음 (디버그 편의성) | 불필요 | 수정 안 함 | 학습에 영향 없음 |
| **random_biased + 200-step의 task room 진입 sparse** (SMOKE §4.6) | 없음 (policy 한계, 환경 결함 아님) | 학습용 full dataset 생성 시 episode_max_steps=600 + num_train=5000으로 해결 | 수정 안 함 (smoke는 의도된 작은 규모) | 학습 단계에서 dataset config로 해결 |

### 6.1 새로 식별된 항목 (Session 6 감사)

추가로 본 감사에서 새로 발견된 사항: **없음**.

코드 전수 감사 결과 Session 4/5에서 보고된 6항목 외에 새로운 결함이나 inconsistency는 발견되지 않았다.

---

## 7. Final Audit Verdict

- **Overall verdict: CONDITIONAL PASS — 월드모델 학습 단계로 진행 가능.**
- **Must-fix before world model training (P0)**: 없음.
- **Should-fix before full experiments (P1)**:
  - `train_apply_family_filter` 옵션 추가 (ood_factor_recomb disjoint 강화). ENV_FIX 후보 #2.
  - `task_probe` 또는 `task-aware` behavior policy 옵션 추가 검토 (학습용 full dataset의 task supervision 강화). ENV_FIX 후보 #3.
- **Can-defer (P2)**:
  - control_mode mid-episode abrupt remap 추가 (change_point 정의 보강). ENV_FIX 후보 #1.
  - cue_style_shift의 의미 강화 (channel permutation 외 cue 값 분포 변경). ENV_FIX 후보 #4.
- **No-action-needed**:
  - 현재 dataset schema (npz/index.jsonl/manifest/episode_meta) — 학습 head에 충분한 numeric raw signal 노출.
  - sparse coupling 강제 — `__post_init__` + validate가 이미 강제.
  - reveal vs shift 분리 — 코드/schema 모두 분리되어 있음.
  - mobility ↔ control-drift 분리 — 코드 / info / npz 모든 레벨에서 분리.
  - deterministic seeding — `--check-determinism` PASS.
  - 8개 split의 OOD invariant — `--strict` PASS=2242 / FAIL=0.

---

## 8. Session 6 재검증 Evidence

본 감사의 정량적 근거:

| 명령 | 결과 | 파일 |
|---|---|---|
| `validate_dataset.py --strict --max-episodes-per-split 50 --json-report ...session6.json` | PASS=2242 / WARN=0 / FAIL=0 / exit code 0 | `data/smoke/validation_report_session6.json` |
| `validate_dataset.py --check-determinism --config configs/dataset_default.yaml --max-episodes-per-split 3` | PASS=332 / WARN=0 / FAIL=0 / exit code 0 (byte-equal 재현) | (in-memory; 임시 dir 자동 삭제) |
| `inspect_episode.py --root data/smoke --split train --index 0 --num-steps 3 --show-grid --show-info` | metadata + transition + step-level 정상 출력. control_mode=IDENTITY. forced_permutation=[2,0,3,1] ⊂ train_pool. | stdout |
| `inspect_episode.py --root data/smoke --split ood_room_perm --index 0 --num-steps 3 --show-grid --show-task --show-fields` | metadata + transition + step-level 정상 출력. control_mode=REV (4). forced_permutation=[3,1,2,0] ∉ train_pool. raw=W eff=S 변환 확인. | stdout |

모든 재검증이 PASS. 환경/dataset 생성 페이즈는 다음 단계(월드모델 학습)로 진입 가능한 상태.
