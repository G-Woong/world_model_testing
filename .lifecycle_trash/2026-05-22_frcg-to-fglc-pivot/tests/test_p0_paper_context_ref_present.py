"""P0 gate test: paper_context_ref files present, docs/README.md present.

Source docs:
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §6.3 CC-P0-G2
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md §10.1
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).parent.parent
REF = ROOT / "paper_context_ref"

REQUIRED_FILES = [
    "00_CONTEXT_INDEX.md",
    "13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md",
    "14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md",
    "15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md",
]


def test_required_paper_context_ref_files_present():
    for name in REQUIRED_FILES:
        assert (REF / name).exists(), f"Missing: paper_context_ref/{name}"


def test_paper_context_ref_has_minimum_files():
    md_files = list(REF.glob("*.md"))
    assert len(md_files) >= 18, f"Expected >=18 MD files, got {len(md_files)}"


def test_docs_readme_present():
    assert (ROOT / "docs" / "README.md").exists(), "docs/README.md missing"
