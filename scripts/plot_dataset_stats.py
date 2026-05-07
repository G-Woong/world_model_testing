"""RG-4F dataset 통계 요약 (Session 4 선택 구현).

split별 episode length / reward / action / change_point / task_id 분포를 CSV로
저장하고, matplotlib가 사용 가능하면 PNG histogram도 같이 저장한다.

PART0 §3 / SESSION3_HANDOFF §9 정합:
- model / planner / agent 코드 0줄.
- 본 script는 단순 통계 집계 도구 (논문 figure 생성기 아님).
- seaborn 사용 금지 (사용자 요구사항 §4).
- 장시간 실행 금지: split별로 모든 npz를 lazy하게 streaming해도 dataset이 커지면
  실행 시간이 늘어날 수 있으므로 ``--max-episodes-per-split`` 옵션을 둔다.

사용법
------
    python scripts/plot_dataset_stats.py --root data/rg4f --out outputs/dataset_stats
    python scripts/plot_dataset_stats.py --root data/rg4f --out outputs/dataset_stats \\
        --max-episodes-per-split 50 --no-plots   # CSV만
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from falsifiable_regime_world_model.rg4f.dataset_io import (
    iter_episodes,
    load_manifest,
    split_dirs,
)


# matplotlib는 requirements.txt에 있으므로 import는 가능하지만 헤드리스 안전 보장
try:
    import matplotlib
    matplotlib.use("Agg")  # 서버 / no-display 환경에서도 동작
    import matplotlib.pyplot as plt  # noqa: E402
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False


# =============================================================================
# Action / Event / Task constants
# =============================================================================

_ACTION_E: int = 4   # types.Action.E (interact)
_EVENT_ROOM_ENTRY: int = 1  # types.EventToken.ROOM_ENTRY
_EVENT_TASK_COMPLETE: int = 12  # types.EventToken.TASK_COMPLETE
_NUM_TASKS: int = 4
# state dim → near_success 평가 시 사용. 0=vision, 1=mobility, 2=interaction, 3=noise, 4=control_drift.


def _per_episode_task_completion(
    arrs: Dict[str, np.ndarray],
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    """한 episode의 per-task completion / first_complete_tick / room_entry / interaction
    / near_success를 계산한다.

    Returns
    -------
    dict with keys:
      per_task_done : List[bool] length 4 (task_id 0..3 = A/B/C/D)
      first_complete_tick : List[int] length 4 (-1 if not completed)
      all_done : bool
      completed_count_final : int
      done_at_end : bool                  (last step의 dones=True)
      truncated_at_end : bool             (last step의 truncateds=True)
      room_entry_count : List[int] length 4
      interaction_count : List[int] length 4
      near_success_count : List[int] length 4

    Definitions
    -----------
    - per_task_done[X]: completed_tasks가 증가한 step에서 그 step의 room_id가 X-task가
      배정된 room이면 task X가 완료된 것으로 본다. permutation은 episode_meta에 저장.
    - room_entry_count[X]: event_token=ROOM_ENTRY인 step에서 task_id==X인 step 수.
    - interaction_count[X]: actions_effective=E이고 task_id==X인 step 수.
    - near_success_count[X]: target_band_active=True이고 task_id==X이며,
      true_state[state_dim] - center 의 절대값이 2 * half_width 이내인 step 수.
      이 정의는 학습용 supervision의 boundary metric (정확한 success는 env가 결정).
    """
    T = int(arrs["rewards"].shape[0])
    per_task_done = [False] * _NUM_TASKS
    first_tick = [-1] * _NUM_TASKS
    room_entry_count = [0] * _NUM_TASKS
    interaction_count = [0] * _NUM_TASKS
    near_success_count = [0] * _NUM_TASKS

    if T == 0:
        return {
            "per_task_done": per_task_done,
            "first_complete_tick": first_tick,
            "all_done": False,
            "completed_count_final": 0,
            "done_at_end": False,
            "truncated_at_end": False,
            "room_entry_count": room_entry_count,
            "interaction_count": interaction_count,
            "near_success_count": near_success_count,
        }

    completed = arrs["completed_tasks"].astype(np.int64)
    room_id = arrs["room_id"].astype(np.int64)
    task_id = arrs["task_id"].astype(np.int64)
    event_token = arrs["event_token"].astype(np.int64)
    actions_eff = arrs["actions_effective"].astype(np.int64)
    dones = arrs["dones"].astype(bool)
    truncateds = arrs["truncateds"].astype(bool)

    # permutation: {RoomID_int: TaskID_int}; episode_meta.permutation. key가 str로 dump된 경우 처리.
    perm_raw = meta.get("permutation") or {}
    perm: Dict[int, int] = {int(k): int(v) for k, v in perm_raw.items()}

    # completion 증가 step 추적 → 그 step의 room_id로 어느 task가 완료됐는지 추론
    diff = np.diff(np.concatenate(([0], completed)))   # length T
    inc_steps = np.where(diff > 0)[0]
    for s in inc_steps.tolist():
        # 같은 step에 여러 task가 동시에 완료되는 경우는 거의 없지만, 안전하게 multi-step도 처리.
        n_increments = int(diff[s])
        # 어느 task가 완료됐는지 결정: 우선 (a) event_token == TASK_COMPLETE인 step의 room
        # (b) 그 외엔 같은 step의 room_id → permutation 매핑.
        room = int(room_id[s])
        if room not in perm:
            continue
        tid = int(perm[room])
        if 0 <= tid < _NUM_TASKS and not per_task_done[tid]:
            per_task_done[tid] = True
            first_tick[tid] = int(s)
        # n_increments가 1보다 크더라도 한 step에서 같은 room의 다른 task가 동시에
        # 완료될 수는 없으므로 (방-task 1:1) 위 처리로 충분.
        del n_increments

    # room_entry_count / interaction_count: tick 단위 누적
    room_entry_mask = (event_token == _EVENT_ROOM_ENTRY)
    interaction_mask = (actions_eff == _ACTION_E)
    for tid in range(_NUM_TASKS):
        match_task = (task_id == tid)
        room_entry_count[tid] = int(np.sum(room_entry_mask & match_task))
        interaction_count[tid] = int(np.sum(interaction_mask & match_task))

    # near_success_count: target_band가 active인 step에서 |state - center| <= 2 * half_width
    if "target_band_active" in arrs and "true_state" in arrs:
        active = arrs["target_band_active"].astype(bool)
        sd = arrs["target_band_state_dim"].astype(np.int64)
        center = arrs["target_band_center"].astype(np.float64)
        half_w = arrs["target_band_half_width"].astype(np.float64)
        ts = arrs["true_state"].astype(np.float64)  # (T, 5)
        # state_dim이 -1이면 inactive에 해당. 안전 마스크.
        valid_dim = (sd >= 0) & (sd < ts.shape[1])
        for tid in range(_NUM_TASKS):
            match_task = (task_id == tid)
            mask = active & valid_dim & match_task
            if not np.any(mask):
                continue
            idx = np.where(mask)[0]
            for i in idx.tolist():
                d = int(sd[i])
                if abs(float(ts[i, d]) - float(center[i])) <= 2.0 * float(half_w[i]):
                    near_success_count[tid] += 1

    completed_count_final = int(completed[-1])
    done_at_end = bool(dones[-1])
    truncated_at_end = bool(truncateds[-1])
    all_done = bool(completed_count_final >= _NUM_TASKS)
    # raw vs effective action mismatch (control-drift remap + miscontrol slip 효과)
    actions_raw = arrs["actions_raw"].astype(np.int64)
    raw_eff_mismatch = int(np.sum(actions_raw != actions_eff))

    return {
        "per_task_done": per_task_done,
        "first_complete_tick": first_tick,
        "all_done": all_done,
        "completed_count_final": completed_count_final,
        "done_at_end": done_at_end,
        "truncated_at_end": truncated_at_end,
        "room_entry_count": room_entry_count,
        "interaction_count": interaction_count,
        "near_success_count": near_success_count,
        "raw_eff_mismatch": raw_eff_mismatch,
    }


def _aggregate_split(
    root: Path,
    split: str,
    max_eps: Optional[int],
) -> Dict[str, Any]:
    """한 split의 통계를 집계하여 dict로 반환."""
    lengths: List[int] = []
    rewards_total: List[float] = []
    rewards_step_mean: List[float] = []
    change_point_counts: List[int] = []
    reveal_counts: List[int] = []
    shift_counts: List[int] = []
    completed_max: List[int] = []
    fail_max: List[int] = []
    action_raw_counter: Counter = Counter()
    action_eff_counter: Counter = Counter()
    task_id_counter: Counter = Counter()
    room_id_counter: Counter = Counter()
    event_token_counter: Counter = Counter()
    local_size_counter: Counter = Counter()
    num_fields_counter: Counter = Counter()
    family_counter: Counter = Counter()
    relocate_field_counts = 0
    obs_perm_counts = 0
    n_episodes = 0

    # per-task aggregation
    per_task_done_count = [0] * _NUM_TASKS
    first_tick_sum = [0.0] * _NUM_TASKS   # only over episodes that completed
    first_tick_n = [0] * _NUM_TASKS
    completed_count_final_sum = 0
    all_done_count = 0
    done_count = 0
    truncated_count = 0
    room_entry_total = [0] * _NUM_TASKS
    interaction_total = [0] * _NUM_TASKS
    near_success_total = [0] * _NUM_TASKS
    raw_eff_mismatch_total = 0
    # v5: collector_metadata aggregation
    collector_mode_counter: Counter = Counter()
    task_order_counter: Counter = Counter()
    task_attempt_ticks_sum = [0, 0, 0, 0]
    task_timeout_sum = [0, 0, 0, 0]
    task_retry_sum = [0, 0, 0, 0]
    n_with_collector_meta = 0

    for bundle in iter_episodes(root, split, max_episodes=max_eps):
        n_episodes += 1
        arrs = bundle.arrays
        meta = bundle.meta or {}
        T = int(arrs["rewards"].shape[0])
        lengths.append(T)
        rewards_total.append(float(arrs["rewards"].sum()))
        rewards_step_mean.append(float(arrs["rewards"].mean()) if T else 0.0)
        change_point_counts.append(int(arrs["change_point"].sum()))
        reveal_counts.append(int(arrs["reveal_event"].sum()))
        shift_counts.append(int(arrs["shift_event"].sum()))
        completed_max.append(int(arrs["completed_tasks"].max()) if T else 0)
        fail_max.append(int(arrs["failure_count"].max()) if T else 0)
        for v in arrs["actions_raw"].tolist():
            action_raw_counter[int(v)] += 1
        for v in arrs["actions_effective"].tolist():
            action_eff_counter[int(v)] += 1
        for v in arrs["task_id"].tolist():
            task_id_counter[int(v)] += 1
        for v in arrs["room_id"].tolist():
            room_id_counter[int(v)] += 1
        for v in arrs["event_token"].tolist():
            event_token_counter[int(v)] += 1
        local_size = int(arrs["observations_local_grid"].shape[1])
        local_size_counter[local_size] += 1
        nf = int(arrs["field_info_mu"].shape[1])
        num_fields_counter[nf] += 1
        for f in meta.get("field_info_static", []) or []:
            family_counter[int(f.get("family", -1))] += 1
        if bool(meta.get("relocate_fields_room_center", False)):
            relocate_field_counts += 1
        if meta.get("obs_channel_perm") is not None:
            obs_perm_counts += 1

        # per-task metrics
        per_task = _per_episode_task_completion(arrs, meta)
        for tid in range(_NUM_TASKS):
            if per_task["per_task_done"][tid]:
                per_task_done_count[tid] += 1
                if per_task["first_complete_tick"][tid] >= 0:
                    first_tick_sum[tid] += float(per_task["first_complete_tick"][tid])
                    first_tick_n[tid] += 1
            room_entry_total[tid] += int(per_task["room_entry_count"][tid])
            interaction_total[tid] += int(per_task["interaction_count"][tid])
            near_success_total[tid] += int(per_task["near_success_count"][tid])
        completed_count_final_sum += int(per_task["completed_count_final"])
        if per_task["all_done"]:
            all_done_count += 1
        if per_task["done_at_end"]:
            done_count += 1
        if per_task["truncated_at_end"]:
            truncated_count += 1
        raw_eff_mismatch_total += int(per_task.get("raw_eff_mismatch", 0))
        # v5: collector_metadata aggregation
        cm = meta.get("collector_metadata") or {}
        if cm:
            n_with_collector_meta += 1
            collector_mode_counter[str(cm.get("collector_mode", "unknown"))] += 1
            task_order_counter[str(cm.get("task_order_str", "?"))] += 1
            attempt = cm.get("task_attempt_ticks") or {}
            timeout = cm.get("task_timeout") or {}
            retry = cm.get("task_retry_count") or {}
            for tid, name in enumerate(("A", "B", "C", "D")):
                task_attempt_ticks_sum[tid] += int(attempt.get(name, 0) or 0)
                task_timeout_sum[tid] += int(timeout.get(name, 0) or 0)
                task_retry_sum[tid] += int(retry.get(name, 0) or 0)

    return {
        "split": split,
        "n_episodes": n_episodes,
        "lengths": lengths,
        "rewards_total": rewards_total,
        "rewards_step_mean": rewards_step_mean,
        "change_point_counts": change_point_counts,
        "reveal_counts": reveal_counts,
        "shift_counts": shift_counts,
        "completed_max": completed_max,
        "fail_max": fail_max,
        "action_raw_counter": dict(action_raw_counter),
        "action_eff_counter": dict(action_eff_counter),
        "task_id_counter": dict(task_id_counter),
        "room_id_counter": dict(room_id_counter),
        "event_token_counter": dict(event_token_counter),
        "local_size_counter": dict(local_size_counter),
        "num_fields_counter": dict(num_fields_counter),
        "family_counter": dict(family_counter),
        "relocate_field_counts": relocate_field_counts,
        "obs_perm_counts": obs_perm_counts,
        # per-task aggregation results
        "per_task_done_count": per_task_done_count,
        "first_tick_sum": first_tick_sum,
        "first_tick_n": first_tick_n,
        "completed_count_final_sum": completed_count_final_sum,
        "all_done_count": all_done_count,
        "done_count": done_count,
        "truncated_count": truncated_count,
        "room_entry_total": room_entry_total,
        "interaction_total": interaction_total,
        "near_success_total": near_success_total,
        "raw_eff_mismatch_total": raw_eff_mismatch_total,
        # v5: collector aggregation
        "collector_mode_counter": dict(collector_mode_counter),
        "task_order_counter": dict(task_order_counter),
        "task_attempt_ticks_sum": task_attempt_ticks_sum,
        "task_timeout_sum": task_timeout_sum,
        "task_retry_sum": task_retry_sum,
        "n_with_collector_meta": n_with_collector_meta,
    }


def _write_summary_csv(out_dir: Path, agg_per_split: List[Dict[str, Any]]) -> Path:
    """split별 요약 통계를 1행씩 CSV로 저장. (기존 컬럼 + per-task aggregation 컬럼)"""
    csv_path = out_dir / "summary.csv"
    fields = [
        "split", "n_episodes",
        "len_min", "len_mean", "len_max",
        "reward_total_mean", "reward_total_std",
        "change_point_mean", "reveal_mean", "shift_mean",
        "completed_max_mean", "fail_max_mean",
        "local_obs_size", "num_fields_mean",
        "relocate_field_count", "obs_perm_count",
        # per-task summary (Session-7 task_probe report용)
        "completed_count_final_mean",
        "all_tasks_completed_rate",
        "done_rate", "truncated_rate",
        "task_A_completed_rate", "task_B_completed_rate",
        "task_C_completed_rate", "task_D_completed_rate",
        "raw_eff_mismatch_count_mean",
        # v5
        "task_order_entropy",
        "most_common_task_order_ratio",
        "most_common_collector_mode_ratio",
        "task_A_attempt_ticks_mean", "task_B_attempt_ticks_mean",
        "task_C_attempt_ticks_mean", "task_D_attempt_ticks_mean",
        "task_A_timeout_rate", "task_B_timeout_rate",
        "task_C_timeout_rate", "task_D_timeout_rate",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp)
        w.writerow(fields)
        for a in agg_per_split:
            L = np.asarray(a["lengths"]) if a["lengths"] else np.zeros(1)
            R = np.asarray(a["rewards_total"]) if a["rewards_total"] else np.zeros(1)
            CP = np.asarray(a["change_point_counts"]) if a["change_point_counts"] else np.zeros(1)
            RV = np.asarray(a["reveal_counts"]) if a["reveal_counts"] else np.zeros(1)
            SF = np.asarray(a["shift_counts"]) if a["shift_counts"] else np.zeros(1)
            CM = np.asarray(a["completed_max"]) if a["completed_max"] else np.zeros(1)
            FM = np.asarray(a["fail_max"]) if a["fail_max"] else np.zeros(1)
            local_size_keys = list(a["local_size_counter"].keys())
            num_fields = a["num_fields_counter"]
            num_fields_mean = (
                sum(k * v for k, v in num_fields.items()) / max(1, sum(num_fields.values()))
            )
            n_eps = max(1, int(a["n_episodes"]))
            ccf_mean = float(a["completed_count_final_sum"]) / n_eps
            adone_rate = float(a["all_done_count"]) / n_eps
            done_rate = float(a["done_count"]) / n_eps
            trunc_rate = float(a["truncated_count"]) / n_eps
            ptd = a["per_task_done_count"]
            tabcd_rates = [float(ptd[i]) / n_eps for i in range(_NUM_TASKS)]
            w.writerow([
                a["split"], a["n_episodes"],
                int(L.min()), float(L.mean()), int(L.max()),
                float(R.mean()), float(R.std()),
                float(CP.mean()), float(RV.mean()), float(SF.mean()),
                float(CM.mean()), float(FM.mean()),
                local_size_keys[0] if len(local_size_keys) == 1 else "mixed:" + ",".join(map(str, local_size_keys)),
                f"{num_fields_mean:.2f}",
                a["relocate_field_counts"], a["obs_perm_counts"],
                f"{ccf_mean:.4f}",
                f"{adone_rate:.4f}",
                f"{done_rate:.4f}", f"{trunc_rate:.4f}",
                f"{tabcd_rates[0]:.4f}", f"{tabcd_rates[1]:.4f}",
                f"{tabcd_rates[2]:.4f}", f"{tabcd_rates[3]:.4f}",
                f"{float(a['raw_eff_mismatch_total']) / n_eps:.4f}",
                # v5: task_order entropy + most_common ratios
                _f4(_entropy_from_counter(a["task_order_counter"])),
                _f4(_most_common_ratio(a["task_order_counter"])),
                _f4(_most_common_ratio(a["collector_mode_counter"])),
                _f4(float(a["task_attempt_ticks_sum"][0]) / max(1, a["n_with_collector_meta"])),
                _f4(float(a["task_attempt_ticks_sum"][1]) / max(1, a["n_with_collector_meta"])),
                _f4(float(a["task_attempt_ticks_sum"][2]) / max(1, a["n_with_collector_meta"])),
                _f4(float(a["task_attempt_ticks_sum"][3]) / max(1, a["n_with_collector_meta"])),
                _f4(float(a["task_timeout_sum"][0]) / max(1, a["n_with_collector_meta"])),
                _f4(float(a["task_timeout_sum"][1]) / max(1, a["n_with_collector_meta"])),
                _f4(float(a["task_timeout_sum"][2]) / max(1, a["n_with_collector_meta"])),
                _f4(float(a["task_timeout_sum"][3]) / max(1, a["n_with_collector_meta"])),
            ])
    return csv_path


def _f4(x: float) -> str:
    """4-자리 소수점 안전 포맷."""
    try:
        return f"{float(x):.4f}"
    except Exception:
        return ""


def _entropy_from_counter(counter: Dict[Any, int]) -> float:
    """Shannon entropy (nat 기반은 아님, log2 기반 — 0이면 단일 모드, 큼=다양)."""
    if not counter:
        return 0.0
    total = float(sum(counter.values()))
    if total <= 0:
        return 0.0
    p = np.asarray([v / total for v in counter.values() if v > 0], dtype=np.float64)
    return float(-np.sum(p * np.log2(p)))


def _most_common_ratio(counter: Dict[Any, int]) -> float:
    """가장 자주 나오는 항목의 비율. 0이면 데이터 없음. 1이면 단일 mode 지배."""
    if not counter:
        return 0.0
    total = float(sum(counter.values()))
    if total <= 0:
        return 0.0
    return float(max(counter.values())) / total


def _write_collector_summary_csv(
    out_dir: Path, agg_per_split: List[Dict[str, Any]],
) -> Path:
    """v5 전용: split × collector_mode × task_order_str의 distribution + per-mode metrics."""
    csv_path = out_dir / "collector_summary.csv"
    fields = [
        "split", "category", "key", "count", "ratio",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp)
        w.writerow(fields)
        for a in agg_per_split:
            n = max(1, int(a["n_with_collector_meta"]))
            for k, v in sorted(a["collector_mode_counter"].items()):
                w.writerow([a["split"], "collector_mode", k, int(v), f"{float(v) / n:.4f}"])
            for k, v in sorted(a["task_order_counter"].items()):
                w.writerow([a["split"], "task_order_str", k, int(v), f"{float(v) / n:.4f}"])
    return csv_path


def _write_per_task_summary_csv(
    out_dir: Path, agg_per_split: List[Dict[str, Any]],
) -> Path:
    """split × Task A/B/C/D 격자형 per-task summary CSV.

    한 행 = (split, task) → completed_rate / first_complete_tick_mean / 
    room_entry_count_mean / interaction_count_mean / near_success_count_mean.
    """
    csv_path = out_dir / "per_task_summary.csv"
    task_names = ["A", "B", "C", "D"]
    fields = [
        "split", "task",
        "n_episodes",
        "completed_rate",
        "first_complete_tick_mean",
        "first_complete_tick_n",
        "room_entry_count_mean",
        "interaction_count_mean",
        "near_success_count_mean",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp)
        w.writerow(fields)
        for a in agg_per_split:
            n_eps = max(1, int(a["n_episodes"]))
            for tid in range(_NUM_TASKS):
                done_n = int(a["per_task_done_count"][tid])
                rate = float(done_n) / n_eps
                ft_n = int(a["first_tick_n"][tid])
                ft_mean = (
                    float(a["first_tick_sum"][tid]) / ft_n if ft_n > 0 else float("nan")
                )
                re_mean = float(a["room_entry_total"][tid]) / n_eps
                ia_mean = float(a["interaction_total"][tid]) / n_eps
                ns_mean = float(a["near_success_total"][tid]) / n_eps
                w.writerow([
                    a["split"], task_names[tid],
                    a["n_episodes"],
                    f"{rate:.4f}",
                    "" if np.isnan(ft_mean) else f"{ft_mean:.2f}",
                    ft_n,
                    f"{re_mean:.4f}",
                    f"{ia_mean:.4f}",
                    f"{ns_mean:.4f}",
                ])
    return csv_path


def _write_distribution_csv(out_dir: Path, agg: Dict[str, Any]) -> Path:
    """한 split의 action / event / task / room counter를 long-form CSV로 저장."""
    csv_path = out_dir / f"{agg['split']}_distributions.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp)
        w.writerow(["category", "key", "count"])
        for cat in (
            "action_raw_counter",
            "action_eff_counter",
            "task_id_counter",
            "room_id_counter",
            "event_token_counter",
            "num_fields_counter",
            "family_counter",
        ):
            for k, v in sorted(agg[cat].items(), key=lambda x: int(x[0])):
                w.writerow([cat, int(k), int(v)])
    return csv_path


def _maybe_plot(out_dir: Path, agg_per_split: List[Dict[str, Any]]) -> List[Path]:
    """matplotlib가 가능하면 split별 episode length histogram + reward histogram + change_point bar 저장.

    그래프 1개당 파일 1개. 모든 그래프는 작게/단순하게 (axis 라벨 + 제목 + grid).
    """
    if not _HAS_MPL:
        return []
    saved: List[Path] = []

    # 1) episode length histogram (모든 split overlay)
    fig, ax = plt.subplots(figsize=(8, 4))
    for a in agg_per_split:
        if not a["lengths"]:
            continue
        ax.hist(a["lengths"], bins=20, alpha=0.5, label=a["split"])
    ax.set_xlabel("episode length")
    ax.set_ylabel("count")
    ax.set_title("Episode length histogram")
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    p = out_dir / "episode_length_hist.png"
    fig.tight_layout()
    fig.savefig(p, dpi=120)
    plt.close(fig)
    saved.append(p)

    # 2) total reward histogram
    fig, ax = plt.subplots(figsize=(8, 4))
    for a in agg_per_split:
        if not a["rewards_total"]:
            continue
        ax.hist(a["rewards_total"], bins=20, alpha=0.5, label=a["split"])
    ax.set_xlabel("total reward")
    ax.set_ylabel("count")
    ax.set_title("Episode total reward histogram")
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    p = out_dir / "reward_total_hist.png"
    fig.tight_layout()
    fig.savefig(p, dpi=120)
    plt.close(fig)
    saved.append(p)

    # 3) change_point count per split (boxplot)
    fig, ax = plt.subplots(figsize=(8, 4))
    data = [a["change_point_counts"] for a in agg_per_split if a["change_point_counts"]]
    labels = [a["split"] for a in agg_per_split if a["change_point_counts"]]
    if data:
        # matplotlib 3.9+에서 labels → tick_labels 이름이 바뀜. 호환성 위해 try/except.
        try:
            ax.boxplot(data, tick_labels=labels, showmeans=True)
        except TypeError:
            ax.boxplot(data, labels=labels, showmeans=True)
        ax.set_ylabel("change_point count per episode")
        ax.set_title("Change-point count per split")
        ax.grid(True, alpha=0.3)
        for tick in ax.get_xticklabels():
            tick.set_rotation(20)
            tick.set_fontsize(7)
        p = out_dir / "change_point_boxplot.png"
        fig.tight_layout()
        fig.savefig(p, dpi=120)
        plt.close(fig)
        saved.append(p)

    return saved


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="RG-4F dataset stats (Session 4)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--root", type=str, default="data/rg4f", help="dataset output_root")
    p.add_argument("--out", type=str, default="outputs/dataset_stats", help="output directory")
    p.add_argument("--max-episodes-per-split", type=int, default=200, help="0 = all")
    p.add_argument("--no-plots", action="store_true", help="skip matplotlib plots even if available")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"[ERROR] root not found: {root}", file=sys.stderr)
        return 2
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        load_manifest(root)
    except Exception as exc:
        print(f"[WARN] manifest.json not loadable ({exc!r}); continuing with split scan", file=sys.stderr)

    splits_found = [s for s, _ in split_dirs(root)]
    print(f"splits found: {splits_found}")
    max_eps = args.max_episodes_per_split if args.max_episodes_per_split > 0 else None

    aggs: List[Dict[str, Any]] = []
    for s in splits_found:
        print(f"=> aggregating {s}")
        a = _aggregate_split(root, s, max_eps)
        aggs.append(a)
        _write_distribution_csv(out_dir, a)
    summary_csv = _write_summary_csv(out_dir, aggs)
    print(f"summary csv -> {summary_csv}")
    per_task_csv = _write_per_task_summary_csv(out_dir, aggs)
    print(f"per-task summary csv -> {per_task_csv}")
    collector_csv = _write_collector_summary_csv(out_dir, aggs)
    print(f"collector summary csv -> {collector_csv}")

    if not args.no_plots:
        if _HAS_MPL:
            saved = _maybe_plot(out_dir, aggs)
            for s in saved:
                print(f"plot -> {s}")
        else:
            print("[INFO] matplotlib not available — only CSV summaries written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
