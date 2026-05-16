# 00_OPTION_B_PHASE_ROADMAP.md
**생성일**: 2026-05-16  
**세션**: War Room R1 직후 Run 0  
**작성 근거**: war_room_R1_synthesis.md (Verdict C, AT_RISK), 2026-05-16_novelty_viability_verdict.md  
**유효 기간**: Option B alignment 기간 한정 (Phase 0~12 완료 후 archive 이동 예정)

---

## Section 1. Purpose — 이 파일의 역할

### 1.1 이 파일은 무엇인가

이 파일은 **구현 계획서가 아니라 최상위 라우터**다.

Claude Code가 새 세션에 진입할 때 다음 세 가지를 1분 안에 파악할 수 있도록 설계되었다.

1. **지금 Run 몇인가** → Section 5 (Run Segmentation Plan) 참조
2. **지금 Phase 몇인가** → Section 4 (Phase 0~12 Master Table) 참조
3. **이 Phase에서 무엇이 허용/금지되는가** → 각 Phase 행의 `Forbidden Actions` 열 참조

### 1.2 다른 라우터와의 관계

| 라우터 | 역할 | 우선순위 |
|---|---|---|
| `paper_context_ref/00_CONTEXT_INDEX.md` | 전사 라우터 (항시 유효) | 최상위 |
| 본 파일 (`00_OPTION_B_PHASE_ROADMAP.md`) | Option B alignment 기간 한정 부차 라우터 | 전사 라우터 하위 |

본 파일은 `paper_context_ref/00_CONTEXT_INDEX.md`를 대체하지 않는다.  
본 파일이 전사 라우터와 충돌할 경우, `00_CONTEXT_INDEX.md`가 우선한다.

Option B alignment 기간이 종료되면 (Phase 12 Survivability Decision Report 생성 후),  
본 파일은 `docs/orchestration/lr_alignment/archive/00_OPTION_B_PHASE_ROADMAP_ARCHIVED.md`로 이동된다.

### 1.3 이 파일이 생겨난 이유

2026-05-16 War Room R1에서 7개 deep critic + area-chair synthesis 결과:

- **Verdict: C (AT RISK), Confidence HIGH**
- Claim survivability: 0 VIABLE / 2 CONDITIONAL (C3, C5) / 4 AT_RISK (C1, C2, C4, C6)
- 4개 FATAL_FLAW 확인 (Section 2 참조)
- C3 핵심 진단: 이론(`F_t = LR scorer`)과 구현(`L_falsification = BCE`)의 간극

이 상황에서 가장 큰 유혹은 "baseline/ablation을 더 추가하면 살아난다"는 것이지만,  
**LR scorer가 구현되지 않은 상태에서 baseline을 추가해도 mechanism delta가 살아나지 않는다**.

따라서 **Option B = 구현을 이론에 맞춘다** 방향으로 경로를 고정한다.

---

## Section 2. Current Critical Diagnosis

> **근거 파일**: war_room_R1_synthesis.md, feasibility_20260516_R1.md, reviewer2_20260516_R1.md,  
> math_critic_20260516_R1.md, claim_align_20260516_R1.md, exp_design_20260516_R1.md,  
> novelty_scout_20260516_R1.md, impl_risk_20260516_R1.md, P3_EVAL.BLOCKED_planning_calls_zero.md

| Issue ID | 내용 | Evidence Path | Status |
|---|---|---|---|
| ISSUE-01 | P3_EVAL invalid: planning_calls=0 (전 5 seed), FRCG-FULL = no_control_grammar (Δ=0). CC-P3-G1/G3/G4 FAIL | `outputs/phase_gates/P3_EVAL.BLOCKED_planning_calls_zero.md`; `outputs/runs/p3_ablations/ablation_results.json`; `feasibility_20260516_R1.md` | **BLOCKED** |
| ISSUE-02 | h_exec trace 미존재: `selected_hypothesis_id` 필드가 step log에 populate되지 않음 → MET-PERSIST-001 계산 불가 | `reviewer2_20260516_R1.md` Attack 2 (REF-PROBLEM-012); `claim_align_20260516_R1.md` C1 | **BLOCKED** |
| ISSUE-03 | C3 LR vs BCE gap: 이론 `F_t = max_{h_alt}[ell(h_alt)−ell(h_exec)]` (09 §6.3 line 171), 구현 `L_falsification = BCE(σ(F_t), y_wrong)` (08 L-MAIN-005 line 208). BCE는 uncertainty threshold로 collapse 가능 | `math_critic_20260516_R1.md` C3 RISK HIGH; `paper_context_ref/09 line 171`; `paper_context_ref/08 line 208` | **CRITICAL** |
| ISSUE-04 | BASE-026 (WAC) / BASE-027 (CUWM) / BASE-028 (WebWorld) 모두 `baselines.py`에 미존재. ATTACK-DEF-004 답변 불가 | `claim_align_20260516_R1.md` Direct-Threat 0/3; `exp_design_20260516_R1.md` BASE-026/027/028 MISSING | **BLOCKED** |
| ISSUE-05 | P4 GUI env scaffold (TASK_1021_A) 실행됐으나 Option B LR alignment 없이 진행됨. gui_env는 LR scorer 경로와 아직 연동되지 않음 | commit `2824381 feat(gui_env): TASK_1021_A`; `war_room_R1_synthesis.md` P4 GUI env stub | **IN_PROGRESS** |
| ISSUE-06 | C1~C6 survivability 위기: 0 VIABLE / 2 CONDITIONAL / 4 AT_RISK. Evidence Card 없이 status 변경 금지 | `war_room_R1_synthesis.md` Claim-by-Claim Survivability; `2026-05-16_novelty_viability_verdict.md` | **AT_RISK** |
| ISSUE-07 | 신규 미등록 위협 3건: CATTS (2602.12276, C6 compute gate 위협), VLAA-GUI (2604.21375, C1/C3 위협), WebUncertainty (2604.17821) | `novelty_scout_20260516_R1.md` New Threats | **UNREGISTERED** |
| ISSUE-08 | CRITICAL ablations 6/14 미구현: ABL-011, ABL-015, ABL-017, ABL-022, ABL-036, ABL-040 | `exp_design_20260516_R1.md`; `claim_align_20260516_R1.md` CRITICAL Ablations | **INCOMPLETE** |

---

## Section 3. Option B Definition — 이 문서가 공식화

> **주의**: "Option B"라는 용어는 이 파일이 최초 등장이다.  
> 이전 어떤 agent report, paper_context_ref, session report에도 이 용어가 사용되지 않았다.  
> 이 파일이 공식 정의 출처(SSoT)다.

### 3.1 Option B vs Option A 정의

| 구분 | 정의 | 채택 여부 |
|---|---|---|
| **Option B** (본 경로) | **구현을 이론에 맞춘다** = `LikelihoodRatioFalsificationScorer`를 main path로 구현, BCE 변종을 ABL-022/023 ablation으로 강등 | **ADOPTED** (Phase 0에서 공식화) |
| Option A (대조 경로) | BCE를 LR approximation으로 reframe하여 narrative에서만 수정 (`math_critic_20260516_R1.md` 방안 A) | **DEFERRED**: ablation 결과가 판정 가능해진 시점 (Phase 11) 이후 비교 옵션으로만 보존 |

Option A가 채택될 수 있는 조건: Phase 11 full eval에서 BCE scorer가 LR scorer와 mechanism delta가 통계적으로 구별되지 않는 것이 확인될 경우. 그 전까지 Option A는 이론적 대안에 불과하다.

### 3.2 Main Path 구현 계약 (Formal)

아래는 Phase 5 (LR Implementation Contract)에서 상세화될 계약의 preview다.

**증거 가능도 (Evidence likelihood)**  
출처: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.2 line 152`
```
ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h)
```

**Falsification Score (Main LR form)**  
출처: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.3 line 171`  
인용: `paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md lines 343, 347`
```
F_t = max_{h_alt ∈ A_t^H} [ ell_t(h_alt) − ell_t(h_exec) ]
```

**h_exec 정의 (실행된 hypothesis)**  
출처: `paper_context_ref/09 §5 Symbol Table line 123`
- `h_t^exec` = 직전 action 생성에 **실제로 사용된** hypothesis (predicted trace only)
- **절대 금지**: inference input으로 사용 (`FORBIDDEN_AGENT_FIELDS` 목록에는 들어가지 않으나, 추론 경로 외부의 oracle label과 혼동 금지)
- `selected_hypothesis_id` 필드를 step log에 populate해야 h_exec trace가 기록됨

**A_t^H 정의 (Alternative hypothesis set)**  
출처: `paper_context_ref/09 §8 PROP-01..10`
- `A_t^H` = alternative **regime/control-grammar** hypotheses. **alternative action이 아님**
- PROP-01..10: grammar property enumeration (context-sensitive vs unconditional, precondition-bound vs effect-constrained 등)

**e_t 구조 (Action-effect evidence)**  
출처: `paper_context_ref/09 §6.2`
```
e_t 포함 항목:
  - effect type (observed)
  - DOM diff summary
  - accessibility diff summary
  - visual diff score
  - precondition status
  - no-effect flag
  - delayed-effect flag
  - noisy-observation flag
  - progress delta
  - failure reason
```

**Posterior (Learned approximation)**  
출처: `paper_context_ref/09 §6.1 line 142`
```
b_t(z^r, z^g) = q_phi(z^r, z^g | H_t)
```
- exact Bayesian posterior가 아님
- `q_phi` = history encoder + latent posterior module의 learned approximation

**Decision-relevance gate**  
출처: `paper_context_ref/09 §6.5 lines 200–209`
```
ΔV_t = max_{h_alt∈A_t^H, a∈A} V(a,h_alt) − max_{a∈A} V(a,h_exec)

G_t = I[
    F_t > τ_f
    ∧ ΔV_t > τ_v
    ∧ P(action_switch | A_t^H, H_t) > τ_a
    ∧ ΔV_t − C_plan > 0
]
```
- `uncertainty > threshold` 조건이 아님. 4개 조건이 모두 충족되어야 함.

**Action-interface rewrite**  
출처: `paper_context_ref/09 §6.6`
```
a_exec = Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*)
```
- `rewrite_confidence < τ_r`일 때 fallback 규칙 발동 (Phase 5에서 상세화)

### 3.3 Auxiliary Path (Ablation으로 강등)

| 항목 | 현 상태 | Option B 이후 역할 |
|---|---|---|
| `BCEBinaryFalsificationScorer` (현재 L-MAIN-005 구현) | main path 구현 | **ABL-022 / ABL-023 ablation으로 강등** |
| BCE의 sufficient statistic 여부 | UNKNOWN (math_critic C3) | Phase 11에서 LR vs BCE 비교 실험으로 판정 |

---

## Section 4. Phase 0~12 Master Table

총 13개 Phase. 각 Phase는 독립된 산출물 집합을 가진다.

### 4.1 요약 표

| Phase ID | Name | 핵심 목적 | Code Impl? | Gate Condition |
|---|---|---|---|---|
| **Phase 0** | Decision Freeze | Option B 공식 채택 기록 | NO | `DEC_OPTION_B_LR_ALIGNMENT.md` 존재 |
| **Phase 1** | Novelty/Theory Threat Audit | 신규 위협 + 기존 위협 재확인 | NO | `01_novelty_theory_threat_audit.md` 존재, 7개 위협 모두 addressed |
| **Phase 2** | Option B LR Design Plan | LR 계약 전체 상세 설계 | NO | `02_option_b_design_plan.md` 존재, F_t/ell/posterior/gate/rewrite 계약 완성 |
| **Phase 3** | Concept Survivability Ledger Design | Evidence Card schema + C1~C6 카드 stub | NO | `03_concept_survivability_ledger.md` 존재, Evidence Card schema 확정 |
| **Phase 4** | MD Refactor Patch Plan | paper_context_ref 수정 대상 목록 + diff 초안 | NO | `04_md_refactor_patch_plan.md` 존재, 사용자 승인 항목 명시 |
| **Phase 5** | LR Implementation Contract | 모듈/시그니처/계약/입출력 schema | PARTIAL (stub only) | `05_lr_implementation_contract.md` + signature stub 파일 |
| **Phase 6** | Unit Test Plan | LR scorer + h_exec trace + visibility audit 테스트 목록 | PARTIAL (stub only) | `06_unit_test_plan.md` + test stub 파일 |
| **Phase 7** | Evaluation Gate Design | 재학습 후 PASS/FAIL 조건, ABL-016/022/023/024 명세 | NO | `07_eval_gate_design.md` 존재 |
| **Phase 8** | Text-only LR Smoke Implementation | `lr_scorer.py` 구현 + text-only smoke | YES | planning_calls > 0, LR > BCE ablation delta > 0 |
| **Phase 9** | Synthetic GUI LR Integration | gui_env collector + LR scorer 연동 | YES | GUI env에서 F_t 계산 가능, smoke 통과 |
| **Phase 10** | Baseline/Ablation Expansion | BASE-026/027/028 + ABL-016/017/022/023/024/035/039 | YES | 모든 추가 항목 단위 테스트 green |
| **Phase 11** | Verification and Evaluation | full eval rerun + leakage audit + metric 계산 | YES | CC-P3-G1/G3/G4 PASS, MET-WM-001/ALT-001/FALS-001/PERSIST-001 계산됨 |
| **Phase 12** | Survivability Decision Report | C1~C6 ALIVE/DEAD/CONDITIONAL 최종 판정 | NO | `12_survivability_decision_report.md` 존재, Evidence Card 모두 채워짐 |

### 4.2 Phase별 상세

---

#### Phase 0 — Decision Freeze

| 항목 | 내용 |
|---|---|
| **Purpose** | Option B (LR main path)를 공식 채택한다는 decision을 기록. 이후 모든 Run에서 이 결정이 valid한 전제임을 명시 |
| **Must Read** | `war_room_R1_synthesis.md`, `math_critic_20260516_R1.md` (C3 RISK HIGH) |
| **Output Files** | `docs/orchestration/lr_alignment/DEC_OPTION_B_LR_ALIGNMENT.md` |
| **Forbidden Actions** | 코드 작성, paper_context_ref 수정, P3 재학습, baseline 추가, Evidence Card 작성 |
| **Gate Condition** | `DEC_OPTION_B_LR_ALIGNMENT.md`가 존재하고, Option B 정의와 채택 근거가 기록되어 있음 |
| **Code Impl Allowed?** | NO |

---

#### Phase 1 — Novelty/Theory Threat Audit

| 항목 | 내용 |
|---|---|
| **Purpose** | 신규 위협 (CATTS/VLAA-GUI/WebUncertainty) + 기존 위협 (WebWorld/WAC/CUWM/VeriGUI) 상태 재확인. 어떤 위협이 어느 Claim을 공격하는지 매핑 |
| **Must Read** | `novelty_scout_20260516_R1.md`, `paper_context_ref/01_RELATED_WORK_THREAT_MAP.md`, `paper_context_ref/02_PROBLEM_NOVELTY_FALSIFICATION.md` |
| **Output Files** | `docs/orchestration/lr_alignment/01_novelty_theory_threat_audit.md` |
| **Forbidden Actions** | `paper_context_ref/01_RELATED_WORK_THREAT_MAP.md` 직접 수정 (사용자 승인 없이), 코드 작성, P3 재학습 |
| **Gate Condition** | CATTS/VLAA-GUI/WebUncertainty/WebWorld/WAC/CUWM/VeriGUI 7개 위협 모두 defense 전략과 함께 기술됨. 신규 위협이 `01_RELATED_WORK_THREAT_MAP.md` 수정 필요 여부 판단 포함 |
| **Code Impl Allowed?** | NO |

---

#### Phase 2 — Option B LR Design Plan

| 항목 | 내용 |
|---|---|
| **Purpose** | Section 3.2에서 sketch한 LR 계약을 full 설계 문서로 확장. F_t/ell/posterior/gate/rewrite 각 component의 입력/출력/의존성/실패 모드까지 명세 |
| **Must Read** | `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md` (§5~§10), `paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md`, `paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md` |
| **Output Files** | `docs/orchestration/lr_alignment/02_option_b_design_plan.md` |
| **Forbidden Actions** | `paper_context_ref/` 수정, 코드 작성, P3 재학습, Evidence Card 작성 |
| **Gate Condition** | `02_option_b_design_plan.md`에 F_t/ell_t/b_t/G_t/Rewrite 5개 component 명세가 완성되고, ABL-022/023 강등 결정이 명시됨 |
| **Code Impl Allowed?** | NO |

---

#### Phase 3 — Concept Survivability Ledger Design

| 항목 | 내용 |
|---|---|
| **Purpose** | Evidence Card schema를 확정하고, C1~C6 각 concept에 대한 카드 stub을 생성. Status 변경 규칙 명문화 |
| **Must Read** | `war_room_R1_synthesis.md` Claim-by-Claim, `2026-05-16_novelty_viability_verdict.md`, `paper_context_ref/02_PROBLEM_NOVELTY_FALSIFICATION.md` |
| **Output Files** | `docs/orchestration/lr_alignment/03_concept_survivability_ledger.md` |
| **Forbidden Actions** | Evidence Card status를 ALIVE/DEAD로 판정 (stub만 생성), 코드 작성, paper_context_ref 수정 |
| **Gate Condition** | Evidence Card schema (6개 필수 필드) 확정, C1~C6 stub 생성, status transition 규칙 명시 |
| **Code Impl Allowed?** | NO |

---

#### Phase 4 — MD Refactor Patch Plan

| 항목 | 내용 |
|---|---|
| **Purpose** | Option B 채택에 따라 수정이 필요한 `paper_context_ref/` 파일 목록과 diff 초안을 작성. **실제 수정은 이 Phase에서 하지 않는다** (사용자 승인 후 Run 5 직전에 실행) |
| **Must Read** | `paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md` (L-MAIN-005), `paper_context_ref/09` (§6.3), `paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md` |
| **Output Files** | `docs/orchestration/lr_alignment/04_md_refactor_patch_plan.md` |
| **Forbidden Actions** | `paper_context_ref/` 실제 수정 (계획서 작성만 허용), 코드 작성 |
| **Gate Condition** | 수정 대상 파일 목록 + 변경 이유 + 사용자 승인 필요 항목이 명시됨 |
| **Code Impl Allowed?** | NO |

---

#### Phase 5 — LR Implementation Contract

| 항목 | 내용 |
|---|---|
| **Purpose** | `LikelihoodRatioFalsificationScorer` 모듈의 인터페이스 계약 확정. 시그니처, 입출력 타입, visibility audit 요구사항, 의존 모듈 목록 작성 |
| **Must Read** | `02_option_b_design_plan.md` (Phase 2 산출물), `paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md` (lines 212–226 FORBIDDEN_AGENT_FIELDS), `src/frcgw/schemas/visibility.py` |
| **Output Files** | `docs/orchestration/lr_alignment/05_lr_implementation_contract.md` + `src/frcgw/falsification/lr_scorer_stub.py` (시그니처 stub, 로직 없음) |
| **Forbidden Actions** | 실제 LR 구현 로직 작성, visibility.py 수정, paper_context_ref 수정, P3 재학습 |
| **Gate Condition** | 계약 문서에 입력/출력/에러/visibility audit 명세 완성. stub 파일이 `import`만 하고 로직이 없음. `pytest tests/test_forbidden_field_mirror_sync.py` green |
| **Code Impl Allowed?** | PARTIAL (signature stub only) |

---

#### Phase 6 — Unit Test Plan

| 항목 | 내용 |
|---|---|
| **Purpose** | LR scorer + h_exec trace + visibility audit에 대한 단위 테스트 목록 확정. 테스트 stub (함수 이름 + docstring만 있는 파일) 생성 |
| **Must Read** | `05_lr_implementation_contract.md` (Phase 5 산출물), `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md` (ABL-016/022/023/024 명세) |
| **Output Files** | `docs/orchestration/lr_alignment/06_unit_test_plan.md` + `tests/test_lr_scorer_stub.py` (stub), `tests/test_h_exec_trace_stub.py` (stub) |
| **Forbidden Actions** | 테스트 로직 구현 (stub만 허용), 기존 `tests/test_ablation_runner.py` count 수정 (Phase 10과 동반해야 함), paper_context_ref 수정 |
| **Gate Condition** | test stub 파일이 존재하고 `import`/`pass`만 있음. `tests/test_ablation_runner.py:63` count 수정 계획이 문서에 명시됨 |
| **Code Impl Allowed?** | PARTIAL (test stub only) |

---

#### Phase 7 — Evaluation Gate Design

| 항목 | 내용 |
|---|---|
| **Purpose** | LR scorer 구현 후 P3 재학습 시 PASS/FAIL 판단 기준 명세. CC-P3-G1/G3/G4 재정의 + ABL-016/022/023/024와의 comparison 조건 |
| **Must Read** | `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md` (CLAIM-EVAL-001..012, MET-WM-001, MET-ALT-001, MET-FALS-001/002), `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP.md` |
| **Output Files** | `docs/orchestration/lr_alignment/07_eval_gate_design.md` |
| **Forbidden Actions** | P3 재학습 실행, baseline/ablation 코드 추가, paper_context_ref 수정 |
| **Gate Condition** | CC-P3-G1/G3/G4 판단 기준이 수식/임계값으로 명시됨. planning_calls > 0 조건 포함. ABL-016/022/023 비교 조건 포함 |
| **Code Impl Allowed?** | NO |

---

#### Phase 8 — Text-only LR Smoke Implementation

| 항목 | 내용 |
|---|---|
| **Purpose** | `LikelihoodRatioFalsificationScorer`를 text-only 환경에서 실제 구현. smoke 학습 (300~500 steps) 후 planning_calls > 0 확인 |
| **Must Read** | `05_lr_implementation_contract.md`, `06_unit_test_plan.md`, `paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md`, `src/frcgw/falsification/` |
| **Output Files** | `src/frcgw/falsification/lr_scorer.py` (실 구현), `outputs/runs/p3_lr_smoke/` (학습 결과) |
| **Forbidden Actions** | visibility.py 수정 (사용자 승인 없이), hidden label을 inference input으로 사용, paper_context_ref 수정, P3_EVAL.passed sentinel 생성 (gate 공식 통과 전) |
| **Gate Condition** | `planning_calls > 0` in >= 10% of episodes. `pytest tests/test_lr_scorer.py` green. `test_forbidden_field_mirror_sync.py` green |
| **Code Impl Allowed?** | YES |

---

#### Phase 9 — Synthetic GUI LR Integration

| 항목 | 내용 |
|---|---|
| **Purpose** | gui_env collector (TASK_1021_A 산출물)와 LR scorer를 연동. GUI observation에서 e_t를 추출하여 F_t 계산 가능한지 smoke 확인 |
| **Must Read** | `src/frcgw/gui_env/` (TASK_1021_A 산출물), `02_option_b_design_plan.md`, `paper_context_ref/05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` |
| **Output Files** | `src/frcgw/gui_env/lr_integration.py` (또는 기존 파일 확장), `outputs/runs/p4_lr_smoke/` |
| **Forbidden Actions** | visibility.py 수정 (사용자 승인 없이), DOM string value leakage probe 없이 연동, hidden label 사용 |
| **Gate Condition** | GUI 환경에서 F_t 계산 smoke pass. `test_gui_env_no_hidden_label_in_observation.py` green. DOM value sanitizer 통과 |
| **Code Impl Allowed?** | YES |

---

#### Phase 10 — Baseline/Ablation Expansion

| 항목 | 내용 |
|---|---|
| **Purpose** | BASE-026 (WAC-style) / BASE-027 (CUWM-style) / BASE-028 (WebWorld-style) + ABL-016/017/022/023/024/035/039 구현. `tests/test_ablation_runner.py:63` count 동반 업데이트 필수 |
| **Must Read** | `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7 (BASE-001..028), §8 (ABL-001..042)`, `claim_align_20260516_R1.md`, `exp_design_20260516_R1.md` |
| **Output Files** | `src/frcgw/evaluation/baselines.py` (BASE-026/027/028 추가), `src/frcgw/evaluation/ablations.py` (ABL-017/022 추가 등), `tests/test_ablation_runner.py` (count 업데이트) |
| **Forbidden Actions** | `tests/test_ablation_runner.py` count 업데이트 없이 ablation 추가. visibility.py 수정. LR scorer 없이 baseline 추가만 하는 것 |
| **Gate Condition** | `pytest tests/test_baselines.py tests/test_ablation_runner.py` all green. BASE-026/027/028 각각 단위 테스트 통과 |
| **Code Impl Allowed?** | YES |

---

#### Phase 11 — Verification and Evaluation

| 항목 | 내용 |
|---|---|
| **Purpose** | LR scorer + 신규 baseline/ablation 포함 full eval rerun. leakage audit. MET-WM-001/MET-ALT-001/MET-FALS-001/MET-PERSIST-001 계산 |
| **Must Read** | `07_eval_gate_design.md`, `paper_context_ref/10 §6 (Metrics)`, `paper_context_ref/13 §9 (Eval procedure)`, `paper_context_ref/15_TDD lines 212–226` |
| **Output Files** | `outputs/runs/p3_lr_eval/` (metrics.json, ablation_results.json), `outputs/phase_gates/P3_LR_EVAL.passed` (gate 통과 시) |
| **Forbidden Actions** | MET-PERSIST-001 계산 없이 P3_LR gate 통과 선언. fake/manual 수치 report에 기재. leakage audit 생략 |
| **Gate Condition** | CC-P3-G1/G3/G4 PASS (07_eval_gate_design.md 기준). planning_calls > 0. MET-WM-001/ALT-001 계산됨. leakage audit green |
| **Code Impl Allowed?** | YES |

---

#### Phase 12 — Survivability Decision Report

| 항목 | 내용 |
|---|---|
| **Purpose** | C1~C6 각 concept에 대해 Evidence Card를 모두 채우고 ALIVE_WITH_EVIDENCE / CONDITIONAL_ALIVE / DEAD_COLLAPSED 최종 판정 |
| **Must Read** | `03_concept_survivability_ledger.md` (Evidence Card schema), Phase 11 산출물 (`outputs/runs/p3_lr_eval/`), `07_eval_gate_design.md` |
| **Output Files** | `docs/orchestration/lr_alignment/12_survivability_decision_report.md` |
| **Forbidden Actions** | Evidence Card 없이 status 판정. fake 수치 사용. Phase 11 gate 통과 없이 Phase 12 시작 |
| **Gate Condition** | C1~C6 모든 Evidence Card의 6개 필수 필드가 채워짐. ALIVE/DEAD/CONDITIONAL 판정 근거가 artifact path로 참조됨 |
| **Code Impl Allowed?** | NO |

---

## Section 5. Run Segmentation Plan

총 7개 Run (Run 0~6). 각 Run은 독립적인 세션에서 실행된다.

| Run | Phase | 목적 | 완료 조건 | 허용 작업 | 금지 작업 |
|---|---|---|---|---|---|
| **Run 0** | 본 파일 작성 | Phase 0~12 최상위 라우터 고정 | 본 파일 git commit (사용자 승인 후), Phase 0~12 표 13행 완비, Run 0~6 표 7행 완비 | MD 파일 1개 신규 작성 | 코드 작성, paper_context_ref 수정, P3 재학습, baseline 추가, Evidence Card 작성, Codex 호출 |
| **Run 1** | Phase 0 / 1 / 2 | Option B 공식화 + 위협 감사 + LR 설계 | `DEC_OPTION_B_LR_ALIGNMENT.md`, `01_novelty_theory_threat_audit.md`, `02_option_b_design_plan.md` 생성. `git diff` 확인 시 3개 신규 파일만 변경됨 | MD 파일 3개 신규 작성, 참조 파일 read-only 활용 | 코드 작성, paper_context_ref 수정, P3 재학습, baseline 추가 |
| **Run 2** | Phase 3 / 4 | Evidence Card 설계 + MD refactor 계획 | `03_concept_survivability_ledger.md` (Evidence Card schema + C1~C6 stub), `04_md_refactor_patch_plan.md` 생성. paper_context_ref 실제 수정은 defer | MD 파일 2개 신규 작성 | paper_context_ref 실제 수정, status를 ALIVE/DEAD로 판정 (stub만), 코드 작성 |
| **Run 3** | Phase 5 / 6 / 7 | LR 구현 계약 + 테스트 계획 + eval gate 명세 | `05_lr_implementation_contract.md`, `06_unit_test_plan.md`, `07_eval_gate_design.md` + stub 파일 생성. 실제 구현 로직 없음 | MD 파일 3개 + signature/test stub 파일, read-only 참조 | 실제 LR 구현 로직 작성, visibility.py 수정, paper_context_ref 수정, P3 재학습 |
| **Run 4** | Phase 8 / 9 | Text-only LR smoke + GUI env LR 연동 | `lr_scorer.py` 구현, text-only smoke planning_calls > 0. GUI env F_t 계산 smoke pass | LR 구현, text-only/GUI smoke 실행 | visibility.py 수정 (사용자 승인 없이), hidden label inference input 사용, paper_context_ref 수정 |
| **Run 5** | Phase 10 | Baseline/Ablation 확장 | BASE-026/027/028 + ABL-017/022 외 누락 항목 구현. `test_ablation_runner.py` count 동반 업데이트. 모든 단위 테스트 green | baselines.py / ablations.py 수정, 테스트 업데이트 | `test_ablation_runner.py` count 미업데이트 상태 ablation 추가, LR scorer 없이 baseline만 추가 |
| **Run 6** | Phase 11 / 12 | Full eval rerun + 최종 판정 | CC-P3-G1/G3/G4 PASS. MET-WM-001/ALT-001/FALS-001/PERSIST-001 계산됨. C1~C6 Evidence Card 완성. `12_survivability_decision_report.md` 생성 | eval rerun, leakage audit, report 생성 | fake 수치 사용, Phase 11 gate 미통과 상태로 Phase 12 진입, Evidence Card 없이 status 판정 |

---

## Section 6. Global Forbidden Actions (반복 강제)

> 이 체크리스트는 매 Run 시작 시 확인한다.  
> 아래 항목 중 하나라도 위반하는 작업은 즉시 중단하고 blocker를 보고한다.

1. **LR alignment gate 없이 P3 재학습 금지**: `05_lr_implementation_contract.md` 존재 전에 P3 재학습을 실행하지 않는다.
2. **LR 구현의 대체재로 baseline/ablation 추가 금지**: `LikelihoodRatioFalsificationScorer` 없는 상태에서 BASE-026/027/028만 추가해도 mechanism delta가 살아나지 않는다.
3. **LR scorer 구현/테스트 전 C3 해결 선언 금지**: `lr_scorer.py` 구현 + `test_lr_scorer.py` green 전에 C3을 SOLVED/ALIVE로 표시하지 않는다.
4. **h_exec trace populate 전 C1 ALIVE 선언 금지**: `selected_hypothesis_id` 필드가 step log에 populate되고 MET-PERSIST-001이 계산 가능해지기 전에 C1을 ALIVE로 표시하지 않는다.
5. **crossed split + ABL-001 + latent probe 전 C2 ALIVE 선언 금지**: `generate_same_regime_diff_grammar_episodes()` 구현, ABL-001 존재, MET-LATENT-001 계산 전에 C2를 ALIVE로 표시하지 않는다.
6. **MET-WM-001/MET-ALT-001 전 C4 ALIVE 선언 금지**: `rollout_fidelity()`, `alternative_adoption_rate()` 함수 구현 전에 C4를 ALIVE로 표시하지 않는다.
7. **ABL-017 + rewrite metric 전 C5 ALIVE 선언 금지**: ABL-017 (no_L_intent_action_mapping) 구현 + MET-REWRITE-001 계산 전에 C5를 ALIVE로 표시하지 않는다.
8. **`P3_EVAL.passed` sentinel을 논문 증거로 사용 금지**: `P3_EVAL.BLOCKED_planning_calls_zero.md`가 해당 sentinel을 supersede한다. Phase 11 gate 통과 후 새 sentinel `P3_LR_EVAL.passed`를 사용한다.
9. **hidden label inference input 사용 금지**: `FORBIDDEN_AGENT_FIELDS` (15개 필드, `paper_context_ref/15_TDD lines 212–226`)가 agent observation, dataloader input, model input, prompt input에 들어가면 즉시 중단한다.
10. **실험 결과 날조 금지**: fake number, placeholder metric, manually typed result를 report에 기재하지 않는다.

---

## Section 7. Evidence and Status Policy

### 7.1 Status 분류 (6단계)

| Status | 정의 | 전환 조건 |
|---|---|---|
| `ALIVE_WITH_EVIDENCE` | Evidence Card 모든 필드 채워짐. ablation delta > sensitivity threshold | Phase 11 eval 완료 + Evidence Card 완성 |
| `CONDITIONAL_ALIVE` | Evidence Card 일부 비어 있으나 대체 증거 있음. ablation delta 측정 중 | Phase 3~10에서 partial evidence 존재 |
| `BLOCKED` | Evidence Card 필수 필드 누락. 다음 Run에서 채워야 함 | 현재 C1~C6 모두 해당 (Phase 0 시점) |
| `DEAD_COLLAPSED` | ablation delta = 0 확정, 또는 SOURCE_ONLY로 확정 | Phase 11 eval + ablation 비교 완료 |
| `SUPERSEDED` | 다른 concept으로 대체됨 (예: BCE falsification scorer → LR scorer) | Evidence Card에 대체 항목 명시 |
| `UNKNOWN_NEEDS_EXPERIMENT` | 측정 자체가 불가능. P4/P5 이후 재평가 필요 | 현재 C2/C4 일부 항목 해당 |

### 7.2 Evidence Card 필수 필드 (6개)

> 상세 schema는 Phase 3 (`03_concept_survivability_ledger.md`)에서 확정된다.  
> 아래는 Phase 3 설계를 위한 preview다.

| 필드 | 내용 |
|---|---|
| `source_evidence` | paper_context_ref MD anchor (파일명 + 섹션 + line 번호) |
| `code_evidence` | 파일 경로 + 함수/클래스 심볼 |
| `test_evidence` | 테스트 파일 + 테스트 함수명 + 마지막 green commit hash |
| `experiment_evidence` | artifact 경로 (해당 없으면 `MISSING`) |
| `counter_evidence` | 반증 가능한 증거 또는 ablation 결과 |
| `decision_rationale` | 한국어 2~3문장 판정 근거 |

### 7.3 Status Transition 규칙

- Status 변경은 **항상 Evidence Card 갱신과 동반**되어야 한다.
- Evidence Card 없이 status만 변경하는 commit은 reject 사유가 된다.
- Status 변경 commit message에는 반드시 `evidence_card: updated` 태그를 포함한다.
- `DEAD_COLLAPSED`로의 전환은 Phase 11 ablation 결과 artifact path가 `experiment_evidence`에 기재된 경우에만 허용된다.

### 7.4 현재 C1~C6 Status (Run 0 시점)

| Claim | 현재 Status | 주요 Blocker | 해제 조건 |
|---|---|---|---|
| C1 wrong-grammar persistence | `BLOCKED` | h_exec trace missing; planning_calls=0 | Phase 8 (h_exec trace) + Phase 11 (MET-PERSIST-001) |
| C2 regime/grammar separation | `BLOCKED` | Locatello impossibility; ABL-001 missing; crossed split absent | Phase 10 (ABL-001) + Phase 11 (latent probe) |
| C3 falsification mechanism | `CONDITIONAL_ALIVE` | LR vs BCE gap (ISSUE-03). LR 구현 후 ablation으로 판정 | Phase 8 (LR scorer) + Phase 11 (ABL-022/023 비교) |
| C4 alternative grammar rollout | `BLOCKED` | MET-WM-001/ALT-001 missing; rollout_steps=0 | Phase 10 (MET-WM-001/ALT-001) + Phase 11 |
| C5 grammar-conditioned rewrite | `CONDITIONAL_ALIVE` | ABL-017 missing | Phase 10 (ABL-017) + Phase 11 |
| C6 compute gate | `BLOCKED` | CATTS threat unregistered; BASE-015 missing | Phase 1 (위협 감사) + Phase 10 (BASE-015) + Phase 11 |

---

## Section 8. Immediate Next Run (Run 1 예고)

### 8.1 Run 1 생성 파일 (3개)

| 파일 | 내용 |
|---|---|
| `docs/orchestration/lr_alignment/DEC_OPTION_B_LR_ALIGNMENT.md` | Option B 공식 채택 decision record. 채택 근거, math_critic C3 분석 요약, Option A 강등 이유, War Room R1 Verdict C 인용 |
| `docs/orchestration/lr_alignment/01_novelty_theory_threat_audit.md` | CATTS (2602.12276) / VLAA-GUI (2604.21375) / WebUncertainty (2604.17821) 신규 위협 + WebWorld (2602.14721) / WAC (2602.15384) / CUWM (2602.17365) / VeriGUI (2604.05477) 기존 위협 재확인. 각 위협에 대한 FRCG-WM defense 전략 명시 |
| `docs/orchestration/lr_alignment/02_option_b_design_plan.md` | Section 3.2 LR 계약을 full 설계로 확장. F_t/ell_t/b_t/G_t/Rewrite 5개 component의 입력/출력/의존성/실패 모드/구현 가이드라인. ABL-022/023 강등 결정 명시. BCE Option A보존 조건 명시 |

### 8.2 Run 1 금지 항목

- 구현 코드 작성 (테스트 skeleton 포함)
- `paper_context_ref/` 실제 수정 (계획서 작성만 허용)
- P3 재학습 또는 P3_EVAL 재실행
- baseline/ablation 코드 추가
- Evidence Card 작성 (Phase 3로 defer)
- TASK 파일 작성 또는 Codex 호출

### 8.3 Run 1 완료 확인 checklist

```
□ git status: docs/orchestration/lr_alignment/ 하위 3개 신규 파일만 변경됨
□ paper_context_ref/ 하위 어떤 파일도 modified 상태 아님
□ src/frcgw/ 하위 어떤 파일도 modified 상태 아님
□ outputs/phase_gates/ 하위 어떤 파일도 modified/deleted 상태 아님
□ DEC_OPTION_B_LR_ALIGNMENT.md: Option B 정의 + 채택 근거 + War Room R1 Verdict C 인용 포함
□ 01_novelty_theory_threat_audit.md: 신규 3개 + 기존 4개 위협 모두 defense 전략과 함께 기술됨
□ 02_option_b_design_plan.md: F_t/ell_t/b_t/G_t/Rewrite 5개 component 명세 완성
```

---

## Appendix A. 참조 파일 빠른 색인

| 파일 | 관련 Section | 주요 내용 |
|---|---|---|
| `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.2~6.6` | Section 3.2 | ell_t, F_t, G_t, Rewrite 공식 |
| `paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md L-MAIN-005` | Section 3.3 | BCE 현재 구현 (강등 대상) |
| `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7~8` | Section 4 Phase 10 | BASE-001..028, ABL-001..042 |
| `paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md lines 212–226` | Section 6 항목 9 | FORBIDDEN_AGENT_FIELDS 15개 |
| `war_room_R1_synthesis.md` | Section 2, Section 7.4 | Claim-by-Claim Survivability |
| `math_critic_20260516_R1.md` | Section 2 ISSUE-03, Section 3.1 | C3 RISK HIGH, LR vs BCE |
| `claim_align_20260516_R1.md` | Section 2 ISSUE-04, Phase 10 | BASE-026/027/028 missing |
| `reviewer2_20260516_R1.md` | Section 2 ISSUE-02 | h_exec trace blocker (REF-PROBLEM-012) |
| `novelty_scout_20260516_R1.md` | Section 2 ISSUE-07, Phase 1 | CATTS/VLAA-GUI/WebUncertainty |
| `exp_design_20260516_R1.md` | Section 2 ISSUE-08, Phase 10 | CRITICAL ablations 6/14 missing |
| `feasibility_20260516_R1.md` | Section 2 ISSUE-01 | P3_EVAL FRCG-FULL = no_control_grammar |
| `impl_risk_20260516_R1.md` | Phase 5 Must Read | Gatekeeper 5조건, FILES_FORBIDDEN |
| `outputs/phase_gates/P3_EVAL.BLOCKED_planning_calls_zero.md` | Section 2 ISSUE-01, Section 6 항목 8 | P3 gate supersede |
| `2026-05-16_novelty_viability_verdict.md` | Section 1.3, Section 7.4 | Verdict C, C1~C6 survivability |

---

## Appendix B. 이 파일 자체에 대한 검증 체크리스트

Run 0 완료 직후 확인:

```
□ git status: docs/orchestration/lr_alignment/00_OPTION_B_PHASE_ROADMAP.md 1개 untracked 파일만 표시
□ paper_context_ref/ 하위 어떤 파일도 modified 상태 아님
□ src/frcgw/ 하위 어떤 파일도 modified 상태 아님
□ outputs/phase_gates/ 하위 어떤 파일도 modified/deleted 상태 아님
□ Phase 0~12 Master Table: 정확히 13행 (4.1 요약 표 기준)
□ Run Segmentation Plan: 정확히 7행 (Run 0~6)
□ 7개 agent report 모두 최소 1회 인용:
    □ war_room_R1_synthesis.md ✓ (Section 1.3, Section 7.4)
    □ math_critic_20260516_R1.md ✓ (Section 2 ISSUE-03, Section 3.1)
    □ claim_align_20260516_R1.md ✓ (Section 2 ISSUE-04)
    □ reviewer2_20260516_R1.md ✓ (Section 2 ISSUE-02)
    □ novelty_scout_20260516_R1.md ✓ (Section 2 ISSUE-07)
    □ exp_design_20260516_R1.md ✓ (Section 2 ISSUE-08)
    □ feasibility_20260516_R1.md ✓ (Section 2 ISSUE-01)
    □ impl_risk_20260516_R1.md ✓ (Phase 5 Must Read)
```

---

*이 파일은 Option B alignment 기간 한정 부차 라우터다. Phase 12 완료 후 archive로 이동된다.*
