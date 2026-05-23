# split-leakage-auditor 보고서 — Step 11-D7 Scaled (450ep) R1

**보고일**: 2026-05-24
**단계**: Scaled Stage 2 (실측, Post-Scaled)
**판정**: PASS

---

## Seed overlap 검사

Scaled 확장 seed pool:

| Split | Seed range | seeds |
|---|---|---|
| train_id | [42, 292) | 250 |
| val_id | [200, 250) | 50 |
| test_id | [300, 350) | 50 |
| ood_mass_low | [500, 550) | 50 |
| ood_friction_low | [600, 650) | 50 |

모든 range가 정수 집합으로 완전 disjoint (겹치는 range 없음). `checkpoint_3_split: PASS` ✓

## Trajectory hash duplicate 검사

`quality_report.json` 실측값:

```json
"hash_intra_duplicate_count": 0,
"hash_inter_duplicate_count": 0,
"hash_collision_pairs": []
```

- Split 내 중복: **0건**
- Split 간 중복: **0건**

근거: `build_split.py::audit_trajectory_hashes()` — 450ep 전체 SHA1 audit 통과.

## Regime contamination 검사

| Split | OOD 파라미터 | 분리 여부 |
|---|---|---|
| train_id / val_id / test_id | 없음 (ID) | OK |
| ood_mass_low | object_mass=1.5 | SEPARATE |
| ood_friction_low | joint_friction=5.0 | SEPARATE |

split-level API 호출 확인 (수집 로그): ood_mass_low 모든 ep에 `seed 500~549`, ood_friction_low 모든 ep에 `seed 600~649` — ID seed pool과 완전 분리.

## D_x / D_a 불변성

dataset_stats.json에서 전 split: D_x=42, D_a=8 ✓

## PASS 조건

- seed overlap=0: ✓
- hash duplicate=0: ✓ (450ep 전체)
- regime contamination=0: ✓
- D_x/D_a 불변: ✓
- forbidden field 부재: ✓ (60 tests PASS, 미변경)
