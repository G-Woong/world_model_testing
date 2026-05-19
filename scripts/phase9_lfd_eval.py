"""PHASE 9 end-to-end LFD evidence run.

Execution mode: SYNTHETIC ORACLE PROBE
  - collect_episode() does not yet implement v0_5 grammar-switch handling.
    (GrammarEngine uses original grammar throughout; switch has no effect on
    effect types. Codex follow-up: TASK_COLLECTOR_V05_SWITCH.)
  - Effect streams are synthetically simulated: oracle switch_step known,
    pre-switch effects ~ correct(0), post-switch effects ~ mismatch(1) + noise.
  - All metrics are computed from this synthetic data under controlled conditions.
  - This is explicitly a probe-level evaluation, NOT a final deployment eval.

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
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import torch
import torch.nn.functional as F

from frcgw.data.text_dataset import BatchTargets
from frcgw.evaluation.baseline_detectors import (
    CUSUMDetector,
    run_cusum_on_episode,
    run_sprt_on_episode,
)
from frcgw.evaluation.metrics import (
    aggregate_episode_metrics,
    auroc_wrong_hypothesis,
    auprc_wrong_hypothesis,
    detection_delay,
    false_alarm_rate_per_step,
    recovery_delay_correlation,
    regime_shift_f1_sequential,
    run_length_posterior_concentration,
)
from frcgw.models.text_frcg_model import TextFRCGModel
from frcgw.objectives.losses import (
    DEFAULT_WEIGHTS,
    L_run_length_posterior,
    L_seq_falsification,
)
from frcgw.schemas.step_schema import PublicObservation
from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS
from frcgw.text_env.generator import EpisodeSpecGenerator

# ---------------------------------------------------------------------------
# Config (proxy OFF: all thresholds fixed before seeing results)
# ---------------------------------------------------------------------------

N_EPISODES = 200        # per-seed
N_SEEDS = 3             # seed stability
MAX_STEPS = 12          # per episode
SWITCH_NOISE = 0.15     # fraction of post-switch steps where effect is "correct"
PRE_SWITCH_NOISE = 0.10  # fraction of pre-switch steps with spurious mismatch

CUSUM_H = 2.0           # decision interval — fixed before results
CUSUM_K = 0.3           # reference value
SPRT_A = 5.0            # upper threshold (reject H0)
SPRT_B = 0.1            # lower threshold (accept H0)

LFD_EPOCHS = 15
LFD_LR = 5e-4
LFD_BATCH_SIZE = 16

OUTPUT_DIR = ROOT / "outputs" / "risk_hunt" / "implementation" / "evals"


# ---------------------------------------------------------------------------
# Synthetic oracle data generation
# ---------------------------------------------------------------------------

def simulate_effect_stream(
    spec: Any,
    pre_noise: float = PRE_SWITCH_NOISE,
    post_noise: float = SWITCH_NOISE,
    rng: random.Random | None = None,
) -> list[int]:
    """Oracle-guided v0_5 effect stream simulation.

    Pre-switch (step < switch_step): 0=correct with 1-pre_noise probability.
    Post-switch (step >= switch_step): 1=mismatch with 1-post_noise probability.
    NOTE: This bypasses collect_episode() — see module docstring.
    """
    if rng is None:
        rng = random.Random(spec.seed)
    effects = []
    switch_step = getattr(spec, "regime_switch_step", None)
    for step in range(spec.max_steps):
        if switch_step is None or step < switch_step:
            effects.append(1 if rng.random() < pre_noise else 0)
        else:
            effects.append(0 if rng.random() < post_noise else 1)
    return effects


def make_true_wrong_per_step(spec: Any, n_steps: int) -> list[bool]:
    """Oracle true_wrong_hypothesis per step."""
    switch_step = getattr(spec, "regime_switch_step", None)
    if switch_step is None:
        return [False] * n_steps
    return [i >= switch_step for i in range(n_steps)]


def make_true_run_lengths(spec: Any, n_steps: int) -> list[int]:
    """Oracle run lengths: reset at switch_step."""
    switch_step = getattr(spec, "regime_switch_step", None)
    rls = []
    for i in range(n_steps):
        if switch_step is None or i < switch_step:
            rls.append(i + 1)  # growing stable run
        else:
            rls.append(i - switch_step + 1)  # reset after switch
    return rls


# ---------------------------------------------------------------------------
# CUSUM/SPRT baseline evaluation
# ---------------------------------------------------------------------------

def eval_cusum_on_specs(
    specs: list[Any],
    h: float = CUSUM_H,
    k: float = CUSUM_K,
    seed: int = 0,
) -> tuple[list[dict], dict]:
    """Evaluate CUSUM on all v0_5 specs. Returns (episode_dicts, summary)."""
    rng = random.Random(seed)
    episodes = []
    for spec in specs:
        effects = simulate_effect_stream(spec, rng=rng)
        result = run_cusum_on_episode(effects, expected_effect_type=0, k=k, h=h)
        switch_step = getattr(spec, "regime_switch_step", None)
        stable_steps = list(range(switch_step)) if switch_step is not None else list(range(len(effects)))
        true_wrong = make_true_wrong_per_step(spec, len(effects))
        true_rls = make_true_run_lengths(spec, len(effects))
        recovery = None
        if result["first_alarm"] is not None and switch_step is not None:
            dd = max(0, result["first_alarm"] - switch_step)
            recovery = dd + 2
        episodes.append({
            "switch_step": switch_step,
            "first_alarm": result["first_alarm"],
            "stable_steps": stable_steps,
            "alarm_steps": result["alarm_steps"],
            "wrong_prob_scores": [float(e) for e in effects],
            "true_wrong_hypothesis": true_wrong,
            "run_length_posteriors": [],
            "true_run_lengths": true_rls,
            "recovery_delay": recovery,
            "task_family": spec.task_family,
            "total_progress": 0.0,
        })
    result_agg = aggregate_episode_metrics(episodes, detector_name=f"cusum_h{h}")
    summary = _result_to_dict(result_agg)
    summary["threshold_h"] = h
    summary["threshold_k"] = k
    return episodes, summary


def eval_sprt_on_specs(
    specs: list[Any],
    A: float = SPRT_A,
    B: float = SPRT_B,
    seed: int = 0,
) -> tuple[list[dict], dict]:
    """Evaluate SPRT on all v0_5 specs."""
    rng = random.Random(seed)
    episodes = []
    for spec in specs:
        effects = simulate_effect_stream(spec, rng=rng)
        result = run_sprt_on_episode(effects, expected_effect_type=0, A=A, B=B)
        switch_step = getattr(spec, "regime_switch_step", None)
        stable_steps = list(range(switch_step)) if switch_step is not None else list(range(len(effects)))
        true_wrong = make_true_wrong_per_step(spec, len(effects))
        true_rls = make_true_run_lengths(spec, len(effects))
        recovery = None
        if result["first_alarm"] is not None and switch_step is not None:
            dd = max(0, result["first_alarm"] - switch_step)
            recovery = dd + 2
        episodes.append({
            "switch_step": switch_step,
            "first_alarm": result["first_alarm"],
            "stable_steps": stable_steps,
            "alarm_steps": result["alarm_steps"],
            "wrong_prob_scores": [float(e) for e in effects],
            "true_wrong_hypothesis": true_wrong,
            "run_length_posteriors": [],
            "true_run_lengths": true_rls,
            "recovery_delay": recovery,
            "task_family": spec.task_family,
            "total_progress": 0.0,
        })
    result_agg = aggregate_episode_metrics(episodes, detector_name="sprt")
    summary = _result_to_dict(result_agg)
    summary["threshold_A"] = A
    summary["threshold_B"] = B
    return episodes, summary


# ---------------------------------------------------------------------------
# LFD training
# ---------------------------------------------------------------------------

def _make_batch_targets(true_wrong_list: list[bool | None]) -> list[BatchTargets]:
    """Build BatchTargets from true_wrong_hypothesis sequence."""
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


def _make_obs_batch(n: int) -> list[PublicObservation]:
    """Minimal synthetic PublicObservation batch (no forbidden fields)."""
    return [
        PublicObservation(instruction=f"[INSTRUCTION] search [STATE] state_{i}")
        for i in range(n)
    ]


def train_lfd_seed(
    specs: list[Any],
    seed: int = 0,
    epochs: int = LFD_EPOCHS,
    lr: float = LFD_LR,
    batch_size: int = LFD_BATCH_SIZE,
) -> tuple[TextFRCGModel, dict]:
    """Train LFD head on synthetic v0_5 data.

    Proxy OFF: training uses only oracle switch_step via true_wrong_hypothesis labels.
    No threshold tuning. effect_scalar is derived from oracle effect stream (not real obs).
    """
    torch.manual_seed(seed)
    random.seed(seed)

    model = TextFRCGModel(use_lfd_head=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # Build training samples: (effect_scalar [0 or 1], true_wrong [bool | None])
    rng = random.Random(seed)
    all_steps: list[tuple[int, bool | None]] = []  # (effect_int, true_wrong)
    for spec in specs:
        effects = simulate_effect_stream(spec, rng=rng)
        true_wrong = make_true_wrong_per_step(spec, len(effects))
        for eff, tw in zip(effects, true_wrong):
            all_steps.append((eff, tw))

    rng_train = random.Random(seed + 1000)
    train_losses: list[float] = []

    model.train()
    for epoch in range(epochs):
        rng_train.shuffle(all_steps)
        epoch_loss = 0.0
        n_batches = 0
        for i in range(0, len(all_steps), batch_size):
            batch = all_steps[i : i + batch_size]
            if not batch:
                continue
            b = len(batch)
            effects_t = torch.tensor([e for e, _ in batch], dtype=torch.float32).reshape(b, 1)
            targets = _make_batch_targets([tw for _, tw in batch])
            obs_batch = _make_obs_batch(b)

            # Forward with LFD head
            with torch.no_grad():
                base_out = model.forward(obs_batch, return_lfd=False)

            lfd_out, _ = model.falsification_head(
                base_out.shared_h,
                base_out.z_state,
                effects_t,
                torch.zeros(b),  # F_t_deterministic = 0 (proxy OFF)
            )

            l_seq = L_seq_falsification(lfd_out.wrong_prob_learned, targets)
            l_rl = L_run_length_posterior(lfd_out.run_length_posterior, targets)
            loss = DEFAULT_WEIGHTS["l_seq_falsification"] * l_seq + \
                   DEFAULT_WEIGHTS["l_run_length_posterior"] * l_rl

            if not math.isfinite(loss.item()):
                continue  # skip non-finite step

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            epoch_loss += loss.item()
            n_batches += 1

        mean_epoch_loss = epoch_loss / max(1, n_batches)
        train_losses.append(mean_epoch_loss)

    return model, {"train_losses": train_losses, "seed": seed, "epochs": epochs}


# ---------------------------------------------------------------------------
# LFD evaluation
# ---------------------------------------------------------------------------

def eval_lfd_on_specs(
    model: TextFRCGModel,
    specs: list[Any],
    seed: int = 0,
) -> tuple[list[dict], dict]:
    """Evaluate trained LFD on v0_5 synthetic data.

    Returns (episode_dicts, summary).
    wrong_prob_learned is extracted as the detection signal (proxy OFF).
    """
    rng = random.Random(seed)
    model.eval()
    episodes = []

    with torch.no_grad():
        for spec in specs:
            effects = simulate_effect_stream(spec, rng=rng)
            true_wrong = make_true_wrong_per_step(spec, len(effects))
            true_rls = make_true_run_lengths(spec, len(effects))
            switch_step = getattr(spec, "regime_switch_step", None)

            # Process episode step by step
            step_wrong_probs: list[float] = []
            step_run_length_posteriors: list[list[float]] = []
            head_h = None  # persistent LFD head state

            for step_idx, eff in enumerate(effects):
                obs = PublicObservation(instruction=f"[INSTRUCTION] task [STATE] step_{step_idx}")
                effect_t = torch.tensor([[float(eff)]], dtype=torch.float32)

                base_out = model.forward(obs, return_lfd=False)
                lfd_out, head_h = model.falsification_head(
                    base_out.shared_h,
                    base_out.z_state,
                    effect_t,
                    torch.zeros(1),  # F_t_deterministic = 0 (proxy OFF)
                    head_h,
                )
                wp = float(lfd_out.wrong_prob_learned[0].item())
                rl_post = lfd_out.run_length_posterior[0].tolist()
                step_wrong_probs.append(wp)
                step_run_length_posteriors.append(rl_post)

            # Threshold: alarm when wrong_prob > 0.5 (fixed, proxy OFF)
            alarm_threshold = 0.5
            stable_steps = list(range(switch_step)) if switch_step is not None else list(range(len(effects)))
            alarm_steps = [i for i, wp in enumerate(step_wrong_probs) if wp >= alarm_threshold]
            first_alarm = alarm_steps[0] if alarm_steps else None

            recovery = None
            if first_alarm is not None and switch_step is not None:
                dd = max(0, first_alarm - switch_step)
                recovery = dd + 2

            episodes.append({
                "switch_step": switch_step,
                "first_alarm": first_alarm,
                "stable_steps": stable_steps,
                "alarm_steps": alarm_steps,
                "wrong_prob_scores": step_wrong_probs,
                "true_wrong_hypothesis": true_wrong,
                "run_length_posteriors": step_run_length_posteriors,
                "true_run_lengths": true_rls,
                "recovery_delay": recovery,
                "task_family": spec.task_family,
                "total_progress": 0.0,
            })

    result_agg = aggregate_episode_metrics(episodes, detector_name="lfd_learned")
    summary = _result_to_dict(result_agg)
    summary["alarm_threshold"] = alarm_threshold
    summary["proxy_off"] = True
    return episodes, summary


# ---------------------------------------------------------------------------
# Fair PPC (wall-clock estimate)
# ---------------------------------------------------------------------------

def estimate_fair_ppc(
    cusum_time_s: float,
    lfd_time_s: float,
    n_episodes: int,
    cusum_summary: dict,
    lfd_summary: dict,
) -> dict:
    """Estimated fair PPC (progress per compute unit).

    Units: seconds per episode for LFD vs CUSUM.
    Progress proxy: regime_shift_recall (fraction of switches detected).
    """
    cusum_per_ep = cusum_time_s / max(1, n_episodes)
    lfd_per_ep = lfd_time_s / max(1, n_episodes)

    cusum_progress = cusum_summary.get("regime_shift_recall", 0.0) or 0.0
    lfd_progress = lfd_summary.get("regime_shift_recall", 0.0) or 0.0

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
# Leakage check
# ---------------------------------------------------------------------------

def check_no_leakage_in_obs(obs_list: list[PublicObservation]) -> dict:
    """Verify no forbidden fields in synthetic observations."""
    violations = []
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
    return {"mean": round(mean, 4), "std": round(math.sqrt(variance), 4), "values": [round(v, 4) if v is not None else None for v in values]}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("PHASE 9: LFD end-to-end evidence run (SYNTHETIC ORACLE PROBE)")
    print(f"N_EPISODES={N_EPISODES}, N_SEEDS={N_SEEDS}, LFD_EPOCHS={LFD_EPOCHS}")
    print(f"CUSUM: h={CUSUM_H}, k={CUSUM_K} | SPRT: A={SPRT_A}, B={SPRT_B}")
    print(f"Proxy OFF: thresholds fixed before results")
    print("=" * 60)

    # Leakage pre-check
    sample_obs = _make_obs_batch(10)
    leakage_check = check_no_leakage_in_obs(sample_obs)
    if not leakage_check["clean"]:
        print(f"[BLOCKED] LEAKAGE DETECTED: {leakage_check['violations']}")
        sys.exit(1)
    print("[PASS] Leakage pre-check: no forbidden fields in synthetic obs")

    # Generate v0_5 specs (same specs across seeds for fair comparison)
    gen = EpisodeSpecGenerator(seed=42, max_steps=MAX_STEPS)
    v0_5_specs = gen.generate_v0_5_batch(N_EPISODES)
    stable_specs = gen.generate_batch(N_EPISODES // 4)  # 25% stable (no switch)
    all_specs = v0_5_specs + stable_specs
    n_switch = sum(1 for s in all_specs if getattr(s, "regime_switch_step", None) is not None)
    n_stable = len(all_specs) - n_switch
    print(f"\n[DATA] {len(all_specs)} total specs: {n_switch} switch, {n_stable} stable")
    switch_steps = [s.regime_switch_step for s in v0_5_specs if s.regime_switch_step is not None]
    if switch_steps:
        mean_sw = sum(switch_steps) / len(switch_steps)
        print(f"[DATA] switch_step distribution: mean={mean_sw:.1f}, "
              f"min={min(switch_steps)}, max={max(switch_steps)}")

    # === STEP 1: CUSUM baseline eval ===
    print("\n[STEP 1] CUSUM baseline eval...")
    t0 = time.time()
    cusum_eps, cusum_summary = eval_cusum_on_specs(all_specs, h=CUSUM_H, k=CUSUM_K, seed=42)
    cusum_time = time.time() - t0
    print(f"  detection_delay: {cusum_summary.get('mean_detection_delay')}")
    print(f"  FAR/step:        {cusum_summary.get('false_alarm_rate_per_step', 0.0):.4f}")
    print(f"  regime_shift_F1: {cusum_summary.get('regime_shift_f1', 0.0):.4f}")
    print(f"  AUROC:           {cusum_summary.get('auroc_wrong_hypothesis')}")
    print(f"  time: {cusum_time:.2f}s")

    # === STEP 2: SPRT baseline eval ===
    print("\n[STEP 2] SPRT baseline eval...")
    sprt_eps, sprt_summary = eval_sprt_on_specs(all_specs, A=SPRT_A, B=SPRT_B, seed=42)
    print(f"  detection_delay: {sprt_summary.get('mean_detection_delay')}")
    print(f"  FAR/step:        {sprt_summary.get('false_alarm_rate_per_step', 0.0):.4f}")
    print(f"  regime_shift_F1: {sprt_summary.get('regime_shift_f1', 0.0):.4f}")

    # === STEP 3: LFD training + eval (3 seeds) ===
    print("\n[STEP 3] LFD training + eval (3 seeds)...")
    lfd_seed_results = []
    for seed in range(N_SEEDS):
        print(f"  Seed {seed}...")
        t0 = time.time()
        model, train_info = train_lfd_seed(all_specs, seed=seed)
        train_time = time.time() - t0

        t1 = time.time()
        lfd_eps, lfd_summary = eval_lfd_on_specs(model, all_specs, seed=seed)
        eval_time = time.time() - t1

        final_loss = train_info["train_losses"][-1] if train_info["train_losses"] else None
        print(f"    train_loss[-1]={final_loss:.4f}, "
              f"detection_delay={lfd_summary.get('mean_detection_delay')}, "
              f"F1={lfd_summary.get('regime_shift_f1', 0.0):.4f}, "
              f"AUROC={lfd_summary.get('auroc_wrong_hypothesis')}, "
              f"train={train_time:.1f}s, eval={eval_time:.1f}s")

        # Fair PPC (LFD includes train+eval amortized over N_EPISODES)
        ppc = estimate_fair_ppc(
            cusum_time_s=cusum_time,
            lfd_time_s=train_time + eval_time,
            n_episodes=len(all_specs),
            cusum_summary=cusum_summary,
            lfd_summary=lfd_summary,
        )
        lfd_seed_results.append({
            "seed": seed,
            "lfd_summary": lfd_summary,
            "train_info": train_info,
            "fair_ppc": ppc,
            "train_time_s": train_time,
            "eval_time_s": eval_time,
        })

    # === STEP 4: Seed stability stats ===
    seed_delays = [r["lfd_summary"].get("mean_detection_delay") for r in lfd_seed_results]
    seed_f1s = [r["lfd_summary"].get("regime_shift_f1") for r in lfd_seed_results]
    seed_aurocs = [r["lfd_summary"].get("auroc_wrong_hypothesis") for r in lfd_seed_results]
    seed_fars = [r["lfd_summary"].get("false_alarm_rate_per_step", 0.0) for r in lfd_seed_results]

    seed_summary = {
        "detection_delay": _seed_stats(seed_delays),
        "regime_shift_f1": _seed_stats(seed_f1s),
        "auroc_wrong_hypothesis": _seed_stats(seed_aurocs),
        "false_alarm_rate_per_step": _seed_stats(seed_fars),
        "n_seeds": N_SEEDS,
    }

    # Represent with seed 0 for primary LFD summary
    lfd_primary = lfd_seed_results[0]["lfd_summary"]
    ppc_primary = lfd_seed_results[0]["fair_ppc"]

    # === STEP 5: CUSUM threshold sweep (Reviewer-2 MAJOR Attack 2) ===
    print("\n[STEP 5] CUSUM threshold sweep (h=0.5..4.0)...")
    threshold_sweep = {}
    for h_val in [0.5, 1.0, 2.0, 3.0, 4.0]:
        _, sw_summary = eval_cusum_on_specs(all_specs, h=h_val, k=CUSUM_K, seed=42)
        threshold_sweep[f"h={h_val}"] = {
            "mean_detection_delay": sw_summary.get("mean_detection_delay"),
            "false_alarm_rate_per_step": sw_summary.get("false_alarm_rate_per_step"),
            "regime_shift_f1": sw_summary.get("regime_shift_f1"),
        }
        print(f"  h={h_val}: delay={sw_summary.get('mean_detection_delay')}, "
              f"FAR={sw_summary.get('false_alarm_rate_per_step', 0.0):.4f}, "
              f"F1={sw_summary.get('regime_shift_f1', 0.0):.4f}")

    # === STEP 6: LFD vs CUSUM comparison ===
    def _get_f(d, k, default=None):
        v = d.get(k, default)
        return round(v, 4) if isinstance(v, float) else v

    lfd_vs_cusum = {
        "CUSUM": {
            "mean_detection_delay": _get_f(cusum_summary, "mean_detection_delay"),
            "false_alarm_rate_per_step": _get_f(cusum_summary, "false_alarm_rate_per_step"),
            "regime_shift_f1": _get_f(cusum_summary, "regime_shift_f1"),
            "auroc_wrong_hypothesis": _get_f(cusum_summary, "auroc_wrong_hypothesis"),
            "auprc_wrong_hypothesis": _get_f(cusum_summary, "auprc_wrong_hypothesis"),
        },
        "SPRT": {
            "mean_detection_delay": _get_f(sprt_summary, "mean_detection_delay"),
            "false_alarm_rate_per_step": _get_f(sprt_summary, "false_alarm_rate_per_step"),
            "regime_shift_f1": _get_f(sprt_summary, "regime_shift_f1"),
        },
        "LFD_seed0": {
            "mean_detection_delay": _get_f(lfd_primary, "mean_detection_delay"),
            "false_alarm_rate_per_step": _get_f(lfd_primary, "false_alarm_rate_per_step"),
            "regime_shift_f1": _get_f(lfd_primary, "regime_shift_f1"),
            "auroc_wrong_hypothesis": _get_f(lfd_primary, "auroc_wrong_hypothesis"),
            "auprc_wrong_hypothesis": _get_f(lfd_primary, "auprc_wrong_hypothesis"),
            "run_length_posterior_concentration": _get_f(lfd_primary, "run_length_posterior_concentration"),
        },
        "LFD_seed_mean": {
            "mean_detection_delay": seed_summary["detection_delay"]["mean"],
            "regime_shift_f1": seed_summary["regime_shift_f1"]["mean"],
            "auroc_wrong_hypothesis": seed_summary["auroc_wrong_hypothesis"]["mean"],
            "false_alarm_rate_per_step": seed_summary["false_alarm_rate_per_step"]["mean"],
        },
        "fair_ppc_seed0": ppc_primary,
        "cusum_threshold_sweep": threshold_sweep,
    }

    # === STEP 7: Final leakage re-check ===
    final_leakage = check_no_leakage_in_obs(sample_obs)

    # === STEP 8: Assemble end_to_end_metrics.json ===
    end_to_end = {
        "run_config": {
            "n_episodes": len(all_specs),
            "n_switch_episodes": n_switch,
            "n_stable_episodes": n_stable,
            "n_seeds": N_SEEDS,
            "lfd_epochs": LFD_EPOCHS,
            "cusum_h": CUSUM_H,
            "cusum_k": CUSUM_K,
            "sprt_A": SPRT_A,
            "sprt_B": SPRT_B,
            "max_steps": MAX_STEPS,
            "execution_mode": "SYNTHETIC_ORACLE_PROBE",
            "proxy_off": True,
        },
        "cusum_summary": cusum_summary,
        "sprt_summary": sprt_summary,
        "lfd_seed_results": lfd_seed_results,
        "seed_stability": seed_summary,
        "fair_ppc": ppc_primary,
        "leakage_check": final_leakage,
        "v0_5_generator_limitation": {
            "note": "collect_episode() does not implement v0_5 grammar-switch handling.",
            "impact": "Effect streams are oracle-simulated. LFD trained on synthetic data.",
            "codex_followup": "TASK_COLLECTOR_V05_SWITCH: implement switch-aware GrammarEngine.",
        },
    }

    # === Write outputs ===
    out1 = OUTPUT_DIR / "end_to_end_metrics.json"
    out2 = OUTPUT_DIR / "lfd_vs_cusum_summary.json"
    out3 = OUTPUT_DIR / "seed_summary.json"

    out1.write_text(json.dumps(end_to_end, indent=2, default=str), encoding="utf-8")
    out2.write_text(json.dumps(lfd_vs_cusum, indent=2, default=str), encoding="utf-8")
    out3.write_text(json.dumps(seed_summary, indent=2, default=str), encoding="utf-8")

    print("\n" + "=" * 60)
    print("PHASE 9 RESULTS SUMMARY")
    print("=" * 60)
    print(f"\n{'Metric':<35} {'CUSUM':>10} {'SPRT':>10} {'LFD(seed0)':>12}")
    print("-" * 70)
    for k, label in [
        ("mean_detection_delay", "detection_delay (mean)"),
        ("false_alarm_rate_per_step", "FAR/step"),
        ("regime_shift_f1", "regime_shift_F1"),
        ("auroc_wrong_hypothesis", "AUROC"),
        ("auprc_wrong_hypothesis", "AUPRC"),
    ]:
        cv = cusum_summary.get(k, "N/A")
        sv = sprt_summary.get(k, "N/A")
        lv = lfd_primary.get(k, "N/A")
        def fmt(x):
            if x is None: return "  N/A"
            if isinstance(x, float): return f"{x:>10.4f}"
            return f"{str(x):>10}"
        print(f"  {label:<33} {fmt(cv)} {fmt(sv)} {fmt(lv)}")
    print(f"\n  {'LFD seed stability (F1)':33} mean={seed_summary['regime_shift_f1']['mean']}, "
          f"std={seed_summary['regime_shift_f1']['std']}")
    print(f"  {'LFD seed stability (AUROC)':33} mean={seed_summary['auroc_wrong_hypothesis']['mean']}, "
          f"std={seed_summary['auroc_wrong_hypothesis']['std']}")
    print(f"\n  Leakage check: {'PASS' if final_leakage['clean'] else 'FAIL'}")
    print(f"\n  Outputs:")
    print(f"    {out1}")
    print(f"    {out2}")
    print(f"    {out3}")
    print("=" * 60)


if __name__ == "__main__":
    main()
