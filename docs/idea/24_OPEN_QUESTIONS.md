# 24_OPEN_QUESTIONS — 열린 질문

## 출처
- main.md §마지막 핵심 정리
- deep-research-report.md §R-18 (열린 질문), §한계와 열린 질문

## 분류된 열린 질문

### Q1: 잠재 수술의 현실성 (높은 우선순위)
보정된 latent z̃_t = z_t + m ⊙ δ가 유효한 잠재 다양체 위에 머무는가?

보정 벡터가 어떤 x_t에 대한 E(x_t)의 분포 밖으로 z̃를 밀어내면:
- 보정된 예측 μ̃_t가 "환상의" 잠재 공간에 있을 수 있음
- Planner가 실제 dynamics 하에서 무의미한 궤적을 최적화할 수 있음
- τ_g 추정(CIRCA)이 off-manifold일 수 있음

**탐색된 완화**: 저랭크 correction (기본 WM의 null space의 저랭크 하위공간에서의 δ);
검색 기반 correction (학습 세트의 가장 가까운 유효 latent에서 검색).

**상태**: 미해결. 경험적 검증 필요: 보정된 z̃가 여전히 E로 인코딩 가능한가?
확인: ||z̃_t - E(D(z̃_t))|| (decoder가 있는 경우 왕복 검사) 또는 학습 잠재 분포에서
최근접 이웃 거리.

### Q2: Conformal-인과 간격 (높은 우선순위)
Conformal falsification은 커버리지 보증을 제공합니다. 인과 귀인(τ_g)은 ATE를 제공합니다.
이 두 가지는 서로를 대체할 수 없는 별도 보증입니다:
- Conformal: "≤ α 오탐율로 불일치를 보고한다"
- τ_g: "그룹 k에 개입하면 유틸리티가 τ_g만큼 바뀐다"

이것들은 별도의 보완적 구성 요소로 유지되어야 합니다.
혼동하는 것(예: conformal gate가 인과 탐지를 제공한다고 주장)은 형식적 오류입니다.

**상태**: 설계 결정 필요. Conformal gate(탐지용)와 τ_g 추정(그룹 선택용)을 분리.
그룹 선택 단계에 conformal 커버리지를 주장하지 마십시오.

### Q3: 보정 하에서 Action 관련성 보존
Correction이 예측 정확도를 개선하지만 예상치 못한 방식으로 정책 분포를 변경하면:
- 보정된 planner가 보정된 dynamics에 대해 국소적으로 최적인 action을 선택할 수 있지만
  장기적으로는 차선적 (planning horizon이 너무 짧아 장기 결과를 볼 수 없음)
- n-step TD 타겟(n=5)을 가진 L_value가 장기 결과를 포착 못할 수 있음

**상태**: 장기 planning 실험(H=20+)으로 검증 필요.

### Q4: 높은 K에서 Sparse Attention vs. Soft Attention
K=6과 entmax/sparsemax에서 정확히 1-2개 그룹만 0이 아닌 attention을 받습니다.
OOD-mixed (질량 + 마찰 + 액션-게인 동시) 하에서 3개 이상의 그룹이 활성화되어야 합니다.
하지만 sparse attention이 올바른 다중 그룹 신호를 억제할 수 있습니다.

**상태**: 희소성(해석 가능성)과 커버리지(다중 팩터 OOD) 사이의 긴장.
ASAP 알고리즘 (Shapley 연합)이 이것을 처리하도록 설계됨.
CIRCA τ_g도 다중 그룹 개입 세트를 통해 상호작용을 추정할 수 있음.

### Q5: 실제 로봇 적용 가능성
ManiSkill/robosuite: 알려진 물리학이 있는 제어 시뮬레이션. DROID/BridgeData: 실제 로봇 데이터.
실제 로봇에서:
- regime_id 절대 사용 불가
- Ground-truth 질량/마찰 알 수 없음 (마스크 정밀도/재현율 지표 계산 불가)
- 잠재 correction이 실제 센서 노이즈를 증폭시킬 수 있음

**상태**: 실제 로봇 평가(R12-DROID/BridgeData)는 새로운 지표 설계가 필요함:
ground-truth 팩터 없이, return/recovery/compute 지표만에 집중.

### Q6: 2025/2026 신규성 위협
"world model correction robotics"에 관한 최근 논문 확인 필요.
보류 중인 MCP 검색은 22_NOVELTY_AND_THREATS.md를 참조하십시오.

## 연결 맵
- 출처: deep-research-report.md §한계와 열린 질문 (R-18)
- 하위: 26_CROSSCHECK_SUMMARY.md (열린 질문 추적)
- 리뷰: reviewer2_attack_fglc_R1.md (공격 1,3,4,5는 각각 Q1,Q4,Q2,Q3에 대응)
