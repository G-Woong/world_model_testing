"""Smoke test for planner interface (Session 11-13).

순수 import + checkpoint load + WorldModelAdapter API + 1~2 episode dry-run을 확인한다.
training/optimizer 호출 없음. ``torch.no_grad`` only.

사용 예:
    .\.venv\Scripts\python.exe scripts\check_planner_interface.py \
        --checkpoint outputs\wm_runs\wm_medium_full_v1\checkpoints\step_00030000.pt \
        --config configs\planner_eval_debug.yaml
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np
import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from falsifiable_regime_world_model.planner import (   # noqa: E402
    ActionSpaceSpec,
    BeliefState,
    ComputeAccountant,
    FRCWMPlanner,
    PlannerConfig,
    PlannerEvalConfig,
    PlannerState,
    PlannerTrace,
    ReactivePlanner,
    WorldModelAdapter,
    enumerate_action_candidates,
    sample_action_sequences,
)
from falsifiable_regime_world_model.planner.action_space import candidates_to_tensor  # noqa: E402
from falsifiable_regime_world_model.planner.config import (  # noqa: E402
    BaselinePlannerConfig,
    FRCPlannerConfig,
)
from falsifiable_regime_world_model.eval import run_episode  # noqa: E402
from falsifiable_regime_world_model.rg4f.config import RG4FConfig  # noqa: E402
from falsifiable_regime_world_model.rg4f.env import RG4FEnv  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True, type=str)
    p.add_argument("--wm-config", default="configs/wm_medium.yaml", type=str)
    p.add_argument("--variant", default="full_model", type=str)
    p.add_argument("--config", default=None, type=str,
                   help="optional planner_eval_debug.yaml — env config base only")
    p.add_argument("--device", default="auto", type=str)
    p.add_argument("--max-steps", type=int, default=20)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    print("=" * 78)
    print("[smoke] Session 11-13 planner interface smoke test")
    print("=" * 78)

    # ------------------------------------------------------------------
    # 1) checkpoint load
    # ------------------------------------------------------------------
    t0 = time.time()
    print(f"\n[1] load checkpoint: {args.checkpoint}")
    print(f"    wm_config={args.wm_config}  variant={args.variant}  device={args.device}")
    adapter = WorldModelAdapter.load_from_checkpoint(
        args.checkpoint,
        wm_config_path=args.wm_config,
        variant=args.variant,
        device=args.device,
    )
    elapsed = time.time() - t0
    print(f"    loaded in {elapsed:.2f}s")
    print(f"    has_regime_head      = {adapter.has_regime_head}")
    print(f"    has_change_point_head= {adapter.has_change_point_head}")
    print(f"    has_mismatch_head    = {adapter.has_mismatch_head}")
    print(f"    has_state_head       = {adapter.has_state_head}")
    print(f"    feature_dim          = {adapter.wm_config.feature_dim}")
    print(f"    device               = {adapter.device}")

    # ------------------------------------------------------------------
    # 2) build env (RG4FConfig default + small max_steps)
    # ------------------------------------------------------------------
    print(f"\n[2] build RG4FEnv (max_steps={args.max_steps})")
    base = {f.name: getattr(RG4FConfig(), f.name) for f in RG4FConfig.__dataclass_fields__.values()}
    base["episode_max_steps"] = int(args.max_steps)
    env_cfg = RG4FConfig.from_dict(base)
    env = RG4FEnv(env_cfg, seed=12345)
    obs, info = env.reset(seed=12345)
    print(f"    obs.local_grid.shape = {obs['local_grid'].shape}")
    print(f"    obs.scalar.shape     = {obs['scalar'].shape}")
    print(f"    obs.event_token      = {int(obs['event_token'])}")
    print(f"    info.true_regime     = {info['true_regime']}")

    # ------------------------------------------------------------------
    # 3) belief update (single step)
    # ------------------------------------------------------------------
    print("\n[3] adapter.update_belief (single step)")
    belief: BeliefState = adapter.update_belief(prev_belief=None, obs=obs, prev_action=None, step_index=0)
    print(f"    belief.h.shape = {tuple(belief.h.shape)}")
    print(f"    belief.z.shape = {tuple(belief.z.shape)}")
    print(f"    head keys      = {sorted(belief.head_outputs.keys())}")
    if "state_pred" in belief.head_outputs:
        print(f"    state_pred[0]  = {belief.head_outputs['state_pred'].detach().cpu().numpy().reshape(-1)[:5]}")

    # ------------------------------------------------------------------
    # 4) action enumeration / sampling
    # ------------------------------------------------------------------
    print("\n[4] action_space candidate generation")
    aspec = ActionSpaceSpec()
    cands = enumerate_action_candidates(aspec, horizon=5, action_mask=obs.get("action_mask"))
    print(f"    enumerate_action_candidates(H=5)  → {len(cands)} candidates")
    rng = np.random.default_rng(0)
    samples = sample_action_sequences(aspec, n_candidates=8, horizon=5, rng=rng, action_mask=obs.get("action_mask"))
    print(f"    sample_action_sequences(8, H=5)  → {len(samples)} candidates")
    arr = candidates_to_tensor(cands, n_samples=1)
    print(f"    candidates_to_tensor.shape       = {arr.shape}")

    # ------------------------------------------------------------------
    # 5) imagine_from_belief
    # ------------------------------------------------------------------
    print("\n[5] adapter.imagine_from_belief")
    rollout = adapter.imagine_from_belief(belief, arr, horizon=5, n_samples=1, n_candidates=arr.shape[0])
    print(f"    rollout.h.shape         = {tuple(rollout.h.shape)}")
    print(f"    rollout.z.shape         = {tuple(rollout.z.shape)}")
    print(f"    rollout.state_pred.shape= {tuple(rollout.state_pred.shape) if rollout.state_pred is not None else None}")
    print(f"    rollout.reward_pred.shape={tuple(rollout.reward_pred.shape) if rollout.reward_pred is not None else None}")
    val = rollout.candidate_value()
    print(f"    candidate_value         = {val.detach().cpu().numpy().tolist()}")
    score = adapter.score_rollout(rollout)
    print(f"    score_rollout (==value) = {score.detach().cpu().numpy().tolist()}")

    # ------------------------------------------------------------------
    # 6) imagine_alternative
    # ------------------------------------------------------------------
    print("\n[6] adapter.imagine_alternative (latent perturb)")
    alt = adapter.imagine_alternative(
        belief, arr, horizon=5, n_samples=1, n_candidates=arr.shape[0],
        latent_perturb_std=0.5, regime_topk_index=1,
    )
    val_alt = alt.candidate_value()
    print(f"    alt.candidate_value     = {val_alt.detach().cpu().numpy().tolist()}")
    diff = (val_alt - val).abs().mean().item()
    print(f"    |alt - cur| mean         = {diff:.4f}")

    # ------------------------------------------------------------------
    # 7) ReactivePlanner one-step decision
    # ------------------------------------------------------------------
    print("\n[7] ReactivePlanner.select_action")
    planner_cfg = PlannerConfig(horizon=5, candidate_action_count=8, sampling_seed=0)
    planner = ReactivePlanner(adapter=adapter, config=planner_cfg)
    state = PlannerState(
        belief=belief,
        accountant=ComputeAccountant(
            budget_total=planner_cfg.compute_budget_total,
            max_planning_calls=planner_cfg.max_planning_calls_per_episode,
        ),
    )
    state.accountant.begin_step()
    decision = planner.select_action(env_obs=obs, belief=belief, planner_state=state)
    print(f"    action={decision.action}  mode={decision.decision_mode}")
    print(f"    used_planning={decision.used_planning} planning_calls={decision.planning_calls}")
    print(f"    rollout_steps={decision.rollout_steps} candidate_count={decision.candidate_count}")

    # ------------------------------------------------------------------
    # 8) FRCWMPlanner one-step decision
    # ------------------------------------------------------------------
    print("\n[8] FRCWMPlanner.select_action")
    frc_planner = FRCWMPlanner(
        adapter=adapter,
        config=PlannerConfig(horizon=5, candidate_action_count=8, sampling_seed=0,
                             enable_alternative_rollout=True, num_alternative_samples=4),
        frc_config=FRCPlannerConfig(),
        baseline_config=BaselinePlannerConfig(),
    )
    state2 = PlannerState(
        belief=belief,
        accountant=ComputeAccountant(budget_total=0, max_planning_calls=1000),
        falsification_window=5,
    )
    state2.accountant.begin_step()
    decision2 = frc_planner.select_action(env_obs=obs, belief=belief, planner_state=state2)
    print(f"    action={decision2.action}  mode={decision2.decision_mode}")
    print(f"    used_planning={decision2.used_planning}  planning_calls={decision2.planning_calls}")
    print(f"    rollout_steps={decision2.rollout_steps} candidate_count={decision2.candidate_count}")
    rsn = decision2.decision_reason
    print(f"    falsification_score={rsn.get('falsification_score', 0.0):.3f}")
    print(f"    action_relevance_max={rsn.get('action_relevance_max', 0.0):.3f}")
    print(f"    stage={rsn.get('stage', 'n/a')}")

    # ------------------------------------------------------------------
    # 9) Run a tiny dry-run episode (2 episodes) with FRC
    # ------------------------------------------------------------------
    print(f"\n[9] dry-run 1 episode with FRCWMPlanner (max_steps={args.max_steps})")
    env2 = RG4FEnv(env_cfg, seed=4242)
    trace = PlannerTrace(
        episode_id="smoke_frc_001",
        split="test_id", model_name="full", planner_name="ours_frc",
        seed=4242, episode_index=0,
    )
    summary = run_episode(
        env=env2,
        planner=frc_planner,
        adapter=adapter,
        planner_config=frc_planner.config,
        trace=trace,
        seed=4242,
        max_steps=int(args.max_steps),
    )
    print(f"    episode_return  = {summary['episode_return']:.3f}")
    print(f"    episode_length  = {summary['episode_length']}")
    print(f"    completed_tasks = {summary['completed_tasks']}")
    print(f"    planning_calls  = {summary['planning_calls']}")
    print(f"    rollout_steps   = {summary['rollout_steps']}")
    print(f"    wallclock       = {summary['wallclock_seconds']:.2f}s")

    print("\n[smoke] all checks PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
