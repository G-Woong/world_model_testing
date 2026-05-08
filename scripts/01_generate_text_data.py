"""scripts/01_generate_text_data.py — CC-P2 text-only data generation entrypoint placeholder.

Source docs:
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §8 (CC-P2)
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §18
"""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate text-only trajectories.")
    parser.add_argument("--config", required=True)
    parser.parse_known_args()
    raise NotImplementedError(
        "CC-P2: implementation deferred. See paper_context_ref/13 §8."
    )


if __name__ == "__main__":
    raise SystemExit(main())
