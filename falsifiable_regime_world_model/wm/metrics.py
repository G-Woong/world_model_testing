"""Lightweight metrics for WM validation (Session 9).

본 모듈은 학습 루프 / valid 루프에서 per-batch metric을 누적해 epoch end에 평균/F1/AUC를
계산하기 위한 헬퍼만 제공한다.

PART3 §3.25 (Switch Detection F1, action-flip metric 등)와 정합. change_point/shift는
tick-level positive가 매우 희소하므로 accuracy만 보면 안 되고 precision/recall/F1을 함께
보고한다.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional

import numpy as np
import torch
from torch import Tensor


# =============================================================================
# 1. binary classification metric (logit + threshold)
# =============================================================================


@dataclass
class BinaryConfusion:
    """누적 binary classification 통계.

    threshold는 logit > 0 (= sigmoid > 0.5)을 기본. mask가 주어지면 mask=1 위치만 집계.
    """
    tp: float = 0.0
    fp: float = 0.0
    fn: float = 0.0
    tn: float = 0.0

    def update(
        self,
        logit: Tensor,
        target: Tensor,
        mask: Optional[Tensor] = None,
        threshold: float = 0.0,
    ) -> None:
        with torch.no_grad():
            pred = (logit > threshold)
            tgt = (target > 0.5)
            if mask is not None:
                m = (mask > 0).to(torch.bool)
                pred = pred & m
                tgt = tgt & m
                # 'invalid' 위치는 모두 0으로 (TP/FP/FN/TN 대상에서 제외)
                # 단순 구현: tn 계산을 mask 포함 위치만 카운트.
                valid_count = m.sum().item()
            else:
                m = torch.ones_like(pred, dtype=torch.bool)
                valid_count = pred.numel()

            tp = (pred & tgt & m).sum().item()
            fp = (pred & ~tgt & m).sum().item()
            fn = (~pred & tgt & m).sum().item()
            tn = max(0, valid_count - tp - fp - fn)

            self.tp += float(tp)
            self.fp += float(fp)
            self.fn += float(fn)
            self.tn += float(tn)

    def compute(self) -> Dict[str, float]:
        eps = 1e-9
        precision = self.tp / max(eps, self.tp + self.fp)
        recall = self.tp / max(eps, self.tp + self.fn)
        f1 = 2.0 * precision * recall / max(eps, precision + recall)
        accuracy = (self.tp + self.tn) / max(eps, self.tp + self.fp + self.fn + self.tn)
        positives = self.tp + self.fn
        return {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "accuracy": float(accuracy),
            "positives": float(positives),
            "tp": float(self.tp),
            "fp": float(self.fp),
            "fn": float(self.fn),
            "tn": float(self.tn),
        }


# =============================================================================
# 2. categorical accuracy (regime)
# =============================================================================


@dataclass
class CategoricalAccuracy:
    correct: float = 0.0
    total: float = 0.0

    def update(self, logits: Tensor, target: Tensor, mask: Optional[Tensor] = None) -> None:
        with torch.no_grad():
            pred = torch.argmax(logits, dim=-1)
            ok = (pred == target).to(torch.float32)
            if mask is not None:
                m = (mask > 0).to(torch.float32)
                self.correct += float((ok * m).sum().item())
                self.total += float(m.sum().item())
            else:
                self.correct += float(ok.sum().item())
                self.total += float(ok.numel())

    def compute(self) -> Dict[str, float]:
        if self.total <= 0:
            return {"accuracy": 0.0, "total": 0.0}
        return {"accuracy": self.correct / self.total, "total": self.total}


# =============================================================================
# 3. running mean
# =============================================================================


@dataclass
class RunningMean:
    """가중 평균 (sample 단위 weight 가능)."""
    sum: float = 0.0
    count: float = 0.0

    def update(self, value: float, weight: float = 1.0) -> None:
        if weight <= 0:
            return
        self.sum += float(value) * float(weight)
        self.count += float(weight)

    def compute(self) -> float:
        return float(self.sum / self.count) if self.count > 0 else 0.0


# =============================================================================
# 4. component-loss aggregator
# =============================================================================


@dataclass
class LossAggregator:
    """compute_total_loss의 components dict을 step 단위로 누적한다."""
    means: Dict[str, RunningMean] = field(default_factory=lambda: defaultdict(RunningMean))

    def update(self, components: Mapping[str, Tensor], total: Tensor, weight: float = 1.0) -> None:
        with torch.no_grad():
            for k, v in components.items():
                self.means[k].update(float(v.detach().item()), weight=weight)
            self.means["total"].update(float(total.detach().item()), weight=weight)

    def compute(self) -> Dict[str, float]:
        return {k: v.compute() for k, v in self.means.items()}


# =============================================================================
# 5. valid metric snapshot
# =============================================================================


@dataclass
class ValidMetrics:
    """valid_event 또는 valid_uniform 단일 평가의 결과."""
    loss_mean: Dict[str, float] = field(default_factory=dict)
    state_mse: float = 0.0
    reward_mse: float = 0.0
    regime_accuracy: float = 0.0
    binary: Dict[str, Dict[str, float]] = field(default_factory=dict)
    n_batches: int = 0

    def to_flat(self, prefix: str) -> Dict[str, float]:
        """jsonl/csv용 평탄 dict. 모든 key는 ``prefix/...`` 로 prefix를 붙인다."""
        flat: Dict[str, float] = {}
        for k, v in self.loss_mean.items():
            flat[f"{prefix}/loss/{k}"] = v
        flat[f"{prefix}/reward/mse"] = self.reward_mse
        flat[f"{prefix}/state/mse"] = self.state_mse
        flat[f"{prefix}/regime/accuracy"] = self.regime_accuracy
        for name, d in self.binary.items():
            for kk, vv in d.items():
                flat[f"{prefix}/{name}/{kk}"] = vv
        flat[f"{prefix}/n_batches"] = float(self.n_batches)
        return flat


# =============================================================================
# 6. helper: total / n_batches reset of LossAggregator
# =============================================================================


def reset_aggregators(*aggs) -> None:
    for a in aggs:
        if isinstance(a, LossAggregator):
            a.means = defaultdict(RunningMean)


__all__ = [
    "BinaryConfusion",
    "CategoricalAccuracy",
    "RunningMean",
    "LossAggregator",
    "ValidMetrics",
    "reset_aggregators",
]
