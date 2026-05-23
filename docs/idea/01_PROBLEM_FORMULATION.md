# 01_PROBLEM_FORMULATION — 문제 정의

## 출처
- main.md §0 — 한 문장 문제 정의, 4개 하위 문제
- deep-research-report.md §요약, §attention을 explanation에서 intervention으로 바꾸는 것

## 주장

현재의 잠재 world model은 **잘못된 dynamics 가설의 지속** 문제를 겪습니다: 물리적 파라미터가
이동할 때(질량/마찰/지연/노이즈/액션-게인), 모델은 잘못된 dynamics 분포에서 예측을 계속
생성하고, planning이 조용히 저하됩니다.

FGLC는 네 가지 연결된 하위 문제를 다룹니다:
1. **현재 world model이 틀렸는가?** → 표준화된 불일치 + falsification gate
2. **잠재 공간의 어느 부분이 틀렸는가?** → 인과화된 그룹 수준 attention
3. **얼마나 많은 보정이 필요한가?** → 경계가 있는 sparse residual correction 모듈
4. **보정이 실제로 planning에 도움이 되는가?** → Value/return 개선 검증

## 수학적 형식화

```
정의: z_t = [z_t^1,...,z_t^K] ∈ R^{K×d}  [K=6 그룹화된 잠재 토큰]
     pθ(z_{t+1}|z_t,a_t,h_t) = N(μ_t, diag(σ_t²))  [기본 dynamics 사전 분포]
     ρ_t = Σ_t^{-1/2}(z_{t+1} - μ_t)  [표준화된 불일치]

Falsification 이벤트: ||ρ_t||²가 보정된 ID 분포 임계값을 초과
목표: sparse α_t ∈ Δ^K (K 그룹에 대한 attention)와 δ_t^k (보정)를 찾아
     μ̃_t = μ_t + β_t Σ_k α_t^k δ_t^k가 value 개선을 최대화하도록 함
     subject to ||α||_0 ≤ k (희소성)와 ||δ^k|| ≤ δ_max (경계)
```

**Attention-as-explanation과의 핵심 차이점**: 표준 attention(Jain & Wallace 2019)은
인과적이라고 주장할 수 없습니다. FGLC의 attention α_t는 **correction gate 정책**으로,
어느 잠재 그룹에 개입할지 지정합니다. 인과성은 necessity/sufficiency/counterfactual
손실로 검증되며, attention 가중치 자체만으로는 부족합니다.
(Grimsley 등: 외과적 개입이 필요)

## 연결 맵
- 상위: docs/main/main.md §0 (출처)
- 하위: M-7 (불일치), M-8 (β gate), M-9 (attention), M-10..M-11 (correction)
- 알고리즘: R-9 (CIRCA), R-1 (SCM/do-개입)

## 체크포인트

- C1 수학적 유효성: **CONDITIONAL** — Attention-인과성 혼용 위험.
  main.md §4.3의 그룹 상호작용 블록은 "dynamics interaction layer, NOT causal attention"으로
  명시됩니다. 문제 설명은 (a) 불일치 점수가 그룹 위치를 결정 (F_t^k 순위)과
  (b) correction gate가 residual을 적용하는 것을 명확히 분리해야 합니다.
  에이전트 보고서: mathematical-validity-critic 결과 2026-05-22 참조
- C2 신규성: 대기 중 (클러스터 리뷰 필요 — 22_NOVELTY_AND_THREATS.md 참조)
- C3 Reviewer 공격: 대기 중 (reviewer-2-attack-agent 완료)
- C4 타당성: CONDITIONAL — ManiSkill state-only Phase 1은 단일 A100에서 실현 가능;
  모달리티 확장(RGB-D, DROID)은 Phase 2+가 필요합니다.
  첫 제출 주장을 위해서는 state-only baseline으로 충분합니다.
- C5 Claim-지표 정렬: CONDITIONAL — 4개 하위 문제 각각이 지표 축에 매핑됨
  (예측 NLL / 탐지 AUROC / attention necessity-sufficiency / return recovery).
  4개 모두 함께 측정해야 합니다; NLL만으로는 주장 증거로 불충분합니다.
- C6 구현 위험: 대기 중
- C7 실험 설계: 대기 중
- C8 실패 해석: 23_FAILURE_MODES.md에 두 가지 핵심 실패 모드 문서화:
  (a) correction 모듈이 너무 강함 → 기본 WM이 학습 안 됨; (b) attention = 지름길.
- C9 관련 연구: 대기 중 (MCP 교차 검증 필요)
- C10 컨텍스트 라우팅: 출처 = main.md §0, deep-research-report.md §요약.
  하위 소비자: 02_FALSIFICATION_THEORY.md, 06_CAUSAL_ATTENTION.md,
  07_CORRECTION_MECHANISM.md, 09_NECESSITY_SUFFICIENCY.md.

## 열린 질문
- R-18: 잠재 수술이 유효한 표현 다양체 위에 머무는가?
- R-18: 인과적 주장에 대한 conformal 커버리지를 동시에 유지할 수 있는가?
- R-18: action 관련 변화를 일으키는 최소 correction 크기는 얼마인가?
