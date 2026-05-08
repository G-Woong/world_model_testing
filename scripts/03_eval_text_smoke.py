"""scripts/03_eval_text_smoke.py — CC-P3 text-only evaluation entrypoint placeholder.

Source docs:
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §9 (CC-P3)
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §18
"""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate text-only FRCG model.")
    parser.add_argument("--config", required=True)
    parser.parse_known_args()
    raise NotImplementedError(
        "CC-P3: implementation deferred. See paper_context_ref/13 §9."
    )


if __name__ == "__main__":
    raise SystemExit(main())
