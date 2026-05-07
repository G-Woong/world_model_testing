"""Per-step / per-episode planner trace storage.

PlannerTrace는 evaluation에서 사후 분석을 위한 *plain-data* 기록 객체다.
- per-step JSON-serializable dict로 누적
- jsonl로 직렬화 (한 line = 한 step)
- ground-truth (env info의 true_state / true_regime 등)는 metric 계산을 위해 *기록만*
  하며, planner의 input으로는 절대 들어가지 않는다 (oracle leakage 방지).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class StepTrace:
    """한 env step의 trace entry.

    필수 필드 (post-eval analysis가 사용)
    ----------------------------------
    step                : 0-based step index
    action              : env에 보낸 raw action (planner decision)
    decision_mode       : reactive | plan_current | plan_alternative | correct |
                          avoid | delay | explore_for_information
    used_planning       : bool
    planning_calls      : 이 step의 planning call (보통 0 or 1)
    rollout_steps       : 이 step의 imagined rollout step 수
    candidate_count     : 평가한 candidate 수
    horizon             : 사용한 horizon
    reward              : env가 반환한 step reward
    cumulative_reward   : episode 누적 reward
    terminated/truncated: env flag
    falsification_score : FRC가 채움 (0 if baseline)
    action_relevance    : FRC가 채움 (0 if baseline)

    diagnostic 필드 (head outputs / ground truth — 기록만, planner input 아님)
    -------------------------------------------------------------------------
    head_pred_summary   : per-step head 예측 요약 (state[0..4], reward, done, regime_argmax,
                          cp_prob, reveal_prob, shift_prob, mismatch_prob)
    info_summary        : env info 요약 (true_state, true_regime, change_point, reveal_event,
                          shift_event, task_id, room_id, completed_tasks, fail_count)

    추가 메타
    --------
    decision_reason     : per-mode score / threshold 등
    """

    step: int
    action: int
    decision_mode: str = "reactive"
    used_planning: bool = False
    planning_calls: int = 0
    rollout_steps: int = 0
    candidate_count: int = 0
    horizon: int = 0
    reward: float = 0.0
    cumulative_reward: float = 0.0
    terminated: bool = False
    truncated: bool = False
    falsification_score: float = 0.0
    action_relevance: float = 0.0
    head_pred_summary: Dict[str, Any] = field(default_factory=dict)
    info_summary: Dict[str, Any] = field(default_factory=dict)
    decision_reason: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlannerTrace:
    """한 episode 전체의 trace 모음.

    Attributes
    ----------
    episode_id     : (split, model, planner, seed, episode_index) 튜플의 string repr
    split          : split name
    model_name     : model variant
    planner_name   : planner name
    seed           : env seed
    episode_index  : index within (split, seed)
    steps          : list of StepTrace
    summary        : episode-level summary dict (final return, success, completed_tasks 등)
    """

    episode_id: str
    split: str = "test_id"
    model_name: str = "full"
    planner_name: str = "ours_frc"
    seed: int = 0
    episode_index: int = 0
    steps: List[StepTrace] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------------------
    # I/O
    # ---------------------------------------------------------------------
    def to_jsonl_lines(self) -> List[str]:
        """각 step + summary line을 jsonl line list로 직렬화."""
        lines: List[str] = []
        # header line
        lines.append(json.dumps({
            "_kind": "header",
            "episode_id": self.episode_id,
            "split": self.split,
            "model_name": self.model_name,
            "planner_name": self.planner_name,
            "seed": self.seed,
            "episode_index": self.episode_index,
        }, default=_json_default))
        # step lines
        for st in self.steps:
            lines.append(json.dumps({"_kind": "step", **asdict(st)}, default=_json_default))
        # summary line
        lines.append(json.dumps({
            "_kind": "summary",
            "episode_id": self.episode_id,
            **self.summary,
        }, default=_json_default))
        return lines

    def write_jsonl(self, path: Path | str) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fp:
            for line in self.to_jsonl_lines():
                fp.write(line + "\n")
        return p


def _json_default(obj: Any) -> Any:
    """JSON 직렬화 fallback (numpy/torch tensor 등)."""
    try:
        import numpy as np  # local import to avoid hard dep at import-time
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.generic):
            return obj.item()
    except Exception:  # noqa: BLE001
        pass
    try:
        import torch
        if isinstance(obj, torch.Tensor):
            return obj.detach().cpu().tolist()
    except Exception:  # noqa: BLE001
        pass
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if hasattr(obj, "as_tuple"):
        return obj.as_tuple()
    return str(obj)


def write_traces_jsonl(traces: List[PlannerTrace], path: Path | str) -> Path:
    """여러 PlannerTrace를 한 jsonl 파일에 합쳐 쓴다."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fp:
        for tr in traces:
            for line in tr.to_jsonl_lines():
                fp.write(line + "\n")
    return p


__all__ = ["StepTrace", "PlannerTrace", "write_traces_jsonl"]
