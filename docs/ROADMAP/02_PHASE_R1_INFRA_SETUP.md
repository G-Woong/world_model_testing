# Phase R1 — 인프라 설정

## 목표
ManiSkill/SAPIEN/h5py/entmax 설치, CUDA 검증, src/fglc/ 스켈레톤 생성.

## 입력
- 이전 단계 sentinel: outputs/phase_gates/R0.passed
- 코드 스텁: src/fglc/__init__.py

## 단계

1. **Python 환경 설정**
   ```powershell
   # 기본 의존성 설치
   pip install -e ".[maniskill,rl,causal]"
   # ManiSkill 검증
   python -c "import mani_skill; print(mani_skill.__version__)"
   # entmax 검증
   python -c "from entmax import sparsemax, entmax15; print('entmax OK')"
   # CUDA 검증
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **src/fglc/ 패키지 스켈레톤 생성**
   ```
   src/fglc/
   ├── __init__.py (완료)
   ├── py.typed (완료)
   ├── schemas/
   │   ├── __init__.py
   │   └── visibility.py  ← FORBIDDEN_AGENT_FIELDS (취약 파일)
   ├── models/
   │   ├── encoder.py     ← MLP encoder, 그룹화된 latent
   │   ├── dynamics.py    ← 기본 dynamics 사전 분포 pθ
   │   └── belief.py      ← GRU belief memory
   ├── detectors/
   │   ├── mismatch.py    ← 표준화된 불일치 ρ_t
   │   └── gate.py        ← falsification gate β_t
   ├── attention/
   │   └── causal.py      ← 개입 정책 attention α_t
   ├── correction/
   │   └── adapter.py     ← sparse residual correction δ_t
   ├── planning/
   │   └── mppi.py        ← MPPI/CEM 잠재 planner
   ├── evaluation/
   │   ├── metrics.py     ← 4축 지표 세트
   │   └── calibration.py ← ECE, 신뢰도 다이어그램
   └── data/
       └── maniskill.py   ← ManiSkill 데이터 로더
   ```

3. **visibility.py 생성 (취약 파일)**
   FORBIDDEN_AGENT_FIELDS 정의: regime_id, true_mass, true_friction 등.
   docs/idea/18_DATA_BENCHMARKS.md §데이터 규칙의 미러.

4. **패키지 임포트 검증**
   ```powershell
   python -c "import fglc; from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS; print(len(FORBIDDEN_AGENT_FIELDS), '금지 필드')"
   ```

5. **가시성 동기화 테스트 생성**
   tests/test_fglc_forbidden_field_sync.py

## 산출물
- 코드: `src/fglc/` (12개 모듈)
- 테스트: `tests/test_fglc_forbidden_field_sync.py`
- 문서 업데이트: 없음

## Gate 기준 (R1.passed를 위해 모두 true여야 함)

- [ ] `pip install -e ".[maniskill]"` 성공
- [ ] `python -c "import fglc.schemas.visibility"` 성공
- [ ] `pytest tests/test_fglc_forbidden_field_sync.py` 통과
- [ ] `python -m pyflakes src/fglc/` → 0 오류
- [ ] ManiSkill 환경 인스턴스화 테스트 통과 (스모크 테스트)

## 위험 등록부 참조
- R-2 (ROADMAP/19): ManiSkill API 드리프트
- R-3 (ROADMAP/19): SAPIEN 버전 호환성

## 커밋 주기
- 커밋 1: `feat(fglc): R1 src/fglc 스켈레톤 + visibility.py`
- 커밋 2: `test(fglc): R1 금지 필드 동기화 테스트 통과`

## Codex 위임
예 — 스켈레톤 생성 (3개 이상 파일) → Codex TASK 파일: `.agent_tasks/codex_queue/TASK_R1_FGLC_SKELETON.md`
