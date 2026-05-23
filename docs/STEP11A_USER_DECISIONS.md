# STEP 11A — User Decisions Record

> 작성일: 2026-05-23  
> 선행: Step 10 완료, Step 11 PLAN 승인  
> 목적: Step 11 (ManiSkill state-only 데이터 파이프라인) 실행 전 §K1~§K10 사용자 결정 기록

---

## K1. ManiSkill 설치 및 task 선택

**결정**: 옵션 A (권장) — mani-skill + sapien 설치 진행, PickCube-v1 사용

- 설치 결과: mani-skill==3.0.1, sapien==3.0.3 (Windows 네이티브, 2026-05-23)
- PushCube / LiftCube = DEFERRED
- Python 3.13 pip과 혼용 방지: venv pip ensurepip 후 venv 전용 pip 사용

---

## K2. requirements.txt 핀 추가 승인

**결정**: 승인 — requirements.txt 핀 추가 진행

실제 추가된 패키지 (29개):
| 패키지 | 버전 |
|---|---|
| mani-skill | 3.0.1 |
| sapien | 3.0.3 |
| h5py | 3.16.0 |
| hydra-core | 1.3.2 |
| omegaconf | 2.3.0 |
| antlr4-python3-runtime | 4.9.3 |
| annotated-doc | 0.0.4 |
| arm-pytorch-utilities | 0.5.0 |
| click | 8.4.1 |
| dacite | 1.9.2 |
| docstring-parser | 0.18.0 |
| gitdb | 4.0.12 |
| GitPython | 3.1.50 |
| hf-xet | 1.5.0 |
| huggingface_hub | 1.16.1 |
| importlib_resources | 7.1.0 |
| lxml | 6.1.1 |
| nvidia-ml-py | 13.595.45 |
| pyperclip | 1.11.0 |
| pytorch-seed | 0.2.0 |
| pytorch_kinematics | 0.7.6 |
| shellingham | 1.5.4 |
| smmap | 5.0.3 |
| tabulate | 0.10.0 |
| transforms3d | 0.4.2 |
| trimesh | 4.12.2 |
| typeguard | 4.5.2 |
| typer | 0.25.1 |
| tyro | 1.0.13 |

총 requirements.txt: 183개 핀 (기존 154 + 신규 29)

---

## K3. CPU vs GPU 수집

**결정**: CPU 수집 (PLAN 권장, 사용자 명시 없음)

- SAPIEN renderer 기본 = CPU
- 학습만 GPU (RTX 4060 Ti, 8 GB VRAM)
- SAPIEN GPU plugin = DEFERRED

---

## K4. OOD axis 우선순위

**결정**: 기본 2개 + latency 조건부 예약

1. **확정 수집**: `ood_mass_low` (object_mass=1.5), `ood_friction_low` (friction=0.7)
2. **조건부 예약**: `ood_latency` (action_delay_steps=3) — D1 probe에서 executed_action/action_buffer 기록 가능성 확인 시에만 추가. 불가 시 DEFERRED.
3. latency split은 반드시 별도 OOD split으로 분리, manifest에 `action_delay_steps=3` 명시
4. noise/gain = DEFERRED

---

## K5/K6. 저장 포맷 및 commit 정책

**결정**: HDF5 + manifest만 commit

- raw .h5 파일: `data/fglc/PickCube-v1/raw/*.h5` = git 외부 (`.gitignore data/*` 차단)
- commit 대상: `manifest.json`, `dataset_stats.json`, `quality_report.json`, `split_config.yaml`
- `.gitignore` 업데이트 완료 (2026-05-23): `*.h5`, `*.hdf5` + 4개 파일 negation

---

## K7. Episode 예산

**결정**: 권장 90 ep

| split | n_episodes |
|---|---|
| train_id | 50 |
| val_id | 10 |
| test_id | 10 |
| ood_mass_low | 10 |
| ood_friction_low | 10 |
| **합계** | **90** |

`DATA_TOO_SMALL` repair candidate 발화 시 자동으로 train 100+ 로 증가.

---

## K8. R3 real smoke 진입 시점

**결정**: 10 checkpoint 모두 PASS 후에만 r3_smoke.py 진입

---

## K9. CANDIDATE_TABLE 보강 승인

**결정**: 승인 — OOD_TOO_HARD + EVAL_NOISE_HIGH repair candidate 추가

- `OOD_TOO_HARD` 후보: `severity_down` (mass 1.5→1.3, friction 0.7→0.85), `expand_coverage` (n_episodes ×2)
- `EVAL_NOISE_HIGH` 후보: `more_seeds`, `longer_episode`
- 발화 조건: `ood_id_nll_diff > 2.0` (OOD_TOO_HARD), `ood_metric_std > threshold` (EVAL_NOISE_HIGH)
- 적용: TASK D6 (Codex 위임)에서 구현

---

## K10. Linux/WSL fallback

**결정**: Windows 네이티브 진행 (2026-05-23 mani-skill==3.0.1 Windows 설치 성공)

- WSL2 fallback = Windows 설치 실패 시. 현재 불필요.
- pinnochio 경고는 state-only obs_mode에서 무관 (robotics kinematics 미사용)

---

## 미결 UNKNOWN (D1 probe에서 확정)

- `D_x`: PickCube-v1 state_dict concat 결과 차원 — UNKNOWN, D1 probe로 확정
- `D_a`: action_space.shape — UNKNOWN, D1 probe로 확정
- `episode_len` 분포: max_steps default — UNKNOWN
- OOD param API: `reconfig_kwargs` / `reset(options=...)` 등 5개 후보 중 동작 확인 — UNKNOWN
- latency API: `action_delay_steps` 기록 가능성 — UNKNOWN
- seed 결정성 수준 — UNKNOWN (D1 reproducibility probe)
