"""RG-4F dataset validator (Session 4).

생성된 dataset이 PART0/RG4F_Environment_Plan/Session 3 contract를 만족하는지
체계적으로 검증한다. 각 invariant 별로 PASS / WARN / FAIL을 기록하고 표 형태로
출력하며 ``--json-report``가 지정되면 결과를 json으로 dump한다.

PART0 §3 / SESSION3_HANDOFF §9 / 사용자 요구사항 §2 정합:
- 본 script는 model / planner / agent / world model 코드가 일절 없다.
- env reset/step API를 사용하지 않는다 (단, ``--check-determinism``일 때 generator를
  subprocess로 한 번 실행하여 별 디렉토리에 dataset을 만들고 비교 후 삭제할 수 있다.
  generator를 import하지 않는 것은 Session 3 generator의 main이 sys.exit를 호출하므로
  test 격리가 무너지기 때문).

종료 코드:
- FAIL이 하나라도 있으면 1.
- WARN만 있거나 PASS면 0.

사용법
------
    python scripts/validate_dataset.py --root data/rg4f
    python scripts/validate_dataset.py --root data/rg4f --strict --max-episodes-per-split 5
    python scripts/validate_dataset.py --root data/rg4f --json-report reports/validation.json
    python scripts/validate_dataset.py --root data/rg4f --check-determinism \\
        --config configs/dataset_default.yaml
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

# 프로젝트 루트를 sys.path에 추가 (script 단독 실행 시 패키지 import 가능하도록)
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from falsifiable_regime_world_model.rg4f.dataset_io import (
    EXPECTED_SPLITS,
    NUM_ACTIONS,
    NUM_LOCAL_CHANNELS,
    OBS_SCALAR_DIM,
    OOD_TYPE_LABELS,
    REQUIRED_NPZ_GROUPS,
    STATE_DIM,
    EpisodeBundle,
    IndexEntry,
    all_required_npz_keys,
    coupled_states_from_meta,
    field_families_from_meta,
    is_finite_array,
    iter_episodes,
    load_index,
    load_manifest,
    missing_required_keys,
    source_positions_from_meta,
)


# =============================================================================
# 1. 검증 결과 컨테이너
# =============================================================================

_STATUS_PASS = "PASS"
_STATUS_WARN = "WARN"
_STATUS_FAIL = "FAIL"


@dataclasses.dataclass
class CheckResult:
    """한 invariant의 검증 결과."""

    name: str
    status: str           # PASS / WARN / FAIL
    detail: str = ""
    scope: str = "global" # global / split=<name> / episode=<id>

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


class Report:
    """전체 검증 진행을 누적한다."""

    def __init__(self) -> None:
        self.results: List[CheckResult] = []

    def add(self, name: str, status: str, detail: str = "", scope: str = "global") -> None:
        if status not in (_STATUS_PASS, _STATUS_WARN, _STATUS_FAIL):
            raise ValueError(f"Invalid status: {status!r}")
        self.results.append(CheckResult(name=name, status=status, detail=detail, scope=scope))

    def passed(self, name: str, detail: str = "", scope: str = "global") -> None:
        self.add(name, _STATUS_PASS, detail, scope)

    def warned(self, name: str, detail: str = "", scope: str = "global") -> None:
        self.add(name, _STATUS_WARN, detail, scope)

    def failed(self, name: str, detail: str = "", scope: str = "global") -> None:
        self.add(name, _STATUS_FAIL, detail, scope)

    def has_fail(self) -> bool:
        return any(r.status == _STATUS_FAIL for r in self.results)

    def has_warn(self) -> bool:
        return any(r.status == _STATUS_WARN for r in self.results)

    def counts(self) -> Dict[str, int]:
        out = {_STATUS_PASS: 0, _STATUS_WARN: 0, _STATUS_FAIL: 0}
        for r in self.results:
            out[r.status] += 1
        return out


# =============================================================================
# 2. 개별 invariant 검사 함수
# =============================================================================

def _check_directory_structure(root: Path, report: Report) -> List[str]:
    """root 아래에 manifest.json + 각 split 폴더 + index.jsonl이 있는지 확인.

    실제 발견한 split 이름 list를 반환 (split coverage 검사가 사용).
    """
    if not root.is_dir():
        report.failed(
            "directory.root_exists",
            detail=f"root directory does not exist: {root}",
        )
        return []
    report.passed("directory.root_exists", detail=str(root))

    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        report.failed("directory.manifest_present", detail=f"missing {manifest_path}")
    else:
        report.passed("directory.manifest_present")

    found_splits: List[str] = []
    for split in EXPECTED_SPLITS:
        sp = root / split
        if not sp.is_dir():
            report.warned(
                "directory.split_dir",
                detail=f"split folder missing: {split}",
                scope=f"split={split}",
            )
            continue
        idx = sp / "index.jsonl"
        eps_dir = sp / "episodes"
        if not idx.is_file():
            report.failed(
                "directory.split_index_jsonl",
                detail=f"missing {idx}",
                scope=f"split={split}",
            )
            continue
        if not eps_dir.is_dir():
            report.failed(
                "directory.split_episodes_dir",
                detail=f"missing {eps_dir}",
                scope=f"split={split}",
            )
            continue
        report.passed("directory.split_dir", scope=f"split={split}")
        found_splits.append(split)
    return found_splits


def _check_split_coverage(found_splits: Sequence[str], report: Report) -> None:
    """기대되는 8개 split이 모두 발견되었는지."""
    missing = [s for s in EXPECTED_SPLITS if s not in found_splits]
    if missing:
        report.failed(
            "split_coverage.all_present",
            detail=f"missing splits: {missing}",
        )
    else:
        report.passed(
            "split_coverage.all_present",
            detail=f"all 8 expected splits found: {list(EXPECTED_SPLITS)}",
        )


def _check_index_entries_exist(
    root: Path, split: str, entries: Sequence[IndexEntry], report: Report,
) -> None:
    """index.jsonl에 기록된 npz/meta 파일이 실제 존재하는지."""
    missing_npz: List[str] = []
    missing_meta: List[str] = []
    for e in entries:
        npz = root / e.npz_path
        if not npz.is_file():
            missing_npz.append(e.episode_id)
        if e.meta_path:
            mp = root / e.meta_path
            if not mp.is_file():
                missing_meta.append(e.episode_id)
    if missing_npz:
        report.failed(
            "index.npz_files_exist",
            detail=f"{len(missing_npz)} missing npz: {missing_npz[:5]}{'...' if len(missing_npz) > 5 else ''}",
            scope=f"split={split}",
        )
    else:
        report.passed("index.npz_files_exist", scope=f"split={split}")
    if missing_meta:
        report.warned(
            "index.meta_files_exist",
            detail=f"{len(missing_meta)} missing meta.json: {missing_meta[:5]}",
            scope=f"split={split}",
        )
    else:
        report.passed("index.meta_files_exist", scope=f"split={split}")


def _check_manifest_count_match(
    manifest: Dict[str, Any],
    split: str,
    actual_count: int,
    report: Report,
) -> None:
    """manifest.counts[split]과 실제 index.jsonl line 수 일치 여부."""
    counts = manifest.get("counts") or {}
    expected = counts.get(split)
    if expected is None:
        report.warned(
            "manifest.split_count_recorded",
            detail=f"manifest.counts missing entry for {split}",
            scope=f"split={split}",
        )
        return
    if int(expected) != int(actual_count):
        report.failed(
            "manifest.split_count_match",
            detail=f"counts[{split}]={expected} but index has {actual_count} entries",
            scope=f"split={split}",
        )
    else:
        report.passed(
            "manifest.split_count_match",
            detail=f"counts[{split}]={expected} matches index lines",
            scope=f"split={split}",
        )


def _check_npz_schema(bundle: EpisodeBundle, report: Report) -> bool:
    """필수 key 모두 존재하는지. group key는 그룹 이름으로 한 번에 체크."""
    arrs = bundle.arrays
    missing = missing_required_keys(arrs)
    scope = f"episode={bundle.entry.episode_id}"
    if missing:
        report.failed(
            "npz.required_keys_present",
            detail=f"missing keys: {missing}",
            scope=scope,
        )
        return False
    report.passed("npz.required_keys_present", scope=scope)

    # group level 보조 검사
    for group_name, keys in REQUIRED_NPZ_GROUPS.items():
        miss = [k for k in keys if k not in arrs]
        if miss:
            report.failed(
                f"npz.group.{group_name}",
                detail=f"missing group keys: {miss}",
                scope=scope,
            )
            return False
    return True


def _check_shape_invariants(
    bundle: EpisodeBundle,
    expected_local_size: int,
    report: Report,
) -> None:
    """T 일치, local_grid shape, scalar dim 등."""
    arrs = bundle.arrays
    scope = f"episode={bundle.entry.episode_id}"
    try:
        T = int(arrs["rewards"].shape[0])
    except Exception as exc:
        report.failed("shape.episode_length", detail=f"{exc!r}", scope=scope)
        return

    # T 일치
    same_T_keys = [
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
        "true_regime_control_mode",
        "change_point",
        "reveal_event",
        "shift_event",
        "reveal_or_shift",
        "task_id",
        "room_id",
        "event_token",
        "target_band_active",
        "target_band_state_dim",
        "target_band_center",
        "target_band_half_width",
        "target_band_kind",
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
    ]
    bad_T: List[str] = []
    for k in same_T_keys:
        if k in arrs and int(arrs[k].shape[0]) != T:
            bad_T.append(f"{k}:{arrs[k].shape}")
    if bad_T:
        report.failed("shape.timesteps_consistent", detail=f"T={T}; mismatched: {bad_T[:5]}", scope=scope)
    else:
        report.passed("shape.timesteps_consistent", detail=f"T={T}", scope=scope)

    # local_grid shape
    lg = arrs["observations_local_grid"]
    if lg.ndim != 4:
        report.failed("shape.local_grid_rank", detail=f"local_grid shape={lg.shape}", scope=scope)
    elif lg.shape[1] != lg.shape[2]:
        report.failed(
            "shape.local_grid_square",
            detail=f"H={lg.shape[1]} W={lg.shape[2]} (must be equal)",
            scope=scope,
        )
    elif lg.shape[3] != NUM_LOCAL_CHANNELS:
        report.failed(
            "shape.local_grid_channels",
            detail=f"C={lg.shape[3]} (expected {NUM_LOCAL_CHANNELS})",
            scope=scope,
        )
    elif lg.shape[1] not in (3, 5, 7):
        report.failed(
            "shape.local_obs_size_in_3_5_7",
            detail=f"local_obs_size={lg.shape[1]} not in {{3,5,7}}",
            scope=scope,
        )
    else:
        report.passed(
            "shape.local_grid_shape",
            detail=f"shape={lg.shape}",
            scope=scope,
        )
        # 기대치(주로 5)와 일치하는지 추가 비교 (warn만)
        if lg.shape[1] != expected_local_size:
            report.warned(
                "shape.local_obs_size_matches_expected",
                detail=f"local_obs_size={lg.shape[1]} (expected from manifest/config={expected_local_size})",
                scope=scope,
            )

    # scalar dim
    sc = arrs["observations_scalar"]
    if sc.ndim != 2 or sc.shape[1] != OBS_SCALAR_DIM:
        report.failed(
            "shape.scalar_dim",
            detail=f"scalar shape={sc.shape} (expected (T, {OBS_SCALAR_DIM}))",
            scope=scope,
        )
    else:
        report.passed("shape.scalar_dim", detail=f"shape={sc.shape}", scope=scope)

    # true_state shape
    ts = arrs["true_state"]
    if ts.shape != (T, STATE_DIM):
        report.failed(
            "shape.true_state",
            detail=f"true_state shape={ts.shape} (expected (T={T}, {STATE_DIM}))",
            scope=scope,
        )
    else:
        report.passed("shape.true_state", scope=scope)

    # next_observations와 observations의 shape 일치
    nxt = arrs["next_observations_local_grid"]
    if nxt.shape != lg.shape:
        report.failed(
            "shape.next_local_matches_obs",
            detail=f"next.shape={nxt.shape} obs.shape={lg.shape}",
            scope=scope,
        )
    else:
        report.passed("shape.next_local_matches_obs", scope=scope)

    # action_mask가 저장되어 있다면 shape 검증 (현재 Session 3는 저장 안 함)
    if "action_mask" in arrs:
        am = arrs["action_mask"]
        if am.ndim != 2 or am.shape != (T, NUM_ACTIONS):
            report.failed(
                "shape.action_mask",
                detail=f"action_mask shape={am.shape} (expected (T={T}, {NUM_ACTIONS}))",
                scope=scope,
            )
        else:
            report.passed("shape.action_mask", scope=scope)


def _check_numeric_validity(bundle: EpisodeBundle, report: Report) -> None:
    """NaN/Inf 없음, state 값 범위, binary field 검증."""
    arrs = bundle.arrays
    scope = f"episode={bundle.entry.episode_id}"

    # finite 검증
    finite_targets = [
        "observations_local_grid",
        "observations_scalar",
        "next_observations_local_grid",
        "next_observations_scalar",
        "rewards",
        "true_state",
        "true_regime_miscontrol_p",
        "target_band_center",
        "target_band_half_width",
        "field_info_mu",
        "field_info_sigma",
        "tick_cost",
        "latency_cost",
        "failure_cost",
        "reset_cost",
        "task_reward",
        "completion_reward",
    ]
    bad_finite: List[str] = []
    for k in finite_targets:
        if k in arrs and not is_finite_array(arrs[k]):
            bad_finite.append(k)
    if bad_finite:
        report.failed(
            "numeric.no_nan_inf",
            detail=f"NaN/Inf in: {bad_finite}",
            scope=scope,
        )
    else:
        report.passed("numeric.no_nan_inf", scope=scope)

    # state 범위: [-1, 1]을 약간 벗어나는 것은 허용 (clip이 step 안에서 일어나지만
    # field/action으로 인해 일시적으로 ε 정도 벗어날 수 있음). 1.5 이상 → FAIL.
    ts = arrs["true_state"]
    if ts.size > 0:
        amax = float(np.max(np.abs(ts)))
        if amax > 1.5:
            report.failed(
                "numeric.true_state_range",
                detail=f"|true_state| max={amax:.4f} (>1.5 is suspicious)",
                scope=scope,
            )
        elif amax > 1.05:
            report.warned(
                "numeric.true_state_range",
                detail=f"|true_state| max={amax:.4f} slightly outside [-1,1]",
                scope=scope,
            )
        else:
            report.passed("numeric.true_state_range", detail=f"max|x|={amax:.4f}", scope=scope)

    # binary field: change_point/reveal_event/shift_event/reset_flag/dones/truncateds는 bool
    for k in ("change_point", "reveal_event", "shift_event", "reset_flag", "dones", "truncateds"):
        if k in arrs:
            arr = arrs[k]
            if arr.dtype != bool:
                report.failed(
                    f"numeric.binary_dtype.{k}",
                    detail=f"{k} dtype={arr.dtype} (expected bool)",
                    scope=scope,
                )

    # reveal_or_shift enum {0,1,2} 범위
    if "reveal_or_shift" in arrs:
        v = arrs["reveal_or_shift"]
        unique = np.unique(v).tolist() if v.size else []
        bad = [int(x) for x in unique if int(x) not in (0, 1, 2)]
        if bad:
            report.failed(
                "numeric.reveal_or_shift_enum",
                detail=f"reveal_or_shift values out of {{0,1,2}}: {bad}",
                scope=scope,
            )
        else:
            report.passed("numeric.reveal_or_shift_enum", scope=scope)

    # actions_raw / actions_effective는 [0, NUM_ACTIONS) 안인지
    for k in ("actions_raw", "actions_effective"):
        if k in arrs and arrs[k].size > 0:
            mn, mx = int(arrs[k].min()), int(arrs[k].max())
            if mn < 0 or mx >= NUM_ACTIONS:
                report.failed(
                    f"numeric.{k}_range",
                    detail=f"{k} range=[{mn},{mx}] not in [0,{NUM_ACTIONS})",
                    scope=scope,
                )

    # task_id / room_id는 -1 (없음) 또는 enum 범위. task_id는 -1..3, room_id는 0..6
    if "task_id" in arrs and arrs["task_id"].size > 0:
        v = arrs["task_id"]
        if int(v.min()) < -1 or int(v.max()) > 3:
            report.failed(
                "numeric.task_id_range",
                detail=f"task_id range=[{int(v.min())},{int(v.max())}] outside [-1,3]",
                scope=scope,
            )
    if "room_id" in arrs and arrs["room_id"].size > 0:
        v = arrs["room_id"]
        if int(v.min()) < -1 or int(v.max()) > 6:
            report.failed(
                "numeric.room_id_range",
                detail=f"room_id range=[{int(v.min())},{int(v.max())}] outside [-1,6]",
                scope=scope,
            )

    # reset_flag는 항상 False (Session 3 contract)
    if "reset_flag" in arrs and arrs["reset_flag"].size > 0:
        if bool(arrs["reset_flag"].any()):
            report.warned(
                "numeric.reset_flag_always_false",
                detail="reset_flag has True somewhere (Session 3 contract is always False during step)",
                scope=scope,
            )


def _check_sparse_coupling(bundle: EpisodeBundle, report: Report) -> None:
    """invisible field의 coupled_states가 |·| ≤ 2임을 확인 (PART0 §3 §10)."""
    scope = f"episode={bundle.entry.episode_id}"
    if bundle.meta is None:
        report.warned(
            "sparse_coupling.meta_present",
            detail="meta.json missing; cannot check sparse coupling",
            scope=scope,
        )
        return
    coupled = coupled_states_from_meta(bundle.meta)
    if not coupled:
        # 0개 field인 경우는 PASS로 처리 (invisible field가 없는 episode)
        report.passed(
            "sparse_coupling.le2",
            detail="no invisible fields recorded",
            scope=scope,
        )
        return
    bad = [(i, cs) for i, cs in enumerate(coupled) if len(cs) > 2]
    if bad:
        report.failed(
            "sparse_coupling.le2",
            detail=f"|coupled_states|>2 found at fields: {bad}",
            scope=scope,
        )
    else:
        report.passed(
            "sparse_coupling.le2",
            detail=f"all {len(coupled)} fields have |coupled_states|<=2",
            scope=scope,
        )


def _check_split_specific(
    split: str,
    bundle: EpisodeBundle,
    manifest: Dict[str, Any],
    report: Report,
    layout_full_h: int,
    layout_full_w: int,
) -> None:
    """OOD split별 invariant. 단일 episode 단위 검사를 모아 호출한다."""
    scope = f"episode={bundle.entry.episode_id}"
    meta = bundle.meta or {}
    expected_ood_type = OOD_TYPE_LABELS.get(split)
    if expected_ood_type is not None:
        # is_ood / ood_type metadata
        if not bool(meta.get("is_ood", False)) or str(meta.get("ood_type", "")) != expected_ood_type:
            report.failed(
                "split_specific.ood_metadata",
                detail=f"meta is_ood={meta.get('is_ood')} ood_type={meta.get('ood_type')} (expected ood_type={expected_ood_type})",
                scope=scope,
            )
        else:
            report.passed("split_specific.ood_metadata", scope=scope)

    if split in ("train", "valid", "test_id"):
        # train/valid/test_id는 같은 distribution. is_ood=False여야.
        if bool(meta.get("is_ood", False)):
            report.failed(
                "split_specific.id_not_ood",
                detail=f"is_ood=True in {split} episode",
                scope=scope,
            )
        else:
            report.passed("split_specific.id_not_ood", scope=scope)

    if split == "ood_room_perm":
        train_pool = {tuple(p) for p in manifest.get("train_pool", [])}
        ood_pool = {tuple(p) for p in manifest.get("ood_pool", [])}
        forced = tuple(meta.get("forced_permutation", []))
        if not forced:
            report.failed(
                "split_specific.room_perm.forced_present",
                detail="forced_permutation missing in meta",
                scope=scope,
            )
            return
        if forced in train_pool:
            report.failed(
                "split_specific.room_perm.disjoint_from_train",
                detail=f"forced_permutation={forced} is in train_pool",
                scope=scope,
            )
        else:
            report.passed(
                "split_specific.room_perm.disjoint_from_train",
                detail=f"forced_permutation={forced} not in train_pool",
                scope=scope,
            )
        if ood_pool and forced not in ood_pool:
            report.warned(
                "split_specific.room_perm.in_ood_pool",
                detail=f"forced_permutation={forced} not in ood_pool {sorted(ood_pool)[:3]}",
                scope=scope,
            )

    if split == "ood_factor_recomb":
        # episode 단위로 family pool ⊂ ood_field_families
        # Session 3 manifest의 split_summaries[ood_factor_recomb].field_family_pool
        summaries = manifest.get("split_summaries", []) or []
        ood_pool: List[int] = []
        for s in summaries:
            if s.get("split") == "ood_factor_recomb":
                ood_pool = [int(x) for x in (s.get("field_family_pool") or [])]
                break
        families = field_families_from_meta(meta)
        if not ood_pool:
            report.warned(
                "split_specific.factor_recomb.ood_pool_recorded",
                detail="manifest split_summaries does not record field_family_pool for ood_factor_recomb",
                scope=scope,
            )
        if families and ood_pool:
            outside = [f for f in families if f not in ood_pool]
            if outside:
                report.failed(
                    "split_specific.factor_recomb.families_in_ood_pool",
                    detail=f"families {outside} not in ood_pool {ood_pool}",
                    scope=scope,
                )
            else:
                report.passed(
                    "split_specific.factor_recomb.families_in_ood_pool",
                    detail=f"all families {families} ⊂ ood_pool {ood_pool}",
                    scope=scope,
                )
        elif not families:
            # field가 0개로 끝난 episode는 의심스럽지만 manifest filter retry 후에도
            # 발생 가능 (Session 3 family_filter_max_retries=8 후 fallback). WARN.
            report.warned(
                "split_specific.factor_recomb.has_fields",
                detail="no invisible fields after filter (rare, possibly retries exhausted)",
                scope=scope,
            )

    if split == "ood_param_shift":
        override = meta.get("rg4f_kwargs_override", {}) or {}
        rg4f_cfg = manifest.get("rg4f_config", {}) or {}
        # 적어도 drift_strength_multiplier 또는 shift_probability_multiplier가 적용되어야
        if not override:
            report.failed(
                "split_specific.param_shift.override_present",
                detail="rg4f_kwargs_override is empty for param_shift episode",
                scope=scope,
            )
        else:
            # 핵심 4개 키 중 적어도 하나는 base 보다 strict하게 다르다.
            keys_to_check = [
                "field_mu_drift_sigma",
                "shift_prob_per_room_entry",
                "shift_prob_per_checkpoint",
                "shift_prob_per_stele_activation",
                "field_radius_max",
            ]
            differs = []
            for k in keys_to_check:
                if k in override:
                    base = float(rg4f_cfg.get(k, 0.0) or 0.0)
                    new = float(override[k])
                    if abs(new - base) > 1e-9:
                        differs.append((k, base, new))
            if not differs:
                report.failed(
                    "split_specific.param_shift.differs_from_train",
                    detail=f"override has no actually-different keys; override={override}",
                    scope=scope,
                )
            else:
                report.passed(
                    "split_specific.param_shift.differs_from_train",
                    detail=f"differs={differs}",
                    scope=scope,
                )

    if split == "ood_obs_shift":
        perm = meta.get("obs_channel_perm")
        if perm is None:
            report.failed(
                "split_specific.obs_shift.channel_perm_present",
                detail="obs_channel_perm missing in meta",
                scope=scope,
            )
        else:
            perm_list = list(perm)
            if sorted(perm_list) != list(range(NUM_LOCAL_CHANNELS)):
                report.failed(
                    "split_specific.obs_shift.channel_perm_valid",
                    detail=f"obs_channel_perm={perm_list} is not a permutation of 0..{NUM_LOCAL_CHANNELS - 1}",
                    scope=scope,
                )
            elif perm_list == list(range(NUM_LOCAL_CHANNELS)):
                report.warned(
                    "split_specific.obs_shift.channel_perm_nontrivial",
                    detail="obs_channel_perm is identity (no actual shift)",
                    scope=scope,
                )
            else:
                report.passed(
                    "split_specific.obs_shift.channel_perm_valid",
                    detail=f"perm={perm_list}",
                    scope=scope,
                )
        # rg4f_kwargs_override는 비어있어야 (underlying dynamics는 train과 동일)
        if meta.get("rg4f_kwargs_override"):
            report.warned(
                "split_specific.obs_shift.no_dynamics_change",
                detail=f"unexpected override in obs_shift: {meta['rg4f_kwargs_override']}",
                scope=scope,
            )

    if split == "ood_field_placement":
        if not bool(meta.get("relocate_fields_room_center", False)):
            report.failed(
                "split_specific.field_placement.relocate_flag",
                detail="relocate_fields_room_center=False in field_placement episode",
                scope=scope,
            )
        else:
            report.passed("split_specific.field_placement.relocate_flag", scope=scope)
        # source_position이 grid 안에 있는지
        positions = source_positions_from_meta(meta)
        bad_pos = [
            (r, c) for (r, c) in positions
            if r < 0 or r >= layout_full_h or c < 0 or c >= layout_full_w
        ]
        if bad_pos:
            report.failed(
                "split_specific.field_placement.source_in_grid",
                detail=f"out-of-grid sources: {bad_pos}",
                scope=scope,
            )


def _grid_full_size_from_manifest(manifest: Dict[str, Any]) -> tuple[int, int]:
    """manifest.rg4f_config의 hall/room/corridor로부터 (full_h, full_w) 계산.

    env.map_generator의 ``_make_anchors``: full = 6 + 2*rs + 2*cs + hs (room/corridor/hall).
    cross 토폴로지는 정사각형이므로 full_h == full_w.
    """
    cfg = manifest.get("rg4f_config", {}) or {}
    rs = int(cfg.get("room_size", 8))
    cs = int(cfg.get("corridor_length", 3))
    hs = int(cfg.get("hall_size", 9))
    full = 6 + 2 * rs + 2 * cs + hs
    return full, full


# =============================================================================
# 3. determinism check (옵션)
# =============================================================================

def _check_determinism(
    config_path: Path,
    report: Report,
    timeout_sec: float = 60.0,
) -> None:
    """같은 config + 같은 seed로 generator를 두 번 호출하여 dataset이 동일한지.

    별도의 임시 디렉토리 두 개에 작은 dataset (각 split 1 episode, max-steps 30)을
    만든 뒤 manifest의 rg4f_config + 모든 npz의 array hash를 비교한다.
    실패 시 임시 디렉토리는 항상 정리된다.
    """
    if not config_path.is_file():
        report.failed(
            "determinism.config_present",
            detail=f"config not found: {config_path}",
        )
        return

    runner = sys.executable
    generate_script = _PROJECT_ROOT / "scripts" / "generate_dataset.py"
    if not generate_script.is_file():
        report.failed(
            "determinism.generator_present",
            detail=f"generate_dataset.py missing at {generate_script}",
        )
        return

    tmp = Path(tempfile.mkdtemp(prefix="rg4f_determ_"))
    try:
        out_a = tmp / "a"
        out_b = tmp / "b"
        common_args = [
            runner,
            str(generate_script),
            "--config",
            str(config_path),
            "--num-train",
            "1",
            "--num-valid",
            "1",
            "--num-test",
            "1",
            "--num-ood-per-type",
            "1",
            "--max-steps",
            "30",
            "--seed",
            "777",
            "--overwrite",
        ]
        for out_dir in (out_a, out_b):
            args = list(common_args) + ["--output-root", str(out_dir)]
            try:
                proc = subprocess.run(
                    args,
                    cwd=str(_PROJECT_ROOT),
                    capture_output=True,
                    timeout=timeout_sec,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                report.failed(
                    "determinism.subprocess_returncode",
                    detail=f"timeout after {timeout_sec}s for {out_dir}",
                )
                return
            if proc.returncode != 0:
                stderr_tail = proc.stderr.decode("utf-8", errors="replace")[-300:]
                report.failed(
                    "determinism.subprocess_returncode",
                    detail=f"generator failed for {out_dir}: rc={proc.returncode} stderr={stderr_tail}",
                )
                return

        # 결과 비교
        diffs: List[str] = []
        for split in EXPECTED_SPLITS:
            a_dir = out_a / split / "episodes"
            b_dir = out_b / split / "episodes"
            if not a_dir.is_dir() or not b_dir.is_dir():
                continue
            a_files = sorted(p.name for p in a_dir.glob("*.npz"))
            b_files = sorted(p.name for p in b_dir.glob("*.npz"))
            if a_files != b_files:
                diffs.append(f"{split}: filenames differ a={a_files[:3]} b={b_files[:3]}")
                continue
            for fn in a_files:
                fa = a_dir / fn
                fb = b_dir / fn
                with np.load(fa) as A, np.load(fb) as B:
                    keys_a = sorted(A.files)
                    keys_b = sorted(B.files)
                    if keys_a != keys_b:
                        diffs.append(f"{split}/{fn}: keys differ")
                        continue
                    for k in keys_a:
                        if not np.array_equal(A[k], B[k]):
                            diffs.append(f"{split}/{fn}: array {k} differs")
                            break
        if diffs:
            report.failed(
                "determinism.equal_output",
                detail=f"{len(diffs)} differences; first: {diffs[:3]}",
            )
        else:
            report.passed(
                "determinism.equal_output",
                detail="two runs of generator with same seed produce identical npz",
            )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# =============================================================================
# 4. 메인 entry
# =============================================================================

def _format_table(report: Report) -> str:
    """terminal에 출력할 표 형태 텍스트."""
    rows = [(r.scope, r.name, r.status, r.detail) for r in report.results]
    if not rows:
        return "(no checks performed)"
    # column widths
    w_scope = max(len("scope"), max(len(r[0]) for r in rows))
    w_name = max(len("check"), max(len(r[1]) for r in rows))
    w_stat = max(len("status"), max(len(r[2]) for r in rows))
    out: List[str] = []
    header = f"{'scope'.ljust(w_scope)}  {'check'.ljust(w_name)}  {'status'.ljust(w_stat)}  detail"
    out.append(header)
    out.append("-" * len(header))
    for scope, name, status, detail in rows:
        d = detail if len(detail) <= 200 else detail[:200] + "..."
        out.append(f"{scope.ljust(w_scope)}  {name.ljust(w_name)}  {status.ljust(w_stat)}  {d}")
    return "\n".join(out)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="RG-4F dataset validator (Session 4)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--root", type=str, default="data/rg4f", help="dataset output_root")
    p.add_argument(
        "--split",
        type=str,
        default="all",
        help="single split name to validate, or 'all' (default)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="treat WARN as FAIL when computing exit code",
    )
    p.add_argument(
        "--max-episodes-per-split",
        type=int,
        default=10,
        help="how many episodes to deeply inspect per split (0 = all)",
    )
    p.add_argument(
        "--check-determinism",
        action="store_true",
        help="run generator twice with same seed in temp dir and compare outputs",
    )
    p.add_argument(
        "--config",
        type=str,
        default=None,
        help="generator config (required when --check-determinism)",
    )
    p.add_argument(
        "--json-report",
        type=str,
        default=None,
        help="write detailed report to this json path",
    )
    p.add_argument("--verbose", action="store_true", help="print full table to stdout")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(args.root).resolve()
    report = Report()

    # 1) directory / file structure
    found_splits = _check_directory_structure(root, report)
    if not found_splits:
        # root 자체가 없거나 split이 하나도 없으면 더 진행 불가
        return _finish(report, args)

    # 2) split coverage
    _check_split_coverage(found_splits, report)

    # 3) manifest 로드
    try:
        manifest = load_manifest(root)
        report.passed("manifest.json_loaded")
    except Exception as exc:
        report.failed("manifest.json_loaded", detail=f"{exc!r}")
        return _finish(report, args)

    # expected local_obs_size (manifest의 rg4f_config로부터)
    rg4f_cfg = manifest.get("rg4f_config", {}) or {}
    expected_local_size = int(rg4f_cfg.get("local_obs_size", 5))
    full_h, full_w = _grid_full_size_from_manifest(manifest)

    # 4) split별 episode 단위 검사
    if args.split == "all":
        target_splits = found_splits
    else:
        if args.split not in found_splits:
            report.failed(
                "args.split_exists",
                detail=f"requested split '{args.split}' not found among {found_splits}",
            )
            return _finish(report, args)
        target_splits = [args.split]

    for split in target_splits:
        try:
            entries = load_index(root / split)
        except Exception as exc:
            report.failed(
                "split.index_loaded",
                detail=f"{exc!r}",
                scope=f"split={split}",
            )
            continue
        report.passed(
            "split.index_loaded",
            detail=f"{len(entries)} entries",
            scope=f"split={split}",
        )

        _check_index_entries_exist(root, split, entries, report)
        _check_manifest_count_match(manifest, split, len(entries), report)

        # 각 episode 단위 검사
        max_ep = args.max_episodes_per_split if args.max_episodes_per_split > 0 else None
        inspected = 0
        for bundle in iter_episodes(root, split, max_episodes=max_ep):
            inspected += 1
            if not _check_npz_schema(bundle, report):
                continue
            _check_shape_invariants(bundle, expected_local_size, report)
            _check_numeric_validity(bundle, report)
            _check_sparse_coupling(bundle, report)
            _check_split_specific(split, bundle, manifest, report, full_h, full_w)
        report.passed(
            "split.episodes_inspected",
            detail=f"deep-inspected {inspected} episodes (limit={args.max_episodes_per_split})",
            scope=f"split={split}",
        )

    # 5) determinism check (옵션)
    if args.check_determinism:
        if not args.config:
            report.failed(
                "determinism.config_required",
                detail="--check-determinism requires --config <path>",
            )
        else:
            _check_determinism(Path(args.config).resolve(), report)

    return _finish(report, args)


def _finish(report: Report, args: argparse.Namespace) -> int:
    """결과 표 출력 + json report 저장 + exit code 결정."""
    counts = report.counts()
    table = _format_table(report)

    if args.verbose or report.has_fail() or report.has_warn():
        print(table)
    print()
    summary = (
        f"=== Validation summary === "
        f"PASS: {counts['PASS']}  WARN: {counts['WARN']}  FAIL: {counts['FAIL']}"
    )
    print(summary)

    if args.json_report:
        out_path = Path(args.json_report).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": counts,
            "has_fail": report.has_fail(),
            "has_warn": report.has_warn(),
            "checks": [r.to_dict() for r in report.results],
        }
        with out_path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)
        print(f"json report -> {out_path}")

    if report.has_fail():
        return 1
    if args.strict and report.has_warn():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
