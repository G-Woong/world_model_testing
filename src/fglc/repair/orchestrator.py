"""Dry-run repair loop orchestrator.

Source: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md Step 8.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol

from fglc.repair.candidates import candidates_for
from fglc.repair.compare import compare_metrics
from fglc.repair.diagnose import diagnose
from fglc.repair.ledger import (
    append_ledger_line,
    build_loop_id,
    build_run_id,
    compute_config_hash,
)
from fglc.repair.ranker import rank
from fglc.repair.taxonomy import FailureCauseId


@dataclass(frozen=True)
class RepairLoopConfig:
    phase: str
    config_path: Path
    split: str
    seed: int
    descriptor: str
    max_iter: int
    max_wall_clock_minutes: float
    max_consecutive_inconclusive: int
    dry_run: bool
    output_root: Path
    metric_directions: Mapping[str, str]
    gate_thresholds: Mapping[str, float]
    failed_metric: str


@dataclass
class RepairLoopState:
    loop_id: str
    iter: int = 0
    metrics_before: dict = field(default_factory=dict)
    metrics_after: dict = field(default_factory=dict)
    consecutive_inconclusive: int = 0
    total_wall_clock_minutes: float = 0.0
    stop_condition_hit: str | None = None


@dataclass(frozen=True)
class RepairIterationResult:
    ledger_line: dict
    diagnosed_causes: tuple
    ranked_candidates: tuple
    chosen_candidate: Any
    compare_result: dict | None
    stop_condition_hit: str | None
    next_action: str


@dataclass(frozen=True)
class RunnerOutput:
    metrics: dict
    wall_clock_minutes: float
    vram_peak_mib: float
    hook_blocked: bool = False
    hook_reason: str | None = None


class RepairRunner(Protocol):
    def __call__(
        self,
        *,
        phase,
        config_path,
        split,
        seed,
        descriptor,
        patch,
        iter_index,
    ) -> RunnerOutput: ...


def git_sha() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5.0,
        )
        return r.stdout.strip() or "unknown"
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def _hash_config(path: Path) -> str:
    if path.exists():
        return compute_config_hash(path)
    return compute_config_hash(f"<missing:{path.as_posix()}>")


def _candidate_none() -> dict:
    return {
        "id": None,
        "patch": {},
        "cost_minutes": None,
        "risk": None,
        "expected_signal": None,
        "rank": None,
    }


def _candidate_line(chosen: Any) -> dict:
    return {
        "id": chosen.id,
        "patch": dict(chosen.patch),
        "cost_minutes": chosen.cost_minutes,
        "risk": chosen.risk,
        "expected_signal": chosen.expected_signal,
        "rank": 1,
    }


def _causes_line(causes: tuple | list, phase: str) -> list[dict[str, str]]:
    return [
        {"cause_id": cause.value, "rationale": f"diagnose@{phase}"}
        for cause in causes
    ]


def _base_line(
    *,
    loop_id: str,
    cfg: RepairLoopConfig,
    config_hash: str,
    sha: str,
    iter_index: int,
    metrics_before: dict,
    metrics_after: dict,
    deltas: dict,
    causes: tuple | list,
    candidate_chosen: dict,
    result: str,
    stop_condition_hit: str | None,
    next_action: str,
    wall_clock_minutes: float,
    vram_peak_mib: float,
) -> dict:
    return {
        "loop_id": loop_id,
        "iter": iter_index,
        "run_id": build_run_id(
            cfg.phase,
            cfg.descriptor,
            cfg.seed,
            {"split": cfg.split, "iter": iter_index},
        ),
        "git_sha": sha,
        "config_hash": config_hash,
        "config_path": str(cfg.config_path),
        "phase": cfg.phase,
        "split": cfg.split,
        "metrics_before": metrics_before,
        "metrics_after": metrics_after,
        "deltas": deltas,
        "failed_metric": cfg.failed_metric,
        "diagnosed_cause": _causes_line(causes, cfg.phase),
        "candidate_chosen": candidate_chosen,
        "result": result,
        "stop_condition_hit": stop_condition_hit,
        "next_action": next_action,
        "wall_clock_minutes": wall_clock_minutes,
        "vram_peak_mib": vram_peak_mib,
    }


def _next_action(result: str, stop: str | None) -> str:
    if stop == "hook_blocked":
        return "escalate_to_user"
    if stop == "target_reached":
        return "stop_target_reached"
    if stop == "wall_clock":
        return "stop_wall_clock"
    if stop == "consecutive_inconclusive":
        return "stop_consecutive_inconclusive"
    if stop == "max_iter":
        return "stop_max_iter"
    if result == "accept":
        return "continue_or_next_phase"
    if result == "reject":
        return "try_next_candidate"
    if result == "inconclusive":
        return "increase_signal_or_eval"
    return "escalate_to_user"


def _gate_passed(value: float, cfg: RepairLoopConfig) -> bool:
    direction = cfg.metric_directions.get(cfg.failed_metric, "lower_better")
    threshold = cfg.gate_thresholds.get(cfg.failed_metric)
    if threshold is None:
        return False
    if "lower" in direction:
        return value <= threshold
    return value >= threshold


def _is_sentinel_only(cands: list) -> bool:
    return (
        len(cands) == 1
        and cands[0].cause_id == FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED
    )


def run_repair_loop(
    cfg: RepairLoopConfig,
    *,
    runner: RepairRunner,
    now=None,
    git_sha_fn=None,
) -> list[RepairIterationResult]:
    loop_id = build_loop_id(now() if now else None)
    config_hash = _hash_config(cfg.config_path)
    ledger_path = cfg.output_root / f"{loop_id}.jsonl"
    cfg.output_root.mkdir(parents=True, exist_ok=True)

    sha = git_sha_fn() if git_sha_fn else git_sha()
    baseline = runner(
        phase=cfg.phase,
        config_path=cfg.config_path,
        split=cfg.split,
        seed=cfg.seed,
        descriptor=cfg.descriptor,
        patch=None,
        iter_index=0,
    )

    if baseline.hook_blocked:
        line = _base_line(
            loop_id=loop_id,
            cfg=cfg,
            config_hash=config_hash,
            sha=sha,
            iter_index=0,
            metrics_before={},
            metrics_after=dict(baseline.metrics),
            deltas={},
            causes=(),
            candidate_chosen=_candidate_none(),
            result="inconclusive",
            stop_condition_hit="hook_blocked",
            next_action="escalate_to_user",
            wall_clock_minutes=baseline.wall_clock_minutes,
            vram_peak_mib=baseline.vram_peak_mib,
        )
        append_ledger_line(ledger_path, line)
        return [
            RepairIterationResult(
                ledger_line=line,
                diagnosed_causes=(),
                ranked_candidates=(),
                chosen_candidate=None,
                compare_result=None,
                stop_condition_hit="hook_blocked",
                next_action=line["next_action"],
            )
        ]

    state = RepairLoopState(loop_id=loop_id)
    state_metrics_before = dict(baseline.metrics)
    total_wall_clock = baseline.wall_clock_minutes
    consecutive_inconclusive = 0
    results: list[RepairIterationResult] = []

    for iter_index in range(1, cfg.max_iter + 1):
        state.iter = iter_index
        cur_val = state_metrics_before.get(cfg.failed_metric)
        if cur_val is not None and _gate_passed(cur_val, cfg):
            line = _base_line(
                loop_id=loop_id,
                cfg=cfg,
                config_hash=config_hash,
                sha=sha,
                iter_index=iter_index,
                metrics_before=dict(state_metrics_before),
                metrics_after=dict(state_metrics_before),
                deltas={cfg.failed_metric: 0.0},
                causes=(),
                candidate_chosen=_candidate_none(),
                result="accept",
                stop_condition_hit="target_reached",
                next_action="stop_target_reached",
                wall_clock_minutes=0.0,
                vram_peak_mib=0.0,
            )
            append_ledger_line(ledger_path, line)
            results.append(
                RepairIterationResult(
                    ledger_line=line,
                    diagnosed_causes=(),
                    ranked_candidates=(),
                    chosen_candidate=None,
                    compare_result=None,
                    stop_condition_hit="target_reached",
                    next_action=line["next_action"],
                )
            )
            return results

        causes = diagnose(state_metrics_before, cfg.phase)
        cands = candidates_for(causes, cfg.phase)

        if not cands or _is_sentinel_only(cands):
            line = _base_line(
                loop_id=loop_id,
                cfg=cfg,
                config_hash=config_hash,
                sha=sha,
                iter_index=iter_index,
                metrics_before=dict(state_metrics_before),
                metrics_after=dict(state_metrics_before),
                deltas={},
                causes=causes,
                candidate_chosen=_candidate_none(),
                result="inconclusive",
                stop_condition_hit="hook_blocked",
                next_action="escalate_to_user",
                wall_clock_minutes=0.0,
                vram_peak_mib=0.0,
            )
            append_ledger_line(ledger_path, line)
            results.append(
                RepairIterationResult(
                    ledger_line=line,
                    diagnosed_causes=tuple(causes),
                    ranked_candidates=(),
                    chosen_candidate=None,
                    compare_result=None,
                    stop_condition_hit="hook_blocked",
                    next_action=line["next_action"],
                )
            )
            return results

        ranked = rank(cands)
        chosen = ranked[0].candidate
        out = runner(
            phase=cfg.phase,
            config_path=cfg.config_path,
            split=cfg.split,
            seed=cfg.seed,
            descriptor=cfg.descriptor,
            patch=chosen.patch,
            iter_index=iter_index,
        )
        if out.hook_blocked:
            line = _base_line(
                loop_id=loop_id,
                cfg=cfg,
                config_hash=config_hash,
                sha=sha,
                iter_index=iter_index,
                metrics_before=dict(state_metrics_before),
                metrics_after=dict(out.metrics),
                deltas={},
                causes=causes,
                candidate_chosen=_candidate_line(chosen),
                result="inconclusive",
                stop_condition_hit="hook_blocked",
                next_action="escalate_to_user",
                wall_clock_minutes=out.wall_clock_minutes,
                vram_peak_mib=out.vram_peak_mib,
            )
            append_ledger_line(ledger_path, line)
            results.append(
                RepairIterationResult(
                    ledger_line=line,
                    diagnosed_causes=tuple(causes),
                    ranked_candidates=tuple(ranked),
                    chosen_candidate=chosen,
                    compare_result=None,
                    stop_condition_hit="hook_blocked",
                    next_action=line["next_action"],
                )
            )
            return results

        total_wall_clock += out.wall_clock_minutes
        metrics_after = dict(out.metrics)
        cmp = compare_metrics(
            state_metrics_before,
            metrics_after,
            cfg.failed_metric,
            dict(cfg.metric_directions),
        )

        if cmp["result"] == "inconclusive":
            consecutive_inconclusive += 1
        else:
            consecutive_inconclusive = 0

        stop = None
        if total_wall_clock >= cfg.max_wall_clock_minutes:
            stop = "wall_clock"
        elif consecutive_inconclusive >= cfg.max_consecutive_inconclusive:
            stop = "consecutive_inconclusive"
        elif iter_index == cfg.max_iter:
            stop = "max_iter"

        line = _base_line(
            loop_id=loop_id,
            cfg=cfg,
            config_hash=config_hash,
            sha=sha,
            iter_index=iter_index,
            metrics_before=dict(state_metrics_before),
            metrics_after=metrics_after,
            deltas=cmp["deltas"],
            causes=causes,
            candidate_chosen=_candidate_line(chosen),
            result=cmp["result"],
            stop_condition_hit=stop,
            next_action=_next_action(cmp["result"], stop),
            wall_clock_minutes=out.wall_clock_minutes,
            vram_peak_mib=out.vram_peak_mib,
        )
        append_ledger_line(ledger_path, line)

        result = RepairIterationResult(
            ledger_line=line,
            diagnosed_causes=tuple(causes),
            ranked_candidates=tuple(ranked),
            chosen_candidate=chosen,
            compare_result=cmp,
            stop_condition_hit=stop,
            next_action=line["next_action"],
        )
        results.append(result)

        if cmp["result"] == "accept":
            state_metrics_before = metrics_after

        if stop:
            return results

    return results
