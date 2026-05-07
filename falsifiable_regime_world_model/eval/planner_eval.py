"""PlannerEvalRunner — (model × planner × split × seed) cross-product 실행.

사용 예 (scripts/evaluate_planners.py에서 호출):
    cfg = PlannerEvalConfig.from_yaml(args.config)
    runner = PlannerEvalRunner(cfg, out_dir=args.out_dir)
    runner.run(max_episodes=args.max_episodes)

본 모듈은:
- model checkpoint를 한 번 로드하면 모든 planner/split/seed가 재사용.
- planner는 spec.kind에 따라 dispatch.
- split별 RG4FConfig override (drift / shift 곱하기 등)를 적용한 RG4FEnv 생성.
- per-episode raw jsonl + per-episode csv + (planner trace 옵션) 저장.

oracle leakage 방지: planner는 obs와 belief만 받으며 ground truth는 trace에만 기록.
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import torch
import yaml

from ..planner import (
    AdaptiveLookaheadPlanner,
    AlwaysPlanPlanner,
    BasePlanner,
    EventOnlyPlanner,
    FixedKPlanner,
    FRCWMPlanner,
    PlannerEvalConfig,
    PlannerSpec,
    PlannerTrace,
    ReactivePlanner,
    SplitSpec,
    UncertaintyGatePlanner,
    WorldModelAdapter,
)
from ..planner.config import ModelSpec
from ..rg4f.config import RG4FConfig
from ..rg4f.env import RG4FEnv
from .metrics import (
    EpisodeResult,
    aggregate_by_planner,
    aggregate_by_split,
    compute_episode_metrics,
)
from .rollout_runner import run_episode


# =============================================================================
# 1. planner factory
# =============================================================================


_PLANNER_FACTORY = {
    "reactive": ReactivePlanner,
    "fixed_k": FixedKPlanner,
    "always_plan": AlwaysPlanPlanner,
    "uncertainty_gate": UncertaintyGatePlanner,
    "adaptive_lookahead": AdaptiveLookaheadPlanner,
    "event_only": EventOnlyPlanner,
    "ours_frc": FRCWMPlanner,
}


def make_planner(
    spec: PlannerSpec,
    *,
    adapter: WorldModelAdapter,
    rng: np.random.Generator,
) -> BasePlanner:
    """spec.kind에 따라 planner 인스턴스 생성."""
    cls = _PLANNER_FACTORY.get(spec.kind)
    if cls is None:
        raise ValueError(
            f"unknown planner kind '{spec.kind}'. allowed: {sorted(_PLANNER_FACTORY.keys())}"
        )
    if cls is FRCWMPlanner:
        return FRCWMPlanner(
            adapter=adapter, config=spec.planner,
            frc_config=spec.frc, baseline_config=spec.baseline,
            rng=rng,
        )
    return cls(
        adapter=adapter, config=spec.planner,
        baseline_config=spec.baseline,
        rng=rng,
    )


# =============================================================================
# 2. RG4FConfig builder per split
# =============================================================================


def _load_base_env_config(path: Optional[str]) -> RG4FConfig:
    """default RG4FConfig + (optional) yaml의 environment 섹션 override."""
    cfg = RG4FConfig()
    if not path:
        return cfg
    p = Path(path)
    if not p.is_file():
        return cfg
    with p.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp) or {}
    env_data = (data.get("environment") or {})
    # generator-friendly key를 RG4FConfig 정확한 필드명으로 변환
    payload: Dict[str, Any] = {}
    for k, v in env_data.items():
        if k == "drift_strength":
            payload["field_mu_drift_sigma"] = float(v)
        elif k == "shift_probability":
            payload["shift_prob_per_room_entry"] = float(v)
            payload["shift_prob_per_checkpoint"] = float(v)
            payload["shift_prob_per_stele_activation"] = float(v)
        elif k == "stochastic_miscontrol_prob":
            payload["miscontrol_p_low"] = float(v)
        elif k in ("field_coupling_type", "task_permutation_mode"):
            continue   # metadata-only
        else:
            payload[k] = v
    # episode_max_steps default 고정 (debug eval용)
    payload.setdefault("episode_max_steps", 600)
    # RG4FConfig.from_dict는 unknown key를 거부
    try:
        return RG4FConfig.from_dict(payload)
    except Exception:
        return cfg


def _build_env_config_for_split(
    base_cfg: RG4FConfig,
    split: SplitSpec,
) -> RG4FConfig:
    """split별 OOD 변형을 RG4FConfig override로 적용.

    지원:
    - ``ood_param_shift``: drift_mu_drift_sigma / shift_prob_*에 multiplier 곱
    - 그 외 OOD: split.config_overrides가 있으면 그대로 적용
    - test_id 등 in-domain: base 그대로

    Notes
    -----
    실제 dataset generator의 split policy를 정확히 일치시키려면 더 복잡한 변형이
    필요하지만, 본 세션에서는 가장 명확한 ``ood_param_shift``만 자동 적용하고
    나머지는 yaml ``config_overrides``로 사용자가 지정하도록 둔다.
    """
    overrides: Dict[str, Any] = dict(split.config_overrides or {})
    if split.name == "ood_param_shift" and not overrides:
        # PART3 §3.24.3: drift / shift parameter를 train range 밖으로
        overrides = {
            "field_mu_drift_sigma": float(base_cfg.field_mu_drift_sigma) * 2.0,
            "shift_prob_per_room_entry": float(base_cfg.shift_prob_per_room_entry) * 2.0,
            "shift_prob_per_checkpoint": float(base_cfg.shift_prob_per_checkpoint) * 2.0,
            "shift_prob_per_stele_activation": float(base_cfg.shift_prob_per_stele_activation) * 2.0,
            "miscontrol_p_low": min(0.5, float(base_cfg.miscontrol_p_low) * 2.0),
        }
    if not overrides:
        return base_cfg
    base_dict = {f.name: getattr(base_cfg, f.name) for f in base_cfg.__dataclass_fields__.values()}
    base_dict.update(overrides)
    return RG4FConfig.from_dict(base_dict)


# =============================================================================
# 3. PlannerEvalRunner
# =============================================================================


class PlannerEvalRunner:
    """top-level evaluation runner.

    실행 결과:
    - <out_dir>/raw_episodes.jsonl
    - <out_dir>/metrics_by_episode.csv
    - <out_dir>/metrics_by_planner.csv
    - <out_dir>/metrics_by_split.csv
    - <out_dir>/aggregate_summary.csv
    - <out_dir>/config_resolved.yaml
    - <out_dir>/planner_traces/<model>__<planner>__<split>__seed<seed>__ep<idx>.jsonl
                  (run.save_traces=true)
    """

    def __init__(
        self,
        config: PlannerEvalConfig,
        *,
        out_dir: str | Path,
        max_episodes_override: Optional[int] = None,
    ) -> None:
        self.config = config
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.trace_dir = self.out_dir / "planner_traces"
        if self.config.run.save_traces:
            self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.max_episodes_override = max_episodes_override

    # ------------------------------------------------------------------
    # public main
    # ------------------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        """모든 (model × planner × split × seed × episode) 조합 실행."""
        results: List[EpisodeResult] = []
        raw_jsonl_path = self.out_dir / "raw_episodes.jsonl"
        with raw_jsonl_path.open("w", encoding="utf-8") as raw_fp:
            for model_spec in self.config.models:
                adapter = self._load_adapter(model_spec)
                base_env_cfg = _load_base_env_config(self.config.base_env_config)
                base_env_cfg = _coerce_max_steps(
                    base_env_cfg, self.config.run.max_steps_per_episode,
                )
                for split in self.config.splits:
                    env_cfg = _build_env_config_for_split(base_env_cfg, split)
                    for seed in split.seeds:
                        n_eps = self._effective_num_episodes(split.num_episodes)
                        for ep in range(n_eps):
                            ep_seed = int(split.seed_base) + int(seed) * 10_000 + int(ep)
                            for planner_spec in self.config.planners:
                                if not self._should_run_planner(planner_spec, model_spec):
                                    continue
                                er = self._run_one(
                                    adapter=adapter,
                                    model_spec=model_spec,
                                    planner_spec=planner_spec,
                                    split=split,
                                    env_cfg=env_cfg,
                                    seed_value=int(seed),
                                    ep_index=int(ep),
                                    env_seed=int(ep_seed),
                                )
                                results.append(er)
                                raw_fp.write(
                                    json.dumps(asdict(er), default=_json_default) + "\n"
                                )
                                raw_fp.flush()
                # release GPU memory between model swaps
                del adapter
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

        # ---- aggregate + write csv ----
        self._write_csv("metrics_by_episode.csv", [asdict(r) for r in results])
        self._write_csv("metrics_by_planner.csv", aggregate_by_planner(results))
        self._write_csv("metrics_by_split.csv", aggregate_by_split(results))
        self._write_csv("aggregate_summary.csv", _aggregate_overall(results))
        # config_resolved
        with (self.out_dir / "config_resolved.yaml").open("w", encoding="utf-8") as fp:
            yaml.safe_dump(_serialize_config(self.config), fp, sort_keys=False, allow_unicode=True)
        return {
            "n_episodes": len(results),
            "raw_jsonl": str(raw_jsonl_path),
            "out_dir": str(self.out_dir),
        }

    # ------------------------------------------------------------------
    # private
    # ------------------------------------------------------------------
    def _effective_num_episodes(self, n: int) -> int:
        if self.max_episodes_override is not None and self.max_episodes_override > 0:
            return min(int(n), int(self.max_episodes_override))
        return int(n)

    def _should_run_planner(self, planner_spec: PlannerSpec, model_spec: ModelSpec) -> bool:
        """variant ablation guard.

        - no_change_point variant 위에서 cp head를 직접 사용하는 baseline (event_only with
          cp signal)은 graceful degrade로 두고, 실행 자체는 막지 않는다 (해당 신호가
          0이라 reactive로 작동).
        """
        return True

    def _load_adapter(self, model_spec: ModelSpec) -> WorldModelAdapter:
        return WorldModelAdapter.load_from_checkpoint(
            model_spec.checkpoint,
            wm_config_path=model_spec.wm_config,
            variant=model_spec.variant,
            device=self.config.run.__dict__.get("device", "auto") if hasattr(self.config.run, "device") else "auto",
        )

    def _run_one(
        self,
        *,
        adapter: WorldModelAdapter,
        model_spec: ModelSpec,
        planner_spec: PlannerSpec,
        split: SplitSpec,
        env_cfg: RG4FConfig,
        seed_value: int,
        ep_index: int,
        env_seed: int,
    ) -> EpisodeResult:
        rng = np.random.default_rng(env_seed + 12345)
        planner = make_planner(planner_spec, adapter=adapter, rng=rng)
        env = RG4FEnv(env_cfg, seed=env_seed)
        episode_id = (
            f"{model_spec.name}__{planner_spec.name}__{split.name}__"
            f"seed{seed_value}__ep{ep_index}"
        )
        trace = PlannerTrace(
            episode_id=episode_id,
            split=split.name,
            model_name=model_spec.name,
            planner_name=planner_spec.name,
            seed=seed_value,
            episode_index=ep_index,
        )
        run_episode(
            env=env,
            planner=planner,
            adapter=adapter,
            planner_config=planner_spec.planner,
            trace=trace,
            seed=env_seed,
            max_steps=int(self.config.run.max_steps_per_episode),
        )
        # save trace
        if self.config.run.save_traces:
            tr_path = self.trace_dir / f"{episode_id}.jsonl"
            trace.write_jsonl(tr_path)
        # episode metrics
        # trace.steps는 StepTrace dataclass list. asdict 변환 후 metric 계산.
        step_dicts = [asdict(s) for s in trace.steps]
        result = compute_episode_metrics(
            trace_steps=step_dicts,
            trace_summary=trace.summary or {},
            episode_id=episode_id,
            split=split.name,
            model_name=model_spec.name,
            planner_name=planner_spec.name,
            seed=seed_value,
            episode_index=ep_index,
        )
        return result

    # ------------------------------------------------------------------
    # CSV writer
    # ------------------------------------------------------------------
    def _write_csv(self, name: str, rows: List[Dict[str, Any]]) -> Path:
        path = self.out_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not rows:
            path.write_text("", encoding="utf-8")
            return path
        # 모든 row의 union key를 header로 사용
        keys: List[str] = []
        seen = set()
        for r in rows:
            for k in r.keys():
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        import csv
        with path.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            for r in rows:
                writer.writerow({
                    k: _csv_value(r.get(k)) for k in keys
                })
        return path


# =============================================================================
# helpers
# =============================================================================


def _coerce_max_steps(cfg: RG4FConfig, max_steps: int) -> RG4FConfig:
    """env max_steps를 평가용으로 override (debug에서 짧게)."""
    base = {f.name: getattr(cfg, f.name) for f in cfg.__dataclass_fields__.values()}
    base["episode_max_steps"] = int(max_steps)
    return RG4FConfig.from_dict(base)


def _aggregate_overall(results: List[EpisodeResult]) -> List[Dict[str, Any]]:
    """planner-only 단일 row + per-(planner, model, split) row 모두 포함."""
    rows: List[Dict[str, Any]] = []
    rows.extend(aggregate_by_split(results))
    rows.extend(aggregate_by_planner(results))
    return rows


def _serialize_config(cfg: PlannerEvalConfig) -> Dict[str, Any]:
    return {
        "meta": {"name": cfg.meta_name, "description": cfg.description},
        "run": {
            "debug": cfg.run.debug, "out_dir": cfg.run.out_dir,
            "max_steps_per_episode": cfg.run.max_steps_per_episode,
            "save_traces": cfg.run.save_traces,
            "save_per_step_logs": cfg.run.save_per_step_logs,
            "skip_existing": cfg.run.skip_existing,
        },
        "models": [asdict(m) for m in cfg.models],
        "planners": [
            {
                "name": p.name, "kind": p.kind,
                "planner": asdict(p.planner),
                "baseline": asdict(p.baseline),
                "frc": asdict(p.frc) if p.kind == "ours_frc" else {},
                "description": p.description,
            } for p in cfg.planners
        ],
        "splits": [
            {
                "name": s.name, "num_episodes": s.num_episodes,
                "seeds": list(s.seeds), "seed_base": s.seed_base,
                "config_overrides": s.config_overrides,
            } for s in cfg.splits
        ],
        "base_env_config": cfg.base_env_config,
    }


def _csv_value(v: Any) -> Any:
    if isinstance(v, (list, tuple, dict)):
        try:
            return json.dumps(v, default=_json_default, ensure_ascii=False)
        except Exception:
            return str(v)
    return v


def _json_default(o: Any) -> Any:
    try:
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, np.generic):
            return o.item()
    except Exception:
        pass
    if hasattr(o, "as_tuple"):
        return o.as_tuple()
    return str(o)


__all__ = ["PlannerEvalRunner", "make_planner"]
