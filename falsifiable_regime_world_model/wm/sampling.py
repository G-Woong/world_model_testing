"""Event-window chunk sampler + tick-level sample_weight boost.

본 모듈은 numpy array만 다룬다 (PyTorch import 없음). PyTorch tensor 변환은
``collate.py``가 담당한다.

핵심 책임:
    1) episode npz arrays를 받아 chunk 시작 위치(``chunk_start``)를 결정한다.
    2) chunk 안의 각 tick에 대해 sample_weight를 계산한다 (event 주변 boost + cap).

동기 (PART2 §3.7, WM_ARCHITECTURE_DESIGN §8):
    - change_point는 tick-level로 ~0.05% 수준으로 매우 희소하다. uniform chunk 샘플링만
      쓰면 모델이 change_point=1 step을 거의 보지 못한다. 따라서 event-window sampling
      (chunk 시작을 event 주변에 가두기) + sample_weight boost (chunk 안 event 주변 tick의
      gradient 비중을 키우기) 두 가지를 함께 사용한다.
    - reveal은 충분히 dense하므로 별도 boost는 약하게.
    - shift는 change_point와 분리 기록.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .data_config import EventWindowConfig, SampleWeightConfig


# =============================================================================
# 1. EventIndex: episode 단위로 추출
# =============================================================================


@dataclass
class EventIndex:
    """episode 1개의 event tick 좌표 모음. numpy int64 array.

    episode npz array(``shape=(T,)``)에서 양성 위치만 추출한다. 학습 input 금지 metadata가
    아니라 *position-only*다 (값 자체는 target에서만 사용된다).
    """

    episode_length: int
    change_point: np.ndarray   # int64, 1d
    shift: np.ndarray
    reveal: np.ndarray
    success: np.ndarray        # done==1
    raw_eff_mismatch: np.ndarray

    @property
    def has_change_point(self) -> bool:
        return self.change_point.size > 0

    @property
    def has_shift(self) -> bool:
        return self.shift.size > 0

    @property
    def has_reveal(self) -> bool:
        return self.reveal.size > 0

    @property
    def has_success(self) -> bool:
        return self.success.size > 0


def extract_event_index(arrays: Mapping[str, np.ndarray]) -> EventIndex:
    """npz arrays(=한 episode)에서 event tick index를 추출한다.

    arrays의 key는 ``rg4f.serialization``의 schema와 일치해야 한다.
    """
    # required keys; 누락이면 빈 array로 처리.
    T = int(_pick_T(arrays))
    cp = _bool_to_idx(arrays.get("change_point"))
    sh = _bool_to_idx(arrays.get("shift_event"))
    rv = _bool_to_idx(arrays.get("reveal_event"))
    # success: done == 1 (terminated). truncated은 별도 — 여기서는 dones만 사용.
    sc = _bool_to_idx(arrays.get("dones"))
    # raw/eff mismatch: actions_raw != actions_effective
    a_raw = arrays.get("actions_raw")
    a_eff = arrays.get("actions_effective")
    if a_raw is None or a_eff is None:
        re = np.empty((0,), dtype=np.int64)
    else:
        re = np.where(a_raw != a_eff)[0].astype(np.int64)
    return EventIndex(
        episode_length=T,
        change_point=cp,
        shift=sh,
        reveal=rv,
        success=sc,
        raw_eff_mismatch=re,
    )


def _pick_T(arrays: Mapping[str, np.ndarray]) -> int:
    for k in ("rewards", "actions_raw", "true_state"):
        a = arrays.get(k)
        if a is not None:
            return int(a.shape[0])
    raise KeyError(
        "event index 추출 실패: rewards/actions_raw/true_state 중 하나도 npz에 없습니다."
    )


def _bool_to_idx(arr: Optional[np.ndarray]) -> np.ndarray:
    if arr is None:
        return np.empty((0,), dtype=np.int64)
    return np.where(np.asarray(arr).astype(bool))[0].astype(np.int64)


# =============================================================================
# 2. Event-window chunk-start sampler
# =============================================================================


# 내부 event type id (확률 정규화에 사용).
_EVENT_TYPES: Tuple[str, ...] = ("change_point", "shift", "reveal", "success", "uniform")


class EventWindowSampler:
    """event 주변에서 chunk_start 위치를 sampling한다 (numpy.random.Generator 기반).

    - ``enabled=False``이거나 ``chunk_len > episode_length``이면 무조건 0 또는 max_start
      안에서 uniform fallback.
    - 매 chunk마다 ``_EVENT_TYPES``에서 type을 sampling하고, 해당 event index가
      ``EventIndex``에 있으면 그 주변에서 chunk_start를 결정한다.
    - 'uniform' type 또는 fallback은 episode 전체 [0, max_start] uniform.
    """

    def __init__(self, cfg: EventWindowConfig) -> None:
        self.cfg = cfg
        # type weight를 정규화
        weights = np.array([
            cfg.change_point_prob,
            cfg.shift_prob,
            cfg.reveal_prob,
            cfg.success_prob,
            cfg.uniform_prob,
        ], dtype=np.float64)
        weights = np.clip(weights, 0.0, None)
        total = float(weights.sum())
        if total <= 0.0:
            # 모든 prob이 0이면 uniform만으로 fallback.
            weights = np.array([0.0, 0.0, 0.0, 0.0, 1.0], dtype=np.float64)
            total = 1.0
        self._type_probs = weights / total

    def sample_chunk_start(
        self,
        index: EventIndex,
        chunk_len: int,
        rng: np.random.Generator,
    ) -> Tuple[int, str]:
        """chunk_start in [0, max_start]를 반환. (-1, '...')은 사용하지 않는다.

        Returns
        -------
        (start, type_name)
            type_name은 sampling에서 실제 사용된 event type ('uniform' 포함).
        """
        T = int(index.episode_length)
        if chunk_len <= 0:
            raise ValueError("chunk_len must be > 0")
        max_start = max(0, T - chunk_len)
        if max_start == 0:
            return 0, "uniform"   # episode가 chunk_len보다 짧음 → 0에서 시작 + padding

        if not self.cfg.enabled:
            return int(rng.integers(0, max_start + 1)), "uniform"

        # type을 categorical sample
        type_idx = int(rng.choice(len(_EVENT_TYPES), p=self._type_probs))
        type_name = _EVENT_TYPES[type_idx]

        # 후보 event index를 가져온다.
        candidates: Optional[np.ndarray]
        if type_name == "change_point":
            candidates = index.change_point
        elif type_name == "shift":
            candidates = index.shift
        elif type_name == "reveal":
            candidates = index.reveal
        elif type_name == "success":
            candidates = index.success
        else:
            candidates = None

        if candidates is None or candidates.size == 0:
            # event 없음 → uniform fallback. type_name은 'uniform_fallback_*'로 기록.
            start = int(rng.integers(0, max_start + 1))
            return start, f"uniform_fallback_{type_name}" if type_name != "uniform" else "uniform"

        # event 주변 [event - radius, event] 사이에서 chunk_start sampling
        # → chunk가 event를 chunk 안 어디든 포함하도록.
        radius = max(0, int(self.cfg.window_radius))
        event_pos = int(rng.choice(candidates))
        # chunk 안에 event가 들어오도록 하는 start 범위:
        #   start ∈ [max(0, event_pos - chunk_len + 1), min(max_start, event_pos)]
        # 추가로 ±radius 범위로 살짝 벌려서 sampling jitter를 준다.
        low = max(0, event_pos - chunk_len + 1 - radius)
        high = min(max_start, event_pos + radius)
        if high < low:
            # corner case (radius 음수 등). uniform fallback.
            start = int(rng.integers(0, max_start + 1))
            return start, f"uniform_fallback_{type_name}"
        start = int(rng.integers(low, high + 1))
        return start, type_name


# =============================================================================
# 3. sample_weight boost
# =============================================================================


def compute_sample_weight(
    arrays: Mapping[str, np.ndarray],
    chunk_start: int,
    chunk_len: int,
    valid_len: int,
    cfg: SampleWeightConfig,
    *,
    raw_eff_mismatch_subsample_max: Optional[int] = None,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """chunk 안의 tick별 sample_weight를 계산한다.

    Parameters
    ----------
    arrays : episode npz arrays (shape=(T,))
    chunk_start : chunk가 episode의 어디에서 시작하는지
    chunk_len : chunk의 max length (padding 포함)
    valid_len : padding 전의 실제 valid tick 수 (≤ chunk_len)
    cfg : SampleWeightConfig

    Returns
    -------
    np.ndarray of shape (chunk_len,) float32. 모든 음수는 0으로 clamp되고 cap이 적용된다.
    padding tick은 항상 0.
    """
    cl = int(chunk_len)
    weights = np.zeros((cl,), dtype=np.float32)
    if not cfg.enabled or valid_len <= 0:
        return weights

    base = float(cfg.base_weight)
    weights[:valid_len] = base
    if base <= 0.0:
        return np.zeros((cl,), dtype=np.float32)

    radius = max(0, int(cfg.boost_radius))
    end = chunk_start + valid_len   # exclusive

    def _boost_event(pos_global: np.ndarray, factor: float) -> None:
        if factor == 1.0 or pos_global.size == 0:
            return
        # event_global 좌표를 chunk-local 좌표로 변환
        in_chunk = (pos_global >= chunk_start) & (pos_global < end)
        if not np.any(in_chunk):
            # event가 chunk 안엔 없지만, ±radius 안엔 있을 수 있음 → 그것도 boost.
            in_extended = (pos_global >= chunk_start - radius) & (pos_global < end + radius)
            if not np.any(in_extended):
                return
            local = pos_global[in_extended] - chunk_start
        else:
            local = pos_global[in_chunk] - chunk_start
        # ±radius 범위 multiplier
        for p in local:
            lo = max(0, int(p) - radius)
            hi = min(valid_len, int(p) + radius + 1)
            if hi > lo:
                weights[lo:hi] *= float(factor)

    # change_point / shift / reveal / success은 직접 npz에서 추출 (event index extract 불필요)
    cp = arrays.get("change_point")
    sh = arrays.get("shift_event")
    rv = arrays.get("reveal_event")
    sc = arrays.get("dones")
    a_raw = arrays.get("actions_raw")
    a_eff = arrays.get("actions_effective")

    if cp is not None:
        _boost_event(np.where(np.asarray(cp).astype(bool))[0].astype(np.int64),
                     cfg.change_point_boost)
    if sh is not None:
        _boost_event(np.where(np.asarray(sh).astype(bool))[0].astype(np.int64),
                     cfg.shift_boost)
    if rv is not None:
        _boost_event(np.where(np.asarray(rv).astype(bool))[0].astype(np.int64),
                     cfg.reveal_boost)
    if sc is not None:
        _boost_event(np.where(np.asarray(sc).astype(bool))[0].astype(np.int64),
                     cfg.success_boost)
    if a_raw is not None and a_eff is not None and cfg.raw_eff_mismatch_boost != 1.0:
        mm = np.where(np.asarray(a_raw) != np.asarray(a_eff))[0].astype(np.int64)
        # mismatch는 매우 많을 수 있으므로 subsample
        if raw_eff_mismatch_subsample_max is not None and mm.size > raw_eff_mismatch_subsample_max:
            if rng is None:
                rng = np.random.default_rng(0)
            mm = rng.choice(mm, size=int(raw_eff_mismatch_subsample_max), replace=False)
        _boost_event(mm, cfg.raw_eff_mismatch_boost)

    # cap
    if cfg.weight_cap > 0:
        np.clip(weights, 0.0, float(cfg.weight_cap), out=weights)
    # padding 강제 0
    if valid_len < cl:
        weights[valid_len:] = 0.0
    return weights


__all__ = [
    "EventIndex",
    "extract_event_index",
    "EventWindowSampler",
    "compute_sample_weight",
]
