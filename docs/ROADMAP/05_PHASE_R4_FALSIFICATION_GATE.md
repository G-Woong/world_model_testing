# Phase R4 — Falsification Gate

## 목표
표준화된 불일치, conformal 보정, β-gate MLP 구현.
Gate: OOD 탐지 AUROC > 0.75, ID에서 오탐율 < 0.2.

## 입력
- 이전 단계 sentinel: outputs/phase_gates/R3.passed
- 코드: src/fglc/detectors/mismatch.py, gate.py
- 데이터: Stage 1 학습된 모델, ID + OOD 분할

## 단계

1. `src/fglc/detectors/mismatch.py` 구현
   ```python
   def standardized_mismatch(z_next, mu, sigma):
       rho = (z_next - mu) / sigma  # 그룹별 [K, d]
       F_k = (rho**2).sum(dim=-1)   # [K]
       F_total = F_k.sum()           # scalar
       return rho, F_k, F_total
   ```

2. `src/fglc/detectors/gate.py` 구현
   ```python
   class FalsificationGate(nn.Module):
       # MLP([F_1,...,F_K, F_total, h_t]) → β_t
       # Conformal 보정: 임계값 = ID holdout의 경험적 (1-α)-분위수
   ```

3. Conformal 보정 실행
   - 보류된 ID 검증 에피소드에서 F_t 분포 수집
   - 임계값 τ = (1-α)-분위수 설정 (α = 0.05 → 95번째 백분위수)
   - 학습 후 보정 (미세 조정 불필요)

4. 분산 보정 검사
   - σ_t 예측에 대한 신뢰도 다이어그램 도표
   - ECE 계산; 목표 ECE < 0.1
   - ECE > 0.2이면: L_cal 페널티 추가 및 재학습

5. 탐지 평가
   - F_t를 점수, regime_id를 오라클 레이블로 사용한 AUROC
   - 탐지 지연 측정
   - ID 데이터에서 오탐율

## Gate 기준 (R4.passed를 위해 모두 true여야 함)

- [ ] OOD 탐지 AUROC > 0.75 (대 무작위 0.5)
- [ ] ID에서 오탐율 < 0.20 (α=0.05 conformal 임계값에서)
- [ ] σ_t 예측에 대한 ECE < 0.15
- [ ] β_t 자기상관 AR(1) > 0.5 (OOD-mass 하에서, ID 노이즈 하에서는 < 0.1)
- [ ] 분산 보정 신뢰도 도표 outputs/에 저장됨
- [ ] `pytest tests/test_fglc_falsification.py` 통과

## 위험 등록부 참조
- R-5: σ 보정이 핵심 — ECE 실패하면 탐지 주장 실패
- R-6: 비교환 가능한 OOD 데이터 하에서 conformal 커버리지 보수적

## 커밋 주기
- 커밋 1: `feat(detect): R4 표준화된 불일치 + 그룹별 F_t`
- 커밋 2: `feat(detect): R4 falsification gate MLP + conformal 보정`
- 커밋 3: `results(R4): OOD AUROC > 0.75 + ECE < 0.15 검증`

## Codex 위임
예 → Codex TASK_R4_FALSIFICATION_GATE.md
