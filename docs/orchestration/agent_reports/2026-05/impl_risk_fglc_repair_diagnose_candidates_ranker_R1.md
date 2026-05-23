# impl_risk_fglc_repair_diagnose_candidates_ranker_R1

> **Agent**: implementation-risk-critic  
> **Task**: Step 7 — FGLC Repair diagnose.py + candidates.py + ranker.py  
> **Date**: 2026-05-23  
> **Verdict**: CONDITIONAL_PASS  

---

## 분석 대상

- TASK: `.agent_tasks/codex_queue/TASK_2026_05_23_FGLC_REPAIR_DIAGNOSE_CANDIDATES_RANKER.md`
- SSoT 1: `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` §D.2/§D.3
- SSoT 2: `src/fglc/repair/taxonomy.py`
- 참조: `src/fglc/repair/compare.py`, `src/fglc/repair/ledger.py` (Step 6)

---

## RISK 분석 결과 (8개 + 1 추가)

### RISK-1: §D.3 자연어 → 정규 metric key 매핑 SSoT 부재
- **SEVERITY: MEDIUM** / **STATUS: ADDRESSED**
- TASK §3에 CANONICAL_METRIC_KEYS 14개 및 점화 함수별 key verbatim 명시됨
- taxonomy DETECTION_THRESHOLDS 임계값과 점화 함수 임계값이 수치상 동일하나 다른 key 참조는 암묵적 연결 — 수용 가능

### RISK-2: LOSS_IMBALANCE phase 불일치 (corrected NLL > uncorrected 행)
- **SEVERITY: HIGH** / **STATUS: ADDRESSED**
- LOSS_IMBALANCE applicable_phases=R3; diagnose() 의사코드의 `if cause_id in applicable` filter가 R6 호출 시 자동 제거
- test (4) `test_phase_filter_drops_R6_causes_in_R3`가 반대 방향을 검증. 역방향(R3 cause가 R6 제거) 테스트 없으나 taxonomy.py 로직에서 보장됨

### RISK-3: EVAL_NOISE_HIGH 점화 함수 누락
- **SEVERITY: HIGH** / **STATUS: PARTIALLY_ADDRESSED**
- EVAL_NOISE_HIGH(R3,R4,R5,R7,R9,R10), BASELINE_MISMATCH(R9,R10), R2 only causes는 §D.2 7행 범위 밖
- 현재 TASK 명세에 "미구현 의도적" 명시 없음 → Codex 오구현 위험
- **P1 (MUST)**: STOP_CONDITION에 범위 외 명시 추가 필요

### RISK-4: Ranker n=1 케이스 score 공식
- **SEVERITY: MEDIUM** / **STATUS: ADDRESSED**
- TASK §5 의사코드: `score=((n-(i+1))/denom if n > 1 else 1.0)` 명시
- `test_single_candidate_score_is_one` 테스트로 강제됨. Division-by-zero 없음

### RISK-5: CANDIDATE_TABLE §D.3 7행 coverage 불완전 위험
- **SEVERITY: MEDIUM** / **STATUS: PARTIALLY_ADDRESSED**
- 테스트 (1)이 MODEL_UNDERCAPACITY만 검증. §D.3 7행 전체 커버리지 테스트 없음
- **P2 (SHOULD)**: `test_candidates_for_all_d3_cause_groups` 추가 필요

### RISK-6: patch dict 공백 — Step 8 no-op 위험
- **SEVERITY: LOW** / **STATUS: ADDRESSED**
- TASK §4 "모든 patch dict은 비어있으면 안 됨" 명시. test (2)에 json serializable 검증 포함
- Step 7은 key-schema 검증 불필요 (Step 8 orchestrator 담당). 경계 적절

### RISK-7: 빈 list 반환 + IMPLEMENTATION_BUG_SUSPECTED not in applicable
- **SEVERITY: MEDIUM** / **STATUS: ADDRESSED**
- R2에서 `diagnose({}, "R2") → []` 빈 list 반환은 의도된 동작 (IMPLEMENTATION_BUG_SUSPECTED.applicable_phases에 R2 없음)
- Step 8 orchestrator가 빈 list 처리 명시 필요 (Step 8 범위)

### RISK-8: ranker → candidates circular import
- **SEVERITY: LOW** / **STATUS: ADDRESSED**
- 의존 그래프: taxonomy ← candidates ← ranker (단방향). diagnose → taxonomy. Circular 없음
- TASK §9 import 정책 명시로 완전 차단

### RISK-A (추가): invalid phase → ValueError 로직 (R1 phase 케이스)
- **SEVERITY: LOW** / **STATUS: N/A**
- `applicable_phases_for("R1")` → frozenset empty → ValueError 발생. "진단 불가 phase"가 맞는 의미이나 ValueError로 통일됨
- Step 8 orchestrator가 R1에서 diagnose 호출하지 않도록 보장해야 함. Step 8 범위.

---

## Gatekeeper 5조건 사전 점검

| 조건 | 사전 평가 | 근거 |
|---|---|---|
| G1: verify exit 0 | 평가 불가 (미실행) | Codex 실행 전 |
| G2: diff review clean | CONDITIONAL | FILES_ALLOWED 6 src/test + 1 RESULT.md 명확 |
| G3: forbidden paths clean | LIKELY PASS | __init__.py, taxonomy.py, compare.py, ledger.py, schemas/, .claude/, docs/, configs/ 모두 명시 |
| G4: RESULT.md 존재 | FILES_ALLOWED에 두 경로 중 하나 포함 | CONDITIONAL |
| G5: REQUIRED_TESTS | ≥20 test 그룹 target 명시 | 3파일 × 6~9 그룹 = 20~26 예상 |

---

## 필수 수정 항목 (TASK 파일 작성 전 반영)

### P1 (MUST, MEDIUM)
TASK STOP_CONDITION에 추가:
> "EVAL_NOISE_HIGH, BASELINE_MISMATCH, R2-only causes(DATA_TOO_SMALL, DATA_BAD_SPLIT, OOD_TOO_HARD, OOD_TOO_EASY)는 §D.2 7행 범위 밖 — Step 7 점화 함수 미구현은 의도적. ci95_over_effect_size 등 해당 metric key를 점화 함수에 추가하지 마라."

### P2 (SHOULD, MEDIUM)
TASK REQUIRED_IMPLEMENTATION §7 테스트에 추가:
> "(10) test_candidates_for_all_d3_cause_groups: §D.3 7행에 해당하는 대표 cause 7개(MODEL_UNDERCAPACITY/SIGMA_CALIBRATION_FAILURE/CORRECTION_TOO_LARGE/ATTENTION_COLLAPSE/CORRECTION_TOO_WEAK/CORRECTION_TOO_LARGE(norm 과다)/PLANNER_BUDGET_TOO_LOW) 각각에 대해 올바른 phase로 candidates_for() 호출 시 len(result) >= 1"

### P3 (OPTIONAL, LOW)
candidates 테스트 (2)에 IMPLEMENTATION_BUG_SUSPECTED sentinel 제외 케이스에 `assert candidate.patch` truthy 검사 추가 권고.

---

## 최종 판정

**CONDITIONAL_PASS**

P1 반영 후 TASK 파일 확정 → Codex 실행 → G1~G6 검증 순서로 ACCEPT_READY 판정 가능.
P2는 B11 시나리오 방어를 위해 강력 권고. P3는 선택사항.
