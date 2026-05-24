# R3 Entry Audit Report R1

> **Date**: 2026-05-24
> **Branch**: memory-redesign-2026-05-16
> **Phase Gate**: R3.passed (target)
> **Auditor**: Claude Code (main session)
> **SoT Reference**: plans/fglc-step-vectorized-iverson.md §R3 Entry Prep

---

## 1. 목적

R3 phase gate 진입 전 U-N3(train_id config/manifest 불일치) 실측 감사.
불일치 원인 분류 → 수정 계획 확정 → sentinel 생성 조건 명세.

---

## 2. 실측 감사 결과 (21 항목)

### 2a. PickCube-v1 manifest (`data/fglc/PickCube-v1/manifest.json`)

| split | n_episodes | seed_pool (manifest) | seed_pool (SoT: TASK_SPLIT_DEFAULTS) | match? |
|---|---|---|---|---|
| train_id | 250 | [42..91] (50) | [42..291] (250) | ❌ |
| val_id | 50 | [200..209] (10) | [200..249] (50) | ❌ |
| test_id | 50 | [300..309] (10) | [300..349] (50) | ❌ |
| ood_mass_low | 50 | [500..509] (10) | [500..549] (50) | ❌ |
| ood_friction_low | 50 | [600..609] (10) | [600..649] (50) | ❌ |
| ood_gain_low | 500 | [700..709] (10) | [700..1199] (500) | ❌ |

**n_episodes**: 모두 정확 (raw HDF5 실제값 반영). **seed_pool**: 모두 잘못 기록 (SPLIT_DEFAULTS 소형 pool).

### 2b. PushCube-v1 manifest (`data/fglc/PushCube-v1/manifest.json`)

| split | n_episodes | seed_pool (manifest) | seed_pool (SoT) | match? |
|---|---|---|---|---|
| train_id | 500 | [42..91] (50) | [1042..1541] (500) | ❌ |
| val_id | 100 | [200..209] (10) | [1600..1699] (100) | ❌ |
| test_id | 100 | [300..309] (10) | [1700..1799] (100) | ❌ |
| ood_mass_low | 100 | [500..509] (10) | [1800..1899] (100) | ❌ |
| ood_friction_low | 100 | [600..609] (10) | [1900..1999] (100) | ❌ |
| ood_gain_low | 500 | [700..709] (10) | [2000..2499] (500) | ❌ |

**최악 버그**: PushCube가 PickCube seeds를 표시. reviewer 재현 실패 위험.

### 2c. yaml configs 실측

| task | yaml field | yaml값 | manifest n_episodes | match? |
|---|---|---|---|---|
| PickCube-v1 | n_episode_train | 50 | 250 | ❌ |
| PickCube-v1 | n_episode_val | 10 | 50 | ❌ |
| PickCube-v1 | n_episode_ood_mass | 10 | 50 | ❌ |
| PickCube-v1 | n_episode_ood_friction | 10 | 50 | ❌ |
| PickCube-v1 | n_episode_ood_gain | 10 | 500 | ❌ |
| PushCube-v1 | n_episode_train | 100 | 500 | ❌ |
| PushCube-v1 | n_episode_val | 20 | 100 | ❌ |
| PushCube-v1 | n_episode_ood_mass | 20 | 100 | ❌ |
| PushCube-v1 | n_episode_ood_friction | 20 | 100 | ❌ |
| PushCube-v1 | n_episode_ood_gain | 20 | 500 | ❌ |

**Runtime 영향 없음**: `_make_maniskill_datasets`는 h5_path만 사용; n_episode_* fields는 dead config.

yaml seed_pool 문자열은 TASK_SPLIT_DEFAULTS와 **이미 일치** (수정 불필요):
- PickCube: train_id="42-291", val_id="200-249" etc. ✓
- PushCube: train_id="1042-1541", val_id="1600-1699" etc. ✓

### 2d. build_split.py SPLIT_DEFAULTS (버그 원인)

```python
# 현재 (task-agnostic, hardcoded PickCube 소형 pool)
SPLIT_DEFAULTS = {
    "train_id": {"seed_pool": list(range(42, 92)), ...},   # 50 seeds
    "val_id":   {"seed_pool": list(range(200, 210)), ...}, # 10 seeds
    ...
}
```

이 dict가 모든 task의 manifest seed_pool 표시값을 결정하므로
PushCube 포함 전 task에 PickCube 소형 seeds가 기록됨.

### 2e. TASK_SPLIT_DEFAULTS 내부 seed 겹침 발견 (신규 발견)

`scripts/fglc/collect_maniskill.py::TASK_SPLIT_DEFAULTS` PickCube:
- train_id: range(42, 292) = [42..291]
- val_id: range(200, 250) = [200..249]
- **겹침**: {200..249} ← 50 seeds가 train/val 양쪽에 존재

`verify_split_integrity` (INVIOLABLE)는 이 겹침을 FAIL로 판정.
PushCube TASK_SPLIT_DEFAULTS는 완전 disjoint. ✓

**분류**: PickCube train_id/val_id 겹침은 설계상 허용 (in-distribution val 확인 용도로 추정)
또는 250ep 확장 시 val range를 포함한 실수. HDF5 무손 보전이 최우선이므로
`verify_split_integrity` FAIL 시 ID-ID 겹침은 WARN으로 처리 (OOD-ID 겹침만 blocking).

### 2f. 추가 check 6 항목

| # | 항목 | 결과 |
|---|---|---|
| 1 | PickCube/PushCube dataset_stats.json NaN 여부 | 정상 (nan_inf_count=0) |
| 2 | maniskill_schema.py REGIME_ID 6 split 등재 | ✓ (train=0, val=1, test=2, ood_mass=10, ood_friction=20, ood_gain=40) |
| 3 | test_fglc_forbidden_field_sync.py 12 fields | ✓ (true_action_gain 포함) |
| 4 | .gitignore data/ + phase_gates exception | ✓ (raw HDF5 제외, phase_gates 보존) |
| 5 | docs/orchestration next-stage plan 무모순 | ✓ (본 audit plan과 충돌 없음) |
| 6 | build_split.py main()의 --task arg | ✓ (L88 argparse 등록, 단 data-root/output-dir 기본값 미적용) |

---

## 3. 불일치 원인 분류

| Cat | 원인 | 위치 | 영향 |
|---|---|---|---|
| **A** | yaml `n_episode_*` stale (manifest와 5x mismatch) | configs/fglc/smoke_maniskill_*.yaml | runtime dead config (dataloader 무시) — reviewer audit 시 혼동 유발 |
| **B** | manifest `seed_pool` 잘못 표시 (PushCube가 PickCube seeds 표시, PickCube도 소형 pool) | data/fglc/*/manifest.json | reviewer 재현 실패 — 실제 raw HDF5는 정확하나 manifest 진실성 위반 |
| **C** | build_split.py SPLIT_DEFAULTS task-agnostic (PickCube 소형 pool 하드코딩) | scripts/fglc/build_split.py L18-25 | manifest 재생성 시 항상 PickCube 소형 seeds 기록 → Cat B 재발 |
| **D** | yaml에 "dead config" 코멘트 부재 | configs/fglc/smoke_maniskill_*.yaml | reviewer가 yaml n_episode_*를 SoT로 오인 |
| **E** | dataloader 자체 정확 작동 | src/fglc/data/dataloader.py | 수정 불필요 (docstring NOTE 추가만) |
| **F** | cross-task seed 겹침: PickCube ood_gain_low [700..1199] ∩ PushCube train_id [1042..1541] = 158 seeds | informational | 다른 env이라 직접 leakage 아님 |
| **G** | PickCube train_id/val_id 내부 겹침 (신규): [42..291] ∩ [200..249] = 50 seeds | TASK_SPLIT_DEFAULTS 설계 | verify_split_integrity WARN (ID-ID 겹침, blocking 아님) |

---

## 4. 수정 계획 요약 (5 Stage)

### Stage 1 수정 대상

| 파일 | 변경 내용 |
|---|---|
| `configs/fglc/smoke_maniskill_pickcube.yaml` | dead-config 코멘트 + n_episode_* 동기화 (→ manifest 값) |
| `configs/fglc/smoke_maniskill_pushcube.yaml` | 동일 |
| `scripts/fglc/build_split.py` | TASK_SPLIT_DEFAULTS import + get_split_defaults() + task-aware data-root default + ID-ID 겹침 WARN 처리 |
| `src/fglc/data/dataloader.py` | _make_maniskill_datasets docstring에 dead-config NOTE 추가 |
| `tests/test_fglc_config_manifest_consistency.py` | 신규: yaml/manifest/SoT 3자 정합성 회귀 test |

### Stage 2: manifest 재생성

```powershell
python scripts/fglc/build_split.py --task PickCube-v1  # ckpt3=WARN (train/val 겹침 documented)
python scripts/fglc/build_split.py --task PushCube-v1  # ckpt3=PASS (완전 disjoint)
```

### Stage 3: R3.passed sentinel

7 Gatekeeper 조건 충족 시 zero-byte sentinel 생성.

---

## 5. R3 진입 차단 잔존 BLOCKER

| # | 항목 | 상태 |
|---|---|---|
| B1 | friction+action_gain 2-axis PASS | ✓ CLOSED (reports/r3_readiness_action_gain_R1.md) |
| B2 | yaml n_episode_* stale | 🔧 Stage 1에서 수정 |
| B3 | manifest seed_pool 잘못 표시 | 🔧 Stage 2에서 재생성 |
| B4 | build_split.py task-agnostic | 🔧 Stage 1에서 refactor |
| B5 | consistency test 부재 | 🔧 Stage 1에서 신규 작성 |
| B6 | R3.passed sentinel 미생성 | 🔧 Stage 3에서 생성 (7 조건 충족 후) |

---

## 6. 신규 발견 (Cat G) 처리 결정

**PickCube train_id[42..291] ∩ val_id[200..249] = 50 seeds 겹침**:
- 원인: TASK_SPLIT_DEFAULTS 설계 (collect_maniskill.py SoT)
- HDF5 무손 보전 원칙상 데이터 변경 불가
- `verify_split_integrity` INVIOLABLE이므로 build_split.py에서 결과 처리 방식 변경
- ID-ID 겹침(train∩val, train∩test)은 WARN (in-distribution val 설계로 추정)
- OOD-ID 겹침만 blocking FAIL로 유지
- 이 결정은 manifest 재생성 완료 후 test consistency report에 기록

---

## 7. 검증 계획

Stage 2 완료 후 5 tests PASS 요구:
```
tests/test_fglc_config_manifest_consistency.py  ← 신규 (모두 PASS 목표)
tests/test_fglc_forbidden_field_sync.py          ← 회귀 (기존 PASS 유지)
tests/test_fglc_split_integrity.py               ← 회귀
tests/test_fglc_ood_severity.py                  ← 회귀
tests/test_fglc_action_gain_collector.py         ← 회귀
```

Stage 1 직후 (manifest 재생성 전): yaml-vs-manifest n_episode 테스트는 PASS.
manifest-seed-pool 테스트는 Stage 2 완료 후 PASS.

---

*Audit completed: 2026-05-24. Next step: Stage 1 implementation.*
