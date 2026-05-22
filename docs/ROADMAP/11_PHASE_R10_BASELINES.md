# Phase R10 — Baselines

## 목표
19_BASELINES.md의 모든 필수 baselines 학습 및 평가. 핵심: 계산 매칭된 baseline.

## Baselines 우선순위

### 높은 우선순위 (논문 주요 주장)
1. TD-MPC2 (참조 baseline) — 공개 코드가 있으면 사용; 없으면 재구현
2. BASE-COMP-04 (계산 매칭된 무작위 재할당) — 공격 5 방어에 핵심
3. BASE-ABL-01 (no-correction) — 이미 R9에 있음
4. BASE-ORACLE-01..04 (오라클 상한값) — ManiSkill 시뮬레이션에서 실현 가능

### 중간 우선순위 (관련 연구 비교)
5. HiP-RSSM — 구현하거나 공개 코드 찾기 필요
6. DreamerV3 — ManiSkill에 적응된 공개 JAX 코드 사용
7. BASE-ABL-03 (CUSUM verifier-only)
8. BASE-ABL-04 (SPRT verifier-only)

### 낮은 우선순위 (예산 허용 시)
9. PLSM, ReDRAW, AdaWM

## Gate 기준
- [ ] TD-MPC2 baseline이 모든 OOD 조건에서 평가됨
- [ ] 계산 매칭된 baseline (BASE-COMP-04) 실행됨 — FGLC와 동일 planning rollouts
- [ ] 오라클 baselines 실행됨 (mass/friction) — 상한값 참조 제공
- [ ] 결과 표 완성: FGLC vs. TD-MPC2 vs. HiP-RSSM vs. 계산 매칭

## 위험 등록부
- R-3: HiP-RSSM은 RSSM 기반 필요; ManiSkill 커스텀 적응 필요 가능
- R-4: DreamerV3 JAX→PyTorch 포트가 복잡할 수 있음
