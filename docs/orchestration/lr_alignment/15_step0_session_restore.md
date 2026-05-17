# 15_step0_session_restore.md — STEP 0: 세션 복원

**작성일**: 2026-05-17  
**Phase**: CC-P3 (pilot/core eval scope)  
**근거**: `docs/orchestration/lr_alignment/13_claim_survivability_decision_report.md`,  
`outputs/runs/p3_lr_eval/metrics.json`, `outputs/runs/p3_ablations/ablation_results.json`  
**범위**: Run 0~6 상태 복원 + C1~C6 현황표. 어떤 status도 이 문서에서 갱신하지 않음.

---

## §1. 안전한 현재 Framing

```
Main Claim  : C3 — LR falsification score (ABL-022/023 vs FRCG-FULL delta +0.403)
Support     : C1 — h_exec null_rate=0.0 (proxy, real persistence 미측정)
Risk        : C5 — rewrite 반대 방향 evidence (ABL-017 direction = OPPOSITE)
Blocked     : C2, C4 — 실험 자체 미실행
```

> **경고**: 위 framing은 pilot/core eval scope이다.  
> `scope_note: "pilot/core eval scope — NOT paper-accept-level evidence"` (metrics.json:57)

---

## §2. Run 0~6 상태 복원

| Run | 명칭 | 주요 목적 | 핵심 산출물 | 결과 |
|---|---|---|---|---|
| **Run 0** | Repo Scaffold + P0 | 기본 구조, schema, visibility test | `src/frcgw/schemas/visibility.py`, `tests/test_forbidden_field_mirror_sync.py` | ✅ COMPLETE — P1.passed |
| **Run 1** | P1 Schema + Tests | FORBIDDEN_AGENT_FIELDS 계약, leakage guard | `visibility.py`, `test_visibility_contract.py`, `test_leakage_auditor.py` | ✅ COMPLETE — P1.passed |
| **Run 2** | P2 Text-Only Data | synthetic episode JSONL 생성 | `data/frcgw_text/v0_1/` (200 episodes, test_id=33) | ✅ COMPLETE — P2.passed |
| **Run 3** | P3 Text Model Scaffold | text-only model, loss, training stub | `src/frcgw/model/`, `src/frcgw/training/` | ✅ COMPLETE — P3.passed |
| **Run 4** | LR Scorer Implementation | `lr_scorer.py` F_t 구현, step_schema 4 필드 | `src/frcgw/evaluation/lr_scorer.py`, `src/frcgw/evaluation/step_schema.py` | ✅ COMPLETE — P3_EVAL.passed |
| **Run 5** | Baseline/Ablation Runner | eval_runner, metrics, ablations, baselines | `src/frcgw/evaluation/{eval_runner,metrics,ablations,baselines}.py` | ✅ COMPLETE |
| **Run 5.5** | Preflight + Ablation Run | `ablation_results.json` 생성 (16 ablations × 5 seeds) | `outputs/runs/p3_ablations/ablation_results.json` | ✅ COMPLETE |
| **Run 6** | LR Eval + Claim Survivability | metrics.json 생성, C1~C6 판정 | `outputs/runs/p3_lr_eval/{metrics,manifest}.json` | ✅ COMPLETE — P3_LR_EVAL.passed |

---

## §3. C1~C6 현황 표 (Run 6 이후, 변경 금지)

> 출처: `13_claim_survivability_decision_report.md` §1 + `outputs/runs/p3_lr_eval/metrics.json`  
> 이 표의 Status는 이 문서에서 갱신하지 않는다. 갱신은 STEP 2~7 PASS 이후에만.

| Claim | Status | Key Evidence | Blocker | Next Required Work |
|---|---|---|---|---|
| **C1** wrong-grammar persistence | CONDITIONAL_ALIVE | `h_exec_null_rate=0.0`, `planning_calls=1`, `MET-PERSIST-001=BLOCKED` | `evidence_timestamp`/`correct_hypothesis_id` collector 미주입 → MET-PERSIST-001 측정 불가 | STEP 3: label 주입 → STEP 6: persistence eval 재실행, FRCG-FULL vs ABL-022 + BASE-006 + VLAA 비교 |
| **C2** regime/grammar separation | **BLOCKED** | `metrics.json.C2.status = "BLOCKED_no_regime_split_eval"` | crossed-split eval 없음, `regime_shift_f1` 미구현, latent probe (MET-LATENT-001) 없음 | STEP (미정): regime_shift_f1 구현 + crossed-split eval + Locatello impossibility 대응 |
| **C3** LR falsification | CONDITIONAL_ALIVE | FRCG_FULL_fals_f1=0.4032, ABL-022=0.0 (Δ+0.4032), ABL-023=0.0 (Δ+0.4032), F_t_variance=1.26 | `predicted_wrong` = proxy (모델 inference 아님), BASE-006/012-CATTS 미실행, N=5 synthetic | STEP 4: real predicted_wrong → STEP 5: BASE-006/012-CATTS 실행 |
| **C4** alt hypothesis WM | **BLOCKED** | `rollout_steps=0`, `MET-WM-001 = BLOCKED_no_rollout_log` | rollout 통합 미구현, MET-WM-001/ALT-001 측정 불가, BASE-027/028 미실행 | STEP (P5+): rollout 구현 → MET-WM-001/ALT-001 → BASE-027/028 비교 |
| **C5** action-interface rewrite | CONDITIONAL_ALIVE (counter-evidence 존재) | `rewrite_success_proxy=0.50`, **ABL-017 OPPOSITE direction** (Δ=-0.4107) | `action_switch_delay=0.0` (no differentiation), BASE-026 (WAC) 미실행. ABL-017 방향 반전은 proxy artifact 가능성 있으나 미해소 | STEP 7: ABL-017 root cause 조사 → STEP 5: BASE-026 실행 |
| **C6** compute gate | CONDITIONAL_ALIVE | FRCG_FULL_ppc=0.2285, ABL-034=0.114 (Δ+0.115, ~2x), `false_planning_call_rate=0.0` | `compute_matched_delta_ppc=null` (BASE-015 미실행), N=1 planning call (statistical power 없음) | STEP 5: BASE-015 실행 → STEP 8: sample size 증가 |

---

## §4. 현재 Phase Gate 상태

| Sentinel | 경로 | 상태 |
|---|---|---|
| P1.passed | `outputs/phase_gates/P1.passed` | ✅ EXISTS |
| P2.passed | `outputs/phase_gates/P2.passed` | ✅ EXISTS |
| P3.passed | `outputs/phase_gates/P3.passed` | ✅ EXISTS |
| P3_EVAL.passed | `outputs/phase_gates/P3_EVAL.passed` | ✅ EXISTS |
| P3_LR_EVAL.passed | `outputs/phase_gates/P3_LR_EVAL.passed` | ✅ EXISTS |
| P3_FULL_EVAL.passed | `outputs/phase_gates/P3_FULL_EVAL.passed` | ❌ NOT YET (STEP 2~6 완료 후) |
| P5.passed | `outputs/phase_gates/P5.passed` | ❌ NOT YET |

---

## §5. Carry-Forward 파일 (상태 보존 의무)

### §5.1 SSoT (절대 수정 금지)

| 파일 | 역할 |
|---|---|
| `paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md` | 33-field 과학적 계약 |
| `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md` | BASE-001~028, ABL-001~042 열거 |
| `src/frcgw/schemas/visibility.py` | FORBIDDEN_AGENT_FIELDS runtime |
| `.claude/settings.json` | 10-hook 매핑 |

### §5.2 Reference Outputs (덮어쓰기 금지 — versioned 경로로만 신규)

| 파일 | 역할 | 내용 |
|---|---|---|
| `outputs/runs/p3_lr_eval/metrics.json` | Run 6 preflight reference | C1~C6 preflight 수치 |
| `outputs/runs/p3_lr_eval/manifest.json` | Run 6 manifest | `run_mode: "full_eval_preflight_metrics"`, `git_sha: "1f62d87"` |
| `outputs/runs/p3_ablations/ablation_results.json` | Run 5 ablation reference | 16 ablations × 5 seeds = 80 rows (deterministic mock) |
| `outputs/runs/p3_lr_smoke/metrics.json` | Run 5.5 smoke reference | smoke 통계 (F_t_variance=1.26, degenerate_count=5) |

### §5.3 Active Reports (수정 금지 — 이 문서들은 현재 reference임)

| 파일 | 역할 |
|---|---|
| `docs/orchestration/lr_alignment/12_run6_lr_eval_report.md` | Run 6 상세 보고 |
| `docs/orchestration/lr_alignment/13_claim_survivability_decision_report.md` | C1~C6 최종 판정 |
| `docs/orchestration/lr_alignment/evidence_cards/` | 각 claim별 evidence card |

---

## §6. 알려진 이슈 / 미해소 Unknown

| ID | 내용 | 근거 | 다음 조치 |
|---|---|---|---|
| ISS-001 | F_t_degenerate_rate = 0.20 원인 미파악 | `metrics.json.C3.F_t_degenerate_rate=0.2`, `smoke.degenerate_count=5/25` | STEP 4에서 분석 |
| ISS-002 | ABL-017 OPPOSITE direction (Δ=-0.4107) | `ablations.py:267-284` random selection → same action_type 감소 가능 | STEP 7에서 root cause |
| ISS-003 | inter-seed variance = 0 (모든 seed 동일 결과) | `ablations.py:60-65` seed가 config에서 파생 안 됨 | STEP 8에서 수정 |
| ISS-004 | task_success_rate = 1.0 for all records | `eval_runner.py:122` OR semantics (success = success or progress > 0) | STEP 8에서 분석 |
| ISS-005 | collector label 미주입 (evidence_timestamp, correct_hypothesis_id) | `metrics.json.C1.MET_PERSIST_001_status = "BLOCKED_no_eval_labels"` | STEP 3 |
| ISS-006 | direct-threat baseline 0 row (BASE-006/012/015/026/027/028) | `13_claim_survivability_decision_report.md` §2 N/A rows | STEP 5 |

---

## §7. STEP 0 PASS 선언

- [x] Run 0~6 상태 복원 완료
- [x] C1~C6 표 기재 (status 갱신 없음, 출처 명시)
- [x] 안전한 framing 명시 (Main=C3, Support=C1, Risk=C5, Blocked=C2/C4)
- [x] Phase gate 현황 기재
- [x] Carry-forward 파일 목록 기재
- [x] 알려진 이슈 목록 기재
- [x] 원본 파일 변경 0

**STEP 0: PASS → STEP 1로 진입 가능**
