TASK_NAME: sync_probe
BACKGROUND: |
  Validate that post-sync Codex sub-agent honors the new AGENTS.md +
  updated codex_prompt_template.md contracts. This is a no-op verification
  task — it does not change any research code, model, data, or eval. Its
  sole purpose is to confirm that Codex: (a) reads AGENTS.md, (b) does not
  touch files outside FILES_ALLOWED, (c) produces a correctly-structured
  8-section RESULT.md, and (d) commits cleanly.

GOAL: |
  Create exactly two files:
    .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_HANDOFF.md
    .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_RESULT.md
  Touch nothing else. The HANDOFF.md records: current HEAD SHA, branch name,
  AGENTS.md byte size, codex_prompt_template.md byte size, and the line
  "Sync probe OK" if all checks pass.

FILES_ALLOWED:
  - .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_HANDOFF.md
  - .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_RESULT.md

FILES_FORBIDDEN:
  - "** (everything else)"

REQUIRED_IMPLEMENTATION: |
  1. Read AGENTS.md in full (from repo root).
  2. Read this TASK file in full.
  3. Run: git rev-parse HEAD   → record SHA.
  4. Run: git branch --show-current   → record branch name.
  5. Get file size of AGENTS.md   → record bytes.
  6. Get file size of .agent_tasks/codex_prompt_template.md   → record bytes.
  7. Write .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_HANDOFF.md
     with the following content (fill in actual values):
       # Sync Probe Handoff — 2026-05-23
       ## HEAD SHA
       <sha>
       ## Branch
       codex-work
       ## AGENTS.md size (bytes)
       <size>
       ## codex_prompt_template.md size (bytes)
       <size>
       ## Verification
       Sync probe OK
  8. No code changes elsewhere.

REQUIRED_TESTS:
  - pwsh: git status --short   # must be empty after commit
  - pwsh: Test-Path .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_HANDOFF.md
  - pwsh: Test-Path .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_RESULT.md

ACCEPTANCE_CRITERIA: |
  - Exactly 2 files added (HANDOFF.md + RESULT.md).
  - 0 files modified outside FILES_ALLOWED.
  - RESULT.md contains exactly 8 sections (Summary through Accept/Reject Recommendation).
  - Working tree clean after commit (git status --short returns empty).
  - HEAD SHA recorded in HANDOFF.md matches current repo HEAD.

COMMIT_MESSAGE: test(codex-sub-agent): sync probe — verify AGENTS.md + template contract

STOP_CONDITION: |
  Stop immediately after the single commit. Do not attempt cleanup,
  scope expansion, or additional file creation.

SANDBOX_MODE: default
