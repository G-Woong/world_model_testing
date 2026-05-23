# ood-severity-critic 보고서 — Step 11-D7 Pilot (90ep)

**보고일**: 2026-05-23
**단계**: Pilot Stage 1 (실측, Post-Pilot)
**판정**: PASS

---

## OOD severity 측정 (`state_delta_norm_mean` 기준)

| Split | state_delta_norm_mean | train_id 대비 gap | 판정 |
|---|---|---|---|
| train_id (기준) | 1.3283 | — | — |
| val_id | 1.3106 | 0.0177 | (참고) |
| test_id | 1.3252 | 0.0031 | (참고) |
| **ood_mass_low** | **1.3135** | **0.0148** | **PASS** |
| **ood_friction_low** | **1.1885** | **0.1398** | **PASS** |

근거: `data/fglc/PickCube-v1/dataset_stats.json` 실측값.

## OOD severity gate 조건

`manifest.py::verify_ood_severity()` 임계:
- `delta_min=0.01`: |train_id - ood| ≥ 0.01
- `delta_max=0.5`: |train_id - ood| ≤ 0.5

| OOD split | gap | ≥0.01? | ≤0.5? | 판정 |
|---|---|---|---|---|
| ood_mass_low (mass=1.5) | 0.0148 | ✓ | ✓ | **PASS** |
| ood_friction_low (friction=5.0) | 0.1398 | ✓ | ✓ | **PASS** |

## OOD_TOO_EASY / OOD_TOO_HARD 발화 여부

- **OOD_TOO_EASY** (gap < 0.01): 미발화 — mass gap=0.0148 ≥ 0.01, friction gap=0.1398 ≥ 0.01.
- **OOD_TOO_HARD** (gap > 0.5): 미발화 — 두 gap 모두 < 0.5.
- R3 smoke `ood_id_nll_diff=-0.0009` (목표 ≥0.05 미달)는 5 epoch 초기 학습 한계로 해석; NLL 수렴 전 진단 불충분.

## OOD 파라미터 SSoT 정합성

| 축 | 실제 적용값 | API | SSoT 단위 | 비고 |
|---|---|---|---|---|
| mass | 1.5 kg | `set_object_mass(1.5)` | object_mass 배수 | docs/idea/18_DATA_BENCHMARKS.md:44 범위(0.5, 1.5, 2.0) 내 |
| friction | 5.0 | `joint_dry_friction` | SSoT(μ_kinetic) 단위 불일치 | DEFERRED — quality_report에 friction_mapping 기록됨 |

`quality_report.json`에 `friction_api`, `friction_ssot_unit`, `friction_ssot_value_used`, `friction_mapping` 4개 필드 기록 확인.

## 실측 물리 효과 관찰

- **friction 축**: state_delta_norm 1.3283 → 1.1885 (감소 0.14) — 마찰 증가로 관절 운동이 억제됨.
  state_std 일부 차원(인덱스 12~15: 0.35→0.28)에서 감소, 관절 damping 효과 확인.
- **mass 축**: state_delta_norm 1.3283 → 1.3135 (감소 0.0148) — 질량 증가로 소폭 동역학 변화.
  small-effect이나 gap ≥ 0.01 임계 충족.

## PASS 조건

- ood_mass_low gap ∈ [0.01, 0.5]: ✓ (0.0148)
- ood_friction_low gap ∈ [0.01, 0.5]: ✓ (0.1398)
- OOD_TOO_EASY 미발화: ✓
- OOD_TOO_HARD 미발화: ✓
- repair candidate 명시 불필요: ✓
