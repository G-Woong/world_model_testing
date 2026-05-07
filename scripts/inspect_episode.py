"""RG-4F episode inspector (Session 4).

사람이 단일 episode를 직접 확인할 수 있도록 episode metadata, transition summary,
step-level inspection, local grid ASCII view, field/task debug를 출력하는 도구.

PART0 §3 / SESSION3_HANDOFF §9 정합:
- model / planner / agent 코드 일절 없음. PyTorch / DreamerV3 import 0회.
- env reset/step API를 호출하지 않는다 (저장된 npz + meta.json만 읽음).

사용법
------
기본:
    python scripts/inspect_episode.py --root data/rg4f --split train --index 0

step range 확인:
    python scripts/inspect_episode.py --root data/rg4f --split train --index 0 \\
        --step 0 --num-steps 10 --show-grid --show-scalar --show-info

OOD episode 확인:
    python scripts/inspect_episode.py --root data/rg4f --split ood_room_perm --index 0 \\
        --num-steps 3 --show-task --show-fields

직접 npz/meta 경로 지정:
    python scripts/inspect_episode.py --episode-path data/rg4f/train/episodes/train_000000.npz \\
        --meta-path data/rg4f/train/episodes/train_000000.meta.json

ASCII 결과 저장:
    python scripts/inspect_episode.py --root data/rg4f --split train --index 0 \\
        --num-steps 5 --show-grid --save-ascii outputs/episode_inspect.txt
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# 프로젝트 루트를 sys.path에 추가
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from falsifiable_regime_world_model.rg4f.dataset_io import (
    NUM_LOCAL_CHANNELS,
    EpisodeBundle,
    IndexEntry,
    load_episode,
    load_index,
)


# =============================================================================
# 1. enum reverse map (출력 가독성을 위해)
# =============================================================================

_ACTION_NAMES = (
    "W", "A", "S", "D", "E",
    "V_PLUS", "V_MINUS", "M_PLUS", "M_MINUS", "I_PLUS",
    "I_MINUS", "N_PLUS", "N_MINUS", "D_PLUS", "D_MINUS", "WAIT",
)
_EVENT_NAMES = (
    "NONE", "ROOM_ENTRY", "ROOM_EXIT", "INTERACTION_SUCCESS", "INTERACTION_FAIL",
    "CHECKPOINT", "DOOR_OPEN", "STELE_TOGGLE", "TILE_FIRST_TOUCH", "FORCED_RESET",
    "CARRY_PICKUP", "CARRY_DROP", "TASK_COMPLETE",
)
_ROOM_NAMES = ("CENTRAL", "NORTH", "SOUTH", "EAST", "WEST", "CORRIDOR", "OUTSIDE")
_TASK_NAMES = ("A", "B", "C", "D")
_CONTROL_NAMES = ("IDENTITY", "CW", "LR", "UD", "REV")
_FIELD_FAMILY_NAMES = ("VISIBILITY", "FRICTION", "INTERACTION_INTERFERENCE", "CONTROL_INTERFERENCE")
_STATE_DIM_NAMES = ("vision", "mobility", "interaction", "noise", "control_drift")
_REVEAL_SHIFT_NAMES = ("none", "reveal", "shift")
_TARGET_BAND_KIND_NAMES = ("none", "match_to_band", "maximize", "threshold", "derivative_zero")


def _safe_name(table, idx: int, prefix: str = "?") -> str:
    """idx가 범위 안이면 이름, 아니면 prefix(idx)."""
    if 0 <= idx < len(table):
        return table[idx]
    if idx == -1:
        return f"{prefix}NONE"
    return f"{prefix}{idx}"


# =============================================================================
# 2. local_grid → ASCII 변환
# =============================================================================
#
# 본 환경 (Session 2)의 LOCAL_CHANNELS:
#   0: wall, 1: floor, 2: corridor, 3: door, 4: task_object,
#   5: stele, 6: altar, 7: cue, 8: agent, 9: traversable
#
# 본 mapping은 Session 2 types.LOCAL_CHANNELS와 정확히 일치한다.
# obs_shift split에서 channel permutation이 적용된 episode는 이 mapping이 의미가
# 깨질 수 있다 (의도적). 그 경우는 출력 헤더에 명시한다.

# 우선순위 ASCII 글자 (높을수록 위에 그려짐)
# (channel_idx, threshold, char, label)
_ASCII_CHANNEL_LAYERS = (
    (8, 0.5, "@", "agent"),
    (3, 0.5, "+", "door"),
    (4, 0.5, "*", "task_object"),
    (5, 0.5, "S", "stele"),
    (6, 0.5, "A", "altar"),
    (7, 0.5, "?", "cue"),
    (0, 0.5, "#", "wall"),
    (2, 0.5, "-", "corridor"),
    (1, 0.5, ".", "floor"),
    (9, 0.5, " ", "traversable"),
)


def _local_grid_to_ascii(grid_t: np.ndarray) -> str:
    """단일 시점 local grid (H, W, C) → ASCII 문자열.

    높은 우선순위 channel 먼저 그리고, 그 다음 낮은 우선순위 channel을 채운다.
    """
    if grid_t.ndim != 3:
        return f"<invalid grid shape {grid_t.shape}>"
    H, W, C = grid_t.shape
    # 기본 ' ' (빈 공간)
    ascii_grid = [[" "] * W for _ in range(H)]
    placed = [[False] * W for _ in range(H)]
    for ch_idx, thr, char, _label in _ASCII_CHANNEL_LAYERS:
        if ch_idx >= C:
            continue
        layer = grid_t[..., ch_idx]
        for r in range(H):
            for c in range(W):
                if not placed[r][c] and float(layer[r, c]) >= thr:
                    ascii_grid[r][c] = char
                    placed[r][c] = True
    return "\n".join("".join(row) for row in ascii_grid)


def _grid_ascii_legend() -> str:
    return (
        "Legend: @ agent | + door | * task_object | S stele | A altar | "
        "? cue | # wall | - corridor | . floor | ' ' empty"
    )


# =============================================================================
# 3. 출력 헬퍼
# =============================================================================

def _print_metadata(out: io.StringIO, bundle: EpisodeBundle) -> None:
    """episode metadata 섹션."""
    e = bundle.entry
    m = bundle.meta or {}
    arrs = bundle.arrays
    actual_T = int(arrs.get("rewards", np.zeros(0)).shape[0])
    obs_shape = list(arrs["observations_local_grid"].shape) if "observations_local_grid" in arrs else None
    out.write("=" * 78 + "\n")
    out.write("# Episode metadata\n")
    out.write("=" * 78 + "\n")
    out.write(f"npz_path:               {bundle.npz_path}\n")
    if bundle.meta_path:
        out.write(f"meta_path:              {bundle.meta_path}\n")
    out.write(f"split:                  {e.split}\n")
    out.write(f"episode_id:             {e.episode_id}\n")
    out.write(f"is_ood:                 {e.is_ood}\n")
    out.write(f"ood_type:               {e.ood_type}\n")
    out.write(f"env_seed:               {e.env_seed}\n")
    out.write(f"action_seed:            {m.get('action_seed', '<n/a>')}\n")
    out.write(f"behavior_policy:        {m.get('behavior_policy', '<n/a>')}\n")
    out.write(f"permutation_id:         {e.permutation_id}\n")
    out.write(f"forced_permutation:     {e.forced_permutation}\n")
    out.write(f"permutation (room→task): {m.get('permutation', '<n/a>')}\n")
    out.write(f"local_obs_size:         {obs_shape[1] if obs_shape else '?'} (full local_grid shape={obs_shape})\n")
    out.write(f"obs_scalar_dim:         {m.get('obs_scalar_dim', '<n/a>')}\n")
    out.write(f"max_steps (recorded):   {m.get('episode_length', actual_T)}\n")
    out.write(f"actual_length:          {actual_T}\n")
    out.write(f"num_invisible_fields:   {e.num_invisible_fields}\n")
    rg = m.get("initial_regime", {})
    out.write(f"initial_regime:         {rg}\n")
    if e.ood_type == "obs_shift":
        out.write(
            f"NOTE: obs_shift episode - channel permutation {m.get('obs_channel_perm')}\n"
            f"      ASCII rendering may LOOK wrong because channel mapping differs from train.\n"
        )
    if e.ood_type == "field_placement":
        out.write(
            f"NOTE: field_placement episode - invisible field source moved to room centers.\n"
        )
    if m.get("rg4f_kwargs_override"):
        out.write(f"rg4f_kwargs_override:   {m['rg4f_kwargs_override']}\n")


def _print_transition_summary(out: io.StringIO, bundle: EpisodeBundle) -> None:
    """transition summary 섹션 (T 전체에 대한 통계)."""
    arrs = bundle.arrays
    out.write("\n" + "=" * 78 + "\n")
    out.write("# Transition summary\n")
    out.write("=" * 78 + "\n")
    T = int(arrs["rewards"].shape[0])
    total_reward = float(arrs["rewards"].sum())
    done_T = int(np.argmax(arrs["dones"])) if bool(arrs["dones"].any()) else -1
    trunc_T = int(np.argmax(arrs["truncateds"])) if bool(arrs["truncateds"].any()) else -1
    completed_max = int(arrs["completed_tasks"].max()) if T > 0 else 0
    fail_max = int(arrs["failure_count"].max()) if T > 0 else 0
    out.write(f"T (steps):              {T}\n")
    out.write(f"total_reward:           {total_reward:.3f}\n")
    out.write(f"reached terminated@:    {done_T}\n")
    out.write(f"reached truncated@:     {trunc_T}\n")
    out.write(f"max completed_tasks:    {completed_max} / 4\n")
    out.write(f"max failure_count:      {fail_max}\n")
    out.write(f"sum tick_cost:          {float(arrs['tick_cost'].sum()):.3f}\n")
    out.write(f"sum latency_cost:       {float(arrs['latency_cost'].sum()):.3f}\n")
    out.write(f"sum failure_cost:       {float(arrs['failure_cost'].sum()):.3f}\n")
    out.write(f"sum reset_cost:         {float(arrs['reset_cost'].sum()):.3f}\n")
    out.write(f"sum task_reward:        {float(arrs['task_reward'].sum()):.3f}\n")
    out.write(f"sum completion_reward:  {float(arrs['completion_reward'].sum()):.3f}\n")
    out.write(f"change_point count:     {int(arrs['change_point'].sum())}\n")
    out.write(f"reveal_event count:     {int(arrs['reveal_event'].sum())}\n")
    out.write(f"shift_event count:      {int(arrs['shift_event'].sum())}\n")

    # task_id 분포
    tasks_unique, tasks_cnt = np.unique(arrs["task_id"], return_counts=True)
    out.write("task_id distribution:   ")
    parts = []
    for v, c in zip(tasks_unique.tolist(), tasks_cnt.tolist()):
        v = int(v)
        name = "<none>" if v == -1 else _safe_name(_TASK_NAMES, v, "Task ")
        parts.append(f"{name}={c}")
    out.write(", ".join(parts) + "\n")

    # room_id 분포
    rooms_unique, rooms_cnt = np.unique(arrs["room_id"], return_counts=True)
    out.write("room_id distribution:   ")
    parts = []
    for v, c in zip(rooms_unique.tolist(), rooms_cnt.tolist()):
        parts.append(f"{_safe_name(_ROOM_NAMES, int(v))}={c}")
    out.write(", ".join(parts) + "\n")

    # action_raw / action_effective 분포
    for key in ("actions_raw", "actions_effective"):
        u, cnt = np.unique(arrs[key], return_counts=True)
        out.write(f"{key:24s}")
        parts = []
        # top 8만
        order = np.argsort(-cnt)[:8]
        for i in order:
            parts.append(f"{_safe_name(_ACTION_NAMES, int(u[i]))}={int(cnt[i])}")
        out.write(", ".join(parts) + "\n")

    # event_token 분포 (top 6)
    u, cnt = np.unique(arrs["event_token"], return_counts=True)
    out.write("event_token (top 6):    ")
    order = np.argsort(-cnt)[:6]
    parts = [
        f"{_safe_name(_EVENT_NAMES, int(u[i]))}={int(cnt[i])}" for i in order
    ]
    out.write(", ".join(parts) + "\n")

    # reveal_or_shift 분포
    u, cnt = np.unique(arrs["reveal_or_shift"], return_counts=True)
    out.write("reveal_or_shift dist:   ")
    parts = []
    for v, c in zip(u.tolist(), cnt.tolist()):
        parts.append(f"{_safe_name(_REVEAL_SHIFT_NAMES, int(v))}={int(c)}")
    out.write(", ".join(parts) + "\n")


def _print_step_level(
    out: io.StringIO,
    bundle: EpisodeBundle,
    start: int,
    num: int,
    show_scalar: bool,
    show_info: bool,
    show_grid: bool,
) -> None:
    """지정 step range의 step-level inspection."""
    arrs = bundle.arrays
    T = int(arrs["rewards"].shape[0])
    end = min(T, start + num)
    out.write("\n" + "=" * 78 + "\n")
    out.write(f"# Step-level inspection: t in [{start}, {end})\n")
    out.write("=" * 78 + "\n")

    if show_grid:
        out.write(_grid_ascii_legend() + "\n")

    for t in range(start, end):
        ra = int(arrs["actions_raw"][t])
        ea = int(arrs["actions_effective"][t])
        rew = float(arrs["rewards"][t])
        done = bool(arrs["dones"][t])
        trunc = bool(arrs["truncateds"][t])
        tid = int(arrs["task_id"][t])
        rid = int(arrs["room_id"][t])
        pos = arrs["agent_position"][t].tolist()
        cp = bool(arrs["change_point"][t])
        re_e = bool(arrs["reveal_event"][t])
        sh_e = bool(arrs["shift_event"][t])
        rs = int(arrs["reveal_or_shift"][t])
        ev = int(arrs["event_token"][t])
        cm = int(arrs["true_regime_control_mode"][t])
        out.write("-" * 78 + "\n")
        out.write(f"t={t:4d}  raw={_safe_name(_ACTION_NAMES, ra):8s} eff={_safe_name(_ACTION_NAMES, ea):8s}  ")
        out.write(f"reward={rew:+.3f}  done={done} trunc={trunc}\n")
        out.write(
            f"        task={ ('<none>' if tid<0 else _safe_name(_TASK_NAMES, tid, 'Task ') ) }  "
            f"room={_safe_name(_ROOM_NAMES, rid)}  pos=({pos[0]},{pos[1]})  "
            f"event={_safe_name(_EVENT_NAMES, ev)}\n"
        )
        out.write(
            f"        change_point={cp}  reveal={re_e}  shift={sh_e}  "
            f"reveal_or_shift={_safe_name(_REVEAL_SHIFT_NAMES, rs)}  "
            f"control_mode={_safe_name(_CONTROL_NAMES, cm)}\n"
        )
        if show_scalar:
            ts = arrs["true_state"][t]
            scalar = arrs["observations_scalar"][t]
            out.write(
                f"        true_state: vision={ts[0]:+.3f} mobility={ts[1]:+.3f} "
                f"interaction={ts[2]:+.3f} noise={ts[3]:+.3f} control_drift={ts[4]:+.3f}\n"
            )
            out.write(
                f"        scalar(14): " + " ".join(f"{x:+.2f}" for x in scalar.tolist()) + "\n"
            )
        if show_info:
            tba = bool(arrs["target_band_active"][t])
            tbsd = int(arrs["target_band_state_dim"][t])
            tbc = float(arrs["target_band_center"][t])
            tbhw = float(arrs["target_band_half_width"][t])
            tbk = int(arrs["target_band_kind"][t])
            sd_name = _safe_name(_STATE_DIM_NAMES, tbsd) if tbsd >= 0 else "<none>"
            kind_name = _safe_name(_TARGET_BAND_KIND_NAMES, tbk)
            out.write(
                f"        target_band: active={tba} dim={sd_name} center={tbc:+.3f} "
                f"half_width={tbhw:.3f} kind={kind_name}\n"
            )
            cost = (
                float(arrs["tick_cost"][t]),
                float(arrs["latency_cost"][t]),
                float(arrs["failure_cost"][t]),
                float(arrs["reset_cost"][t]),
            )
            rew_decomp = (
                float(arrs["task_reward"][t]),
                float(arrs["completion_reward"][t]),
            )
            out.write(
                f"        cost: tick={cost[0]:.2f} latency={cost[1]:.2f} "
                f"failure={cost[2]:.2f} reset={cost[3]:.2f} | "
                f"task_reward={rew_decomp[0]:+.2f} completion={rew_decomp[1]:+.2f}\n"
            )
            out.write(
                f"        completed={int(arrs['completed_tasks'][t])} "
                f"failure_count={int(arrs['failure_count'][t])} "
                f"miscontrol_p={float(arrs['true_regime_miscontrol_p'][t]):.3f} "
                f"periodic_slip={bool(arrs['true_regime_periodic_slip'][t])}\n"
            )
            # field dynamic
            mu = arrs["field_info_mu"][t].tolist()
            sigma = arrs["field_info_sigma"][t].tolist()
            if mu:
                out.write(f"        field mu:    " + " ".join(f"{x:+.3f}" for x in mu) + "\n")
                out.write(f"        field sigma: " + " ".join(f"{x:+.3f}" for x in sigma) + "\n")
        if show_grid:
            grid = arrs["observations_local_grid"][t]
            ascii_text = _local_grid_to_ascii(grid)
            for line in ascii_text.split("\n"):
                out.write(f"        | {line}\n")


def _print_field_task(
    out: io.StringIO,
    bundle: EpisodeBundle,
    show_fields: bool,
    show_task: bool,
) -> None:
    """field/task debug 섹션."""
    if not (show_fields or show_task):
        return
    out.write("\n" + "=" * 78 + "\n")
    out.write("# Field / Task debug\n")
    out.write("=" * 78 + "\n")
    m = bundle.meta or {}
    if show_fields:
        fields = m.get("field_info_static", []) or []
        out.write(f"## Invisible fields ({len(fields)})\n")
        if not fields:
            out.write("  (no invisible fields recorded)\n")
        for i, f in enumerate(fields):
            family = int(f.get("family", -1))
            family_name = _safe_name(_FIELD_FAMILY_NAMES, family)
            cs = [int(x) for x in (f.get("coupled_states") or [])]
            cs_names = [_safe_name(_STATE_DIM_NAMES, x) for x in cs]
            out.write(
                f"  [{i}] family={family_name}({family})  "
                f"source=({f.get('source_row')}, {f.get('source_col')})  "
                f"radius={float(f.get('radius', 0.0)):.2f}  "
                f"sigma_init={float(f.get('sigma_init', 0.0)):.3f}\n"
            )
            out.write(
                f"      coupled_states={cs_names} (|·|={len(cs)})  "
                f"sparse={'OK' if len(cs) <= 2 else 'VIOLATED'}\n"
            )
        # 동적 mu/sigma 마지막 step
        arrs = bundle.arrays
        if "field_info_mu" in arrs and arrs["field_info_mu"].shape[1] > 0:
            last_mu = arrs["field_info_mu"][-1].tolist()
            last_sigma = arrs["field_info_sigma"][-1].tolist()
            out.write(f"  last-step mu:    " + " ".join(f"{x:+.3f}" for x in last_mu) + "\n")
            out.write(f"  last-step sigma: " + " ".join(f"{x:+.3f}" for x in last_sigma) + "\n")

    if show_task:
        out.write("## Tasks (per-room assignment)\n")
        perm = m.get("permutation", {}) or {}
        # permutation: dict[room_id, task_id]
        for room_id_str in sorted(perm.keys(), key=lambda x: int(x)):
            rid = int(room_id_str)
            tid = int(perm[room_id_str])
            out.write(
                f"  room {rid} ({_safe_name(_ROOM_NAMES, rid)}) "
                f"-> task {tid} ({_safe_name(_TASK_NAMES, tid, 'Task ')})\n"
            )
        # target band 활성 step 수 / 첫 활성 step / 분포
        arrs = bundle.arrays
        tba = arrs.get("target_band_active")
        if tba is not None and tba.size > 0:
            active_steps = int(tba.sum())
            out.write(f"  target_band active steps: {active_steps} / {int(tba.shape[0])}\n")
            # 활성 step에서의 중심값 분포
            if active_steps:
                centers = arrs["target_band_center"][tba]
                halfw = arrs["target_band_half_width"][tba]
                out.write(
                    f"    center min/mean/max: {centers.min():+.3f} {centers.mean():+.3f} {centers.max():+.3f}\n"
                )
                out.write(
                    f"    half_width min/mean/max: {halfw.min():.3f} {halfw.mean():.3f} {halfw.max():.3f}\n"
                )
        # task_id 별 진입 step 수
        tid_arr = arrs.get("task_id")
        if tid_arr is not None:
            for t_idx in (0, 1, 2, 3):
                cnt = int((tid_arr == t_idx).sum())
                out.write(
                    f"  steps in {_safe_name(_TASK_NAMES, t_idx, 'Task ')}: {cnt}\n"
                )


# =============================================================================
# 4. 메인 entry
# =============================================================================

def _resolve_target(args: argparse.Namespace) -> EpisodeBundle:
    """CLI 인자에서 EpisodeBundle을 만든다.

    case A: --episode-path (+ --meta-path 선택). index 우회.
    case B: --root + --split + --index.
    """
    if args.episode_path is not None:
        npz = Path(args.episode_path).resolve()
        if not npz.is_file():
            raise FileNotFoundError(f"npz not found: {npz}")
        meta_path = Path(args.meta_path).resolve() if args.meta_path else None
        # IndexEntry 가짜 만들기 (root는 npz의 parent.parent.parent로 두고 npz_path는 상대)
        # 간단히 root=npz.parent로 두고 npz_path=npz.name
        synthetic_root = npz.parent
        entry = IndexEntry(
            episode_id=npz.stem,
            split=npz.parent.parent.name if npz.parent.parent else "<unknown>",
            is_ood=False,
            ood_type=None,
            npz_path=npz.name,
            meta_path=meta_path.name if meta_path is not None else None,
            episode_length=0,
            permutation_id=-1,
            forced_permutation=[],
            env_seed=0,
            num_invisible_fields=0,
            raw={},
        )
        bundle = load_episode(synthetic_root, entry, load_meta=meta_path is not None)
        # meta가 None인데 명시 경로가 있으면 직접 read
        if meta_path is not None and bundle.meta is None and meta_path.is_file():
            with meta_path.open("r", encoding="utf-8") as fp:
                bundle.meta = json.load(fp)  # type: ignore[assignment]
        return bundle

    root = Path(args.root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"root not found: {root}")
    split_dir = root / args.split
    entries = load_index(split_dir)
    if not entries:
        raise FileNotFoundError(f"no episodes in {split_dir}/index.jsonl")
    if not (0 <= args.index < len(entries)):
        raise IndexError(f"--index {args.index} out of range [0, {len(entries)})")
    return load_episode(root, entries[args.index], load_meta=True)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="RG-4F episode inspector (Session 4)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--root", type=str, default="data/rg4f", help="dataset output_root")
    p.add_argument("--split", type=str, default="train", help="split name (train/valid/...)")
    p.add_argument("--index", type=int, default=0, help="episode index in index.jsonl")
    p.add_argument("--episode-path", type=str, default=None, help="direct npz path (overrides --root/--split/--index)")
    p.add_argument("--meta-path", type=str, default=None, help="direct meta.json path (used with --episode-path)")
    p.add_argument("--step", type=int, default=0, help="start step for step-level view")
    p.add_argument("--num-steps", type=int, default=10, help="how many steps to print from --step")
    p.add_argument("--show-grid", action="store_true", help="print local_grid as ASCII per step")
    p.add_argument("--show-scalar", action="store_true", help="print scalar / true_state per step")
    p.add_argument("--show-info", action="store_true", help="print target_band / cost / regime per step")
    p.add_argument("--show-fields", action="store_true", help="print invisible field static / last-step dynamics")
    p.add_argument("--show-task", action="store_true", help="print room→task assignment + target band stats")
    p.add_argument("--save-ascii", type=str, default=None, help="write the entire output to this file")
    return p.parse_args()


def main() -> int:
    # Windows의 cp949 등 비-UTF8 콘솔 인코딩에서 → 같은 유니코드 문자가 출력될 때
    # UnicodeEncodeError가 나는 것을 방지한다. 출력 내용 자체는 변하지 않는다.
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    args = _parse_args()
    try:
        bundle = _resolve_target(args)
    except Exception as exc:
        print(f"[ERROR] failed to load episode: {exc}", file=sys.stderr)
        return 2

    out = io.StringIO()
    _print_metadata(out, bundle)
    _print_transition_summary(out, bundle)
    _print_step_level(
        out=out,
        bundle=bundle,
        start=int(args.step),
        num=int(args.num_steps),
        show_scalar=args.show_scalar,
        show_info=args.show_info,
        show_grid=args.show_grid,
    )
    _print_field_task(
        out=out,
        bundle=bundle,
        show_fields=args.show_fields,
        show_task=args.show_task,
    )

    text = out.getvalue()
    print(text)
    if args.save_ascii:
        save_path = Path(args.save_ascii).resolve()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(text, encoding="utf-8")
        print(f"saved -> {save_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
