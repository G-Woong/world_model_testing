# Reviewer-2 공격 보고서 — FGLC

**날짜**: 2026-05-22
**에이전트**: reviewer-2-attack-agent (T5 deep mode)
**판정**: ATTACK_MANAGEABLE (공격 관리 가능) — 5가지 주요 공격, 모두 특정 실험으로 방어 가능

## 공격 1 — "Causal" Attention은 인과 어휘로 포장된 상관관계 (주요)

**공격**: α_t = CausalAttention(...)라는 명칭이 정당화되지 않습니다. Jain & Wallace (2019)는
대안적 attention 분포가 동일한 예측을 생성할 수 있음을 보였습니다. 수술적 개입 기준이 정의되지 않습니다.

**방어**: α_t를 학습된 개입 정책으로 재구성, 인과 귀인자가 아닌. CIRCA 방식 추가: 학습 중
m_t^k ~ Bernoulli(α_t^k) 무작위 게이트 사용. τ_g = E[U|do(m^k=1)] - E[U|do(m^k=0)] 추정.
정렬 손실 ||α - Normalize(τ_+)||² 추가. "causal"을 "intervention-policy attention"으로 교체.

**검증**: Jain-Wallace 조작 테스트 (동일한 correction으로 대안적 α' 존재).
do(m^k=1) 하에서 유틸리티 변화의 t-검정, OOD 에피소드 500개, 그룹당 p < 0.05.

## 공격 2 — 이것은 여분의 표기법이 있는 ReDRAW / 잔차 적응 (주요)

**공격**: 핵심 보정 방정식 μ̃_t^k = μ_t^k + β_t α_t^k δ_t^k는 동결된 기반에 적용된 게이팅된 residual 어댑터입니다.
ReDRAW 및 온라인 어댑터 방법이 이미 이것을 수행합니다. FGLC를 "K-헤드 잔차 어댑터 + 불확실성 게이트"와
구별하는 것은 무엇입니까?

**방어**: 구별되는 주장은 correction 형태가 아니라 value 관련성 선택 강제입니다. 표준 잔차 어댑터는
가장 높은 예측 오류가 아닌 planning 관련 하위공간만 선택하는 메커니즘이 없습니다.
L_nec와 L_suf는 이것을 강제합니다. BASE-ReDRAW 기준으로 실행: 동일한 동결 기반, correction 용량 동일,
α 선택 없음, 전체 잔차. 제어 지표에서 FGLC > 이것이면 기여가 실제임.

**검증**: Ablation ABL-no-attention (균일 α=1/K). FGLC > 균일-α (return/recovery),
효과 크기 > 0.3σ, p < 0.05.

## 공격 3 — K=6 그룹화는 자의적이고 의미론적으로 의미 있는 것을 학습하지 않음 (주요)

**공격**: K=6은 아키텍처 편의를 위해 선택됩니다. Locatello et al. (2019): 보조 신호 없이
비지도 disentanglement는 근본적으로 식별 불가능합니다. 그룹 레이블은 학습 후 연구자가 할당한 것입니다.

**방어**: 논문의 설계는 의미론적 ground-truth를 명시적으로 부인합니다: "우리는 latent를 인간이
해석 가능한 진짜 원인명으로 복원하지 않는다." 이것이 올바른 입장으로 논문에 명확히 기술되어야 합니다.
K=6 주장은 기능적이며, 의미론적이 아닙니다. 검증: 시드 간 OOD 유형 조건부 attention 분포의 Spearman 상관.

**검증**: 5개 무작위 시드 전반에서, 각 OOD 유형에 대해 mean attention 벡터 계산. OOD 유형별
attention 벡터의 시드 간 Spearman > 0.7. 또한 K ablation: K=3, 6, 12.

## 공격 4 — Falsification Gate ≡ 이상 탐지 (주요)

**공격**: β_t = sigmoid(MLP([F_t, h_t]))는 표준화된 예측 잔차에 대한 보정된 이상 탐지기를 계산합니다.
이것은 정확히 보정된 이상 탐지기가 하는 일입니다. 센서 노이즈, 적대적 섭동, 진짜 dynamics 이동을 구별하지 않습니다.

**방어**: h_t (GRU belief memory)가 구별 요소입니다. 진짜 falsification 이벤트는 여러 타임스텝에 걸쳐
시간적으로 일관된 높은 β 값을 생성해야 합니다 (regime 지속). 반면 센서 이상은 고립된 스파이크를 생성합니다.
시간적 일관성 지표: OOD vs. ID 노이즈 에피소드 조건부로 5스텝 윈도우에 걸쳐 β_t 자기상관 계산.

**검증**: 다음 하에서 β_t 활성화율 비교: (a) 진짜 OOD 물리 이동, (b) 동일 크기의 추가된 가우시안 관측 노이즈,
(c) 무작위 action 섭동. ID 노이즈에서 오탐율 < 0.2와 함께 진짜 OOD에서 β_t 재현율 > 0.8.

## 공격 5 — 4축 지표 개선 주장이 공동으로 위조 불가능 (주요)

**공격**: Return, 회복 시간, planning 계산 효율성 (계산당 return), 잘못된 가설 지속 시간이 독립적이지 않습니다.
회복 시간과 잘못된 가설 지속 시간은 correction 메커니즘을 감안하면 거의 동어반복입니다.
더 빠르게 correction을 적용하는 모든 모델은 구조적으로 더 짧은 잘못된 가설 지속 시간을 가집니다.

**방어**: 오라클 ground-truth로 지표를 분리하여 구성: 잘못된 가설 지속 시간은 모델이 β_t를 발화한 타임스텝이 아닌
regime이 실제로 변경된 타임스텝에서 측정되어야 합니다. 고정 계산 예산 실험에서 return 보고:
FGLC와 baseline 모두 에피소드당 동일한 총 planning rollout을 매칭받음.

**검증**: 계산 매칭된 무작위 재할당 baseline (CLAUDE.md §Baselines: BASE-COMP-04) 실행.
계산 매칭 하에서 FGLC의 계산당 return 우위가 사라지면 → correction이 아닌 추가 계산에서 이득.
이것이 planning 효율성 주장의 단일 가장 중요한 위조 가능성 테스트입니다.

## 요약

```yaml
rejection_risk: MED (중간 거절 위험)
verdict: ATTACK_MANAGEABLE (공격 관리 가능)
unresolvable_weakness: |
  "Causal" 명칭은 모든 ablation이 통과되더라도 지속적인 skepticism을 유발합니다.
  반드시 "intervention-policy attention"으로 이름을 변경하거나 τ_g 무작위화된 개입 실험을 실행해야 합니다.
highest_priority_experiment: |
  계산 매칭된 baseline (공격 5) — 프로젝트 자체 baseline 계약에서 이미 필수이며,
  그 부재가 현재 설계와 방어 가능한 제출 사이의 가장 명확한 간격입니다.
```

**전체 평가**: 치명적 결함 없음. 5가지 공격 모두 주요하지만 각각 구체적인 실험적 방어가 있습니다.
가장 위험한 공격은 공격 1 (인과 명칭)입니다. 모든 ablation이 통과되더라도 지속되는 용어/구성 문제이기 때문입니다 —
논문은 반드시 τ_g 무작위화된 개입 실험을 실행하거나 메커니즘을 이름 변경하고 재구성해야 합니다.
계산 매칭된 실험 (공격 5)은 프로젝트 자체 계약에서 이미 필수이므로 추가해야 할 가장 중요한 단일 실험입니다.
