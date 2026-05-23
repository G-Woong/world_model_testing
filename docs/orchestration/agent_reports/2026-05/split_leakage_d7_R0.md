# split-leakage-auditor — Step 11-D7 Pilot R0

**판정**: PASS  
**보고일**: 2026-05-23  
**전체 보고서**: `reports/split_leakage_agent_report.md`

## 요약

- seed overlap: 0 (5 split × 10 쌍 모두 disjoint range)
- trajectory hash duplicate: intra=0, inter=0
- regime contamination: 0 (OOD split — ID split axis 완전 분리)
- D_x/D_a: 전 split 42/8 ✓
- forbidden field 12개 부재: ✓ (test_fglc_forbidden_field_sync PASS)

## PASS 조건

- seed overlap=0: ✓
- hash duplicate=0: ✓
- regime contamination=0: ✓
- D_x/D_a 불변: ✓
- forbidden field 부재: ✓
