"""audit_step4_lr_comparison - Compare plan_meta.F_t vs LR scorer F_t.

COMPARE-ONLY: Does not modify the active F_t path.
Source: docs/orchestration/lr_alignment/21_step4_execution_plan.md section D.3
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.schemas.step_schema import (  # noqa: E402
    ActionRecord,
    CandidateAction,
    EvaluationLabels,
    PublicEffect,
    PublicHistoryItem,
    PublicObservation,
    StepRecord,
    TrainingLabels,
)


DEFAULT_DATASET_CANDIDATES = (
    "data/frcgw_text/v0_3/test_id.jsonl",
    "data/frcgw_text/v0_2/test_id.jsonl",
)
DEFAULT_OUT = "outputs/audits/step4_lr_comparison.json"
FALLBACK_PUBLIC_SAFE_METADATA_KEYS = frozenset(
    {
        "expected_effect_type",
        "expected_no_effect_flag",
        "expected_precondition_status",
        "expected_progress_direction",
        "expected_failure_reason_public",
    }
)


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value):
        return asdict(value)
    return {}


def _coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            return parsed
    return []


def _coerce_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _float_or_default(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _candidate_from_raw(raw: Any, fallback_index: int = 0) -> CandidateAction:
    data = _as_dict(raw)
    if data:
        return CandidateAction(
            action_id=str(data.get("action_id") or f"candidate_{fallback_index}"),
            action_type=str(data.get("action_type") or "noop"),
            action_params=_coerce_dict(data.get("action_params")),
        )
    return CandidateAction(
        action_id=f"candidate_{fallback_index}",
        action_type=str(raw) if raw is not None else "noop",
        action_params={},
    )


def _history_from_raw(raw: Any, fallback_index: int = 0) -> PublicHistoryItem:
    data = _as_dict(raw)
    if data:
        return PublicHistoryItem(
            step_index=int(data.get("step_index", fallback_index)),
            action_summary=str(data.get("action_summary") or ""),
            effect_summary=_str_or_none(data.get("effect_summary")),
        )
    return PublicHistoryItem(
        step_index=fallback_index,
        action_summary=str(raw) if raw is not None else "",
        effect_summary=None,
    )


def _public_observation_from_raw(raw: Any) -> PublicObservation:
    data = _as_dict(raw)
    candidates = [
        _candidate_from_raw(item, idx)
        for idx, item in enumerate(_coerce_list(data.get("candidate_actions_public")))
    ]
    history = [
        _history_from_raw(item, idx)
        for idx, item in enumerate(_coerce_list(data.get("history_public")))
    ]
    return PublicObservation(
        instruction=str(data.get("instruction") or ""),
        dom_snapshot_public=data.get("dom_snapshot_public"),
        accessibility_tree_public=data.get("accessibility_tree_public"),
        screenshot_ref=_str_or_none(data.get("screenshot_ref")),
        history_public=history,
        candidate_actions_public=candidates,
    )


def _last_effect_summary(obs: PublicObservation) -> str | None:
    if not obs.history_public:
        return None
    return obs.history_public[-1].effect_summary


def _selected_hypothesis_value(action_data: dict[str, Any], key: str) -> str | None:
    value = action_data.get(key)
    return None if value is None else str(value)


def _step_record_from_raw(
    step: dict[str, Any],
    episode_id: str,
    fallback_step_index: int,
) -> StepRecord:
    obs = _public_observation_from_raw(step.get("public_observation") or {})
    base_action = (
        obs.candidate_actions_public[0]
        if obs.candidate_actions_public
        else CandidateAction("noop", "noop", {})
    )

    action_data = _as_dict(step.get("action"))
    action = ActionRecord(
        action_id=str(action_data.get("action_id") or base_action.action_id),
        action_type=str(action_data.get("action_type") or base_action.action_type),
        action_params=_coerce_dict(
            action_data.get("action_params") or base_action.action_params
        ),
        rewritten=bool(action_data.get("rewritten", False)),
        selected_hypothesis_id=_selected_hypothesis_value(
            action_data, "selected_hypothesis_id"
        ),
        selected_hypothesis_type=_selected_hypothesis_value(
            action_data, "selected_hypothesis_type"
        ),
        selected_hypothesis_confidence=(
            None
            if action_data.get("selected_hypothesis_confidence") is None
            else _float_or_default(action_data.get("selected_hypothesis_confidence"))
        ),
        selected_hypothesis_source=_selected_hypothesis_value(
            action_data, "selected_hypothesis_source"
        ),
    )

    effect_data = _as_dict(step.get("observed_effect_public"))
    effect_type = (
        effect_data.get("effect_type")
        or _last_effect_summary(obs)
        or "none"
    )
    observed_effect = PublicEffect(
        effect_type=str(effect_type),
        dom_diff_public=effect_data.get("dom_diff_public"),
        text_diff_public=_str_or_none(effect_data.get("text_diff_public")),
    )

    step_index = int(step.get("step_index", fallback_step_index))
    return StepRecord(
        step_id=str(step.get("step_id") or f"{episode_id}:step:{step_index}"),
        episode_id=episode_id,
        step_index=step_index,
        public_observation=obs,
        action=action,
        observed_effect_public=observed_effect,
        training_labels=TrainingLabels(
            true_regime="",
            true_control_grammar="",
            true_change_point="",
            true_reveal_vs_shift="",
            true_action_effect_type="",
            true_failed_action=False,
            failure_reason=None,
            progress_delta=0.0,
        ),
        evaluation_labels=EvaluationLabels(),
        counterfactuals=[],
        audit_metadata=None,
    )


def _select_dataset(explicit_dataset: str | None) -> Path | None:
    if explicit_dataset is not None:
        return Path(explicit_dataset)
    return next(
        (
            Path(candidate)
            for candidate in DEFAULT_DATASET_CANDIDATES
            if Path(candidate).exists()
        ),
        None,
    )


def _load_episodes(dataset_path: Path, n_episodes: int) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    for line in dataset_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        if "steps" not in raw:
            raw = {"episode_id": raw.get("episode_id", ""), "steps": [raw]}
        episodes.append(raw)
        if len(episodes) >= n_episodes:
            break
    return episodes


def _build_model() -> Any:
    from frcgw.models.text_frcg_model import TextFRCGModel

    model = TextFRCGModel()
    model.eval()
    return model


def _new_planner_state() -> Any:
    from frcgw.planning.planner import PlannerState

    return PlannerState()


def _gate_config() -> Any:
    from frcgw.planning.decision_gate import GateConfig

    return GateConfig(tau_f=0.5)


def _planner_f_t(
    obs: PublicObservation,
    step_idx: int,
    candidates: list[CandidateAction],
    model: Any,
    planner_state: Any,
    gate_cfg: Any,
) -> float:
    import torch
    from frcgw.planning.planner import text_frcg_plan

    with torch.no_grad():
        _, plan_meta = text_frcg_plan(
            obs,
            step_idx,
            candidates,
            model,
            planner_state,
            gate_cfg,
        )
    return float(getattr(plan_meta, "F_t", 0.0))


def _load_lr_components() -> tuple[dict[str, Any] | None, str | None]:
    try:
        from frcgw.falsification import lr_scorer
        from frcgw.falsification.lr_scorer import (
            EvidenceFeatures,
            EvidenceLikelihood,
            HypothesisCandidate,
            HypothesisTrace,
            LikelihoodRatioFalsificationScorer,
        )
    except Exception as exc:  # pragma: no cover - exercised by runtime environments
        return None, str(exc)

    return (
        {
            "module": lr_scorer,
            "EvidenceFeatures": EvidenceFeatures,
            "EvidenceLikelihood": EvidenceLikelihood,
            "HypothesisCandidate": HypothesisCandidate,
            "HypothesisTrace": HypothesisTrace,
            "LikelihoodRatioFalsificationScorer": LikelihoodRatioFalsificationScorer,
            "PUBLIC_SAFE_METADATA_KEYS": getattr(
                lr_scorer,
                "_PUBLIC_SAFE_METADATA_KEYS",
                FALLBACK_PUBLIC_SAFE_METADATA_KEYS,
            ),
        },
        None,
    )


def _evidence_features_from_step(
    step_record: StepRecord,
    lr_components: dict[str, Any] | None = None,
) -> Any:
    if lr_components is None:
        lr_components, import_error = _load_lr_components()
        if lr_components is None:
            raise RuntimeError(import_error or "lr_scorer import failed")

    evidence_cls = lr_components["EvidenceFeatures"]
    from_public_step = getattr(evidence_cls, "from_public_step", None)
    if callable(from_public_step):
        return from_public_step(step_record)

    effect = step_record.observed_effect_public
    return evidence_cls(
        effect_type=effect.effect_type,
        dom_diff_summary=str(effect.dom_diff_public or ""),
        accessibility_diff_summary=effect.text_diff_public or "",
        visual_diff_score=0.0,
        precondition_status="unknown",
        no_effect_flag=effect.effect_type in ("no_effect", "no_change", "noop"),
        delayed_effect_flag=False,
        noisy_observation_flag=False,
        progress_delta=0.0,
        failure_reason=None,
    )


def _public_safe_metadata(
    metadata: dict[str, Any],
    lr_components: dict[str, Any],
) -> dict[str, Any]:
    safe_keys = set(lr_components["PUBLIC_SAFE_METADATA_KEYS"])
    return {key: value for key, value in metadata.items() if key in safe_keys}


def _make_hypothesis_candidates(
    evidence: Any,
    lr_components: dict[str, Any],
) -> tuple[Any, Any, list[Any]]:
    hypothesis_trace_cls = lr_components["HypothesisTrace"]
    candidate_cls = lr_components["HypothesisCandidate"]

    effect_type = str(getattr(evidence, "effect_type", "none") or "none")
    no_effect_flag = bool(getattr(evidence, "no_effect_flag", False))
    precondition_status = str(getattr(evidence, "precondition_status", "unknown"))

    exec_metadata = _public_safe_metadata(
        {
            "expected_effect_type": "no_effect",
            "expected_no_effect_flag": True,
            "expected_precondition_status": precondition_status,
            "expected_progress_direction": "zero",
        },
        lr_components,
    )
    alt_metadata = [
        {
            "expected_effect_type": effect_type,
            "expected_no_effect_flag": no_effect_flag,
            "expected_precondition_status": precondition_status,
            "expected_progress_direction": "zero",
        },
        {
            "expected_effect_type": "no_effect",
            "expected_no_effect_flag": True,
            "expected_precondition_status": precondition_status,
        },
        {
            "expected_effect_type": "state_change",
            "expected_no_effect_flag": False,
            "expected_progress_direction": "positive",
        },
        {
            "expected_effect_type": "failed",
            "expected_no_effect_flag": False,
            "expected_progress_direction": "negative",
        },
        {"expected_precondition_status": precondition_status},
        {"expected_progress_direction": "zero"},
        {"expected_effect_type": effect_type},
        {"expected_no_effect_flag": no_effect_flag},
    ]

    h_exec_trace = hypothesis_trace_cls(
        selected_hypothesis_id="h_exec",
        hypothesis_type="predicted",
        confidence=0.5,
        source="audit_public_proxy",
        is_oracle_label=False,
    )
    h_exec_candidate = candidate_cls(
        hypothesis_id="h_exec",
        regime_id="r_public",
        control_grammar_id="g_exec",
        prior_logprob=0.0,
        metadata=exec_metadata,
    )
    alt_candidates = [
        candidate_cls(
            hypothesis_id=f"h_alt_{idx}",
            regime_id="r_public",
            control_grammar_id=f"g_alt_{idx}",
            prior_logprob=0.0,
            metadata=_public_safe_metadata(metadata, lr_components),
        )
        for idx, metadata in enumerate(alt_metadata)
    ]
    return h_exec_trace, h_exec_candidate, alt_candidates


def _lr_scorer_f_t(
    step_record: StepRecord,
    lr_components: dict[str, Any] | None,
    lr_import_error: str | None,
) -> tuple[float, bool, str | None]:
    if lr_components is None:
        return 0.0, False, lr_import_error

    try:
        evidence = _evidence_features_from_step(step_record, lr_components)
        likelihood = lr_components["EvidenceLikelihood"]()
        scorer = lr_components["LikelihoodRatioFalsificationScorer"]()
        h_exec_trace, h_exec_candidate, alt_candidates = _make_hypothesis_candidates(
            evidence,
            lr_components,
        )
        exec_likelihood = likelihood.score(evidence, h_exec_candidate, None, None)
        alt_likelihoods = [
            likelihood.score(evidence, alt_candidate, None, None)
            for alt_candidate in alt_candidates
        ]
        lr_result = scorer.score(
            h_exec_trace=h_exec_trace,
            exec_likelihood=exec_likelihood,
            alt_likelihoods=alt_likelihoods,
            alt_candidates=alt_candidates,
        )
        return float(getattr(lr_result, "F_t", 0.0)), True, None
    except Exception as exc:
        return 0.0, False, str(exc)


def run_comparison(dataset_path: Path, n_episodes: int, out_path: Path) -> dict[str, Any]:
    episodes = _load_episodes(dataset_path, n_episodes)
    model = _build_model()
    gate_cfg = _gate_config()
    lr_components, lr_import_error = _load_lr_components()
    results: list[dict[str, Any]] = []

    for episode in episodes:
        episode_id = str(episode.get("episode_id", ""))
        planner_state = _new_planner_state()
        for fallback_idx, raw_step in enumerate(episode.get("steps", [])):
            if not isinstance(raw_step, dict):
                continue
            step_record = _step_record_from_raw(raw_step, episode_id, fallback_idx)
            obs = step_record.public_observation
            candidates = list(obs.candidate_actions_public)
            f_t_planner = _planner_f_t(
                obs,
                step_record.step_index,
                candidates,
                model,
                planner_state,
                gate_cfg,
            )
            f_t_lr, lr_ok, lr_error = _lr_scorer_f_t(
                step_record,
                lr_components,
                lr_import_error,
            )
            abs_diff = abs(f_t_planner - f_t_lr)
            row = {
                "episode_id": episode_id,
                "step_index": step_record.step_index,
                "F_t_planner": f_t_planner,
                "F_t_lr_scorer": f_t_lr,
                "abs_diff": abs_diff,
                "degenerate_planner": f_t_planner == 0.0,
                "degenerate_lr": f_t_lr == 0.0,
                "lr_scorer_ok": lr_ok,
            }
            if lr_error:
                row["lr_error"] = lr_error
            results.append(row)

    if not results:
        mean_abs_diff = 0.0
        interpretation = "no_steps"
    else:
        mean_abs_diff = sum(row["abs_diff"] for row in results) / len(results)
        if mean_abs_diff < 0.01:
            interpretation = "numerically_equivalent"
        elif mean_abs_diff < 0.5:
            interpretation = "minor_drift"
        else:
            interpretation = "major_divergence"

    report = {
        "dataset": str(dataset_path),
        "n_episodes": len(episodes),
        "n_steps": len(results),
        "mean_abs_diff": mean_abs_diff,
        "interpretation": interpretation,
        "degenerate_planner_rate": (
            sum(1 for row in results if row["degenerate_planner"])
            / max(1, len(results))
        ),
        "degenerate_lr_rate": (
            sum(1 for row in results if row["degenerate_lr"]) / max(1, len(results))
        ),
        "lr_scorer_failure_rate": (
            sum(1 for row in results if not row["lr_scorer_ok"])
            / max(1, len(results))
        ),
        "steps": results,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--n-episodes", type=int, default=5)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    dataset_path = _select_dataset(args.dataset)
    if dataset_path is None:
        print("ERROR: no test_id dataset found")
        return 1
    if not dataset_path.exists():
        print(f"ERROR: dataset not found: {dataset_path}")
        return 1

    report = run_comparison(
        dataset_path=dataset_path,
        n_episodes=args.n_episodes,
        out_path=Path(args.out),
    )
    print(f"LR comparison report: {args.out}")
    print(
        "  mean_abs_diff: "
        f"{report['mean_abs_diff']:.4f} ({report['interpretation']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
