"""P0 gate test: README.md contains required contract keywords.

Source docs:
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §6.3 CC-P0-G3
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md §10.1
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).parent.parent

REQUIRED_KEYWORDS = [
    "paper_context_ref/00_CONTEXT_INDEX.md",
    "Required Execution Order",
    "Forbidden",
    "hidden",
    "falsification",
]


def test_readme_contains_required_keywords():
    readme = ROOT / "README.md"
    assert readme.exists(), "README.md missing"
    content = readme.read_text(encoding="utf-8")
    for kw in REQUIRED_KEYWORDS:
        assert kw in content, f"README.md missing required keyword: {kw!r}"
