from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data" / "frcgw_text" / "v0_2"
OOD_FAMILIES = {"filter_accordion", "nested_scroll"}
ID_FAMILIES = {
    "search_form",
    "required_dropdown",
    "modal_blocker",
    "pagination_vs_infinite",
    "loading_delayed",
    "permission_gate",
}


def _load_episodes(split: str) -> list[dict[str, Any]]:
    path = DATA_ROOT / f"{split}.jsonl"
    assert path.exists(), f"missing generated split: {path}"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _eval_labels(step: dict[str, Any]) -> dict[str, Any]:
    labels = step.get("evaluation_labels")
    if isinstance(labels, dict):
        return labels
    labels = step.get("eval_labels")
    if isinstance(labels, dict):
        return labels
    return {}


def test_test_ood_jsonl_created_with_distinct_grammar_families() -> None:
    episodes = _load_episodes("test_ood")
    families = {episode["task_family"] for episode in episodes}

    assert families
    assert families <= OOD_FAMILIES
    assert families.isdisjoint(ID_FAMILIES)


def test_ood_type_present_in_all_ood_episodes() -> None:
    episodes = _load_episodes("test_ood")

    for episode in episodes:
        for step in episode["steps"]:
            assert _eval_labels(step)["ood_type"] == "grammar_shift"


def test_ood_split_does_not_duplicate_test_id_exactly() -> None:
    test_id_ids = {episode["episode_id"] for episode in _load_episodes("test_id")}
    test_ood_ids = {episode["episode_id"] for episode in _load_episodes("test_ood")}

    assert test_id_ids.isdisjoint(test_ood_ids)
