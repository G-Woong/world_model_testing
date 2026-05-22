# Phase R15 — Reviewer 공격 방어

## 목표
5가지 주요 reviewer-2 공격 모두 사전에 대응 (reviewer2_attack_fglc_R1.md 참조).

## 필수 방어

1. **공격 1 (causal 명칭)**: CIRCA τ_g 실험 결과 추가 또는 논문 전반에 걸쳐
   "intervention-policy attention"으로 이름 변경. 06_CAUSAL_ATTENTION.md 참조.

2. **공격 2 (ReDRAW 유사성)**: BASE-ReDRAW baseline 결과 보여줌; ABL-02 (no-attention) < FGLC의
   return 개선을 구별 증거로 인용.

3. **공격 3 (K=6 자의적)**: 보충 자료에 시드 간 Spearman > 0.7 결과 + K={3,6,12} 스윕 보여줌.
   Locatello 한계 명시적 인용.

4. **공격 4 (이상 탐지)**: β_t 자기상관 AR(1) > 0.5 (OOD 하에서), < 0.1 (ID 노이즈 하에서) 보여줌.
   주요 표에 recall/FPR 구별 표 보고.

5. **공격 5 (계산 매칭)**: 주요 표에 BASE-COMP-04 결과 보여줌.
   FGLC > 계산 매칭이면: "FGLC는 더 표적화된 correction으로 더 나은 return 달성."
   FGLC ≈ 계산 매칭이면: 주장을 "correction이 무작위 재할당보다 더 효율적"으로 축소.

## 보충 자료 부록 요구사항
- K 민감도 스윕 (K=3,6,12)
- 시드 간 attention 일관성 (OOD 유형당 5개 시드 Spearman)
- β_t 시간적 상관 분석
- OOD 유형당 그룹당 τ_g 유의성
- 표준 편차가 있는 전체 ablation 표

## Gate 기준
- [ ] 5가지 공격 모두 논문 본문 또는 보충 자료에서 다루어짐
- [ ] 보충 자료 부록 완성
- [ ] 최종 관련 연구 섹션에서 fglc-related-work-scout 실행됨
