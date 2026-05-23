# split-leakage-auditor 보고서 — Step 11-D7 Pilot (90ep)

**보고일**: 2026-05-23
**단계**: Pilot Stage 1 (실측, Post-Pilot)
**판정**: PASS

---

## Seed overlap 검사

| Split 쌍 | Seed range A | Seed range B | Overlap |
|---|---|---|---|
| train_id ↔ val_id | [42, 92) | [200, 210) | 0 |
| train_id ↔ test_id | [42, 92) | [300, 310) | 0 |
| train_id ↔ ood_mass_low | [42, 92) | [500, 510) | 0 |
| train_id ↔ ood_friction_low | [42, 92) | [600, 610) | 0 |
| val_id ↔ test_id | [200, 210) | [300, 310) | 0 |
| val_id ↔ ood_mass_low | [200, 210) | [500, 510) | 0 |
| val_id ↔ ood_friction_low | [200, 210) | [600, 610) | 0 |
| test_id ↔ ood_mass_low | [300, 310) | [500, 510) | 0 |
| test_id ↔ ood_friction_low | [300, 310) | [600, 610) | 0 |
| ood_mass_low ↔ ood_friction_low | [500, 510) | [600, 610) | 0 |

근거: `scripts/fglc/collect_maniskill.py:34-75 SPLIT_DEFAULTS` — 모든 seed pool이 disjoint range로 하드코딩됨.

## Trajectory hash duplicate 검사

`quality_report.json` 실측값:

```json
"hash_intra_duplicate_count": 0,
"hash_inter_duplicate_count": 0,
"hash_collision_pairs": []
```

- Split 내 중복: **0건**
- Split 간 중복: **0건**
- 충돌 쌍: **없음**

근거: `build_split.py::audit_trajectory_hashes()` — SHA1 기반 split-내/split-간 audit, `quality_report.json`에 직렬화.

## Regime contamination 검사

| Split | OOD 파라미터 | ID 파라미터 | 분리 여부 |
|---|---|---|---|
| train_id / val_id / test_id | 없음 (ID) | default | OK |
| ood_mass_low | object_mass=1.5 | default(1.0) | SEPARATE |
| ood_friction_low | joint_friction=5.0 | default | SEPARATE |

OOD mass/friction 파라미터는 collector의 split-level API 호출로만 적용됨 — episode-level 혼용 없음 (`src/fglc/data/collector.py:148-149`).

## D_x / D_a 일치 검사

| Split | D_x | D_a |
|---|---|---|
| train_id | 42 | 8 |
| val_id | 42 | 8 |
| test_id | 42 | 8 |
| ood_mass_low | 42 | 8 |
| ood_friction_low | 42 | 8 |

모든 split: D_x=42, D_a=8 — `configs/fglc/smoke_maniskill_pickcube.yaml:8-9`와 일치.

## Forbidden field 감사

`tests/test_fglc_forbidden_field_sync.py` — Codex 패치 A 이후 60 tests PASS 확인.
`FORBIDDEN_AGENT_FIELDS` 12개 (regime_id, true_mass, true_friction, true_latency, true_noise_sigma, true_action_gain, oracle_action, counterfactual_reward, split_id, ood_type, seed, template_id) 모두 dataloader output에 미포함.

## PASS 조건

- seed overlap=0: ✓
- hash duplicate=0: ✓
- regime contamination=0: ✓
- D_x/D_a 불변: ✓ (모든 split 42/8)
- forbidden field 부재: ✓
