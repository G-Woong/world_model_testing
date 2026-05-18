"""P0 gate test: frcgw package importability, script syntax, config validity.

Source docs:
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §6.3
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md §10.1
"""
from __future__ import annotations

import importlib
import py_compile
import pathlib
import yaml


ROOT = pathlib.Path(__file__).parent.parent


SUBPACKAGES = [
    "frcgw",
    "frcgw.schemas",
    "frcgw.text_env",
    "frcgw.gui_env",
    "frcgw.logging",
    "frcgw.data",
    "frcgw.models",
    "frcgw.objectives",
    "frcgw.planning",
    "frcgw.training",
    "frcgw.evaluation",
    "frcgw.reporting",
    "frcgw.utils",
]

SCRIPTS = [
    "scripts/00_validate_docs.py",
    "scripts/01_generate_text_data.py",
    "scripts/02_train_text_smoke.py",
    "scripts/03_eval_text_smoke.py",
    "scripts/04_generate_gui_mve_data.py",
    "scripts/05_validate_dataset.py",
    "scripts/06_train_vlm_mve.py",
    "scripts/07_eval_vlm_mve.py",
    "scripts/08_run_core_ablations.py",
    "scripts/09_generate_reports.py",
]

CONFIGS = [
    "configs/text_smoke.yaml",
    "configs/data_collection_text.yaml",
    "configs/data_collection_gui_mve.yaml",
    "configs/model_text.yaml",
    "configs/train_text.yaml",
    "configs/eval_text.yaml",
    "configs/ablation_core.yaml",
]


def test_frcgw_subpackages_importable():
    for pkg in SUBPACKAGES:
        importlib.import_module(pkg)


def test_scripts_syntax_valid():
    for rel in SCRIPTS:
        path = ROOT / rel
        assert path.exists(), f"Script missing: {rel}"
        py_compile.compile(str(path), doraise=True)


def test_configs_yaml_valid_with_phase_key():
    for rel in CONFIGS:
        path = ROOT / rel
        assert path.exists(), f"Config missing: {rel}"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None, f"Config empty: {rel}"
        assert "phase" in data, f"Config missing 'phase' key: {rel}"
