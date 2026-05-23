# 18_DATA_BENCHMARKS — 데이터 벤치마크 (취약 파일)

## 출처
- main.md §2 (입력 데이터), §15 (데이터 분할), §16 (모달리티 진행)
- deep-research-report.md §실험 설계와 벤치마크 (R-13)

## 주장

제어된 물리적 파라미터 변화를 가진 ManiSkill state-only 데이터가 주요 벤치마크를 제공합니다.
regime_id와 env_state (실제 물리적 파라미터)는 **평가 전용** 필드이며
학습 손실이나 추론 입력에 절대 포함되지 않습니다.

## 데이터 스키마

```python
transition_t = {
    # 추론 입력 (허용됨)
    "state":   x_t,         # shape: [D_x] — 로봇 고유감각 + 물체 + 목표
    "action":  a_t,         # shape: [D_a] — 델타 EEF + 그리퍼
    "reward":  r_t,         # 스칼라
    "done":    d_t,         # 스칼라

    # 평가 전용 (추론 입력에 금지됨)
    "regime_id":    g_t,    # 물리적 regime 레이블
    "true_mass":    m_t,    # 실제 물체 질량
    "true_friction": f_t,   # 실제 마찰
    "true_latency":  l_t,   # 실제 액션 지연
    "true_noise":    n_t,   # 실제 관측 노이즈 σ
    "true_action_gain": ag_t, # 실제 액션 게인

    # 오라클 baseline (명시적으로 레이블됨; 표준 에이전트에 금지됨)
    "oracle_action": oa_t,  # 실제 물리적 파라미터를 감안한 최적 action
    "split_id": sid_t,      # OOD 분할 소속
}
```

## OOD 분할 설계

```
Train-ID:    mass=1.0, friction=1.0, latency=0, noise=0.0, action_gain=1.0
Valid-ID:    동일 분포
Test-ID:     동일 분포, 미본 시드

OOD-mass:    mass ∈ {0.5, 1.5, 2.0}
OOD-friction: friction ∈ {0.3, 0.7, 1.5}
OOD-latency:  delay ∈ {3, 5, 8} 스텝
OOD-noise:   obs_noise σ ∈ {0.05, 0.1, 0.2}
OOD-action-gain: gain ∈ {0.7, 0.85, 1.3}
OOD-mixed:   mass × friction × latency 결합
```

## 데이터셋

| 데이터셋 | 역할 | 모달리티 | OOD 축 |
|---|---|---|---|
| ManiSkill PickCube/PushCube/LiftCube | 주요: 제어된 실험 | state_dict | mass/friction/latency/noise/gain |
| robosuite/robomimic | HDF5 파이프라인 검증 | states+actions | 카메라 dropout, 관측 손상 |
| DROID (Khazatsky 2024) | 실제 로봇 검증 Phase 2 | language+proprio+3-RGB | collector 분할, 장면 이동 |
| BridgeData V2 (Walke 2023) | 실제 로봇 일반화 | image+goal-image | 기관/물체 분할 |

## 데이터 규칙 (규범적)

- regime_id: **평가 전용** — 학습 손실에 없음, 모델 입력에 없음
- env_state (mass/friction/latency/noise/gain): **평가 전용**
- oracle_action: **오라클 BASELINE만** — 명시적으로 레이블된 실험
- split_id: **분할 추적만** — 모델 입력에 없음

**근거**: FGLC는 오라클 regime 레이블 **없이** regime 이동을 식별한다고 주장합니다.
regime_id가 학습에 포함되면, "regime 레이블이 필요 없음"이라는 주장이 위반됩니다.

## 연결 맵
- 상위: docs/main/main.md §2, §15
- 하위: 모든 학습/평가 스크립트; 21_METRICS.md (평가는 split_id 사용)
- **취약 파일**: 이 문서가 데이터 규칙의 규범적 SSoT입니다

## 체크포인트

- C1 수학적 유효성: 해당 없음 (데이터 스키마 설계)
- C2 신규성: 해당 없음
- C3 Reviewer 공격: 중간 — "평가 시 regime_id 사용 — 누수 아닌가?"
  방어: regime_id는 **평가 계층화**에만 사용 (어떤 OOD 분할?), 모델 입력이나
  학습 신호로 사용 안 됨. 정확도 계산을 위해 테스트 셋 레이블을 사용하는 것과 유사.
- C4 타당성: CONDITIONAL — DROID/BridgeData 다운로드는 큰 저장공간 필요 (~100GB+).
  Phase 1 (state-only ManiSkill): 완전히 실현 가능. Phase 2: DROID 접근 필요.
- C5 Claim-지표: OOD 탐지 AUROC는 ground-truth 레이블로 regime_id 사용.
  예측/planning 지표는 OOD 분할별로 계산.
- C6 구현 위험: 중간 — ManiSkill OOD 변화는 환경 파라미터 API 필요.
- C7 실험 설계: OOD 도전 존재 검증: OOD NLL >> ID NLL (Stage 1).
- C8 실패 해석: OOD 분할이 측정 가능한 dynamics 이동 생성 안 하면: 데이터셋 설계 실패.
- C9 관련 연구: ManiSkill v3 (arXiv 2410.00425); DROID arXiv 2403.12945 — 대기 중 ≥2 출처
- C10 컨텍스트 라우팅: 출처 = main.md §2,15. **이 파일은 취약 (규범적 데이터 SSoT).**
