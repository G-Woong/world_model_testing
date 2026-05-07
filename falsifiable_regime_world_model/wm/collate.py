"""Chunk(numpy) → batched torch tensor dict.

본 모듈은 ``data.RG4FChunkIterableDataset``가 yield한 ``EpisodeChunk`` list를 PyTorch
``DataLoader.collate_fn``에 사용 가능한 batch dict 1개로 합친다.

핵심 책임:
    1) chunk-level numpy arrays를 torch.Tensor로 변환 (dtype contract 강제).
    2) 모델 입력 (``inputs``)과 학습 target (``targets``)을 분리한다.
    3) collector_metadata 등 forbidden key가 ``inputs``에 들어가지 않도록 hard guard.
    4) sample_weight + valid_mask + meta(소스 분포 통계용)를 추가로 노출한다.

batch dict 구조 (Session 7 §10.1, §10.2 contract):
    batch = {
        "inputs":  {                              # RSSMWorldModel.forward에 그대로 넘김
            "local_grid":   FloatTensor[B, T, H, W, C],
            "scalar":       FloatTensor[B, T, S],
            "event_token":  LongTensor[B, T],
            "action_raw":   LongTensor[B, T],
            "action_prev_raw": LongTensor[B, T],   # 0 padded at t=0
        },
        "targets": {                              # compute_total_loss에 그대로 넘김
            "obs_local_target":  FloatTensor[B, T, H, W, C],
            "obs_scalar_target": FloatTensor[B, T, S],
            "reward":            FloatTensor[B, T],
            "done":              FloatTensor[B, T],
            "true_state":        FloatTensor[B, T, 5],
            "true_regime_control_mode": LongTensor[B, T],
            "change_point":      FloatTensor[B, T],
            "reveal_event":      FloatTensor[B, T],
            "shift_event":       FloatTensor[B, T],
            "raw_eff_mismatch":  FloatTensor[B, T],
        },
        "sample_weight": FloatTensor[B, T],       # event-aware boost 적용 완료
        "valid_mask":    FloatTensor[B, T],       # padding=0, valid=1
        "meta": {                                 # debug/analysis 전용. model에 입력 금지.
            "source_id":   LongTensor[B],
            "source_name": List[str],
            "split":       List[str],
            "episode_id":  List[str],
            "chunk_start": LongTensor[B],
            "sampler_type": List[str],
            "valid_len":   LongTensor[B],
        },
    }
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

import numpy as np
import torch
from torch import Tensor

from .data import EpisodeChunk
from .data_config import FORBIDDEN_INPUT_KEYS


# =============================================================================
# 1. dtype contract
# =============================================================================

# (key, expected_torch_dtype). collate가 강제로 캐스팅한다.
_INPUT_DTYPES: Dict[str, torch.dtype] = {
    "local_grid":      torch.float32,
    "scalar":          torch.float32,
    "event_token":     torch.long,
    "action_raw":      torch.long,
    "action_prev_raw": torch.long,
}

_TARGET_DTYPES: Dict[str, torch.dtype] = {
    "obs_local_target":          torch.float32,
    "obs_scalar_target":         torch.float32,
    "reward":                    torch.float32,
    # done family (Session 9 PATCH): backward-compatible split
    "done":                      torch.float32,   # alias of success_done by default
    "success_done":              torch.float32,   # = dones.float()  (true task success)
    "truncated":                 torch.float32,   # = truncateds.float()  (timeout)
    "terminal":                  torch.float32,   # = (dones | truncateds).float()
    "true_state":                torch.float32,
    "true_regime_control_mode":  torch.long,
    "change_point":              torch.float32,
    "reveal_event":              torch.float32,
    "shift_event":               torch.float32,
    "raw_eff_mismatch":          torch.float32,
}


# =============================================================================
# 2. core collate function
# =============================================================================


def collate_chunks(chunks: Sequence[EpisodeChunk]) -> Dict[str, object]:
    """list[EpisodeChunk] → batch dict (위 contract 그대로).

    Notes
    -----
    - **Done family 분리 (Session 9 PATCH):**
        ``success_done = dones.float()``
        ``truncated    = truncateds.float()``
        ``terminal     = (dones | truncateds).float()``
        ``done         = success_done``  (backward-compat alias; default = success_done)
      world model의 ``done_logit``은 ``done_target_mode``에 따라 trainer가 ``targets["done"]``
      를 ``success_done`` 또는 ``terminal``로 dispatch한다 (default = success_done).
    - ``action_prev_raw`` = ``action_raw``를 한 step 우측 shift, t=0은 0.
    - source_name 등 string은 list로 보관 (Tensor 아님). 메타는 ``batch["meta"]``로만 노출.
    """
    if len(chunks) == 0:
        raise ValueError("collate_chunks: empty chunk list")

    B = len(chunks)
    chunk_len = next(iter(chunks[0].arrays.values())).shape[0]

    # ---- inputs ----
    local_grid = _stack_float32(chunks, "observations_local_grid")    # (B, T, H, W, C)
    scalar = _stack_float32(chunks, "observations_scalar")             # (B, T, S)
    event_token = _stack_long(chunks, "observations_event_token")      # (B, T)
    action_raw = _stack_long(chunks, "actions_raw")                    # (B, T)
    action_prev_raw = _shift_right(action_raw)                         # (B, T)

    inputs: Dict[str, Tensor] = {
        "local_grid": local_grid,
        "scalar": scalar,
        "event_token": event_token,
        "action_raw": action_raw,
        "action_prev_raw": action_prev_raw,
    }
    _assert_no_forbidden_keys(inputs)

    # ---- targets ----
    obs_local_t = _stack_float32(chunks, "obs_target_local_grid")
    obs_scalar_t = _stack_float32(chunks, "obs_target_scalar")
    reward = _stack_float32(chunks, "rewards")
    # done family (Session 9 PATCH): 명시적으로 4개 키를 분리 노출
    success_done, truncated, terminal = _stack_done_components(chunks)
    done = success_done                                 # backward-compat alias
    true_state = _stack_float32(chunks, "true_state")
    regime = _stack_long(chunks, "true_regime_control_mode")
    cp = _stack_bool_to_float(chunks, "change_point")
    rv = _stack_bool_to_float(chunks, "reveal_event")
    sh = _stack_bool_to_float(chunks, "shift_event")
    mm = _stack_float32(chunks, "raw_eff_mismatch")

    targets: Dict[str, Tensor] = {
        "obs_local_target": obs_local_t,
        "obs_scalar_target": obs_scalar_t,
        "reward": reward,
        # done family
        "done": done,                  # = success_done (default; trainer가 mode에 따라 dispatch)
        "success_done": success_done,  # task 성공 종료 (= dones)
        "truncated": truncated,        # timeout (= truncateds)
        "terminal": terminal,          # (dones | truncateds); rollout-stop / 분석용
        "true_state": true_state,
        "true_regime_control_mode": regime,
        "change_point": cp,
        "reveal_event": rv,
        "shift_event": sh,
        "raw_eff_mismatch": mm,
    }

    # ---- sample_weight + valid_mask ----
    sw = torch.from_numpy(np.stack([c.sample_weight for c in chunks], axis=0)).to(torch.float32)
    valid_mask = _build_valid_mask(chunks, chunk_len)

    # ---- meta ----
    meta = {
        "source_id":   torch.tensor([c.source_id for c in chunks], dtype=torch.long),
        "source_name": [c.source_name for c in chunks],
        "split":       [c.split for c in chunks],
        "episode_id":  [c.episode_id for c in chunks],
        "chunk_start": torch.tensor([c.chunk_start for c in chunks], dtype=torch.long),
        "sampler_type": [c.sampler_type for c in chunks],
        "valid_len":   torch.tensor([c.valid_len for c in chunks], dtype=torch.long),
    }

    # ---- final dtype enforcement (cheap sanity) ----
    for k, dt in _INPUT_DTYPES.items():
        assert inputs[k].dtype == dt, f"inputs[{k}].dtype={inputs[k].dtype} != {dt}"
    for k, dt in _TARGET_DTYPES.items():
        assert targets[k].dtype == dt, f"targets[{k}].dtype={targets[k].dtype} != {dt}"

    return {
        "inputs": inputs,
        "targets": targets,
        "sample_weight": sw,
        "valid_mask": valid_mask,
        "meta": meta,
    }


# =============================================================================
# 3. helpers
# =============================================================================


def _stack_float32(chunks: Sequence[EpisodeChunk], key: str) -> Tensor:
    arrs = [_get_or_zeros(c, key) for c in chunks]
    return torch.from_numpy(np.stack(arrs, axis=0)).to(torch.float32)


def _stack_long(chunks: Sequence[EpisodeChunk], key: str) -> Tensor:
    arrs = [_get_or_zeros(c, key) for c in chunks]
    out = torch.from_numpy(np.stack(arrs, axis=0)).to(torch.long)
    return out


def _stack_bool_to_float(chunks: Sequence[EpisodeChunk], key: str) -> Tensor:
    arrs = [_get_or_zeros(c, key).astype(np.float32) for c in chunks]
    return torch.from_numpy(np.stack(arrs, axis=0)).to(torch.float32)


def _stack_done_components(chunks: Sequence[EpisodeChunk]) -> tuple[Tensor, Tensor, Tensor]:
    """``dones`` / ``truncateds`` 원본을 분리한 (success_done, truncated, terminal) 3-튜플.

    각 텐서는 ``(B, T)`` float32. invariants:
        - ``terminal == (success_done.bool() | truncated.bool()).float()``
        - 학습 step에서 ``done_target_mode``가 'success_done'이면 ``done := success_done``,
          'terminal'이면 ``done := terminal``로 dispatch (trainer 책임).
    """
    suc_list: List[np.ndarray] = []
    trc_list: List[np.ndarray] = []
    term_list: List[np.ndarray] = []
    for c in chunks:
        d = _get_or_zeros(c, "dones").astype(bool)
        t = _get_or_zeros(c, "truncateds").astype(bool)
        suc_list.append(d.astype(np.float32))
        trc_list.append(t.astype(np.float32))
        term_list.append((d | t).astype(np.float32))
    success_done = torch.from_numpy(np.stack(suc_list, axis=0)).to(torch.float32)
    truncated = torch.from_numpy(np.stack(trc_list, axis=0)).to(torch.float32)
    terminal = torch.from_numpy(np.stack(term_list, axis=0)).to(torch.float32)
    return success_done, truncated, terminal


def _get_or_zeros(c: EpisodeChunk, key: str) -> np.ndarray:
    """key가 없으면 chunk_len 0-array를 만든다 (방어적)."""
    a = c.arrays.get(key)
    if a is None:
        chunk_len = next(iter(c.arrays.values())).shape[0]
        return np.zeros((chunk_len,), dtype=np.float32)
    return a


def _shift_right(action_raw: Tensor) -> Tensor:
    """(B, T) → (B, T). prev[:, 0]=0, prev[:, 1:]=action_raw[:, :-1]."""
    out = torch.zeros_like(action_raw)
    out[:, 1:] = action_raw[:, :-1]
    return out


def _build_valid_mask(chunks: Sequence[EpisodeChunk], chunk_len: int) -> Tensor:
    """sample_weight과는 별도로, padding=0 / valid=1인 binary mask."""
    mask = np.zeros((len(chunks), chunk_len), dtype=np.float32)
    for i, c in enumerate(chunks):
        mask[i, : c.valid_len] = 1.0
    return torch.from_numpy(mask)


def _assert_no_forbidden_keys(inputs: Mapping[str, Tensor]) -> None:
    """oracle leak 방지 — inputs dict에 forbidden key가 들어 있지 않은지 hard 검사."""
    bad = [k for k in inputs.keys() if k in FORBIDDEN_INPUT_KEYS]
    if bad:
        raise RuntimeError(
            f"Forbidden key(s) leaked into model inputs: {bad}. "
            f"FORBIDDEN_INPUT_KEYS = {FORBIDDEN_INPUT_KEYS}"
        )


__all__ = [
    "collate_chunks",
]
