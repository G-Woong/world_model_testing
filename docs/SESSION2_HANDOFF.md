# SESSION 2 → SESSION 3 Handoff

> 본 문서는 다음 Cursor 세션이 이전 대화 맥락 없이 단독으로 Session 3을 시작할 수
> 있도록 작성된 인계 문서다. 본 문서만으로 Session 3의 모든 결정 근거가 추적
> 가능해야 한다.

---

## 1. Session 2에서 생성된 파일

본 세션은 RG-4F 환경 코드(7 파일) + 패키지 entry 2 파일 + 본 핸드오프 1 파일을
생성했다. dataset / model / planner / agent 코드는 일절 만들지 않았다.

| 경로 | 목적 |
|---|---|
| `falsifiable_regime_world_model/__init__.py` | 최상위 패키지 진입점 (lazy/explicit import). |
| `falsifiable_regime_world_model/rg4f/__init__.py` | `RG4FEnv`, `RG4FConfig`, `Action` 등 외부 노출 API의 re-export. |
| `falsifiable_regime_world_model/rg4f/types.py` | 모든 enum / dataclass (`Action`, `EventToken`, `RoomID`, `TaskID`, `ControlMode`, `MobilityMode`, `FieldFamily`, `StateDim`, `CellType`, `LOCAL_CHANNELS`, `Position`, `AgentState`, `TaskInstance`, `FieldInfoEntry`, `TargetBandInfo`, `RegimeState`, `StepDebug`). 로직 없음. |
| `falsifiable_regime_world_model/rg4f/config.py` | `RG4FConfig` dataclass + `__post_init__` validation. yaml 로딩은 Session 3에서 추가. 모든 수치(`hall_size`, `room_size`, `corridor_length`, `local_obs_size`, drift / shift / field / task / reward) 단일 출처. |
| `falsifiable_regime_world_model/rg4f/map_generator.py` | 중앙홀(9×9) + 4방(8×8) + 복도(길이 3, 1셀 wide)의 cross 토폴로지 grid, `RoomID` lookup, `traversable` mask, room-task permutation 4! sampling, task object placement, invisible field source placement. `EpisodeLayout` 컨테이너 반환. |
| `falsifiable_regime_world_model/rg4f/fields.py` | invisible field 동역학: `evaluate_field_effects` (sparse coupling 거리 기반 effect), `apply_small_drift` (μ_{j,t+1} = μ_{j,t} + N(0, σ²_η)), `apply_event_shift` (room_entry / checkpoint / stele_activation 확률 기반 abrupt shift), `summarize_fields_for_info` (info용 요약). |
| `falsifiable_regime_world_model/rg4f/tasks.py` | `BaseTask` 인터페이스(reset / on_enter_room / step / interact / is_completed / get_target_band / get_local_cues / get_debug_info)와 Task A/B/C/D 구현. 각 task는 PART3 §3.18, RG4F_Environment_Plan §6 의미 그대로: A=weight-order pieces+altar, B=vision-positive stele+zero-mobility gate(마지막 N tick vision 안정 조건 포함), C=noise-zero stele+initial control-drift bin+방향별 Δn, D=tile-induced (Δi, Δn, Δv)+zero-i altar+3-fail forced reset. `TaskStepResult` 표준화로 `state_deltas` / `reveal_event` / `shift_event` / `forced_reset` 분리. |
| `falsifiable_regime_world_model/rg4f/observation.py` | partial obs 변환: `build_local_grid` (`local_obs_size`×`local_obs_size`×10ch, vision-level cue mask 적용, 외부는 wall padding), `build_scalar` (state5+room_norm+completed+fail+step_norm+carrying+per-task done = 14차원), `build_action_mask` (16차원), `build_observation` 통합 dict 빌더. 전체 맵, hidden field 위치, 정확한 regime label은 obs에 절대 포함되지 않는다. |
| `falsifiable_regime_world_model/rg4f/env.py` | `RG4FEnv` 메인 클래스: `__init__(config, seed)` / `reset(seed=None)` / `step(action)` / `observe()` / `render_ascii()` / `get_debug_state()`. 5-tuple `(obs, reward, terminated, truncated, info)` 반환. control-drift remap + 약한 stochastic miscontrol + (옵션) 주기적 slip, mobility cooldown 분리, invisible field sparse coupling effect, task FSM 호출, reward decomposition (PART2 §3.12; `λ_plan C^plan`은 환경이 채우지 않음). info에 `true_state`, `true_regime`, `change_point`, `reveal_event`/`shift_event`(분리), `target_band`, `field_info`, `permutation`, `task_debug`, 풍부한 `debug` trace 노출. |
| `docs/SESSION2_HANDOFF.md` | 본 문서. |

본 세션에서 명시적으로 **수행하지 않은 것** (PART0 §3 §6 / SESSION1_HANDOFF §6 정합):
- `scripts/generate_dataset.py`, `scripts/inspect_episode.py`, `scripts/validate_dataset.py` 어떤 것도 생성하지 않음.
- `configs/dataset_default.yaml` 작성 안 함 (Session 3 책임).
- 모델/agent/planner 코드 일절 없음. PyTorch import 없음.
- DreamerV3 / SOTA backbone import 없음.
- 100 episode 이상 자동 생성 시도 없음. smoke test는 단발성 reset + 짧은 step trajectory.
- `ref/PART0~3` 및 `requirements.txt` 변경 없음.

---

## 2. 외부 노출 API (Session 3가 그대로 사용)

```python
from falsifiable_regime_world_model.rg4f import (
    RG4FEnv, RG4FConfig,
    Action, EventToken, RoomID, TaskID, ControlMode, FieldFamily, StateDim,
    Position, TargetBandInfo,
)

config = RG4FConfig()                  # 모든 수치 default. yaml은 Session 3에서.
env = RG4FEnv(config=config, seed=42)
obs, info = env.reset()                # (Dict[str, np.ndarray], Dict[str, Any])
obs, reward, terminated, truncated, info = env.step(int(action))
obs = env.observe()                    # 현재 state로부터 obs 재빌드
ascii_dump = env.render_ascii()        # 디버깅용
debug = env.get_debug_state()          # full ground-truth snapshot
```

### 2.1 obs dict
| key | shape / type | 설명 |
|---|---|---|
| `local_grid` | `(local_obs_size, local_obs_size, 10)` `float32` | 채널: wall, floor, corridor, door, task_object, stele, altar, cue(vision-mask), agent, traversable. |
| `scalar` | `(14,)` `float32` | state(5) + room_norm + completed + fail + step_norm + carrying + per-task-done(4). |
| `event_token` | `int32` scalar | `EventToken` enum의 정수값. |
| `action_mask` | `(16,)` `float32` | mobility cooldown 중 이동 action은 0 (hint, hard constraint 아님). |

### 2.2 info dict (Session 3의 dataset generator가 episode 저장 시 그대로 dump해야 함)

| key | type | 설명 |
|---|---|---|
| `true_state` | `dict{vision/mobility/interaction/noise/control_drift: float}` | hidden 5차원 ground-truth. obs에는 노출 안 됨. |
| `true_regime` | `dict{control_mode/mobility_mode/miscontrol_p/periodic_slip_active/active_field_families}` | factorized regime ground-truth. |
| `change_point` | `bool` | 본 step이 ground-truth regime transition인지. 현재는 `shift_event`와 동일 정의. |
| `reveal_event` / `shift_event` | `bool` / `bool` | 분리된 라벨. PART0 §3 §8 강제. |
| `reveal_or_shift` | `"reveal" \| "shift" \| "none"` | 단일 문자열로 합본 (편의용). |
| `task_id` | `int` | 현재 활성 task. 방 밖이면 -1. |
| `room_id` | `int` | 현재 위치한 영역. `RoomID` enum. |
| `event_token` | `int` | 이번 step의 가장 의미 있는 event. |
| `raw_action` / `effective_action` | `int` / `int` | control-drift remap + miscontrol 전후. |
| `tick_cost` / `latency_cost` / `failure_cost` / `reset_cost` / `step_cost` / `task_reward` / `completion_reward` | `float` | reward decomposition (PART2 §3.12). `λ_plan C^plan`은 미포함 (planner 책임). |
| `target_band` | `dict \| None` | 현재 활성 band: `{state_dim, center, half_width, kind}`. 없으면 None. |
| `field_info` | `list[dict]` | 모든 invisible field의 ground-truth 요약: `{family, source_row, source_col, radius, mu, sigma, coupled_states, last_effect}`. |
| `local_obs_size` | `int` | 진단용 echo. |
| `agent_position` | `(row, col)` tuple | |
| `completed_tasks` | `int` | 0..4. |
| `wrong_interaction_count` | `int` | (현재는 env 단에서는 누적하지 않고 task별로만 추적; Session 3에서 통합 가능). |
| `control_mode` / `mobility_mode` | `int` / `int` | 같은 정보를 top-level에도 노출. |
| `permutation` | `dict{room_id: task_id}` | 본 episode의 room-task assignment. |
| `task_debug` | `dict` | 현재 활성 task의 진행 상태 (used_pieces, stele_on, vision_history, tile_visited 등). |
| `debug` | `dict` | step-level 풍부한 trace: `miscontrolled`, `move_attempted/succeeded`, `cooldown_blocked`, `field_effect`, `field_drift_applied`, `field_event_shift_applied`, `interaction_outcome`, `extras`(task-specific) 등. |
| `reset_flag` | `bool` | reset 직후 호출인지. step 결과에서는 False. |

---

## 3. 구현된 핵심 기능 체크리스트

| 기능 | 구현 위치 | 비고 |
|---|---|---|
| `reset(seed)` deterministic | `env.py::RG4FEnv.reset` | `np.random.default_rng(seed)`만 사용 (numpy 2.1.3, 결정적). |
| `step(action)` 5-tuple | `env.py::RG4FEnv.step` | `(obs, reward, terminated, truncated, info)`. |
| partial observation | `observation.py::build_local_grid` | 외부는 wall padding, agent 중심 window. |
| `local_obs_size` 기본 5, ablation {3,5,7} | `config.py::RG4FConfig.__post_init__` | 검증 강제. |
| 16-dim action space | `types.py::Action` | W/A/S/D + E + ±5state + WAIT. PICKUP/DROP은 E 한 action으로 통합 (task FSM이 결정). |
| control-drift remap (이산) | `env.py::_CONTROL_REMAP` + `_apply_control_drift` | identity/cw/lr/ud/rev. |
| 약한 stochastic miscontrol | `env.py::_apply_control_drift` | 90° 인접 방향 slip. |
| 주기적 slip (옵션) | `env.py::step` 첫 단계 | `enable_periodic_slip=True`일 때만, mod K==0에서 p_high. |
| mobility cooldown (control-drift와 분리) | `env.py::_compute_movement_cooldown` | `cd = max(1, ceil(κ / (1 + α m_t)))` + carry penalty. |
| invisible field sparse coupling | `fields.py::evaluate_field_effects` + `types.py::FIELD_COUPLED_STATES` | `\|coupled_states\| ≤ 2` 강제 (config + types 양쪽). 5개 dim 동시 흔드는 field 불가능. |
| field mean small drift | `fields.py::apply_small_drift` | 매 tick. |
| event-triggered abrupt shift | `fields.py::apply_event_shift` + `env.py` 방 진입 hook | room_entry / checkpoint / stele_activation 분기. |
| Task A/B/C/D state machine | `tasks.py` | base interface + 4 subclass. `TaskStepResult`로 표준화. |
| reveal vs shift 분리 라벨 | `tasks.py::TaskStepResult` + `env.py::_build_info` | info에 두 채널 분리. |
| reward decomposition | `env.py::step` 11~12 단계 | task_reward + completion_reward − λ_step·step − λ_latency·latency − λ_fail·fail − λ_reset·reset. `λ_plan` 미포함. |
| seed-determinism 재현 | smoke test §4 | 같은 seed + 같은 action sequence → 동일 grid/state/reward. |

---

## 4. Smoke test 결과

모든 명령은 Windows PowerShell + `.venv\Scripts\python.exe`로 실행했다. 30초 이상
걸린 명령은 없다.

### 4.1 user 명시 검증 1: reset + step + key 확인

명령:
```powershell
.\.venv\Scripts\python.exe -c "from falsifiable_regime_world_model.rg4f import RG4FEnv, RG4FConfig, Action; c=RG4FConfig(local_obs_size=5); e=RG4FEnv(c, seed=42); obs, info=e.reset(); print(obs.keys()); print(info.keys()); out=e.step(Action.W); print(type(out), len(out)); print(out[-1].keys())"
```

결과 요약:
- `obs.keys()` → `dict_keys(['local_grid', 'scalar', 'event_token', 'action_mask'])`
- `info.keys()` → 31개 (필수 키 모두 포함; §2.2 표 참조)
- `out` → `tuple` length **5**
- step 직후 info에도 동일 31개 키 존재

### 4.2 user 명시 검증 2: local_obs_size 3/5/7

명령:
```powershell
.\.venv\Scripts\python.exe -c "from falsifiable_regime_world_model.rg4f import RG4FEnv, RG4FConfig; [print(s, RG4FEnv(RG4FConfig(local_obs_size=s), seed=42).reset()[0]['local_grid'].shape) for s in [3,5,7]]"
```

결과:
```
3 (3, 3, 10)
5 (5, 5, 10)
7 (7, 7, 10)
```

### 4.3 deterministic replay

같은 seed=123으로 두 번 reset 후 동일한 16-action sequence를 재생 → `local_grid` /
`reward` / `true_state` 모두 정확히 동일. seed=999로 바꾸면 permutation, reward,
true_state가 달라짐 (§ smoke test "Determinism 검증").

### 4.4 task interaction 정상 동작

`initial_identity_prob=1.0`, `miscontrol_p=0`, `enable_invisible_fields=False`로
heaviest piece 위치까지 단순 path-find 후 `E` 호출:
- `event_token = 10` (CARRY_PICKUP)
- `outcome = "pickup"`
- `task_a_carrying_weight = 0.8`
- `mobility = -0.8` (Δm = -w_j 적용)
- `interaction = -0.099` (pre-sampled persistent shift)
- `noise = +0.017` (pre-sampled persistent shift)
- `reveal_event = True`, `shift_event = False` (PART0 §3 §8 분리 만족)

### 4.5 발견된 이슈와 수정

- **이슈**: 초기 `_make_anchors`의 full grid size 계산 오류 (`4 + 2rs + 2cs + hs`로 둠 → wall 6개를 4개로 잘못 셈).
- **증상**: 첫 reset에서 `IndexError: index 35 is out of bounds for axis 0 with size 35`.
- **수정**: `full = 6 + 2*rs + 2*cs + hs`로 변경. 기본값 (`rs=8, cs=3, hs=9`)에서 full=37로 정정. 이후 모든 smoke test 통과.

---

## 5. PART0 / RG4F_Environment_Plan과 다르게 결정한 항목

본 세션은 **PART0/Plan/PART1~3와 충돌하지 않게** 구현했다. 다만 몇 가지 PART3
원안과 다른 결정은 모두 SESSION1_HANDOFF §7에서 이미 명시된 결정의 연장이다.

1. `local_obs_size` 메인 = 5 (PART3 원안 7 대신). SESSION1 §7 결정.
2. action 수 = 16 (W/A/S/D/E/±5state/WAIT). PICKUP/DROP은 별도 action 없이 E로 통합 — `tasks.TaskA.interact`가 cell context에 따라 결정. PART0 §3 §7 ("키워드 분기 금지")을 위반하지 않으려고 task FSM 자체가 분기 권한을 가지며, env는 어떤 분기 로직도 가지지 않는다.
3. corridor 폭 = 1셀 (PART3 / Plan에서 폭 명시 없음 → 1로 둠. 5×5 obs 안에서도 통로 인식 가능함을 ASCII 렌더로 확인).
4. cue 채널은 vision-level mask로 자동 가려짐 (`cue_visibility_threshold` config 키). PART3 §3.16.1 / RG4F_Environment_Plan §3.3과 정합.
5. `task_a_correct_order`는 weight 내림차순으로 결정론적으로 derive (heuristic 키워드 매핑 아님).

---

## 6. Session 3 목표 — Dataset generator + config

Session 3가 책임지는 것:
1. `configs/dataset_default.yaml` 작성 (RG4F_Environment_Plan §9의 모든 항목 포함).
2. `scripts/generate_dataset.py` 작성:
   - yaml load → `RG4FConfig.from_dict` → `RG4FEnv` 생성.
   - split별(train/valid/test_id/4개 OOD) episode 단위 trajectory 저장.
   - episode 메타: split, map_family_id, task_permutation, regime_factor, field_coupling_id, drift/shift schedule.
   - 저장 포맷: `.npz` per episode + `index.jsonl` (RG4F_Environment_Plan §9 default).
3. (선택) `falsifiable_regime_world_model/rg4f/serialization.py` — episode → dict / npz 변환 헬퍼.
4. (선택) `falsifiable_regime_world_model/rg4f/dataset.py` — episode 단위 random-access loader.

Session 3가 책임지지 않는 것 (PART0 §3 / SESSION1_HANDOFF §6 그대로):
- 모델 학습, planner, agent, allocator, world model rollout 코드.
- DreamerV3 / SOTA 코드.
- 대규모 long-running episode 생성 (smoke 단위만 허용, 본 실험은 별도 페이즈).

---

## 7. Session 3에서 반드시 읽어야 할 파일 (권장 순서)

1. `ref/PART0_IMPLEMENTATION_STRATEGY.md` — 6세션 전체 계획과 11개 금지사항.
2. `docs/RG4F_Environment_Plan.md` — 모든 환경 수치의 single source of truth (특히 §9 config schema).
3. `docs/SESSION1_HANDOFF.md` — Session 2의 contract.
4. `docs/SESSION2_HANDOFF.md` — 본 문서. 외부 노출 API와 info schema.
5. `falsifiable_regime_world_model/rg4f/config.py` — yaml에 매핑될 dataclass 필드 목록.
6. `falsifiable_regime_world_model/rg4f/env.py` — info에 어떤 키들이 있는지, 어떻게 dump하면 되는지.
7. `falsifiable_regime_world_model/rg4f/types.py` — enum 정수값 (저장 시 그대로 직렬화).
8. `ref/PART3_EXPERIMENT_DESIGN.md` §3.21 / §3.24 — split 정의와 OOD protocol.
9. `requirements.txt` — `numpy 2.1.3`, `pyyaml 6.0.3` 사용 가능. 새 dependency 추가 시 사용자 승인 필요.

---

## 8. Session 3에서 생성해야 할 파일 후보

| 파일 | 책임 |
|---|---|
| `configs/dataset_default.yaml` | RG4F_Environment_Plan §9의 모든 항목. `RG4FConfig.from_dict`로 로드 가능해야 함. |
| `scripts/generate_dataset.py` | yaml load + split별 episode 생성 + `data/rg4f/<split>/<episode_id>.npz` + `index.jsonl`. |
| `falsifiable_regime_world_model/rg4f/serialization.py` (선택) | episode trajectory → npz dict 변환 헬퍼. |
| `falsifiable_regime_world_model/rg4f/dataset.py` (선택) | npz 파일 random-access loader (Session 4 inspect/validate가 사용). |
| `docs/SESSION3_HANDOFF.md` | Session 4 인계. |

---

## 9. Session 3 금지사항 (재확인)

1. 모델 / planner / agent / allocator 코드 절대 금지.
2. SOTA / Dreamer / RSSM SOTA backbone 코드 절대 금지.
3. 학습 loop, optimizer, training run 절대 금지.
4. `RG4FEnv`의 reset/step/observe/info 컨트랙트 변경 금지. 필요 시 본 문서를 먼저 갱신한 뒤 변경.
5. dataset에 모델이 직접 쓰는 latent (예: `z_t`, `q_t(r)`)는 들어가지 않는다. info에 노출되는 ground-truth만 저장.
6. seed 고정 invariant 위반 금지. 같은 yaml + 같은 seed → 같은 dataset.

---

## 10. 알려진 미해결 ambiguity / TODO (Session 3+ 검토 필요)

- **split-aware permutation**: 현재 `sample_room_task_permutation`은 단순 4! random.
  Session 3에서 train/`ood_room_perm` disjoint를 강제할 때 permutation set 분리 로직
  필요. 후보: `RG4FConfig.task_permutation_mode`를 yaml에서 `"split_aware"`로 두고
  `RG4FEnv.reset`이 split 메타를 인자로 받도록 확장하거나, dataset generator가
  config의 `permutation_pool`을 외부에서 주입하는 방식.
- **wrong_interaction_count top-level 통합**: 현재 env top-level info의
  `wrong_interaction_count`는 0으로 둠 (task별로 `task_debug`에 포함). Session 4 `validate_dataset`이 통합 카운터를 요구하면 env에서 누적값을 따로 유지하면 됨.
- **change_point 정의**: 현재 `change_point = shift_event`. Posterior shift만으로 정의하면 순환논리(PART2 §3.7.3) → ground-truth는 외부 evidence 기반이어야 한다. 본 환경의 ground-truth shift는 (1) `apply_event_shift`가 field mu를 점프시킨 경우, (2) Task C `on_enter_room`이 `initial_d` 강제 set한 경우. 이들이 `shift_event=True`로 정확히 잡힘. 추후 abrupt control-mode remap (event-triggered) 추가 시 `_regime.control_mode` 변경 시점도 `shift_event=True`로 잡아야 함.
- **abrupt control-mode shift**: 현재 `RegimeState.control_mode`는 episode 시작 시 sampling되고 변하지 않는다. PART2 §3.10.3 / RG4F_Environment_Plan §5.3은 main env에서 "이산 remap + 약한 miscontrol"만 있으면 충분하다고 명시했으므로 mid-episode remap shift는 필수 아님. Session 3 `validate_dataset`에서 이 부분이 trade-off로 받아들여지는지 확인 필요.
- **mobility cooldown 표면 모델**: `_compute_movement_cooldown`은 `m_t`에 대해 단조 감소이지만 carry 시 +1 추가. PART3 §3.17.2의 burdened mobility regime은 더 복잡한 규칙(예: weight 비례)이 가능. 현재 `carry_cooldown_extra=1`로 단순화. Session 5 smoke validate에서 episode length가 합리적인지 확인 후 조정.
- **periodic_slip의 actually 켜기**: 현재 default `enable_periodic_slip=False`. Session 3 yaml에 ablation split (`configs/dataset_periodic_drift.yaml` 등) 분리 후 켤 수 있다.

---

## 11. Self-Audit 결과

| Check | Status | Evidence |
|---|---|---|
| Session 1 산출물을 모두 읽었는가 | PASS | PART0/RG4F_Environment_Plan/SESSION1_HANDOFF/PART1/PART2/PART3/requirements.txt 모두 Read 도구로 확인. |
| 기존 ref/PART1~3와 requirements.txt를 수정하지 않았는가 | PASS | 변경 0. 본 핸드오프 외에 docs 변경 없음. |
| dataset generator를 만들지 않았는가 | PASS | `scripts/` 디렉토리 부재. `generate_dataset.py` 없음. |
| model/planner/agent 코드를 만들지 않았는가 | PASS | torch import 0회, world_model/planner/agent 디렉토리 없음. |
| RG4FEnv.reset()이 동작하는가 | PASS | smoke §4.1, obs/info dict 반환 확인. |
| RG4FEnv.step(action)이 동작하는가 | PASS | smoke §4.1/§4.4, 5-tuple 반환 확인. |
| observe()가 partial observation을 반환하는가 | PASS | `local_grid` shape `(n, n, 10)`. 외부 padding 적용. |
| local_obs_size 기본값이 5인가 | PASS | `RG4FConfig.local_obs_size = 5` (config.py L48). |
| local_obs_size 3,5,7이 모두 동작하는가 | PASS | smoke §4.2 출력. |
| 7x7을 main으로 고정하지 않았는가 | PASS | `local_obs_size_default=5`이며 ablation set은 `(3, 5, 7)`. |
| mobility와 control-drift가 분리되어 있는가 | PASS | `_compute_movement_cooldown`(mobility) ≠ `_apply_control_drift`(control). info의 `mobility_mode` ≠ `control_mode`. |
| control-drift가 discrete remap/miscontrol로 구현되었는가 | PASS | `_CONTROL_REMAP` (5 modes) + `_NEIGHBOR_ACTIONS` slip. 연속 각도 drift 없음. |
| invisible field가 sparse coupling을 지키는가 | PASS | `FIELD_COUPLED_STATES`의 모든 family는 정확히 2개 (NOISE + 한 dim). config validation에서 `field_coupling_max_dims ≤ 2` 강제. |
| Task A/B/C/D가 모두 존재하는가 | PASS | `tasks.py` TaskA/B/C/D + `_TASK_CLASS` 매핑. |
| info에 true_state, true_regime, change_point, event_token, target_band, field_info가 포함되는가 | PASS | smoke §4.1 info.keys() 출력. |
| seed 고정 시 reset 결과가 재현되는가 | PASS | smoke §4.3 deterministic replay 확인. |
| docs/SESSION2_HANDOFF.md를 작성했는가 | PASS | 본 문서. |

---

## 12. 본 문서가 Session 3에 던지는 단 한 줄 요약

> **dataset generator만 만든다. `RG4FEnv`/`RG4FConfig` 컨트랙트와 info schema는 본
> 문서대로 고정이며, episode trajectory + ground-truth (true_state / true_regime /
> change_point / reveal_event / shift_event / target_band / field_info)를 디스크에
> 저장하는 것이 전부다. 모델/planner/SOTA는 절대 건드리지 않는다.**
