from __future__ import annotations

import json
from dataclasses import asdict
from types import SimpleNamespace

from scripts import audit_step4_lr_comparison as audit


def _raw_step(step_index: int = 0, *, effect_type: str = "no_effect") -> dict:
    return {
        "step_id": f"ep0_step_{step_index:03d}",
        "step_index": step_index,
        "public_observation": {
            "instruction": "open the panel",
            "history_public": [
                {
                    "step_index": max(0, step_index - 1),
                    "action_summary": "wait",
                    "effect_summary": effect_type,
                }
            ],
            "candidate_actions_public": [
                {
                    "action_id": "open",
                    "action_type": "click",
                    "action_params": {"target": "panel"},
                }
            ],
        },
        "action": {
            "action_id": "open",
            "action_type": "click",
            "selected_hypothesis_id": "h_model",
            "selected_hypothesis_type": "predicted",
            "selected_hypothesis_confidence": 0.7,
            "selected_hypothesis_source": "test",
        },
        "observed_effect_public": {
            "effect_type": effect_type,
            "dom_diff_public": {"panel": "open"},
            "text_diff_public": "panel opened",
        },
        "training_labels": {
            "true_regime": "hidden",
            "true_control_grammar": "hidden",
            "true_change_point": "hidden",
            "true_reveal_vs_shift": "hidden",
            "true_action_effect_type": "hidden",
            "true_failed_action": False,
            "failure_reason": None,
            "progress_delta": 1.0,
        },
        "evaluation_labels": {
            "true_wrong_hypothesis": True,
            "h_exec_id": "oracle_h",
            "correct_hypothesis_id": "oracle_correct",
        },
        "audit_metadata": {
            "split_id": "test_id",
            "policy_id": "hidden",
            "template_id": "hidden",
        },
    }


def _write_dataset(tmp_path, steps: list[dict]) -> str:
    dataset = tmp_path / "test_id.jsonl"
    dataset.write_text(
        json.dumps({"episode_id": "ep0", "steps": steps}) + "\n",
        encoding="utf-8",
    )
    return str(dataset)


def _patch_planner(monkeypatch, value: float) -> None:
    monkeypatch.setattr(
        audit,
        "_build_model",
        lambda: SimpleNamespace(eval=lambda: None),
    )
    monkeypatch.setattr(audit, "_gate_config", lambda: object())
    monkeypatch.setattr(audit, "_new_planner_state", lambda: object())
    monkeypatch.setattr(
        audit,
        "_planner_f_t",
        lambda obs, step_idx, candidates, model, planner_state, gate_cfg: value,
    )


def test_lr_comparison_script_emits_json(tmp_path, monkeypatch) -> None:
    dataset = _write_dataset(tmp_path, [_raw_step(effect_type="state_change")])
    out_path = tmp_path / "report.json"
    _patch_planner(monkeypatch, value=0.25)

    exit_code = audit.main(
        [
            "--dataset",
            dataset,
            "--n-episodes",
            "1",
            "--out",
            str(out_path),
        ]
    )

    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert out_path.exists()
    assert "mean_abs_diff" in report


def test_lr_scorer_receives_no_forbidden_metadata() -> None:
    from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS

    step_record = audit._step_record_from_raw(_raw_step(), "ep0", 0)
    features = audit._evidence_features_from_step(step_record)

    feature_keys = set(asdict(features))
    assert feature_keys.isdisjoint(FORBIDDEN_AGENT_FIELDS)


def test_hypothesis_candidate_metadata_keys_subset_of_public_safe() -> None:
    from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS

    lr_components, import_error = audit._load_lr_components()
    assert lr_components is not None, import_error

    step_record = audit._step_record_from_raw(
        _raw_step(effect_type="state_change"),
        "ep0",
        0,
    )
    features = audit._evidence_features_from_step(step_record, lr_components)
    _, h_exec_candidate, alt_candidates = audit._make_hypothesis_candidates(
        features,
        lr_components,
    )

    public_safe = set(lr_components["PUBLIC_SAFE_METADATA_KEYS"])
    for candidate in [h_exec_candidate, *alt_candidates]:
        metadata_keys = set(candidate.metadata)
        assert metadata_keys <= public_safe
        assert metadata_keys.isdisjoint(FORBIDDEN_AGENT_FIELDS)
        assert not any(
            key.startswith(("true_", "oracle_")) for key in metadata_keys
        )


def test_lr_comparison_reports_degenerate_rate(tmp_path, monkeypatch) -> None:
    dataset = _write_dataset(tmp_path, [_raw_step(0), _raw_step(1)])
    out_path = tmp_path / "report.json"
    _patch_planner(monkeypatch, value=0.0)

    exit_code = audit.main(
        [
            "--dataset",
            dataset,
            "--n-episodes",
            "1",
            "--out",
            str(out_path),
        ]
    )

    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["n_steps"] == 2
    assert report["degenerate_planner_rate"] == 1.0
