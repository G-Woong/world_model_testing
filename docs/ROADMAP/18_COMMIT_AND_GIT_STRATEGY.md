# Commit and Git Strategy

## Branch Policy
- Primary: `memory-redesign-2026-05-16` (current)
- Phase R14+ onward: create `paper-drafting-YYYY-MM-DD` branch
- PR to main: only after R14 gate passes and war-room synthesis PASS

## Conventional Commit Vocabulary

| prefix | meaning |
|---|---|
| `feat(fglc)` | new feature in src/fglc/ |
| `feat(data)` | new data collection or processing |
| `feat(train)` | training loop or loss implementation |
| `feat(detect)` | falsification gate / mismatch detector |
| `feat(attn)` | attention / CIRCA intervention module |
| `feat(correction)` | correction adapter |
| `feat(plan)` | planner integration |
| `test(fglc)` | new pytest for fglc |
| `results(R<N>)` | phase gate results verified |
| `docs(idea)` | docs/idea/ update |
| `docs(roadmap)` | docs/ROADMAP/ update |
| `chore(pivot)` | pivot-related infrastructure (used in Phase A) |
| `chore(turn)` | auto-commit from session end hook |
| `fix(fglc)` | bugfix in src/fglc/ |

## Atomic Commit Cadence
- One commit per logical unit (not per file)
- Never commit unverified experimental results
- Phase gate sentinel created ONLY after gate criteria verified (not speculatively)

## PR Boundaries
- R0..R7: single branch, sequential commits
- R8+: consider feature branches for each algorithm (ASAP, I3G, IVI)
- Paper sections: separate branch from code changes
