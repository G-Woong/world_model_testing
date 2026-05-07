# P1 FIX REPORT — `train_apply_family_filter` 적용 + Full Dataset 생성 계획

> 본 문서는 ENV_FIX_INSTRUCTIONS.md의 **Issue 2 (P1)** "train family filter 부재"를
> 코드 수준에서 해결하고, smoke 검증을 거친 뒤 학습용 full dataset 생성 계획을 산출한
> 결과를 기록한다. full dataset 실제 생성은 본 작업의 범위가 아니며, 사용자가
> 명시적으로 실행할 명령만 제공한다.

---

## 1. 수정 파일 목록

| 경로 | 수정 종류 | 변경 라인 수 |
|---|---|---|
| `configs/dataset_default.yaml` | 옵션 추가 | +5 |
| `scripts/generate_dataset.py` | 정책 적용 + manifest 기록 + regime sync | +27 |
| `scripts/_p1_check_family_disjoint.py` | 신규 (검증 보조) | +112 |
| `docs/P1_TRAIN_FAMILY_FILTER_FIX_REPORT.md` | 신규 (본 문서) | — |

수정 대상이 아닌 파일 (변경 0줄):
- `ref/PART0~3`, `requirements.txt`, `falsifiable_regime_world_model/rg4f/{types,config,env,fields,observation,tasks,map_generator,serialization,dataset_io}.py`, `scripts/{validate_dataset,inspect_episode,plot_dataset_stats}.py`, `docs/{ENV_AUDIT_REPORT,ENV_FIX_INSTRUCTIONS,RG4F_EXECUTION_GUIDE,SESSION6_HANDOFF,SMOKE_REPORT,RG4F_Environment_Plan,SESSION1~5_HANDOFF}.md`.

---

## 2. 수정 전 문제 (코드 기준 정량 evidence)

### 2.1 yaml 상태

```yaml
split_policy:
  factor_recomb:
    enabled: true
    train_field_families: [0, 1]    # 라벨만 존재 (메타데이터)
    ood_field_families: [2, 3]       # 라벨만 존재
    # train_apply_family_filter 옵션 없음  ← P1 문제
```

### 2.2 generator 동작 (수정 전)

`scripts/generate_dataset.py._build_split_plans` L405-416:
```python
if s in ("train", "valid", "test_id"):
    plans.append(SplitPlan(
        ...,
        field_family_pool=None,   # train도 모든 family 허용
        ...,
    ))
```
즉 train/valid/test_id에는 family filter가 적용되지 않았고, ood_factor_recomb (L429-440)에만 `field_family_pool=ood_families` 적용.

### 2.3 정량 evidence (SMOKE_REPORT §4.7)

수정 전 smoke의 invisible field family 분포:

| split | family 0 (VIS) | family 1 (FRIC) | family 2 (INT_INTF) | family 3 (CTRL_INTF) | 검증 |
|---|---|---|---|---|---|
| train | 16 | 23 | **17** | **18** | train ⊃ ood_pool {2,3} → 안티 disjoint |
| ood_factor_recomb | 0 | 0 | 10 | 15 | strict subset {2,3} 정상 |

→ "ood_factor_recomb는 train에서 못 본 조합"이라는 주장이 약해짐. reviewer 친화적이지 않음.

---

## 3. 수정 내용

### 3.1 `configs/dataset_default.yaml`

```yaml
split_policy:
  factor_recomb:
    enabled: true
    train_field_families: [0, 1]
    ood_field_families: [2, 3]
    # P1 (Session 6 ENV_FIX_INSTRUCTIONS Issue 2): true이면 train/valid/test_id에도
    # train_field_families를 강제 적용 → ood_factor_recomb가 train과 strict disjoint.
    # false이면 기존 동작 유지 (train은 4 family 자유 노출, ood만 [2,3] 강제).
    train_apply_family_filter: true
```

### 3.2 `scripts/generate_dataset.py._build_split_plans`

```python
train_apply_family_filter = bool(factor_policy.get("train_apply_family_filter", False))
train_filter_pool: Optional[List[int]] = train_families if train_apply_family_filter else None
...
if s in ("train", "valid", "test_id"):
    plans.append(SplitPlan(
        ...,
        # P1: train_apply_family_filter=true면 train_filter_pool을 적용,
        # false면 None (기존 동작: 4 family 자유 노출).
        field_family_pool=train_filter_pool,
        ...,
    ))
```

### 3.3 `scripts/generate_dataset.py._run_one_episode` (regime sync)

family filter 후 `RegimeState.active_field_families`도 동기화하여 episode_meta의 `initial_regime`이 실제 사용된 family pool과 일관되도록 보정.

### 3.4 manifest 보강

`manifest.json`에 `factor_recomb_policy` 블록 추가 (full dataset 재현/감사용):

```json
"factor_recomb_policy": {
  "train_field_families": [0, 1],
  "ood_field_families": [2, 3],
  "train_apply_family_filter": true,
  "disjoint": true
}
```

### 3.5 backward compatibility

- yaml 기본값 = `train_apply_family_filter: true` (P1 적용 상태). false로 되돌리면 기존 동작 그대로.
- npz schema **변경 없음** — 모든 array key/shape/dtype 동일.
- env.reset/step API **변경 없음**.
- `RG4FConfig` dataclass field **변경 없음**.
- `RegimeState.active_field_families`만 generator에서 filter 후 갱신 (RGFEnv 내부엔 영향 없음, episode_meta의 initial_regime만 정확해짐).

---

## 4. smoke_p1_filtered 생성 명령

```powershell
python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\smoke_p1_filtered --num-train 50 --num-valid 20 --num-test 20 --num-ood-per-type 20 --max-steps 200 --overwrite
```

소요시간: **6.60초** (190 episodes × 200 steps).

생성 결과:
- `data/smoke_p1_filtered/manifest.json` (factor_recomb_policy 블록 포함)
- `data/smoke_p1_filtered/<8 splits>/index.jsonl` + `episodes/*.npz` + `episodes/*.meta.json`
- `data/smoke_p1_filtered/validation_report.json`

---

## 5. Validation 결과

### 5.1 strict validation

```powershell
python scripts\validate_dataset.py --root data\smoke_p1_filtered --strict --max-episodes-per-split 50 --json-report data\smoke_p1_filtered\validation_report.json
```

| 항목 | 값 |
|---|---|
| **PASS** | 2242 |
| **WARN** | 0 |
| **FAIL** | 0 |
| exit code | 0 |
| json report | `data\smoke_p1_filtered\validation_report.json` |

→ 기존 invariant (directory / npz schema / shape / numeric / sparse_coupling / split_specific) 모두 유지됨을 확인.

### 5.2 determinism check

```powershell
python scripts\validate_dataset.py --root data\smoke_p1_filtered --check-determinism --config configs\dataset_default.yaml --max-episodes-per-split 3
```

| 항목 | 값 |
|---|---|
| **PASS** | 332 |
| **WARN** | 0 |
| **FAIL** | 0 |
| exit code | 0 |
| 두 번 호출 결과 | 모든 split의 모든 npz가 byte-equal |

→ 동일 yaml + 동일 seed → byte-equal 재현 보장.

---

## 6. Observed Field Family Disjoint Table

Episode meta의 `field_info_static[*].family`를 split별로 집계:

| split | allowed pool | observed pool | counts (50 episodes 기준) | PASS/FAIL |
|---|---|---|---|---|
| train | {0, 1} | **{0, 1}** | VISIBILITY=27, FRICTION=33 | **PASS** |
| valid | {0, 1} | **{0, 1}** | VISIBILITY=12, FRICTION=10 | **PASS** |
| test_id | {0, 1} | **{0, 1}** | VISIBILITY=13, FRICTION=11 | **PASS** |
| ood_room_perm | {0, 1, 2, 3} | {0, 1, 2, 3} | VIS=5, FRIC=14, INT_INTF=8, CTRL_INTF=3 | **PASS** |
| **ood_factor_recomb** | {2, 3} | **{2, 3}** | INT_INTF=10, CTRL_INTF=15 | **PASS** |
| ood_param_shift | {0, 1, 2, 3} | {0, 1, 2, 3} | VIS=7, FRIC=8, INT_INTF=7, CTRL_INTF=3 | **PASS** |
| ood_obs_shift | {0, 1, 2, 3} | {0, 1, 2, 3} | VIS=6, FRIC=7, INT_INTF=7, CTRL_INTF=14 | **PASS** |
| ood_field_placement | {0, 1, 2, 3} | {0, 1, 2, 3} | VIS=10, FRIC=7, INT_INTF=3, CTRL_INTF=11 | **PASS** |
| **OVERALL** | — | — | — | **PASS** |

### 6.1 핵심 disjoint 결과

- **train ∩ ood_factor_recomb = ∅** → strict disjoint 달성.
- train/valid/test_id 모두 동일 분포 ({0, 1}만) → 학습-검증-테스트 3종이 in-distribution 관계.
- 다른 OOD splits (room_perm, param_shift, obs_shift, field_placement)는 family를 강제하지 않으므로 4 family 자유 등장 — 기존 invariant 유지.

검증 명령 (재현 가능):
```powershell
python scripts\_p1_check_family_disjoint.py data\smoke_p1_filtered
```

---

## 7. 기존 OOD Invariant 유지 여부

| invariant | 유지? | evidence |
|---|---|---|
| `ood_room_perm`은 train permutation과 disjoint | YES | manifest `train_pool` (12) ∩ `ood_pool` (12) = ∅. validate `split_specific.room_perm.disjoint_from_train` PASS (50 episodes). |
| `ood_param_shift` drift/shift/radius multiplier 적용 | YES | meta `rg4f_kwargs_override`: `field_mu_drift_sigma=0.02 (×2)`, `shift_prob_per_*=0.10 (×2)`, `field_radius_max=12.0 (×2)`. validate `split_specific.param_shift.differs_from_train` PASS. |
| `ood_obs_shift` channel_perm 유지 | YES | meta `obs_channel_perm` 길이 10 permutation. validate `split_specific.obs_shift.channel_perm_valid` + `no_dynamics_change` PASS. |
| `ood_field_placement` relocate flag 유지 | YES | meta `relocate_fields_room_center=true`. validate `split_specific.field_placement.relocate_flag` + `source_in_grid` PASS. |
| sparse coupling `|coupled_states| ≤ 2` | YES | validate `sparse_coupling.le2` 모든 episode PASS (190 episodes). 수정 후 변화 없음. |
| determinism (byte-equal 재현) | YES | `--check-determinism` PASS=332 / FAIL=0. |

→ P1 수정으로 기존 OOD 5종의 invariant가 깨지지 않았음을 정량적으로 확인.

---

## 8. Full Dataset 생성 계획표

> **현재 `data/smoke` 또는 `data/smoke_p1_filtered`는 검증용 smoke dataset이며,
> 학습용 full dataset은 별도로 생성해야 한다.**
>
> **데이터 단위는 단순 월드맵 1개가 아니라 episode 1개다.** episode 1개는 월드맵
> 배치, room-task permutation, invisible field 배치, target band, drift/shift 발생,
> agent 행동 trajectory가 결합된 하나의 transition sequence다.

### 8.1 split별 생성량

| 범주 | 목적 | 생성량 |
|---|---|---:|
| `train` | 모델 학습용 기본 분포 | **5,000 episodes** |
| `valid` | 학습 중 checkpoint / model selection | **500 episodes** |
| `test_id` | train과 같은 분포의 최종 평가 | **500 episodes** |
| `ood_room_perm` | 방-task 위치 조합 OOD | **500 episodes** |
| `ood_factor_recomb` | field coupling 조합 OOD | **500 episodes** |
| `ood_param_shift` | drift / shift 강도 변화 OOD | **500 episodes** |
| `ood_obs_shift` | 관측 encoding 변화 OOD | **500 episodes** |
| `ood_field_placement` | invisible field 위치 prior 변화 OOD | **500 episodes** |

### 8.2 총량 계산

```
총 episodes = 5,000 + 500 + 500 + (5 × 500)
            = 5,000 + 500 + 500 + 2,500
            = 8,500 episodes
```

```
max transitions = 8,500 × 600 (episode_max_steps)
                = 5,100,000 transitions
```

→ episode 1개당 평균 ~600 step (random_biased가 task 4개 모두 완료 못 하면 truncated). 실제 transition 수는 5.1M보다 약간 적을 수 있음 (early termination 시).

### 8.3 디스크 용량 추정

| 항목 | smoke_p1_filtered (190 eps × 200 steps) | full (8500 eps × 600 steps) |
|---|---|---|
| episode 1개 npz | ~18 KB | ~55 KB |
| episode 1개 meta.json | ~60 KB (debug_trace 포함) | ~180 KB |
| 8500 episodes total | — | **약 2~3 GB** (compressed npz) |

---

## 9. Split별 Random / Fixed / 변화 설명

### 9.1 모든 split에서 fixed인 것

- 중앙홀 (9×9) + 4방 (8×8) + 복도 (length=3) cross 토폴로지
- `hall_size=9`, `room_size=8`, `corridor_length=3`
- `local_obs_size=5` (메인 세팅)
- 5개 상태값 `(v, m, i, n, d) ∈ [-1, 1]^5`
- Task A/B/C/D 4종의 정의 (weight-order / vision-positive / noise-zero / tile-drift)
- sparse coupling 원칙 `|coupled_states| ≤ 2`
- 저장 형식 npz + meta.json + index.jsonl + manifest.json
- behavior_policy = random_biased (movement 55% / E 15% / state-adjust 30% / WAIT 0%)
- `episode_max_steps=600` (full)

### 9.2 모든 split에서 random인 것

- episode seed (master_seed에서 deterministic하게 파생, 단 episode 단위 다른 값)
- room-task permutation (split-aware pool에서 sampling)
- invisible field source 위치 (free placement)
- field radius / mean / sigma (config range 안에서 sampling)
- target band 값 (`τ_i` 등)
- task별 parameter (Task A piece weight 순서, Task B 어느 stele가 vision-positive 등)
- agent action trajectory (random_biased로 sampling)
- small drift sample (매 step마다 `N(0, σ_η)` 발생)
- event-triggered shift 발생 여부 (확률 적용)
- stochastic miscontrol 발생 여부 (`p_slip` 확률)
- periodic slip 활성 (step 0, 4, 8, ...에서 `p_high=0.30`)

### 9.3 split별 변화

#### `train`
- **fixed**: `field_family_pool=[0, 1]` (P1 적용). `is_ood=False`. `rg4f_kwargs_override={}`. permutation pool은 `train_pool` (24개 중 12개).
- **random**: 9.2 항목 모두 + `train_pool` 안에서 permutation sampling.
- **변화/목적**: 모델이 sufficient capacity로 학습 가능한지 검증하는 reference distribution.

#### `valid`
- **fixed**: train과 동일 (family `[0, 1]`, train_pool, override 없음).
- **random**: 9.2 항목 + train_pool 안에서 permutation. 단 episode seed가 train과 disjoint (split rng 다름).
- **변화/목적**: 학습 중 checkpoint 선택 + hyperparameter tuning.

#### `test_id`
- **fixed**: train/valid와 동일 분포.
- **random**: 9.2 항목 + train_pool 안에서 permutation. episode seed가 train/valid와 disjoint.
- **변화/목적**: in-distribution 일반화 성능 (train/valid와 동일 분포에서 새 seed).

#### `ood_room_perm`
- **fixed**: `field_family_pool=None` (4 family 자유). override 없음.
- **random**: 9.2 항목 + permutation sampling.
- **train과 다른 점**: permutation pool이 `ood_pool` (24-12=12개). `train_pool ∩ ood_pool = ∅`. 즉 episode마다 강제되는 forced_permutation이 train에서 한 번도 등장 안 한 4-tuple.
- **검증 목적**: agent가 "북쪽 방 = Task A" 같은 위치 암기를 했는지, 아니면 task rule을 이해했는지 분리 검증.

#### `ood_factor_recomb`
- **fixed**: `field_family_pool=[2, 3]` (strict). permutation은 `train_pool`. override 없음.
- **random**: 9.2 항목 + train_pool에서 permutation sampling.
- **train과 다른 점**: invisible field family가 train ({0, 1})과 strict disjoint한 {2, 3}만 등장. INTERACTION_INTERFERENCE 또는 CONTROL_INTERFERENCE만.
- **검증 목적**: factorized regime model의 일반화. monolithic regime 모델은 train family overlap이 사라지므로 약해야 함.

#### `ood_param_shift`
- **fixed**: `field_family_pool=None`. permutation은 `train_pool`. **override 적용**: `field_mu_drift_sigma×2.0`, `shift_prob_per_*×2.0`, `field_radius_max×2.0`.
- **random**: 9.2 항목.
- **train과 다른 점**: 같은 dynamics family이지만 drift / shift / field 영향 반경이 train range의 2배.
- **검증 목적**: scale/intensity가 바뀌어도 robust한가.

#### `ood_obs_shift`
- **fixed**: `field_family_pool=None`. permutation은 `train_pool`. **`obs_channel_perm` 적용** (length 10 permutation). 동역학 변경 없음.
- **random**: 9.2 항목.
- **train과 다른 점**: obs `local_grid`의 channel 순서가 train과 다름 (예: cue 채널이 다른 index에). 근본 dynamics는 동일.
- **검증 목적**: novelty detector의 false positive 검증. 진짜 regime shift가 아닌데도 novelty 신호가 발생하는가.

#### `ood_field_placement`
- **fixed**: `field_family_pool=None`. permutation은 `train_pool`. **`relocate_fields_room_center=true`**. 동역학 변경 없음.
- **random**: 9.2 항목 + 4방 중심 ± 8-neighborhood traversable cell 중에서 source 위치 random sampling.
- **train과 다른 점**: invisible field source의 spatial prior가 train (grid 전역 random) 대비 4방 중심에 집중.
- **검증 목적**: hidden field에 대한 belief의 spatial generalization.

---

## 10. 사용자가 실행해야 할 최종 명령

> **본 작업의 범위는 P1 수정 + smoke 검증 + 계획 산출까지다. Full dataset 생성은
> 사용자가 명시적으로 결정한 시점에 직접 실행한다.**

### 10.1 Full dataset 생성

```powershell
python scripts\generate_dataset.py --config configs\dataset_default.yaml --output-root data\rg4f --num-train 5000 --num-valid 500 --num-test 500 --num-ood-per-type 500 --max-steps 600 --overwrite
```

예상 소요시간: 60~150분 (CPU 단일 프로세스 기준 추정. smoke 6.60초 / 190 ep × 200 step = step당 ~0.17ms 기준 단순 환산 시 8,500 ep × 600 step ≈ 14분이지만 episode_max_steps 증가에 따른 비선형 효과 / disk IO를 고려하면 60분 이상 소요 가능).

### 10.2 생성 후 검증 명령

```powershell
# 1. strict validation
python scripts\validate_dataset.py --root data\rg4f --strict --max-episodes-per-split 100 --json-report data\rg4f\validation_report.json

# 2. determinism check (선택)
python scripts\validate_dataset.py --root data\rg4f --check-determinism --config configs\dataset_default.yaml --max-episodes-per-split 3

# 3. 통계
python scripts\plot_dataset_stats.py --root data\rg4f --out outputs\rg4f_stats --max-episodes-per-split 500

# 4. P1 family disjoint 재확인
python scripts\_p1_check_family_disjoint.py data\rg4f

# 5. inspect (각 split 1개 episode)
python scripts\inspect_episode.py --root data\rg4f --split train --index 0 --num-steps 5 --show-grid --show-scalar --show-info
python scripts\inspect_episode.py --root data\rg4f --split ood_factor_recomb --index 0 --num-steps 5 --show-grid --show-task --show-fields
```

### 10.3 정상 기준 (full dataset 검증 시)

| 항목 | 정상 |
|---|---|
| strict validation | PASS, FAIL=0, WARN=0, exit 0 |
| `data\rg4f\manifest.json`의 `factor_recomb_policy.disjoint` | `true` |
| family disjoint 검증 (`_p1_check_family_disjoint.py`) | OVERALL PASS |
| determinism | PASS, FAIL=0 |
| `outputs\rg4f_stats\summary.csv`의 `task_id` 분포 | task=0/1/2/3 모두 등장 (600-step + random_biased로 task room 진입 통계 충분) |
| `change_point_mean` | split별 1.0 ~ 5.0 수준 (smoke의 0.05~0.45보다 두꺼움) |
| 디스크 용량 | `data\rg4f` 약 2~3 GB |

---

## 11. 최종 판정

### **PASS — train family filter 적용 완료, 학습용 full dataset 생성 준비 완료.**

근거 요약:

1. P1 수정의 핵심 목적인 **`train ∩ ood_factor_recomb = ∅` (strict disjoint)** 달성. observed family 분포가 train={0,1}, ood_factor_recomb={2,3}으로 정확 검증.
2. strict validation **PASS=2242 / WARN=0 / FAIL=0**. 기존 8개 split의 모든 OOD invariant 유지.
3. determinism check **PASS=332**. 동일 yaml + seed → byte-equal 재현.
4. npz schema / env API / serialization API **변경 0줄**.
5. `train_apply_family_filter`가 yaml의 toggle로 노출되어, `false`로 되돌리면 기존 동작 그대로 (backward compatibility 보장).
6. manifest에 `factor_recomb_policy` 블록을 명시적으로 기록하여 dataset 감사/재현 가능성 강화.

다음 단계는 사용자가 §10.1 명령으로 학습용 full dataset (8,500 episodes)을 생성하는 것이다.

---

## 12. Self-Audit

| Check | Status | Evidence |
|---|---|---|
| ENV_AUDIT_REPORT와 ENV_FIX_INSTRUCTIONS를 읽었는가 | PASS | 두 문서 모두 Read 도구로 §1 (Issue 2 P1 분류) + §2.1 (Fix Priority Table) 정독. |
| `train_apply_family_filter` 옵션을 yaml에 추가했는가 | PASS | `configs/dataset_default.yaml` L92-99에 신규 옵션 + 주석 추가. |
| train/valid/test_id에 `train_field_families` 필터가 적용되는가 | PASS | dry-run 결과 train/valid/test_id의 `field_family_pool: [0, 1]`. observed family disjoint 표에서 train={VIS:27, FRIC:33}, valid={VIS:12, FRIC:10}, test_id={VIS:13, FRIC:11}. |
| `ood_factor_recomb`에 `ood_field_families` 필터가 적용되는가 | PASS | dry-run `field_family_pool: [2, 3]`. observed family={INT_INTF:10, CTRL_INTF:15}. |
| 기존 npz schema를 깨지 않았는가 | PASS | validate strict의 `npz.required_keys_present` + `shape.*` + `numeric.*` 모두 PASS=2242/FAIL=0. dataset_io.py / serialization.py 변경 0줄. |
| smoke_p1_filtered를 생성했는가 | PASS | `data/smoke_p1_filtered/` 8 splits × 190 episodes. wall-clock 6.60초. |
| validate strict FAIL=0인가 | PASS | PASS=2242 / WARN=0 / FAIL=0 / exit 0. `data/smoke_p1_filtered/validation_report.json`. |
| train observed field family가 {0, 1} 안에 있는가 | PASS | family disjoint 표: train, valid, test_id 모두 observed = {0, 1}. outside family = ∅. |
| ood_factor_recomb observed field family가 {2, 3} 안에 있는가 | PASS | family disjoint 표: ood_factor_recomb observed = {2, 3}. outside family = ∅. |
| 기존 OOD invariant가 유지되는가 | PASS | §7 표: ood_room_perm disjoint / param_shift override / obs_shift channel_perm / field_placement relocate / sparse_coupling 모두 PASS. determinism PASS=332. |
| full dataset 생성량 표를 출력했는가 | PASS | §8.1 표 8 splits × 생성량 명시. |
| 8,500 episodes와 5,100,000 transitions 계산을 포함했는가 | PASS | §8.2 계산 식: `5000+500+500+5×500=8500`, `8500×600=5,100,000`. |
| split별 fixed/random/변화 설명을 작성했는가 | PASS | §9 모든 8 split 각각 fixed/random/변화/목적 항목 작성. |
| 사용자가 실행할 full generation 명령을 포함했는가 | PASS | §10.1 명령 + §10.2 생성 후 검증 5단계 명령. |
| `docs/P1_TRAIN_FAMILY_FILTER_FIX_REPORT.md`를 작성했는가 | PASS | 본 문서. |

전체 항목 PASS. P1 수정 작업의 의무사항 모두 충족.
