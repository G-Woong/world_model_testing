# 14_ALGORITHM_ASAP — 비대칭 Shapley Attention Planning

## 출처
- deep-research-report.md §ASAP (R-10), §Shapley·removal-based·ASV (R-3)

## 우선순위: 3

## 주장

ASAP는 top-k attention을 빠른 제안 엔진으로 사용하고, 최종 correction 점수를
Monte Carlo 개입적 비대칭 Shapley Values (ASV)로 계산합니다. ASV는 잠재 그룹 간
인과 순서를 존중합니다(예: context → dynamics → reward). 계산 비용이 높지만
상호작용 효과에 대한 가장 강력한 형식적 보증을 제공합니다.

## 수학적 형식화

```
개입적 가치 함수:
  v(S) = E[-NLL(S) + λQ(S)]   S = 보정된 그룹 집합

비대칭 Shapley Value:
  φ_i^ASV = ordered-Shapley(v)  [그룹의 인과 순서 존중]
  (허용되지 않는 순서는 연합 평균에서 제외)

ASAP 학습:
  1. World model과 planner/가치 헤드 학습
  2. Gate-net이 attention을 통해 top-k 잠재 그룹 제안
  3. top-k에 대해서만: v(S)를 사용한 개입적 ASV의 Monte-Carlo 추정
  4. 정규화된 ASV를 attention α에 증류
  5. Correction 전에 불일치에 conformal gate 사용

ASAP 추론:
  1. 보정된 불일치에서 트리거
  2. top-k 그룹에 대한 소예산 ASV 재계산
  3. 양의 ASV와 충분한 효과 크기를 가진 그룹만 보정

복잡도: O(2^k · n_mc) 여기서 k = top-k 선택, n_mc = MC 샘플
  실용적: k=2~3, n_mc=20 → O(4~8 × 20) = 80~160 순방향 패스/스텝
  → planning 시간 척도에 적합, 실시간 정책에는 부적합
```

## ASAP가 CIRCA를 능가하는 경우

ASAP는 상호작용 효과를 포착합니다: "그룹 2와 4가 함께 이동을 유발하며, 개별적으로는 아님."
CIRCA는 그룹당 한계적 τ_g를 추정합니다 (상호작용을 놓칠 수 있음).
예상 우위: 여러 그룹이 동시에 이동하는 조건
(예: OOD-mixed: 질량 + 마찰 + 액션-게인 동시).

## 연결 맵
- 상위: R-3 (Shapley/ASV), M-9 (attention α), R-6 (conformal gate)
- 알고리즘 동료: 13_ALGORITHM_CIRCA.md, 15_ALGORITHM_I3G.md, 16_ALGORITHM_IVI.md
- 하위: 17_ALGORITHM_COMPARISON.md

## 체크포인트

- C1 수학적 유효성: CONDITIONAL — 인과 순서가 있는 ASV는 알려진 인과 그래프 필요.
  잠재 그룹 간 인과 순서(z^1=고유감각 → z^2=물체 → z^3=접촉)는 가정이며, 도출된 것 아님.
  잘못된 순서는 잘못된 ASV를 줍니다. 위험: 인과 순서가 모호하면 ASV가 표준 Shapley로 축소.
- C2 신규성: CONDITIONAL — RL/WM 컨텍스트에서 개입적 Shapley는 비교적 새로움.
- C3 Reviewer 공격: 높음 — "실제 배포에 너무 비쌈."
  방어: ASAP는 상호작용 효과를 이해하기 위한 연구 비교용; CIRCA가 배포 가능한 알고리즘.
- C4 타당성: CONDITIONAL — k=2, n_mc=20: planning 시간에 실현 가능.
  k=4, n_mc=50: ~250 순방향 패스/스텝; 빠른 조작(>30Hz)에는 너무 느림. 배치 평가만 가능.
- C5 Claim-지표: ASV 값이 OOD 조건별 그룹 중요도 점수 제공.
  CIRCA τ_g와 비교: 동의하는가? 불일치 = 상호작용 효과 존재.
- C6 구현 위험: 중간 — MC Shapley 추정 + ASV를 통한 기울기 전파.
- C7 실험 설계: 병렬 비교: OOD-mixed 조건에서 CIRCA vs. ASAP.
  가설: ASAP > CIRCA, 특히 다중 팩터 OOD 하에서.
- C8 실패 해석: ASAP ≈ CIRCA (모든 조건): 상호작용이 약함; Shapley 오버헤드 불필요.
  ASAP 역할을 ablation만으로 축소.
- C9 관련 연구: Frye et al. (2020) ASV; Shapley+RL — 대기 중 ≥2 출처
- C10 컨텍스트 라우팅: 출처 = deep-research-report.md §ASAP. 하위: 17_ALGORITHM_COMPARISON.md
