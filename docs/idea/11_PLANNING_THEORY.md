# 11_PLANNING_THEORY — Planning 이론

## 출처
- main.md §14 (planning 구조), §20.2-20.3 (rollout 루프)
- deep-research-report.md §Robust control·DRO (R-8), §Inference decision flow (R-17)

## 주장

Planner는 보정된 잠재 rollout에 대해 MPPI/CEM을 사용합니다.
현재 타임스텝에서 얻은 correction 마스크 α_t, δ_t는 H_corr=3~5 미래 스텝 동안 외삽되며
(**단기 유지**, short-horizon hold), 물리적 regime 이동이 스텝에 걸쳐 지속되기 때문입니다.
계산 절약은 β_t < 임계값일 때 기본 planner를 사용함으로써 이루어집니다.

## 수학적 형식화

```
Planner 입력:
  현재 z_t, h_t; 후보 action 시퀀스 A = [a_t,...,a_{t+H-1}]

비보정 rollout (β_τ가 낮을 것으로 예측되는 타임스텝):
  ẑ_{τ+1} = fθ(ẑ_τ, a_τ, h_τ)
  r̂_τ = Rθ(ẑ_τ, a_τ)

보정 rollout (β_t가 트리거될 때 첫 H_corr=3~5 스텝):
  현재 (α_t, δ_t) correction 마스크 사용 (단기 유지)
  z̃_{τ+1} = fθ(z̃_τ, a_τ, h_τ) + β_τ · α_t · δ_τ    [α_t는 H_corr 스텝 동안 고정]
  
전체 궤적 점수:
  J(A) = Σ_{τ=t}^{t+H-1} γ^{τ-t} r̂_τ + γ^H V̂(ẑ_{t+H})
  
MPPI 업데이트:
  weights_i ∝ exp(J(A_i) / temperature)
  a_t* = Σ_i weights_i · a_t^i

계산 게이팅 planning:
  β_t < threshold이면: 기본 planner 사용 (correction 없음)
  β_t ≥ threshold이면: 보정된 planner 사용

결정 관련 계산: action/value 변화가 계산 비용을 정당화할 때만 planning 호출
```

## Robust MPC (CIRCA 변형)

deep-research-report.md §R-17은 보정된 latent 하에서 robust MPC를 제안합니다:
1. 보정된 falsification gate → correction 여부 결정 (go/no-go)
2. α에 의한 top-k 그룹 선택
3. 효과 재평가 (개입 유틸리티 확인)
4. Value 개선 확인
5. 개선 예상 시: 보정된 z̃ 하에서 robust MPC

## 연결 맵
- 상위: M-6 (dynamics), M-8 (β_t gate), M-9 (α_t), M-11 (δ_t)
- 하위: M-12 (return/recovery 검증은 planner 출력 사용)
- 알고리즘: R-8 (robust MPC), R-15 (인과 그래프), R-17 (추론 흐름)

## 체크포인트

- C1 수학적 유효성: PASS — MPPI/CEM은 표준. 단기 유지는 휴리스틱
  (regime 이동의 지속성으로 정당화됨). Value 일관성 손실 검증됨.
- C2 신규성: CONDITIONAL — 보정된 latent에 대한 MPPI/CEM이 조합입니다.
  개별 구성 요소로는 새롭지 않음; 통합 시스템으로서 새로움.
- C3 Reviewer 공격: 공격 5 (4축 지표 동어반복). 계산 매칭된 baseline 필요.
  reviewer2_attack_fglc_R1.md §공격 5 참조.
- C4 타당성: PASS — 512 rollout, H=10으로 A100에서 MPPI: ~50ms/스텝. 실현 가능.
- C5 Claim-지표: Return + recovery time + 에피소드당 planning 호출 + 최악의 경우 return.
  모두 측정해야 함; 계산 매칭된 실험 필요.
- C6 구현 위험: 중간 — correction을 MPPI rollout 루프에 통합하는 데 신중한 구현 필요.
- C7 실험 설계: 필수: 계산 매칭된 baseline. FGLC와 baseline 모두 에피소드당
  동일한 전체 planning rollout을 받음.
- C8 실패 해석: 계산 매칭된 baseline이 FGLC와 동등하면: 계산 추가에서 이점 발생.
  이는 correction이 예측을 개선하지만 planning 효율성은 아님을 의미.
- C9 관련 연구: MPPI (Williams et al. 2017), CEM — 대기 중 ≥2 출처
- C10 컨텍스트 라우팅: 출처 = main.md §14. 하위: 12_TRAINING_STAGES.md, 13_ALGORITHM_CIRCA.md
