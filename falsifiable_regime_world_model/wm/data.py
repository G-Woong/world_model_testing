"""Episode index + Chunk-level IterableDataset for the RG-4F world model.

본 모듈은 ``rg4f.dataset_io``가 정의한 dataset schema를 그대로 받아, world model 학습용
chunk batch를 yield하는 PyTorch ``IterableDataset``을 제공한다.

핵심 책임:
    1) ``data/<root>/<split>/index.jsonl``을 읽어 episode 메타 정보를 캐시한다 (npz는
       lazy load).
    2) source(=dataset root) 여러 개를 mixture weight로 sampling.
    3) 각 source 안에서 episode를 sampling.
    4) 각 episode 안에서 ``EventWindowSampler``로 chunk 시작 위치 결정.
    5) chunk를 numpy dict + meta로 yield.

본 모듈은 batch dict로의 변환을 직접 하지 않는다 — chunk-level numpy dict까지만 만든다.
``torch.Tensor``로의 변환과 forbidden-key guard는 ``collate.py``가 책임진다.

학습 split policy (PART0 §3, Session 7 §6):
    - ``split`` 값은 무조건 ``{"train", "valid"}`` 중 하나여야 한다.
    - test_id / ood_* split이 들어오면 즉시 ``ValueError``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Mapping, Optional, Sequence

import numpy as np
import torch
from torch.utils.data import IterableDataset, get_worker_info

# rg4f.dataset_io는 이미 manifest/index 로딩 + npz 로딩을 제공한다 — 재사용한다.
from ..rg4f.dataset_io import (  # type: ignore
    EpisodeBundle,
    IndexEntry,
    load_episode,
    load_index,
    load_manifest,
)

from .data_config import (
    ALLOWED_TRAIN_SPLITS,
    FORBIDDEN_TRAIN_SPLITS,
    DatasetSourceConfig,
    EventWindowConfig,
    SampleWeightConfig,
    SplitConfig,
    TargetConfig,
    WMDataConfig,
)
from .sampling import EventWindowSampler, compute_sample_weight, extract_event_index


# =============================================================================
# 1. EpisodeRecord: chunk yield의 단위
# =============================================================================


@dataclass
class EpisodeChunk:
    """sampling된 단일 chunk. numpy dict 기반.

    Attributes
    ----------
    arrays : per-tick numpy arrays. 모든 array의 첫 차원은 chunk_len.
    valid_len : padding 전 실제 데이터 tick 수 (1 ≤ valid_len ≤ chunk_len).
    sample_weight : (chunk_len,) float32. event-aware boost가 이미 적용됨.
    source_id : 0-based source index (mixture에서 어느 dataset인지).
    source_name : 'random_2000' 등 인간 친화적 이름.
    split : 'train' | 'valid'.
    episode_id : index.jsonl의 episode_id.
    chunk_start : episode 안에서 chunk가 시작한 global tick.
    sampler_type : event-window sampler가 사용한 type 이름 (debug용).
    """

    arrays: Dict[str, np.ndarray]
    valid_len: int
    sample_weight: np.ndarray
    source_id: int
    source_name: str
    split: str
    episode_id: str
    chunk_start: int
    sampler_type: str


# =============================================================================
# 2. SourceIndex: dataset root 1개의 split별 IndexEntry 캐시
# =============================================================================


class SourceIndex:
    """단일 dataset root의 ``index.jsonl``을 캐시. 본 클래스는 lazy npz load만 담당.

    학습 split 정책:
        - ``train`` 또는 ``valid``만 yield 가능.
        - 다른 split을 요청하면 즉시 ``ValueError``.
    """

    def __init__(self, source: DatasetSourceConfig) -> None:
        self.source = source
        self.root = source.root_path()
        self.manifest = load_manifest(self.root)
        # 학습 가능한 split만 캐시한다. test_id/OOD는 아예 메모리에 안 올린다.
        self._entries: Dict[str, List[IndexEntry]] = {}
        for split in ALLOWED_TRAIN_SPLITS:
            split_dir = self.root / split
            if not split_dir.is_dir():
                continue
            self._entries[split] = load_index(split_dir)

    def entries(self, split: str) -> List[IndexEntry]:
        if split in FORBIDDEN_TRAIN_SPLITS:
            raise ValueError(
                f"Split leakage detected: test_id/OOD splits must not be used "
                f"for training loaders. Got: {split!r}. "
                f"Allowed: {ALLOWED_TRAIN_SPLITS}"
            )
        if split not in ALLOWED_TRAIN_SPLITS:
            raise ValueError(
                f"Unknown split {split!r}. Allowed: {ALLOWED_TRAIN_SPLITS}"
            )
        return self._entries.get(split, [])

    def load_episode_arrays(
        self,
        split: str,
        idx: int,
    ) -> Dict[str, np.ndarray]:
        """index list의 ``idx`` 번째 episode의 npz를 numpy dict로 반환한다.

        meta.json은 의도적으로 로드하지 않는다 — collector_metadata 같은 oracle metadata가
        모델 input/target에 흘러들어가지 않도록 schema 단계에서부터 차단한다.
        """
        entries = self.entries(split)
        entry = entries[idx]
        bundle: EpisodeBundle = load_episode(self.root, entry, load_meta=False, mmap=False)
        return bundle.arrays


# =============================================================================
# 3. ChunkDataset: 단일 source 안에서 chunk를 yield하는 IterableDataset
# =============================================================================


class RG4FChunkIterableDataset(IterableDataset):
    """단일 source + 단일 split에 대해 chunk를 무한 yield하는 IterableDataset.

    매 epoch마다 ``chunks_per_epoch``개를 yield한다. iter() 호출은 ``rng`` seed를
    재설정하므로 결정성(determinism)을 갖는다.
    """

    def __init__(
        self,
        source_index: SourceIndex,
        source_id: int,
        split: str,
        split_cfg: SplitConfig,
        event_window: EventWindowConfig,
        sample_weight_cfg: SampleWeightConfig,
        target_cfg: TargetConfig,
        chunks_per_epoch: int,
        seed: int,
        epoch: int = 0,
    ) -> None:
        super().__init__()
        if split in FORBIDDEN_TRAIN_SPLITS:
            raise ValueError(
                f"Split leakage detected: test_id/OOD splits must not be used "
                f"for training loaders. Got: {split!r}."
            )
        if split not in ALLOWED_TRAIN_SPLITS:
            raise ValueError(
                f"Unknown split {split!r}. Allowed: {ALLOWED_TRAIN_SPLITS}"
            )
        self.source_index = source_index
        self.source_id = int(source_id)
        self.split = split
        self.split_cfg = split_cfg
        self.event_window = event_window
        self.sample_weight_cfg = sample_weight_cfg
        self.target_cfg = target_cfg
        self.chunks_per_epoch = int(chunks_per_epoch)
        self.seed = int(seed)
        self.epoch = int(epoch)
        self._sampler = EventWindowSampler(event_window)

    def set_epoch(self, epoch: int) -> None:
        self.epoch = int(epoch)

    def __iter__(self) -> Iterator[EpisodeChunk]:
        worker_info = get_worker_info()
        worker_id = worker_info.id if worker_info is not None else 0
        num_workers = worker_info.num_workers if worker_info is not None else 1
        # worker별 독립 seed
        rng = np.random.default_rng(
            (self.seed + 1) * 100003 + self.epoch * 7919 + worker_id * 31
        )
        entries = self.source_index.entries(self.split)
        if not entries:
            return  # 빈 split

        # 본 worker가 yield할 chunk 수 (전체 chunks_per_epoch을 worker에 분배)
        per_worker = self.chunks_per_epoch // max(1, num_workers)
        if worker_id < (self.chunks_per_epoch - per_worker * num_workers):
            per_worker += 1

        for _ in range(per_worker):
            # episode를 uniform 샘플 (epi_weight를 도입할 수 있으나 단순 uniform이 baseline)
            ep_idx = int(rng.integers(0, len(entries)))
            arrays = self.source_index.load_episode_arrays(self.split, ep_idx)
            chunk = self._sample_chunk(arrays, entries[ep_idx], rng)
            yield chunk

    # ---------------------------------------------------------------------
    # internal: chunk 생성
    # ---------------------------------------------------------------------
    def _sample_chunk(
        self,
        arrays: Dict[str, np.ndarray],
        entry: IndexEntry,
        rng: np.random.Generator,
    ) -> EpisodeChunk:
        ev_index = extract_event_index(arrays)
        chunk_len = int(self.split_cfg.chunk_len)
        T = ev_index.episode_length
        chunk_start, sampler_type = self._sampler.sample_chunk_start(
            ev_index, chunk_len, rng,
        )
        valid_len = min(chunk_len, T - chunk_start)
        if valid_len <= 0:
            # safety: episode 길이가 0이거나 음수가 나올 일은 없지만 방어
            chunk_start = max(0, T - 1)
            valid_len = 1

        sliced = _slice_episode(arrays, chunk_start, chunk_len, valid_len, self.target_cfg)
        sample_weight = compute_sample_weight(
            arrays=arrays,
            chunk_start=chunk_start,
            chunk_len=chunk_len,
            valid_len=valid_len,
            cfg=self.sample_weight_cfg,
            raw_eff_mismatch_subsample_max=self.event_window.raw_eff_mismatch_subsample_max,
            rng=rng,
        )
        return EpisodeChunk(
            arrays=sliced,
            valid_len=int(valid_len),
            sample_weight=sample_weight,
            source_id=self.source_id,
            source_name=self.source_index.source.name,
            split=self.split,
            episode_id=str(entry.episode_id),
            chunk_start=int(chunk_start),
            sampler_type=sampler_type,
        )


# =============================================================================
# 4. Mixture: source 여러 개를 weight로 sampling하는 IterableDataset
# =============================================================================


class MixtureChunkIterableDataset(IterableDataset):
    """여러 ``RG4FChunkIterableDataset``를 weight 기반 categorical sampling으로 섞는다.

    - 매 chunk마다 source를 weight categorical로 선택.
    - 선택된 source의 ``RG4FChunkIterableDataset``에서 단일 chunk를 yield.
    - 무한 yield를 막기 위해 ``chunks_per_epoch``개만 yield.
    """

    def __init__(
        self,
        sub_datasets: List[RG4FChunkIterableDataset],
        weights: Sequence[float],
        chunks_per_epoch: int,
        seed: int,
        epoch: int = 0,
    ) -> None:
        super().__init__()
        if len(sub_datasets) == 0:
            raise ValueError("MixtureChunkIterableDataset: sub_datasets is empty")
        if len(sub_datasets) != len(weights):
            raise ValueError(
                f"sub_datasets length {len(sub_datasets)} != weights length {len(weights)}"
            )
        w = np.asarray(weights, dtype=np.float64)
        if (w < 0).any() or w.sum() <= 0:
            raise ValueError(f"invalid mixture weights: {weights}")
        self.sub_datasets = sub_datasets
        self.weights = (w / w.sum()).astype(np.float64)
        self.chunks_per_epoch = int(chunks_per_epoch)
        self.seed = int(seed)
        self.epoch = int(epoch)

    def set_epoch(self, epoch: int) -> None:
        self.epoch = int(epoch)
        for ds in self.sub_datasets:
            ds.set_epoch(epoch)

    def __iter__(self) -> Iterator[EpisodeChunk]:
        worker_info = get_worker_info()
        worker_id = worker_info.id if worker_info is not None else 0
        num_workers = worker_info.num_workers if worker_info is not None else 1
        rng = np.random.default_rng(
            (self.seed + 1) * 100019 + self.epoch * 6151 + worker_id * 47
        )
        # worker 분배
        per_worker = self.chunks_per_epoch // max(1, num_workers)
        if worker_id < (self.chunks_per_epoch - per_worker * num_workers):
            per_worker += 1

        # 각 sub-dataset의 entries는 미리 가져와 두고, chunk 단위로 직접 sampling.
        # __iter__ 호출 시 sub-dataset의 generator를 만들지 않고, sub-dataset의
        # _sample_chunk를 직접 호출하면 worker 간 결정성도 더 단순.
        for _ in range(per_worker):
            src_idx = int(rng.choice(len(self.sub_datasets), p=self.weights))
            sub = self.sub_datasets[src_idx]
            entries = sub.source_index.entries(sub.split)
            if not entries:
                continue
            ep_idx = int(rng.integers(0, len(entries)))
            arrays = sub.source_index.load_episode_arrays(sub.split, ep_idx)
            chunk = sub._sample_chunk(arrays, entries[ep_idx], rng)  # noqa: SLF001
            yield chunk


# =============================================================================
# 5. helpers: episode arrays → chunk arrays (slice + pad)
# =============================================================================


# input/target에서 사용하는 npz key 화이트리스트.
# 이 화이트리스트에 없는 key는 numpy dict에 들어가지 않는다 (forbidden metadata 차단).
_INPUT_NPZ_KEYS: tuple[str, ...] = (
    "observations_local_grid",
    "observations_scalar",
    "observations_event_token",
    "actions_raw",
    "actions_effective",   # target/raw_eff_mismatch 계산용. collate에서 input에는 안 넣음.
)
_TARGET_NPZ_KEYS: tuple[str, ...] = (
    # obs reconstruction target (next_step 또는 same_step 모드에 따라 결정)
    "next_observations_local_grid",
    "next_observations_scalar",
    # reward / done
    "rewards",
    "dones",
    "truncateds",
    # state / regime
    "true_state",
    "true_regime_control_mode",
    # event targets
    "change_point",
    "reveal_event",
    "shift_event",
)
_KEYS_TO_SLICE: tuple[str, ...] = _INPUT_NPZ_KEYS + _TARGET_NPZ_KEYS


def _slice_episode(
    arrays: Mapping[str, np.ndarray],
    chunk_start: int,
    chunk_len: int,
    valid_len: int,
    target_cfg: TargetConfig,
) -> Dict[str, np.ndarray]:
    """episode arrays의 화이트리스트 key만 [chunk_start, chunk_start + valid_len)으로 slice
    한 뒤 chunk_len에 맞춰 0-padding한 dict를 만든다.

    target_cfg.obs_recon_mode == "same_step"이면 obs_target_*은 observations_*의 복사본을,
    "next_step"이면 next_observations_*을 사용한다.
    """
    out: Dict[str, np.ndarray] = {}
    for key in _KEYS_TO_SLICE:
        if key not in arrays:
            continue
        a = np.asarray(arrays[key])
        out[key] = _pad_to_len(a, chunk_start, chunk_len, valid_len)

    # obs target alias: obs_target_local_grid / obs_target_scalar / obs_target_event_token
    # (모델 입장에선 next_step prediction or auto-encoding 둘 다 같은 인터페이스)
    if target_cfg.obs_recon_mode == "next_step":
        if "next_observations_local_grid" in out:
            out["obs_target_local_grid"] = out["next_observations_local_grid"]
        if "next_observations_scalar" in out:
            out["obs_target_scalar"] = out["next_observations_scalar"]
    else:  # same_step
        if "observations_local_grid" in out:
            out["obs_target_local_grid"] = out["observations_local_grid"].copy()
        if "observations_scalar" in out:
            out["obs_target_scalar"] = out["observations_scalar"].copy()

    # raw_eff_mismatch (action_raw != action_effective). float32 (1.0 / 0.0).
    if "actions_raw" in out and "actions_effective" in out:
        diff = (out["actions_raw"] != out["actions_effective"]).astype(np.float32)
        # padding 위치는 0 처리 (action_effective도 padding이 0이라 두 0의 비교는 0)
        out["raw_eff_mismatch"] = diff

    return out


def _pad_to_len(
    a: np.ndarray,
    chunk_start: int,
    chunk_len: int,
    valid_len: int,
) -> np.ndarray:
    """``a[chunk_start : chunk_start + valid_len]``을 chunk_len에 맞춰 0-padding."""
    sl = a[chunk_start: chunk_start + valid_len]
    if valid_len == chunk_len:
        return np.ascontiguousarray(sl)
    pad_shape = (chunk_len - valid_len,) + a.shape[1:]
    pad = np.zeros(pad_shape, dtype=a.dtype)
    return np.ascontiguousarray(np.concatenate([sl, pad], axis=0))


# =============================================================================
# 6. helper: convenience builders (loader 생성 헬퍼)
# =============================================================================


def build_source_indices(cfg: WMDataConfig) -> List[SourceIndex]:
    """WMDataConfig.sources 각각에 대해 SourceIndex를 만든다.

    학습 split만 메모리에 올린다 (test_id/OOD는 SourceIndex가 자동으로 무시).
    """
    cfg.validate()
    return [SourceIndex(s) for s in cfg.sources]


def build_chunk_dataset(
    cfg: WMDataConfig,
    split: str,
    *,
    epoch: int = 0,
    sources: Optional[List[SourceIndex]] = None,
) -> MixtureChunkIterableDataset:
    """WMDataConfig + split → mixture IterableDataset.

    - split는 'train' 또는 'valid'만 허용.
    - source mixture weight는 yaml의 train_weight / valid_weight를 정규화하여 사용.
    - chunks_per_epoch / seed는 split section에서 가져온다.
    """
    if split in FORBIDDEN_TRAIN_SPLITS:
        raise ValueError(
            f"Split leakage detected: test_id/OOD splits must not be used "
            f"for training loaders. Got: {split!r}."
        )
    if split not in ALLOWED_TRAIN_SPLITS:
        raise ValueError(
            f"Unknown split {split!r}. Allowed: {ALLOWED_TRAIN_SPLITS}"
        )
    src_indices = sources if sources is not None else build_source_indices(cfg)
    weights = cfg.normalized_weights(split)
    split_cfg = cfg.train if split == "train" else cfg.valid

    sub_datasets = [
        RG4FChunkIterableDataset(
            source_index=si,
            source_id=i,
            split=split,
            split_cfg=split_cfg,
            event_window=cfg.event_window,
            sample_weight_cfg=cfg.sample_weight,
            target_cfg=cfg.target,
            chunks_per_epoch=split_cfg.chunks_per_epoch,
            seed=split_cfg.seed + i,    # source별 seed offset
            epoch=epoch,
        )
        for i, si in enumerate(src_indices)
    ]
    return MixtureChunkIterableDataset(
        sub_datasets=sub_datasets,
        weights=weights,
        chunks_per_epoch=split_cfg.chunks_per_epoch,
        seed=split_cfg.seed,
        epoch=epoch,
    )


__all__ = [
    "EpisodeChunk",
    "SourceIndex",
    "RG4FChunkIterableDataset",
    "MixtureChunkIterableDataset",
    "build_source_indices",
    "build_chunk_dataset",
]
