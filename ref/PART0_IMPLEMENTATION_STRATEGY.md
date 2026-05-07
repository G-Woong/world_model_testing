# PART 0 — Implementation Strategy

## 0. 이 문서의 위치

본 문서는 NeurIPS 2026 메인트랙 제출(가제: *Wrong-Hypothesis-Aware World-Model Planning via Falsification-Driven Compute Reallocation*) 구현의 “북극성”이다. PART1/2/3가 “왜·무엇·어떻게 평가”를 정의했다면, PART0는 “그 주장을 어떤 코드로, 어떤 backbone 위에서, 어떤 순서로 검증할 것인가”를 고정한다.

본 문서는 코드를 만들지 않는다. 다음 세션들이 흔들리지 않도록 구현전략과 절대 원칙을 못 박는 contract 역할만 한다. 이후 모든 세션은 본 문서와 충돌하는 결정을 해서는 안 되며, 만약 충돌이 발생하면 본 문서를 먼저 수정한 뒤 후속 세션을 진행한다.

---

## 1. 논문 구현전략

### 1.1 본 논문은 architecture novelty가 아니라 mechanism novelty다

본 논문의 기여는 “더 강력한 world-model backbone을 새로 만들었다”에 있지 않다. 기여는 다음 메커니즘 묶음에 있다.

- hidden state / hidden regime / change-point의 명시적 분리
- reveal vs shift 구분
- current vs alternative regime hypothesis 비교
- falsification score (likelihood ratio + change-point posterior)
- action relevance (value gap / action flip)
- compute allocation이 아니라 **compute reallocation** (current-rollout → alternative-rollout)
- control-drift와 mobility의 분리 (이산 remap/약한 miscontrol vs latency/cooldown)
- adaptation vs correction의 cost-sensitive 선택
- default utility + local override (target band)
- sparse invisible field coupling
- small drift / abrupt shift의 동시 처리
- wrong-hypothesis persistence time(WHPT) 감소

따라서 “backbone을 무엇을 쓰느냐”는 본 논문의 변수가 아니라 **통제해야 하는 confound**다. SOTA backbone(DreamerV3 등) 위에서 실험을 진행하면 성능 차이가 backbone의 capacity, 학습 안정성, 시각 인코딩 품질 등에 묻힐 수 있다. 그러면 reviewer는 “본 논문 기여가 mechanism인가 SOTA backbone 활용인가”를 구분할 수 없게 된다.

### 1.2 메인 backbone은 직접 구현한 RSSM/GRU-lite controlled backbone

본 논문의 메인 실험은 우리가 직접 통제 가능한 controlled backbone 위에서 수행한다. 구체적으로는 다음 두 옵션 중 하나를 메인으로 둔다.

- **GRU-lite recurrent latent backbone**: 단일 recurrent state + 5개 head (state head / regime head / change-point head / observation reconstruction head / value head). 가장 단순하고, 모든 ablation의 “same-backbone control”을 가장 깔끔하게 만든다.
- **RSSM-lite (Recurrent State-Space Model, 경량 버전)**: deterministic recurrent + stochastic latent split. Dreamer 계열과 가장 가까우면서도 우리가 모든 hyperparameter, latent 차원, regularizer, training schedule을 직접 통제한다.

이 두 옵션 중 어느 것을 메인으로 쓰든, 다음 조건을 반드시 만족해야 한다.

1. 모든 ablation(no regime, no change-point, raw mismatch only, no action relevance, monolithic regime 등)이 **동일한 backbone, 동일한 capacity, 동일한 training schedule, 동일한 hyperparameter** 위에서 수행되어야 한다.
2. backbone parameter 수, latent 차원, optimizer, 학습 step 수가 모든 비교 모델 간에 통제 변수로 고정되어야 한다.
3. 모든 reallocation 메커니즘은 backbone 안에 박는 것이 아니라 backbone 위에 얹는 “head + allocator + planner” 구조로 구현되어 on/off가 가능해야 한다.

이 조건이 충족되어야 “성능 차이가 mechanism에서 왔다”는 주장을 reviewer 앞에서 방어할 수 있다.

### 1.3 Dreamer / SOTA world model은 보조 baseline / 확장 실험 / reviewer 방어용 비교군

DreamerV3, Dreamer-style, 기타 SOTA world model은 메인이 아니다. 이들은 다음 위치에만 둔다.

- **확장 실험 (Appendix급 또는 Supplementary)**: “mechanism이 SOTA backbone에 얹어도 작동하는가?”를 보이는 transferability 실험.
- **보조 baseline**: full-success 비교가 아니라, frontier 비교에서 “SOTA backbone + naive planner”와 “controlled backbone + 제안 mechanism” 간의 compute-normalized return 비교.
- **reviewer 방어**: “왜 SOTA를 안 썼느냐”라는 질문에 “본 논문은 mechanism 논문이며 SOTA에서도 같은 메커니즘이 작동함을 transferability 실험으로 보였다”고 답하기 위한 카드.

따라서 SOTA backbone 통합은 **메인 실험이 모두 안정화된 이후** 진행하며, 본 6개 세션 안에서는 어떤 SOTA backbone 코드도 구현하지 않는다.

### 1.4 핵심 ablation은 반드시 same-backbone 조건에서 비교

PART3 §3.23의 ablation들(no regime, no change-point, raw mismatch only, no action relevance, risk-only gate, no memory, monolithic regime, no faithfulness, no adaptation/correction distinction, no sparse coupling)은 전부 **동일 backbone + 동일 capacity + 동일 학습 schedule** 위에서만 의미 있다.

만약 ablation A는 우리 controlled backbone에서 돌리고 ablation B는 DreamerV3 위에서 돌린다면, 그 비교는 무효다. 따라서 본 논문의 모든 메인 ablation은 §1.2의 controlled backbone에서만 수행한다. SOTA backbone 위에서의 ablation은 “mechanism이 이식 가능한가”를 보이는 보조 결과로만 둔다.

### 1.5 SOTA backbone을 메인으로 쓰면 위험한 이유 (요약)

- 기여가 mechanism이 아니라 backbone 성능에 묻힐 수 있다.
- backbone hyperparameter 차이가 ablation 차이보다 클 수 있다.
- 학습 비용이 폭발하여 6개 세션 안에 메커니즘 자체를 통제 검증할 수 없다.
- DreamerV3-style 코드는 reproducibility 측면에서 우리가 모든 변수를 잡기 어렵다.
- reviewer는 “이게 mechanism의 효과인지 SOTA에 mechanism을 끼워 맞춘 효과인지” 의심한다.

따라서 메인은 controlled backbone, SOTA는 보조다. 이 결정은 본 6개 세션 동안 절대 뒤집히지 않는다.

---

## 2. 전체 6세션 실행 계획

본 프로젝트의 1차 목표는 **RG-4F 월드맵/데이터셋 생성 가능 상태까지 도달**하는 것이다. 모델 학습, planner 구현, 본 실험은 본 6세션 이후 별도 페이즈에서 진행한다.

각 세션은 단독으로 실행 가능해야 하며, 세션 간 상태는 오직 “파일”로만 인계된다. (chat history나 휘발성 메모는 신뢰하지 않는다.)

### Session 1 — 구현전략 + RG-4F 환경 설계 문서 (현재 세션)

- **목적**: 다음 5개 세션이 흔들리지 않도록 mechanism-vs-architecture 우선순위, RG-4F 환경 사양, partial observability 기본값을 문서로 고정한다.
- **입력 파일**: `ref/PART1_PROBLEM_FRAMING.md`, `ref/PART2_ALGORITHM.md`, `ref/PART3_EXPERIMENT_DESIGN.md`, `requirements.txt`.
- **생성 파일**: `ref/PART0_IMPLEMENTATION_STRATEGY.md`, `docs/RG4F_Environment_Plan.md`, `docs/SESSION1_HANDOFF.md`.
- **완료 기준**:
  - 위 3개 문서가 모두 존재한다.
  - PART0에 mechanism-novelty 우선 원칙과 6세션 계획이 모두 명시되어 있다.
  - RG4F_Environment_Plan에 월드맵 구조, partial observability 기본값(`local_obs_size=5`), 5개 상태값, Task A/B/C/D, invisible field sparse coupling, split 설계, config 항목이 모두 포함되어 있다.
  - SESSION1_HANDOFF에 Session 2가 단독 실행 가능한 정보가 포함되어 있다.
  - 본 세션에서 Python 코드, src/, scripts/, configs/ 어떤 파일도 생성되지 않는다.
- **다음 세션 handoff 항목**: PART0, RG4F_Environment_Plan, SESSION1_HANDOFF 3개 파일.

### Session 2 — RG-4F 환경 코드 구현

- **목적**: RG-4F 환경의 reset/step/observe 인터페이스를 구현한다. dataset generator, model, planner는 구현하지 않는다.
- **입력 파일**: `ref/PART0_IMPLEMENTATION_STRATEGY.md`, `docs/RG4F_Environment_Plan.md`, `docs/SESSION1_HANDOFF.md`, `ref/PART1~3`.
- **생성 파일**:
  - `falsifiable_regime_world_model/rg4f/types.py`
  - `falsifiable_regime_world_model/rg4f/config.py`
  - `falsifiable_regime_world_model/rg4f/map_generator.py`
  - `falsifiable_regime_world_model/rg4f/observation.py`
  - `falsifiable_regime_world_model/rg4f/fields.py`
  - `falsifiable_regime_world_model/rg4f/tasks.py`
  - `falsifiable_regime_world_model/rg4f/env.py`
- **완료 기준**:
  - `env.reset(seed=...)`로 초기 관측을 받을 수 있다.
  - `env.step(action)`이 (obs, reward, terminated, truncated, info)를 반환한다.
  - obs는 `local_obs_size=5` 기본값을 따르고 config로 {3, 5, 7}이 변경 가능하다.
  - info에 `true_state`, `true_regime`, `change_point`, `task_id`, `room_id`, `event_token`, `target_band`, `field_info`가 기록된다.
  - 동일 seed에서 동일한 trajectory가 재현된다 (deterministic).
  - dataset 저장 코드, 모델 코드, planner 코드는 작성하지 않는다.
- **다음 세션 handoff 항목**: 위 7개 코드 파일과 `docs/SESSION2_HANDOFF.md`.

### Session 3 — Dataset generator + config 구현

- **목적**: RG-4F 환경에서 episode 단위 데이터셋을 생성하고 disk에 저장하는 generator + 기본 config를 구현한다.
- **입력 파일**: Session 2까지의 생성물 + `docs/SESSION2_HANDOFF.md`.
- **생성 파일**:
  - `scripts/generate_dataset.py`
  - `configs/dataset_default.yaml`
  - (필요시) `falsifiable_regime_world_model/rg4f/dataset.py`
- **완료 기준**:
  - 단일 명령으로 train/valid/test_id/OOD 각 split별 episode를 생성할 수 있다.
  - episode metadata에 split, map_family_id, task_permutation, regime_factor, field_coupling_id, drift/shift schedule이 모두 포함된다.
  - episode 저장 포맷이 명시되어 있고 (예: `.npz` 또는 `.pkl` per episode + `index.jsonl`), 추후 dataloader에서 random access가 가능하다.
  - config 파일이 §3.9의 모든 항목을 포함한다.
  - 학습 코드, agent 코드, planner 코드는 작성하지 않는다.
- **다음 세션 handoff 항목**: 위 코드 파일과 `docs/SESSION3_HANDOFF.md`.

### Session 4 — Inspection / validation script 구현

- **목적**: 생성된 데이터셋이 PART0/RG4F_Environment_Plan과 일치하는지 검증하는 스크립트를 구현한다.
- **입력 파일**: Session 3까지의 생성물 + `docs/SESSION3_HANDOFF.md`.
- **생성 파일**:
  - `scripts/inspect_episode.py` (단일 episode 시각화/통계 출력)
  - `scripts/validate_dataset.py` (split 단위 invariant 검증)
- **완료 기준**:
  - inspect_episode가 임의 episode를 받아 (a) action sequence (b) true_state/true_regime trajectory (c) change_point 위치 (d) reveal/shift 라벨 (e) target band hit 여부 (f) reward decomposition을 출력한다.
  - validate_dataset이 다음 invariant를 자동 검증한다:
    - split별 episode 수가 config와 일치
    - room-task permutation이 train과 OOD 사이에서 disjoint
    - factor recombination OOD가 train에서 보지 못한 조합만 포함
    - parameter shift OOD가 train range 밖
    - invisible field coupling이 sparse condition (`|{k: g_{j,k} ≠ 0}| ≤ 2`)을 만족
    - seed 고정 시 episode 재현 가능
  - 학습/모델 코드는 여전히 작성하지 않는다.
- **다음 세션 handoff 항목**: 위 코드 파일과 `docs/SESSION4_HANDOFF.md`.

### Session 5 — Small smoke dataset 생성 및 검증

- **목적**: 실제 작은 규모의 smoke dataset을 한 번 생성하고 inspect/validate를 통해 환경+generator+config가 end-to-end로 일관되는지 확인한다.
- **입력 파일**: Session 4까지의 생성물 + `docs/SESSION4_HANDOFF.md`.
- **생성 파일**:
  - `data/smoke/` 아래에 train/valid/test_id/OOD 각 split의 작은 데이터셋 (예: split당 episode 50~200개 수준).
  - `docs/SMOKE_REPORT.md` (validate_dataset 결과, inspect_episode 샘플 출력, 발견된 이슈)
- **완료 기준**:
  - validate_dataset이 모든 invariant를 통과한다.
  - inspect_episode가 각 split에서 최소 1개 episode를 정상 출력한다.
  - 발견된 모든 이슈가 SMOKE_REPORT에 기록된다 (이슈가 없어도 “이상 없음”을 명시).
  - 이 단계까지 모델 학습은 일절 수행하지 않는다.
- **다음 세션 handoff 항목**: smoke dataset 경로, SMOKE_REPORT, `docs/SESSION5_HANDOFF.md`.

### Session 6 — 환경 코드 감사 및 수정 지시문 생성

- **목적**: Session 1~5의 결과를 외부 reviewer 시각으로 다시 감사하고, 본격 학습 페이즈로 넘어가기 전에 “고쳐야 할 것” 리스트를 만든다.
- **입력 파일**: Session 5까지의 모든 생성물.
- **생성 파일**:
  - `docs/ENV_AUDIT_REPORT.md` (PART1/2/3 vs 실제 구현 간 불일치 리스트, 위험 요소, 미해결 ambiguity)
  - `docs/ENV_FIX_INSTRUCTIONS.md` (다음 페이즈에서 수행할 코드 수정 지시문, 우선순위, 검증 방법)
  - `docs/SESSION6_HANDOFF.md` (전체 1차 마무리 + 다음 페이즈 진입점 정의)
- **완료 기준**:
  - 감사 결과가 PART1/2/3와의 정합성 표로 정리되어 있다.
  - 모든 수정 지시문이 “파일 경로 / 함수 / 변경 전 / 변경 후 / 검증 방법” 항목을 포함한다.
  - 학습 페이즈 진입 전 반드시 닫혀야 할 blocker가 식별되어 있다.
- **다음 세션 handoff 항목**: 위 3개 문서. 이후 페이즈는 학습/모델/planner 페이즈로 넘어간다.

---

## 3. 금지사항

본 6개 세션 전체에 걸쳐 다음을 금지한다. 어느 세션이든 아래 행위를 발견하면 즉시 중단하고 PART0를 우선 수정한다.

1. **처음부터 DreamerV3 전체 구현 금지.** 메인 실험이 끝날 때까지 SOTA backbone 코드를 만들지 않는다.
2. **SOTA 코드 복붙 중심 구현 금지.** controlled backbone은 반드시 우리가 직접 작성한 짧은 코드여야 하며, 외부 SOTA 레포에서 가져온 큰 코드 블록을 그대로 메인 backbone으로 쓰지 않는다.
3. **메커니즘 검증 전 대규모 학습 금지.** dataset 검증 + 환경 감사가 끝나기 전에는 long-running training을 시작하지 않는다.
4. **config 없이 hard-coded 수치 박기 금지.** 모든 수치 (room size, drift_strength, target_band_width, num_train, …)는 `configs/*.yaml`을 통해서만 흘러야 한다. 코드 내부 magic number 금지.
5. **debug/info trace 없는 환경 구현 금지.** env.step의 info에는 §2.5(완료 기준)의 모든 진단 변수가 반드시 포함되어야 하며, debug 모드에서 step 단위 로그가 가능해야 한다.
6. **모델 학습 / agent / planner 구현을 월드맵 생성 단계에 섞는 것 금지.** 본 6세션은 “환경 + 데이터셋”까지만 다룬다. 그 안에서 model/agent/planner 코드는 일절 만들지 않는다.
7. **휴리스틱 / 키워드 기반 단기 땜빵 금지.** 예: “task_id 문자열로 분기”, “room name 하드코딩으로 task 매핑”, “magic threshold로 change-point 라벨 부여” 등은 전부 안티패턴이다. 모든 분기는 config + factorized regime code + 명시적 schedule을 통해서만 결정된다.
8. **reveal과 shift를 한 라벨로 합치는 것 금지.** 환경은 ground-truth `reveal_event`와 `shift_event`를 별도 채널로 기록해야 한다.
9. **mobility와 control-drift를 같은 변수로 다루는 것 금지.** mobility는 cooldown/latency 축, control-drift는 action remap/miscontrol 축이다. 두 변수는 코드, info, metadata 레벨에서 분리되어 있어야 한다.
10. **invisible field가 5개 상태를 동시에 흔드는 구현 금지.** 모든 field는 sparse coupling (`|{k: g_{j,k} ≠ 0}| ≤ 2`)을 만족해야 하며, validate_dataset이 이를 자동 검증해야 한다.
11. **task A/B/C/D를 room 위치에 고정하는 구현 금지.** room-task permutation이 episode-level로 sampling되어야 하며, train/test 사이에 disjoint permutation을 보장해야 한다.

---

## 4. 오늘의 범위

- **오늘 목표**: RG-4F 월드맵/데이터셋 생성 가능 상태까지 도달하는 6세션 중 첫 세션을 마치는 것.
- **이번 Session 1의 범위**: 문서화까지만. 코드 작성 없음. 어떤 환경도 reset되지 않으며, 어떤 모델도 학습되지 않는다.
- **다음 세션부터의 범위**: Session 2부터 RG-4F 환경 코드 구현이 시작된다. Session 5까지 “환경 + 데이터셋 + 검증”이 닫힌다. Session 6에서 감사 및 수정 지시문이 만들어지고, 이후 별도 페이즈에서 model / planner / 학습이 시작된다.

---

## 5. 본 문서의 변경 정책

- 본 문서를 변경하려면 반드시 (a) 변경 사유 (b) 어떤 PART1/2/3 조항과 연결되는지 (c) 어떤 세션의 완료 기준이 함께 갱신되어야 하는지를 기록한 뒤 갱신한다.
- 단순한 오타 수정은 변경 정책의 적용 대상이 아니다.
- 본 문서가 PART1/2/3와 충돌할 경우 PART1/2/3가 우선한다. PART0는 PART1/2/3를 “구현 관점에서 어떻게 운영할지” 정의하는 보조 문서다.
