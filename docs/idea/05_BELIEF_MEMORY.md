# 05_BELIEF_MEMORY — Belief Memory (h_t)

## 출처
- main.md §4.2 (belief memory h_t)
- deep-research-report.md §I3G 알고리즘 (R-11), HiP-RSSM 비교

## 주장

GRU 기반 belief memory h_t는 지속적인 dynamics 이동 감지에 필수적입니다.
시간적 컨텍스트 없이, β_t는 일회성 노이즈 스파이크(ID)와 10+ 스텝 동안 지속될
regime 변화(OOD 질량/마찰/액션-게인)를 구분할 수 없습니다.

## 수학적 형식화

```
h_t = GRU(h_{t-1}, [flatten(z_t), a_{t-1}, r_{t-1}])

입력 차원: K*d + D_a + 1 = 192 + 7 + 1 = 200
은닉 차원: h_dim = 256
출력: h_t ∈ R^256

사용처:
  β_t = sigmoid(MLP([F_1,...,F_K, F_total, h_t]))   [falsification gate]
  α_t = SparseAttention(ρ_t, z_t, a_t, h_t, ∇Q)    [correction attention]
  δ_t^k = tanh(MLP([z_t^k, ρ_t^k, a_t, h_t]))       [correction 모듈]
```

**물리적 정당성**: 숨겨진 regime 속성(질량, 마찰)은 단일 관측에서 추론할 수 없습니다.
여러 관측이 필요합니다:
- 컵 무게: 밀기 → 느끼기 → 믿음 업데이트
- 마찰 변화: 여러 스텝에 걸친 미끄러짐 거리

h_t는 DreamerV3의 RSSM 결정론적 상태와 동일한 역할을 하지만,
전체 이미지 재구성(decoder)이 필요하지 않습니다(decoder-free 설계).

## HiP-RSSM 비교

HiP-RSSM (Achterhold et al. 2022)은 잠재 파라미터가 다양한 역학 시스템을 인코딩하는
컨텍스트 조건부 RSSM을 사용합니다. 핵심 차이점:
- HiP-RSSM: 어떤 dynamics family가 적용되는지 파라메트릭 추론
- FGLC: belief h_t가 증거를 축적; β_t gate가 falsification 발생 여부를 결정;
  α_t가 correction이 적용될 위치를 결정. 명시적 파라미터 추론 없음.

## 연결 맵
- 상위: M-4 (encoder), M-6 (dynamics는 h_t 입력으로 μ_t,σ_t 생성)
- 하위: M-8 (β_t gate), M-9 (α_t attention), M-11 (correction δ_t), R-11 (I3G context)
- Baselines: HiP-RSSM (파라미터 추론 vs. belief 축적 비교)

## 체크포인트

- C1 수학적 유효성: PASS — GRU는 표준; h_t 차원은 처리 가능합니다.
- C2 신규성: 해당 없음 — GRU belief는 표준. 신규성은 h_t 사용 방식에 있음.
- C3 Reviewer 공격: 낮음 — 잘 확립된 구성 요소. 주요 공격은 "RSSM 확률적
  구성 요소가 더 나을 수 있다" (방어 가능: decoder-free RSSM 확률적은 더 복잡하여 R11로 연기).
- C4 타당성: PASS — 256차원 GRU, 표준.
- C5 Claim-지표: C5-CONDITIONAL — β_t 자기상관을 OOD regime 이동 하에서 > 0.6으로
  보여야 함 (공격 4 reviewer-2 방어). h_t가 이 시간적 컨텍스트를 제공합니다.
- C6 구현 위험: 낮음
- C7 실험 설계: Ablation: belief-less β_t (h_t 없이 ρ_t만 사용).
  가설: h_t 없이 ID 노이즈에서 오탐율이 크게 증가합니다.
- C8 실패 해석: h_t가 구별에 도움이 안 되면, regime 이동이 단일 스텝 ρ_t만으로
  탐지 가능함을 시사합니다 (큰 이동에 가능). 치명적이지 않음.
- C9 관련 연구: HiP-RSSM arXiv 2206.14697 — 대기 중 ≥2 출처
- C10 컨텍스트 라우팅: 출처 = main.md §4.2. 하위: 02_FALSIFICATION_THEORY.md,
  06_CAUSAL_ATTENTION.md.
