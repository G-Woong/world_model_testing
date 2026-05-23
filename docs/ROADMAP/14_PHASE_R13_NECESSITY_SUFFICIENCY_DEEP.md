# Phase R13 — Necessity/Sufficiency 심층 평가

## 목표
시뮬레이션 ground-truth 팩터 오라클을 사용하여 귀인 품질 평가.
알려진 물리적 파라미터 대비 OOD 유형별 마스크 정밀도/재현율 보고.

## 단계

1. 각 OOD 조건에 대해 가장 높은 α_t를 가진 그룹 측정 (100 에피소드에 걸친 평균)
2. Ground-truth 변경된 팩터와 비교:
   - OOD-mass → z^context 또는 z^action_gain 그룹이 활성화될 것으로 예상
   - OOD-friction → z^contact 또는 z^object 그룹이 활성화될 것으로 예상
   - OOD-latency → z^action_gain 그룹이 활성화될 것으로 예상
3. Ground-truth 팩터 대비 top-1 그룹 선택의 정밀도/재현율 계산

## Gate 기준
- [ ] 최소 2가지 OOD 조건에서 top-1 그룹의 마스크 정밀도 > 0.5
- [ ] 시드 간 일관성: 5개 시드 전반에 Spearman ρ > 0.7 (OOD 유형당)
- [ ] τ_g 유의성 확인: 상위 활성화 그룹에 대해 p < 0.05

## 위험 등록부
- Q3 (24_OPEN_QUESTIONS): 잠재 그룹 할당이 예상된 물리적 팩터에 대응 안 할 수 있음
  정밀도 < 0.5이면: 그룹이 단일 물리적 파라미터에 깔끔하게 대응 안 함 (다중 팩터 그룹)
