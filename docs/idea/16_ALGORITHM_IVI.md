# 16_ALGORITHM_IVI — 영향 검증 개입

## 출처
- deep-research-report.md §IVI (R-12), §영향 함수 (R-2)

## 우선순위: 4

## 주장

IVI는 영향 함수를 빠른 1차 순위 매기기에 사용하고, 최종 선택은 무작위화된 knockout으로
재검증합니다. 4가지 알고리즘 중 계산적으로 가장 효율적이지만, 큰 dynamics 이동에서는
국소 선형 영향 가정이 무너지는 가장 약한 알고리즘입니다.

## 수학적 형식화

```
국소 영향 점수:
  I_g ≈ |∂U/∂z^(g)|   [그룹 g에 대한 유틸리티의 기울기]
  
  전체 Hessian 기반: I_g ≈ |∂²U/∂z^(g)∂θ · H_θ^{-1} · ∂L/∂θ|
  (HVP를 통해 근사: Hessian-벡터 곱)

결합 점수:
  score_g = ω₁ I_g + ω₂ ΔÛ_g^{knockout}
  여기서 ΔÛ_g = U(z, 그룹 g 보정됨) - U(z 비보정)

IVI 학습:
  1. World model + value-aware 손실 학습
  2. 잠재 그룹에 대한 국소 영향 점수 계산
  3. top-k 그룹에 대해서만 무작위화된 knockouts 실행
  4. 결합 점수를 sparse attention에 증류
  5. Correction 적용 전에 보정된 순차 gate 사용

복잡도: O(BT · C_wm + n_mc · k) 여기서 n_mc << ASAP의 2^k
  기본 WM 이상 ~2-3× 오버헤드; 배포에 가장 실용적
```

## IVI가 CIRCA를 능가하는 경우

IVI가 가장 빠릅니다. 작은 dynamics 이동(5-10% 질량 변화)에 대해 국소 선형 영향이
대부분의 효과를 정확하게 포착합니다. 예상 최고 성능: 실시간 배포,
저예산 계산, 작은 섭동.

예상 약점: 국소 근사가 무너지는 큰 이동(2× 질량 변화).

## 연결 맵
- 상위: R-2 (영향 함수), M-9 (α), M-11 (correction δ)
- 알고리즘 동료: 13_ALGORITHM_CIRCA.md, 14_ALGORITHM_ASAP.md, 15_ALGORITHM_I3G.md
- 하위: 17_ALGORITHM_COMPARISON.md

## 체크포인트

- C1 수학적 유효성: CONDITIONAL — Hessian 근사는 국소적으로 유효; 큰 이동에 대해 무너짐.
  1차 필터로서의 Influence(영향-as-ranker)는 전체 영향이 부정확하더라도 여전히 유효.
- C2 신규성: 낮음 — 신경망에 대한 영향 함수는 잘 확립됨 (Koh & Liang 2017).
  새로운 측면: WM 컨텍스트에서 그룹 수준 잠재 순위 매기기에 적용.
- C3 Reviewer 공격: 중간 — "국소 방법은 큰 regime 이동을 처리할 수 없음."
  인정된 한계. IVI는 주요 알고리즘이 아닌 경량 baseline입니다.
- C4 타당성: PASS — HVP 계산은 PyTorch에서 표준. 4가지 알고리즘 중 가장 효율적.
- C5 Claim-지표: IVI는 작은 이동에서 CIRCA와 동등해야 합니다
  (OOD-noise, 작은 OOD-friction).
  IVI는 큰 이동에서 CIRCA보다 낮아야 합니다 (2× 질량, OOD-mixed).
- C6 구현 위험: 낮음 — torch.autograd.functional.vjp를 통한 HVP.
- C7 실험 설계: 이동 크기 전반에 걸쳐 IVI vs. CIRCA 비교.
  가설: IVI ≈ CIRCA (작은 이동), IVI < CIRCA (큰 이동).
  이것은 "효율성을 위해 IVI 사용" 권장사항을 검증합니다.
- C8 실패 해석: IVI ≈ CIRCA (모든 조건): CIRCA의 무작위화된 개입이 가치 없음.
  이는 영향 기반 순위 매기기가 충분함을 시사합니다.
- C9 관련 연구: Koh & Liang (2017) 영향 함수 arXiv 1703.04730 — 대기 중 ≥2 출처
- C10 컨텍스트 라우팅: 출처 = deep-research-report.md §IVI. 하위: 17_ALGORITHM_COMPARISON.md
