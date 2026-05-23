# STEP 10A — R3 Prerequisite Audit Report

> 작성일: 2026-05-23  
> 작성자: Claude (TASK 10A — Codex 위임 없음, Claude 직접 처리)  
> 선행 단계: STEP9.5_PASS (commits `e243455`, `7218c6d`, `68888e5`)  
> Plan 출처: Step 10 PLAN (plans/fglc-step-tidy-crayon.md)

---

## 1. 검증 실행 결과

### 1.1 pytest baseline
```
실행: .\.venv\Scripts\python.exe -m pytest tests/ -q
결과: 159 passed in 6.01s
```
**PASS** — Step 10 전체의 precondition 충족.

### 1.2 `import fglc` smoke
```
실행: .\.venv\Scripts\python.exe -c "import fglc; print(fglc.__version__)"
결과: fglc import OK, version: 0.1.0
```
**PASS** — `src/fglc/__init__.py` 패키지 임포트 정상.

### 1.3 핵심 의존성 smoke
```
실행: python -c "import torch, numpy; print(...)"
결과: torch: 2.6.0+cu124 | numpy: 2.1.3 | cuda: True
```
**PASS** — synthetic toy 경로에 필요한 최소 의존성(torch + numpy) 모두 사용 가능, CUDA 활성화.

### 1.4 repair harness 신구조 확인
```
outputs/repair/loop_2026-05-23T09-29-55-3eef/ledger.jsonl
... (총 7개 loop_*/ledger.jsonl 확인)
```
**PASS** — Step 9.5 CD-1/CD-9 패치 후 신구조 `{loop_id}/ledger.jsonl` 정상.

### 1.5 phase_gates 상태
```
outputs/phase_gates/R0.passed  (zero-byte, 2026-05-22 15:59)
R1.passed ~ R16.passed: 미생성
```
**확인** — R1.passed 생성은 이 TASK 종료 시 사용자 승인 후 수행.

---

## 2. src/fglc/ 스켈레톤 감사

### 2.1 존재하는 파일
| 파일 | 상태 |
|---|---|
| `src/fglc/__init__.py` | ✅ R1~R8 컴포넌트 docstring 약속 |
| `src/fglc/schemas/__init__.py` | ✅ |
| `src/fglc/schemas/visibility.py` | ✅ FORBIDDEN_AGENT_FIELDS 12개, SSoT |
| `src/fglc/repair/taxonomy.py` | ✅ |
| `src/fglc/repair/diagnose.py` | ✅ CANONICAL_METRIC_KEYS 14개 |
| `src/fglc/repair/candidates.py` | ✅ R3 patch keys 포함 |
| `src/fglc/repair/ranker.py` | ✅ |
| `src/fglc/repair/compare.py` | ✅ |
| `src/fglc/repair/ledger.py` | ✅ REQUIRED_KEYS 19개 |
| `src/fglc/repair/orchestrator.py` | ✅ RepairRunner Protocol(L74-85), run_repair_loop |
| `src/fglc/repair/__init__.py` | ✅ |

### 2.2 미생성 (BLOCKED → TASK 10B~10E에서 해결)
| 경로 | TASK |
|---|---|
| `src/fglc/models/` (encoder, belief, dynamics, heads) | 10C |
| `src/fglc/training/` (trainer_r3) | 10D |
| `src/fglc/evaluation/` (metrics) | 10D |
| `src/fglc/data/` (state_only_dataset, dataloader) | 10B |
| `src/fglc/runners/` (r3_runner) | 10E |
| `src/fglc/detectors/`, `src/fglc/attention/`, `src/fglc/correction/`, `src/fglc/planning/` | R4+ (Step 10 범위 밖) |

### 2.3 config 상태 (CD-8 미해결)
`configs/fglc/smoke_4060.yaml` — 6 lines stub (`phase, seed, K, d, h, batch_size`).  
K=4, h=64, batch_size=32는 Step 10 PLAN 권장(K=6, h=128, batch=16)과 불일치.  
**TASK 10B에서 전체 schema 확장 예정** (dataset/model/trainer/metric 섹션 추가).

---

## 3. 의존성 결정 (synthetic toy 경로)

### 3.1 Step 10 필요 의존성 (충족됨)
| 라이브러리 | 버전 | 용도 | 상태 |
|---|---|---|---|
| `torch` | 2.6.0+cu124 | 모델 학습/평가 | ✅ 설치됨 |
| `numpy` | 2.1.3 | synthetic 데이터 생성 | ✅ 설치됨 |
| `pytest` | 9.0.3 | unit tests | ✅ 설치됨 |
| `filelock` | (최신) | ledger atomic write | ✅ 설치됨 |

### 3.2 Step 10 불필요 (synthetic 경로 = 미설치 OK)
| 라이브러리 | 이유 | 상태 |
|---|---|---|
| `h5py` | ManiSkill HDF5 파일 파싱용 — synthetic은 on-the-fly 생성 | ❌ 미설치, Step 10 무관 |
| `hydra-core` / `omegaconf` | yaml config 관리 — Step 10은 단순 yaml.safe_load 충분 | ❌ 미설치, Step 10 무관 |
| `mani-skill` / `sapien` | ManiSkill 환경 — synthetic 경로 불필요 | ❌ 미설치, Step 10 무관 |

**결론**: synthetic toy 경로는 h5py/hydra/mani-skill 없이 진행 가능. 의존성 갭 = Step 10 차단 사유 아님.

---

## 4. R1 mini-closure 조건 정의

R1.passed는 다음 4 조건 모두 충족 시 생성:

| 조건 | 기준 | 확인 방법 |
|---|---|---|
| C1. `import fglc` smoke | ModuleNotFoundError 없음 | `python -c "import fglc"` |
| C2. `src/fglc/schemas/visibility.py` 정상 | 12 forbidden fields, assert_no_forbidden_fields 함수 존재 | `python -c "from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS; assert len(FORBIDDEN_AGENT_FIELDS)==12"` |
| C3. `src/fglc/repair/` 8 모듈 정상 | import 성공, RepairRunner Protocol 존재 | `python -c "from fglc.repair.orchestrator import RepairRunner, run_repair_loop"` |
| C4. 159 tests passed (기존 전체 suite) | 회귀 없음 | `pytest tests/ -q` |

**현재 4개 조건 모두 충족** → R1.passed 생성 준비 완료. 사용자 승인 대기.

---

## 5. R2 mini-closure 조건 정의

R2.passed는 TASK 10B 종료 후 다음 5 조건 충족 시 생성:

| 조건 | 기준 |
|---|---|
| C1. `src/fglc/data/state_only_dataset.py` 생성 | torch + numpy만 사용, h5py/mani-skill 불필요 |
| C2. 4 split shape 일관성 | train/val/ood_mass/ood_friction, episode_len=64, D_x=8, D_a=4 |
| C3. forbidden field 0건 | `assert_no_forbidden_fields(batch)` 통과 |
| C4. `configs/fglc/smoke_4060.yaml` CD-8 적용 | K=6, h_dim=128, batch_size=16, +4 섹션 |
| C5. `tests/test_fglc_dataset_state_only.py` PASS | 신규 dataset tests green |

---

## 6. 미처리 CD 항목 상태 (Step 9.5에서 이월)

| CD | 내용 | Step 10 해결 TASK |
|---|---|---|
| CD-2 | iter_{N}/ 4종 artifact 생성 (config.yaml, metrics.json, compare.json, run_manifest.json) | TASK 10E |
| CD-3 | `id_nll_1step` vs `id_nll` 명명 표준화 → `id_nll`로 통일, ledger schema 문서 패치 | TASK 10D |
| CD-4 | `repair_loop.py:84` default gate `id_nll: 0.4` → `0.5` (4060 path 정렬) | TASK 10E |
| CD-5 | `--dry-run` help text 보강 | TASK 10E |
| CD-8 | `smoke_4060.yaml` 6키 stub → 전체 schema 확장 | TASK 10B |

CD-1/CD-9는 Step 9.5에서 완료.

---

## 7. Step 10 하위 TASK 진행 계획 요약

| Sub-step | 범위 | 위임 | 다음 Sentinel |
|---|---|---|---|
| **10A** (현재) | Audit + R1 mini-closure | Claude 직접 | `R1.passed` (사용자 승인 후) |
| **10B** | Config schema 확장 + state-only toy dataset + R2 mini-closure | Codex TASK_10B | `R2.passed` |
| **10C** | Base WM 모듈 (encoder/belief/dynamics/heads) | Codex TASK_10C | — |
| **10D** | Trainer + Evaluator + metrics.json artifact | Codex TASK_10D | — |
| **10E** | R3Runner adapter + repair_loop 연결 | Codex TASK_10E | — |
| **10F** | 1-iter real smoke 실행 + 결과 보고 | Claude 직접 | `docs/STEP10_RESULT_REPORT.md` |

R3.passed 생성 금지 — synthetic 단계만으로는 R3 과학적 gate 통과 간주 불가.

---

## 8. 절대 하지 말 것 (사용자 지시 재확인)

- `outputs/phase_gates/R3.passed` 생성 금지
- ManiSkill / DROID / baseline grid 시작 금지
- `docs/idea/`, `docs/ROADMAP/` 임의 수정 금지
- empirical result 추측/fake number 기록 금지
- smoke 실패를 최종 결론으로 처리 금지 — 항상 repair loop 입력으로 변환

---

## 9. 결론

**R1 mini-closure 4 조건 모두 충족. R1.passed 생성 준비 완료.**

사용자 승인 요청:
- `/fglc-phase-check --pass R1` 호출하여 `outputs/phase_gates/R1.passed` 생성?
