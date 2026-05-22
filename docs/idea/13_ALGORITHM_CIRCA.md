# 13_ALGORITHM_CIRCA — 인과 개입 무작위 Conformal Attention

## 출처
- deep-research-report.md §CIRCA (R-9), §이론 점검을 통과하는 알고리즘 골격

## 우선순위: 1 (FGLC의 주요 알고리즘)

## 주장

CIRCA는 주요 FGLC 알고리즘입니다. 다음을 결합합니다:
1. 평균 처치 효과(τ_g) 추정을 위한 **무작위 Bernoulli gate**
2. 보정된 탐지를 위한 **conformal falsification gate**
3. τ_g 효과와 attention을 정렬하는 **α-증류(α-distillation)**
4. 보정된 latent 하에서 action 선택을 위한 **robust MPC**

이것은 5가지 reviewer-2 공격 모두를 가장 직접적으로 다루는 알고리즘입니다:
- 공격 1: τ_g 추정이 개입 검증된 attention 제공
- 공격 2: value-aware 증류가 CIRCA를 순수 residual 어댑터와 구분
- 공격 4: conformal gate가 CIRCA를 이상 탐지와 구분

## 수학적 형식화

```
CIRCA 전체 손실:
  L_CIRCA = L_wm
           + β · L_conf          [conformal 보정]
           + γ · ||α - Norm(τ̂_+)||²  [attention-τ_g 정렬]
           + ρ · ||m||₁          [gate에 대한 희소성]
           - ξ · ΔQ_robust       [가치 개선]

여기서:
  τ̂_g = E[U_t | do(m^(g)=1)] - E[U_t | do(m^(g)=0)]   [평균 처치 효과]
  U_t = -NLL(z_{t+1} | z̃_t) + λQ(z̃_t, a_t)            [유틸리티: 예측 + 가치]
  Norm(τ̂_+)_g = max(0, τ̂_g) / Σ_k max(0, τ̂_k)

학습 알고리즘:
  1. ID 궤적에서 기본 world model pθ와 가치 헤드 Qψ 학습
  2. 잠재 z를 G개 그룹으로 분할; gate-net이 π = σ(a(z, h)) 출력
  3. 무작위 gate 샘플링: m ~ Bernoulli(π); 개입된 z̃ = z + m ⊙ δ 계산
  4. 사실적/개입적 유틸리티 U = -NLL + λQ 계산
  5. 무작위화된 개입에서 그룹 효과 τ̂_g 추정 (IPW 또는 평균 차이)
  6. α가 양의 τ̂_g와 정렬되도록 gate-net 업데이트; 희소성 강제
  7. 보류된 ID 데이터의 잔차 점수 s_t에 대한 conformal/CRC 보정 세트 적합

추론:
  1. s_t ≤ 보정된 임계값이면: 기본 planner 사용 (correction 없음)
  2. 그렇지 않으면 α_t에 의한 top-k 그룹 선택
  3. 선택된 그룹에 대해서만 δ 최적화
  4. 보정된 latent z + m⊙δ 하에서 robust MPC로 action 선택

복잡도: O(BT(C_wm + G) + k·H·C_plan)
  B = 배치 크기, T = horizon, G = 그룹, k = top-k, H = planning horizon
```

## 핵심 속성

| 속성 | CIRCA | 표준 residual | 무작위 gate |
|---|---|---|---|
| 개입 유효성 | τ_g (ATE) | 없음 | 구조적으로 있음 |
| 탐지 보정 | Conformal (유한 샘플) | 없음 | 없음 |
| Action 관련성 | -ξΔQ_robust | 없음 | 없음 |
| Attention 정렬 | τ_g-증류 | 해당 없음 | 해당 없음 |

## 연결 맵
- 상위: R-1 (SCM gate), R-6 (conformal), R-8 (robust MPC), M-9 (α), M-8 (β)
- 알고리즘 동료: 14_ALGORITHM_ASAP.md, 15_ALGORITHM_I3G.md, 16_ALGORITHM_IVI.md
- 하위: 17_ALGORITHM_COMPARISON.md, 11_PLANNING_THEORY.md

## 체크포인트

- C1 수학적 유효성: CONDITIONAL — ATE 추정은 IPW/평균 차이로 양성 + 무관성 하에 유효.
  양성(Positivity): 학습 중 α_t^k ∈ (0,1) 필요 (하드 0/1 아님).
  무관성(Ignorability): m_t^k ~ Bernoulli(π)가 z_t,h_t 컨텍스트에 조건부로 무작위화.
  위험: Bernoulli 샘플링이 잠재 다양체를 방해하면 τ_g 추정이 off-manifold일 수 있음.
- C2 신규성: CONDITIONAL — CIRCA의 조합은 사전 문헌에 없음.
  deep-research-report.md §실무: "현재 공개 문헌에서 동일한 형태로 정리된 예 드뭄."
  하지만 각 구성 요소는 존재함. 신규성 주장: WM 컨텍스트에서 특정 조합.
- C3 Reviewer 공격: 중간 (관리 가능) — τ_g 무작위화가 공격 1 해결.
  Off-manifold 개입 위험 (공격 1 실패 모드): 저랭크 correction 제약이 완화.
- C4 타당성: CONDITIONAL — τ_g 추정이 학습 오버헤드 ~20% 추가.
  IPW 추정기는 단순; DR 추정기는 더 복잡. Phase 1: 평균 차이로 충분.
- C5 Claim-지표: τ_g 유의성 (t-검정 p<0.05/그룹, 500개 OOD 에피소드).
  수준 α에서 보류된 ID의 conformal 커버리지 비율 (주장된 α와 일치해야 함).
- C6 구현 위험: 중간 — 학습 중 Bernoulli 샘플링은 straight-through 추정기 또는
  Gumbel-softmax를 통한 기울기 흐름 필요.
- C7 실험 설계: 동일한 벤치마크에서 CIRCA vs. I3G vs. ASAP vs. IVI 비교.
  모든 알고리즘은 동일한 기본 WM (Stage 1 가중치) 공유.
- C8 실패 해석: 모든 그룹에서 τ_g ≈ 0이면: correction에 개입 유틸리티 없음.
  의미: world model dynamics가 이미 이동 하에서 planning에 충분히 정확.
- C9 관련 연구: Bernoulli gate 개입 이론, CRC (Angelopoulos 2022) — 대기 중 ≥2 출처
- C10 컨텍스트 라우팅: 출처 = deep-research-report.md §CIRCA. 하위: 17_ALGORITHM_COMPARISON.md
