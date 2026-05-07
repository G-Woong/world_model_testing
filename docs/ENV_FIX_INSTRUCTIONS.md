# ENV_FIX_INSTRUCTIONS — RG-4F Environment Fix Priority

> Session 6 산출물 (2/4). 본 문서는 ENV_AUDIT_REPORT.md의 판정 결과에 따라
> "수정해야 한다면 무엇을, 언제, 어떻게 고칠지"를 우선순위 표로 분류한다.
> 본 세션은 코드 수정을 직접 수행하지 않으며 (Session 5에서 이미 inspect_episode.py
> em-dash 호환성 한 건 수정 완료, Session 6에서는 추가 수정 0건), 다음 페이즈에서
> 어떤 시점에 어떤 수정을 할지 결정 근거만 제공한다.

---

## 1. Fix Priority Table

| Priority | Issue | Impact | Fix timing | Target files | Recommendation |
|---|---|---|---|---|---|
| **P0** | (없음) | — | — | — | 월드모델 학습 단계로 즉시 진행 가능. |
| **P1** | train family filter 부재 → ood_factor_recomb 안티 disjoint | reviewer가 “train에서 family={2,3}을 우연히 학습했을 수도 있다”라고 공격 가능. ablation의 sharpness 약화 가능. | full experiments 전 (학습 시작 ~ ablation 사이) | `configs/dataset_default.yaml`, `scripts/generate_dataset.py` (15~30줄) | `train_apply_family_filter: bool` yaml flag + generator의 `_run_one_episode`에 train도 family filter 적용. |
| **P1** | random_biased + 학습용 dataset의 task room 진입 sparse | task-conditional dynamics head supervision 약화 가능. | 학습용 full dataset 생성 시 (학습 직전) | `configs/dataset_default.yaml` (1줄: episode_max_steps=600), `scripts/generate_dataset.py` (선택적 `task_probe` policy 추가 시 ~50줄) | 1차로는 episode_max_steps=600 + num_train=5000으로 해결 (config만). 2차로 task_probe policy 추가 검토 (학습 후 결정). |
| **P2** | change_point = shift_event 정의의 control_mode 누락 | reviewer가 “PART2 §3.10.3은 abrupt remap shift를 명시하는데 control_mode mid-episode 변화가 없다”라고 공격 가능. 단 reveal/shift 분리 라벨 존재. | 논문 robustness/ablation 단계 | `falsifiable_regime_world_model/rg4f/env.py` (~30줄) | event-triggered shift 시 일정 확률로 control_mode resample 추가. shift_event=True / change_point=True 동시 set. |
| **P2** | ood_obs_shift의 channel permutation 의미 한계 | reviewer가 “channel permutation은 visual variant가 아니다”라고 공격 가능. | 논문 robustness/ablation 단계 | `scripts/generate_dataset.py`의 `_apply_obs_channel_permutation` 확장 (~50줄) | cue 채널의 값 분포 변경 (예: cue intensity scaling, cue mask 변경) 추가 옵션. 또는 paper writeup에서 "input encoding shift"로 honest 명시. |
| **Defer** | inspect_episode의 ood_obs_shift inverse permutation 자동 적용 | 디버그 편의성. 학습에 영향 없음. | 필요 시 (사용자 요청 시) | `scripts/inspect_episode.py` | `--invert-channel-perm` 옵션 추가. low priority. |
| **No Fix** | object dtype field 한계 (Session 4 §6.4) | 의도된 안전장치. 모든 npz array가 numeric. | — | — | 수정 불필요. |
| **No Fix** | ASCII rendering 한계 (Session 4 §6.5) | 디버그 편의성만 영향. 학습에 무영향. | — | — | 수정 불필요. |

---

## 2. Specific Fix Instructions

### Issue 1 (P2). control_mode mid-episode abrupt remap을 change_point에 포함

#### Problem
현재 `env.py` L394는 `change_point = shift_event`로 정의되며, `shift_event`는 (a) field mu jump, (b) Task C `on_enter_room` initial_d set 두 트리거에 한정된다. 즉 episode 시작 시 sampling된 `control_mode`가 episode 동안 고정되어, `IDENTITY → CW` 같은 mid-episode abrupt remap이 데이터에 존재하지 않는다.

#### Why it matters
- PART2 §3.10.3은 “abrupt remap shift (identity → cw 등) 가능”을 명시.
- PART3 §3.21은 “small drift / abrupt shift 동시 처리”를 핵심 hard case로 둔다.
- reviewer가 "그 핵심 hard case가 dataset에 없으면 mechanism 검증이 무엇이냐"라고 공격 가능.

#### Current evidence
- smoke의 모든 episode `meta.json`의 `initial_regime.control_mode`가 episode 동안 변화하지 않음 (`true_regime_control_mode (T,)` array가 episode 내에서 constant).
- inspect 결과: train episode = IDENTITY 200 step, ood_room_perm episode = REV 200 step.

#### Recommended action

학습 단계에서 change-point head supervision이 약하다고 진단되면 다음 패치를 적용:

```python
# env.py의 step()의 ---- 4. 방 전환 & on_enter_room hook ---- 직후
# event-triggered control_mode shift 가능성 (방 진입 시)
# 기존 apply_event_shift는 field mu에만 작동하므로 control_mode resample은 별도로 처리.
if (
    self.config.enable_event_triggered_shift
    and new_room != prev_room
    and new_room in TASK_ROOM_IDS
    and self._rng.random() < self.config.shift_prob_per_room_entry_control_mode
):
    new_modes = [_STR_TO_CONTROL_MODE[m] for m in self.config.drift_abrupt_remap_modes
                 if _STR_TO_CONTROL_MODE[m] != self._regime.control_mode]
    if new_modes:
        new_mode = ControlMode(int(self._rng.choice([int(x) for x in new_modes])))
        self._regime.control_mode = new_mode
        shift_event = True
        debug.extras["control_mode_remap"] = {
            "from": int(prev_mode), "to": int(new_mode),
        }
```

추가로 `RG4FConfig.shift_prob_per_room_entry_control_mode: float = 0.10` 필드 추가.

#### Target files
- `falsifiable_regime_world_model/rg4f/env.py` (+~25 lines)
- `falsifiable_regime_world_model/rg4f/config.py` (+1 field)
- `configs/dataset_default.yaml` (선택적 — 명시 시 generator가 RG4FConfig.from_dict로 흘림)

#### Backward compatibility
- 기존 npz schema 영향: 없음 (`true_regime_control_mode (T,)`가 이미 시간 축 array이므로 mid-episode 변화도 그대로 저장).
- 기존 dataset 재생성 필요: **있음** (학습용 full dataset 생성 시).
- API 변경: 없음 (env.reset/step 시그니처 동일).

#### Verification command

```powershell
# 1. 코드 수정 후 smoke 재생성
python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\smoke --num-train 50 --num-valid 20 --num-test 20 --num-ood-per-type 20 --max-steps 200 --overwrite

# 2. validate strict
python scripts\validate_dataset.py --root data\smoke --strict --max-episodes-per-split 50

# 3. inspect: episode 1개에서 control_mode가 mid-episode 변화하는지 확인
python scripts\inspect_episode.py --root data\smoke --split train --index 0 --num-steps 200 --show-info
# stdout에서 t=k의 control_mode가 t=0과 다른 episode가 통계적으로 발생해야 함.

# 4. 통계
python scripts\plot_dataset_stats.py --root data\smoke --out outputs\smoke_stats_after_p2 --max-episodes-per-split 50
# change_point_distribution이 더 두꺼워지는지 확인.
```

---

### Issue 2 (P1). train family filter 부재 (ood_factor_recomb disjoint 강화)

#### Problem
- yaml `split_policy.factor_recomb.train_field_families: [0, 1]`은 metadata 라벨일 뿐, 실제로 generator가 train에 family filter를 강제하지 않는다.
- ood_factor_recomb는 강제로 `[2, 3]`만 사용하지만, train은 4 family `{0, 1, 2, 3}` 모두 sampling 가능.
- 결과: smoke train의 family 분포 = 4 family 모두 등장 (SMOKE §4.7).

#### Why it matters
- ood_factor_recomb의 reviewer 친화성이 약해진다 — “train에서 이미 family={2,3}을 봤는데 ood라고 부를 수 있느냐”.
- 단, validate 자체는 ood family ⊂ ood_pool만 검증하므로 schema invariant는 PASS.
- ablation에서 monolithic regime model이 train family overlap으로 ood에 일부 generalize 가능 → mechanism 효과의 sharpness 약화.

#### Current evidence
- SMOKE §4.7의 family 분포 표:
  - train: family 0=16, 1=23, 2=17, 3=18 (4 family 모두)
  - ood_factor_recomb: family 2=10, 3=15 ({2,3}만)
  - 즉 train ⊃ ood_factor_recomb의 family 집합.

#### Recommended action

option A (권장, 약 15줄). `configs/dataset_default.yaml`에 옵션 추가:

```yaml
split_policy:
  factor_recomb:
    enabled: true
    train_field_families: [0, 1]
    ood_field_families: [2, 3]
    train_apply_family_filter: true   # NEW: train도 family filter 강제
```

`scripts/generate_dataset.py._build_split_plans`에서 train/valid/test_id의 SplitPlan에도 `field_family_pool=train_families` (yaml flag가 true일 때만) 적용:

```python
# scripts/generate_dataset.py L405 부근
train_apply_filter = bool(factor_policy.get("train_apply_family_filter", False))
if s in ("train", "valid", "test_id"):
    plans.append(SplitPlan(
        ...,
        field_family_pool=train_families if train_apply_filter else None,
        ...,
    ))
```

option B. 옵션 추가하지 않고, paper writeup에서 “train에서는 4 family 자유 노출 + ood는 strict subset”이라고 honest 명시. (이 경우 코드 수정 0줄.)

#### Target files
- `configs/dataset_default.yaml` (+1 line)
- `scripts/generate_dataset.py` (+~10 lines, train SplitPlan에 family_filter 적용)

#### Backward compatibility
- 기본값 = `train_apply_family_filter: false` (현재 동작 유지) → 영향 없음.
- 명시적으로 `true` 설정 시 train family 분포 변경 → dataset 재생성 필요.
- npz schema 변경 없음.

#### Verification command

```powershell
# 1. 코드 수정 후 smoke 재생성
python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\smoke_p1_filtered --num-train 50 --num-valid 20 --num-test 20 --num-ood-per-type 20 --max-steps 200 --overwrite

# 2. validate strict
python scripts\validate_dataset.py --root data\smoke_p1_filtered --strict

# 3. 통계 확인 (train family 분포 = {0, 1}만이어야)
python scripts\plot_dataset_stats.py --root data\smoke_p1_filtered --out outputs\smoke_stats_p1 --max-episodes-per-split 50
# train_distributions.csv의 field family count: family_0과 family_1 (>0), family_2, family_3 (=0).
```

---

### Issue 3 (P1). random_biased + 200-step의 task room 진입 sparsity (학습용 full dataset에서 보강)

#### Problem
- smoke (max_steps=200, num_train=50, random_biased)에서 train의 모든 transition이 task=-1 (방 밖). 실제 task room 진입이 sparse.
- 원인: random_biased policy로 200-step 안에 4방 중 하나에 진입할 expected step 수가 50~100 step 수준 → 200-step은 task progression까지 도달하기에 부족.

#### Why it matters
- 환경 결함이 아니라 policy + episode_length 한계.
- 학습용 full dataset에서는 episode_max_steps 증가 + episode 수 증가로 통계적으로 해결 가능.
- 단 task supervision이 약하다면 task-conditional dynamics head가 학습 어려움.

#### Current evidence
- SMOKE §4.6: train의 task_id 분포가 모두 `-1`. 단 ood_factor_recomb (task=1: 79, task=2: 84) 등 일부 split에서 task=0/1/2 등장 (env_seed 차이로 일부 episode가 더 일찍 방에 도달).

#### Recommended action

**1차 (recommended)**: 학습용 full dataset 생성 시 다음 config 사용 (코드 수정 0줄):

```yaml
generation:
  num_train: 5000
  num_valid: 500
  num_test: 500
  num_ood_per_type: 500
  episode_max_steps: 600        # smoke의 200에서 3배 증가
  behavior_policy: random_biased
```

이는 yaml의 default값과 일치 (smoke에서만 CLI override로 200/50 사용). 600-step + 5000 episodes면 task room 진입이 episode당 평균 1.5~2회 발생 (random walk 추정).

**2차 (학습 후 진단 결과 task supervision이 약하면)**: `scripts/generate_dataset.py`에 `task_probe` behavior policy 추가:

```python
def _build_action_probs_task_probe(env, episode_step):
    """매 episode 시작 시 한 방향 random sampling 후 그 방향으로 향한다.
    방에 진입하면 random_biased로 전환. 단순한 epsilon-greedy.
    """
    # 단, PART0 §3 §6 "agent 코드 금지" 위반 방지를 위해 model-free + state-free
    # epsilon-greedy로 한정 — episode 시작 시 한 번 결정된 방향에만 의존.
```

#### Target files
- 1차: `configs/dataset_default.yaml` (수정 0줄, smoke override만 명시적으로 yaml default 사용 시 600/5000으로 복귀).
- 2차: `scripts/generate_dataset.py` (+~50 lines for task_probe policy).

#### Backward compatibility
- 1차: 영향 없음 (yaml default를 그대로 사용).
- 2차: behavior_policy=random_biased는 그대로 유지. 새 옵션 task_probe만 추가.

#### Verification command

```powershell
# 학습용 full dataset 생성 (사용자 명시적 실행 필요. 본 세션에서는 실행 금지)
python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\rg4f --num-train 5000 --num-valid 500 --num-test 500 --num-ood-per-type 500 --max-steps 600 --overwrite

# validate strict
python scripts\validate_dataset.py --root data\rg4f --strict --max-episodes-per-split 100 --json-report data\rg4f\validation_report.json

# task_id 분포 확인
python scripts\plot_dataset_stats.py --root data\rg4f --out outputs\rg4f_stats --max-episodes-per-split 200
# train_distributions.csv의 task_id count: task=0, 1, 2, 3 모두 >0이어야.
```

---

### Issue 4 (P2). ood_obs_shift의 channel permutation 의미 한계

#### Problem
ood_obs_shift는 현재 `local_grid`의 channel index permutation `[5,9,7,0,4,3,6,1,2,8]`만 적용. PART3 §3.21의 “tile/sprite/icon 표현이 다른 visual variant”와는 표현 방식이 다르다.

#### Why it matters
- novelty detector FP 검증 목적에는 channel permutation으로도 충분 (input distribution shift).
- 단 reviewer가 “이건 visual variant가 아니라 input encoding shift”라고 공격 가능.

#### Current evidence
- yaml `split_policy.obs_shift.cue_style_shift: true` (metadata flag만, 실제 cue 의미는 변경 없음).
- smoke `obs_channel_perm=[5,9,7,0,4,3,6,1,2,8]`의 ASCII rendering이 cue 채널 위치 변경으로 `?????` 표시 (디버그 편의성 한계).

#### Recommended action

option A (권장 — paper writeup만 변경, 코드 수정 0줄):
- paper writeup에서 “ood_obs_shift represents input encoding shift (channel permutation), which is sufficient to test novelty detector false positive without confounding with dynamics shift”라고 honest 명시.

option B (코드 확장 — 학습 후 reviewer 우려가 실제로 강해지면):
- `scripts/generate_dataset.py._apply_obs_channel_permutation`을 확장하여 cue 채널의 값 분포 변경 (예: cue intensity ×0.5 또는 cue mask shape 변경) 추가.

#### Target files
- option A: 없음 (paper writeup만).
- option B: `scripts/generate_dataset.py` (+~50 lines).

#### Backward compatibility
- option A: 영향 없음.
- option B: ood_obs_shift episode의 npz의 `observations_local_grid` 값 분포 변경 → dataset 재생성 필요. validate `no_dynamics_change` invariant는 그대로 PASS (dynamics는 변경 없음).

#### Verification command

```powershell
# option B 적용 시
python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\smoke_p2_visual --num-train 50 --num-valid 20 --num-test 20 --num-ood-per-type 20 --max-steps 200 --overwrite
python scripts\validate_dataset.py --root data\smoke_p2_visual --strict
# ood_obs_shift episode의 cue 채널 값이 train과 다른지 numpy로 직접 확인.
```

---

### Issue 5 (No-fix). true_state/true_regime schema 학습 head 충분성

#### Problem (실제로는 문제 아님)
- World model의 5-head supervision (state head, regime head, change-point head, observation reconstruction, value head)에 numeric encoding이 충분한가?

#### Current evidence
- `true_state (T, 5) float32`: state head의 regression target으로 직접 사용 가능.
- `true_regime_control_mode (T,) int32`: regime head의 classification target (5 classes).
- `true_regime_mobility_mode (T,) int32`: regime head의 classification target (3 classes).
- `true_regime_miscontrol_p (T,) float32`: continuous regime descriptor.
- `true_regime_periodic_slip (T,) bool`: binary classification.
- `change_point (T,) bool`: change-point head의 binary target.
- `reveal_event (T,) bool` + `shift_event (T,) bool` + `reveal_or_shift (T,) int32`: reveal/shift 분리 head 또는 합산 enum head 모두 가능.
- `task_id (T,) int32` (-1 for outside): task-conditional head의 classification target.
- `observations_local_grid (T, H, W, C)` + `next_*`: observation reconstruction head의 target.
- 모든 6개 reward component (`tick_cost`, `latency_cost`, `failure_cost`, `reset_cost`, `task_reward`, `completion_reward`): value head 또는 cost-decomposed head의 target.

#### Recommended action
**수정 불필요**. schema가 모든 학습 head에 충분한 numeric raw signal을 제공.

---

## 3. Minimal Patch Plan

### **P0 없음. 월드모델 학습 단계로 진행 가능.**

본 세션에서 환경/dataset 코드를 수정하지 않았다 (Session 5에서 inspect_episode.py em-dash 호환성 한 건 수정 후 재검증 완료. 그 외 0줄 변경).

학습 단계 진입 전 선택 사항:
1. (옵션) Issue 2 (P1) 적용 후 smoke 재생성 + validate strict + plot stats 1회. 약 10분.
2. (필수) 학습용 full dataset 생성: `episode_max_steps=600`, `num_train=5000` 등 (Issue 3 1차 안). 약 60~120분 (CPU 기준 추정).

학습 단계 진행 중 진단 결과에 따라:
- change-point head supervision이 약하면 → Issue 1 (P2) 적용.
- ood_obs_shift에 reviewer 우려가 강해지면 → Issue 4 (P2) option B 적용.
- 다른 모든 항목 (P2/Defer/No-fix)은 학습/실험 단계에서 결정.

다음 페이즈에서의 수정 순서 권장:
1. **WM Session 1 (RSSM/GRU-lite plan)**에서 Issue 2 적용 여부 결정.
2. **WM Session 2 (dataset loader + model code)** 직전 학습용 full dataset 생성 (Issue 3 1차 안).
3. **WM Session 3 (training loop)** 후 Issue 1 (change_point control_mode) 보강 여부 결정.
4. **WM Session 4 (world model evaluation)** 후 Issue 4 (channel permutation) 강화 여부 결정.
