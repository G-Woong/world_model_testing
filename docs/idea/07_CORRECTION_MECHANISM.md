# 07_CORRECTION_MECHANISM — Correction 메커니즘

## 출처
- main.md §8 (correction 위치), §9 (correction 모듈)
- deep-research-report.md §SCM/do-개입/매개 효과 (R-1)

## 주장

Correction은 z_t를 직접 수정하는 것이 아니라 **전이 예측**(μ_t)에 적용됩니다.
이것은 "전이 어댑터" 패턴입니다: 기본 WM이 H0 예측을 제공하고;
correction 모듈이 조건부 residual을 제공합니다. 최종 보정된 예측은:
μ̃_t^k = μ_t^k + β_t · α_t^k · δ_t^k

이것은 사후 잠재 공간 편집이 아닙니다 — falsification이 감지될 때 추론 시 적용되는
**조건부 residual**로, β_t로 게이팅되고, α_t로 선택됩니다.

## 수학적 형식화

```
세 가지 correction 위치 선택지:
  (a) 현재 latent:    z̃_t = z_t + α_t ⊙ δ_t     [상태 추정 보정]
  (b) 다음 예측:      μ̃_t = μ_t + α_t ⊙ δ_t     [dynamics 예측 보정]
  (c) 전이 어댑터:    μ̃_t = fθ(z_t,a_t,h_t) + α_t ⊙ gψ(z_t,ρ_t,a_t,h_t)

권장: 선택지 (c) 전이 어댑터

그룹 k별 correction 모듈:
  δ_t^k = Gψ^k(z_t^k, ρ_t^k, a_t, h_t)
         = δ_max · tanh(MLP([z_t^k, ρ_t^k, a_t, h_t]))
  
  MLP: Linear(d_z+d_rho+d_a+d_h → 128) → SiLU → LayerNorm → Linear(128→128) → SiLU → Linear(128→d)

최종 보정된 예측:
  μ̃_t^k = μ_t^k + β_t · α_t^k · δ_t^k
  
  β_t:    falsification gate   (보정 여부)
  α_t^k:  그룹 선택            (어느 그룹을 보정할지)
  δ_t^k:  correction 벡터      (그룹당 얼마나 보정할지)

경계 설정:
  tanh는 ||δ_t^k|| ≤ δ_max를 보장 (correction 모듈이 기본 WM을 지배하는 것 방지)
  δ_max = 0.1 ~ 0.5 latent std (초기값: 0.25)

Correction 크기 페널티:
  L_corr_size = Σ_k ||α_t^k · δ_t^k||₂²
  (correction이 모든 기본 WM 예측 오류를 흡수하는 것 방지)
```

## 왜 전이 어댑터 > z_t 직접 편집인가

선택지 (a): 현재 상태 belief를 편집 — encoder z_t가 이미 잘 보정된 경우 불안정.
선택지 (b): 다음 예측만 편집 — h_t에 축적된 지속적인 regime 컨텍스트를 놓침.
선택지 (c): 전체 전이 어댑터: 기본 WM이 H0 참조로 보존됨; correction 모듈이
조건부 residual을 캡처. NLP 미세 조정의 어댑터 레이어와 유사.

## 연결 맵
- 상위: M-8 (β_t gate), M-9 (α_t attention), M-6 (μ_t 기본 예측)
- 하위: M-12 (value 관련성이 δ를 검증), M-13..M-15 (nec/suf/contrast)
- 알고리즘: R-1 (SCM: δ는 매개 gate에 대한 개입), R-9 (CIRCA correction 경로)

## 체크포인트

- C1 수학적 유효성: PASS — tanh bounding + β_t · α_t^k · δ_t^k 공식은 잘 정의됨.
  correction 크기 페널티는 유효한 정규화기. 수학적 불일치 없음.
- C2 신규성: CONDITIONAL — ReDRAW 비교가 중요 (공격 2 reviewer-2 참조).
  차이점: L_nec + L_suf + value-aware 선택 vs. 균일 residual 어댑터.
- C3 Reviewer 공격: 중간 — 공격 2: "이것은 ReDRAW다."
  방어는 BASE-ReDRAW baseline 실행 + FGLC > 균일-α ablation (제어 지표)을 필요로 함.
- C4 타당성: PASS — 그룹별 MLP correction은 가벼움 (~50k 파라미터/그룹).
- C5 Claim-지표: Correction은 다음으로 검증됨: ABL-no-attention, ABL-no-correction,
  necessity (L_without - L_with > margin), sufficiency (L_selected ≈ L_full).
- C6 구현 위험: 낮음 — 표준 MLP 아키텍처; tanh bounding 잘 이해됨.
- C7 실험 설계: 필수 ablation: no-correction (기본 WM만), no-attention
  (균일 α), no-falsification-gate (always-correct).
- C8 실패 해석: 실패 모드 1: correction이 너무 강함 → 기본 WM이 학습 안 됨.
  완화: L_corr_size + δ_max clamp + staged 학습 (Stage 2에서 base 동결).
- C9 관련 연구: ReDRAW (residual WM), AdaWM — 대기 중 ≥2 출처
- C10 컨텍스트 라우팅: 출처 = main.md §8-9. 하위: 09_NECESSITY_SUFFICIENCY.md,
  10_LOSS_DESIGN.md, 11_PLANNING_THEORY.md
