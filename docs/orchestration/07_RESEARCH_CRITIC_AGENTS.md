# 07_RESEARCH_CRITIC_AGENTS.md

Research Critic Agent 설계 명세  
작성일: 2026-05-15  
작성자: Main Claude (Phase 2)  
근거: `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md`, `paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md`, `paper_context_ref/01_RELATED_WORK_THREAT_MAP.md`

**주의**: 본 문서는 설계 명세이다. 실제 `.claude/agents/` 파일 생성은 Phase 3+ human approval 후.

---

## Agent Schema 공통 형식

각 agent는 아래 schema를 따른다.

```yaml
purpose: <agent 목적>
when_to_call: <fixed trigger T1~T6 매핑 + discretionary>
required_inputs: <필요한 입력 목록>
forbidden_actions: <절대 금지 행동>
allowed_tools_proposal: <허용 제안 tools (실제 권한은 Phase 3)>
report_schema: <report에 포함해야 할 필드>
output_path: <docs/orchestration/agent_reports/YYYY-MM/<agent>_*.md>
pass_fail_criteria: <PASS 판정 기준>
escalation_condition: <Main Claude에게 escalation해야 할 조건>
how_main_claude_should_use_output: <Main Claude가 이 output을 어떻게 활용하는가>
```

---

## 1. mathematical-validity-critic

```yaml
purpose: >
  수학적 정의/가정/loss/identifiability/falsification 조건의 논리적 일관성을 검증한다.
  특히 falsification mechanism이 단순 anomaly detection과 구분되는 조건을 명확히 한다.

when_to_call:
  - T1 (핵심 claim 변경 전) — 필수
  - T2 (실험설계 변경 전) — 권장
  - Discretionary: loss/objective 정의 변경 시

required_inputs:
  - paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
  - paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md
  - paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
  - 검토 대상 claim 텍스트 또는 수식

forbidden_actions:
  - 코드 직접 편집
  - git 조작
  - settings/hooks/agents 수정
  - Codex task 직접 생성

allowed_tools_proposal:
  - Read (paper_context_ref/, src/, docs/)
  - Grep (수식 패턴, loss 함수명)
  - Glob (관련 파일 탐색)

report_schema:
  claim_under_review: <검토된 claim>
  mathematical_definitions_checked:
    - definition: <수식/정의>
      status: <VALID | INVALID | UNKNOWN>
      note: <근거>
  assumptions_verified:
    - assumption: <가정>
      holds: <YES | NO | CONDITIONAL>
  identifiability:
    status: <IDENTIFIABLE | NOT_IDENTIFIABLE | UNKNOWN>
    argument: <근거>
  falsification_condition:
    distinguishable_from_anomaly_detection: <YES | NO | UNCERTAIN>
    argument: <근거>
  mathematical_risks:
    - risk: <위험>
      severity: <HIGH | MED | LOW>
      resolution: <해결책>
      verification: <검증법>
  verdict: <PASS | FAIL | NEEDS_REVISION>

output_path: docs/orchestration/agent_reports/YYYY-MM/mathematical-validity-critic_<topic>_<id>.md

pass_fail_criteria: >
  모든 핵심 수식이 VALID, identifiability 확보, falsification이 anomaly detection과 구분 가능,
  UNKNOWN 항목은 UNKNOWN으로 명시 (숨김 금지)

escalation_condition: >
  identifiability UNKNOWN + 논문 submission 임박 시,
  falsification 조건이 verifier-only baseline과 구분 불가 시

how_main_claude_should_use_output: >
  FAIL/NEEDS_REVISION 항목을 paper_context_ref/ 또는 src/ 수정 Codex task로 변환.
  UNKNOWN은 DECISIONS_REQUIRED에 기록.
```

---

## 2. experiment-design-expander

```yaml
purpose: >
  ablation/baseline/OOD split/failure mode 설계를 확장하여 CRITICAL ablation 14개와
  direct threat baseline 3개(BASE-026/027/028)가 누락되지 않도록 감시한다.

when_to_call:
  - T2 (실험설계 변경 전) — 필수
  - T1 (claim 변경 전) — 권장
  - Discretionary: eval config 수정 시

required_inputs:
  - paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md (§8 CRITICAL 14개 + §7 BASE-001~028)
  - paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md
  - 현재 실험 설정 파일 (configs/)

forbidden_actions:
  - 코드 직접 편집
  - git 조작
  - settings/hooks/agents 수정

allowed_tools_proposal:
  - Read (paper_context_ref/, configs/, src/)
  - Grep (baseline/ablation 구현 현황)
  - Glob

report_schema:
  current_experiment_design_summary: <현재 실험 설계 요약>
  critical_ablations_14:
    - ablation: <이름>
      status: <IMPLEMENTED | MISSING | PLANNED>
      note: <메모>
  direct_threat_baselines_3:
    - baseline: <BASE-026 WAC-style | BASE-027 CUWM-style | BASE-028 WebWorld-style>
      status: <IMPLEMENTED | MISSING | PLANNED>
  missing_items:
    - item: <누락 항목>
      priority: <CRITICAL | HIGH | MED>
      impact_on_claim: <어떤 claim이 영향받는가>
  expansion_proposals:
    - proposal: <추가 제안>
      rationale: <이유>
      effort_estimate: <낮음 | 중간 | 높음>
  verdict: <COMPLETE | INCOMPLETE_CRITICAL | INCOMPLETE_MED>

output_path: docs/orchestration/agent_reports/YYYY-MM/experiment-design-expander_<topic>_<id>.md

pass_fail_criteria: >
  CRITICAL ablation 14개 모두 IMPLEMENTED 또는 PLANNED (누락 금지),
  direct threat baseline 3개 IMPLEMENTED 또는 PLANNED

escalation_condition: >
  CRITICAL ablation이 실험 설계에서 제거 또는 비활성화될 위험 감지 시

how_main_claude_should_use_output: >
  MISSING CRITICAL 항목을 즉시 Codex task로 변환.
  INCOMPLETE_CRITICAL 판정 시 Phase gate FAIL 권고.
```

---

## 3. novelty-threat-scout

```yaml
purpose: >
  WebWorld, CUWM, WAC, VeriGUI 등 direct threat 논문과의 novelty 구분을 검증하고,
  2025/2026년 신규 논문 위협을 탐색한다. generic GUI world model 주장으로 흐르지 않도록 감시.

when_to_call:
  - T1 (claim 변경 전) — 필수
  - T5 (논문 섹션 수정 전) — 권장
  - T6 (novelty-risk 감지 시) — 필수
  - Discretionary: related work 작성 시

required_inputs:
  - paper_context_ref/01_RELATED_WORK_THREAT_MAP.md
  - paper_context_ref/02_PROBLEM_NOVELTY_FALSIFICATION.md
  - paper_context_ref/00_MASTER_REFERENCE.md (REF-CORE-020 등)

forbidden_actions:
  - 코드 직접 편집
  - git 조작
  - settings/hooks/agents 수정

allowed_tools_proposal:
  - Read (paper_context_ref/)
  - WebFetch (arXiv, Semantic Scholar — 실제 권한은 Phase 3)
  - WebSearch (신규 논문 탐색)
  - Grep, Glob

report_schema:
  novelty_core_claim: <FRCG-WM의 핵심 novelty 요약>
  direct_threats:
    - paper: <논문명>
      threat_type: <OVERLAP | PARTIAL_OVERLAP | ADDRESSED>
      distinguishing_factor: <구분 요소>
      defense_strength: <STRONG | MODERATE | WEAK>
  new_2025_2026_threats:
    - paper: <논문명>
      url: <arXiv URL>
      threat_level: <HIGH | MED | LOW>
      notes: <설명>
  generic_gui_drift_check:
    at_risk: <YES | NO>
    evidence: <근거>
  recommendations:
    - action: <권고 행동>
      target: <paper section 또는 claim>
      resolution: <해결책>
      verification: <검증법>
  verdict: <NOVELTY_SECURE | NOVELTY_AT_RISK | NOVELTY_COMPROMISED>

output_path: docs/orchestration/agent_reports/YYYY-MM/novelty-threat-scout_<topic>_<id>.md

pass_fail_criteria: >
  NOVELTY_SECURE, 모든 direct threat ADDRESSED 또는 PARTIAL_OVERLAP+강력한 구분,
  generic GUI world model drift 없음

escalation_condition: >
  NOVELTY_COMPROMISED 판정 시, 새 2025/2026 논문이 FRCG-WM 핵심 기여와 HIGH 중복 시

how_main_claude_should_use_output: >
  NOVELTY_AT_RISK 이상 시 논문 related work / claim 수정 검토.
  new threat 발견 시 paper_context_ref/01_RELATED_WORK_THREAT_MAP.md 갱신 Codex task 생성.
```

---

## 4. feasibility-and-cost-auditor

```yaml
purpose: >
  GPU 예산, 학습 시간, 데이터 규모, 구현 난이도를 검증하여
  현실적으로 실행 가능한 실험인지 확인한다.

when_to_call:
  - T2 (실험설계 변경 전) — 필수
  - Discretionary: 새 Phase 시작 전

required_inputs:
  - paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md
  - paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md
  - 현재 실험 설정 파일

forbidden_actions:
  - 코드 직접 편집
  - git 조작

allowed_tools_proposal:
  - Read (paper_context_ref/, configs/)
  - Grep, Glob

report_schema:
  compute_estimate:
    gpu_hours: <예상 GPU 시간>
    model_size: <파라미터 수>
    dataset_size: <샘플 수>
  feasibility_verdict: <FEASIBLE | BORDERLINE | NOT_FEASIBLE>
  bottlenecks:
    - bottleneck: <병목>
      severity: <HIGH | MED | LOW>
      mitigation: <완화책>
      verification: <검증법>
  phase_alignment: <현재 required execution order에 맞는가 YES | NO>

output_path: docs/orchestration/agent_reports/YYYY-MM/feasibility-and-cost-auditor_<topic>_<id>.md

pass_fail_criteria: >
  FEASIBLE 판정, 모든 HIGH bottleneck에 mitigation 존재, phase order 준수

escalation_condition: >
  NOT_FEASIBLE 판정 또는 phase order 위반 감지 시

how_main_claude_should_use_output: >
  NOT_FEASIBLE 시 실험 규모 축소 Codex task 생성. BORDERLINE 시 DECISIONS_REQUIRED로 사용자 판단 요청.
```

---

## 5. reviewer-2-attack-agent

```yaml
purpose: >
  가장 공격적인 reviewer 관점에서 논문의 약점을 찾는다.
  반드시 해결책과 검증법을 동반한다.

when_to_call:
  - T1, T5 — 필수
  - T6 (reviewer-risk 감지) — 필수
  - Discretionary: 논문 draft 준비 시

required_inputs:
  - paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md (FC-01~FC-05, Reviewer Defense 13종)
  - paper_context_ref/00_MASTER_REFERENCE.md
  - 검토 대상 논문 섹션

forbidden_actions:
  - 코드 직접 편집
  - git 조작
  - settings 수정

allowed_tools_proposal:
  - Read (paper_context_ref/, docs/)
  - Grep, Glob

report_schema:
  attack_claims:
    - attack: <공격 포인트 (Level 3 강도)>
      target: <논문 섹션 또는 claim>
      severity: <FATAL | MAJOR | MINOR>
      defense: <방어 전략>
      evidence_required: <어떤 실험/근거로 방어 가능>
      verification: <검증법>
  unresolvable_weaknesses:
    - weakness: <해결 불가 약점 (있다면)>
      impact: <논문 acceptability에 미치는 영향>
      mitigation: <완화 가능성>
  overall_rejection_risk: <HIGH | MED | LOW>
  verdict: <ATTACK_MANAGEABLE | HIGH_RISK | FATAL_FLAW>

output_path: docs/orchestration/agent_reports/YYYY-MM/reviewer-2-attack-agent_<topic>_<id>.md

pass_fail_criteria: >
  FATAL_FLAW 없음, 모든 MAJOR attack에 defense 존재, 해결책 없는 비판 없음

escalation_condition: >
  FATAL_FLAW 판정 시, MAJOR attack의 50%+ 방어 불가 시

how_main_claude_should_use_output: >
  FATAL_FLAW 시 연구 방향 재검토 사용자 보고. MAJOR defense 부족 시 추가 실험 Codex task 생성.
```

---

## 6. area-chair-synthesis-agent

```yaml
purpose: >
  여러 reviewer 의견 충돌을 정리하고 최종 acceptability를 판단한다.
  Deep mode에서 다른 agent들의 report를 종합한다.

when_to_call:
  - T4 (결과 해석 전) — deep mode에서 필수
  - T1, T5 — deep mode에서 선택
  - Discretionary: reviewer #2 공격이 심각할 때

required_inputs:
  - 동일 세션에서 생성된 다른 agent report들
  - paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md

forbidden_actions:
  - 코드 직접 편집
  - git 조작

allowed_tools_proposal:
  - Read (docs/orchestration/agent_reports/, paper_context_ref/)
  - Grep, Glob

report_schema:
  conflicting_opinions:
    - issue: <충돌하는 주제>
      agent_A: <agent A 의견>
      agent_B: <agent B 의견>
      resolution: <AC 판단>
  final_acceptability: <ACCEPT | MAJOR_REVISION | REJECT>
  top_3_priorities:
    - priority: <최우선 해결 항목>
      resolution: <해결책>
      verification: <검증법>
  overall_verdict_rationale: <판정 근거>

output_path: docs/orchestration/agent_reports/YYYY-MM/area-chair-synthesis-agent_<topic>_<id>.md

pass_fail_criteria: >
  ACCEPT 또는 MAJOR_REVISION 판정, 모든 충돌 의견에 resolution 존재

escalation_condition: REJECT 판정 시

how_main_claude_should_use_output: >
  top_3_priorities를 Codex task 또는 DECISIONS_REQUIRED로 변환.
  REJECT 시 사용자 즉시 보고.
```

---

## 7. claim-metric-alignment-auditor

```yaml
purpose: >
  claim → metric → baseline → ablation → failure 1:1 정렬을 검증한다.
  각 claim에 대응하는 실험이 빠짐없이 존재하는지 확인한다.

when_to_call:
  - T1 (claim 변경 전) — 필수
  - T4 (결과 해석 전) — 필수
  - Discretionary: eval config 변경 시

required_inputs:
  - paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
  - paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md (FC-01~FC-05)
  - 현재 claim 목록과 eval config

forbidden_actions:
  - 코드 직접 편집
  - git 조작

allowed_tools_proposal:
  - Read (paper_context_ref/, configs/, docs/)
  - Grep (claim/metric/baseline 구현 현황)
  - Glob

report_schema:
  alignment_table:
    - claim: <claim 텍스트>
      metric: <대응 metric>
      baseline: <대응 baseline (BASE-XXX)>
      ablation: <대응 ablation (ABL-XXX)>
      failure_mode: <대응 FAIL-XXX>
      status: <ALIGNED | MISALIGNED | MISSING_METRIC | MISSING_BASELINE | MISSING_ABLATION>
  misaligned_items:
    - claim: <claim>
      missing: <무엇이 없는가>
      resolution: <해결책>
      verification: <검증법>
  verdict: <FULLY_ALIGNED | PARTIALLY_ALIGNED | MISALIGNED>

output_path: docs/orchestration/agent_reports/YYYY-MM/claim-metric-alignment-auditor_<topic>_<id>.md

pass_fail_criteria: >
  FULLY_ALIGNED 또는 PARTIALLY_ALIGNED (MISALIGNED 항목에 해결책 존재)

escalation_condition: >
  핵심 claim에 metric/baseline/ablation 중 하나라도 완전 누락 시

how_main_claude_should_use_output: >
  MISALIGNED 항목을 즉시 Codex task(실험 추가)로 변환.
```

---

## 8. failure-interpretation-critic

```yaml
purpose: >
  실험 실패 시 claim 약화/수정/보존 여부를 검토한다.
  FAIL-001~024 (paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §14) 기반.

when_to_call:
  - T4 (결과 해석 전) — 필수
  - Discretionary: eval run 완료 후

required_inputs:
  - paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §14 (FAIL-001~024)
  - 실험 결과 artifact (outputs/runs/ 또는 eval report)

forbidden_actions:
  - 코드 직접 편집
  - git 조작

allowed_tools_proposal:
  - Read (paper_context_ref/, outputs/)
  - Grep, Glob

report_schema:
  experiment_result_summary: <실험 결과 요약>
  failure_interpretation:
    - fail_id: <FAIL-XXX>
      triggered: <YES | NO>
      interpretation: <실패 원인 해석>
      claim_impact: <WEAKENS | REQUIRES_MODIFICATION | PRESERVES | INVALIDATES>
      recommended_action: <해결책>
      verification: <검증법>
  overall_claim_status: <PRESERVED | MODIFIED | WEAKENED | INVALIDATED>
  negative_result_disclosure: <숨겨진 negative result 없음을 확인 YES | NO>

output_path: docs/orchestration/agent_reports/YYYY-MM/failure-interpretation-critic_<topic>_<id>.md

pass_fail_criteria: >
  모든 triggered FAIL-XXX에 interpretation 존재,
  negative result 숨김 없음, INVALIDATED 시 즉시 escalation

escalation_condition: >
  overall_claim_status INVALIDATED 시, negative result 숨김 의심 시

how_main_claude_should_use_output: >
  WEAKENED/MODIFIED claim에 대해 논문 수정 또는 추가 실험 Codex task 생성.
  INVALIDATED 시 사용자 즉시 보고.
```

---

## 9. related-work-mcp-scout

```yaml
purpose: >
  arXiv, Semantic Scholar 등 외부 탐색을 통해 direct threat 논문과
  2025/2026 신규 관련 논문을 발굴한다.
  실제 MCP 설치 없이 허용된 tools로 탐색한다.

when_to_call:
  - T5 (논문 섹션 수정 전) — 권장
  - T6 (novelty-risk 감지) — 권장
  - Discretionary: 새 Phase 시작 전

required_inputs:
  - paper_context_ref/01_RELATED_WORK_THREAT_MAP.md
  - 검색 키워드 (Main Claude 제공)

forbidden_actions:
  - 코드 직접 편집
  - git 조작
  - MCP 설치 (새 MCP는 frcgw-plugin-audit 후 human approval 필수)

allowed_tools_proposal:
  - WebFetch (arXiv, Semantic Scholar, ACL Anthology)
  - WebSearch (신규 논문 탐색)
  - Read (paper_context_ref/)

report_schema:
  search_queries: <사용된 검색 쿼리>
  new_papers_found:
    - title: <논문 제목>
      url: <arXiv/DOI URL>
      year: <출판년도>
      relevance: <HIGH | MED | LOW>
      threat_type: <DIRECT | INDIRECT | NONE>
      notes: <핵심 내용 요약>
  citation_cross_check:
    - paper: <논문>
      sources_verified: <출처 2개 이상>
  threat_update_required: <paper_context_ref/01 갱신 필요 YES | NO>
  recommendations:
    - action: <권고>
      resolution: <해결책>
      verification: <검증법>

output_path: docs/orchestration/agent_reports/YYYY-MM/related-work-mcp-scout_<topic>_<id>.md

pass_fail_criteria: >
  관련 키워드 탐색 완료, citation 2개 이상 교차검증, HIGH threat에 대응 방안 존재

escalation_condition: >
  2025/2026 논문이 FRCG-WM 핵심 기여와 HIGH 중복 시

how_main_claude_should_use_output: >
  new HIGH threat 발견 시 novelty-threat-scout 추가 호출.
  threat_update_required YES 시 paper_context_ref/ 갱신 사용자 승인 요청.
```

---

## 10. implementation-risk-critic

```yaml
purpose: >
  Codex 구현 가능성, 테스트 커버리지, scope creep 위험을 검토한다.
  주로 Codex merge 전 (T3) 호출.

when_to_call:
  - T3 (Codex merge 전) — 필수
  - Discretionary: 복잡한 TASK 파일 검토 시

required_inputs:
  - 검토 대상 Codex TASK 파일
  - Codex RESULT.md
  - git diff (staged)

forbidden_actions:
  - 코드 직접 편집
  - git 조작

allowed_tools_proposal:
  - Read (docs/orchestration/, .agent_tasks/, src/, tests/)
  - Grep (scope violation 패턴 탐색)
  - Glob

report_schema:
  task_id: <TASK_XXXX>
  scope_compliance:
    allowed_files_only: <YES | NO>
    forbidden_paths_clean: <YES | NO>
    violations: <위반 목록>
  test_coverage:
    required_tests_passed: <YES | NO>
    missing_tests: <누락된 테스트>
  scope_creep_risk:
    - area: <scope creep 위험 영역>
      severity: <HIGH | MED | LOW>
      recommendation: <권고>
      verification: <검증법>
  gatekeeper_5_conditions:
    verify_exit_0: <YES | NO>
    diff_review_clean: <YES | NO>
    forbidden_paths_clean: <YES | NO>
    result_md_exists: <YES | NO>
    required_tests_passed: <YES | NO>
  verdict: <ACCEPT_READY | NEEDS_FIX | REJECT>

output_path: docs/orchestration/agent_reports/YYYY-MM/implementation-risk-critic_<topic>_<id>.md

pass_fail_criteria: >
  Gatekeeper 5조건 모두 YES, ACCEPT_READY 판정

escalation_condition: >
  forbidden_paths 위반 감지, REJECT 판정 시

how_main_claude_should_use_output: >
  REJECT 시 rejection_id 생성 후 Codex 재작업 지시.
  NEEDS_FIX 시 구체 수정 항목 Codex에 전달.
  ACCEPT_READY 시 codex_orchestration_rules.md Gatekeeper 5조건 최종 확인 후 accept.
```
