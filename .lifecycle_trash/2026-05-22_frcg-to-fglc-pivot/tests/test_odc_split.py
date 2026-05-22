"""Tests for grammar-template OOD split (TASK_LFD_001 M7 defense).

Source: .agent_tasks/codex_queue/TASK_LFD_001_cusum_sprt_baseline.md
"""
from __future__ import annotations

from frcgw.evaluation.metrics import split_episodes_by_grammar_ood
from frcgw.text_env.generator import OOD_GRAMMAR_FAMILIES, ID_GRAMMAR_FAMILIES


def test_odc_split_families_disjoint() -> None:
    """ID and OOD grammar families must be disjoint."""
    id_set = set(str(f) for f in ID_GRAMMAR_FAMILIES)
    ood_set = set(str(f) for f in OOD_GRAMMAR_FAMILIES)
    overlap = id_set & ood_set
    assert not overlap, f"ID and OOD families should be disjoint, got overlap: {overlap}"


def test_split_episodes_by_grammar_ood_correct_assignment() -> None:
    """filter_accordion and nested_scroll → OOD; others → ID."""
    episodes = [
        {"task_family": "filter_accordion"},
        {"task_family": "nested_scroll"},
        {"task_family": "search_form"},
        {"task_family": "modal_blocker"},
        {"task_family": "unknown_family"},
    ]
    id_eps, ood_eps = split_episodes_by_grammar_ood(episodes)

    id_families = {ep["task_family"] for ep in id_eps}
    ood_families = {ep["task_family"] for ep in ood_eps}

    assert "filter_accordion" in ood_families
    assert "nested_scroll" in ood_families
    assert "search_form" in id_families
    assert "modal_blocker" in id_families
    assert len(id_eps) + len(ood_eps) == len(episodes)


def test_split_empty_episodes() -> None:
    id_eps, ood_eps = split_episodes_by_grammar_ood([])
    assert id_eps == []
    assert ood_eps == []


def test_split_all_ood() -> None:
    episodes = [
        {"task_family": "filter_accordion"},
        {"task_family": "nested_scroll"},
    ]
    id_eps, ood_eps = split_episodes_by_grammar_ood(episodes)
    assert len(ood_eps) == 2
    assert len(id_eps) == 0
