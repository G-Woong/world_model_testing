# 17_ALGORITHM_COMPARISON — 4가지 알고리즘 비교

## 출처
- deep-research-report.md §이론 점검을 통과하는 알고리즘 골격, §우선순위

## 주장

4가지 FGLC 알고리즘(CIRCA, I3G, ASAP, IVI)은 개입 유효성/통계적 보정/action 관련성/
계산 비용 공간에서 서로 다른 지점을 커버합니다. 4가지 모두 동일한 Stage 1 기본 WM 가중치를
공유하는 동일한 벤치마크에서 비교되어야 합니다.

## 4가지 알고리즘 교차표

| 속성 | CIRCA | ASAP | I3G | IVI |
|---|---|---|---|---|
| 우선순위 | 1 | 3 | 2 | 4 |
| 개입 유효성 | 강함 (τ_g ATE) | 강함 (ASV 연합) | 중간~강함 (iVAE+ICP) | 중간 (국소 영향) |
| 통계적 보정 | Conformal (유한 샘플) | Conformal | SPCI/CUSUM | 보정된 gate |
| Action 관련성 | 있음 (robust MPC -ξΔQ) | 있음 (개입적 v(S)) | 있음 (value-aware planner) | 있음 (value-aware 손실) |
| 계산 비용 | 중간 | 높음 | 중간~높음 | 낮음 |
| 예상 우위 | 탐지+회복 | 다중 팩터 OOD | 시뮬레이션 귀인 | 실시간 배포 |
| 핵심 약점 | Off-manifold 개입 | 실시간에 너무 느림 | u_t 보조 변수 필요 | 큰 이동에 취약 |

## 알고리즘 선택 안내

```
배포 시나리오:
  연구 이해 + 인과 귀인 → I3G (가장 강한 식별 가능성)
  높은 정확도 + 시간 예산 → ASAP (가장 강한 연합 상호작용)
  주요 방법 (논문 주장) → CIRCA (균형: 유효성+보정+action)
  실시간 / 낮은 계산 → IVI

벤치마킹 요구사항:
  4가지 알고리즘 모두 동일한 Stage 1 기본 WM 가중치 공유
  Stage 2 학습: 알고리즘별 (CIRCA는 τ_g, ASAP는 ASV 등)
  평가: 동일한 지표 세트 (21_METRICS.md §4축 지표)
```

## 예상 실험 결과

deep-research-report.md §실험 설계와 벤치마크 §알고리즘별 기대 결과 기반:

| 시나리오 | 최고 | 2위 | 3위 | 최하 |
|---|---|---|---|---|
| 탐지+회복 곡선 | CIRCA | I3G | IVI | ASAP |
| 상호작용 집약적 OOD-mixed | ASAP | CIRCA | I3G | IVI |
| 귀인 정밀도 (시뮬레이션 오라클) | I3G | CIRCA | ASAP | IVI |
| 계산 효율성 (return/compute) | IVI | CIRCA | I3G | ASAP |
| 큰 이동 (2× 질량) | CIRCA | I3G | ASAP | IVI |

## 연결 맵
- 상위: 13,14,15,16 (4가지 알고리즘 모두)
- 하위: 19_BASELINES.md, 20_ABLATIONS.md, 21_METRICS.md
- 논문: 25_PAPER_TITLE_CONTRIBUTIONS.md (CIRCA = 주요 기여)

## 체크포인트

- C1 수학적 유효성: 해당 없음 — 예상 결과 예측, 수학적 주장 아님.
- C2 신규성: CONDITIONAL — 4가지 알고리즘 비교 프레임워크 자체가 기여
  (WM correction에서 개입 유효성/보정 트레이드오프의 체계적 연구).
- C3 Reviewer 공격: 중간 — "왜 모든 것에 ASAP를 사용하지 않는가?"
  방어: ASAP는 실시간에 너무 비쌈; CIRCA가 배포 가능한 알고리즘.
- C4 타당성: CONDITIONAL — 3가지 태스크 × 5가지 OOD 조건에서 4가지 알고리즘 모두 실행:
  ~4 알고리즘 × 3 태스크 × 5 OOD = 60개 평가 실행. 상당한 계산.
  계획: CIRCA+IVI 먼저 실행; 예산이 허용되면 ASAP+I3G 추가.
- C5 Claim-지표: 4가지 모두 동일한 4축 지표 세트에서 평가되어야 함.
- C6 구현 위험: 높음 — 공유 기반에서 4가지 별도 학습 절차. 버전 관리 필요.
- C7 실험 설계: 공유 Stage 1 → 알고리즘별 Stage 2 → 동일한 평가 프로토콜.
- C8 실패 해석: CIRCA < IVI (모든 조건): 무작위화된 개입이 오버헤드 없이 이점 없음.
  IVI + CIRCA (2가지 알고리즘 비교)로 축소.
- C9 관련 연구: 해당 없음 (비교 섹션)
- C10 컨텍스트 라우팅: 출처 = deep-research-report.md §우선순위.
  소비자: 25_PAPER_TITLE_CONTRIBUTIONS.md, 19_BASELINES.md
