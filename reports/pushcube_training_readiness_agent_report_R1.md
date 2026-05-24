# Agent F — Training Readiness Auditor Report (PushCube-v1)

**상태**: PENDING — Stage 3 PushCube full collection + Q8 R3 smoke 완료 후 populate  
**Phase**: R3 진입 전 (Stage 6)  
**트리거**: Stage 4 Agent F (plans/fglc-step-vectorized-iverson.md §G.6)  
**담당**: frcgw-experiment-evaluator 또는 Claude 직접  
**입력**: PushCube-v1 5 HDF5 + smoke_maniskill_pushcube.yaml  

---

## 검사 항목

| 항목 | 기준 | 결과 |
|---|---|---|
| ManiSkillStateOnlyDataset PushCube HDF5 로드 | 오류 없음 | PENDING |
| D_x 확정 | 실제 D_x ≠ 42 시 config 업데이트 | PENDING |
| 1-batch forward | no error, tensor shape valid | PENDING |
| 1-epoch smoke run | no OOM, no NaN | PENDING |
| metrics.json 생성 | NLL, ELBO, MSE 모두 finite | PENDING |
| ID NLL < gate threshold (0.5) | smoke 기준 완화 가능 | PENDING |

## 1-epoch Smoke 결과 (Stage 6 완료 후)

```json
{
  "task": "PushCube-v1",
  "D_x": "PENDING",
  "id_nll": "PENDING",
  "id_mse": "PENDING",
  "ood_mass_nll": "PENDING",
  "ood_mass_nll_gap": "PENDING",
  "status": "PENDING"
}
```

## Config 유효성 체크

- `smoke_maniskill_pushcube.yaml` D_x 값: PLACEHOLDER (Q6에서 확정 필요)
- batch_size=16, T=8, K=6, d=32, h_dim=128: PickCube와 동일 → VRAM 안전

## 판정

**PENDING** — Stage 6 R3 smoke 완료 후 채워질 것.

최종 판정 기준:
- PASS: 1-epoch smoke 성공, NLL finite
- FAIL: NaN loss 또는 OOM → config 수정 필요
