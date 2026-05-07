"""WM Trainer (Session 9).

본 모듈은 RSSM/Dreamer-style WM의 train/valid loop을 구현한다. dataset loader와 model
은 외부 module(`wm/data.py`, `wm/heads.py`)을 그대로 사용한다.

핵심 책임:
    1) optimizer / scheduler / AMP scaler 생성.
    2) stage schedule에 따라 train_loader를 갈아끼우기.
    3) batch → forward → loss → backward → step + metric 로그.
    4) 매 eval_every_steps에 valid_event + valid_uniform 평가.
    5) checkpoint last/step/best/interrupted 저장.
    6) NaN/Inf grad 감지 시 stop + checkpoint.
    7) KeyboardInterrupt 시 interrupt checkpoint.

PART0 정합:
    - test_id/OOD에 절대 접근하지 않는다 (loader 단계 + train_config 단계 다중 차단).
    - collector_metadata 등 forbidden key가 model input에 들어갈 수 없도록 collate가
      hard guard. trainer는 그 guard에 의존한다.
"""
from __future__ import annotations

import json
import math
import os
import platform
import random
import signal
import time
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import torch
from torch import Tensor, nn
from torch.utils.data import DataLoader

from .checkpointing import (
    ManagedCheckpointer,
    capture_rng_state,
    env_summary,
    load_checkpoint,
    model_state_dict_cpu,
    restore_rng_state,
)
from .collate import collate_chunks
from .config import WMConfig
from .data import build_chunk_dataset, build_source_indices
from .data_config import (
    ALLOWED_TRAIN_SPLITS,
    FORBIDDEN_INPUT_KEYS,
    FORBIDDEN_TRAIN_SPLITS,
    EventWindowConfig,
    WMDataConfig,
)
from .env_check import collect_env_report, pick_precision
from .heads import RSSMWorldModel
from .losses import WMLossOutput, compute_total_loss
from .metrics import (
    BinaryConfusion,
    CategoricalAccuracy,
    LossAggregator,
    RunningMean,
    ValidMetrics,
)
from .schedules import build_lr_scheduler
from .train_config import (
    StageScheduleEntry,
    WMTrainConfig,
)


# =============================================================================
# 1. forbidden split / metadata guard (training-script 단의 redundant 방어선)
# =============================================================================


def assert_safe_data_config(cfg: WMDataConfig, *, label: str = "") -> None:
    """data config 안에 절대 train/valid 외 split이 들어가지 못하도록 guard."""
    cfg.validate()   # 내부적으로 source root + manifest + obs_recon_mode 검증
    # 추가 방어: 사용자가 yaml의 다른 키를 통해 forbidden split을 끼워넣었는지 검사할 게 없으므로
    # 본 구현에서는 위로 충분 (data_config / SourceIndex / ChunkDataset 다중 차단).


def assert_safe_inputs(inputs: Mapping[str, Tensor]) -> None:
    """training step 단에서도 inputs dict이 forbidden key를 갖지 않는지 redundant 검사.

    collate.py에서 1차로 막지만, trainer 단에서 한 번 더 확인하여 silent leak 위험을 줄인다.
    """
    leaked = [k for k in inputs.keys() if k in FORBIDDEN_INPUT_KEYS]
    if leaked:
        raise RuntimeError(
            f"Forbidden key(s) leaked into training inputs: {leaked}. "
            f"FORBIDDEN_INPUT_KEYS = {FORBIDDEN_INPUT_KEYS}"
        )


# =============================================================================
# 2. precision context
# =============================================================================


@dataclass
class PrecisionContext:
    name: str            # bf16 | fp16 | fp32
    autocast_dtype: Optional[torch.dtype]
    use_grad_scaler: bool


def make_precision_context(name: str, *, device: str) -> PrecisionContext:
    name = name.lower()
    if name == "bf16" and device == "cuda":
        return PrecisionContext(name="bf16", autocast_dtype=torch.bfloat16, use_grad_scaler=False)
    if name == "fp16" and device == "cuda":
        return PrecisionContext(name="fp16", autocast_dtype=torch.float16, use_grad_scaler=True)
    if name == "fp32" or device == "cpu":
        return PrecisionContext(name="fp32", autocast_dtype=None, use_grad_scaler=False)
    return PrecisionContext(name="fp32", autocast_dtype=None, use_grad_scaler=False)


# =============================================================================
# 3. valid loader builder
# =============================================================================


def make_uniform_event_window_config(base_data_cfg: WMDataConfig) -> WMDataConfig:
    """valid_uniform용으로 event_window를 uniform-only로 변경한 새 WMDataConfig 반환."""
    import copy
    new_cfg = copy.deepcopy(base_data_cfg)
    new_cfg.event_window = EventWindowConfig(
        enabled=False,                     # off → 항상 uniform fallback
        window_radius=base_data_cfg.event_window.window_radius,
        change_point_prob=0.0,
        shift_prob=0.0,
        reveal_prob=0.0,
        success_prob=0.0,
        uniform_prob=1.0,
        raw_eff_mismatch_subsample_max=base_data_cfg.event_window.raw_eff_mismatch_subsample_max,
    )
    # sample_weight도 uniform: boost factor 1.0으로 (loss가 chunk 안 모든 valid tick을 동일 가중)
    new_cfg.sample_weight.change_point_boost = 1.0
    new_cfg.sample_weight.shift_boost = 1.0
    new_cfg.sample_weight.reveal_boost = 1.0
    new_cfg.sample_weight.success_boost = 1.0
    new_cfg.sample_weight.raw_eff_mismatch_boost = 1.0
    return new_cfg


def build_train_loader(
    data_cfg_path: str,
    *,
    batch_size: int,
    num_workers: int,
    chunk_len_override: Optional[int] = None,
    epoch: int = 0,
) -> Tuple[WMDataConfig, DataLoader]:
    cfg = WMDataConfig.from_yaml(data_cfg_path)
    if chunk_len_override is not None:
        cfg.train.chunk_len = int(chunk_len_override)
        cfg.valid.chunk_len = int(chunk_len_override)
    assert_safe_data_config(cfg, label="train")
    sources = build_source_indices(cfg)
    ds = build_chunk_dataset(cfg, "train", epoch=epoch, sources=sources)
    loader = DataLoader(
        ds,
        batch_size=batch_size,
        num_workers=int(num_workers),
        collate_fn=collate_chunks,
        drop_last=False,
    )
    return cfg, loader


def build_valid_loaders(
    *,
    valid_event_data_cfg_path: str,
    valid_uniform_data_cfg_path: str,
    batch_size: int,
    num_workers: int,
    chunk_len_override: Optional[int] = None,
) -> Dict[str, DataLoader]:
    out: Dict[str, DataLoader] = {}

    # event-window (Session 8 default)
    cfg_event = WMDataConfig.from_yaml(valid_event_data_cfg_path)
    if chunk_len_override is not None:
        cfg_event.train.chunk_len = int(chunk_len_override)
        cfg_event.valid.chunk_len = int(chunk_len_override)
    assert_safe_data_config(cfg_event, label="valid_event")
    sources_event = build_source_indices(cfg_event)
    ds_event = build_chunk_dataset(cfg_event, "valid", epoch=0, sources=sources_event)
    out["valid_event"] = DataLoader(
        ds_event, batch_size=batch_size, num_workers=int(num_workers),
        collate_fn=collate_chunks, drop_last=False,
    )

    # uniform (event-window off, sample_weight boost 1.0)
    cfg_uni_base = WMDataConfig.from_yaml(valid_uniform_data_cfg_path)
    if chunk_len_override is not None:
        cfg_uni_base.train.chunk_len = int(chunk_len_override)
        cfg_uni_base.valid.chunk_len = int(chunk_len_override)
    cfg_uni = make_uniform_event_window_config(cfg_uni_base)
    assert_safe_data_config(cfg_uni, label="valid_uniform")
    sources_uni = build_source_indices(cfg_uni)
    ds_uni = build_chunk_dataset(cfg_uni, "valid", epoch=0, sources=sources_uni)
    out["valid_uniform"] = DataLoader(
        ds_uni, batch_size=batch_size, num_workers=int(num_workers),
        collate_fn=collate_chunks, drop_last=False,
    )
    return out


# =============================================================================
# 4. stage scheduler
# =============================================================================


@dataclass
class StageState:
    name: str
    data_config: str
    loader: DataLoader
    iterator: Iterator
    data_cfg: WMDataConfig


def stages_from_config(train_cfg: WMTrainConfig, *, epoch: int = 0) -> Dict[str, StageState]:
    """stage_schedule 항목별로 train loader를 미리 만든다 (lazy iterator 포함)."""
    out: Dict[str, StageState] = {}
    for entry in train_cfg.stage_schedule:
        cfg, loader = build_train_loader(
            entry.data_config,
            batch_size=train_cfg.batch_size,
            num_workers=train_cfg.num_workers,
            chunk_len_override=train_cfg.chunk_len,
            epoch=epoch,
        )
        out[entry.name] = StageState(
            name=entry.name,
            data_config=entry.data_config,
            loader=loader,
            iterator=iter(loader),
            data_cfg=cfg,
        )
    return out


# =============================================================================
# 5. Trainer
# =============================================================================


class Trainer:
    """RSSM/Dreamer-style WM trainer. one process, single-GPU 가정."""

    def __init__(
        self,
        train_cfg: WMTrainConfig,
        wm_cfg: WMConfig,
        *,
        run_name: str,
        resume_from: Optional[str] = None,
        log: bool = True,
    ) -> None:
        train_cfg.validate()
        self.train_cfg = train_cfg
        self.wm_cfg = wm_cfg.apply_variant(train_cfg.variant)
        self.run_name = run_name
        self.run_dir = Path(train_cfg.output_root) / run_name
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.log = log

        # ---- env / device / precision ----
        env = collect_env_report(cwd=str(Path.cwd()))
        if train_cfg.device == "auto":
            self.device = torch.device("cuda" if env.gpu.available else "cpu")
        else:
            self.device = torch.device(train_cfg.device)
        precision_name = pick_precision(env.gpu, train_cfg.precision)
        self.precision = make_precision_context(precision_name, device=str(self.device.type))

        # ---- seed ----
        _seed_everything(train_cfg.seed)

        # ---- model ----
        self.model = RSSMWorldModel(self.wm_cfg).to(self.device)

        # ---- optimizer / scheduler / scaler ----
        self.optimizer = self._build_optimizer()
        self.scheduler = build_lr_scheduler(
            self.optimizer,
            name=train_cfg.scheduler.name,
            warmup_steps=train_cfg.scheduler.warmup_steps,
            total_steps=train_cfg.max_steps,
            min_lr_factor=train_cfg.scheduler.min_lr_factor,
        )
        self.scaler = torch.amp.GradScaler("cuda") if self.precision.use_grad_scaler else None

        # ---- checkpointer ----
        self.ckpt = ManagedCheckpointer(
            self.run_dir,
            keep_last_n=train_cfg.checkpoint.keep_last_n,
            keep_best_n=train_cfg.checkpoint.keep_best_n,
            best_metric_keys=train_cfg.checkpoint.best_metric_keys,
            best_metric_modes=train_cfg.checkpoint.best_metric_modes,
        )

        # ---- step counters ----
        self.global_step: int = 0
        self.best_metrics: Dict[str, float] = {}
        self.consecutive_overweight: int = 0

        # ---- valid loaders ----
        self.valid_loaders = build_valid_loaders(
            valid_event_data_cfg_path=train_cfg.eval.valid_event_data_config,
            valid_uniform_data_cfg_path=train_cfg.eval.valid_uniform_data_config,
            batch_size=train_cfg.batch_size,
            num_workers=train_cfg.num_workers,
            chunk_len_override=train_cfg.chunk_len,
        )

        # ---- stage loaders ----
        self.stages: Dict[str, StageState] = stages_from_config(train_cfg, epoch=0)

        # ---- log files ----
        self.train_log_path = self.run_dir / "train_log.jsonl"
        self.valid_log_path = self.run_dir / "valid_log.jsonl"
        self.metrics_csv_path = self.run_dir / "metrics.csv"
        self.config_resolved_path = self.run_dir / "config_resolved.yaml"
        self.env_report_path = self.run_dir / "env_report.json"

        # config_resolved 저장
        _write_yaml(self.config_resolved_path, {
            "train_config": _dataclass_to_simple(train_cfg),
            "wm_config": {"name": self.wm_cfg.meta.name, "variant": train_cfg.variant,
                          "scale": self.wm_cfg.meta.scale,
                          "feature_dim": int(self.wm_cfg.feature_dim)},
            "device": str(self.device),
            "precision": self.precision.name,
            "run_dir": str(self.run_dir),
        })
        # env report
        with self.env_report_path.open("w", encoding="utf-8") as fp:
            json.dump(env.to_dict(), fp, indent=2)

        # ---- resume ----
        if resume_from:
            self._resume_from(resume_from)

    # ---------------------------------------------------------------------
    # build helpers
    # ---------------------------------------------------------------------
    def _build_optimizer(self) -> torch.optim.Optimizer:
        opt_cfg = self.train_cfg.optimizer
        params = [p for p in self.model.parameters() if p.requires_grad]
        if opt_cfg.name.lower() != "adamw":
            raise ValueError(f"unsupported optimizer: {opt_cfg.name!r} (only adamw)")
        return torch.optim.AdamW(
            params,
            lr=opt_cfg.lr,
            weight_decay=opt_cfg.weight_decay,
            betas=tuple(opt_cfg.betas),
            eps=opt_cfg.eps,
        )

    # ---------------------------------------------------------------------
    # resume
    # ---------------------------------------------------------------------
    def _resume_from(self, path: str) -> None:
        state = load_checkpoint(path, map_location=self.device)
        self.model.load_state_dict(state["model"])
        self.optimizer.load_state_dict(state["optimizer"])
        self.scheduler.load_state_dict(state["scheduler"])
        if state.get("scaler") is not None and self.scaler is not None:
            self.scaler.load_state_dict(state["scaler"])
        if state.get("rng") is not None:
            restore_rng_state(state["rng"])
        self.global_step = int(state.get("global_step", 0))
        self.best_metrics = dict(state.get("best_metrics", {}) or {})
        self._log_console(f"[resume] from {path}, global_step={self.global_step}")

    # ---------------------------------------------------------------------
    # main run
    # ---------------------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        """학습 루프. KeyboardInterrupt를 받으면 interrupt checkpoint 저장 후 종료."""
        start_t = time.time()
        try:
            while self.global_step < self.train_cfg.max_steps:
                self._train_one_step()

                if (self.global_step % max(1, self.train_cfg.eval.eval_every_steps)) == 0:
                    self._eval_and_log()

                if (self.global_step % max(1, self.train_cfg.checkpoint.save_every_steps)) == 0:
                    self._save_step()

        except KeyboardInterrupt:
            self._log_console("[trainer] KeyboardInterrupt — saving interrupted checkpoint...")
            self._save_interrupted()
            raise
        except (RuntimeError, ValueError) as exc:
            # NaN/Inf 등은 _train_one_step에서 raise됨. 마지막 checkpoint 저장 후 raise.
            self._log_console(f"[trainer] FATAL: {exc} — saving last checkpoint...")
            self._save_step()
            raise

        # 마지막 평가 + 저장
        self._eval_and_log()
        self._save_step()
        elapsed = time.time() - start_t
        summary = {
            "global_step": self.global_step,
            "elapsed_sec": elapsed,
            "best_metrics": dict(self.best_metrics),
            "run_dir": str(self.run_dir),
        }
        _write_yaml(self.run_dir / "run_summary.yaml", summary)
        return summary

    # ---------------------------------------------------------------------
    # one training step
    # ---------------------------------------------------------------------
    def _train_one_step(self) -> None:
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        accum = max(1, self.train_cfg.grad_accum_steps)

        loss_agg = LossAggregator()
        sw_max = 0.0
        sw_mean = 0.0
        sample_weight_total_count = 0
        source_dist: Dict[str, int] = {}
        sampler_type_dist: Dict[str, int] = {}

        # stage 결정
        stage_entry = self.train_cfg.stage_for_step(self.global_step)
        stage = self.stages[stage_entry.name]

        step_t0 = time.time()
        for accum_idx in range(accum):
            batch = self._next_batch(stage)
            assert_safe_inputs(batch["inputs"])
            self._track_batch_meta(batch, source_dist, sampler_type_dist)
            sw = batch["sample_weight"]
            sw_max = max(sw_max, float(sw.max().item()))
            sw_mean += float(sw.mean().item())
            sample_weight_total_count += 1

            inputs = {k: v.to(self.device, non_blocking=True) for k, v in batch["inputs"].items()}
            targets = self._prepare_targets(batch)
            sw_dev = sw.to(self.device, non_blocking=True)

            with self._autocast():
                out = self.model(inputs)
                loss_out = compute_total_loss(
                    out, targets, self.wm_cfg.loss, sample_weight=sw_dev,
                )
            total = loss_out.total / accum

            self._check_loss_finite(loss_out)
            if self.scaler is not None:
                self.scaler.scale(total).backward()
            else:
                total.backward()
            loss_agg.update(loss_out.components, loss_out.total, weight=1.0 / accum)

        # grad clip + step
        if self.scaler is not None:
            self.scaler.unscale_(self.optimizer)
        grad_norm = torch.nn.utils.clip_grad_norm_(
            self.model.parameters(),
            max_norm=float(self.train_cfg.stability.grad_clip),
        )
        self._check_grad_finite(grad_norm)

        if self.scaler is not None:
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            self.optimizer.step()
        self.scheduler.step()

        self.global_step += 1
        elapsed = time.time() - step_t0

        # over-weight monitor
        agg = loss_agg.compute()
        cp_ratio = agg.get("change_point", 0.0) / max(1e-9, agg.get("total", 1.0))
        if cp_ratio > self.train_cfg.stability.overweight_warn_ratio:
            self.consecutive_overweight += 1
        else:
            self.consecutive_overweight = 0

        # log
        if self.global_step == 1 or (self.global_step % max(1, self.train_cfg.log_every_steps)) == 0:
            self._log_train_step(
                stage_entry=stage_entry,
                loss_agg=agg,
                grad_norm=float(grad_norm.item()) if torch.is_tensor(grad_norm) else float(grad_norm),
                step_time=elapsed,
                source_dist=source_dist,
                sampler_type_dist=sampler_type_dist,
                sw_max=sw_max,
                sw_mean=(sw_mean / max(1, sample_weight_total_count)),
                cp_ratio=cp_ratio,
            )

    def _track_batch_meta(self, batch, source_dist, sampler_type_dist):
        meta = batch.get("meta", {})
        for s in meta.get("source_name", []):
            source_dist[s] = source_dist.get(s, 0) + 1
        for s in meta.get("sampler_type", []):
            sampler_type_dist[s] = sampler_type_dist.get(s, 0) + 1

    def _next_batch(self, stage: StageState):
        try:
            batch = next(stage.iterator)
        except StopIteration:
            stage.iterator = iter(stage.loader)
            batch = next(stage.iterator)
        return batch

    # ---------------------------------------------------------------------
    # done target 분리 (Session 9 PATCH)
    # ---------------------------------------------------------------------
    def _prepare_targets(self, batch: Mapping[str, Any]) -> Dict[str, Tensor]:
        """training_config.done_target_mode에 따라 targets["done"]을 재정의한다.

        Done family (collate에서 분리 노출됨):
            success_done = dones.float()           ← 진짜 task 성공 종료
            truncated    = truncateds.float()      ← timeout (시간 초과)
            terminal     = (dones | truncateds).float()
            done         = success_done            ← backward-compat default

        ``done_target_mode`` 동작:
            - "success_done" (default, 권장): targets["done"] := targets["success_done"].
              world model의 done_logit이 진짜 task 성공만 학습하도록 한다 (timeout으로 인한
              truncated를 success로 오해 학습하지 않게).
            - "terminal": targets["done"] := targets["terminal"].
              done_logit을 sequence stop 신호 학습용으로 사용. 메인 권장 경로 아님.

        ``terminal``은 어떤 mode에서도 별도 key로 유지되며, 후속 모듈이 rollout stop /
        sequence mask / 분석용 (성공 라벨로 *해석하지 않음*)으로 사용 가능하다.
        """
        targets = {k: v.to(self.device, non_blocking=True) for k, v in batch["targets"].items()}
        mode = self.train_cfg.done_target_mode
        if mode == "success_done":
            targets["done"] = targets["success_done"]
        elif mode == "terminal":
            targets["done"] = targets["terminal"]
        else:
            # train_config.validate에서 이미 거름. 방어적으로 raise.
            raise ValueError(f"unknown done_target_mode: {mode!r}")
        # terminal/success_done/truncated는 그대로 둔다 (분석/평가에서 사용).
        return targets

    # ---------------------------------------------------------------------
    # eval
    # ---------------------------------------------------------------------
    @torch.no_grad()
    def _eval_loader(self, loader: DataLoader, max_batches: int) -> ValidMetrics:
        self.model.eval()
        loss_agg = LossAggregator()
        regime_acc = CategoricalAccuracy()
        cp_conf = BinaryConfusion()
        sh_conf = BinaryConfusion()
        rv_conf = BinaryConfusion()
        mm_conf = BinaryConfusion()
        # done family (Session 9 PATCH): success_done / terminal 분리 평가 + truncated rate
        success_done_conf = BinaryConfusion()
        terminal_conf = BinaryConfusion()
        truncated_rate = RunningMean()    # truncated tick의 평균 비율 (analysis용)
        reward_se = RunningMean()
        state_se = RunningMean()
        n_seen = 0
        for batch in loader:
            if n_seen >= max_batches:
                break
            n_seen += 1
            assert_safe_inputs(batch["inputs"])
            inputs = {k: v.to(self.device, non_blocking=True) for k, v in batch["inputs"].items()}
            targets = self._prepare_targets(batch)
            sw = batch["sample_weight"].to(self.device, non_blocking=True)
            with self._autocast():
                out = self.model(inputs)
                loss_out = compute_total_loss(out, targets, self.wm_cfg.loss, sample_weight=sw)
            loss_agg.update(loss_out.components, loss_out.total, weight=1.0)

            # binary metrics — valid_mask로 padding 제외
            mask = batch["valid_mask"].to(self.device, non_blocking=True)
            if "regime_logits" in out:
                regime_acc.update(
                    out["regime_logits"], targets["true_regime_control_mode"], mask=mask,
                )
            if "change_point_logit" in out:
                cp_conf.update(
                    out["change_point_logit"], targets["change_point"],
                    mask=mask, threshold=0.0,
                )
            if "shift_logit" in out:
                sh_conf.update(
                    out["shift_logit"], targets["shift_event"],
                    mask=mask, threshold=0.0,
                )
            if "reveal_logit" in out:
                rv_conf.update(
                    out["reveal_logit"], targets["reveal_event"],
                    mask=mask, threshold=0.0,
                )
            if "raw_eff_mismatch_logit" in out:
                mm_conf.update(
                    out["raw_eff_mismatch_logit"], targets["raw_eff_mismatch"],
                    mask=mask, threshold=0.0,
                )
            # done family 분리 평가: done_logit 1개로 두 target에 대한 metric을 모두 계산.
            # 권장 mode(success_done)에서는 success_done이 main metric이고 terminal은 보조.
            # mode=terminal일 때는 그 반대.
            if "done_logit" in out:
                if "success_done" in targets:
                    success_done_conf.update(
                        out["done_logit"], targets["success_done"],
                        mask=mask, threshold=0.0,
                    )
                if "terminal" in targets:
                    terminal_conf.update(
                        out["done_logit"], targets["terminal"],
                        mask=mask, threshold=0.0,
                    )
            if "truncated" in targets:
                # tick-level truncated rate (mask=valid)
                t = targets["truncated"]
                truncated_rate.update(
                    float((t * mask).sum().item()),
                    weight=float(mask.sum().item()),
                )
            if "reward_pred" in out:
                err = (out["reward_pred"] - targets["reward"]) ** 2
                reward_se.update(float((err * mask).sum().item()), weight=float(mask.sum().item()))
            if "state_pred" in out:
                err = ((out["state_pred"] - targets["true_state"]) ** 2).mean(dim=-1)
                state_se.update(float((err * mask).sum().item()), weight=float(mask.sum().item()))

        binary: Dict[str, Dict[str, float]] = {
            "change_point": cp_conf.compute(),
            "shift": sh_conf.compute(),
            "reveal": rv_conf.compute(),
            "raw_eff_mismatch": mm_conf.compute(),
            # done family
            "success_done": success_done_conf.compute(),
            "terminal": terminal_conf.compute(),
        }
        # truncated rate는 binary 그룹 안에 별도로 노출 (단일 scalar)
        binary["truncated"] = {"rate": float(truncated_rate.compute())}

        metrics = ValidMetrics(
            loss_mean=loss_agg.compute(),
            state_mse=float(state_se.compute()),
            reward_mse=float(reward_se.compute()),
            regime_accuracy=float(regime_acc.compute().get("accuracy", 0.0)),
            binary=binary,
            n_batches=n_seen,
        )
        return metrics

    def _eval_and_log(self) -> None:
        flat: Dict[str, float] = {}
        for name, loader in self.valid_loaders.items():
            max_b = (
                self.train_cfg.eval.valid_event_max_batches if name == "valid_event"
                else self.train_cfg.eval.valid_uniform_max_batches
            )
            m = self._eval_loader(loader, max_batches=max_b)
            flat.update(m.to_flat(name))
        # train-valid gap (loss)
        # train의 마지막 epoch loss는 train_log에서 직접 합산하지 않고, 단순히 valid_uniform/total_loss를
        # train_total_loss(가장 최근 step)와 비교 가능. 본 함수에서는 valid 결과만 기록.
        self._append_jsonl(self.valid_log_path, {
            "global_step": self.global_step,
            **flat,
        })
        # 콘솔 짧게 (PATCH: done family 분리 표시)
        self._log_console(
            f"[valid] step={self.global_step} "
            f"uni_total={flat.get('valid_uniform/loss/total', float('nan')):.3f} "
            f"event_total={flat.get('valid_event/loss/total', float('nan')):.3f} "
            f"cp_f1(event)={flat.get('valid_event/change_point/f1', 0.0):.3f} "
            f"done_mode={self.train_cfg.done_target_mode} "
            f"sd_f1(uni)={flat.get('valid_uniform/success_done/f1', 0.0):.3f} "
            f"term_f1(uni)={flat.get('valid_uniform/terminal/f1', 0.0):.3f} "
            f"trunc_rate(uni)={flat.get('valid_uniform/truncated/rate', 0.0):.4f}"
        )
        # best 갱신 + checkpoint
        self.best_metrics.update({k: float(v) for k, v in flat.items() if isinstance(v, (int, float))})
        state = self._collect_state_for_checkpoint()
        saved = self.ckpt.maybe_save_best(state, flat)
        if saved:
            self._log_console(f"[ckpt] best updated: {[str(p.name) for p in saved]}")

    # ---------------------------------------------------------------------
    # checkpoint helpers
    # ---------------------------------------------------------------------
    def _collect_state_for_checkpoint(self) -> Dict[str, Any]:
        return {
            "model": model_state_dict_cpu(self.model),
            "optimizer": self.optimizer.state_dict(),
            "scheduler": self.scheduler.state_dict(),
            "scaler": self.scaler.state_dict() if self.scaler is not None else None,
            "wm_config": _dataclass_to_simple(self.wm_cfg),
            "train_config": _dataclass_to_simple(self.train_cfg),
            "variant": self.train_cfg.variant,
            "global_step": self.global_step,
            "epoch": 0,
            "best_metrics": dict(self.best_metrics),
            "rng": capture_rng_state(),
            "env_summary": env_summary(),
            "git_commit": None,
            "schema_version": 1,
        }

    def _save_step(self) -> None:
        state = self._collect_state_for_checkpoint()
        last, step = self.ckpt.save_step(state, self.global_step)
        self._log_console(f"[ckpt] saved last={last.name} step={step.name}")

    def _save_interrupted(self) -> None:
        state = self._collect_state_for_checkpoint()
        path = self.ckpt.save_interrupted(state, self.global_step)
        self._log_console(f"[ckpt] saved interrupted={path.name}")

    # ---------------------------------------------------------------------
    # autocast / safety
    # ---------------------------------------------------------------------
    def _autocast(self):
        if self.precision.autocast_dtype is None or str(self.device.type) == "cpu":
            return nullcontext()
        return torch.amp.autocast("cuda", dtype=self.precision.autocast_dtype)

    def _check_loss_finite(self, loss_out: WMLossOutput) -> None:
        v = float(loss_out.total.detach().item())
        if math.isnan(v) or math.isinf(v):
            self._log_console(
                f"[FATAL] loss is NaN/Inf at step {self.global_step}. components="
                + json.dumps({k: float(t.detach().item()) for k, t in loss_out.components.items()})
            )
            raise RuntimeError(f"loss not finite: total={v}")

    def _check_grad_finite(self, grad_norm) -> None:
        v = float(grad_norm.item()) if torch.is_tensor(grad_norm) else float(grad_norm)
        if math.isnan(v) or math.isinf(v):
            if self.train_cfg.stability.nan_action == "skip":
                self.optimizer.zero_grad(set_to_none=True)
                return
            raise RuntimeError(f"grad_norm not finite at step {self.global_step}: {v}")

    # ---------------------------------------------------------------------
    # logging utility
    # ---------------------------------------------------------------------
    def _log_train_step(
        self,
        *,
        stage_entry: StageScheduleEntry,
        loss_agg: Dict[str, float],
        grad_norm: float,
        step_time: float,
        source_dist: Dict[str, int],
        sampler_type_dist: Dict[str, int],
        sw_max: float,
        sw_mean: float,
        cp_ratio: float,
    ) -> None:
        gpu_alloc = 0
        gpu_reserved = 0
        if torch.cuda.is_available():
            gpu_alloc = int(torch.cuda.memory_allocated())
            gpu_reserved = int(torch.cuda.memory_reserved())
        record = {
            "global_step": self.global_step,
            "stage": stage_entry.name,
            "stage_data_config": stage_entry.data_config,
            "lr": float(self.optimizer.param_groups[0]["lr"]),
            "precision": self.precision.name,
            "batch_size": self.train_cfg.batch_size,
            "chunk_len": self.train_cfg.chunk_len,
            "grad_accum_steps": self.train_cfg.grad_accum_steps,
            "done_target_mode": self.train_cfg.done_target_mode,   # PATCH
            "source_dist": source_dist,
            "sampler_type_dist": sampler_type_dist,
            "sample_weight": {"mean": sw_mean, "max": sw_max},
            "loss": loss_agg,
            "loss_change_point_ratio": cp_ratio,
            "grad_norm": grad_norm,
            "gpu_memory_allocated": gpu_alloc,
            "gpu_memory_reserved": gpu_reserved,
            "step_time_sec": step_time,
            "consecutive_overweight": self.consecutive_overweight,
        }
        self._append_jsonl(self.train_log_path, record)
        self._log_console(
            f"[step {self.global_step}] stage={stage_entry.name} loss={loss_agg.get('total', 0.0):.3f} "
            f"cp={loss_agg.get('change_point', 0.0):.3f} (cp/total={cp_ratio:.2f}) "
            f"grad={grad_norm:.2f} t={step_time:.2f}s"
        )
        if self.consecutive_overweight >= self.train_cfg.stability.overweight_warn_consecutive:
            self._log_console(
                f"[WARN] change_point loss has dominated >50% for {self.consecutive_overweight} consecutive steps"
            )

    def _append_jsonl(self, path: Path, record: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, default=_json_default) + "\n")

    def _log_console(self, msg: str) -> None:
        if self.log:
            print(msg, flush=True)


# =============================================================================
# 6. helpers
# =============================================================================


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _json_default(o: Any) -> Any:
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (Path,)):
        return str(o)
    return str(o)


def _dataclass_to_simple(obj: Any) -> Any:
    """dataclass tree를 dict/list/scalar로 직렬화 (yaml.safe_dump 가능)."""
    from dataclasses import is_dataclass, fields
    if is_dataclass(obj):
        out = {}
        for f in fields(obj):
            out[f.name] = _dataclass_to_simple(getattr(obj, f.name))
        return out
    if isinstance(obj, (list, tuple)):
        return [_dataclass_to_simple(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _dataclass_to_simple(v) for k, v in obj.items()}
    if isinstance(obj, Path):
        return str(obj)
    return obj


def _write_yaml(path: Path, data: Dict[str, Any]) -> None:
    import yaml
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        yaml.safe_dump(data, fp, sort_keys=False, allow_unicode=False)


__all__ = [
    "Trainer",
    "PrecisionContext",
    "make_precision_context",
    "build_train_loader",
    "build_valid_loaders",
    "make_uniform_event_window_config",
    "stages_from_config",
    "assert_safe_data_config",
    "assert_safe_inputs",
]
