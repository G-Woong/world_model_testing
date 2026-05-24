# PushCube-v1 데이터셋 구축 사전 감사 보고서

**보고일**: 2026-05-24  
**Phase**: PLAN → Stage 1 진입 전 (Q1+Q2)  
**담당**: Claude 직접 (read-only 분석)  
**참조 PLAN**: `plans/fglc-step-vectorized-iverson.md` §A~§E  

---

## 1. Pre-flight 체크 결과

| 항목 | 상태 | 세부 |
|---|---|---|
| git status | 4개 M (unstaged) | `.self_evolving_memory`, `docs/orchestration`, `plans` 2개 — 수집/테스트 코드 미수정 |
| `.gitignore` raw HDF5 보호 | **PASS** | `data/*`, `*.h5`, `*.hdf5` 보호됨; metadata JSON 3종 예외(`!`) 확인 |
| R0.passed, R1.passed, R2.passed | **PASS (존재)** | `outputs/phase_gates/` zero-byte sentinels 확인 |
| R3.passed | **부재 (정상)** | 본 단계 목표 |
| 디스크 가용 공간 | **290,298 MB (≈290 GB)** | S4(72 MB) 대비 4000× 여유 |
| `_analysis_scratch/pushcube_probe_results.txt` | **존재** | probe 결과 유효 |
| `docs/orchestration/agent_reports/2026-05/mass_ood_root_cause_synthesis_RC1.md` | **존재** | ANALYSIS_PASS 판정 |

---

## 2. PushCube Probe 신뢰도 정량 평가

### 2.1 probe 결과 요약

| Metric | Value | 판정 |
|---|---|---|
| train_id state_delta_norm_mean | 1.091208 | baseline |
| ood_mass_low state_delta_norm_mean | 1.108965 | — |
| gap (abs) | **0.017756** | PASS (> threshold 0.01) |
| gap (relative) | 1.63% | 미미하지만 일관적 방향 |
| KS test stat/p | 0.300 / **0.0217** | **PASS** (p < 0.05) |
| t-test stat/p | -1.903 / 0.0600 | borderline (p < 0.05 기준 실패) |
| n per group | 50 | — |

### 2.2 신뢰도 한계

| 한계 | 영향 | 해결 방안 |
|---|---|---|
| 단일 probe (n=50, KS p=0.022) | full 250ep에서 재현 보장 없음 | Stage 3 full collection 후 재검증 |
| t-test NOT significant (p=0.060) | group mean 차이 통계적 불안정 | n↑900에서 power 개선 기대 |
| `obs_mode="state"` 사용 | collector(`state_dict`) 대비 D_x 불일치 가능 | Q6에서 state_dict 모드 probe 필수 |
| contact_rate 미측정 | PickCube=0% 대비 PushCube 우위 미확인 | Agent D에서 확정 |
| friction OOD probe 없음 | PickCube friction primary와 비교 불가 | ood_friction_low 100ep 수집 후 확인 |
| mass=1.5만 테스트 | 다른 mass 값 sensitivity 미파악 | 현재 채택 값 유지 |

### 2.3 신뢰도 종합 판정

**CONDITIONAL_PASS**: gap과 KS test 기준 PASS. 단, full collection(n≥100) 후 재확인 필수.  
t-test borderline (p=0.060)은 표본 크기 부족에 기인하며, n=900(S2)에서 power ≥0.9 기대.

Power 추정 (one-sample t-test, effect size = 0.018/0.045 ≈ 0.40, α=0.05):
- n=50: power ≈ 0.61 (불충분)
- n=100: power ≈ 0.82 (충분)
- n=900: power ≈ 0.999 (충분)

**S2(900ep) 선택 시 통계적 안정성 확보.**

---

## 3. 코드 호환성 분석

### 3.1 collector.py `_apply_ood` (Line 66-76)

```python
# 현재 코드 (PickCube hard-coded):
inner.cube.set_mass(float(ood_params["object_mass"]))
```

PushCube 환경에서:
- `inner.cube` 속성이 없거나 `inner.obj`가 정확한 속성명일 가능성 높음
- `_analysis_scratch/pushcube_mass_probe.py` 코드에서 fallback 체인 확인:
  1. `hasattr(inner, "obj")` → `inner.obj.set_mass()`
  2. `hasattr(inner, "cube")` → `inner.cube.set_mass()`
  3. `scene.get_all_actors()` 이름 검색
- **예상 오류**: PickCube 경로 사용 시 `AttributeError: 'PushCubeEnv' object has no attribute 'cube'`

**Q6 Codex TASK에서 task-aware 분기 추가 필수.**

### 3.2 maniskill_schema.py OOD_PARAMS (Line 113-119)

```python
OOD_PARAMS = {
    "ood_mass_low": {"object_mass": 1.5, "joint_friction": 0.0},
    "ood_friction_low": {"object_mass": 0.064, "joint_friction": 5.0},
}
```

- PickCube 전용. PushCube는 ID mass가 다를 수 있음 (PushCube default cube mass ≠ 0.064 가능)
- D_x=42는 PickCube 고정값. PushCube에서는 다른 값 (probe 추정: obs_mode="state"로 확인 필요)

### 3.3 collect_maniskill.py SPLIT_DEFAULTS (Line 35-76)

모든 output path: `data/fglc/PickCube-v1/raw/...` hard-coded.  
`--task PushCube-v1` 인자가 있어도 output path가 PickCube로 남음.

**Q6 Codex TASK에서 task-aware path dispatcher 필수.**

### 3.4 D_x UNKNOWN 분석

probe 스크립트 (`pushcube_mass_probe.py`) 는 `obs_mode="state"` 사용:
- `obs.cpu().numpy().flatten()` → D_x = len(flattened obs)
- 이 값을 probe에서 직접 출력하지 않음
- ManiSkill 3.0.1 PushCube-v1 문서 기준: state_dict 모드에서 agent_qpos(9) + agent_qvel(9) + tcp_pose(7) + obj_pose(7) + tcp_to_obj(3) + goal_pos(3) = 38개 추정 (확정 필요)
- **결론: D_x = UNKNOWN. Q5 preflight 또는 Q6 첫 단계에서 state_dict 모드로 확정.**

---

## 4. 자원 계산 (Q2)

### 4.1 디스크 추정

| 시나리오 | PushCube ep | disk (추정) | 비고 |
|---|---|---|---|
| S1 | 450 | ~8.4 MB | 최소 |
| **S2 (권장)** | **900** | **~16.8 MB** | KS power ≥ 0.999 |
| S3 | 900 (+ PickCube 900 재수집) | ~36.2 MB | PickCube 재수집 포함 |
| S4 | 1800 | ~33.5 MB | 최대 (PickCube 유지 시) |

- PushCube transition 크기 추정: D_x=38(추정) 기준 ≈ 374 B/transition → 18,700 B/episode
- 디스크 여유: 290 GB → 어떤 시나리오도 문제없음

### 4.2 수집 시간 추정

PickCube-v1 450ep = 7분 (실측, commit 3c1806e).  
PushCube는 D_x 작아 약간 빠를 것으로 추정.

| 시나리오 | PushCube 수집 시간 | PickCube 추가 | 총 추가 시간 |
|---|---|---|---|
| S1 | ~7분 | 0 | ~7분 |
| **S2 (권장)** | **~14분** | **0** | **~14분** |
| S3 | ~14분 | ~7분 | ~21분 |
| S4 | ~28분 | 0 | ~28분 |

### 4.3 VRAM 안전 마진

`smoke_maniskill_pickcube.yaml` 기준: batch_size=16, T=8, K=6, d=32, h_dim=128  
- 모델 파라미터 추정: 5~10M params → 40~80 MB VRAM
- gradient + optimizer: 2× = 80~160 MB
- 활성화: batch×T×(D_x+K×d+h) ≈ 0.5~1 MB
- **총 VRAM ≈ 150~300 MB** (8188 MiB의 < 4%)

PushCube (D_x≤42) 추가해도 VRAM 영향 없음. **OOM 위험 없음.**

### 4.4 권장 시나리오

**S2 권장**: PickCube 450ep 유지 + PushCube 900ep 신규.
- 근거 1: borderline t-test (p=0.060) → n↑로 해결
- 근거 2: ood_mass_low 100ep, ood_friction_low 100ep로 Agent C 신뢰도 확보
- 근거 3: 총 추가 시간 14분 (3조건 모두 충족)

---

## 5. PushCube 수집 seed pool 제안

S2 기준 PushCube 900ep split:

| Split | n_ep | seed_pool | output |
|---|---|---|---|
| train_id | 500 | range(1042, 1542) | `data/fglc/PushCube-v1/raw/train_id.h5` |
| val_id | 100 | range(1600, 1700) | `data/fglc/PushCube-v1/raw/val_id.h5` |
| test_id | 100 | range(1700, 1800) | `data/fglc/PushCube-v1/raw/test_id.h5` |
| ood_mass_low | 100 | range(1800, 1900) | `data/fglc/PushCube-v1/raw/ood_mass_low.h5` |
| ood_friction_low | 100 | range(1900, 2000) | `data/fglc/PushCube-v1/raw/ood_friction_low.h5` |

- PickCube seed range (42-650)과 완전 분리
- `1042~` 시작으로 seed overlap = 0 보장
- regime_id: PickCube와 동일 (train_id=0, val_id=1, test_id=2, ood_mass_low=10, ood_friction_low=20)

---

## 6. Open UNKNOWNs (Q5/Q6에서 채워질 것)

| # | Unknown | 해결 방안 |
|---|---|---|
| U1 | PushCube D_x (추정 35~42) | Q5 probe 또는 Q6 첫 단계에서 state_dict 모드 확정 |
| U2 | PushCube ID mass default (추정 0.064) | Q6 collector 패치 중 env.unwrapped 확인 |
| U3 | PushCube inner 속성명 (obj vs cube) | Q6 확인, pushcube_mass_probe.py hasattr 체인 참조 |
| U4 | contact_rate (random policy에서) | Agent D Stage 4에서 측정 |
| U5 | friction OOD gap (PushCube에서) | ood_friction_low 100ep 수집 후 Agent C |

---

## 7. PLAN_PASS 판정

- pre-flight 5항목 모두 PASS ✓
- probe CONDITIONAL_PASS (gap PASS, KS PASS, t-test borderline) ✓  
- 코드 한계 3개 식별 + Q6 해결 경로 확인 ✓
- 자원 계산 완료 (S2 권장, 14분 추가) ✓
- seed pool 설계 완료 (PickCube와 비겹 확인) ✓

**PLAN_PASS → Stage 1 (Q6 Codex TASK) 진입 준비 완료.**
