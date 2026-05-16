---
file_id: MD-REFACTOR-PATCH-PLAN-R2
title: MD Refactor Patch Plan — Phase 4 산출물
phase: 4 (MD Refactor Patch Plan)
run: 2
date: 2026-05-16
status: PATCH_PLAN
language: ko
type: patch_plan_not_actual_edit
---

# 04_md_refactor_patch_plan.md

**Phase**: 4 — MD Refactor Patch Plan  
**Run**: 2  
**Date**: 2026-05-16  
**Type**: 수정 계획서 (수정본 아님). **이 파일은 paper_context_ref를 수정하지 않는다.**

---

## Section 1. Purpose

이 문서는 **paper_context_ref 수정 완료 보고가 아니다**.

역할:
- Option B 채택 (`DEC_OPTION_B_LR_ALIGNMENT.md`)과 Run 2 ledger (`03_concept_survivability_ledger.md`)에 따라 `paper_context_ref/` 어떤 파일을 어떻게 고쳐야 하는지 **patch plan만 작성**
- 실제 `paper_context_ref/` 수정은 이 Phase에서 절대 하지 않는다
- 수정 순서, 의존성, 사용자 승인 필요 항목을 명시

핵심 방향:
- **약화가 아니라 정렬이다.** Run 2는 claim을 약화/폐기하지 않는다.
- **C1/C3/C5는 primary survival axis다.** 이 세 claim은 약화 금지.
- **C2는 high-risk architecture hypothesis다.** DEAD_COLLAPSED 판정 전까지 유지.
- **C4/C6는 supporting mechanism/efficiency claim이다.** evidence path 명확화.
- **generic WM novelty claim은 줄이되 wrong-hypothesis-aware mechanism claim은 강화한다.**
- **실제 paper_context_ref 수정은 Run 2에서 금지다.**

이 문서에서 절대 하지 않는 것:
- `paper_context_ref/` 임의 수정
- claim을 Evidence 없이 약화/폐기
- 수정 계획 없이 "patch 완료" 선언
- Run 3 이전에 실제 코드 변경

---

## Section 2. Refactor Scope Summary

10개 target file에 대한 요약 표.

| # | Target File | Refactor Need | Option B Impact | Claim Impact | Required Change Type | Risk if Not Updated | Requires User Approval? | Actual Edit Allowed in Run 2? |
|---|---|---|---|---|---|---|---|---|
| 1 | `01_RELATED_WORK_THREAT_MAP.md` | 신규 위협 3건 미등록 (CATTS/VLAA-GUI/WebUncertainty) | 간접 영향 — BASE 요구사항 명시화 | C1/C3/C6 방어 불가 | ADDITIVE (신규 항목 추가) | C6 CATTS 방어 공백, C3 VeriGUI/VLAA-GUI 방어 공백 | YES | NO |
| 2 | `02_PROBLEM_NOVELTY_FALSIFICATION.md` | falsification = binary flag 아님 명확화 필요. high-confidence wrong grammar case 미명시 | LR falsification = F_t 정의가 BC-gap 해소와 연결 | C1/C3 정의 정렬 | CLARIFICATION + ADDITIVE | wrong-grammar persistence가 failure loop/anomaly detection과 혼동될 위험 | YES | NO |
| 3 | `03_CORE_CONCEPT_TAXONOMY.md` | h_exec, H_alt, e_t, ell_t, F_t, b_t, G_t, Rewrite 개념 추가/정렬 | 모든 symbol이 Option B contract과 일치해야 함 | C1~C6 전체 | ADDITIVE + CLARIFICATION | symbol mismatch → implementation contract 불일치 위험 | YES | NO |
| 4 | `06_DATA_SCHEMA_AND_LABELING.md` | 16개 log field 추가 계획 (`selected_hypothesis_id` 등) | Option B LR scorer가 요구하는 log fields 추가 | C1/C3/C5 측정 가능성 | ADDITIVE (log field 추가) | h_exec trace 기록 불가 → MET-PERSIST-001 불가 | YES | NO |
| 5 | `07_LATENT_ARCHITECTURE_DESIGN.md` | LR scorer input/output ↔ latent posterior 연결 명확화. C2 high-risk hypothesis 표시 | Option B LR scorer가 latent posterior module과 어떻게 연결되는지 명시 | C2/C3 architecture alignment | CLARIFICATION | LR scorer가 posterior module과 분리되어 설계될 위험 | YES | NO |
| 6 | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | L-MAIN-005 BCE를 main objective로 두는 현재 표현이 Option B main path와 불일치 | **가장 직접적인 영향**: L-MAIN-005 reframe 또는 보완 필요 | C3 핵심 (LR vs BCE 불일치 해소) | STRUCTURAL REFRAME (main path 재정렬) | math_critic C3 RISK HIGH 미해소 → ICLR reviewer 공격 노출 | YES | NO |
| 7 | `09_PLANNING_THEORY_ALGORITHM.md` | F_t formula 기존 유지 + implementation contract 연결 강화. G_t = uncertainty gate가 아님 명확화 | F_t 수식은 이미 옳음. BCE ↔ LR 연결 표현 정리 | C3/C6 수식 정렬 | CLARIFICATION | G_t가 uncertainty gate와 혼동될 위험 | YES | NO |
| 8 | `10_EVALUATION_BASELINE_ABLATION.md` | BASE-CATTS/BASE-VLAA-loop/BASE-026/027/028 추가. ABL-017/022/023/024/036 필요성 명시 | Option B에서 BASE-026/027/028 비교가 더 중요해짐 | C1~C6 전체 (특히 C3/C4/C5/C6) | ADDITIVE (신규 항목 추가) | direct threat baseline 공백 → ATTACK-DEF-004 불가 | YES | NO |
| 9 | `FINAL_RESEARCH_BLUEPRINT.md` | main thesis가 "generic Web/GUI WM"으로 흐르지 않도록 재정렬. C3 Option B 선택 반영 | Option B 채택 → L-MAIN-005 narrative 업데이트 | C1~C6 전체 claim framing | STRUCTURAL REFRAME (thesis 재정렬) | paper framing이 generic WM으로 흐름 → novelty claim 희석 | YES | NO |
| 10 | `00_MASTER_REFERENCE.md` / `00_CONTEXT_INDEX.md` | Option B routing + LR alignment 경로 추가 여부 판단 | Option B 경로 문서들이 routing에 반영될 필요 있음 | routing 명확성 | ROUTING UPDATE (필요 시) | 새 세션에서 Option B 문서를 찾지 못할 위험 | YES | NO |

---

## Section 3. File-by-File Patch Plan (10개 섹션)

---

### 3.1 `01_RELATED_WORK_THREAT_MAP.md`

**Current Problem**  
CATTS (2602.12276), VLAA-GUI (2604.21375), WebUncertainty (2604.17821) 3개 신규 위협이 등록되지 않음. 2-source confirmed (arXiv + secondary source) 상태로 `01_novelty_theory_threat_audit.md`에는 기술되어 있으나, `paper_context_ref/01_RELATED_WORK_THREAT_MAP.md`에는 반영되지 않음. 직접 위협 WebWorld/WAC/CUWM/VeriGUI의 Option B 기준 distinction 재정렬도 미완성.

**Required Patch**  
- CATTS (2602.12276): C6 위협으로 추가. THREAT-01 defense (G_t ≠ uncertainty gate, high-confidence wrong grammar episode) 반영
- VLAA-GUI (2604.21375): C1/C3 위협으로 추가. THREAT-02 defense (F_t posterior-based ≠ heuristic loop detection) 반영
- WebUncertainty (2604.17821): C6 위협으로 추가. THREAT-03 defense (4-way conjunction ≠ dual-level uncertainty) 반영
- POPPER (2502.09858): UNKNOWN_NEEDS_MORE_SEARCH 상태 유지. 보류. 추가 검토 후 결정.
- 기존 WebWorld/WAC/CUWM/VeriGUI: Option B LR scorer 기준 distinction 명시 강화

**Sections Likely Affected**  
신규 섹션 추가 (CATTS, VLAA-GUI, WebUncertainty); 기존 WebWorld/WAC/CUWM/VeriGUI 섹션의 "distinction" 항목 업데이트

**Claims Affected**  
C1 (VLAA-GUI), C3 (VeriGUI + VLAA-GUI), C6 (CATTS + WebUncertainty)

**Evidence Required Before Finalizing**  
POPPER (2502.09858) 2-source 확인 완료 이후 POPPER 항목 결정 가능. CATTS/VLAA-GUI/WebUncertainty 항목은 2-source 확인 완료 (`01_novelty_theory_threat_audit.md`).

**Proposed Patch Summary**  
CATTS, VLAA-GUI, WebUncertainty를 §2 (신규 위협) 또는 §3 (기존 위협과 distinction 비교)에 추가. 각 항목에 `01_novelty_theory_threat_audit.md`의 THREAT-01/02/03 내용 반영. WebWorld/WAC/CUWM/VeriGUI의 distinction 항목에 Option B LR scorer 기반 distinction 강화.

**Forbidden in This Run**  
실제 파일 수정 금지. POPPER 판정 금지 (UNKNOWN_NEEDS_MORE_SEARCH 유지).

**Future Run to Apply**  
Run 3 또는 Run 4 직전 (사용자 승인 후). 실제 paper_context_ref 수정은 Run 2 이후 별도 승인 필요.

---

### 3.2 `02_PROBLEM_NOVELTY_FALSIFICATION.md`

**Current Problem**  
- "wrong-grammar hypothesis가 high-confidence로 유지되는 episode"가 명시되지 않음 → CATTS/WebUncertainty와의 구분이 불명확
- Falsification이 "failed action flag"로 단순 표현되면 VeriGUI (binary verification)와 distinction이 흐림
- VLAA-GUI (heuristic mode switch)와 FRCG-WM (posterior-based falsification)의 차이가 명시되지 않음

**Required Patch**  
- "High-confidence wrong-grammar episode" 사례 추가: agent가 confident하게 wrong grammar로 action을 선택하지만, LR score F_t는 높은 episode. 이 사례에서 CATTS/WebUncertainty의 uncertainty gate는 작동 안 함.
- Falsification 정의를 LR evidence comparison (`F_t = max_alt[ell(h_alt)-ell(h_exec)]`)으로 명확화. "failed action flag"가 아님을 명시.
- VLAA-GUI와의 distinction 추가: heuristic (repeat count + screen hash) ≠ posterior-based LR falsification
- wrong-grammar persistence가 "failure loop"와 다른 이유 추가: persistence는 external perturbation (StressWeb)이 아닌 internal hypothesis 유지

**Sections Likely Affected**  
§2 (Problem Statement), §3 (Novelty Claims), §4 (Distinction from Existing Methods)

**Claims Affected**  
C1 (persistence ≠ failure loop), C3 (falsification ≠ binary verification, ≠ anomaly detection)

**Evidence Required Before Finalizing**  
Phase 11 실험 결과 전까지 "FRCG-WM이 VLAA-GUI를 능가한다"는 주장은 불가. 문구는 distinction을 명확화하는 수준에 한정.

**Proposed Patch Summary**  
"High-confidence wrong grammar" case를 Example로 추가. Falsification evidence의 definition을 LR score 기반으로 강화. VLAA-GUI/StressWeb distinction paragraph 추가.

**Forbidden in This Run**  
실제 파일 수정 금지. "VLAA-GUI보다 우수하다"는 empirical claim 작성 금지 (evidence 없음).

**Future Run to Apply**  
Run 3 또는 Run 4 직전 (사용자 승인 후).

---

### 3.3 `03_CORE_CONCEPT_TAXONOMY.md`

**Current Problem**  
- `h_exec`, `H_alt`, `e_t`, `ell_t`, `F_t`, `b_t`, `G_t`, `Rewrite` 중 일부 개념이 taxonomy에 정의되지 않았거나 기존 정의가 `02_option_b_design_plan.md`의 symbol table과 불일치
- `h_exec`가 oracle label이 아니라 predicted trace임을 명확히 하는 항목 필요
- `A_t^H`가 alternative action set이 아니라 alternative control-grammar hypothesis set임을 명시 필요

**Required Patch**  
아래 8개 심볼 추가/정렬 (출처: `02_option_b_design_plan.md §3 Symbol Table`):

| Symbol | 추가/수정 내용 |
|---|---|
| `h_exec` | "직전 action 생성에 실제로 사용된 hypothesis (predicted trace, NOT oracle label)". `true_control_grammar`/`true_regime`과 구분 명시. |
| `H_alt` / `A_t^H` | "alternative regime/control-grammar hypothesis set. NOT alternative action set." PROP-01..10 참조 추가. |
| `e_t` | "action-effect evidence (10개 하위 필드: effect_type, dom_diff, accessibility_diff, visual_diff_score, precondition_status, no_effect_flag, delayed_effect_flag, noisy_observation_flag, progress_delta, failure_reason)" |
| `ell_t(h)` | "`log p_theta(e_t | H_{t-1}, a_{t-1}, h)` — hypothesis h의 evidence 설명력" |
| `F_t` | "`max_{h_alt ∈ A_t^H} [ell_t(h_alt) − ell_t(h_exec)]` — LR falsification score. F_t > 0 = alternative hypothesis가 h_exec보다 evidence를 더 잘 설명함 = falsification 발생" |
| `b_t(z^r,z^g)` | "`q_phi(z^r, z^g | H_t)` — exact Bayesian posterior가 아님. learned approximation." |
| `G_t` | "`I[F_t > τ_f ∧ ΔV_t > τ_v ∧ P_switch > τ_a ∧ ΔV_t − C_plan > 0]` — NOT `uncertainty > threshold`. 4개 조건의 conjunction." |
| `Rewrite` | "`Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*)` — grammar-conditioned action rewrite. h*는 predicted trace에서 선택. oracle label 아님." |

**Sections Likely Affected**  
§X (Symbol / Concept Glossary 또는 해당 taxonomy 섹션 전체)

**Claims Affected**  
C1~C6 전체 (symbol mismatch가 있으면 implementation contract 불일치 발생)

**Evidence Required Before Finalizing**  
Phase 5 (LR Implementation Contract) 완성 이후에 symbol 정의가 final이 됨. Phase 3/4에서는 `02_option_b_design_plan.md §3`을 SSoT로 사용하고, Phase 5 이후 paper_context_ref 업데이트 가능.

**Proposed Patch Summary**  
`02_option_b_design_plan.md §3 Symbol Table`의 9개 심볼 정의를 taxonomy 파일에 이식. 기존 정의와 충돌 시 conflict resolution 명시.

**Forbidden in This Run**  
실제 파일 수정 금지. Phase 5 계약 완성 전 final symbol 확정 금지.

**Future Run to Apply**  
Run 3 직후 (Phase 5 계약 완성 이후, 사용자 승인 후).

---

### 3.4 `06_DATA_SCHEMA_AND_LABELING.md`

**Current Problem**  
- `selected_hypothesis_id`, `alternative_hypothesis_ids`, `loglik_exec`, `loglik_alt_best`, `F_t`, `posterior_before`, `posterior_after`, `rewrite_triggered` 등 16개 LR scorer log field가 §4 (33개 필드 카탈로그)에 등록되지 않음
- 이 필드들은 inference-safe (agent observation 가능) 필드이나, 현재 스키마에 없어서 collector/dataloader에서 기록하지 않음
- `selected_hypothesis_id` 미등록 → h_exec trace 기록 불가 → MET-PERSIST-001 계산 불가 → C1 BLOCKED의 직접 원인

**Required Patch**  
아래 16개 필드를 §4에 추가 (출처: `02_option_b_design_plan.md §7 Required Logs`):

| 필드명 | 카테고리 | 설명 |
|---|---|---|
| `selected_hypothesis_id` | `agent_observable` (inference-safe) | h_exec ID. predicted trace. |
| `alternative_hypothesis_ids` | `agent_observable` | A_t^H 구성 ID 목록 |
| `evidence_summary` | `agent_observable` | e_t 10개 하위 필드 |
| `loglik_exec` | `agent_observable` | ell_t(h_exec) |
| `loglik_alt_best` | `agent_observable` | max_{h_alt} ell_t(h_alt) |
| `F_t` | `agent_observable` | LR falsification score |
| `posterior_before` | `agent_observable` | 이전 step b_t |
| `posterior_after` | `agent_observable` | 현재 step b_t |
| `adopted_hypothesis_id` | `agent_observable` | G_t=1일 때 h* ID |
| `decision_relevance_delta` | `agent_observable` | ΔV_t |
| `gate_reason` | `agent_observable` | G_t 판정 이유 |
| `rewrite_triggered` | `agent_observable` | Rewrite 발동 여부 |
| `rewrite_confidence` | `agent_observable` | Rewrite confidence |
| `fallback_used` | `agent_observable` | fallback rule 발동 여부 |
| `planning_calls` | `audit_only` | episode 내 G_t=1 횟수 (eval용) |
| `rollout_steps` | `audit_only` | 실제 rollout steps (eval용) |

**Sections Likely Affected**  
§4 (33개 필드 + 16개 신규 = 49개 필드 카탈로그)

**Claims Affected**  
C1 (`selected_hypothesis_id`), C3 (`loglik_exec/alt_best`, `F_t`), C4 (`adopted_hypothesis_id`, `rollout_steps`), C5 (`rewrite_triggered`, `rewrite_confidence`), C6 (`planning_calls`, `gate_reason`)

**Evidence Required Before Finalizing**  
Phase 5 (LR Implementation Contract)에서 visibility audit 요구사항 확정 후 field 카테고리 최종화. `FORBIDDEN_AGENT_FIELDS`와의 mirror sync 확인 필요 (`tests/test_forbidden_field_mirror_sync.py`).

**Proposed Patch Summary**  
`02_option_b_design_plan.md §7` 16개 필드를 §4에 이식. 각 필드의 visibility bucket (`agent_observable` vs `audit_only` vs `inference_forbidden`) 명시. 신규 `agent_observable` 필드가 FORBIDDEN_AGENT_FIELDS에 들어가지 않도록 확인.

**Forbidden in This Run**  
실제 파일 수정 금지. `FORBIDDEN_AGENT_FIELDS` 목록에 새 필드 추가 금지 (Phase 5 계약 전). `visibility.py` 수정 금지 (사용자 승인 없이).

**Future Run to Apply**  
Run 3 직후 또는 Run 4 직전 (사용자 승인 후). `visibility.py` mirror sync는 반드시 동반.

---

### 3.5 `07_LATENT_ARCHITECTURE_DESIGN.md`

**Current Problem**  
- LR scorer (`EvidenceLikelihood` + `LikelihoodRatioFalsificationScorer`)가 latent posterior module (`PosteriorUpdater`)과 어떻게 연결되는지 architecture 다이어그램/설명이 명확하지 않음
- C2 (regime/grammar separation)의 Locatello impossibility 위험이 architecture level에서 "high-risk hypothesis"로 명시되어 있으나, 이를 관리하기 위한 ABL-001 crossed split 전략이 architecture 문서에 반영되지 않음
- COLLAPSE-07-001 (`:370-371`)에 이미 collapse 위험이 기록되어 있으나 Option B 채택과의 연결이 없음

**Required Patch**  
- LR scorer pipeline이 latent posterior module의 output (`b_t(z^r,z^g)`)을 어떻게 활용하는지 연결 다이어그램 추가
- `EvidenceLikelihood` → `LikelihoodRatioFalsificationScorer` → `PosteriorUpdater` 연결 명시
- C2는 "final architecture fact"가 아니라 "high-risk architecture hypothesis"로 표현 변경. Locatello impossibility에 의한 non-identifiability 위험 + ABL-001 + crossed split으로 경험적 검증 예정임을 명시

**Sections Likely Affected**  
§3 (Architecture Overview) 또는 §4 (Module Connections); C2 관련 섹션에 "high-risk hypothesis" 표시 추가

**Claims Affected**  
C2 (latent factorization), C3 (LR scorer ↔ latent posterior 연결)

**Evidence Required Before Finalizing**  
Phase 5 (LR Implementation Contract)에서 module 간 인터페이스가 확정된 이후. Phase 11 latent probe 결과 이전에는 "C2 architecture hypothesis"는 미확정 상태 유지.

**Proposed Patch Summary**  
Option B 5개 component pipeline (ell_t → F_t → b_t → G_t → Rewrite)과 latent posterior module의 연결을 architecture 섹션에 추가. C2 관련 항목에 "PRIMARY_LATENT_CONTESTED" → "HIGH_RISK_ARCHITECTURE_HYPOTHESIS" 표시 업데이트.

**Forbidden in This Run**  
실제 파일 수정 금지. C2를 DEAD_COLLAPSED로 기록 금지 (evidence 없음). COLLAPSE-07-001 항목 임의 삭제 금지.

**Future Run to Apply**  
Run 3 이후 (사용자 승인 후).

---

### 3.6 `08_LOSS_REWARD_TRAINING_OBJECTIVE.md`

**Current Problem**  
**L-MAIN-005 현재 표현**:
```
L_falsification = BCE(σ(F_t), y_wrong)
where F_t = log p_θ(e_t|h_alt*) - log p_θ(e_t|h_exec)
```
**문제**: BCE를 main objective로 기술하면서 F_t를 LR로 정의하는 구조가 Option B main path (`LikelihoodRatioFalsificationScorer`)와 불일치. math_critic이 C3 RISK HIGH로 판정한 직접 원인.

**Required Patch** (2가지 선택지, 사용자 승인 필요)

**선택지 A (권장)**: L-MAIN-005를 split:
- L-MAIN-005a (new): `L_falsification_LR` = main path. `F_t = max_{h_alt}[ell(h_alt) - ell(h_exec)]`를 main objective로 기술. 학습 방법은 contrastive or log-prob supervision.
- L-MAIN-005b (ablation): `L_falsification_BCE` = ABL-022/ABL-023 ablation 경로로 강등. `BCE(σ(F_t), y_wrong)` 유지하되 주석으로 "ABL-022/023 path only" 명시.

**선택지 B**: L-MAIN-005 표현을 "BCE approximates LR"로 reframe. "BCE-trained score is LR approximation if BCE is sufficient statistic of LR"를 명시하고 UNKNOWN 상태로 표시. Phase 11에서 판정.

선택지 A가 Option B 채택 정신에 부합. 선택지 B는 Phase 11 전까지 UNKNOWN 상태 유지가 명확해야 함.

**Sections Likely Affected**  
§6 Main Loss Candidate Table (L-MAIN-005 행); §6.1 Main Loss Survival Criteria (L_falsification 행)

**Claims Affected**  
C3 (가장 직접적 영향); C1/C5/C6 간접 영향

**Evidence Required Before Finalizing**  
Phase 11 LR vs BCE mechanism delta 비교 결과 이후 선택지 A vs B 최종 결정 가능. 그 전에는 선택지 A (주석으로 ABL-022/023 ablation path 표시)를 사용.

**Proposed Patch Summary**  
L-MAIN-005를 Option B 채택 내용으로 업데이트. BCE는 main path에서 ABL-022/023 ablation path로 강등 표시. `LikelihoodRatioFalsificationScorer`가 main falsification method임을 명시.

**Forbidden in This Run**  
실제 파일 수정 금지. BCE를 삭제 금지 (ABL-022/023 ablation role 유지). "Option A (BCE reframe) 채택" 선언 금지 (Phase 11 evidence 전).

**Future Run to Apply**  
Run 3 이후 (사용자 승인 후). 이 수정은 invariant preservation (Fragile File에 해당하지 않으나, scientific contract 변경이므로) 사용자 명시적 승인 필요.

---

### 3.7 `09_PLANNING_THEORY_ALGORITHM.md`

**Current Problem**  
- §6.3의 F_t 공식은 이미 올바름: `F_t = max_{h_alt ∈ A_t^H} [ell_t(h_alt) - ell_t(h_exec)]`
- 그러나 §6.5 G_t gate 설명에서 "uncertainty > threshold" 단일 조건과의 혼동을 방지하는 명시적 표현이 부족
- `G_t`를 uncertainty gate가 아니라 decision-relevant falsification gate임을 명확히 하는 paragraph 필요
- Phase 5 (LR Implementation Contract)와의 연결 anchor가 없어 구현 계약과 이론 문서가 분리됨

**Required Patch**  
- §6.5 G_t 설명에 다음 추가:
  - "G_t는 uncertainty > threshold 단일 조건이 아니다. 4개 조건의 conjunction이다."
  - "CATTS/WebUncertainty-style uncertainty gate와의 구분: high-confidence wrong grammar episode에서 uncertainty는 낮지만 F_t는 높다. G_t는 이 episode를 포착, uncertainty gate는 포착하지 못한다."
- §6.2~6.6 수식에 Phase 5 implementation contract anchor 주석 추가 (예: "→ see 05_lr_implementation_contract.md §X for module-level contract")
- §6.3 F_t candidates 상태 업데이트: BCE candidate는 "ABL-022/023 ablation path" 표시

**Sections Likely Affected**  
§6.3 (F_t candidates); §6.5 (G_t gate + CATTS/WebUncertainty distinction); §5 (Symbol Table — h_exec definition 강화)

**Claims Affected**  
C3 (F_t definition), C6 (G_t ≠ uncertainty gate)

**Evidence Required Before Finalizing**  
Phase 5 계약 완성 이후 anchor 추가 가능. CATTS distinction paragraph는 Phase 1 threat audit (`01_novelty_theory_threat_audit.md`)을 근거로 즉시 추가 가능.

**Proposed Patch Summary**  
G_t ≠ uncertainty gate 구분 paragraph 추가. F_t BCE candidate를 ablation path로 강등 표시. Phase 5 anchor 추가 (Phase 5 완성 이후).

**Forbidden in This Run**  
실제 파일 수정 금지. F_t = LR 공식 변경 금지 (이미 올바름). G_t 4-way conjunction 구조 변경 금지.

**Future Run to Apply**  
Run 3 이후 (사용자 승인 후).

---

### 3.8 `10_EVALUATION_BASELINE_ABLATION.md`

**Current Problem**  
- BASE-026 (WAC-style), BASE-027 (CUWM-style), BASE-028 (WebWorld-style): §7에 등재되어 있으나 구현 `baselines.py`에 없음. `claim_align_20260516_R1.md`에서 0/3 (0%) 확인.
- CATTS-equivalent baseline (uncertainty entropy gate), BASE-loop-heuristic (VLAA-GUI style): §7에 미등재.
- ABL-017 (no_L_intent_action_mapping), ABL-022 (no falsification score gate) standalone: §8에 있으나 `ablations.py` ABLATION_REGISTRY에 없음.
- ABL-036 (no_counterfactual_target): §8에 있으나 구현 없음.
- C1/C3/C5 primary survival axis 반영 내용 없음.

**Required Patch**  
- BASE-uncertainty-entropy-gate: CATTS-equivalent baseline 추가 (C6 방어용). compute-matched uncertainty gate baseline.
- BASE-loop-heuristic: VLAA-GUI-equivalent baseline 추가 (C1/C3 방어용). repeat count + screen hash based mode switch.
- §7 BASE-026/027/028 항목에 "직접 위협 baseline (direct threat response required)" 표시 강화.
- ABL-017 standalone entry 추가. `no_L_intent_action_mapping` — loss-level training ablation. C5 primary axis claim.
- ABL-022 standalone entry 추가 (ABL-016과 분리). `no_falsification_score_gate` — inference-time gate ablation.
- §8에 primary survival axis 반영: C1/C3/C5에 "PRIMARY SURVIVAL AXIS — ablation required before ALIVE judgment" 표시.

**Sections Likely Affected**  
§7 Baseline Table (BASE-XXX 추가); §8 Ablation Table (ABL-017/022 standalone 추가, 표시 강화)

**Claims Affected**  
C1~C6 전체. 특히 C3/C4/C5/C6 방어에 직접 영향.

**Evidence Required Before Finalizing**  
Phase 10 구현 이전에 §7/§8 목록 업데이트 가능 (계획 수준). 구현 상태 표시는 Phase 10 이후 업데이트.

**Proposed Patch Summary**  
BASE-uncertainty-entropy-gate, BASE-loop-heuristic 신규 항목 추가. ABL-017/022 standalone 항목 추가. C1/C3/C5 primary axis 표시. §8 CRITICAL ablation 표시 강화 (ABL-011/015/017/022/040 — 모두 MISSING 상태 반영).

**Forbidden in This Run**  
실제 파일 수정 금지. `baselines.py` / `ablations.py` 수정 금지. test_ablation_runner.py count 변경 금지 (Phase 10 동반 업데이트 필요).

**Future Run to Apply**  
Run 3 이후 계획 문서 업데이트 가능 (사용자 승인 후). 구현 상태 업데이트는 Run 5 (Phase 10) 이후.

---

### 3.9 `FINAL_RESEARCH_BLUEPRINT.md`

**Current Problem**  
- main thesis가 "FRCG-WM: Falsification-guided Reasoning for Control-Grammar World Models" 수준에서 유지되고 있으나, "Web/GUI world model"이라는 framing이 WAR Room R1 FATAL_FLAW 2번 ("Web/GUI agent paper framing unjustifiable")과 충돌
- L-MAIN-005 BCE ↔ LR 불일치가 blueprint의 C3 claim 표현과도 불일치
- C2/C4/C6가 C1/C3/C5와 동등한 수준으로 제시되어 있어 primary/secondary axis 구분이 없음
- 신규 위협 3건이 related work에 없어 novelty framing이 공격에 노출

**Required Patch**  
- Main thesis 정렬: "wrong-control-grammar persistence + LR falsification + grammar-conditioned rewrite"가 핵심 novelty 3축임을 명시
- "generic Web/GUI world model"이 아님을 명확히. "wrong-hypothesis-aware mechanism"이 핵심
- C1/C3/C5 = primary survival axis로 표시. C4/C6 = supporting mechanism. C2 = high-risk architecture hypothesis.
- C3 claim 표현: "LR falsification scorer that distinguishes grammar hypothesis alternatives via evidence likelihood ratio" (BCE 이중 표현 정리)
- 신규 위협 (CATTS/VLAA-GUI/WebUncertainty) 방어 전략 paragraph 추가

**Sections Likely Affected**  
Abstract claim, Introduction novelty paragraph, Contribution list, Related Work 연결

**Claims Affected**  
C1~C6 전체. Paper framing 전반.

**Evidence Required Before Finalizing**  
Phase 11 evidence 없이 FRCG-WM이 신규 위협 방어를 "실험적으로 보여준다"는 표현 금지. Phase 4에서는 distinction 방향만 명시, empirical claim 작성 금지.

**Proposed Patch Summary**  
Main thesis를 wrong-grammar-persistence + LR-falsification + grammar-conditioned-rewrite 3축으로 재정렬. Primary/secondary/high-risk claim 구분. C3 Option B 채택 반영. generic WM novelty claim 축소, wrong-hypothesis-aware mechanism claim 강화.

**Forbidden in This Run**  
실제 파일 수정 금지. "generic WM novelty claim"을 완전 제거 금지 (paper_context_ref에서는 단계적으로 조정해야 함). "FRCG-WM이 CATTS/VLAA-GUI를 능가한다"는 empirical claim 작성 금지 (evidence 없음).

**Future Run to Apply**  
Run 3 이후 또는 Run 7 (paper writing 직전). 사용자 승인 필수.

---

### 3.10 `00_MASTER_REFERENCE.md` / `00_CONTEXT_INDEX.md`

**Current Problem**  
- `docs/orchestration/lr_alignment/` 경로의 Option B 문서들이 context routing에 반영되지 않음
- 새 세션이 시작될 때 `00_CONTEXT_INDEX.md §3 memory map`이 Option B phase 경로를 알려주지 않음
- Run 2 완성 후 Run 3 시작 시 새 세션이 `00_OPTION_B_PHASE_ROADMAP.md`를 먼저 읽어야 한다는 안내 없음

**Required Patch (판단 사항)**  
다음 두 가지 중 선택:
- **선택지 A**: `00_CONTEXT_INDEX.md §3 memory map`에 Option B alignment 기간 한정 subsection 추가. `00_OPTION_B_PHASE_ROADMAP.md`를 "항시 최상위 라우터 (`paper_context_ref/00_CONTEXT_INDEX.md`) 하위 부차 라우터"로 명시하는 routing note 추가.
- **선택지 B**: `00_CONTEXT_INDEX.md` 수정 없이, `CLAUDE.md` 또는 `CLAUDE.local.md`에 Option B alignment 기간 한정 routing 주석 추가.

`00_OPTION_B_PHASE_ROADMAP.md §1.2`에 "본 파일은 `paper_context_ref/00_CONTEXT_INDEX.md`를 대체하지 않는다"라고 이미 명시되어 있어, 선택지 B가 더 적절할 수 있음.

**Sections Likely Affected**  
`00_CONTEXT_INDEX.md §3 (memory map)` 또는 CLAUDE.md (선택지에 따라)

**Claims Affected**  
routing 명확성. claim 자체에는 직접 영향 없음.

**Evidence Required Before Finalizing**  
Run 3 시작 전에 결정 필요. 새 세션에서 Option B 문서를 찾지 못하면 실행 실패 위험.

**Proposed Patch Summary**  
`00_CONTEXT_INDEX.md §3`에 Option B alignment 기간 한정 note 추가 (또는 CLAUDE.local.md에 주석으로 추가). `00_OPTION_B_PHASE_ROADMAP.md`를 "phase 진입 전 필독"으로 routing.

**Forbidden in This Run**  
실제 파일 수정 금지.

**Future Run to Apply**  
Run 2 완료 직후 (사용자 승인 후) 또는 Run 3 시작 직전.

---

## Section 4. Claim-Preserving Refactor Strategy (6개 전략 문구)

1. **약화가 아니라 정렬이다.** Run 2의 모든 patch plan은 claim을 약화/폐기하는 것이 아니라, 구현 계약/이론/실험과의 정렬을 목적으로 한다. Evidence 없이 claim을 폐기하는 수정은 금지다.

2. **C1/C3/C5는 primary survival axis다.** 이 세 claim과 관련된 paper_context_ref 표현은 약화 방향으로 수정하지 않는다. 오히려 더 명확하고 강한 표현으로 정렬한다. L-MAIN-005 reframe(3.6)도 BCE 약화가 아니라 LR main path 강화를 목적으로 한다.

3. **C2는 high-risk architecture hypothesis다.** C2가 DEAD_COLLAPSED 판정을 받기 전까지, architecture 문서에서 C2 관련 항목을 삭제하거나 폐기하지 않는다. "high-risk"로 표시하되, ABL-001 + crossed split + latent probe 경로를 제시하는 방향으로 수정한다.

4. **C4/C6는 supporting mechanism/efficiency claim이다.** C1/C3/C5의 primary axis를 지원하는 역할로 재정렬한다. C4는 C3 LR falsification 이후 어떤 grammar를 채택하는가, C6는 언제 compute를 쓰는가의 efficiency claim이다. 이 위치 조정은 novelty 약화가 아니라 claim 구조 명확화다.

5. **generic WM novelty claim은 줄이되 wrong-hypothesis-aware mechanism claim은 강화한다.** "Web/GUI world model"이라는 일반적 표현에서 "wrong-control-grammar hypothesis-aware LR falsification + grammar-conditioned rewrite"라는 구체적 표현으로 이동한다. 이는 CATTS/VLAA-GUI/WebUncertainty 같은 신규 위협에 대해 더 방어적인 framing이다.

6. **실제 paper_context_ref 수정은 Run 2에서 금지다.** 이 section의 6개 전략은 수정 방향을 명시하는 것이지, 수정 실행을 허가하는 것이 아니다. 실제 수정은 사용자 명시적 승인 + 해당 Phase 도달 후에만 허용된다.

---

## Section 5. Approval Matrix

각 target file의 수정 우선순위와 승인 상태.

| Target File | Approval Status | Priority | Actual Edit in Run 2? | Future Run |
|---|---|---|---|---|
| `01_RELATED_WORK_THREAT_MAP.md` | `NEEDS_USER_REVIEW` | HIGH | NO | Run 3 이후 |
| `02_PROBLEM_NOVELTY_FALSIFICATION.md` | `NEEDS_USER_REVIEW` | HIGH | NO | Run 3 이후 |
| `03_CORE_CONCEPT_TAXONOMY.md` | `WAIT_FOR_RUN3_CONTRACT` | HIGH | NO | Phase 5 계약 완성 후 |
| `06_DATA_SCHEMA_AND_LABELING.md` | `WAIT_FOR_RUN3_CONTRACT` | CRITICAL | NO | Phase 5 계약 + visibility.py sync 후 |
| `07_LATENT_ARCHITECTURE_DESIGN.md` | `NEEDS_USER_REVIEW` | MED | NO | Run 3 이후 |
| `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | `NEEDS_USER_REVIEW` | CRITICAL | NO | Run 3 이후 (사용자 선택지 결정 필요) |
| `09_PLANNING_THEORY_ALGORITHM.md` | `NEEDS_USER_REVIEW` | HIGH | NO | Run 3 이후 |
| `10_EVALUATION_BASELINE_ABLATION.md` | `NEEDS_USER_REVIEW` | HIGH | NO | Run 3 이후 (구현 상태 업데이트는 Run 5) |
| `FINAL_RESEARCH_BLUEPRINT.md` | `WAIT_FOR_RUN6_EVIDENCE` | MED | NO | Run 7 (paper writing 직전) 또는 Run 3 이후 (framing 수준만) |
| `00_MASTER_REFERENCE.md` / `00_CONTEXT_INDEX.md` | `APPROVE_LATER` | LOW | NO | Run 2 완료 직후 또는 Run 3 직전 |

**Status 정의**:
- `NEEDS_USER_REVIEW`: 수정 방향이 명확하나 사용자 확인 후 실행 가능
- `WAIT_FOR_RUN3_CONTRACT`: Phase 5 LR Implementation Contract 완성 이후에야 최종화 가능
- `WAIT_FOR_RUN6_EVIDENCE`: Phase 11 evaluation 결과 이후 최종화 가능
- `APPROVE_LATER`: 기술적으로 즉시 가능하나 Run 2 완료 후 별도 결정 필요

---

## Section 6. Patch Dependency Graph

수정 의존성 순서 (위에서 아래로 진행):

```
단계 1: 개념 정의 기반 (기타 모든 수정의 선행 요건)
  └─ 03_CORE_CONCEPT_TAXONOMY.md (symbol 정의)
      → 의존: 02_option_b_design_plan.md §3 Symbol Table (완성됨)
      → Phase 5 계약 완성 이후 final

단계 2: 데이터/로그 스키마 (구현 계약 의존)
  └─ 06_DATA_SCHEMA_AND_LABELING.md (16개 log field 추가)
      → 의존: 03_CORE_CONCEPT_TAXONOMY.md (symbol 정의)
      → 의존: Phase 5 LR Implementation Contract
      → visibility.py mirror sync 동반 필수

단계 3: 학습 목적함수 (Option B 채택 반영)
  └─ 08_LOSS_REWARD_TRAINING_OBJECTIVE.md (L-MAIN-005 reframe)
      → 의존: 03_CORE_CONCEPT_TAXONOMY.md
      → 사용자 선택지 (A vs B) 결정 필요

단계 4: 알고리즘 계약 (수식 연결 강화)
  └─ 09_PLANNING_THEORY_ALGORITHM.md (G_t ≠ uncertainty gate, Phase 5 anchor)
      → 의존: 08_LOSS_REWARD_TRAINING_OBJECTIVE.md 수정 방향 결정 후

단계 5: 평가 계약 (baseline/ablation 추가)
  └─ 10_EVALUATION_BASELINE_ABLATION.md (신규 항목 추가)
      → 의존: 03_CORE_CONCEPT_TAXONOMY.md, 08, 09
      → 구현 상태 업데이트는 Phase 10 이후

단계 6: 문제 정의 / 위협 방어 (claim framing 정렬)
  ├─ 02_PROBLEM_NOVELTY_FALSIFICATION.md (falsification LR로 명확화)
  │   → 의존: 03 (symbol), 08 (loss), 09 (algorithm)
  └─ 01_RELATED_WORK_THREAT_MAP.md (신규 위협 3건 추가)
      → 의존: 01_novelty_theory_threat_audit.md (완성됨)

단계 7: Architecture 정렬 (latent posterior ↔ LR scorer 연결)
  └─ 07_LATENT_ARCHITECTURE_DESIGN.md (pipeline 연결 명확화)
      → 의존: 03, 06, Phase 5 계약

단계 8: Blueprint 최종 정렬 (paper framing)
  └─ FINAL_RESEARCH_BLUEPRINT.md (primary/secondary/high-risk claim 구분)
      → 의존: 01, 02, 03, 06, 07, 08, 09, 10 모두 완성 후
      → Phase 11 evidence 이후 empirical claim 최종화

단계 9: Routing 업데이트 (선택적)
  └─ 00_CONTEXT_INDEX.md / 00_MASTER_REFERENCE.md
      → 의존: 없음 (독립적). Run 2 완료 직후 가능.
```

---

## Section 7. Handoff to Run 3

Run 3에서 작성해야 하는 산출물 (Run 2에서는 작성 금지):

| 파일 | 역할 | Phase |
|---|---|---|
| `docs/orchestration/lr_alignment/05_lr_implementation_contract.md` | LR scorer 모듈 I/O contract, signature stub 파일 | Phase 5 |
| `docs/orchestration/lr_alignment/06_unit_test_plan.md` | LR scorer + h_exec trace + visibility audit 단위 테스트 목록 | Phase 6 |
| `docs/orchestration/lr_alignment/07_eval_gate_design.md` | CC-P3-G1/G3/G4 재정의 + ablation 비교 조건 | Phase 7 |

Run 3 진입 시 반드시 선행 읽어야 하는 파일:
- `docs/orchestration/lr_alignment/00_OPTION_B_PHASE_ROADMAP.md` (Router)
- `docs/orchestration/lr_alignment/03_concept_survivability_ledger.md` (Evidence Card schema)
- `docs/orchestration/lr_alignment/04_md_refactor_patch_plan.md` (이 파일 — patch 의존성 확인)
- `docs/orchestration/lr_alignment/02_option_b_design_plan.md` (LR I/O contract 선행 설계)

Run 3 진입 시 허용 작업:
- signature stub 파일 생성 (구현 로직 없음)
- test stub 파일 생성 (테스트 로직 없음)
- MD 문서 3개 (05/06/07) 신규 작성

Run 3 진입 시 금지 작업:
- 실제 LR 구현 로직 작성 (Phase 8)
- paper_context_ref 실제 수정 (사용자 승인 없이)
- P3 재학습 실행
- C1~C6 ALIVE/DEAD 확정 판정

---

## Section 8. Phase 4 Verdict

**`REFACTOR_PLAN_READY`**

근거:
1. 10개 target file 모두 `Current Problem`, `Required Patch`, `Sections Likely Affected`, `Claims Affected`, `Evidence Required Before Finalizing`, `Proposed Patch Summary`, `Forbidden in This Run`, `Future Run to Apply` 8개 필드 완성
2. Claim-Preserving Refactor Strategy 6개 전략 문구 명시
3. Approval Matrix: 10개 target file 모두 `Actual Edit in Run 2? NO`
4. Patch Dependency Graph: 9단계 순서 명시
5. Run 3 handoff item 명시

**주의**: "REFACTOR_PLAN_READY"는 patch plan 문서가 완성되어 Run 3 진입 준비가 됐다는 의미다.  
"paper_context_ref 수정 완료"가 **절대 아니다**. 실제 수정은 사용자 명시적 승인 후에만 허용된다.

---

*생성일: 2026-05-16 / Run 2 / Phase 4 산출물*  
*근거: `docs/orchestration/lr_alignment/00_OPTION_B_PHASE_ROADMAP.md` Section 4 Phase 4, Section 5 Run 2*  
*수정 금지: `paper_context_ref/` 전체 (이 파일은 계획서, 수정본 아님)*
