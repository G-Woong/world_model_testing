# Phase R7 — Planner 통합

## 목표
보정된 dynamics rollout으로 MPPI/CEM 통합.
Gate: 폐쇄 루프 FGLC > ≥2 OOD 조건에서 TD-MPC2 return (p < 0.05).

## 입력
- 이전 단계 sentinel: outputs/phase_gates/R6.passed

## 단계

1. MPPI planner 구현 (src/fglc/planning/mppi.py)
   - 기본 rollout: β_t < 임계값일 때 비보정 dynamics 사용
   - 보정 rollout: 트리거될 때 첫 H_corr=3~5 스텝 동안 보정된 μ̃_t 사용

2. 폐쇄 루프 평가 루프 구현
   ```python
   for episode in eval_episodes:
       for t in range(max_steps):
           z_t, h_t = encode_and_update_belief(obs)
           rho, F_k, F_total = compute_mismatch(z_t, ...)
           beta = gate(rho, h_t)
           if beta > threshold:
               alpha = attention(rho, z_t, a, h_t)
               delta = correction(z_t, rho, a, h_t)
           action = mppi.plan(z_t, h_t, beta, alpha, delta)
           obs, reward, done = env.step(action)
   ```

3. 계산 매칭 실험
   - TD-MPC2에 FGLC가 correction에 사용하는 것과 동일한 추가 planning rollout 제공
   - 이것이 BASE-COMP-04 baseline (공격 5 방어에 핵심)

## Gate 기준

- [ ] FGLC return > ≥2 OOD 조건에서 TD-MPC2 return (p < 0.05)
- [ ] FGLC return > ≥2 OOD 조건에서 no-correction baseline
- [ ] 계산 매칭된 baseline 결과 사용 가능 (BASE-COMP-04)
- [ ] 회복 시간 측정 구현됨 (regime_id 타임스탬프 필요)
- [ ] `pytest tests/test_fglc_planner.py` 통과

## 위험 등록부 참조
- R-5: MPPI 결정론 — 재현성을 위한 시드 제어 필요
- R-7: MPPI correction 통합 복잡성

## 커밋 주기
- 커밋 1: `feat(plan): R7 MPPI/CEM 잠재 planner (비보정)`
- 커밋 2: `feat(plan): R7 H_corr 단기 유지가 있는 보정 rollout`
- 커밋 3: `results(R7): 폐쇄 루프 FGLC > OOD에서 TD-MPC2 검증`

## Codex 위임
예 → Codex TASK_R7_PLANNER.md
