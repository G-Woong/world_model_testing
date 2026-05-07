# SESSION 6 → World Model Phase Handoff

> 본 문서는 RG-4F 환경/데이터셋 생성 6세션 페이즈를 마무리하고, 다음 "월드모델 학습
> 페이즈"로 넘어가기 위한 인계 문서다. Session 6는 6/6 마지막 세션이며, 이후의 모든
> 페이즈(WM Session 1~6, 본 실험, 논문 작성)는 본 인계 문서를 출발점으로 삼는다.

---

## 1. Session 6 생성물

### 1.1 본 세션에서 생성한 파일 (4개 문서)

| 경로 | 의미 |
|---|---|
| `docs/ENV_AUDIT_REPORT.md` | PART0~3 / RG4F_Environment_Plan vs 실제 구현의 정합성 표 + Core Mechanism Support Audit (hidden state / regime / change-point / reveal-shift / falsification / action relevance) + OOD Validity Audit + Data Collection Policy Audit + Known Limitations Reassessment + Final Audit Verdict. |
| `docs/ENV_FIX_INSTRUCTIONS.md` | Fix Priority Table (P0/P1/P2/Defer/No-fix) + 5개 후보 이슈 각각의 Problem/Why/Evidence/Recommended action/Target files/Backward compatibility/Verification command + Minimal Patch Plan. |
| `docs/RG4F_EXECUTION_GUIDE.md` | 가상환경 확인 → smoke 재생성 → strict validation → determinism check → inspect → stats → 옵션 조절 가이드 → 학습용 full dataset 권장 시작값 → troubleshooting. 모든 명령은 실제 PowerShell 명령. |
| `docs/SESSION6_HANDOFF.md` | 본 문서. |

### 1.2 본 세션에서 수정한 코드

**0줄.** Session 5에서 `inspect_episode.py`의 em-dash → ASCII hyphen + utf-8 reconfigure 안전망이 micro-fix 완료되었으므로, Session 6에서는 추가 수정 불필요. 모든 검증 (validate strict, determinism, inspect 8 splits)이 PASS이므로 명백한 버그 없음.

### 1.3 본 세션에서 명시적으로 수행하지 않은 것 (PART0 §3 / 사용자 요구사항)

- world model / RSSM / GRU-lite / DreamerV3 / SOTA backbone 코드 0줄.
- planner / agent / allocator 코드 0줄.
- 학습 loop, optimizer, training run 0줄.
- 학습용 full dataset 생성 0회 (smoke만 재검증).
- env API / serialization API / dataset schema 변경 0회.
- `ref/PART0~3` 변경 0줄.
- `requirements.txt` 변경 0줄.
- `docs/RG4F_Environment_Plan.md`, `docs/SESSION1~5_HANDOFF.md`, `docs/SMOKE_REPORT.md` 변경 0줄.

---

## 2. 최종 판정

### **CONDITIONAL PASS — 월드모델 학습 단계로 진행 가능.**

근거 요약:

1. **Strict validation**: PASS=2242 / WARN=0 / FAIL=0 / exit code 0 (Session 6 재실행, `data/smoke/validation_report_session6.json`).
2. **Determinism check**: PASS=332 / WARN=0 / FAIL=0 (byte-equal 재현).
3. **PART0~3 모든 핵심 설계가 코드/yaml/dataset에 일관 반영**: `local_obs_size=5` main + `[3,5,7]` ablation, 중앙홀+4방+복도 cross 토폴로지, 5개 상태값 numeric, sparse coupling `|·|≤2`, mobility ↔ control-drift 분리, reveal vs shift 분리 라벨, 8개 split의 OOD invariant, deterministic seeding.
4. **P0 blocker 없음**. 학습 진입 차단 사항 없음.
5. **2개의 boundary issue (P1, P2)는 학습 단계에서 해결 가능**: (a) train family filter 부재 → ENV_FIX Issue 2; (b) random_biased + 짧은 episode의 task room sparsity → ENV_FIX Issue 3.

자세한 판정 근거는 `docs/ENV_AUDIT_REPORT.md` §1, §7 참조.

---

## 3. 월드모델 학습 단계로 넘길 입력물

### 3.1 핵심 자산

| 자산 | 위치 | 의미 |
|---|---|---|
| **Smoke dataset (sanity check 용)** | `data/smoke/` | 190 episodes (8 splits). 학습용 full dataset 생성 전 환경 + generator + validator + inspector + stats가 end-to-end로 정상 작동함의 evidence. |
| **Validation evidence** | `data/smoke/validation_report.json` (Session 5) + `data/smoke/validation_report_session6.json` (Session 6 재검증) | strict invariant PASS=2242 / FAIL=0 |
| **Generator** | `scripts/generate_dataset.py` | yaml + CLI 받아 8개 split 생성. 학습용 full dataset도 동일 generator로 생성. |
| **Validator** | `scripts/validate_dataset.py` | 학습용 full dataset 생성 후 동일 명령으로 검증. |
| **Inspector** | `scripts/inspect_episode.py` | 학습 디버깅 시 episode 단위 시각화. |
| **Stats** | `scripts/plot_dataset_stats.py` | distribution / sanity check. |
| **Default config** | `configs/dataset_default.yaml` | 모든 environment / split policy / generation 수치의 single source of truth. |
| **환경 코드** | `falsifiable_regime_world_model/rg4f/{__init__,types,config,map_generator,observation,fields,tasks,env,serialization,dataset_io}.py` | reset/step/info contract + episode I/O. 학습 페이즈에서 그대로 import + 재사용. |

### 3.2 인계 문서

| 문서 | 위치 | 사용 시점 |
|---|---|---|
| `ref/PART0_IMPLEMENTATION_STRATEGY.md` | ref/ | 모든 WM Session에서 첫 번째로 읽어야 함 |
| `ref/PART1_PROBLEM_FRAMING.md` | ref/ | hidden ontology 정의 |
| `ref/PART2_ALGORITHM.md` | ref/ | falsification + action relevance + reallocation 정의 |
| `ref/PART3_EXPERIMENT_DESIGN.md` | ref/ | 실험 설계 (ablation, OOD split, metric) 정의 |
| `docs/RG4F_Environment_Plan.md` | docs/ | 환경 single source of truth |
| `docs/SESSION1~5_HANDOFF.md` | docs/ | 각 세션 산출물의 인계 evidence |
| `docs/SMOKE_REPORT.md` | docs/ | Session 5 smoke 검증 결과 |
| `docs/ENV_AUDIT_REPORT.md` | docs/ | 본 세션의 정합성 감사 (반드시 WM Session 1 시작 시 읽기) |
| `docs/ENV_FIX_INSTRUCTIONS.md` | docs/ | P1/P2 수정 후보의 timing/근거 (학습 페이즈 진행 중 참조) |
| `docs/RG4F_EXECUTION_GUIDE.md` | docs/ | 학습용 full dataset 생성 명령 + troubleshooting |
| `docs/SESSION6_HANDOFF.md` | docs/ | 본 문서 |

### 3.3 환경 코드 외부 노출 API (변경 금지)

```python
from falsifiable_regime_world_model.rg4f import (
    Action, RG4FConfig, RG4FEnv, StateDim,
    # types: ControlMode, MobilityMode, FieldFamily, TaskID, RoomID, EventToken, ...
)
from falsifiable_regime_world_model.rg4f.serialization import EpisodeBuffer
from falsifiable_regime_world_model.rg4f.dataset_io import (
    EpisodeBundle, IndexEntry, iter_episodes, load_index, load_manifest,
    EXPECTED_SPLITS, NUM_ACTIONS, NUM_LOCAL_CHANNELS, OBS_SCALAR_DIM, STATE_DIM,
)
```

월드모델 학습 페이즈는 위 API만 import해야 한다 (PART0 §10 책임 경계).

---

## 4. 월드모델 학습 전 반드시 확인할 것

### 4.1 학습 시작 직전 체크리스트

| 항목 | 확인 명령 | 정상 |
|---|---|---|
| **학습용 full dataset 생성 여부** | `Test-Path data\rg4f\manifest.json` | True (생성 후) |
| **Validation strict PASS** | `python scripts\validate_dataset.py --root data\rg4f --strict --max-episodes-per-split 100` | exit code 0, FAIL=0 |
| **State / regime / change-point labels 존재** | `python -c "import numpy as np; d = np.load('data/rg4f/train/episodes/train_000000.npz'); print(list(d.keys())[:30])"` | `true_state`, `true_regime_control_mode/mobility_mode/miscontrol_p/periodic_slip`, `change_point`, `reveal_event`, `shift_event`, `reveal_or_shift` 모두 존재 |
| **npz schema (필수 key)** | `python scripts\validate_dataset.py --root data\rg4f --max-episodes-per-split 5 --verbose` | `npz.required_keys_present` PASS |
| **train ↔ OOD split disjoint** | `python -c "import json; m = json.load(open('data/rg4f/manifest.json', encoding='utf-8')); print('disjoint=', m['ood_room_perm_disjoint_from_train'], 'train=', len(m['train_pool']), 'ood=', len(m['ood_pool']))"` | `disjoint=True train=12 ood=12` |
| **local_obs_size 일관** | `python -c "import json; m = json.load(open('data/rg4f/manifest.json', encoding='utf-8')); print(m['rg4f_config']['local_obs_size'])"` | 5 |
| **config 값** | `Get-Content configs\dataset_default.yaml \| Select-String "local_obs_size:"` | `local_obs_size: 5` |

### 4.2 dataset 통계가 합리적인지 확인

```powershell
python scripts\plot_dataset_stats.py --root data\rg4f --out outputs\rg4f_stats --max-episodes-per-split 200
Get-Content outputs\rg4f_stats\summary.csv
```

기대 분포 (full dataset 기준):

| 항목 | 기대 |
|---|---|
| `len_mean` | ~600 (truncated 또는 task complete) |
| `completed_max_mean` | > 0 (random_biased로도 일부 episode가 task progress) |
| `change_point_mean` | split별 1.0 ~ 5.0 수준 (smoke의 0.05~0.45보다 두꺼움) |
| `reveal_mean` | split별 5.0 ~ 30.0 수준 (task interaction 발생 빈도 높아짐) |
| `task_id` 분포 | 0/1/2/3 모두 등장 (random_biased + 600-step) |
| `action_state_adjust%` | ≈ 30% |

---

## 5. 다음 페이즈 권장 세션 (월드모델 학습 6세션)

월드모델 학습 페이즈는 6세션으로 분할 권장. 각 세션은 단독 실행 가능하도록 인계 문서 작성.

### WM Session 1: RSSM/GRU-lite Architecture Plan

- **목적**: 메인 backbone (RSSM-lite 또는 GRU-lite) 결정 + latent 차원 / head 구조 / hyperparameter 통제 변수 / training schedule 고정.
- **입력**: PART0~3, RG4F_Environment_Plan, ENV_AUDIT_REPORT, ENV_FIX_INSTRUCTIONS, RG4F_EXECUTION_GUIDE.
- **생성**: `docs/WM_SESSION1_HANDOFF.md`, `docs/WM_BACKBONE_PLAN.md` (architecture/capacity/training schedule 단일 source of truth).
- **금지**: 코드 작성 0줄. 학습 0회.

### WM Session 2: Dataset Loader + Model Code

- **목적**: `data/rg4f` 디렉토리에서 npz를 random-access로 로드하는 PyTorch dataset + RSSM/GRU-lite forward pass + 5 head (state / regime / change-point / observation reconstruction / value).
- **입력**: WM_BACKBONE_PLAN + Session 6 인계 자산.
- **생성**: `falsifiable_regime_world_model/wm/{__init__,dataset.py,model.py,heads.py}` + `docs/WM_SESSION2_HANDOFF.md`.
- **금지**: 학습 loop 미구현. forward pass + dummy loss 검증까지만.

### WM Session 3: Training Loop + Checkpoint/Logging

- **목적**: optimizer, loss 가중치, gradient clipping, checkpoint, tensorboard/wandb logging, deterministic seeding.
- **입력**: WM Session 2 산출물.
- **생성**: `scripts/train_world_model.py` + `configs/wm_default.yaml` + `docs/WM_SESSION3_HANDOFF.md`.
- **금지**: planner / agent 미구현. 학습은 single-GPU smoke (예: 100 step) 검증까지만.

### WM Session 4: World Model Evaluation

- **목적**: trained model의 reconstruction loss / regime accuracy / change-point F1 / state RMSE / next-step prediction을 8개 split에서 측정.
- **입력**: WM Session 3 산출물 + checkpoint.
- **생성**: `scripts/evaluate_world_model.py` + `docs/WM_EVAL_REPORT.md` + `docs/WM_SESSION4_HANDOFF.md`.

### WM Session 5: Rollout Fidelity / Regime / Change-point Diagnostics

- **목적**: imagined trajectory의 state divergence / regime switch detection latency / falsification score baseline 측정.
- **입력**: WM Session 4 metric.
- **생성**: `scripts/diagnose_rollout.py` + `docs/WM_DIAGNOSTICS_REPORT.md`.

### WM Session 6: Planner / FRC-WM 연결 준비

- **목적**: trained world model 위에 planner head / falsification module / compute reallocator를 얹는 인터페이스 정의 (코드 작성 X, 인터페이스 명세만).
- **생성**: `docs/PLANNER_INTERFACE_PLAN.md` + `docs/WM_SESSION6_HANDOFF.md`.

이후 별도 페이즈에서 planner 본격 구현 + 본 실험 + 논문 작성.

---

## 6. 다음 페이즈 금지사항

PART0 §3의 11개 금지사항이 그대로 유지된다. 추가로 본 환경 페이즈가 다음 페이즈에 강제하는 추가 금지사항:

1. **Dreamer / SOTA backbone을 메인으로 두지 말 것.** 메인 실험은 RSSM/GRU-lite controlled backbone에서만. SOTA는 transferability 보조 실험에서만.
2. **planner / agent 코드를 world model 진단 전에 붙이지 말 것.** WM Session 4 (evaluation) + WM Session 5 (diagnostics)에서 model 자체의 fidelity가 충족되어야 planner 연결 의미 있음.
3. **환경 / dataset / serialization API 변경 금지.** Session 1~6에서 결정된 contract 그대로 유지. 변경이 필요하면 RG4F_Environment_Plan.md를 먼저 갱신한 뒤 환경 코드 + 모든 dataset 재생성.
4. **본 6세션에서 smoke dataset이 이미 있으므로, 학습용 full dataset 생성 외에는 dataset 재생성 금지.** P1/P2 수정 적용 시에만 재생성.
5. **모든 수치는 yaml로만 흘러야 한다 (PART0 §3 §4).** 학습 페이즈에서도 magic number 코드에 박지 말 것. `configs/wm_default.yaml`을 single source of truth로 유지.
6. **휴리스틱 / 키워드 분기 금지 (PART0 §3 §7).** 예: "task_id 문자열로 분기", "magic threshold로 change-point 라벨 부여" 등은 안티패턴.
7. **reveal과 shift를 한 라벨로 합치는 것 금지.** world model에서도 두 head 분리 유지.

---

## 7. 본 문서가 다음 페이즈에 던지는 단 한 줄 요약

> **환경 + dataset 페이즈는 reviewer 시각으로 봐도 학습 진입 가능 상태로 닫혔다.
> 다음 페이즈는 RSSM/GRU-lite controlled backbone 위에 5 head world model을
> 학습/평가/진단하는 6세션이다. SOTA backbone과 planner는 그 다음 페이즈에서.**

---

## 8. Self-Audit (본 세션 내부 검증)

| Check | Status | Evidence |
|---|---|---|
| Session 1~5 산출물을 모두 읽었는가 | PASS | PART0/PART1/PART2/PART3/RG4F_Environment_Plan/SESSION1~5_HANDOFF/SMOKE_REPORT 모두 Read 도구로 정독. rg4f/{types,config,env,fields,serialization}.py + scripts/{generate_dataset,validate_dataset,inspect_episode,plot_dataset_stats}.py + dataset_default.yaml 모두 정독. |
| PART0~3 설계 대비 구현 정합성을 감사했는가 | PASS | ENV_AUDIT_REPORT.md §2 (정합성 표 25개 항목) + §3 (Core Mechanism Support Audit 6개 영역) + §4 (OOD Validity Audit 5개 split) + §5 (Data Collection Policy Audit) + §6 (Known Limitations Reassessment 6개). |
| 기존 ref/PART0~3와 requirements.txt를 수정하지 않았는가 | PASS | git status 확인 (변경 0줄). |
| world model / planner / agent 코드를 만들지 않았는가 | PASS | `falsifiable_regime_world_model/wm/` 디렉토리 부재. `scripts/train_*.py` 부재. torch import 0회. |
| ENV_AUDIT_REPORT.md를 작성했는가 | PASS | `docs/ENV_AUDIT_REPORT.md` 생성. 8개 섹션 (Executive Summary / 정합성 표 / Core Mechanism Support / OOD Validity / Data Collection / Known Limitations / Final Verdict / Re-validation Evidence). |
| ENV_FIX_INSTRUCTIONS.md를 작성했는가 | PASS | `docs/ENV_FIX_INSTRUCTIONS.md` 생성. Fix Priority Table + 5개 후보 이슈 각각 (Issue 1 control_mode mid-episode / Issue 2 train family filter / Issue 3 task room sparsity / Issue 4 channel permutation / Issue 5 schema 충분성) + Minimal Patch Plan. |
| RG4F_EXECUTION_GUIDE.md를 작성했는가 | PASS | `docs/RG4F_EXECUTION_GUIDE.md` 생성. 가상환경 / smoke 재생성 / strict validation / determinism / inspect / stats / 옵션 표 / full dataset 권장 / troubleshooting 9개 섹션. |
| SESSION6_HANDOFF.md를 작성했는가 | PASS | 본 문서. |
| local_obs_size=5 main setting을 재확인했는가 | PASS | yaml `local_obs_size: 5`. RG4FConfig.local_obs_size: int = 5. manifest `rg4f_config.local_obs_size=5`. inspect 시 npz `(200, 5, 5, 10)` 확인. |
| OOD 5종 invariant를 재확인했는가 | PASS | validate strict의 `split_specific.{room_perm,factor_recomb,param_shift,obs_shift,field_placement}` 모든 invariant PASS. ENV_AUDIT_REPORT §4의 OOD Validity Audit 표. |
| change_point/reveal_or_shift 정의 한계를 평가했는가 | PASS | ENV_AUDIT_REPORT §3.3 (Change-point support: control_mode mid-episode 누락 분류 = P2 Defer) + §3.4 (Reveal vs Shift support: 분리 라벨 PASS). ENV_FIX_INSTRUCTIONS Issue 1. |
| train family filter 부재를 평가했는가 | PASS | ENV_AUDIT_REPORT §4 (ood_factor_recomb 표) + §6 (Known Limitations 표) + ENV_FIX_INSTRUCTIONS Issue 2 = P1. |
| random_biased task-room sparsity를 평가했는가 | PASS | ENV_AUDIT_REPORT §5 (Data Collection Policy Audit) + ENV_FIX_INSTRUCTIONS Issue 3 = P1. |
| 실행 가이드에 실제 PowerShell 명령을 포함했는가 | PASS | RG4F_EXECUTION_GUIDE의 모든 명령이 PowerShell + `python` (활성화된 .venv) + 실제 경로. §10.1 한 줄 reference도 포함. |
| 옵션 조절 위치와 의미를 설명했는가 | PASS | RG4F_EXECUTION_GUIDE §7 (옵션 표 18개 항목) + §7.2 (핵심 명시 5건). |
| full dataset 권장 시작값을 제안했는가 | PASS | RG4F_EXECUTION_GUIDE §8 (권장 config 표 11개 항목 + 명령 예시 + 후속 검증 명령). |
| Session 6 최종 판정을 PASS/CONDITIONAL PASS/FAIL로 내렸는가 | PASS | ENV_AUDIT_REPORT §1 / §7 + 본 SESSION6_HANDOFF §2: **CONDITIONAL PASS**. |
| 다음 world model 학습 페이즈 handoff를 작성했는가 | PASS | 본 문서 §3 (인계 자산) + §4 (학습 전 체크리스트) + §5 (WM Session 1~6 권장 분할) + §6 (다음 페이즈 금지사항). |

전체 항목 PASS. Session 6 의무사항 모두 충족.
