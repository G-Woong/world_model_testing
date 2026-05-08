"""P0 gate test: no fake-result markers anywhere in the repo (excluding paper_context_ref/).

Source docs:
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §16 ROAD-GATE-010
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md §10.1
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).parent.parent

# Tokens are split so this file itself doesn't trigger the scan.
FORBIDDEN_TOKENS = [
    "FAKE" + "_RESULT",
    "placeholder" + " result",
    "manually" + " filled metric",
]

EXCLUDED_DIRS = {"paper_context_ref", ".git", ".venv", ".claude", "plans"}
EXCLUDED_NAME_SUFFIXES = {".egg-info"}


def _iter_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        parts = set(rel.parts)
        if parts & EXCLUDED_DIRS:
            continue
        # Skip generated egg-info directories
        if any(part.endswith(".egg-info") for part in rel.parts):
            continue
        # Skip this test file itself (it holds the token definitions)
        if rel == pathlib.Path("tests") / "test_p0_no_fake_result_marker.py":
            continue
        if path.suffix in {".py", ".md", ".yaml", ".yml", ".toml", ".txt", ".json"}:
            yield path


def test_no_fake_result_markers():
    found = []
    for path in _iter_text_files():
        try:
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for token in FORBIDDEN_TOKENS:
            if token.lower() in content:
                found.append(f"{path.relative_to(ROOT)}: {token!r}")
    assert not found, "Forbidden fake-result markers found:\n" + "\n".join(found)
