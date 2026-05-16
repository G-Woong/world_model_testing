---
file_id: CONCEPT-SURVIVABILITY-LEDGER-R2
title: Concept Survivability Ledger — Phase 3 산출물
phase: 3 (Concept Survivability Ledger Design)
run: 2
date: 2026-05-16
status: LEDGER_DESIGN
language: ko
type: survivability_ledger_not_final_verdict
---

# 03_concept_survivability_ledger.md

**Phase**: 3 — Concept Survivability Ledger Design  
**Run**: 2  
**Date**: 2026-05-16  
**Type**: survivability ledger (FINAL VERDICT 아님. C1~C6 ALIVE/DEAD 판정 금지)

---

## Section 1. Purpose

이 문서는 **final verdict가 아니다**.

이 문서의 역할:
- C1~C6를 세션이 바뀌어도 추적하기 위한 survivability ledger
- Evidence Card schema 확정: 각 concept에 대해 어떤 증거가 쌓여야 status 변경이 가능한지를 명시
- C1~C6 각각에 대해 stub 카드를 생성하여 Phase 3~12에서 순차적으로 채워 나갈 기초 구조 제공
- Status 변경은 **Evidence Card 없이는 금지**

이 문서에서 절대 하지 않는 것:
- C1~C6를 `ALIVE_WITH_EVIDENCE` 또는 `DEAD_COLLAPSED`로 확정 판정
- Evidence 없이 claim status를 변경
- Phase 11 전에 final survivability decision을 내림
- 실험 결과를 날조하거나 fake metric을 사용

핵심 원칙: **약화가 아니라 정렬이다.**  
Run 2는 증거 없이 claim을 약화/폐기하지 않는다. 핵심 목표는 살릴 수 있는 claim을 검증 가능한 evidence path에 연결하는 것이다.

---

## Section 2. Status Taxonomy (6단계)

| Status | Meaning | Run 2에서 허용? | Transition Requirement |
|---|---|---|---|
| `ALIVE_WITH_EVIDENCE` | full evidence로 살아남음. ablation delta > sensitivity threshold. Evidence Card 전 필드 완성. | NO | Phase 11 eval artifact 필요. `P3_LR_EVAL.passed` sentinel 필요. |
| `CONDITIONAL_ALIVE` | 설계상 생존 가능하나 evidence 일부 부족. source/design evidence 존재하나 code/test/experiment evidence 미완성. | YES | source/design evidence 필요. Phase 3 이후 Run마다 진척 업데이트. |
| `BLOCKED` | 필수 evidence/log/metric/baseline이 없어 판정 불가. BLOCKER 해소 전 status 변경 금지. | YES | blocker 해소 + Evidence Card 부분 채우기. |
| `DEAD_COLLAPSED` | baseline/ablation으로 collapse 확정. ablation delta = 0 또는 SOURCE_ONLY로 확정. | NO | Phase 11 ablation artifact path가 `experiment_evidence`에 기재된 경우에만 가능. |
| `SUPERSEDED` | 더 강한 개념으로 대체됨. 대체 개념 명시 필수. | YES | 대체 concept ID + 대체 rationale 필수 기재. |
| `UNKNOWN_NEEDS_EXPERIMENT` | 측정 자체가 불가능하거나, 개념 정의 자체가 실험에 의존. | YES | required experiment 명시 필수. |

**Run 2에서 허용되는 status**: `CONDITIONAL_ALIVE`, `BLOCKED`, `SUPERSEDED`, `UNKNOWN_NEEDS_EXPERIMENT` 4개만.  
`ALIVE_WITH_EVIDENCE`, `DEAD_COLLAPSED`는 Phase 11 이후에만 허용.

---

## Section 3. Evidence Card Schema (18개 필수 필드)

각 Evidence Card는 아래 18개 필드를 포함한다.

| 번호 | 필드명 | 의미 | 필수 여부 | Run 2에서 채울 수 있는가? | 채워야 하는 시점 |
|---|---|---|---|---|---|
| 1 | `concept_id` | 개념 식별자 (C1~C6, 또는 서브 개념) | 필수 | YES | Phase 3 (Run 2) |
| 2 | `claim_id` | 연관 논문 claim ID (FRCG-WM 계약 내 claim 번호) | 필수 | YES | Phase 3 (Run 2) |
| 3 | `current_status` | 현재 Status Taxonomy 값 | 필수 | YES (BLOCKED 또는 CONDITIONAL_ALIVE만) | Phase 3 (Run 2) — 잠정값만 |
| 4 | `source_evidence` | paper_context_ref MD anchor (파일명 + 섹션 + line 번호) | 필수 | YES | Phase 3 (Run 2) |
| 5 | `design_evidence` | Run 1/Run 2 docs anchor (DEC, 01, 02, 03 파일 참조) | 필수 | YES | Phase 3 (Run 2) |
| 6 | `code_evidence` | `src/frcgw/` 경로 + 함수/클래스 심볼. 구현 전에는 `MISSING` | 조건부 | NO (구현 전) | Phase 8/9 (Run 4) |
| 7 | `test_evidence` | 테스트 파일 경로 + 테스트 함수명 + 마지막 green commit hash. 구현 전에는 `MISSING` | 조건부 | NO (테스트 작성 전) | Phase 6/8 (Run 3/4) |
| 8 | `experiment_evidence` | artifact 경로 (`outputs/runs/` 하위). 실험 전에는 `MISSING` | 조건부 | NO (실험 전) | Phase 11 (Run 6) |
| 9 | `counter_evidence` | 반증 가능한 ablation 결과 경로 또는 예상 collapse 조건. 실험 전에는 설계만 기재. | 필수 | YES (설계 수준) | Phase 3 (설계) → Phase 11 (실제) |
| 10 | `required_metric` | 이 concept 생존을 판정하기 위해 반드시 계산해야 하는 metric ID | 필수 | YES | Phase 3 (Run 2) |
| 11 | `required_baseline` | 이 concept과 비교해야 하는 baseline ID (BASE-XXX) | 필수 | YES | Phase 3 (Run 2) |
| 12 | `required_ablation` | 이 concept을 검증하기 위해 반드시 실행해야 하는 ablation ID (ABL-XXX) | 필수 | YES | Phase 3 (Run 2) |
| 13 | `required_split` | 이 concept 검증을 위해 필요한 데이터 분할 방법 (crossed split 등) | 조건부 | YES | Phase 3 (Run 2) |
| 14 | `required_future_run` | 이 card를 채우기 위해 필요한 미래 Run 번호 (Run 3~6) | 필수 | YES | Phase 3 (Run 2) |
| 15 | `blocker` | 현재 status 변경을 막는 blocking issue. BLOCKED가 아니면 `none`. | 필수 | YES | Phase 3 (Run 2) |
| 16 | `decision_rationale` | 잠정 status를 내린 이유. 한국어 2~3문장. Evidence에 근거한 정성적 설명. | 필수 | YES | Phase 3 (Run 2) |
| 17 | `last_updated` | 마지막 업데이트 날짜 (YYYY-MM-DD) | 필수 | YES | 매 업데이트 시 갱신 |
| 18 | `owner_phase` | 이 card를 최종 완성해야 하는 Phase 번호 (Phase 3~12) | 필수 | YES | Phase 3 (Run 2) |

> **주의**: Evidence Card stub에는 위 18개 필드 외에 `survival_path`와 `collapse_condition` 2개 필드를 추가 포함한다. stub level에서 claim 생존/붕괴 시나리오를 명시하기 위함이다.

---

## Section 4. Status Transition Rules (10개)

1. **Evidence Card 없는 status 변경 금지**: status 변경 commit에는 반드시 `evidence_card: updated` 태그와 Evidence Card 갱신이 동반되어야 한다. Evidence Card 없이 status만 변경하는 commit은 reject 사유다.

2. **`ALIVE_WITH_EVIDENCE`는 Phase 11 full eval 이후에만 가능**: `outputs/runs/p3_lr_eval/metrics.json` artifact path가 `experiment_evidence`에 기재된 경우에만 허용. Phase 11 gate 통과 전 `ALIVE_WITH_EVIDENCE` 선언 금지.

3. **`DEAD_COLLAPSED`는 ablation/baseline artifact가 있을 때만 가능**: Phase 11 ablation 결과 파일 path가 `counter_evidence`에 기재된 경우에만 허용. ablation delta = 0 확정 전 `DEAD_COLLAPSED` 선언 금지.

4. **C1은 `h_exec` trace 없이는 ALIVE 불가**: `selected_hypothesis_id` 필드가 step log에 populate되고 MET-PERSIST-001이 계산 가능해질 때까지 C1의 `ALIVE_WITH_EVIDENCE` 불가. 근거: `reviewer2_20260516_R1.md` Attack 2 (REF-PROBLEM-012).

5. **C2는 crossed split + ABL-001 + latent probe 없이는 ALIVE 불가**: `generate_same_regime_diff_grammar_episodes()` 구현, ABL-001 (no_regime) 존재, MET-LATENT-001 (latent_factorization_probe) 계산 전에 C2 `ALIVE_WITH_EVIDENCE` 불가. 근거: `math_critic_20260516_R1.md` C2 CRITICAL.

6. **C3는 LR scorer 구현 + BCE/Verifier comparison 없이는 ALIVE 불가**: `src/frcgw/falsification/lr_scorer.py` 구현 + `tests/test_lr_scorer.py` green + ABL-022/ABL-023 비교 실험 전에 C3 `ALIVE_WITH_EVIDENCE` 불가. 근거: `math_critic_20260516_R1.md` C3 RISK HIGH.

7. **C4는 MET-WM-001/MET-ALT-001 없이는 ALIVE 불가**: `rollout_fidelity()`, `alternative_adoption_rate()` 함수 구현 + Phase 11 계산 전에 C4 `ALIVE_WITH_EVIDENCE` 불가. 근거: `claim_align_20260516_R1.md` C4 CRITICAL.

8. **C5는 ABL-017 + rewrite metric 없이는 ALIVE 불가**: ABL-017 (no_L_intent_action_mapping) 구현 + MET-REWRITE-001 계산 전에 C5 `ALIVE_WITH_EVIDENCE` 불가. 근거: `claim_align_20260516_R1.md` C5 PARTIAL.

9. **C6는 CATTS/WebUncertainty-style compute baseline 없이는 ALIVE 불가**: BASE-015 (ComputeMatchedRandomReallocation) + ABL-023 (uncertainty instead of falsification) 비교 실험 전에 C6 `ALIVE_WITH_EVIDENCE` 불가. 근거: `novelty_scout_20260516_R1.md` THREAT-01/03.

10. **`P3_EVAL.passed`는 superseded evidence로 취급**: `P3_EVAL.BLOCKED_planning_calls_zero.md`가 `P3_EVAL.passed`를 supersede한다. `P3_EVAL.passed`를 논문 claim 근거로 사용 금지. Phase 11 gate 통과 후 새 sentinel `P3_LR_EVAL.passed`를 사용한다. 근거: `war_room_R1_synthesis.md` Consensus Item 5.

---

## Section 5. C1~C6 Evidence Card Stub

> **Run 2 preliminary status, final 판정 아님.**  
> 이 섹션의 모든 status는 잠정값이다. Phase 11 Evidence Card 완성 전까지 ALIVE/DEAD 확정 불가.

---

### Card-C1: wrong-control-grammar persistence

| 필드 | 내용 |
|---|---|
| `concept_id` | C1 |
| `claim_id` | wrong-control-grammar-persistence; CLAIM-02-001 (02_PROBLEM_NOVELTY_FALSIFICATION.md) |
| `current_status` | **BLOCKED** (Run 2 preliminary, final 판정 아님) |
| `source_evidence` | `paper_context_ref/02_PROBLEM_NOVELTY_FALSIFICATION.md §2 (wrong-control-grammar persistence definition)`; `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §5 Symbol Table line 123 (h_exec definition)` |
| `design_evidence` | `docs/orchestration/lr_alignment/DEC_OPTION_B_LR_ALIGNMENT.md §2.4` (h_exec trace missing); `docs/orchestration/lr_alignment/02_option_b_design_plan.md §6 C1 row` (BLOCKED); `docs/orchestration/agent_reports/2026-05/reviewer2_20260516_R1.md` Attack 2 REF-PROBLEM-012 |
| `code_evidence` | `src/frcgw/evaluation/metrics.py:78` (MET-PERSIST-001 구현 확인); `src/frcgw/models/grammar.py:201-222` (is_wrong_grammar_failure — oracle hidden_state_flags 의존 확인 필요); `selected_hypothesis_id` log field: **MISSING** |
| `test_evidence` | `tests/test_metrics_compute_wrong_grammar_persistence` — MISSING (stub 작성 전); `tests/test_forbidden_field_mirror_sync.py` — green (관련 필드 leakage 감시) |
| `experiment_evidence` | `outputs/runs/p3_ablations/ablation_results.json` — INVALID (planning_calls=0 across all 5 seeds); `outputs/phase_gates/P3_EVAL.BLOCKED_planning_calls_zero.md` — SUPERSEDE 증거 |
| `counter_evidence` | ABL-002 (no-control-grammar)에서 FRCG-FULL 동일 성능이면 DEAD_COLLAPSED 조건 성립. ABL-022 (no falsification score gate)에서 복구 지연 감소 없으면 persistence claim 약화. 현재 ablation_results.json에서 FRCG-FULL = no_control_grammar (Δ=0) — 반증 가능 |
| `required_metric` | MET-PERSIST-001 (wrong_control_grammar_persistence) — Phase 11; MET-BELIEF-001 (belief_update_delay) — Phase 11; MET-FAIL-002 (failure repetition rate) — Phase 11 |
| `required_baseline` | BASE-001 (FrozenBaseLLM); BASE-005 (VerifierOnlyAgent — real implementation 필요, 현재 string-length heuristic); BASE-loop-heuristic (VLAA-GUI style) |
| `required_ablation` | ABL-002 (no-control-grammar) — IMPLEMENTED; ABL-022 (no falsification score gate) — MISSING; ABL-011 (no-action-effect-log) — MISSING |
| `required_split` | standard train/val/test split 충분. 단, h_exec trace 없이는 측정 자체가 불가 |
| `required_future_run` | Run 4 (Phase 8): `selected_hypothesis_id` step log populate + MET-PERSIST-001 실계산; Run 6 (Phase 11): Evidence Card 완성 + ALIVE/DEAD 판정 |
| `blocker` | **CRITICAL**: `selected_hypothesis_id` 필드가 step log에 populate되지 않음 → MET-PERSIST-001 계산 불가. P3_EVAL invalid (planning_calls=0). h_exec trace 없이 persistence 주장 불가. |
| `decision_rationale` | War Room R1에서 reviewer2가 Attack 2 (REF-PROBLEM-012)로 지적한 바와 같이, `selected_hypothesis_id` 없이는 어떤 hypothesis가 action 생성에 사용됐는지 추적 불가능하다. P3_EVAL.BLOCKED_planning_calls_zero.md는 현 구현이 planning_calls=0으로 mechanism을 전혀 실행하지 않음을 보여주므로, evidence가 없는 상태다. C1은 h_exec trace populate(Phase 8) + MET-PERSIST-001 실계산(Phase 11) 이후에만 생존 판정이 가능하다. |
| `last_updated` | 2026-05-16 |
| `owner_phase` | Phase 12 (최종 판정); Phase 8 (h_exec trace populate) |
| `survival_path` | Phase 8에서 `selected_hypothesis_id`를 step log에 populate → Phase 11에서 MET-PERSIST-001 계산 → wrong-grammar hypothesis persistence가 BASE-001/BASE-005보다 통계적으로 유의미하게 높은 episode 수를 보임 → ABL-002에서 FRCG-FULL이 no_control_grammar보다 persistence 감소가 확인됨 |
| `collapse_condition` | Phase 11에서 ABL-002 (no-control-grammar)와 FRCG-FULL의 MET-PERSIST-001 값이 통계적 동등성 검증 통과 (Δ ≈ 0) → C1 DEAD_COLLAPSED |

---

### Card-C2: regime/control-grammar separation

| 필드 | 내용 |
|---|---|
| `concept_id` | C2 |
| `claim_id` | regime-control-grammar-separation; COLLAPSE-07-001 (07_LATENT_ARCHITECTURE_DESIGN.md:370-371) |
| `current_status` | **BLOCKED** (Run 2 preliminary, final 판정 아님) |
| `source_evidence` | `paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md:370-371` (COLLAPSE-07-001); `:77` (Locatello impossibility 1811.12359); `:142` (z_regime: PRIMARY_LATENT_CONTESTED); `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.1 line 142` (b_t learned approximation) |
| `design_evidence` | `docs/orchestration/agent_reports/2026-05/math_critic_20260516_R1.md` C2 CRITICAL (Locatello impossibility, 1:1 mapping risk); `docs/orchestration/agent_reports/2026-05/claim_align_20260516_R1.md` C2 CRITICAL GAPS (ABL-001 missing); `docs/orchestration/lr_alignment/02_option_b_design_plan.md §4.3` (PosteriorUpdater failure mode — posterior collapse known risk) |
| `code_evidence` | `src/frcgw/models/grammar.py:14-23` (ControlGrammar Enum — potential 1:1 regime-grammar mapping 위험); `src/frcgw/evaluation/ablations.py` (ABL-001 no_regime: **MISSING**); crossed split 생성 함수: **MISSING** |
| `test_evidence` | ABL-001 관련 테스트: **MISSING**; MET-LATENT-001 테스트: **MISSING**; crossed split 테스트: **MISSING** |
| `experiment_evidence` | MISSING — latent probe 실험 미실행; crossed split dataset 미생성 |
| `counter_evidence` | ABL-003 (merged regime-grammar) ablation에서 MI probe가 분리 불가를 보이면 DEAD_COLLAPSED 조건 성립. ABL-006 (collapsed latent)에서 성능 차이 없으면 factorization claim 약화. 현재 grammar.py:14-23 ControlGrammar Enum 구조가 1:1 mapping이면 이론적으로 DEAD_COLLAPSED. |
| `required_metric` | MET-LATENT-001 (latent_factorization_probe) — Phase 11; MET-OOD-003 (ood_grammar_performance) — Phase 11; MET-REC-001 (regime recombination accuracy) — 구현됨 |
| `required_baseline` | BASE-009 (NextStateWMOnlyAgent) — 구현됨; BASE-013 (TreeSearchAgent) — MISSING |
| `required_ablation` | ABL-001 (no_regime) — **MISSING** (CRITICAL); ABL-003 (merged regime-grammar) — 구현됨; ABL-006 (collapsed latent) — 구현됨 |
| `required_split` | **crossed split 필수**: `generate_same_regime_diff_grammar_episodes()` 구현 필요; `generate_same_grammar_diff_regime_episodes()` 구현 필요 — 현재 둘 다 MISSING |
| `required_future_run` | Run 5 (Phase 10): ABL-001 구현 + crossed split 생성; Run 6 (Phase 11): latent probe + MET-LATENT-001 계산 |
| `blocker` | **CRITICAL**: (1) Locatello impossibility — 비선형 ICA 특성상 regime/grammar 분리가 이론적으로 보장되지 않음. (2) ABL-001 (no_regime) 미구현 — C2 factorization 검증 자체 불가. (3) crossed split 부재 — same regime/diff grammar 조합 에피소드 없음. (4) grammar.py:14-23 1:1 대응 위험 미해소. |
| `decision_rationale` | math_critic이 C2를 CONDITIONAL_CRITICAL로 판정한 근거는 Locatello impossibility 때문이다 — 비선형 ICA에서 regime과 grammar가 동시에 식별 가능한지 이론적 보장이 없다. ABL-001 없이는 regime 요인의 독립적 기여를 실험적으로 분리할 수 없으며, crossed split 없이는 "same regime, different grammar" 에피소드를 생성할 수 없어 factorization 주장이 공허하다. C2는 논문의 high-risk architecture hypothesis로 유지하되, Phase 10 ABL-001 구현 + Phase 11 latent probe 결과 이전에는 생존 판정이 불가능하다. |
| `last_updated` | 2026-05-16 |
| `owner_phase` | Phase 12 (최종 판정); Phase 10 (ABL-001 구현, crossed split 생성) |
| `survival_path` | Phase 10에서 ABL-001 구현 + crossed split 생성 → Phase 11에서 MET-LATENT-001 latent probe가 regime/grammar separation을 MI > threshold로 보임 → ABL-003에서 merged가 full보다 유의미하게 낮은 성능 → C2 CONDITIONAL_ALIVE 또는 ALIVE_WITH_EVIDENCE |
| `collapse_condition` | Phase 11에서 latent probe MI ≈ 0 (separation 불가) 또는 ABL-003 (merged regime-grammar)가 FRCG-FULL과 통계적 동등성 → C2 DEAD_COLLAPSED |

---

### Card-C3: likelihood-ratio falsification mechanism

| 필드 | 내용 |
|---|---|
| `concept_id` | C3 |
| `claim_id` | likelihood-ratio-falsification; L-MAIN-005 (08_LOSS_REWARD_TRAINING_OBJECTIVE.md:208); F_t definition (09_PLANNING_THEORY_ALGORITHM.md:172) |
| `current_status` | **CONDITIONAL_ALIVE** (Run 2 preliminary, final 판정 아님) |
| `source_evidence` | `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.3 line 171-172` (F_t = max_{h_alt}[ell(h_alt)-ell(h_exec)]); `paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md:208` (L-MAIN-005 현재 BCE 구현); `paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md lines 343,347` (LR scorer 인용) |
| `design_evidence` | `docs/orchestration/lr_alignment/DEC_OPTION_B_LR_ALIGNMENT.md §2.2` (C3 LR Theory vs BCE Implementation Gap); `docs/orchestration/lr_alignment/02_option_b_design_plan.md §4.2` (LikelihoodRatioFalsificationScorer I/O contract); `docs/orchestration/agent_reports/2026-05/math_critic_20260516_R1.md` C3 CONDITIONAL (theory-implementation gap); `docs/orchestration/lr_alignment/00_OPTION_B_PHASE_ROADMAP.md §3.1` (Option B ADOPTED) |
| `code_evidence` | `src/frcgw/evaluation/ablations.py:121` (ABL-016 no L_falsification — 구현됨); `src/frcgw/evaluation/ablations.py:137` (ABL-023 uncertainty instead — 구현됨); `src/frcgw/falsification/lr_scorer.py` — **MISSING** (Phase 8 구현 대상); `BCEBinaryFalsificationScorer` 현재 구현 위치 — Phase 5 계약에서 확정 예정 |
| `test_evidence` | `tests/test_lr_scorer_stub.py` — MISSING (Phase 6 stub 작성 예정); `tests/test_forbidden_field_mirror_sync.py` — green (관련 leakage 감시); `tests/test_ablation_runner.py` — ABL-022 standalone 미등록으로 count 미반영 |
| `experiment_evidence` | MISSING — LR scorer 구현 전 실험 불가; ABL-022/023 비교 실험 미실행 |
| `counter_evidence` | ABL-016 (no L_falsification)에서 성능 차이 없으면 falsification claim 약화. ABL-022 (no falsification score gate)에서 FRCG-FULL과 차이 없으면 F_t gate 자체가 불필요하다는 반증. ABL-023 (uncertainty instead of falsification)에서 uncertainty gate와 LR gate가 동등한 성능이면 "LR과 uncertainty의 차이 없음" — C3 핵심 구분 붕괴. |
| `required_metric` | MET-FALS-001 (falsification_precision) — 구현됨; MET-FALS-002 (falsification_recall) — 구현됨; MET-CAL-001 (falsification calibration) — 구현됨 |
| `required_baseline` | BASE-005 (VerifierOnlyAgent — real implementation 필요); BASE-006 (VerifierHeuristicRecoveryAgent) — MISSING; BASE-012 (UncertaintyGatedAgent) — 구현됨 |
| `required_ablation` | ABL-016 (no L_falsification) — 구현됨; ABL-022 (no falsification score gate) — **MISSING** (C1과 공유); ABL-023 (uncertainty instead of falsification) — 구현됨 |
| `required_split` | standard split 충분. 단 high-confidence wrong grammar episode dataset 구성 필요 (CATTS/WebUncertainty 방어용) |
| `required_future_run` | Run 3 (Phase 5): LR scorer I/O contract 확정; Run 4 (Phase 8): `lr_scorer.py` 구현 + planning_calls > 0; Run 6 (Phase 11): ABL-022/023 비교 + ALIVE/DEAD 판정 |
| `blocker` | **HIGH**: LR scorer 미구현. ABL-022 (no falsification score gate) standalone 미등록. 현재 L-MAIN-005 BCE와 F_t 이론의 불일치 → narrative만으로는 해소 불가 (DEC_OPTION_B_LR_ALIGNMENT.md §2.2). Option B 채택으로 방향 확정됐으나 구현은 Phase 8까지 유보. |
| `decision_rationale` | C3은 이론 (`F_t = max_alt[ell(h_alt)-ell(h_exec)]`)이 paper_context_ref/09에 완전히 정의되어 있고, Option B 채택으로 `LikelihoodRatioFalsificationScorer`를 main path로 구현하기로 결정했으므로 설계상 생존 경로가 명확하다. 그러나 `lr_scorer.py`가 아직 구현되지 않았으며, ABL-022 standalone이 없어 실험적 검증이 불가능하다. `CONDITIONAL_ALIVE`는 이론/설계 증거가 충분하지만 code/test/experiment 증거가 모두 미완성인 상태를 반영한다. |
| `last_updated` | 2026-05-16 |
| `owner_phase` | Phase 12 (최종 판정); Phase 8 (lr_scorer.py 구현) |
| `survival_path` | Phase 8에서 `lr_scorer.py` 구현 + planning_calls > 0 달성 → Phase 11에서 ABL-022 비교에서 LR scorer가 falsification gate 없는 것보다 유의미한 성능 향상 → ABL-023 비교에서 LR gate가 uncertainty gate보다 high-confidence wrong grammar episode에서 우수 → VeriGUI/VLAA-GUI 대비 MET-FALS-001/002 우위 → C3 ALIVE_WITH_EVIDENCE |
| `collapse_condition` | Phase 11에서 ABL-023 (uncertainty instead of falsification)이 FRCG-FULL과 통계적 동등성 (Δ ≈ 0) → LR과 uncertainty의 차이 없음 → C3 핵심 distinction 붕괴 → DEAD_COLLAPSED 조건 |

---

### Card-C4: alternative grammar rollout

| 필드 | 내용 |
|---|---|
| `concept_id` | C4 |
| `claim_id` | alternative-grammar-rollout; V(a,h) definition (09_PLANNING_THEORY_ALGORITHM.md §6.4); ΔV_t (§6.5) |
| `current_status` | **BLOCKED** (Run 2 preliminary, final 판정 아님) |
| `source_evidence` | `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.4 lines 186-197` (V(a,h) grammar-conditioned value); `paper_context_ref/09 §8 PROP-01..10` (grammar property enumeration); `paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md §5` (Rollout Model architecture) |
| `design_evidence` | `docs/orchestration/lr_alignment/02_option_b_design_plan.md §4.4` (DecisionRelevanceGate I/O); `docs/orchestration/agent_reports/2026-05/claim_align_20260516_R1.md` C4 CRITICAL GAPS (MET-WM-001/ALT-001 missing); `docs/orchestration/agent_reports/2026-05/math_critic_20260516_R1.md` C4 CONDITIONAL (horizon + counterfactual supervision) |
| `code_evidence` | `src/frcgw/evaluation/ablations.py:157` (ABL-024 no-alternative-hypothesis — 구현됨); `src/frcgw/evaluation/ablations.py:185` (ABL-026 no-rollout — 구현됨); MET-WM-001 (`rollout_fidelity()`): **MISSING**; MET-ALT-001 (`alternative_adoption_rate()`): **MISSING** |
| `test_evidence` | ABL-024/026 관련 테스트 — ablation_runner.py에서 count 확인 필요; MET-WM-001/ALT-001 테스트: **MISSING** |
| `experiment_evidence` | MISSING — rollout_steps=0 in current P3 runs; predicted_rollout tracking 미구현 |
| `counter_evidence` | ABL-024 (no-alternative-hypothesis)에서 성능 차이 없으면 alternative grammar hypothesis가 불필요하다는 반증. BASE-028 (WebWorld-style: grammar-agnostic next-state WM)과 FRCG-FULL이 동등하면 grammar conditioning의 가치 없음. ABL-026 (no-rollout)에서 차이 없으면 rollout 자체가 불필요 → C4 DEAD_COLLAPSED 조건. |
| `required_metric` | MET-WM-001 (rollout_fidelity) — **MISSING** (CRITICAL); MET-ALT-001 (alternative_adoption_rate) — **MISSING** (CRITICAL); MET-REC-001 (regime recombination accuracy) — 구현됨 |
| `required_baseline` | BASE-009 (NextStateWMOnlyAgent) — 구현됨; BASE-013 (TreeSearchAgent) — MISSING; BASE-028 (WebWorld-style) — MISSING |
| `required_ablation` | ABL-024 (no-alternative-hypothesis) — 구현됨; ABL-026 (no-rollout) — 구현됨; ABL-036 (no_counterfactual_target) — **MISSING** |
| `required_split` | standard split + rollout horizon ablation (H=1,2,3,5) 비교 필요. `paper_context_ref/09 §6.4` 기본 H=3. |
| `required_future_run` | Run 4 (Phase 8): MET-WM-001/ALT-001 구현 + rollout_steps > 0 달성; Run 5 (Phase 10): BASE-028 구현 + ABL-036 추가; Run 6 (Phase 11): Evidence Card 완성 |
| `blocker` | **CRITICAL**: (1) MET-WM-001 (rollout_fidelity) 미구현 — mechanism metric 완전 부재. (2) MET-ALT-001 (alternative_adoption_rate) 미구현. (3) BASE-028 (WebWorld-style) 미구현 — WebWorld (THREAT-04) 방어 불가. (4) rollout_steps=0 in current P3 — 구현 자체가 동작하지 않음. |
| `decision_rationale` | C4의 핵심 claim은 grammar-conditioned alternative hypothesis rollout이 grammar-agnostic rollout보다 우수하다는 것이다. 그런데 MET-WM-001 (rollout_fidelity)과 MET-ALT-001 (alternative_adoption_rate)이 모두 미구현 상태이고, 현재 P3에서 rollout_steps=0이므로 mechanism 자체가 동작하지 않는다. CUWM (THREAT-06)과 WebWorld (THREAT-04) 방어를 위한 BASE-027/028도 미구현이어서 direct threat response가 불가능하다. C4는 Phase 8에서 mechanism을 먼저 살려야 논의가 가능하다. |
| `last_updated` | 2026-05-16 |
| `owner_phase` | Phase 12 (최종 판정); Phase 8 (MET-WM-001/ALT-001 구현); Phase 10 (BASE-028 구현) |
| `survival_path` | Phase 8에서 MET-WM-001/ALT-001 구현 + rollout_steps > 0 → Phase 10에서 BASE-028 구현 → Phase 11에서 MET-WM-001 기준 grammar-conditioned rollout이 grammar-agnostic (BASE-028)보다 fidelity 높음 확인 → ABL-024에서 no-alternative-hypothesis가 full보다 유의미하게 낮은 성능 → C4 ALIVE_WITH_EVIDENCE |
| `collapse_condition` | Phase 11에서 BASE-028 (WebWorld-style)과 FRCG-FULL의 MET-WM-001 값 통계적 동등성 → grammar conditioning의 rollout 이점 없음 → C4 DEAD_COLLAPSED |

---

### Card-C5: grammar-conditioned rewrite

| 필드 | 내용 |
|---|---|
| `concept_id` | C5 |
| `claim_id` | grammar-conditioned-rewrite; `a_exec = Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*)` (09_PLANNING_THEORY_ALGORITHM.md §6.6) |
| `current_status` | **CONDITIONAL_ALIVE** (Run 2 preliminary, final 판정 아님) |
| `source_evidence` | `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.6` (Rewrite formula); `paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md:209` (L-MAIN-006 L_intent_action_mapping); `paper_context_ref/09 §8 PROP-01..10` (grammar property: intent-to-action mapping) |
| `design_evidence` | `docs/orchestration/lr_alignment/02_option_b_design_plan.md §4.5` (GrammarConditionedRewrite I/O contract); `docs/orchestration/agent_reports/2026-05/math_critic_20260516_R1.md` C5 CONDITIONAL (best claim mathematically); `docs/orchestration/agent_reports/2026-05/claim_align_20260516_R1.md` C5 PARTIAL (ABL-017 missing) |
| `code_evidence` | `src/frcgw/evaluation/ablations.py:198` (ABL-035 no-action-rewrite — 구현됨); `src/frcgw/evaluation/metrics.py:204` (MET-SWITCH-001 — 구현됨); `GrammarConditionedRewrite` module: **MISSING** (Phase 8 구현 대상); ABL-017 (no_L_intent_action_mapping): **MISSING** |
| `test_evidence` | ABL-035 관련 테스트 — ablation_runner.py에서 count 확인 필요; ABL-017 테스트: **MISSING**; MET-REWRITE-001 테스트: **MISSING** |
| `experiment_evidence` | MISSING — Rewrite module 미구현 상태로 실험 불가 |
| `counter_evidence` | ABL-017 (no_L_intent_action_mapping)에서 rewrite 모듈이 있어도 훈련 손실 없으면 grammar conditioning 학습 불가. ABL-035 (no-action-rewrite)에서 성능 차이 없으면 rewrite 자체가 불필요 → C5 DEAD_COLLAPSED 조건. BASE-026 (WAC-style)과 FRCG-FULL이 동등하면 "grammar-conditioned rewrite ≠ generic correction" 구분 불가. |
| `required_metric` | MET-REWRITE-001 (rewrite_success_rate) — **MISSING**; MET-SWITCH-001 (action switch delay) — 구현됨; MET-FAIL-002 (failure repetition rate) — 구현됨 |
| `required_baseline` | BASE-003 (AlwaysRetryAgent) — 구현됨; BASE-004 (BaseLLMSelfCorrectionAgent) — MISSING; BASE-006 (VerifierHeuristicRecovery) — MISSING; BASE-026 (WAC-style) — MISSING |
| `required_ablation` | ABL-017 (no_L_intent_action_mapping) — **MISSING** (CRITICAL: loss-level ablation, training/inference 분리 불가); ABL-035 (no-action-rewrite) — 구현됨 |
| `required_split` | standard split. grammar conditioning 효과 측정을 위해 multiple grammar per task episode 포함 필요 |
| `required_future_run` | Run 4 (Phase 8): `GrammarConditionedRewrite` 구현 + MET-REWRITE-001; Run 5 (Phase 10): ABL-017 추가 + BASE-026 구현; Run 6 (Phase 11): Evidence Card 완성 |
| `blocker` | **HIGH**: ABL-017 (no_L_intent_action_mapping) 미구현 — training level에서 grammar conditioning이 learning에 기여하는지 측정 불가. MET-REWRITE-001 미구현. BASE-026 (WAC-style) 미구현 — WAC (THREAT-05) 방어 불가. 단, 수식 명확 + ABL-035 구현됨으로 `BLOCKED`가 아닌 `CONDITIONAL_ALIVE` 판정. |
| `decision_rationale` | C5는 math_critic이 "best claim mathematically"로 판정한 claim으로, `Rewrite(intent, base, h*)` 수식이 명확하고 grammar conditioning의 이론적 근거가 탄탄하다. ABL-035 (no-action-rewrite)가 구현되어 있어 일부 검증 경로가 마련되어 있다. 그러나 ABL-017 (training level ablation)이 없어 grammar conditioning이 training에서 실제로 학습되는지 확인할 수 없으며, MET-REWRITE-001 없이는 성공률을 측정할 수 없다. 설계 증거가 충분하므로 `CONDITIONAL_ALIVE`로 잠정 판정한다. |
| `last_updated` | 2026-05-16 |
| `owner_phase` | Phase 12 (최종 판정); Phase 8 (Rewrite 구현, MET-REWRITE-001); Phase 10 (ABL-017, BASE-026) |
| `survival_path` | Phase 8에서 `GrammarConditionedRewrite` 구현 + MET-REWRITE-001 → Phase 10에서 ABL-017 + BASE-026 → Phase 11에서 ABL-017 비교에서 grammar conditioning이 training에 기여함 확인 + WAC-style보다 rewrite_success_rate 우위 → C5 ALIVE_WITH_EVIDENCE |
| `collapse_condition` | Phase 11에서 ABL-017 없이도 ABL-035 (no-action-rewrite)와 FRCG-FULL이 동등 (Δ ≈ 0) → rewrite 자체가 불필요 → C5 DEAD_COLLAPSED; 또는 BASE-026 (WAC-style)과 통계적 동등성 → grammar conditioning 없이도 동일 성능 → C5 DEAD_COLLAPSED |

---

### Card-C6: decision-relevant compute gate

| 필드 | 내용 |
|---|---|
| `concept_id` | C6 |
| `claim_id` | decision-relevant-compute-gate; G_t definition (09_PLANNING_THEORY_ALGORITHM.md §6.5); VOC-style gate |
| `current_status` | **BLOCKED** (Run 2 preliminary, final 판정 아님) |
| `source_evidence` | `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.5 lines 200-209` (G_t 4-way conjunction definition); `paper_context_ref/09 §6.5 ΔV_t formula`; `paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md` (L-AUX-015 L_value_of_computation_proxy: UNKNOWN_NEEDS_EXPERIMENT) |
| `design_evidence` | `docs/orchestration/lr_alignment/01_novelty_theory_threat_audit.md` THREAT-01 (CATTS) + THREAT-03 (WebUncertainty) — G_t ≠ uncertainty gate 구분 필요; `docs/orchestration/lr_alignment/02_option_b_design_plan.md §4.4` (DecisionRelevanceGate I/O, failure modes); `docs/orchestration/agent_reports/2026-05/novelty_scout_20260516_R1.md` THREAT-01 Verdict: MANAGEABLE_WITH_LR |
| `code_evidence` | `src/frcgw/evaluation/ablations.py:137` (ABL-023 uncertainty instead — 구현됨); `src/frcgw/evaluation/ablations.py:234` (ABL-033 no decision-relevance gate — 구현됨); `src/frcgw/evaluation/ablations.py:208` (ABL-034 always-plan — 구현됨); BASE-015 (ComputeMatchedRandomReallocation): **MISSING**; ABL-020 (no_compute_penalty): **MISSING** |
| `test_evidence` | ABL-023/033/034 관련 테스트 — ablation_runner.py count 확인; BASE-015 테스트: **MISSING**; MET-COMP-003 테스트: **MISSING** |
| `experiment_evidence` | MISSING — G_t never fires in current P3 (planning_calls=0); compute-matched experiment 미실행 |
| `counter_evidence` | ABL-023 (uncertainty instead of falsification)에서 uncertainty gate와 LR gate가 통계적 동등 → G_t 4-way conjunction의 falsification 조건이 불필요 → C6 uncertainty로 환원. BASE-015 (ComputeMatchedRandom)과 FRCG-FULL이 동등하면 compute allocation 자체가 무의미 → C6 DEAD_COLLAPSED. CATTS baseline과 compute-matched 비교에서 동등하면 → C6 CATTS로 흡수. |
| `required_metric` | MET-COMP-003 (compute_normalized_return) — **MISSING**; MET-COMP-004 (compute_efficiency_gain) — 구현됨; MET-COMP-007 — 구현됨 |
| `required_baseline` | BASE-010 (AlwaysPlanAgent) — 구현됨; BASE-012 (UncertaintyGatedAgent) — 구현됨; BASE-015 (ComputeMatchedRandomReallocation) — **MISSING** (C6 falsifiability critical); BASE-uncertainty-entropy-gate (CATTS-equivalent) — MISSING |
| `required_ablation` | ABL-020 (no_compute_penalty) — **MISSING** (objective-level); ABL-023 (uncertainty instead of falsification) — 구현됨; ABL-033 (no decision-relevance gate) — 구현됨; ABL-034 (always-plan) — 구현됨 |
| `required_split` | standard split + high-confidence wrong grammar episode dataset (CATTS/WebUncertainty 방어 핵심: uncertainty 낮지만 F_t 높은 에피소드 필요) |
| `required_future_run` | Run 5 (Phase 10): BASE-015 + ABL-020 구현; Run 6 (Phase 11): compute-matched experiment + CATTS baseline 비교 |
| `blocker` | **HIGH**: (1) CATTS (THREAT-01) + WebUncertainty (THREAT-03) 미등록/미방어 — compute gate novelty claim이 uncertainty gate로 흡수될 위험. (2) BASE-015 (ComputeMatchedRandom) 미구현 — C6 falsifiability 없음. (3) planning_calls=0 in P3 — G_t 자체가 동작하지 않음. (4) G_t 4개 threshold (τ_f, τ_v, τ_a + C_plan) calibration 방법 미명시 (math_critic C6 HIGH). |
| `decision_rationale` | C6의 핵심 구분점은 G_t = F_t ∧ ΔV_t ∧ P_switch ∧ cost-benefit이 uncertainty > threshold와 다르다는 것이다. 그런데 CATTS (THREAT-01)와 WebUncertainty (THREAT-03)가 모두 uncertainty 기반 compute gate를 +9.1% WebArena-Lite 성능 향상으로 보여주고 있어, compute gating 자체는 이미 선점된 상태다. BASE-015 없이는 compute-matched 비교가 불가능하고, planning_calls=0이어서 G_t 자체가 동작하지 않는다. C6는 Option B LR scorer 구현 이후에야 CATTS와의 구분 실험이 가능하다. |
| `last_updated` | 2026-05-16 |
| `owner_phase` | Phase 12 (최종 판정); Phase 10 (BASE-015, ABL-020 구현); Phase 11 (compute-matched experiment) |
| `survival_path` | Phase 10에서 BASE-015 + ABL-020 구현 → Phase 11에서 high-confidence wrong grammar episode에서 CATTS/WebUncertainty-style은 gate 미발동, G_t는 발동 확인 → MET-COMP-003 기준 compute-matched 성능 우위 → ABL-023과 통계적 유의미 차이 → C6 ALIVE_WITH_EVIDENCE |
| `collapse_condition` | Phase 11에서 ABL-023 (uncertainty instead of falsification)과 FRCG-FULL이 통계적 동등성 → LR과 uncertainty의 차이 없음 → C6 DEAD_COLLAPSED; 또는 CATTS-equivalent baseline과 compute-matched 비교에서 동등 → compute gate novelty 없음 → C6 DEAD_COLLAPSED |

---

## Section 6. Claim Survival Strategy

### 6.1 Primary survival axis (핵심 주장 — 약화 금지)

**C1/C3/C5는 primary survival axis다.**

| Claim | 왜 중요한가 | 현재 blocker | 어떻게 살릴 수 있는가 | 어떤 실험에서 죽는가 |
|---|---|---|---|---|
| **C1** wrong-grammar persistence | FRCG-WM의 문제 정의 자체가 C1에 의존. C1 없이는 "wrong grammar hypothesis가 persistent하다"는 motivating observation 자체가 사라짐 | `selected_hypothesis_id` 미populate → MET-PERSIST-001 불가 | Phase 8 h_exec trace populate → Phase 11 persistence metric 계산 | ABL-002 (no-control-grammar)와 FRCG-FULL의 MET-PERSIST-001 값이 Δ ≈ 0 |
| **C3** LR falsification | Option B의 core mechanism. LR scorer가 없으면 VeriGUI/VLAA-GUI 방어 불가. C3 없이는 "왜 LR인가"를 설명할 수 없음 | `lr_scorer.py` 미구현. ABL-022 standalone 미등록. L-MAIN-005 BCE와 이론 불일치 | Option B: Phase 8에서 `lr_scorer.py` 구현 → Phase 11 ABL-022/023 비교 | ABL-023 (uncertainty instead of falsification)과 FRCG-FULL이 통계적 동등 |
| **C5** grammar-conditioned rewrite | 수식 명확 + ABL-035 구현됨. math_critic이 "best claim mathematically"로 판정. WAC (THREAT-05) 방어의 핵심 | ABL-017 미구현, MET-REWRITE-001 미구현, BASE-026 미구현 | Phase 8 Rewrite 구현 + Phase 10 ABL-017 + Phase 11 WAC-style 비교 | ABL-035 (no-action-rewrite)와 FRCG-FULL이 Δ ≈ 0 |

**주의**: primary survival axis claim을 약화하거나 폐기하는 결정은 Phase 11 evidence 없이는 금지다.

### 6.2 Secondary support axis (지원 mechanism — evidence 조건 명확화)

**C4/C6는 supporting mechanism/efficiency claim이다.**

| Claim | 역할 | 현재 blocker | 생존 조건 |
|---|---|---|---|
| **C4** alternative grammar rollout | C3 LR falsification 이후 어떤 alternative grammar를 채택하는가를 결정하는 mechanism. C3 없이는 C4도 없음 | MET-WM-001/ALT-001 미구현, rollout_steps=0, BASE-028 미구현 | Phase 8 MET-WM-001/ALT-001 구현 → Phase 10 BASE-028 → Phase 11 grammar-conditioned rollout fidelity 우위 |
| **C6** decision-relevant compute gate | C3 LR score를 활용해 언제 planning compute를 쓸지 결정. compute efficiency claim. CATTS 방어 핵심 | planning_calls=0, BASE-015 미구현, CATTS/WebUncertainty 미방어 | Phase 10 BASE-015 → Phase 11 high-confidence wrong grammar episode에서 G_t ≠ uncertainty gate 확인 |

### 6.3 High-risk architecture hypothesis (Locatello impossibility 영향)

**C2는 high-risk architecture hypothesis다.**

| Claim | 위험 요인 | 관리 전략 |
|---|---|---|
| **C2** regime/grammar separation | Locatello impossibility: 비선형 ICA에서 regime/grammar 동시 식별 이론적 보장 없음. grammar.py:14-23 1:1 mapping 위험. ABL-001 미구현. crossed split 부재. | primary claim으로 전진하지 않음. ABL-001 + crossed split + latent probe로 경험적 evidence 수집. Phase 11 전에 DEAD_COLLAPSED 선언 금지. ALIVE_WITH_EVIDENCE는 가능하면 좋지만 C1/C3/C5가 먼저임. |

---

## Section 7. Handoff to Run 3~6

### Run 3 (Phase 5/6/7) — Implementation Contract / Test Plan / Eval Gate

이 run에서 채워야 할 evidence fields:
- `code_evidence`: `lr_scorer_stub.py` signature + docstring (stub만, 구현 없음)
- `test_evidence`: `test_lr_scorer_stub.py` + `test_h_exec_trace_stub.py` (stub만)
- C1~C6 card의 `required_future_run` 필드 업데이트 (Phase 5 계약 완성 후)

### Run 4 (Phase 8/9) — LR scorer 구현 + GUI env 연동

이 run에서 채워야 할 evidence fields:
- C1 card: `code_evidence`에 `selected_hypothesis_id` populate 경로 + `test_evidence` 추가
- C3 card: `code_evidence`에 `lr_scorer.py` + `test_evidence`에 `test_lr_scorer.py` green 추가
- C5 card: `code_evidence`에 `GrammarConditionedRewrite` + `test_evidence` 추가
- C4 card: `code_evidence`에 `rollout_fidelity()`, `alternative_adoption_rate()` 추가

### Run 5 (Phase 10) — baseline/ablation 구현

이 run에서 채워야 할 evidence fields:
- C1 card: `required_ablation`의 ABL-022 → IMPLEMENTED로 업데이트
- C2 card: `required_ablation`의 ABL-001 → IMPLEMENTED로 업데이트; `required_split` 채우기
- C4 card: `required_baseline`의 BASE-028 → IMPLEMENTED로 업데이트
- C5 card: `required_ablation`의 ABL-017 → IMPLEMENTED로 업데이트
- C6 card: `required_baseline`의 BASE-015 → IMPLEMENTED로 업데이트

### Run 6 (Phase 11/12) — final survivability decision

이 run에서 채워야 할 evidence fields:
- 모든 card의 `experiment_evidence`: `outputs/runs/p3_lr_eval/` artifact path
- 모든 card의 `counter_evidence`: 실제 ablation 결과 path
- 모든 card의 `current_status`: ALIVE_WITH_EVIDENCE 또는 DEAD_COLLAPSED 또는 CONDITIONAL_ALIVE 최종 판정

---

## Section 8. Phase 3 Verdict

**`LEDGER_READY_FOR_REFACTOR_PLAN`**

근거:
1. Evidence Card schema 18개 필드 확정
2. Status Taxonomy 6단계 + Run 2 허용 status 4개 명시
3. Status Transition Rules 10개 명시 (Phase 11 이전 ALIVE/DEAD 확정 금지 포함)
4. C1~C6 Evidence Card stub 생성 완료 (각 16+2 = 18 필드)
5. C1/C3/C5 primary survival axis + C4/C6 secondary support axis + C2 high-risk architecture hypothesis로 전략 명확화
6. Run 3~6 handoff item 명시

**주의**: "LEDGER_READY_FOR_REFACTOR_PLAN"은 Phase 4 (MD Refactor Patch Plan) 진행이 준비되었다는 의미다. C1~C6의 ALIVE/DEAD 판정이 완료되었다는 의미가 아니다.

---

*생성일: 2026-05-16 / Run 2 / Phase 3 산출물*  
*근거: `docs/orchestration/lr_alignment/00_OPTION_B_PHASE_ROADMAP.md` Section 4 Phase 3, Section 5 Run 2*  
*수정 금지: `paper_context_ref/` 전체 (Phase 4 계획 + 사용자 승인 후)*  
*C1~C6 ALIVE/DEAD 최종 판정 금지: Phase 11 Evidence Card 완성 이후에만 허용*
