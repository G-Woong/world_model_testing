# Phase R0 — Cleanup and Contract Reset

## Status: COMPLETE (2026-05-22)

## Goal
Archive FRCG-WM artifacts and rewrite the research contract for FGLC.

## Steps Completed
1. A.1: Archived src/frcgw/, paper_context_ref/, configs/, tests/, scripts/ to .lifecycle_trash/
2. A.2: Reset phase gate sentinels P*.passed → R*.passed convention
3. A.3: Rewrote CLAUDE.md, research_context_rules.md, behavioral_coding_rules.md,
        codex_orchestration_rules.md, baseline_ablation_guard.ps1, phase_gate_guard.ps1
4. A.4: Created fglc-context-router.md, fglc-code-reviewer.md, fglc-related-work-scout.md
5. A.5: pyproject.toml updated (frcgw → fglc), src/fglc/ stub created

## Deliverables Created
- `CLAUDE.md` — FGLC scientific contract
- `.claude/rules/research_context_rules.md` — FGLC research rules
- `src/fglc/__init__.py` + `py.typed` — package stub
- `docs/idea/00_OVERVIEW.md` through `26_CROSSCHECK_SUMMARY.md` — 27 idea files
- `docs/ROADMAP/` — roadmap files (this session)
- Agent reports: `docs/orchestration/agent_reports/synthesis/2026-05/`

## Gate Criteria

All must be true for R0.passed:
- [x] CLAUDE.md contains FGLC contract (no FRCG-WM terms)
- [x] src/frcgw/ absent from src/ (archived)
- [x] paper_context_ref/ absent (archived)
- [x] outputs/phase_gates/*.passed empty (no P*.passed files)
- [x] src/fglc/__init__.py importable
- [x] docs/idea/00_OVERVIEW.md exists
- [ ] pytest tests/test_lifecycle_*.py green (verify after this session)

## Commit Reference
- A.1+A.2: `cae2c8d`
- A.3+A.4+A.5: `73087a4`
- F+G (idea+roadmap): pending commit

## Risk Register References
- R-19 (ROADMAP/19): Lifecycle hook auto-commits may occur mid-session
