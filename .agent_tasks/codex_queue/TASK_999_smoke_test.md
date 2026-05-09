TASK_NAME: smoke_test
TASK_NUMBER: 999

BACKGROUND:
This is a harness smoke test. Its purpose is to verify the Claude→Codex orchestration
pipeline (assign → dispatch → verify → prepare-merge) end-to-end without touching any
real source code. No implementation work is required.

GOAL:
Verify that the orchestration harness operates correctly by completing a no-op task:
run the required tests, report results, write RESULT.md, and commit.

FILES_ALLOWED:
- .agent_tasks/codex_done/TASK_999_smoke_test_RESULT.md

FILES_FORBIDDEN:
- src/
- tests/
- scripts/
- paper_context_ref/
- .claude/
- CLAUDE.md
- .mcp.json
- .venv/
- data/
- outputs/
- secrets/
- .env*

REQUIRED_IMPLEMENTATION:
No source code changes. Only write RESULT.md to .agent_tasks/codex_done/TASK_999_smoke_test_RESULT.md.
The RESULT.md must include: files changed, tests run, pass/fail summary, blockers (none expected).

REQUIRED_TESTS:
python -m pytest tests/test_text_env.py

ACCEPTANCE_CRITERIA:
- python -m pytest tests/test_text_env.py exits 0
- .agent_tasks/codex_done/TASK_999_smoke_test_RESULT.md exists and is committed
- No source files modified
- Working tree is clean after commit

COMMIT_MESSAGE:
codex: complete smoke_test

STOP_CONDITION:
Stop immediately after the commit that includes RESULT.md. Do not modify any other files.
