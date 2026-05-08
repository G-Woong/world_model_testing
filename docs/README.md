# docs/

**Design context lives in `paper_context_ref/`. Do not duplicate or modify it.**

This directory is for operational artifacts generated during P1+ phases (handoff notes, gate logs, run summaries). It does not replace or copy `paper_context_ref/`.

---

## Context Router (from 13 §3 read policy)

| Task Type | Must Read | Then Read |
|---|---|---|
| repo scaffold / phase planning | `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md` | `14`, `15` |
| requirements checking | `paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md` | `13`, `15` |
| implementation design | `paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md` | `13`, `14` |
| schema / dataloader | `paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md` | `12`, `14`, `15` |
| data collection | `paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md` | `05`, `06`, `11`, `15` |
| model architecture | `paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md` | `03`, `06`, `08`, `09`, `15` |
| loss / reward | `paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | `06`, `07`, `09`, `15` |
| planning | `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md` | `07`, `08`, `10`, `15` |
| evaluation / baselines | `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md` | `07`, `08`, `09`, `11`, `15` |
| text-only smoke | `paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md` | `06`, `08`, `09`, `10`, `11`, `12` |
| synthetic GUI env | `paper_context_ref/05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` | `06`, `11`, `12`, `15` |
| paper framing | `paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md` | `00`, `01`, `02`, `10` |

**Always read first:** `paper_context_ref/00_CONTEXT_INDEX.md`

---

## docs/ Usage Policy

Any document added to `docs/` must:
1. Not fabricate empirical results.
2. Cite its source MD from `paper_context_ref/`.
3. Not duplicate or modify files in `paper_context_ref/`.

New documents placed here are operational (handoff notes, gate logs, run summaries), not design contracts.
