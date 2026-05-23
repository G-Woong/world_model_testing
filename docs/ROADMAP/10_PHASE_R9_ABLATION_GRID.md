# Phase R9 — Ablation Grid

## 목표
docs/idea/20_ABLATIONS.md의 11가지 ablation family 모두 실행. OOD 조건별 결과 보고.

## Ablation 실행 순서 (우선순위)

1. ABL-01 (no-correction) — 문제 존재 검증
2. ABL-08 (K=1 collapsed latent) — 분해 필요성 검증
3. ABL-02 (no-attention, 균일 α) — 선택 기여 검증
4. ABL-10 (no-conformal-calibration) — 보정 기여 검증
5. ABL-03 (no-falsification-gate) — β_t gate 계산 절약 검증
6. ABL-05 (no-value) — value-aware 손실 검증
7. ABL-04 (random-mask) — 비무작위성 검증
8-11. ABL-06, ABL-07, ABL-09, ABL-11 — 2차 검증

## 중단 조건

- ABL-01 ≈ FGLC: **중단** — 문제 존재 실패
- ABL-02 ≈ FGLC: **중단** — attention이 균일 선택 이상을 추가 안 함
- ABL-08 ≈ FGLC: **중단** — K=1으로 충분; 그룹 분해 불필요

## Gate 기준
- [ ] 11가지 ablation 모두 실행됨 (3개 시드, 5가지 OOD 조건, 조건당 100개 평가 에피소드)
- [ ] ABL-01 < OOD return에서 FGLC (p < 0.05) — 문제 존재
- [ ] ABL-02 < return/recovery에서 FGLC (효과 크기 > 0.3σ)
- [ ] 논문용 결과 표 완성
