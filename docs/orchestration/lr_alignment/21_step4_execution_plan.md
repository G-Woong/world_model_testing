# 21_step4_execution_plan.md — STEP 4 Execution Plan

작성일: 2026-05-17
branch: `memory-redesign-2026-05-16` @ `cd30f55`
선행: `P3_STEP3_DATASET_BACKFILL.passed`, `P3_LR_REAL_EVAL.passed`

---

## 1. Purpose

이 문서는 STEP 4 Evidence Integrity Repair + Counterfactual Rollout + LR Disclosure의
구현 실행 계획이다. Blocker-to-claim 맵, Codex Task 분업, 검증 체크리스트를 담는다.

---

## 2. Claim-to-Blocker Map

| Metric/Claim | Blocker 번호 | 설명 | STEP 4 Action |
|---|---|---|---|
| C1 wrong_grammar_persistence | B0 | evidence_timestamp=step_index (의미 오류) | collector.py _backfill_episode_timestamps 확장 |
| C1 (namespace mismatch) | B0a | correct_hypothesis_id vs selected_hypothesis_id 불일치 | audit only; BLOCKED reason 명시 |
| C3 F1=0.0 | (not B0) | random-init artifact, STEP 5에서 pretraining 으로 해소 | 회귀 전 disclosure |
| C4 counterfactual_action_effects | B1 | counterfactuals=[] 하드코딩 | counterfactual_rollout.py 신규 |
| LR scorer vs planner F_t | B2 | lr_scorer dead code in text path | comparison report only |
| valid_trained_eval field | B3 | manifest에 disclosure field 없음 | 10_run_lr_real_eval.py 1-line |
| per_step trace null | B4 | selected_hypothesis_id/confidence 100% null | _TracingAgent.act() + writer 수정 |
| C5 ECE=0.025 | B5 | degenerate predictor artifact | C5_calibration_status flag 추가 |

---

## 3. Scope Boundary

### In Scope (STEP 4)

- B0: collector.py `_backfill_episode_timestamps` 에 evidence_ts 계산 추가
- B0a: namespace audit (read-only, BLOCKED reason 명시)
- B1: `src/frcgw/text_env/counterfactual_rollout.py` 신규 + collector.py L391 1-line patch
- B2: `scripts/audit_step4_lr_comparison.py` 신규 (compare-only, active path 변경 X)
- B3: `scripts/10_run_lr_real_eval.py` L518-544 `valid_trained_eval` field 추가
- B4: `_TracingAgent` per_step trace writer fix
- B5: ECE degeneracy flag + audit JSON
- B6: v0_3 dataset 생성 (B0+B1 반영)
- B7: smoke eval on v0_3 (test_id + test_ood)
- B8: 22_step5_handoff.md 작성
- B9: 이 실행 계획 문서 + 20_step4_handoff.md append

### Out of Scope (STEP 5+)

- C4_rollout_fidelity metric 함수 (metrics.py 신규 작성) — FC-04/MET-WM-001 이관
- C2_regime_split metric 함수
- LR scorer active path 교체
- Pre-training checkpoint
- Calibration training
- falsification/grammar.py 신규
- **BASE-026 (WAC-style)**: STEP 5 Task — 구현 예정
- **BASE-027 (CUWM-style)**: STEP 5 Task — 구현 예정
- **BASE-028 (WebWorld-style)**: STEP 5 Task — 구현 예정
  (3개 direct threat baseline이 STEP 5로 이관됨. ATTACK-DEF-003/004 방어 경로 유지)
- **ABL-011 (no-action-effect-log)**: STEP 5 실행 — configs/ablation_core.yaml에 등록 완료 (2026-05-17)
- **ABL-015 (no L_control_grammar loss)**: STEP 5 실행 — configs/ablation_core.yaml에 등록 완료
- **ABL-040 (leakage sanity probe)**: STEP 5 실행 — configs/ablation_core.yaml에 등록 완료
- C1 namespace mismatch (correct_hypothesis_id vs selected_hypothesis_id): STEP 5 mapping table
- degenerate_f_t_count per-episode counter bug (runner): STEP 5

---

## 4. Codex Task Breakdown

### Task 1 — B0 evidence_timestamp fix

**Task ID**: TASK_1038_step4_evidence_timestamp
**Files allowed**: `src/frcgw/text_env/collector.py`, `tests/test_step4_evidence_timestamp.py`
**Files forbidden**: visibility.py, paper_context_ref/**, data/**, settings.json, run_codex_task.ps1,
  frcg_agent.py, 10_run_lr_real_eval.py, eval_runner.py, metrics.py
**Tests**: 8개 (test_step4_evidence_timestamp.py)
**Acceptance**: 8 tests green; v0_1/v0_2 unmodified

### Task 2 — B1 counterfactual rollout

**Task ID**: TASK_1039_step4_counterfactual_rollout
**Files allowed**:
  - `src/frcgw/text_env/counterfactual_rollout.py` (신규)
  - `src/frcgw/text_env/collector.py` (L391 1-line patch만)
  - `tests/test_step4_counterfactual_rollout.py`
  - `tests/test_step4_counterfactual_no_leakage.py`
**Files forbidden**: visibility.py, validation.py, step_schema.py, paper_context_ref/**, data/**,
  frcg_agent.py, 10_run_lr_real_eval.py, metrics.py
**Tests**: 13개 (9 rollout + 4 leakage)
**Acceptance**: 13 tests green; visibility/leakage 회귀 green; v0_2 unmodified

### Task 3 — B2 LR comparison script

**Task ID**: TASK_1040_step4_lr_comparison
**Files allowed**:
  - `scripts/audit_step4_lr_comparison.py` (신규)
  - `tests/test_step4_lr_comparison.py`
**Files forbidden**: frcg_agent.py, planner.py, planning/falsification.py, lr_scorer.py (read-only),
  10_run_lr_real_eval.py, visibility.py, paper_context_ref/**, data/**
**Tests**: 4개
**Acceptance**: 4 tests green; active F_t path 변경 없음

### Task 4 — B3+B4+B5 disclosure + trace fix + ECE flag

**Task ID**: TASK_1041_step4_disclosure_trace_ece
**Files allowed**:
  - `scripts/10_run_lr_real_eval.py`
  - `scripts/audit_step4_ece_artifact.py` (신규)
  - `tests/test_step4_valid_trained_eval.py`
  - `tests/test_step4_trace_writer.py`
  - `tests/test_step4_ece_artifact.py`
**Files forbidden**: collector.py, frcg_agent.py (write 불가), metrics.py, visibility.py,
  paper_context_ref/**, data/**
**Tests**: 12개 (5+3+4)
**Acceptance**: 12 tests green; test_lr_real_eval_runner.py 14개 회귀 green

### Task 5 — Red-team Review

**Task ID**: TASK_1042_step4_redteam_review
**Files**: read-only 모든 STEP 4 변경 파일
**Purpose**: hidden label leakage / fake counterfactual / random-init misuse / claim overstatement 검토

---

## 5. Execution Timeline

```
PHASE C (now)    → docs 생성 (이 파일, 20_step4_handoff.md append)
                 → T2 agents launch

PHASE D          → Task 1 (B0) → T3 pre-audit → codex run → T3 post-audit → accept
                 → Task 2 (B1) → T3 pre + leakage-auditor → codex run → post audits → accept
                 → Task 3 (B2) → T3 pre-audit → codex run → accept
                 → Task 4 (B3+B4+B5) → T3 pre → codex run → T3 post → accept
                 → Task 5 (red-team) → accept

PHASE E          → configs/dataset_v0_3.yaml
                 → configs/lr_eval_real_v0_3.yaml
                 → python 01_generate_text_data.py --config configs/dataset_v0_3.yaml

PHASE F          → smoke eval: test_id + test_ood (max_episodes=3)
                 → LR comparison audit run
                 → ECE artifact audit run
                 → pytest (37 new + 45 regression)

PHASE G          → manifest / metrics 검증
                 → 22_step5_handoff.md 작성

PHASE H          → T4 agents (failure-interpretation + area-chair + reviewer-2)

PHASE I          → git commit scope 확인
                 → /frcgw-phase-check --pass P3_STEP4_EVIDENCE_INTEGRITY
```

---

## 6. Gate Checklist

### Audit Gate (PHASE C end)
- [x] 21_step4_execution_plan.md 작성
- [ ] 20_step4_handoff.md status append
- [ ] T2 agents PASS

### Implementation Gate (per Task)
- [ ] T1038: Codex verify exit 0, T3 PASS, 8 tests green
- [ ] T1039: Codex verify exit 0, T3 PASS, leakage-auditor PASS, 13 tests green
- [ ] T1040: Codex verify exit 0, T3 PASS, 4 tests green
- [ ] T1041: Codex verify exit 0, T3 PASS, 12 tests green, 14 regression green
- [ ] T1042: red-team PASS

### Smoke Gate (PHASE F end)
- [ ] data/frcgw_text/v0_3/{train,valid,test_id,test_ood}.jsonl 존재
- [ ] v0_3 manifest leakage_gate_pass=true, coverage_gate_pass=true
- [ ] evidence_timestamp per-step-index 패턴 미사용
- [ ] counterfactual non-empty rate > 0 (목표 > 50%)
- [ ] STEP 4 smoke manifest: forbidden_source_assertion=none_read, valid_trained_eval present
- [ ] metrics: fake_metric_count=0, C5_calibration_status present
- [ ] per_step: selected_hypothesis_id null rate < 20% for FRCG-LR
- [ ] outputs/audits/step4_lr_comparison.json 존재
- [ ] outputs/audits/step4_ece_degenerate_predictor_audit.json 존재
- [ ] 37 new + ≥45 regression tests green

### Commit Gate
- [ ] git diff --name-only STEP 4 scope 내
- [ ] pre-existing dirty 5개 미포함
- [ ] v0_1 / v0_2 미수정

### Sentinel Gate
- [ ] P3_STEP4_EVIDENCE_INTEGRITY.passed 생성

---

## 7. Risk Register

| Risk | Probability | Mitigation |
|---|---|---|
| B0 namespace mismatch (correct_hypothesis_id vs selected_hypothesis_id) | HIGH | B0a audit → BLOCKED reason 명시; B0 본체는 evidence_ts만 unblock |
| B1 state mutation (engine.apply mutates hidden_preconditions) | MEDIUM | deep-copy + snapshot assertion test |
| B1 rng seed missing → flaky test | MEDIUM | rng=random.Random(seed) 명시 + deterministic test |
| B2 lr_scorer import side-effect | LOW | subprocess isolation or lazy import |
| B5 ECE degeneracy false positive | LOW | variance<1e-6 AND unique<2 AND mean(F_t)==0 모두 충족 시에만 |
| v0_3 schema 비호환 | LOW | schema_version 일치 확인; v0_2 manifest 비교 |

---

## 8. B0a Namespace Audit Result (Claude direct)

`correct_hypothesis_id` (grammar name, e.g. `direct_search`) vs
`selected_hypothesis_id` (policy string, e.g. `oracle_best_action_proxy`):

- **namespace 불일치 확인**: EvaluationLabels.correct_hypothesis_id = grammar name
- **ActionRecord.selected_hypothesis_id** = policy_id string (from policies.py)
- MET-PERSIST-001 v1 metrics에서 이 두 값은 절대 매치 안 됨 (다른 namespace)
- **판정**: BLOCKED — STEP 5에서 mapping table 또는 unified namespace 설계 필요
- STEP 4 scope: evidence_timestamp만 수정; namespace mismatch는 STEP 5 handoff 항목으로 기록
