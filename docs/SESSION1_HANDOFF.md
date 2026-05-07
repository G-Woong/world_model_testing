# SESSION 1 → SESSION 2 Handoff

> 본 문서는 다음 Cursor 세션이 이전 대화 맥락 없이 단독으로 Session 2를 시작할 수 있도록 작성된 인계 문서다. 이 문서만으로 Session 2의 모든 결정 근거가 추적 가능해야 한다.

---

## 1. Session 1에서 생성된 파일

본 세션은 코드 0줄, 문서 3개를 생성했다.

| 경로 | 목적 |
|---|---|
| `ref/PART0_IMPLEMENTATION_STRATEGY.md` | 본 논문이 architecture novelty가 아니라 mechanism novelty임을 못 박고, 메인 backbone을 controlled RSSM/GRU-lite로 고정. SOTA(Dreamer 등)는 보조 baseline / 확장 실험으로만 둠을 명시. 6개 세션 전체 실행 계획(목적 / 입력 / 생성 / 완료 기준 / handoff)과 11개 금지사항을 정의. |
| `docs/RG4F_Environment_Plan.md` | RG-4F 환경의 코드 직전 단계 사양. 월드맵 구조(중앙홀 9x9 + 4방 8x8 + 복도 3), partial observability 메인 세팅(`local_obs_size=5`, ablation `{3, 5, 7}`), 5개 상태값(vision/mobility/interaction/noise/control-drift)의 default utility + local override + target band, control-drift의 이산 remap/약한 miscontrol/주기 slip 정의, Task A/B/C/D 세부 설계, sparse invisible field coupling, 8개 split(train/valid/test_id/4개 OOD), `configs/dataset_default.yaml` 항목, 다음 세션 구현 파일 책임 경계를 모두 포함. |
| `docs/SESSION1_HANDOFF.md` | 본 문서. Session 2 단독 실행을 위한 인계 명세. |

본 세션에서 다음은 명시적으로 **수행하지 않았다**:
- `ref/PART1_PROBLEM_FRAMING.md`, `ref/PART2_ALGORITHM.md`, `ref/PART3_EXPERIMENT_DESIGN.md`, `requirements.txt` — 읽기만 했고 변경 없음.
- 어떤 Python 코드도 작성하지 않음 (`falsifiable_regime_world_model/`, `scripts/`, `configs/` 디렉토리 아래 어떤 파일도 추가/변경하지 않음).
- 어떤 환경 reset, dataset 생성, 모델 학습, planner 호출도 수행하지 않음.

---

## 2. Session 2의 목표

**Session 2는 RG-4F 환경 코드 구현이다.** dataset generator, model, planner, agent는 구현하지 않는다.

구체적으로 Session 2가 책임지는 것은 다음 일곱 가지다.

1. RG-4F 환경의 type system 정립 (`types.py`).
2. yaml config 로드 및 validation (`config.py`).
3. 중앙홀 + 4방 + 복도 + room object + invisible field source의 정적 layout sampling (`map_generator.py`).
4. partial observation 변환 (`observation.py`) — 메인 `local_obs_size=5`.
5. invisible field 동역학과 sparse coupling (`fields.py`).
6. Task A/B/C/D의 진행 상태 추적, success/failure 판정, target band 검사 (`tasks.py`).
7. `RG4FEnv` 클래스 — `reset` / `step` / `info` 컨트랙트 (`env.py`).

Session 2가 책임지지 않는 것은 다음과 같다 (PART0 §3 금지사항과 정합):

- dataset 저장/로드 코드.
- 모델 / agent / planner 코드.
- 학습 loop.
- SOTA backbone 통합.
- 대량의 환경 step (smoke test 정도까지만 허용).

---

## 3. Session 2에서 반드시 읽어야 할 파일

순서는 권장 읽기 순서다.

1. **`ref/PART0_IMPLEMENTATION_STRATEGY.md`** — 이 세션이 어떤 큰 그림 안에 있는지, 무엇을 하면 안 되는지 먼저 확인한다.
2. **`docs/RG4F_Environment_Plan.md`** — 본 세션의 모든 코드 결정의 single source of truth. 모든 수치/구조/책임 경계가 이 문서에서 결정되어 있다.
3. **`docs/SESSION1_HANDOFF.md`** — 본 문서. Session 1 산출물의 위치와 Session 2의 contract.
4. **`ref/PART1_PROBLEM_FRAMING.md`** — hidden state / hidden regime / change-point / reveal vs shift / scope 정의. 환경 info의 ground-truth 구조가 왜 이래야 하는지 근거.
5. **`ref/PART2_ALGORITHM.md`** — falsification / action relevance / compute reallocation / control-drift 정의 / adaptation vs correction / reward decomposition. 환경이 “info를 어떻게 노출해야 향후 알고리즘이 가능한지”의 근거.
6. **`ref/PART3_EXPERIMENT_DESIGN.md`** — RG-4F 원안. 단, **`local_obs_size`는 본 세션의 RG4F_Environment_Plan §3의 결정(메인 5x5)이 우선**한다. PART3는 7x7로 적혀 있지만 §1.2의 partial observability 압력 분석에 따라 갱신되었다.
7. `requirements.txt` — 사용 가능한 라이브러리 (numpy 2.1.3, gymnasium 1.2.3, torch 2.6.0+cu124, pyyaml 6.0.3 등). 새 dependency를 추가해야 한다면 사용자에게 먼저 확인.

---

## 4. Session 2에서 생성해야 할 파일 후보

생성 위치는 `falsifiable_regime_world_model/rg4f/` 아래.

| 파일 | 책임 |
|---|---|
| `falsifiable_regime_world_model/rg4f/__init__.py` | 모듈 진입점. 외부 노출 API만 re-export. |
| `falsifiable_regime_world_model/rg4f/types.py` | 모든 enum / dataclass / TypedDict. 로직 없음. |
| `falsifiable_regime_world_model/rg4f/config.py` | yaml 로드 + dataclass 변환 + validation. |
| `falsifiable_regime_world_model/rg4f/map_generator.py` | map family / room layout / object placement / invisible field placement / room-task permutation sampling. |
| `falsifiable_regime_world_model/rg4f/observation.py` | partial observation 변환, vision-level cue mask, scalar 조립, event token. |
| `falsifiable_regime_world_model/rg4f/fields.py` | invisible field 동역학, mean drift, event-triggered shift, sparse coupling. |
| `falsifiable_regime_world_model/rg4f/tasks.py` | Task A/B/C/D 진행 추적, success/failure, target band 검사, task별 local cue 생성. |
| `falsifiable_regime_world_model/rg4f/env.py` | `RG4FEnv` 메인 클래스, `reset` / `step` / `info` 컨트랙트, gymnasium-like API. |

`__init__.py`는 위 목록에서 명시되지 않았더라도 패키지 구성을 위해 필요하면 작성할 수 있다. 그 외 새 파일을 만들고 싶다면 RG4F_Environment_Plan §10 책임 경계를 위반하지 않는지 먼저 확인한다.

---

## 5. Session 2의 완료 기준

다음 모두를 만족해야 Session 2가 완료된 것으로 본다.

1. **`env.reset(seed=...)`이 가능하다.**
   - `(obs, info)` tuple을 반환한다.
   - 같은 seed로 두 번 reset하면 같은 초기 obs와 같은 초기 info를 얻는다.
2. **`env.step(action)`이 가능하다.**
   - `(obs, reward, terminated, truncated, info)` 5-tuple을 반환한다.
   - reward는 PART2 §3.12의 분해형(`R^task − λ_step C^step − λ_fail C^fail − λ_reset C^reset − λ_latency C^latency`)을 따른다. `λ_plan C^plan`은 환경이 직접 채우지 않고 agent/planner 단에서 합산된다 — 단, env는 `info["step_cost"]`, `info["failure_cost"]`, `info["reset_cost"]`, `info["latency_cost"]`를 노출한다.
3. **`observe()` (또는 step/reset이 반환하는 obs)이 partial observation을 반환한다.**
   - `obs["local"]`은 shape `(local_obs_size, local_obs_size, C)` (메인 default `5 x 5`).
   - `obs["scalar"]`는 §3.2에 명시된 dimension.
   - `obs["event"]`는 enum 정수.
   - 전체 맵, hidden field 위치, 정확한 regime label은 obs에 절대 포함하지 않는다.
4. **`local_obs_size` 기본값은 5이며, config에서 3, 5, 7로 변경 가능하다.**
   - `config.py`의 validation이 `local_obs_size ∈ {3, 5, 7}`을 강제.
   - Session 2에서 세 값 모두 reset/step이 동작함을 단순 smoke test로 확인 (단, 자동화된 테스트 스위트는 Session 4에서 작성).
5. **`info`에 다음 키가 모두 존재한다.**
   - `true_state` (5개 상태값의 정확한 현재 값, dict 또는 dataclass).
   - `true_regime` (vision_mode / mobility_mode / interaction_mode / noise_mode / control_mode).
   - `change_point` (현재 step이 ground-truth regime transition step인지 bool).
   - `task_id` (현재 활성 task: A / B / C / D 중 하나).
   - `room_id` (현재 위치한 방 id 또는 central_hall / corridor).
   - `event_token` (이번 step에서 발생한 EventToken enum).
   - `target_band` (현재 활성 target band 정보 — 없으면 None).
   - `field_info` (현재 영향을 미치는 invisible field들의 sparse coupling, mean, drift schedule 요약).
   - `reveal_event` / `shift_event` (분리된 ground-truth 라벨).
6. **seed 고정 시 deterministic behavior가 확인된다.**
   - 같은 seed + 같은 action sequence → 같은 obs/info/reward sequence.
   - 단, 학습 단계가 아니므로 정식 reproducibility test suite는 Session 4 책임. Session 2에서는 “수동으로 두 번 돌려도 같은 결과가 나오는지” 정도만 확인.
7. **dataset 저장은 하지 않는다.**
   - `np.savez`, `pickle.dump`, `h5py.File` 같은 저장 호출이 환경 코드에 들어가서는 안 된다.
   - dataset 저장은 Session 3의 `scripts/generate_dataset.py` 책임.
8. **모델 / agent / planner 코드가 일절 포함되지 않는다.**
9. **`configs/dataset_default.yaml`은 Session 2에서 작성하지 않는다.**
   - Session 2는 `config.py`의 “스키마”만 정의한다. 실제 yaml 작성은 Session 3.
   - 단, 단위 테스트나 smoke 동작 확인을 위해 Session 2에서 임시 default를 코드 안 dataclass default에 넣는 것은 허용된다 (Session 3에서 yaml로 옮겨질 예정).

---

## 6. Session 2에서 금지할 것

PART0 §3과 정합. 명시적으로 다시 못 박는다.

1. **모델 학습 코드 금지.** PyTorch model, optimizer, training loop 어떤 형태로든 작성 금지.
2. **planner / agent 코드 금지.** policy, planner, allocator, world-model rollout 코드 금지.
3. **dataset 대량 생성 금지.** Session 2 안에서 100 episode를 넘는 자동 생성 시도 금지.
4. **SOTA / Dreamer 코드 금지.** DreamerV3, RSSM SOTA, 기타 SOTA backbone 코드 import 또는 복붙 금지.
5. **long-running execution 금지.** 코드 작성 후 단순 smoke test (한 episode 정도)만 수행. 30초 이상 걸리는 실행 금지.
6. **휴리스틱 / 키워드 분기 금지.** task 분기에 string 비교, room id 하드코딩으로 task 매핑, magic threshold로 change-point 라벨 부여 등은 금지. 모든 분기는 config + factorized regime code + 명시적 schedule을 통해서만 결정된다.
7. **mobility와 control-drift 혼용 금지.** 두 변수는 코드/info/metadata의 모든 레벨에서 분리된 채널이다.
8. **invisible field가 5개 상태를 동시에 흔드는 구현 금지.** sparse coupling 강제 (`|{k : g_{j,k} ≠ 0}| ≤ 2`).
9. **task를 room 위치에 고정하는 구현 금지.** room-task permutation은 episode-level sampling.
10. **reveal과 shift를 합치는 라벨 금지.** info에 `reveal_event`, `shift_event` 분리 채널 필수.

---

## 7. 의사결정 트레이스 (Session 1에서 PART3 원안과 달라진 점)

다음 두 항목은 Session 1에서 의도적으로 PART3 원안과 다르게 결정되었다. Session 2는 이 결정을 따르며, 만약 다시 뒤집어야 한다면 PART0를 먼저 갱신해야 한다.

1. **`local_obs_size`의 메인 세팅을 `7`에서 `5`로 변경.**
   - 사유: `7 x 7 = 49`칸은 한 방의 약 76.5%를 한 시점에 보여주어 partial observability 압력이 약하다. `5 x 5 = 25`칸은 한 방의 39.1%만 보여주어 hidden state belief가 필요해진다. 동시에 cue 가시성 보장 원칙(§3.3)으로 blind trial-and-error를 막는다.
   - 위치: `docs/RG4F_Environment_Plan.md` §3.1.
   - 영향: `7 x 7`은 easy/visibility ablation으로 격하, `3 x 3`은 hard ablation.

2. **메인 backbone을 “직접 구현한 RSSM/GRU-lite controlled backbone”으로 고정. SOTA는 보조.**
   - 사유: 본 논문이 architecture novelty가 아니라 mechanism novelty이므로 backbone confound를 통제하기 위함.
   - 위치: `ref/PART0_IMPLEMENTATION_STRATEGY.md` §1.1 ~ §1.5.
   - 영향: 이번 6세션에서 Dreamer-style 구현은 절대 만들지 않는다. 이는 Session 2에는 직접 영향이 적지만 (Session 2는 환경만 다룸), 환경 info 노출이 “controlled backbone 위 mechanism”에서 활용 가능한 형태인지 확인하는 기준이 된다.

---

## 8. Session 2 시작 시 권장 첫 작업 순서

본 세션의 다음 세션이 코드 작성을 시작할 때 권장하는 순서. 강제 사항은 아니지만, 이 순서가 의존성 cycle을 가장 잘 막는다.

1. `falsifiable_regime_world_model/rg4f/types.py` (의존성 0).
2. `falsifiable_regime_world_model/rg4f/config.py` (types만 의존).
3. `falsifiable_regime_world_model/rg4f/fields.py` (types, config).
4. `falsifiable_regime_world_model/rg4f/observation.py` (types, config).
5. `falsifiable_regime_world_model/rg4f/tasks.py` (types, config).
6. `falsifiable_regime_world_model/rg4f/map_generator.py` (types, config, fields, tasks 일부).
7. `falsifiable_regime_world_model/rg4f/env.py` (모두 의존).

각 파일 작성 직후 짧은 smoke import 또는 한 episode reset/step 확인 정도만 수행. 자동화된 테스트 스위트는 Session 4 책임이므로 깊게 만들지 않는다.

---

## 9. Session 2 → Session 3 인계 시 작성해야 할 문서

Session 2 종료 시 `docs/SESSION2_HANDOFF.md`를 새로 작성한다. 이 문서에는 최소 다음을 포함:

- Session 2에서 실제로 생성된 파일 목록.
- 각 파일의 외부 노출 API (`RG4FEnv` public method, key dataclass).
- Session 2에서 PART0/RG4F_Environment_Plan과 다르게 결정한 항목 (있다면, 사유와 함께).
- Session 3의 시작점: `scripts/generate_dataset.py`와 `configs/dataset_default.yaml`이 어떤 API에 어떻게 의존하면 되는지.
- 알려진 미해결 ambiguity / TODO.

---

## 10. 본 문서가 Session 2에 던지는 단 한 줄 요약

> **environment만 만든다. controlled backbone 위 mechanism 검증을 가능케 하는 reset/step/info 컨트랙트를 `local_obs_size=5` default로 구현한다. 모델/dataset/planner/SOTA는 절대 건드리지 않는다.**
