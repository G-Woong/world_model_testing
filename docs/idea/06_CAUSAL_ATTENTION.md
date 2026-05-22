# 06_CAUSAL_ATTENTION — Causal Attention (인과 Attention)

## 출처
- main.md §7 (커스텀 attention 설계)
- deep-research-report.md §R-0 (attention 비판), §R-3 (Shapley/ASV), §R-9 (CIRCA)

## 주장

Correction attention α_t는 **개입 정책**(인과적 귀인자가 아님)입니다.
높은 α_t^k는 "그룹 k에 개입하면 실제로 planning 유틸리티가 바뀐다"는 것을 의미하며,
무작위화된 개입 실험(τ_g 유틸리티 효과 추정)으로 검증됩니다.
표준 softmax attention과 작동적으로 구별 가능합니다.

**용어 결정**: reviewer-2-attack-agent 공격 1에 따라, "causal attention"이라는 용어는
반드시 "intervention-policy attention"(개입 정책 attention)으로 이름을 바꾸거나,
전체 τ_g 무작위화된 개입 실험(CIRCA 방식)으로 뒷받침되어야 합니다.
논문은 이 두 경로 중 하나를 선택해야 합니다.

## 수학적 형식화

```
Correction attention 쿼리:
  context_t = [flatten(ρ_t), flatten(σ_t), a_embed, h_t, value_signal, history_embed]
  
그룹 토큰 키:
  group_token_k = concat(z_t^k, ρ_t^k, σ_t^k)
  K_k = W_K @ group_token_k
  
쿼리:
  q = W_Q @ context_t

원시 attention 가중치:
  ẽ_k = q · K_k / sqrt(d)
  
Sparse attention (권장 진행 단계):
  Phase 1: α_k = softmax(ẽ) + L_entropy 페널티
  Phase 2: entmax/sparsemax(ẽ)  [비선택 그룹에 대한 정확한 0]
  Phase 3: top-k Gumbel mask  [하드 선택]

개입 정책 공식화 (CIRCA 방식, 유효성 방어용):
  m_t^k ~ Bernoulli(α_t^k)   [학습 중: 무작위화된 gate]
  τ̂_g = E[U_t|do(m^k=1)] - E[U_t|do(m^k=0)]  [IPW 또는 DR로 추정]
  L_alignment = ||α - Normalize(τ̂_+)||²   [양의 유틸리티 효과와 attention 정렬]
```

## Attention-as-Explanation 비판 (Jain & Wallace 2019)

표준 attention은 세 가지 인과적 기준을 충족하지 못합니다 (Grimsley 등):
1. 다른 attention 분포 → 동일한 예측 (고유하지 않음)
2. 높은 attention 토큰 제거 → 작은 효과 (필요하지 않음)
3. 외과적 개입이 정의되지 않음

FGLC의 응답: α_t는 예측을 설명하는 것이 아니라, 보정 개입을 선택합니다.
L_nec 손실은 필요성을 검증합니다. L_suf 손실은 충분성을 검증합니다.
τ_g 추정은 높은 α 그룹이 양의 개입 유틸리티를 가짐을 검증합니다.
이들이 함께 작동적으로 검증된 개입 정책을 구성합니다, 단순한 attention이 아닙니다.

## 연결 맵
- 상위: M-7 (ρ_t 입력), M-8 (β_t가 attention 게이팅), R-0 (attention 비판), R-3 (Shapley)
- 하위: M-10 (correction은 α_t 사용), M-13..M-15 (nec/suf/contrast는 α_t 사용)
- 알고리즘: R-9 (CIRCA가 τ_g 추정 추가), R-10 (ASAP가 ASV 추정 추가)

## 체크포인트

- C1 수학적 유효성: CONDITIONAL — Attention 공식은 유효하지만 "causal" 레이블은
  τ_g 무작위화된 개입 실험 없이는 수학적으로 정당화되지 않습니다.
  필수: CIRCA 방식의 τ_g 학습 추가 또는 이름 변경. 수학적 유효성 비평가 보고서 참조.
- C2 신규성: CONDITIONAL — 보정을 위한 sparse attention은 단독으로 새롭지 않습니다.
  개입 정책 구성 + L_nec/L_suf + τ_g 정렬이 차별화 요소입니다.
  확인: world model 컨텍스트에서 세 가지 모두를 결합한 선행 연구 없음.
- C3 Reviewer 공격: 높음 — 공격 1 (causal attention 비판)이 가장 위험한 공격입니다.
  방어에는 τ_g 실험 또는 용어 변경이 필요합니다. reviewer2_attack_fglc_R1.md 참조.
- C4 타당성: CONDITIONAL — entmax/sparsemax는 라이브러리로 사용 가능;
  top-k Gumbel은 커스텀 구현 필요. τ_g 추정은 ~20% 학습 오버헤드 추가. 실현 가능.
- C5 Claim-지표: Attention 주장은 다음으로 검증됨:
  (1) necessity 테스트 (그룹 선택 AUROC), (2) sufficiency 테스트,
  (3) τ_g 유의성 (그룹별 p<0.05), (4) Jain-Wallace 적대적 테스트.
- C6 구현 위험: 중간 — entmax 라이브러리 의존성; Gumbel-softmax 기울기 안정성.
- C7 실험 설계: 필수: ABL-no-attention (균일 α=1/K).
  FGLC > 균일-α가 return/recovery에서 효과 크기 > 0.3σ임을 보여야 합니다.
- C8 실패 해석: ABL-no-attention이 FGLC와 동등하면: attention 모듈이 아무것도 추가 안 함.
  의미: 주장은 그룹 선택 없는 "게이팅된 residual correction"으로 축소됩니다.
- C9 관련 연구: Jain & Wallace (2019), Wiegreffe & Pinter (2019), entmax (Peters et al.) — 대기 중
- C10 컨텍스트 라우팅: 출처 = main.md §7, deep-research-report.md §R-0,R-3.
  하위: 07_CORRECTION_MECHANISM.md, 13_ALGORITHM_CIRCA.md
