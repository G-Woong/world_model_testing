"""LR schedules + stage scheduler for WM training.

본 모듈은 ``torch.optim.lr_scheduler.LambdaLR``로 동작하는 가벼운 schedule 함수와,
``WMTrainConfig.stage_schedule``을 step → stage entry로 매핑하는 stage 헬퍼만 제공한다.

학습 loop는 본 모듈을 직접 호출한다 — checkpoint resume에서도 그대로 동작한다 (
LambdaLR은 last_epoch만 기록되므로 step 기반 closure 함수가 동일하면 OK).
"""
from __future__ import annotations

import math
from typing import Callable

from torch.optim import Optimizer
from torch.optim.lr_scheduler import LambdaLR


# =============================================================================
# 1. lr lambdas
# =============================================================================


def warmup_cosine_lambda(warmup_steps: int, total_steps: int, min_lr_factor: float) -> Callable[[int], float]:
    """linear warmup + cosine decay to ``min_lr_factor * lr``.

    return f(step) ∈ [min_lr_factor, 1.0]. step >= total_steps이면 min_lr_factor로 수렴.
    """
    warmup_steps = max(1, int(warmup_steps))
    total_steps = max(warmup_steps + 1, int(total_steps))
    min_lr_factor = float(min_lr_factor)

    def f(step: int) -> float:
        if step < warmup_steps:
            return float(step) / float(warmup_steps)
        progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
        progress = min(1.0, max(0.0, progress))
        cosine = 0.5 * (1.0 + math.cos(math.pi * progress))
        return min_lr_factor + (1.0 - min_lr_factor) * cosine

    return f


def warmup_linear_lambda(warmup_steps: int, total_steps: int, min_lr_factor: float) -> Callable[[int], float]:
    """linear warmup + linear decay to ``min_lr_factor * lr``."""
    warmup_steps = max(1, int(warmup_steps))
    total_steps = max(warmup_steps + 1, int(total_steps))
    min_lr_factor = float(min_lr_factor)

    def f(step: int) -> float:
        if step < warmup_steps:
            return float(step) / float(warmup_steps)
        progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
        progress = min(1.0, max(0.0, progress))
        return 1.0 - (1.0 - min_lr_factor) * progress

    return f


def constant_lambda(warmup_steps: int) -> Callable[[int], float]:
    warmup_steps = max(1, int(warmup_steps))

    def f(step: int) -> float:
        return min(1.0, float(step) / float(warmup_steps))

    return f


def build_lr_scheduler(
    optimizer: Optimizer,
    name: str,
    warmup_steps: int,
    total_steps: int,
    min_lr_factor: float,
) -> LambdaLR:
    """``WMTrainConfig.scheduler``를 보고 LambdaLR 생성."""
    name = (name or "warmup_cosine").lower()
    if name == "warmup_cosine":
        fn = warmup_cosine_lambda(warmup_steps, total_steps, min_lr_factor)
    elif name == "warmup_linear":
        fn = warmup_linear_lambda(warmup_steps, total_steps, min_lr_factor)
    elif name == "constant":
        fn = constant_lambda(warmup_steps)
    else:
        raise ValueError(f"unknown scheduler: {name}")
    return LambdaLR(optimizer, lr_lambda=fn)


__all__ = [
    "warmup_cosine_lambda",
    "warmup_linear_lambda",
    "constant_lambda",
    "build_lr_scheduler",
]
