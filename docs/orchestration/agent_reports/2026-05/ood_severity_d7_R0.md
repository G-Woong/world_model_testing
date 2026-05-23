# ood-severity-critic — Step 11-D7 Pilot R0

**판정**: PASS  
**보고일**: 2026-05-23  
**전체 보고서**: `reports/ood_severity_agent_report.md`

## 요약

| OOD split | state_delta_norm_mean | train_id gap | 판정 |
|---|---|---|---|
| train_id | 1.3283 | — | 기준 |
| ood_mass_low (mass=1.5) | 1.3135 | **0.0148** | PASS [0.01, 0.5] |
| ood_friction_low (friction=5.0) | 1.1885 | **0.1398** | PASS [0.01, 0.5] |

- OOD_TOO_EASY 미발화 (gap ≥ 0.01 두 축 모두)
- OOD_TOO_HARD 미발화 (gap < 0.5 두 축 모두)
- friction 물리 효과: state_std 일부 차원 20% 감소 확인

## PASS 조건

- ood_mass_low gap ∈ [0.01, 0.5]: ✓ (0.0148)
- ood_friction_low gap ∈ [0.01, 0.5]: ✓ (0.1398)
- repair candidate 불필요: ✓
