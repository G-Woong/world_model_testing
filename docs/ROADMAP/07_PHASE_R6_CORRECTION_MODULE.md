# Phase R6 — Correction 모듈

## 목표
tanh bounding과 necessity/sufficiency 손실을 가진 그룹별 correction MLP δ_t^k 구현.
Gate: L_nec (necessity)와 L_suf (sufficiency) 테스트가 필수 임계값에서 통과.

## 입력
- 이전 단계 sentinel: outputs/phase_gates/R5.passed

## 단계

1. Correction 어댑터 구현 (src/fglc/correction/adapter.py)
   ```python
   class CorrectionAdapter(nn.Module):
       def forward(self, z_k, rho_k, a, h):
           raw = MLP(concat(z_k, rho_k, a, h))  # → d
           delta_k = delta_max * torch.tanh(raw)
           return delta_k  # 경계가 있는 correction
   
   def corrected_dynamics(mu, beta, alpha, delta, groups):
       # mu_tilde_k = mu_k + beta * alpha_k * delta_k
       return mu + beta.unsqueeze(-1) * alpha.unsqueeze(-1) * delta
   ```

2. Correction 크기 페널티 L_corr_size 추가
3. 시간적 일관성 손실 L_temporal 추가 (α_t ≈ α_{t+1})
4. Necessity/sufficiency/무작위 대비 손실 구현
5. OOD 유형별 그룹별 correction 크기 측정

## Gate 기준

- [ ] Necessity 테스트: OOD-mass에서 L_without - L_with > 0.05 nat (보정 선택 그룹이 필요함)
- [ ] Sufficiency 테스트: |L_selected - L_full| < 0.1 nat (선택 그룹으로 충분)
- [ ] 무작위 대비: L_random - L_selected > 0.05 nat (무작위보다 나음)
- [ ] Correction 크기 ||δ_t^k|| < δ_max = 0.25 (오버플로 없음)
- [ ] `pytest tests/test_fglc_correction.py` 통과

## 위험 등록부 참조
- R-1: Correction 모듈이 기본 WM 학습을 방해. Stage 2 중 L_corr_size 모니터링.
  correction 크기가 기본 WM 예측 분산의 2배를 초과하면 중단.

## 커밋 주기
- 커밋 1: `feat(correction): R6 그룹별 correction 어댑터 + tanh bounding`
- 커밋 2: `feat(loss): R6 necessity/sufficiency/대비 손실`
- 커밋 3: `results(R6): necessity+sufficiency 임계값 검증`

## Codex 위임
예 → Codex TASK_R6_CORRECTION.md
