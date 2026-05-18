# 24_step5_direct_threat_baseline_report.md — BASE-026/027/028 Reviewer-Response

작성일: 2026-05-18
단계: STEP 5 (T8)
branch: `memory-redesign-2026-05-16`

---

## §1. Purpose

이 문서는 BASE-026 (WAC), BASE-027 (CUWM), BASE-028 (WebWorld) 세 개의 direct-threat baseline
현재 구현 상태와 한계를 명시하고, 논문 reviewer 공격에 대한 방어 wording을 기록한다.

**금지 표현** (이 문서 어디에도 사용 불가):
- "direct-threat baselines defeated"
- "outperforms WAC/CUWM/WebWorld"
- "FRCG-LR beats direct threats"
- "faithful implementation of WAC/CUWM/WebWorld"

**허용 표현**:
- "preliminary comparison with heuristic approximations of direct-threat baselines"
- "STEP 6 enhancement required for faithful comparison"
- "heuristic approximation, not algorithmic faithful re-implementation"

---

## §2. BASE-026 — WAC-Style Consequence Correction (WAC)

### §2.1 현재 구현 명시

`WACStyleConsequenceCorrectionAgent` (baselines.py)는 WAC 논문의 **heuristic approximation**이며
faithful re-implementation이 아니다.

### §2.2 WAC Similarity Matrix

| 항목 | 유사점 | 미흡점 |
|---|---|---|
| 목적 | consequence-based correction loop | WAC §3 Algorithm 1: learned consequence model missing |
| 입력 | public consequence feedback | Grammar posterior 미사용 |
| 루프 | correction iteration | Learned action-effect log 미사용 |
| 교정 | heuristic best candidate re-selection | WAC §3 §5 "consequence score" 계산 로직 누락 |
| 검색 | 없음 (static candidate) | WAC §4 candidate search tree 없음 |

### §2.3 Reviewer Attack Vectors

**Attack**: "WAC already solves this — your baseline isn't faithful."
**Defense**: "BASE-026 is a heuristic approximation of WAC's consequence correction loop.
Faithful algorithmic re-implementation of WAC §3 Algorithm 1 (with learned consequence model
and grammar posterior) is STEP 6 scope. Current comparison is preliminary — results should not
be interpreted as FRCG-LR defeating WAC."

**Attack**: "Why not run the actual WAC checkpoint?"
**Defense**: "WAC's public codebase targets different state representations. We implement
a heuristic proxy that captures WAC's core insight (consequence-based correction) while
maintaining compatibility with our grammar-grounded evaluation protocol. Full WAC integration
is STEP 6 priority."

---

## §3. BASE-027 — CUWM-Style Candidate Simulation (CUWM)

### §3.1 현재 구현 명시

`CUWMStyleCandidateSimulationAgent` (baselines.py)는 CUWM 논문의 **heuristic approximation**이며
faithful re-implementation이 아니다.

### §3.2 CUWM Similarity Matrix

| 항목 | 유사점 | 미흡점 |
|---|---|---|
| 목적 | candidate simulation + frozen base | CUWM §4 latent state simulation missing |
| 구조 | frozen-base wrapping | Grammar posterior 미사용 |
| 시뮬레이션 | heuristic candidate comparison | CUWM §4 Algorithm 1: learned world model missing |
| 선택 | best candidate by heuristic | Counterfactual outcome prediction 없음 |

### §3.3 Reviewer Attack Vectors

**Attack**: "CUWM uses a proper world model — your baseline doesn't."
**Defense**: "BASE-027 is a heuristic approximation of CUWM's candidate simulation principle.
The frozen base model wrapping is structurally similar, but CUWM's learned latent state model
(§4 Algorithm 1) is not re-implemented. Faithful comparison requires STEP 6 integration
with grammar posterior — labeled as 'preliminary comparison with heuristic approximation.'"

---

## §4. BASE-028 — WebWorld-Style Search (WebWorld)

### §4.1 현재 구현 명시

`WebWorldStyleSearchAgent` (baselines.py)는 WebWorld 논문의 **heuristic approximation**이며
faithful re-implementation이 아니다.

### §4.2 WebWorld Similarity Matrix

| 항목 | 유사점 | 미흡점 |
|---|---|---|
| 목적 | next-state heuristic + action search | WebWorld §3 learned next-state model missing |
| 탐색 | heuristic candidate selection | Search tree depth 제한 (1-step lookahead only) |
| 상태 | public observation | Grammar posterior 미사용 |
| 보상 | heuristic progress proxy | WebWorld §3 reward model 없음 |

### §4.3 Reviewer Attack Vectors

**Attack**: "WebWorld has a proper tree search — your 1-step lookahead is trivial."
**Defense**: "BASE-028 captures WebWorld's core insight (next-state search) as a heuristic
approximation. Full tree search with learned reward model and grammar posterior integration
is STEP 6 scope. Results labeled as 'preliminary comparison with heuristic approximations.'"

---

## §5. STEP 6 고도화 우선순위

| 순위 | Baseline | 이유 |
|---|---|---|
| 1st | BASE-026 (WAC) | 가장 직접적 threat; grammar posterior 통합 → 실질 비교 가능 |
| 2nd | BASE-027 (CUWM) | frozen base + posterior 구조가 FRCG-LR과 유사 → 대비 명확 |
| 3rd | BASE-028 (WebWorld) | search tree 확장 필요; 최고 복잡도 |

---

## §6. 현재 결과표 Wording Rules

### §6.1 제목/캡션에 허용 표현

```
"Table X: Preliminary comparison of FRCG-LR vs. heuristic approximations of direct-threat baselines.
BASE-026/027/028 are structural approximations; faithful algorithmic re-implementations are STEP 6 scope."
```

### §6.2 본문 허용 표현

```
"FRCG-LR shows [metric X] in preliminary comparison with heuristic approximations of
WAC (BASE-026), CUWM (BASE-027), and WebWorld (BASE-028). These results are preliminary;
faithful algorithmic re-implementations (STEP 6) are required before drawing conclusions
about FRCG-LR's advantage over direct threats."
```

### §6.3 절대 금지 표현

```
"FRCG-LR outperforms WAC/CUWM/WebWorld"
"direct-threat baselines defeated"
"We beat/surpass WAC"
"our approach is superior to WebWorld/CUWM/WAC"
```

---

## §7. STEP 5 Commit Policy

이 문서(24_step5_direct_threat_baseline_report.md)는 STEP 5 commit에 포함.
알고리즘 충실 재구현 코드 변경은 STEP 5에 포함하지 않음.

---

## §8. Cross-references

- `paper_context_ref/01_RELATED_WORK_THREAT_MAP.md` — WAC/CUWM/WebWorld threat map
- `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7` — BASE-026/027/028 SSoT
- `docs/orchestration/lr_alignment/25_step6_handoff.md` — STEP 6 고도화 계획
