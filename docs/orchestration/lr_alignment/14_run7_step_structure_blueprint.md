# 14_run7_step_structure_blueprint.md — Run 7 이후 전체 STEP 구조 설계도

**작성일**: 2026-05-17  
**Phase**: CC-P3 → P5 진입 준비  
**근거**: `docs/orchestration/lr_alignment/13_claim_survivability_decision_report.md`,  
`paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP.md`  
**범위**: STEP 0~8 전체 구조 설계. 본 문서는 PLAN 문서이며 어떤 코드/데이터/모델도 변경하지 않음.

---

## §1. 설계 원칙

1. **한 턴에 모든 STEP을 실행하지 않는다.** 각 STEP은 독립적 작업 단위로, PASS 조건을 충족한 후 다음으로 진입한다.
2. **pilot/core eval scope 표시는 제거하지 않는다.** STEP 2 이후에서만 근거가 쌓이면 갱신 가능.
3. **원본 파일 이동·삭제 0 원칙**: STEP 1.5의 lifecycle 작업은 별도 PR 라운드에서만 실행.
4. **Claim status를 임의로 ALIVE_WITH_EVIDENCE로 승격하지 않는다.** 각 STEP PASS 조건 충족 후에만.
5. **STEP 건너뛰기 금지**: 특히 STEP 2 (full eval runner)를 건너뛰고 STEP 5~8(직접 위협 baseline) 실행 불가.

---

## §2. STEP-MAP 전체 구조

| STEP | 명칭 | 주요 목적 | 필수 선행 STEP | 예상 소요 범위 |
|---|---|---|---|---|
| **STEP 0** | 세션 복원 | Run 0~6 상태 / C1~C6 blocker 정리 | 없음 | 본 턴 ✅ |
| **STEP 1** | 신뢰성 감사 | preflight 확인, metric source trace, dataset coverage | STEP 0 | 본 턴 ✅ |
| **STEP 1.5** | Lifecycle 설계 | 기존 정책 분석 + copy-only staging 설계 | STEP 1 | 본 턴 ✅ |
| **STEP 2** | Full eval runner contract | `09_run_lr_eval.py` 재작성 → `EvaluationRunner.run()` 호출 | STEP 1 PASS | 다음 턴 |
| **STEP 3** | Trace/label coverage 복구 | collector에 `evidence_timestamp`, `correct_hypothesis_id`, `predicted_wrong`, `wrong_prob` 주입 | STEP 2 | 다음 턴 |
| **STEP 4** | Non-proxy C3 metric | real model-predicted `predicted_wrong`, F_t_degenerate 원인 분석 | STEP 3 | 다음 턴 |
| **STEP 5** | 직접 위협 baseline 실행 | BASE-006 / 012-CATTS / 015 / 026 / 027 / 028 실제 episode 실행 | STEP 2 + 3 | 다음 턴 |
| **STEP 6** | C1 persistence eval | MET-PERSIST-001 labeled episode 재실행 | STEP 3 | 다음 턴 |
| **STEP 7** | C5 counter-evidence 조사 | ABL-017 OPPOSITE direction 근본 원인 + 수정 또는 claim weakening | STEP 2 + 4 | 다음 턴 |
| **STEP 8** | Statistical reliability 보고서 | seed variance 복원, N 증가, episode-level CI | STEP 5~7 모두 PASS | 다음 턴 이후 |

---

## §3. STEP별 상세 명세

### STEP 0 — 세션 복원

**목적**: Run 0~6 전체 상태를 단일 문서에 복원하여 이후 STEP들이 올바른 출발점에서 시작.

**필수 산출물**:
- `docs/orchestration/lr_alignment/15_step0_session_restore.md`

**PASS 조건**:
- Run 0~6 각각의 목적/결과/산출물 기재
- C1~C6 표 (Status / Evidence / Blocker / Next Required Work)
- 안전한 현재 framing 명시: Main=C3 LR falsification, Support=C1 h_exec proxy, Risk=C5 counter-evidence
- Carry-forward 파일 목록

**다음 STEP 진입 조건**: STEP 0 MD 존재 확인

---

### STEP 1 — 신뢰성 감사

**목적**: Run 6 결과가 preflight aggregator인지 full eval인지 확인하고, 각 metric의 신뢰 수준을 분류.

**필수 산출물**:
- `docs/orchestration/lr_alignment/16_step1_reliability_audit.md`

**PASS 조건**:
- `scripts/09_run_lr_eval.py` 코드 감사 (line 64-197 aggregator, line 264-278 no-op shard path) 결과 기재
- Metric source trace: C1/C3/C5/C6 각각 어느 파일·라인에서 값이 오는지
- Dataset coverage: 33 episodes, predicted_wrong/wrong_prob missing, splits aliased 확인
- Ablation seed variance 0 + task_success 1.0 saturated 분석
- Direct-threat baseline N/A 근거 (BASE-006/012-CATTS/015/026/027/028 = 0 row)
- Trust Level 분류 표 (High / Medium / Low + 이유)

**다음 STEP 진입 조건**: Trust Level 표 완성 + "preflight 확인됨" 명시

---

### STEP 1.5 — Lifecycle/Cleanup 정책 설계

**목적**: 기존 정책 분석 + copy-only review staging 신규 layer 설계. 원본 파일 변경 0.

**필수 산출물**:
- `docs/orchestration/lr_alignment/17_step1_5_lifecycle_cleanup_design.md`
- (조건부) `outputs/cleanup_audit/<YYYYMMDD_HHMMSS>/candidate_manifest.{json,md}`

**PASS 조건**:
- `14_REPORT_LIFECYCLE_POLICY.md` §3 5조건 및 §6 dry-run pipeline 분석
- `scripts/audit_stale_reports.py` `--apply` 차단 line 243-249 분석
- copy-only staging 신규 layer 설계 (기존 정책과 충돌 없음 명시)
- Candidate taxonomy 12개 + `deletion_allowed_now=false` 강제
- Human review instructions
- 원본 파일 변경 0 확인

**다음 STEP 진입 조건**: 설계 문서 완성 + human review guide 포함

---

### STEP 2 — Full Eval Runner Contract

**목적**: `scripts/09_run_lr_eval.py`를 재작성하여 `EvaluationRunner.run()`을 실제로 호출하고,
hidden leakage guard를 활성화. 현재 no-op 코드를 real episode 실행으로 대체.

**필수 산출물**:
- `scripts/09_run_lr_eval.py` (재작성)
- `outputs/runs/p3_lr_eval_v2/metrics.json` (실제 episode 실행 결과)
- `outputs/runs/p3_lr_eval_v2/manifest.json` (`run_mode: "full_eval"`)

**PASS 조건**:
- `manifest.json.run_mode` = `"full_eval"` (preflight 아님)
- `hidden_leakage_count` = 0 (real guard 통과)
- `predicted_wrong` / `wrong_prob` 데이터 실제 존재 (proxy 아님)
- episode count ≥ 33 (test_id shard 전체)
- `eval_runner.py:100-103` `assert_no_hidden_labels_in_input` 실제 호출됨

**블로커 위험**:
- `EvaluationLabels.evidence_timestamp` collector 미주입 → STEP 3 선행 필요
- dataset shard 접근 권한

---

### STEP 3 — Trace/Label Coverage 복구

**목적**: text env collector에 MET-PERSIST-001이 요구하는 라벨들을 실제로 주입.

**대상 라벨**:
- `evidence_timestamp` (action-effect 발생 시각)
- `correct_hypothesis_id` (정답 hypothesis ID)
- `predicted_wrong` (모델 예측 — proxy 아님)
- `wrong_prob` (calibration용 확률)

**PASS 조건**:
- 수집된 episode JSONL에 위 4 필드 존재 확인
- `visibility.py::FORBIDDEN_AGENT_FIELDS` 미포함 확인 (leakage guard 통과)
- `tests/test_forbidden_field_mirror_sync.py` green

---

### STEP 4 — Non-Proxy C3 Metric

**목적**: `predicted_wrong`을 실제 모델 inference 기반으로 측정.
현재 `eval_runner.py:107-110`의 `agent.last_predicted_wrong` 경로를 실제 FRCG-WM agent로 교체.

**PASS 조건**:
- `falsification_precision` / `falsification_recall` 실제 모델 prediction 기반
- `F_t_degenerate_rate` 원인 분석 (현재 0.20, 원인 미파악)
- calibration ECE 실제 wrong_prob 기반

---

### STEP 5 — 직접 위협 Baseline 실행

**목적**: BASE-006 / BASE-012-CATTS / BASE-015 / BASE-026 / BASE-027 / BASE-028을
실제 episode 위에서 실행하여 C3/C5/C6 직접 비교 가능하게.

**대상 baseline**:

| Baseline ID | 명칭 | Claim 관련 |
|---|---|---|
| BASE-006 | Verifier-Only | C3 falsification |
| BASE-012-CATTS | CATTS | C3 falsification |
| BASE-015 | Compute-Matched Random | C6 compute gate |
| BASE-026 | WAC | C5 rewrite |
| BASE-027 | CUWM | C4 alt WM |
| BASE-028 | WebWorld | C4 alt WM |

**PASS 조건**:
- 6개 baseline 모두 실행 완료 (N/A → 실수 값)
- `ablation_results.json` 또는 별도 baseline manifest에 기록
- 각 baseline의 falsification_f1 / progress_per_compute / failed_rep_rate 존재

---

### STEP 6 — C1 Persistence Eval

**목적**: MET-PERSIST-001 `BLOCKED_no_eval_labels` 해소. STEP 3 label 주입 후 재실행.

**PASS 조건**:
- `MET-PERSIST-001` = numeric (BLOCKED 아님)
- `evidence_timestamp` 기반 h_exec 측정
- FRCG-FULL vs ABL-022 + BASE-006 + VLAA 비교 가능

---

### STEP 7 — C5 Counter-Evidence 조사

**목적**: ABL-017 OPPOSITE direction (−0.4107) 근본 원인 규명.
`ablations.py:267-284` `_random_public_candidate` → 동일 action 연속 감소 → metric confound.

**결과 분기**:
- A) Root cause = proxy artifact → real episode로 재측정 후 direction 재확인
- B) Root cause = 실제 claim 반증 → C5 claim weakening (CONDITIONAL → COUNTER-EVIDENCE)
- C) Root cause 불확실 → STEP 7 BLOCKED로 보고

**PASS 조건**:
- ABL-017 direction 결론 (A/B/C) 명시
- C5 claim status 갱신 (새 status 명시)

---

### STEP 8 — Statistical Reliability 보고서

**목적**: 전체 실험의 statistical power 확보. seed variance 복원, episode N 증가.

**주요 변경**:
- `ablations.py:60-65` seed salt를 config seed에서 파생하도록 수정
- episode 수 33 → 목표 N (paper 기준 minimum N 확인 필요)
- episode-level confidence interval 계산

**PASS 조건**:
- inter-seed variance > 0 확인
- task_success_rate < 1.0 (saturation 해소)
- episode-level CI 존재
- paper-accept-level evidence 수준 판단 (별도 gate)

---

## §4. Carry-Forward 파일 (모든 STEP에서 유지 의무)

### 코드 (변경 전 테스트 필수)

| 파일 | 역할 |
|---|---|
| `src/frcgw/schemas/visibility.py` | FORBIDDEN_AGENT_FIELDS runtime SSoT |
| `src/frcgw/evaluation/eval_runner.py` | episode 실행 + leakage guard |
| `src/frcgw/evaluation/metrics.py` | MET-PERSIST/FALS/CAL 구현 |
| `src/frcgw/evaluation/ablations.py` | ABL-001~042 구현 |
| `src/frcgw/evaluation/baselines.py` | BASE-001~028 구현 |
| `src/frcgw/evaluation/lr_scorer.py` | F_t 구현 |

### 데이터 (변경 금지)

| 파일 | 역할 |
|---|---|
| `data/frcgw_text/v0_1/test_id.jsonl` | 33-episode test shard |
| `data/frcgw_text/v0_1/manifest.json` | dataset manifest |

### 출력 (덮어쓰기 금지 — versioned 경로로만 신규 생성)

| 파일 | 역할 |
|---|---|
| `outputs/runs/p3_lr_eval/metrics.json` | Run 6 preflight 결과 (reference) |
| `outputs/runs/p3_ablations/ablation_results.json` | Run 5 ablation 결과 (reference) |

---

## §5. Phase Gate 관계

| STEP | 관련 Phase Gate |
|---|---|
| STEP 0~1.5 | `P3_LR_EVAL.passed` (이미 존재, 갱신 불필요) |
| STEP 2 완료 | 별도 gate 불필요 (sub-step) |
| STEP 3~6 완료 | `P3_FULL_EVAL.passed` (신규 — 별도 라운드에서 `/frcgw-phase-check --pass` 호출) |
| STEP 7~8 완료 | `P5.passed` 진입 조건 검토 |

---

## §6. 절대 금지 (모든 STEP 공통)

1. `paper_context_ref/` 실질 수정 금지
2. `outputs/phase_gates/` 임의 생성/삭제 금지
3. 원본 report 이동/삭제 금지
4. C1~C6 status를 실험 없이 ALIVE_WITH_EVIDENCE로 승격 금지
5. lifecycle policy 본문을 이 STEP-MAP에서 직접 수정 금지
6. `git push` 금지 (명시적 사용자 지시 시에만)
