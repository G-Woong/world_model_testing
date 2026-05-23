# 09_NECESSITY_SUFFICIENCY — 필요성과 충분성

## 출처
- main.md §11 (necessity/sufficiency 검증)
- deep-research-report.md §SCM/do-개입 (R-1), §Shapley/ASV (R-3)

## 주장

Attention 가이드 correction은 필요성, 충분성, 무작위 마스크 대비 손실을 통해
부분적으로 검증될 수 있습니다. 이것은 인과적 식별 가능성을 증명하지 않지만
**개입 수준 검증**을 구성합니다: 선택된 마스크가 (a) 성능에 필요하고,
(b) 단독으로 거의 완전한 correction 성능에 충분하며, (c) 무작위 선택보다 나음을 보입니다.

## 수학적 형식화

```
정의:
  L_with    = 선택된 correction 후 예측/value 손실 (α에 의한 top-k)
  L_without = 선택된 correction이 제거된 예측/value 손실
  L_full    = 모든 그룹 보정 후 예측/value 손실
  L_random  = 무작위 k 그룹 보정 후 예측/value 손실
  m_selected = α_t에 의한 top-k 그룹 (correction 마스크)

필요성 (Necessity):
  L_nec = max(0, margin - (L_without - L_with))
  목표: L_without > L_with  →  선택된 그룹 제거 시 성능 저하
  
충분성 (Sufficiency):
  L_suf = |L_selected - L_full|
  목표: L_selected ≈ L_full  →  선택된 그룹만으로 대부분의 이점 획득

무작위 대비 (Random contrast):
  L_rand = max(0, margin - (L_random - L_selected))
  목표: L_selected < L_random  →  무작위 그룹 선택보다 나음

학습 스케줄:
  Stage 1: 기본 WM만 (nec/suf 없음)
  Stage 2: L_nec + L_suf + L_rand 추가
  (필요성/충분성 손실은 기본 WM이 어느 정도 학습된 후에 필요)
```

**한계**: L_nec는 선택된 그룹이 필요함(제거되면 성능 저하)을 검증합니다.
L_suf는 선택된 그룹이 충분함을 검증합니다. 하지만 이것은 α_t가
*인과적으로 올바른* 그룹을 식별했다는 것을 증명하지 않습니다 — 개입이 효과적이라는 것만을.
진정한 인과 식별에는 ground-truth 팩터 접근(시뮬레이션에서 물리적 파라미터 할당을 통해 가능)이나
무작위화된 τ_g 추정(CIRCA)이 필요합니다.

## 연결 맵
- 상위: M-9 (α_t 선택), M-10 (correction δ_t), M-12 (value 관련성)
- 하위: M-16 (전체 손실에 L_nec+L_suf+L_rand 포함)
- 알고리즘: R-1 (SCM necessity는 ~τ_g > 0), R-3 (Shapley sufficiency 해석)
- 지표: 21_METRICS.md §귀인 축

## 체크포인트

- C1 수학적 유효성: PASS — L_nec, L_suf, L_rand는 잘 정의된 힌지/절대값 손실입니다.
  Margin 항은 학습 가능한 임계값이 아닌 하이퍼파라미터입니다.
- C2 신규성: CONDITIONAL — Attention에 대한 necessity/sufficiency 테스트가 제안된 바 있음.
  새로운 측면: 평가 테스트만이 아닌 학습 손실로 적용 (WM 컨텍스트에서).
- C3 Reviewer 공격: 중간 — "Necessity/sufficiency는 인과적 귀인을 증명하지 않는다."
  방어 (문서화됨): 이것은 개입 수준 검증이며, 인과 증명이 아닙니다.
  시뮬레이션 ground-truth는 추가 검증을 위한 인과 오라클을 제공합니다
  (변경된 팩터 대비 마스크 정밀도/재현율).
- C4 타당성: PASS — 세 가지 손실 모두 표준 미분 가능 연산입니다.
- C5 Claim-지표: 21_METRICS.md §귀인 축의 Necessity-Δ, Sufficiency-Δ, Random-Δ.
  또한: OOD 조건에서 선택된 마스크가 Necessity-Δ > 0.2, Sufficiency-Δ < 0.1을 달성하는 것 정량화.
- C6 구현 위험: 낮음
- C7 실험 설계: 필수: 각 지표 정량화. 선택된 마스크가
  OOD 조건에서 Necessity-Δ > 0.2, Sufficiency-Δ < 0.1을 달성하는 것 보여야 함.
- C8 실패 해석: L_without ≈ L_with이면 (필요성 실패): 선택이 중복적.
  L_selected << L_full이면 (충분성 실패): 선택된 그룹 불충분, k가 너무 작음.
- C9 관련 연구: Jain & Wallace 제거 기반 평가; Shapley (Frye 2020 ASV) — 대기 중
- C10 컨텍스트 라우팅: 출처 = main.md §11. 하위: 10_LOSS_DESIGN.md, 21_METRICS.md
