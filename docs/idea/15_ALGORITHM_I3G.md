# 15_ALGORITHM_I3G — 식별 가능한 불변 개입 Gate

## 출처
- deep-research-report.md §I3G (R-11), §iVAE/nonlinear ICA (R-4), §ICP/IRM/anchor (R-5)

## 우선순위: 2

## 주장

I3G는 iVAE 방식의 컨텍스트 조건부 사전 분포와 ICP/anchor 회귀 불변성 페널티를 결합하여
잠재 그룹을 식별 가능하고 불변하게 만듭니다. 이는 *어떤* 그룹이 *어떤 유형*의 물리적 이동에
대응하는지에 대한 가장 강력한 이론적 보증을 제공하지만, 보조 컨텍스트 변수 u_t
(태스크 ID 또는 도메인 ID)가 필요합니다.

## 수학적 형식화

```
컨텍스트 조건부 사전 분포 (iVAE 영감):
  p_θ(z_t | u_t) = Π_k p_θ(z_t^k | u_t)   [보조 변수 u_t: 태스크/도메인/시간 컨텍스트]

I3G 전체 손실:
  L = L_wm
    + λ_id   L_iVAE        [식별 가능성: 인수분해된 사전 분포를 가진 ELBO]
    + λ_inv  L_ICP_anchor  [불변성: 환경 전반에 걸쳐 일관적인 잔차]
    + λ_s    ||m||_{2,1}   [sparse group gates]

iVAE 손실:
  L_iVAE = ELBO(z_t | x_t, u_t), p_θ(z_t^k | u_t) = ExpFam(λ_k(u_t))

불변성 손실 (ICP/anchor 변형):
  L_ICP = Σ_env_e Var_e[residual(z_t^k; causal_S)] - E[residual^2(z_t^k; causal_S)]
  (환경 전반에 걸쳐 잔차의 분산 페널티)

I3G 학습:
  1. 보조 변수 u_t를 사용한 컨텍스트 조건부 잠재 모델 z_t 학습
  2. 환경 전반에 걸쳐 불변성 페널티 적용 (다양한 OOD 조건을 환경으로)
  3. 불변/식별 가능한 그룹에 대해서만 sparse group gates 학습
  4. 순차적 잔차 탐지기 보정 (SPCI 또는 CUSUM)

I3G 추론:
  1. 보정된 gate로 불일치 탐지
  2. 상태 그룹보다 컨텍스트/숨겨진-파라미터 그룹 먼저 업데이트 (인과 우선순위)
  3. 보정된 컨텍스트 조건부 모델로 planning
```

## I3G가 CIRCA를 능가하는 경우

I3G는 가장 강한 해석 가능성을 가집니다: 질량이 이동할 때, (u_t로 식별 가능한) z^context가
시드 전반에 걸쳐 일관되게 활성화됩니다. 시뮬레이션에서 물리적 팩터의 ground-truth를 알 때,
I3G는 변경된 팩터 대비 가장 높은 마스크 정밀도/재현율을 가져야 합니다.

예상 우위: ground-truth 물리적 팩터를 알고 + 좋은 u_t를 가진 시뮬레이션 평가.
예상 약점: u_t가 없거나 노이즈가 있는 실제 로봇.

## 연결 맵
- 상위: R-4 (iVAE), R-5 (ICP/anchor), R-11 (SPCI), M-3 (잠재 분해)
- 알고리즘 동료: 13_ALGORITHM_CIRCA.md, 14_ALGORITHM_ASAP.md, 16_ALGORITHM_IVI.md
- 하위: 17_ALGORITHM_COMPARISON.md

## 체크포인트

- C1 수학적 유효성: CONDITIONAL — iVAE 식별 가능성은 충분한 변화를 가진 보조 변수 u_t 필요.
  ManiSkill에서 u_t = 태스크 조건(질량/마찰 값)이 이것을 제공할 것임 —
  하지만 질량/마찰 레이블을 학습 시 u_t로 사용하면 "추론 시 regime 레이블 없음" 정책과 충돌.
  모순: iVAE는 학습 시 regime 컨텍스트가 필요하고, 추론 시는 아님.
  해결책: u_t = 에피소드 시간 인덱스 (약한 보조) 또는 태스크-유형 (PickCube vs PushCube).
  이것은 식별 가능성 보증을 약화시키지만 그룹 일관성을 개선할 수 있음.
- C2 신규성: CONDITIONAL — iVAE + ICP + sparse gates 조합은 표준이 아님.
  가장 가까운 것: HiP-RSSM (컨텍스트-RSSM); 차별화: FGLC는 sparse correction gates 사용.
- C3 Reviewer 공격: 높음 — "학습 시 regime 레이블이 필요함 (u_t = 질량/마찰)."
  이것은 oracle-레이블 없음 원칙을 위반합니다. 방어: u_t = 태스크 유형 (물리적 파라미터 아님),
  이것은 관측 가능합니다. 논문에서 명확한 설명 필요.
- C4 타당성: CONDITIONAL — 인수분해된 사전 분포를 가진 iVAE ELBO가 복잡성 추가.
  OOD 조건 전반에 걸친 ICP는 멀티 환경 배치 필요. CIRCA보다 ~3× 더 복잡.
- C5 Claim-지표: 시뮬레이션 ground-truth: 변경된 팩터 대비 마스크 정밀도/재현율
  (질량 이동 → z^context 활성화; 마찰 이동 → z^contact 활성화). I3G가 여기서 최고여야 함.
- C6 구현 위험: 높음 — iVAE 인수분해된 사전 분포 + ICP 멀티-환경 학습에 신중한 배치 필요.
- C7 실험 설계: ground-truth 팩터 오라클이 있는 시뮬레이션 평가.
  OOD 유형당 I3G attention 활성화 vs. 변경된 물리적 파라미터 비교.
- C8 실패 해석: I3G가 CIRCA보다 마스크 정밀도가 높지 않으면: 식별 가능성 가정이
  사용 가능한 보조 신호에 의해 충족되지 않음. I3G를 ablation으로 축소.
- C9 관련 연구: Khemakhem et al. (2020) iVAE; Peters et al. (2016) ICP — 대기 중 ≥2 출처
- C10 컨텍스트 라우팅: 출처 = deep-research-report.md §I3G. 하위: 17_ALGORITHM_COMPARISON.md
