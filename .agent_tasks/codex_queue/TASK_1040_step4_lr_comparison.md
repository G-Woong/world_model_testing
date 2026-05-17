TASK_NAME: TASK_1040_step4_lr_comparison
SANDBOX_MODE: bypass

BACKGROUND: |
  FRCG-WM STEP 4 — B2 blocker.
  `LikelihoodRatioFalsificationScorer` (lr_scorer.py:349) 는 text path에서 dead code다.
  active F_t = `planning/falsification.py::falsification_score` via `text_frcg_plan`.

  이 Task는 active path를 변경하지 않고, 같은 dataset에서 두 F_t를 나란히 계산해
  차이를 정량화하는 comparison report만 작성한다.

  lr_scorer.py에서 PUBLIC_SAFE_METADATA_KEYS (L266-272) 목록이 있으며,
  HypothesisCandidate (L144-156)는 public-safe 필드만 사용한다.
  `EvidenceFeatures.from_public_step()` API를 사용해야 한다.

  비교 결정 기준 (계획 §D.3):
  - mean abs_diff < 0.01  → "numerically equivalent, full wiring OK as STEP 5 work"
  - 0.01 ≤ mean abs_diff < 0.5 → "minor drift, document and decide in STEP 5"
  - mean abs_diff ≥ 0.5  → "major divergence, STEP 5 must reconcile before any C3 claim"

GOAL: |
  1. scripts/audit_step4_lr_comparison.py 신규 생성
     - v0_3 or v0_2 test_id 처음 5 episodes 대상
     - 각 step에서 plan_meta.F_t (A) 와 LikelihoodRatioFalsificationScorer.score() F_t (B) 산출
     - outputs/audits/step4_lr_comparison.json 에 결과 기록
  2. tests/test_step4_lr_comparison.py (4개 테스트)

FILES_ALLOWED: |
  scripts/audit_step4_lr_comparison.py
  tests/test_step4_lr_comparison.py

FILES_FORBIDDEN: |
  src/frcgw/evaluation/frcg_agent.py
  src/frcgw/planning/planner.py
  src/frcgw/planning/falsification.py
  scripts/10_run_lr_real_eval.py
  src/frcgw/schemas/visibility.py
  paper_context_ref/
  data/
  .claude/settings.json
  scripts/run_codex_task.ps1
  configs/
  outputs/

REQUIRED_IMPLEMENTATION: |
  ### audit_step4_lr_comparison.py (신규)

  ```python
  """audit_step4_lr_comparison — Comparison of plan_meta.F_t vs LR scorer F_t.

  COMPARE-ONLY: Does not modify the active F_t path.
  Source: docs/orchestration/lr_alignment/21_step4_execution_plan.md §D.3
  """
  import json
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parents[1]
  SRC_ROOT = REPO_ROOT / "src"
  if str(SRC_ROOT) not in sys.path:
      sys.path.insert(0, str(SRC_ROOT))

  import argparse

  def main() -> int:
      parser = argparse.ArgumentParser()
      parser.add_argument("--dataset", default=None)
      parser.add_argument("--n-episodes", type=int, default=5)
      parser.add_argument("--out", default="outputs/audits/step4_lr_comparison.json")
      args = parser.parse_args()

      # Fallback: v0_3 first, then v0_2
      if args.dataset is None:
          candidates = [
              "data/frcgw_text/v0_3/test_id.jsonl",
              "data/frcgw_text/v0_2/test_id.jsonl",
          ]
          dataset_path = next(
              (Path(c) for c in candidates if Path(c).exists()), None
          )
          if dataset_path is None:
              print("ERROR: no test_id dataset found")
              return 1
      else:
          dataset_path = Path(args.dataset)

      from frcgw.falsification.lr_scorer import (
          EvidenceFeatures,
          EvidenceLikelihood,
          LikelihoodRatioFalsificationScorer,
      )
      from frcgw.models.text_frcg_model import TextFRCGModel
      from frcgw.planning.planner import PlannerState, text_frcg_plan
      from frcgw.planning.decision_gate import GateConfig
      from frcgw.schemas.step_schema import CandidateAction, PublicObservation

      import torch

      lines = [
          json.loads(line)
          for line in dataset_path.read_text(encoding="utf-8").splitlines()
          if line.strip()
      ][:args.n_episodes]

      model = TextFRCGModel()
      model.eval()
      scorer = LikelihoodRatioFalsificationScorer()
      likelihood = EvidenceLikelihood()
      gate_cfg = GateConfig(tau_f=0.5)
      results = []

      for ep in lines:
          planner_state = PlannerState()
          for step_idx, step in enumerate(ep.get("steps", [])):
              obs_raw = step.get("public_observation") or {}
              candidates = [
                  CandidateAction(
                      action_id=ca.get("action_id", ""),
                      action_type=ca.get("action_type", ""),
                      action_params=dict(ca.get("action_params") or {}),
                  )
                  for ca in obs_raw.get("candidate_actions_public", [])
              ]
              obs = PublicObservation(
                  instruction=str(obs_raw.get("instruction", "")),
                  history_public=list(obs_raw.get("history_public") or []),
                  candidate_actions_public=candidates,
              )

              with torch.no_grad():
                  _, plan_meta = text_frcg_plan(
                      obs, step_idx, candidates, model, planner_state, gate_cfg
                  )
              f_t_planner = float(plan_meta.F_t)

              # LR scorer path (dead code in active agent)
              try:
                  features = EvidenceFeatures.from_public_step(obs, step_idx)
                  likelihood_result = likelihood.score(features)
                  lr_result = scorer.score([
                      type('H', (), {'grammar_id': f'g{i}', 'log_prob': float(p)})()
                      for i, p in enumerate([0.5] * 8)
                  ], likelihood_result)
                  f_t_lr = float(getattr(lr_result, 'F_t', 0.0))
                  lr_ok = True
              except Exception as e:
                  f_t_lr = 0.0
                  lr_ok = False

              abs_diff = abs(f_t_planner - f_t_lr)
              results.append({
                  "episode_id": str(ep.get("episode_id", "")),
                  "step_index": step_idx,
                  "F_t_planner": f_t_planner,
                  "F_t_lr_scorer": f_t_lr,
                  "abs_diff": abs_diff,
                  "degenerate_planner": f_t_planner == 0.0,
                  "degenerate_lr": f_t_lr == 0.0,
                  "lr_scorer_ok": lr_ok,
              })

      if not results:
          mean_abs_diff = 0.0
          interpretation = "no_steps"
      else:
          mean_abs_diff = sum(r["abs_diff"] for r in results) / len(results)
          if mean_abs_diff < 0.01:
              interpretation = "numerically_equivalent"
          elif mean_abs_diff < 0.5:
              interpretation = "minor_drift"
          else:
              interpretation = "major_divergence"

      report = {
          "dataset": str(dataset_path),
          "n_episodes": len(lines),
          "n_steps": len(results),
          "mean_abs_diff": mean_abs_diff,
          "interpretation": interpretation,
          "degenerate_planner_rate": sum(1 for r in results if r["degenerate_planner"]) / max(1, len(results)),
          "degenerate_lr_rate": sum(1 for r in results if r["degenerate_lr"]) / max(1, len(results)),
          "lr_scorer_failure_rate": sum(1 for r in results if not r["lr_scorer_ok"]) / max(1, len(results)),
          "steps": results,
      }

      out_path = Path(args.out)
      out_path.parent.mkdir(parents=True, exist_ok=True)
      out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
      print(f"LR comparison report: {out_path}")
      print(f"  mean_abs_diff: {mean_abs_diff:.4f} ({interpretation})")
      return 0

  if __name__ == "__main__":
      sys.exit(main())
  ```

  Note: If `EvidenceFeatures.from_public_step()` or `EvidenceLikelihood` don't exist
  in lr_scorer.py, use the available public API. The script should gracefully handle
  import errors and mark lr_scorer_ok=False for those steps.

REQUIRED_TESTS: |
  tests/test_step4_lr_comparison.py — 4개:

  1. test_lr_comparison_script_emits_json
     - mock dataset; run main() with tmp out file; assert json exists + has "mean_abs_diff" key

  2. test_lr_scorer_receives_no_forbidden_metadata
     - The EvidenceFeatures input must not contain any field from FORBIDDEN_AGENT_FIELDS
     - Use visibility.py::FORBIDDEN_AGENT_FIELDS set and assert no key appears in features dict

  3. test_hypothesis_candidate_metadata_keys_subset_of_public_safe
     - LR scorer HypothesisCandidate fields are a subset of _PUBLIC_SAFE_METADATA_KEYS (lr_scorer.py:266)
     - No hidden label fields present

  4. test_lr_comparison_reports_degenerate_rate
     - Mock all steps with F_t_planner=0.0 → degenerate_planner_rate should be 1.0 in output

ACCEPTANCE_CRITERIA: |
  - pytest tests/test_step4_lr_comparison.py -q → 4/4 PASSED
  - scripts/audit_step4_lr_comparison.py --help exits 0 (or --dataset / dry run)
  - Active F_t path (frcg_agent.py, planner.py, planning/falsification.py) 미수정
  - lr_scorer.py read-only (no writes)
  - If lr_scorer imports fail, script handles gracefully (lr_scorer_ok=False)

COMMIT_MESSAGE: |
  feat(step4/task3): LR scorer comparison audit script

  B2 blocker: adds audit_step4_lr_comparison.py to compare plan_meta.F_t
  vs LikelihoodRatioFalsificationScorer F_t on same dataset without modifying
  active F_t path. Reports mean_abs_diff and interpretation.

  4 new tests in test_step4_lr_comparison.py.

STOP_CONDITION: |
  4 tests green, FILES_FORBIDDEN 미수정, active F_t path unchanged.
  Import error 시 graceful handling 확인 후 계속.
