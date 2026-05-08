"""scripts/08_run_core_ablations.py — CC-P6 core ablation runner entrypoint placeholder.

Source docs:
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §12 (CC-P6)
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §18
"""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Run core ablations.")
    parser.add_argument("--config", required=True)
    parser.parse_known_args()
    raise NotImplementedError(
        "CC-P6: implementation deferred. See paper_context_ref/13 §12."
    )


if __name__ == "__main__":
    raise SystemExit(main())
