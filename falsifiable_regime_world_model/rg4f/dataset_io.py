"""RG-4F dataset 입출력 / schema 헬퍼 (Session 4).

Session 3의 ``scripts/generate_dataset.py``가 만든 dataset
(``data/rg4f/<split>/episodes/*.npz`` + ``index.jsonl`` + ``manifest.json``)을
inspect / validate 두 script가 공통으로 읽기 위한 단일 source of truth.

본 모듈은 다음만 책임진다.
    1) manifest.json / index.jsonl / episode npz / episode_meta.json 로드.
    2) Session 3 npz schema의 필수 key 그룹 정의 (validate_dataset가 사용).
    3) field_info_static에서 sparse coupling 등을 추출하기 위한 단순 헬퍼.

PART0 §3 / SESSION3_HANDOFF §1 정합:
- 본 모듈은 model / planner / agent 코드와 완전히 분리되어 있다.
- environment 코드의 reset/step/observe API를 일절 변경하지 않는다.
- numpy + 표준 라이브러리만 사용 (PyTorch / DreamerV3 import 0회).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

import numpy as np


# =============================================================================
# 1. Session 3가 저장하는 npz schema (single source of truth)
# =============================================================================
#
# 본 표는 SESSION3_HANDOFF §3.2와 정확히 일치한다.
# 사용자 요구사항 §2.3은 "필수 key" 목록을 명시하지만, Session 3는 ``true_regime``,
# ``target_band``, ``field_info``를 단일 key가 아닌 분해 key로 저장한다. 따라서
# 검증은 "그룹" 단위로 수행한다 (예: ``true_regime`` 그룹 = control_mode, mobility_mode,
# miscontrol_p, periodic_slip 4개 key 모두 존재).

# 본문에서 1:1 key (단일 array)
REQUIRED_NPZ_KEYS_FLAT: Tuple[str, ...] = (
    "observations_local_grid",
    "observations_scalar",
    "observations_event_token",
    "next_observations_local_grid",
    "next_observations_scalar",
    "next_observations_event_token",
    "actions_raw",
    "actions_effective",
    "rewards",
    "dones",
    "truncateds",
    "true_state",
    "change_point",
    "reveal_event",
    "shift_event",
    "reveal_or_shift",
    "task_id",
    "room_id",
    "event_token",
    "agent_position",
    "completed_tasks",
    "failure_count",
    "tick_cost",
    "latency_cost",
    "failure_cost",
    "reset_cost",
    "task_reward",
    "completion_reward",
    "reset_flag",
)

# 그룹 key: 사용자 요구사항 §2.3의 "true_regime", "target_band", "field_info"는
# Session 3가 아래 분해 key로 저장한다. 그룹 안의 모든 key가 존재해야 PASS.
REQUIRED_NPZ_GROUPS: Dict[str, Tuple[str, ...]] = {
    "true_regime": (
        "true_regime_control_mode",
        "true_regime_mobility_mode",
        "true_regime_miscontrol_p",
        "true_regime_periodic_slip",
    ),
    "target_band": (
        "target_band_active",
        "target_band_state_dim",
        "target_band_center",
        "target_band_half_width",
        "target_band_kind",
    ),
    "field_info": (
        "field_info_mu",
        "field_info_sigma",
    ),
}


def all_required_npz_keys() -> Tuple[str, ...]:
    """평면 key + 그룹 내부 key를 모두 합친 전체 required key 목록."""
    flat = list(REQUIRED_NPZ_KEYS_FLAT)
    for group_keys in REQUIRED_NPZ_GROUPS.values():
        flat.extend(group_keys)
    return tuple(flat)


# 8개 표준 split. validate_dataset의 split coverage 검사가 사용.
EXPECTED_SPLITS: Tuple[str, ...] = (
    "train",
    "valid",
    "test_id",
    "ood_room_perm",
    "ood_factor_recomb",
    "ood_param_shift",
    "ood_obs_shift",
    "ood_field_placement",
)

# OOD split → metadata에 기대되는 ood_type 라벨
OOD_TYPE_LABELS: Dict[str, str] = {
    "ood_room_perm": "room_perm",
    "ood_factor_recomb": "factor_recomb",
    "ood_param_shift": "param_shift",
    "ood_obs_shift": "obs_shift",
    "ood_field_placement": "field_placement",
}

# action 수 (env types.Action) — schema sanity check에 사용.
NUM_ACTIONS: int = 16

# observation local grid의 channel 수 (types.LOCAL_CHANNELS 길이)
NUM_LOCAL_CHANNELS: int = 10

# obs scalar dim (Session 2/3 결정)
OBS_SCALAR_DIM: int = 14

# state vector 차원
STATE_DIM: int = 5


# =============================================================================
# 2. dataclass: 로드 결과 컨테이너
# =============================================================================

@dataclass
class IndexEntry:
    """index.jsonl의 한 줄을 그대로 들고 있는 컨테이너."""

    episode_id: str
    split: str
    is_ood: bool
    ood_type: Optional[str]
    npz_path: str
    meta_path: Optional[str]
    episode_length: int
    permutation_id: int
    forced_permutation: List[int]
    env_seed: int
    num_invisible_fields: int
    raw: Dict[str, Any]   # 원본 dict (앞으로 추가될 key 보존)


@dataclass
class EpisodeBundle:
    """한 episode의 npz + meta + index entry를 한 묶음으로 반환."""

    entry: IndexEntry
    arrays: Dict[str, np.ndarray]
    meta: Optional[Dict[str, Any]]
    npz_path: Path
    meta_path: Optional[Path]


# =============================================================================
# 3. 로드 헬퍼
# =============================================================================

def load_manifest(root: Path) -> Dict[str, Any]:
    """``<root>/manifest.json``을 dict로 반환한다.

    파일이 없으면 ``FileNotFoundError``. 빈 dict나 잘못된 형태면 ``ValueError``.
    """
    p = root / "manifest.json"
    if not p.is_file():
        raise FileNotFoundError(f"manifest.json not found at {p}")
    with p.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, dict):
        raise ValueError(f"manifest.json must be a dict; got {type(data).__name__}")
    return data


def load_index(split_dir: Path) -> List[IndexEntry]:
    """``<split_dir>/index.jsonl``을 읽어 IndexEntry 리스트를 반환한다.

    빈 파일이면 빈 리스트. JSON parsing 실패는 그대로 전파.
    """
    p = split_dir / "index.jsonl"
    if not p.is_file():
        raise FileNotFoundError(f"index.jsonl not found at {p}")
    entries: List[IndexEntry] = []
    raw_text = p.read_text(encoding="utf-8").strip()
    if not raw_text:
        return entries
    for lineno, line in enumerate(raw_text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"index.jsonl {p} line {lineno} invalid: {exc}") from exc
        entries.append(IndexEntry(
            episode_id=str(obj.get("episode_id", "")),
            split=str(obj.get("split", "")),
            is_ood=bool(obj.get("is_ood", False)),
            ood_type=obj.get("ood_type"),
            npz_path=str(obj.get("npz_path", "")),
            meta_path=obj.get("meta_path"),
            episode_length=int(obj.get("episode_length", 0)),
            permutation_id=int(obj.get("permutation_id", -1)),
            forced_permutation=list(obj.get("forced_permutation", [])),
            env_seed=int(obj.get("env_seed", 0)),
            num_invisible_fields=int(obj.get("num_invisible_fields", 0)),
            raw=obj,
        ))
    return entries


def load_episode(
    root: Path,
    entry: IndexEntry,
    *,
    load_meta: bool = True,
    mmap: bool = False,
) -> EpisodeBundle:
    """index entry를 받아 npz + meta.json을 모두 읽어 ``EpisodeBundle``로 반환한다.

    Parameters
    ----------
    root : Path
        dataset의 ``output_root`` (manifest.json이 있는 폴더).
    entry : IndexEntry
    load_meta : bool
        False이면 meta.json은 로드하지 않는다 (대용량 dataset에서 IO 절약).
    mmap : bool
        np.load의 mmap_mode='r' 사용 여부. inspect/validate 단계에서는 보통 False.
    """
    npz_path = (root / entry.npz_path).resolve()
    if not npz_path.is_file():
        raise FileNotFoundError(f"npz file not found: {npz_path}")

    arrays: Dict[str, np.ndarray] = {}
    # np.load의 npz는 lazy. 강제 read를 위해 dict copy.
    with np.load(npz_path, mmap_mode="r" if mmap else None, allow_pickle=False) as data:
        for k in data.files:
            if mmap:
                arrays[k] = data[k]
            else:
                # NpzFile은 contextmanager 종료 시 닫히므로 array를 미리 복사
                arrays[k] = np.array(data[k])

    meta: Optional[Dict[str, Any]] = None
    meta_path: Optional[Path] = None
    if load_meta and entry.meta_path:
        meta_path = (root / entry.meta_path).resolve()
        if meta_path.is_file():
            with meta_path.open("r", encoding="utf-8") as fp:
                meta = json.load(fp)
    return EpisodeBundle(
        entry=entry,
        arrays=arrays,
        meta=meta,
        npz_path=npz_path,
        meta_path=meta_path,
    )


def iter_episodes(
    root: Path,
    split: str,
    *,
    load_meta: bool = True,
    max_episodes: Optional[int] = None,
) -> Iterator[EpisodeBundle]:
    """split의 episode를 순차적으로 yield한다.

    ``max_episodes``가 주어지면 앞에서 N개만 yield (validate의 sample 검사용).
    """
    split_dir = root / split
    if not split_dir.is_dir():
        return
    entries = load_index(split_dir)
    if max_episodes is not None:
        entries = entries[: int(max_episodes)]
    for entry in entries:
        yield load_episode(root, entry, load_meta=load_meta)


# =============================================================================
# 4. schema 검증 헬퍼 (validate_dataset.py가 직접 사용)
# =============================================================================

def missing_required_keys(arrays: Dict[str, np.ndarray]) -> List[str]:
    """npz arrays dict에서 빠진 required key 목록을 돌려준다 (없으면 빈 리스트)."""
    return [k for k in all_required_npz_keys() if k not in arrays]


def is_finite_array(arr: np.ndarray) -> bool:
    """numeric array에 NaN/Inf가 없는지 검사. bool/int는 항상 finite."""
    if arr.dtype.kind in ("b", "i", "u"):
        return True
    if arr.dtype.kind not in ("f", "c"):
        # 그 외 dtype (object 등)은 finite 검사를 우회 → False로 거부
        return False
    return bool(np.all(np.isfinite(arr)))


def first_episode_length(arrays: Dict[str, np.ndarray]) -> int:
    """대표 array의 T를 추출 (rewards 또는 actions_raw 기준)."""
    for k in ("rewards", "actions_raw", "true_state"):
        if k in arrays:
            arr = arrays[k]
            return int(arr.shape[0])
    raise KeyError("None of (rewards, actions_raw, true_state) present in npz arrays.")


def coupled_states_from_meta(meta: Dict[str, Any]) -> List[List[int]]:
    """episode_meta.json의 ``field_info_static`` → list[list[int]] 추출."""
    fields = meta.get("field_info_static", []) or []
    result: List[List[int]] = []
    for f in fields:
        cs = f.get("coupled_states", [])
        result.append([int(x) for x in cs])
    return result


def field_families_from_meta(meta: Dict[str, Any]) -> List[int]:
    """episode_meta.json의 ``field_info_static`` → family ID 리스트."""
    fields = meta.get("field_info_static", []) or []
    return [int(f.get("family", -1)) for f in fields]


def source_positions_from_meta(meta: Dict[str, Any]) -> List[Tuple[int, int]]:
    """episode_meta.json의 ``field_info_static`` → (source_row, source_col) 리스트."""
    fields = meta.get("field_info_static", []) or []
    return [(int(f.get("source_row", -1)), int(f.get("source_col", -1))) for f in fields]


def split_dirs(root: Path) -> List[Tuple[str, Path]]:
    """root 아래의 모든 split 폴더 후보 (이름 + 경로) 리스트.

    EXPECTED_SPLITS 외에도 root 직속의 디렉토리는 모두 후보로 보고,
    ``index.jsonl``이 있는 것만 split으로 인정한다.
    """
    if not root.is_dir():
        return []
    out: List[Tuple[str, Path]] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if (child / "index.jsonl").is_file():
            out.append((child.name, child))
    return out


__all__ = [
    "REQUIRED_NPZ_KEYS_FLAT",
    "REQUIRED_NPZ_GROUPS",
    "all_required_npz_keys",
    "EXPECTED_SPLITS",
    "OOD_TYPE_LABELS",
    "NUM_ACTIONS",
    "NUM_LOCAL_CHANNELS",
    "OBS_SCALAR_DIM",
    "STATE_DIM",
    "IndexEntry",
    "EpisodeBundle",
    "load_manifest",
    "load_index",
    "load_episode",
    "iter_episodes",
    "missing_required_keys",
    "is_finite_array",
    "first_episode_length",
    "coupled_states_from_meta",
    "field_families_from_meta",
    "source_positions_from_meta",
    "split_dirs",
]
