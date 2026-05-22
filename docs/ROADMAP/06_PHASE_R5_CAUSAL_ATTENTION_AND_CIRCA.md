# Phase R5 — Causal Attention 및 CIRCA

## 목표
개입 정책 attention α_t, τ_g 추정을 위한 무작위 Bernoulli gate, τ_g에서 α-증류, CIRCA 학습 루프 구현.
Gate: 보정된 NLL < OOD 조건에서 비보정 NLL.

## 입력
- 이전 단계 sentinel: outputs/phase_gates/R4.passed
- 코드: src/fglc/attention/causal.py, src/fglc/correction/adapter.py

## 단계

1. Attention 모듈 구현
   ```python
   class InterventionPolicyAttention(nn.Module):
       # 입력: [ρ_t, σ_t, a_t, h_t, value_signal]
       # 출력: α_t ∈ Δ^K (sparse, 그룹 수준)
       # 옵션: softmax → entmax → top-k (단계적)
   ```

2. 무작위 Bernoulli gate 구현 (CIRCA 전용)
   ```python
   def sample_random_gate(pi, training=True):
       if training:
           m = torch.bernoulli(pi)  # 기울기를 위한 straight-through 추정기
       else:
           m = (alpha > 0.5).float()  # 추론 시 하드 선택
       return m
   ```

3. τ_g 유틸리티 효과 추정
   ```python
   # 각 그룹 g에 대해:
   # U(m=1) = -NLL(z_next | 그룹_g가 보정된 corrected) + λQ(...)
   # U(m=0) = -NLL(z_next | 그룹_g 없이) + λQ(...)
   # τ_g = E[U(m=1)] - E[U(m=0)]  (평균 차이)
   ```

4. α-증류 손실 구현
   ```python
   L_align = ||α - Normalize(clamp(τ_g, min=0))||²
   ```

5. Stage 2 CIRCA 학습: 기본 WM 동결, β-gate + attention + correction 어댑터 학습

## Gate 기준 (R5.passed를 위해 모두 true여야 함)

- [ ] OOD-mass에서 보정된 NLL < 비보정 NLL (> 0.1 nat 개선)
- [ ] OOD 조건당 최소 1개 그룹에서 τ_g > 0 (p < 0.05, t-검정, 100 에피소드)
- [ ] Attention 엔트로피 < 1.0 nat (sparse attention 활성)
- [ ] ABL-no-attention baseline 실행: 균일 α=1/K (R9 비교 준비됨)
- [ ] `pytest tests/test_fglc_circa.py` 통과

## 위험 등록부 참조
- R-1: Off-manifold 개입 — ||z̃_t - z_t|| < 3*δ_max 모니터링
- R-6: Bernoulli gate의 Straight-through 추정기 불안정성

## 커밋 주기
- 커밋 1: `feat(attn): R5 개입 정책 attention (softmax 단계)`
- 커밋 2: `feat(attn): R5 CIRCA Bernoulli gate + τ_g 추정`
- 커밋 3: `feat(train): R5 Stage 2 CIRCA 학습 루프`
- 커밋 4: `results(R5): OOD에서 보정된 NLL < 비보정 NLL 검증`

## Codex 위임
예 → Codex TASK_R5_CIRCA.md
