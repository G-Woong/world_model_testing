# novelty-relevance-critic 보고서 — Step 11-D7 Scaled (450ep) R1

**보고일**: 2026-05-24
**단계**: Scaled Stage 2 (실측, Post-Scaled)
**판정**: CONDITIONAL_PASS (mass OOD 신뢰성 저하)

---

## 업데이트된 6개 질문 답변

### Q1. mass/friction shift가 physical dynamics hypothesis shift인가?

**답변: PARTIAL (friction YES, mass UNCERTAIN)**

- **friction (gap=0.138)**: state_delta_norm 1.184 vs 1.322 → 명확한 dynamics 변화. ✓
- **mass (gap=0.004)**: state_delta_norm이 train_id와 구분 안 됨. Scaled 50ep에서 gap이 통계적으로 유의미하지 않음.

mass=1.5 shift는 `state_delta_norm` 기준으로 physical dynamics hypothesis shift를 재현하지 못함. mass OOD axis는 별도 repair 필요.

### Q2. base WM OOD mismatch 누적 가능성

**답변: friction LIKELY, mass UNCERTAIN**

- friction gap=0.138 → state distribution 변화가 충분하므로 WM prediction mismatch 누적 가능성 있음.
- mass gap=0.004 → WM이 ID와 OOD mass episode를 구분하기 어려울 것. 학습 신호 약함.

### Q3~Q6: 이전 Pilot 보고서 판정 유지

- Q3 (β_t 감지): friction 축 LIKELY, mass 축 UNCERTAIN
- Q4 (group-wise latent 구조): friction 축 PARTIAL (일부 차원 20% std 감소)
- Q5 (action/value 영향): friction 유지, mass 재확인 필요
- Q6 (persistence): R3 smoke 전에 관찰 불가

## mass OOD axis 신뢰성 문제

| 단계 | mass gap | 샘플 |
|---|---|---|
| Pilot | 0.0148 | n=10 episodes |
| Scaled | 0.0038 | n=50 episodes |

Pilot gap=0.0148은 소표본 variance였음. Scaled에서 수렴하면서 실제 gap=0.0038로 드러남.
FGLC novelty(dynamics hypothesis shift)를 위한 mass OOD axis의 state_delta_norm 신뢰성이 낮음.

## CONDITIONAL_PASS 근거

friction axis는 gap=0.138로 충분한 dynamics shift를 보임 → Q1~Q3 PARTIAL PASS 유지.
mass axis는 현재 metric(state_delta_norm) 기준으로 OOD 신호 불충분.

## 다음 단계 권고

1. mass axis repair (RC-1: mass 3.0 probe) → state_delta_norm gap 재측정
2. 또는 mass 측정 metric 변경 (reward_mean_diff 등)
3. friction axis만으로 단기 R3 진행 가능성 검토 (mass 재수집 전)
