TASK_NAME: fglc_repair_diagnose_candidates_ranker

BACKGROUND: |
  docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.2 (observation → cause-id 매핑 7행)
  + §D.3 (cause → candidate cheapest-first 7행) + Step 5 taxonomy.py + Step 6 ledger schema가
  closed-loop repair harness의 결정 직전 단계를 정의한다.
  이 TASK는 그 명세를 세 개의 Python 모듈로 구현한다:
    diagnose(metrics, phase) → cause-id list
    candidates_for(causes, phase) → RepairCandidate list
    rank(candidates) → RankedCandidate list (rank=1이 best)

  Step 5 산출물: src/fglc/repair/taxonomy.py (FailureCauseId 20개 enum, applicable_phases_for, DETECTION_THRESHOLDS)
  Step 6 산출물: src/fglc/repair/compare.py, src/fglc/repair/ledger.py (읽기 전용 참조)

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
    tests/test_fglc_repair_diagnose.py    (>=9 test groups)
    tests/test_fglc_repair_candidates.py  (>=7 test groups)
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
         _fire_id_nll(metrics)
           # id_nll > 0.5 AND stagnant_epochs >= 10 → [MODEL_UNDERCAPACITY, DATA_TOO_SMALL, HORIZON_TOO_SHORT, LOSS_IMBALANCE]
           # §D.2 row 1: "ID NLL 높음"
         _fire_ood_auroc(metrics)
           # ood_auroc < 0.7 → [SIGMA_CALIBRATION_FAILURE, BETA_GATE_COLLAPSE, OOD_TOO_EASY, DATA_BAD_SPLIT]
           # §D.2 row 2: "OOD AUROC 낮음"
         _fire_corrected_gain(metrics)
           # corrected_nll_gain > 0 (corrected NLL > uncorrected) → [CORRECTION_TOO_LARGE, ATTENTION_COLLAPSE, LOSS_IMBALANCE]
           # §D.2 row 3
         _fire_attention(metrics)
           # attention_entropy < 0.1 OR attention_entropy > 0.95 * log_k → [ATTENTION_COLLAPSE]
           # §D.2 row 4: "attention entropy 과다"
         _fire_correction_weak(metrics)
           # correction_norm_mean < 0.01 → [CORRECTION_TOO_WEAK, BETA_GATE_COLLAPSE]
           # §D.2 row 5: "correction norm ≈ 0"
         _fire_correction_large(metrics)
           # correction_norm_mean > 0.9 (proxy for bound hit ratio high) → [CORRECTION_TOO_LARGE]
           # §D.2 row 6: "correction norm 과다"
         _fire_planner(metrics)
           # planner_return_gain <= 0 → [PLANNER_BUDGET_TOO_LOW, HORIZON_TOO_LONG, IMPLEMENTATION_BUG_SUSPECTED]
           # §D.2 row 7: "planner return 개선 없음"
       각 함수는 metrics.get()으로 누락 key silent skip.
       누락 key는 해당 조건을 False로 처리하여 빈 list 반환.
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
     - from __future__ import annotations
     - from dataclasses import dataclass
     - from typing import Any, Mapping, Sequence
     - from src.fglc.repair.taxonomy import FailureCauseId
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
       Candidate id 규약: f"{cause_id.value}_{slug}" where slug matches regex [a-z0-9_]{2,40}.

       §D.3 row 1: ID NLL 높음 → MODEL_UNDERCAPACITY, DATA_TOO_SMALL, HORIZON_TOO_SHORT, LOSS_IMBALANCE
       예시:
         RepairCandidate(id="MODEL_UNDERCAPACITY_h_dim_256",
                         cause_id=FailureCauseId.MODEL_UNDERCAPACITY,
                         patch={"hidden_dim": 256},
                         cost_minutes=15, risk=0.1, expected_signal=0.6,
                         description="Increase hidden_dim 128→256.",
                         applicable_phases=("R3",))
         RepairCandidate(id="DATA_TOO_SMALL_episode_x2",
                         cause_id=FailureCauseId.DATA_TOO_SMALL,
                         patch={"num_episodes": 200},
                         cost_minutes=30, risk=0.1, expected_signal=0.5,
                         description="Double episode count.",
                         applicable_phases=("R2", "R3"))
         RepairCandidate(id="HORIZON_TOO_SHORT_horizon_16",
                         cause_id=FailureCauseId.HORIZON_TOO_SHORT,
                         patch={"horizon": 16},
                         cost_minutes=20, risk=0.2, expected_signal=0.4,
                         description="Extend training horizon 8→16.",
                         applicable_phases=("R3",))
         RepairCandidate(id="LOSS_IMBALANCE_weights_rebalance",
                         cause_id=FailureCauseId.LOSS_IMBALANCE,
                         patch={"loss_weights": {"nll": 1.0, "kl": 0.1}},
                         cost_minutes=10, risk=0.2, expected_signal=0.4,
                         description="Rebalance loss component weights.",
                         applicable_phases=("R3",))

       §D.3 row 2: OOD AUROC 낮음 → SIGMA_CALIBRATION_FAILURE, BETA_GATE_COLLAPSE, OOD_TOO_EASY, DATA_BAD_SPLIT
         RepairCandidate(id="SIGMA_CALIBRATION_FAILURE_add_l_cal",
                         cause_id=FailureCauseId.SIGMA_CALIBRATION_FAILURE,
                         patch={"calibration_loss_weight": 0.1},
                         cost_minutes=10, risk=0.1, expected_signal=0.7,
                         description="Add L_cal calibration penalty.",
                         applicable_phases=("R4",))
         RepairCandidate(id="BETA_GATE_COLLAPSE_reparam",
                         cause_id=FailureCauseId.BETA_GATE_COLLAPSE,
                         patch={"beta_reparameterize": True},
                         cost_minutes=15, risk=0.2, expected_signal=0.5,
                         description="Reparameterize beta gate to avoid collapse.",
                         applicable_phases=("R4",))
         RepairCandidate(id="OOD_TOO_EASY_shift_strength_2x",
                         cause_id=FailureCauseId.OOD_TOO_EASY,
                         patch={"ood_shift_scale": 2.0},
                         cost_minutes=20, risk=0.2, expected_signal=0.5,
                         description="Double OOD shift magnitude.",
                         applicable_phases=("R2",))
         RepairCandidate(id="DATA_BAD_SPLIT_regenerate",
                         cause_id=FailureCauseId.DATA_BAD_SPLIT,
                         patch={"regenerate_split": True},
                         cost_minutes=30, risk=0.3, expected_signal=0.6,
                         description="Regenerate ID/OOD split.",
                         applicable_phases=("R2",))

       §D.3 row 3: corrected NLL > uncorrected → CORRECTION_TOO_LARGE, ATTENTION_COLLAPSE, LOSS_IMBALANCE
         RepairCandidate(id="CORRECTION_TOO_LARGE_delta_max_01",
                         cause_id=FailureCauseId.CORRECTION_TOO_LARGE,
                         patch={"delta_max": 0.1},
                         cost_minutes=5, risk=0.1, expected_signal=0.7,
                         description="Reduce delta_max 0.25→0.1.",
                         applicable_phases=("R6",))
         RepairCandidate(id="ATTENTION_COLLAPSE_entmax",
                         cause_id=FailureCauseId.ATTENTION_COLLAPSE,
                         patch={"attention_type": "entmax"},
                         cost_minutes=10, risk=0.2, expected_signal=0.6,
                         description="Switch to entmax/sparsemax attention.",
                         applicable_phases=("R5", "R6"))
         RepairCandidate(id="LOSS_IMBALANCE_corrected_loss_weight_down",
                         cause_id=FailureCauseId.LOSS_IMBALANCE,
                         patch={"corrected_loss_weight": 0.5},
                         cost_minutes=5, risk=0.1, expected_signal=0.5,
                         description="Reduce corrected_loss_weight.",
                         applicable_phases=("R3",))
         RepairCandidate(id="CORRECTION_TOO_LARGE_base_wm_freeze",
                         cause_id=FailureCauseId.CORRECTION_TOO_LARGE,
                         patch={"freeze_base_wm": True},
                         cost_minutes=15, risk=0.3, expected_signal=0.5,
                         description="Freeze base WM during correction training.",
                         applicable_phases=("R6",))

       §D.3 row 4: attention entropy 과다 → ATTENTION_COLLAPSE
         RepairCandidate(id="ATTENTION_COLLAPSE_entmax_alpha_15",
                         cause_id=FailureCauseId.ATTENTION_COLLAPSE,
                         patch={"entmax_alpha": 1.5},
                         cost_minutes=5, risk=0.1, expected_signal=0.6,
                         description="Set entmax alpha=1.5 for sparse attention.",
                         applicable_phases=("R5",))
         RepairCandidate(id="ATTENTION_COLLAPSE_topk_mask_k2",
                         cause_id=FailureCauseId.ATTENTION_COLLAPSE,
                         patch={"topk_mask_k": 2},
                         cost_minutes=5, risk=0.1, expected_signal=0.5,
                         description="Apply top-k mask with k=2.",
                         applicable_phases=("R5",))
         RepairCandidate(id="ATTENTION_COLLAPSE_sparsity_penalty",
                         cause_id=FailureCauseId.ATTENTION_COLLAPSE,
                         patch={"attention_sparsity_penalty": 0.01},
                         cost_minutes=5, risk=0.1, expected_signal=0.4,
                         description="Add sparsity penalty to attention.",
                         applicable_phases=("R5",))

       §D.3 row 5: correction norm ≈ 0 → CORRECTION_TOO_WEAK, BETA_GATE_COLLAPSE
         RepairCandidate(id="CORRECTION_TOO_WEAK_delta_head_init_scale",
                         cause_id=FailureCauseId.CORRECTION_TOO_WEAK,
                         patch={"delta_head_init_scale": 0.1},
                         cost_minutes=5, risk=0.1, expected_signal=0.6,
                         description="Increase delta head init scale.",
                         applicable_phases=("R6",))
         RepairCandidate(id="CORRECTION_TOO_WEAK_corrected_loss_weight_up",
                         cause_id=FailureCauseId.CORRECTION_TOO_WEAK,
                         patch={"corrected_loss_weight": 2.0},
                         cost_minutes=5, risk=0.1, expected_signal=0.5,
                         description="Increase corrected loss weight.",
                         applicable_phases=("R6",))
         RepairCandidate(id="BETA_GATE_COLLAPSE_prior_scale_reset",
                         cause_id=FailureCauseId.BETA_GATE_COLLAPSE,
                         patch={"beta_prior_scale": 1.0},
                         cost_minutes=10, risk=0.2, expected_signal=0.4,
                         description="Reset beta prior scale.",
                         applicable_phases=("R4",))

       §D.3 row 6: correction norm 과다 → CORRECTION_TOO_LARGE (별도 candidate 세트)
         RepairCandidate(id="CORRECTION_TOO_LARGE_delta_max_reduce",
                         cause_id=FailureCauseId.CORRECTION_TOO_LARGE,
                         patch={"delta_max": 0.05},
                         cost_minutes=5, risk=0.1, expected_signal=0.7,
                         description="Reduce delta_max to 0.05.",
                         applicable_phases=("R6",))
         RepairCandidate(id="CORRECTION_TOO_LARGE_l_corr_size_up",
                         cause_id=FailureCauseId.CORRECTION_TOO_LARGE,
                         patch={"l_corr_size_weight": 0.1},
                         cost_minutes=5, risk=0.1, expected_signal=0.5,
                         description="Increase L_corr_size penalty weight.",
                         applicable_phases=("R6",))

       §D.3 row 7: planner return 개선 없음 → PLANNER_BUDGET_TOO_LOW, HORIZON_TOO_LONG, IMPLEMENTATION_BUG_SUSPECTED
         RepairCandidate(id="PLANNER_BUDGET_TOO_LOW_n_candidate_up",
                         cause_id=FailureCauseId.PLANNER_BUDGET_TOO_LOW,
                         patch={"n_candidates": 512},
                         cost_minutes=10, risk=0.1, expected_signal=0.6,
                         description="Increase planner rollout count.",
                         applicable_phases=("R7",))
         RepairCandidate(id="HORIZON_TOO_LONG_horizon_3",
                         cause_id=FailureCauseId.HORIZON_TOO_LONG,
                         patch={"planning_horizon": 3},
                         cost_minutes=5, risk=0.1, expected_signal=0.5,
                         description="Reduce planning horizon 5→3.",
                         applicable_phases=("R7",))
         RepairCandidate(id="PLANNER_BUDGET_TOO_LOW_value_head_retrain",
                         cause_id=FailureCauseId.PLANNER_BUDGET_TOO_LOW,
                         patch={"retrain_value_head": True},
                         cost_minutes=20, risk=0.3, expected_signal=0.5,
                         description="Retrain reward/value head.",
                         applicable_phases=("R7",))
         RepairCandidate(id="IMPLEMENTATION_BUG_SUSPECTED_manual_blocker",
                         cause_id=FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED,
                         patch={"action": "manual_blocker_report"},
                         cost_minutes=1, risk=0.0, expected_signal=0.0,
                         description="Escalate to user; no automated patch.",
                         applicable_phases=("R3", "R4", "R5", "R6", "R7"))

       NOTE on heuristic values: cost_minutes / risk / expected_signal are heuristic estimates.
       Calibration is deferred to Step 8 orchestrator.

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
     - 모든 patch dict은 비어있으면 안 됨 (단 IMPLEMENTATION_BUG_SUSPECTED sentinel {"action":"manual_blocker_report"} 허용).
       IMPLEMENTATION_BUG_SUSPECTED sentinel 제외 모든 candidate의 patch는 bool(patch) == True여야 한다.

  5. Implement src/fglc/repair/ranker.py:
     - module docstring: "Source: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.1 step6 + §H + plan A.6 (lexicographic + normalized)"
     - from __future__ import annotations
     - from dataclasses import dataclass
     - from typing import Sequence
     - from src.fglc.repair.candidates import RepairCandidate
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

  6. Implement tests/test_fglc_repair_diagnose.py (>=9 test groups):
     - sys.path bootstrap: insert REPO_ROOT/src into sys.path before imports
       (REPO_ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(REPO_ROOT / "src")))
     - import from fglc.repair.diagnose (not src.fglc.repair.diagnose)
     (1) test_empty_metrics_with_R3_falls_back_to_bug_suspected:
           diagnose({}, "R3") == [FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED]
     (2) test_id_nll_high_fires_undercapacity:
           diagnose({"id_nll":0.7,"stagnant_epochs":12,"train_nll":0.7}, "R3")
           → FailureCauseId.MODEL_UNDERCAPACITY in result
     (3) test_id_nll_below_threshold_does_not_fire:
           diagnose({"id_nll":0.4,"stagnant_epochs":12}, "R3")
           → FailureCauseId.MODEL_UNDERCAPACITY NOT in result
     (4) test_phase_filter_drops_R6_causes_in_R3:
           diagnose({"correction_norm_mean":0.005}, "R3")
           → FailureCauseId.CORRECTION_TOO_WEAK NOT in result
     (5) test_dedup_unique_causes:
           If both _fire_corrected_gain and _fire_planner would fire IMPLEMENTATION_BUG_SUSPECTED in R7,
           diagnose({"corrected_nll_gain":0.05, "planner_return_gain":-0.1}, "R7")
           → result.count(FailureCauseId.CORRECTION_TOO_LARGE) <= 1
     (6) test_attention_collapse_fires_low_entropy:
           diagnose({"attention_entropy":0.05,"log_k":2.0}, "R5")
           → FailureCauseId.ATTENTION_COLLAPSE in result
     (7) test_corrected_gain_positive_fires_correction_too_large:
           diagnose({"corrected_nll_gain":0.05}, "R6")
           → FailureCauseId.CORRECTION_TOO_LARGE in result
     (8) test_invalid_phase_raises:
           with pytest.raises(ValueError):
               diagnose({"id_nll":0.7}, "R99")
     (9) test_canonical_metric_keys_nonempty:
           len(CANONICAL_METRIC_KEYS) >= 10
           all(isinstance(k, str) for k in CANONICAL_METRIC_KEYS)

  7. Implement tests/test_fglc_repair_candidates.py (>=7 test groups):
     - sys.path bootstrap (same pattern as diagnose test)
     - import from fglc.repair.candidates (not src.fglc.repair.candidates)
     (1) test_candidates_for_undercapacity_R3_nonempty:
           causes=[FailureCauseId.MODEL_UNDERCAPACITY], phase="R3" → len(result) >= 1
     (2) test_candidate_field_types:
           For each c in result:
             assert isinstance(c.cost_minutes, int) and c.cost_minutes > 0
             assert 0.0 <= c.risk <= 1.0
             assert 0.0 <= c.expected_signal <= 1.0
             assert isinstance(c.patch, dict)
             # patch truthy except IMPLEMENTATION_BUG_SUSPECTED sentinel
             if c.cause_id != FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED:
                 assert c.patch
             import re
             assert re.match(r'^[A-Z_]+_[a-z0-9_]{2,40}$', c.id)
     (3) test_candidate_cause_id_subset_of_input:
           causes = [FailureCauseId.MODEL_UNDERCAPACITY, FailureCauseId.SIGMA_CALIBRATION_FAILURE]
           result = candidates_for(causes, "R3")
           assert all(c.cause_id in causes for c in result)
     (4) test_duplicate_cause_dedup:
           causes=[FailureCauseId.MODEL_UNDERCAPACITY, FailureCauseId.MODEL_UNDERCAPACITY]
           result1 = candidates_for(causes, "R3")
           result2 = candidates_for([FailureCauseId.MODEL_UNDERCAPACITY], "R3")
           assert result1 == result2
     (5) test_phase_filter_drops_inapplicable:
           causes=[FailureCauseId.CORRECTION_TOO_WEAK], phase="R3"
           → result == [] (CORRECTION_TOO_WEAK candidates have applicable_phases=("R6",))
     (6) test_implementation_bug_suspected_has_sentinel_patch:
           result = candidates_for([FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED], "R3")
           assert len(result) >= 1
           assert result[0].patch == {"action": "manual_blocker_report"}
     (7) test_candidates_for_all_d3_cause_groups:
           # §D.3 7행의 대표 cause별 올바른 phase로 호출 시 len(result) >= 1
           test_cases = [
               (FailureCauseId.MODEL_UNDERCAPACITY, "R3"),
               (FailureCauseId.SIGMA_CALIBRATION_FAILURE, "R4"),
               (FailureCauseId.ATTENTION_COLLAPSE, "R5"),
               (FailureCauseId.CORRECTION_TOO_WEAK, "R6"),
               (FailureCauseId.CORRECTION_TOO_LARGE, "R6"),
               (FailureCauseId.PLANNER_BUDGET_TOO_LOW, "R7"),
               (FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED, "R3"),
           ]
           for cause, phase in test_cases:
               r = candidates_for([cause], phase)
               assert len(r) >= 1, f"No candidates for {cause} in phase {phase}"

  8. Implement tests/test_fglc_repair_ranker.py (>=6 test groups):
     - sys.path bootstrap
     - import from fglc.repair.candidates (RepairCandidate) and fglc.repair.ranker
     - Helper: def make_candidate(id, cost, risk, signal, cause_id=None):
         return RepairCandidate(
             id=id,
             cause_id=cause_id or FailureCauseId.MODEL_UNDERCAPACITY,
             patch={"hidden_dim": 256},
             cost_minutes=cost,
             risk=risk,
             expected_signal=signal,
             description="test",
             applicable_phases=("R3",)
         )
     (1) test_sorted_by_cost_then_risk_then_signal_desc_then_id:
           c1 = make_candidate("c1", cost=5, risk=0.1, signal=0.6)   # best
           c2 = make_candidate("c2", cost=10, risk=0.1, signal=0.6)  # 2nd
           c3 = make_candidate("c3", cost=5, risk=0.2, signal=0.6)   # 3rd (cost same, higher risk)
           result = rank([c2, c3, c1])
           assert result[0].candidate.id == "c1"
           assert result[1].candidate.id == "c3"
           assert result[2].candidate.id == "c2"
     (2) test_score_in_unit_interval:
           candidates = [make_candidate(f"c{i}", cost=i+1, risk=0.1, signal=0.5) for i in range(5)]
           result = rank(candidates)
           assert all(0.0 <= r.score <= 1.0 for r in result)
     (3) test_empty_returns_empty:
           assert rank([]) == []
     (4) test_single_candidate_score_is_one:
           c = make_candidate("c1", cost=5, risk=0.1, signal=0.5)
           result = rank([c])
           assert len(result) == 1
           assert result[0].rank == 1
           assert result[0].score == 1.0
     (5) test_invalid_cost_raises:
           c = make_candidate("bad", cost=0, risk=0.1, signal=0.5)
           with pytest.raises(ValueError):
               rank([c])
     (6) test_invalid_risk_raises:
           c = make_candidate("bad", cost=5, risk=1.5, signal=0.5)
           with pytest.raises(ValueError):
               rank([c])
     (7) test_tie_breaker_by_id:
           c1 = make_candidate("aaa", cost=5, risk=0.1, signal=0.5)
           c2 = make_candidate("bbb", cost=5, risk=0.1, signal=0.5)
           result = rank([c2, c1])
           assert result[0].candidate.id == "aaa"
     (8) test_round_trip_diagnose_candidates_rank:
           from fglc.repair.diagnose import diagnose
           metrics = {"id_nll": 0.7, "stagnant_epochs": 12, "train_nll": 0.7}
           causes = diagnose(metrics, "R3")
           assert len(causes) >= 1
           from fglc.repair.candidates import candidates_for
           candidates = candidates_for(causes, "R3")
           assert len(candidates) >= 1
           result = rank(candidates)
           assert len(result) >= 1
           assert result[0].rank == 1
           import re
           assert re.match(r'^[A-Z_]+_[a-z0-9_]{2,40}$', result[0].candidate.id)

  9. import 정책 (전체 3 모듈 + 3 테스트):
     - diagnose.py: from fglc.repair.taxonomy import ... + stdlib (typing, dataclasses, collections.abc) only
     - candidates.py: from fglc.repair.taxonomy import ... + stdlib only
     - ranker.py: from fglc.repair.candidates import RepairCandidate + stdlib only
     - compare.py / ledger.py / __init__.py / configs/ 일절 import 금지
     - 외부 dep 추가 없음 (filelock도 안 씀)
     - Test files sys.path bootstrap: insert REPO_ROOT/src before imports
       (REPO_ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(REPO_ROOT / "src")))

REQUIRED_TESTS: |
  .venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_diagnose.py tests\test_fglc_repair_candidates.py tests\test_fglc_repair_ranker.py
  NOTE: .venv\Scripts\pytest.exe is broken (silent exit 1). Use python -m pytest ONLY.
  Expected: all green, total tests >= 22.

ACCEPTANCE_CRITERIA: |
  - Exactly 6 source/test files added (3 src + 3 test).
  - RESULT.md added (7th file).
  - 0 files modified outside FILES_ALLOWED.
  - .venv\Scripts\python.exe -m pytest -q (above 3 files) → all green, total tests >= 22.
  - No test writes files under outputs/, data/, configs/ (Step 7 has no file IO).
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

  SCOPE BOUNDARY — DO NOT IMPLEMENT:
  EVAL_NOISE_HIGH, BASELINE_MISMATCH, and R2-only causes (DATA_TOO_SMALL, DATA_BAD_SPLIT,
  OOD_TOO_HARD, OOD_TOO_EASY) are OUTSIDE the §D.2 7-row scope.
  Do NOT add fire functions for ci95_over_effect_size or other metrics beyond the 7 rows.
  These causes may appear in CANDIDATE_TABLE but must NOT be added as fire functions in diagnose.py.
  The 7 _fire_* functions must map EXACTLY to the 7 rows in §D.2.

SANDBOX_MODE: bypass

RELATED_AGENT_REPORT_IDS:
  - docs/orchestration/agent_reports/2026-05/impl_risk_fglc_repair_diagnose_candidates_ranker_R1.md
