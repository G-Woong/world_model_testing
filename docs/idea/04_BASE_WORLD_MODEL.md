# 04_BASE_WORLD_MODEL — 기본 World Model

## 출처
- main.md §1 (기본 WM 선택), §4 (encoder + belief + dynamics)
- deep-research-report.md §요약 (TD-MPC2 / Dreamer 권장)

## 주장

TD-MPC2 방식의 decoder-free 잠재 world model이 권장 기반이며, 부분 관측 가능성을 위해
RSSM 방식의 GRU belief memory를 추가합니다. 이것은 기여 주장이 아닙니다 —
이것은 새로운 FGLC 모듈이 작동하는 **기반**입니다.

## 아키텍처

```
상태 encoder (MLP, state-only Phase 1):
  E: x_t ∈ R^{D_x} → z_t = [z_t^1,...,z_t^K] ∈ R^{K×d}
  x_norm = (x - mean_train) / std_train
  E = Linear(D_x→256) → SiLU → LayerNorm → Linear(256→256) → SiLU → Linear(256→K*d)
  Reshape: [K*d] → [K, d]

Belief memory (GRU):
  h_t = GRU(h_{t-1}, [flatten(z_t), a_{t-1}, r_{t-1}])
  h_dim = 256

그룹 상호작용 transformer:
  tokens = [z_t^1,...,z_t^K, action_token, belief_token]
  Z'_t = 2-layer Transformer (d_model=32~64, heads=4)
  주의: 이것은 DYNAMICS INTERACTION layer이며, causal attention이 아님
  
기본 dynamics 사전 분포 (그룹별 MLP + 그룹 상호작용):
  μ_t^k, logσ_t^k = GroupDynamicsMLP_k([Z'_t^k, a_embed, h_embed])
  pθ(z_{t+1}^k | z_t, a_t, h_t) = N(μ_t^k, diag((σ_t^k)²))

보상/가치 헤드:
  r̂_t = Rθ(flatten(z_t), a_t, h_t)
  Q̂_t = Qθ(flatten(z_t), a_t, h_t)
  V̂_t = Vθ(flatten(z_t), h_t)
```

**왜 decoder-free (TD-MPC2 방식)인가?**
- FGLC는 이미지 재구성 잠재가 아닌 action 예측 잠재가 필요합니다
- Decoder-free는 Phase 1에서 픽셀 재구성 오버헤드를 피합니다
- 잠재 planning (MPPI/CEM)이 z 공간에서 직접 작동합니다

**왜 GRU belief를 추가하는가 (RSSM 방식)?**
- 물리적 파라미터 이동(질량/마찰)은 단일 관측으로 보이지 않습니다
- h_t는 여러 타임스텝에 걸쳐 숨겨진 regime의 증거를 축적합니다
- h_t 없이는 β_t gate가 지속적인 dynamics 이동과 일시적 노이즈를 구분할 수 없습니다

## 차별화

| 접근법 | h_t memory | Decoder | 대상 |
|---|---|---|---|
| TD-MPC2 순수 | 없음 | 없음 | 연속 제어 (참조) |
| DreamerV3 | RSSM | Decoder | 픽셀 재구성 + planning |
| FGLC (우리) | GRU belief | 없음 | Falsification-guided correction |

## 연결 맵
- 상위: M-3 (그룹화된 latent), docs/main/main.md §1-4
- 하위: M-7 (불일치는 μ_t,σ_t 사용), M-8 (gate는 h_t 사용), M-9 (attention은 h_t 사용)
- Baselines: TD-MPC2, DreamerV3 (19_BASELINES.md의 직접 비교)

## 체크포인트

- C1 수학적 유효성: PASS — 아키텍처는 표준; 새로운 수학적 주장 없음.
  CONDITIONAL: 그룹 상호작용 transformer는 "dynamics layer"로 올바르게 레이블링됨,
  "causal"이 아님.
- C2 신규성: 해당 없음 — 기본 WM은 표준 구성 요소. 신규성은 FGLC 모듈에 있음.
- C3 Reviewer 공격: 낮음 — 새로운 주장 없음; 설명이 published TD-MPC2/RSSM 문헌과 일치.
- C4 타당성: PASS — TD-MPC2 state-only on ManiSkill: ~2M 파라미터, A100 호환.
  태스크당 Stage 1 학습 ~2시간; 8주 A100 예산 내 실현 가능.
- C5 Claim-지표: 기본 WM 자체에 해당 없음. Stage 1 gate: ID 1단계 NLL ≤ 0.1 nat.
- C6 구현 위험: 낮음 — 표준 MLP/GRU/Transformer 아키텍처, 잘 테스트됨.
- C7 실험 설계: correction 모듈 전에 Stage 1 학습이 필요합니다.
- C8 실패 해석: 기본 WM이 ID dynamics 학습 실패(NLL 감소 안 함)하면
  모든 하위 주장이 무효입니다. Gate: R4 전에 ID NLL 수렴 검사 필요.
- C9 관련 연구: TD-MPC2 (Hansen 2024, arXiv:2310.16828) — 대기 중 ≥2 출처
- C10 컨텍스트 라우팅: 출처 = main.md §1-4. 소비자: 02_FALSIFICATION_THEORY.md,
  05_BELIEF_MEMORY.md, 12_TRAINING_STAGES.md
