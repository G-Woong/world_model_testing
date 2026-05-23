# STEP 11A — Dependency Audit Report

> 작성일: 2026-05-23  
> Checkpoint 0 결과 기록 (Step 11 PLAN §E Checkpoint 0)

---

## Checkpoint 0: Dependency Gate

### 검증 명령
```powershell
$py = "C:\Users\computer\Desktop\ICLR_WM_claude-code\.venv\Scripts\python.exe"
& $py -c "
import mani_skill; print('mani_skill:', mani_skill.__version__)
import sapien; print('sapien:', sapien.__version__)
import h5py; print('h5py:', h5py.__version__)
import gymnasium; print('gymnasium:', gymnasium.__version__)
import hydra; print('hydra:', hydra.__version__)
import omegaconf; print('omegaconf:', omegaconf.__version__)
print('Checkpoint 0: ALL PASS')
"
```

### 결과

| 패키지 | 기대 버전 | 실제 버전 | 상태 |
|---|---|---|---|
| mani-skill | ≥3.0.0b18 | 3.0.1 | ✅ PASS |
| sapien | ≥3.0.0 | 3.0.3 | ✅ PASS |
| h5py | ≥3.9 | 3.16.0 | ✅ PASS |
| gymnasium | 1.2.3 (pin) | 1.2.3 | ✅ PASS |
| hydra-core | ≥1.3 | 1.3.2 | ✅ PASS |
| omegaconf | ≥2.3 | 2.3.0 | ✅ PASS |

**Checkpoint 0: PASS** (2026-05-23)

### 경고 (무시 가능)
```
UserWarning: pinnochio package is not installed, robotics functionalities will not be available
```
- 원인: SAPIEN의 pinocchio (robotics kinematics) 선택적 dependency 미설치
- 영향: state-only obs_mode 사용 시 영향 없음. FK/IK 계산은 필요 없음.
- 조치: 미설치 유지 (pinocchio Windows 빌드 복잡, FGLC에서 불필요)

---

## 설치 경위

### 설치 전 상태 (2026-05-23 오전)
- `mani_skill`: ModuleNotFoundError (미설치)
- `sapien`: ModuleNotFoundError (미설치)
- `h5py`: ModuleNotFoundError (미설치)
- `hydra-core`: ModuleNotFoundError (미설치)
- `omegaconf`: ModuleNotFoundError (미설치)
- `gymnasium`: 1.2.3 (기설치)

### pip 부트스트랩
venv에 pip 미설치 상태였으므로 먼저 ensurepip 실행:
```powershell
& $py -m ensurepip --upgrade
# → pip-24.0 설치
```

### 설치 순서
```powershell
# Step 1: h5py, hydra-core, omegaconf (표준 패키지)
& $py -m pip install "h5py>=3.9" "hydra-core>=1.3" "omegaconf>=2.3"
# → h5py-3.16.0, hydra-core-1.3.2, omegaconf-2.3.0, antlr4-python3-runtime-4.9.3

# Step 2: mani-skill (sapien을 자동 포함)
& $py -m pip install "mani-skill>=3.0.0b18"
# → mani-skill-3.0.1, sapien-3.0.3 + 24개 의존성
```

### Windows 호환성
- mani-skill 3.0.1 + sapien 3.0.3 Windows 네이티브 설치 성공 확인
- SAPIEN GPU plugin 미설치 (CPU renderer 사용)
- Windows path / NTFS 호환성 이상 없음

---

## requirements.txt 업데이트

- 기존: 154개 핀
- 추가: 29개 (신규 설치된 모든 패키지)
- 업데이트 후: 183개 핀 (알파벳 정렬 유지)
- 업데이트 방법: Python sorted() 병합 (중복 제거, 소문자 정렬 키)

---

## 다음 단계

- Checkpoint 1a~1e: PickCube-v1 task probe (TASK D1, Codex 위임)
  - 1a: Task 등록 + state_dict reset/step
  - 1b: D_x / D_a shape 확정
  - 1c: reward / done / success API 확인
  - 1d: seed 재현성 probe
  - 1e: OOD param API (5개 후보 순차 시도)

**BLOCKED 해소 여부:**
- [x] mani-skill 미설치 → 해소 (3.0.1)
- [x] sapien 미설치 → 해소 (3.0.3)
- [x] h5py 미설치 → 해소 (3.16.0)
- [x] hydra-core 미설치 → 해소 (1.3.2)
- [x] omegaconf 미설치 → 해소 (2.3.0)
- [x] requirements.txt 미핀 → 해소 (183개)
- [x] *.h5 gitignore 패턴 없음 → 해소 (.gitignore 업데이트)
- [ ] OOD param API 불명 → D1 probe에서 해소 예정
- [ ] D_x / D_a / episode_len → D1 probe에서 해소 예정
