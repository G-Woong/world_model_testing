---
file_id: NOVELTY-THREAT-AUDIT-R1
title: Novelty/Theory Threat Audit — Phase 1 산출물
phase: 1 (Novelty/Theory Threat Audit)
run: 1
date: 2026-05-16
status: THREAT_AUDIT_RECORD
language: ko
type: analysis_not_final_related_work
---

# 01_novelty_theory_threat_audit.md

**Phase**: 1 — Novelty/Theory Threat Audit  
**Run**: 1  
**Date**: 2026-05-16  
**Type**: analysis document (not final related work)

---

## Section 1. Purpose

이 문서는 **related work 최종본이 아니다**.

역할:
- Option B LR scorer가 novelty 방어에 실제로 필요한지를 threat별로 감사
- 신규 위협 (CATTS/VLAA-GUI/WebUncertainty) + 기존 위협 (WebWorld/WAC/CUWM/VeriGUI) 재확인
- `paper_context_ref/01_RELATED_WORK_THREAT_MAP.md` 수정은 하지 않음 (사용자 승인 + Phase 4 이후)

원칙:
- **novelty 확정 금지**: Run 1은 threat audit만
- **C1~C6를 ALIVE/DEAD로 판정 금지**: threat audit verdict만 기록
- 모든 distinction은 required baseline / ablation / metric과 연결

---

## Section 2. Threat Coverage Table

총 14개 threat (신규 3, 기존 4, 추가 6, 선택 1).

---

### THREAT-01: CATTS

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-01 |
| **Threat Name** | CATTS (Calibrated Adaptive Token and Task Scaling) |
| **Source Anchor** | arXiv 2602.12276 (2-source confirmed: arxiv.org + alanhou.org blog) |
| **What It Already Solves** | 동적 compute allocation: vote entropy + top-1/top-2 margin으로 uncertainty-based compute gate. +9.1% WebArena-Lite, 2.3x fewer tokens than uniform scaling |
| **What It Does Not Solve** | grammar hypothesis 전환 조건 미명시. wrong-grammar hypothesis가 high confidence로 유지되는 episode에서 compute gate 미작동. `h_exec` 개념 없음 |
| **Overlap With FRCG-WM** | C6 "decision-relevant compute gate"와 phenomenologically 유사. compute를 불확실도 기반으로 배분한다는 표면 구조 겹침 |
| **Option B Distinction** | CATTS의 gate = prediction uncertainty (entropy). FRCG-WM의 G_t = F_t (LR score) ∧ ΔV_t ∧ P_switch ∧ cost-benefit. LR scorer 없이는 CATTS와의 구분이 uncertainty threshold로 collapse됨. compute-matched experiment 필요 |
| **Attacked Claims** | C6 (decision-relevant compute gate) PRIMARY; C3 (falsification) SECONDARY |
| **Required Baseline** | BASE-015 (ComputeMatchedRandomReallocation), CATTS-equivalent (uncertainty-entropy gate) |
| **Required Ablation** | ABL-023 (uncertainty instead of falsification), ABL-033 (no decision-relevance gate) |
| **Required Metric** | MET-COMP-003 (compute_normalized_return), MET-COMP-004 (compute_efficiency_gain) |
| **Verdict** | `MANAGEABLE_WITH_LR` — F_t (grammar switch value) ≠ prediction entropy는 LR scorer가 있어야 실험 가능 |

---

### THREAT-02: VLAA-GUI

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-02 |
| **Threat Name** | VLAA-GUI (Visual Loop-Aware Agent for GUI) |
| **Source Anchor** | arXiv 2604.21375 (2-source confirmed: arxiv.org + huggingface.co/papers) |
| **What It Already Solves** | Loop Breaker: rule-based (repeat count + screen hash) → interaction mode switch + search. Nearly halves wasted steps; 77.5% OSWorld. wrong-grammar failure loop를 heuristic rule로 탈출 |
| **What It Does Not Solve** | grammar hypothesis posterior 업데이트 없음. false positive (같은 grammar가 다른 mode에서 재사용 가능할 때) 처리 미명시. `h_exec` trace 없음 |
| **Overlap With FRCG-WM** | C1 (wrong-grammar persistence 감소), C3 (failure detection + mode switch)와 phenomenologically 유사. failure loop를 줄이고 mode를 전환한다는 표면 구조 겹침 |
| **Option B Distinction** | VLAA-GUI의 detection = heuristic (repeat count + hash). FRCG-WM의 F_t = LR score over alternative hypotheses. posterior update → alternative grammar adoption → rollout → rewrite가 VLAA-GUI에 없음. Precision/Recall 비교 실험으로 구분 가능 |
| **Attacked Claims** | C1 (persistence detection) PRIMARY; C3 (falsification mechanism) SECONDARY |
| **Required Baseline** | BASE-loop-heuristic (VLAA-GUI style: repeat count gate), BASE-005 (VerifierOnlyAgent) |
| **Required Ablation** | ABL-002 (no-control-grammar), ABL-016 (no L_falsification) |
| **Required Metric** | MET-PERSIST-001 (wrong_control_grammar_persistence), MET-FALS-001 (falsification_precision), MET-FALS-002 (falsification_recall) |
| **Verdict** | `MANAGEABLE_WITH_LR` — heuristic vs posterior-based falsification 비교는 F_t 구현 이후 가능 |

---

### THREAT-03: WebUncertainty

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-03 |
| **Threat Name** | WebUncertainty (Dual-Level Uncertainty for Web Agent) |
| **Source Anchor** | arXiv 2604.17821 (2-source confirmed: arxiv.org/html + arxiv.org/abs) |
| **What It Already Solves** | Dual-level uncertainty (aleatoric + epistemic) + MCTS reasoning. 불확실도 수준에 따라 reasoning depth를 조정 |
| **What It Does Not Solve** | grammar hypothesis 구조 없음. falsification evidence accumulation 없음. alternative grammar posterior 없음 |
| **Overlap With FRCG-WM** | C6 (compute gate) + C3 (falsification gate) 표면 구조 겹침. uncertainty가 높을 때 더 많은 compute를 쓴다는 행동 유사 |
| **Option B Distinction** | WebUncertainty의 gate = aleatoric/epistemic uncertainty. FRCG-WM의 G_t = F_t ∧ ΔV_t ∧ P_switch ∧ cost-benefit. high confidence wrong grammar episode (F_t > τ_f이지만 epistemic uncertainty 낮음)에서 구분됨. LR scorer로 이 사례 생성 가능 |
| **Attacked Claims** | C6 (compute gate) PRIMARY; C3 SECONDARY |
| **Required Baseline** | BASE-012 (UncertaintyGatedAgent) 강화판 |
| **Required Ablation** | ABL-023 (uncertainty instead of falsification) |
| **Required Metric** | MET-COMP-003, MET-COMP-004 |
| **Verdict** | `MANAGEABLE_WITH_LR` — 고신뢰 오류 문법 episode를 F_t로 탐지한다는 실험이 필요 |

---

### THREAT-04: WebWorld

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-04 |
| **Threat Name** | WebWorld (Generic Web World Model) |
| **Source Anchor** | arXiv 2602.14721 (2-source: arxiv.org + huggingface.co/Qwen/WebWorld-8B) |
| **What It Already Solves** | Generic web world model. next-state prediction, task execution on web. Qwen2.5-7B 기반. action-effect 예측 포함 |
| **What It Does Not Solve** | control grammar hypothesis 구조 없음. regime 개념 없음. alternative hypothesis set 없음. wronggrammar persistence 측정 불가. grammar-conditioned rewrite 없음 |
| **Overlap With FRCG-WM** | C4 (alternative grammar rollout)과 next-state WM 구조 겹침. action-effect 예측이 표면적으로 유사 |
| **Option B Distinction** | WebWorld WM 예측 = grammar-agnostic next state. FRCG-WM WM = grammar-conditioned alternative hypothesis rollout. ABL-002 (no-control-grammar) ablation이 이 distinction을 실험적으로 검증해야 함 |
| **Attacked Claims** | C4 (alternative grammar rollout) PRIMARY; C1/C3 SECONDARY |
| **Required Baseline** | BASE-028 (WebWorld-style: grammar-agnostic next-state WM) |
| **Required Ablation** | ABL-002 (no-control-grammar), ABL-024 (no-alternative-hypothesis) |
| **Required Metric** | MET-WM-001 (rollout_fidelity), MET-ALT-001 (alternative_adoption_rate) |
| **Verdict** | `REQUIRES_BASELINE` — BASE-028 없이는 ATTACK-DEF-004 (direct threat response) 불가 |

---

### THREAT-05: WAC

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-05 |
| **Threat Name** | WAC (Web Agent with Consequence Simulation) |
| **Source Anchor** | arXiv 2602.15384 (2-source: arxiv.org/abs + arxiv.org/html) |
| **What It Already Solves** | Action correction + consequence simulation. 행동 실행 전 결과를 시뮬레이션하고 correction |
| **What It Does Not Solve** | grammar hypothesis 구조 없음. alternative grammar adoption 없음. grammar-conditioned rewrite 없음. `h_exec` 개념 없음 |
| **Overlap With FRCG-WM** | C5 (grammar-conditioned rewrite)와 action correction 표면 구조 겹침. correction + simulation이 유사하게 보임 |
| **Option B Distinction** | WAC correction = generic consequence simulation. FRCG-WM Rewrite = grammar-conditioned (selected_hypothesis h*에 의존). 같은 intent이라도 다른 grammar에서 다른 rewrite 결과가 나와야 C5 distinction이 성립 |
| **Attacked Claims** | C5 (grammar-conditioned rewrite) PRIMARY; C4 SECONDARY |
| **Required Baseline** | BASE-026 (WAC-style: consequence simulation without grammar conditioning) |
| **Required Ablation** | ABL-017 (no_L_intent_action_mapping), ABL-035 (no-action-rewrite) |
| **Required Metric** | MET-REWRITE-001 (rewrite_success_rate) |
| **Verdict** | `REQUIRES_BASELINE` — BASE-026 없이 C5 defense 불가 |

---

### THREAT-06: CUWM

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-06 |
| **Threat Name** | CUWM (Controlled Uncertainty World Model) |
| **Source Anchor** | arXiv 2602.17365 (2-source: arxiv.org + huggingface.co/papers) |
| **What It Already Solves** | Frozen base + WM test-time search. frozen LLM에 WM을 붙여 test-time search로 성능 향상 |
| **What It Does Not Solve** | grammar hypothesis 구조 없음. alternative grammar posterior 없음. grammar-conditioned rollout 없음 |
| **Overlap With FRCG-WM** | C4 (alternative hypothesis rollout) + C6 (compute-controlled search)와 표면 구조 겹침 |
| **Option B Distinction** | CUWM search = grammar-agnostic uncertainty-based. FRCG-WM = grammar-conditioned alternative hypothesis adoption. ABL-024 (no-alternative-hypothesis)가 이 distinction을 실험해야 함 |
| **Attacked Claims** | C4 PRIMARY; C6 SECONDARY |
| **Required Baseline** | BASE-027 (CUWM-style: frozen LLM + grammar-agnostic WM search) |
| **Required Ablation** | ABL-024 (no-alternative-hypothesis), ABL-033 (no decision-relevance gate) |
| **Required Metric** | MET-WM-001 (rollout_fidelity), MET-COMP-003 |
| **Verdict** | `REQUIRES_BASELINE` — BASE-027 없이 C4 defense 불가 |

---

### THREAT-07: VeriGUI

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-07 |
| **Threat Name** | VeriGUI (Don't Act Blindly — Action Verification for GUI) |
| **Source Anchor** | arXiv 2604.05477 (2-source: arxiv.org/abs + arxiv.org/html) |
| **What It Already Solves** | Action-effect verification + failure recovery. action → verify → [fail] → corrective reasoning → new action. binary verification layer |
| **What It Does Not Solve** | grammar hypothesis posterior update 없음. alternative grammar set 없음. grammar-conditioned rewrite 없음. `F_t = LR score` 없음 |
| **Overlap With FRCG-WM** | C3 (falsification mechanism) + C5 (rewrite)와 가장 가까운 overlap. verification 후 corrective action을 취한다는 구조가 유사 |
| **Option B Distinction** | VeriGUI = binary verification (action failed/succeeded) → corrective reasoning. FRCG-WM = F_t = max_alt[ell(h_alt)-ell(h_exec)] → posterior update → alternative grammar adoption → grammar-conditioned rollout → Rewrite. VeriGUI는 verification layer에서 종료. FRCG-WM은 posterior update + alternative grammar adoption + rewrite까지 진행. LR scorer 없이는 이 distinction이 "binary verifier vs LR verifier" 차이로만 보임 |
| **Attacked Claims** | C3 (falsification) PRIMARY; C5 (rewrite) SECONDARY |
| **Required Baseline** | BASE-005 (VerifierOnlyAgent 강화: real effect-checking policy), BASE-006 (VerifierHeuristicRecovery) |
| **Required Ablation** | ABL-016 (no L_falsification), ABL-022 (no falsification score gate), ABL-023 (uncertainty instead of falsification) |
| **Required Metric** | MET-FALS-001 (falsification_precision), MET-FALS-002 (falsification_recall) |
| **Verdict** | `MANAGEABLE_WITH_LR` — VeriGUI는 binary verify. FRCG-WM은 LR posterior update. LR scorer 구현 이후 비교 가능 |

---

### THREAT-08: StressWeb

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-08 |
| **Threat Name** | StressWeb (Action Semantic Remapping) |
| **Source Anchor** | arXiv 2604.16385 (2-source: arxiv.org/abs + arxiv.org/html; war_room_R1_synthesis 확인: P-013 CONFIRMED) |
| **What It Already Solves** | External perturbation (RemapE/Remap): action semantics가 외부에서 바뀌는 환경에서 agent behavior. grammar shift를 외부 환경 변화로 구현 |
| **What It Does Not Solve** | internal hypothesis persistence 없음. agent의 내부 hypothesis가 외부 perturbation에 맞게 업데이트되는지 측정 없음 |
| **Overlap With FRCG-WM** | C1 (wrong-grammar persistence) + 문제 정의에서 "grammar shift"가 겹침 |
| **Option B Distinction** | StressWeb = external perturbation (grammar가 외부에서 바뀜). FRCG-WM = internal hypothesis persistence (agent가 correct grammar를 이미 관찰했지만 wrong hypothesis를 유지함). 출처와 방향이 다름 |
| **Attacked Claims** | C1 SECONDARY; 문제 정의 uniqueness |
| **Required Baseline** | 없음 (추가 baseline 불필요) |
| **Required Ablation** | ABL-002 (no-control-grammar) |
| **Required Metric** | MET-PERSIST-001 (wrong_control_grammar_persistence) |
| **Verdict** | `MANAGEABLE_WITH_LR` — external perturbation vs internal persistence 구분은 명확 |

---

### THREAT-09: Generic Anomaly Detection

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-09 |
| **Threat Name** | Generic Anomaly Detection (행동 이상 탐지 류) |
| **Source Anchor** | 특정 2026 논문 미특정. 패턴으로서 위협 |
| **What It Already Solves** | action-effect anomaly 탐지. 예상과 다른 결과가 나오면 재시도 또는 다른 행동 선택 |
| **What It Does Not Solve** | grammar hypothesis 구조 없음. alternative hypothesis 정의 없음. falsification이 아니라 outlier detection |
| **Overlap With FRCG-WM** | C3 (falsification mechanism)이 anomaly detection으로 환원될 수 있다는 주장 |
| **Option B Distinction** | Anomaly detection = unsupervised outlier. FRCG-WM falsification = hypothesis-conditioned LR score (F_t). "이상 탐지"와 "grammar hypothesis 반증"은 입력 구조가 다름. ABL-016 (no L_falsification) ablation이 이 distinction 검증 |
| **Attacked Claims** | C3 PRIMARY |
| **Required Baseline** | BASE-005 강화 (anomaly detection 기반 recovery) |
| **Required Ablation** | ABL-016 (no L_falsification) |
| **Required Metric** | MET-FALS-001, MET-FALS-002 |
| **Verdict** | `MANAGEABLE_WITH_LR` — LR 구조가 anomaly detection과 다름을 ABL-016으로 보여줄 수 있음 |

---

### THREAT-10: Generic Uncertainty Gating

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-10 |
| **Threat Name** | Generic Uncertainty Gating (불확실도 기반 계획 게이팅) |
| **Source Anchor** | 패턴으로서 위협 (CATTS/WebUncertainty와 겹치나 더 일반적) |
| **What It Already Solves** | 모델 불확실도 > threshold일 때 planning compute를 추가. entropy, dropout uncertainty 등 다양한 방법 |
| **What It Does Not Solve** | grammar hypothesis 구조 없음. high-confidence wrong grammar episode (F_t > τ_f이지만 uncertainty 낮음) 처리 불가 |
| **Overlap With FRCG-WM** | C6 (decision-relevant compute gate)와 행동적으로 구분 어려움 |
| **Option B Distinction** | Uncertainty gate = `uncertainty > threshold`. FRCG-WM gate G_t = F_t ∧ ΔV_t ∧ P_switch ∧ cost-benefit. 핵심 구분 포인트: high-confidence wrong-grammar episode에서 uncertainty gate는 작동하지 않지만 F_t gate는 작동 |
| **Attacked Claims** | C6 PRIMARY; C3 SECONDARY |
| **Required Baseline** | BASE-012 (UncertaintyGatedAgent) |
| **Required Ablation** | ABL-023 (uncertainty instead of falsification) |
| **Required Metric** | MET-COMP-003, MET-COMP-004 |
| **Verdict** | `MANAGEABLE_WITH_LR` — high-confidence wrong-grammar episode dataset으로 구분 가능 |

---

### THREAT-11: Generic Verifier-Only Recovery

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-11 |
| **Threat Name** | Generic Verifier-Only Recovery (검증기 단독 복구) |
| **Source Anchor** | 패턴으로서 위협. BASE-005/BASE-006이 이 패턴 |
| **What It Already Solves** | action failure 탐지 후 재시도 또는 대안 행동 선택. verifier output = binary (fail/succeed) |
| **What It Does Not Solve** | grammar hypothesis posterior 업데이트 없음. alternative grammar adoption 없음. grammar-conditioned rewrite 없음 |
| **Overlap With FRCG-WM** | C3/C5와 표면 구조 겹침. "fail → recover" 행동이 유사 |
| **Option B Distinction** | Verifier-only = binary fail → 재시도. FRCG-WM = F_t (LR) → grammar posterior update → alternative grammar → Rewrite. LR scorer 없이는 "sophisticated verifier"와 구분이 흐릿함 |
| **Attacked Claims** | C3 PRIMARY; C5 SECONDARY |
| **Required Baseline** | BASE-005, BASE-006 |
| **Required Ablation** | ABL-016 (no L_falsification), ABL-022 (no falsification score gate) |
| **Required Metric** | MET-FALS-001, MET-FALS-002, MET-REWRITE-001 |
| **Verdict** | `MANAGEABLE_WITH_LR` — verifier-only가 맞추는 episode와 LR-falsification이 맞추는 episode가 다르다는 실험 필요 |

---

### THREAT-12: Generic Tree Search

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-12 |
| **Threat Name** | Generic Tree Search (문법 무관 트리 탐색) |
| **Source Anchor** | 패턴으로서 위협. BASE-013 (TreeSearchAgent)이 이 패턴 |
| **What It Already Solves** | 다양한 action sequence를 트리 형태로 탐색. 더 많은 compute로 더 좋은 action 선택 |
| **What It Does Not Solve** | grammar hypothesis 구조 없음. alternative grammar adoption 없음. grammar-conditioned rollout 없음 |
| **Overlap With FRCG-WM** | C4 (alternative grammar rollout)과 "여러 가능성 탐색" 표면 구조 겹침 |
| **Option B Distinction** | Tree search = action space 탐색 (grammar-agnostic). FRCG-WM = grammar hypothesis space 탐색 (A_t^H). same action이 다른 grammar 아래서 다른 expected value를 가진다는 것이 핵심 구분 |
| **Attacked Claims** | C4 PRIMARY |
| **Required Baseline** | BASE-013 (TreeSearchAgent) |
| **Required Ablation** | ABL-024 (no-alternative-hypothesis), ABL-026 (no-rollout) |
| **Required Metric** | MET-WM-001, MET-ALT-001 |
| **Verdict** | `REQUIRES_BASELINE` — BASE-013 없이 C4 tree search 방어 불가 |

---

### THREAT-13: Next-State World Model (Generic)

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-13 |
| **Threat Name** | Generic Next-State World Model |
| **Source Anchor** | 패턴으로서 위협. BASE-009 (NextStateWMOnlyAgent)이 이 패턴 |
| **What It Already Solves** | 다음 상태 예측. action-effect 예측 기반 action 선택 |
| **What It Does Not Solve** | grammar hypothesis conditioning 없음. alternative grammar adoption 없음. posterior update 없음 |
| **Overlap With FRCG-WM** | C4와 next-state prediction 구조 겹침. WebWorld와 유사 |
| **Option B Distinction** | Generic next-state WM = p(s_{t+1} | s_t, a_t). FRCG-WM = p(s_{t+1} | s_t, a_t, h) where h = grammar hypothesis. grammar conditioning이 핵심. ABL-002 (no-control-grammar) ablation이 이 distinction 검증 |
| **Attacked Claims** | C4 PRIMARY; C3 SECONDARY |
| **Required Baseline** | BASE-009 (NextStateWMOnlyAgent) |
| **Required Ablation** | ABL-002 (no-control-grammar), ABL-024 (no-alternative-hypothesis) |
| **Required Metric** | MET-WM-001 (rollout_fidelity) |
| **Verdict** | `MANAGEABLE_WITH_LR` — grammar-conditioned rollout vs grammar-agnostic rollout은 ABL-002로 검증 가능 |

---

### THREAT-14: POPPER (선택 항목)

| 필드 | 내용 |
|---|---|
| **Threat ID** | THREAT-14 |
| **Threat Name** | POPPER (Scientific Falsification Agent) |
| **Source Anchor** | arXiv 2502.09858 (novelty_scout_20260516_R1.md: UNKNOWN — 추가 확인 필요) |
| **What It Already Solves** | 과학적 가설 반증 에이전트. scientific hypothesis를 데이터로 반증하는 구조 |
| **What It Does Not Solve** | Web/GUI agent context 미확인. control grammar hypothesis 구조와의 overlap 미분석 |
| **Overlap With FRCG-WM** | "falsification"이라는 개념적 단어 겹침. mechanism은 다를 가능성 높음 |
| **Option B Distinction** | 미분석. 추가 검토 필요 |
| **Attacked Claims** | C3 (falsification mechanism) POTENTIAL |
| **Required Baseline** | UNKNOWN — 더 읽어야 판단 가능 |
| **Required Ablation** | UNKNOWN |
| **Required Metric** | UNKNOWN |
| **Verdict** | `UNKNOWN_NEEDS_MORE_SEARCH` — 2-source cross-check 미완료. Phase 1에서 verdict 보류 |

---

## Section 3. Compound Attacks

### §3.1 VeriGUI (THREAT-07) + VLAA-GUI (THREAT-02) + WebWorld (THREAT-04)

**1. 이 조합이 FRCG-WM을 어떻게 흡수할 수 있는가?**

VeriGUI (action-effect verification) + VLAA-GUI (heuristic mode switch + loop breaker) + WebWorld (generic next-state WM)를 파이프라인으로 연결하면:
- failure detection → mode switch → WM-guided action selection

이 파이프라인이 FRCG-WM의:
- C3 (LR falsification) → VeriGUI로 대체 가능?
- C1 (persistence detection) → VLAA-GUI로 대체 가능?
- C4 (alternative grammar rollout) → WebWorld WM으로 대체 가능?

라는 주장이 가능. 3개 기존 방법의 ensemble = FRCG-WM?

**2. Option B LR scorer가 없으면 무엇이 붕괴되는가?**

LR scorer 없이는:
- VeriGUI (binary verification) vs FRCG-WM (LR posterior update)의 구분이 "더 복잡한 verifier"로만 보임
- `F_t`가 단순 failure flag (VeriGUI)와 다른 이유를 실험적으로 보여줄 수 없음
- 복합 파이프라인과의 비교 실험 설계 자체가 불가능 (MET-FALS-001/002 없음)

**3. 필요한 방어 실험**

- VeriGUI가 성공한 episode에서도 FRCG-WM의 `F_t`가 grammar hypothesis를 계속 잘못 판정하는지 확인
- 즉: "verification success 후에도 wrong grammar hypothesis를 유지하는 episode" 생성 실험 필요
- BASE-005/006 (VeriGUI-style) vs FRCG-WM LR full pipeline 비교 → MET-PERSIST-001 비교
- ABL-016 (no L_falsification) + ABL-022 (no falsification score gate) 동반 필요

---

### §3.2 CATTS (THREAT-01) + WebUncertainty (THREAT-03)

**1. 이 조합이 FRCG-WM을 어떻게 흡수할 수 있는가?**

CATTS (uncertainty-based compute gate: vote entropy + margin) + WebUncertainty (dual-level aleatoric+epistemic uncertainty + MCTS)를 결합하면:
- "uncertainty가 높을 때 더 많은 compute를 쓴다" + "dual-level uncertainty로 precision 향상"

이 조합이 FRCG-WM의 C6 (decision-relevant compute gate)를 uncertainty 프레임으로 완전히 커버한다는 주장이 가능.

**2. Option B LR scorer가 없으면 무엇이 붕괴되는가?**

LR scorer 없이는:
- `G_t = F_t ∧ ΔV_t ∧ P_switch ∧ cost-benefit` 구조가 `uncertainty > threshold`로 collapse됨
- ABL-023 (uncertainty instead of falsification) 비교가 무의미 (LR score vs uncertainty score 비교가 불가)
- "high confidence wrong grammar" episode — uncertainty는 낮지만 F_t는 높은 episode — 를 생성/보여줄 수 없음

**3. 필요한 방어 실험**

- High-confidence wrong grammar dataset 구성: agent가 confident하게 wrong grammar를 쓰는 episode
- 이 dataset에서 CATTS/WebUncertainty gate vs FRCG-WM G_t 비교
- compute-matched experiment: 같은 compute budget에서 LR gate vs entropy gate 비교 (MET-COMP-003/004)
- ABL-023 (uncertainty instead of falsification) 결과와 LR full model 결과 비교

---

### §3.3 WAC (THREAT-05) + CUWM (THREAT-06) + WebWorld (THREAT-04)

**1. 이 조합이 FRCG-WM을 어떻게 흡수할 수 있는가?**

WAC (action correction + consequence simulation) + CUWM (frozen LLM + WM test-time search) + WebWorld (generic WM) 조합:
- "FRCG-WM = WebWorld의 WM + WAC의 correction + CUWM의 frozen search"라는 주장

C4 (rollout) → CUWM/WebWorld, C5 (rewrite) → WAC, C3 (falsification) → WAC consequence check로 분해 가능하다는 framing.

**2. Option B LR scorer가 없으면 무엇이 붕괴되는가?**

LR scorer 없이는:
- no-control-grammar ablation (ABL-002)이 이 3중 조합과 FRCG-WM 모두에서 동일한 degradation을 보일 경우, distinction이 불가능
- BASE-026/027/028이 없으면 이 조합을 baseline으로 비교 자체가 불가

**3. 필요한 방어 실험**

- BASE-026 (WAC-style) + BASE-027 (CUWM-style) + BASE-028 (WebWorld-style) 개별 구현
- ABL-002 (no-control-grammar)가 FRCG-WM full을 WAC/CUWM/WebWorld 수준으로 끌어내리는지 확인
- grammar-conditioned rollout이 grammar-agnostic rollout보다 fidelity 높음을 MET-WM-001로 보여야 함
- 핵심: C3/C4/C5가 각각 WAC/CUWM/WebWorld로 환원되지 않는다는 실험이 모두 독립적으로 필요

---

## Section 4. Claim Impact Matrix

C1~C6 각각에 대해 위협 분석 요약.

| Claim | Main Threats | Option B Defense | Still Missing | Run Needed |
|---|---|---|---|---|
| **C1** (wrong-grammar persistence) | VLAA-GUI (THREAT-02), StressWeb (THREAT-08) | LR scorer + h_exec trace → VLAA-GUI heuristic과 P/R 비교 가능 | h_exec trace (selected_hypothesis_id), MET-PERSIST-001 실계산, MET-BELIEF-001 | Phase 8 (h_exec trace) + Phase 11 (PERSIST metric) |
| **C2** (regime/grammar separation) | Generic Anomaly Detection (THREAT-09), THREAT-13 | b_t factorization + crossed split → Locatello impossibility 완화 | ABL-001 (no_regime), MET-LATENT-001 (latent probe), crossed split episodes | Phase 10 (ABL-001) + Phase 11 (latent probe) |
| **C3** (falsification mechanism) | VeriGUI (THREAT-07), THREAT-09, THREAT-11 | F_t (LR score) ≠ binary verification → VeriGUI distinction 가능 | LR scorer 구현, ABL-022 (no falsification score gate), BASE-006 | Phase 8 (LR scorer) + Phase 10 (ABL-022) + Phase 11 |
| **C4** (alternative grammar rollout) | WebWorld (THREAT-04), CUWM (THREAT-06), THREAT-12, THREAT-13 | grammar-conditioned rollout vs grammar-agnostic | MET-WM-001, MET-ALT-001, BASE-027/028, ABL-036 | Phase 10 (baselines) + Phase 11 (metrics) |
| **C5** (grammar-conditioned rewrite) | WAC (THREAT-05), THREAT-11 | Rewrite(intent, base, h*) — grammar conditioning이 핵심 | ABL-017 (no_L_intent_action_mapping), MET-REWRITE-001, BASE-026 | Phase 10 (ABL-017) + Phase 11 (rewrite metric) |
| **C6** (decision-relevant compute gate) | CATTS (THREAT-01), WebUncertainty (THREAT-03), THREAT-10 | G_t 4-way conjunction ≠ uncertainty gate. High-confidence wrong grammar episode로 구분 | BASE-015, ABL-020, MET-COMP-003, CATTS-equivalent baseline | Phase 10 (BASE-015, ABL-020) + Phase 11 |

---

## Section 5. Required Updates Later (paper_context_ref 미수정, 기록만)

Run 1에서는 아래 수정을 실행하지 않는다. 기록만 한다.

### `01_RELATED_WORK_THREAT_MAP.md` 추가/수정 항목

- CATTS (2602.12276): C6 위협으로 추가. THREAT-01 내용 반영
- VLAA-GUI (2604.21375): C1/C3 위협으로 추가. THREAT-02 내용 반영
- WebUncertainty (2604.17821): C6 위협으로 추가. THREAT-03 내용 반영
- StressWeb (2604.16385): P-013 CONFIRMED → 기존 항목 업데이트
- POPPER (2502.09858): 2-source 확인 후 추가 결정 (현재 UNKNOWN_NEEDS_MORE_SEARCH)

### `10_EVALUATION_BASELINE_ABLATION.md` 추가 baseline/ablation

- BASE-uncertainty-entropy-gate (CATTS-equivalent)
- BASE-loop-heuristic (VLAA-GUI-equivalent)
- BASE-026/027/028: 이미 §7 등재 필요 (현재 미구현)

### `02_PROBLEM_NOVELTY_FALSIFICATION.md` 반영 distinction

- VLAA-GUI와의 distinction 명시: heuristic rule-based vs posterior-based falsification
- CATTS와의 distinction 명시: uncertainty gate vs grammar-conditioned LR gate
- "wrong-grammar persistence"가 "failure loop"과 다른 이유 추가 명시

### `FINAL_RESEARCH_BLUEPRINT.md` 약화/강화 claim 후보

- 약화 후보: C6 novelty claim — CATTS + WebUncertainty로 "compute gating" 자체는 선점됨. "grammar-conditioned gating"으로 좁혀야 함
- 강화 후보: C3 LR distinction — VeriGUI (binary) vs FRCG-WM (LR posterior) 구분이 Option B로 명확해짐
- C1 표현: "wrong-grammar persistence" → "persistent wrong control-grammar hypothesis (≠ failure loop, ≠ mode switch trigger)"로 명확화 권고

---

## Section 6. Run 1 Verdict

**`OPTION_B_NECESSARY`**

근거:

1. **C3 defense 불가**: LR scorer 없이는 VeriGUI (THREAT-07) + VLAA-GUI (THREAT-02) 복합 공격에서 "더 복잡한 verifier" 이상의 distinction을 실험적으로 보여줄 수 없음

2. **C6 defense 불가**: LR scorer 없이는 ABL-023 (uncertainty instead of falsification) 비교가 무의미. CATTS (THREAT-01) + WebUncertainty (THREAT-03) 복합 공격에서 G_t ≠ uncertainty gate를 실험적으로 증명할 수 없음

3. **4개 surviving novelty 항목 모두 LR 의존**:
   - (a) wrong-grammar persistence as measurable failure mode → h_exec trace 필요 → LR scorer와 동반
   - (b) LR falsification ≠ binary verification → LR scorer 없이는 "≠"를 보여줄 수 없음
   - (c) grammar-conditioned alternative hypothesis rollout → rollout conditioning이 grammar hypothesis에 의존
   - (d) grammar-conditioned intent-to-action rewrite → Rewrite(intent, base, h*)에서 h*가 LR기반 posterior에서 선택됨

4. **Option A (BCE reframe)는 불충분**: BCE-trained score가 true LR의 sufficient statistic인지 UNKNOWN 상태에서 narrative만 바꾸면 math_critic C3 RISK HIGH가 해소되지 않음

**주의**: 이 verdict는 C1~C6 ALIVE/DEAD 판정이 아니다. Run 1 threat audit에서 Option B의 novelty defense 필요성을 확인하는 verdict다.

---

*생성일: 2026-05-16 / Run 1 / Phase 1 산출물*  
*근거: `docs/orchestration/lr_alignment/00_OPTION_B_PHASE_ROADMAP.md` Section 4 Phase 1, Section 5 Run 1*  
*수정 금지: `paper_context_ref/01_RELATED_WORK_THREAT_MAP.md` (사용자 승인 + Phase 4 이후)*
