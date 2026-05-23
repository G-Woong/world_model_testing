# ood-severity-critic — Step 11-D7 Scaled R1

**판정**: FAIL  
**보고일**: 2026-05-24  
**전체 보고서**: `reports/ood_severity_agent_report_scaled_R1.md`

## 핵심

- ood_mass_low gap=0.003747 < delta_min=0.01 → **FAIL**
- ood_friction_low gap=0.138043 → **PASS**
- 원인: mass=1.5 shift가 state_delta_norm으로 통계적으로 구분 불가 (n=50 수렴)
- Pilot gap=0.0148은 소표본(n=10) variance

## Repair Candidate

| RC | 내용 | risk |
|---|---|---|
| RC-1 (추천) | mass 3.0으로 재수집 (probe 5ep 먼저) | 0.3 |
| RC-2 | severity metric → reward_mean_diff | 0.4 |
| RC-3 | gate delta_min_mass 0.003으로 완화 | 0.6 |

## 결론

**R3 smoke 금지 (Agent C FAIL)**. 사용자 결정 필요.
