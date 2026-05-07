# RG-4F Environment Plan

> 본 문서는 RG-4F (RegimeGrid-4Room Factorized Tasks) 환경의 코드 구현 직전 단계 사양을 고정한다. PART1/2/3의 정신과 충돌하지 않으며, PART3 §3.16의 일부 기본값(특히 `local_obs_size`)을 본 문서에서 더 엄격한 값으로 갱신한다. 본 문서가 정의한 값과 다른 hard-coded 수치를 코드에 박는 것은 PART0 §3 금지사항 위반이다.

---

## 1. RG-4F 환경 목적

RG-4F는 “복잡한 2D 게임”을 만들기 위한 환경이 아니다. 이 환경은 **wrong-hypothesis-aware world-model planning이 baseline보다 강한 순간을 분해해서 증명**하기 위해 의도적으로 단순화되고 통제된 mechanism benchmark다.

본 환경의 핵심 가치는 다음에 있다.

1. **geometry complexity를 의도적으로 낮춘다.** 미로/맵 자체로 어렵게 만드는 환경이 아니다. 벽 배치를 어렵게 만드는 것이 목적이라면 굳이 RG-4F를 새로 설계할 필요가 없다.
2. **compositional regime complexity를 통제 가능한 방식으로 높인다.** Task A/B/C/D는 각각 다른 factor family (mobility-interaction, vision-mobility, noise-control, interaction-noise)를 자극한다. invisible field는 sparse coupling으로 제한된다. drift는 small cumulative와 abrupt event-triggered가 동시에 존재한다.
3. **중앙홀 + 4방 구조는 “단순한 공간 + 복잡한 규칙”의 분리를 가능하게 한다.** 모든 episode가 같은 토폴로지에서 시작하므로 spatial confound가 통제되고, 그 위에 task permutation, parameter randomization, factor recombination, invisible placement OOD를 얹어 dynamics-level generalization을 검증할 수 있다.

### 1.1 “맵이 단순하다”는 reviewer 공격에 대한 방어

RG-4F의 단순한 토폴로지는 결함이 아니다. 본 환경은 다음 5가지 차원에서 복잡도를 가진다.

- **Task permutation**: room-task assignment가 episode마다 sampling되며 train/test 간 disjoint permutation을 강제한다. 즉 “북쪽 방 = Task A”라는 위치 암기가 불가능하다.
- **Factor recombination**: regime factor (vision, mobility, interaction, noise, control-drift)가 train에서 본 조합 밖에서 다시 조합되어 OOD를 만든다.
- **Parameter shift**: 같은 dynamics family의 수치 범위가 train/test에서 다르게 sampling된다.
- **Observation shift**: tile/sprite/icon 표현은 바뀌지만 underlying rule은 그대로인 변형이 OOD에 포함된다.
- **Invisible sparse field placement**: hidden field source의 수, 위치, radius prior가 train/test에서 다르다.

이 다섯 축이 결합될 때, 단순한 4방 토폴로지는 사실상 매우 큰 dynamics-level 조합 공간이 된다.

또한 small cumulative drift, abrupt event-triggered shift, periodic disturbance, hidden local hazard의 4가지 drift/shift scenario(PART3 §3.21)가 환경 내부에서 동시에 가능하다. 이는 “복잡한 미로 풀기”와는 완전히 다른 종류의 어려움이다.

---

## 2. 월드맵 구조

본 절의 모든 수치는 `configs/dataset_default.yaml`의 default값으로 노출되며, 코드에 hard-coded 되어서는 안 된다.

### 2.1 공간 사양

- **중앙홀(`central_hall`) 크기**: `9 x 9` (셀 단위, traversable 내부 영역 기준).
- **북/남/동/서 4방(`room_north`, `room_south`, `room_east`, `room_west`) 크기**: 각 `8 x 8` (traversable 내부 영역 기준).
- **연결 복도(`corridor`) 길이**: 각 방향 `3` (셀 단위).
- **벽 두께**: 1 (각 영역 외곽).
- **시작 위치**: 중앙홀 중심 셀.
- **방 완료 후**: 자동으로 중앙홀 중심으로 복귀(또는 복귀 강제 이벤트로 처리). 복귀는 1 tick의 reset cost를 부과한다.
- **전체 목표**: Task A, B, C, D 4개 모두 완료. 각 task는 정확히 하나의 방에 episode마다 sampling된다.

### 2.2 토폴로지 다이어그램 (개념)

```
                +---------+
                |  ROOM   |
                |  NORTH  |
                | 8 x 8   |
                +----+----+
                     |
                  corridor
                  length 3
                     |
+--------+      +----+----+      +--------+
|  ROOM  |---c--| CENTRAL |--c---|  ROOM  |
|  WEST  |      |  HALL   |      |  EAST  |
| 8 x 8  |      |  9 x 9  |      | 8 x 8  |
+--------+      +----+----+      +--------+
                     |
                  corridor
                  length 3
                     |
                +----+----+
                |  ROOM   |
                |  SOUTH  |
                | 8 x 8   |
                +---------+
```

(c = corridor)

### 2.3 episode-level goal

PART3 §3.15.1을 따르되, room-task permutation을 명시적으로 둔다.

- 각 episode 시작 시 4개의 방에 4개의 task가 무작위 permutation으로 배정된다.
- permutation은 `4! = 24` 후보 중 split-aware 방식으로 sampling된다 (train/test 간 disjoint, §6 split 설계 참조).
- 모든 task가 완료되어야 episode가 성공한다.
- `episode_max_steps`(기본값 §7) 내에 완료하지 못하면 실패로 종료한다.

---

## 3. 부분관측 구조

### 3.1 핵심 결정: `local_obs_size = 5` (메인 세팅)

PART3 §3.16.1은 local observation을 `7 x 7`로 두었다. 본 문서에서는 이 값을 **메인 세팅에서 `5 x 5`로 갱신**한다. 사유는 다음과 같다.

- 한 방 크기가 `8 x 8 = 64`칸이다. `7 x 7 = 49`칸 관측 시, 한 방의 약 **76.5%**를 한 시점에서 볼 수 있다. 즉 agent는 거의 “방 한 칸 안에서 거의 다 보이는” 수준이 된다.
- 이 정도 가시성이면 agent는 hidden state belief를 거의 유지할 필요가 없다. local cue를 그냥 “현재 보이는 풍경”으로 처리할 수 있고, 이는 hidden state / hidden regime 분리의 필요성을 약화시킨다.
- `5 x 5 = 25`칸 관측은 한 방의 약 **39.1%**만 보여준다. 이 정도가 “주변 풍경은 보이지만 방 전체와 hidden field source는 보이지 않는다”에 해당하는 적정 partial observability다.

따라서 본 문서는 다음을 확정한다.

- **메인 세팅**: `local_obs_size = 5` (`5 x 5` window).
- **Easy / visibility ablation**: `local_obs_size = 7` (`7 x 7`). 가시성이 높아 hidden state tracking 압력이 약한 비교 조건.
- **Hard / limited-visibility ablation**: `local_obs_size = 3` (`3 x 3`). 극단적 부분관측. blind trial-and-error에 가까워지지 않도록 §3.4 cue 가시성 조건과 함께 검증한다.
- **지원 ablation 집합**: `local_obs_ablation_values = [3, 5, 7]`.

### 3.2 관측 구성

PART3 §3.16과 동일하되 차원과 채널을 명시한다.

```
o_t = (o_t^local, o_t^scalar, e_t)
```

- `o_t^local ∈ R^{H x W x C}` with `H = W = local_obs_size` (기본 5). 채널 `C`는 다음을 포함한다 (config로 on/off 가능, 기본 활성):
  - `wall_mask`
  - `corridor_mask`
  - `room_id_onehot` (어느 방 영역인지, 4 방 + 중앙홀 + 복도)
  - `agent_self_position` (window 내 agent 위치 mask)
  - `object_layer` (조각/stele/altar/door/tile 등 task object)
  - `local_cue_layer` (Task별 weak cue. §5 참조. cue 가시성은 vision level에 따라 mask가 가려질 수 있음)
  - `traversable_mask`
  - `interaction_target_marker` (해당 셀에서 interaction이 가능한지)
- `o_t^scalar ∈ R^d`:
  - 5차원 상태 벡터 `x_t = (v_t, m_t, i_t, n_t, d_t) ∈ [-1, 1]^5`
  - `room_id` (현재 위치한 방 id, central_hall 포함)
  - `completed_count` (완료된 task 수, 0~4 정수)
  - `fail_count` (실패한 interaction 누적, task별로도 분리 가능)
  - `step_norm` (`t / episode_max_steps`)
  - `carrying_weight` (Task A의 조각 운반 시 현재 들고 있는 조각의 weight, 그 외에는 0)
- `e_t ∈ E`: discrete event token. enum으로 정의한다.
  - `NONE`, `ROOM_ENTRY`, `ROOM_EXIT`, `INTERACTION_SUCCESS`, `INTERACTION_FAIL`, `CHECKPOINT`, `DOOR_OPEN`, `STELE_TOGGLE`, `TILE_FIRST_TOUCH`, `FORCED_RESET`, `CARRY_PICKUP`, `CARRY_DROP`, `TASK_COMPLETE`.
- 전체 맵, hidden field source의 정확한 위치, regime label, change-point ground truth는 **관측에 포함되지 않는다**. 이들은 info/metadata에만 기록된다.

### 3.3 5x5 안에서 cue 가시성을 보장한다

부분관측을 강하게 만들되 blind trial-and-error로 빠지면 mechanism 검증이 무너진다. 따라서 다음 원칙을 둔다.

- 각 task의 핵심 local cue는 agent가 5칸 이내로 접근하면 관측 가능하도록 배치한다.
- cue는 약하게 주어진다. 즉 정확한 target band 수치(`τ_i`, `τ_n` 등)를 cue가 직접 표시하지 않는다. cue는 “이 방향 / 이 패턴이 의미 있다”는 약한 hint만 준다.
- vision level이 낮으면 cue가 부분적으로 가려질 수 있다. 그러나 vision이 적정 수준이면 5x5 안에서 cue가 보인다.

이 원칙은 “5x5라서 너무 어렵지 않은가?”라는 우려를 “5x5 안에 cue가 들어오므로 hidden state belief + 최근 action outcome으로 추론 가능하다”는 형태로 닫는다.

### 3.4 hidden state / hidden regime 추적이 왜 필요한가?

- 전체 맵이 가려지므로 “방 안에 어떤 object가 있는가”는 hidden state다.
- field source의 위치, coupling 형태는 직접 관측되지 않으므로 hidden state다.
- task permutation, target band, drift schedule은 episode마다 다르며, 관측에 직접 노출되지 않는다. 따라서 “현재 어떤 dynamics regime가 활성화되어 있는가”는 hidden regime다.
- `5 x 5` window + scalar + event token만으로는 “방금 일어난 변화가 reveal인지 shift인지”를 단일 step에서 판정할 수 없다. 따라서 짧은 evidence window 위에서 likelihood ratio + change-point posterior를 추적해야 한다.

이 구조가 PART1 §3.3 ~ §3.5의 latent ontology를 환경 차원에서 강제하는 장치다.

---

## 4. 5개 상태값

상태값 `x_t = (v_t, m_t, i_t, n_t, d_t) ∈ [-1, 1]^5`는 **항상 0으로 유지해야 하는 값이 아니다.** 초기값 `(0, 0, 0, 0, 0)`은 episode baseline일 뿐이며, 전역적으로는 default utility 방향으로 움직이는 게 유리하지만 특정 local condition에서는 target band가 우선한다 (PART3 §3.17, §3.19).

각 상태값은 다음 5개 항목으로 정의한다.

### 4.1 Vision (`v_t`)

- **기본 의미**: agent가 local map을 얼마나 넓고 선명하게 볼 수 있는가. cue 가시성과 관측 mask에 영향을 준다.
- **전역 default utility**: vision이 높을수록 정보 획득이 빠르고 wrong-stele/hazard 회피가 쉬워진다. 따라서 default utility는 `+w_v · v_t` 형태로 모델링된다.
- **local override**: Task B의 “마지막 2 tick 동안 vision 변화 없음” 조건. 이 순간에는 vision을 키우는 것보다 안정화시키는 것이 우선이다. local override가 활성화되면 default utility 가중치가 줄고 target band 조건이 우세해진다.
- **target band 연결**: 일반적으로 vision은 maximize-type이지만, Task B에서는 “derivative 조건” (`Δv_{t-2:t} = 0`)이라는 변형 target band를 가진다.
- **잘못 추정될 때의 cost**: cue를 늦게 발견하여 episode length 증가, wrong stele 선택, hazard hint 미감지로 forced reset, observation 변화를 regime shift로 오해.
- **drift/shift와의 연결**: vision은 visibility field와 sparse coupling될 수 있다 (`noise + vision`). field mean drift 시 vision이 천천히 흔들리고, event-triggered shift 시 한 번에 변할 수 있다.

### 4.2 Mobility (`m_t`)

- **기본 의미**: 이동 효율 = 같은 방향 이동에 걸리는 cooldown/latency. 이동 방향이 바뀌는 것이 아니다(이건 control-drift다).
- **전역 default utility**: 보통 mobility가 높으면 episode length가 줄어 step cost가 감소한다. default utility는 `+w_m · m_t`.
- **local override**: Task B의 zero-mobility gate(`m_t ∈ [-0.02, +0.02]`). 문 앞에서는 “느리거나 멈춰 있어야” 문이 열린다. 이때는 maximize가 아닌 match-to-band가 우세하다.
- **target band 연결**: 대부분 maximize-type이지만 특정 gate에서는 match-to-band(`τ_m = 0`)로 전환.
- **잘못 추정될 때의 cost**: 도착 시간 오추정, interaction timing 실패, gate 미충족, correction 여부 오판, 이동 cooldown 누적.
- **drift/shift와의 연결**: friction field와 sparse coupling(`noise + mobility`). 또한 Task A의 조각 운반 시 `Δm = -w_j` 형태의 deterministic state shift (이건 regime shift가 아니라 state-level 변화).

### 4.3 Interaction (`i_t`)

- **기본 의미**: object/stele/altar/door와 상호작용할 때 필요한 강도/calibration 상태. interaction latency가 `|i_t - τ|`에 비례.
- **전역 default utility**: 일반적으로 interaction 안정성이 높으면 시간이 줄어든다. default utility는 약하게 `+w_i · i_t` 또는 `-w_i · |i_t|` 형태로 모델링 가능.
- **local override**: Task A 최종 altar의 `i_t ∈ [τ_i - 0.02, τ_i + 0.02]`, Task D 최종 altar의 `i_t ∈ [-0.02, 0.02]` 같은 정밀 match-to-band.
- **target band 연결**: 대부분의 task에서 interaction은 정밀 match-to-band가 핵심이다.
- **잘못 추정될 때의 cost**: interaction latency 증가, 실패 interaction 누적, forced reset, final altar 실패.
- **drift/shift와의 연결**: interaction interference field와 sparse coupling (`noise + interaction`). Task D의 tile 최초 통과 시 `Δi ∼ U[-0.10, 0.10]`로 누적 drift 발생.

### 4.4 Noise (`n_t`)

- **기본 의미**: invisible field와 연결된 공통 latent disturbance 축. 단, **모든 상태를 동시에 흔들지 않는다** (sparse coupling).
- **전역 default utility**: 보통 `n_t ≈ 0`이 안정적이지만, **noise 자체를 reward target으로 두지 않는다.** noise는 task cost와 disturbance의 원인으로만 작동한다.
- **local override**: Task C의 stele 활성화 조건 `n_t ∈ [-0.02, 0.02]`. 이 순간 noise는 maximize/minimize가 아닌 match-to-band다.
- **target band 연결**: 일반적으로는 “0 근처 안정”이 유리하나, task-specific gate에서만 정밀 band가 강제된다.
- **잘못 추정될 때의 cost**: observation cue 오해, invisible field family 오추정, interaction target drift 미감지, control-drift와 noise coupling 혼동, reveal/shift 오판.
- **drift/shift와의 연결**: noise는 모든 invisible field의 공통 입력 축이다. field mean drift는 noise mean을 천천히 이동시키고, event-triggered shift는 noise mean을 갑자기 점프시킨다.

### 4.5 Control-drift (`d_t`)

- **기본 의미**: 입력 action `W/A/S/D`가 실제 movement outcome으로 매핑되는 규칙의 왜곡. **이동 속도가 아니라 action semantics 자체가 바뀐다.**
- **전역 default utility**: identity control이 일반적으로 유리. default utility는 `-w_d · |d_t|`. 단, 짧은 구간이라면 adaptation이 더 쌀 수 있어 항상 0으로 보내는 것이 답은 아니다.
- **local override**: 특정 interference field 안 / narrow corridor / 문 앞 / final altar 직전에는 작은 remap도 치명적이다. 이 경우 correction이 우세해진다.
- **target band 연결**: Task C의 stele 활성화 시 “현재 control regime에 맞는 입력 패턴”을 요구하는 형태로 target band가 정의된다.
- **잘못 추정될 때의 cost**: wrong movement, collision, hazard tile 진입, target cell 이탈, unnecessary correction, detour, forced reset.
- **drift/shift와의 연결**: control interference field와 sparse coupling (`noise + control`). drift는 small cumulative (`d_{t+1} = d_t + ε_t`, `ε_t ∼ U[-0.01, 0.03]`)와 abrupt remap shift (identity → cw, lr 등)가 모두 가능.

---

## 5. control-drift 최종 정의

PART2 §3.10을 환경 코드 차원에서 못 박는다.

### 5.1 연속 각도 drift는 사용하지 않는다

본 환경은 4방향 grid 환경이다. 연속 각도 drift (예: 13° 회전, 27° 회전 등)는 action semantics와 정합하지 않는다. **연속 각도 drift 설명은 폐기한다.**

### 5.2 control-drift는 다음 세 메커니즘으로만 정의된다

#### 5.2.1 이산 remap

action mapping function `Π_{r^ctrl}` 자체가 이산적으로 바뀐다.

- `identity`: `W → up, A → left, S → down, D → right`
- `cw` (clockwise): `W → right, D → down, S → left, A → up`
- `lr` (left-right flip): `A ↔ D`, `W, S` 유지
- `ud` (up-down flip): `W ↔ S`, `A, D` 유지
- `rev` (reverse): 모든 방향 반대

regime hypothesis comparison에 가장 적합한 메커니즘이며, current vs alternative rollout이 명확히 갈린다.

#### 5.2.2 약한 stochastic miscontrol

기본 mapping은 유지되지만 일정 확률 `p_slip`으로 인접 방향으로 미끄러진다.

```
ã_t = Π(a_t)                           with prob 1 - p_slip
ã_t = a' ∼ NeighborActions(a_t)        with prob p_slip
```

`NeighborActions`는 4방향 grid에서 90° 좌/우 인접 두 방향. subtle drift를 만들어 baseline detector가 즉시 잡지 못하게 한다.

#### 5.2.3 주기적 slip

```
p_slip(t) = p_high if t mod K == 0 else p_low
```

adaptation vs correction의 hard case를 만든다. 주기를 알면 wait/timing/우회로 적응 가능하다.

### 5.3 main vs ablation

- **메인 환경 default**: 이산 remap + 약한 miscontrol.
- **adaptation/correction hard case ablation**: 주기적 slip을 별도로 활성화한 split.
- 세 메커니즘을 모두 한 episode에 동시에 활성화하지 않는다 (식별성 보호).

### 5.4 mobility와 절대 섞지 않는다

- mobility는 이동 cooldown/latency. 같은 방향으로 가되 느려진다.
- control-drift는 입력 해석 규칙. 다른 방향으로 해석된다.
- 두 개념은 **코드 / info / metadata 모든 레벨에서 분리된 채널**로 기록한다.
  - `info["true_state"]["mobility"]` vs `info["true_state"]["control_drift"]`
  - `info["true_regime"]["mobility_mode"]` (cooldown 함수의 mode) vs `info["true_regime"]["control_mode"]` (`identity`, `cw`, `lr`, `ud`, `rev` 등)

---

## 6. Task A/B/C/D 설계

PART3 §3.18을 따르되, 각 항목을 환경 코드 차원에서 “주 상태값 / 보조 상태값 / local cue / target band / drift/shift 가능성 / wrong hypothesis / falsification-driven planning이 드러나는 이유”의 7항목으로 통일한다.

### 6.1 Task A — Weight-Order + Interaction Calibration

- **task 목적**: 4개의 조각을 무거운 것부터 가벼운 것 순으로 정확한 슬롯에 배치한 뒤, 최종 altar에서 `i_t`를 episode-sampled target band 안에 맞춰 interaction.
- **주 상태값**: mobility (`m`), interaction (`i`).
- **보조 상태값**: noise (`n`).
- **local cue**: 조각 주변 tile mark / 조각 크기 / pressure plate pattern으로 weight order를 약하게 hint. altar 주변 cue로 target band 방향 hint (정확한 수치는 X). cue는 vision level에 가려질 수 있음.
- **target band**: 최종 altar에서 `τ_i ∼ U_{0.01}[-0.20, +0.20]`, 폭 `α_i = 0.02`. 즉 `i_t ∈ [τ_i - 0.02, τ_i + 0.02]`.
- **발생 가능한 drift/shift**:
  - 조각 운반 시 mobility의 deterministic state-level penalty (`Δm = -w_j`).
  - 조각 최초 픽업 시 `i, n`의 persistent shift (`Δi ∼ U[-0.10, 0.10]`, `Δn ∼ U[-0.03, 0.03]`).
  - interaction interference field의 small drift / event shift.
- **wrong hypothesis**:
  - 조각 운반 mobility penalty를 일시 state로만 보고 burdened mobility regime를 놓침.
  - target band를 `τ_i ≈ 0`이라고 잘못 가정.
  - noise shift로 인한 interaction drift를 단순 observation noise로 처리.
  - heavy-to-light order를 trial-and-error로 시도.
- **falsification-driven planning이 드러나는 이유**: current hypothesis가 “지금 바로 altar interaction이 최선”이라고 추천하는 시점에, alternative hypothesis는 “`i_t`가 target band 밖이므로 `i^-` / `i^+` correction 후 interaction이 최선”을 추천. 이때 action flip이 발생한다.

### 6.2 Task B — Vision-Positive Selection + Zero-Mobility Gate

- **task 목적**: 4개의 stele 중 vision-positive(`Δv_k > 0`)인 정확히 2개의 stele만 켠 뒤, 최종 interaction cell에서 mobility를 zero-band로 맞추고 마지막 2 tick 동안 vision이 안정된 상태에서 문을 연다.
- **주 상태값**: vision (`v`), mobility (`m`).
- **보조 상태값**: control-drift (`d`).
- **local cue**: stele 주변 visual cue로 vision-positive 여부를 약하게 hint. cue는 vision level에 따라 부분적으로 가려질 수 있음. zero-mobility gate 입구 주변에 “정지 표시” cue.
- **target band**: 
  - mobility gate: `m_t ∈ [-0.02, +0.02]`.
  - vision 안정 조건: `Δv_{t-2:t} = 0` (마지막 2 tick).
  - stele 활성화 조건: `|{k : ON}| = 2`이고 모두 `Δv_k > 0`.
- **발생 가능한 drift/shift**:
  - 각 stele ON 시 `Δv ∼ U[-0.10, 0.10]`, `Δm ∼ U[-0.10, 0.10]`, `Δd ∼ U[-0.03, 0.03]` 의 persistent shift.
  - subtle control-drift small cumulative.
- **wrong hypothesis**:
  - vision-positive stele을 외형 cue가 아닌 방 위치로 외움.
  - mobility를 항상 높게 유지하는 default utility만 믿고 zero-mobility gate를 놓침.
  - subtle control perturbation을 단순 collision으로 봄.
  - 마지막 2 tick 안정 조건을 무시.
- **falsification-driven planning이 드러나는 이유**: 평소에는 “vision/mobility를 키워라”가 default utility지만, 문 앞에서는 local override가 강해진다. current hypothesis가 “지금 `E`가 최선”이라고 보더라도 alternative hypothesis는 “mobility가 아직 band 밖 + vision 안정 조건 미충족 → wait 또는 `m^-`”이 최선이라고 본다. action flip 발생.

### 6.3 Task C — Noise-Zero Multi-Stele + Control-Drift Tracking

- **task 목적**: 활성 stele(`N_stele ∈ {2, 3, 4}`)을 모두 활성화하되, 각 stele 활성화 시점에 noise를 zero-band 안에 맞추고, 동시에 변화하는 control-drift를 추적.
- **주 상태값**: noise (`n`), control-drift (`d`).
- **보조 상태값**: mobility (`m`).
- **local cue**: stele 주변 방향별 noise correction cue (서쪽 stele 주변 패턴이 `A` 방향 이동의 noise 영향을 약하게 hint). cue는 항상 완전하지 않다.
- **target band**: 각 stele 활성화 조건 `n_t ∈ [-0.02, +0.02]`. control-drift는 명시 band 없이 “현재 regime에 맞는 입력”을 요구.
- **발생 가능한 drift/shift**:
  - 방향별 noise increment `Δn_{W,A,S,D} ∼ U[-0.10, 0.10]`.
  - 방 진입 시 initial control-drift bin `d_0 ∈ {-0.70, -0.35, 0.00, +0.35, +0.70}` 중 하나로 sampling.
  - small cumulative drift `d_{t+1} = d_t + ε_t`, `ε_t ∼ U[-0.01, +0.03]`.
  - 방 내 특정 checkpoint에서 abrupt remap shift (identity → cw 등) 가능.
- **wrong hypothesis**:
  - control-drift를 mobility latency로 오해.
  - `W`를 눌렀는데 다른 방향 이동을 단순 collision으로 해석.
  - noise-zero 실패를 interaction 실수로 해석.
  - small drift 무시 → cumulative control cost 폭증.
  - current remap hypothesis(예: identity)를 너무 오래 유지.
- **falsification-driven planning이 드러나는 이유**: Task C는 본 논문의 핵심 hard case다. current hypothesis가 identity면 “`W`로 북진”을 추천하지만 alternative hypothesis가 cw remap이면 같은 목표를 위해 `A`를 눌러야 한다. action flip이 직접적이며 falsification × action relevance가 모두 켜진다.

### 6.4 Task D — Tile-Induced Interaction Drift + Final Zero-Interaction Altar

- **task 목적**: tile 영역을 통과하며 interaction drift를 누적한 뒤, 최종 altar에서 `i_t ∈ [-0.02, 0.02]` 조건을 맞춰 interaction. 오답 interaction 3회 누적 시 중앙홀로 forced reset.
- **주 상태값**: interaction (`i`), noise (`n`).
- **보조 상태값**: vision (`v`).
- **local cue**: tile pattern이 interaction drift 방향을 약하게 hint (정확한 크기는 hint하지 않음). feedback은 success/fail count 위주.
- **target band**: 최종 altar `i_t ∈ [-0.02, 0.02]`.
- **발생 가능한 drift/shift**:
  - 각 tile 최초 통과 시 `Δi ∼ U[-0.10, 0.10]`, `Δn ∼ U[-0.05, 0.05]`, `Δv ∼ U[-0.03, 0.03]` 의 누적 drift.
  - interaction interference field의 small drift.
  - final altar 직전 event-triggered shift 가능.
- **wrong hypothesis**:
  - tile-induced drift를 일회성 noise로 처리.
  - target altar가 항상 `i = 0`이라고 가정 (실제로는 tile 통과로 누적 drift 존재).
  - failure feedback만 보고 target band 위치를 잘못 추정.
  - correction 없이 immediate interaction → reset 유발.
- **falsification-driven planning이 드러나는 이유**: 이동 중에는 adaptation이 유리하지만 final altar 직전에는 correction이 필요하다. current hypothesis가 `E` 즉시 추천하더라도, alternative hypothesis는 `i^-` / `i^+` / wait 후 `E`를 추천한다. phase-dependent action flip이 발생한다.

---

## 7. Invisible Noise Field 설계

### 7.1 invisible field를 넣는 이유

- agent가 보이지 않는 원인 때문에 상태값이 조금씩 변하는 상황을 만들어, hidden state tracking + reveal/shift 구분을 강제한다.
- field source는 직접 관측되지 않는다. agent는 “특정 위치 진입 시 상태가 변한다 / interaction latency가 바뀐다 / control outcome이 흔들린다”는 evidence로 field 존재를 추론해야 한다.
- 단순한 “보이는 noise”가 아닌 “보이지 않는 원인 + 약한 cue + 누적 효과”가 partial observability와 latent regime의 이유를 강화한다.

### 7.2 모든 상태를 동시에 흔들면 안 되는 이유

- `(v, m, i, n, d)` 5개를 동시에 흔들면 식별 불가능 → agent가 어떤 family인지 추론할 수 없다.
- baseline도, 제안법도 모두 어려워져서 모델 간 차이가 흐려진다.
- mechanism paper의 메시지가 무뎌진다.

### 7.3 sparse coupling 원칙

```
x_{t+1}^{(k)} = x_t^{(k)} + Σ_{j ∈ F} g_{j,k}(p_t) · ε_{j,t}
```

- 각 field `j`에 대해 `|{k : g_{j,k} ≠ 0}| ≤ 2`.
- 즉 한 field는 최대 1~2개 상태값에만 영향.
- coupling indicator `g_{j,k}`는 0/1 binary 또는 episode-sampled real strength로 두되, sparsity는 항상 강제.

### 7.4 map family-based coupling randomness

coupling은 완전 랜덤이 아니다. map family마다 가능한 coupling 종류를 제한한다.

- `visibility_field`: `noise + vision`
- `friction_field`: `noise + mobility`
- `interaction_interference_field`: `noise + interaction`
- `control_interference_field`: `noise + control-drift`

각 episode는 map family를 sampling한 뒤, 그 family가 허용하는 coupling 중 하나를 선택. 이 구조는 “다양한 family가 있지만 family 안에서는 일관된 규칙”을 만든다.

### 7.5 field mean drift

```
μ_{j, t+1} = μ_{j, t} + η_{j, t},   η_{j, t} ∼ N(0, σ_η^2)
```

- small cumulative drift. 일반 step에서 적용.
- σ_η는 매우 작게 두어 단일 step에서는 거의 보이지 않지만 누적되면 큰 비용을 만든다.

### 7.6 event-triggered shift

```
μ_{j, t+1} ← μ_{j, t} + δ_j   (specific events only)
```

- checkpoint 통과, room entry, stele activation, final altar 접근 등 특정 event에서 큰 점프.
- δ_j는 충분히 커서 baseline도 어느 정도 잡을 수 있는 abrupt shift를 만든다.
- small drift와 abrupt shift의 공존이 mechanism의 강점을 분해 가능하게 만든다 (small drift에서는 baseline 약함, abrupt shift에서는 baseline도 가능).

---

## 8. Split 설계

각 split은 train/test 사이의 disjoint 조건과 검증 목적을 명확히 한다. 모든 split은 metadata로 자기 정체성을 기록해야 한다.

### 8.1 train

- **train과 다른 점**: 본 split이 reference. 특정 room-task permutation 부분집합, 특정 factor combination 부분집합, 특정 parameter range, 특정 invisible field placement prior에서 sampling.
- **검증하려는 것**: 모델이 sufficient capacity로 학습 가능한가.
- **metadata**:
  - `split = "train"`
  - 사용한 room-task permutation set
  - 사용한 factor combination set
  - parameter range
  - field placement prior

### 8.2 valid

- **train과 다른 점**: 같은 분포에서 sampling되었으나 episode seed가 train과 disjoint.
- **검증하려는 것**: 학습 중 model selection 및 hyperparameter tuning.
- **metadata**: `split = "valid"`, train과 동일한 distribution descriptor + disjoint seed pool.

### 8.3 test_id (in-distribution)

- **train과 다른 점**: train/valid와 동일한 분포지만 episode seed가 모두 disjoint.
- **검증하려는 것**: in-distribution 일반화 성능.
- **metadata**: `split = "test_id"`, train distribution descriptor + disjoint seed pool.

### 8.4 ood_room_perm (room-task permutation OOD)

- **train과 다른 점**: train에서 본 적 없는 room-task permutation으로 강제.
- **검증하려는 것**: 위치 암기 vs task rule 이해. agent가 “북쪽 방 = Task A”를 외웠는지 검증.
- **metadata**: `split = "ood_room_perm"`, 사용된 permutation이 train permutation set과 disjoint임을 명시.

### 8.5 ood_factor_recomb (factor recombination OOD)

- **train과 다른 점**: train에서 보지 못한 regime factor 조합 (예: train에는 `(vision + mobility)`, `(noise + control)`만 있었고 test에는 `(vision + noise)`, `(mobility + control)`).
- **검증하려는 것**: factorized regime 일반화. monolithic regime 모델이 약해야 함.
- **metadata**: `split = "ood_factor_recomb"`, 사용된 factor combination이 train과 disjoint임을 명시.

### 8.6 ood_param_shift (parameter shift OOD)

- **train과 다른 점**: 같은 dynamics family이지만 수치 범위가 다름 (예: drift 강도, hazard radius, interaction calibration scale).
- **검증하려는 것**: 같은 family 안에서 scale/intensity가 바뀌어도 robust한가.
- **metadata**: `split = "ood_param_shift"`, train range vs test range 비교 가능한 수치 기록.

### 8.7 ood_obs_shift (observation shift OOD)

- **train과 다른 점**: tile/sprite/icon/색 표현이 다르지만 underlying dynamics는 train과 동일.
- **검증하려는 것**: novelty와 진짜 regime shift 구분. novelty detector는 여기서 false positive를 내야 함.
- **metadata**: `split = "ood_obs_shift"`, 사용된 visual variant id, dynamics는 train과 동일임을 명시.

### 8.8 ood_field_placement (invisible field placement OOD)

- **train과 다른 점**: invisible field source의 수, 위치 prior, radius 분포가 train과 다름.
- **검증하려는 것**: hidden field에 대한 belief 일반화.
- **metadata**: `split = "ood_field_placement"`, field source count / placement prior / radius distribution 기록.

---

## 9. Config 설계

이후 `configs/dataset_default.yaml`에 그대로 매핑될 항목 목록. 모든 수치는 코드가 아니라 config로만 관리된다.

```yaml
# 최상위 default config (실제 yaml 작성은 Session 3에서 수행)

seed: 42

# split별 episode 수
num_train: 5000              # 메인 학습용
num_valid: 500
num_test: 500                # test_id
num_ood_per_type: 500        # ood_room_perm / ood_factor_recomb / ood_param_shift / ood_obs_shift / ood_field_placement 각각

# episode 길이
episode_max_steps: 600

# map family
map_family_count: 100
# 각 map family는 vision/friction/interaction-interference/control-interference 중 하나의 invisible field family에 속한다

# 공간 구조
hall_size: [9, 9]            # central_hall (h, w)
room_size: [8, 8]            # 각 방 (h, w)
corridor_length: 3

# 부분관측
local_obs_size: 5            # 메인 세팅
local_obs_ablation_values: [3, 5, 7]

# control-drift
drift_strength:
  small_cumulative: 0.02     # |ε_t| 평균
  abrupt_remap_modes: [identity, cw, lr, ud, rev]
  miscontrol_p_low: 0.05
  miscontrol_p_high: 0.30
  periodic_K: 4              # adaptation/correction hard case ablation에서 사용

shift_probability:
  per_room_entry: 0.20       # 방 진입 시 abrupt shift 확률
  per_checkpoint: 0.40       # checkpoint 통과 시 abrupt shift 확률
  per_stele_activation: 0.30 # stele 활성화 후 abrupt shift 확률

# invisible field coupling
field_coupling_type:
  allowed_families:
    - {name: visibility,        couples: [noise, vision]}
    - {name: friction,          couples: [noise, mobility]}
    - {name: interaction_intf,  couples: [noise, interaction]}
    - {name: control_intf,      couples: [noise, control_drift]}
  max_couples_per_field: 2
  num_fields_train: [1, 2]
  num_fields_ood: [2, 3]

# task permutation
task_permutation_mode: "split_aware"
# split_aware: train과 ood_room_perm은 disjoint permutation set
# random: 단순 random (train ablation 용)

# target band 폭
target_band_width:
  interaction_altar: 0.02
  zero_mobility_gate: 0.02
  noise_zero_stele: 0.02
  task_a_target_range: [-0.20, 0.20]   # τ_i sampling 범위

# data IO
save_format: "npz_per_episode"
# npz_per_episode: episode 하나당 하나의 .npz + index.jsonl
# 대안: zarr / hdf5 (Session 3에서 결정)
output_root: "data/rg4f"
```

위 항목들은 `configs/dataset_default.yaml` 외에도 ablation별 derived config (`configs/dataset_obs3.yaml`, `configs/dataset_obs7.yaml`, `configs/dataset_periodic_drift.yaml` 등)로 파생될 수 있다. 모든 파생 config는 default를 inherit해야 하며, override 항목만 명시한다.

---

## 10. 다음 세션 구현 파일 구조 제안

본 절은 Session 2~4에서 생성될 코드 파일의 책임 경계를 고정한다. 이 경계를 벗어나는 코드 분산은 PART0 §3 금지사항 위반이다.

### 10.1 환경 코어 (Session 2)

#### `falsifiable_regime_world_model/rg4f/types.py`
- 모든 enum / dataclass / TypedDict 정의.
- `Action` (`W`, `A`, `S`, `D`, `E`, `M_PLUS`, `M_MINUS`, `I_PLUS`, `I_MINUS`, `D_PLUS`, `D_MINUS`, `WAIT` 등 — 정확한 액션 집합은 §10.6 참조).
- `EventToken` enum (§3.2 e_t 정의).
- `ControlMode` enum (`identity`, `cw`, `lr`, `ud`, `rev`).
- `RegimeFactor` dataclass (vision_mode, mobility_mode, interaction_mode, noise_mode, control_mode).
- `TrueState` / `TrueRegime` / `ChangePoint` / `FieldInfo` / `TargetBand` 등의 info용 dataclass.
- 다른 모듈에서 import만 하고, 어떤 로직도 두지 않는다.

#### `falsifiable_regime_world_model/rg4f/config.py`
- yaml 로드, validation, dataclass 변환만 담당.
- 어떤 환경 로직도 두지 않는다.
- `local_obs_size ∈ {3, 5, 7}` validation, sparse coupling validation 등을 구현.

#### `falsifiable_regime_world_model/rg4f/map_generator.py`
- map family sampling.
- 중앙홀 + 4방 + 복도의 grid layout 생성.
- room object placement (조각, stele, altar, tile 영역).
- invisible field source placement (sparse coupling 조건 만족).
- room-task permutation sampling (split-aware).
- task parameter sampling (target_band 등).

#### `falsifiable_regime_world_model/rg4f/observation.py`
- partial observation 생성 (`local_obs_size` 적용).
- vision level에 따른 local cue mask 적용.
- scalar feature 조립.
- event token 생성.
- 전역 정보(전체 맵, hidden field 위치)는 절대 obs에 포함하지 않는다.

#### `falsifiable_regime_world_model/rg4f/fields.py`
- invisible field source 객체.
- field mean drift (small cumulative).
- event-triggered shift.
- coupling indicator `g_{j,k}` 적용.
- 5개 상태값 중 sparse coupling subset만 갱신.

#### `falsifiable_regime_world_model/rg4f/tasks.py`
- Task A/B/C/D 각각의 진행 상태 추적.
- success / failure 판정.
- target band 검사.
- task별 local cue 생성.
- task permutation에 따라 어느 방에 어느 task가 배치될지 결정 (실제 sampling은 map_generator에서 수행, tasks.py는 진행 상태만 관리).

#### `falsifiable_regime_world_model/rg4f/env.py`
- `RG4FEnv` 클래스. gymnasium-like API (`reset`, `step`, `render` 옵션).
- `reset(seed)` → `(obs, info)`.
- `step(action)` → `(obs, reward, terminated, truncated, info)`.
- info dict에 다음을 반드시 포함:
  - `true_state` (현재 5개 상태값의 정확한 값)
  - `true_regime` (현재 모든 regime factor의 ground truth)
  - `change_point` (현재 step이 ground-truth regime transition인지)
  - `task_id` (현재 활성 task)
  - `room_id` (현재 위치한 방)
  - `event_token`
  - `target_band` (현재 활성 target band 정보)
  - `field_info` (sparse coupling, 현재 mean, drift schedule)
  - `step_cost`, `failure_cost`, `reset_cost`, `latency_cost` (`planning_cost`는 환경이 아니라 agent/planner 단에서 계산되므로 env가 직접 채우지 않음)
  - `reveal_event` / `shift_event` 분리 라벨
- 학습 코드, dataset 저장 코드, planner 코드, agent 코드 일절 포함하지 않는다.

### 10.2 Dataset 생성 (Session 3)

#### `scripts/generate_dataset.py`
- yaml config 로드.
- 각 split에 대해 episode 단위로 env를 돌려 trajectory 저장.
- episode metadata와 함께 `data/rg4f/<split>/<episode_id>.npz` + `data/rg4f/<split>/index.jsonl` 형태로 저장.
- 모델/agent/planner 코드 미포함. agent는 random policy 또는 단순 deterministic policy(환경 검증용)로 충분.

### 10.3 Inspection / Validation (Session 4)

#### `scripts/inspect_episode.py`
- 임의 episode를 받아 trajectory 시각화 / 통계 출력.
- step별 (action, true_state, true_regime, change_point, reveal/shift 라벨, target band 충족, reward decomposition)을 사람이 읽을 수 있는 형태로 출력.

#### `scripts/validate_dataset.py`
- split 단위 invariant 검증.
- 검증 항목 (PART0 Session 4 완료 기준 §2 참조).
- 통과/실패를 stdout + exit code + 보고서 파일로 기록.

### 10.4 Configs (Session 3)

#### `configs/dataset_default.yaml`
- §9 항목을 모두 포함.
- 파생 config는 default를 inherit하는 yaml anchor 또는 별도 inherit 메커니즘으로 구성.

### 10.5 책임 경계 요약

- **types/config**: 데이터 정의 + validation. 로직 없음.
- **map_generator**: 정적 layout + 정적 sampling (episode 시작 시 한 번).
- **observation**: 매 step 관측 변환. 로직은 `local_obs_size` 적용 + masking에 한정.
- **fields**: invisible field 동역학 (state-level 영향).
- **tasks**: task 진행 상태 + success/failure 판정 + target band 검사.
- **env**: 모든 하위 모듈을 묶고 `reset` / `step` / `info` 컨트랙트를 책임짐.
- **scripts/**: env를 “사용”만 한다. 환경 로직을 추가하지 않는다.
- **configs/**: 모든 수치의 단일 소스.

### 10.6 Action 공간 (잠정 — Session 2에서 확정)

- `W, A, S, D`: 4방향 이동.
- `E`: interaction.
- `M_PLUS, M_MINUS`: mobility 조절.
- `I_PLUS, I_MINUS`: interaction calibration 조절.
- `D_PLUS, D_MINUS`: control-drift 조절 (correction action).
- `WAIT` (또는 `NOOP`): 1 tick 대기.
- `PICKUP`, `DROP`: Task A 조각 처리.

각 action의 정확한 의미와 cost는 Session 2에서 코드 작성 시 확정한다. 위는 `tasks.py` / `env.py` 설계가 견딜 수 있어야 할 최소 action 집합이다.
