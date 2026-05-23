# 00_OVERVIEW — FGLC 아이디어 탐색 지도

## 한 문장 문제 정의

잠재 world model의 예측 분포가 실제 관측 전이와 통계적으로 불일치할 때 (**falsification 이벤트**),
기존 모델은 잘못된 dynamics 가설을 조용히 지속합니다. FGLC는 이 위반을 감지하고,
**인과화된 attention**을 통해 *어떤* 그룹화된 잠재 하위공간이 planning 실패를 유발하는지
식별하며, **sparse residual correction**을 해당 하위공간에만 적용하고,
necessity/sufficiency/counterfactual rollout으로 검증합니다.

## 핵심 수식 세트

```
pθ(z_{t+1}|z_t,a_t,h_t) = N(μ_t, Σ_t)                   [기본 dynamics 사전 분포]
ρ_t = Σ_t^{-1/2}(z_{t+1} − μ_t)                          [표준화된 불일치]
F_t^k = ||ρ_t^k||₂²,  F_t = Σ_k F_t^k                    [falsification 점수]
β_t = sigmoid(MLP([F_1,...,F_K, F_t, h_t]))               [보정된 gate]
α_t = SparseAttention(ρ_t, z_t, a_t, h_t, ∇_z Q)         [그룹 수준, value-aware]
δ_t^k = tanh(MLP([z_t^k, ρ_t^k, a_t, h_t])) · δ_max      [경계가 있는 correction]
μ̃_t^k = μ_t^k + β_t · α_t^k · δ_t^k                     [보정된 dynamics]
```

## 44개 원자 단위 — M↔R 교차 검증 매트릭스

### main.md 단위 (M-0..M-25)

| ID | 단위 | 핵심 주장 | 연결된 R 단위 |
|---|---|---|---|
| M-0 | 한 문장 문제 정의 | 4개 하위 문제 (감지/국소화/보정/검증) | R-0, R-18 |
| M-1 | 기본 WM 선택 (TD-MPC2 vs Dreamer) | TD-MPC2 decoder-free 하이브리드 권장 | R-11 |
| M-2 | 입력 데이터 구조 | ManiSkill state_dict, T=16~32 학습 horizon | R-13 |
| M-3 | Latent 분해 | K=6 그룹, d=32; 기능적, 의미론적 아님 | R-4 |
| M-4 | Encoder | MLP D_x→256→K*d, LayerNorm, SiLU | R-4 |
| M-5 | Belief memory h_t | GRU on flatten(z)+a+r | R-11 |
| M-6 | 기본 dynamics 사전 분포 | N(μ,diag(σ²)); 그룹 상호작용 transformer | R-4 |
| M-7 | 표준화된 불일치 | ρ_t = (z-μ)/σ; χ²/conformal 보정 | R-7 |
| M-8 | Falsification gate β_t | sigmoid(MLP), 보정됨; 분산 clamp | R-6 |
| M-9 | Causal attention α_t | 그룹 수준, sparse; entmax/sparsemax/top-k | R-0, R-3, R-4 |
| M-10 | Correction 위치 | 전이 어댑터 권장: μ̃=μ+βαδ | R-1, R-9 |
| M-11 | Correction 모듈 Gψ | tanh bounding δ_max; correction 크기 페널티 | R-2 |
| M-12 | Action/value 관련성 | Q 민감도, 정책 KL, cause_score 정렬 | R-8 |
| M-13 | Necessity 손실 | L_nec = max(0, m - (L_without - L_with)) | R-1, R-3 |
| M-14 | Sufficiency 손실 | L_suf = |L_selected - L_full| | R-1, R-3 |
| M-15 | 무작위 마스크 대비 | L_rand = max(0, m - (L_random - L_selected)) | R-1, R-3 |
| M-16 | 전체 손실 (10항) | L_total = L_base + λ1..λ10 항 | — |
| M-17 | 학습 단계 | Stage 1 기본 / Stage 2 동결+보정 / Stage 3 planner | — |
| M-18 | Planner MPPI/CEM | corrected rollout; H_corr=3~5 유지 | R-15..R-17 |
| M-19 | 데이터 분할 | ID + OOD-mass/friction/latency/noise/mixed | R-13 |
| M-20 | 모달리티 진행 | state-only → +RGB → RGB-D → DROID/Bridge | R-13 |
| M-21 | 7개 귀납적 편향 | 그룹화/sparse/경계/시간/액션/nec-suf/OOD | — |
| M-22 | HiP-RSSM/PLSM 차별화 | 파라미터 추론 vs sparse falsification-correction | R-11 |
| M-23 | 아키텍처 스펙 | K=6,d=32,h=256,T=16,H_plan=5-15,δ_max=0.25 | — |
| M-24 | 학습 루프 의사 코드 | Stage-1,Stage-2,개방 루프 rollout | — |
| M-25 | 이론 통합 | F_t,β_t,α_t,μ̃_t 불변식; 최소화 목표 | — |

### deep-research-report.md 단위 (R-0..R-18)

| ID | 단위 | 핵심 통찰 | 연결된 M 단위 |
|---|---|---|---|
| R-0 | Attention-as-explanation 비판 | Jain&Wallace/Grimsley: 외과적 개입 필요 | M-9 |
| R-1 | SCM/do-개입/매개 효과 | Gate m^(g) Bernoulli; τ_g 개입적 효과 | M-10,13,14,15 |
| R-2 | 영향 함수 | Hessian 벡터 곱; 국소 민감도 | M-11 |
| R-3 | Shapley/ASV | 개입적 v(S); 인과 순서 존중 | M-9,13,14,15 |
| R-4 | iVAE/비선형 ICA | Khemakhem: 보조 변수 u 하에서 식별 가능 | M-3,4,6,9 |
| R-5 | ICP/IRM/anchor 회귀 | 불변성 사전 분포; IRM 실용적 실패 사례 | M-22 |
| R-6 | Conformal 예측/CRC | 유한 샘플 커버리지; 온라인 conformal | M-8 |
| R-7 | CUSUM/SPRT/BOCPD | 순차적 변화 탐지; 고전적 baseline | M-7 |
| R-8 | Robust 제어/DRO | Value-aware 손실; Wasserstein 모호성 집합 | M-12 |
| R-9 | CIRCA 알고리즘 | Bernoulli gate + conformal + α-distill + robust MPC | M-10 |
| R-10 | ASAP 알고리즘 | Top-k + MC 개입적 ASV + α-distill | M-9 |
| R-11 | I3G 알고리즘 | iVAE + ICP/anchor + SPCI gate + sparse group gates | M-5,22 |
| R-12 | IVI 알고리즘 | Influence 순위 + knockout + sparse α-distill | M-11 |
| R-13 | 데이터셋 | ManiSkill/robosuite/DROID/BridgeData V2 | M-2,19,20 |
| R-14 | 4축 지표 | 예측/탐지/귀인/행동 | M-22 |
| R-15 | 인과 그래프 | encoder→pred→불일치→트리거→gate→보정→planner | M-18 |
| R-16 | 학습 파이프라인 | base→식별→무작위화→ASV→distill→보정→plan | M-17 |
| R-17 | 추론 결정 흐름 | 보정된 gate→top-k→효과 평가→value 확인→robust MPC | M-18 |
| R-18 | 열린 질문 | 잠재 수술 현실성 / conformal-인과 간격 / action 관련성 | M-0 |

## 탐색 안내

구현 작업 시 다음 순서로 읽습니다:
1. 이 파일 (탐색)
2. `01_PROBLEM_FORMULATION.md` (여기서 시작)
3. `04_BASE_WORLD_MODEL.md` → `02_FALSIFICATION_THEORY.md` → `06_CAUSAL_ATTENTION.md` → `07_CORRECTION_MECHANISM.md`
4. `13_ALGORITHM_CIRCA.md` (주요 알고리즘)
5. `19_BASELINES.md` + `20_ABLATIONS.md` + `21_METRICS.md` (평가)

논문 구성: `22_NOVELTY_AND_THREATS.md` → `25_PAPER_TITLE_CONTRIBUTIONS.md`
체크포인트 요약: `26_CROSSCHECK_SUMMARY.md`

## 체크포인트 상태 (세션 2026-05-22)

클러스터 1 (M-0, R-0, R-18): Agent team T1 리뷰 — 완료 (CONDITIONAL)
클러스터 2 (M-1..M-6, R-4): 대기 중
클러스터 3 (M-7, M-8, R-6, R-7): Agent team T1 리뷰 — 완료 (CONDITIONAL)
클러스터 4 (M-9..M-11, R-1..R-3, R-9..R-12): 대기 중
클러스터 5 (M-12..M-15): 대기 중
클러스터 6 (M-16..M-18, M-23..M-25, R-15..R-17): 대기 중
클러스터 7 (M-19..M-22, R-5, R-8, R-13, R-14): 대기 중

주: 모든 docs/idea/ 파일은 main.md + deep-research-report.md의 스캐폴드 내용을 담고 있습니다.
전체 C1..C10 체크포인트 판정은 클러스터별 agent team 실행이 필요합니다.
