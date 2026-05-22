# Phase R2 — 데이터 파이프라인

## 목표
ID와 OOD 분할이 있는 ManiSkill state-only 데이터셋, replay loader, 데이터 검증 테스트.

## 입력
- 이전 단계 sentinel: outputs/phase_gates/R1.passed
- 코드: src/fglc/data/maniskill.py

## 단계

1. **ManiSkill 환경 설정 + rollout 수집**
   ```python
   # 태스크: PickCube, PushCube, LiftCube
   # 정책: 초기를 위한 무작위 에이전트 + 인간 데모 재생
   # 상태 관측: state_dict (robot_qpos + object_pose + goal)
   ```

2. **OOD 파라미터 변화**
   ```python
   # 각 OOD 축에 대해 별도 데이터셋 분할 수집:
   OOD_CONFIGS = {
       "ood_mass":     [{"object_mass": v} for v in [0.5, 1.5, 2.0]],
       "ood_friction": [{"friction": v} for v in [0.3, 0.7, 1.5]],
       "ood_latency":  [{"action_delay": v} for v in [3, 5, 8]],  # 스텝
       "ood_noise":    [{"obs_noise_sigma": v} for v in [0.05, 0.1, 0.2]],
       "ood_gain":     [{"action_gain": v} for v in [0.7, 0.85, 1.3]],
       "ood_mixed":    [{"object_mass": 1.5, "friction": 0.7, "action_delay": 3}],
   }
   ```

3. **데이터 스키마 강제**
   각 전이는 평가 전용 분할에서 FORBIDDEN 필드와 함께 HDF5로 저장됩니다.
   금지 필드는 모델 입력 텐서 구성에 절대 포함되지 않습니다.

4. **Replay loader + 데이터 검증**
   `src/fglc/data/maniskill.py`: (state, action, next_state, reward, done)을 반환하는 DataLoader
   검증: `tests/test_fglc_data_pipeline.py`

5. **OOD 도전 존재 검증**
   핵심 GATE: 기본 WM NLL이 OOD에서 ID NLL보다 측정 가능하게 높아야 합니다.
   OOD_NLL ≈ ID_NLL이면 → 데이터셋 설계 실패 → 중단.

## 산출물
- 데이터: `data/fglc/` (태스크당 ID + 6개 OOD 분할)
- 코드: `src/fglc/data/maniskill.py`
- 테스트: `tests/test_fglc_data_pipeline.py`

## Gate 기준 (R2.passed를 위해 모두 true여야 함)

- [ ] 3개 태스크 × 7개 분할 (ID + 6개 OOD) 수집, 각 ≥1000 에피소드
- [ ] 평가 전용 파티션에 FORBIDDEN 필드 격리됨
- [ ] Replay loader가 올바른 텐서 형태 반환
- [ ] `pytest tests/test_fglc_data_pipeline.py` 통과
- [ ] OOD 도전 검증: ID NLL 측정됨 (Stage 1 비교를 위한 gate)

## 위험 등록부 참조
- R-2: ManiSkill API 드리프트 (물체 mass/friction 파라미터 이름이 변경될 수 있음)
- R-4: 계산 비용 — 3개 태스크 × 7개 분할 × 1000 에피소드 × T=16은 ~8시간 소요 가능

## 커밋 주기
- 커밋 1: `feat(data): R2 ManiSkill state-only ID 분할 loader`
- 커밋 2: `feat(data): R2 OOD 분할 (mass/friction/latency/noise/gain/mixed)`
- 커밋 3: `test(data): R2 데이터 파이프라인 검증 통과`

## Codex 위임
예 — 데이터 loader + 검증 (다중 파일) → Codex TASK_R2_DATA_PIPELINE.md
