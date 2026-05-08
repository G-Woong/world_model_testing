"""scripts/04_generate_gui_mve_data.py — CC-P4 synthetic GUI MVE data collection entrypoint placeholder.

Source docs:
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §10 (CC-P4)
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §18
"""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic GUI MVE data.")
    parser.add_argument("--config", required=True)
    parser.parse_known_args()
    raise NotImplementedError(
        "CC-P4: implementation deferred. See paper_context_ref/13 §10."
    )


if __name__ == "__main__":
    raise SystemExit(main())
