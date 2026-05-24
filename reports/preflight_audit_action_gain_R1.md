# Preflight Audit: action_gain OOD Axis — R1

**Date**: 2026-05-24
**Branch**: memory-redesign-2026-05-16
**Stage**: Stage 0 (read-only, precedes TASK_2050 Codex impl)
**Author**: Claude (main session)

---

## 6-Check Summary

| # | Check | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | collect_maniskill.py TASK_SPLIT_DEFAULTS, ood_gain_low 부재 | ood_gain_low 없음 | PickCube/PushCube 각 5개 split (train_id/val_id/test_id/ood_mass_low/ood_friction_low), ood_gain_low 미존재 | ✅ PASS |
| 2 | build_split.py SPLIT_DEFAULTS, ood_gain_low 부재 | ood_gain_low 없음 | L18-24: 5개 entries, ood_gain_low 미존재 | ✅ PASS |
| 3 | collector.py L148-149 삽입 가능 위치 확인 | a=sample() → step() 사이 빈 공간 | L148: `a = env.action_space.sample()`, L149: `obs_next, r, term, trunc, info = env.step(a)`. np import L19 존재. true_action_gain L191 존재 | ✅ PASS |
| 4 | requirements.txt mani-skill / numpy pin | mani-skill 3.0.x, numpy 2.1.3 | mani-skill==3.0.1 (L85), numpy==2.1.3 (L104) | ✅ PASS |
| 5 | data/fglc/*/raw/ 기존 HDF5 무변경 확인 | PickCube 5 + PushCube 5 HDF5, ood_gain_low 없음 | PickCube: {train_id, val_id, test_id, ood_mass_low, ood_friction_low}.h5. PushCube: 동일 5개. ood_gain_low.h5 없음 | ✅ PASS |
| 6 | outputs/phase_gates/ R0/R1/R2.passed 존재 + R3.passed 부재 | R0/R1/R2 있음, R3 없음 | R0.passed(2026-05-22), R1.passed(2026-05-23), R2.passed(2026-05-23) 존재. R3.passed 부재 | ✅ PASS |

**Overall Preflight**: ✅ 6/6 PASS — TASK_2050 위임 가능

---

## 추가 확인 사항 (Phase 1 탐색 보완)

### maniskill_schema.py 상태
- `REGIME_ID` 현재 항목: train_id=0, val_id=1, test_id=2, ood_mass_low=10, ood_friction_low=20, ood_latency=30
- ood_gain_low **미존재** → 40 추가 예정
- `TASK_OOD_PARAMS` PickCube-v1/PushCube-v1: ood_gain_low **미존재** → `{"action_gain": 0.7}` 추가 예정
- `EvalOnlyTransition.__slots__`: `true_action_gain` 이미 존재 → 변경 불필요

### collector.py 상태
- eval_metas에 `"true_action_gain": float(config.ood_params.get("action_gain", 1.0))` 이미 L191 존재 → 변경 불필요
- `np` import L19 존재 → 신규 import 불필요

### config 파일 상태
- `smoke_maniskill_pickcube.yaml`: seed_pool 블록 **없음** (U-N1 확인) → TASK_2050에서 추가
- `smoke_maniskill_pushcube.yaml`: seed_pool 블록 존재 (train_id~ood_friction_low 5개) → ood_gain_low 추가만 필요

### Seed Pool 격리 확인
| Split | PickCube seeds | PushCube seeds |
|---|---|---|
| train_id | 42-291 | 1042-1541 |
| val_id | 200-249 | 1600-1699 |
| test_id | 300-349 | 1700-1799 |
| ood_mass_low | 500-549 | 1800-1899 |
| ood_friction_low | 600-649 | 1900-1999 |
| **ood_gain_low (신규)** | **700-1199** | **2000-2499** |

PickCube: 기존 최대 seed = 649 (ood_friction_low 끝). 신규 700 시작. Disjoint ✅
PushCube: 기존 최대 seed = 1999 (ood_friction_low 끝). 신규 2000 시작. Disjoint ✅

---

## TASK_2050 파일 경로

`.agent_tasks/codex_queue/TASK_2050_ACTION_GAIN_IMPL.md` — 작성 완료

### 7개 FILES_ALLOWED
1. `src/fglc/data/collector.py`
2. `src/fglc/data/maniskill_schema.py`
3. `scripts/fglc/collect_maniskill.py`
4. `scripts/fglc/build_split.py`
5. `configs/fglc/smoke_maniskill_pickcube.yaml`
6. `configs/fglc/smoke_maniskill_pushcube.yaml`
7. `tests/test_fglc_action_gain_collector.py` (신규)

---

## 잔존 UNKNOWN (Stage 0 해결 불가)

| UNKNOWN | 상태 | 처리 |
|---|---|---|
| U-N3 (train_id manifest 250ep vs yaml 50ep) | 영향 없음 (action_gain은 신규 split만 생성) | 무시 |
| U-N4 (Ckpt 4 FAIL vs STEP11_RESULT Ckpt 4 PASS) | mass 관련 충돌, action_gain 무관 | Stage 5 report에 명시 |
| U-N8 (PickCube ID baseline action_std) | Stage 2 probe에서 산출 예정 | Stage 2 |

---

## Stage 0 결론

- 6/6 PASS → TASK_2050 위임 조건 충족
- Blocker: NONE
- 다음 단계: Stage 1 TASK_2050 구현 (직접 구현)
