# FGLC

**FGLC: Falsification-Guided Latent Correction for Robotics World Models**
(허위 검증 유도 잠재 공간 보정 기반 로봇공학 세계 모델)

일반적인 로봇공학 world model이 아닙니다.
대상은 falsification-guided latent correction입니다:
표준화된 예측 불일치 → dynamics 가설 위반 감지(falsification)
→ 그룹화된 잠재 하위공간에 대한 causal attention → sparse residual correction
→ necessity/sufficiency 검증 → robust MPC planning.

---

## 핵심 수식

```
pθ(z_{t+1}|z_t,a_t,h_t) = N(μ_t, Σ_t)
ρ_t = Σ_t^{-1/2}(z_{t+1} − μ_t)          [표준화된 예측 불일치]
β_t = FalsificationGate(ρ_t, h_t)          [보정된 β gate]
α_t = CausalAttention(ρ_t, z_t, a_t, ∇Q)  [sparse, value-aware]
μ̃_t^k = μ_t^k + β_t α_t^k δ_t^k         [그룹화된 latent correction]
```

## 현재 상태

- R0: ✅ 계약 초기화 완료 (FRCG-WM → FGLC 피벗)
- R1..R16: 진행 예정 (`docs/ROADMAP/00_ROADMAP_OVERVIEW.md` 참조)

## 패키지

```python
import fglc  # src/fglc/ (스텁 — 전체 구현은 R1+ 이후)
```

## 문서

- 아키텍처: `docs/main/main.md`
- 방법론 조사: `docs/main/deep-research-report.md`
- 아이디어 단위 (44개 원자): `docs/idea/00_OVERVIEW.md`
- 로드맵 (R0..R16): `docs/ROADMAP/00_ROADMAP_OVERVIEW.md`

## 알고리즘

| 알고리즘 | 우선순위 | 핵심 메커니즘 |
|---|---|---|
| CIRCA | 1 | 무작위 Bernoulli gate + conformal + α-distill + robust MPC |
| I3G | 2 | iVAE + ICP/anchor + SPCI gate + sparse group gates |
| ASAP | 3 | Top-k 제안 + MC 개입적 ASV + α-distill |
| IVI | 4 | Influence 순위 + 무작위 knockout + sparse α-distill |

## 벤치마크

**환경**: ManiSkill PickCube/PushCube/LiftCube (state-only → RGB-D)
**OOD 축**: mass × {0.5,1,2} / friction × {0.5,1,2} / latency / noise / action-gain
**전이 검증**: robosuite, DROID, BridgeData V2
