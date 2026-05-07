"""WM diagnostics utilities (Session 10).

본 모듈은 학습 완료된 run을 *읽기 전용*으로 분석하는 헬퍼만 제공한다. 학습/optimizer/
checkpoint write 코드는 들어 있지 않다 (Session 10은 read-only diagnostic).

PART0 §3 정합:
    - test_id / OOD에 대한 평가는 frozen checkpoint로 no_grad evaluation만 수행하며,
      절대 hyperparameter / checkpoint 선택에 사용하지 않는다 (held-out diagnostic).
    - collector_metadata 등 forbidden key는 본 모듈도 입력으로 받지 않는다.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import torch
from torch import Tensor


# =============================================================================
# 1. log parsing
# =============================================================================


def read_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    """jsonl 파일을 list[dict]로 읽는다. 빈 줄/잘못된 줄은 skip."""
    p = Path(path)
    if not p.is_file():
        return []
    out: List[Dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:   # noqa: BLE001
            continue
    return out


def last_record(records: Sequence[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    return dict(records[-1]) if records else None


def best_record(
    records: Sequence[Mapping[str, Any]],
    key: str,
    *,
    mode: str = "min",
) -> Optional[Dict[str, Any]]:
    """list[dict]에서 ``key`` 기준 best record (min 또는 max).

    key가 없는 record는 skip. positives==0인 경우는 호출자가 별도 검증.
    """
    best: Optional[Dict[str, Any]] = None
    best_v: Optional[float] = None
    for r in records:
        v = r.get(key)
        if v is None:
            continue
        try:
            v = float(v)
        except Exception:   # noqa: BLE001
            continue
        if best_v is None or (mode == "min" and v < best_v) or (mode == "max" and v > best_v):
            best_v = v
            best = dict(r)
    return best


# =============================================================================
# 2. run-level summary
# =============================================================================


@dataclass
class RunSummary:
    """단일 run의 요약. 본 dataclass는 csv 행으로 변환 가능."""
    run_name: str
    variant: str
    final_step: int = 0
    final_stage: str = ""
    elapsed_time_sec: float = 0.0
    final_train_total_loss: float = float("nan")
    final_valid_uniform_total: float = float("nan")
    final_valid_event_total: float = float("nan")
    best_valid_uniform_total: float = float("nan")
    best_valid_uniform_step: int = 0
    best_valid_event_change_point_f1: float = float("nan")
    best_valid_event_change_point_step: int = 0
    # common-core (final eval at last valid)
    reward_mse_uniform: float = float("nan")
    state_mse_uniform: float = float("nan")
    regime_accuracy_uniform: float = float("nan")
    change_point_f1_event: float = float("nan")
    change_point_precision_event: float = float("nan")
    change_point_recall_event: float = float("nan")
    reveal_f1_event: float = float("nan")
    shift_f1_event: float = float("nan")
    raw_eff_mismatch_f1_event: float = float("nan")
    train_valid_gap: float = float("nan")
    notes: str = ""

    def to_row(self) -> Dict[str, Any]:
        return self.__dict__.copy()


# variant ablation에서 N/A로 처리해야 할 키들. 진단 단계에서만 사용.
VARIANT_NA_FIELDS: Dict[str, Tuple[str, ...]] = {
    "no_regime": ("regime_accuracy_uniform",),
    "no_change_point": (
        "change_point_f1_event",
        "change_point_precision_event",
        "change_point_recall_event",
        "best_valid_event_change_point_f1",
        "best_valid_event_change_point_step",
    ),
    "no_reveal": ("reveal_f1_event",),
    "no_state_aux": ("state_mse_uniform",),
}


def summarize_run(
    run_dir: Path,
    *,
    variant: str = "full_model",
) -> RunSummary:
    """run_dir의 train_log/valid_log를 파싱해 RunSummary를 만든다.

    head가 ablate된 variant의 N/A 필드는 ``float("nan")``로 둔다 (csv writer가 빈 칸으로
    출력해도 좋고, ``str(float('nan'))=='nan'``이므로 의미가 명확).
    """
    rsum = RunSummary(run_name=run_dir.name, variant=variant)
    train_log = read_jsonl(run_dir / "train_log.jsonl")
    valid_log = read_jsonl(run_dir / "valid_log.jsonl")

    last_t = last_record(train_log)
    last_v = last_record(valid_log)
    if last_t is None or last_v is None:
        rsum.notes = "missing train_log or valid_log"
        return rsum

    rsum.final_step = int(last_t.get("global_step", 0))
    rsum.final_stage = str(last_t.get("stage", ""))
    rsum.final_train_total_loss = float(last_t.get("loss", {}).get("total", float("nan")))
    rsum.final_valid_uniform_total = float(last_v.get("valid_uniform/loss/total", float("nan")))
    rsum.final_valid_event_total = float(last_v.get("valid_event/loss/total", float("nan")))
    rsum.reward_mse_uniform = float(last_v.get("valid_uniform/reward/mse", float("nan")))
    rsum.state_mse_uniform = float(last_v.get("valid_uniform/state/mse", float("nan")))
    rsum.regime_accuracy_uniform = float(last_v.get("valid_uniform/regime/accuracy", float("nan")))
    rsum.change_point_f1_event = float(last_v.get("valid_event/change_point/f1", float("nan")))
    rsum.change_point_precision_event = float(last_v.get("valid_event/change_point/precision", float("nan")))
    rsum.change_point_recall_event = float(last_v.get("valid_event/change_point/recall", float("nan")))
    rsum.reveal_f1_event = float(last_v.get("valid_event/reveal/f1", float("nan")))
    rsum.shift_f1_event = float(last_v.get("valid_event/shift/f1", float("nan")))
    rsum.raw_eff_mismatch_f1_event = float(last_v.get("valid_event/raw_eff_mismatch/f1", float("nan")))

    # best valid_uniform/loss/total (mode=min)
    best_uni = best_record(valid_log, "valid_uniform/loss/total", mode="min")
    if best_uni is not None:
        rsum.best_valid_uniform_total = float(best_uni.get("valid_uniform/loss/total", float("nan")))
        rsum.best_valid_uniform_step = int(best_uni.get("global_step", 0))

    # best valid_event/change_point/f1 (mode=max)
    if variant != "no_change_point":
        best_cp = best_record(valid_log, "valid_event/change_point/f1", mode="max")
        if best_cp is not None:
            rsum.best_valid_event_change_point_f1 = float(best_cp.get("valid_event/change_point/f1", float("nan")))
            rsum.best_valid_event_change_point_step = int(best_cp.get("global_step", 0))

    # train-valid gap (latest)
    if not math.isnan(rsum.final_train_total_loss) and not math.isnan(rsum.final_valid_uniform_total):
        rsum.train_valid_gap = rsum.final_valid_uniform_total - rsum.final_train_total_loss

    # elapsed
    run_summary_yaml = run_dir / "run_summary.yaml"
    if run_summary_yaml.is_file():
        try:
            import yaml
            with run_summary_yaml.open("r", encoding="utf-8") as f:
                d = yaml.safe_load(f) or {}
            rsum.elapsed_time_sec = float(d.get("elapsed_sec", 0.0))
        except Exception:   # noqa: BLE001
            pass

    # variant N/A 처리
    for f in VARIANT_NA_FIELDS.get(variant, ()):
        if hasattr(rsum, f):
            setattr(rsum, f, float("nan"))

    return rsum


# =============================================================================
# 3. checkpoint inventory
# =============================================================================


@dataclass
class CkptStatus:
    run_name: str
    variant: str
    last_pt: bool
    step_30000_pt: bool
    step_29000_pt: bool
    best_valid_uniform_pt: bool
    best_valid_event_cp_f1_pt: bool
    primary_path: str          # 비교에 사용할 ckpt 경로
    alias_missing_notes: str


def inventory_checkpoints(run_dir: Path, variant: str) -> CkptStatus:
    """checkpoint 파일 존재 여부 + primary 선택을 반환한다."""
    ck_dir = run_dir / "checkpoints"
    last = ck_dir / "last.pt"
    step30 = ck_dir / "step_00030000.pt"
    step29 = ck_dir / "step_00029000.pt"
    best_uni = ck_dir / "best_valid_uniform_loss_total.pt"
    best_cp = ck_dir / "best_valid_event_change_point_f1.pt"

    primary: Optional[Path] = None
    if step30.is_file():
        primary = step30
    elif last.is_file():
        primary = last
    elif step29.is_file():
        primary = step29

    notes = []
    if not best_uni.is_file():
        notes.append("best_valid_uniform alias missing")
    if not best_cp.is_file() and variant != "no_change_point":
        notes.append("best_cp_f1 alias missing")

    return CkptStatus(
        run_name=run_dir.name,
        variant=variant,
        last_pt=last.is_file(),
        step_30000_pt=step30.is_file(),
        step_29000_pt=step29.is_file(),
        best_valid_uniform_pt=best_uni.is_file(),
        best_valid_event_cp_f1_pt=best_cp.is_file(),
        primary_path=str(primary.relative_to(run_dir.parent.parent)) if primary else "",
        alias_missing_notes=" / ".join(notes),
    )


# =============================================================================
# 4. binary classification metric utilities (PR-AUC, threshold sweep)
# =============================================================================


def threshold_sweep(
    logit: np.ndarray,
    target: np.ndarray,
    mask: Optional[np.ndarray] = None,
    *,
    thresholds: Optional[Sequence[float]] = None,
) -> List[Dict[str, float]]:
    """logit/target/mask에서 threshold 별 P/R/F1을 산출.

    thresholds 미지정 시 logit space [-5, ..., 5] 11개 + sigmoid 0.01/0.05/0.1/0.2/0.3/0.7/0.9도 추가.
    """
    if thresholds is None:
        # logit space + 일부 probability space (logit으로 변환)
        logit_thresholds = list(range(-5, 6))   # -5..5
        prob_thresholds = [0.01, 0.05, 0.1, 0.2, 0.3, 0.7, 0.9]
        # logit = log(p / (1-p))
        prob_logits = [math.log(p / (1.0 - p)) for p in prob_thresholds]
        thresholds = sorted(set(logit_thresholds + prob_logits))

    if mask is None:
        m = np.ones_like(target, dtype=bool)
    else:
        m = mask.astype(bool)
    tgt = (target > 0.5) & m

    out: List[Dict[str, float]] = []
    for t in thresholds:
        pred = (logit > float(t)) & m
        tp = int((pred & tgt).sum())
        fp = int((pred & ~tgt & m).sum())
        fn = int((~pred & tgt).sum())
        tn = max(0, int(m.sum()) - tp - fp - fn)
        eps = 1e-9
        precision = tp / max(eps, tp + fp)
        recall = tp / max(eps, tp + fn)
        f1 = 2.0 * precision * recall / max(eps, precision + recall)
        out.append({
            "threshold_logit": float(t),
            "threshold_prob": float(1.0 / (1.0 + math.exp(-float(t)))),
            "tp": float(tp), "fp": float(fp), "fn": float(fn), "tn": float(tn),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
        })
    return out


def pr_auc(
    logit: np.ndarray,
    target: np.ndarray,
    mask: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """Average-precision style PR-AUC + best-F1 threshold (sklearn 의존성 없이 수기 구현).

    extreme imbalance 시 잘 정의된다 (F1 최대 threshold도 함께 반환).
    """
    if mask is not None:
        m = mask.astype(bool)
        logit = logit[m]
        target = target[m]
    tgt = (target > 0.5).astype(np.int64)
    n_pos = int(tgt.sum())
    n = int(tgt.size)
    if n_pos == 0 or n == 0:
        return {
            "pr_auc": 0.0,
            "best_f1": 0.0,
            "best_threshold_logit": float("nan"),
            "best_precision": 0.0,
            "best_recall": 0.0,
            "n_positive": 0.0,
            "n_total": float(n),
            "pos_logit_mean": 0.0,
            "neg_logit_mean": 0.0,
            "separation": 0.0,
        }
    # sort by logit descending
    order = np.argsort(-logit)
    logit_s = logit[order]
    tgt_s = tgt[order]
    cum_tp = np.cumsum(tgt_s)
    cum_fp = np.cumsum(1 - tgt_s)
    precision = cum_tp / np.maximum(1, cum_tp + cum_fp)
    recall = cum_tp / max(1, n_pos)
    # AP = sum over thresholds of (R[i] - R[i-1]) * P[i] (sklearn average_precision_score 동일)
    recall_prev = np.concatenate([[0.0], recall[:-1]])
    ap = float(np.sum((recall - recall_prev) * precision))
    # best-F1 threshold
    f1 = 2.0 * precision * recall / np.maximum(1e-9, precision + recall)
    best_idx = int(np.argmax(f1))
    best_threshold = float(logit_s[best_idx])
    pos_mean = float(logit[tgt == 1].mean()) if n_pos > 0 else 0.0
    neg_mean = float(logit[tgt == 0].mean()) if (n - n_pos) > 0 else 0.0
    return {
        "pr_auc": ap,
        "best_f1": float(f1[best_idx]),
        "best_threshold_logit": best_threshold,
        "best_precision": float(precision[best_idx]),
        "best_recall": float(recall[best_idx]),
        "n_positive": float(n_pos),
        "n_total": float(n),
        "pos_logit_mean": pos_mean,
        "neg_logit_mean": neg_mean,
        "separation": pos_mean - neg_mean,
    }


# =============================================================================
# 5. reward long-tail diagnostics
# =============================================================================


def reward_diagnostics(
    pred: np.ndarray,
    target: np.ndarray,
    mask: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """reward 예측의 normal/spike 분리 분석. PART2 §3.12 reward decomp 정합."""
    if mask is not None:
        m = mask.astype(bool)
        pred = pred[m]
        target = target[m]
    err = (pred - target) ** 2

    def _mse_subset(sel: np.ndarray) -> float:
        return float(err[sel].mean()) if sel.any() else 0.0

    sm_normal = np.abs(target) < 5.0
    sm_pos = target > 0
    sm_large = target >= 50.0
    sm_completion = target >= 200.0

    pred_sign = np.sign(pred)
    tgt_sign = np.sign(target)

    sign_acc = float((pred_sign == tgt_sign).mean()) if pred.size else 0.0

    # spike precision/recall: spike = target > 50 vs predicted > 50
    pred_spike = pred > 50
    tgt_spike = target >= 50
    tp = int((pred_spike & tgt_spike).sum())
    fp = int((pred_spike & ~tgt_spike).sum())
    fn = int((~pred_spike & tgt_spike).sum())
    eps = 1e-9
    spike_precision = tp / max(eps, tp + fp)
    spike_recall = tp / max(eps, tp + fn)

    # error percentile
    abs_err = np.abs(pred - target)
    perc = {f"p{p}": float(np.percentile(abs_err, p)) for p in (50, 90, 95, 99)} if abs_err.size else {}
    return {
        "n": float(pred.size),
        "mse_total": float(err.mean()) if pred.size else 0.0,
        "mse_normal_abs_lt_5": _mse_subset(sm_normal),
        "mse_positive": _mse_subset(sm_pos),
        "mse_large_ge_50": _mse_subset(sm_large),
        "mse_completion_ge_200": _mse_subset(sm_completion),
        "n_normal": float(sm_normal.sum()),
        "n_positive": float(sm_pos.sum()),
        "n_large": float(sm_large.sum()),
        "n_completion": float(sm_completion.sum()),
        "reward_sign_accuracy": sign_acc,
        "spike_precision": float(spike_precision),
        "spike_recall": float(spike_recall),
        **{f"abs_err_{k}": v for k, v in perc.items()},
    }


# =============================================================================
# 6. csv writer helper
# =============================================================================


def write_csv(path: str | Path, rows: Sequence[Mapping[str, Any]], *, columns: Optional[Sequence[str]] = None) -> Path:
    import csv
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8")
        return p
    cols = list(columns) if columns else list(rows[0].keys())
    with p.open("w", newline="", encoding="utf-8") as fp:
        w = csv.DictWriter(fp, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            row = {}
            for k in cols:
                v = r.get(k, "")
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    row[k] = ""
                else:
                    row[k] = v
            w.writerow(row)
    return p


__all__ = [
    "read_jsonl",
    "last_record",
    "best_record",
    "RunSummary",
    "VARIANT_NA_FIELDS",
    "summarize_run",
    "CkptStatus",
    "inventory_checkpoints",
    "threshold_sweep",
    "pr_auc",
    "reward_diagnostics",
    "write_csv",
]
