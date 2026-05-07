"""Atomic checkpoint save/load + best/last keep policy.

본 모듈은 학습 중 model / optimizer / scheduler / scaler / RNG state / config 정보를 한
파일로 저장/복원한다. 저장은 ``.tmp``로 먼저 쓰고 rename하여 corruption 위험을 줄인다.

저장 형식 (Session 9 §7):
    {
      "model":     state_dict,
      "optimizer": state_dict,
      "scheduler": state_dict,
      "scaler":    state_dict | None,
      "wm_config": dict,
      "train_config": dict,
      "variant":   str,
      "global_step": int,
      "epoch":     int,
      "best_metrics": dict,
      "rng": {python, numpy, torch, cuda},
      "env_summary": dict,
      "git_commit": str | None,
      "schema_version": int,
    }
"""
from __future__ import annotations

import os
import platform
import random
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from torch import nn


SCHEMA_VERSION: int = 1


# =============================================================================
# 1. RNG state capture / restore
# =============================================================================


def capture_rng_state() -> Dict[str, Any]:
    state = {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state(),
    }
    if torch.cuda.is_available():
        state["cuda"] = [s for s in torch.cuda.get_rng_state_all()]
    return state


def restore_rng_state(state: Dict[str, Any]) -> None:
    if "python" in state:
        try:
            random.setstate(state["python"])
        except Exception:   # noqa: BLE001
            pass
    if "numpy" in state:
        try:
            np.random.set_state(state["numpy"])
        except Exception:   # noqa: BLE001
            pass
    if "torch" in state:
        try:
            torch.set_rng_state(state["torch"])
        except Exception:   # noqa: BLE001
            pass
    if "cuda" in state and torch.cuda.is_available():
        try:
            torch.cuda.set_rng_state_all(state["cuda"])
        except Exception:   # noqa: BLE001
            pass


# =============================================================================
# 2. atomic save / load
# =============================================================================


def atomic_save(state: Dict[str, Any], path: str | Path) -> Path:
    """``.tmp``로 저장 후 ``rename(target)``. 같은 파일 시스템에서만 atomic 보장."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    torch.save(state, tmp)
    # Windows에서 destination이 존재할 때 rename은 실패하므로 replace로.
    os.replace(tmp, p)
    return p


def load_checkpoint(path: str | Path, *, map_location: str | torch.device = "cpu") -> Dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"checkpoint not found: {p}")
    # weights_only=False: 우리는 dict (state_dict + python objects) 그대로 저장한다.
    state = torch.load(p, map_location=map_location, weights_only=False)
    if not isinstance(state, dict) or "model" not in state:
        raise ValueError(f"invalid checkpoint format at {p}")
    return state


# =============================================================================
# 3. ManagedCheckpointer: keep_last_n / keep_best_n 정책
# =============================================================================


@dataclass
class _BestEntry:
    metric_value: float
    path: Path


class ManagedCheckpointer:
    """run_dir 안의 ``checkpoints/`` 폴더를 관리한다.

    저장 파일 규칙:
        - last.pt                                 (항상 최신)
        - step_{global_step:08d}.pt              (rolling, keep_last_n)
        - best_{metric_key.replace('/', '_')}.pt (best, keep_best_n)
        - interrupted_step_{global_step:08d}.pt  (KeyboardInterrupt 시)
    """

    def __init__(
        self,
        run_dir: Path,
        *,
        keep_last_n: int = 3,
        keep_best_n: int = 3,
        best_metric_keys: Optional[List[str]] = None,
        best_metric_modes: Optional[List[str]] = None,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.ckpt_dir = self.run_dir / "checkpoints"
        self.ckpt_dir.mkdir(parents=True, exist_ok=True)
        self.keep_last_n = max(0, int(keep_last_n))
        self.keep_best_n = max(1, int(keep_best_n))
        self.best_metric_keys = list(best_metric_keys or [])
        self.best_metric_modes = list(best_metric_modes or [])
        # 내부: best metric 추적
        self._best: Dict[str, List[_BestEntry]] = {k: [] for k in self.best_metric_keys}
        # 내부: rolling step 추적
        self._rolling: List[Path] = []

    # ---------------------------------------------------------------------
    # 저장
    # ---------------------------------------------------------------------
    def save_step(self, state: Dict[str, Any], global_step: int) -> Tuple[Path, Path]:
        """매 ``save_every_steps``마다 호출.

        Returns
        -------
        (last_path, step_path)
        """
        last = self.ckpt_dir / "last.pt"
        step = self.ckpt_dir / f"step_{global_step:08d}.pt"
        atomic_save(state, last)
        if self.keep_last_n > 0:
            atomic_save(state, step)
            self._rolling.append(step)
            self._evict_rolling()
        return last, step

    def save_interrupted(self, state: Dict[str, Any], global_step: int) -> Path:
        target = self.ckpt_dir / f"interrupted_step_{global_step:08d}.pt"
        atomic_save(state, target)
        # interrupt도 last로 동기화
        atomic_save(state, self.ckpt_dir / "last.pt")
        return target

    def maybe_save_best(self, state: Dict[str, Any], metrics: Dict[str, float]) -> List[Path]:
        """metric dict을 받아 best_metric_keys에 매칭되는 항목이 있으면 best 저장.

        Returns
        -------
        실제로 저장된 파일 경로 list.
        """
        saved: List[Path] = []
        for key, mode in zip(self.best_metric_keys, self.best_metric_modes or []):
            if key not in metrics:
                continue
            value = float(metrics[key])
            ml = self._best.setdefault(key, [])
            if not self._is_better(ml, value, mode):
                continue
            target = self.ckpt_dir / f"best_{_safe_key(key)}.pt"
            atomic_save(state, target)
            ml.append(_BestEntry(metric_value=value, path=target))
            self._best[key] = self._evict_best(ml, mode)
            saved.append(target)
        return saved

    # ---------------------------------------------------------------------
    # rolling/best eviction
    # ---------------------------------------------------------------------
    def _evict_rolling(self) -> None:
        # 최근 N개만 남기고 나머지 삭제
        while len(self._rolling) > self.keep_last_n:
            old = self._rolling.pop(0)
            try:
                old.unlink(missing_ok=True)
            except Exception:   # noqa: BLE001
                pass

    def _is_better(self, ml: List[_BestEntry], value: float, mode: str) -> bool:
        if not ml:
            return True
        if mode == "max":
            return value > min(e.metric_value for e in ml) or len(ml) < self.keep_best_n
        # default min
        return value < max(e.metric_value for e in ml) or len(ml) < self.keep_best_n

    def _evict_best(self, ml: List[_BestEntry], mode: str) -> List[_BestEntry]:
        # 정렬 후 keep_best_n만 유지
        if mode == "max":
            ml = sorted(ml, key=lambda e: e.metric_value, reverse=True)
        else:
            ml = sorted(ml, key=lambda e: e.metric_value)
        keep = ml[: self.keep_best_n]
        # 남기지 않을 파일은 삭제 (best_<key>.pt 자체는 같은 파일을 덮어쓰므로 일반적으로 1개만 남음)
        for entry in ml[self.keep_best_n:]:
            try:
                entry.path.unlink(missing_ok=True)
            except Exception:   # noqa: BLE001
                pass
        return keep


def _safe_key(key: str) -> str:
    return key.replace("/", "_").replace(":", "_")


# =============================================================================
# 4. helpers
# =============================================================================


def env_summary() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "torch": torch.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cuda_available": torch.cuda.is_available(),
    }
    if torch.cuda.is_available():
        info["device_name"] = torch.cuda.get_device_name(0)
        info["torch_cuda"] = getattr(torch.version, "cuda", None)
    return info


def model_state_dict_cpu(model: nn.Module) -> Dict[str, torch.Tensor]:
    """state_dict를 CPU로 옮긴 사본을 반환한다 (저장용)."""
    return {k: v.detach().cpu() for k, v in model.state_dict().items()}


__all__ = [
    "SCHEMA_VERSION",
    "capture_rng_state",
    "restore_rng_state",
    "atomic_save",
    "load_checkpoint",
    "ManagedCheckpointer",
    "env_summary",
    "model_state_dict_cpu",
]
