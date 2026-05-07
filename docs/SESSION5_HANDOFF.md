# SESSION 5 → SESSION 6 Handoff

> 본 문서는 다음 Cursor 세션이 이전 대화 맥락 없이 단독으로 Session 6 (환경 코드
> 감사 및 수정 지시문 생성)을 시작할 수 있도록 작성된 인계 문서다. 본 문서만으로
> Session 6의 모든 결정 근거가 추적 가능해야 한다.

---

## 1. Session 5 산출물

### 1.1 생성한 파일

| 경로 | 의미 |
|---|---|
| `data/smoke/` | small smoke dataset (190 episodes, 8 splits, master_seed=42, max_steps=200, behavior_policy=random_biased). |
| `data/smoke/manifest.json` | generation manifest (train_pool, ood_pool, rg4f_config, split_summaries, elapsed_seconds=6.70). |
| `data/smoke/<split>/index.jsonl` | 각 split의 episode lookup. 한 줄당 1 episode. |
| `data/smoke/<split>/episodes/<id>.npz` + `.meta.json` | 각 episode 데이터와 metadata. |
| `data/smoke/validation_report.json` | strict validate 전체 결과 (PASS=2242 / WARN=0 / FAIL=0). |
| `outputs/smoke_inspections/` | split별 inspect_episode ASCII 저장. 10개 파일. |
| `outputs/smoke_stats/` | summary.csv + 8개 split별 distribution CSV + 3개 PNG (episode_length_hist, reward_total_hist, change_point_boxplot). |
| `docs/SMOKE_REPORT.md` | 본 세션의 검증 보고서. PASS/WARN/FAIL, 사람 inspection 요약, 통계 해석, 발견된 이슈, Session 6 감사 권장사항. |
| `docs/SESSION5_HANDOFF.md` | 본 문서. |

### 1.2 수정한 코드

본 세션은 **단 하나의 명백한 코드 결함**을 수정했다:

| 경로 | 수정 사유 | 변경 의미 | backward compatibility |
|---|---|---|---|
| `scripts/inspect_episode.py` | `_print_metadata`의 NOTE 라인 두 곳에서 em dash(`—`)가 Windows cp949 콘솔에서 `UnicodeEncodeError`를 일으켜 `ood_obs_shift` / `ood_field_placement` split inspect가 crash. | (1) NOTE 라인 두 곳의 em dash → ASCII hyphen. (2) `main()` 진입부에 `sys.stdout/stderr.reconfigure(encoding="utf-8", errors="replace")` 안전망 추가 (Python 3.7+; 실패 시 무시). | 영향 없음. dataset / npz / meta / index / manifest / 다른 script에 어떤 변경도 없음. CLI 옵션 / 출력 포맷 / 출력 의미 동일. NOTE 라인 표기만 `—` → `-`. |

### 1.3 수정 안 한 파일

- `falsifiable_regime_world_model/rg4f/{types,config,map_generator,observation,fields,tasks,env,serialization,dataset_io}.py` — 0줄 변경.
- `scripts/{generate_dataset,validate_dataset,plot_dataset_stats}.py` — 0줄 변경.
- `configs/dataset_default.yaml` — 0줄 변경.
- `ref/PART0~3` — 0줄 변경.
- `requirements.txt` — 0줄 변경.
- `docs/RG4F_Environment_Plan.md`, `docs/SESSION1~4_HANDOFF.md` — 0줄 변경.

### 1.4 본 세션에서 명시적으로 수행하지 않은 것 (PART0 §3 / 사용자 요구사항 §1)

- world model / RSSM / GRU-lite / DreamerV3 / SOTA backbone 코드 0줄.
- planner / agent / allocator 코드 0줄.
- 학습 loop, optimizer, training run 0줄.
- 대규모 dataset 생성 0회 (190 episode, 6.7초로 종료).
- env API / serialization API / dataset schema 변경 0회.

---

## 2. Smoke dataset 위치와 실행 명령

### 2.1 smoke dataset 위치

```
C:\Users\computer\Desktop\NeurIPS2026\data\smoke\
  manifest.json
  validation_report.json
  train/
    index.jsonl
    episodes/                  # 50 episode (npz + meta.json 짝)
  valid/                       # 20 episode
  test_id/                     # 20 episode
  ood_room_perm/               # 20 episode
  ood_factor_recomb/           # 20 episode
  ood_param_shift/             # 20 episode
  ood_obs_shift/               # 20 episode
  ood_field_placement/         # 20 episode
```

### 2.2 generate 명령 (재생성)

```powershell
.\.venv\Scripts\python.exe scripts\generate_dataset.py `
  --config configs\dataset_default.yaml `
  --output-root data\smoke `
  --num-train 50 --num-valid 20 --num-test 20 --num-ood-per-type 20 `
  --max-steps 200 --overwrite
```

소요시간: 6.70초. determinism 보장 (master_seed=42 → byte-equal 재현).

### 2.3 validate 명령

```powershell
# strict + 풍부한 보고
.\.venv\Scripts\python.exe scripts\validate_dataset.py `
  --root data\smoke --strict --max-episodes-per-split 50 `
  --json-report data\smoke\validation_report.json --verbose

# determinism check (별도 임시 디렉토리에서 두 번 generator 호출 후 비교)
.\.venv\Scripts\python.exe scripts\validate_dataset.py `
  --root data\smoke --check-determinism `
  --config configs\dataset_default.yaml --max-episodes-per-split 3
```

### 2.4 inspect 명령 (split별)

```powershell
# 기본 (각 split 1 episode, 5 step, ASCII grid + scalar + info)
.\.venv\Scripts\python.exe scripts\inspect_episode.py --root data\smoke `
  --split <split> --index 0 --num-steps 5 --show-grid --show-scalar --show-info `
  --save-ascii outputs\smoke_inspections\<split>_episode0.txt

# field / task detail (ood_room_perm, ood_field_placement)
.\.venv\Scripts\python.exe scripts\inspect_episode.py --root data\smoke `
  --split <split> --index 0 --num-steps 5 --show-grid --show-task --show-fields `
  --save-ascii outputs\smoke_inspections\<split>_episode0_detail.txt
```

본 세션에서 8개 split 모두 정상 출력. 결과는 `outputs\smoke_inspections\`에 저장.

### 2.5 stats 명령

```powershell
.\.venv\Scripts\python.exe scripts\plot_dataset_stats.py `
  --root data\smoke --out outputs\smoke_stats --max-episodes-per-split 50
```

생성물: `summary.csv`, 8개 `<split>_distributions.csv`, 3개 PNG (
`episode_length_hist.png`, `reward_total_hist.png`, `change_point_boxplot.png`).

---

## 3. Session 6 목표 — 환경 코드 감사 및 수정 지시문 생성

PART0 §2 Session 6 정의에 따라 다음을 책임진다:

1. **`docs/ENV_AUDIT_REPORT.md`** 작성:
   - PART1 / PART2 / PART3 / PART0 / RG4F_Environment_Plan vs 실제 구현 간 정합성 표.
   - 위험 요소, 미해결 ambiguity 정리.
   - reviewer 시각의 가능한 공격 라인 (mechanism vs backbone, OOD strength,
     reveal vs shift, sparse coupling, partial observability, task permutation 등) 별
     방어 가능성.
2. **`docs/ENV_FIX_INSTRUCTIONS.md`** 작성:
   - 본격 학습 페이즈로 넘어가기 전 수정해야 할 항목 리스트.
   - 각 항목에 대해: 파일 경로 / 함수 / 변경 전 / 변경 후 / 검증 방법.
   - 우선순위 (blocker / high / medium / low).
3. **`docs/SESSION6_HANDOFF.md`** 작성:
   - 1차 페이즈 마무리 + 다음 페이즈 (model / planner / 학습) 진입점.
   - 본 6세션 산출물의 최종 디렉토리 구조 요약.

Session 6는 **수정 지시문**을 만들 뿐, 본격 코드 수정은 다음 페이즈 책임이다 (단,
명백한 micro-fix는 §6에서 결정).

---

## 4. Session 6에서 반드시 읽어야 할 파일

권장 읽기 순서:

1. `ref/PART0_IMPLEMENTATION_STRATEGY.md` — 6세션 전체 계획, 11개 금지사항, mechanism vs
   backbone 결정.
2. `docs/RG4F_Environment_Plan.md` — 환경 single source of truth.
3. `docs/SESSION1_HANDOFF.md` — Session 2의 contract.
4. `docs/SESSION2_HANDOFF.md` — RG4FEnv 외부 노출 API + info schema.
5. `docs/SESSION3_HANDOFF.md` — dataset generator 사용법 + 저장 schema + split 구현 +
   behavior policy.
6. `docs/SESSION4_HANDOFF.md` — validate / inspect / stats 사용법 + invariant 목록 +
   known limitations.
7. `docs/SESSION5_HANDOFF.md` — 본 문서.
8. `docs/SMOKE_REPORT.md` — Session 5 검증 결과 + Research Design Check + Issues.
9. `falsifiable_regime_world_model/rg4f/types.py` — enum / dataclass schema.
10. `falsifiable_regime_world_model/rg4f/config.py` — yaml에 매핑되는 RG4FConfig.
11. `falsifiable_regime_world_model/rg4f/env.py` — reset/step/info 컨트랙트.
12. `falsifiable_regime_world_model/rg4f/{map_generator,observation,fields,tasks}.py` —
    각 책임 영역.
13. `falsifiable_regime_world_model/rg4f/serialization.py` + `dataset_io.py` — episode 저장 /
    로드.
14. `scripts/generate_dataset.py` — split-aware policy + behavior policy + OOD 차별화 로직.
15. `scripts/validate_dataset.py` — invariant 검증 로직 (Session 6 감사의 직접적 baseline).
16. `scripts/inspect_episode.py` — Session 5에서 micro-fix됨 (cp949 호환).
17. `scripts/plot_dataset_stats.py` — 통계 aggregation.
18. `configs/dataset_default.yaml` — 모든 환경/생성 수치의 single source of truth.
19. `ref/PART1_PROBLEM_FRAMING.md`, `ref/PART2_ALGORITHM.md`, `ref/PART3_EXPERIMENT_DESIGN.md`
    — 알고리즘/실험 설계 contract. 환경이 이를 어떻게 enable해야 하는지의 근거.
20. `requirements.txt` — 사용 가능한 dependency. 변경 금지.

---

## 5. Session 6 감사 포인트

본 세션에서 직접 검증하거나 발견된 사항으로 Session 6에서 반드시 깊게 감사할 것:

### 5.1 PART0~3 설계 vs 실제 구현 일치 여부

| 항목 | 본 smoke에서 일치? | Session 6 확인 |
|---|---|---|
| local_obs_size=5 메인 + ablation [3,5,7] | YES | yaml + RG4FConfig.__post_init__ + npz shape 모두 일관. |
| 5x5 한 방의 39.1% 노출 (PART3 §3.16 갱신) | YES | 한 방 8x8 = 64칸 중 25칸 = 39.1%. |
| 5개 상태값 (vision/mobility/interaction/noise/control_drift) | YES | scalar.shape (T, 14) + true_state (T, 5). |
| sparse coupling \|coupled_states\| ≤ 2 | YES | validate sparse_coupling.le2 모든 episode PASS. |
| 8개 split 모두 발견 | YES | manifest.splits + index.jsonl 8개. |
| ood_room_perm disjoint | YES | manifest invariant + episode forced_permutation 검증. |
| reveal vs shift 분리 라벨 | YES | npz의 `reveal_event` + `shift_event` + `reveal_or_shift` int enum. |
| mobility vs control-drift 분리 | YES | env.py의 cooldown 함수와 remap 함수 분리. info의 `mobility_mode` ≠ `control_mode`. |
| control-drift 이산 remap (5 modes) + 약한 miscontrol + 주기적 slip | YES | smoke inspection의 `raw=W eff=S` (REV) + `miscontrol_p=0.300 periodic_slip=True` 확인. |
| invisible field mean drift + event-triggered shift | YES | `field_mu_drift_sigma=0.01` + `shift_prob_per_*=0.05`. |

### 5.2 Session 6에서 결정 필요한 사항

1. **`change_point = shift_event` 정의의 reviewer 방어**: PART2 §3.7.3 "circular logic"
   주장에 어떻게 답할지. 현재 ground-truth 라벨은 (a) `apply_event_shift`의 field mu jump,
   (b) Task C `on_enter_room`의 initial_d 강제 set, 두 외부 evidence 기반. control_mode
   mid-episode abrupt remap을 추가하면 PART2 §3.10.3 정합성 강화 — Session 6에서 추가 여부
   결정.
2. **train family filter 정책**: yaml의 `split_policy.factor_recomb.train_field_families:
   [0,1]`이 metadata 라벨일 뿐 강제되지 않는다. 두 안 중 결정:
   - 안 1 (recommended): yaml에 `train_apply_family_filter: bool` 추가 + generator에서 train
     도 family filter 강제. ood_factor_recomb의 disjoint가 더 엄격해짐.
   - 안 2: 현재 정책 유지 + paper의 OOD protocol 설명에 "train pool 안에서는 4 family 자유
     허용" 솔직히 명시.
3. **task supervision data 강화 방안**: random_biased + 200-step에서 task room 진입이 sparse.
   학습 단계에서:
   - `episode_max_steps=600` (yaml default) + train 5000 episode 사용 시 통계적으로 충분.
   - 또는 단순 task-aware sampler (예: 시작 시 한 방향으로 가는 epsilon-greedy) 추가. 단,
     PART0 §3 §6 "agent 코드 금지"와 충돌하지 않도록 단순 sampler 형태로 한정해야 함.
4. **ood_obs_shift의 visual variant 강화 여부**: 현재는 channel index permutation. PART3
   원안의 "tile/sprite 변경"과 표현 방식이 다름. novelty detector false positive 검증에는
   충분하지만 paper writeup에서 명시적으로 다룰 필요.
5. **inspect_episode의 ood_obs_shift inverse permutation 옵션**: 디버깅 편의성. 학습에는
   영향 없음. low priority.

### 5.3 Session 6에서 보류 가능한 사항

- ASCII rendering의 channel permutation inverse 자동 적용 (low priority).
- visual variant (cue 채널 값 분포 변경) 추가 (현 channel index 변경으로 충분).
- object dtype field 부재 (의도적 안전장치).
- mid-episode random_biased policy의 task room 진입 sparse (학습 페이즈에서 episode 길이 +
  episode 수 증가로 해결).

---

## 6. Session 6 금지사항 (PART0 §3 / 사용자 요구사항 재확인)

1. **world model / RSSM / GRU-lite / DreamerV3 / SOTA backbone 코드** 0줄.
2. **planner / agent / allocator / world model rollout** 코드 0줄.
3. **학습 loop, optimizer, training run** 0줄.
4. **대규모 full dataset 생성** 금지. (필요 시 별도 페이즈.)
5. **`requirements.txt` 변경** 금지.
6. **`ref/PART0~3` 변경** 금지.
7. **`docs/RG4F_Environment_Plan.md` 변경** 금지 (PART1~3와 동급 frozen 문서).
8. **`docs/SESSION1~5_HANDOFF.md` 변경** 금지.
9. **`docs/SMOKE_REPORT.md` 변경** 금지 (Session 5의 인계 evidence).

Session 6의 책임은 "감사 + 수정 지시문"이지 "수정 실행"이 아니다. 단, 수정 지시문 작성을
위해 Read / Grep / SemanticSearch / Glob 등 read-only tool은 자유롭게 사용 가능.

---

## 7. Session 6 → 본격 학습 페이즈 진입 시 인계 자산

Session 6 종료 시점에 다음이 모두 갖춰져야 학습 페이즈가 단독 시작 가능:

| 자산 | 위치 |
|---|---|
| RG-4F 환경 코드 | `falsifiable_regime_world_model/rg4f/*.py` |
| dataset generator | `scripts/generate_dataset.py` + `configs/dataset_default.yaml` |
| validation / inspection / stats 도구 | `scripts/{validate_dataset,inspect_episode,plot_dataset_stats}.py` |
| episode I/O 라이브러리 | `falsifiable_regime_world_model/rg4f/{serialization,dataset_io}.py` |
| smoke dataset (검증용) | `data/smoke/` |
| validation evidence | `data/smoke/validation_report.json` |
| stats evidence | `outputs/smoke_stats/summary.csv` + 분포 CSV/PNG |
| 6세션 docs | `ref/PART0~3`, `docs/RG4F_Environment_Plan.md`, `docs/SESSION1~6_HANDOFF.md`, `docs/SMOKE_REPORT.md`, `docs/ENV_AUDIT_REPORT.md`, `docs/ENV_FIX_INSTRUCTIONS.md` |

학습 페이즈는 위 자산을 그대로 사용해 controlled backbone (RSSM-lite / GRU-lite) 위에서
mechanism (regime head / change-point head / falsification score / action relevance / compute
reallocation / adaptation vs correction)을 구현하는 것을 시작점으로 삼는다.

---

## 8. Self-Audit 결과

| Check | Status | Evidence |
|---|---|---|
| Session 1~4 산출물을 모두 읽었는가 | PASS | PART0/Plan/SESSION1~4_HANDOFF/PART1~3 + scripts/{generate,validate,inspect,plot}.py + dataset_default.yaml + 일부 rg4f/*.py 모두 Read 도구로 확인. |
| 기존 ref/PART0~3와 requirements.txt를 수정하지 않았는가 | PASS | 변경 0줄. |
| world model / planner / agent 코드를 만들지 않았는가 | PASS | torch import 0회. world_model/planner/agent 디렉토리 없음. |
| full dataset이 아니라 small smoke dataset만 생성했는가 | PASS | 190 episode = 50 + 20 + 20 + 5×20 (PART0 §2 Session 5 §완료 기준 수준). 생성 6.7초. |
| data/smoke에 모든 split이 생성됐는가 | PASS | manifest.splits 8개, 각 split의 index.jsonl line 수 = 요청한 episode 수. |
| validate_dataset --strict가 FAIL 0으로 통과했는가 | PASS | PASS=2242 / WARN=0 / FAIL=0 / exit code 0. |
| determinism check가 통과했는가 | PASS | PASS=332 / WARN=0 / FAIL=0. byte-equal 재현. |
| 각 split 최소 1개 episode를 inspect했는가 | PASS | 8개 split × 1개 episode + ood 2개 detail = 10개 ASCII 파일 `outputs/smoke_inspections/`. |
| OOD split 최소 2개에서 field/task detail을 확인했는가 | PASS | `ood_room_perm_episode0_detail.txt` + `ood_field_placement_episode0_detail.txt`. |
| plot/stat summary를 생성했는가 | PASS | `outputs/smoke_stats/summary.csv` + 8개 split distribution CSV + 3개 PNG. |
| local_obs_size 기본값 5가 유지되는가 | PASS | yaml `local_obs_size: 5`, manifest `rg4f_config.local_obs_size: 5`, 모든 npz `(T, 5, 5, 10)` 확인. |
| task_id/action/change_point 분포가 collapse하지 않았는가 | PASS | action 분포 random_biased target과 일치 (movement 54.92%, E 14.44%, state-adjust 30.64%, WAIT 0%). cp_mean split별 0.05~0.45. task_id가 일부 split에서 0/1/2 모두 등장. |
| OOD 5종 invariant가 모두 유지되는가 | PASS | room_perm.disjoint_from_train, factor_recomb.families_in_ood_pool, param_shift.differs_from_train, obs_shift.channel_perm_valid + no_dynamics_change, field_placement.relocate_flag 모두 PASS. |
| known limitation을 재평가했는가 | PASS | SMOKE_REPORT §5.6에서 5개 항목 모두 재평가. 본 smoke에서 문제 없음 + Session 6 감사 권장사항으로 분류. |
| docs/SMOKE_REPORT.md를 작성했는가 | PASS | `docs/SMOKE_REPORT.md` 8개 섹션 (요청 §7 구조 그대로). |
| docs/SESSION5_HANDOFF.md를 작성했는가 | PASS | 본 문서. |

---

## 9. 본 문서가 Session 6에 던지는 단 한 줄 요약

> **환경 코드와 dataset generator를 reviewer 시각으로 감사한다. PART0~3 / Plan과 실제
> 구현의 정합성 표 + 학습 전 수정 지시문 + 1차 페이즈 마무리 핸드오프, 세 문서만 만든다.
> 모델 / planner / 학습 / SOTA / 대규모 dataset 생성은 절대 건드리지 않는다.**
