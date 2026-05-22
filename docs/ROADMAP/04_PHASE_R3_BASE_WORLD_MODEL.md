# Phase R3 — 기본 World Model

## 목표
Stage 1 구현 및 학습: encoder + 그룹화된 latent + GRU belief + dynamics + reward/value.
Gate: ID 1단계 NLL 수렴; OOD NLL이 ID보다 측정 가능하게 높음 (문제 존재).

## 입력
- 이전 단계 sentinel: outputs/phase_gates/R2.passed
- 코드: src/fglc/models/ (encoder.py, dynamics.py, belief.py)
- 데이터: data/fglc/ ID 분할

## 아키텍처 (docs/idea/04_BASE_WORLD_MODEL.md 기반)

```python
K=6, d=32, h_dim=256  # 하이퍼파라미터

class FGLCBaseWorldModel(nn.Module):
    encoder    # MLP D_x→256→256→K*d, LayerNorm, SiLU
    group_transformer  # 2-layer, d_model=32~64, heads=4 (DYNAMICS layer)
    dynamics   # 그룹별 MLP → μ_t^k, logσ_t^k
    belief     # GRU(hidden=256, input=K*d+D_a+1)
    reward_head    # MLP flatten(z)+a+h → scalar
    value_head     # MLP flatten(z)+h → scalar
```

## 단계

1. `src/fglc/models/encoder.py` 구현
2. `src/fglc/models/dynamics.py` 구현 (그룹 MLP + 상호작용 transformer)
3. `src/fglc/models/belief.py` 구현 (GRU)
4. 학습 루프 `src/fglc/training/train_base_wm.py` 구현 (Stage 1 손실)
5. Stage 1 학습 실행 (3개 태스크 × ID 데이터): A100에서 ~6시간
6. 평가: ID NLL 수렴 + OOD NLL 간격 측정

## Gate 기준 (R3.passed를 위해 모두 true여야 함)

- [ ] 수렴 시 ID 1단계 NLL < 0.1 nat (PickCube 참조)
- [ ] OOD-mass NLL > ID NLL by > 0.2 nat (OOD 도전 존재)
- [ ] OOD-friction NLL > ID NLL by > 0.1 nat
- [ ] GRU belief h_t 차원 = 256 (스펙과 일치)
- [ ] `pytest tests/test_fglc_base_wm.py` 통과 (아키텍처 형태, 순방향 패스)
- [ ] 실행 manifest 저장됨 (config, seed, 데이터셋 hash, 최종 NLL)

## 위험 등록부 참조
- R-7: MPPI 결정론 — 해당 없음
- R-8: 가치-Q 수렴 — 가치 헤드 느리게 수렴 가능; bootstrapped target 사용
- R-9: Planner-WM 결합 — 해당 없음 (Stage 1은 모델 전용)

## 커밋 주기
- 커밋 1: `feat(model): R3 encoder + 그룹화된 latent + GRU belief`
- 커밋 2: `feat(model): R3 그룹 상호작용 transformer + 그룹별 dynamics`
- 커밋 3: `feat(train): R3 Stage 1 학습 루프 + 손실`
- 커밋 4: `results(R3): 기본 WM ID 수렴 + OOD NLL 간격 검증`

## Codex 위임
예 — 다중 파일 모델 구현 → Codex TASK_R3_BASE_WM.md
