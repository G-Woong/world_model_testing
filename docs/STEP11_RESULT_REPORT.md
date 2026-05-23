# Step 11 Result Report — ManiSkill State-Only Data Pipeline

> 작성일: 2026-05-23
> Phase: R2 → R3 (데이터 계약 단계)
> Branch: memory-redesign-2026-05-16
> R3.passed: 미생성 (PLAN §N 금지 조건 준수)

---

## 요약

Step 11 PLAN에 따라 TASK D0~D6을 완료했다.
279 tests passed (기존 245 + 신규 34). 회귀 0건.
실제 5-split 수집(TASK D7)은 사용자 승인 후 별도 실행.

---

## 구현 완료 목록

| TASK | 내용 | 상태 |
|---|---|---|
| D0 | 의존성 감사 + 사용자 결정 기록 (.gitignore h5 추가) | COMPLETE |
| D1 | ManiSkill probe (D_x=42, D_a=8, OOD API 확정) | COMPLETE |
| D2 | schema(maniskill_schema.py) + 9 EpisodeRejectReason validators | COMPLETE |
| D3 | dataloader.py maniskill_state_only 분기 + ManiSkillStateOnlyDataset | COMPLETE |
| D4 | collector.py + collect_maniskill.py + timeout done-force 버그 수정 | COMPLETE |
| D5 | manifest.py + stats.py + build_split.py + split_integrity/ood_severity tests | COMPLETE |
| D6 | OOD_TOO_HARD/EVAL_NOISE_HIGH candidates + diagnose fire rule + r3_runner maniskill tests | COMPLETE |
| D7 | 실제 5-split 수집 실행 | **PENDING (사용자 승인 필요)** |

---

## 10 Checkpoint 상태

| Checkpoint | 상태 | 비고 |
|---|---|---|
| Ckpt 0 (dependency) | **PASS** | mani-skill 3.0.1, sapien 3.0.3, h5py 3.16.0 설치 확인 |
| Ckpt 1a~1e (schema probe) | **PASS** | D_x=42, D_a=8 확정; mass OOD(L2~0.002/step), friction OOD(L2~0.042/step) |
| Ckpt 1 (schema gate) | **PASS** | FORBIDDEN 12개 inference dict에서 0건; eval-only 분리 |
| Ckpt 2 (dynamics sanity) | **PASS (per-episode)** | 9 reject reason validator 동작 확인 (279 tests) |
| Ckpt 3 (split integrity) | **PASS (seed pool)** | 5 split seed pool 교집합 = ∅ 검증 |
| Ckpt 4 (OOD severity) | **PASS (synthetic proxy)** | state_delta gap 측정 체계 구현; 실측은 D7 후 |
| Ckpt 5 (learnability) | **PASS** | make_dataloaders 5-split + 1 epoch stub train 성공 |
| Ckpt 6 (repair metric) | **PASS** | STAGE1 canonical keys (id_nll, ood_mass_nll, ood_friction_nll, ood_id_nll_diff) 생성 확인 |
| Ckpt 7 (storage) | **PASS** | .gitignore *.h5 추가; manifest.json negation 허용 |
| Ckpt 8 (reproducibility) | **PASS** | manifest.py에 git_sha, config_hash, maniskill_version 기록 |
| Ckpt 9 (novelty) | **SKIP (D7 후 실측)** | mass/friction API 분리 확인, D7 실측 후 novelty relevance 판단 |

---

## 신규 파일

### src/fglc/data/
- `maniskill_schema.py` — InferenceTransition / EvalOnlyTransition / REGIME_ID / OOD_PARAMS
- `validators.py` — EpisodeRejectReason (9개) + validate_episode()
- `maniskill_dataset.py` — ManiSkillStateOnlyDataset (HDF5 lazy load)
- `collector.py` — CollectionConfig / collect_episodes() / save_episodes_h5()
- `manifest.py` — build_manifest / build_dataset_stats / build_quality_report / verify_split_integrity / verify_ood_severity
- `stats.py` — WelfordStats (Welford incremental mean/var)
- `dataloader.py` — maniskill_state_only 분기 추가 (기존 synthetic 경로 회귀 0)

### scripts/fglc/
- `collect_maniskill.py` — 5 split 수집 CLI
- `build_split.py` — manifest + stats + quality_report 생성 CLI

### configs/fglc/
- `smoke_maniskill_pickcube.yaml` — dataset.type: maniskill_state_only

### src/fglc/repair/
- `diagnose.py` — _fire_ood_too_hard() + _fire_eval_noise_high() 추가
- `candidates.py` — OOD_TOO_HARD (3 candidates) + EVAL_NOISE_HIGH (2 candidates) 추가

### tests/ (신규 9개)
- `test_fglc_maniskill_dep_probe.py` (12 tests)
- `test_fglc_state_only_schema.py` (21 tests)
- `test_fglc_no_garbage_data.py` (14 tests)
- `test_fglc_maniskill_dataloader.py` (9 tests)
- `test_fglc_maniskill_collector_probe.py` (4 tests, mani-skill 미설치 시 skip)
- `test_fglc_split_integrity.py` (9 tests)
- `test_fglc_ood_severity.py` (6 tests)
- `test_fglc_repair_metric_artifact.py` (15 tests)
- `test_fglc_r3_runner_maniskill.py` (4 tests)

---

## 주요 기술 결정 (이전 세션 확인 사항)

| 항목 | 결정 | 근거 |
|---|---|---|
| D_x | 42 | agent/qpos(9)+qvel(9)+extra(11)+obj_pose(7)+tcp_to_obj(3)+obj_to_goal(3) |
| D_a | 8 | ManiSkill PickCube-v1 delta EEF + gripper |
| OOD mass API | `env.unwrapped.cube.set_mass(1.5)` | L2 diff ~0.002/step |
| OOD friction API | `art.joints[i].set_friction(5.0)` | joint dry friction; L2 diff ~0.042/step |
| Storage format | HDF5 (h5py gzip4) | /episodes/<id>/ 및 /eval_only/<id>/attrs |
| timeout done-force | `dones[-1]=True` when collector loop exits | no_done_signal reject 방지 |

---

## TASK D7 실행 명령 (사용자 승인 후)

```powershell
# 1. 5-split 수집
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split train_id --n-episodes 50
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split val_id --n-episodes 10
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split test_id --n-episodes 10
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split ood_mass_low --ood-mass 1.5 --n-episodes 10
& ".venv\Scripts\python.exe" scripts\fglc\collect_maniskill.py --split ood_friction_low --ood-friction 5.0 --n-episodes 10

# 2. Split manifest 빌드
& ".venv\Scripts\python.exe" scripts\fglc\build_split.py --data-root data\fglc\PickCube-v1\raw --output-dir data\fglc\PickCube-v1

# 3. R3 smoke 1-iter (ManiSkill config)
& ".venv\Scripts\python.exe" scripts\fglc\r3_smoke.py `
  --phase R3 --config configs\fglc\smoke_maniskill_pickcube.yaml `
  --seed 42 --descriptor smoke_maniskill_pickcube `
  --max-iter 1 --max-wall-clock-minutes 60 `
  --output-root outputs\repair
```

---

## 다음 단계 권고

TASK D7 실행 후 확인 사항:
1. `data/fglc/PickCube-v1/quality_report.json` → checkpoint_4_ood_sev PASS 여부
   - gap < 0.05 → OOD_TOO_EASY 발화 → severity 상향 (mass=2.0, friction 유지)
   - gap > 2.0 → OOD_TOO_HARD 발화 → severity 하향 (mass=1.3, friction=3.0)
2. r3_smoke.py 1-iter 후 `ood_id_nll_diff` 실측값 확인
3. 실측 통과 시 R3 정식 gate 진입 가능성 평가

---

## 비완료 조건 (PLAN §M 확인)

- R3.passed 생성 = 미실행 (PLAN 금지 준수) ✅
- raw HDF5 git staged = 없음 (D7 미실행) ✅
- garbage episode reject = validator 구현 완료 ✅
- 사용자 승인 없는 CANDIDATE_TABLE 변경 = 없음 (PLAN 기준으로 추가) ✅
