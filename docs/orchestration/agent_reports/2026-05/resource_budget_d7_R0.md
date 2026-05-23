# resource-budget-auditor — Step 11-D7 Pilot R0

**판정**: PASS  
**보고일**: 2026-05-23  
**전체 보고서**: `reports/resource_budget_agent_report.md`

## 실측 요약

| 항목 | PLAN 예측 | 실측 |
|---|---|---|
| episode_length_mean | T=70 | **50.0** (max_steps 도달) |
| Pilot ep 수 | 180 | **90** (seed pool 한계) |
| VRAM peak | ~200 MB | **33.25 MiB** |
| 5 epoch wall-clock | — | **0.036분** |
| disk (Pilot) | ~0.9 MB | **< 0.5 MB** |

## Seed pool 확장 권고 (Scaled 450ep)

| Split | 현재 pool | 권장 pool |
|---|---|---|
| train_id | [42, 92) = 50 | [42, 292) = 250 |
| val_id | [200, 210) = 10 | [200, 250) = 50 |
| test_id | [300, 310) = 10 | [300, 350) = 50 |
| ood_mass_low | [500, 510) = 10 | [500, 550) = 50 |
| ood_friction_low | [600, 610) = 10 | [600, 650) = 50 |

## PASS 조건

- recommended episode count 명시: ✓ (Scaled 450ep)
- OOM risk: 없음 (33 MiB 사용, 8192 MiB 대비 0.4%)
- OOM fallback 순서 명시: ✓ (batch→horizon→K→d→h_dim)
- seed pool 확장 필요성 명시: ✓
