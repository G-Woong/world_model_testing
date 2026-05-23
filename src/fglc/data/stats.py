"""Streaming dataset statistics (Welford online algorithm) for FGLC Step 11.

Source: docs/STEP11_PLAN.md §F.5, §C.5
"""

from __future__ import annotations

import numpy as np


class WelfordStats:
    """Incremental mean/variance via Welford's algorithm for a fixed-dim vector."""

    def __init__(self, dim: int) -> None:
        self.n = 0
        self._mean = np.zeros(dim, dtype=np.float64)
        self._M2 = np.zeros(dim, dtype=np.float64)

    def update(self, x: np.ndarray) -> None:
        self.n += 1
        delta = x.astype(np.float64) - self._mean
        self._mean += delta / self.n
        self._M2 += delta * (x.astype(np.float64) - self._mean)

    @property
    def mean(self) -> np.ndarray:
        return self._mean.copy()

    @property
    def variance(self) -> np.ndarray:
        if self.n < 2:
            return np.zeros_like(self._mean)
        return self._M2 / (self.n - 1)

    @property
    def std(self) -> np.ndarray:
        return np.sqrt(self.variance)
