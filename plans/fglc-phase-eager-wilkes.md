# Step 7 — FGLC Repair diagnose.py + candidates.py + ranker.py (Codex 위임 PLAN, 2026-05-23)

> **Status**: PLAN ONLY. ExitPlanMode 승인 후 execute 단계에서 Codex TASK enqueue + 실행 + 검증을 수행.
> **Branch**: memory-redesign-2026-05-16 (main Claude) / codex-work (Codex worktree)
> **Prior commit**: `1649d73` (Step 6 merge — compare/ledger), main HEAD `4165d85` (auto-commit). codex-work HEAD `6ef1795` — ff-merge로 main과 동기화 필요.
> **현재 task**: Step 7 — `src/fglc/repair/diagnose.py` + `src/fglc/repair/candidates.py` + `src/fglc/repair/ranker.py` + 양쪽 테스트 구현을 Codex(gpt-5.5)에 위임

---

## Context — 왜 이 변경인가

`docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` §G Step 7은 closed-loop repair harness의 **결정 직전 단계**를 정의한다:

```
metrics → diagnose() → [cause-id, ...]
       → candidates_for(causes, phase) → [RepairCandidate, ...]
       → rank(candidates) → [RankedCandidate, ...]
       → orchestrator picks rank=1 → Step 8 patch + rerun
```

- §D.2 (observation → cause list 매핑 7행) 와 §D.3 (cause → cheapest-first candidate 매핑 7행) 가 verbatim 표로 존재.
- Step 6의 `compare_metrics()`가 산출한 deltas/result는 ledger line의 일부 키와 1:1 정합되었듯이, Step 7의 세 모듈 출력은 ledger line의 `diagnosed_cause` (list), `candidate_chosen` (dict), `candidate_rank_score` (float) 와 1:1 정합되어야 한다.
- 세 모듈을 분리 TASK로 발주하면 cause-id ↔ patch dict ↔ score 키 스펙이 어긋날 위험 + 세 번의 6-gatekeeper 라운드 = 3× 오버헤드. round-trip 통합 테스트(diagnose→candidates→ranker)는 한 TASK 안에서만 가능. → **단일 TASK** (사용자 결정).

Codex 위임 트리거(`.claude/rules/codex_orchestration_rules.md` §Codex 호출 트리거):
- (a) 3개 이상 파일 동시 수정 (실제 6 src/test 파일)
- (b) 테스트 작성 + 구현 동반
- (d) repair-loop 데이터/평가 파이프라인 구현

Step 5/6과 동일하게 새 모듈 추가 → **T3 트리거 의무** (`implementation-risk-critic`, compact mode).

---

## A. 모듈 scope 결정 (좁히기)

### A.1 `diagnose.py`가 *제공*하는 것

| 항목 | 형태 |
|---|---|
| `diagnose(metrics: Mapping[str, float], phase: str) -> list[FailureCauseId]` | pure function. SSoT §D.2의 7개 점화 함수를 묶어 cause-id list 반환. |
| `CANONICAL_METRIC_KEYS: frozenset[str]` | 정규 metric 키 목록 (모듈 상수). 11~14개 키 (id_nll, ood_auroc, corrected_nll_gain, attention_entropy, correction_norm_mean, planner_return_gain, val_train_nll_gap, ood_id_nll_diff, beta_mean, ece, stagnant_epochs, log_k, kstep_nll_slope, train_nll). |
| `_fire_*` 점화 함수 7개 | §D.2 7행 1:1 — `_fire_id_nll`, `_fire_ood_auroc`, `_fire_corrected_gain`, `_fire_attention`, `_fire_correction_weak`, `_fire_correction_large`, `_fire_planner`. 각 함수는 `metrics.get(...)` 으로 누락 key silent skip. |
| 결과 순서·dedup | SSoT §D.2 행 순서 유지 + 동일 cause-id 중복 제거. `applicable_phases_for(phase)`로 phase 부적합 cause 필터. |
| Fallback | 모든 점화 함수가 빈 list 반환 + `FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED in applicable_phases_for(phase)` → `[IMPLEMENTATION_BUG_SUSPECTED]` 반환 (사용자 결정 #2). |

### A.2 `diagnose.py`가 **제공하지 않는** 것

| 항목 | 위임 Step |
|---|---|
| metric 수집/측정 | Step 9~10 (train/eval runner) |
| cause → candidate 매핑 | A.3 `candidates.py` |
| ranking | A.5 `ranker.py` |
| ledger write | Step 8 orchestrator |
| `IMPLEMENTATION_BUG_SUSPECTED` blocker report 생성 | Step 8 orchestrator |

### A.3 `candidates.py`가 *제공*하는 것

| 항목 | 형태 |
|---|---|
| `@dataclass(frozen=True) class RepairCandidate` | `id: str`, `cause_id: FailureCauseId`, `patch: Mapping[str, Any]` (inline dict), `cost_minutes: int` (>0), `risk: float` ([0,1]), `expected_signal: float` ([0,1]), `description: str`, `applicable_phases: tuple[str, ...]`. |
| `CANDIDATE_TABLE: dict[FailureCauseId, tuple[RepairCandidate, ...]]` | SSoT §D.3 cheapest-first 7행 × ~4 candidate ≈ 25~30개 hard-code 후보. cost/risk/signal 추정치는 heuristic (docstring에 "calibration in Step 8 orchestrator" 명시). |
| `candidates_for(causes: Sequence[FailureCauseId], phase: str) -> list[RepairCandidate]` | input cause-id list × CANDIDATE_TABLE → candidate list. `applicable_phases` filter 적용 + cause-id 중복 제거. |
| Candidate id 규약 | `<CAUSE_ID>_<short_slug>` (예: `MODEL_UNDERCAPACITY_h_dim_256`). slug regex `[a-z0-9_]{2,40}`. |
| patch 표현 | **Inline dict** (예: `{"hidden_dim": 256}`). `configs/` 디렉터리에 새 파일 생성 금지(FILES_FORBIDDEN). Step 8 orchestrator가 base config에 deep-merge. |
| `IMPLEMENTATION_BUG_SUSPECTED` 처리 | patch=`{"action": "manual_blocker_report"}` sentinel, cost=1, risk=0, signal=0 (cost>0 강제로 ranker 검증 통과). |

### A.4 `candidates.py`가 **제공하지 않는** 것

| 항목 | 위임 Step |
|---|---|
| patch dict의 key를 실제 config schema와 검증 | Step 8 orchestrator (Step 7 테스트는 dict shape만 검사) |
| YAML 파일 로딩 | configs/ FORBIDDEN — Step 8 orchestrator |
| 동적 candidate 생성 (LLM 등) | 명시적 미구현 |

### A.5 `ranker.py`가 *제공*하는 것

| 항목 | 형태 |
|---|---|
| `@dataclass(frozen=True) class RankedCandidate` | `candidate: RepairCandidate`, `rank: int` (1-based), `score: float` ([0,1]). |
| `rank(candidates: Sequence[RepairCandidate]) -> list[RankedCandidate]` | sort key = `(cost_minutes asc, risk asc, -expected_signal, id asc)`. rank=1이 best. score=`(n-rank)/max(1,n-1)` 정규화, n=1일 때 score=1.0. (사용자 결정 #1.) |
| 입력 검증 | `cost_minutes <= 0` → `ValueError`. `risk ∉ [0,1]` → `ValueError`. `expected_signal ∉ [0,1]` → `ValueError`. |
| edge case | empty → empty. n=1 → score=1.0. |

### A.6 결정 사항 확정 (사용자 + Plan agent)

1. **Ranker 공식 = Lexicographic + 정규화** (사용자 결정 1). sort key `(cost asc, risk asc, -signal, id asc)`; score `(n-rank)/max(1,n-1)`.
2. **diagnose 누락 metric = Silent skip + IMPLEMENTATION_BUG_SUSPECTED fallback** (사용자 결정 2). `metrics.get()` 사용. 모든 점화 함수 빈 결과 + IMPLEMENTATION_BUG_SUSPECTED phase 허용 시 fallback.
3. **단일 TASK 묶음** (사용자 결정 3). 6 src/test 파일 + RESULT.md = 7 파일 단일 commit.
4. **Candidate id 규약** = `<CAUSE_ID>_<slug>` (Plan agent 권장).
5. **Patch 표현** = inline dict (Plan agent 권장, configs/ FORBIDDEN 제약).
6. **CANDIDATE_TABLE 25~30개 candidate hard-code** (Plan agent 권장). cost/risk/signal heuristic, docstring 명시.

### A.7 파일 간 의존 그래프

```
diagnose.py    --- imports taxonomy.py (FailureCauseId, applicable_phases_for) → stdlib only otherwise
candidates.py  --- imports taxonomy.py (FailureCauseId) → stdlib only otherwise
ranker.py      --- imports candidates.py (RepairCandidate) → stdlib only otherwise
tests/test_fglc_repair_diagnose.py    --- imports diagnose only
tests/test_fglc_repair_candidates.py  --- imports candidates only
tests/test_fglc_repair_ranker.py      --- imports candidates + ranker (round-trip dataclass usage)
```

**compare.py / ledger.py 직접 import 안 함** — diagnose/candidates/ranker는 ledger line의 일부 키를 채울 뿐, 직접 ledger write는 Step 8 orchestrator 담당. `__init__.py` 갱신 없음 (Step 6과 동일 정책).

### A.8 SSoT 매핑 표 (Codex TASK 명세에 verbatim 포함)

#### §D.2 diagnose 점화 규칙
| observation | cause-id list (SSoT 순서) |
|---|---|
| ID NLL 높음 | MODEL_UNDERCAPACITY, DATA_TOO_SMALL, HORIZON_TOO_SHORT, LOSS_IMBALANCE |
| OOD AUROC 낮음 | SIGMA_CALIBRATION_FAILURE, BETA_GATE_COLLAPSE, OOD_TOO_EASY, DATA_BAD_SPLIT |
| corrected NLL > uncorrected NLL | CORRECTION_TOO_LARGE, ATTENTION_COLLAPSE, LOSS_IMBALANCE |
| attention entropy 과다 (uniform 또는 collapse) | ATTENTION_COLLAPSE |
| correction norm ≈ 0 | CORRECTION_TOO_WEAK, BETA_GATE_COLLAPSE |
| correction norm 과다 (bound hit ratio 높음) | CORRECTION_TOO_LARGE |
| planner return 개선 없음 | PLANNER_BUDGET_TOO_LOW, HORIZON_TOO_LONG, IMPLEMENTATION_BUG_SUSPECTED |

#### §D.3 cause → candidate cheapest-first
| cause group | candidate (cheapest first) |
|---|---|
| ID NLL | `h_dim 128→256` / `episode ×2` / `horizon 8→16` / `weights 재정렬` |
| OOD AUROC | `L_cal 추가` / `β reparam` / `OOD shift 강화` / `split 재생성` |
| corrected NLL | `δ_max 0.25→0.1` / `entmax/sparsemax` / `corrected_loss_weight ↓` / `base WM freeze` |
| attention entropy | `entmax-alpha 1.5` / `top-k mask k=2` / `sparsity penalty` |
| δ ≈ 0 | `δ head init scale ↑` / `corrected loss weight ↑` / `β prior scale 재설정` |
| δ 과다 | `δ_max ↓` / `L_corr_size ↑` / `base WM freeze` |
| planner return | `n_candidate ↑` / `horizon 5→3` / `reward/value head 재학습` / `rollout error 재측정` |

---

## B. TASK 파일 명세 (Codex 입력)

### B.1 TASK 파일 경로

```
.agent_tasks/codex_queue/TASK_2026_05_23_FGLC_REPAIR_DIAGNOSE_CANDIDATES_RANKER.md
```

### B.2 TASK YAML

```yaml
TASK_NAME: fglc_repair_diagnose_candidates_ranker

BACKGROUND: |
  docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.2 (observation → cause-id 매핑)
  + §D.3 (cause → candidate cheapest-first) + Step 5 taxonomy.py + Step 6 ledger schema가
  closed-loop repair harness의 결정 직전 단계를 정의한다.
  이 TASK는 그 명세를 세 개의 Python 모듈로 구현한다:
    diagnose(metrics, phase) → cause-id list
    candidates_for(causes, phase) → RepairCandidate list
    rank(candidates) → RankedCandidate list (rank=1이 best)

GOAL: |
  Create:
    src/fglc/repair/diagnose.py
      - diagnose() pure function
      - CANONICAL_METRIC_KEYS frozenset
      - _fire_* 점화 함수 7개 (§D.2 verbatim)
      - 누락 key silent skip + IMPLEMENTATION_BUG_SUSPECTED fallback
    src/fglc/repair/candidates.py
      - @dataclass(frozen=True) class RepairCandidate
      - CANDIDATE_TABLE (cause-id → tuple[RepairCandidate, ...])
      - candidates_for() function
    src/fglc/repair/ranker.py
      - @dataclass(frozen=True) class RankedCandidate
      - rank() function (lexicographic + normalized score)
    tests/test_fglc_repair_diagnose.py    (>=8 test groups)
    tests/test_fglc_repair_candidates.py  (>=6 test groups)
    tests/test_fglc_repair_ranker.py      (>=6 test groups)

  Touch nothing else. Do not modify src/fglc/repair/__init__.py / taxonomy.py /
  compare.py / ledger.py. Do not write any files under outputs/, data/, configs/, docs/.

FILES_ALLOWED:
  - src/fglc/repair/diagnose.py
  - src/fglc/repair/candidates.py
  - src/fglc/repair/ranker.py
  - tests/test_fglc_repair_diagnose.py
  - tests/test_fglc_repair_candidates.py
  - tests/test_fglc_repair_ranker.py
  - .agent_tasks/codex_done/TASK_2026_05_23_FGLC_REPAIR_DIAGNOSE_CANDIDATES_RANKER_RESULT.md
  - .agent_tasks/codex_done/TASK_2030_fglc_repair_diagnose_candidates_ranker_RESULT.md

FILES_FORBIDDEN:
  - src/fglc/repair/__init__.py
  - src/fglc/repair/taxonomy.py
  - src/fglc/repair/compare.py
  - src/fglc/repair/ledger.py
  - src/fglc/schemas/
  - .claude/
  - CLAUDE.md
  - docs/
  - scripts/
  - configs/
  - outputs/
  - data/
  - "** (all other files not listed in FILES_ALLOWED)"

REQUIRED_IMPLEMENTATION: |
  1. Read docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.2/§D.3 (observation → cause + cause → candidate SSoT).
  2. Read src/fglc/repair/taxonomy.py (FailureCauseId, applicable_phases_for, DETECTION_THRESHOLDS).
  3. Implement src/fglc/repair/diagnose.py:
     - module docstring: "Source: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.2 + src/fglc/repair/taxonomy.py"
     - CANONICAL_METRIC_KEYS: frozenset[str] containing at minimum:
         "id_nll", "ood_auroc", "corrected_nll_gain", "attention_entropy",
         "correction_norm_mean", "planner_return_gain",
         "val_train_nll_gap", "ood_id_nll_diff",
         "beta_mean", "ece", "stagnant_epochs", "log_k",
         "kstep_nll_slope", "train_nll"
     - 7 점화 함수 (private, return list[FailureCauseId]):
         _fire_id_nll(metrics)            # id_nll > 0.5 → §D.2 row 1
         _fire_ood_auroc(metrics)         # ood_auroc 임계값 → §D.2 row 2
         _fire_corrected_gain(metrics)    # corrected_nll_gain > 0 → §D.2 row 3
         _fire_attention(metrics)         # attention_entropy < 0.1 or > 0.95*log_k → §D.2 row 4
         _fire_correction_weak(metrics)   # correction_norm_mean < 0.01 → §D.2 row 5
         _fire_correction_large(metrics)  # correction_norm_mean > threshold → §D.2 row 6
         _fire_planner(metrics)           # planner_return_gain ≤ 0 → §D.2 row 7
       각 함수는 metrics.get()으로 누락 key silent skip.
     - def diagnose(metrics: Mapping[str, float], phase: str) -> list[FailureCauseId]:
         applicable = applicable_phases_for(phase)
         if not applicable:
             raise ValueError(f"invalid phase: {phase!r}")
         causes: list[FailureCauseId] = []
         for fire_fn in [_fire_id_nll, _fire_ood_auroc, _fire_corrected_gain,
                         _fire_attention, _fire_correction_weak,
                         _fire_correction_large, _fire_planner]:
             for cause_id in fire_fn(metrics):
                 if cause_id in applicable and cause_id not in causes:
                     causes.append(cause_id)
         if not causes and FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED in applicable:
             return [FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED]
         return causes
  4. Implement src/fglc/repair/candidates.py:
     - module docstring: "Source: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.3"
     - @dataclass(frozen=True) class RepairCandidate:
         id: str
         cause_id: FailureCauseId
         patch: Mapping[str, Any]
         cost_minutes: int
         risk: float
         expected_signal: float
         description: str
         applicable_phases: tuple[str, ...]
     - CANDIDATE_TABLE: dict[FailureCauseId, tuple[RepairCandidate, ...]]
       §D.3 7행 × ~4 candidate ≈ 25~30개 hard-code.
       Candidate id 규약: f"{cause_id.value}_{slug}" where slug ∈ [a-z0-9_]{2,40}.
       예: RepairCandidate(id="MODEL_UNDERCAPACITY_h_dim_256",
                          cause_id=FailureCauseId.MODEL_UNDERCAPACITY,
                          patch={"hidden_dim": 256},
                          cost_minutes=15, risk=0.1, expected_signal=0.6,
                          description="Increase hidden_dim 128→256.",
                          applicable_phases=("R3",))
       IMPLEMENTATION_BUG_SUSPECTED candidate:
         RepairCandidate(id="IMPLEMENTATION_BUG_SUSPECTED_manual_blocker",
                         cause_id=FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED,
                         patch={"action": "manual_blocker_report"},
                         cost_minutes=1, risk=0.0, expected_signal=0.0,
                         description="Escalate to user; no automated patch.",
                         applicable_phases=("R3","R4","R5","R6","R7"))
     - def candidates_for(causes: Sequence[FailureCauseId], phase: str) -> list[RepairCandidate]:
         result, seen = [], set()
         for cause_id in causes:
             if cause_id in seen:
                 continue
             seen.add(cause_id)
             for c in CANDIDATE_TABLE.get(cause_id, ()):
                 if phase in c.applicable_phases:
                     result.append(c)
         return result
     - 모든 patch dict은 비어있으면 안 됨 (단 IMPLEMENTATION_BUG_SUSPECTED는 sentinel 허용).
  5. Implement src/fglc/repair/ranker.py:
     - module docstring: "Source: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.1 step6 + §H + plan A.6 (lexicographic + normalized)"
     - @dataclass(frozen=True) class RankedCandidate:
         candidate: RepairCandidate
         rank: int
         score: float
     - def rank(candidates: Sequence[RepairCandidate]) -> list[RankedCandidate]:
         for c in candidates:
             if c.cost_minutes <= 0:
                 raise ValueError(f"cost_minutes must be > 0: {c.id}")
             if not (0.0 <= c.risk <= 1.0):
                 raise ValueError(f"risk must be in [0,1]: {c.id}")
             if not (0.0 <= c.expected_signal <= 1.0):
                 raise ValueError(f"expected_signal must be in [0,1]: {c.id}")
         sorted_ = sorted(candidates, key=lambda c: (c.cost_minutes, c.risk,
                                                     -c.expected_signal, c.id))
         n = len(sorted_)
         denom = max(1, n - 1)
         return [
             RankedCandidate(candidate=c, rank=i+1,
                             score=((n-(i+1))/denom if n > 1 else 1.0))
             for i, c in enumerate(sorted_)
         ]
  6. Implement tests/test_fglc_repair_diagnose.py (>=8 test groups):
     - sys.path bootstrap (Step 6 pattern: REPO_ROOT/src 삽입)
     (1) test_empty_metrics_with_R3_falls_back_to_bug_suspected:
           diagnose({}, "R3") → [IMPLEMENTATION_BUG_SUSPECTED]
     (2) test_id_nll_high_fires_undercapacity:
           diagnose({"id_nll":0.7,"stagnant_epochs":12,"train_nll":0.7}, "R3")
           → includes MODEL_UNDERCAPACITY
     (3) test_id_nll_below_threshold_does_not_fire:
           diagnose({"id_nll":0.4,"stagnant_epochs":12}, "R3")
           → does NOT include MODEL_UNDERCAPACITY
     (4) test_phase_filter_drops_R6_causes_in_R3:
           correction metric 동시 입력, phase=R3 → CORRECTION_TOO_WEAK/LARGE 제외
     (5) test_dedup_unique_causes:
           동일 cause-id가 두 점화 함수에서 점화되어도 list에 1회만 포함
     (6) test_attention_collapse_fires_low_entropy:
           {"attention_entropy":0.05,"log_k":2.0} → includes ATTENTION_COLLAPSE
     (7) test_corrected_gain_positive_fires_correction_too_large:
           {"corrected_nll_gain":0.05} → includes CORRECTION_TOO_LARGE
     (8) test_invalid_phase_raises:
           diagnose({"id_nll":0.7}, "R99") → ValueError
     (9) test_canonical_metric_keys_nonempty:
           len(CANONICAL_METRIC_KEYS) >= 10
  7. Implement tests/test_fglc_repair_candidates.py (>=6 test groups):
     - sys.path bootstrap
     (1) test_candidates_for_undercapacity_R3_nonempty:
           causes=[MODEL_UNDERCAPACITY] phase="R3" → len(result) >= 1
     (2) test_candidate_field_types:
           모든 result element가 cost_minutes int>0, risk∈[0,1], signal∈[0,1],
           patch dict (json serializable), id str matches regex
     (3) test_candidate_cause_id_subset_of_input:
           모든 result.cause_id ∈ input causes
     (4) test_duplicate_cause_dedup:
           causes=[MODEL_UNDERCAPACITY, MODEL_UNDERCAPACITY] → 단일 입력과 동일 결과
     (5) test_phase_filter_drops_inapplicable:
           causes=[CORRECTION_TOO_LARGE] phase="R3" → 빈 list (R6 only)
     (6) test_implementation_bug_suspected_has_sentinel_patch:
           candidates_for([IMPLEMENTATION_BUG_SUSPECTED], "R3")
           → patch == {"action":"manual_blocker_report"}
     (7) test_candidate_id_regex:
           모든 candidate.id == f"{cause_id.value}_{slug}" with slug regex
  8. Implement tests/test_fglc_repair_ranker.py (>=6 test groups):
     - sys.path bootstrap
     (1) test_sorted_by_cost_then_risk_then_signal_desc_then_id:
           3 candidate with diverse (cost, risk, signal, id) → 정확한 lex 순서
     (2) test_score_in_unit_interval:
           모든 ranked.score ∈ [0, 1]
     (3) test_empty_returns_empty:
           rank([]) → []
     (4) test_single_candidate_score_is_one:
           rank([single]) → [(rank=1, score=1.0)]
     (5) test_invalid_cost_raises:
           cost_minutes=0 candidate → ValueError
     (6) test_invalid_risk_raises:
           risk=1.5 candidate → ValueError
     (7) test_tie_breaker_by_id:
           동일 cost/risk/signal, 다른 id 두 개 → id 사전순
     (8) test_round_trip_diagnose_candidates_rank:
           metrics → diagnose → candidates_for → rank → rank=1 candidate id is well-formed
  9. import 정책 (전체 3 모듈):
     - stdlib (typing, dataclasses, collections.abc) 만 + taxonomy.py.
     - compare.py / ledger.py / __init__.py / configs/ 일절 import 금지.
     - 외부 dep 추가 없음 (filelock도 안 씀).

REQUIRED_TESTS: |
  .venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_diagnose.py tests\test_fglc_repair_candidates.py tests\test_fglc_repair_ranker.py
  NOTE: .venv\Scripts\pytest.exe is broken (silent exit 1). Use python -m pytest only.

ACCEPTANCE_CRITERIA: |
  - Exactly 6 source/test files added (3 src + 3 test).
  - RESULT.md added (7th file).
  - 0 files modified outside FILES_ALLOWED.
  - .venv\Scripts\python.exe -m pytest -q (위 3 file) → all green, total tests >= 20.
  - No test writes files under outputs/, data/, configs/ (Step 7은 file IO 없음).
  - No import from src/fglc/schemas/, src/fglc/repair/compare.py, src/fglc/repair/ledger.py,
    or src/fglc/repair/__init__.py.
  - No external deps beyond stdlib.
  - Working tree clean after commit (git status --short returns empty).

COMMIT_MESSAGE: feat(repair): add diagnose/candidates/ranker modules (cause → patch → rank)

STOP_CONDITION: |
  Stop immediately after the single commit. Do not implement orchestrator.py /
  repair_loop.py — those are Step 8.
  Do not modify docs/EXPERIMENT_REPAIR_LOOP_PLAN.md (read-only SSoT).
  Do not modify src/fglc/repair/__init__.py / taxonomy.py / compare.py / ledger.py.
  Do not add new entries to src/fglc/repair/__init__.py — Step 8 orchestrator merge 시 일괄.

SANDBOX_MODE: bypass

RELATED_AGENT_REPORT_IDS:
  - docs/orchestration/agent_reports/2026-05/impl_risk_fglc_repair_diagnose_candidates_ranker_R1.md
```

### B.3 REQUIRED_TESTS (Step 7 verify 기준)

```
.venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_diagnose.py tests\test_fglc_repair_candidates.py tests\test_fglc_repair_ranker.py
```

기대: ≥20 test 그룹, 모두 PASS. import-time error 없음.

---

## C. Pre-Codex 체크리스트 (main Claude 실행)

```
[ ] 1. Codex worktree 존재 확인:
        Test-Path C:\Users\computer\Desktop\ICLR_WM_codex   → True

[ ] 2. Codex worktree clean state 확인:
        git -C C:\Users\computer\Desktop\ICLR_WM_codex status --short   → empty
        git -C C:\Users\computer\Desktop\ICLR_WM_codex branch --show-current   → codex-work

[ ] 3. Codex worktree를 main과 동기화:
        현재 codex-work HEAD = 6ef1795
        main HEAD = 4165d85 (auto-commit) 또는 이후
        → ff-merge 필요 (codex-work에서: git merge --ff-only memory-redesign-2026-05-16)

[ ] 4. T3 agent 호출 (Codex 실행 *전* — TASK 명세 review):
        implementation-risk-critic agent를 다음 입력으로 호출:
          - TASK 파일 경로: .agent_tasks/codex_queue/TASK_2026_05_23_FGLC_REPAIR_DIAGNOSE_CANDIDATES_RANKER.md
          - SSoT 1: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.2/§D.3
          - SSoT 2: src/fglc/repair/taxonomy.py (Step 5 산출물)
          - 이전 산출물: src/fglc/repair/compare.py, ledger.py (Step 6, read-only 참조)
        보고서 저장 경로:
          docs/orchestration/agent_reports/2026-05/impl_risk_fglc_repair_diagnose_candidates_ranker_R1.md
        verify: PASS 또는 fixable RISK

        체크해야 할 RISK 항목 (Plan agent 식별 8개):
        - RISK-1: §D.3 자연어 → 정규 metric key 매핑이 SSoT 부재 → diagnose 모듈 안 매핑이 SSoT 일탈 위험
        - RISK-2: §D.3 row "corrected NLL > uncorrected"가 LOSS_IMBALANCE도 점화하나 §D.2 verbatim 표 누락 금지
        - RISK-3: EVAL_NOISE_HIGH 같은 multi-phase cause를 R3/R4/R5/R7/R9/R10에서 모두 점화시킬 위험 → DETECTION_THRESHOLDS 명시적 trigger 없으면 점화 안 함
        - RISK-4: Ranker n=1 케이스 division-by-zero → score=1.0
        - RISK-5: CANDIDATE_TABLE 25~30개 hard-code, cost/risk/signal heuristic — docstring "calibration in Step 8 orchestrator" 명시
        - RISK-6: patch dict key가 실제 config schema와 불일치 가능 — Step 7 테스트는 dict shape만 검사
        - RISK-7: IMPLEMENTATION_BUG_SUSPECTED patch=`{}` 위배 → `{"action": "manual_blocker_report"}` sentinel
        - RISK-8: diagnose가 빈 list 반환 시 Step 8이 잘못 accept 위험 → IMPLEMENTATION_BUG_SUSPECTED fallback (사용자 결정 #2)

[ ] 5. TASK 파일 작성:
        Path: .agent_tasks/codex_queue/TASK_2026_05_23_FGLC_REPAIR_DIAGNOSE_CANDIDATES_RANKER.md
        Content: 위 B.2 YAML (RELATED_AGENT_REPORT_IDS는 4번 결과로 채움)
```

---

## D. Codex 실행 절차

```
[ ] 6. Codex worktree를 main과 ff-merge:
        Push-Location C:\Users\computer\Desktop\ICLR_WM_codex
        git fetch
        git merge --ff-only memory-redesign-2026-05-16
        Pop-Location
        verify: 새 HEAD가 main HEAD와 일치

[ ] 7. Codex 호출:
        scripts\run_codex_task.ps1 `
          -Mode run `
          -TaskName fglc_repair_diagnose_candidates_ranker `
          -TaskFile .agent_tasks\codex_queue\TASK_2026_05_23_FGLC_REPAIR_DIAGNOSE_CANDIDATES_RANKER.md `
          -BypassSandbox

[ ] 8. exit code 확인:
        0 = 정상 → Step E
        10 = precondition 실패
        20 = TASK schema 위반
        30 = Codex 실행 실패
        40 = commit 누락 / 금지 경로 위반 / RESULT.md 누락 → Step G.B4 fallback
        50 = merge conflict

[ ] 9. (Codex worktree에서) git diff HEAD~1 --stat 및 --name-only:
        기대 파일 7개만:
          src/fglc/repair/diagnose.py
          src/fglc/repair/candidates.py
          src/fglc/repair/ranker.py
          tests/test_fglc_repair_diagnose.py
          tests/test_fglc_repair_candidates.py
          tests/test_fglc_repair_ranker.py
          .agent_tasks/codex_done/TASK_2030_fglc_repair_diagnose_candidates_ranker_RESULT.md
          (또는 TASK_2026_05_23_FGLC_REPAIR_DIAGNOSE_CANDIDATES_RANKER_RESULT.md)
```

---

## E. Post-Codex 6-Gatekeeper 검증

(`.claude/rules/codex_orchestration_rules.md` §Gatekeeper 정책)

```
[ ] G1. verify mode exit code 0
[ ] G2. git diff HEAD~1 수동 review (Codex worktree):
         - diagnose.py:
           * CANONICAL_METRIC_KEYS frozenset 정의 + 11~14개 키
           * 7개 점화 함수 (§D.2 verbatim) 정확히 매핑
           * metrics.get() 으로 누락 key silent skip
           * applicable_phases_for(phase) filter
           * IMPLEMENTATION_BUG_SUSPECTED fallback (사용자 결정 #2)
           * 잘못된 phase → ValueError
         - candidates.py:
           * RepairCandidate frozen dataclass + 8 필드
           * CANDIDATE_TABLE 25~30개 entry (§D.3 7행 × ~4 candidate)
           * Candidate id 규약 `<CAUSE_ID>_<slug>`
           * patch는 inline dict (configs/ 참조 없음)
           * IMPLEMENTATION_BUG_SUSPECTED candidate sentinel patch
           * candidates_for() 중복 제거 + phase filter
         - ranker.py:
           * RankedCandidate frozen dataclass
           * sort key (cost asc, risk asc, -signal, id asc) (사용자 결정 #1)
           * score (n-rank)/max(1,n-1) 정규화 + n=1 edge=1.0
           * cost<=0 / risk∉[0,1] / signal∉[0,1] → ValueError
         - import 정책:
           * diagnose: taxonomy + stdlib only
           * candidates: taxonomy + stdlib only
           * ranker: candidates + stdlib only
           * compare/ledger/__init__/schemas import 절대 없음
[ ] G3. 금지 경로 미수정:
         git diff HEAD~1 --name-only에 다음 미포함:
           src/fglc/repair/__init__.py
           src/fglc/repair/taxonomy.py
           src/fglc/repair/compare.py
           src/fglc/repair/ledger.py
           src/fglc/schemas/
           .claude/, docs/, configs/, outputs/, scripts/, data/
[ ] G4. RESULT.md 존재 — 8 섹션 (Summary / Files Changed / Commands Run / Tests Run /
                                    Evidence / Risks / Patch Review Notes / Accept/Reject)
[ ] G5. REQUIRED_TESTS 재실행 (Codex worktree, merge 전):
         Push-Location C:\Users\computer\Desktop\ICLR_WM_codex
         .venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_diagnose.py `
                                                tests\test_fglc_repair_candidates.py `
                                                tests\test_fglc_repair_ranker.py
         Pop-Location
         → ≥20 passed, 0 failed
[ ] G6. T3 implementation-risk-critic report PASS 확인:
         docs/orchestration/agent_reports/2026-05/impl_risk_fglc_repair_diagnose_candidates_ranker_R1.md
         verdict: PASS 또는 LOW RISK (fixable post-merge)
```

**하나라도 실패 → `git merge --abort` (또는 Codex commit 미반영 시 ignore).**

---

## F. Accept 절차 (모든 G1~G6 PASS 시)

```
[ ] 10. Codex commit을 main Claude 브랜치에 fast-forward merge:
         git -C C:\Users\computer\Desktop\ICLR_WM_claude-code merge --ff-only codex-work
         (Step 6 교훈: harness가 staged merge 상태로 만들어두면 git commit 직접 실행)

[ ] 11. merge 결과 확인:
         git log --oneline -3
         → "feat(repair): add diagnose/candidates/ranker modules ..." + Co-Author 라인

[ ] 12. main worktree 최종 smoke + 회귀 테스트:
         .venv\Scripts\python.exe -m pytest -q `
            tests\test_fglc_repair_diagnose.py `
            tests\test_fglc_repair_candidates.py `
            tests\test_fglc_repair_ranker.py `
            tests\test_fglc_repair_compare.py `
            tests\test_fglc_repair_ledger.py `
            tests\test_fglc_repair_taxonomy.py
         → 모두 green (≥ 20 + 21 + 8 = ≥49 passed)

[ ] 13. plan 파일 자체는 수정 안 함 (이 plan은 Step 7 record로 보존).
         다음 Step 8용 plan은 이 파일을 overwrite하여 별도 plan으로 작성.
```

---

## G. BLOCKER 시나리오

| # | 시나리오 | 대응 |
|---|---|---|
| B1 | Codex worktree dirty | git stash 또는 사용자 확인. destructive reset 금지. |
| B2 | T3 BLOCKED 반환 | TASK REQUIRED_IMPLEMENTATION 보강 (예: §D.2 row별 임계값 명시) 후 재호출. |
| B3 | exit code 30 (timeout) | RUN_*.err.log 확인. SANDBOX_MODE bypass 미적용 가능성. |
| B4 | exit code 40 (commit 누락) | Step 6 교훈: pytest.exe 실패가 원인일 가능성. Codex worktree에서 manual `python -m pytest` 실행 후 통과 시 (a) git diff 7 파일 확인 → (b) 수동 git add + commit → (c) verify 재실행 → (d) merge. |
| B5 | exit code 40 (금지 경로 위반) | git merge --abort. 특히 src/fglc/repair/__init__.py / taxonomy.py / compare.py / ledger.py 수정 시도 차단. |
| B6 | G5 pytest 실패 (테스트 < 20 또는 일부 fail) | git merge 보류. TASK YAML §6/§7/§8 test group 리스트 강화 후 재시도. |
| B7 | G6 T3 report FAIL | TASK 명세 변경 또는 scope 축소. plan 수정 → 재시도. |
| B8 | round-trip 테스트 실패 (diagnose→candidates→ranker chain) | 세 모듈 dataclass 키 정합 불일치. RepairCandidate 필드명 확인 + ranker 입력 type 확인. |
| B9 | Codex가 IMPLEMENTATION_BUG_SUSPECTED fallback 누락 | TASK §3 fallback 정책을 verbatim 인용 강화 + diagnose test (1) 강제. |
| B10 | Codex가 ranker에 lex 대신 multiplicative score 사용 | TASK §5 sort key tuple `(cost, risk, -signal, id)` verbatim 인용 강화 + ranker test (1) 강제. |
| B11 | CANDIDATE_TABLE에 §D.3 일부 행 누락 | TASK §4 candidate test (1) "≥1 per cause row"가 강제. T3에서 D.3 7행 1:1 정합 검증. |
| B12 | patch dict이 빈 dict로 채워짐 (sentinel 외) | candidates test (2)가 강제. IMPLEMENTATION_BUG_SUSPECTED만 sentinel `{"action": "manual_blocker_report"}` 허용. |

---

## H. 수정 대상 파일 (이 Step 7 한정)

### H.1 신규 생성 (Codex 위임)

| 경로 | 작성자 |
|---|---|
| `src/fglc/repair/diagnose.py` | Codex |
| `src/fglc/repair/candidates.py` | Codex |
| `src/fglc/repair/ranker.py` | Codex |
| `tests/test_fglc_repair_diagnose.py` | Codex |
| `tests/test_fglc_repair_candidates.py` | Codex |
| `tests/test_fglc_repair_ranker.py` | Codex |
| `.agent_tasks/codex_done/TASK_<2030 또는 2026_05_23>_fglc_repair_diagnose_candidates_ranker_RESULT.md` | Codex |

### H.2 신규 생성 (main Claude)

| 경로 | 작성자 |
|---|---|
| `.agent_tasks/codex_queue/TASK_2026_05_23_FGLC_REPAIR_DIAGNOSE_CANDIDATES_RANKER.md` | main Claude (Pre-Codex C.5) |
| `docs/orchestration/agent_reports/2026-05/impl_risk_fglc_repair_diagnose_candidates_ranker_R1.md` | main Claude (T3 결과) |

### H.3 수정 금지 (불변 보존)

CLAUDE.md §불변 보존:
- `src/fglc/schemas/visibility.py`
- `docs/idea/18_DATA_BENCHMARKS.md`
- `docs/idea/19_BASELINES.md`
- `docs/idea/20_ABLATIONS.md`
- `.claude/settings.json`
- `scripts/run_codex_task.ps1`

Step 7 추가 보존:
- `docs/idea/FGLC_FAILURE_TAXONOMY.md` (read-only SSoT)
- `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` (read-only spec)
- `docs/EXPERIMENT_LEDGER_SCHEMA.md` (read-only spec)
- `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md` (read-only spec)
- `.agent_tasks/codex_prompt_template.md` (Codex 측 contract)
- **`src/fglc/repair/__init__.py` (Step 5 산출물 — Step 8 일괄 처리)**
- **`src/fglc/repair/taxonomy.py` (Step 5)**
- **`src/fglc/repair/compare.py` (Step 6)**
- **`src/fglc/repair/ledger.py` (Step 6)**

---

## I. 명시적 비-범위 (이 Step에서 안 함)

- `src/fglc/repair/orchestrator.py` (Step 8)
- `scripts/fglc/repair_loop.py` (Step 8)
- `configs/fglc/smoke_4060.yaml` (Step 8)
- `src/fglc/repair/__init__.py` 갱신 (compare/ledger/diagnose/candidates/ranker re-export) — Step 8과 함께
- `outputs/repair/{loop_id}/` 디렉터리 생성 (Step 8 orchestrator)
- ledger.append_ledger_line 직접 호출 (Step 8 orchestrator)
- 실제 metric 수집/측정 (Step 9~10 runner)
- patch dict의 config schema 검증 (Step 8 orchestrator)
- phase gate sentinel 생성
- AGENTS.md / hooks / settings.json 수정

---

## J. 검증 (이 plan이 사용자 의도와 정합한지)

1. **§D.2 7행 verbatim** — A.8 표 + B.2 §3 `_fire_*` 7 함수 1:1.
2. **§D.3 7행 verbatim** — A.8 표 + B.2 §4 CANDIDATE_TABLE 25~30 candidate.
3. **사용자 결정 3건 모두 반영**:
   - 결정 #1 Ranker = lex + 정규화 → A.5 + B.2 §5 sort key + score 공식 명시
   - 결정 #2 누락 metric = silent skip + fallback → A.1 + B.2 §3 metrics.get() + fallback 명시
   - 결정 #3 단일 TASK → B 전체 + H.1 7 파일 단일 commit
4. **Plan agent 결정 3건 반영**:
   - id 규약 `<CAUSE_ID>_<slug>` → A.3 + B.2 §4 예시
   - patch = inline dict → A.3 + B.2 §4 + FILES_FORBIDDEN configs/
   - CANDIDATE_TABLE 25~30 hard-code + heuristic docstring → A.3 + B.2 §4 RISK-5
5. **Codex 금지 경로 정합성** — codex_prompt_template.md Step 2 forbidden + TASK FILES_FORBIDDEN 1:1.
6. **T3 트리거** — 3 모듈 동시 도입 = 주요 Codex merge → impl-risk-critic 의무.
7. **6-gatekeeper** — G1~G6 매핑 완전.
8. **Step 6 교훈 반영** — REQUIRED_TESTS에 `pytest.exe` 사용 금지 + B4 manual recovery 절차 + harness staged-merge → manual commit (F.10).
9. **불변 파일 H.3 등록** — CLAUDE.md 6개 + plan 산출물 4개 + Step 5/6 산출물 4개.
10. **BLOCKER 12개 모두 대응 절차 있음**.
11. **outputs/ 경로 보호** — Step 7은 file IO 없음 (tmp_path 불필요).
12. **추가 dep 없음** — stdlib only.

검증 실패 항목 발견 시 plan을 이 파일에서만 수정.

---

## K. 다음 execute 단계에서 수행할 최소 작업

이 plan이 ExitPlanMode로 승인되면 **즉시 수행할 최소 작업**:

1. C.1~C.2 Codex worktree 상태 확인 (read-only).
2. C.3 / D.6 Codex worktree를 main과 ff-merge.
3. C.4 T3 implementation-risk-critic agent 호출. 보고서 저장.
4. C.5 TASK 파일 작성: `.agent_tasks/codex_queue/TASK_2026_05_23_FGLC_REPAIR_DIAGNOSE_CANDIDATES_RANKER.md`.
5. D.7 Codex 실행: `scripts/run_codex_task.ps1 -Mode run -TaskName fglc_repair_diagnose_candidates_ranker ...`.
6. D.8~E.G6 검증.
7. F.10 git merge --ff-only codex-work (모든 G PASS 시; Step 6 교훈상 harness 상태에 따라 수동 commit).
8. F.12 main worktree에서 회귀 테스트 (diagnose/candidates/ranker + compare/ledger/taxonomy 모두).

이 단계에서 **절대 안 함**:
- 코드 직접 작성 (3 모듈 + 테스트 모두 Codex 작성).
- 다른 repair 모듈 (orchestrator, scripts/fglc/repair_loop.py) 작성.
- docs/ 수정.
- 새 sentinel 생성.
- 실제 학습 실행.
- src/fglc/repair/__init__.py 갱신.
- outputs/ / data/ / configs/ 아래 파일 생성.
