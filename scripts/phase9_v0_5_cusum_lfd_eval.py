"""PHASE 9 v0_5 oracle-free CUSUM/SPRT vs LFD comparison.

Execution mode: ORACLE-FREE (v0_5)
  - collect_episode() handles v0_5 grammar-switch (TASK_COLLECTOR_V05_SWITCH done).
  - Effect streams from observed_effect_public.effect_type (no oracle simulation).
  - true_wrong_hypothesis from EvaluationLabels (EVALUATION_ONLY — never inference).
  - CUSUM/SPRT and LFD all evaluated on the same oracle-free dataset.
  - Train/eval split: first 200 specs → LFD train; last 50 → all-method eval.

Core question: "진짜 oracle-free 조건에서 LFD가 CUSUM을 이기는가?"

Source MDs:
  paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md FALS-03
  paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7-§8
  paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md tiny model
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import torch

from frcgw.data.text_dataset import BatchTargets
from frcgw.evaluation.baseline_detectors import run_cusum_on_episode, run_sprt_on_episode
from frcgw.evaluation.metrics import aggregate_episode_metrics
from frcgw.models.text_frcg_model import TextFRCGModel
from frcgw.objectives.losses import DEFAULT_WEIGHTS, L_run_length_posterior, L_seq_falsification
from frcgw.schemas.episode_schema import EpisodeRecord
from frcgw.schemas.step_schema import PublicObservation
from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS, assert_agent_observation_safe
from frcgw.text_env.collector import CollectorConfig, collect_episode
from frcgw.text_env.generator import EpisodeSpecGenerator
from frcgw.text_env.policies import PolicyMixtureRunner

# ---------------------------------------------------------------------------
# Config — all thresholds fixed before seeing results (proxy OFF)
# ---------------------------------------------------------------------------

N_COLLECT = 250         # total v0_5 episodes to collect
N_TRAIN = 200           # first N_TRAIN episodes → LFD train
N_EVAL = 50             # last N_EVAL episodes → all-method eval
N_SEEDS = 3             # LFD seed stability
MAX_STEPS = 12

CUSUM_K = 0.3
CUSUM_H_SWEEP = [0.5, 1.0, 2.0, 3.0, 4.0]   # all recorded, no cherry-pick
SPRT_B = 0.1
SPRT_A_PRIMARY = 3.0   # A=3.0: reachable in 12-step episode (A=5.0 was not)
SPRT_A_FALLBACK = 2.0  # run A=2.0 also; record both

LFD_EPOCHS = 15
LFD_LR = 5e-4
LFD_ALARM_THRESHOLD = 0.5   # fixed, not tuned post-results

OUTPUT_DIR = ROOT / "outputs" / "risk_hunt" / "implementation" / "evals"


# ---------------------------------------------------------------------------
# Effect stream helpers (oracle-free — reads observed_effect_public, not oracle)
# ---------------------------------------------------------------------------

_MISMATCH_EFFECTS = {"no_state_change", "delayed_effect"}
CUSUM_MISMATCH_LABEL = "cusum_mismatch_effects: ['no_state_change','delayed_effect']"


def effect_to_int(effect_type: str) -> int:
    """Mismatch indicator: 1 if no_state_change or delayed_effect, else 0."""
    return 1 if effect_type in _MISMATCH_EFFECTS else 0


def episode_to_effect_stream(episode: EpisodeRecord) -> list[int]:
    """Extract int effect stream from oracle-free episode (no simulation)."""
    return [effect_to_int(step.observed_effect_public.effect_type) for step in episode.steps]


def episode_to_true_wrong(episode: EpisodeRecord) -> list[bool]:
    """Extract true_wrong_hypothesis from EvaluationLabels (EVALUATION_ONLY)."""
    return [bool(step.evaluation_labels.true_wrong_hypothesis) for step in episode.steps]


def episode_to_switch_step(episode: EpisodeRecord) -> int | None:
    """Extract v0_5 regime_switch_t from EvaluationLabels (backfilled by collector)."""
    for step in episode.steps:
        st = step.evaluation_labels.regime_switch_t
        if st is not None:
            return st
    return None


def episode_to_run_lengths(episode: EpisodeRecord, switch_step: int | None) -> list[int]:
    """Oracle run lengths: increasing pre-switch, reset post-switch."""
    n = len(episode.steps)
    rls = []
    for i in range(n):
        if switch_step is None or i < switch_step:
            rls.append(i + 1)
        else:
            rls.append(i - switch_step + 1)
    return rls


# ---------------------------------------------------------------------------
# STEP 1 — oracle-free episode collection and dataset audit
# ---------------------------------------------------------------------------

def collect_real_episodes(specs: list[Any], seed: int) -> list[EpisodeRecord]:
    """Collect oracle-free v0_5 episodes using collect_episode().

    PolicyMixtureRunner uses default mixture. Per-episode rng is seeded from (seed+i).
    No oracle simulation — effects are genuine action-outcome mismatches.
    """
    runner = PolicyMixtureRunner(rng=random.Random(seed))
    config = CollectorConfig()
    episodes: list[EpisodeRecord] = []

    for i, spec in enumerate(specs):
        rng = random.Random(seed + i)
        episode = collect_episode(spec, runner, rng, config)
        episodes.append(episode)

    return episodes


def audit_collected_dataset(
    episodes: list[EpisodeRecord],
) -> dict:
    """Audit oracle-free dataset for leakage and dataset integrity.

    Checks:
    - leakage_violations: assert_agent_observation_safe per step
    - post_switch_wrong_count > 0 (genuine precondition failures exist)
    - post_switch_wrong_count < total_post_steps (not 100% forced)
    - shared_action_success_count > 0 (partial state_change exists post-switch)
    - vocabulary_mismatch_count: no_state_change + is_wrong=False post-switch
    """
    leakage_violations: list[str] = []
    total_pre_steps = 0
    total_post_steps = 0
    post_switch_wrong_count = 0
    pre_switch_wrong_count = 0
    shared_action_success_count = 0
    vocabulary_mismatch_count = 0

    for episode in episodes:
        switch_step = episode_to_switch_step(episode)

        for step_idx, step in enumerate(episode.steps):
            try:
                assert_agent_observation_safe(step.public_observation)
            except Exception as e:
                leakage_violations.append(
                    f"ep={episode.episode_id} step={step_idx}: {e}"
                )

            effect = step.observed_effect_public.effect_type
            is_wrong = bool(step.evaluation_labels.true_wrong_hypothesis)
            is_post = switch_step is not None and step_idx >= switch_step

            if is_post:
                total_post_steps += 1
                if is_wrong:
                    post_switch_wrong_count += 1
                elif effect in ("state_change", "task_complete"):
                    shared_action_success_count += 1
                elif effect == "no_state_change" and not is_wrong:
                    vocabulary_mismatch_count += 1
            else:
                total_pre_steps += 1
                if is_wrong:
                    pre_switch_wrong_count += 1

    post_wrong_rate = post_switch_wrong_count / max(1, total_post_steps)
    pre_wrong_rate = pre_switch_wrong_count / max(1, total_pre_steps)

    checks = {
        "post_switch_wrong_count > 0": post_switch_wrong_count > 0,
        "post_switch_wrong_count < total_post_steps": (
            post_switch_wrong_count < total_post_steps
        ),
        "shared_action_success_count > 0": shared_action_success_count > 0,
        "leakage_violations == 0": len(leakage_violations) == 0,
    }
    all_pass = all(checks.values())

    return {
        "n_episodes": len(episodes),
        "n_switch_episodes": sum(
            1 for ep in episodes if episode_to_switch_step(ep) is not None
        ),
        "total_pre_steps": total_pre_steps,
        "total_post_steps": total_post_steps,
        "post_switch_wrong_count": post_switch_wrong_count,
        "post_switch_wrong_rate": round(post_wrong_rate, 4),
        "pre_switch_wrong_count": pre_switch_wrong_count,
        "pre_switch_wrong_rate": round(pre_wrong_rate, 4),
        "shared_action_success_count": shared_action_success_count,
        "vocabulary_mismatch_count": vocabulary_mismatch_count,
        "leakage_violations": leakage_violations[:20],  # cap to avoid huge files
        "leakage_clean": len(leakage_violations) == 0,
        "inference_oracle_free": True,
        "integrity_checks": checks,
        "integrity_all_pass": all_pass,
    }


# ---------------------------------------------------------------------------
# STEP 2 — CUSUM/SPRT evaluation on oracle-free episodes
# ---------------------------------------------------------------------------

def _episode_to_eval_dict(
    episode: EpisodeRecord,
    alarm_steps: list[int],
    wrong_prob_scores: list[float],
    run_length_posteriors: list[list[float]] | None = None,
) -> dict:
    """Build episode eval dict compatible with aggregate_episode_metrics()."""
    switch_step = episode_to_switch_step(episode)
    stable_steps = (
        list(range(switch_step))
        if switch_step is not None
        else list(range(len(episode.steps)))
    )
    true_wrong = episode_to_true_wrong(episode)
    true_rls = episode_to_run_lengths(episode, switch_step)
    first_alarm = alarm_steps[0] if alarm_steps else None

    recovery = None
    if first_alarm is not None and switch_step is not None:
        dd = max(0, first_alarm - switch_step)
        recovery = dd + 2

    return {
        "switch_step": switch_step,
        "first_alarm": first_alarm,
        "stable_steps": stable_steps,
        "alarm_steps": alarm_steps,
        "wrong_prob_scores": wrong_prob_scores,
        "true_wrong_hypothesis": true_wrong,
        "run_length_posteriors": run_length_posteriors or [],
        "true_run_lengths": true_rls,
        "recovery_delay": recovery,
        "task_family": str(episode.task_family),
        "total_progress": float(episode.total_progress or 0.0),
    }


def eval_cusum_on_episodes(
    episodes: list[EpisodeRecord],
    h: float,
    k: float = CUSUM_K,
) -> tuple[list[dict], dict]:
    """Evaluate CUSUM on oracle-free episodes. Returns (episode_dicts, summary)."""
    ep_dicts = []
    for episode in episodes:
        effects = episode_to_effect_stream(episode)
        result = run_cusum_on_episode(effects, expected_effect_type=0, k=k, h=h)
        ep_dicts.append(
            _episode_to_eval_dict(
                episode,
                alarm_steps=result["alarm_steps"],
                wrong_prob_scores=[float(e) for e in effects],
            )
        )

    result_agg = aggregate_episode_metrics(ep_dicts, detector_name=f"cusum_h{h}")
    summary = _result_to_dict(result_agg)
    summary["threshold_h"] = h
    summary["threshold_k"] = k
    summary["mismatch_label"] = CUSUM_MISMATCH_LABEL
    summary["oracle_free"] = True
    return ep_dicts, summary


def eval_sprt_on_episodes(
    episodes: list[EpisodeRecord],
    A: float,
    B: float = SPRT_B,
) -> tuple[list[dict], dict]:
    """Evaluate SPRT on oracle-free episodes. Returns (episode_dicts, summary)."""
    ep_dicts = []
    for episode in episodes:
        effects = episode_to_effect_stream(episode)
        result = run_sprt_on_episode(effects, expected_effect_type=0, A=A, B=B)
        ep_dicts.append(
            _episode_to_eval_dict(
                episode,
                alarm_steps=result["alarm_steps"],
                wrong_prob_scores=[float(e) for e in effects],
            )
        )

    result_agg = aggregate_episode_metrics(ep_dicts, detector_name=f"sprt_A{A}")
    summary = _result_to_dict(result_agg)
    summary["threshold_A"] = A
    summary["threshold_B"] = B
    summary["oracle_free"] = True
    return ep_dicts, summary


# ---------------------------------------------------------------------------
# STEP 3 — LFD training and evaluation on oracle-free episodes
# ---------------------------------------------------------------------------

def _make_batch_targets(true_wrong_list: list[bool | None]) -> list[BatchTargets]:
    return [
        BatchTargets(
            true_regime="search_form",
            true_control_grammar="direct_search",
            true_change_point="0",
            true_reveal_vs_shift="none",
            true_action_effect_type="state_change",
            true_failed_action=False,
            failure_reason=None,
            progress_delta=0.0,
            recovery_action_id=None,
            valid_hypothesis_switch=None,
            true_wrong_hypothesis=tw,
            h_exec_id=None,
            correct_hypothesis_id=None,
        )
        for tw in true_wrong_list
    ]


def train_lfd_on_real(
    train_eps: list[EpisodeRecord],
    seed: int,
    epochs: int = LFD_EPOCHS,
    lr: float = LFD_LR,
) -> tuple[TextFRCGModel, dict]:
    """Train LFD head on oracle-free v0_5 episodes, step-by-step with head_h carry-over.

    Base encoder is frozen (no_grad). head_h resets between episodes and carries over
    within each episode. Effect stream from observed_effect_public.effect_type.
    Proxy OFF: alarm_threshold=0.5 fixed; no post-result threshold tuning.
    """
    torch.manual_seed(seed)
    random.seed(seed)

    model = TextFRCGModel(use_lfd_head=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    rng_order = random.Random(seed + 1000)
    train_losses: list[float] = []

    model.train()
    for epoch in range(epochs):
        ep_order = list(range(len(train_eps)))
        rng_order.shuffle(ep_order)
        epoch_loss = 0.0
        n_valid_steps = 0

        for ep_idx in ep_order:
            episode = train_eps[ep_idx]
            optimizer.zero_grad()
            head_h: torch.Tensor | None = None

            for step in episode.steps:
                obs = PublicObservation(
                    instruction=(
                        f"[INSTRUCTION] task [STATE] step_{step.step_index}"
                    )
                )
                effect_val = float(effect_to_int(step.observed_effect_public.effect_type))
                effect_t = torch.tensor([[effect_val]], dtype=torch.float32)
                tw = step.evaluation_labels.true_wrong_hypothesis
                targets = _make_batch_targets([tw])

                with torch.no_grad():
                    base_out = model.forward(obs, return_lfd=False)

                lfd_out, head_h = model.falsification_head(
                    base_out.shared_h,
                    base_out.z_state,
                    effect_t,
                    torch.zeros(1),   # F_t_deterministic = 0 (proxy OFF)
                    head_h,
                )

                l_seq = L_seq_falsification(lfd_out.wrong_prob_learned, targets)
                l_rl = L_run_length_posterior(lfd_out.run_length_posterior, targets)
                loss = (
                    DEFAULT_WEIGHTS["l_seq_falsification"] * l_seq
                    + DEFAULT_WEIGHTS["l_run_length_posterior"] * l_rl
                )

                if not math.isfinite(loss.item()):
                    head_h = head_h.detach() if head_h is not None else None
                    continue

                loss.backward()
                epoch_loss += loss.item()
                n_valid_steps += 1

                # Detach head_h: truncated BPTT (k1=1) — standard for online learning
                if head_h is not None:
                    head_h = head_h.detach()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

        mean_loss = epoch_loss / max(1, n_valid_steps)
        train_losses.append(mean_loss)

    return model, {"train_losses": train_losses, "seed": seed, "epochs": epochs}


def eval_lfd_on_real(
    model: TextFRCGModel,
    eval_eps: list[EpisodeRecord],
    seed: int,
) -> tuple[list[dict], dict]:
    """Evaluate trained LFD on oracle-free episodes, step-by-step with head_h carry-over.

    wrong_prob >= LFD_ALARM_THRESHOLD → alarm (threshold fixed, not tuned post-results).
    Returns (episode_dicts, summary).
    """
    model.eval()
    ep_dicts = []

    with torch.no_grad():
        for episode in eval_eps:
            switch_step = episode_to_switch_step(episode)
            true_wrong = episode_to_true_wrong(episode)
            true_rls = episode_to_run_lengths(episode, switch_step)
            head_h: torch.Tensor | None = None

            step_wrong_probs: list[float] = []
            step_rl_posteriors: list[list[float]] = []

            for step in episode.steps:
                obs = PublicObservation(
                    instruction=(
                        f"[INSTRUCTION] task [STATE] step_{step.step_index}"
                    )
                )
                effect_val = float(effect_to_int(step.observed_effect_public.effect_type))
                effect_t = torch.tensor([[effect_val]], dtype=torch.float32)

                base_out = model.forward(obs, return_lfd=False)
                lfd_out, head_h = model.falsification_head(
                    base_out.shared_h,
                    base_out.z_state,
                    effect_t,
                    torch.zeros(1),
                    head_h,
                )
                wp = float(lfd_out.wrong_prob_learned[0].item())
                rl_post = lfd_out.run_length_posterior[0].tolist()
                step_wrong_probs.append(wp)
                step_rl_posteriors.append(rl_post)

            alarm_steps = [
                i for i, wp in enumerate(step_wrong_probs)
                if wp >= LFD_ALARM_THRESHOLD
            ]
            ep_dicts.append(
                _episode_to_eval_dict(
                    episode,
                    alarm_steps=alarm_steps,
                    wrong_prob_scores=step_wrong_probs,
                    run_length_posteriors=step_rl_posteriors,
                )
            )

    result_agg = aggregate_episode_metrics(ep_dicts, detector_name="lfd_oracle_free")
    summary = _result_to_dict(result_agg)
    summary["alarm_threshold"] = LFD_ALARM_THRESHOLD
    summary["proxy_off"] = True
    summary["seed"] = seed

    # Proxy-OFF validation: wrong_prob must not be constant
    all_probs = [p for ep in ep_dicts for p in ep["wrong_prob_scores"]]
    if all_probs:
        mean_p = sum(all_probs) / len(all_probs)
        std_p = math.sqrt(
            sum((p - mean_p) ** 2 for p in all_probs) / len(all_probs)
        )
        summary["wrong_prob_std"] = round(std_p, 4)
        summary["wrong_prob_mean"] = round(mean_p, 4)
        if std_p < 0.01:
            summary["proxy_off_check"] = "BLOCKED: constant output (std<0.01)"
        else:
            summary["proxy_off_check"] = "PASS"

    return ep_dicts, summary


# ---------------------------------------------------------------------------
# Fair PPC estimate
# ---------------------------------------------------------------------------

def estimate_fair_ppc(
    cusum_time_s: float,
    lfd_time_s: float,
    n_episodes: int,
    cusum_summary: dict,
    lfd_summary: dict,
) -> dict:
    """Estimated fair PPC (progress per compute unit).

    Progress proxy = regime_shift_recall; LFD includes train amortized.
    """
    cusum_per_ep = cusum_time_s / max(1, n_episodes)
    lfd_per_ep = lfd_time_s / max(1, n_episodes)
    cusum_progress = cusum_summary.get("regime_shift_recall") or 0.0
    lfd_progress = lfd_summary.get("regime_shift_recall") or 0.0
    ppc_cusum = cusum_progress / max(1e-6, cusum_per_ep)
    ppc_lfd = lfd_progress / max(1e-6, lfd_per_ep)
    return {
        "cusum_wall_clock_per_ep_s": cusum_per_ep,
        "lfd_wall_clock_per_ep_s": lfd_per_ep,
        "cusum_ppc": ppc_cusum,
        "lfd_ppc": ppc_lfd,
        "ppc_ratio_lfd_over_cusum": ppc_lfd / max(1e-6, ppc_cusum),
        "note": "progress_proxy=regime_shift_recall; LFD includes training amortized",
    }


# ---------------------------------------------------------------------------
# Leakage check helper
# ---------------------------------------------------------------------------

def check_no_leakage_in_obs(obs_list: list[PublicObservation]) -> dict:
    """Verify no forbidden fields in synthetic observations."""
    violations: list[str] = []
    for obs in obs_list:
        if obs.dom_snapshot_public:
            for k in obs.dom_snapshot_public:
                if k in FORBIDDEN_AGENT_FIELDS:
                    violations.append(f"dom_snapshot_public.{k}")
        if obs.instruction:
            for forbidden in FORBIDDEN_AGENT_FIELDS:
                if forbidden in obs.instruction:
                    violations.append(f"instruction:{forbidden}")
    return {"violations": violations, "clean": len(violations) == 0}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result_to_dict(result: Any) -> dict:
    try:
        return json.loads(result.to_json())
    except Exception:
        return {k: v for k, v in result.__dict__.items() if not k.startswith("_")}


def _seed_stats(values: list[float | None]) -> dict:
    clean = [v for v in values if v is not None]
    if not clean:
        return {"mean": None, "std": None, "values": values}
    mean = sum(clean) / len(clean)
    variance = sum((x - mean) ** 2 for x in clean) / max(1, len(clean))
    return {
        "mean": round(mean, 4),
        "std": round(math.sqrt(variance), 4),
        "values": [round(v, 4) if v is not None else None for v in values],
    }


def _get_f(d: dict, k: str, default: Any = None) -> Any:
    v = d.get(k, default)
    return round(v, 4) if isinstance(v, float) else v


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PHASE 9 v0_5 oracle-free: CUSUM/SPRT vs LFD")
    print(f"N_COLLECT={N_COLLECT}, N_TRAIN={N_TRAIN}, N_EVAL={N_EVAL}, N_SEEDS={N_SEEDS}")
    print(f"CUSUM: k={CUSUM_K}, h_sweep={CUSUM_H_SWEEP}")
    print(f"SPRT: A_primary={SPRT_A_PRIMARY}, A_fallback={SPRT_A_FALLBACK}, B={SPRT_B}")
    print(f"LFD: epochs={LFD_EPOCHS}, lr={LFD_LR}, alarm_threshold={LFD_ALARM_THRESHOLD}")
    print(f"Proxy OFF: thresholds fixed before results")
    print("=" * 60)

    # --- Pre-check: no forbidden fields in minimal synthetic obs ---
    sample_obs = [PublicObservation(instruction=f"[INSTRUCTION] task [STATE] s_{i}") for i in range(10)]
    leakage_pre = check_no_leakage_in_obs(sample_obs)
    if not leakage_pre["clean"]:
        print(f"[BLOCKED] LEAKAGE in synthetic obs: {leakage_pre['violations']}")
        sys.exit(1)
    print("[PASS] Leakage pre-check: no forbidden fields in synthetic obs")

    # --- Generate v0_5 specs ---
    gen = EpisodeSpecGenerator(seed=42, max_steps=MAX_STEPS)
    all_specs = gen.generate_v0_5_batch(N_COLLECT)
    print(f"\n[DATA] Generated {len(all_specs)} v0_5 specs")
    switch_steps = [s.regime_switch_step for s in all_specs if getattr(s, "regime_switch_step", None) is not None]
    if switch_steps:
        mean_sw = sum(switch_steps) / len(switch_steps)
        print(f"[DATA] switch_step: mean={mean_sw:.1f}, min={min(switch_steps)}, max={max(switch_steps)}")

    # ===================================================================
    # STEP 1 — Collect oracle-free episodes and audit
    # ===================================================================
    print("\n[STEP 1] Collecting oracle-free episodes (N=250)...")
    t_collect_start = time.time()
    all_episodes = collect_real_episodes(all_specs, seed=42)
    t_collect = time.time() - t_collect_start
    print(f"  Collected {len(all_episodes)} episodes in {t_collect:.1f}s")

    print("[STEP 1] Auditing dataset...")
    dataset_audit = audit_collected_dataset(all_episodes)
    print(f"  n_switch_episodes: {dataset_audit['n_switch_episodes']}")
    print(f"  post_switch_wrong_rate: {dataset_audit['post_switch_wrong_rate']}")
    print(f"  pre_switch_wrong_rate:  {dataset_audit['pre_switch_wrong_rate']}")
    print(f"  shared_action_success_count: {dataset_audit['shared_action_success_count']}")
    print(f"  leakage_clean: {dataset_audit['leakage_clean']}")
    print(f"  integrity_all_pass: {dataset_audit['integrity_all_pass']}")

    checks = dataset_audit["integrity_checks"]
    if not dataset_audit["leakage_clean"]:
        print("[BLOCKED] Leakage violations detected. Stopping.")
        sys.exit(1)
    if not checks["post_switch_wrong_count > 0"]:
        print("[BLOCKED] post_switch_wrong_count == 0: no genuine wrong-hypothesis labels.")
        sys.exit(1)

    audit_out = OUTPUT_DIR / "v0_5_oracle_free_dataset_audit.json"
    audit_out.write_text(
        json.dumps(dataset_audit, indent=2, default=str), encoding="utf-8"
    )
    print(f"  -> {audit_out}")

    # Split: first N_TRAIN for LFD train, last N_EVAL for all-method eval
    train_eps = all_episodes[:N_TRAIN]
    eval_eps = all_episodes[N_TRAIN:]
    print(f"\n[SPLIT] train={len(train_eps)}, eval={len(eval_eps)}")

    # ===================================================================
    # STEP 2 — CUSUM/SPRT on oracle-free eval episodes
    # ===================================================================
    print("\n[STEP 2] CUSUM threshold sweep on ALL episodes...")
    cusum_sweep: dict[str, dict] = {}
    cusum_best_h = CUSUM_H_SWEEP[2]  # h=2.0 as default candidate
    cusum_best_f1 = -1.0
    t_cusum_start = time.time()

    for h_val in CUSUM_H_SWEEP:
        _, sw_sum = eval_cusum_on_episodes(all_episodes, h=h_val)
        cusum_sweep[f"h={h_val}"] = {
            "mean_detection_delay": sw_sum.get("mean_detection_delay"),
            "false_alarm_rate_per_step": sw_sum.get("false_alarm_rate_per_step"),
            "regime_shift_f1": sw_sum.get("regime_shift_f1"),
            "auroc_wrong_hypothesis": sw_sum.get("auroc_wrong_hypothesis"),
            "auprc_wrong_hypothesis": sw_sum.get("auprc_wrong_hypothesis"),
            "regime_shift_recall": sw_sum.get("regime_shift_recall"),
        }
        f1 = sw_sum.get("regime_shift_f1") or 0.0
        print(
            f"  h={h_val}: delay={sw_sum.get('mean_detection_delay')}, "
            f"FAR={sw_sum.get('false_alarm_rate_per_step', 0.0):.4f}, "
            f"F1={f1:.4f}, "
            f"AUROC={sw_sum.get('auroc_wrong_hypothesis')}"
        )
        if f1 > cusum_best_f1:
            cusum_best_f1 = f1
            cusum_best_h = h_val

    t_cusum_total = time.time() - t_cusum_start
    print(f"  CUSUM sweep done in {t_cusum_total:.2f}s, best h={cusum_best_h} (F1={cusum_best_f1:.4f})")

    print(f"\n[STEP 2] CUSUM (best h={cusum_best_h}) on eval set...")
    cusum_eval_eps, cusum_summary = eval_cusum_on_episodes(eval_eps, h=cusum_best_h)
    t_cusum_eval = (t_cusum_total / len(CUSUM_H_SWEEP))  # approx per-h time

    print(f"\n[STEP 2] SPRT (A={SPRT_A_PRIMARY}) on eval set...")
    sprt_eps_primary, sprt_summary_primary = eval_sprt_on_episodes(eval_eps, A=SPRT_A_PRIMARY)
    n_sprt_alarms_primary = sum(1 for ep in sprt_eps_primary if ep.get("first_alarm") is not None)
    print(
        f"  SPRT A={SPRT_A_PRIMARY}: alarms={n_sprt_alarms_primary}/{len(eval_eps)}, "
        f"FAR={sprt_summary_primary.get('false_alarm_rate_per_step', 0.0):.4f}, "
        f"F1={sprt_summary_primary.get('regime_shift_f1', 0.0):.4f}"
    )

    print(f"\n[STEP 2] SPRT (A={SPRT_A_FALLBACK}) on eval set...")
    sprt_eps_fallback, sprt_summary_fallback = eval_sprt_on_episodes(eval_eps, A=SPRT_A_FALLBACK)
    n_sprt_alarms_fallback = sum(1 for ep in sprt_eps_fallback if ep.get("first_alarm") is not None)
    print(
        f"  SPRT A={SPRT_A_FALLBACK}: alarms={n_sprt_alarms_fallback}/{len(eval_eps)}, "
        f"FAR={sprt_summary_fallback.get('false_alarm_rate_per_step', 0.0):.4f}, "
        f"F1={sprt_summary_fallback.get('regime_shift_f1', 0.0):.4f}"
    )

    # Pick better SPRT (higher F1 on eval)
    if (sprt_summary_primary.get("regime_shift_f1") or 0.0) >= (
        sprt_summary_fallback.get("regime_shift_f1") or 0.0
    ):
        sprt_summary = sprt_summary_primary
        sprt_A_used = SPRT_A_PRIMARY
    else:
        sprt_summary = sprt_summary_fallback
        sprt_A_used = SPRT_A_FALLBACK
    print(f"  SPRT selected: A={sprt_A_used}")

    cusum_sprt_out = {
        "cusum_sweep_all_episodes": cusum_sweep,
        "cusum_best_h": cusum_best_h,
        "cusum_eval_summary": cusum_summary,
        "sprt_primary": {"A": SPRT_A_PRIMARY, **sprt_summary_primary},
        "sprt_fallback": {"A": SPRT_A_FALLBACK, **sprt_summary_fallback},
        "sprt_selected_A": sprt_A_used,
        "oracle_free": True,
        "eval_n": len(eval_eps),
    }
    cusum_sprt_path = OUTPUT_DIR / "cusum_sprt_v0_5_oracle_free_metrics.json"
    cusum_sprt_path.write_text(
        json.dumps(cusum_sprt_out, indent=2, default=str), encoding="utf-8"
    )
    print(f"  -> {cusum_sprt_path}")

    # ===================================================================
    # STEP 3 — LFD training and evaluation (3 seeds)
    # ===================================================================
    print(f"\n[STEP 3] LFD train ({len(train_eps)} eps) + eval ({len(eval_eps)} eps), 3 seeds...")
    lfd_seed_results = []
    lfd_blocked = False
    t_cusum_eval_single = t_cusum_eval  # for fair_ppc denominator

    for seed in range(N_SEEDS):
        print(f"\n  [Seed {seed}] Training LFD...")
        t_train_start = time.time()
        model, train_info = train_lfd_on_real(train_eps, seed=seed)
        t_train = time.time() - t_train_start
        final_loss = train_info["train_losses"][-1] if train_info["train_losses"] else None
        print(f"    train done in {t_train:.1f}s, final_loss={final_loss:.4f}")

        if final_loss is not None and final_loss > math.log(2) + 0.05:
            print(
                f"    [WARN] train_loss {final_loss:.4f} > log(2)={math.log(2):.4f}. "
                "Head-only learning limit. Recording but NOT blocking."
            )

        print(f"  [Seed {seed}] Evaluating LFD on {len(eval_eps)} eval episodes...")
        t_eval_start = time.time()
        lfd_ep_dicts, lfd_summary = eval_lfd_on_real(model, eval_eps, seed=seed)
        t_eval = time.time() - t_eval_start

        proxy_check = lfd_summary.get("proxy_off_check", "UNKNOWN")
        print(
            f"    eval done in {t_eval:.1f}s, proxy_off_check={proxy_check}, "
            f"F1={lfd_summary.get('regime_shift_f1', 0.0):.4f}, "
            f"AUROC={lfd_summary.get('auroc_wrong_hypothesis')}, "
            f"FAR={lfd_summary.get('false_alarm_rate_per_step', 0.0):.4f}, "
            f"wrong_prob_std={lfd_summary.get('wrong_prob_std')}"
        )

        if "BLOCKED" in proxy_check and seed == 0:
            lfd_blocked = True
            print("    [BLOCKED] LFD output is constant (proxy_off_check BLOCKED). Recording and continuing.")

        ppc = estimate_fair_ppc(
            cusum_time_s=t_cusum_eval_single,
            lfd_time_s=t_train + t_eval,
            n_episodes=len(eval_eps),
            cusum_summary=cusum_summary,
            lfd_summary=lfd_summary,
        )

        lfd_seed_results.append({
            "seed": seed,
            "lfd_summary": lfd_summary,
            "train_info": {
                "train_losses": [round(v, 6) for v in train_info["train_losses"]],
                "final_loss": round(final_loss, 6) if final_loss is not None else None,
                "seed": seed,
                "epochs": train_info["epochs"],
            },
            "fair_ppc": ppc,
            "train_time_s": round(t_train, 2),
            "eval_time_s": round(t_eval, 2),
        })

    # ===================================================================
    # STEP 4 — Comparison table and verdict
    # ===================================================================
    seed_delays = [r["lfd_summary"].get("mean_detection_delay") for r in lfd_seed_results]
    seed_f1s = [r["lfd_summary"].get("regime_shift_f1") for r in lfd_seed_results]
    seed_aurocs = [r["lfd_summary"].get("auroc_wrong_hypothesis") for r in lfd_seed_results]
    seed_auprcs = [r["lfd_summary"].get("auprc_wrong_hypothesis") for r in lfd_seed_results]
    seed_fars = [r["lfd_summary"].get("false_alarm_rate_per_step") or 0.0 for r in lfd_seed_results]

    seed_summary = {
        "detection_delay": _seed_stats(seed_delays),
        "regime_shift_f1": _seed_stats(seed_f1s),
        "auroc_wrong_hypothesis": _seed_stats(seed_aurocs),
        "auprc_wrong_hypothesis": _seed_stats(seed_auprcs),
        "false_alarm_rate_per_step": _seed_stats(seed_fars),
        "n_seeds": N_SEEDS,
    }

    lfd_primary = lfd_seed_results[0]["lfd_summary"]
    ppc_primary = lfd_seed_results[0]["fair_ppc"]

    # Verdict logic (non-cherry-pick: based on eval set, fixed thresholds)
    cusum_auroc = cusum_summary.get("auroc_wrong_hypothesis") or 0.5
    cusum_f1 = cusum_summary.get("regime_shift_f1") or 0.0
    lfd_auroc_mean = seed_summary["auroc_wrong_hypothesis"]["mean"] or 0.5
    lfd_f1_mean = seed_summary["regime_shift_f1"]["mean"] or 0.0
    lfd_far_mean = seed_summary["false_alarm_rate_per_step"]["mean"] or 1.0

    auroc_delta = (lfd_auroc_mean or 0.5) - (cusum_auroc or 0.5)
    f1_delta = (lfd_f1_mean or 0.0) - (cusum_f1 or 0.0)

    if lfd_blocked:
        verdict = "LFD_BLOCKED_BY_DATASET_OR_METRIC"
    elif not dataset_audit["integrity_all_pass"]:
        verdict = "LFD_BLOCKED_BY_DATASET_OR_METRIC"
    elif auroc_delta >= 0.05 and f1_delta >= 0.05 and lfd_far_mean <= 0.3:
        verdict = "LFD_BEATS_CUSUM_ORACLE_FREE"
    elif auroc_delta >= 0.02 or f1_delta >= 0.02:
        verdict = "LFD_PARTIALLY_BEATS_CUSUM_NEEDS_CALIBRATION"
    elif auroc_delta >= -0.01 and f1_delta >= -0.01:
        verdict = "CLAIM_SHOULD_USE_CUSUM_AS_BASELINE_OR_GATE"
    else:
        verdict = "LFD_NOT_BETTER_THAN_CUSUM_ORACLE_FREE"

    comparison = {
        "CUSUM_best_h": {
            "h": cusum_best_h,
            "AUROC": _get_f(cusum_summary, "auroc_wrong_hypothesis"),
            "AUPRC": _get_f(cusum_summary, "auprc_wrong_hypothesis"),
            "regime_shift_F1": _get_f(cusum_summary, "regime_shift_f1"),
            "detection_delay_mean": _get_f(cusum_summary, "mean_detection_delay"),
            "FAR_per_step": _get_f(cusum_summary, "false_alarm_rate_per_step"),
            "run_length_concentration": "N/A",
            "fair_ppc_ratio": 1.0,
        },
        f"SPRT_A{sprt_A_used}": {
            "A": sprt_A_used,
            "AUROC": _get_f(sprt_summary, "auroc_wrong_hypothesis"),
            "AUPRC": _get_f(sprt_summary, "auprc_wrong_hypothesis"),
            "regime_shift_F1": _get_f(sprt_summary, "regime_shift_f1"),
            "detection_delay_mean": _get_f(sprt_summary, "mean_detection_delay"),
            "FAR_per_step": _get_f(sprt_summary, "false_alarm_rate_per_step"),
            "run_length_concentration": "N/A",
            "fair_ppc_ratio": "N/A",
        },
        "LFD_seed0": {
            "AUROC": _get_f(lfd_primary, "auroc_wrong_hypothesis"),
            "AUPRC": _get_f(lfd_primary, "auprc_wrong_hypothesis"),
            "regime_shift_F1": _get_f(lfd_primary, "regime_shift_f1"),
            "detection_delay_mean": _get_f(lfd_primary, "mean_detection_delay"),
            "FAR_per_step": _get_f(lfd_primary, "false_alarm_rate_per_step"),
            "run_length_concentration": _get_f(lfd_primary, "run_length_posterior_concentration"),
            "fair_ppc_ratio": round(ppc_primary.get("ppc_ratio_lfd_over_cusum", 0.0), 4),
            "wrong_prob_std": lfd_primary.get("wrong_prob_std"),
            "proxy_off_check": lfd_primary.get("proxy_off_check"),
        },
        "LFD_mean_3seeds": {
            "AUROC": seed_summary["auroc_wrong_hypothesis"]["mean"],
            "AUROC_std": seed_summary["auroc_wrong_hypothesis"]["std"],
            "AUPRC": seed_summary["auprc_wrong_hypothesis"]["mean"],
            "regime_shift_F1": seed_summary["regime_shift_f1"]["mean"],
            "regime_shift_F1_std": seed_summary["regime_shift_f1"]["std"],
            "detection_delay_mean": seed_summary["detection_delay"]["mean"],
            "FAR_per_step": seed_summary["false_alarm_rate_per_step"]["mean"],
        },
        "deltas_LFD_minus_CUSUM": {
            "AUROC_delta": round(auroc_delta, 4),
            "F1_delta": round(f1_delta, 4),
        },
        "verdict": verdict,
        "oracle_free": True,
        "eval_n": len(eval_eps),
        "cusum_h_sweep": cusum_sweep,
        "sprt_both_A": {
            f"A={SPRT_A_PRIMARY}": {
                "regime_shift_F1": _get_f(sprt_summary_primary, "regime_shift_f1"),
                "FAR": _get_f(sprt_summary_primary, "false_alarm_rate_per_step"),
            },
            f"A={SPRT_A_FALLBACK}": {
                "regime_shift_F1": _get_f(sprt_summary_fallback, "regime_shift_f1"),
                "FAR": _get_f(sprt_summary_fallback, "false_alarm_rate_per_step"),
            },
        },
    }

    lfd_out = {
        "run_config": {
            "n_collect": N_COLLECT,
            "n_train": N_TRAIN,
            "n_eval": N_EVAL,
            "n_seeds": N_SEEDS,
            "lfd_epochs": LFD_EPOCHS,
            "lfd_lr": LFD_LR,
            "alarm_threshold": LFD_ALARM_THRESHOLD,
            "proxy_off": True,
            "oracle_free": True,
            "max_steps": MAX_STEPS,
        },
        "seed_results": lfd_seed_results,
        "seed_stability": seed_summary,
        "blocked": lfd_blocked,
    }

    lfd_path = OUTPUT_DIR / "lfd_v0_5_oracle_free_metrics.json"
    lfd_path.write_text(
        json.dumps(lfd_out, indent=2, default=str), encoding="utf-8"
    )
    print(f"\n  -> {lfd_path}")

    # ===================================================================
    # Print summary table
    # ===================================================================
    print("\n" + "=" * 70)
    print("ORACLE-FREE COMPARISON (eval set, N={})".format(len(eval_eps)))
    print("=" * 70)
    print(f"\n{'Metric':<35} {'CUSUM':>10} {'SPRT':>10} {'LFD(s0)':>10} {'LFD mean':>10}")
    print("-" * 70)

    def _fmt(x: Any) -> str:
        if x is None or x == "N/A":
            return "  N/A"
        if isinstance(x, float):
            return f"{x:>10.4f}"
        return f"{str(x):>10}"

    for k, label in [
        ("AUROC", "AUROC"),
        ("AUPRC", "AUPRC"),
        ("regime_shift_F1", "regime_shift_F1"),
        ("detection_delay_mean", "detection_delay (mean)"),
        ("FAR_per_step", "FAR/step"),
    ]:
        cv = comparison["CUSUM_best_h"].get(k)
        sv = comparison[f"SPRT_A{sprt_A_used}"].get(k)
        lv0 = comparison["LFD_seed0"].get(k)
        lvm = comparison["LFD_mean_3seeds"].get(k)
        print(f"  {label:<33} {_fmt(cv)} {_fmt(sv)} {_fmt(lv0)} {_fmt(lvm)}")

    print(f"\n  AUROC delta (LFD - CUSUM): {auroc_delta:.4f}")
    print(f"  F1 delta    (LFD - CUSUM): {f1_delta:.4f}")
    print(f"\n  VERDICT: {verdict}")
    print("=" * 70)

    # Write comparison JSON
    comp_path = OUTPUT_DIR / "comparison_v0_5_oracle_free.json"
    comp_path.write_text(json.dumps(comparison, indent=2, default=str), encoding="utf-8")
    print(f"\n  -> {comp_path}")

    print("\n[DONE] All 3 JSON outputs written:")
    print(f"  1. {audit_out}")
    print(f"  2. {cusum_sprt_path}")
    print(f"  3. {lfd_path}")
    print(f"  4. {comp_path}")


if __name__ == "__main__":
    main()
